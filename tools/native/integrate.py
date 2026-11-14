from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = Path('buildsrc')
PKG = BUILD / 'android/app/src/main/kotlin/com/ultimatervc/mobile'
PKG.mkdir(parents=True, exist_ok=True)
(PKG / 'SourceSeparationBridge.kt').write_text((ROOT / 'tools/native/SourceSeparationBridge.kt').read_text(), encoding='utf-8')

cpp = BUILD / 'android/app/src/main/cpp'
cpp.mkdir(parents=True, exist_ok=True)
for name in ('source_separation_jni.cpp', 'CMakeLists.txt'):
    (cpp / name).write_text((ROOT / 'tools/native' / name).read_text(), encoding='utf-8')

engine = BUILD / 'android/app/src/main/kotlin/com/ultimatervc/mobile/RvcInferenceEngine.kt'
es = engine.read_text(encoding='utf-8')
decode_anchor = '    private fun decodeAudioSegment(file: File, startUs: Long, endUs: Long): DecodedAudio {'
decode_method = '''    fun decodeAudioToWav(inputPath: String, outputPath: String) {
        val source = File(inputPath)
        require(source.isFile) { "The selected audio file does not exist." }
        val durationUs = readAudioDurationUs(source)
        require(durationUs > 0L) { "Could not determine the selected audio duration." }

        val segments = buildAudioSegments(durationUs)
        val output = RandomAccessFile(File(outputPath), "rw")
        var totalDataBytes = 0L
        var outputSampleRate = 0
        var outputChannels = 0
        try {
            output.setLength(0L)
            output.write(ByteArray(44))
            segments.forEach { segment ->
                val decoded = decodeAudioSegment(source, segment.decodeStartUs, segment.decodeEndUs)
                require(decoded.channelCount in 1..2) { "Only mono or stereo audio can be separated." }
                require(decoded.sampleRate > 0) { "The audio decoder returned an invalid sample rate." }
                if (outputSampleRate == 0) {
                    outputSampleRate = decoded.sampleRate
                    outputChannels = decoded.channelCount
                }
                require(decoded.sampleRate == outputSampleRate && decoded.channelCount == outputChannels) {
                    "The audio format changed while decoding the file."
                }
                require(decoded.samples.size % outputChannels == 0) {
                    "The audio decoder returned an incomplete PCM frame."
                }

                val frames = decoded.samples.size / outputChannels
                val leadingFrames = (((segment.centerStartUs - segment.decodeStartUs).coerceAtLeast(0L) *
                    outputSampleRate.toLong()) / 1_000_000L).toInt()
                val centerFrames = (((segment.centerEndUs - segment.centerStartUs).coerceAtLeast(0L) *
                    outputSampleRate.toLong()) / 1_000_000L).toInt()
                val startFrame = leadingFrames.coerceIn(0, frames)
                val endFrame = (startFrame + centerFrames).coerceIn(startFrame, frames)
                val sampleStart = startFrame * outputChannels
                val sampleEnd = endFrame * outputChannels
                val sampleCount = sampleEnd - sampleStart
                if (sampleCount > 0) {
                    val pcm = ByteBuffer.allocate(sampleCount * 2).order(ByteOrder.LITTLE_ENDIAN)
                    for (index in sampleStart until sampleEnd) {
                        val clipped = decoded.samples[index].coerceIn(-1f, 1f)
                        pcm.putShort((clipped * Short.MAX_VALUE).roundToInt().toShort())
                    }
                    output.write(pcm.array())
                    totalDataBytes += sampleCount.toLong() * 2L
                    require(totalDataBytes <= Int.MAX_VALUE.toLong() - 36L) {
                        "The decoded WAV would exceed the supported 2 GB file size."
                    }
                }
            }

            require(totalDataBytes > 0L && outputSampleRate > 0 && outputChannels in 1..2) {
                "The audio decoder produced no usable PCM samples."
            }
            val header = ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN)
            header.put("RIFF".toByteArray(Charsets.US_ASCII))
            header.putInt((36L + totalDataBytes).toInt())
            header.put("WAVE".toByteArray(Charsets.US_ASCII))
            header.put("fmt ".toByteArray(Charsets.US_ASCII))
            header.putInt(16)
            header.putShort(1)
            header.putShort(outputChannels.toShort())
            header.putInt(outputSampleRate)
            header.putInt(outputSampleRate * outputChannels * 2)
            header.putShort((outputChannels * 2).toShort())
            header.putShort(16)
            header.put("data".toByteArray(Charsets.US_ASCII))
            header.putInt(totalDataBytes.toInt())
            output.seek(0L)
            output.write(header.array())
            output.fd.sync()
        } finally {
            output.close()
        }
    }

'''
if 'fun decodeAudioToWav(inputPath: String, outputPath: String)' not in es:
    if decode_anchor not in es: raise RuntimeError('Audio decoder insertion anchor missing')
    es = es.replace(decode_anchor, decode_method + decode_anchor, 1)
engine.write_text(es, encoding='utf-8')

plugin = PKG / 'RVCPlugin.kt'
s = plugin.read_text(encoding='utf-8')
dispatch = '            "convertIndex" -> convertIndex(call, result)'
if '"separateSongVocals" -> separateSongVocals(call, result)' not in s:
    if dispatch not in s:
        raise RuntimeError('RVCPlugin dispatch anchor missing')
    s = s.replace(dispatch, dispatch + '\n            "separateSongVocals" -> separateSongVocals(call, result)\n            "mixSongCover" -> mixSongCover(call, result)', 1)
methods = '''
    private fun separateSongVocals(call: MethodCall, result: Result) {
        val inputPath = call.argument<String>("inputPath")
        if (inputPath.isNullOrBlank()) { result.error("INVALID_ARGUMENTS", "Missing input WAV path.", null); return }
        scope.launch {
            try {
                val modelDir = File(appContext.filesDir, "song_cover_models").apply { mkdirs() }
                fun bundledModel(name: String): File {
                    val target = File(modelDir, name)
                    if (!target.exists() || target.length() == 0L) {
                        appContext.assets.open("flutter_assets/assets/models/separation/$name").use { input -> target.outputStream().use { output -> input.copyTo(output) } }
                    }
                    require(target.length() > 0L) { "Bundled separation model is empty: $name" }
                    return target
                }
                val vocalsModel = bundledModel("vocals.fp16.onnx")
                val accompanimentModel = bundledModel("accompaniment.fp16.onnx")
                val outputDir = File(appContext.filesDir, "song_covers").apply { mkdirs() }
                val stamp = System.currentTimeMillis()
                val vocals = File(outputDir, "vocals_$stamp.wav")
                val accompaniment = File(outputDir, "accompaniment_$stamp.wav")
                val decodedInput = File(outputDir, "decoded_$stamp.wav")
                try {
                    RvcInferenceEngine(
                        modelsDir = File(getModelsDirectory()),
                        resumableJobStore = ResumableInferenceJobStore(appContext.filesDir),
                    ).decodeAudioToWav(inputPath, decodedInput.absolutePath)
                    SourceSeparationBridge.separateWav(decodedInput.absolutePath, vocals.absolutePath, accompaniment.absolutePath, vocalsModel.absolutePath, accompanimentModel.absolutePath, 1)
                } finally {
                    decodedInput.delete()
                }
                withContext(Dispatchers.Main) { result.success(mapOf("vocalsPath" to vocals.absolutePath, "accompanimentPath" to accompaniment.absolutePath)) }
            } catch (e: Exception) { withContext(Dispatchers.Main) { result.error("SEPARATION_FAILED", e.message ?: "Offline vocal separation failed.", null) } }
        }
    }

    private fun mixSongCover(call: MethodCall, result: Result) {
        val vocalsPath = call.argument<String>("vocalsPath")
        val accompanimentPath = call.argument<String>("accompanimentPath")
        if (vocalsPath.isNullOrBlank() || accompanimentPath.isNullOrBlank()) { result.error("INVALID_ARGUMENTS", "Missing song-cover stem paths.", null); return }
        val vocalGain = (call.argument<Double>("vocalGain") ?: 1.0).toFloat().coerceIn(0f, 2f)
        val accompanimentGain = (call.argument<Double>("accompanimentGain") ?: 0.85).toFloat().coerceIn(0f, 2f)
        scope.launch {
            try {
                val outputDir = File(appContext.filesDir, "outputs").apply { mkdirs() }
                val output = File(outputDir, "song_cover_${System.currentTimeMillis()}.wav")
                SourceSeparationBridge.mixWav(vocalsPath, accompanimentPath, output.absolutePath, vocalGain, accompanimentGain)
                withContext(Dispatchers.Main) { result.success(output.absolutePath) }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) { result.error("MIX_FAILED", e.message ?: "Could not mix the song-cover stems.", null) }
            }
        }
    }

'''
anchor = '    private fun convertIndex(call: MethodCall, result: Result) {'
if 'private fun separateSongVocals(call: MethodCall, result: Result)' not in s:
    if anchor not in s: raise RuntimeError('RVCPlugin convertIndex anchor missing')
    s = s.replace(anchor, methods + anchor, 1)

# Validate the ONNX graph before presenting a model as runnable. Extension-only
# checks allowed incompatible ONNX exports to appear ready until inference failed.
if 'import ai.onnxruntime.OrtEnvironment' not in s:
    s = s.replace('package com.ultimatervc.mobile\n', 'package com.ultimatervc.mobile\n\nimport ai.onnxruntime.OrtEnvironment\nimport ai.onnxruntime.OrtSession\n', 1)
dispatch_anchor = '            "infer" -> infer(call, result)'
if '"validateVoiceModel" -> validateVoiceModel(call, result)' not in s:
    if dispatch_anchor not in s: raise RuntimeError('RVCPlugin inference dispatch anchor missing')
    s = s.replace(dispatch_anchor, '            "validateVoiceModel" -> validateVoiceModel(call, result)\n' + dispatch_anchor, 1)
validation = '''
    private fun validateVoiceModel(call: MethodCall, result: Result) {
        val path = call.argument<String>("modelPath")
        if (path.isNullOrBlank()) {
            result.error("INVALID_ARGUMENTS", "Choose an ONNX voice model first.", null)
            return
        }
        scope.launch {
            try {
                val model = File(path)
                require(model.isFile && model.length() > 0L) { "The selected ONNX model is missing or empty." }
                require(model.extension.equals("onnx", ignoreCase = true)) {
                    "This Android engine runs ONNX models. PTH/PT checkpoints must be exported first."
                }
                val validation = OrtSession.SessionOptions().use { options ->
                    val session = OrtEnvironment.getEnvironment().createSession(model.absolutePath, options)
                    try {
                        val actualInputs = session.inputNames.toSet()
                        val requiredInputs = setOf("phone", "phone_lengths", "pitch", "pitchf", "ds", "rnd")
                        val missing = requiredInputs - actualInputs
                        val phoneInfo = session.inputInfo["phone"]?.info as? ai.onnxruntime.TensorInfo
                        val phoneShape = phoneInfo?.shape
                        val phoneDimensionOk = phoneShape != null && phoneShape.size == 3 &&
                            (phoneShape[2] == 768L || phoneShape[2] == -1L)
                        val compatible = missing.isEmpty() && phoneDimensionOk
                        val message = when {
                            missing.isNotEmpty() ->
                                "This ONNX file is missing RVC v2 inputs: ${missing.sorted().joinToString()}. Found: ${actualInputs.sorted().joinToString()}."
                            !phoneDimensionOk ->
                                "This model's phone input is not RVC v2 / 768-dimensional. The app requires [1, frames, 768]; found: ${phoneShape?.contentToString() ?: "unknown"}."
                            else -> "Compatible RVC v2 ONNX model (768-dimensional phone input)."
                        }
                        Triple(compatible, message, actualInputs.sorted())
                    } finally {
                        session.close()
                    }
                }
                withContext(Dispatchers.Main) {
                    result.success(mapOf("compatible" to validation.first, "message" to validation.second, "inputs" to validation.third))
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    result.error("MODEL_VALIDATION_FAILED", e.message ?: "Could not open the ONNX model.", null)
                }
            }
        }
    }

'''
if 'private fun validateVoiceModel(call: MethodCall, result: Result)' not in s:
    anchor = '    private fun convertIndex(call: MethodCall, result: Result) {'
    if anchor not in s: raise RuntimeError('RVCPlugin convertIndex anchor missing')
    s = s.replace(anchor, validation + anchor, 1)
plugin.write_text(s, encoding='utf-8')

# Expose the native model preflight to Flutter.
bridge = BUILD / 'lib/services/rvc_bridge.dart'
bs = bridge.read_text(encoding='utf-8')
if 'Future<void> validateVoiceModel(String modelPath)' not in bs:
    anchor = '  Future<void> startRecording() async {'
    method = '''  Future<void> validateVoiceModel(String modelPath) async {
    final raw = await _channel.invokeMethod('validateVoiceModel', {'modelPath': modelPath});
    final data = Map<String, dynamic>.from(raw as Map);
    if (data['compatible'] != true) {
      throw StateError(data['message'] as String? ?? 'The selected ONNX model is not compatible with RVC v2.');
    }
  }

'''
    if anchor not in bs: raise RuntimeError('RVCBridge insertion anchor missing')
    bridge.write_text(bs.replace(anchor, method + anchor, 1), encoding='utf-8')

# Validate both newly imported and previously stored ONNX files before selection.
picker = BUILD / 'lib/screens/model_picker_screen.dart'
ps = picker.read_text(encoding='utf-8')
if 'await _bridge.validateVoiceModel(imported.path);' not in ps:
    import_selection = '        _selectedModelPath = imported.path;'
    if import_selection not in ps: raise RuntimeError('Model import selection anchor missing')
    ps = ps.replace(import_selection, '        await _bridge.validateVoiceModel(imported.path);\n' + import_selection, 1)
if 'await _bridge.validateVoiceModel(path);' not in ps:
    use_selection = '    _selectedModelPath = path;'
    if use_selection not in ps: raise RuntimeError('Model library use anchor missing')
    guard = '''    try {
      await _bridge.validateVoiceModel(path);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('MODEL NOT COMPATIBLE: $e')));
      return;
    }
'''
    ps = ps.replace(use_selection, guard + use_selection, 1)
picker.write_text(ps, encoding='utf-8')

plugin.write_text(s, encoding='utf-8')

gradle = BUILD / 'android/app/build.gradle'
g = gradle.read_text(encoding='utf-8')
if 'src/main/cpp/CMakeLists.txt' not in g:
    g = g.replace("        ndk {\n            abiFilters 'arm64-v8a'\n        }\n", "        ndk {\n            abiFilters 'arm64-v8a'\n        }\n        externalNativeBuild { cmake { cppFlags '-std=c++17' } }\n", 1)
    g = g.replace("\n}\n\nflutter {\n", "\n    externalNativeBuild { cmake { path file('src/main/cpp/CMakeLists.txt'); version '3.22.1' } }\n}\n\nflutter {\n", 1)
if 'src/main/cpp/CMakeLists.txt' not in g: raise RuntimeError('Could not configure Android CMake')
gradle.write_text(g, encoding='utf-8')

# Install the Flutter song-cover screen and expose the native operations.
# Include the separately bundled Spleeter ONNX models in Flutter's asset manifest.
pubspec = BUILD / 'pubspec.yaml'
pubspec_text = pubspec.read_text(encoding='utf-8')
separation_asset = '    - assets/models/separation/\n'
if separation_asset not in pubspec_text:
    model_asset = '    - assets/models/\n'
    if model_asset not in pubspec_text:
        raise RuntimeError('Flutter model asset declaration missing')
    pubspec_text = pubspec_text.replace(model_asset, model_asset + separation_asset, 1)
    pubspec.write_text(pubspec_text, encoding='utf-8')

screen_source = ROOT / 'tools/ui/song_cover_screen.dart'
screen_target = BUILD / 'lib/screens/song_cover_screen.dart'
screen_target.parent.mkdir(parents=True, exist_ok=True)
screen_target.write_text(screen_source.read_text(encoding='utf-8'), encoding='utf-8')

bridge = BUILD / 'lib/services/rvc_bridge.dart'
bs = bridge.read_text(encoding='utf-8')
if 'Future<Map<String, String>> separateSongVocals' not in bs:
    anchor = '  Future<void> startRecording() async {'
    methods = '''  Future<Map<String, String>> separateSongVocals(String inputPath) async {
    final result = await _channel.invokeMethod('separateSongVocals', {
      'inputPath': inputPath,
    });
    final values = Map<String, dynamic>.from(result as Map);
    final vocals = values['vocalsPath'];
    final accompaniment = values['accompanimentPath'];
    if (vocals is! String || accompaniment is! String) {
      throw StateError('The separation engine returned incomplete stem paths.');
    }
    return {'vocalsPath': vocals, 'accompanimentPath': accompaniment};
  }

  Future<String> mixSongCover({
    required String convertedVocalsPath,
    required String accompanimentPath,
    double vocalGain = 1.0,
    double accompanimentGain = 0.85,
  }) async {
    final result = await _channel.invokeMethod('mixSongCover', {
      'vocalsPath': convertedVocalsPath,
      'accompanimentPath': accompanimentPath,
      'vocalGain': vocalGain,
      'accompanimentGain': accompanimentGain,
    });
    if (result is! String || result.isEmpty) {
      throw StateError('The audio mixer did not return an output path.');
    }
    return result;
  }

'''
    if anchor not in bs: raise RuntimeError('RVCBridge insertion anchor missing')
    bs = bs.replace(anchor, methods + anchor, 1)
bridge.write_text(bs, encoding='utf-8')

main = BUILD / 'lib/main.dart'
ms = main.read_text(encoding='utf-8')
if "import 'screens/song_cover_screen.dart';" not in ms:
    anchor = "import 'screens/pitch_detection_screen.dart';"
    if anchor not in ms: raise RuntimeError('main.dart import anchor missing')
    ms = ms.replace(anchor, anchor + "\nimport 'screens/song_cover_screen.dart';", 1)
old = 'onSongCovers: _openAudioConversion,'
new = """onSongCovers: () {
          final selectedModel = _selectedModelPath;
          if (selectedModel == null || !selectedModel.toLowerCase().endsWith('.onnx')) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Select a compatible ONNX voice in Model Library first. PTH/PT files must be converted before use.')),
            );
            return;
          }
          final selectedIndex = _selectedIndexPath;
          final mobileIndex = selectedIndex != null && selectedIndex.toLowerCase().endsWith('.mobile.index')
              ? selectedIndex
              : null;
          Navigator.of(context).push(MaterialPageRoute(builder: (_) => SongCoverScreen(
            modelPath: selectedModel,
            indexPath: mobileIndex,
          )));
        },"""
if old in ms: ms = ms.replace(old, new, 1)
elif 'onSongCovers: () {' not in ms: raise RuntimeError('Song Covers dashboard callback missing')
main.write_text(ms, encoding='utf-8')


# Keep the app's Java API and Sherpa-ONNX native library on the same ONNX Runtime release.
ort_gradle = BUILD / 'android/app/build.gradle'
ort_text = ort_gradle.read_text(encoding='utf-8')
ort_text = ort_text.replace('com.microsoft.onnxruntime:onnxruntime-android:1.20.0', 'com.microsoft.onnxruntime:onnxruntime-android:1.28.0')
ort_gradle.write_text(ort_text, encoding='utf-8')

# The upstream mobile template pins an old Kotlin compiler in some build paths.
# AndroidX artifacts bundled with the current engine use Kotlin 1.8 metadata.
settings_gradle = BUILD / 'android/settings.gradle'
if settings_gradle.exists():
    settings_text = settings_gradle.read_text(encoding='utf-8')
    settings_text = settings_text.replace(
        'id "org.jetbrains.kotlin.android" version "1.8.10" apply false',
        'id "org.jetbrains.kotlin.android" version "1.8.22" apply false',
    )
    settings_gradle.write_text(settings_text, encoding='utf-8')

root_gradle = BUILD / 'android/build.gradle'
if root_gradle.exists():
    root_text = root_gradle.read_text(encoding='utf-8')
    root_text = root_text.replace(
        'org.jetbrains.kotlin:kotlin-gradle-plugin:1.8.10',
        'org.jetbrains.kotlin:kotlin-gradle-plugin:1.8.22',
    )
    root_gradle.write_text(root_text, encoding='utf-8')


# Optional native GGUF runtime integration. CI supplies the prebuilt Android ARM64
# JNI library through RVC_GGML_ANDROID_SO; source-only checks remain possible
# without downloading or compiling model weights.
ggml_bridge = ROOT / 'tools/native/RvcGgmlNative.kt'
(PKG / 'RvcGgmlNative.kt').write_text(ggml_bridge.read_text(encoding='utf-8'), encoding='utf-8')

import os
import shutil

ggml_so = os.environ.get('RVC_GGML_ANDROID_SO', '')
if ggml_so:
    source_so = Path(ggml_so)
    if not source_so.is_file() or source_so.stat().st_size == 0:
        raise RuntimeError(f'RVC_GGML_ANDROID_SO is missing or empty: {source_so}')
    jni_dir = BUILD / 'android/app/src/main/jniLibs/arm64-v8a'
    jni_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_so, jni_dir / 'libred_rvc_ggml.so')

# Expose the CPU-only GGUF conversion method through the existing Flutter channel.
plugin = PKG / 'RVCPlugin.kt'
plugin_text = plugin.read_text(encoding='utf-8')
ggml_dispatch = '            "convertGguf" -> convertGguf(call, result)'
if ggml_dispatch not in plugin_text:
    anchor = '            "convertIndex" -> convertIndex(call, result)'
    if anchor not in plugin_text:
        raise RuntimeError('RVCPlugin convertIndex dispatch anchor missing for GGUF bridge')
    plugin_text = plugin_text.replace(anchor, anchor + '\n' + ggml_dispatch, 1)

ggml_method = '''
    private fun convertGguf(call: MethodCall, result: Result) {
        val hubertPath = call.argument<String>("hubertPath")
        val rmvpePath = call.argument<String>("rmvpePath")
        val voicePath = call.argument<String>("voicePath")
        val indexPath = call.argument<String>("indexPath") ?: ""
        val inputPath = call.argument<String>("inputPath")
        val outputPath = call.argument<String>("outputPath")
        if (listOf(hubertPath, rmvpePath, voicePath, inputPath, outputPath).any { it.isNullOrBlank() }) {
            result.error("INVALID_ARGUMENTS", "HuBERT, RMVPE, voice GGUF and input/output WAV paths are required.", null)
            return
        }
        val pitch = call.argument<Int>("pitch") ?: 0
        val sid = call.argument<Int>("speakerId") ?: 0
        val indexRate = (call.argument<Double>("indexRate") ?: 0.0).toFloat()
        val protect = (call.argument<Double>("protect") ?: 0.33).toFloat()
        val rmsMix = (call.argument<Double>("rmsMixRate") ?: 0.25).toFloat()
        scope.launch {
            try {
                val output = File(outputPath!!)
                output.parentFile?.mkdirs()
                val error = RvcGgmlNative.convert(
                    hubertPath!!, rmvpePath!!, voicePath!!, indexPath,
                    inputPath!!, output.absolutePath, pitch, sid, indexRate, protect, rmsMix
                )
                require(error.isEmpty()) { error }
                require(output.isFile && output.length() > 44L) { "Native RVC returned no usable WAV output." }
                withContext(Dispatchers.Main) { result.success(output.absolutePath) }
            } catch (e: UnsatisfiedLinkError) {
                withContext(Dispatchers.Main) {
                    result.error("GGML_LIBRARY_MISSING", "The native RVC library is not packaged in this APK.", null)
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    result.error("GGML_CONVERSION_FAILED", e.message ?: "Native GGUF conversion failed.", null)
                }
            }
        }
    }

'''
if 'private fun convertGguf(call: MethodCall, result: Result)' not in plugin_text:
    anchor = '    private fun convertIndex(call: MethodCall, result: Result) {'
    if anchor not in plugin_text:
        raise RuntimeError('RVCPlugin convertIndex method anchor missing for GGUF bridge')
    plugin_text = plugin_text.replace(anchor, ggml_method + anchor, 1)
plugin.write_text(plugin_text, encoding='utf-8')

bridge = BUILD / 'lib/services/rvc_bridge.dart'
bridge_text = bridge.read_text(encoding='utf-8')
if 'Future<String> convertGguf({' not in bridge_text:
    anchor = '  Future<void> startRecording() async {'
    dart_method = '''
  /// Run the experimental, fully local CPU-only RVC-GGUF inference backend.
  /// The three GGUF model files must already have been exported from source checkpoints.
  Future<String> convertGguf({
    required String hubertPath,
    required String rmvpePath,
    required String voicePath,
    String? indexPath,
    required String inputPath,
    required String outputPath,
    int pitch = 0,
    int speakerId = 0,
    double indexRate = 0.0,
    double protect = 0.33,
    double rmsMixRate = 0.25,
  }) async {
    final result = await _channel.invokeMethod<String>('convertGguf', {
      'hubertPath': hubertPath,
      'rmvpePath': rmvpePath,
      'voicePath': voicePath,
      'indexPath': indexPath ?? '',
      'inputPath': inputPath,
      'outputPath': outputPath,
      'pitch': pitch,
      'speakerId': speakerId,
      'indexRate': indexRate,
      'protect': protect,
      'rmsMixRate': rmsMixRate,
    });
    if (result == null || result.isEmpty) {
      throw StateError('The native RVC engine did not return an output file.');
    }
    return result;
  }

'''
    if anchor not in bridge_text:
        raise RuntimeError('RVCBridge insertion anchor missing for GGUF method')
    bridge_text = bridge_text.replace(anchor, dart_method + anchor, 1)
bridge.write_text(bridge_text, encoding='utf-8')

# Make the experimental native GGUF converter reachable from the app drawer.
# Song Covers remains the separate ONNX workflow; this screen requires
# pre-exported HuBERT, RMVPE and voice GGUF files.
converter_source = ROOT / 'tools/ui/model_converter_screen.dart'
converter_target = BUILD / 'lib/screens/model_converter_screen.dart'
converter_target.parent.mkdir(parents=True, exist_ok=True)
converter_target.write_text(converter_source.read_text(encoding='utf-8'), encoding='utf-8')

main = BUILD / 'lib/main.dart'
ms = main.read_text(encoding='utf-8')
if "import 'screens/model_converter_screen.dart';" not in ms:
    import_anchor = "import 'screens/song_cover_screen.dart';"
    if import_anchor not in ms:
        raise RuntimeError('Song-cover import anchor missing for native GGUF screen')
    ms = ms.replace(import_anchor, import_anchor + "\nimport 'screens/model_converter_screen.dart';", 1)

open_converter = '''  void _openModelConverter() {
    setState(() => _moduleIndex = 8);
    _saveState();
    _scaffoldKey.currentState?.closeDrawer();
  }

'''
if 'void _openModelConverter()' not in ms:
    anchor = '  Drawer _buildDrawer() {'
    if anchor not in ms:
        raise RuntimeError('Drawer builder anchor missing for native GGUF screen')
    ms = ms.replace(anchor, open_converter + anchor, 1)

drawer_item = '''          ListTile(
            leading: Icon(Icons.memory),
            title: Text("Native GGUF Runner"),
            selected: _moduleIndex == 8,
            onTap: _openModelConverter,
          ),
'''
if 'title: Text("Native GGUF Converter")' not in ms:
    anchor = '''          ListTile(leading: const Icon(Icons.multitrack_audio), title: const Text('Pitch Detection'), selected: _moduleIndex == 7, onTap: _openPitchDetection),
'''
    if anchor not in ms:
        raise RuntimeError('Pitch detection drawer item anchor missing')
    ms = ms.replace(anchor, anchor + drawer_item, 1)

screen_entry = '      ModelConverterScreen(),'
if screen_entry not in ms:
    anchor = '      PitchDetectionScreen(isActive: _moduleIndex == 7),'
    if anchor not in ms:
        raise RuntimeError('Pitch detection module screen anchor missing')
    ms = ms.replace(anchor, anchor + '\n' + screen_entry, 1)

main.write_text(ms, encoding='utf-8')

