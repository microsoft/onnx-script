# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# --------------------------------------------------------------------------

"""Typings for function definitions."""

from __future__ import annotations

from typing import TypeVar, Union

from onnxscript import DOUBLE, FLOAT, FLOAT16, INT8, INT16, INT32, INT64

FloatType = Union[FLOAT16, FLOAT, DOUBLE]
IntType = Union[INT8, INT16, INT32, INT64]

TFloat = TypeVar("TFloat", bound=FloatType)
TInt = TypeVar("TInt", bound=IntType)
