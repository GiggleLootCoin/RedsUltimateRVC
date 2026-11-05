from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRAND = ROOT / "tools/brand.py"
INDEX_TOOLS = ROOT / "tools/ui/index_converter_screen.dart"
WORKFLOW = ROOT / ".github/workflows/build-apk.yml"


def test_integrated_model_picker_imports_source_models_without_android_extension_filters():
    source = BRAND.read_text(encoding="utf-8")
    assert "type: FileType.any" in source
    assert "['onnx', 'pth', 'pt', 'zip'].contains(ext)" in source
    assert "_bridge.importPickedFile(kind: 'model', sourcePath: source)" in source
    assert "PTH/PT/ZIP is stored safely but is not directly runnable" in source


def test_integrated_index_library_accepts_faiss_and_mobile_indexes_without_fake_conversion():
    source = BRAND.read_text(encoding="utf-8")
    assert "Select an RVC .index or .mobile.index file" in source
    assert "Standard .index stored in your Index Library" in source
    assert "does not include FAISS-to-mobile conversion" in source


def test_dashboard_and_full_engine_open_the_integrated_model_picker():
    source = BRAND.read_text(encoding="utf-8")
    assert source.count("onModels: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ModelPickerScreen(") == 3
    assert "onModels: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ModelPickerScreen(onModelSelected:" in source


def test_index_tools_discloses_faiss_conversion_is_not_on_device():
    source = INDEX_TOOLS.read_text(encoding="utf-8")
    assert "Standard RVC/FAISS .index files are not converted by this Android app yet" in source
    assert "Importing or renaming one does not make it compatible" in source


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
