# SPDX-License-Identifier: Apache-2.0

from onnxscript.onnx import opset15 as op
from onnxscript.onnx_types import FLOAT

# same variable assigned multiple times


def renaming(A: FLOAT["N"]) -> FLOAT["N"]:
    T = op.Abs(A)
    T = op.Neg(A)
    return T

# clash between generated-name and pre-existing name


def renaming2(A: FLOAT["N"]) -> FLOAT["N"]:
    T_0 = op.Relu(A)
    T = op.Abs(A)
    T = op.Neg(A)
    return T
