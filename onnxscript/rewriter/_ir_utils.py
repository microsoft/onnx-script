"""This is a temporary utility to assist new IR while it's still under development."""

from __future__ import annotations

import typing

import numpy as np

from onnxscript import ir

GRAPH_OUTPUT_META_KEY = "pkg.onnxscript.rewriter.generic_pattern.graph_output"


def propagate_const_value(ir_value: ir.Value) -> ir.Value:
    """Temporary method to propagate a constant value to the IR value."""
    node = ir_value.producer()
    if ir_value.const_value is None and node is not None and node.op_type == "Constant":
        for attr_name in (
            "value_float",
            "value_int",
            "value_string",
            "value",
            "value_floats",
            "value_ints",
            "value_strings",
        ):
            attr_value = node.attributes.get(attr_name)
            if attr_value is None or not isinstance(attr_value, ir.Attr):
                continue

            const_value: ir.TensorProtocol
            if attr_name in {"value_float", "value_floats"}:
                const_value = ir.Tensor(
                    np.array(attr_value.value, dtype=np.float32), name=ir_value.name
                )
            elif attr_name in {"value_int", "value_ints"}:
                const_value = ir.Tensor(
                    np.array(attr_value.value, dtype=np.int64), name=ir_value.name
                )
            elif attr_name in {"value_string", "value_strings"}:
                const_value = ir.StringTensor(
                    np.array(attr_value.value, dtype=np.bytes_), name=ir_value.name
                )
            elif attr_name == "value":
                const_value = typing.cast(ir.TensorProtocol, attr_value.value)

            ir_value.const_value = const_value
            ir_value.shape = const_value.shape  # type: ignore
            ir_value.dtype = const_value.dtype
            break
    return ir_value


def get_numpy_from_ir_value(value: ir.Value) -> np.ndarray | None:
    constant_value = value.const_value
    if constant_value is not None:
        if isinstance(constant_value, ir.serde.TensorProtoTensor):
            return constant_value.numpy()
        return np.array(constant_value)
    return constant_value
