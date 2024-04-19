import logging
import unittest

import numpy as np
import onnx.parser

from onnxscript import ir
from onnxscript.rewriter import _ir_utils, cast_constant_of_shape, pattern

logger = logging.getLogger(__name__)
op = pattern.onnxop
msft_op = pattern.msft_op


class ReciprocalMulTest(unittest.TestCase):
    def rule(self) -> pattern.RewriteRule:
        def reciprocal_mul_pattern(x, y):
            return (1 / x) * y

        def div(x, y):
            return y / x

        return pattern.RewriteRule(reciprocal_mul_pattern, div)

    def test_single_match(self):
        model_proto = onnx.parser.parse_model(
            """
            <ir_version: 7, opset_import: [ "" : 17]>
            agraph (float[N] x, float[N] y) => (float[N] z)
            {
                c1 = Constant<value_float = 1.0>()
                t1 = Div(c1, x)
                z1 = Mul(t1, y)
                z = Identity(z1)
            }
        """
        )
        model = ir.serde.deserialize_model(model_proto)
        count = self.rule().apply_to_model(model)
        self.assertEqual(count, 1)
        self.assertEqual(len(model.graph), 3)

    def test_failed_match(self):
        model_proto = onnx.parser.parse_model(
            """
            <ir_version: 7, opset_import: [ "" : 17]>
            agraph (float[N] x, float[N] y) => (float[N] z)
            {
                c1 = Constant<value_float = 0.9>()
                t1 = Div(c1, x)
                z1 = Mul(t1, y)
                z = Identity(z1)
            }
        """
        )
        model = ir.serde.deserialize_model(model_proto)
        count = self.rule().apply_to_model(model)
        self.assertEqual(count, 0)
        self.assertEqual(len(model.graph), 4)

    def test_multiple_matches(self):
        model_proto = onnx.parser.parse_model(
            """
            <ir_version: 7, opset_import: [ "" : 17]>
            agraph (float[N] x, float[N] y) => (float[N] z)
            {
                # {c1, t1, z1} is a valid match
                # {c2, t2, z2} is a valid match
                # {c3, t3, z3} is a match, but cannot be replaced since t3 has other-uses.
                c1 = Constant<value_float = 1.0>()
                c2 = Constant<value_float = 1.0>()
                t2 = Div(c2, y)
                t1 = Div(c1, x)
                z1 = Mul(t1, y)
                z2 = Mul(t2, z1)

                c3 = Constant<value_float = 1.0>()
                t3 = Div(c3, x)
                z3 = Mul(t3, y)
                reuse_t3 = Div(t3, x)
                z = Add(z2, reuse_t3)
            }
        """
        )
        model = ir.serde.deserialize_model(model_proto)
        count = self.rule().apply_to_model(model)
        self.assertEqual(count, 2)
        self.assertEqual(len(model.graph), 9)


class FastGeluTest(unittest.TestCase):
    def rule(self) -> pattern.RewriteRule:
        def fast_gelu_pattern1(x):
            b = 0.044715
            c = 0.79788
            tanh = op.Tanh(c * (x + (x**3) * b))
            return (1.0 + tanh) * (0.5 * x)

        def fast_gelu(x):
            return msft_op.FastGelu(x)

        return pattern.RewriteRule(fast_gelu_pattern1, fast_gelu)

    def long_form_rule(self) -> pattern.RewriteRule:
        def fast_gelu_pattern1_long(x):
            three = pattern.Constant(3)
            x_cube = op.Pow(x, three)
            b = pattern.Constant(0.044715)
            x_cube_mul_b = op.Mul(x_cube, b)  # support OR op.Mul(B, x_cube)
            sum_ = op.Add(x, x_cube_mul_b)
            c = pattern.Constant(0.79788)
            c_times_sum = op.Mul(c, sum_)
            tanh = op.Tanh(c_times_sum)
            one = pattern.Constant(1.0)
            one_plus_tanh = op.Add(one, tanh)
            half = pattern.Constant(0.5)
            half_x = op.Mul(half, x)
            return op.Mul(one_plus_tanh, half_x)

        def fast_gelu(x):
            return msft_op.FastGelu(x)

        return pattern.RewriteRule(fast_gelu_pattern1_long, fast_gelu)

    def _check(self, rule):
        model_proto = onnx.parser.parse_model(
            """
            <ir_version: 7, opset_import: [ "" : 17]>
            agraph (float[N] x, float[N] y) => (float[N] z)
            {
                three = Constant <value_int=3>()
                x_cube = Pow(x, three)
                B = Constant <value_float=0.044715>()
                x_cube_mul_B = Mul(x_cube, B)
                sum = Add(x, x_cube_mul_B)
                C = Constant <value_float=0.79788>()
                C_times_sum = Mul(C, sum)
                tanh = Tanh(C_times_sum)
                one = Constant <value_float=1.0> ()
                one_plus_tanh = Add(one, tanh)
                half = Constant <value_float=0.5> ()
                half_x = Mul(half, x)
                z = Mul(one_plus_tanh, half_x)
            }
        """
        )
        model = ir.serde.deserialize_model(model_proto)
        count = rule.apply_to_model(model)
        self.assertEqual(count, 1)
        # 5 Constant nodes and 1 FastGelu node
        self.assertEqual(len(model.graph), 6)

    def test_short_rule(self):
        self._check(self.rule())

    def test_long_rule(self):
        self._check(self.long_form_rule())


class ConcatTest(unittest.TestCase):
    def rule(self) -> pattern.RewriteRule:
        def concat_pattern(x, y, axis):
            seq = op.SequenceConstruct(x, y)
            return op.ConcatFromSequence(seq, axis=axis)

        def concat(x, y, axis):
            return op.Concat(x, y, axis=axis)

        return pattern.RewriteRule(concat_pattern, concat)

    def test_concat(self):
        model_proto = onnx.parser.parse_model(
            """
            <ir_version: 7, opset_import: [ "" : 17]>
            agraph (float[N] x, float[N] y) => (float[M] z)
            {
                t = SequenceConstruct (x, y)
                z = ConcatFromSequence <axis=0> (t)
            }
        """
        )
        model = ir.serde.deserialize_model(model_proto)
        count = self.rule().apply_to_model(model)
        self.assertEqual(count, 1)
        self.assertEqual(len(model.graph), 1)

    def test_concat_in_function(self):
        model_proto = onnx.parser.parse_model(
            """
            <ir_version: 7, opset_import: [ "" : 17, "pkg.custom": 1]>
            agraph (float[N] x, float[M] y) => (float[Z] z)
            {
                z = afunction (x, y)
            }
            <domain: "pkg.custom", opset_import: [ "" : 17]>
            afunction (x, y) => (z)
            {
                t = SequenceConstruct (x, y)
                z = ConcatFromSequence <axis=0> (t)
            }
        """
        )
        model = ir.serde.deserialize_model(model_proto)
        count = self.rule().apply_to_model(model)
        self.assertEqual(count, 1)
        self.assertEqual(len(model.functions), 1)
        self.assertEqual(len(model.functions[("pkg.custom", "afunction", "")]), 1)
        self.assertEqual(model.functions[("pkg.custom", "afunction", "")][0].op_type, "Concat")


class RewriteRuleTest(unittest.TestCase):
    def test_commute(self):
        def add_0(x):
            return x + 0

        def identity(x):
            return op.Identity(x)

        add_0_rule = pattern.RewriteRule(add_0, identity)

        model_proto = onnx.parser.parse_model(
            """
            <ir_version: 7, opset_import: [ "" : 17]>
            agraph (float[N] x) => (float[M] z)
            {
                zero = Constant <value_float=0.0> ()
                z = Add (zero, x)
            }
        """
        )
        model = ir.serde.deserialize_model(model_proto)
        count = pattern.RewriteRuleSet([add_0_rule], commute=True).apply_to_model(model)
        optimized_model = ir.serde.serialize_model(model)
        self.assertEqual(count, 1)
        nodes = optimized_model.graph.node
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[1].op_type, "Identity")

    def test_const_value(self):
        def reshape(x, newshape):
            return op.Reshape(x, newshape)

        def identity(x, newshape):
            del newshape  # Unused
            return op.Identity(x)

        def _check_for_redundant_reshape(x, newshape):
            oldshape = x.shape
            newshape = _ir_utils.propagate_const_value(newshape)
            newshape = _ir_utils.get_numpy_from_ir_value(newshape)
            if not isinstance(newshape, np.ndarray):
                return False
            newshape = newshape.tolist()

            if len(oldshape) != len(newshape):
                return False
            return all(not (d1 != d2 and d2 != -1) for d1, d2 in zip(oldshape, newshape))  # pylint: disable=consider-using-in

        def check_for_redundant_reshape(bindings):
            return _check_for_redundant_reshape(**bindings)

        rule = pattern.RewriteRule(reshape, identity, check_for_redundant_reshape)

        model_proto = onnx.parser.parse_model(
            """
            <ir_version: 7, opset_import: [ "" : 17]>
            agraph (float[10, 20, 30] x) => (float[10, 20, 30] z)
            {
                shape = Constant <value_ints=[10, 20, 30]> ()
                z = Reshape (x, shape)
            }
        """
        )
        model = ir.serde.deserialize_model(model_proto)
        count = pattern.RewriteRuleSet([rule]).apply_to_model(model)
        optimized_model = ir.serde.serialize_model(model)
        self.assertEqual(count, 1)
        nodes = optimized_model.graph.node
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[1].op_type, "Identity")

    def test_delayed_run_provides_correct_bindings_for_multiple_matches(self):
        model_proto = onnx.parser.parse_model(
            """
            <ir_version: 7, opset_import: [ "" : 17]>
            agraph (int64[2] input_x) => (float16[1, 4] output, float[1, 4] output2)
            {
                constant = ConstantOfShape <value: tensor = float[1] {1.}>(input_x)
                output = Cast <to = 10> (constant)
                constant2 = ConstantOfShape <value: tensor = float[1] {1.}>(input_x)
                output2 = Cast <to = 1> (constant2)
            }
            """
        )
        model = ir.serde.deserialize_model(model_proto)
        count = cast_constant_of_shape.rules.apply_to_model(model)
        self.assertEqual(count, 2)
        self.assertEqual(len(model.graph), 2)
        self.assertEqual(model.graph[0].attributes["value"].value.dtype, 10)
        self.assertEqual(model.graph[1].attributes["value"].value.dtype, 1)


if __name__ == "__main__":
    unittest.main()
