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
                SourceSeparationBridge.separateWav(inputPath, vocals.absolutePath, accompaniment.absolutePath, vocalsModel.absolutePath, accompanimentModel.absolutePath, 1)
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
        try {
            val outputDir = File(appContext.filesDir, "outputs").apply { mkdirs() }
            val output = File(outputDir, "song_cover_${System.currentTimeMillis()}.wav")
            SourceSeparationBridge.mixWav(vocalsPath, accompanimentPath, output.absolutePath, vocalGain, accompanimentGain)
            result.success(output.absolutePath)
        } catch (e: Exception) { result.error("MIX_FAILED", e.message ?: "Could not mix the song-cover stems.", null) }
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
          if (_selectedModelPath == null) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Select a compatible ONNX voice in Model Library first.')),
            );
            return;
          }
          Navigator.of(context).push(MaterialPageRoute(builder: (_) => SongCoverScreen(
            modelPath: _selectedModelPath!,
            indexPath: _selectedIndexPath,
          )));
        },"""
if old in ms: ms = ms.replace(old, new, 1)
elif 'onSongCovers: () {' not in ms: raise RuntimeError('Song Covers dashboard callback missing')
main.write_text(ms, encoding='utf-8')

