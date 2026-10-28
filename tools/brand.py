import re
from pathlib import Path
import urllib.request

root = Path("buildsrc")
repo_root = Path(__file__).resolve().parent.parent

# Install the intended Android dashboard/training workspace into the upstream app.
for ui_name in ("red_home_screen.dart", "training_screen.dart"):
    source_ui = repo_root / "tools" / "ui" / ui_name
    target_ui = root / "lib" / "screens" / ui_name
    target_ui.parent.mkdir(parents=True, exist_ok=True)
    target_ui.write_text(source_ui.read_text(encoding="utf-8"), encoding="utf-8")


# Approved Red's Ultimate RVC artwork created for this project.
LOGO_URL = "https://cdn.websitepublisher.ai/custom/wid25042/images/reds-ultimate-rvc-logo.svg"
logo_svg = root / "assets" / "images" / "reds-ultimate-rvc-logo.svg"
logo_svg.parent.mkdir(parents=True, exist_ok=True)
urllib.request.urlretrieve(LOGO_URL, logo_svg)


def replace_in(path, replacements):
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")

def regex_replace(path, pattern, replacement):
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text)
    if count == 0:
        raise RuntimeError(f"Required compatibility patch did not match: {path}")
    path.write_text(updated, encoding="utf-8")

replace_in(
    root / "lib" / "main.dart",
    [
        ("Ultimate RVC Mobile", "Red\\'s Ultimate RVC"),
        ("音频推理", "Audio Conversion"),
        ("实时推理", "Realtime"),
        ("变声器模式", "Voice Changer"),
        ("分贝仪", "dB Meter"),
        ("音高检测", "Pitch Detection"),
        ("参数解释", "RVC Controls"),
        ("mobile.index 转换教程", "Index Converter"),
        ("primarySwatch: Colors.blue,", "primarySwatch: Colors.red,"),
        ("backgroundColor: Colors.white", "backgroundColor: const Color(0xFF09090D)"),
    ],
)

# Brand the upstream drawer header with the approved artwork.
s_drawer = (root / "lib" / "main.dart").read_text(encoding="utf-8")
s_drawer = s_drawer.replace("child: Text('Ultimate RVC', style: Theme.of(context).textTheme.headlineSmall),", "child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.end, children: [SizedBox(height: 74, child: SvgPicture.asset('assets/images/reds-ultimate-rvc-logo.svg', fit: BoxFit.contain, alignment: Alignment.centerLeft)), const SizedBox(height: 8), const Text(\"RED'S ULTIMATE RVC\", style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800)), const SizedBox(height: 4), const Text('Local Android voice conversion', style: TextStyle(color: Color(0xFFB8B8C2), fontSize: 12))]),")
(root / "lib" / "main.dart").write_text(s_drawer, encoding="utf-8")

# Keep upstream test imports valid after renaming the Flutter package.
for dart in (root / "test").rglob("*.dart"):
    content = dart.read_text(encoding="utf-8")
    content = content.replace("package:ultimate_rvc_mobile/", "package:reds_ultimate_rvc/")
    dart.write_text(content, encoding="utf-8")


# Make Android model/index selection practical on Samsung's document picker.
# The upstream screen used FileType.any and then rejected everything except ONNX,
# which made common .pth RVC models appear unusable. We explicitly expose the
# formats the app can store, while clearly distinguishing inference-ready ONNX
# from source .pth models.
# Restore only files that still exist. Android/Flutter temp paths can disappear
# between launches; never reopen a stale cached selection.
main_state = root / "lib" / "main.dart"
main_text = main_state.read_text(encoding="utf-8")
load_pattern = r'  Future<void> _loadSavedState\(\) async \{.*?\n  \}\n\n  Future<void> _saveState'
load_replacement = '''  Future<void> _loadSavedState() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;

    String? existingPath(String? path) {
      if (path == null || path.isEmpty) return null;
      return File(path).existsSync() ? path : null;
    }

    final songPath = existingPath(prefs.getString('selectedSongPath'));
    final modelPath = existingPath(prefs.getString('selectedModelPath'));
    final indexPath = existingPath(prefs.getString('selectedIndexPath'));
    final outputPath = existingPath(prefs.getString('generatedOutputPath'));

    if (songPath == null) {
      await prefs.remove('selectedSongPath');
      await prefs.remove('selectedSongDisplayName');
    }
    if (modelPath == null) {
      await prefs.remove('selectedModelPath');
      await prefs.remove('selectedModelDisplayName');
    }
    if (indexPath == null) {
      await prefs.remove('selectedIndexPath');
      await prefs.remove('selectedIndexDisplayName');
    }
    if (outputPath == null) {
      await prefs.remove('generatedOutputPath');
      await prefs.remove('generationDurationMs');
    }

    setState(() {
      _selectedSongPath = songPath;
      _selectedSongDisplayName = songPath == null ? null : (prefs.getString('selectedSongDisplayName') ?? File(songPath).uri.pathSegments.last);
      _selectedModelPath = modelPath;
      _selectedModelDisplayName = modelPath == null ? null : (prefs.getString('selectedModelDisplayName') ?? File(modelPath).uri.pathSegments.last);
      _selectedIndexPath = indexPath;
      _selectedIndexDisplayName = indexPath == null ? null : (prefs.getString('selectedIndexDisplayName') ?? File(indexPath).uri.pathSegments.last);
      _generatedOutputPath = outputPath;
      final generationDurationMs = outputPath == null ? null : prefs.getInt('generationDurationMs');
      _generationDuration = generationDurationMs == null ? null : Duration(milliseconds: generationDurationMs);
      _moduleIndex = prefs.getInt('moduleIndex') ?? 0;
      _audioStepIndex = prefs.getInt('audioStepIndex') ?? 0;
      if (_selectedSongPath == null) {
        _audioStepIndex = 0;
      } else if (_selectedModelPath == null && _audioStepIndex > 1) {
        _audioStepIndex = 1;
      } else if (_selectedModelPath != null && _generatedOutputPath == null && _audioStepIndex > 2) {
        _audioStepIndex = 2;
      } else if (_generatedOutputPath == null && _audioStepIndex == 3) {
        _audioStepIndex = 2;
      }
    });
    if (_audioPageController.hasClients) {
      _audioPageController.jumpToPage(_audioStepIndex);
    } else {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted && _audioPageController.hasClients) {
          _audioPageController.jumpToPage(_audioStepIndex);
        }
      });
    }
  }

  Future<void> _saveState'''
updated, count = re.subn(load_pattern, load_replacement, main_text, count=1, flags=re.S)
if count != 1:
    raise RuntimeError("Required stale-state recovery patch did not match main.dart")
main_state.write_text(updated, encoding="utf-8")

model_picker = root / "lib" / "screens" / "model_picker_screen.dart"
mp = model_picker.read_text(encoding="utf-8")
mp = mp.replace(
"""      final result = await FilePicker.platform.pickFiles(
        type: FileType.any,
        allowMultiple: false,
      );""",
"""      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['onnx'],
        allowMultiple: false,
        withData: false,
      );""",
1)
mp = mp.replace(
"""      final result = await FilePicker.platform.pickFiles(
        type: FileType.any,
        allowMultiple: false,
      );""",
"""      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['mobile.index'],
        allowMultiple: false,
        withData: false,
      );""",
1)
mp = mp.replace(
"""  bool _isSupportedModelFile(String filePath) {
    final lowerPath = filePath.toLowerCase();
    return lowerPath.endsWith('.onnx');
  }""",
"""  bool _isSupportedModelFile(String filePath) {
    final lowerPath = filePath.toLowerCase();
    return lowerPath.endsWith('.onnx');
  }"""
)
mp = mp.replace(
"""  bool _isSupportedIndexFile(String filePath) {
    return filePath.toLowerCase().endsWith('.mobile.index');
  }""",
"""  bool _isSupportedIndexFile(String filePath) {
    final lowerPath = filePath.toLowerCase();
    return lowerPath.endsWith('.mobile.index');
  }"""
)
mp = mp.replace(
"""                        '支持：.onnx 模型',
""",
"""                        'Supported: .onnx voice models (required for mobile inference)',
"""
)
mp = mp.replace(
"""                        '支持：mobile.index 索引',
""",
"""                        'Supported: mobile.index (convert standard .index first)',
"""
)
mp = mp.replace(
"""              ElevatedButton.icon(
                onPressed: selectedModelPath != null ? onContinue : null,
""",
"""              ElevatedButton.icon(
                onPressed: selectedModelPath != null &&
                        selectedModelPath!.toLowerCase().endsWith('.onnx')
                    ? onContinue
                    : null,
"""
)
model_picker.write_text(r'''import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/rvc_bridge.dart';

class ModelPickerScreen extends StatefulWidget {
  final Function(String) onModelSelected;
  final VoidCallback? onModelCleared;
  final Function(String?) onIndexSelected;
  final VoidCallback onContinue;
  final String? selectedModelPath;
  final String? selectedModelDisplayName;
  final String? selectedIndexPath;
  final String? selectedIndexDisplayName;
  final String? selectedSongPath;
  final String? selectedSongDisplayName;

  const ModelPickerScreen({
    required this.onModelSelected, this.onModelCleared, required this.onIndexSelected,
    required this.onContinue, this.selectedModelPath, this.selectedModelDisplayName,
    this.selectedIndexPath, this.selectedIndexDisplayName, this.selectedSongPath, this.selectedSongDisplayName,
  });

  @override State<ModelPickerScreen> createState() => _ModelPickerScreenState();
}

class _ModelPickerScreenState extends State<ModelPickerScreen> {
  final RVCBridge _bridge = RVCBridge();
  final List<String> _library = <String>[];
  bool _busy = false;

  bool _isRuntimeModel(String p) => p.toLowerCase().endsWith('.onnx');

  Future<void> _loadLibrary() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getStringList('rvc_model_library') ?? <String>[];
    if (mounted) setState(() { _library..clear()..addAll(saved); });
  }

  Future<void> _saveLibrary() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList('rvc_model_library', _library);
  }

  Future<void> _pickModel() async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['onnx', 'pth', 'pt', 'zip'],
        allowMultiple: false,
        withData: false,
      );
      final source = result?.files.single.path;
      if (source == null) return;
      final imported = await _bridge.importPickedFile(kind: 'model', sourcePath: source);
      final path = imported.path;
      if (!_library.contains(path)) _library.insert(0, path);
      await _saveLibrary();
      if (!mounted) return;
      if (_isRuntimeModel(path)) {
        widget.onModelSelected(path);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('ONNX model imported and ready for mobile inference.')));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Source model imported. PTH/PT/ZIP files are stored but are not directly runnable by the Android ONNX engine.')));
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Model import failed: ' + e.toString())));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _pickIndex() async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['index', 'mobile.index'],
        allowMultiple: false,
        withData: false,
      );
      final source = result?.files.single.path;
      if (source == null) return;
      final imported = await _bridge.importPickedFile(kind: 'index', sourcePath: source);
      widget.onIndexSelected(imported.path);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(
        source.toLowerCase().endsWith('.mobile.index')
          ? 'mobile.index imported.'
          : 'Standard .index imported. Convert it before mobile inference.'
      )));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Index import failed: ' + e.toString())));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override void initState() { super.initState(); _loadLibrary(); }

  @override
  Widget build(BuildContext context) {
    final selected = widget.selectedModelPath;
    return Scaffold(
      appBar: AppBar(title: const Text("RED'S ULTIMATE RVC"), centerTitle: true),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(18, 12, 18, 28),
        children: [
          _section(Icons.graphic_eq, 'VOICE MODEL',
            selected == null ? 'No runtime model selected' : (widget.selectedModelDisplayName ?? selected.split('/').last),
            Row(children: [
              Expanded(child: ElevatedButton.icon(onPressed: _busy ? null : _pickModel, icon: const Icon(Icons.upload_file), label: const Text('UPLOAD MODEL'))),
              if (selected != null) IconButton(onPressed: widget.onModelCleared, icon: const Icon(Icons.close)),
            ])),
          const SizedBox(height: 12),
          _section(Icons.account_tree, 'INDEX',
            widget.selectedIndexDisplayName ?? 'Optional mobile.index / standard .index',
            Row(children: [
              Expanded(child: OutlinedButton.icon(onPressed: _busy ? null : _pickIndex, icon: const Icon(Icons.upload_file), label: const Text('UPLOAD INDEX'))),
              if (widget.selectedIndexPath != null) IconButton(onPressed: () => widget.onIndexSelected(null), icon: const Icon(Icons.close)),
            ])),
          const SizedBox(height: 12),
          _section(Icons.library_music, 'MODEL LIBRARY',
            _library.length.toString() + ' imported source model' + (_library.length == 1 ? '' : 's'),
            Column(children: _library.isEmpty
              ? [const Align(alignment: Alignment.centerLeft, child: Text('Nothing imported yet.'))]
              : _library.map((p) {
                  final runtime = _isRuntimeModel(p);
                  return ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: Icon(runtime ? Icons.check_circle : Icons.inventory_2, color: runtime ? Colors.redAccent : Colors.grey),
                    title: Text(p.split('/').last, maxLines: 1, overflow: TextOverflow.ellipsis),
                    subtitle: Text(runtime ? 'READY FOR MOBILE INFERENCE' : 'SOURCE FILE — CONVERSION/TRAINING REQUIRED'),
                    onTap: runtime ? () => widget.onModelSelected(p) : null,
                  );
                }).toList()),
          ),
          const SizedBox(height: 16),
          SizedBox(height: 54, child: ElevatedButton.icon(
            onPressed: selected != null && _isRuntimeModel(selected) ? widget.onContinue : null,
            icon: const Icon(Icons.arrow_forward), label: const Text('CONTINUE TO GENERATE'))),
          const SizedBox(height: 14),
          Text('Android inference uses ONNX voice models. PTH/PT/ZIP files can be uploaded and kept in the library, but they cannot be executed directly by this local ONNX engine.',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.grey), textAlign: TextAlign.center),
        ],
      ),
    );
  }

  Widget _section(IconData icon, String title, String subtitle, Widget child) => Card(
    child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [Icon(icon, color: Colors.redAccent), const SizedBox(width: 10), Expanded(child: Text(title, style: const TextStyle(fontWeight: FontWeight.w800, letterSpacing: 1.1)))]),
      const SizedBox(height: 6), Text(subtitle, maxLines: 2, overflow: TextOverflow.ellipsis),
      const SizedBox(height: 14), child,
    ])),
  );
}
''', encoding="utf-8")
# legacy upstream picker write intentionally disabled; custom picker above is authoritative

main = root / "lib" / "main.dart"
m = main.read_text(encoding="utf-8")
if "screens/red_home_screen.dart" not in m:
    m = m.replace("import 'screens/pitch_detection_screen.dart';", "import 'screens/pitch_detection_screen.dart';\nimport 'screens/red_home_screen.dart';\nimport 'screens/training_screen.dart';")
m = m.replace("int _moduleIndex = 0;", "int _moduleIndex = 7;", 1)
home_block = '''      RedHomeScreen(
        onGenerate: () { setState(() { _moduleIndex = 0; _audioStepIndex = 0; }); _saveState(); },
        onSongCovers: _openAudioConversion,
        onSpeech: _openVoiceChanger,
        onModels: () { setState(() { _moduleIndex = 0; _audioStepIndex = 1; }); _saveState(); },
        onUploadDownload: () { Navigator.of(context).push(MaterialPageRoute(builder: (_) => ModelPickerScreen(
          onModelSelected: _onModelSelected, onModelCleared: _onModelCleared, onIndexSelected: _onIndexSelected,
          onContinue: _continueToGenerate, selectedModelPath: _selectedModelPath, selectedModelDisplayName: _selectedModelDisplayName,
          selectedIndexPath: _selectedIndexPath, selectedIndexDisplayName: _selectedIndexDisplayName,
          selectedSongPath: _selectedSongPath, selectedSongDisplayName: _selectedSongDisplayName,
        ))); },
        onTrain: () { Navigator.of(context).push(MaterialPageRoute(builder: (_) => const TrainingScreen())); },
        onAudio: _openAudioConversion,
        onSettings: _openParameterGuide,
      ),
'''
if "onUploadDownload:" not in m:
    m = m.replace("    final moduleScreens = [\n", "    final moduleScreens = [\n" + home_block, 1)
main.write_text(m, encoding="utf-8")

# Add a visible model capability explanation so a .pth file is not presented
# as if it were already inference-ready.
for dart in (root / "lib" / "screens").rglob("*.dart"):
    content = dart.read_text(encoding="utf-8")
    content = content.replace(
        "Please select an .onnx model file.",
        "Choose an .onnx voice model. RVC .pth models must be converted to .onnx before mobile use."
    )
    dart.write_text(content, encoding="utf-8")

# Render the exact approved SVG artwork into a launcher PNG.
launcher_png = root / "android" / "app" / "src" / "main" / "res" / "drawable" / "reds_ultimate_rvc_logo.png"
launcher_png.parent.mkdir(parents=True, exist_ok=True)
try:
    import cairosvg
    cairosvg.svg2png(url=str(logo_svg), write_to=str(launcher_png), output_width=512, output_height=512)
except Exception as exc:
    raise RuntimeError(f"Could not render the approved Red's Ultimate RVC logo: {exc}")

manifest = root / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
replace_in(
    manifest,
    [
        ('android:label="Ultimate RVC Mobile"', 'android:label="Red\'s Ultimate RVC"'),
        ('android:icon="@mipmap/ic_launcher"', 'android:icon="@drawable/reds_ultimate_rvc_logo"'),
    ],
)

# The CI intentionally uses Flutter 3.24.5. Its Android template uses
# Gradle 8.3, AGP 8.1.0 and Kotlin 1.8.22. The upstream RVC project is older
# (Gradle 7.6.3 / AGP 7.3.0 / Kotlin 1.8.10), which causes Flutter's Android
# dependency validation to reject the build. Keep all three versions aligned.
settings_gradle = root / "android" / "settings.gradle"
regex_replace(
    settings_gradle,
    r'(id\s+["\']com\.android\.application["\']\s+version\s+["\'])[^"\']+(["\']\s+apply\s+false)',
    r'\g<1>8.1.0\2',
)
regex_replace(
    settings_gradle,
    r'(id\s+["\']org\.jetbrains\.kotlin\.android["\']\s+version\s+["\'])[^"\']+(["\']\s+apply\s+false)',
    r'\g<1>1.8.22\2',
)

android_build = root / "android" / "build.gradle"
regex_replace(
    android_build,
    r'(com\.android\.tools\.build:gradle:)[^"\']+',
    r'\g<1>8.1.0',
)
regex_replace(
    android_build,
    r'(org\.jetbrains\.kotlin:kotlin-gradle-plugin:)[^"\']+',
    r'\g<1>1.8.22',
)

wrapper = root / "android" / "gradle" / "wrapper" / "gradle-wrapper.properties"
regex_replace(
    wrapper,
    r'(distributionUrl=.*gradle-)[^\\/]+(-all\.zip)',
    r'\g<1>8.3\2',
)

pubspec = root / "pubspec.yaml"
replace_in(
    pubspec,
    [
        ("name: ultimate_rvc_mobile", "name: reds_ultimate_rvc"),
        ("Cross-platform RVC voice conversion app", "Red's Ultimate RVC - local Android voice conversion"),
        ("dev_dependencies:\n", "dependency_overrides:\n  win32: 5.5.5\n\ndev_dependencies:\n"),
    ],
)

# R8 fails on Flutter's optional Play Store deferred-component classes when
# shrinking this standalone APK. Red's Ultimate RVC does not use deferred
# Play Feature Delivery, so keep release shrinking off for a reliable APK.
app_gradle = root / "android" / "app" / "build.gradle"
replace_in(
    app_gradle,
    [
        ("minifyEnabled true", "minifyEnabled false"),
        ("shrinkResources true", "shrinkResources false"),
    ],
)

gradle_props = root / "android" / "gradle.properties"
replace_in(
    gradle_props,
    [("org.gradle.java.home=/usr/lib/jvm/java-17-openjdk-amd64\n", "")],
)


ui = {
"生成已中止":"Generation stopped","生成完成":"Conversion complete","初始化失败":"Initialization failed","初始化中...":"Initializing...",
"再按一次退出":"Press back again to exit","确定":"OK","音频推理":"Audio Conversion","实时推理":"Realtime Conversion","变声器模式":"Voice Changer",
"分贝仪":"dB Meter","音高检测":"Pitch Detection","参数解释":"RVC Controls","mobile.index 转换教程":"Index Converter",
"音频":"Audio","音色":"Voice Model","生成":"Convert","结果":"Result","未启动":"Ready","需要麦克风权限":"Microphone permission required",
"实时测量中":"Measuring","测量失败":"Measurement failed","已锁定":"Locked","解除锁定":"Unlock","锁定当前数值":"Lock current value",
"分贝实时曲线":"Live dB Level","清空曲线":"Clear chart","准备生成":"Ready to convert","处理出错了，请重新生成":"Processing failed. Please try again.",
"恢复进度中":"Restoring progress","无法继续":"Cannot continue","不做任何操作。":"No action was taken.","生成音频":"Convert Audio",
"输入音频：":"Input audio: ","音色模型：":"Voice model: ","索引文件：":"Index file: ","未选择":"Not selected","参数":"Parameters",
"高级参数":"Advanced","恢复默认":"Reset defaults","生成中...":"Converting...","生成用时：":"Conversion time: ","正在中止":"Stopping...",
"终止生成":"Stop conversion","重新生成":"Convert again","开始生成":"Start conversion","继续未完成":"Resume unfinished job",
"处理时间取决于音频长度":"Processing time depends on audio length.","为什么要先转换":"Why conversion is required",
"标准 RVC/FAISS .index 需要先在电脑上转换，转换后再传到手机选择。":"Standard RVC/FAISS .index files must be converted on a computer before using them here.",
"转换命令":"Conversion command","请选择 .onnx 模型文件":"Please select an .onnx model file.","请选择 mobile.index 文件":"Please select a mobile.index file.",
"选择模型失败":"Model selection failed","选择索引失败":"Index selection failed","选择音色模型":"Select voice model","已选择音色：":"Selected voice: ",
"支持：.onnx 模型":"Supported: .onnx models","更换模型":"Change model","选择模型":"Choose model","清除模型":"Clear model",
"索引文件（可选）":"Index file (optional)","支持：mobile.index 索引":"Supported: mobile.index","更换 mobile.index":"Change mobile.index",
"选择 mobile.index":"Choose mobile.index","清除索引":"Clear index","继续":"Continue","当前音频：":"Current audio: ",
"Pitch（音调设置）":"Pitch","音调设置":"Pitch","半音":"semitones","Index Rate（索引强度）":"Index Rate","Index Rate（检索特征占比）":"Index Rate",
"检索特征占比":"Feature retrieval ratio","索引强度":"Index strength","Formant（性别因子/声线粗细）":"Formant","性别因子/声线粗细":"Voice character",
"Noise Gate（噪声过滤）":"Noise Gate","噪声过滤":"Noise gate","Sample Rate（采样率）":"Sample Rate","采样率":"Sample rate",
"降噪优化":"Denoise","音域过滤":"Vocal Range Filter","只影响处理结果，不改原始录音文件":"Affects processing only; original recording is unchanged.",
"Filter Radius（音高滤波）":"Filter Radius","音高滤波":"Pitch smoothing","RMS Mix（响度混合）":"RMS Mix","响度混合":"Loudness mix",
"RMS Mix（响度因子）":"RMS Mix","响度因子":"Loudness mix","Protect（辅音保护）":"Protect","辅音保护":"Consonant protection",
"正在停止实时推理":"Stopping realtime conversion","已停止":"Stopped","请选择 .onnx 音色模型":"Please choose an .onnx voice model.",
"启动实时推理":"Start realtime conversion","停止实时推理":"Stop realtime conversion","状态：":"Status: ","音频采样率":"Audio sample rate",
"采样长度":"Chunk length","淡入淡出长度":"Crossfade length","额外推理时长":"Extra inference time","延时缓冲":"Delay buffer","播放延迟":"Playback delay",
"悬浮控制":"Floating controls","悬浮窗直径":"Overlay size","悬浮窗不透明度":"Overlay opacity","关闭悬浮窗":"Close overlay","打开悬浮窗":"Open overlay",
"录制模式":"Recording mode","处理声线参数":"Voice settings","选择 .onnx 模型":"Choose .onnx model","更换 .onnx 模型":"Change .onnx model",
"移除索引":"Remove index","分享失败":"Share failed","已保存":"Saved","保存失败":"Save failed","生成结果":"Conversion result",
"音频已生成":"Audio converted","播放":"Play","暂停":"Pause","分享":"Share","保存":"Save","选择音频失败":"Audio selection failed",
"录音失败":"Recording failed","选择音频":"Choose audio","支持：MP3、WAV、M4A、FLAC、OGG":"Supported: MP3, WAV, M4A, FLAC, OGG",
"更换音频":"Change audio","清除音频":"Clear audio","停止录音":"Stop recording","直接录音":"Record","录音时长：":"Recording time: ",
"音高检测设置":"Pitch detection settings","基准音高（留空默认 C4）":"Reference pitch (blank = C4)","图表 Y 轴模式":"Chart Y-axis mode",
"相对半音值":"Relative semitone","频率 Hz":"Frequency Hz","音名（A2/C4）":"Note name (A2/C4)","检测灵敏度":"Detection sensitivity",
"取消":"Cancel","音高实时曲线":"Live pitch","音名":"Note","相对半音值：":"Relative semitone: ","手机端限制":"Mobile limitations",
"这个页面仅供演示。":"Realtime conversion page.","手机端实时推理性能和系统音频能力限制很大。":"Realtime conversion depends on device performance and Android audio routing.",
"当前无法指定输入输出设备。":"Android does not expose selectable input/output devices here.","知道了":"Got it",
"这是 Ultimate RVC 生成的音频。":"Audio converted with Red's Ultimate RVC.","Ultimate RVC 生成音频":"Red's Ultimate RVC audio","悬浮窗":"Overlay"
}

for dart in (root / "lib").rglob("*.dart"):
    s = dart.read_text(encoding="utf-8")
    for a, b in ui.items():
        s = s.replace(a, b)
    def clean(m):
        q, body = m.group(1), m.group(2)
        body = re.sub(r"[\u3400-\u9fff]+", "", body).strip()
        return q + (body or "RVC") + q
    s = re.sub(r"(['\"])([^'\"\n]*[\u3400-\u9fff][^'\"\n]*)\\1", clean, s)
    dart.write_text(s, encoding="utf-8")

main = root / "lib" / "main.dart"
s = main.read_text(encoding="utf-8")
s = s.replace(
    "theme: ThemeData(",
    "theme: ThemeData(\n"
    "        brightness: Brightness.dark,\n"
    "        scaffoldBackgroundColor: const Color(0xFF08080C),\n"
    "        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFFE00020), brightness: Brightness.dark),\n"
    "        appBarTheme: const AppBarTheme(backgroundColor: Color(0xFF08080C), foregroundColor: Colors.white, elevation: 0, centerTitle: true),\n"
    "        cardTheme: CardTheme(color: Color(0xFF121218), surfaceTintColor: Colors.transparent, elevation: 0, shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(18)), side: BorderSide(color: Color(0xFF282831)))),"
)
s = s.replace("title: 'Ultimate RVC Mobile',", "title: \"Red's Ultimate RVC\",")
main.write_text(s, encoding="utf-8")


# Final sanity scrub: the branded build must never ship untranslated CJK text.
for dart in (root / "lib").rglob("*.dart"):
    content = dart.read_text(encoding="utf-8")
    content = re.sub(r"[\u3400-\u9fff]+", "", content)
    dart.write_text(content, encoding="utf-8")

# FINAL PATCH: authoritative model manager and dashboard wiring
final_model_picker = r"""import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/rvc_bridge.dart';

class ModelPickerScreen extends StatefulWidget {
  final Function(String) onModelSelected;
  final VoidCallback? onModelCleared;
  final Function(String?) onIndexSelected;
  final VoidCallback onContinue;
  final String? selectedModelPath;
  final String? selectedModelDisplayName;
  final String? selectedIndexPath;
  final String? selectedIndexDisplayName;
  final String? selectedSongPath;
  final String? selectedSongDisplayName;
  const ModelPickerScreen({super.key, required this.onModelSelected, this.onModelCleared, required this.onIndexSelected, required this.onContinue, this.selectedModelPath, this.selectedModelDisplayName, this.selectedIndexPath, this.selectedIndexDisplayName, this.selectedSongPath, this.selectedSongDisplayName});
  @override State<ModelPickerScreen> createState() => _ModelPickerScreenState();
}

class _ModelPickerScreenState extends State<ModelPickerScreen> {
  final RVCBridge _bridge = RVCBridge();
  final List<String> _library = [];
  bool _busy = false;
  bool _runtime(String p) => p.toLowerCase().endsWith('.onnx');

  @override void initState() { super.initState(); _loadLibrary(); }

  Future<void> _loadLibrary() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getStringList('rvc_model_library') ?? [];
    if (mounted) setState(() { _library..clear()..addAll(saved); });
  }

  Future<void> _saveLibrary() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList('rvc_model_library', _library);
  }

  Future<void> _pickModel() async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final result = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['onnx','pth','pt','zip'], allowMultiple: false, withData: false);
      final source = result?.files.single.path;
      if (source == null) return;
      final imported = await _bridge.importPickedFile(kind: 'model', sourcePath: source);
      if (!_library.contains(imported.path)) _library.insert(0, imported.path);
      await _saveLibrary();
      if (_runtime(imported.path)) {
        widget.onModelSelected(imported.path);
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('ONNX model imported and ready.')));
      } else if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Source model uploaded and saved. Use Train / Model Lab for training or conversion.')));
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Model upload failed: $e')));
    } finally { if (mounted) setState(() => _busy = false); }
  }

  Future<void> _pickIndex() async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final result = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['index','mobile.index'], allowMultiple: false, withData: false);
      final source = result?.files.single.path;
      if (source == null) return;
      final imported = await _bridge.importPickedFile(kind: 'index', sourcePath: source);
      widget.onIndexSelected(imported.path);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(source.toLowerCase().endsWith('.mobile.index') ? 'mobile.index imported.' : 'Standard .index imported and stored. Convert it before mobile inference.')));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Index upload failed: $e')));
    } finally { if (mounted) setState(() => _busy = false); }
  }

  @override Widget build(BuildContext context) {
    final selected = widget.selectedModelPath;
    return Scaffold(
      appBar: AppBar(title: const Text("RED'S ULTIMATE RVC"), centerTitle: true),
      body: ListView(padding: const EdgeInsets.fromLTRB(16,12,16,28), children: [
        Card(child: Padding(padding: const EdgeInsets.all(18), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('VOICE MODEL', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
          const SizedBox(height: 6),
          Text(selected == null ? 'No inference model selected' : (widget.selectedModelDisplayName ?? selected.split('/').last)),
          const SizedBox(height: 12),
          SizedBox(width: double.infinity, height: 52, child: ElevatedButton.icon(onPressed: _busy ? null : _pickModel, icon: const Icon(Icons.upload_file), label: const Text('UPLOAD MODEL'))),
          const SizedBox(height: 8),
          const Text('Accepted: .onnx, .pth, .pt, .zip. ONNX is directly runnable on Android; source models are stored for training/conversion.', style: TextStyle(color: Colors.grey)),
        ]))),
        const SizedBox(height: 12),
        Card(child: Padding(padding: const EdgeInsets.all(18), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('INDEX', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
          const SizedBox(height: 6),
          Text(widget.selectedIndexDisplayName ?? 'Optional .mobile.index / .index'),
          const SizedBox(height: 10),
          SizedBox(width: double.infinity, height: 48, child: OutlinedButton.icon(onPressed: _busy ? null : _pickIndex, icon: const Icon(Icons.upload_file), label: const Text('UPLOAD INDEX'))),
          const SizedBox(height: 6),
          const Text('mobile.index is directly usable. Standard .index is stored and must be converted before mobile inference.', style: TextStyle(color: Colors.grey)),
        ]))),
        const SizedBox(height: 12),
        Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('MODEL LIBRARY', style: TextStyle(fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          if (_library.isEmpty) const Text('No uploaded models yet.')
          else ..._library.map((p) => ListTile(
            contentPadding: EdgeInsets.zero,
            leading: Icon(_runtime(p) ? Icons.check_circle : Icons.inventory_2, color: _runtime(p) ? Colors.redAccent : Colors.grey),
            title: Text(p.split('/').last, maxLines: 1, overflow: TextOverflow.ellipsis),
            subtitle: Text(_runtime(p) ? 'READY FOR MOBILE INFERENCE' : 'SOURCE MODEL — TRAIN / CONVERT'),
            onTap: _runtime(p) ? () => widget.onModelSelected(p) : null,
          )),
        ]))),
        const SizedBox(height: 14),
        SizedBox(height: 54, child: ElevatedButton.icon(onPressed: selected != null && _runtime(selected) ? widget.onContinue : null, icon: const Icon(Icons.arrow_forward), label: const Text('CONTINUE TO GENERATE'))),
      ]),
    );
  }
}
""";

(root / 'lib' / 'screens' / 'model_picker_screen.dart').write_text(final_model_picker, encoding='utf-8')

main = root / 'lib' / 'main.dart'
text = main.read_text(encoding='utf-8')
if "import 'screens/red_home_screen.dart';" not in text:
    text = text.replace("import 'screens/pitch_detection_screen.dart';", "import 'screens/pitch_detection_screen.dart';\nimport 'screens/red_home_screen.dart';\nimport 'screens/training_screen.dart';")

text = text.replace("void _openAudioConversion() {\n    setState(() => _moduleIndex = 0);", "void _openAudioConversion() {\n    setState(() => _moduleIndex = 1);")
text = text.replace("void _openRealtimeInference() {\n    setState(() => _moduleIndex = 1);", "void _openRealtimeInference() {\n    setState(() => _moduleIndex = 2);")
text = text.replace("void _openVoiceChanger() {\n    setState(() => _moduleIndex = 2);", "void _openVoiceChanger() {\n    setState(() => _moduleIndex = 3);")
text = text.replace("void _openIndexConverter() {\n    setState(() => _moduleIndex = 3);", "void _openIndexConverter() {\n    setState(() => _moduleIndex = 4);")
text = text.replace("void _openParameterGuide() {\n    setState(() => _moduleIndex = 4);", "void _openParameterGuide() {\n    setState(() => _moduleIndex = 5);")
text = text.replace("void _openDecibelMeter() {\n    setState(() => _moduleIndex = 5);", "void _openDecibelMeter() {\n    setState(() => _moduleIndex = 6);")
text = text.replace("void _openPitchDetection() {\n    setState(() => _moduleIndex = 6);", "void _openPitchDetection() {\n    setState(() => _moduleIndex = 7);")
text = text.replace("bottomNavigationBar: _moduleIndex == 0", "bottomNavigationBar: _moduleIndex == 1")


# Patch the upstream main screen after all existing branding changes.
main = root / 'lib' / 'main.dart'
text = main.read_text(encoding='utf-8')
if "import 'screens/red_home_screen.dart';" not in text:
    text = text.replace("import 'screens/pitch_detection_screen.dart';", "import 'screens/pitch_detection_screen.dart';\nimport 'screens/red_home_screen.dart';\nimport 'screens/training_screen.dart';")

text = text.replace("void _openAudioConversion() {\n    setState(() => _moduleIndex = 0);", "void _openAudioConversion() {\n    setState(() => _moduleIndex = 1);")
text = text.replace("void _openRealtimeInference() {\n    setState(() => _moduleIndex = 1);", "void _openRealtimeInference() {\n    setState(() => _moduleIndex = 2);")
text = text.replace("void _openVoiceChanger() {\n    setState(() => _moduleIndex = 2);", "void _openVoiceChanger() {\n    setState(() => _moduleIndex = 3);")
text = text.replace("void _openIndexConverter() {\n    setState(() => _moduleIndex = 3);", "void _openIndexConverter() {\n    setState(() => _moduleIndex = 4);")
text = text.replace("void _openParameterGuide() {\n    setState(() => _moduleIndex = 4);", "void _openParameterGuide() {\n    setState(() => _moduleIndex = 5);")
text = text.replace("void _openDecibelMeter() {\n    setState(() => _moduleIndex = 5);", "void _openDecibelMeter() {\n    setState(() => _moduleIndex = 6);")
text = text.replace("void _openPitchDetection() {\n    setState(() => _moduleIndex = 6);", "void _openPitchDetection() {\n    setState(() => _moduleIndex = 7);")
text = text.replace("bottomNavigationBar: _moduleIndex == 0", "bottomNavigationBar: _moduleIndex == 1")

marker = "    final moduleScreens = ["
pos = text.find(marker)
end_marker = "    ];\n\n    return PopScope("
end = text.find(end_marker, pos)
if pos >= 0 and end > pos:
    block = text[pos:end + 7]
    first = block.find("      GestureDetector(")
    audio = block[first:]
    shifted = audio.replace("_moduleIndex == 5", "_moduleIndex == 6").replace("_moduleIndex == 6", "_moduleIndex == 7")
    dashboard = """    final moduleScreens = [
      RedHomeScreen(
        onGenerate: _openAudioConversion,
        onSongCovers: _openAudioConversion,
        onSpeech: _openVoiceChanger,
        onModels: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ModelPickerScreen(onModelSelected: _onModelSelected, onModelCleared: _onModelCleared, onIndexSelected: _onIndexSelected, onContinue: _continueToGenerate, selectedModelPath: _selectedModelPath, selectedModelDisplayName: _selectedModelDisplayName, selectedIndexPath: _selectedIndexPath, selectedIndexDisplayName: _selectedIndexDisplayName, selectedSongPath: _selectedSongPath, selectedSongDisplayName: _selectedSongDisplayName))),
        onUploadDownload: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ModelPickerScreen(onModelSelected: _onModelSelected, onModelCleared: _onModelCleared, onIndexSelected: _onIndexSelected, onContinue: _continueToGenerate, selectedModelPath: _selectedModelPath, selectedModelDisplayName: _selectedModelDisplayName, selectedIndexPath: _selectedIndexPath, selectedIndexDisplayName: _selectedIndexDisplayName, selectedSongPath: _selectedSongPath, selectedSongDisplayName: _selectedSongDisplayName))),
        onTrain: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const TrainingScreen())),
        onAudio: _openAudioConversion, onSettings: _openParameterGuide,
      ),
""" + shifted
    text = text[:pos] + dashboard + text[end + 7:]

main.write_text(text, encoding='utf-8')

pub = root / 'pubspec.yaml'
pub_text = pub.read_text(encoding='utf-8')
if 'url_launcher:' not in pub_text:
    pub_text = pub_text.replace('dependencies:\n', 'dependencies:\n  url_launcher: 6.2.6\n')
pub.write_text(pub_text, encoding='utf-8')


# ==================== FINAL RED'S ULTIMATE RVC FINALIZER ====================
# Keep the custom Red dashboard. Do not normalize back to the upstream-looking UI.
# Samsung's Android document picker is deliberately unfiltered so RVC model files
# are not greyed out; the app validates the extension after selection.
model_picker = root / "lib" / "screens" / "model_picker_screen.dart"
mp = model_picker.read_text(encoding="utf-8")
mp = re.sub(
    r"type: FileType\.custom,\s*allowedExtensions: \['onnx','pth','pt','zip'\],",
    "type: FileType.any,",
    mp,
    count=1,
)
mp = re.sub(
    r"type: FileType\.custom,\s*allowedExtensions: \['index','mobile\.index'\],",
    "type: FileType.any,",
    mp,
    count=1,
)
model_picker.write_text(mp, encoding="utf-8")

# The dashboard is the intended landing screen.
main = root / "lib" / "main.dart"
mt = main.read_text(encoding="utf-8")
if "RedHomeScreen(" not in mt:
    raise RuntimeError("Red dashboard was not wired into main.dart")
if "training_screen.dart" not in mt:
    raise RuntimeError("Training workspace was not wired into main.dart")
main.write_text(mt, encoding="utf-8")
