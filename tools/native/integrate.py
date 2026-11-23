from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = Path('buildsrc')
PKG = BUILD / 'android/app/src/main/kotlin/com/ultimatervc/mobile'
PKG.mkdir(parents=True, exist_ok=True)

# Package the locally built ARM64 FAISS AAR so the on-device .index exporter
# is actually available to the Android plugin, not merely compiled in CI.
faiss_aar = ROOT / 'tools/native/faiss/faiss-android.aar'
if not faiss_aar.is_file() or faiss_aar.stat().st_size == 0:
    raise RuntimeError('Native FAISS Android AAR is missing; cannot enable on-phone index conversion.')
app_libs = BUILD / 'android/app/libs'
app_libs.mkdir(parents=True, exist_ok=True)
(app_libs / 'faiss-android.aar').write_bytes(faiss_aar.read_bytes())
app_gradle = BUILD / 'android/app/build.gradle'
gradle_text = app_gradle.read_text(encoding='utf-8')
faiss_dependency = "    implementation files('libs/faiss-android.aar')"
if faiss_dependency not in gradle_text:
    anchor = 'dependencies {'
    if gradle_text.count(anchor) != 1:
        raise RuntimeError('Could not uniquely locate Android app dependencies block for FAISS AAR.')
    gradle_text = gradle_text.replace(anchor, anchor + '\n' + faiss_dependency, 1)
    app_gradle.write_text(gradle_text, encoding='utf-8')
(PKG / 'SourceSeparationBridge.kt').write_text((ROOT / 'tools/native/SourceSeparationBridge.kt').read_text(), encoding='utf-8')
(PKG / 'RvcPthNative.kt').write_text((ROOT / 'tools/native/RvcPthNative.kt').read_text(), encoding='utf-8')
(PKG / 'FaissIndexConverter.kt').write_text((ROOT / 'tools/native/FaissIndexConverter.kt').read_text(encoding='utf-8'), encoding='utf-8')

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
if "import com.developermindset.faiss.FAISS" not in s:
    s = s.replace("package com.ultimatervc.mobile", "package com.ultimatervc.mobile" + chr(10) + chr(10) + "import com.developermindset.faiss.FAISS", 1)
if "import ai.onnxruntime.OrtEnvironment" not in s:
    s = s.replace("package com.ultimatervc.mobile", "package com.ultimatervc.mobile" + chr(10) + chr(10) + "import ai.onnxruntime.OrtEnvironment" + chr(10) + "import ai.onnxruntime.OrtSession", 1)
dispatch = '            "convertIndex" -> convertIndex(call, result)'
if '"convertFaissIndex" -> convertFaissIndex(call, result)' not in s:
    if dispatch not in s: raise RuntimeError('RVCPlugin convertIndex dispatch anchor missing for FAISS bridge')
    s = s.replace(dispatch, dispatch + '\n            "convertFaissIndex" -> convertFaissIndex(call, result)', 1)
if '"convertPth" -> convertPth(call, result)' not in s:
    if dispatch not in s: raise RuntimeError('RVCPlugin convertIndex dispatch anchor missing for PTH bridge')
    s = s.replace(dispatch, dispatch + '\n            "convertPth" -> convertPth(call, result)', 1)
if '"separateSongVocals" -> separateSongVocals(call, result)' not in s:
    if dispatch not in s:
        raise RuntimeError('RVCPlugin dispatch anchor missing')
    s = s.replace(dispatch, dispatch + '\n            "separateSongVocals" -> separateSongVocals(call, result)\n            "mixSongCover" -> mixSongCover(call, result)', 1)
if '"validateVoiceModel" -> validateVoiceModel(call, result)' not in s:
    if dispatch not in s:
        raise RuntimeError('RVCPlugin dispatch anchor missing for ONNX validation')
    s = s.replace(dispatch, dispatch + '\n            "validateVoiceModel" -> validateVoiceModel(call, result)', 1)

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

    private fun convertPth(call: MethodCall, result: Result) {
        val inputPath = call.argument<String>("inputWavPath")
        val modelPath = call.argument<String>("pthModelPath")
        val selectedIndexPath = call.argument<String>("indexPath")
        val pitchShift = (call.argument<Double>("pitchShift") ?: 0.0).toInt()
        val indexRate = (call.argument<Double>("indexRate") ?: 0.75).toFloat().coerceIn(0f, 1f)
        if (inputPath.isNullOrBlank() || modelPath.isNullOrBlank()) {
            result.error("INVALID_ARGUMENTS", "A vocal WAV and PTH model path are required.", null)
            return
        }
        scope.launch {
            var retrievalIndex: FAISS.Index? = null
            try {
                if (!selectedIndexPath.isNullOrBlank()) {
                    val selected = File(selectedIndexPath)
                    require(selected.isFile) { "The selected retrieval index is missing." }
                    val sourceIndex = if (selected.name.endsWith(".mobile.index", ignoreCase = true)) {
                        File(selected.parentFile, selected.name.substring(0, selected.name.length - ".mobile.index".length) + ".index")
                    } else selected
                    require(sourceIndex.isFile && sourceIndex.length() > 16L) {
                        "The mobile index is ready for ONNX conversion, but its original FAISS .index file is not beside it. Re-import the original .index to enable native PTH retrieval blending."
                    }
                    require(sourceIndex.length() <= 512L * 1024L * 1024L) {
                        "This FAISS index is larger than the 512 MB on-phone retrieval limit."
                    }
                    val activityManager = appContext.getSystemService(android.content.Context.ACTIVITY_SERVICE) as android.app.ActivityManager
                    val memoryInfo = android.app.ActivityManager.MemoryInfo()
                    activityManager.getMemoryInfo(memoryInfo)
                    val minimumAvailable = sourceIndex.length() * 3L / 2L + 192L * 1024L * 1024L
                    require(memoryInfo.availMem >= minimumAvailable) {
                        "There is not enough free memory to load this FAISS index safely. Close other apps and try again."
                    }
                    val opened = withContext(Dispatchers.IO) { FAISS.readIndex(sourceIndex.absolutePath) }
                    retrievalIndex = opened
                    require(opened.dimension() == 768 && opened.isTrained() && opened.ntotal() > 0L) {
                        "The selected FAISS index must be trained, non-empty and 768-dimensional for RVC v2."
                    }
                    withContext(Dispatchers.IO) { opened.prepareForRvc() }
                }

                val modelDir = File(appContext.filesDir, "rvc_pth_models").apply { mkdirs() }
                fun copyBundledModel(name: String): File {
                    val target = File(modelDir, name)
                    if (!target.isFile || target.length() == 0L) {
                        val temporary = File(modelDir, "$name.copying")
                        appContext.assets.open("flutter_assets/assets/models/$name").use { input ->
                            temporary.outputStream().use { output -> input.copyTo(output) }
                        }
                        require(temporary.isFile && temporary.length() > 1_000_000L) { "Bundled $name model is missing or incomplete." }
                        if (target.exists()) target.delete()
                        check(temporary.renameTo(target)) { "Could not install bundled $name model." }
                    }
                    require(target.isFile && target.length() > 1_000_000L) { "Bundled $name model is missing or empty." }
                    return target
                }
                val hubert = copyBundledModel("hubert.onnx")
                val rmvpe = copyBundledModel("rmvpe.onnx")
                val outputDir = File(appContext.filesDir, "outputs").apply { mkdirs() }
                val output = File(outputDir, "pth_cover_${System.currentTimeMillis()}.wav")
                val activeIndex = retrievalIndex
                val error = withContext(Dispatchers.IO) {
                    RvcPthNative().convertPth(
                        inputPath, modelPath, hubert.absolutePath, rmvpe.absolutePath,
                        output.absolutePath, pitchShift, activeIndex, indexRate
                    )
                }
                require(error.isNullOrEmpty()) { error ?: "Native PTH conversion failed." }
                require(output.isFile && output.length() > 44L) { "Native PTH conversion returned no usable WAV output." }
                withContext(Dispatchers.Main) { result.success(output.absolutePath) }
            } catch (e: UnsatisfiedLinkError) {
                withContext(Dispatchers.Main) {
                    result.error("PTH_LIBRARY_MISSING", "The native PTH inference library or FAISS retrieval runtime is not packaged in this APK.", null)
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    result.error("PTH_CONVERSION_FAILED", e.message ?: "Native PTH conversion failed.", null)
                }
            } finally {
                withContext(Dispatchers.IO) { retrievalIndex?.close() }
            }
        }
    }


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
faiss_method = '''
    private fun convertFaissIndex(call: MethodCall, result: Result) {
        val sourcePath = call.argument<String>("sourcePath")
        if (sourcePath.isNullOrBlank()) {
            result.error("INVALID_ARGUMENTS", "Missing source index path.", null)
            return
        }
        scope.launch {
            try {
                val imported = FaissIndexConverter.convert(appContext, File(sourcePath))
                withContext(Dispatchers.Main) { result.success(mapOf("path" to imported.path, "referenceCount" to imported.referenceCount, "lastUpdatedAtMs" to imported.lastUpdatedAtMs)) }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    result.error("FAISS_CONVERSION_FAILED", e.message ?: "On-device FAISS conversion failed.", null)
                }
            }
        }
    }

'''
# The dispatch entries above must have matching implementations inside RVCPlugin.
# Install the complete native conversion and source-separation handlers before
# the existing ONNX index converter, exactly once.
if 'private fun separateSongVocals(call: MethodCall, result: Result)' not in s:
    anchor = '    private fun convertIndex(call: MethodCall, result: Result) {'
    if anchor not in s:
        raise RuntimeError('RVCPlugin conversion-method insertion anchor missing')
    s = s.replace(anchor, methods + anchor, 1)

if 'private fun convertFaissIndex(call: MethodCall, result: Result)' not in s:
    anchor = '    private fun convertIndex(call: MethodCall, result: Result) {'
    if anchor not in s: raise RuntimeError('RVCPlugin convertIndex method anchor missing')
    s = s.replace(anchor, faiss_method + anchor, 1)
plugin.write_text(s, encoding='utf-8')

# Expose the native model preflight to Flutter.
bridge = BUILD / 'lib/services/rvc_bridge.dart'
bs = bridge.read_text(encoding='utf-8')
if 'Future<String> convertFaissIndex(String sourcePath)' not in bs:
    anchor = '  Future<String> convertIndex(String sourcePath) async {'
    method = '''  Future<ImportedFileHandle> convertFaissIndex(String sourcePath) async {
    try {
      final result = await _channel.invokeMethod('convertFaissIndex', {'sourcePath': sourcePath});
      return ImportedFileHandle.fromMap(Map<String, dynamic>.from(result as Map));
    } on PlatformException catch (e) {
      throw Exception('FAISS conversion failed: ${e.message}');
    }
  }

'''
    if anchor not in bs: raise RuntimeError('RVCBridge convertIndex anchor missing')
    bs = bs.replace(anchor, method + anchor, 1)
    bridge.write_text(bs, encoding='utf-8')

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
if "if (imported.path.toLowerCase().endsWith('.onnx')) await _bridge.validateVoiceModel(imported.path);" not in ps:
    import_selection = '        _selectedModelPath = imported.path;'
    if import_selection not in ps: raise RuntimeError('Model import selection anchor missing')
    ps = ps.replace(import_selection, "        if (imported.path.toLowerCase().endsWith('.onnx')) await _bridge.validateVoiceModel(imported.path);\n" + import_selection, 1)
if "if (path.toLowerCase().endsWith('.onnx')) await _bridge.validateVoiceModel(path);" not in ps:
    use_selection = '    _selectedModelPath = path;'
    if use_selection not in ps: raise RuntimeError('Model library use anchor missing')
    guard = '''    try {
      if (path.toLowerCase().endsWith('.onnx')) await _bridge.validateVoiceModel(path);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('MODEL NOT COMPATIBLE: $e')));
      return;
    }
'''
    ps = ps.replace(use_selection, guard + use_selection, 1)

# The upstream picker originally rejects every voice checkpoint except ONNX.
# Add the native PTH route to the picker itself; otherwise Android users can
# never select a .pth file even though the native runtime is packaged.
# The branded picker already validates .onnx/.pth via _runtime() and
# uses Android SAF without restrictive extension filters. Older upstream
# picker variants use the lowerPath predicate below; support both safely.
if "bool _runtime(String path) => ['onnx', 'pth'].contains(_ext(path));" not in ps and "return lowerPath.endsWith('.onnx') || lowerPath.endsWith('.pth');" not in ps:
    old_model_filter = "return lowerPath.endsWith('.onnx');"
    if old_model_filter not in ps:
        raise RuntimeError('Model picker has neither the branded ONNX/PTH runtime predicate nor the expected upstream ONNX filter')
    ps = ps.replace(old_model_filter,
        "return lowerPath.endsWith('.onnx') || lowerPath.endsWith('.pth');", 1)
ps = ps.replace("请选择 .onnx 模型文件", "Choose a compatible ONNX or supported RVC v2 PTH voice model")
ps = ps.replace("'支持：.onnx 模型'", "'Supported: RVC v2 PTH (768d / 100fps) or compatible ONNX'")
ps = ps.replace("Text('选择音色模型')", "Text('Select Voice Model')")
ps = ps.replace("Text('更换模型')", "Text('Change Model')")
ps = ps.replace("Text('选择模型')", "Text('Choose Model')")

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
if 'url_launcher:' not in pubspec_text:
    pubspec_text = pubspec_text.replace('dependencies:\n', 'dependencies:\n  url_launcher: ^6.3.1\n', 1)
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
if 'Future<String> convertPth({' not in bs:
    anchor = '  Future<void> startRecording() async {'
    if anchor not in bs: raise RuntimeError('RVCBridge insertion anchor missing for PTH method')
    bs = bs.replace(anchor, "  Future<String> convertPth({\n    required String inputWavPath,\n    required String pthModelPath,\n    String? indexPath,\n    double indexRate = 0.75,\n    int pitchShift = 0,\n  }) async {\n    final result = await _channel.invokeMethod<String>('convertPth', {\n      'inputWavPath': inputWavPath,\n      'pthModelPath': pthModelPath,\n      'indexPath': indexPath,\n      'indexRate': indexRate,\n      'pitchShift': pitchShift.toDouble(),\n    });\n    if (result == null || result.isEmpty) {\n      throw StateError('The native PTH converter did not return a converted WAV.');\n    }\n    return result;\n  }\n\n" + anchor, 1)
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
          if (selectedModel == null || !selectedModel.toLowerCase().endsWith('.pth')) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Choose your supported RVC v2 .pth voice model in Voice Library first. The converter does not require a user-supplied ONNX file.')),
            );
            return;
          }
          final selectedIndex = _selectedIndexPath;
          Navigator.of(context).push(MaterialPageRoute(builder: (_) => SongCoverScreen(
            modelPath: selectedModel,
            // Pass the selected original .index or .mobile.index. The native
            // PTH bridge resolves the original FAISS sidecar when necessary.
            indexPath: selectedIndex,
          )));
        },"""
if old in ms: ms = ms.replace(old, new, 1)
elif 'onSongCovers: () {' not in ms: raise RuntimeError('Song Covers dashboard callback missing')
main.write_text(ms, encoding='utf-8')

# Route the workspace's primary conversion entry directly into the native PTH
# song-cover pipeline. The legacy Generate screen only executes ONNX voice
# models and was the reason PTH users were still being asked for ONNX.
old_conversion = '''  void _openAudioConversion() {
    setState(() => _moduleIndex = 1);
    _saveState();
    _scaffoldKey.currentState?.closeDrawer();
  }'''
new_conversion = '''  void _openAudioConversion() {
    final selectedModel = _selectedModelPath;
    if (selectedModel == null || !selectedModel.toLowerCase().endsWith('.pth')) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Choose your compatible .pth voice model in Voice Library first.')),
      );
      _scaffoldKey.currentState?.closeDrawer();
      return;
    }
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => SongCoverScreen(
      modelPath: selectedModel,
      indexPath: _selectedIndexPath,
    )));
    _scaffoldKey.currentState?.closeDrawer();
  }'''
if old_conversion not in ms:
    raise RuntimeError('Could not locate legacy conversion entry point; refusing to leave ONNX-only navigation active.')
ms = ms.replace(old_conversion, new_conversion, 1)
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


