# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# --------------------------------------------------------------------------
from __future__ import annotations

import dataclasses
import logging
import types
from enum import IntFlag
from typing import Any, Optional, _GenericAlias  # type: ignore[attr-defined]

import onnx
import onnx.defs

from onnxscript import irbuilder, sourceinfo, tensor


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

            logger = logging.getLogger("onnx-script")
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


class Op:
    """Represents an ONNX op instance (for example, the MatMul op from ONNX opset version 13).
    It belongs to a particular Opset and has a name.
    """

    def __init__(
        self, opset, opname: str, opschema: Optional[onnx.defs.OpSchema] = None
    ) -> None:
        self.opset = opset
        self.opname = opname
        self.opschema = opschema

    def is_single_op(self) -> bool:
        return isinstance(self.opname, str)

    def get_schema(self) -> onnx.defs.OpSchema:
        if self.opschema:
            return self.opschema
        return self.opset[self.opname]

    def has_schema(self) -> bool:
        return self.opschema is not None

    def adapt_kwargs(self, kwargs):
        """Replaces function-valued attribute-values by their GraphProto representation."""
        closure: dict[str, Any] = {}
        for k, v in kwargs.items():
            if isinstance(v, OnnxClosure):
                kwargs[k] = v.function_ir.to_graph_proto()
                for pyvar, onnxvar in v.function_ir.outer_scope_variables:
                    closure[onnxvar.value] = v.frame.f_locals[pyvar]
            elif callable(v):
                raise ValueError(
                    f"Error: function-valued attribute {v.__name__!r} has no graph_proto"
                    "attribute. Did you forget to decorate it with @graph?"
                )
        return kwargs, closure

    def _convert_kwargs_to_numpy(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        new_kwargs = {}
        for k, v in kwargs.items():
            new_kwargs[k] = v
            if isinstance(v, tensor.Tensor):
                new_kwargs[k] = v.value

        return new_kwargs

    def __call__(self, *args, **kwargs):
        # FIXME(after #225): Move import to the top of the file.
        from onnxscript import evaluator  # pylint: disable=import-outside-toplevel

        return evaluator.default().eval(
            self.opschema, args, self._convert_kwargs_to_numpy(kwargs)
        )


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

    def __init__(self, opset, pyfun, irfun, source, kwargs):
        opset = opset or Opset(irfun.domain, 1)
        super().__init__(opset, irfun.name)
        self.function = pyfun
        self.function_ir = irfun
        self.source = source
        self.kwargs = kwargs

    @property
    def name(self):
        """Returns the function name."""
        return self.opname

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

    def to_function_proto(self):
        """Converts the function into :class:`onnx.FunctionProto`."""
        return self.function_ir.to_function_proto()

    def to_model_proto(self, **kwargs):
        """Converts the function into :class:`onnx.ModelProto`."""
        if self.function_ir.attrs:
            raise ValueError("A function with attributes cannot be exported as a model.")
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
