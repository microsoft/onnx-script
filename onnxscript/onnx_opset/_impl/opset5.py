# --------------------------------------------------------------------------
# ⚠️ WARNING - AUTO-GENERATED CODE - DO NOT EDIT ⚠️
# ⚙️ Generated by 'python -m opgen'
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# --------------------------------------------------------------------------
# flake8: noqa
# mypy: disable-error-code=override
# pylint: disable=W0221,W0222,W0237,W0246,R0901
# --------------------------------------------------------------------------

from typing import Callable, Union

from onnx.defs import get_schema

from onnxscript.onnx_opset._impl.opset4 import Opset4
from onnxscript.onnx_types import (
    BOOL,
    COMPLEX64,
    COMPLEX128,
    DOUBLE,
    FLOAT,
    FLOAT16,
    INT8,
    INT16,
    INT32,
    INT64,
    STRING,
    UINT8,
    UINT16,
    UINT32,
    UINT64,
)
from onnxscript.values import Op, Opset


class Opset5(Opset4):
    def __new__(cls):
        return Opset.__new__(cls, "", 5)

    def __init__(self):
        super().__init__()

    def Reshape(
        self,
        data: Union[
            BOOL,
            COMPLEX128,
            COMPLEX64,
            DOUBLE,
            FLOAT,
            FLOAT16,
            INT16,
            INT32,
            INT64,
            INT8,
            STRING,
            UINT16,
            UINT32,
            UINT64,
            UINT8,
        ],
        shape: INT64,
    ) -> Union[
        BOOL,
        COMPLEX128,
        COMPLEX64,
        DOUBLE,
        FLOAT,
        FLOAT16,
        INT16,
        INT32,
        INT64,
        INT8,
        STRING,
        UINT16,
        UINT32,
        UINT64,
        UINT8,
    ]:
        r"""[🌐 Reshape(5)](https://onnx.ai/onnx/operators/onnx__Reshape.html#reshape-5 "Online Documentation")


        Reshape the input tensor similar to numpy.reshape.
        First input is the data tensor, second input is a shape tensor which specifies the output shape. It outputs the reshaped tensor.
        At most one dimension of the new shape can be -1. In this case, the value is
        inferred from the size of the tensor and the remaining dimensions. A dimension
        could also be 0, in which case the actual dimension value is unchanged (i.e. taken
        from the input tensor). Shape (second input) could be an empty shape, which means converting to a scalar.
        The input tensor's shape and the output tensor's shape are required to have the same number of elements.

        Args:
            data: An input tensor.

            shape: Specified shape for output.
        """

        schema = get_schema("Reshape", 5, "")
        op: Callable[
            ...,
            Union[
                BOOL,
                COMPLEX128,
                COMPLEX64,
                DOUBLE,
                FLOAT,
                FLOAT16,
                INT16,
                INT32,
                INT64,
                INT8,
                STRING,
                UINT16,
                UINT32,
                UINT64,
                UINT8,
            ],
        ] = Op(self, "Reshape", schema)
        return op(*self._prepare_inputs(schema, data, shape))
