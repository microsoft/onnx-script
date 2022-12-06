# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# --------------------------------------------------------------------------
# mypy: disable-error-code=misc
# mypy: disable-error-code=type-arg
# mypy: disable-error-code=valid-type
# mypy: disable-error-code=assignment
"""torch.ops.aten operators under the `nested` module.

- No inplace operators.
- All functions should not have the script() decorator. This is because
    we want to delay the compilation of the function.
"""
from __future__ import annotations

from typing import Optional

from onnxscript import TensorType


def aten_nested_to_padded_tensor(
    self: TensorType, padding: float, output_size: Optional[int] = None
) -> TensorType:
    # nested_to_padded_tensor(Tensor self, float padding, int[]? output_size=None) -> Tensor

    raise NotImplementedError()
