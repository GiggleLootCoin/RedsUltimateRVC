from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INTEGRATION = ROOT / "tools/native/integrate.py"
SCREEN = ROOT / "tools/ui/model_converter_screen.dart"


def test_native_gguf_converter_is_copied_into_the_android_app():
    source = INTEGRATION.read_text(encoding="utf-8")
    assert "converter_source = ROOT / 'tools/ui/model_converter_screen.dart'" in source
    assert "converter_target = BUILD / 'lib/screens/model_converter_screen.dart'" in source
    assert "converter_target.write_text" in source


def test_native_gguf_converter_has_a_real_navigation_entry():
    source = INTEGRATION.read_text(encoding="utf-8")
    assert "import 'screens/model_converter_screen.dart';" in source
    assert "void _openModelConverter()" in source
    assert "setState(() => _moduleIndex = 8);" in source
    assert 'title: Text("Native GGUF Converter")' in source
    assert "selected: _moduleIndex == 8" in source
    assert "ModelConverterScreen()" in source
    assert "PitchDetectionScreen(isActive: _moduleIndex == 7)" in source


def test_native_converter_does_not_claim_to_accept_raw_pth_checkpoints():
    source = SCREEN.read_text(encoding="utf-8")
    assert "required bool gguf" in source
    assert "lower.endsWith('.gguf')" in source
    assert "Raw PyTorch .pth checkpoints still need the upstream exporter first" in source
