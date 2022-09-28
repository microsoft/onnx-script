# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# --------------------------------------------------------------------------

import ast
import inspect
import os
import sys
import textwrap
import types
import unittest
import warnings

import numpy as np
import onnx
import onnxruntime
from numpy.testing import assert_almost_equal
from onnx import TensorProto
from onnx.helper import make_tensor, printable_graph
from onnx.onnx_cpp2py_export.checker import ValidationError
from onnxruntime.capi.onnxruntime_pybind11_state import (
    Fail,
    InvalidArgument,
    InvalidGraph,
)
from packaging.version import Version

from onnxscript import OnnxFunction, script
from onnxscript.converter import Converter, TranslationError
from onnxscript.onnx_opset import opset15 as op
from onnxscript.onnx_types import FLOAT, INT64
from onnxscript.test.testutils import TestBase

TEST_INPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
TEST_OUTPUT_DIR = os.path.join(TEST_INPUT_DIR, "testoutputs")


class TestConverter(TestBase):
    def validate(self, script):
        if isinstance(script, types.ModuleType):
            fnlist = [f for f in script.__dict__.values() if isinstance(f, OnnxFunction)]
        elif isinstance(script, OnnxFunction):
            fnlist = [script]
        else:
            fnlist = script
        if not os.path.exists(TEST_OUTPUT_DIR):
            os.makedirs(TEST_OUTPUT_DIR)
        for f in fnlist:
            with self.subTest(f=f.name):
                f.to_function_proto()

    def validate_save(
        self,
        script,
        save_text=False,
        check_ort=False,
        shape_inference=True,
        skip_check_ort=None,
    ):
        if isinstance(script, types.ModuleType):
            fnlist = [f for f in script.__dict__.values() if isinstance(f, OnnxFunction)]
        elif isinstance(script, OnnxFunction):
            fnlist = [script]
        else:
            fnlist = script
        if not os.path.exists(TEST_OUTPUT_DIR):
            os.makedirs(TEST_OUTPUT_DIR)
        fcts = {}
        for f in fnlist:
            with self.subTest(f=f.name):
                model = f.to_model_proto(io_types=FLOAT)
                if save_text:
                    with open(os.path.join(TEST_OUTPUT_DIR, f"{f.name}.txt"), "w") as fi:
                        fi.write(printable_graph(model.graph))
                        for fct in model.functions:
                            fi.write("\n-------------------------\n")
                            fi.write(printable_graph(fct))
                if check_ort and (skip_check_ort is None or f.name not in skip_check_ort):
                    try:
                        onnxruntime.InferenceSession(model.SerializeToString())
                    except (Fail, InvalidGraph, InvalidArgument) as e:
                        raise AssertionError(
                            f"onnxruntime cannot load function " f"{f.name}\n--\n{str(model)}"
                        ) from e
                if shape_inference:
                    model = onnx.shape_inference.infer_shapes(model)
                if save_text:
                    with open(os.path.join(TEST_OUTPUT_DIR, f"{f.name}.shape.txt"), "w") as fi:
                        fi.write(printable_graph(model.graph))
                        for fct in model.functions:
                            f.write("\n-------------------------\n")
                            f.write(printable_graph(fct))
                try:
                    onnx.checker.check_model(model)
                except ValidationError as e:
                    if "Field 'shape' of 'type' is required but missing" in str(
                        e
                    ) or "Field 'shape' of type is required but missing" in str(e):
                        # input or output shapes are missing because the function
                        # was defined with FLOAT[...].
                        warnings.warn(str(e))
                    else:
                        onnx.save(model, os.path.join(TEST_OUTPUT_DIR, f"{f.name}.error.onnx"))
                        raise AssertionError("Verification of model failed.") from e
                onnx.save(model, os.path.join(TEST_OUTPUT_DIR, f"{f.name}.onnx"))
                fcts[f.name] = model
        return fcts

    def validate_expansion(self, script):
        functions = self.validate_save(script, check_ort=True)
        for name in functions:
            if not name.endswith("_expanded"):
                f = functions[name]
                name_expanded = f"{name}_expanded"
                if name_expanded in functions:
                    with self.subTest("Expansion test", function=name):
                        f_expanded = functions[name_expanded]
                        self.assertSame(f, f_expanded)

    def test_eager_op(self):
        from onnxscript.test.models import eager_op

        test_functions = self.validate_save(eager_op, check_ort=True)

        x = np.array([0, 5, -2], dtype=np.float32)

        onx = test_functions["eager_op"]
        self.assertIn('name: "fmod"', str(onx))
        sess = onnxruntime.InferenceSession(onx.SerializeToString())
        y = sess.run(None, {"X": x})[0]
        self.assertEqual(y.tolist(), [0.0, 0.5, -0.5])
        # numpy fmod and operator % disagree on this example
        res = eager_op.eager_op(x)
        self.assertEqual(res.tolist(), [0.0, 0.5, -0.5])

        onx = test_functions["eager_abs"]
        sess = onnxruntime.InferenceSession(onx.SerializeToString())
        y = sess.run(None, {"X": x})[0]
        self.assertEqual(y.tolist(), [1, 6, 3])
        res = eager_op.eager_abs(x)
        self.assertEqual(res.tolist(), [1, 6, 3])

    def test_error_undefined(self):
        with self.assertRaises(ValueError) as e:

            @script()
            def square(x):
                return op.Mul(undefined, x)  # noqa: F821

        self.assertIn("square:3", str(e.exception))

    def test_run_ort(self):
        @script()
        def square(x):
            return op.Mul(x, x)

        with self.assertRaises(TypeError) as cm:
            # checking that the function raises an exception when types are not defined.
            square.to_model_proto()
        self.assertIn("square:2", str(cm.exception))
        self.assertIn("Variable x is missing", str(cm.exception))
        model = square.to_model_proto(io_types=FLOAT)
        sess = onnxruntime.InferenceSession(model.SerializeToString())
        x = np.array([5, 6], dtype=np.float32)
        got = sess.run(None, {"x": x})
        self.assertEqual((x * x).tolist(), got[0].tolist())

    def test_onnxfns1(self):
        from onnxscript.test.models import onnxfns1

        self.validate(onnxfns1)

    def test_onnxfns1A(self):
        from onnxscript.test.models import onnxfns1A

        self.validate(onnxfns1A)

    def test_ort_custom_ops(self):
        from onnxscript.test.functions import ort_custom_ops

        self.validate(ort_custom_ops)

    def test_unary_op(self):
        from onnxscript.test.models import m1

        self.validate_save(m1)

    def test_subfunction_check_model(self):
        from onnxscript.test.models import subfunction

        model = subfunction.MyElu.function_ir.to_model_proto(producer_name="p2o")
        model = onnx.shape_inference.infer_shapes(model)
        onnx.checker.check_model(model)

    @unittest.skipIf(
        Version(onnxruntime.__version__) < Version("1.12"),
        reason="onnxruntime does not support that scenario.",
    )
    def test_subfunction(self):
        from onnxscript.test.models import subfunction

        self.validate_save(subfunction, check_ort=True)

    def test_if_models(self):
        from onnxscript.test.models import if_statement

        self.validate_save(if_statement)

    def test_docstring(self):
        @script()
        def sumprod(x: FLOAT["N"], N: INT64) -> (FLOAT["N"], FLOAT["N"]):  # noqa: F821
            """
            Combines ReduceSum, ReduceProd.
            """
            sum = op.Identity(x)
            prod = op.Identity(x)
            for _ in range(N):
                sum = sum + x
                prod = prod * x
            return sum, prod

        proto = sumprod.to_function_proto()
        self.assertEqual(proto.doc_string.strip(), "Combines ReduceSum, ReduceProd.")

    def test_signal(self):
        from onnxscript.test.models import signal_dft

        # shape_inference crashes on stft.
        self.validate_save(signal_dft, shape_inference=False)

    def test_multi(self):
        from onnxscript.test.models import multi

        self.validate_save(multi, shape_inference=False)

    def test_dropout(self):
        from onnxscript.test.models import dropout

        self.validate_save(dropout, shape_inference=False)

    def test_attrref(self):
        from onnxscript.test.models import attrref

        self.validate_save(attrref, shape_inference=False)

    def test_renaming(self):
        from onnxscript.test.models import renaming

        self.validate_save(renaming, shape_inference=False)

    @unittest.skipIf(True, reason="TypeError: val must be numeric not <class 'NoneType'>")
    def test_opt_output(self):
        from onnxscript.test.models import opt_output

        self.validate_save(opt_output, shape_inference=False)

    def test_opt_input(self):
        from onnxscript.test.models import opt_input

        self.validate_save(opt_input, shape_inference=False)

    @unittest.skipIf(
        True, reason="ValueError: A function with attributes " "cannot be exported as a model."
    )
    def test_onnxfns2(self):
        from onnxscript.test.models import onnxfns2

        self.validate_save(onnxfns2, shape_inference=False)

    def test_none_as_input(self):
        """
        Test that use of None as an actual parameter is accepted.
        """

        @script()
        def clipmax(x: FLOAT, max: FLOAT):  # noqa: F821
            return op.Clip(x, None, max)

        self.validate_save(clipmax)

    def test_type_double(self):
        from onnxscript.test.models import type_double

        fcts = self.validate_save(type_double, check_ort=False)
        f = fcts["double_abs"]
        self.assertEqual(f.graph.input[0].type.tensor_type.elem_type, 11)
        self.assertEqual(f.graph.output[0].type.tensor_type.elem_type, 11)
        f = fcts["double_cast"]
        self.assertEqual(f.graph.input[0].type.tensor_type.elem_type, 7)
        self.assertEqual(f.graph.output[0].type.tensor_type.elem_type, 11)
        f = fcts["double_abs_subgraph"]
        self.assertEqual(f.graph.input[0].type.tensor_type.elem_type, 11)
        self.assertEqual(f.graph.output[0].type.tensor_type.elem_type, 11)
        g = f.graph.node[3].attribute[0].g
        self.assertEqual(g.output[0].type.tensor_type.elem_type, 11)
        g = f.graph.node[3].attribute[1].g
        self.assertEqual(g.output[0].type.tensor_type.elem_type, 11)
        self.validate_save(type_double, check_ort=True)

    def test_cast_like(self):
        from onnxscript.test.models import cast_like

        self.validate_expansion(cast_like)

    def test_opset_import(self):
        from onnxscript.test.models import different_opset

        fcts = self.validate_save(different_opset, shape_inference=False)
        s16 = str(fcts["shape_A"])
        s14 = str(fcts["shape_B"])
        sdef = str(fcts["inc_any"])
        self.assertIn("version: 16", s16)
        self.assertNotIn("version: 14", s16)
        self.assertIn("version: 14", s14)
        self.assertNotIn("version: 16", s14)
        self.assertIn("version: 16", sdef)
        self.assertNotIn("version: 14", sdef)
        self.assertNotIn("version: 15", sdef)

    def test_sequences(self):
        from onnxscript.test.models import sequences

        test_functions = self.validate_save(sequences, check_ort=True)

        f = test_functions["make_sequence_tensor"]

        A = np.array([[0, 1, 2]], dtype=np.float32)
        eager_mode = sequences.make_sequence_tensor(A)
        self.assertEqual(eager_mode.shape, (5, 3))
        self.assertEqual(eager_mode.dtype, np.float32)

        sess = onnxruntime.InferenceSession(f.SerializeToString())
        result = sess.run(None, {"A": A})[0]
        assert_almost_equal(eager_mode, result)

        f = test_functions["make_sequence_tensor_accumulated"]

        A = np.array([[0, 1, 2]], dtype=np.float32)
        eager_mode = sequences.make_sequence_tensor_accumulated(A)
        self.assertEqual(eager_mode.shape, (5, 3))
        self.assertEqual(eager_mode.dtype, np.float32)

        sess = onnxruntime.InferenceSession(f.SerializeToString())
        result = sess.run(None, {"A": A})[0]
        assert_almost_equal(eager_mode, result)

    def test_loops_break(self):
        from onnxscript.test.models import loops_break

        test_functions = self.validate_save(loops_break, check_ort=True)
        self.assertIn("loop1", test_functions)
        for name in ["loop1", "loop_range_cond"]:
            with self.subTest(fct=name):
                f = test_functions[name]
                self.assertIn('op_type: "Loop"', str(f))
        onx = test_functions["loop_range_cond"]
        sess = onnxruntime.InferenceSession(onx.SerializeToString())
        x = np.array([0, 1, 2], dtype=np.float32)
        y = sess.run(None, {"A": x})[0]
        self.assertEqual(loops_break.loop_range_cond(x).tolist(), [0.0, 46.0, 92.0])
        self.assertEqual(y.tolist(), [0.0, 46.0, 92.0])
        x = np.array([0, 1, -2], dtype=np.float32)
        y = sess.run(None, {"A": x})[0]
        self.assertEqual(loops_break.loop_range_cond(x).tolist(), [0, 11, -22])
        self.assertEqual(y.tolist(), [0, 11, -22])

    def test_loops_while(self):
        from onnxscript.test.models import loops_while

        test_functions = self.validate_save(loops_while, check_ort=True)
        self.assertIn("loop1", test_functions)
        for name in ["loop1", "loop_range_cond_only"]:
            with self.subTest(fct=name):
                f = test_functions[name]
                self.assertIn('op_type: "Loop"', str(f))
        onx = test_functions["loop_range_cond_only"]
        sess = onnxruntime.InferenceSession(onx.SerializeToString())
        x = np.array([0, 1, -2], dtype=np.float32)
        y = sess.run(None, {"A": x})[0]
        self.assertEqual(y.tolist(), [0, 10, -20])
        res = loops_while.loop_range_cond_only(x)
        self.assertEqual(res.tolist(), [0, 10, -20])

    @unittest.skipIf(
        sys.version_info[:2] < (3, 8), reason="Notation [...] not supported in python 3.7."
    )
    def test_getitem(self):
        from onnxscript.test.models import getitem

        if sys.version_info[:2] >= (3, 8):
            skip_check_ort = None
        else:
            # negative indices are not supported in python 3.7
            # one constant is evaluated as float
            skip_check_ort = ["getitem_i_slice_neg", "getitem_i_slice_step"]
        test_functions = self.validate_save(
            getitem, check_ort=True, skip_check_ort=skip_check_ort
        )

        # eager mode is disabled because A[np.array([0]): np.array([1])] is not a valid
        # expression.
        A = np.array([0, 1, 2])
        i = np.array([0])
        try:
            A[i : i + 1]
            eager = True
        except Exception:
            # TypeError: only integer scalar arrays can be converted to a scalar index
            eager = False

        def check_function(x, name, expected, eager=True):
            if skip_check_ort is not None and name in skip_check_ort:
                return
            with self.subTest(name=name):
                onx = test_functions[name]
                sess = onnxruntime.InferenceSession(onx.SerializeToString())
                try:
                    y = sess.run(None, {"A": x})[0]
                except Exception as e:
                    raise AssertionError(
                        f"Unable to run ONNX for function {name!r} " f"due to {e!r}\n{onx}."
                    ) from e
                self.assertEqual(y.tolist(), expected)
                f = getattr(getitem, name)
                if eager:
                    self.assertEqual(f(x).tolist(), expected)

        x = np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11]], dtype=np.float32)

        check_function(x, "getitem_i", [0.0, 1.0, 2.0])
        check_function(x, "getitem_i_last", [9.0, 10.0, 11.0])
        check_function(x, "getitem_i_expr", [1.0, 2.0, 3.0])
        check_function(x, "getitem_i_slice", [[3.0, 4.0, 5.0]])
        check_function(x, "getitem_i_slice_left", [[3, 4, 5], [6, 7, 8], [9, 10, 11]])
        check_function(x, "getitem_i_slice_right", [[0, 1, 2], [3, 4, 5]])
        check_function(x, "getitem_i_slice_neg", [[3, 4, 5], [6, 7, 8]])
        check_function(x, "getitem_i_slice_step", [[6.0, 7.0, 8.0], [3.0, 4.0, 5.0]])
        # TODO: force eager to True when the following issue is resolved.
        check_function(x, "getitem_i_var", [[3.0, 4.0, 5.0]], eager=eager)
        check_function(x, "getitem_i_tuple", [[0], [3]])
        check_function(x, "getitem_i_mixed_tuple", [0, 3])
        check_function(x, "getitem_column", [1.0, 4.0, 7.0, 10.0])
        check_function(x, "getitem_index_int0_1", [3, 4, 5], eager=eager)
        check_function(x, "getitem_index_int0", [0, 1, 2], eager=eager)
        check_function(x, "getitem_rev", x[:0:-1].tolist())
        check_function(x, "getitem_rev0", x[0, :0:-1].tolist())

    @unittest.skipIf(
        sys.version_info[:2] < (3, 9), reason="Notation [...] not supported in python 3.8."
    )
    def test_getitem39(self):
        from onnxscript.test.models import getitem39

        test_functions = self.validate_save(getitem39, check_ort=True)

        # eager mode is disabled because A[np.array([0]): np.array([1])] is not a valid
        # expression.
        A = np.array([0, 1, 2])
        i = np.array([0])
        try:
            A[i : i + 1]
            eager = True
        except Exception:
            # TypeError: only integer scalar arrays can be converted to a scalar index
            eager = False

        def check_function(x, name, expected, eager=True):
            with self.subTest(name=name):
                onx = test_functions[name]
                sess = onnxruntime.InferenceSession(onx.SerializeToString())
                try:
                    y = sess.run(None, {"A": x})[0]
                except Exception as e:
                    raise AssertionError(
                        f"Unable to run ONNX for function {name!r} " f"due to {e!r}\n{onx}."
                    ) from e
                self.assertEqual(y.tolist(), expected)
                f = getattr(getitem39, name)
                if eager:
                    self.assertEqual(f(x).tolist(), expected)

        x = np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11]], dtype=np.float32)

        check_function(x, "getitem_index_int", [2.0], eager=eager)
        check_function(x, "getitem_index_int2", [2.0], eager=eager)

    def check_failure(self, f, msg):
        source = textwrap.dedent(inspect.getsource(f))
        global_names = globals().copy()
        top_level_ast = ast.parse(source)
        f_ast = top_level_ast.body[0]
        cvt = Converter(opset=op, global_names=global_names, source=source, default_opset=op)
        try:
            cvt.top_level_stmt(f_ast)
        except TranslationError as e:
            if msg not in str(e):
                raise AssertionError(f"Unable to find {msg!r} in {e!r} in\n{source}") from e
            return
        raise AssertionError("No raised exception.")

    @unittest.skipIf(
        sys.version_info[:2] < (3, 8), reason="Notation [...] not supported in python 3.7."
    )
    def test_getitem_failure(self):
        def f1(A: FLOAT[...]) -> FLOAT[...]:
            zero = op.Constant(value=make_tensor("zero", TensorProto.INT64, [1], [0]))
            index = zero, zero + 1
            r = A[index]
            return r

        ast_name = "_ast" if sys.version_info[:2] < (3, 9) else "ast"
        self.check_failure(f1, f"Left term must be a tuple not <class '{ast_name}.Name'>")

        def f2(A: FLOAT[...]) -> FLOAT[...]:
            return A[::-1]

        ast_name = "_ast" if sys.version_info[:2] < (3, 9) else "ast"
        self.check_failure(f2, "`?::-1` cannot be expressed with ONNX")


if __name__ == "__main__":
    # import logging
    # logging.basicConfig(level=logging.DEBUG)
    # TestConverter().test_getitem()
    unittest.main(verbosity=2)
