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

from typing import Callable, Optional, Tuple, Union

from onnx.defs import get_schema

from onnxscript.onnx_opset._impl.opset5 import Opset5
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


class Opset6(Opset5):
    def __new__(cls):
        return Opset.__new__(cls, "", 6)

    def __init__(self):
        super().__init__()

    def Abs(
        self,
        X: Union[
            DOUBLE, FLOAT, FLOAT16, INT16, INT32, INT64, INT8, UINT16, UINT32, UINT64, UINT8
        ],
    ) -> Union[
        DOUBLE, FLOAT, FLOAT16, INT16, INT32, INT64, INT8, UINT16, UINT32, UINT64, UINT8
    ]:
        r"""[🌐 Abs(6)](https://onnx.ai/onnx/operators/onnx__Abs.html#abs-6 "Online Documentation")


        Absolute takes one input data (Tensor<T>) and produces one output data
        (Tensor<T>) where the absolute is, y = abs(x), is applied to
        the tensor elementwise.


        Args:
            X: Input tensor
        """

        schema = get_schema("Abs", 6, "")
        op: Callable[
            ...,
            Union[
                DOUBLE,
                FLOAT,
                FLOAT16,
                INT16,
                INT32,
                INT64,
                INT8,
                UINT16,
                UINT32,
                UINT64,
                UINT8,
            ],
        ] = Op(self, "Abs", schema)
        return op(*self._prepare_inputs(schema, X))

    def Add(
        self,
        A: Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64],
        B: Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64],
        axis: Optional[int] = None,
        broadcast: int = 0,
    ) -> Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64]:
        r"""[🌐 Add(6)](https://onnx.ai/onnx/operators/onnx__Add.html#add-6 "Online Documentation")


        Performs element-wise binary addition (with limited broadcast support).

        If necessary the right-hand-side argument will be broadcasted to match the
        shape of left-hand-side argument. When broadcasting is specified, the second
        tensor can either be of element size 1 (including a scalar tensor and any
        tensor with rank equal to or smaller than the first tensor), or having its
        shape as a contiguous subset of the first tensor's shape. The starting of the
        mutually equal shape is specified by the argument "axis", and if it is not set,
        suffix matching is assumed. 1-dim expansion doesn't work yet.

        For example, the following tensor shapes are supported (with broadcast=1):

          shape(A) = (2, 3, 4, 5), shape(B) = (,), i.e. B is a scalar tensor
          shape(A) = (2, 3, 4, 5), shape(B) = (1, 1), i.e. B is an 1-element tensor
          shape(A) = (2, 3, 4, 5), shape(B) = (5,)
          shape(A) = (2, 3, 4, 5), shape(B) = (4, 5)
          shape(A) = (2, 3, 4, 5), shape(B) = (3, 4), with axis=1
          shape(A) = (2, 3, 4, 5), shape(B) = (2), with axis=0

        Attribute `broadcast=1` needs to be passed to enable broadcasting.


        Args:
            A: First operand, should share the type with the second operand.

            B: Second operand. With broadcasting can be of smaller size than A. If
                broadcasting is disabled it should be of the same size.

            axis: If set, defines the broadcast dimensions. See doc for details.

            broadcast: Pass 1 to enable broadcasting
        """

        schema = get_schema("Add", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64]] = Op(
            self, "Add", schema
        )
        return op(*self._prepare_inputs(schema, A, B), axis=axis, broadcast=broadcast)

    def BatchNormalization(
        self,
        X: Union[DOUBLE, FLOAT, FLOAT16],
        scale: Union[DOUBLE, FLOAT, FLOAT16],
        B: Union[DOUBLE, FLOAT, FLOAT16],
        mean: Union[DOUBLE, FLOAT, FLOAT16],
        var: Union[DOUBLE, FLOAT, FLOAT16],
        epsilon: float = 9.999999747378752e-06,
        is_test: int = 0,
        momentum: float = 0.8999999761581421,
        spatial: int = 1,
    ) -> Tuple[
        Union[DOUBLE, FLOAT, FLOAT16],
        Union[DOUBLE, FLOAT, FLOAT16],
        Union[DOUBLE, FLOAT, FLOAT16],
        Union[DOUBLE, FLOAT, FLOAT16],
        Union[DOUBLE, FLOAT, FLOAT16],
    ]:
        r"""[🌐 BatchNormalization(6)](https://onnx.ai/onnx/operators/onnx__BatchNormalization.html#batchnormalization-6 "Online Documentation")


        Carries out batch normalization as described in the paper
        https://arxiv.org/abs/1502.03167. Depending on the mode it is being run,
        there are multiple cases for the number of outputs, which we list below:

        Output case #1: Y, mean, var, saved_mean, saved_var (training mode)
        Output case #2: Y (test mode)


        Args:
            X: Input data tensor from the previous operator; dimensions for image case
                are (N x C x H x W), where N is the batch size, C is the number of
                channels, and H and W are the height and the width of the data. For non
                image case, the dimensions are in the form of (N x C x D1 x D2 ... Dn),
                where N is the batch size.

            scale: The scale as a 1-dimensional tensor of size C to be applied to the
                output.

            B: The bias as a 1-dimensional tensor of size C to be applied to the output.

            mean: The running mean (training) or the estimated mean (testing) as a
                1-dimensional tensor of size C.

            var: The running variance (training) or the estimated variance (testing) as
                a 1-dimensional tensor of size C.

            epsilon: The epsilon value to use to avoid division by zero, default is
                1e-5f.

            is_test: If set to nonzero, run spatial batch normalization in test mode,
                default is 0.

            momentum: Factor used in computing the running mean and variance.e.g.,
                running_mean = running_mean * momentum + mean * (1 - momentum), default
                is 0.9f.

            spatial: If true, compute the mean and variance across all spatial elements
                If false, compute the mean and variance across per feature.Default is 1.
        """

        schema = get_schema("BatchNormalization", 6, "")
        op: Callable[
            ...,
            Tuple[
                Union[DOUBLE, FLOAT, FLOAT16],
                Union[DOUBLE, FLOAT, FLOAT16],
                Union[DOUBLE, FLOAT, FLOAT16],
                Union[DOUBLE, FLOAT, FLOAT16],
                Union[DOUBLE, FLOAT, FLOAT16],
            ],
        ] = Op(self, "BatchNormalization", schema)
        return op(
            *self._prepare_inputs(schema, X, scale, B, mean, var),
            epsilon=epsilon,
            is_test=is_test,
            momentum=momentum,
            spatial=spatial,
        )

    def Cast(
        self,
        input: Union[
            BOOL,
            DOUBLE,
            FLOAT,
            FLOAT16,
            INT16,
            INT32,
            INT64,
            INT8,
            UINT16,
            UINT32,
            UINT64,
            UINT8,
        ],
        to: Optional[int] = None,
    ) -> Union[
        BOOL, DOUBLE, FLOAT, FLOAT16, INT16, INT32, INT64, INT8, UINT16, UINT32, UINT64, UINT8
    ]:
        r"""[🌐 Cast(6)](https://onnx.ai/onnx/operators/onnx__Cast.html#cast-6 "Online Documentation")


        The operator casts the elements of a given input tensor to a data type
        specified by the 'to' argument and returns an output tensor of the same size in
        the converted type. The 'to' argument must be one of the data types specified
        in the 'DataType' enum field in the TensorProto message.
        NOTE: Casting to and from strings is not supported yet.


        Args:
            input: Input tensor to be cast.

            to: The data type to which the elements of the input tensor are cast.
                Strictly must be one of the types from DataType enum in TensorProto
        """

        schema = get_schema("Cast", 6, "")
        op: Callable[
            ...,
            Union[
                BOOL,
                DOUBLE,
                FLOAT,
                FLOAT16,
                INT16,
                INT32,
                INT64,
                INT8,
                UINT16,
                UINT32,
                UINT64,
                UINT8,
            ],
        ] = Op(self, "Cast", schema)
        return op(*self._prepare_inputs(schema, input), to=to)

    def Ceil(self, X: Union[DOUBLE, FLOAT, FLOAT16]) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Ceil(6)](https://onnx.ai/onnx/operators/onnx__Ceil.html#ceil-6 "Online Documentation")


        Ceil takes one input data (Tensor<T>) and produces one output data
        (Tensor<T>) where the ceil is, y = ceil(x), is applied to
        the tensor elementwise.


        Args:
            X: Input tensor
        """

        schema = get_schema("Ceil", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Ceil", schema)
        return op(*self._prepare_inputs(schema, X))

    def Clip(
        self,
        input: Union[DOUBLE, FLOAT, FLOAT16],
        max: float = 3.4028234663852886e38,
        min: float = -3.4028234663852886e38,
    ) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Clip(6)](https://onnx.ai/onnx/operators/onnx__Clip.html#clip-6 "Online Documentation")


        Clip operator limits the given input within an interval. The interval is
        specified with arguments 'min' and 'max'. They default to
        numeric_limits::lowest() and numeric_limits::max() respectively.


        Args:
            input: Input tensor whose elements to be clipped

            max: Maximum value, above which element is replaced by max

            min: Minimum value, under which element is replaced by min
        """

        schema = get_schema("Clip", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Clip", schema)
        return op(*self._prepare_inputs(schema, input), max=max, min=min)

    def Div(
        self,
        A: Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64],
        B: Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64],
        axis: Optional[int] = None,
        broadcast: int = 0,
    ) -> Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64]:
        r"""[🌐 Div(6)](https://onnx.ai/onnx/operators/onnx__Div.html#div-6 "Online Documentation")


        Performs element-wise binary division (with limited broadcast support).

        If necessary the right-hand-side argument will be broadcasted to match the
        shape of left-hand-side argument. When broadcasting is specified, the second
        tensor can either be of element size 1 (including a scalar tensor and any
        tensor with rank equal to or smaller than the first tensor), or having its
        shape as a contiguous subset of the first tensor's shape. The starting of the
        mutually equal shape is specified by the argument "axis", and if it is not set,
        suffix matching is assumed. 1-dim expansion doesn't work yet.

        For example, the following tensor shapes are supported (with broadcast=1):

          shape(A) = (2, 3, 4, 5), shape(B) = (,), i.e. B is a scalar tensor
          shape(A) = (2, 3, 4, 5), shape(B) = (1, 1), i.e. B is an 1-element tensor
          shape(A) = (2, 3, 4, 5), shape(B) = (5,)
          shape(A) = (2, 3, 4, 5), shape(B) = (4, 5)
          shape(A) = (2, 3, 4, 5), shape(B) = (3, 4), with axis=1
          shape(A) = (2, 3, 4, 5), shape(B) = (2), with axis=0

        Attribute `broadcast=1` needs to be passed to enable broadcasting.


        Args:
            A: First operand, should share the type with the second operand.

            B: Second operand. With broadcasting can be of smaller size than A. If
                broadcasting is disabled it should be of the same size.

            axis: If set, defines the broadcast dimensions. See doc for details.

            broadcast: Pass 1 to enable broadcasting
        """

        schema = get_schema("Div", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64]] = Op(
            self, "Div", schema
        )
        return op(*self._prepare_inputs(schema, A, B), axis=axis, broadcast=broadcast)

    def Dropout(
        self, data: Union[DOUBLE, FLOAT, FLOAT16], is_test: int = 0, ratio: float = 0.5
    ) -> Tuple[Union[DOUBLE, FLOAT, FLOAT16], Union[DOUBLE, FLOAT, FLOAT16]]:
        r"""[🌐 Dropout(6)](https://onnx.ai/onnx/operators/onnx__Dropout.html#dropout-6 "Online Documentation")


        Dropout takes one input data (Tensor<float>) and produces two Tensor outputs,
        output (Tensor<float>) and mask (Tensor<bool>). Depending on whether it is in
        test mode or not, the output Y will either be a random dropout, or a simple
        copy of the input. Note that our implementation of Dropout does scaling in
        the training phase, so during testing nothing needs to be done.


        Args:
            data: The input data as Tensor.

            is_test: (int, default 0) if nonzero, run dropout in test mode where the
                output is simply Y = X.

            ratio: (float, default 0.5) the ratio of random dropout
        """

        schema = get_schema("Dropout", 6, "")
        op: Callable[
            ..., Tuple[Union[DOUBLE, FLOAT, FLOAT16], Union[DOUBLE, FLOAT, FLOAT16]]
        ] = Op(self, "Dropout", schema)
        return op(*self._prepare_inputs(schema, data), is_test=is_test, ratio=ratio)

    def Elu(
        self, X: Union[DOUBLE, FLOAT, FLOAT16], alpha: float = 1.0
    ) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Elu(6)](https://onnx.ai/onnx/operators/onnx__Elu.html#elu-6 "Online Documentation")


        Elu takes one input data (Tensor<T>) and produces one output data
        (Tensor<T>) where the function `f(x) = alpha * (exp(x) - 1.) for x <
        0`, `f(x) = x for x >= 0`., is applied to the tensor elementwise.



        Args:
            X: (differentiable) 1D input tensor

            alpha: Coefficient of ELU.
        """

        schema = get_schema("Elu", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Elu", schema)
        return op(*self._prepare_inputs(schema, X), alpha=alpha)

    def Exp(self, input: Union[DOUBLE, FLOAT, FLOAT16]) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Exp(6)](https://onnx.ai/onnx/operators/onnx__Exp.html#exp-6 "Online Documentation")


        Calculates the exponential of the given input tensor, element-wise.


        Args:
            input: Input tensor
        """

        schema = get_schema("Exp", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Exp", schema)
        return op(*self._prepare_inputs(schema, input))

    def Floor(self, X: Union[DOUBLE, FLOAT, FLOAT16]) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Floor(6)](https://onnx.ai/onnx/operators/onnx__Floor.html#floor-6 "Online Documentation")


        Floor takes one input data (Tensor<T>) and produces one output data
        (Tensor<T>) where the floor is, y = floor(x), is applied to
        the tensor elementwise.


        Args:
            X: Input tensor
        """

        schema = get_schema("Floor", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Floor", schema)
        return op(*self._prepare_inputs(schema, X))

    def Gemm(
        self,
        A: Union[DOUBLE, FLOAT, FLOAT16],
        B: Union[DOUBLE, FLOAT, FLOAT16],
        C: Union[DOUBLE, FLOAT, FLOAT16],
        alpha: float = 1.0,
        beta: float = 1.0,
        broadcast: int = 0,
        transA: int = 0,
        transB: int = 0,
    ) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Gemm(6)](https://onnx.ai/onnx/operators/onnx__Gemm.html#gemm-6 "Online Documentation")

        General Matrix multiplication:
        https://en.wikipedia.org/wiki/Basic_Linear_Algebra_Subprograms#Level_3
        Compute Y = alpha * A * B + beta * C, where input tensor A has
        dimension (M X K), input tensor B has dimension (K X N), input tensor C and
        output tensor Y have dimension (M X N).
        If attribute broadcast is non-zero, input tensor C will be broadcasted to match
        the dimension requirement. A will be transposed before doing the computation
        if attribute transA is non-zero, same for B and transB.


        Args:
            A: Input tensor A

            B: Input tensor B

            C: Input tensor C

            alpha: Scalar multiplier for the product of input tensors A * B, the default
                value is 1.0.

            beta: Scalar multiplier for input tensor C, the default value is 1.0.

            broadcast: Whether C should be broadcasted

            transA: Whether A should be transposed

            transB: Whether B should be transposed
        """

        schema = get_schema("Gemm", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Gemm", schema)
        return op(
            *self._prepare_inputs(schema, A, B, C),
            alpha=alpha,
            beta=beta,
            broadcast=broadcast,
            transA=transA,
            transB=transB,
        )

    def HardSigmoid(
        self,
        X: Union[DOUBLE, FLOAT, FLOAT16],
        alpha: float = 0.20000000298023224,
        beta: float = 0.5,
    ) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 HardSigmoid(6)](https://onnx.ai/onnx/operators/onnx__HardSigmoid.html#hardsigmoid-6 "Online Documentation")


        HardSigmoid takes one input data (Tensor<T>) and produces one output data
        (Tensor<T>) where the HardSigmoid function, y = max(0, min(1, alpha * x + beta)),
        is applied to the tensor elementwise.


        Args:
            X: (differentiable) Input tensor

            alpha: Value of alpha.

            beta: Value of beta.
        """

        schema = get_schema("HardSigmoid", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "HardSigmoid", schema)
        return op(*self._prepare_inputs(schema, X), alpha=alpha, beta=beta)

    def InstanceNormalization(
        self,
        input: Union[DOUBLE, FLOAT, FLOAT16],
        scale: Union[DOUBLE, FLOAT, FLOAT16],
        B: Union[DOUBLE, FLOAT, FLOAT16],
        epsilon: float = 9.999999747378752e-06,
    ) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 InstanceNormalization(6)](https://onnx.ai/onnx/operators/onnx__InstanceNormalization.html#instancenormalization-6 "Online Documentation")


        Carries out instance normalization as described in the paper
        https://arxiv.org/abs/1607.08022.

        y = scale * (x - mean) / sqrt(variance + epsilon) + B,
        where mean and variance are computed per instance per channel.



        Args:
            input: (differentiable) Input data tensor from the previous operator;
                dimensions for image case are (N x C x H x W), where N is the batch
                size, C is the number of channels, and H and W are the height and the
                width of the data. For non image case, the dimensions are in the form of
                (N x C x D1 x D2 ... Dn), where N is the batch size.

            scale: (differentiable) The input 1-dimensional scale tensor of size C.

            B: (differentiable) The input 1-dimensional bias tensor of size C.

            epsilon: The epsilon value to use to avoid division by zero.
        """

        schema = get_schema("InstanceNormalization", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(
            self, "InstanceNormalization", schema
        )
        return op(*self._prepare_inputs(schema, input, scale, B), epsilon=epsilon)

    def LeakyRelu(
        self, X: Union[DOUBLE, FLOAT, FLOAT16], alpha: float = 0.009999999776482582
    ) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 LeakyRelu(6)](https://onnx.ai/onnx/operators/onnx__LeakyRelu.html#leakyrelu-6 "Online Documentation")


        LeakyRelu takes input data (Tensor<T>) and an argument alpha, and produces one
        output data (Tensor<T>) where the function `f(x) = alpha * x for x < 0`,
        `f(x) = x for x >= 0`, is applied to the data tensor elementwise.


        Args:
            X: (differentiable) Input tensor

            alpha: Coefficient of leakage.
        """

        schema = get_schema("LeakyRelu", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "LeakyRelu", schema)
        return op(*self._prepare_inputs(schema, X), alpha=alpha)

    def Log(self, input: Union[DOUBLE, FLOAT, FLOAT16]) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Log(6)](https://onnx.ai/onnx/operators/onnx__Log.html#log-6 "Online Documentation")


        Calculates the natural log of the given input tensor, element-wise.


        Args:
            input: Input tensor
        """

        schema = get_schema("Log", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Log", schema)
        return op(*self._prepare_inputs(schema, input))

    def Max(self, *data_0: Union[DOUBLE, FLOAT, FLOAT16]) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Max(6)](https://onnx.ai/onnx/operators/onnx__Max.html#max-6 "Online Documentation")


        Element-wise max of each of the input tensors. All inputs and outputs must
        have the same shape and data type.


        Args:
            data_0: (variadic) List of tensors for Max.
        """

        schema = get_schema("Max", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Max", schema)
        return op(*self._prepare_inputs(schema, *data_0))

    def Mean(self, *data_0: Union[DOUBLE, FLOAT, FLOAT16]) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Mean(6)](https://onnx.ai/onnx/operators/onnx__Mean.html#mean-6 "Online Documentation")


        Element-wise mean of each of the input tensors. All inputs and outputs must
        have the same shape and data type.


        Args:
            data_0: (variadic) List of tensors for Mean.
        """

        schema = get_schema("Mean", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Mean", schema)
        return op(*self._prepare_inputs(schema, *data_0))

    def Min(self, *data_0: Union[DOUBLE, FLOAT, FLOAT16]) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Min(6)](https://onnx.ai/onnx/operators/onnx__Min.html#min-6 "Online Documentation")


        Element-wise min of each of the input tensors. All inputs and outputs must
        have the same shape and data type.


        Args:
            data_0: (variadic) List of tensors for Min
        """

        schema = get_schema("Min", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Min", schema)
        return op(*self._prepare_inputs(schema, *data_0))

    def Mul(
        self,
        A: Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64],
        B: Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64],
        axis: Optional[int] = None,
        broadcast: int = 0,
    ) -> Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64]:
        r"""[🌐 Mul(6)](https://onnx.ai/onnx/operators/onnx__Mul.html#mul-6 "Online Documentation")


        Performs element-wise binary multiplication (with limited broadcast support).

        If necessary the right-hand-side argument will be broadcasted to match the
        shape of left-hand-side argument. When broadcasting is specified, the second
        tensor can either be of element size 1 (including a scalar tensor and any
        tensor with rank equal to or smaller than the first tensor), or having its
        shape as a contiguous subset of the first tensor's shape. The starting of the
        mutually equal shape is specified by the argument "axis", and if it is not set,
        suffix matching is assumed. 1-dim expansion doesn't work yet.

        For example, the following tensor shapes are supported (with broadcast=1):

          shape(A) = (2, 3, 4, 5), shape(B) = (,), i.e. B is a scalar tensor
          shape(A) = (2, 3, 4, 5), shape(B) = (1, 1), i.e. B is an 1-element tensor
          shape(A) = (2, 3, 4, 5), shape(B) = (5,)
          shape(A) = (2, 3, 4, 5), shape(B) = (4, 5)
          shape(A) = (2, 3, 4, 5), shape(B) = (3, 4), with axis=1
          shape(A) = (2, 3, 4, 5), shape(B) = (2), with axis=0

        Attribute `broadcast=1` needs to be passed to enable broadcasting.


        Args:
            A: First operand, should share the type with the second operand.

            B: Second operand. With broadcasting can be of smaller size than A. If
                broadcasting is disabled it should be of the same size.

            axis: If set, defines the broadcast dimensions. See doc for details.

            broadcast: Pass 1 to enable broadcasting
        """

        schema = get_schema("Mul", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64]] = Op(
            self, "Mul", schema
        )
        return op(*self._prepare_inputs(schema, A, B), axis=axis, broadcast=broadcast)

    def Neg(
        self, X: Union[DOUBLE, FLOAT, FLOAT16, INT16, INT32, INT64, INT8]
    ) -> Union[DOUBLE, FLOAT, FLOAT16, INT16, INT32, INT64, INT8]:
        r"""[🌐 Neg(6)](https://onnx.ai/onnx/operators/onnx__Neg.html#neg-6 "Online Documentation")


        Neg takes one input data (Tensor<T>) and produces one output data
        (Tensor<T>) where each element flipped sign, y = -x, is applied to
        the tensor elementwise.


        Args:
            X: Input tensor
        """

        schema = get_schema("Neg", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16, INT16, INT32, INT64, INT8]] = Op(
            self, "Neg", schema
        )
        return op(*self._prepare_inputs(schema, X))

    def PRelu(
        self, X: Union[DOUBLE, FLOAT, FLOAT16], slope: Union[DOUBLE, FLOAT, FLOAT16]
    ) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 PRelu(6)](https://onnx.ai/onnx/operators/onnx__PRelu.html#prelu-6 "Online Documentation")



        PRelu takes input data (Tensor<T>) and slope tensor as input, and produces one
        output data (Tensor<T>) where the function `f(x) = slope * x for x < 0`,
        `f(x) = x for x >= 0`., is applied to the data tensor elementwise.



        Args:
            X: Input tensor

            slope: Slope tensor. If `Slope` is of size 1, the value is sharedacross
                different channels
        """

        schema = get_schema("PRelu", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "PRelu", schema)
        return op(*self._prepare_inputs(schema, X, slope))

    def Reciprocal(self, X: Union[DOUBLE, FLOAT, FLOAT16]) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Reciprocal(6)](https://onnx.ai/onnx/operators/onnx__Reciprocal.html#reciprocal-6 "Online Documentation")


        Reciprocal takes one input data (Tensor<T>) and produces one output data
        (Tensor<T>) where the reciprocal is, y = 1/x, is applied to
        the tensor elementwise.


        Args:
            X: Input tensor
        """

        schema = get_schema("Reciprocal", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Reciprocal", schema)
        return op(*self._prepare_inputs(schema, X))

    def Relu(self, X: Union[DOUBLE, FLOAT, FLOAT16]) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Relu(6)](https://onnx.ai/onnx/operators/onnx__Relu.html#relu-6 "Online Documentation")


        Relu takes one input data (Tensor<T>) and produces one output data
        (Tensor<T>) where the rectified linear function, y = max(0, x), is applied to
        the tensor elementwise.


        Args:
            X: Input tensor
        """

        schema = get_schema("Relu", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Relu", schema)
        return op(*self._prepare_inputs(schema, X))

    def Selu(
        self,
        X: Union[DOUBLE, FLOAT, FLOAT16],
        alpha: float = 1.6732631921768188,
        gamma: float = 1.0507010221481323,
    ) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Selu(6)](https://onnx.ai/onnx/operators/onnx__Selu.html#selu-6 "Online Documentation")


        Selu takes one input data (Tensor<T>) and produces one output data
        (Tensor<T>) where the scaled exponential linear unit function,
        `y = gamma * (alpha * e^x - alpha) for x <= 0`, `y = gamma * x for x > 0`,
        is applied to the tensor elementwise.


        Args:
            X: (differentiable) Input tensor

            alpha: Coefficient of SELU default to 1.67326319217681884765625 (i.e.,
                float32 approximation of 1.6732632423543772848170429916717).

            gamma: Coefficient of SELU default to 1.05070102214813232421875 (i.e.,
                float32 approximation of 1.0507009873554804934193349852946).
        """

        schema = get_schema("Selu", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Selu", schema)
        return op(*self._prepare_inputs(schema, X), alpha=alpha, gamma=gamma)

    def Sigmoid(self, X: Union[DOUBLE, FLOAT, FLOAT16]) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Sigmoid(6)](https://onnx.ai/onnx/operators/onnx__Sigmoid.html#sigmoid-6 "Online Documentation")


        Sigmoid takes one input data (Tensor<T>) and produces one output data
        (Tensor<T>) where the sigmoid function, y = 1 / (1 + exp(-x)), is applied to the
        tensor elementwise.


        Args:
            X: Input tensor
        """

        schema = get_schema("Sigmoid", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Sigmoid", schema)
        return op(*self._prepare_inputs(schema, X))

    def Sqrt(self, X: Union[DOUBLE, FLOAT, FLOAT16]) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Sqrt(6)](https://onnx.ai/onnx/operators/onnx__Sqrt.html#sqrt-6 "Online Documentation")


        Square root takes one input data (Tensor<T>) and produces one output data
        (Tensor<T>) where the square root is, y = x^0.5, is applied to
        the tensor elementwise. If x is negative, then it will return NaN.


        Args:
            X: Input tensor
        """

        schema = get_schema("Sqrt", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Sqrt", schema)
        return op(*self._prepare_inputs(schema, X))

    def Sub(
        self,
        A: Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64],
        B: Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64],
        axis: Optional[int] = None,
        broadcast: int = 0,
    ) -> Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64]:
        r"""[🌐 Sub(6)](https://onnx.ai/onnx/operators/onnx__Sub.html#sub-6 "Online Documentation")


        Performs element-wise binary subtraction (with limited broadcast support).

        If necessary the right-hand-side argument will be broadcasted to match the
        shape of left-hand-side argument. When broadcasting is specified, the second
        tensor can either be of element size 1 (including a scalar tensor and any
        tensor with rank equal to or smaller than the first tensor), or having its
        shape as a contiguous subset of the first tensor's shape. The starting of the
        mutually equal shape is specified by the argument "axis", and if it is not set,
        suffix matching is assumed. 1-dim expansion doesn't work yet.

        For example, the following tensor shapes are supported (with broadcast=1):

          shape(A) = (2, 3, 4, 5), shape(B) = (,), i.e. B is a scalar tensor
          shape(A) = (2, 3, 4, 5), shape(B) = (1, 1), i.e. B is an 1-element tensor
          shape(A) = (2, 3, 4, 5), shape(B) = (5,)
          shape(A) = (2, 3, 4, 5), shape(B) = (4, 5)
          shape(A) = (2, 3, 4, 5), shape(B) = (3, 4), with axis=1
          shape(A) = (2, 3, 4, 5), shape(B) = (2), with axis=0

        Attribute `broadcast=1` needs to be passed to enable broadcasting.


        Args:
            A: First operand, should share the type with the second operand.

            B: Second operand. With broadcasting can be of smaller size than A. If
                broadcasting is disabled it should be of the same size.

            axis: If set, defines the broadcast dimensions. See doc for details.

            broadcast: Pass 1 to enable broadcasting
        """

        schema = get_schema("Sub", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16, INT32, INT64, UINT32, UINT64]] = Op(
            self, "Sub", schema
        )
        return op(*self._prepare_inputs(schema, A, B), axis=axis, broadcast=broadcast)

    def Sum(self, *data_0: Union[DOUBLE, FLOAT, FLOAT16]) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Sum(6)](https://onnx.ai/onnx/operators/onnx__Sum.html#sum-6 "Online Documentation")


        Element-wise sum of each of the input tensors. All inputs and outputs must
        have the same shape and data type.


        Args:
            data_0: (variadic) List of tensors for Sum.
        """

        schema = get_schema("Sum", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Sum", schema)
        return op(*self._prepare_inputs(schema, *data_0))

    def Tanh(self, input: Union[DOUBLE, FLOAT, FLOAT16]) -> Union[DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 Tanh(6)](https://onnx.ai/onnx/operators/onnx__Tanh.html#tanh-6 "Online Documentation")


        Calculates the hyperbolic tangent of the given input tensor element-wise.


        Args:
            input: Input tensor
        """

        schema = get_schema("Tanh", 6, "")
        op: Callable[..., Union[DOUBLE, FLOAT, FLOAT16]] = Op(self, "Tanh", schema)
        return op(*self._prepare_inputs(schema, input))

    def Tile(
        self,
        input: Union[
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
        repeats: INT64,
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
        r"""[🌐 Tile(6)](https://onnx.ai/onnx/operators/onnx__Tile.html#tile-6 "Online Documentation")

        Constructs a tensor by tiling a given tensor.
        This is the same as function `tile` in Numpy, but no broadcast.
        For example A = [[1, 2], [3, 4]], B = [1, 2], tile(A, B) = [[1, 2, 1, 2], [3, 4, 3, 4]]


        Args:
            input: Input tensor of any shape.

            repeats: 1D int64 tensor of the same length as input's dimension number,
                includes numbers of repeated copies along input's dimensions.
        """

        schema = get_schema("Tile", 6, "")
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
        ] = Op(self, "Tile", schema)
        return op(*self._prepare_inputs(schema, input, repeats))
