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
