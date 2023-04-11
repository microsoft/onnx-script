"""
Test data for aten operators which don't exist in PyTorch file:
pytorch/torch/testing/_internal/common_methods_invocations.py.
"""

import functools
from typing import Any, List

import torch
from torch import testing as torch_testing
from torch.testing._internal import (
    common_dtype,
    common_methods_invocations,
    common_utils,
)
from torch.testing._internal.opinfo import core as opinfo_core


def sample_inputs_conv3d(op_info, device, dtype, requires_grad, **kwargs):
    del op_info
    make_arg = functools.partial(
        torch_testing.make_tensor, device=device, dtype=dtype, requires_grad=requires_grad
    )

    # Ordered as shapes for input, weight, bias,
    # and a dict of values of (stride, padding, dilation, groups)
    cases: tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...], dict[str, Any]] = (  # type: ignore[assignment]
        (
            (1, 3, 3, 224, 224),
            (32, 3, 3, 3, 3),
            None,
            {
                "stride": (2, 2, 2),
                "padding": (1, 1, 1),
                "dilation": (1, 1, 1),
                "groups": 1,
            },
        ),
        (
            (2, 4, 3, 56, 56),
            (32, 4, 3, 3, 3),
            (32,),
            {
                "stride": (3, 3, 3),
                "padding": 2,
                "dilation": (1, 1, 1),
                "groups": 1,
            },
        ),
    )

    for input_shape, weight, bias, kwargs in cases:  # type: ignore[assignment]
        # Batched
        yield opinfo_core.SampleInput(
            make_arg(input_shape),
            args=(make_arg(weight), make_arg(bias) if bias is not None else bias),
            kwargs=kwargs,
        )
        # Unbatched
        yield opinfo_core.SampleInput(
            make_arg(input_shape[1:]),  # type: ignore[index]
            args=(make_arg(weight), make_arg(bias) if bias is not None else bias),
            kwargs=kwargs,
        )


def sample_inputs_convolution(op_info, device, dtype, requires_grad, **kwargs):
    del op_info
    make_arg = functools.partial(
        torch_testing.make_tensor, device=device, dtype=dtype, requires_grad=requires_grad
    )

    # Ordered as shapes for input, weight, bias,
    # and a dict of values of (stride, padding, dilation, groups)
    cases: tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...], dict[str, Any]] = (  # type: ignore[assignment]
        (
            (1, 3, 4),
            (3, 3, 3),
            (3,),
            {
                "stride": (2,),
                "padding": (2,),
                "dilation": (1,),
                "transposed": False,
                "output_padding": (0,),
                "groups": 1,
            },
        ),
        (
            (1, 3, 4),
            (3, 3, 3),
            None,
            {
                "stride": (2,),
                "padding": (2,),
                "dilation": (1,),
                "transposed": True,
                "output_padding": (0,),
                "groups": 1,
            },
        ),
        (
            (1, 3, 224, 224),
            (32, 3, 3, 3),
            None,
            {
                "stride": (2, 2),
                "padding": (1, 1),
                "dilation": (1, 1),
                "transposed": False,
                "output_padding": (0, 0),
                "groups": 1,
            },
        ),
        (
            (1, 3, 3, 224, 224),
            (32, 3, 3, 3, 3),
            (32,),
            {
                "stride": (2, 2, 2),
                "padding": (1, 1, 1),
                "dilation": (1, 1, 1),
                "transposed": False,
                "output_padding": (0, 0, 0),
                "groups": 1,
            },
        ),
        # FIXME(jiz): Uncomment out these test data once
        # torch 2.0 is released.
        # (
        #     (1, 3, 224, 224, 224),
        #     (32, 3, 3, 3, 3),
        #     (32,),
        #     {
        #         "stride": (2, 2, 2),
        #         "padding": (1, 1, 1),
        #         "dilation": (1, 1, 1),
        #         "transposed": False,
        #         "output_padding": (0, 0, 0),
        #         "groups": 1,
        #     },
        # ),
        (
            (2, 4, 6, 6),
            (4, 1, 3, 3),
            (4,),
            {
                "stride": (3, 2),
                "padding": (1, 1),
                "dilation": (1, 1),
                "transposed": True,
                "output_padding": (0, 0),
                "groups": 4,
            },
        ),
    )

    for input_shape, weight, bias, kwargs in cases:  # type: ignore[assignment]
        yield opinfo_core.SampleInput(
            make_arg(input_shape),
            args=(make_arg(weight), make_arg(bias) if bias is not None else bias),
            kwargs=kwargs,
        )


def sample_inputs_layer_norm(op_info, device, dtype, requires_grad, **kwargs):
    del op_info  # unused
    del kwargs
    make_arg = functools.partial(
        torch_testing.make_tensor, device=device, dtype=dtype, requires_grad=requires_grad
    )

    # Ordered as input shape, normalized_shape, eps
    cases: tuple[tuple[int], tuple[int], float] = (  # type: ignore[assignment]
        ((1, 2, 3), (1, 2, 3), 0.5),
        ((2, 2, 3), (2, 3), -0.5),
        ((1,), (1,), 1e-5),
        ((1, 2), (2,), 1e-5),
        ((0, 1), (1,), 1e-5),
    )

    for input_shape, normalized_shape, eps in cases:  # type: ignore[misc]
        # Shape of weight and bias should be the same as normalized_shape
        weight = make_arg(normalized_shape)  # type: ignore[has-type]
        bias = make_arg(normalized_shape)  # type: ignore[has-type]
        yield opinfo_core.SampleInput(
            make_arg(input_shape),  # type: ignore[has-type]
            args=(normalized_shape, weight, bias, eps),  # type: ignore[has-type]
        )
        yield opinfo_core.SampleInput(
            make_arg(input_shape),  # type: ignore[has-type]
            args=(normalized_shape, None, bias, eps),  # type: ignore[has-type]
        )
        yield opinfo_core.SampleInput(
            make_arg(input_shape),  # type: ignore[has-type]
            args=(normalized_shape, weight, None, eps),  # type: ignore[has-type]
        )
        yield opinfo_core.SampleInput(
            make_arg(input_shape),  # type: ignore[has-type]
            args=(normalized_shape, None, None, eps),  # type: ignore[has-type]
        )


def sample_inputs_max_pool2d_with_indices(op_info, device, dtype, requires_grad, **kwargs):
    del op_info
    make_arg = functools.partial(
        torch_testing.make_tensor, device=device, dtype=dtype, requires_grad=False
    )
    params_generator = (
        common_methods_invocations._TestParamsMaxPool2d()  # pylint: disable=protected-access
    )
    for (shape, memory_format), kwargs in params_generator.gen_input_params():
        arg = make_arg(shape).to(memory_format=memory_format).requires_grad_(requires_grad)
        yield opinfo_core.SampleInput(arg, kwargs=kwargs)


def sample_inputs_max_pool3d_with_indices(op_info, device, dtype, requires_grad, **kwargs):
    del op_info
    make_arg = functools.partial(
        torch_testing.make_tensor, device=device, dtype=dtype, requires_grad=False
    )
    params_generator = (
        common_methods_invocations._TestParamsMaxPool3d()  # pylint: disable=protected-access
    )
    for (shape, memory_format), kwargs in params_generator.gen_input_params():
        arg = make_arg(shape).to(memory_format=memory_format).requires_grad_(requires_grad)
        yield opinfo_core.SampleInput(arg, kwargs=kwargs)


def sample_inputs_col2im(op_info, device, dtype, requires_grad, **kwargs):
    del op_info
    # input_shape, output_size, kernal, dilation, padding, stride
    cases = (
        (
            (1, 12, 12),
            (4, 5),
            (2, 2),
            {"dilation": (1, 1), "padding": (0, 0), "stride": (1, 1)},
        ),
        (
            (1, 8, 30),
            (4, 5),
            (2, 2),
            {"dilation": (1, 1), "padding": (1, 1), "stride": (1, 1)},
        ),
        (
            (1, 8, 9),
            (4, 4),
            (2, 2),
            {"dilation": (1, 1), "padding": (0, 0), "stride": (1, 1)},
        ),
        (
            (1, 8, 25),
            (4, 4),
            (2, 2),
            {"dilation": (1, 1), "padding": (1, 1), "stride": (1, 1)},
        ),
        (
            (1, 8, 9),
            (4, 4),
            (2, 2),
            {"dilation": (1, 1), "padding": (1, 1), "stride": (2, 2)},
        ),
        (
            (1, 9, 4),
            (4, 4),
            (3, 3),
            {"dilation": (1, 1), "padding": (1, 1), "stride": (2, 2)},
        ),
        (
            (1, 18, 16),
            (2, 2),
            (1, 1),
            {"dilation": (2, 2), "padding": (3, 3), "stride": (2, 2)},
        ),
    )

    make_arg = functools.partial(
        torch_testing.make_tensor, device=device, dtype=dtype, requires_grad=requires_grad
    )
    for shape, output_size, kernel_size, kwargs in cases:
        tensor = make_arg(shape)
        yield opinfo_core.SampleInput(tensor, args=(output_size, kernel_size), kwargs=kwargs)


OP_DB: List[opinfo_core.OpInfo] = [
    opinfo_core.OpInfo(
        "col2im",
        op=torch.ops.aten.col2im,
        aten_name="col2im",
        dtypes=common_dtype.floating_and_complex_types_and(torch.half, torch.bfloat16),
        sample_inputs_func=sample_inputs_col2im,
        supports_out=False,
    ),
    opinfo_core.OpInfo(
        "convolution",
        aliases=("convolution",),
        aten_name="convolution",
        dtypes=common_dtype.floating_and_complex_types_and(torch.int64, torch.bfloat16),
        sample_inputs_func=sample_inputs_convolution,
        supports_forward_ad=True,
        supports_fwgrad_bwgrad=True,
        gradcheck_nondet_tol=common_utils.GRADCHECK_NONDET_TOL,
        skips=(),
        supports_out=False,
    ),
    opinfo_core.OpInfo(
        "layer_norm",
        aliases=("layer_norm",),
        aten_name="layer_norm",
        dtypes=common_dtype.floating_and_complex_types_and(torch.int64, torch.bfloat16),
        sample_inputs_func=sample_inputs_layer_norm,
        supports_forward_ad=True,
        supports_fwgrad_bwgrad=True,
        gradcheck_nondet_tol=common_utils.GRADCHECK_NONDET_TOL,
        skips=(),
        supports_out=False,
    ),
    opinfo_core.OpInfo(
        "nn.functional.conv3d",
        aliases=("conv3d",),
        aten_name="conv3d",
        dtypes=common_dtype.floating_and_complex_types_and(torch.int64, torch.bfloat16),
        sample_inputs_func=sample_inputs_conv3d,
        supports_forward_ad=True,
        supports_fwgrad_bwgrad=True,
        gradcheck_nondet_tol=common_utils.GRADCHECK_NONDET_TOL,
        skips=(),
        supports_out=False,
    ),
    opinfo_core.OpInfo(
        "nn.functional.max_pool2d_with_indices",
        aten_name="max_pool2d_with_indices",
        supports_forward_ad=True,
        supports_fwgrad_bwgrad=True,
        dtypes=common_dtype.floating_types_and(torch.bfloat16),
        skips=(),
        sample_inputs_func=sample_inputs_max_pool2d_with_indices,
    ),
    opinfo_core.OpInfo(
        "nn.functional.max_pool3d_with_indices",
        aten_name="max_pool3d_with_indices",
        supports_forward_ad=True,
        supports_fwgrad_bwgrad=True,
        dtypes=common_dtype.floating_types_and(torch.bfloat16),
        skips=(),
        sample_inputs_func=sample_inputs_max_pool3d_with_indices,
    ),
]
