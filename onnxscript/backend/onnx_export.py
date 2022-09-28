# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# --------------------------------------------------------------------------

from typing import Union

import numpy
import onnx
from onnx import FunctionProto, ModelProto, TensorProto, ValueInfoProto
from onnx.helper import make_node

from onnxscript.onnx_types import ParametricTensor

_template_python = '''
import numpy
from onnx import TensorProto
from onnx.helper import make_tensor
from onnxscript import script, external_tensor
from onnxscript.values import Opset
{% if unique_types %}
from onnxscript.onnx_types import {{ ", ".join(unique_types) }}
{%- endif %}
from onnxscript.onnx_opset import opset{{ opsets[''] }}
{% for domain, version in unique_function_domain_version: %}
{{ domain }}{{ version }} = Opset("{{ domain }}", {{ version }}){% endfor %}
{% for domain, name, fct in functions: %}
@script({{ domain }}{{ version }})
def {{ python_make_node_name(fct['proto'].domain, 1, fct['proto'].name) }}({{
    ", ".join(map(rename, fct['proto'].input)) }}):
    # attributes are missing
    {% if fct['proto'].doc_string %}"""
    {{ fct['proto'].doc_string }}
    """{%- endif %}
    {%- for node in fct['proto'].node: %}
{{ python_make_node(node, opsets, indent=1) }}{% endfor %}
    return {{ ", ".join(map(rename, fct['proto'].output)) }}
{% endfor %}
@script()
def {{ function_name }}{{translate_sig(graph.input, graph.output)}}
    {% if doc_string %}"""
    {{ doc_string }}
    """{%- endif %}
{{ python_make_node_graph(graph, opsets, indent=1) }}
    return {{ rename(graph.output[0]) }}{%
        for o in graph.output[1:]: %}, {{ rename(o) }}{% endfor %}
'''


kwlist = {
    "False",
    "None",
    "True",
    "and",
    "as",
    "assert",
    "async",
    "await",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "nonlocal",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
}


def _get_const_repr(const_node):
    """Given an ONNX Constant-op node, returns a string representation of
    the constant-value in ONNXScript, if a compact representation is possible.
    Returns None otherwise.
    Supports only FLOAT/INT64 values and scalars and small rank-1 tensors.
    This needs to be reconciled with the ONNXScript converter.
    """
    assert const_node.op_type == "Constant", "Expected a constant node"
    attr = const_node.attribute[0]
    if not attr.HasField("t"):
        return None
    tensor_proto = attr.t
    if tensor_proto.data_type in {TensorProto.FLOAT, TensorProto.INT64}:
        rank = len(tensor_proto.dims)
        if rank == 0:
            array = onnx.numpy_helper.to_array(tensor_proto).reshape(1)
            return repr(array[0])
        if rank == 1 and tensor_proto.dims[0] < 5:
            return repr(list(onnx.numpy_helper.to_array(tensor_proto)))
    return None


def _rename_variable(name):
    """Renames all names equal to a python keyword."""
    if isinstance(name, ValueInfoProto):
        # Handle graph/function input/output uniformly
        name = name.name
    if name in kwlist:
        return "r_" + name
    if name == "":
        return None
    return name


def _translate_type(onnx_type):
    """Converts a onnx type into a type defined by *onnx-script*."""
    if onnx_type.HasField("tensor_type"):
        typ = ParametricTensor.types[onnx_type.tensor_type.elem_type]
        name = repr(typ)
        if onnx_type.tensor_type.HasField("shape"):
            shape = []
            for d in onnx_type.tensor_type.shape.dim:
                if d.HasField("dim_value"):
                    shape.append(str(d.dim_value))
                else:
                    shape.append(d.dim_param)
            if len(shape) == 0:
                return name
            return "%s[%s]" % (name, ",".join(shape))
        return name + "[...]"
    raise NotImplementedError("Unable to translate type %r into onnx-script type." % onnx_type)


def _translate_signature(inputs, outputs):
    """Produce the script-functions signature."""

    def input_sig(inp: Union[ValueInfoProto, str]):
        if isinstance(inp, ValueInfoProto):
            # GraphProto inputs/outputs are ValueInfoProto
            return _rename_variable(inp.name) + ": " + _translate_type(inp.type)
        else:
            # FunctionProto inputs/outputs are just strings
            return _rename_variable(inp)

    result = "(" + ", ".join([input_sig(x) for x in inputs]) + ")"
    if outputs and isinstance(outputs[0], ValueInfoProto):
        result += " -> (" + ", ".join([_translate_type(x.type) for x in outputs]) + ")"
    return result + ":"


def _to_str(s):
    if isinstance(s, bytes):
        return s.decode("utf-8")
    return s


def _attribute_value(attr):
    if attr.HasField("f"):
        return attr.f
    if attr.HasField("i"):
        return attr.i
    if attr.HasField("s"):
        return _to_str(attr.s)
    if attr.HasField("t"):
        tensor_proto = attr.t
        if onnx.external_data_helper.uses_external_data(tensor_proto):
            return tensor_proto
        else:
            return onnx.numpy_helper.to_array(tensor_proto)
    if attr.floats:
        return list(attr.floats)
    if attr.ints:
        return list(attr.ints)
    if attr.strings:
        return list(map(_to_str, attr.strings))
    raise NotImplementedError("Unable to return a value for attribute %r." % attr)


def _python_make_node_name(domain, version, name, node=False):
    if node:
        if version is None:
            version = 1
        if not isinstance(version, int):
            raise TypeError(
                "version must be an integer not %r for domain=%r and name=%r."
                % (version, domain, name)
            )
        if domain == "":
            return "opset%d.%s" % (version, name)
        return "%s%d.%s" % (domain.replace(".", "_"), version, name)
    return name


class Exporter:
    """Class used for recursive traversal of Proto structures."""

    def __init__(self, use_operators=False, rename_function=None, inline_const=False) -> None:
        self.use_operators = use_operators
        self._rename_variable = rename_function or _rename_variable
        self.inline_const = inline_const
        self.constants = {}

    def _rename_variable_s(self, name):
        """Renames all names equal to a python keyword."""
        return str(self._rename_variable(name))

    def _python_make_node_graph(self, graph, opsets, indent=0, output_names=None):
        """Translates a GraphProto into python."""
        code = []
        sindent = "    " * indent
        if hasattr(graph, "initializer"):
            for init in graph.initializer:
                node = make_node(
                    "Constant", [], [self._rename_variable(init.name)], value=init
                )
                code.append(self._python_make_node(node, opsets, indent=indent))
        if hasattr(graph, "sparse_initializer") and len(graph.sparse_initializer) > 0:
            raise NotImplementedError("Unable to convert sparse_initilizer into python.")
        for node in graph.node:
            pynode = self._python_make_node(node, opsets, indent=indent)
            if pynode:
                code.append(pynode)
        if output_names is not None:
            for fr, to in zip(graph.output, output_names):
                code.append(
                    "%s%s = %s"
                    % (sindent, self._rename_variable(to), self._rename_variable(fr.name))
                )
        final = "\n".join(code)
        return final

    def _python_make_node_make_attribute_str(self, node):
        attributes = []
        for at in node.attribute:
            value = _attribute_value(at)
            if isinstance(value, str):
                attributes.append((at.name, "%r" % value))
                continue
            if isinstance(value, numpy.ndarray):
                onnx_dtype = at.t.data_type
                if len(value.shape) == 0:
                    text = 'make_tensor("value", %s, dims=[], vals=[%r])' "" % (
                        onnx_dtype,
                        value.tolist(),
                    )
                else:
                    text = 'make_tensor("value", %s, dims=%r, vals=%r)' "" % (
                        onnx_dtype,
                        list(value.shape),
                        value.ravel().tolist(),
                    )
                attributes.append((at.name, text))
                continue
            if isinstance(value, TensorProto):
                metadata = onnx.external_data_helper.ExternalDataInfo(value)
                name = value.name or "value"
                text = "external_tensor("
                text += f"{repr(name)}, {value.data_type}, {repr(list(value.dims))}"
                text += f", {repr(metadata.location)}"
                if metadata.offset:
                    text += ", offset=" + repr(metadata.offset)
                if metadata.length:
                    text += ", length=" + repr(metadata.length)
                attributes.append((at.name, text))
                continue
            attributes.append((at.name, repr(value)))

        return ", ".join("%s=%s" % (k, v) for k, v in attributes)

    def _python_make_node_if(self, node, opsets, indent=0):
        """Translates a node If into python."""
        sindent = "    " * indent
        code = ["%sif %s:" % (sindent, node.input[0])]
        if len(node.attribute) != 2:
            raise RuntimeError(
                "Node %r expected two attributes not %d." % (node.op_type, len(node.attribute))
            )
        atts = node.attribute
        if atts[0].name == "else_branch":
            else_branch, then_branch = atts[0].g, atts[1].g
        else:
            else_branch, then_branch = atts[1].g, atts[0].g
        code.append(
            self._python_make_node_graph(
                then_branch, opsets, indent=indent + 1, output_names=node.output
            )
        )
        code.append("%selse:" % sindent)
        code.append(
            self._python_make_node_graph(
                else_branch, opsets, indent=indent + 1, output_names=node.output
            )
        )
        return "\n".join(code)

    def _python_make_node_loop(self, node, opsets, indent=0):
        """Translates a node Loop into python."""
        body = node.attribute[0].g
        sindent = "    " * indent
        n_iter = self._rename_variable(node.input[0])
        cond = self._rename_variable(node.input[1])
        # v_initial = node.input[2]
        rows = []
        if n_iter and not cond:
            rows.append("%sfor %s in range(%s):" % (sindent, body.input[0].name, n_iter))
        elif not n_iter and cond:
            rows.append("%swhile %s:" % (sindent, cond))
        elif n_iter and cond:
            rows.append("%sfor %s in range(%s):" % (sindent, body.input[0].name, n_iter))
            rows.append("%s    if not %s:" % (sindent, cond))
            rows.append("%s        break" % sindent)
        else:
            raise RuntimeError(
                "Unable to export loop type %r into python because there is no "
                "stop condition." % (node.op_type,)
            )
        rows.append(
            self._python_make_node_graph(
                body, opsets, indent=indent + 1, output_names=node.output
            )
        )
        return "\n".join(rows)

    def _python_make_node_scan(self, node, opsets, indent=0):
        """Translates a node Scan into python."""
        raise NotImplementedError()

    def lookup(self, var):
        if var in self.constants:
            return self.constants[var]
        else:
            return self._rename_variable_s(var)

    def _python_make_node(self, onnx_node, opsets, indent=0):
        if isinstance(onnx_node, dict):
            node = onnx_node["onnx_node"]
        else:
            node = onnx_node
        if self.inline_const and node.op_type == "Constant":
            val = _get_const_repr(node)
            if val is not None:
                self.constants[node.output[0]] = str(val)
                return ""
        if node.op_type in {"If", "Loop", "Scan"}:
            # If, Loop, Scan
            if node.op_type == "If":
                return self._python_make_node_if(node, opsets, indent=indent)
            if node.op_type == "Loop":
                return self._python_make_node_loop(node, opsets, indent=indent)
            if node.op_type == "Scan":
                return self._python_make_node_scan(node, opsets, indent=indent)
            raise RuntimeError("Unable to export node type %r into python." % (node.op_type,))
        if any(
            map(
                lambda att: hasattr(att, "g") and att.g and att.g.ByteSize() > 0,
                node.attribute,
            )
        ):
            raise RuntimeError("Unable to export node type %r into python." % node.op_type)
        ops = {
            "Add": "+",
            "Sub": "-",
            "Mul": "*",
            "MatMul": "@",
            "Div": "/",
            "Pow": "**",
            "And": "&",
            "Or": "|",
            "Greater": ">",
            "Equal": "==",
            "Lesser": "<",
            "GreaterOrEqual": ">=",
            "LessOrEqual": "<=",
        }
        sindent = "    " * indent
        if self.use_operators and node.op_type in ops:
            return "%s%s = %s" % (
                sindent,
                self._rename_variable(node.output[0]),
                (" %s " % ops[node.op_type]).join(map(self.lookup, node.input)),
            )
        name = _python_make_node_name(
            node.domain, opsets[node.domain], node.op_type, node=True
        )
        attributes_str = self._python_make_node_make_attribute_str(node)
        if len(node.input) > 0 and len(attributes_str) > 0:
            attributes_str = ", " + attributes_str
        output_names = []
        for i, o in enumerate(node.output):
            if o in ("", None):
                output_names.append("_%d" % i)
            else:
                output_names.append(self._rename_variable(o))

        text = [
            sindent,
            ", ".join(output_names),
            " = ",
            name,
            "(",
            ", ".join(map(self.lookup, node.input)),
            attributes_str,
            ")",
        ]
        return "".join(text)


def export_template(
    model_onnx,
    template,
    name=None,
    autopep_options=None,
    function_name="main_function",
    clean_code=True,
    use_operators=False,
    rename=False,
    inline_const: bool = False,
):
    """Exports an ONNX model into a code based on a template.

    Args:
        model_onnx: string or ONNX graph
        template: exporting template
        name: to overwrite onnx name
        autopep_options: :epkg:`autopep8` options
        function_name: main function name in the code
        clean_code: clean the code
        rename: rename variable name to get shorter names
        inline_const: replace ONNX constants inline if compact

    Returns:
        python code
    """
    # delayed import to avoid raising an exception if not installed.
    import autopep8

    # unique_function_domain_version
    unique_function_domain_version = set()
    if hasattr(model_onnx, "functions"):
        for f in model_onnx.functions:
            unique_function_domain_version.add((f.domain, 1))
    unique_function_domain_version = list(sorted(unique_function_domain_version))

    if rename:
        variable_names = dict()

        def rename_variable(name):
            var_name = _rename_variable(name)
            if var_name in variable_names:
                return variable_names[var_name]
            new_name = f"v{len(variable_names) + 1}"
            variable_names[var_name] = new_name
            return new_name

    else:

        def rename_variable(name):
            return _rename_variable(name)

    exporter = Exporter(use_operators, rename_variable, inline_const)

    # containers
    context = {
        "main_model": model_onnx,
        "python_make_node": exporter._python_make_node,
        "python_make_node_graph": exporter._python_make_node_graph,
        "python_make_node_name": _python_make_node_name,
        "unique_function_domain_version": unique_function_domain_version,
        "rename": rename_variable,
        "translate_sig": _translate_signature,
    }

    # opset
    if hasattr(model_onnx, "opset_import"):
        opsets = {}
        for oimp in model_onnx.opset_import:
            opsets[oimp.domain] = oimp.version
        context["opsets"] = opsets

    graph = model_onnx.graph if hasattr(model_onnx, "graph") else model_onnx

    # types
    unique_types = set()
    for t in list(graph.input) + list(graph.output):
        if hasattr(t, "type"):
            ts = _translate_type(t.type)
            its = ts.split("[", maxsplit=1)[0]
            unique_types.add(its)
    context["unique_types"] = list(sorted(unique_types))

    # functions
    functions = []
    if hasattr(model_onnx, "functions"):
        for fct in model_onnx.functions:
            opsets_fct = {}
            for oimp in fct.opset_import:
                opsets_fct[oimp.domain] = oimp.version
            functions.append((fct.domain, fct.name, {"proto": fct, "opsets": opsets_fct}))
    context["functions"] = functions

    # node
    context["graph"] = graph

    # graph
    context["name"] = name or graph.name
    context["function_name"] = function_name
    if hasattr(model_onnx, "graph"):
        context["doc_string"] = model_onnx.doc_string
    else:
        context["doc_string"] = ""

    # First rendering to detect any unused or replaced initializer.
    from jinja2 import Template  # delayed import

    template = Template(template)
    final = template.render(
        enumerate=enumerate, sorted=sorted, len=len, repr=repr, map=map, **context
    )

    final += "\n"
    if "\nreturn" in final:
        raise SyntaxError("The produced code is wrong.\n%s" % final)
    if clean_code:
        cleaned_code = autopep8.fix_code(final, options=autopep_options)
        if "\nreturn" in cleaned_code:
            raise SyntaxError(
                "The cleaned code is wrong.\n%s\n------%s" % (final, cleaned_code)
            )
        return cleaned_code
    return final


def export2python(
    model_onnx,
    opset=None,
    verbose=True,
    name=None,
    rename=False,
    autopep_options=None,
    function_name="main",
    use_operators=False,
    clean_code=True,
    inline_const: bool = False,
):
    """Exports an ONNX model to the *python* syntax.

    Args:
        model_onnx: string or ONNX graph
        opset: opset to export to (None to select the one from the
            graph)
        verbose: inserts prints
        name: to overwrite onnx name
        rename: rename the names to get shorter names
        autopep_options: :epkg:`autopep8` options
        function_name: main function name
        clean_code: clean the code
        inline_const: replace ONNX constants inline if compact

    Returns:
        python code
    The following example shows what a python code creating a graph
    implementing the KMeans would look like.
    .. runpython::
        :showcode:
        :process:
        import numpy
        from sklearn.cluster import KMeans
        from mlprodict.onnx_conv import to_onnx
        from mlprodict.onnx_tools.onnx_export import export2python
        X = numpy.arange(20).reshape(10, 2).astype(numpy.float32)
        tr = KMeans(n_clusters=2)
        tr.fit(X)
        onx = to_onnx(tr, X, target_opset=14)
        code = export2python(onx)
        print(code)
    """
    if isinstance(model_onnx, str):
        model_onnx = onnx.load(model_onnx)

    if not isinstance(model_onnx, (ModelProto, FunctionProto)):
        raise TypeError("The function expects a ModelProto not %r." % type(model_onnx))
    code = export_template(
        model_onnx,
        template=_template_python,
        name=name,
        autopep_options=autopep_options,
        clean_code=clean_code,
        function_name=function_name,
        use_operators=use_operators,
        rename=rename,
        inline_const=inline_const,
    )
    return code
