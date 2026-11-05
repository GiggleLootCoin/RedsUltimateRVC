from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRAND = ROOT / "tools/brand.py"
LIBRARY = ROOT / "tools/ui/model_library_screen.dart"
INDEX_TOOLS = ROOT / "tools/ui/index_converter_screen.dart"
WORKFLOW = ROOT / ".github/workflows/build-apk.yml"


def test_source_model_library_imports_and_persists_supported_files():
    source = LIBRARY.read_text(encoding="utf-8")
    for extension in (".onnx", ".pth", ".pt", ".zip", ".index", ".mobile.index"):
        assert extension in source
    assert "FileType.any" in source
    assert "getApplicationDocumentsDirectory()" in source
    assert "File(sourcePath).copy(destination.path)" in source
    assert "await file.delete()" in source


def test_source_library_does_not_claim_pth_is_runnable():
    source = LIBRARY.read_text(encoding="utf-8")
    assert "Only compatible ONNX models can be selected" in source
    assert "does not convert or train them" in source
    assert "onModelSelected" in source
    assert "onIndexSelected" in source


def test_branding_installs_library_and_routes_dashboard_to_it():
    source = BRAND.read_text(encoding="utf-8")
    assert '"model_library_screen.dart"' in source
    assert "import 'screens/model_library_screen.dart';" in source
    assert "ModelLibraryScreen(onModelSelected: _onModelSelected, onIndexSelected: _onIndexSelected)" in source
    assert source.count("onModels: _openModelLibrary") == 2
    assert r"\\n    Navigator" not in source


def test_index_tools_discloses_faiss_conversion_is_not_on_device():
    source = INDEX_TOOLS.read_text(encoding="utf-8")
    assert "Standard RVC/FAISS .index files are not converted by this Android app yet" in source
    assert "Changing a file extension" not in source


def test_workflow_runs_tests_and_supports_private_persistent_signing():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "flutter test --reporter expanded" in source
    assert "python/tests/*_static.py" in source
    for secret in (
        "RED_RVC_KEYSTORE_BASE64",
        "RED_RVC_STORE_PASSWORD",
        "RED_RVC_KEY_ALIAS",
        "RED_RVC_KEY_PASSWORD",
    ):
        assert secret in source
    assert "temporary GitHub runner debug key" in source
