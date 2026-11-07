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


def test_home_dashboard_has_a_working_official_youtube_channel_button():
    source = BRAND.read_text(encoding="utf-8")
    assert "final VoidCallback onYouTube;" in source
    assert "label: const Text('VISIT MY YOUTUBE CHANNEL')" in source
    assert "@Little-Red-Big-Smile • OFFICIAL CHANNEL" in source
    assert "onYouTube: _openCreatorYouTube" in source
    assert "final VoidCallback onFullRvc;" in source
    assert "label: const Text('OPEN FULL RVC ENGINE')" in source
    assert "https://www.youtube.com/@Little-Red-Big-Smile" in source


def test_dashboard_discloses_song_cover_and_realtime_limits():
    source = BRAND.read_text(encoding="utf-8")
    assert "Separate vocals, convert your voice, and mix the cover" in (ROOT / "tools/ui/red_home_screen.dart").read_text(encoding="utf-8")
    assert "REALTIME RVC — EXPERIMENTAL" in source
    assert "Limited Android support; may stutter" in source


def test_gradle_can_use_a_private_persistent_release_keystore():
    source = BRAND.read_text(encoding="utf-8")
    assert "redSigningProperties" in source
    assert "signingConfigs.redRelease" in source
    assert "signingConfigs.debug" in source


def test_index_tools_discloses_faiss_conversion_is_not_on_device():
    source = INDEX_TOOLS.read_text(encoding="utf-8")
    assert "Standard RVC/FAISS .index files are not converted by this Android app yet" in source
    assert "Importing or renaming one does not make it compatible" in source


def test_workflow_runs_tests_and_supports_private_persistent_signing():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "flutter test --reporter expanded" in source
    assert "python3 -m py_compile tools/brand.py" in source
    assert "python3 -m pytest -q tools/tests" in source
    for secret in (
        "RED_RVC_KEYSTORE_BASE64",
        "RED_RVC_STORE_PASSWORD",
        "RED_RVC_KEY_ALIAS",
        "RED_RVC_KEY_PASSWORD",
    ):
        assert secret in source
    assert "temporary GitHub runner debug key" in source
    assert "if: github.event_name != 'pull_request'" in source


def test_upstream_song_picker_is_translated_to_english_before_build():
    source = BRAND.read_text(encoding="utf-8")
    for text in (
        '"选择音频": "Select Audio"',
        '"已选择：": "Selected: "',
        '"未选择": "No audio selected"',
        '"选择音频失败：$e": "Audio selection failed: $e"',
        '"需要麦克风权限": "Microphone permission is required"',
        '"录音失败：$e": "Recording failed: $e"',
        '"停止录音": "Stop Recording"',
        '"直接录音": "Record Audio"',
        '"支持：MP3、WAV、M4A、FLAC、OGG": "Supported: MP3, WAV, M4A, FLAC, OGG"',
    ):
        assert text in source
    assert "song_picker_text = song_picker_text.replace(source_text, english_text)" in source
    assert "FileType.audio" in source





def test_dataset_lab_is_phone_local_and_does_not_advertise_cloud_training():
    training = (ROOT / "tools/ui/training_screen.dart").read_text(encoding="utf-8")
    assert "ON-PHONE DATASET WORKSPACE" in training
    assert "This phone prepares and exports your voice dataset locally" in training
    assert "It does not train an RVC neural network" in training
    assert "Kaggle" not in training
    assert "Colab" not in training
    assert "url_launcher/url_launcher.dart" not in training


def test_dataset_export_creates_a_single_zip_for_android_sharing():
    training = (ROOT / "tools/ui/training_screen.dart").read_text(encoding="utf-8")
    brand = BRAND.read_text(encoding="utf-8")
    assert "import 'package:archive/archive_io.dart';" in training
    assert "ZipFileEncoder()" in training
    assert "encoder.addDirectory(audio, includeDirName: true)" in training
    assert "XFile(zipPath, mimeType: 'application/zip')" in training
    assert "archive: ^3.6.1" in brand


def test_offline_song_cover_native_pipeline_is_wired_into_android_build():
    integration = (ROOT / "tools/native/integrate.py").read_text(encoding="utf-8")
    kotlin = (ROOT / "tools/native/SourceSeparationBridge.kt").read_text(encoding="utf-8")
    native = (ROOT / "tools/native/source_separation_jni.cpp").read_text(encoding="utf-8")
    screen = (ROOT / "tools/ui/song_cover_screen.dart").read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "separateSongVocals" in integration
    assert "mixSongCover" in integration
    assert "SherpaOnnxCreateOfflineSourceSeparation" in native
    assert "SherpaOnnxOfflineSourceSeparationProcess" in native
    assert "SherpaOnnxWriteWaveMultiChannel" in native
    assert "output_rate = music->sample_rate" in native
    assert "static_cast<double>(frame) * wave->sample_rate / output_rate" in native
    assert "The converted vocals and accompaniment have incompatible audio formats." not in native
    assert "output_channels = std::max(vocals->num_channels, music->num_channels)" in native
    assert "System.loadLibrary(\"sherpa-onnx-c-api\")" in kotlin
    assert "SourceSeparationBridge.separateWav" in integration
    assert "SourceSeparationBridge.mixWav" in integration
    assert "await _bridge.separateSongVocals" in screen
    assert "await _bridge.infer" in screen
    assert "await _bridge.mixSongCover" in screen
    assert "k2-fsa/sherpa-onnx" in workflow
    assert "SHERPA_ONNX_ENABLE_C_API=ON" in workflow
    assert "BUILD_SHARED_LIBS=OFF" in workflow
    assert "build-android-arm64-v8a-static/install/lib/libsherpa-onnx-c-api.so" in workflow
    assert "SherpaOnnxCreateOfflineSourceSeparation" in workflow
    assert "SherpaOnnxOfflineSourceSeparationProcess" in workflow
    assert "libonnxruntime.so" in workflow
    assert "sherpa-onnx-spleeter-2stems-fp16.tar.bz2" in workflow


def test_song_cover_uses_android_media_codec_to_prepare_common_audio_formats():
    integration = (ROOT / "tools/native/integrate.py").read_text(encoding="utf-8")
    screen = (ROOT / "tools/ui/song_cover_screen.dart").read_text(encoding="utf-8")
    assert "decodeAudioToWav(inputPath, decodedInput.absolutePath)" in integration
    assert "decodeAudioSegment(source, 0L, durationUs)" in integration
    assert "writeDecodedAudioWav(File(outputPath), decoded)" in integration
    assert "Android decodes it locally to PCM WAV" in screen
    assert "type: FileType.audio" in screen
