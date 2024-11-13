# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
from __future__ import annotations

from onnxscript.rewriter import _ir_utils, pattern


def rotate_half_pattern(op, x, start1, end1, start2, end2):
    # Slice(input, starts, ends, axes, steps)
    x1 = op.Slice(x, start1, end1, [3], [1])
    x2 = op.Slice(x, start2, end2, [3], [1])
    minus_x2 = op.Neg(x2)
    rotated_x = op.Concat(minus_x2, x1, axis=-1)
    return rotated_x


def _rotary_embedding_pattern(op, x, cos, sin, start1, end1, start2, end2):
    return x * cos + rotate_half_pattern(op, x, start1, end1, start2, end2) * sin


def _rotary_embedding(op, x, cos, sin, start1, end1, start2, end2):
    # Check that x is being split into two equal halves:
    start1_val = _ir_utils.get_singleton_value(start1)
    end1_val = _ir_utils.get_singleton_value(end1)
    start2_val = _ir_utils.get_singleton_value(start2)
    end2_val = _ir_utils.get_singleton_value(end2)

    if x is None or x.shape is None or len(x.shape) != 4:
        return None
    dim_size = x.shape[3]
    half_dim_size = dim_size // 2
    if (
        start1_val == 0
        and end1_val == half_dim_size
        and start2_val == half_dim_size
        and end2_val >= dim_size
    ):
        return op.RotaryEmbedding(x, cos, sin, interleaved=0, _domain="com.microsoft")
    return None


_rule = pattern.RewriteRule(_rotary_embedding_pattern, _rotary_embedding)

rotary_embedding_rules = pattern.RewriteRuleSet([_rule])
