"""Test with different environment configuration with nox.

Documentation:
    https://nox.thea.codes/
"""

import nox

nox.options.error_on_missing_interpreters = False


COMMON_TEST_DEPENDENCIES = (
    "jinja2",
    "numpy==1.23.5",
    "typing_extensions",
    "beartype",
    "types-PyYAML",
    "expecttest",
    "hypothesis",
    "packaging",
    "parameterized",
    "pytest-cov",
    "pytest-randomly",
    "pytest-subtests",
    "pytest-xdist",
    "pytest!=7.1.0",
    "pyyaml",
)
ONNX = "onnx==1.13.1"
ONNX_RUNTIME = "onnxruntime==1.14.1"
PYTORCH = "torch==2.0.0"
ONNX_RUNTIME_NIGHTLY_DEPENDENCIES = (
    "flatbuffers",
    "coloredlogs",
    "sympy",
    "numpy",
    "packaging",
    "protobuf",
)


@nox.session(tags=["build"])
def build(session):
    """Build package."""
    session.install("build", "wheel")
    session.run("python", "-m", "build")


@nox.session(tags=["test"])
def test(session):
    """Test onnxscript and documentation."""
    session.install(
        *COMMON_TEST_DEPENDENCIES,
        PYTORCH,
        ONNX,
        ONNX_RUNTIME,
    )
    session.install(".", "--no-deps")
    session.run("pip", "list")
    session.run("pytest", "onnxscript", *session.posargs)
    session.run("pytest", "docs/test", *session.posargs)


@nox.session(tags=["test-function-experiment"])
def test_onnx_func_expe(session):
    """Test with onnx function experiment builds."""
    # TODO(justinchuby): Remove when test-ort-nightly contains this change.
    session.install(
        *COMMON_TEST_DEPENDENCIES,
        PYTORCH,
    )
    # Install ONNX and ORT with experimental ONNX function support
    session.install(
        "-f",
        "https://onnxruntimepackages.z14.web.core.windows.net/onnxruntime-function-experiment.html",
        "--pre",
        "ort-function-experiment-nightly",
    )

    session.install("-r", "requirements/ci/requirements-onnx-weekly.txt")
    session.install(".", "--no-deps")
    session.run("pip", "list")
    # Ignore ops_correctness_test because this version of ORT does not contain the
    # latest fixes and may fail some tests in the torch op tests.
    session.run(
        "pytest",
        "onnxscript",
        "--ignore=onnxscript/tests/function_libs/torch_aten/ops_correctness_test.py",
        *session.posargs,
    )
    session.run("pytest", "docs/test", *session.posargs)


@nox.session(tags=["test-torch-nightly"])
def test_torch_nightly(session):
    """Test with PyTorch nightly (preview) build."""
    session.install(
        *COMMON_TEST_DEPENDENCIES,
        ONNX,
        ONNX_RUNTIME,
    )
    session.install(
        "--pre", "torch", "--index-url", "https://download.pytorch.org/whl/nightly/cpu"
    )
    session.install(".", "--no-deps")
    session.run("pip", "list")
    session.run("pytest", "onnxscript", *session.posargs)


@nox.session(tags=["test-onnx-weekly"])
def test_onnx_weekly(session):
    """Test with ONNX weekly (preview) build."""
    session.install(*COMMON_TEST_DEPENDENCIES, ONNX_RUNTIME, PYTORCH)
    session.install("-r", "requirements/ci/requirements-onnx-weekly.txt")
    session.install(".", "--no-deps")
    session.run("pip", "list")
    session.run("pytest", "onnxscript", *session.posargs)


@nox.session(tags=["test-ort-nightly"])
def test_ort_nightly(session):
    """Test with ONNX Runtime nightly builds."""
    session.install(
        *COMMON_TEST_DEPENDENCIES, PYTORCH, ONNX, *ONNX_RUNTIME_NIGHTLY_DEPENDENCIES
    )
    session.install("-r", "requirements/ci/requirements-ort-nightly.txt")
    session.install(".", "--no-deps")
    session.run("pip", "list")
    session.run("pytest", "onnxscript", *session.posargs)
