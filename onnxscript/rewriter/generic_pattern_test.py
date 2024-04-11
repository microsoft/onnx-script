from __future__ import annotations

import contextlib
import io
import os
import time
import unittest

import numpy as np
import onnx
import onnx.helper as oh
import onnx.numpy_helper as onh
from numpy.testing import assert_almost_equal
from onnx.reference import ReferenceEvaluator
from onnx.reference.op_run import OpRun

import onnxscript._legacy_ir as oir
import onnxscript._legacy_ir.protobuilder as oip
import onnxscript.rewriter.generic_pattern as org

TFLOAT = onnx.TensorProto.FLOAT


class GenericPatternTest(unittest.TestCase):
    def test_bridge_model(self):
        model = onnx.parser.parse_model(
            """
            <ir_version: 7, opset_import: [ "" : 17]>
            agraph (float[2, 3, 5, 4] input_x, float[5] input_y, float[2, 3, 5] input_z) => (float[2, 4, 6] output)
            {
                shape_a = Constant<value: tensor = int64[4] {2, 3, 5, 4}>()
                reshape_x = Reshape (input_x, shape_a)
                gemm = Gemm<alpha=1.0, beta=1.0> (reshape_x, input_y, input_z)
                shape_d = Constant<value: tensor = int64[3] {2, 4, 6}>()
                output = Reshape (gemm, shape_d)
            }
        """
        )
        org.ModelWithGraphStructure(oir.irbuilder.build_ir(model))

    def _range(self, *shape, bias: float | None = None):
        n = np.prod(shape)
        x = np.arange(n).astype(np.float32) / n
        if bias:
            x = x + bias
        return x.reshape(tuple(shape)).astype(np.float32)

    def test_graph_pattern_builder(self):
        class AddAddPattern(org.GenericPattern):
            """Replaces Add + Add by AddAdd."""

            @classmethod
            def match_pattern(cls, op: org.BuilderWithGraphStructure, x, y, z):
                """Builds the pattern to match."""
                tmp = op.Add(x, y)
                return op.Add(tmp, z)

            @classmethod
            def apply_pattern(cls, op: org.BuilderWithGraphStructure, x, y, z):
                """Builds the pattern to match."""
                return op.AddAdd(x, y, z, domain="ZZZ")

            def validate_mapping(
                self,
                g: oir.Model,
                match_result: org.PatternMatchResult,
            ) -> bool:
                assert g
                assert len(match_result.model_nodes) == 2
                return True

        class AddAdd(OpRun):
            op_domain = "ZZZ"

            def _run(self, x, y, z):
                return (x + y + z,)

        model = oh.make_model(
            oh.make_graph(
                [
                    oh.make_node("Add", ["x", "y"], ["gggg"]),
                    oh.make_node("Add", ["gggg", "z"], ["final"]),
                ],
                "dummy",
                [
                    oh.make_tensor_value_info("x", TFLOAT, [None, None]),
                    oh.make_tensor_value_info("y", TFLOAT, [None, None]),
                    oh.make_tensor_value_info("z", TFLOAT, [None, None]),
                ],
                [oh.make_tensor_value_info("final", TFLOAT, [None, None])],
            ),
            opset_imports=[oh.make_opsetid("", 18)],
            ir_version=9,
        )
        onnx.checker.check_model(model)

        ir_model = oir.irbuilder.build_ir(model)

        pattern = AddAddPattern(verbose=0)
        rule = pattern.make_rule()
        rule.apply_to_model(ir_model)
        self.assertEqual(
            ["AddAdd"],
            [n.op_type for n in ir_model.graph.nodes],
        )
        # TODO: do that in pattern.py.
        ir_model.version_map["ZZZ"] = 1

        builder = oip.ModelProtoBuilder()
        opt_onx = builder.visit_ir_model(ir_model)

        self.assertEqual(
            ["AddAdd"],
            [n.op_type for n in opt_onx.graph.node],
        )

        feeds = {
            "x": self._range(5, 6),
            "y": self._range(5, 6),
            "z": self._range(5, 6),
        }
        ref1 = ReferenceEvaluator(model)
        expected = ref1.run(None, feeds)

        self.assertEqual(0, len(opt_onx.graph.initializer))
        opsets = {v.domain: v.version for v in opt_onx.opset_import}
        self.assertIn("ZZZ", opsets)
        self.assertEqual(opsets["ZZZ"], 1)

        ref2 = ReferenceEvaluator(opt_onx, new_ops=[AddAdd])
        got = ref2.run(None, feeds)
        assert_almost_equal(expected[0], got[0])

    def test_graph_pattern_builder_multi_outputs(self):
        class AddAddAddAddPattern(org.GenericPattern):
            """Replaces ConstantOfShape + ScatterND with ScatterNDOfShape (com.domain)."""

            @classmethod
            def match_pattern(cls, op, x, y, w, z):
                """Builds the pattern to match."""
                tmp = op.Add(x, y)
                tmp2 = op.Add(tmp, w)
                r1 = op.Add(tmp, z)
                return tmp2, r1

            @classmethod
            def apply_pattern(cls, op, x, y, w, z):
                """Builds the pattern to match."""
                return op.AddAddAddAdd(x, y, w, z, domain="ZZZ", output_names=2)

            def validate_mapping(
                self,
                g: oir.Model,
                match_result: org.PatternMatchResult,
            ) -> bool:
                assert g
                assert len(match_result.model_nodes) == 3
                return True

        class AddAddAddAdd(OpRun):
            op_domain = "ZZZ"

            def _run(self, x, y, w, z):
                return (x + y + w, x + y + z)

        model = oh.make_model(
            oh.make_graph(
                [
                    oh.make_node("Add", ["x", "y"], ["gggg"]),
                    oh.make_node("Add", ["gggg", "w"], ["f1"]),
                    oh.make_node("Add", ["gggg", "z"], ["f2"]),
                ],
                "dummy",
                [
                    oh.make_tensor_value_info("x", TFLOAT, [None, None]),
                    oh.make_tensor_value_info("y", TFLOAT, [None, None]),
                    oh.make_tensor_value_info("z", TFLOAT, [None, None]),
                    oh.make_tensor_value_info("w", TFLOAT, [None, None]),
                ],
                [
                    oh.make_tensor_value_info("f1", TFLOAT, [None, None]),
                    oh.make_tensor_value_info("f2", TFLOAT, [None, None]),
                ],
            ),
            opset_imports=[oh.make_opsetid("", 18)],
            ir_version=9,
        )
        onnx.checker.check_model(model)

        ir_model = oir.irbuilder.build_ir(model)

        pattern = AddAddAddAddPattern(verbose=0)
        rule = pattern.make_rule()
        rule.apply_to_model(ir_model)
        self.assertEqual(
            ["AddAddAddAdd"],
            [n.op_type for n in ir_model.graph.nodes],
        )
        # TODO: do that in pattern.py.
        ir_model.version_map["ZZZ"] = 1

        builder = oip.ModelProtoBuilder()
        opt_onx = builder.visit_ir_model(ir_model)

        self.assertEqual(
            ["AddAddAddAdd"],
            [n.op_type for n in opt_onx.graph.node],
        )

        feeds = {
            "x": self._range(5, 6),
            "y": self._range(5, 6),
            "w": self._range(5, 6),
            "z": self._range(5, 6),
        }
        ref1 = ReferenceEvaluator(model)
        expected = ref1.run(None, feeds)

        self.assertEqual(0, len(opt_onx.graph.initializer))
        opsets = {v.domain: v.version for v in opt_onx.opset_import}
        self.assertIn("ZZZ", opsets)
        self.assertEqual(opsets["ZZZ"], 1)

        ref2 = ReferenceEvaluator(opt_onx, new_ops=[AddAddAddAdd])
        got = ref2.run(None, feeds)
        assert_almost_equal(expected[0], got[0])

    def check_with_ort(self, model: onnx.ModelProto, providers=None):
        import onnxruntime

        if hasattr(onnxruntime, "rewrite"):
            raise unittest.SkipTest(
                "cannot check with onnxruntime because of a subfolder called onnxruntime."
            )

        if providers is None:
            providers = ["CPUExecutionProvider"]

        if isinstance(model, onnx.ModelProto):
            model = model.SerializeToString()
        sess = onnxruntime.InferenceSession(model, providers=providers)
        return sess

    def get_rotary_model(self):
        inputs = [
            oh.make_tensor_value_info("x", onnx.TensorProto.INT64, shape=[]),
            oh.make_tensor_value_info("pos_ids", onnx.TensorProto.FLOAT, shape=[]),
            oh.make_tensor_value_info("axis", onnx.TensorProto.INT64, shape=[]),
        ]
        nodes = [
            oh.make_node("Unsqueeze", ["x", "axis"], ["_onx_unsqueeze0"]),
            oh.make_node("Cast", ["_onx_unsqueeze0"], ["_onx_cast0"], to=1),
            oh.make_node("MatMul", ["pos_ids", "_onx_cast0"], ["_onx_matmul0"]),
            oh.make_node("Transpose", ["_onx_matmul0"], ["_onx_transpose0"]),
            oh.make_node(
                "ConcatTraining",
                ["_onx_transpose0", "_onx_transpose0"],
                ["_onx_concattraining0", "_onx_concattraining1"],
                domain="com.microsoft",
            ),
            oh.make_node("Sin", ["_onx_concattraining0"], ["_onx_sin0"]),
            oh.make_node("Cast", ["_onx_sin0"], ["_onx_cast02"], to=1),
            oh.make_node("Cos", ["_onx_concattraining0"], ["_onx_cos0"]),
            oh.make_node("Cast", ["_onx_cos0"], ["_onx_cast03"], to=1),
        ]
        outputs = [
            oh.make_tensor_value_info("_onx_cast02", onnx.TensorProto.UNDEFINED, []),
            oh.make_tensor_value_info("_onx_cast03", onnx.TensorProto.UNDEFINED, []),
        ]
        model = oh.make_model(
            oh.make_graph(
                nodes,
                "experiment",
                inputs,
                outputs,
            ),
            opset_imports=[
                oh.make_opsetid("", 18),
                oh.make_opsetid("com.microsoft", 18),
            ],
        )
        return model

    def test_rotary_embedding(self):
        # The test work on a model if it has the expected name.
        # A dummy model is used if not present (not implemented yet).

        class RotaryEmbeddingPattern(org.GenericPattern):
            """Fusion for Rotary."""

            @classmethod
            def match_pattern(cls, op, x, pos_ids, axis):
                # original code: the code does verifies the constant yet
                # unsqueeze = op.Unsqueeze(x, [1])

                unsqueeze = op.Unsqueeze(x, axis)
                cast = op.Cast(unsqueeze, to=onnx.TensorProto.FLOAT)

                matmul = op.MatMul(pos_ids, cast)
                transpose = op.Transpose(matmul)
                output, length = op.ConcatTraining(
                    transpose,
                    transpose,
                    domain="com.microsoft",
                    output_names=2,
                )

                sin = op.Sin(output)
                cast1 = op.Cast(sin, to=onnx.TensorProto.FLOAT)
                cos = op.Cos(output)
                cast2 = op.Cast(cos, to=onnx.TensorProto.FLOAT)
                return cast1, cast2

            def validate_mapping(self, g, match_result) -> bool:
                # If some pattern needs to be rejected.
                del g
                del match_result
                return True

            @classmethod
            def apply_pattern(cls, op, x, pos_ids, axis):
                del axis
                cos_cache = op.Constant(
                    value=onh.from_array(np.random.rand(256, 256).astype(np.float16))
                )
                sin_cache = op.Constant(
                    value=onh.from_array(np.random.rand(256, 256).astype(np.float16))
                )
                return op.RotaryEmbedding(
                    x,
                    pos_ids,
                    cos_cache,
                    sin_cache,
                    domain="com.microsoft",
                    output_names=2,
                )

        model = self.get_rotary_model()

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            # back to ir
            ir_model = oir.irbuilder.build_ir(model)

            # starts matching
            pattern = RotaryEmbeddingPattern(verbose=10)
            rule = pattern.make_rule()
            rule.apply_to_model(ir_model)
            ir_model.version_map["com.microsoft"] = 1

            builder = oip.ModelProtoBuilder()
            opt_onx = builder.visit_ir_model(ir_model)

        expected = ["Constant", "Constant", "RotaryEmbedding"]
        self.assertEqual(expected, [n.op_type for n in opt_onx.graph.node])
        out = buffer.getvalue()
        self.assertIn("[GenericPattern.match", out)

    def test_rotary_embedding_onnxscript(self):
        # The test work on a model if it has the expected name.
        # A dummy model is used if not present (not implemented yet).
        import onnxscript

        op = onnxscript.opset18
        msft_op = onnxscript.values.Opset("com.microsoft", 1)

        def rotary_match_pattern(x, pos_ids, axis):
            unsqueeze = op.Unsqueeze(x, axis)
            cast = op.Cast(unsqueeze, to=onnx.TensorProto.FLOAT)

            matmul = op.MatMul(pos_ids, cast)
            transpose = op.Transpose(matmul)
            output, length = msft_op.ConcatTraining(transpose, transpose)

            sin = op.Sin(output)
            cast1 = op.Cast(sin, to=onnx.TensorProto.FLOAT)
            cos = op.Cos(output)
            cast2 = op.Cast(cos, to=onnx.TensorProto.FLOAT)
            return cast1, cast2

        def validate_rotary_mapping(g, match_result) -> bool:
            # If some pattern needs to be rejected.
            del g
            del match_result
            return True

        def rotary_apply_pattern(x, pos_ids, axis):
            cos_cache = op.Constant(
                value=onh.from_array(np.random.rand(256, 256).astype(np.float16))
            )
            sin_cache = op.Constant(
                value=onh.from_array(np.random.rand(256, 256).astype(np.float16))
            )
            part1, part2 = msft_op.RotaryEmbedding(x, pos_ids, cos_cache, sin_cache)
            return part1, part2

        model = self.get_rotary_model()

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            # back to ir
            ir_model = oir.irbuilder.build_ir(model)

            # starts matching
            rule = org.make_pattern_rule(
                rotary_match_pattern,
                rotary_apply_pattern,
                validate_rotary_mapping,
                verbose=10,
            )

            rule.apply_to_model(ir_model)
            ir_model.version_map["com.microsoft"] = 1

            builder = oip.ModelProtoBuilder()
            opt_onx = builder.visit_ir_model(ir_model)

        expected = ["Constant", "Constant", "RotaryEmbedding"]
        self.assertEqual(expected, [n.op_type for n in opt_onx.graph.node])
        out = buffer.getvalue()
        self.assertIn("[GenericPattern.match", out)

    def test_rotary_emb_file_onnxscript(self):
        # The test work on a model if it has the expected name.
        # A dummy model is used if not present (not implemented yet).
        import onnxscript

        op = onnxscript.opset18
        msft_op = onnxscript.values.Opset("com.microsoft", 1)

        def rotary_match_pattern(x, pos_ids, axis):
            unsqueeze = op.Unsqueeze(x, axis)
            cast = op.Cast(unsqueeze, to=onnx.TensorProto.FLOAT)

            matmul = op.MatMul(pos_ids, cast)
            transpose = op.Transpose(matmul)
            output, length = msft_op.ConcatTraining(transpose, transpose)

            sin = op.Sin(output)
            cast1 = op.Cast(sin, to=onnx.TensorProto.FLOAT)
            cos = op.Cos(output)
            cast2 = op.Cast(cos, to=onnx.TensorProto.FLOAT)
            return cast1, cast2

        def validate_rotary_mapping(g, match_result) -> bool:
            # If some pattern needs to be rejected.
            del g
            del match_result
            return True

        def rotary_apply_pattern(x, pos_ids, axis):
            cos_cache = op.Constant(
                value=onh.from_array(np.random.rand(256, 256).astype(np.float16))
            )
            sin_cache = op.Constant(
                value=onh.from_array(np.random.rand(256, 256).astype(np.float16))
            )
            part1, part2 = msft_op.RotaryEmbedding(x, pos_ids, cos_cache, sin_cache)
            return part1, part2

        model = "gemma_optimized_pre_grad_training_2.onnx"
        if not os.path.exists(model):
            raise unittest.SkipTest(f"{model!r} is missing")

        begin = time.perf_counter()
        onx = onnx.load(model)
        ir_model = oir.irbuilder.build_ir(onx)
        if __name__ == "__main__":
            print(f"Loading done in {time.perf_counter() - begin}s")

        begin = time.perf_counter()
        rule = org.make_pattern_rule(
            rotary_match_pattern,
            rotary_apply_pattern,
            validate_rotary_mapping,
            verbose=10,
        )

        rule.apply_to_model(ir_model)

        if __name__ == "__main__":
            print(f"Matching done in {time.perf_counter() - begin}s")

        # TODO: do that in pattern.py.
        ir_model.version_map["ZZZ"] = 1

        begin = time.perf_counter()
        builder = oip.ModelProtoBuilder()
        opt_onx = builder.visit_ir_model(ir_model)
        if __name__ == "__main__":
            print(f"Building done in {time.perf_counter() - begin}s")

        begin = time.perf_counter()
        buffer = opt_onx.SerializeToString()
        with open(f"{model}.opt.onnx", "wb") as f:
            f.write(buffer)
        if __name__ == "__main__":
            print(f"Saving done in {time.perf_counter() - begin}s")
        self.check_with_ort(opt_onx)

    def test_transpose_transpose_onnxscript(self):
        # The test work on a model if it has the expected name.
        # A dummy model is used if not present (not implemented yet).
        transpose_transpose_pattern = oh.make_function(
            "any",
            "transpose_transpose_pattern",
            ["X"],
            ["Y"],
            [
                oh.make_node("Transpose", ["X"], ["xt"]),
                oh.make_node("Transpose", ["xt"], ["Y"]),
            ],
            [oh.make_opsetid("", 18)],
        )

        def transpose_transpose_mapping(g, match_result) -> bool:
            # If some pattern needs to be rejected.
            del g
            perms = []
            for n in match_result.model_nodes:
                perms.append(list(n.attribute[0].ints))
            perm = perms[0]
            new_perm = [0 for p in perm]
            for i, p in enumerate(perms[1]):
                new_perm[i] = perm[p]
            match_result.add_kwargs("perm", new_perm)
            return True

        def transpose_transpose_apply_pattern(x, perm=None):
            if perm is None:
                return oh.make_function(
                    "any",
                    "id",
                    ["X"],
                    ["Y"],
                    [
                        oh.make_node("Identity", ["X"], ["Y"]),
                    ],
                    [oh.make_opsetid("", 18)],
                )
            return oh.make_function(
                "any",
                "id",
                ["X"],
                ["Y"],
                [
                    oh.make_node("Transpose", ["X"], ["Y"], perm=perm),
                ],
                [oh.make_opsetid("", 18)],
            )

        model = oh.make_model(
            oh.make_graph(
                [
                    oh.make_node("Transpose", ["X"], ["xt"], perm=[1, 2, 0]),
                    oh.make_node("Transpose", ["xt"], ["Y"], perm=[1, 2, 0]),
                ],
                "name",
                [oh.make_tensor_value_info("X", TFLOAT, [None, None, None])],
                [oh.make_tensor_value_info("Y", TFLOAT, [None, None, None])],
            ),
            opset_imports=[oh.make_opsetid("", 18)],
        )

        # back to ir
        ir_model = oir.irbuilder.build_ir(model)

        # starts matching
        rule = org.make_pattern_rule(
            transpose_transpose_pattern,
            transpose_transpose_apply_pattern,
            transpose_transpose_mapping,
            verbose=0,
            use_onnxscript=False,
        )

        rule.apply_to_model(ir_model)

        builder = oip.ModelProtoBuilder()
        opt_onx = builder.visit_ir_model(ir_model)

        expected = ["Transpose"]
        self.assertEqual(expected, [n.op_type for n in opt_onx.graph.node])
        node = opt_onx.graph.node[0]
        self.assertEqual(len(node.attribute), 1)
        att = node.attribute[0]
        self.assertEqual(att.name, "perm")
        self.assertEqual(list(att.ints), [2, 0, 1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
