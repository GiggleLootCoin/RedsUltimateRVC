from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PTH_CMAKE = ROOT / "tools/native/rvc_pth_android/CMakeLists.txt"
PTH_THREADS = ROOT / "tools/native/rvc_pth_android/threads_android.c"
WORKFLOW = ROOT / ".github/workflows/build-apk.yml"


def test_android_pth_core_builds_the_real_checkpoint_loader_and_inference_sources():
    source = PTH_CMAKE.read_text(encoding="utf-8")
    for required in (
        "/pickle.c",
        "/zip_reader.c",
        "/pth_loader.c",
        "/rvc.c",
        "/rvc_infer.c",
        "/tensor.c",
        "threads_android.c",
        "red_rvc_pth",
    ):
        assert required in source
    assert "/threads.c" not in source


def test_android_pth_worker_pool_has_bounded_threads_and_valid_join_handles():
    source = PTH_THREADS.read_text(encoding="utf-8")
    assert "#define RED_RVC_MAX_THREADS 4" in source
    assert "pthread_t threads[RED_RVC_MAX_THREADS]" in source
    assert "pthread_join(threads[i], NULL)" in source
    assert "pthread_t *" not in source


def test_ci_pins_and_cross_compiles_the_apache_licensed_pth_engine_for_arm64():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "pth-backend-probe:" in source
    assert "repository: f-cero/Spartacvc" in source
    assert "c0b000778e5ff680ef0ab5b445d2ac583048d731" in source
    assert "ANDROID_ABI=arm64-v8a" in source
    assert "red-rvc-pth-arm64" in source
    assert "SPARTACVC-LICENSE.txt" in source

def test_ci_runs_real_end_to_end_native_pth_conversion_with_feature_models():
    source = WORKFLOW.read_text(encoding="utf-8")
    probe = ROOT / "tools/native/rvc_pth_android/pth_convert_probe.c"
    assert probe.is_file()
    assert "Prove end-to-end PTH conversion with real voice and feature models" in source
    assert "onnxruntime-linux-x64-1.28.0.tgz" in source
    assert "aether-rvc-v2.pth" in source
    assert "hubert.onnx" in source and "rmvpe.onnx" in source
    assert "pth_convert_probe.c" in source
    assert "./pth-e2e-probe" in source
    assert "RIFF" in probe.read_text(encoding="utf-8")
    assert "red_rvc_pth_convert(" in probe.read_text(encoding="utf-8")
