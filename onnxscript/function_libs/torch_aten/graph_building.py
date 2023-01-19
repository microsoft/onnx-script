"""Graph building functions for torchscript graph backend."""
from __future__ import annotations

import collections
import typing
import warnings
from typing import Dict, List, Sequence, Union, Any

import numpy as np
import onnx
import torch
from torch.onnx import _type_utils
from torch.onnx._internal import jit_utils

import onnxscript
from onnxscript import evaluator, tensor as onnxscript_tensor


ValidArgumentType = Union["TorchScriptTensor", str, int, float]


class TorchScriptTensor(onnxscript_tensor.Tensor):
    """A onnxscript tensor that wraps a torchscript Value."""

    def __init__(self, value: torch.Value):
        super().__init__(None)
        self._value = value

    @property
    def value(self) -> np.ndarray:
        raise NotImplementedError()

    def symbolic_value(self) -> torch.Value:
        return self._value

    @property
    def rank(self) -> int | None:
        value_type = self._value.type()
        if value_type is None:
            return None
        value_type = typing.cast(torch.TensorType, value_type)
        return value_type.dim()

    @property
    def shape(self) -> tuple[int | None, ...] | None:
        value_type = self._value.type()
        if value_type is None:
            return None
        value_type = typing.cast(torch.TensorType, value_type)
        shape = value_type.varyingSizes()
        if shape is None:
            return None
        return tuple(shape)

    @property
    def dtype(self):
        # TODO: Return numpy dtype
        return _type_utils.JitScalarType.from_value(
            self._value, default=_type_utils.JitScalarType.UNDEFINED
        ).dtype()

    @property
    def onnx_dtype(self):
        return _type_utils.JitScalarType.from_value(
            self._value, _type_utils.JitScalarType.UNDEFINED
        ).onnx_type()


def _parse_torch_value(value: torch.Value, attr_type: onnx.AttributeProto.AttributeType):
    if attr_type == onnx.AttributeProto.FLOAT:
        return float(value)
    if attr_type == onnx.AttributeProto.INT:
        return int(value)
    if attr_type == onnx.AttributeProto.STRING:
        return str(value)
    if attr_type == onnx.AttributeProto.FLOATS:
        return [float(v) for v in value]
    if attr_type == onnx.AttributeProto.INTS:
        return [int(v) for v in value]

    return value


def _parse_node(value: torch.Value):
    # Why do we find the node and then get the same value back?
    node = value.node()
    if node.mustBeNone():
        return None
    if node.kind() == "onnx::Constant":
        return torch.onnx.symbolic_helper._node_get(node, "value")
    raise ValueError("[ERROR] Attribute is not Constant!!!")


def _adapt_torchscript_inputs(onnx_func, args, kwargs):
    func_ir = onnx_func.function_ir
    assert len(func_ir.inputs) + len(func_ir.attr_protos) == len(args)
    # The first len(func_ir.inputs) arguements are onnx inputs
    onnx_inputs = args[: len(func_ir.inputs)]
    # The rest is onnx attributes
    # Contruct a dictionary of attributes with names specified in the function
    # definition
    attributes = args[len(func_ir.inputs) :]
    onnx_attrs = {}

    # (1) Some/All attributes are supplied as positional arguments
    # (2) Some attributes are supplied as kwargs
    # (3) Some arguments in kwargs are not defined in the onnx function
    attr_name_to_protos = collections.OrderedDict(
        (attr.name, attr) for attr in func_ir.attr_protos
    )
    assert len(attr_name_to_protos) >= len(attributes)
    for attr_proto, attr_value in zip(attr_name_to_protos.values(), attributes):
        node_val = _parse_node(attr_value)
        onnx_attrs[attr_proto.name] = _parse_torch_value(node_val, attr_proto.type)

    for key, value in kwargs.items():
        if key not in attr_name_to_protos:
            warnings.warn(f"Attribute '{key}' is not defined in the function definition")
            continue
        # Fill in the values from kwargs
        attr_proto = attr_name_to_protos[key]
        onnx_attrs[key] = _parse_torch_value(value, attr_proto.type)

    # Fill in the default values
    for key, attr_proto in attr_name_to_protos.items():
        if key not in onnx_attrs:
            onnx_attrs[key] = attr_proto.value

    onnx_inputs = _wrap_torch_value_to_tensor(onnx_inputs)
    onnx_attrs = _wrap_torch_value_to_tensor(onnx_attrs)

    return onnx_inputs, onnx_attrs


def _convert_kwargs_for_torchscript(kwargs):
    encoded = {}
    for attr_name, attr in kwargs.items():
        if isinstance(attr, float):
            attr_name += "_f"
        elif isinstance(attr, int):
            attr_name += "_i"
        elif isinstance(attr, str):
            attr_name += "_s"
        elif isinstance(attr, list):
            if isinstance(attr, float):
                attr_name += "_f"
            elif isinstance(attr, int):
                attr_name += "_i"
        encoded[attr_name] = attr
    return encoded


def _wrap_torch_value_to_tensor(
    value: Union[Dict[str, Any], List]
) -> Union[Dict[str, Any], List]:
    # wrap torch.Value with TorchScriptTensor
    if isinstance(value, dict):
        value = {
            k: TorchScriptTensor(v) if isinstance(v, torch.Value) else v
            for k, v in value.items()
        }
    elif isinstance(value, list):
        value = [TorchScriptTensor(v) if isinstance(v, torch.Value) else v for v in value]
    elif isinstance(value, tuple):
        return tuple(TorchScriptTensor(v) if isinstance(v, torch.Value) else v for v in value)
    elif isinstance(value, TorchScriptTensor):
        value = value.symbolic_value()
    return value


class TorchScriptEvaluator(evaluator.Evaluator):
    def __init__(self, graph: TorchScriptGraph):
        self._graph = graph

    @property
    def graph(self) -> TorchScriptGraph:
        return self._graph

    def eval_function(self, function: onnxscript.OnnxFunction, *args, **kwargs):
        return self._graph.add_function(function, args, kwargs)

    def _eval(self, schema, inputs, attributes):
        # TODO: Does it really know what the inputs are?
        return self._graph.add_op(schema, inputs, attributes)


class TorchScriptGraph:
    def __init__(self):
        self._graph = torch._C.Graph()
        self._graph_context = jit_utils.GraphContext(
            graph=self._graph,
            block=self._graph.block(),  # Pointless. Just make linter happy.
            opset=-1,
            original_node=self._graph.insertPoint(),  # Pointless. Just make linter happy.
            params_dict={},  # Pointless. Just make linter happy.
            env={},  # Pointless. Just make linter happy.
        )
        # All the functions used, deduplicated by name
        self._function_store: dict[str, onnxscript.OnnxFunction] = {}

    @property
    def graph(self):
        return self._graph

    # @property
    # def graph_context(self):
    #     return self._graph_context

    def add_input(self, input_name: str, input_value: torch.Tensor) -> TorchScriptTensor:
        # TODO: Take in a TorchScriptTensor?
        torch_value = self._graph.addInput(input_name)
        torch_value.setType(torch._C.TensorType.create_from_tensor(input_value))
        return torch_value

    def register_output(
        self, outputs: Union[TorchScriptTensor, tuple[TorchScriptTensor, ...]]
    ):
        # TODO: Unwrap TorchScriptTensors?
        if isinstance(outputs, TorchScriptTensor):
            self._graph.registerOutput(outputs)
        else:
            for ts_output in outputs:
                assert isinstance(
                    ts_output, TorchScriptTensor
                ), f"ts_output must be a torch._C.Value, not {type(ts_output)}"
                self._graph.registerOutput(ts_output)
        return

    def _add_torchscript_op(
        self,
        name,
        args,
        kwargs,
        outputs: int,
    ) -> TorchScriptTensor | tuple[TorchScriptTensor, ...]:
    # TODO: here
        unwrapped_args = [
            v.symbolic_value() if isinstance(v, TorchScriptTensor) else v for v in args
        ]
        unwrapped_kwargs = {
            k: v.symbolic_value() if isinstance(v, TorchScriptTensor) else v
            for k, v in kwargs.items()
        }
        encoded_kwargs = _convert_kwargs_for_torchscript(unwrapped_kwargs)
        result = self._graph_context.op(name, *args, outputs=1, **encoded_kwargs)
        if isinstance(result, Sequence):
            return tuple(TorchScriptTensor(v) for v in result)
        return TorchScriptTensor(result)

    def add_op(
        self,
        onnx_op,
        args: Sequence[ValidArgumentType | Sequence[ValidArgumentType]],
        kwargs: dict[str, ValidArgumentType | Sequence[ValidArgumentType]],
    ):
        # TODO: Decide input and outputs

        encoded_kwargs = _convert_kwargs_for_torchscript(kwargs)

        # Compute outputs from the onnx_op op schema

        # This is not a tuple for now. TODO: Check output
        result = self._add_torchscript_op(
            onnx_op.name, onnx_inputs, onnx_attributes, outputs=1
        )

        return result

    def add_function(
        self,
        onnx_function: onnxscript.OnnxFunction,
        args,
        kwargs,
    ):
        self._function_store[onnx_function.name] = onnx_function

        # TODO: Decide input and outputs

        encoded_kwargs = _convert_kwargs_for_torchscript(kwargs)

        # Compute outputs from the onnx_op op schema

        # This is not a tuple for now. TODO: Check output
        result = self._add_torchscript_op(
            onnx_function.name, onnx_inputs, onnx_attributes, outputs=1
        )

        return result
