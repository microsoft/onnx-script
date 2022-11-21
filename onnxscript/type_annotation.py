# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# --------------------------------------------------------------------------
from __future__ import annotations

from typing import List

import onnx

pytype_to_attrtype_map = {
    float: onnx.AttributeProto.FLOAT,
    int: onnx.AttributeProto.INT,
    str: onnx.AttributeProto.STRING,
    List[  # pylint: disable=unhashable-member # TODO: Need change
        int
    ]: onnx.AttributeProto.INTS,
}


def is_attr(typeinfo):
    return typeinfo in {
        float,
        int,
        str,
        List[float],  # pylint: disable=unhashable-member # TODO: Need change
        List[int],  # pylint: disable=unhashable-member # TODO: Need change
        List[str],  # pylint: disable=unhashable-member # TODO: Need change
    }


def is_tensor(typeinfo):
    return hasattr(typeinfo, "to_type_proto")
    # return isinstance(typeinfo, onnxscript.Tensor)  # TODO


def is_valid(typeinfo):
    return is_attr(typeinfo) or is_tensor(typeinfo)
