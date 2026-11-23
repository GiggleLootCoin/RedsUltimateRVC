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
    assert "bool _runtime(String path) => ['onnx', 'pth'].contains(_ext(path));" in source
    assert "PT/ZIP files are storage-only; supported PTH and ONNX models can be used for conversion." in source
    assert "onPressed: ready && widget.selectedSongPath != null && _ext(selected!) == 'onnx' ? widget.onContinue : null" in source
    assert "PTH VOICE — USE SONG COVERS" in source
    assert "READY — Native PTH supports RVC v2, 768 dimensions / 100 fps only." in source


def test_integrated_index_library_converts_standard_faiss_and_validates_mobile_indexes():
    source = BRAND.read_text(encoding="utf-8")
    assert "Select an RVC .index or .mobile.index file" in source
    assert "_bridge.convertFaissIndex(imported.path)" in source
    assert "_bridge.convertFaissIndex(path)" in source
    assert "Standard FAISS index converted on this phone" in source


def test_native_faiss_converter_is_wired_through_android_and_flutter():
    integration = (ROOT / "tools/native/integrate.py").read_text(encoding="utf-8")
    converter = (ROOT / "tools/native/FaissIndexConverter.kt").read_text(encoding="utf-8")
    screen = (ROOT / "tools/ui/index_converter_screen.dart").read_text(encoding="utf-8")
    assert "FaissIndexConverter.kt" in integration
    assert "convertFaissIndex(call, result)" in integration
    assert "FaissIndexConverter.convert(appContext, File(sourcePath))" in integration
    assert "Future<ImportedFileHandle> convertFaissIndex(String sourcePath)" in integration
    assert "implementation files('libs/faiss-android.aar')" in integration
    assert "FAISS.readIndex(source.absolutePath)" in converter
    assert "exportMobileIndex" in converter
    assert "convertFaissIndex(imported.path)" in screen


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
    brand = BRAND.read_text(encoding="utf-8")
    assert '"song_cover_screen.dart"' in brand
    assert "import 'screens/song_cover_screen.dart';" in brand
    assert "onSongCovers: () {" in brand
    assert "SongCoverScreen(" in brand
    assert "modelPath: modelPath" in brand
    assert "indexPath: _selectedIndexPath" in brand
    assert "onSongCovers: _openAudioConversion" not in brand
    assert "endsWith('.onnx') && !modelPath.toLowerCase().endsWith('.pth')" in brand
    assert "Song Covers needs a compatible ONNX or supported RVC v2 PTH voice" in brand
    full_engine = (ROOT / "tools/ui/full_rvc_screen.dart").read_text(encoding="utf-8")
    assert "Song Covers is available from the main dashboard" in full_engine
    assert "bundled offline vocal separation" in full_engine
    assert "Dataset Lab prepares samples; optional CPU training is separate" in full_engine
    source = BRAND.read_text(encoding="utf-8")
    assert "Separate vocals, convert your voice, and mix the cover" in (ROOT / "tools/ui/red_home_screen.dart").read_text(encoding="utf-8")
    assert "REALTIME RVC — EXPERIMENTAL" in source
    assert "Limited Android support; may stutter" in source


def test_gradle_can_use_a_private_persistent_release_keystore():
    source = BRAND.read_text(encoding="utf-8")
    assert "redSigningProperties" in source
    assert "signingConfigs.redRelease" in source
    assert "signingConfigs.debug" in source


def test_index_tools_performs_local_faiss_conversion_for_supported_indexes():
    source = INDEX_TOOLS.read_text(encoding="utf-8")
    assert "convertFaissIndex(imported.path)" in source
    assert "pickAndImportFile(kind:" in source
    assert "768-dimensional RVC v2 FAISS indexes" in source
    assert "conversion runs locally" in source
    assert "does not yet apply index blending" in source


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
    assert "if: github.ref == 'refs/heads/main' && github.event_name == 'workflow_dispatch'" in source


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
    assert "VOICE DATASET + NEURAL TRAINING" in training
    assert "Your samples are prepared and stored on this phone" in training
    assert "requires uploading the exported ZIP" in training
    assert "Do not use recordings you consider private or confidential" in training
    assert "OPEN GENUINE RVC TRAINING WORKFLOW" in training
    assert "package:url_launcher/url_launcher.dart" in training


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
    assert "endsWith('.onnx')" in integration
    assert "endsWith('.mobile.index')" in integration
    assert "SherpaOnnxCreateOfflineSourceSeparation" in native
    assert "SherpaOnnxOfflineSourceSeparationProcess" in native
    assert "Pcm16WaveReader" in native
    assert "Pcm16WaveWriter" in native
    assert "center_frames" in native
    assert "context_frames" in native
    assert "kBlockFrames = 8192" in native
    assert "ReadFrames(start, count)" in native
    assert "SherpaOnnxOfflineSourceSeparationProcess" in native
    assert "SherpaOnnxDestroySourceSeparationOutput" in native
    assert "SherpaOnnxReadWaveMultiChannel" not in native
    assert "std::vector<std::vector<float>> mixed(output_channels, std::vector<float>(frames" not in native
    assert "The converted vocals and accompaniment have incompatible audio formats." not in native
    assert "System.loadLibrary(\"sherpa-onnx-c-api\")" in kotlin
    assert "SourceSeparationBridge.separateWav" in integration
    assert "SourceSeparationBridge.mixWav" in integration
    assert "withContext(Dispatchers.Main) { result.success(output.absolutePath) }" in integration
    assert "await _bridge.separateSongVocals" in screen
    assert "await _bridge.infer" in screen
    assert "await _bridge.convertPth" in screen
    assert "final isPth = widget.modelPath.toLowerCase().endsWith('.pth')" in screen
    assert "await _bridge.mixSongCover" in screen
    assert ".clamp(0.0, 1.0).toDouble()" in screen
    assert "k2-fsa/sherpa-onnx" in workflow
    assert "ref: v1.13.8" in workflow
    assert 'yes | "$SDKMANAGER" --licenses >/dev/null || true' in workflow
    assert "SHERPA_ONNX_ENABLE_C_API=ON" in workflow
    assert "BUILD_SHARED_LIBS=ON" in workflow
    assert "build-android-arm64-v8a/install/lib/libsherpa-onnx-c-api.so" in workflow
    assert "SherpaOnnxCreateOfflineSourceSeparation" in workflow
    assert "SherpaOnnxOfflineSourceSeparationProcess" in workflow
    assert "libonnxruntime.so" in workflow
    assert "onnxruntime-android:1.28.0" in workflow
    assert "libred_source_separation.so" in workflow
    assert "libsherpa-onnx-c-api.so" in workflow
    assert "assets/flutter_assets/assets/models/separation/vocals.fp16.onnx" in workflow
    assert "readelf -d \"$SHERPA_SO\" | grep -q 'libonnxruntime.so'" in workflow
    assert "sherpa-onnx-spleeter-2stems-fp16.tar.bz2" in workflow


def test_song_cover_uses_android_media_codec_to_prepare_common_audio_formats():
    integration = (ROOT / "tools/native/integrate.py").read_text(encoding="utf-8")
    screen = (ROOT / "tools/ui/song_cover_screen.dart").read_text(encoding="utf-8")
    assert "decodeAudioToWav(inputPath, decodedInput.absolutePath)" in integration
    assert "val segments = buildAudioSegments(durationUs)" in integration
    assert "decodeAudioSegment(source, segment.decodeStartUs, segment.decodeEndUs)" in integration
    assert "RandomAccessFile(File(outputPath), \"rw\")" in integration
    assert "output.write(pcm.array())" in integration
    assert "decodeAudioSegment(source, 0L, durationUs)" not in integration
    assert "writeDecodedAudioWav(File(outputPath), decoded)" not in integration
    assert "Android decodes it locally to PCM WAV" in screen
    assert "_getOrCreateStems" in screen
    assert "rvc_song_stems_" in screen
    assert "pickAndImportAudioFiles" in screen
    assert "FilePicker.platform.pickFiles" not in screen


def test_sherpa_runtime_diagnostic_matches_the_pinned_onnx_runtime_version():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "SHERPA_ONNX_ONNXRUNTIME_VERSION=1.28.0" in source
    assert "onnxruntime-android:1.28.0" in source
    assert "matching ONNX Runtime 1.28.0 library" in source
    assert "matching ONNX Runtime 1.28.2 library" not in source


def test_onnx_voice_models_are_opened_and_checked_for_the_exact_rvc_v2_inputs_before_selection():
    integration = (ROOT / "tools/native/integrate.py").read_text(encoding="utf-8")
    assert 'import ai.onnxruntime.OrtEnvironment' in integration
    assert '"validateVoiceModel" -> validateVoiceModel(call, result)' in integration
    assert 'setOf("phone", "phone_lengths", "pitch", "pitchf", "ds", "rnd")' in integration
    assert 'session.inputNames.toSet()' in integration
    assert 'session.inputInfo["phone"]?.info as? ai.onnxruntime.TensorInfo' in integration
    assert 'phoneShape.size == 3' in integration
    assert 'phoneShape[2] == 768L || phoneShape[2] == -1L' in integration
    assert 'not RVC v2 / 768-dimensional' in integration
    assert 'await _bridge.validateVoiceModel(imported.path)' in integration
    assert 'await _bridge.validateVoiceModel(path)' in integration
    assert 'MODEL NOT COMPATIBLE' in integration
    assert 'Future<void> validateVoiceModel(String modelPath)' in integration


def test_native_pth_converter_applies_real_faiss_retrieval_blending():
    patch = (ROOT / "tools/native/patch_faiss_mobile.py").read_text(encoding="utf-8")
    integration = (ROOT / "tools/native/integrate.py").read_text(encoding="utf-8")
    jni = (ROOT / "tools/native/rvc_pth_android/pth_jni.cpp").read_text(encoding="utf-8")
    pipeline = (ROOT / "tools/native/rvc_pth_android/pth_pipeline.c").read_text(encoding="utf-8")
    bridge = (ROOT / "tools/native/RvcPthNative.kt").read_text(encoding="utf-8")
    screen = (ROOT / "tools/ui/song_cover_screen.dart").read_text(encoding="utf-8")
    assert "nativeSearchAndBlend" in patch
    assert "faiss_Index_search" in patch
    assert "faiss_Index_reconstruct" in patch
    assert "nativePrepareForRvc" in patch
    assert "FAISS.readIndex(sourceIndex.absolutePath)" in integration
    assert "opened.prepareForRvc()" in integration
    assert "searchAndBlend" in jni
    assert "blend_index(index_context, phone, segment_frames, index_rate)" in pipeline
    assert "retrievalIndex: FAISS.Index?" in bridge
    assert "indexPath: widget.indexPath" in screen
    assert "RETRIEVAL STRENGTH" in screen
