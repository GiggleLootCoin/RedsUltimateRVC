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
        val decoded = decodeAudioSegment(source, 0L, durationUs)
        require(decoded.channelCount in 1..2) { "Only mono or stereo audio can be separated." }
        writeDecodedAudioWav(File(outputPath), decoded)
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
