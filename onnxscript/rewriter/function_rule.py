# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
from __future__ import annotations

import functools
import logging
from typing import Callable

import onnx
from packaging import version

import onnxscript
from onnxscript import ir
from onnxscript.rewriter import pattern

logger = logging.getLogger(__name__)


class FunctionRewriteError(RuntimeError): ...


@functools.lru_cache
def parse_domain(function_domain: str) -> tuple[str, version.Version | None]:
    splits = function_domain.split(".")
    if splits[0] != "pkg":
        raise FunctionRewriteError(
            f"Invalid domain: {function_domain}. Must start with 'pkg'."
        )
    splits = splits[1:]
    for i, s in enumerate(splits):
        if s.isdigit():
            return ".".join(splits[:i]), version.parse(".".join(splits[i:]))
    return ".".join(splits), None


MIN_VERSION = version.parse("0")
MAX_VERSION = version.parse("9999")


class VersionController:
    def __init__(self):
        # A dispatch table for rewrite implementation based on the function package version.
        self.dispatch_table: dict[tuple[version.Version, version.Version], Callable] = {}

    def register_version(
        self,
        min_version: version.Version | str | None = None,
        max_version: version.Version | str | None = None,
    ):
        """Register a function implementation for a specific package version range [min_version, max_version).

        Args:
            min_version: The minimum version of the package. Inclusive.
            max_version: The maximum version of the package. Exclusive.
        """
        # TODO: check for version overloap

        min_version = MIN_VERSION if min_version is None else min_version
        max_version = MAX_VERSION if max_version is None else max_version
        if isinstance(min_version, str):
            min_version = version.parse(min_version)
        if isinstance(max_version, str):
            max_version = version.parse(max_version)

        def deco(func):
            self.dispatch_table[(min_version, max_version)] = func
            return func

        return deco

    def dispatch(self, version: version.Version | None) -> Callable | None:
        if version is None:
            if len(self.dispatch_table) == 1:
                return next(iter(self.dispatch_table.values()))
            raise ValueError(
                "No function package version specified, however there are multiple "
                f"fusion rules based on package version: {self.dispatch_table.keys()}."
            )
        for (min_version, max_version), func in self.dispatch_table.items():
            greater_than_min = min_version is None or min_version <= version
            less_than_max = max_version is None or version < max_version
            if greater_than_min and less_than_max:
                return func
        return None


class FunctionRewriteRule(pattern.RewriteRule):
    FUNCTION_KEYWORD: str | tuple[str]
    PACKAGE_NAME: str
    _opset_imports: dict[str, int]
    onnx_opset: onnxscript.values.Opset

    def __init__(self, opset: onnxscript.values.Opset = onnxscript.opset18) -> None:
        self.onnx_opset = opset

    def _match_function(self, function: ir.Function, pkg_name: str) -> bool:
        print("----> Checking function:", function.name, "in package:", pkg_name)
        if pkg_name != self.PACKAGE_NAME:
            logger.info(
                "Rule %s did not match function %s::%s. Package name mismatch '%s' != '%s'.",
                self.__class__.__name__,
                function.domain,
                function.name,
                self.PACKAGE_NAME,
                pkg_name,
            )
            return False
        if isinstance(self.FUNCTION_KEYWORD, str):
            match = function.name.find(self.FUNCTION_KEYWORD) != -1
            print(f"----> Function name '{function.name}' match with '{self.FUNCTION_KEYWORD}': {match}")
            return match
        elif isinstance(self.FUNCTION_KEYWORD, tuple):
            match = any(function.name.find(keyword) != -1 for keyword in self.FUNCTION_KEYWORD)
            print(f"----> Function name '{function.name}' match with any of '{self.FUNCTION_KEYWORD}': {match}")
            return match
        else:
            raise ValueError(
                f"Function keyword must be str or tuple, got {self.FUNCTION_KEYWORD}"
            )

    def _find_node_contains_key_in_name(
        self, function: onnx.FunctionProto, keyword: str
    ) -> onnx.NodeProto | None:
        for node in function.node:
            if node.name.find(keyword) != -1:
                return node
        return None

    def _find_function_by_name(
        self, function: ir.Function, keyword: str
    ) -> ir.Function | None:
        for node in function:
            if node.name.find(keyword) != -1:
                return node
        return None

    def _find_node_by_type(
        self, function: ir.Function, domain: str, op_type: str
    ) -> ir.Node | None:
        for node in function:
            if node.domain == domain and node.op_type == op_type:
                return node
        return None

    def compose_new_function(
        self, old_function: ir.Function, pkg_version: version.Version | None
    ) -> ir.Function:
        print("----> (2) pkg_version", pkg_version, "old_function", old_function.name)
        func = self._version_controller.dispatch(pkg_version)
        if func is not None:
            print("----> (2.5) Dispatch function found, applying...")
            new_function = func(self, old_function)
            print("----> (2.6) New function created.")
            return new_function
        raise FunctionRewriteError(
            f"No rewrite implementation for package version {pkg_version}."
        )

    def try_rewrite_function(
        self, function: ir.Function
    ) -> tuple[ir.OperatorIdentifier, ir.Function] | None:
        try:
            pkg_name, pkg_version = parse_domain(function.domain)
            print("----> (1) Parsed domain, pkg_name:", pkg_name, "pkg_version:", pkg_version)
        except FunctionRewriteError as e:
            logger.warning("Could not parse domain: %s", e)
            return None

        if pkg_version is None and not pkg_name.startswith("onnxscript"):
            logger.warning(
                "Could not parse version for domain of function %s::%s. "
                "Usually this implies the model source is not from a package, but from arbitrary python files instead. "
                "For example, models not defined in huggingface/transformers but loaded via 'trust_remote_code=True'.",
                function.domain,
                function.name,
            )

        if not self._match_function(function, pkg_name):
            print("----> (1.5) Function does not match.")
            return None
        logger.info(
            "Rule %s matched function %s::%s",
            self.__class__.__name__,
            function.domain,
            function.name,
        )
        print("----> (1.6) Function matched.")
        try:
            new_function = self.compose_new_function(function, pkg_version)
        except FunctionRewriteError as e:
            logger.warning("Could not rewrite function: %s", e)
            return None

        if not hasattr(new_function, 'name'):
            logger.error("new_function does not have a 'name' attribute. Received: %s", type(new_function))
            return None

        new_function.name = function.name
        new_function.domain = function.domain

        return function.identifier(), new_function

    def try_rewrite(self, model: ir.Model, value) -> bool:
        raise NotImplementedError(
            "Use try_rewrite_function instead for function based rewrites."
        )

    def apply_to_model(
        self, model: ir.Model, *, commute: bool = False
    ) -> tuple[int, ir.Model]:
        del commute

        old_function_to_new_function: dict[ir.OperatorIdentifier, ir.Function] = {}
        for function in model.functions.values():
            rewrite_or_none = self.try_rewrite_function(function)
            if rewrite_or_none is not None:
                old_function_to_new_function[rewrite_or_none[0]] = rewrite_or_none[1]
        model = self.update_to_new_function(model, old_function_to_new_function)
        return len(old_function_to_new_function), model

    def update_to_new_function(
        self,
        model: ir.Model,
        old_function_to_new_function: dict[ir.OperatorIdentifier, ir.Function],
    ) -> ir.Model:
        for old_function_id, new_function_ir in old_function_to_new_function.items():
            model.functions[old_function_id] = new_function_ir
            for new_opset, opset_version in new_function_ir.opset_imports.items():
                if new_opset not in model.opset_imports:
                    model.opset_imports[new_opset] = opset_version
        return model

    def count_matches(self, model, *, commute: bool = False) -> int:
        raise NotImplementedError()

    def commute(self) -> list[pattern.RewriteRule]:
        raise NotImplementedError()
