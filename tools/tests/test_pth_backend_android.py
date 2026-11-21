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
    assert "onnxruntime-1.28.0.jar" in source
    assert "native/linux-x64/libonnxruntime.so" in source
    assert "MODEL=\"pth-fixtures/nahida-jp.pth\"" in source
    assert "repo1.maven.org/maven2" in source
    assert "repo.maven.apache.org/maven2" in source
    assert "AAR_PATH=" in source
    assert "hubert.onnx" in source and "rmvpe.onnx" in source
    assert "pth_convert_probe.c" in source
    assert "./pth-e2e-probe" in source
    assert "RIFF" in probe.read_text(encoding="utf-8")
    assert "red_rvc_pth_convert(" in probe.read_text(encoding="utf-8")


def test_ort_128_compatibility_patch_preserves_mutable_release_handles_and_const_run_view():
    patch = (ROOT / "tools/native/patch_spartacvc_ort_compat.py").read_text(encoding="utf-8")
    assert "float *const in_w[3]" in patch
    assert "float *const rs_w[3]" in patch
    assert "OrtValue *ort_inputs[8]" in patch
    assert "const OrtValue *ort_input_values[8]" in patch
    assert "const OrtValue *ort_inputs[8]" not in patch
    assert "in_names,  ort_input_values" in patch



def test_android_model_picker_accepts_native_pth_instead_of_rejecting_it():
    integration = (ROOT / "tools/native/integrate.py").read_text(encoding="utf-8")
    assert "return lowerPath.endsWith('.onnx') || lowerPath.endsWith('.pth');" in integration
    assert "Choose a compatible ONNX or supported RVC v2 PTH voice model" in integration
    assert "Supported: RVC v2 PTH (768d / 100fps) or compatible ONNX" in integration


def test_faiss_patch_exports_mobile_index_streaming_and_handles_ivf():
    patch = (ROOT / "tools/native/patch_faiss_mobile.py").read_text(encoding="utf-8")
    assert "nativeExportMobileIndex" in patch
    assert "URVCIDX1" in patch
    assert "faiss_IndexIVF_make_direct_map" in patch
    assert "faiss_Index_reconstruct" in patch
    assert "fwrite(vector, sizeof(float)" in patch
    assert "remove(cpath)" in patch


def test_faiss_android_converter_is_local_and_dimension_checked():
    converter = (ROOT / "tools/native/FaissIndexConverter.kt").read_text(encoding="utf-8")
    assert "FEATURE_DIMENSION = 768" in converter
    assert "FAISS.readIndex" in converter
    assert "exportMobileIndex" in converter
    assert "TempWorkspaceManager" in converter
    assert "importPickedFile(ImportedFileKind.INDEX" in converter


def test_faiss_android_build_keeps_lapack_enabled_for_native_linking():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "-DBUILD_WITHOUT_LAPACK=OFF" in workflow
    assert "-DC_LAPACK=ON" in workflow
    assert "source = source.replace(\"-DBUILD_WITHOUT_LAPACK=OFF\", \"-DBUILD_WITHOUT_LAPACK=ON\"" not in workflow
    assert "source = source.replace(\"-DC_LAPACK=ON\", \"-DC_LAPACK=OFF\"" not in workflow
