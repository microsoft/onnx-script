"""
ModelProto Properties
=====================

A ModelProto, in ONNX, usually stores extra information beyond the
computational graph, such as `ir_version` or `producer_name`.
Such properties of a generated ModelProto can be set by passing in extra named
parameters to the call to script (or the call to `to_model_proto`),
as illustrated by the example below.
Only the valid fields defined in the protobuf message ModelProto should
be specified in this fashion.

"""

# %%
# First, we define the implementation of a square-loss function in onnxscript.

from onnxscript import FLOAT
from onnxscript import opset15 as op
from onnxscript import proto2text, script


@script(ir_version=7, producer_name="OnnxScript", producer_version="0.1")
def square_loss(X: FLOAT["N"], Y: FLOAT["N"]) -> FLOAT[1]:  # noqa: F821
    diff = X - Y
    return op.ReduceSum(diff * diff, keepdims=1)


# %%
# Let's see what the generated model looks like.
model = square_loss.to_model_proto()
print(proto2text(model))
