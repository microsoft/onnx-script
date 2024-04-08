# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# --------------------------------------------------------------------------
"""In-memory intermediate representation for ONNX graphs."""

__all__ = [
    # Modules
    "serde",
    # IR classes
    "Attr",
    "AttrFloat32",
    "AttrFloat32s",
    "AttrGraph",
    "AttrGraphs",
    "AttrInt64",
    "AttrInt64s",
    "AttrSparseTensor",
    "AttrSparseTensors",
    "AttrString",
    "AttrStrings",
    "AttrTensor",
    "AttrTensors",
    "AttrTypeProto",
    "Dimension",
    "ExternalTensor",
    "Function",
    "Graph",
    "Input",
    "Model",
    "Node",
    "RefAttr",
    "Shape",
    "Tensor",
    "Value",
    "TensorType",
    "OptionalType",
    "SequenceType",
    "SparseTensorType",
    # Protocols
    "ArrayCompatible",
    "DLPackCompatible",
    "TensorProtocol",
    "ValueProtocol",
    "ModelProtocol",
    "NodeProtocol",
    "GraphProtocol",
    "AttributeProtocol",
    "ReferenceAttributeProtocol",
    "SparseTensorProtocol",
    "DimensionProtocol",
    "ShapeProtocol",
    "TypeProtocol",
    "MapTypeProtocol",
    "FunctionProtocol",
    # Enums
    "AttributeType",
    "DataType",
]

from onnxscript.ir import serde
from onnxscript.ir._core import (
    Attr,
    AttrFloat32,
    AttrFloat32s,
    AttrGraph,
    AttrGraphs,
    AttrInt64,
    AttrInt64s,
    AttrSparseTensor,
    AttrSparseTensors,
    AttrString,
    AttrStrings,
    AttrTensor,
    AttrTensors,
    AttrTypeProto,
    Dimension,
    ExternalTensor,
    Function,
    Graph,
    Input,
    Model,
    Node,
    OptionalType,
    RefAttr,
    SequenceType,
    Shape,
    SparseTensorType,
    Tensor,
    TensorType,
    Value,
)
from onnxscript.ir._enums import (
    AttributeType,
    DataType,
)
from onnxscript.ir._protocols import (
    ArrayCompatible,
    AttributeProtocol,
    DimensionProtocol,
    DLPackCompatible,
    FunctionProtocol,
    GraphProtocol,
    MapTypeProtocol,
    ModelProtocol,
    NodeProtocol,
    ReferenceAttributeProtocol,
    ShapeProtocol,
    SparseTensorProtocol,
    TensorProtocol,
    TypeProtocol,
    ValueProtocol,
)
