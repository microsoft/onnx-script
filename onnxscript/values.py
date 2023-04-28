# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# --------------------------------------------------------------------------
from __future__ import annotations

import dataclasses
import inspect
import logging
import types
from enum import IntFlag
from typing import _GenericAlias  # type: ignore[attr-defined]
from typing import Any, Optional, Sequence

import onnx
import onnx.defs

from onnxscript import irbuilder, sourceinfo, type_annotation
from onnxscript._internal import version_utils

_ATTRIBUTE_TYPE_TO_PYTHON_TYPE = {
    onnx.defs.OpSchema.AttrType.FLOAT: float,
    onnx.defs.OpSchema.AttrType.INT: int,
    onnx.defs.OpSchema.AttrType.STRING: str,
    onnx.defs.OpSchema.AttrType.TENSOR: None,
    onnx.defs.OpSchema.AttrType.GRAPH: None,
    onnx.defs.OpSchema.AttrType.SPARSE_TENSOR: None,
    onnx.defs.OpSchema.AttrType.TYPE_PROTO: None,
    onnx.defs.OpSchema.AttrType.FLOATS: Sequence[float],
    onnx.defs.OpSchema.AttrType.INTS: Sequence[int],
    onnx.defs.OpSchema.AttrType.STRINGS: Sequence[str],
    onnx.defs.OpSchema.AttrType.TENSORS: None,
    onnx.defs.OpSchema.AttrType.GRAPHS: None,
    onnx.defs.OpSchema.AttrType.SPARSE_TENSORS: None,
    onnx.defs.OpSchema.AttrType.TYPE_PROTOS: None,
}

# A special value to indicate that the default value is not specified
_EmptyDefault = object()
_ONNX_OP_SCHEMA_WRITABLE = not version_utils.onnx_older_than("1.14")


class Opset:
    """Represents an ONNX Opset, which consists of a domain name, a version.

    It also contains a set of operations. This represents an Opset defined
    in the ONNX schema registry and the operations are retrieved from the
    ONNX schema registry. It also stores function definitions created for
    ops in the corresponding Opset.

    Only a single instance of Opset is created for a given (domain, version) pair.
    """

    cache: dict[tuple[type, str, int], Opset] = {}

    def __new__(cls, domain: str, version: int):
        key = (cls, domain, version)
        existing = cls.cache.get(key)
        if existing:
            return existing
        instance = super().__new__(cls)
        instance.domain = domain  # type: ignore[attr-defined]
        instance.version = version  # type: ignore[attr-defined]
        instance.function_defs = {}  # type: ignore[attr-defined]
        cls.cache[key] = instance
        return instance

    def __init__(self, domain: Optional[str] = None, version: Optional[int] = None):
        # Nothing to do. Object is initialized by __new__
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}({self.domain!r}, {self.version!r})"

    def __getitem__(self, opname):
        try:
            return onnx.defs.get_schema(opname, self.version, self.domain)
        except Exception:  # pylint: disable=broad-except # TODO: more specific exception
            return None

    def __contains__(self, opname):
        try:
            onnx.defs.get_schema(opname, self.version, self.domain)
            return True
        except Exception:  # pylint: disable=broad-except # TODO: more specific exception
            return False

    def __str__(self) -> str:
        return self.domain

    def __getattr__(self, attr: str):
        try:
            schema = onnx.defs.get_schema(attr, self.version, self.domain)
            return Op(self, attr, schema)
        except Exception as exc:
            raise AttributeError(f"Attribute {attr} not found.") from exc

    def add_function_def(self, fun):
        if fun.name in self.function_defs:
            logger = logging.getLogger("onnxscript")
            logger.warning("%s: Already defined.", fun.name)
        self.function_defs[fun.name] = fun

    def _prepare_inputs(self, _: onnx.defs.OpSchema, *inputs):
        """Trims 'None' values from the end of the inputs list. This is used to support
        omitting optional inputs when no more required inputs follow to prepare a valid call
        against the Op. Used by the static opset code generator.
        """
        # TODO: validate the op schema as 'None' values are removed?
        input_list = list(inputs)
        while input_list and input_list[-1] is None:
            del input_list[-1]
        return input_list


# ONNX ops


@dataclasses.dataclass(frozen=True)
class ParamSchema:
    """A schema for a parameter of an Op or a OnnxFunction.

    Attributes:
        name: The name of the parameter.
        type: The type of the parameter.
        default: The default value of the parameter.
        required: Whether the input or attribute is required.
            For example, `Slice` has two optional inputs `axes` and `steps`.
            `SoftmaxCrossEntropyLoss` has an optional attribute `ignore_index`.
        is_input: Whether the parameter is an ONNX input.
        is_variadic_input: Whether the parameter, which has to be an INPUT, is variadic.
    """

    name: str
    type: Any = None  # Op input does not have a type, for now
    default: Any = _EmptyDefault
    required: bool = True
    is_input: bool = True
    is_variadic_input: bool = False

    def __str__(self) -> str:
        """Return a string representation of the parameter.

        E.g. "x: Input[INT64]" or "axis: Attribute[int] = 0"
        """
        param_kind = "Input" if self.is_input else "Attribute"
        text = f"{self.name}: {param_kind}[{self.type}]"
        if self.default is not _EmptyDefault:
            text += f" = {self.default}"
        return text

    @property
    def is_attribute(self) -> bool:
        """Returns True if the parameter is an ONNX attribute."""
        return not self.is_input


def _get_attribute_value(attr_proto: onnx.AttributeProto) -> Any:
    """Get the default value of an ONNX attribute."""
    if attr_proto.type == onnx.AttributeProto.UNDEFINED:
        return _EmptyDefault
    return onnx.helper.get_attribute_value(attr_proto)


class Op:
    """Represents an ONNX op instance (for example, the MatMul op from ONNX opset version 13).
    It belongs to a particular Opset and has a name.

    Attributes:
        opset: The Opset that this op belongs to.
        opname: The name of the op.
        opschema: The ONNX OpSchema for the op.
    """

    def __init__(
        self, opset, opname: str, opschema: Optional[onnx.defs.OpSchema] = None
    ) -> None:
        self.opset = opset
        self.opname = opname
        self._opschema = opschema
        self._param_schemas: Optional[tuple[ParamSchema, ...]] = None

    def __call__(self, *args, **kwargs):
        # FIXME(after #225): Move import to the top of the file.
        from onnxscript import evaluator  # pylint: disable=import-outside-toplevel

        schema = self.opschema
        if schema is None:
            raise RuntimeError(
                f"Op '{self.opname}' does not have an OpSchema and cannot be evaluated."
            )
        return evaluator.default().eval(schema, args, kwargs)

    @property
    def opschema(self) -> Optional[onnx.defs.OpSchema]:
        return self._opschema

    def has_schema(self) -> bool:
        """Returns True if this op has an OpSchema."""
        return self.opschema is not None

    def param_schemas(self) -> Optional[tuple[ParamSchema, ...]]:
        """Returns the parameter schemas for this op, if it has one."""
        if self._param_schemas is not None:
            return self._param_schemas

        op_schema = self.opschema
        if op_schema is None:
            return None
        schemas = []
        for input_ in op_schema.inputs:
            param_schema = ParamSchema(
                name=input_.name,
                is_input=True,
                required=(input_.option != onnx.defs.OpSchema.FormalParameterOption.Optional),
                is_variadic_input=(
                    input_.option == onnx.defs.OpSchema.FormalParameterOption.Variadic
                ),
            )
            schemas.append(param_schema)
        for attr_name, attribute in op_schema.attributes.items():
            default_attr_proto = attribute.default_value
            param_schema = ParamSchema(
                name=attr_name,
                type=_ATTRIBUTE_TYPE_TO_PYTHON_TYPE[attribute.type],
                default=_get_attribute_value(default_attr_proto),
                is_input=False,
                required=attribute.required,
            )
            schemas.append(param_schema)

        self._param_schemas = tuple(schemas)
        return self._param_schemas  # type: ignore[return-value]


@dataclasses.dataclass(repr=False, eq=False)
class OnnxClosure:
    """Represents a nested function used as a graph-valued attribute for an ONNX op call."""

    function_ir: irbuilder.IRFunction

    # frame is python's stack-frame for the execution of top-level
    # script function (in eager-mode). It is used to get the current
    # value of outer-scope variables referred to inside this nested
    # function/GraphProto.
    frame: types.FrameType

    function: Any


@dataclasses.dataclass
class TypeConstraint:
    """Represents a type constraint for an ONNX op.

    Attributes:
        name: The name of the type constraint.
        allowed_types: The allowed types for the type constraint.
    """

    name: str
    allowed_types: list[str]
    description: str = ""

    def as_tuple(self) -> tuple[str, list[str], str]:
        """Returns the type constraint as a tuple."""
        return (self.name, self.allowed_types, self.description)


def op_schema_from_function_ir(
    function_ir: irbuilder.IRFunction, opset: Opset
) -> onnx.defs.OpSchema:
    """Construct an ONNX OpSchema from an IRFunction."""

    # Find all distinct types in the inputs and outputs
    distinct_types = {arg.typeinfo for arg in function_ir.inputs}.union(
        {arg.typeinfo for arg in function_ir.outputs}
    )
    # Create a mapping from type to a unique name
    type_to_constraint = {}
    for i, type_ in enumerate(distinct_types):
        name = f"T{i}"
        type_to_constraint[type_] = TypeConstraint(
            name=type_annotation.get_type_constraint_name(type_) or name,
            allowed_types=type_annotation.pytype_to_type_strings(type_),
        )

    formal_inputs = [
        onnx.defs.OpSchema.FormalParameter(
            arg.name,
            type_to_constraint[arg.typeinfo].name,
            param_option=(
                onnx.defs.OpSchema.FormalParameterOption.Optional
                if type_annotation.is_optional(arg.typeinfo)
                else onnx.defs.OpSchema.FormalParameterOption.Single
            ),
            # TODO(justinchu): Check this is_homogeneous thing
            is_homogeneous=True,
        )
        for arg in function_ir.inputs
    ]
    formal_outputs = [
        onnx.defs.OpSchema.FormalParameter(
            arg.name,
            type_to_constraint[arg.typeinfo].name,
            param_option=(
                onnx.defs.OpSchema.FormalParameterOption.Optional
                if type_annotation.is_optional(arg.typeinfo)
                else onnx.defs.OpSchema.FormalParameterOption.Single
            ),
            # TODO(justinchu): Check this is_homogeneous thing
            is_homogeneous=True,
        )
        for arg in function_ir.outputs
    ]

    return onnx.defs.OpSchema(
        function_ir.name,
        opset.domain,
        since_version=opset.version,
        doc=function_ir.docstring,
        inputs=formal_inputs,
        outputs=formal_outputs,
        type_constraints=[constraint.as_tuple() for constraint in type_to_constraint.values()],
        attributes=[
            *[
                onnx.defs.OpSchema.Attribute(
                    attr.name,
                    type=onnx.defs.OpSchema.AttrType(attr.type),
                )
                for attr in function_ir.attrs
                if not attr.has_default
            ],
            *[
                onnx.defs.OpSchema.Attribute(
                    attr.name,
                    default_value=attr.attr_proto,
                )
                for attr in function_ir.attrs
                if attr.has_default
            ],
        ],
    )


class OnnxFunction(Op):
    """Represents an ONNX op for which a function-body has been defined in onnxscript.

    Args:
        opset: opset the function belongs to
        pyfun: python function
        irfun: python code parsed by class
            :class:`onnxscript.converter.Converter`
        source: source code used to generate the function
        kwargs: additional properties used to construct a ModelProto
    """

    def __init__(
        self,
        opset: Optional[Opset],
        pyfun: types.FunctionType,
        irfun: irbuilder.IRFunction,
        source: str,
        kwargs: dict[str, Any],
    ):
        opset = opset or Opset(irfun.domain, 1)
        super().__init__(opset, irfun.name)
        self.function = pyfun
        self.function_ir = irfun
        self.source = source
        self.kwargs = kwargs
        self._param_schemas: Optional[tuple[ParamSchema, ...]] = None
        self._opschema: Optional[onnx.defs.OpSchema] = None
        # Set the signature of the class to function's
        self.__signature__ = inspect.signature(pyfun)

    @property
    def name(self):
        """Returns the function name."""
        return self.opname

    @property
    def opschema(self) -> Optional[onnx.defs.OpSchema]:
        """Construct an OpSchema from function_ir."""
        if self._opschema is not None:
            return self._opschema

        if not _ONNX_OP_SCHEMA_WRITABLE:
            return None

        self._opschema = op_schema_from_function_ir(self.function_ir, self.opset)

        return self._opschema

    def __getitem__(self, instance):
        """Returns a lambda to evaluate function using given evaluator instance.

        Usage:
            script_fun(X) executes the function using the default evaluator instance.
            script_fun[instance](X) executes the function using the given evaluator instance.
        """

        def fun(*args, **kwargs):
            # FIXME(after #225): Move import to the top of the file.
            from onnxscript import evaluator  # pylint: disable=import-outside-toplevel

            with evaluator.default_as(instance):
                return self.__call__(*args, **kwargs)

        return fun

    def __call__(self, *args, **kwargs):
        """Implements an eager-mode execution of an onnxscript function."""
        # FIXME(after #225): Move import to the top of the file.
        from onnxscript import evaluator  # pylint: disable=import-outside-toplevel

        return evaluator.default().eval_function(self, args, kwargs)

    def param_schemas(self) -> tuple[ParamSchema, ...]:
        """Returns the parameter schemas of this function."""
        if self._param_schemas is not None:
            return self._param_schemas

        # NOTE: We generate the parameter schemas from the function_ir instead
        # of relying on the auto generated OpSchema because we need to preserve the keyword
        # argument order from the Python function definition, which is lost in OpSchema.
        function_ir = self.function_ir
        # The first len(func_ir.inputs) arguments are onnx inputs
        inputs = function_ir.inputs
        # The rest is onnx attributes

        schemas = []
        for arg in inputs:
            if isinstance(arg.typeinfo, onnx.TypeProto.Optional):
                required = False
            else:
                required = True
            schemas.append(
                ParamSchema(name=arg.name, type=arg.typeinfo, is_input=True, required=required)
            )

        for attr_parameter in function_ir.attrs:
            schemas.append(
                ParamSchema(
                    name=attr_parameter.name,
                    type=_ATTRIBUTE_TYPE_TO_PYTHON_TYPE.get(
                        onnx.defs.OpSchema.AttrType(attr_parameter.type)  # type: ignore[call-arg]
                    ),
                    default=_EmptyDefault
                    if attr_parameter.default_value is None
                    else attr_parameter.default_value,
                    is_input=False,
                    required=not attr_parameter.has_default,
                )
            )

        self._param_schemas = tuple(schemas)
        return self._param_schemas  # type: ignore[return-value]

    def to_function_proto(self):
        """Converts the function into :class:`onnx.FunctionProto`."""
        return self.function_ir.to_function_proto()

    def to_model_proto(self, **kwargs):
        """Converts the function into :class:`onnx.ModelProto`."""
        if self.function_ir.attrs and any(
            not attr.has_default for attr in self.function_ir.attrs
        ):
            raise ValueError(
                "A function with required attributes cannot be exported as a model."
            )
        # Note: The function must also have monomorphic type annotation for inputs/outputs
        # to be converted into a valid model. Otherwise, we can still produce an ONNX
        # model, but it will not pass the ONNX model checker. We do not report an error
        # at this stage.

        # Merge kwargs specified in script-decorator with those specified in this call.
        merged_kw_args = {**self.kwargs, **kwargs}
        return self.function_ir.to_model_proto(**merged_kw_args)


class SymbolValue:
    """Represents script-time value information about named variables used in a script.

    At translation-time, the (local) variables of a script, including its parameters,
    are bound to a SymbolValue.

    SymbolValues fall into the following categories:

    AttrRef: Function parameters of attribute-kind, also mapped to ONNX attributes

    Dynamic: values computed at runtime (of tensor type, for now) mapped to NodeArgs.
    Dynamic values include input-parameters of the script, as well intermediate
    values computed in the script.

    For example, consider the following script definition:
    ::

        @script()
        def ThresholdedRelu(X, alpha: float):
            zero = op.CastLike(0, X)
            return op.Where(X > alpha, X, zero)

    Here, `X` has a Dynamic value, `alpha` has an AttrRef value, and `zero`
    has a Dynamic value.

    Scripts may also contain references to global variables, but the translator
    does not associate a SymbolValue with them. The python value of global variables
    is used directly in the translation, and such global variables are intended
    to be used for limited purposes, namely:
    * To identify an opset
    * To represent constant-values, translated into ONNX constants.
    """

    def __init__(self, info: sourceinfo.SourceInfo) -> None:
        if not isinstance(info, sourceinfo.SourceInfo):
            raise TypeError(f"info must be of type sourceinfo.SourceInfo not {type(info)!r}.")
        self.info = info


class AttrRef(SymbolValue):
    def __init__(
        self, attr_name: str, typeinfo: _GenericAlias, info: sourceinfo.SourceInfo
    ) -> None:
        """Initializes AttrRef.

        Arguments:
            attr_name: name of the attribute-parameter
            typeinfo: type annotation of the attribute.
                op's attributes in ONNX are usually single type or list of single type.
            info: for debugging use.
        """
        super().__init__(info)
        self.value = attr_name
        self.typeinfo = typeinfo
        if not isinstance(typeinfo, (type, _GenericAlias)):
            # typing._GenericAlias for List[int] and List[str], etc.
            raise TypeError(f"Expecting a type not f{type(typeinfo)} for typeinfo.")
        self.typeinfo = typeinfo


class DynamicKind(IntFlag):
    Unknown = 0
    Input = 1
    Output = 2
    Intermediate = 4
    Loop = 8


class Dynamic(SymbolValue):
    def __init__(
        self, onnx_var: str, kind: DynamicKind, info: sourceinfo.SourceInfo, typeinfo=None
    ) -> None:
        """Initializes Dynamic.

        Arguments:
            onnx_var: the name of the ONNX variable used to represent this value
            kind: the DynamicKind of this variable
            info: source-location information for error-messages/debugging
            typeinfo: type-information for the value
        """
        super().__init__(info)
        assert isinstance(kind, DynamicKind)
        self.value = onnx_var
        self.kind = kind
        self.typeinfo = typeinfo
