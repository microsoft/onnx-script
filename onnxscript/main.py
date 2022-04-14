from types import ModuleType
import ast
import inspect
from .converter import Converter
import onnx.helper
from . import values


def script_check(f: ast.FunctionDef, opset, global_names):
    '''
    Check that a function falls into the ONNXScript subset of Python.
    '''
    # See if conversion succeeds.
    # TODO: cleanup Converter interface/API, separating checker from
    # converter
    converter = Converter(opset=opset, global_names=global_names)
    return converter.top_level_stmt(f)


class OnnxFunction:
    def __init__(self, f, opset):
        if inspect.isfunction(f):
            src = inspect.getsource(f)
            module = inspect.getmodule(f)
            top_level_ast = ast.parse(src)
            assert type(top_level_ast) == ast.Module
            assert len(top_level_ast.body) == 1
            f_ast = top_level_ast.body[0]
            assert type(f_ast) == ast.FunctionDef
            result = script_check(f_ast, opset, module.__dict__.copy())

            self.function = f
            self.function_ir = result
            # TODO: add transformations.
        else:
            raise TypeError(
                "The ONNXScript decorator should be applied to functions only.")

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def to_function_proto(self):
        return self.function_ir.to_function_proto(values.Opset(self.function_ir.domain, 1))


def script(opset=None):
    if (opset is not None) and (not isinstance(opset, values.Opset)):
        raise TypeError(
            "Script parameter must be an opset. Did you use @script instead of @script()?")

    def transform(f):
        return OnnxFunction(f, opset)
    return transform


def is_converted_fun(f):
    '''
    Return True if f is a function converted by onnx-script decorator.
    '''
    return isinstance(f, OnnxFunction)


def export_onnx_lib(module: ModuleType, filename: str) -> None:
    funs = set([v for k, v in module.__dict__.items() if is_converted_fun(v)])

    # Since we don't yet have LibProto defined, we use a ModelProto as a temporary
    # container for the list of functions exported as a library, with an empty graph
    # and dummy opset_imports.
    model = onnx.helper.make_model(
        onnx.GraphProto(),
        functions=[f.to_function_proto() for f in funs],
        producer_name='p2o',
        opset_imports=[onnx.helper.make_opsetid("", 15)])

    onnx.save(model, filename)
