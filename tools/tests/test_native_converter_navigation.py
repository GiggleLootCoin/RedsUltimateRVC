from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/build-apk.yml"


def test_redundant_gguf_runner_is_not_included_in_android_builds():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "RVC_GGML_ANDROID_SO" not in source
    assert "red-rvc-ggml-arm64" not in source
    assert "libred_rvc_ggml.so" not in source
    assert "libred_rvc_pth.so" in source


def test_generated_kotlin_dispatch_uses_real_newline_escape():
    integration = (ROOT / "tools/native/integrate.py").read_text(encoding="utf-8")
    single_escaped = "dispatch + " + chr(39) + chr(92) + "n"
    double_escaped = "dispatch + " + chr(39) + chr(92) * 2 + "n"
    assert double_escaped not in integration
    assert single_escaped in integration
    assert "validateVoiceModel" in integration


def test_workspace_conversion_no_longer_routes_pth_to_onnx_generate_screen():
    source = (ROOT / "tools/native/integrate.py").read_text(encoding="utf-8")
    assert "Choose your compatible .pth voice model in Voice Library first." in source
    assert "indexPath: _selectedIndexPath" in source
    assert "indexPath: selectedIndex" in source
    assert "selectedModel == null || !selectedModel.toLowerCase().endsWith('.pth')" in source
    assert "selectedModel.toLowerCase().endsWith('.onnx')" not in source
    assert 'ms = ms.replace("onContinue: _continueToGenerate,", "onContinue: _continueToPthConversion,")' in source
    assert "void _continueToPthConversion()" in source
    assert "old_generate_screen = '''canGenerate" in source
    assert "? SongCoverScreen(" in source
    assert "initialSongPath: _selectedSongPath" in source
    assert "onCoverComplete: _onGenerationComplete" in source
    assert "label: 'PTH Cover'" in source
    assert "final mobileIndex = selectedIndex" not in source
    assert "No user-supplied ONNX voice model is required." in source or "No ONNX voice-model export or upload is required." in (ROOT / "tools/ui/song_cover_screen.dart").read_text(encoding="utf-8")


def test_direct_pth_native_route_resolves_mobile_index_to_original_sidecar_case_safely():
    source = (ROOT / "tools/native/integrate.py").read_text(encoding="utf-8")
    assert 'selected.name.endsWith(".mobile.index", ignoreCase = true)' in source
    assert 'selected.name.substring(0, selected.name.length - ".mobile.index".length) + ".index"' in source
