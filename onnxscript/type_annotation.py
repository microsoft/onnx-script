# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# --------------------------------------------------------------------------
from __future__ import annotations

import collections
import inspect
import typing
from typing import Optional, Sequence, TypeVar, Union

import onnx
from typing_extensions import get_args, get_origin

from onnxscript import onnx_types

# TypeAnnotationValue represents the (value of) valid type-annotations recognized
# by ONNX Script. TODO: Flesh out a formal definition. Currently, it supports
# - float, int, str (primitive attribute types)
# - Sequence[float], Sequence[int], Sequence[str] (attribute types)
# - Tensor types
# - Sequence[Tensor] types
# - Union of above 2
# - TypeVars with above bounds
# - Above types with annotation attached
TypeAnnotationValue = typing.Any

# Map from python type to corresponding ONNX AttributeProto type
_PYTYPE_TO_ATTRTYPE_MAP = {
    float: onnx.AttributeProto.FLOAT,
    int: onnx.AttributeProto.INT,
    str: onnx.AttributeProto.STRING,
    bool: onnx.AttributeProto.INT,  # experimental
}

# Map from python type to corresponding ONNX AttributeProto type,
# for repeated (i.e., list of) values
_LISTTYPE_TO_ATTRTYPE_MAP = {
    float: onnx.AttributeProto.FLOATS,
    int: onnx.AttributeProto.INTS,
    str: onnx.AttributeProto.STRINGS,
    bool: onnx.AttributeProto.INTS,  # experimental
}

_LIST_CONSTRUCTORS = frozenset([list, typing.List, typing.Sequence, collections.abc.Sequence])

ALL_TYPE_STRINGS = (
    "tensor(bfloat16)",
    "tensor(bool)",
    "tensor(double)",
    "tensor(float)",
    "tensor(float16)",
    "tensor(int16)",
    "tensor(int32)",
    "tensor(int64)",
    "tensor(int8)",
    "tensor(string)",
    "tensor(uint16)",
    "tensor(uint32)",
    "tensor(uint64)",
    "tensor(uint8)",
)


def _remove_annotation(typeinfo: TypeAnnotationValue) -> TypeAnnotationValue:
    """Remove Annotated wrapper if present, otherwise return typeinfo as is."""
    if hasattr(typing, "Annotated"):
        # Present in Python 3.9+
        if get_origin(typeinfo) is typing.Annotated:
            return get_args(typeinfo)[0]
    return typeinfo


def _is_primitive_attr_type(typeinfo: TypeAnnotationValue) -> bool:
    return typeinfo in _PYTYPE_TO_ATTRTYPE_MAP


def pytype_to_attrtype(
    pytype: TypeAnnotationValue,
) -> typing.Optional[onnx.AttributeProto.AttributeType]:
    pytype = _remove_annotation(pytype)
    if pytype in _PYTYPE_TO_ATTRTYPE_MAP:
        return _PYTYPE_TO_ATTRTYPE_MAP[pytype]
    type_constructor = get_origin(pytype)
    # Remove Optional wrapper if present, which is represented as an Union[..., type(None)]
    if type_constructor is typing.Union:
        # Filter out type(None), since typing.Optional[X] evaluates to Union[X, type(None)]
        args = [x for x in get_args(pytype) if x is not type(None)]
        if len(args) == 1:
            return pytype_to_attrtype(args[0])
    if type_constructor in _LIST_CONSTRUCTORS:
        elt_type = get_args(pytype)[0]
        if elt_type in _LISTTYPE_TO_ATTRTYPE_MAP:
            return _LISTTYPE_TO_ATTRTYPE_MAP[elt_type]
    return None


def _is_tensor_type(typeinfo: TypeAnnotationValue) -> bool:
    if isinstance(typeinfo, onnx_types.TensorType):
        return True
    if inspect.isclass(typeinfo) and issubclass(typeinfo, onnx_types.TensorType):
        return True
    return False


def is_value_type(typeinfo: TypeAnnotationValue) -> bool:
    """Returns True if typeinfo represents a value type, False if it is an attribute type.
    Raises ValueError if typeinfo is not a supported type annotation.
    """
    typeinfo = _remove_annotation(typeinfo)
    if _is_tensor_type(typeinfo):
        return True
    if _is_primitive_attr_type(typeinfo):
        return False
    type_constructor = get_origin(typeinfo)
    # Handle List-like type-constructor
    # Eg. List[INT32] is a value type, while List[int] is an attribute type
    if type_constructor in _LIST_CONSTRUCTORS:
        elt_type = get_args(typeinfo)[0]
        return is_value_type(elt_type)
    # Handle Union and Optional type-constructors
    if type_constructor is typing.Union:
        # Filter out None, since typing.Optional[X] evaluates to Union[X, None]
        args = [x for x in get_args(typeinfo) if x is not type(None)]
        args_value_check = [is_value_type(x) for x in args]
        if all(args_value_check):
            # Handles cases like Optional[INT32] as well as Union[FLOAT16, FLOAT, DOUBLE]
            return True
        elif (len(args) == 1) and args_value_check[0] is False:
            # Handle the case of optional attribute: eg. Optional[int]
            # Note that we do not allow Union[int, float] for attributes.
            return False
        else:
            raise ValueError(f"Unsupported type annotation '{typeinfo}'")
    # Handle TypeVars:
    if isinstance(typeinfo, typing.TypeVar):
        if hasattr(typeinfo, "__bound__"):
            bound = typeinfo.__bound__
            return is_value_type(bound)
    raise ValueError(f"Unsupported type annotation {typeinfo}")


def is_attr_type(pytype: TypeAnnotationValue):
    return is_value_type(pytype) is False


def is_valid_type(typeinfo: TypeAnnotationValue):
    try:
        return is_value_type(typeinfo) in {True, False}
    except ValueError:
        return False


def get_return_types(typeinfo: type | typing.Sequence[type]) -> typing.Sequence[type]:
    """Converts return-type annotation into a sequence of types.

    The return type annotation can be either a single type (for a single output)
    or a Tuple type (for multiple outputs). This function normalizes the
    representation so that it is always a sequence of types, even for a single
    output.
    """
    if isinstance(typeinfo, typing.Sequence):
        return typeinfo
    if get_origin(typeinfo) is tuple:
        return get_args(typeinfo)
    return (typeinfo,)


# A sorted list of all type strings used in an OpSchema
ALL_TYPE_STRINGS = (
    "tensor(bfloat16)",
    "tensor(bool)",
    "tensor(double)",
    "tensor(float)",
    "tensor(float16)",
    "tensor(int16)",
    "tensor(int32)",
    "tensor(int64)",
    "tensor(int8)",
    "tensor(string)",
    "tensor(uint16)",
    "tensor(uint32)",
    "tensor(uint64)",
    "tensor(uint8)",
)


def pytype_to_input_strings(pytype: TypeAnnotationValue) -> list[str]:
    """Returns a list of all supported input types in string representation for a given type annotation.

    Args:
        pytype: A type annotation.

    Returns:
        A list of all supported input types for the given type annotation.
        Ensures that the list is sorted in the same order as ALL_TYPE_STRINGS.
    """
    if pytype is None:
        return list(ALL_TYPE_STRINGS)
    if pytype is type(None):
        return list(ALL_TYPE_STRINGS)
    if pytype is onnx_types.TensorType:
        return list(ALL_TYPE_STRINGS)
    if isinstance(pytype, type) and issubclass(pytype, onnx_types.TensorType):
        return [pytype.to_string()]
    if isinstance(pytype, onnx_types.TensorType):
        return [pytype.to_string()]
    if isinstance(pytype, TypeVar):
        constraints = pytype.__constraints__
        if constraints:
            return pytype_to_input_strings(Union.__getitem__(constraints))
        bound = pytype.__bound__
        if bound is None:
            return list(ALL_TYPE_STRINGS)
        return pytype_to_input_strings(bound)
    if typing.get_origin(pytype) is Union:
        options = []
        subtypes = typing.get_args(pytype)
        # A None type in a Union is equivalent to an optional type
        is_optional = any(subtype is type(None) for subtype in subtypes)
        for subtype in subtypes:
            if subtype is type(None):
                # Skip None type because we are handling it with is_optional
                continue
            if is_optional:
                options += [
                    *pytype_to_input_strings(subtype),
                    *[f"optional({s})" for s in pytype_to_input_strings(subtype)],
                ]
            else:
                options += pytype_to_input_strings(subtype)
        # Remove duplicates
        return sorted(set(options))
    if typing.get_origin(pytype) in _LIST_CONSTRUCTORS:
        subtypes = typing.get_args(pytype)
        return [f"seq({s})" for s in pytype_to_input_strings(subtypes[0])]

    raise ValueError(f"Unsupported type: {pytype}")


def get_type_constraint_name(pytype: TypeAnnotationValue) -> Optional[str]:
    """Returns the name of the type constraint for a given type annotation.

    Args:
        pytype: A type annotation.

    Returns:
        The name of the type constraint if it is a TypeVar.
        - Prefixes the name with "Optional_" if the type annotation is Optional[TypeVar].
        - Prefixes the name with "Sequence_" if the type annotation is a Sequence[].
        - Returns None if the type annotation does not have a type constraint.
    """
    if isinstance(pytype, TypeVar):
        return pytype.__name__
    if typing.get_origin(pytype) is Union:
        subtypes = typing.get_args(pytype)
        if len(subtypes) == 2 and type(None) in subtypes:
            for subtype in subtypes:
                if isinstance(subtype, TypeVar):
                    return f"Optional_{subtype.__name__}"
    if typing.get_origin(pytype) in _LIST_CONSTRUCTORS:
        subtypes = typing.get_args(pytype)
        if len(subtypes) == 1 and isinstance(subtypes[0], TypeVar):
            return f"Sequence_{get_type_constraint_name(subtypes[0])}"
    return None
