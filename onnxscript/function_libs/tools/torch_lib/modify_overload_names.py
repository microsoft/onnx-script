from __future__ import annotations

import enum
import os
import pathlib
import pprint
from typing import Dict, List, Set, Tuple

import libcst as cst
from libcst import matchers
from libcst._nodes.statement import FunctionDef

from onnxscript.function_libs.torch_lib import registration


class _StatusEnum(enum.Enum):
    SUCCESS = enum.auto()
    """Success."""
    FAILURE_OVERLOAD_EXIST = enum.auto()
    """Failure: overload name already exists."""
    FAILURE_OVERLOAD_INVALID = enum.auto()
    """Failure: overload name is invalid."""
    FAILURE_OP_NOT_FOUND = enum.auto()
    """Failure: op not found."""
    FAILURE_OP_MULTIPLE_IMPL = enum.auto()
    """Failure: op has multiple implementations. Cannot decide which to add new overload name to."""


def _cst_arg_to_overload_names(arg: cst.Arg) -> Tuple[str, ...]:
    if matchers.matches(arg, matchers.Arg(value=matchers.SimpleString())):
        overload_names = (cst.ensure_type(arg.value, cst.SimpleString).value,)
    else:
        overload_names = tuple(
            cst.ensure_type(element.value, cst.SimpleString).value
            for element in cst.ensure_type(arg.value, cst.Tuple).elements
        )
    overload_names = tuple(name.replace('"', "") for name in overload_names)
    return overload_names


def _overload_names_to_namespace_op(overload_names: Tuple[str, ...]) -> str:
    match = registration._QUALIFIED_OPERATOR_NAME_REGEX.fullmatch(overload_names[0])
    assert match is not None
    namespace = match.group("namespace")
    name = match.group("name")
    return f"{namespace}::{name}"


class _TorchlibOpOverloadCollector(cst.CSTVisitor):
    def __init__(self):
        self._op_overloads: Dict[str, List[Tuple[str, List[str]]]] = {}
        self._stack: List[str] = []

    def visit_FunctionDef(self, node: FunctionDef) -> bool | None:
        self._stack.append(node.name.value)

    def leave_FunctionDef(self, node: FunctionDef) -> None:
        self._stack.pop()

    def visit_Call(self, node: cst.Call) -> None:
        if not matchers.matches(node.func, matchers.Name("torch_op")):
            return

        # skip private ops
        if any(
            matchers.matches(
                arg,
                matchers.Arg(value=matchers.Name("True"), keyword=matchers.Name("private")),
            )
            for arg in node.args
        ):
            return

        function_name = self._stack[-1]
        overload_names = _cst_arg_to_overload_names(node.args[0])
        namespace_op_name = _overload_names_to_namespace_op(overload_names)

        self._op_overloads.setdefault(namespace_op_name, [])
        self._op_overloads[namespace_op_name].append((function_name, list(overload_names)))


class _TorchlibOpOverloadAdder(cst.CSTTransformer):
    def __init__(
        self,
        overload_names: Dict[str, List[Tuple[str, List[str]]]],
        new_overload_names: Set[str],
    ):
        self._overload_names = overload_names
        self._results: Dict[str, _StatusEnum] = {}

        for new_overload_name in new_overload_names:
            match = registration._QUALIFIED_OPERATOR_NAME_REGEX.fullmatch(new_overload_name)
            if not match:
                self._results[new_overload_name] = _StatusEnum.FAILURE_OVERLOAD_INVALID
                continue
            overload = match.group("overload") or ""
            if overload == "default":
                overload = ""
            dot_overload = f".{overload}" if overload else ""
            op_name = match.group("name")
            namespace = match.group("namespace")
            namespace_op_name = f"{namespace}::{op_name}"
            qualified_name = f"{namespace_op_name}{dot_overload}"

            if namespace_op_name not in self._overload_names:
                self._results[new_overload_name] = _StatusEnum.FAILURE_OP_NOT_FOUND
                continue

            if len(self._overload_names[namespace_op_name]) > 1:
                self._results[new_overload_name] = _StatusEnum.FAILURE_OP_MULTIPLE_IMPL
                continue

            if qualified_name in self._overload_names[namespace_op_name][0][1]:
                self._results[new_overload_name] = _StatusEnum.FAILURE_OVERLOAD_EXIST
                continue

            self._overload_names[namespace_op_name][0][1].append(qualified_name)
            self._results[new_overload_name] = _StatusEnum.SUCCESS

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        if not matchers.matches(original_node.func, matchers.Name("torch_op")):
            return original_node

        # skip private ops
        if any(
            matchers.matches(
                arg,
                matchers.Arg(value=matchers.Name("True"), keyword=matchers.Name("private")),
            )
            for arg in original_node.args
        ):
            return original_node

        original_overload_names = _cst_arg_to_overload_names(original_node.args[0])
        namespace_op_name = _overload_names_to_namespace_op(original_overload_names)
        overload_names = self._overload_names[namespace_op_name][0][1]
        if len(overload_names) == 1:
            return original_node
        return updated_node.with_changes(
            args=[
                cst.Arg(
                    value=cst.Tuple(
                        elements=[
                            cst.Element(cst.SimpleString(value=f'"{name}"'))
                            for name in overload_names
                        ]
                    )
                ),
                *original_node.args[1:],
            ],
        )


def add_overload_names(
    module_path: pathlib.Path, overload_names: Set[str]
) -> Dict[str, _StatusEnum]:
    """NOTE: This function assumes"""
    source_tree = cst.parse_module(module_path.read_text())
    op_overload_collector = _TorchlibOpOverloadCollector()
    source_tree.visit(op_overload_collector)
    transformer = _TorchlibOpOverloadAdder(op_overload_collector._op_overloads, overload_names)
    modified_tree = source_tree.visit(transformer)
    module_path.write_text(modified_tree.code)
    return transformer._results


def main():
    new_overload_names_from_bench = {
        "aten.add.Tensor": 35510,
        "aten.bitwise_and.Tensor": 12,
        "aten.clamp.Tensor": 2690,
        "aten.div.Tensor": 10622,
        "aten.div.Tensor_mode": 2,
        "aten.empty.memory_format": 12486,
        "aten.eq.Scalar": 72,
        "aten.eq.Tensor": 112,
        "aten.fill.Tensor": 28,
        "aten.ge.Scalar": 4,
        "aten.ge.Tensor": 4,
        "aten.gt.Scalar": 46,
        "aten.le.Tensor": 32,
        "aten.lt.Scalar": 80,
        "aten.masked_fill.Scalar": 360,
        "aten.masked_fill.Tensor": 396,
        "aten.mul.Tensor": 24214,
        "aten.ne.Scalar": 630,
        "aten.pow.Tensor_Scalar": 528,
        "aten.pow.Tensor_Tensor": 1820,
        "aten.rsub.Scalar": 354,
        "aten.scatter_reduce.two": 18,
        "aten.select.int": 4669,
        "aten.slice.Tensor": 17717,
        "aten.split.Tensor": 3182,
        "aten.sub.Tensor": 7868,
        "aten.sum.dim_IntList": 6122,
        "aten.transpose.int": 13219,
        "aten.unbind.int": 1188,
        "aten.where.self": 732,
    }
    new_overload_names = set(
        {k.replace("aten.", "aten::") for k in new_overload_names_from_bench}
    )
    file_paths = [
        pathlib.Path(os.path.join(root, file))
        for root, dirs, files in os.walk("onnxscript/function_libs/torch_lib/ops")
        for file in files
    ]
    for file_path in file_paths:
        print("Processing file:", file_path)
        pprint.pprint(add_overload_names(file_path, new_overload_names))


if __name__ == "__main__":
    main()
