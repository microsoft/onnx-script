# SPDX-License-Identifier: Apache-2.0

import unittest
import os
import textwrap
import numpy as np
import onnx
from onnx import helper
import onnxruntime
from onnxscript.converter import Converter

CURRENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")


class TestConverter(unittest.TestCase):
    def _convert(self, script):
        converter = Converter()
        return converter.convert(script)

    def _convert_and_save(self, script):
        converter = Converter()
        fnlist = converter.convert(script)
        TEST_OUTPUT_DIR = os.path.join(CURRENT_DIR, "testoutputs")
        if not os.path.exists(TEST_OUTPUT_DIR):
            os.makedirs(TEST_OUTPUT_DIR)
        for f in fnlist:
            graph = f.to_graph_proto()
            text = helper.printable_graph(graph)
            with open(os.path.join(TEST_OUTPUT_DIR, f.name + ".txt"), "w") as f:
                f.write(text)
            model = onnx.helper.make_model(
                graph, producer_name='p2o',
                opset_imports=[onnx.helper.make_opsetid("", 15)])
            model = onnx.shape_inference.infer_shapes(model)
            onnx.checker.check_model(model)
            onnx.save(model, os.path.join(TEST_OUTPUT_DIR, f.name + ".onnx"))

    def test_source_input(self):
        script = textwrap.dedent("""
            def square(x):
                return onnx.Mul(x, x)
            """)
        res = self._convert(script)
        self.assertEqual(len(res), 1)

    def test_source_input_ort(self):
        script = textwrap.dedent("""
            def square(x):
                y = onnx.Mul(x, x)
                return y
            """)
        res = self._convert(script)
        self.assertEqual(len(res), 1)
        proto = res[0].to_graph_proto()
        model = onnx.helper.make_model(
            proto, producer_name='p2o',
            opset_imports=[onnx.helper.make_opsetid("", 15)])
        sess = onnxruntime.InferenceSession(model.SerializeToString())
        x = np.array([5, 6], dtype=np.float32)
        got = sess.run(None, {'x': x})
        self.assertEqual((x * x).tolist(), got[0].tolist())

    def test_constant(self):
        script = textwrap.dedent("""
            def square(x):
                y = x + 1
                return y
            """)
        res = self._convert(script)
        self.assertEqual(len(res), 1)
        proto = res[0].to_graph_proto()
        model = onnx.helper.make_model(
            proto, producer_name='p2o',
            opset_imports=[onnx.helper.make_opsetid("", 15)])
        sess = onnxruntime.InferenceSession(model.SerializeToString())
        x = np.array([5, 6], dtype=np.float32)
        got = sess.run(None, {'x': x})
        self.assertEqual((x + 1).tolist(), got[0].tolist())

    def test_constants(self):
        script = textwrap.dedent("""
            def square(x):
                z = 1
                w = 2
                y = x + z + w
                return y
            """)
        res = self._convert(script)
        self.assertEqual(len(res), 1)
        proto = res[0].to_graph_proto()
        model = onnx.helper.make_model(
            proto, producer_name='p2o',
            opset_imports=[onnx.helper.make_opsetid("", 15)])
        sess = onnxruntime.InferenceSession(model.SerializeToString())
        x = np.array([5, 6], dtype=np.float32)
        got = sess.run(None, {'x': x})
        self.assertEqual((x + 3).tolist(), got[0].tolist())

    def test_constants2(self):
        script = textwrap.dedent("""
            def square(x):
                y = x + (1 + 2)
                return y
            """)
        res = self._convert(script)
        self.assertEqual(len(res), 1)
        proto = res[0].to_graph_proto()
        model = onnx.helper.make_model(
            proto, producer_name='p2o',
            opset_imports=[onnx.helper.make_opsetid("", 15)])
        sess = onnxruntime.InferenceSession(model.SerializeToString())
        x = np.array([5, 6], dtype=np.float32)
        got = sess.run(None, {'x': x})
        self.assertEqual((x + 3).tolist(), got[0].tolist())

    def test_msdomain(self):
        # Temporary patch to use com.microsoft domain
        script = textwrap.dedent("""
            def foo(x):
                return msdomain.bar(x, x)
            """)
        self._convert(script)

    def test_onnxfns(self):
        self._convert(os.path.join(CURRENT_DIR, "onnxfns.py"))

    def test_models(self):
        self._convert_and_save(os.path.join(CURRENT_DIR, "onnxmodels.py"))

    def test_if_models(self):
        self._convert_and_save(os.path.join(CURRENT_DIR, "if.py"))

    def test_loop_models(self):
        self._convert_and_save(os.path.join(CURRENT_DIR, "loop.py"))


if __name__ == '__main__':
    # import logging
    # log = logging.getLogger('onnx-script')
    # log.setLevel(logging.DEBUG)
    # logging.basicConfig(level=logging.DEBUG)
    # TestConverter().test_constants2()
    unittest.main()
