# SPDX-License-Identifier: Apache-2.0

from onnxscript.onnx import opset15 as op
from onnxscript.onnx_types import FLOAT, INT64

# simple loop


def sumprod(x: FLOAT['N'], N: INT64) -> (FLOAT['N'], FLOAT['N']):
    sum = op.Identity(x)
    prod = op.Identity(x)
    for i in range(N):
        sum = sum + x
        prod = prod * x
    return sum, prod

# loop: loop-bound as an expression


def sumprod2(x: FLOAT['N'], N: INT64) -> (FLOAT['N'], FLOAT['N']):
    sum = op.Identity(x)
    prod = op.Identity(x)
    for i in range(2 * N + 1):
        sum = sum + x
        prod = prod * x
    return sum, prod
