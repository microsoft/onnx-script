# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# --------------------------------------------------------------------------


import copy
import dataclasses
import numbers
import unittest
import warnings
from typing import Any, List, Optional, Union

import numpy as np
import onnx
import onnx.backend.test.case.node as node_test
from onnx import ModelProto
from onnx.onnx_cpp2py_export.checker import ValidationError
from onnxruntime import InferenceSession
from onnxruntime.capi.onnxruntime_pybind11_state import (
    Fail,
    InvalidArgument,
    InvalidGraph,
)

import onnxscript
from onnxscript import utils


@dataclasses.dataclass(repr=False, eq=False)
class FunctionTestParams:
    function: onnxscript.OnnxFunction
    input: Union[list, dict]
    output: list
    attrs: dict = None


class OnnxScriptTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # A function (and node) in a model tells its domain, not version.
        # When building a model that consumes functions and nodes, model opset_imports
        # indicate domains and versions of nodes and functions that are used.
        # Function version number is needed for a runtime to run it without inlining.
        # Before ONNX IR (or FunctionIR) being updated
        # for FunctionProto to have version number we
        # need to put a default version number here to workaround the problem.
        cls.local_function_opset_version = 1
        cls.atol = 1e-7
        cls.rtol = 1e-7
        try:
            # experimental version
            cls.all_test_cases = node_test.collect_testcases()
        except TypeError:
            # official version
            cls.all_test_cases = node_test.collect_testcases(None)

    def _create_model_from_param(
        self, param: FunctionTestParams, onnx_case_model: ModelProto
    ) -> ModelProto:
        local_function_proto = param.function.function_ir.to_function_proto("")
        if not onnx_case_model:
            input_names = [f"input_{str(i)}" for i in range(len(param.input))]
            output_names = [f"output_{str(i)}" for i in range(len(param.output))]
            input_value_infos = utils.values_to_value_infos(input_names, param.input)
        elif len(onnx_case_model.graph.input) == len(local_function_proto.input) and all(
            [i != "" for i in onnx_case_model.graph.input]
        ):
            # we want to create a model that onnx_test_runner
            # can run with onnx test case data
            input_names = [i.name for i in onnx_case_model.graph.input]
            output_names = [o.name for o in onnx_case_model.graph.output]
            input_value_infos = utils.values_to_value_infos(input_names, param.input)
        else:
            # in an onnx test case, an optional input with missing input data
            # is dropped, if it is a tailing input, and otherwise the input is named "".
            # a models from script keeps all optional inputs,
            # to run script model with onnx test data, we need to map input test data
            # to the corresponding script model input.
            # take Clip test case for example:
            # clip function input is like: ["input", "min2", "max2"]
            # (1) when min is missing, the test_case_model is ["x", "", "max"]
            #   in this case we want to create a model with input being: ["x", "min", "max"]
            #   input feed: {x: ?, min: None, max: ?} # ? is a np.array
            # (2) when max is missing, the test_case_model is ["x", "min"]
            #   in this case we want to create a model with input being: ["x", "min", "max2"]
            #   input feed: {x: ?, min: ?, max: None} # ? is a np.array

            # there is another issue: when input data is missing,
            # there is not way from the onnx test case's model and feed to get TypeProto
            # in order to build a model.
            # we have to resolve the TypeProto from script function.
            local_function_model_proto = param.function.function_ir.to_model_proto()
            input_value_infos = []
            for i, input in enumerate(local_function_model_proto.graph.input):
                vi = copy.deepcopy(input)
                if (
                    i < len(onnx_case_model.graph.node[0].input)
                    and onnx_case_model.graph.node[0].input[i] != ""
                ):
                    vi.name = onnx_case_model.graph.node[0].input[i]
                else:
                    vi.name = input.name
                input_value_infos.append(vi)

            output_names = [o.name for o in onnx_case_model.graph.output]

        output_value_infos = utils.values_to_value_infos(output_names, param.output)

        return utils.make_model_from_function_proto(
            local_function_proto,
            self.local_function_opset_version,
            input_value_infos,
            output_value_infos,
            **(param.attrs or {}),
        )

    def _filter_test_case_by_op_type(self, op_type):
        test_cases = [
            case
            for case in self.all_test_cases
            if (
                case.kind == "node"
                and len(case.model.graph.node) == 1
                and case.model.graph.node[0].op_type == op_type
            )
        ]
        return test_cases

    def run_converter_test(
        self, param: FunctionTestParams, onnx_case_model: ModelProto = None
    ):
        # we need the latest version in onnx.ai domain
        # to build a function
        if onnx_case_model:
            model = self._create_model_from_param(param, onnx_case_model)
        else:
            model = param.function.function_ir.to_model_proto(producer_name="call_clip")
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
                raise AssertionError("Verification of model failed.") from e

        if isinstance(param.input, dict):
            input = param.input
        else:
            # onnx_case_model is provided with testing with onnx test cases.
            if onnx_case_model:
                input = {}
                feed_index = 0
                for i, model_input in enumerate(model.graph.input):
                    # take care of ["x", "", "max"] and ["x", "min"] cases
                    if (
                        feed_index < len(param.input)
                        and onnx_case_model.graph.node[0].input[i] != ""
                    ):
                        input[model_input.name] = (
                            np.array(param.input[feed_index])
                            if isinstance(param.input[feed_index], numbers.Number)
                            else param.input[feed_index]
                        )
                        feed_index += 1
                    else:
                        input[model_input.name] = None
            else:
                input = {
                    vi.name: np.array(t) if isinstance(t, numbers.Number) else t
                    for vi, t in zip(model.graph.input, param.input)
                }
        try:
            sess = InferenceSession(
                model.SerializeToString(), providers=["CPUExecutionProvider"]
            )
        except (Fail, InvalidArgument, InvalidGraph) as e:
            raise AssertionError(f"Unable to load model\n{str(model)}") from e
        # input['input_2'] = None
        actual = sess.run(None, input)
        np.testing.assert_allclose(actual, param.output, rtol=self.rtol)

    def run_eager_test(
        self, param: FunctionTestParams, rtol: float = None, atol: float = None
    ):
        actual = param.function(*param.input, **(param.attrs or {}))
        np.testing.assert_allclose(
            actual if isinstance(actual, list) else [actual],
            param.output,
            rtol=rtol or self.rtol,
            atol=atol or self.atol,
        )

    def run_onnx_test(
        self,
        function: onnxscript.OnnxFunction,
        rtol: float = None,
        atol: float = None,
        skip_eager_test: bool = False,
        skip_test_names: Optional[List[str]] = None,
        **attrs: Any,
    ) -> None:
        """Run ONNX test cases with an onnxscript.OnnxFunction.
        The function shall have test cases in ONNX repo.
        For example: in onnx/test/case/node.
        Test case models and data are used to do converter and eager mode test.

        Arguments:
            function (onnxscript.OnnxFunction): the function to be tested.
            skip_eager_test (bool): not to run eager test if Ture.
            skip_test_names (List[str]): to skip these tests.
            attrs (Any): default attributes of the function node.

        """
        if skip_test_names is None:
            skip_test_names = []

        cases = self._filter_test_case_by_op_type(function.function_ir.name)
        for case in cases:
            if len(case.model.graph.node) != 1:
                raise ValueError(
                    "run_onnx_test only \
                    tests models with one operator node."
                )

            if case.name not in skip_test_names:
                test_case_attrs = {
                    a.name: onnx.helper.get_attribute_value(a)
                    for a in case.model.graph.node[0].attribute
                }
                test_case_attrs = {**attrs, **test_case_attrs}

                for ds in case.data_sets:
                    param = FunctionTestParams(function, ds[0], ds[1], attrs=test_case_attrs)
                    self.run_converter_test(param, case.model)
                    if not skip_eager_test:
                        self.run_eager_test(param, rtol=rtol, atol=atol)
