# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# --------------------------------------------------------------------------
from __future__ import annotations

import pathlib
import tempfile
import unittest
from typing import Any

import ml_dtypes
import numpy as np
import onnx
import onnx.external_data_helper
import parameterized
import torch

from onnxscript import ir
from onnxscript.ir import _core


class TensorTest(unittest.TestCase):
    def test_initialize(self):
        tensor = _core.Tensor(
            np.random.rand(1, 2).astype(np.float32),
            dtype=ir.DataType.FLOAT,
            shape=_core.Shape((1, 2)),
            name="test",
        )
        self.assertEqual(tensor.name, "test")
        self.assertEqual(tensor.dtype, ir.DataType.FLOAT)
        self.assertEqual(tensor.shape, _core.Shape((1, 2)))
        np.testing.assert_array_equal(tensor, tensor)

    def test_init_raises_when_value_is_not_array(self):
        with self.assertRaises(TypeError):
            _core.Tensor(42)

    def test_init_requires_type_when_value_is_not_np_array(self):
        torch_tensor = torch.tensor(42)
        with self.assertRaises(ValueError):
            _core.Tensor(torch_tensor)

    @parameterized.parameterized.expand(
        [
            ("bfloat16", np.uint16, ir.DataType.BFLOAT16),
            (
                "float8e4m3fn",
                np.dtype((np.uint8, {"e4m3fn": (np.uint8, 0)})),
                ir.DataType.FLOAT8E4M3FN,
            ),
            ("float8e4m3fnuz", np.uint8, ir.DataType.FLOAT8E4M3FNUZ),
            ("float8e5m2", np.uint8, ir.DataType.FLOAT8E5M2),
            ("float8e5m2fnuz", np.uint8, ir.DataType.FLOAT8E5M2FNUZ),
            ("int4", np.int8, ir.DataType.INT4),
            ("int4_uint8", np.uint8, ir.DataType.INT4),
            ("uint4", np.uint8, ir.DataType.UINT4),
        ]
    )
    def test_init_with_non_native_numpy_dtype(self, _: str, np_dtype, dtype: ir.DataType):
        array = np.array([0b1, 0b11], dtype=np_dtype)
        tensor = _core.Tensor(array, dtype=dtype)
        self.assertEqual(tensor.dtype, dtype)
        np.testing.assert_array_equal(tensor, array)

    def test_initialize_with_just_np_array(self):
        array = np.random.rand(1, 2)
        tensor = _core.Tensor(array)
        np.testing.assert_array_equal(tensor, array)

    def test_initialize_raises_when_numpy_dtype_doesnt_match(self):
        array = np.random.rand(1, 2).astype(np.float32)
        with self.assertRaises(TypeError):
            _core.Tensor(array, dtype=ir.DataType.INT64)

    def test_initialize_raises_when_numpy_dtype_doesnt_match_custom_dtype(self):
        custom_dtype = np.dtype((np.uint8, {"e4m3fn": (np.uint8, 0)}))
        array = np.random.rand(1, 2).astype(custom_dtype)
        with self.assertRaises(TypeError):
            _core.Tensor(array, dtype=ir.DataType.BFLOAT16)

    def test_initialize_with_torch_tensor(self):
        array = np.random.rand(1, 2).astype(np.int64)
        np_tensor = _core.Tensor(array)
        torch_tensor = _core.Tensor(torch.tensor(array), dtype=ir.DataType.INT64)
        np.testing.assert_array_equal(torch_tensor, array)
        np.testing.assert_array_equal(torch_tensor, np_tensor)

    def test_dlpack_np_to_torch(self):
        array = np.random.rand(1, 2).astype(np.float32)
        tensor = _core.Tensor(array)
        torch_tensor = torch.from_dlpack(tensor)
        np.testing.assert_array_equal(torch_tensor, array)

    def test_dlpack_torch_to_np(self):
        torch_tensor = torch.rand(1, 2)
        tensor = _core.Tensor(torch_tensor, dtype=ir.DataType.FLOAT)
        array = np.from_dlpack(tensor)
        np.testing.assert_array_equal(array, torch_tensor)

    def test_repr(self):
        tensor = _core.Tensor(np.random.rand(1, 2).astype(np.float32))
        self.assertIsInstance(repr(tensor), str)

    def test_dtype_returns_data_type_enum(self):
        tensor = _core.Tensor(np.random.rand(1, 2).astype(np.float32))
        self.assertEqual(tensor.dtype, ir.DataType.FLOAT)

    def test_shape(self):
        tensor = _core.Tensor(np.random.rand(1, 2).astype(np.float32))
        self.assertEqual(tensor.shape, _core.Shape((1, 2)))

    def test_numpy_returns_np_array(self):
        array = np.random.rand(1, 2).astype(np.float32)
        tensor = _core.Tensor(array)
        np.testing.assert_equal(tensor.numpy(), array)

    def test_numpy_returns_data_when_dtype_is_not_supported(self):
        array = np.array([1], dtype=np.uint8)
        tensor = _core.Tensor(array, dtype=ir.DataType.INT4)
        np.testing.assert_equal(tensor.numpy(), array)

    def test_tobytes(self):
        array = np.random.rand(1, 2).astype(np.float32)
        torch_tensor = torch.tensor(array)
        tensor = _core.Tensor(torch_tensor, dtype=ir.DataType.FLOAT)
        self.assertEqual(tensor.tobytes(), array.tobytes())

    def test_tobtyes_returns_packed_data_for_int4(self):
        array = np.array([-8, -1, 0, 1, 2, 7, 1], dtype=np.int8)
        # Test odd sized array
        assert len(array) % 2 == 1
        tensor = _core.Tensor(array, dtype=ir.DataType.INT4)
        self.assertEqual(tensor.tobytes(), b"\xf8\x10r\x01")

    def test_tobtyes_returns_packed_data_for_uint4(self):
        array = np.array([0, 1, 2, 7, 15], dtype=np.uint8)
        # Test odd sized array
        assert len(array) % 2 == 1
        tensor = _core.Tensor(array, dtype=ir.DataType.UINT4)
        self.assertEqual(tensor.tobytes(), b"\x10r\x0f")

    def test_metadata(self):
        array = np.random.rand(1, 2).astype(np.float32)
        tensor = _core.Tensor(array)
        tensor.meta["test"] = 1
        self.assertEqual(tensor.meta["test"], 1)
        tensor.metadata_props["test"] = "any string"
        self.assertEqual(tensor.metadata_props["test"], "any string")


def _to_external_tensor(tensor_proto, dir: str, filename: str):
    onnx.external_data_helper.set_external_data(tensor_proto, location=filename)
    path = pathlib.Path(dir) / filename
    with open(path, "wb") as f:
        f.write(tensor_proto.raw_data)
    tensor_proto.ClearField("raw_data")
    tensor_proto.data_location = onnx.TensorProto.EXTERNAL


class ExternalTensorTest(unittest.TestCase):
    """Test the memory mapped external tensor class."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.external_data_name = "test_model.bin"
        self.base_path = self.temp_dir.name
        self.data = np.random.rand(2, 42).astype(np.float32)
        self.data_float16 = np.random.rand(2, 42).astype(np.float16)
        self.model = self._simple_model_with_external(
            self.base_path, self.external_data_name, self.data
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _simple_model_with_external(
        self, base_path: str, external_data_name: str, data: np.ndarray
    ) -> onnx.ModelProto:
        input = onnx.helper.make_tensor_value_info("input", onnx.TensorProto.FLOAT, [None])
        output = onnx.helper.make_tensor_value_info("output", onnx.TensorProto.FLOAT, [None])
        raw_data = data.tobytes()
        tensor = onnx.helper.make_tensor(
            "input", onnx.TensorProto.FLOAT, data.shape, raw_data, raw=True
        )
        raw_data2 = self.data_float16.tobytes()
        tensor2 = onnx.helper.make_tensor(
            "input2", onnx.TensorProto.FLOAT16, data.shape, raw_data2, raw=True
        )
        onnx.external_data_helper.set_external_data(
            tensor, external_data_name, offset=0, length=len(raw_data)
        )
        onnx.external_data_helper.set_external_data(
            tensor2, external_data_name, offset=len(raw_data), length=len(raw_data2)
        )

        node = onnx.helper.make_node("Identity", inputs=["input"], outputs=["output"])
        model = onnx.helper.make_model(
            onnx.helper.make_graph(
                [node], "test_graph", [input], [output], initializer=[tensor, tensor2]
            )
        )
        tensor.ClearField("raw_data")
        tensor2.ClearField("raw_data")
        # Save the data to disk
        with open(pathlib.Path(base_path) / external_data_name, "wb") as f:
            f.write(raw_data)
            f.write(raw_data2)
        return model

    def test_initialize(self):
        external_tensor = self.model.graph.initializer[0]
        external_info = onnx.external_data_helper.ExternalDataInfo(external_tensor)
        tensor = _core.ExternalTensor(
            path=pathlib.Path(self.base_path) / external_info.location,
            offset=external_info.offset,
            length=external_info.length,
            dtype=ir.DataType.FLOAT,
            name="input",
            shape=_core.Shape(external_tensor.dims),
        )
        self.assertEqual(tensor.dtype, ir.DataType.FLOAT)
        np.testing.assert_equal(tensor, self.data)
        # Ensure repeated reads are consistent
        np.testing.assert_equal(tensor, self.data)

    def test_totypes_returns_correct_data_in(self):
        external_tensor = self.model.graph.initializer[0]
        external_info = onnx.external_data_helper.ExternalDataInfo(external_tensor)
        tensor = _core.ExternalTensor(
            path=pathlib.Path(self.base_path) / external_info.location,
            offset=external_info.offset,
            length=external_info.length,
            dtype=ir.DataType.FLOAT,
            name="input",
            shape=_core.Shape(external_tensor.dims),
        )
        external_tensor2 = self.model.graph.initializer[1]
        external_info2 = onnx.external_data_helper.ExternalDataInfo(external_tensor2)
        tensor2 = _core.ExternalTensor(
            path=pathlib.Path(self.base_path) / external_info2.location,
            offset=external_info2.offset,
            length=external_info2.length,
            dtype=ir.DataType.FLOAT16,
            name="input",
            shape=_core.Shape(external_tensor2.dims),
        )
        self.assertEqual(tensor.tobytes(), self.data.tobytes())
        self.assertEqual(tensor2.tobytes(), self.data_float16.tobytes())
        # Ensure repeated reads are consistent
        self.assertEqual(tensor.tobytes(), self.data.tobytes())
        self.assertEqual(tensor2.tobytes(), self.data_float16.tobytes())

    @parameterized.parameterized.expand(
        [
            ("FLOAT", ir.DataType.FLOAT),
            ("BOOL", ir.DataType.BOOL),
            ("FLOAT16", ir.DataType.FLOAT16),
            ("DOUBLE", ir.DataType.DOUBLE),
        ]
    )
    def test_external_tensor(self, _: str, dtype: ir.DataType):
        expected_array = np.array(
            [[-3.0, -1.0, -0.5, -0.0, +0.0, 0.5, 1.0, 42.0, 2.0]]
        ).astype(dtype.numpy())
        tensor_proto = ir.serde.serialize_tensor(ir.Tensor(expected_array, dtype=dtype))
        with tempfile.TemporaryDirectory() as temp_dir:
            _to_external_tensor(tensor_proto, temp_dir, "tensor.bin")
            tensor = ir.serde.deserialize_tensor(tensor_proto, temp_dir)
            np.testing.assert_array_equal(tensor.numpy(), expected_array)
            # Close the mmap file by deleting the reference to tensor so Windows doesn't complain
            # about permission errors
            del tensor

    def test_external_tensor_bfloat16(self):
        expected_array = np.array(
            [[-3.0, -1.0, -0.5, -0.0, +0.0, 0.5, 1.0, 42.0, 2.0]]
        ).astype(ml_dtypes.bfloat16)
        tensor_proto = ir.serde.serialize_tensor(
            ir.Tensor(expected_array.view(np.uint16), dtype=ir.DataType.BFLOAT16)
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            _to_external_tensor(tensor_proto, temp_dir, "tensor.bin")
            tensor = ir.serde.deserialize_tensor(tensor_proto, temp_dir)
            np.testing.assert_array_equal(
                tensor.numpy().view(ml_dtypes.bfloat16), expected_array
            )
            # Close the mmap file by deleting the reference to tensor so Windows doesn't complain
            # about permission errors
            del tensor

    @parameterized.parameterized.expand(
        [
            (
                "FLOAT8E4M3FN",
                ir.DataType.FLOAT8E4M3FN,
                ml_dtypes.float8_e4m3fn,
            ),
            (
                "FLOAT8E4M3FNUZ",
                ir.DataType.FLOAT8E4M3FNUZ,
                ml_dtypes.float8_e4m3fnuz,
            ),
            (
                "FLOAT8E5M2",
                ir.DataType.FLOAT8E5M2,
                ml_dtypes.float8_e5m2,
            ),
            (
                "FLOAT8E5M2FNUZ",
                ir.DataType.FLOAT8E5M2FNUZ,
                ml_dtypes.float8_e5m2fnuz,
            ),
        ]
    )
    def test_external_tensor_float8(self, _: str, dtype: ir.DataType, np_dtype):
        expected_array = np.array(
            [[-3.0, -1.0, -0.5, -0.0, +0.0, 0.5, 1.0, 40.0, 2.0]]
        ).astype(np_dtype)
        tensor_proto = ir.serde.serialize_tensor(
            ir.Tensor(expected_array.view(np.uint8), dtype=dtype)
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            _to_external_tensor(tensor_proto, temp_dir, "tensor.bin")
            tensor = ir.serde.deserialize_tensor(tensor_proto, temp_dir)
            np.testing.assert_array_equal(tensor.numpy().view(np_dtype), expected_array)
            # Close the mmap file by deleting the reference to tensor so Windows doesn't complain
            # about permission errors
            del tensor

    @parameterized.parameterized.expand(
        [
            ("INT8", ir.DataType.INT8),
            ("INT16", ir.DataType.INT16),
            ("INT32", ir.DataType.INT32),
            ("INT64", ir.DataType.INT64),
            ("INT4", ir.DataType.INT4),
        ]
    )
    def test_external_tensor_int(self, _: str, dtype: ir.DataType):
        expected_array = np.array([[-1, 0, 1, 7]]).astype(dtype.numpy())
        tensor_proto = ir.serde.serialize_tensor(ir.Tensor(expected_array, dtype=dtype))
        with tempfile.TemporaryDirectory() as temp_dir:
            _to_external_tensor(tensor_proto, temp_dir, "tensor.bin")
            tensor = ir.serde.deserialize_tensor(tensor_proto, temp_dir)
            np.testing.assert_array_equal(tensor.numpy(), expected_array)
            # Close the mmap file by deleting the reference to tensor so Windows doesn't complain
            # about permission errors
            del tensor

    @parameterized.parameterized.expand(
        [
            ("UINT8", ir.DataType.UINT8),
            ("UINT16", ir.DataType.UINT16),
            ("UINT32", ir.DataType.UINT32),
            ("UINT64", ir.DataType.UINT64),
            ("UINT4", ir.DataType.UINT4),
        ]
    )
    def test_external_tensor_uint(self, _: str, dtype: ir.DataType):
        expected_array = np.array([[0, 1, 8]]).astype(dtype.numpy())
        tensor_proto = ir.serde.serialize_tensor(ir.Tensor(expected_array, dtype=dtype))
        with tempfile.TemporaryDirectory() as temp_dir:
            _to_external_tensor(tensor_proto, temp_dir, "tensor.bin")
            tensor = ir.serde.deserialize_tensor(tensor_proto, temp_dir)
            np.testing.assert_array_equal(tensor.numpy(), expected_array)
            # Close the mmap file by deleting the reference to tensor so Windows doesn't complain
            # about permission errors
            del tensor

    @parameterized.parameterized.expand(
        [
            ("COMPLEX64", np.complex64),
            ("COMPLEX128", np.complex128),
        ]
    )
    def test_external_tensor_complex(self, _: str, np_dtype: np.dtype):
        expected_array = np.array([[0.0 + 1j, 0.2 - 1j, 0.3]], dtype=np_dtype)
        tensor_proto = ir.serde.serialize_tensor(ir.Tensor(expected_array))
        with tempfile.TemporaryDirectory() as temp_dir:
            _to_external_tensor(tensor_proto, temp_dir, "tensor.bin")
            tensor = ir.serde.deserialize_tensor(tensor_proto, temp_dir)
            np.testing.assert_array_equal(tensor.numpy(), expected_array)
            # Close the mmap file by deleting the reference to tensor so Windows doesn't complain
            # about permission errors
            del tensor

    def test_external_tensor_empty_tensor(self):
        expected_array = np.array([], dtype=np.float32)
        tensor_proto = ir.serde.serialize_tensor(ir.Tensor(expected_array))
        with tempfile.TemporaryDirectory() as temp_dir:
            _to_external_tensor(tensor_proto, temp_dir, "tensor.bin")
            tensor = ir.serde.deserialize_tensor(tensor_proto, temp_dir)
            np.testing.assert_array_equal(tensor.numpy(), expected_array)
            # Close the mmap file by deleting the reference to tensor so Windows doesn't complain
            # about permission errors
            del tensor


class SymbolicDimTest(unittest.TestCase):
    def test_init_raises_when_value_is_int(self):
        # Static dimensions should be python integers
        with self.assertRaises(TypeError):
            _core.SymbolicDim(42)

    @parameterized.parameterized.expand([("str", "any string"), ("None", None)])
    def test_equality_with_other_dimensions(self, _: str, value: Any):
        dim1 = _core.SymbolicDim(value)
        dim2 = _core.SymbolicDim(value)
        self.assertEqual(dim1, dim2)

    @parameterized.parameterized.expand([("str", "any string"), ("None", None)])
    def test_equality_with_python_values(self, _: str, value: Any):
        dim = _core.SymbolicDim(value)
        self.assertEqual(dim, value)
        self.assertIn(value, [dim])
        self.assertIn(dim, [value])

    @parameterized.parameterized.expand([("str", "any string"), ("None", None)])
    def test_it_is_hashable(self, _: str, value: Any):
        dim = _core.SymbolicDim(value)
        self.assertEqual(hash(dim), hash(value))
        self.assertIn(dim, {dim})
        self.assertIn(dim, {value})


class ShapeTest(unittest.TestCase):
    def test_init_raises_when_denotations_and_dims_have_different_lengths(self):
        with self.assertRaisesRegex(ValueError, "denotations"):
            _core.Shape([42], ["DATA_CHANNEL", "BATCH"])

    def test_int_dimensions_are_python_ints(self):
        shape = _core.Shape([42])
        self.assertIsInstance(shape[0], int)

    @parameterized.parameterized.expand(
        [
            ("empty", (), ()),
            ("1d", (42,), (42,)),
            ("int", (42, 42), (42, 42)),
            ("str", ("any string", "any string"), ("any string", "any string")),
            ("None", (None, None), (None, None)),
        ]
    )
    def test_eq_with_other_shapes(
        self, _: str, dims_1: tuple[Any, ...], dims_2: tuple[Any, ...]
    ):
        shape_1 = _core.Shape(dims_1)
        shape_2 = _core.Shape(dims_2)
        self.assertEqual(shape_1, shape_2)

    @parameterized.parameterized.expand(
        [
            ("empty", ()),
            ("1d", (42,)),
            ("int", (42, 42)),
            ("str", ("any string", "any string")),
            ("None", (None, None)),
        ]
    )
    def test_eq_with_tuple(self, _: str, dims: tuple[Any, ...]):
        shape = _core.Shape(dims)
        self.assertEqual(shape, dims)

    @parameterized.parameterized.expand(
        [
            ("empty", []),
            (
                "1d",
                [
                    42,
                ],
            ),
            ("int", [42, 42]),
            ("str", ["any string", "any string"]),
            ("None", [None, None]),
        ]
    )
    def test_eq_with_list(self, _: str, dims: list[Any]):
        shape = _core.Shape(dims)
        self.assertEqual(shape, dims)

    def test_eq_with_np_shape(self):
        dims = (42,)
        array = np.zeros(dims)
        shape = _core.Shape(dims)
        self.assertEqual(shape, array.shape)

    @parameterized.parameterized.expand(
        [
            ("empty", (), (1,)),
            ("d", (42,), (0,)),
            ("rank", (42, 42), (42, 42, 42)),
            ("str", ("any string",), (42,)),
            ("None", (None, None), (None, 42)),
        ]
    )
    def test_ne_with_other_shapes(
        self, _: str, dims_1: tuple[Any, ...], dims_2: tuple[Any, ...]
    ):
        shape_1 = _core.Shape(dims_1)
        shape_2 = _core.Shape(dims_2)
        self.assertNotEqual(shape_1, shape_2)

    def test_ne_with_random_object(self):
        shape = _core.Shape((42,))
        self.assertNotEqual(shape, 42)

    def test_setitem_raises_when_shape_is_frozen(self):
        shape = _core.Shape([42], denotations=("DATA_CHANNEL",), frozen=True)
        with self.assertRaisesRegex(TypeError, "frozen"):
            shape[0] = 1

    def test_getitem(self):
        shape = _core.Shape([42], denotations=("DATA_CHANNEL",))
        self.assertEqual(shape[0], 42)

    def test_getitem_accepts_a_slice(self):
        shape = _core.Shape([1, 2, 3, 4])
        self.assertEqual(shape[1:3], (2, 3))

    @parameterized.parameterized.expand(
        [
            ("int", 42),
            ("str", "any string"),
            ("None", None),
            ("SymbolicDim", _core.SymbolicDim("any string")),
        ]
    )
    def test_setitem(self, _: str, value):
        shape = _core.Shape([0])
        shape[0] = value
        dim = shape[0]
        if isinstance(dim, _core.SymbolicDim):
            self.assertEqual(dim.value, value)
        else:
            self.assertEqual(dim, value)

    def test_get_denotation(self):
        shape = _core.Shape([42], denotations=("DATA_CHANNEL",))
        self.assertEqual(shape.get_denotation(0), "DATA_CHANNEL")

    def test_set_denotation(self):
        shape = _core.Shape([42, 0], ["DATA_CHANNEL", "BATCH"])
        shape.set_denotation(1, "UPDATED")
        self.assertEqual(shape.get_denotation(1), "UPDATED")

    def test_set_denotation_is_still_possible_when_shape_is_frozen(self):
        shape = _core.Shape([42], denotations=("DATA_CHANNEL",), frozen=True)
        shape.set_denotation(0, "UPDATED")
        self.assertEqual(shape.get_denotation(0), "UPDATED")


class ValueTest(unittest.TestCase):
    def test_initialize(self):
        _ = _core.Value(None, index=0)

    def test_meta(self):
        value = _core.Value(None, index=0)
        value.meta["test"] = 1
        self.assertEqual(value.meta["test"], 1)
        value.metadata_props["test"] = "any string"
        self.assertEqual(value.metadata_props["test"], "any string")

    # TODO(justinchuby): Test all methods


class NodeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.v0 = _core.Value(None, index=None)
        self.v1 = _core.Value(None, index=None)
        self.node = _core.Node("test", "TestOp", inputs=(self.v0, self.v1), num_outputs=3)

    def test_init_with_values(self):
        self.assertEqual(self.node.domain, "test")
        self.assertEqual(self.node.op_type, "TestOp")
        self.assertEqual(self.node.inputs, (self.v0, self.v1))
        self.assertEqual(len(self.node.outputs), 3)
        self.assertEqual(self.node.attributes, {})

    def test_init_with_preinitialized_outputs(self):
        out_1 = _core.Value(
            None,
            index=None,
            name="out_1",
            shape=_core.Shape([1]),
            type=_core.TensorType(ir.DataType.BFLOAT16),
        )
        out_2 = _core.Value(
            None,
            index=None,
            name="out_2",
            shape=_core.Shape([2]),
            type=_core.TensorType(ir.DataType.INT4),
        )
        node = _core.Node("test", "TestOp", inputs=(self.v0, self.v1), outputs=[out_1, out_2])
        self.assertEqual(node.outputs[0].name, "out_1")
        self.assertEqual(node.outputs[0].shape, _core.Shape([1]))
        self.assertEqual(node.outputs[0].dtype, ir.DataType.BFLOAT16)
        self.assertEqual(node.outputs[1].name, "out_2")
        self.assertEqual(node.outputs[1].shape, _core.Shape([2]))
        self.assertEqual(node.outputs[1].dtype, ir.DataType.INT4)
        self.assertIs(node.outputs[0], out_1)
        self.assertIs(node.outputs[1], out_2)
        self.assertIs(node.outputs[0].producer(), node)
        self.assertIs(node.outputs[1].producer(), node)
        self.assertIs(node.outputs[0].index(), 0)
        self.assertIs(node.outputs[1].index(), 1)

    def test_init_raises_when_num_outputs_does_not_match_outputs(self):
        with self.assertRaisesRegex(ValueError, "outputs"):
            _core.Node("test", "TestOp", inputs=(self.v0, self.v1), num_outputs=2, outputs=[])

    def test_init_with_zero_num_outputs(self):
        node = _core.Node("test", "TestOp", inputs=(self.v0, self.v1), num_outputs=0)
        self.assertEqual(node.outputs, ())

    def test_init_with_empty_outputs(self):
        node = _core.Node("test", "TestOp", inputs=(self.v0, self.v1), outputs=[])
        self.assertEqual(node.outputs, ())

    def test_init_produces_one_output_with_unspecified_output_argument(self):
        node = _core.Node("test", "TestOp", inputs=(self.v0, self.v1))
        self.assertEqual(len(node.outputs), 1)

    def test_metadata(self):
        self.node.meta["test"] = 1
        self.assertEqual(self.node.meta["test"], 1)
        self.node.metadata_props["test"] = "any string"
        self.assertEqual(self.node.metadata_props["test"], "any string")

    def test_it_is_added_to_a_graph_if_specified(self):
        graph = _core.Graph(
            (self.v0, self.v1),  # type: ignore
            self.node.outputs,
            nodes=(self.node,),
            opset_imports={"": 1},
        )
        self.assertIn(self.node, graph)

    # TODO(justinchuby): Test all methods


class GraphTest(unittest.TestCase):
    def setUp(self) -> None:
        self.v0 = _core.Input(name="v0")
        self.v1 = _core.Input(name="v1")
        self.node = _core.Node(
            "", "Add", inputs=(self.v0, self.v1), num_outputs=1, name="node_add"
        )
        self.graph = _core.Graph(
            (self.v0, self.v1),
            self.node.outputs,
            nodes=(self.node,),
            opset_imports={"": 1},
        )

    def test_initialize(self):
        self.assertEqual(self.graph.inputs, [self.v0, self.v1])
        self.assertEqual(self.graph.outputs, [*self.node.outputs])
        self.assertEqual(self.graph.opset_imports, {"": 1})
        self.assertEqual(self.graph.initializers, {})
        self.assertIsNone(self.graph.doc_string)

    def test_it_is_iterable_of_nodes(self):
        self.assertEqual(list(self.graph), [self.node])

    def test_node_returns_node_by_name(self):
        self.assertIs(self.graph.node("node_add"), self.node)

    def test_node_returns_node_by_index(self):
        self.assertIs(self.graph.node(0), self.node)

    def test_node_raises_when_node_does_not_exist(self):
        with self.assertRaisesRegex(ValueError, "not found"):
            self.graph.node("non_existent")

    def test_node_raises_when_index_out_of_range(self):
        with self.assertRaises(IndexError):
            self.graph.node(1)

    def test_num_nodes_returns_the_count_of_nodes(self):
        self.assertEqual(self.graph.num_nodes(), 1)
        self.assertEqual(self.graph.num_nodes(), len(self.graph))

    def test_metadata(self):
        self.graph.meta["test"] = 1
        self.assertEqual(self.graph.meta["test"], 1)
        self.graph.metadata_props["test"] = "any string"
        self.assertEqual(self.graph.metadata_props["test"], "any string")

    def test_remove_removes_node_from_graph(self):
        self.graph.remove(self.node)
        self.assertEqual(list(self.graph), [])
        self.assertIsNone(self.node.graph)

    def test_remove_does_not_change_input_users(self):
        self.graph.remove(self.node)
        self.assertEqual(tuple(self.v0.uses()), ((self.node, 0),))
        self.assertEqual(tuple(self.v1.uses()), ((self.node, 1),))

    def test_remove_does_not_change_graph_in_out(self):
        self.graph.remove(self.node)
        self.assertEqual(self.graph.inputs, [self.v0, self.v1])
        self.assertEqual(self.graph.outputs, list(self.node.outputs))

    def test_remove_raises_when_node_does_not_belong_to_graph(self):
        node = _core.Node("", "Add", inputs=(self.v0, self.v1), num_outputs=1)
        with self.assertRaisesRegex(ValueError, "graph"):
            self.graph.remove(node)

    def test_remove_safe_raises_when_node_output_is_graph_output(self):
        with self.assertRaisesRegex(ValueError, "output"):
            self.graph.remove(self.node, safe=True)

    def test_remove_safe_raises_when_node_has_users(self):
        v0 = _core.Input(name="v0")
        v1 = _core.Input(name="v1")
        add_node = _core.Node("", "Add", inputs=(v0, v1), num_outputs=1)
        identity_node = _core.Node("", "Identity", inputs=add_node.outputs, num_outputs=1)
        graph = _core.Graph(
            (v0, v1),
            identity_node.outputs,
            nodes=(add_node, identity_node),
            opset_imports={"": 1},
        )
        with self.assertRaisesRegex(ValueError, "used by other nodes"):
            graph.remove(add_node, safe=True)

    def test_remove_safe_removes_uses_of_removed_nodes(self):
        v0 = _core.Input(name="v0")
        v1 = _core.Input(name="v1")
        add_node = _core.Node("", "Add", inputs=(v0, v1), num_outputs=1)
        identity_node = _core.Node("", "Identity", inputs=add_node.outputs, num_outputs=1)
        graph = _core.Graph(
            (v0, v1),
            identity_node.outputs,
            nodes=(add_node, identity_node),
            opset_imports={"": 1},
        )
        # Remove add_node and check that it is no longer a consumer of v0 and v1
        sub_node = _core.Node("", "Sub", inputs=(v0, v1), num_outputs=1)
        identity_node.replace_input_with(0, sub_node.outputs[0])
        graph.insert_before(identity_node, sub_node)
        graph.remove(add_node, safe=True)
        self.assertEqual(tuple(v0.uses()), ((sub_node, 0),))
        self.assertEqual(tuple(v1.uses()), ((sub_node, 1),))
        self.assertEqual(tuple(graph), (sub_node, identity_node))
        self.assertEqual(add_node.inputs, (None, None))

    # TODO(justinchuby): Test graph mutation methods


if __name__ == "__main__":
    unittest.main()
