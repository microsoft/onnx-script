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

from typing import Callable, Optional, Sequence, Tuple, Union

from onnx import GraphProto
from onnx.defs import get_schema

from onnxscript.onnx_opset._impl.opset16 import Opset16
from onnxscript.onnx_types import (
    BFLOAT16,
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


class Opset17(Opset16):
    def __new__(cls):
        return Opset.__new__(cls, "", 17)

    def __init__(self):
        super().__init__()

    def BlackmanWindow(
        self, size: Union[INT32, INT64], output_datatype: int = 1, periodic: int = 1
    ) -> Union[
        BFLOAT16,
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
    ]:
        r"""[🌐 BlackmanWindow(17)](https://onnx.ai/onnx/operators/onnx__BlackmanWindow.html#blackmanwindow-17 "Online Documentation")


        Generates a Blackman window as described in the paper https://ieeexplore.ieee.org/document/1455106.


        Args:
            size: (non-differentiable) A scalar value indicating the length of the
                window.

            output_datatype: The data type of the output tensor. Strictly must be one of
                the values from DataType enum in TensorProto whose values correspond to
                T2. The default value is 1 = FLOAT.

            periodic: If 1, returns a window to be used as periodic function. If 0,
                return a symmetric window. When 'periodic' is specified, hann computes a
                window of length size + 1 and returns the first size points. The default
                value is 1.
        """

        schema = get_schema("BlackmanWindow", 17, "")
        op: Callable[
            ...,
            Union[
                BFLOAT16,
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
        ] = Op(self, "BlackmanWindow", schema)
        return op(
            *self._prepare_inputs(schema, size),
            output_datatype=output_datatype,
            periodic=periodic,
        )

    def DFT(
        self,
        input: Union[BFLOAT16, DOUBLE, FLOAT, FLOAT16],
        dft_length: Optional[Union[INT32, INT64]] = None,
        axis: int = 1,
        inverse: int = 0,
        onesided: int = 0,
    ) -> Union[BFLOAT16, DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 DFT(17)](https://onnx.ai/onnx/operators/onnx__DFT.html#dft-17 "Online Documentation")

        Computes the discrete Fourier transform of input.

        Args:
            input: (non-differentiable) For real input, the following shape is expected:
                [batch_idx][signal_dim1][signal_dim2]...[signal_dimN][1]. For complex
                input, the following shape is expected:
                [batch_idx][signal_dim1][signal_dim2]...[signal_dimN][2]. The first
                dimension is the batch dimension. The following N dimentions correspond
                to the signal's dimensions. The final dimension represents the real and
                imaginary parts of the value in that order.

            dft_length: (optional, non-differentiable) The length of the signal.If
                greater than the axis dimension, the signal will be zero-padded up to
                dft_length. If less than the axis dimension, only the first dft_length
                values will be used as the signal. It's an optional value.

            axis: The axis on which to perform the DFT. By default this value is set to
                1, which corresponds to the first dimension after the batch index.

            inverse: Whether to perform the inverse discrete fourier transform. By
                default this value is set to 0, which corresponds to false.

            onesided: If onesided is 1, only values for w in [0, 1, 2, ...,
                floor(n_fft/2) + 1] are returned because the real-to-complex Fourier
                transform satisfies the conjugate symmetry, i.e., X[m, w] =
                X[m,w]=X[m,n_fft-w]*. Note if the input or window tensors are complex,
                then onesided output is not possible. Enabling onesided with real inputs
                performs a Real-valued fast Fourier transform (RFFT). When invoked with
                real or complex valued input, the default value is 0. Values can be 0 or
                1.
        """

        schema = get_schema("DFT", 17, "")
        op: Callable[..., Union[BFLOAT16, DOUBLE, FLOAT, FLOAT16]] = Op(self, "DFT", schema)
        return op(
            *self._prepare_inputs(schema, input, dft_length),
            axis=axis,
            inverse=inverse,
            onesided=onesided,
        )

    def HammingWindow(
        self, size: Union[INT32, INT64], output_datatype: int = 1, periodic: int = 1
    ) -> Union[
        BFLOAT16,
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
    ]:
        r"""[🌐 HammingWindow(17)](https://onnx.ai/onnx/operators/onnx__HammingWindow.html#hammingwindow-17 "Online Documentation")


        Generates a Hamming window as described in the paper https://ieeexplore.ieee.org/document/1455106.


        Args:
            size: (non-differentiable) A scalar value indicating the length of the
                window.

            output_datatype: The data type of the output tensor. Strictly must be one of
                the values from DataType enum in TensorProto whose values correspond to
                T2. The default value is 1 = FLOAT.

            periodic: If 1, returns a window to be used as periodic function. If 0,
                return a symmetric window. When 'periodic' is specified, hann computes a
                window of length size + 1 and returns the first size points. The default
                value is 1.
        """

        schema = get_schema("HammingWindow", 17, "")
        op: Callable[
            ...,
            Union[
                BFLOAT16,
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
        ] = Op(self, "HammingWindow", schema)
        return op(
            *self._prepare_inputs(schema, size),
            output_datatype=output_datatype,
            periodic=periodic,
        )

    def HannWindow(
        self, size: Union[INT32, INT64], output_datatype: int = 1, periodic: int = 1
    ) -> Union[
        BFLOAT16,
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
    ]:
        r"""[🌐 HannWindow(17)](https://onnx.ai/onnx/operators/onnx__HannWindow.html#hannwindow-17 "Online Documentation")


        Generates a Hann window as described in the paper https://ieeexplore.ieee.org/document/1455106.


        Args:
            size: (non-differentiable) A scalar value indicating the length of the
                window.

            output_datatype: The data type of the output tensor. Strictly must be one of
                the values from DataType enum in TensorProto whose values correspond to
                T2. The default value is 1 = FLOAT.

            periodic: If 1, returns a window to be used as periodic function. If 0,
                return a symmetric window. When 'periodic' is specified, hann computes a
                window of length size + 1 and returns the first size points. The default
                value is 1.
        """

        schema = get_schema("HannWindow", 17, "")
        op: Callable[
            ...,
            Union[
                BFLOAT16,
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
        ] = Op(self, "HannWindow", schema)
        return op(
            *self._prepare_inputs(schema, size),
            output_datatype=output_datatype,
            periodic=periodic,
        )

    def LayerNormalization(
        self,
        X: Union[BFLOAT16, DOUBLE, FLOAT, FLOAT16],
        Scale: Union[BFLOAT16, DOUBLE, FLOAT, FLOAT16],
        B: Optional[Union[BFLOAT16, DOUBLE, FLOAT, FLOAT16]] = None,
        axis: int = -1,
        epsilon: float = 9.999999747378752e-06,
        stash_type: int = 1,
    ) -> Tuple[
        Union[BFLOAT16, DOUBLE, FLOAT, FLOAT16], Union[BFLOAT16, FLOAT], Union[BFLOAT16, FLOAT]
    ]:
        r"""[🌐 LayerNormalization(17)](https://onnx.ai/onnx/operators/onnx__LayerNormalization.html#layernormalization-17 "Online Documentation")


              This is layer normalization defined in ONNX as function.
              The overall computation can be split into two stages.
              The first stage is standardization, which makes the
              normalized elements have zero mean and unit variances.
              The computation required by standardization can be
              described by the following equations.
              ```
              Mean = ReduceMean<axes=normalized_axes>(X)
              D = Sub(X, Mean)
              DD = Mul(Diff, Diff)
              Var = ReduceMean<axes=normalized_axes>(DD)
              VarEps = Add(Var, epsilon)
              StdDev = Sqrt(VarEps)
              InvStdDev = Reciprocal(StdDev)
              Normalized = Mul(D, InvStdDev)
              ```
              where `normalized_axes` is `[axis, ..., rank of X - 1]`.
              The variables `Var` and `StdDev` stand for variance and
              standard deviation, respectively. The second output is
              `Mean` and the last one is `InvStdDev`.
              Depending on `stash_type` attribute, the actual computation
              must happen in different floating-point precision.
              For example, if `stash_type` is 1, this operator casts
              all input variables to 32-bit float, perform the computation, and
              finally cast `Normalized` back to the original type of `X`.
              The second stage then scales and shifts the outcome of the
              first stage using
              ```
              NormalizedScaled = Mul(Normalized, Scale)
              Y = Add(NormalizedScaled, B)
              ```
              The second stage doesn't depends on `stash_type`.
              All equations are in [this syntax](https://github.com/onnx/onnx/blob/main/docs/Syntax.md).
              The same variable (i.e., input, output, and attribute) uses
              the same name in the equations above and this operator's definition.
              Let `d[i]` indicate the i-th dimension of `X`.
              If `X`'s shape is `[d[0], ..., d[axis-1], d[axis], ..., d[rank-1]]`,
              the shape of `Mean` and `InvStdDev` is `[d[0], ..., d[axis-1], 1, ..., 1]`.
              `Y` and `X` have the same shape.


        Args:
            X: Tensor to be normalized.

            Scale: Scale tensor.

            B: (optional) Bias tensor.

            axis: The first normalization dimension. If rank(X) is r, axis' allowed
                range is [-r, r]. Negative value means counting dimensions from the
                back.

            epsilon: The epsilon value to use to avoid division by zero.

            stash_type: Type of Mean and InvStdDev. This also specifies stage one's
                computation precision.
        """

        schema = get_schema("LayerNormalization", 17, "")
        op: Callable[
            ...,
            Tuple[
                Union[BFLOAT16, DOUBLE, FLOAT, FLOAT16],
                Union[BFLOAT16, FLOAT],
                Union[BFLOAT16, FLOAT],
            ],
        ] = Op(self, "LayerNormalization", schema)
        return op(
            *self._prepare_inputs(schema, X, Scale, B),
            axis=axis,
            epsilon=epsilon,
            stash_type=stash_type,
        )

    def MelWeightMatrix(
        self,
        num_mel_bins: Union[INT32, INT64],
        dft_length: Union[INT32, INT64],
        sample_rate: Union[INT32, INT64],
        lower_edge_hertz: Union[BFLOAT16, DOUBLE, FLOAT, FLOAT16],
        upper_edge_hertz: Union[BFLOAT16, DOUBLE, FLOAT, FLOAT16],
        output_datatype: int = 1,
    ) -> Union[
        BFLOAT16,
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
    ]:
        r"""[🌐 MelWeightMatrix(17)](https://onnx.ai/onnx/operators/onnx__MelWeightMatrix.html#melweightmatrix-17 "Online Documentation")


        Generate a MelWeightMatrix that can be used to re-weight a Tensor containing a linearly sampled frequency spectra (from DFT or STFT) into num_mel_bins frequency information based on the [lower_edge_hertz, upper_edge_hertz] range on the mel scale.
        This function defines the mel scale in terms of a frequency in hertz according to the following formula:

            mel(f) = 2595 * log10(1 + f/700)

        In the returned matrix, all the triangles (filterbanks) have a peak value of 1.0.

        The returned MelWeightMatrix can be used to right-multiply a spectrogram S of shape [frames, num_spectrogram_bins] of linear scale spectrum values (e.g. STFT magnitudes) to generate a "mel spectrogram" M of shape [frames, num_mel_bins].


        Args:
            num_mel_bins: (non-differentiable) The number of bands in the mel spectrum.

            dft_length: (non-differentiable) The size of the original DFT. The size of
                the original DFT is used to infer the size of the onesided DFT, which is
                understood to be floor(dft_length/2) + 1, i.e. the spectrogram only
                contains the nonredundant DFT bins.

            sample_rate: (non-differentiable) Samples per second of the input signal
                used to create the spectrogram. Used to figure out the frequencies
                corresponding to each spectrogram bin, which dictates how they are
                mapped into the mel scale.

            lower_edge_hertz: (non-differentiable) Lower bound on the frequencies to be
                included in the mel spectrum. This corresponds to the lower edge of the
                lowest triangular band.

            upper_edge_hertz: (non-differentiable) The desired top edge of the highest
                frequency band.

            output_datatype: The data type of the output tensor. Strictly must be one of
                the values from DataType enum in TensorProto whose values correspond to
                T3. The default value is 1 = FLOAT.
        """

        schema = get_schema("MelWeightMatrix", 17, "")
        op: Callable[
            ...,
            Union[
                BFLOAT16,
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
        ] = Op(self, "MelWeightMatrix", schema)
        return op(
            *self._prepare_inputs(
                schema,
                num_mel_bins,
                dft_length,
                sample_rate,
                lower_edge_hertz,
                upper_edge_hertz,
            ),
            output_datatype=output_datatype,
        )

    def STFT(
        self,
        signal: Union[BFLOAT16, DOUBLE, FLOAT, FLOAT16],
        frame_step: Union[INT32, INT64],
        window: Optional[Union[BFLOAT16, DOUBLE, FLOAT, FLOAT16]] = None,
        frame_length: Optional[Union[INT32, INT64]] = None,
        onesided: int = 1,
    ) -> Union[BFLOAT16, DOUBLE, FLOAT, FLOAT16]:
        r"""[🌐 STFT(17)](https://onnx.ai/onnx/operators/onnx__STFT.html#stft-17 "Online Documentation")

        Computes the Short-time Fourier Transform of the signal.

        Args:
            signal: (non-differentiable) Input tensor representing a real or complex
                valued signal. For real input, the following shape is expected:
                [batch_size][signal_length][1]. For complex input, the following shape
                is expected: [batch_size][signal_length][2], where
                [batch_size][signal_length][0] represents the real component and
                [batch_size][signal_length][1] represents the imaginary component of the
                signal.

            frame_step: (non-differentiable) The number of samples to step between
                successive DFTs.

            window: (optional, non-differentiable) A tensor representing the window that
                will be slid over the signal.The window must have rank 1 with shape:
                [window_shape]. It's an optional value.

            frame_length: (optional, non-differentiable) A scalar representing the size
                of the DFT. It's an optional value.

            onesided: If onesided is 1, only values for w in [0, 1, 2, ...,
                floor(n_fft/2) + 1] are returned because the real-to-complex Fourier
                transform satisfies the conjugate symmetry, i.e., X[m, w] =
                X[m,w]=X[m,n_fft-w]*. Note if the input or window tensors are complex,
                then onesided output is not possible. Enabling onesided with real inputs
                performs a Real-valued fast Fourier transform (RFFT).When invoked with
                real or complex valued input, the default value is 1. Values can be 0 or
                1.
        """

        schema = get_schema("STFT", 17, "")
        op: Callable[..., Union[BFLOAT16, DOUBLE, FLOAT, FLOAT16]] = Op(self, "STFT", schema)
        return op(
            *self._prepare_inputs(schema, signal, frame_step, window, frame_length),
            onesided=onesided,
        )

    def SequenceMap(
        self,
        input_sequence: Union[
            Sequence[BOOL],
            Sequence[COMPLEX128],
            Sequence[COMPLEX64],
            Sequence[DOUBLE],
            Sequence[FLOAT],
            Sequence[FLOAT16],
            Sequence[INT16],
            Sequence[INT32],
            Sequence[INT64],
            Sequence[INT8],
            Sequence[STRING],
            Sequence[UINT16],
            Sequence[UINT32],
            Sequence[UINT64],
            Sequence[UINT8],
        ],
        *additional_inputs: Union[
            Sequence[BOOL],
            Sequence[COMPLEX128],
            Sequence[COMPLEX64],
            Sequence[DOUBLE],
            Sequence[FLOAT],
            Sequence[FLOAT16],
            Sequence[INT16],
            Sequence[INT32],
            Sequence[INT64],
            Sequence[INT8],
            Sequence[STRING],
            Sequence[UINT16],
            Sequence[UINT32],
            Sequence[UINT64],
            Sequence[UINT8],
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
        body: Optional[GraphProto] = None,
    ) -> Union[
        Sequence[BOOL],
        Sequence[COMPLEX128],
        Sequence[COMPLEX64],
        Sequence[DOUBLE],
        Sequence[FLOAT],
        Sequence[FLOAT16],
        Sequence[INT16],
        Sequence[INT32],
        Sequence[INT64],
        Sequence[INT8],
        Sequence[STRING],
        Sequence[UINT16],
        Sequence[UINT32],
        Sequence[UINT64],
        Sequence[UINT8],
    ]:
        r"""[🌐 SequenceMap(17)](https://onnx.ai/onnx/operators/onnx__SequenceMap.html#sequencemap-17 "Online Documentation")


        Applies a sub-graph to each sample in the input sequence(s).

        Inputs can be either tensors or sequences, with the exception of the first input which must
        be a sequence. The length of the first input sequence will determine the number of samples in the
        outputs. Any other sequence inputs should have the same number of samples. The number of inputs
        and outputs, should match the one of the subgraph.

        For each i-th element in the output, a sample will be extracted from the input sequence(s) at
        the i-th position and the sub-graph will be applied to it.
        The outputs will contain the outputs of the sub-graph for each sample, in the same order as in
        the input.

        This operator assumes that processing each sample is independent and could executed in parallel
        or in any order. Users cannot expect any specific ordering in which each subgraph is computed.

        Args:
            input_sequence: Input sequence.

            additional_inputs: (variadic, heterogeneous) Additional inputs to the graph

            body: The graph to be run for each sample in the sequence(s). It should have
                as many inputs and outputs as inputs and outputs to the SequenceMap
                function.
        """

        schema = get_schema("SequenceMap", 17, "")
        op: Callable[
            ...,
            Union[
                Sequence[BOOL],
                Sequence[COMPLEX128],
                Sequence[COMPLEX64],
                Sequence[DOUBLE],
                Sequence[FLOAT],
                Sequence[FLOAT16],
                Sequence[INT16],
                Sequence[INT32],
                Sequence[INT64],
                Sequence[INT8],
                Sequence[STRING],
                Sequence[UINT16],
                Sequence[UINT32],
                Sequence[UINT64],
                Sequence[UINT8],
            ],
        ] = Op(self, "SequenceMap", schema)
        return op(*self._prepare_inputs(schema, input_sequence, *additional_inputs), body=body)
