import re
from pathlib import Path
import urllib.request

root = Path("buildsrc")
repo_root = Path(__file__).resolve().parent.parent

# Red's Ultimate RVC is a branded product layer around the verified local
# Ultimate RVC Mobile engine. This script intentionally replaces the previous
# accumulated patch stack with one deterministic finalizer.

# ---------------------------------------------------------------------------
# Assets / custom UI
# ---------------------------------------------------------------------------
logo_url = "https://cdn.websitepublisher.ai/custom/wid25042/images/reds-ultimate-rvc-logo.svg"
logo = root / "assets" / "images" / "reds-ultimate-rvc-logo.svg"
logo.parent.mkdir(parents=True, exist_ok=True)
urllib.request.urlretrieve(logo_url, logo)

for name in ("red_home_screen.dart", "training_screen.dart", "full_rvc_screen.dart", "model_converter_screen.dart"):
    src = repo_root / "tools" / "ui" / name
    dst = root / "lib" / "screens" / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

# Keep user-imported models and indexes in persistent app-private storage.
# The upstream manager originally used appCacheDir, which Android may clear.
# Keep the temporary FilePicker staging directory in cache, but put the actual
# imported library and its reference registry under filesDir.
workspace_manager = root / "android" / "app" / "src" / "main" / "kotlin" / "com" / "ultimatervc" / "mobile" / "TempWorkspaceManager.kt"
if workspace_manager.exists():
    manager_text = workspace_manager.read_text(encoding="utf-8")
    old_import_root = 'return File(File(appCacheDir, IMPORTS_DIRECTORY_NAME), kind.directoryName).also { it.mkdirs() }'
    new_import_root = 'return File(File(appFilesDir, IMPORTS_DIRECTORY_NAME), kind.directoryName).also { it.mkdirs() }'
    old_registry = 'return File(File(appCacheDir, IMPORTS_DIRECTORY_NAME), REGISTRY_FILE_NAME)'
    new_registry = 'return File(File(appFilesDir, IMPORTS_DIRECTORY_NAME), REGISTRY_FILE_NAME)'
    if old_import_root not in manager_text or old_registry not in manager_text:
        raise RuntimeError("TempWorkspaceManager storage layout changed; review persistent model-library patch")
    manager_text = manager_text.replace(old_import_root, new_import_root, 1)
    manager_text = manager_text.replace(old_registry, new_registry, 1)
    workspace_manager.write_text(manager_text, encoding="utf-8")
else:
    raise RuntimeError("TempWorkspaceManager.kt missing; cannot guarantee persistent model imports")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def replace_once(path, old, new, required=True):
    text = path.read_text(encoding="utf-8")
    if old not in text:
        if required:
            raise RuntimeError(f"Required text not found in {path}: {old[:120]}")
        return
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")

def regex_once(path, pattern, replacement):
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Required regex did not match exactly once: {path}: {pattern}")
    path.write_text(updated, encoding="utf-8")

# ---------------------------------------------------------------------------
# Pubspec / package identity
# ---------------------------------------------------------------------------
pubspec = root / "pubspec.yaml"
pt = pubspec.read_text(encoding="utf-8")
if "  url_launcher:" not in pt:
    pt = pt.replace("  flutter_svg: ^2.0.10+1\n", "  flutter_svg: ^2.0.10+1\n  url_launcher: ^6.3.1\n")
pt = pt.replace("name: ultimate_rvc_mobile", "name: reds_ultimate_rvc")
if "  webview_flutter:" not in pt:
    pt = pt.replace("  url_launcher: ^6.3.1\n", "  url_launcher: ^6.3.1\n  webview_flutter: ^4.10.0\n")
pt = pt.replace("  url_launcher: 6.2.6\n", "")

if "dependency_overrides:" not in pt:
    pt += "\ndependency_overrides:\n  win32: 5.5.5\n"
write(pubspec, pt)

# ---------------------------------------------------------------------------
# Clean Red dashboard
# ---------------------------------------------------------------------------
home = root / "lib" / "screens" / "red_home_screen.dart"
write(home, r'''import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class RedHomeScreen extends StatelessWidget {
  final VoidCallback onGenerate;
  final VoidCallback onSongCovers;
  final VoidCallback onRealtime;
  final VoidCallback onVoiceChanger;
  final VoidCallback onModels;
  final VoidCallback onTrain;
  final VoidCallback onAudioTools;
  final VoidCallback onSettings;

  const RedHomeScreen({
    super.key,
    required this.onGenerate,
    required this.onSongCovers,
    required this.onRealtime,
    required this.onVoiceChanger,
    required this.onModels,
    required this.onTrain,
    required this.onAudioTools,
    required this.onSettings,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      backgroundColor: const Color(0xFF07070A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF09090D),
        elevation: 0,
        title: const Text("RED'S ULTIMATE RVC", style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: .4)),
        centerTitle: true,
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 30),
          children: [
            Container(
              padding: const EdgeInsets.fromLTRB(18, 18, 18, 20),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(26),
                border: Border.all(color: const Color(0xFFE00022).withOpacity(.55), width: 1.2),
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFF250008), Color(0xFF0C0C11), Color(0xFF07070A)],
                ),
                boxShadow: const [BoxShadow(color: Color(0x55000000), blurRadius: 22, offset: Offset(0, 10))],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    height: 112,
                    width: double.infinity,
                    child: SvgPicture.asset(
                      'assets/images/reds-ultimate-rvc-logo.svg',
                      fit: BoxFit.contain,
                      alignment: Alignment.centerLeft,
                    ),
                  ),
                  const SizedBox(height: 10),
                  const Text("RED'S ULTIMATE RVC", style: TextStyle(fontSize: 25, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 6),
                  Text(
                    'Your Android voice conversion studio.',
                    style: theme.textTheme.bodyMedium?.copyWith(color: const Color(0xFFBEBEC7)),
                  ),
                  const SizedBox(height: 13),
                  Row(
                    children: const [
                      Icon(Icons.wifi_off, size: 17, color: Color(0xFF70D890)),
                      SizedBox(width: 7),
                      Text('LOCAL • PRIVATE • ANDROID', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, letterSpacing: .8)),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            _section('CREATE & CONVERT'),
            _grid([
              _Action(Icons.graphic_eq, 'CONVERT AUDIO', 'Song / speech to your selected voice', onGenerate),
              _Action(Icons.music_video, 'SONG COVERS', 'Full-length audio conversion', onSongCovers),
              _Action(Icons.settings_voice, 'REALTIME RVC', 'Live microphone conversion', onRealtime),
              _Action(Icons.record_voice_over, 'VOICE CHANGER', 'Use RVC while recording', onVoiceChanger),
            ]),
            const SizedBox(height: 16),
            _section('VOICES & TRAINING'),
            _grid([
              _Action(Icons.library_music, 'MODEL LIBRARY', 'Import, manage and select voices', onModels),
              _Action(Icons.model_training, 'VOICE DATASET LAB', 'Record and organise voice samples on this phone', onTrain),
              _Action(Icons.tune, 'AUDIO TOOLS', 'Index, pitch and level tools', onAudioTools),
              _Action(Icons.settings, 'SETTINGS & CONTROLS', 'RVC parameters and options', onSettings),
            ]),
            const SizedBox(height: 18),
            Container(
              padding: const EdgeInsets.all(15),
              decoration: BoxDecoration(
                color: const Color(0xFF101016),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFF292932)),
              ),
              child: const Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.info_outline, color: Color(0xFFE00022)),
                  SizedBox(width: 11),
                  Expanded(
                    child: Text(
                      'RVC conversion is performed locally on the phone. ONNX voice models are directly usable by the Android engine; source .pth/.pt models can be stored in the library but require conversion to a mobile-compatible model before inference.',
                      style: TextStyle(color: Color(0xFFC7C7D0), height: 1.35, fontSize: 12.5),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _section(String title) => Padding(
    padding: const EdgeInsets.only(left: 3, bottom: 9),
    child: Text(title, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w900, letterSpacing: 1.25, color: Color(0xFFE00022))),
  );

  Widget _grid(List<_Action> actions) => GridView.count(
    crossAxisCount: 2,
    shrinkWrap: true,
    physics: const NeverScrollableScrollPhysics(),
    mainAxisSpacing: 10,
    crossAxisSpacing: 10,
    childAspectRatio: 1.34,
    children: actions,
  );
}

class _Action extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _Action(this.icon, this.title, this.subtitle, this.onTap);

  @override
  Widget build(BuildContext context) => Material(
    color: const Color(0xFF111117),
    borderRadius: BorderRadius.circular(20),
    child: InkWell(
      borderRadius: BorderRadius.circular(20),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(13),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: const Color(0xFF282831)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 42, height: 42,
              decoration: BoxDecoration(
                color: const Color(0x22E00022),
                borderRadius: BorderRadius.circular(13),
              ),
              child: Icon(icon, color: const Color(0xFFFF334F), size: 23),
            ),
            const SizedBox(height: 9),
            Text(title, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 12.5)),
            const SizedBox(height: 4),
            Text(subtitle, maxLines: 2, overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: Color(0xFF92929D), fontSize: 10.5, height: 1.2)),
          ],
        ),
      ),
    ),
  );
}
''')

# Fix the apostrophe inside the Dart const string above.
write(home, (repo_root / "tools" / "ui" / "red_home_screen.dart").read_text(encoding="utf-8"))
ht = home.read_text(encoding="utf-8")
write(home, ht)

# ---------------------------------------------------------------------------
# Model library: Samsung-safe picker + persistent app storage + clear status
# ---------------------------------------------------------------------------
picker = root / "lib" / "screens" / "model_picker_screen.dart"
write(picker, r'''import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
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
    super.key,
    required this.onModelSelected,
    this.onModelCleared,
    required this.onIndexSelected,
    required this.onContinue,
    this.selectedModelPath,
    this.selectedModelDisplayName,
    this.selectedIndexPath,
    this.selectedIndexDisplayName,
    this.selectedSongPath,
    this.selectedSongDisplayName,
  });

  @override
  State<ModelPickerScreen> createState() => _ModelPickerScreenState();
}

class _ModelPickerScreenState extends State<ModelPickerScreen> {
  final RVCBridge _bridge = RVCBridge();
  List<String> _library = [];
  String? _selectedModelPath;
  String? _selectedModelDisplayName;
  String? _selectedIndexPath;
  String? _selectedIndexDisplayName;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _selectedModelPath = widget.selectedModelPath;
    _selectedModelDisplayName = widget.selectedModelDisplayName;
    _selectedIndexPath = widget.selectedIndexPath;
    _selectedIndexDisplayName = widget.selectedIndexDisplayName;
    _loadLibrary();
  }

  @override
  void didUpdateWidget(covariant ModelPickerScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.selectedModelPath != widget.selectedModelPath) {
      _selectedModelPath = widget.selectedModelPath;
      _selectedModelDisplayName = widget.selectedModelDisplayName;
    }
    if (oldWidget.selectedIndexPath != widget.selectedIndexPath) {
      _selectedIndexPath = widget.selectedIndexPath;
      _selectedIndexDisplayName = widget.selectedIndexDisplayName;
    }
  }

  Future<void> _loadLibrary() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getStringList('red_rvc_model_library') ?? [];
    final valid = saved.where((p) => File(p).existsSync()).toList();
    await prefs.setStringList('red_rvc_model_library', valid);
    if (mounted) setState(() => _library = valid);
  }

  Future<void> _saveLibrary() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList('red_rvc_model_library', _library);
  }

  String _ext(String path) {
    final p = path.toLowerCase();
    if (p.endsWith('.mobile.index')) return 'mobile.index';
    final i = p.lastIndexOf('.');
    return i >= 0 ? p.substring(i + 1) : '';
  }

  bool _runtime(String path) => _ext(path) == 'onnx';

  bool _sourceModel(String path) => ['pth', 'pt', 'zip'].contains(_ext(path));

  bool _index(String path) => ['index', 'mobile.index'].contains(_ext(path));

  Future<void> _pickModel() async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      // Use Android's unrestricted document picker: custom extension filters can
      // grey out legitimate .pth/.pt/.index files in Samsung My Files.
      // Validate the selected extension after the user chooses the file.
      final result = await FilePicker.platform.pickFiles(
        type: FileType.any,
        allowMultiple: false,
        withData: false,
      );
      final source = result?.files.single.path;
      if (source == null || source.isEmpty) return;
      final ext = _ext(source);
      if (!['onnx', 'pth', 'pt', 'zip'].contains(ext)) {
        throw Exception('Select an RVC model: .onnx, .pth, .pt or .zip');
      }

      final imported = await _bridge.importPickedFile(kind: 'model', sourcePath: source);
      if (!_library.contains(imported.path)) _library.insert(0, imported.path);
      if (_runtime(imported.path)) {
        _selectedModelPath = imported.path;
        _selectedModelDisplayName = File(imported.path).uri.pathSegments.last;
      }
      await _saveLibrary();

      if (!mounted) return;
      setState(() {});
      if (_runtime(imported.path)) {
        widget.onModelSelected(imported.path);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('ONNX model imported and ready.')));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Model imported into the library. PTH/PT/ZIP is stored safely but is not directly runnable by the Android ONNX engine.')),
        );
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('MODEL IMPORT FAILED: $e')));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _pickIndex() async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.any,
        allowMultiple: false,
        withData: false,
      );
      final source = result?.files.single.path;
      if (source == null || source.isEmpty) return;
      final ext = _ext(source);
      if (!_index(source)) throw Exception('Select an RVC .index or .mobile.index file');

      final imported = await _bridge.importPickedFile(kind: 'index', sourcePath: source);
      _selectedIndexPath = imported.path;
      _selectedIndexDisplayName = File(imported.path).uri.pathSegments.last;
      if (mounted) setState(() {});
      widget.onIndexSelected(imported.path);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(ext == 'mobile.index' ? 'mobile.index imported and ready.' : 'Standard .index imported. Use Index Tools to convert it for mobile use.')),
        );
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('INDEX IMPORT FAILED: $e')));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _use(String path) async {
    if (!_runtime(path)) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('This source model is stored, but Android inference requires an ONNX model.')));
      return;
    }
    _selectedModelPath = path;
    _selectedModelDisplayName = File(path).uri.pathSegments.last;
    widget.onModelSelected(path);
    if (mounted) setState(() {});
  }

  Future<void> _delete(String path) async {
    try {
      await _bridge.releaseImportedFile(path);
    } catch (_) {}
    _library.remove(path);
    if (_selectedModelPath == path) {
      _selectedModelPath = null;
      _selectedModelDisplayName = null;
      widget.onModelCleared?.call();
    }
    await _saveLibrary();
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final selected = _selectedModelPath;
    final ready = selected != null && _runtime(selected);
    return Scaffold(
      appBar: AppBar(title: const Text("RED'S ULTIMATE RVC — MODEL LIBRARY"), centerTitle: true),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 30),
        children: [
          _card(
            title: 'VOICE MODEL',
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(
                selected == null ? 'No runtime voice selected' : (_selectedModelDisplayName ?? File(selected).uri.pathSegments.last),
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900),
              ),
              const SizedBox(height: 7),
              Text(ready ? 'READY — ONNX model can be used for conversion.' : 'Choose an ONNX model for conversion. Source RVC models can also be stored below.', style: const TextStyle(color: Color(0xFFAAAAB5))),
              const SizedBox(height: 13),
              Row(children: [
                Expanded(child: ElevatedButton.icon(onPressed: _busy ? null : _pickModel, icon: const Icon(Icons.upload_file), label: const Text('IMPORT MODEL'))),
                if (selected != null && widget.onModelCleared != null) ...[
                  const SizedBox(width: 8),
                  IconButton(onPressed: widget.onModelCleared, icon: const Icon(Icons.clear), tooltip: 'Clear selected model'),
                ],
              ]),
            ]),
          ),
          const SizedBox(height: 12),
          _card(
            title: 'INDEX — OPTIONAL',
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(_selectedIndexDisplayName ?? (_selectedIndexPath == null ? 'No index selected' : File(_selectedIndexPath!).uri.pathSegments.last),
                style: const TextStyle(fontWeight: FontWeight.w800)),
              const SizedBox(height: 8),
              const Text('mobile.index is directly usable. Standard .index files can be converted with Index Tools.', style: TextStyle(color: Color(0xFF9E9EA8), height: 1.3)),
              const SizedBox(height: 12),
              OutlinedButton.icon(onPressed: _busy ? null : _pickIndex, icon: const Icon(Icons.upload_file), label: const Text('IMPORT INDEX')),
              const SizedBox(height: 9),
              const Text('PTH → ONNX conversion is not included in this offline mobile engine. Imported PTH files remain stored safely, but cannot be selected for inference until a genuine converter is integrated.', style: TextStyle(color: Color(0xFFFFA3AE), height: 1.35)),
            ]),
          ),
          const SizedBox(height: 12),
          _card(
            title: 'IMPORTED LIBRARY',
            child: _library.isEmpty
              ? const Text('No imported models yet.', style: TextStyle(color: Color(0xFF9999A4)))
              : Column(children: _library.map((p) {
                  final runtime = _runtime(p);
                  final source = _sourceModel(p);
                  return ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: Icon(runtime ? Icons.check_circle : Icons.inventory_2, color: runtime ? const Color(0xFF5DE58A) : const Color(0xFFFF334F)),
                    title: Text(File(p).uri.pathSegments.last, maxLines: 1, overflow: TextOverflow.ellipsis),
                    subtitle: Text(runtime ? 'READY FOR MOBILE INFERENCE' : source ? 'SOURCE MODEL — CONVERSION REQUIRED' : 'IMPORTED FILE'),
                    trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                      if (runtime) IconButton(onPressed: () => _use(p), icon: const Icon(Icons.play_arrow), tooltip: 'Use model'),
                      IconButton(onPressed: () => _delete(p), icon: const Icon(Icons.delete_outline), tooltip: 'Delete'),
                    ]),
                  );
                }).toList()),
          ),
          const SizedBox(height: 14),
          SizedBox(height: 52, child: ElevatedButton.icon(
            onPressed: ready && widget.selectedSongPath != null ? widget.onContinue : null,
            icon: const Icon(Icons.arrow_forward),
            label: const Text('CONTINUE TO CONVERSION'),
          )),
        ],
      ),
    );
  }

  Widget _card({required String title, required Widget child}) => Card(
    color: const Color(0xFF111117),
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20), side: const BorderSide(color: Color(0xFF292932))),
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: const TextStyle(color: Color(0xFFE00022), fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 1.1)),
        const SizedBox(height: 10),
        child,
      ]),
    ),
  );
}
'''.replace("Color(0xFFAAAA B5)", "Color(0xFFAAAAB5)"))

# ---------------------------------------------------------------------------
# Main.dart: deterministic dashboard-first navigation, clean English/red theme
# ---------------------------------------------------------------------------
main = root / "lib" / "main.dart"
mt = main.read_text(encoding="utf-8")

# Add custom imports.
if "import 'screens/red_home_screen.dart';" not in mt:
    mt = mt.replace("import 'screens/pitch_detection_screen.dart';",
                    "import 'screens/pitch_detection_screen.dart';\nimport 'screens/red_home_screen.dart';\nimport 'screens/training_screen.dart';\nimport 'screens/full_rvc_screen.dart';\nimport 'package:url_launcher/url_launcher.dart';")

# The model picker already copies selected files into the app-owned library. Do not import the same path a second time.
mt = mt.replace("final importedPath = await _importPickedFile(kind: 'model', sourcePath: path);", "final importedPath = File(path).absolute.path;")
mt = mt.replace("final importedPath = path == null ? null : await _importPickedFile(kind: 'index', sourcePath: path);", "final importedPath = path == null ? null : File(path).absolute.path;")

# Theme/branding text.
mt = mt.replace("Ultimate RVC Mobile", "Reds Ultimate RVC")
mt = mt.replace("primarySwatch: Colors.blue,", "primarySwatch: Colors.red,")
mt = re.sub(r"theme: ThemeData\(.*?\),\n      home:", """theme: ThemeData(
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFFE00022), brightness: Brightness.dark, surface: const Color(0xFF111117)),
        scaffoldBackgroundColor: const Color(0xFF07070A),
        canvasColor: const Color(0xFF0B0B10),
        cardColor: const Color(0xFF111117),
        appBarTheme: const AppBarTheme(backgroundColor: Color(0xFF09090D), foregroundColor: Colors.white, elevation: 0, centerTitle: true),
        elevatedButtonTheme: ElevatedButtonThemeData(style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFE00022), foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(13)))),
        outlinedButtonTheme: OutlinedButtonThemeData(style: OutlinedButton.styleFrom(foregroundColor: const Color(0xFFFF5269), side: const BorderSide(color: Color(0xFF8D1B2B)))),
        visualDensity: VisualDensity.adaptivePlatformDensity,
        useMaterial3: true,
      ),
      home:""", mt, count=1, flags=re.S)
mt = mt.replace("backgroundColor: Colors.white", "backgroundColor: const Color(0xFF07070A)")
for a,b in {
    "音频推理":"Audio Conversion",
    "实时推理":"Realtime RVC",
    "变声器模式":"Voice Changer",
    "分贝仪":"dB Meter",
    "音高检测":"Pitch Detection",
    "参数解释":"RVC Controls",
    "mobile.index 转换教程":"Index Tools",
}.items():
    mt = mt.replace(a,b)

# Module indexes: 0 dashboard, 1 audio, 2 realtime, 3 changer, 4 index, 5 controls, 6 dB, 7 pitch.
for name, old_index, new_index in [
    ("_openAudioConversion", 0, 1),
    ("_openRealtimeInference", 1, 2),
    ("_openVoiceChanger", 2, 3),
    ("_openIndexConverter", 3, 4),
    ("_openParameterGuide", 4, 5),
    ("_openDecibelMeter", 5, 6),
    ("_openPitchDetection", 6, 7),
]:
    old_line = f"void {name}() {{\n    setState(() => _moduleIndex = {old_index});"
    new_line = f"void {name}() {{\n    setState(() => _moduleIndex = {new_index});"
    if old_line not in mt:
        raise RuntimeError(f"Could not patch {name}")
    mt = mt.replace(old_line, new_line, 1)

# Whenever normal audio flow returns to the main area, return to audio module 1.
for method in ("_onSongSelected", "_continueToGenerate", "_onGenerationComplete", "_startNewGeneration"):
    pat = rf"(Future<void>\s+{method}\([^{{]*\{{|void\s+{method}\([^{{]*\{{)"
    # We only replace the first _moduleIndex = 0 occurring after the method.
    m = re.search(pat, mt)
    if m:
        tail_start = m.start()
        tail_end = mt.find("\n  }", tail_start)
        if tail_end > tail_start:
            segment = mt[tail_start:tail_end]
            segment = segment.replace("_moduleIndex = 0;", "_moduleIndex = 1;")
            mt = mt[:tail_start] + segment + mt[tail_end:]

# Load state: dashboard is the launch destination. Audio progress itself remains saved.
mt = re.sub(r"_moduleIndex\s*=\s*prefs\.getInt\('moduleIndex'\)\s*\?\?\s*\d+;", "_moduleIndex = 0;", mt, count=1)
mt = mt.replace("final prefs = await SharedPreferences.getInstance();\n    if (!mounted) return;",
                "final prefs = await SharedPreferences.getInstance();\n    await prefs.remove('moduleIndex');\n    if (!mounted) return;", 1)

# Replace the entire moduleScreens list with a clean authoritative one.
start = mt.find("    final moduleScreens = [")
end = mt.find("    return PopScope(", start)
if start < 0 or end < 0:
    raise RuntimeError("moduleScreens block not found")

dashboard = '''    final moduleScreens = [
      RedHomeScreen(
        onGenerate: _openAudioConversion,
        onSongCovers: _openAudioConversion,
        onRealtime: _openRealtimeInference,
        onVoiceChanger: _openVoiceChanger,
        onModels: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ModelPickerScreen(
          onModelSelected: _onModelSelected,
          onModelCleared: _onModelCleared,
          onIndexSelected: _onIndexSelected,
          onContinue: _continueToGenerate,
          selectedModelPath: _selectedModelPath,
          selectedModelDisplayName: _selectedModelDisplayName,
          selectedIndexPath: _selectedIndexPath,
          selectedIndexDisplayName: _selectedIndexDisplayName,
          selectedSongPath: _selectedSongPath,
          selectedSongDisplayName: _selectedSongDisplayName,
        ))),
        onTrain: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const TrainingScreen())),
        onAudioTools: _openIndexConverter,
        onSettings: _openParameterGuide,
        onFullRvc: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => FullRvcScreen(onConvert: _openAudioConversion, onModels: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ModelPickerScreen(onModelSelected: _onModelSelected, onModelCleared: _onModelCleared, onIndexSelected: _onIndexSelected, onContinue: _continueToGenerate, selectedModelPath: _selectedModelPath, selectedModelDisplayName: _selectedModelDisplayName, selectedIndexPath: _selectedIndexPath, selectedIndexDisplayName: _selectedIndexDisplayName, selectedSongPath: _selectedSongPath, selectedSongDisplayName: _selectedSongDisplayName))), onRealtime: _openRealtimeInference, onVoiceChanger: _openVoiceChanger, onTraining: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const TrainingScreen())), onIndexTools: _openIndexConverter))),
        onYouTube: _openCreatorYouTube,
      ),
      GestureDetector(
        behavior: HitTestBehavior.translucent,
        onHorizontalDragUpdate: _handleAudioHorizontalDragUpdate,
        onHorizontalDragEnd: _handleAudioHorizontalDragEnd,
        child: PageView(
          controller: _audioPageController,
          physics: const NeverScrollableScrollPhysics(),
          onPageChanged: _onAudioPageChanged,
          children: audioScreens,
        ),
      ),
      RealtimeInferenceScreen(
        otherModeRunning: _generationState.isGenerating,
        onRunningChanged: _onRealtimeInferenceRunningChanged,
      ),
      VoiceChangerScreen(
        otherModeRunning: _generationState.isGenerating || (_inferenceProcessRunning && !_voiceChangerProcessing),
        onProcessingChanged: _onVoiceChangerProcessingChanged,
      ),
      IndexConverterScreen(),
      ParameterGuideScreen(),
      DecibelMeterScreen(isActive: _moduleIndex == 6),
      PitchDetectionScreen(isActive: _moduleIndex == 7),
    ];

'''
mt = mt[:start] + dashboard + mt[end:]

# Bottom navigation belongs only to the audio workflow (module 1).
mt = mt.replace("bottomNavigationBar: _moduleIndex == 0", "bottomNavigationBar: _moduleIndex == 1")

# Replace drawer completely.
dstart = mt.find("  Drawer _buildDrawer()")
dend = mt.find("  @override\n  Widget build", dstart)
if dstart < 0 or dend < 0:
    raise RuntimeError("Drawer block not found")
drawer = r'''  Future<void> _openCreatorYouTube() async {
    final uri = Uri.parse('https://www.youtube.com/@Little-Red-Big-Smile');
    final opened = await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (!opened && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Unable to open YouTube. Check your connection and try again.')),
      );
    }
  }

  Drawer _buildDrawer() {
    return Drawer(
      backgroundColor: const Color(0xFF0B0B10),
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          DrawerHeader(
            decoration: const BoxDecoration(
              gradient: LinearGradient(colors: [Color(0xFF270008), Color(0xFF0B0B10)], begin: Alignment.topLeft, end: Alignment.bottomRight),
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.end, children: [
              SizedBox(height: 68, child: SvgPicture.asset('assets/images/reds-ultimate-rvc-logo.svg', fit: BoxFit.contain, alignment: Alignment.centerLeft)),
              const SizedBox(height: 7),
              const Text("RED'S ULTIMATE RVC", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 17)),
            ]),
          ),
          ListTile(leading: const Icon(Icons.home), title: const Text('Home'), selected: _moduleIndex == 0, onTap: () { setState(() => _moduleIndex = 0); _saveState(); Navigator.pop(context); }),
          ListTile(leading: const Icon(Icons.graphic_eq), title: const Text('Audio Conversion'), selected: _moduleIndex == 1, onTap: _openAudioConversion),
          ListTile(leading: const Icon(Icons.settings_voice), title: const Text('Realtime RVC'), selected: _moduleIndex == 2, onTap: _openRealtimeInference),
          ListTile(leading: const Icon(Icons.record_voice_over), title: const Text('Voice Changer'), selected: _moduleIndex == 3, onTap: _openVoiceChanger),
          ListTile(leading: const Icon(Icons.sync_alt), title: const Text('Index Tools'), selected: _moduleIndex == 4, onTap: _openIndexConverter),
          ListTile(leading: const Icon(Icons.tune), title: const Text('RVC Controls'), selected: _moduleIndex == 5, onTap: _openParameterGuide),
          ListTile(leading: const Icon(Icons.speed), title: const Text('dB Meter'), selected: _moduleIndex == 6, onTap: _openDecibelMeter),
          ListTile(leading: const Icon(Icons.multitrack_audio), title: const Text('Pitch Detection'), selected: _moduleIndex == 7, onTap: _openPitchDetection),
          const Divider(color: Color(0xFF282832)),
          ListTile(leading: const Icon(Icons.library_music), title: const Text('Model Library'), onTap: () {
            Navigator.pop(context);
            Navigator.of(context).push(MaterialPageRoute(builder: (_) => ModelPickerScreen(
              onModelSelected: _onModelSelected,
              onModelCleared: _onModelCleared,
              onIndexSelected: _onIndexSelected,
              onContinue: _continueToGenerate,
              selectedModelPath: _selectedModelPath,
              selectedModelDisplayName: _selectedModelDisplayName,
              selectedIndexPath: _selectedIndexPath,
              selectedIndexDisplayName: _selectedIndexDisplayName,
              selectedSongPath: _selectedSongPath,
              selectedSongDisplayName: _selectedSongDisplayName,
            )));
          }),
          ListTile(leading: const Icon(Icons.open_in_new), title: const Text('Full RVC Engine'), onTap: () {
            Navigator.pop(context);
            Navigator.of(context).push(MaterialPageRoute(builder: (_) => FullRvcScreen(onConvert: _openAudioConversion, onModels: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ModelPickerScreen(onModelSelected: _onModelSelected, onModelCleared: _onModelCleared, onIndexSelected: _onIndexSelected, onContinue: _continueToGenerate, selectedModelPath: _selectedModelPath, selectedModelDisplayName: _selectedModelDisplayName, selectedIndexPath: _selectedIndexPath, selectedIndexDisplayName: _selectedIndexDisplayName, selectedSongPath: _selectedSongPath, selectedSongDisplayName: _selectedSongDisplayName))), onRealtime: _openRealtimeInference, onVoiceChanger: _openVoiceChanger, onTraining: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const TrainingScreen())), onIndexTools: _openIndexConverter)));
          }),
          ListTile(leading: const Icon(Icons.model_training), title: const Text('Voice Dataset Lab'), onTap: () {
            Navigator.pop(context);
            Navigator.of(context).push(MaterialPageRoute(builder: (_) => const TrainingScreen()));
          }),
        ],
      ),
    );
  }

'''
mt = mt[:dstart] + drawer + mt[dend:]
write(main, mt)

# Fix old package imports in tests.
testdir = root / "test"
if testdir.exists():
    for dart in testdir.rglob("*.dart"):
        write(dart, dart.read_text(encoding="utf-8").replace("package:ultimate_rvc_mobile/", "package:reds_ultimate_rvc/"))

# English-only UI translation pass. This runs over every Dart screen, including
# error messages and tooltips, not just the dashboard.
translations = {
  "生成已中止：推理进程已结束": "Generation aborted: the inference process ended",
  "生成已中止：推理进程已中断": "Generation aborted: the inference process was interrupted",
  "生成已中止": "Generation aborted",
  "生成完成": "Generation complete",
  "初始化失败": "Initialization failed",
  "RVC 初始化失败：$e": "RVC initialization failed: $e",
  "再按一次退出": "Press back again to exit",
  "确定": "OK",
  "音频推理": "Audio Conversion",
  "实时推理": "Realtime Inference",
  "变声器模式": "Voice Changer",
  "分贝仪": "Decibel Meter",
  "音高检测": "Pitch Detection",
  "参数解释": "RVC Controls",
  "mobile.index 转换教程": "Mobile Index Guide",
  "音频": "audio",
  "音色": "voice",
  "生成": "Generate",
  "结果": "Results",
  "未启动": "Not started",
  "需要麦克风权限": "Microphone permission required",
  "实时测量中": "Measuring live",
  "测量失败：$error": "Measurement failed: $error",
  "已锁定": "Locked",
  "分贝实时曲线": "Live decibel chart",
  "解除锁定": "Unlock",
  "锁定当前数值": "Lock current reading",
  "准备生成": "Ready to generate",
  "初始化中...": "Initializing...",
  "处理出错了，请重新生成": "Processing failed. Please try again.",
  "恢复进度中": "Restoring progress",
  "保存进度点": "Saving checkpoint",
  "无法继续": "Cannot continue",
  "当前任务与历史不一致，无法继续。\\n不做任何操作。": "This task does not match the saved history. No changes were made.",
  "推理进程已中断": "Inference process interrupted",
  "推理进程已断开": "Inference process disconnected",
  "处理出错：$message": "Processing error: $message",
  "正在中止生成": "Stopping generation",
  "正在等待推理进程结束": "Waiting for the inference process to stop",
  "终止生成失败：$e": "Could not stop generation: $e",
  "生成音频": "Generate audio",
  "输入音频：": "Input audio: ",
  "音色模型：": "Voice model: ",
  "索引文件：": "Index file: ",
  "未选择": "Not selected",
  "参数": "parameters",
  "Pitch（音调设置）": "Pitch",
  "Index Rate（索引强度）": "Index Rate",
  "Index Rate（检索特征占比）": "Index Rate",
  "Formant（性别因子/声线粗细）": "Formant",
  "Noise Gate（噪声过滤）": "Noise Gate",
  "Sample Rate（采样率）": "Sample Rate",
  "Filter Radius（音高滤波）": "Filter Radius",
  "RMS Mix（响度因子）": "RMS Mix",
  "RMS Mix（响度混合）": "RMS Mix",
  "Protect（辅音保护）": "Protect",
  "高级参数": "Advanced settings",
  "降噪优化": "Noise reduction",
  "只影响处理结果，不改原始录音文件": "Affects processed audio only; the original recording is unchanged.",
  "音域过滤": "Vocal frequency filter",
  "恢复默认": "Restore defaults",
  "生成中...": "Generating...",
  "生成用时：": "Processing time: ",
  "正在中止": "Stopping",
  "终止生成": "Stop generation",
  "重新生成": "Generate again",
  "开始生成": "Start generation",
  "继续未完成": "Resume",
  "处理时间取决于音频长度": "Processing time depends on audio length",
  "为什么要先转换": "Why conversion is needed",
  "手机端当前只读取 mobile.index。标准 RVC/FAISS .index 需要先在电脑上转换，转换后再传到手机选择。": "This Android version reads mobile.index files. Standard FAISS indexes are not supported directly.",
  "转换命令": "Conversion command",
  "在仓库目录执行：\\npython3 ultimate_rvc_mobile/python/convert_faiss_index.py input.index output.mobile.index": "Index conversion is not available in this Android version.",
  "请选择 .onnx 模型文件": "Please select an .onnx model file",
  "选择模型失败：$e": "Model selection failed: $e",
  "请选择 mobile.index 文件": "Please select a mobile.index file",
  "选择索引失败：$e": "Index selection failed: $e",
  "选择音色模型": "Select voice model",
  "已选择音色：": "Selected voice: ",
  "支持：.onnx 模型": "Supported: .onnx models",
  "更换模型": "Change model",
  "选择模型": "Select model",
  "清除模型": "Clear model",
  "索引文件（可选）": "Index file (optional)",
  "支持：mobile.index 索引": "Supported: mobile.index files",
  "更换 mobile.index": "Change mobile.index",
  "选择 mobile.index": "Select mobile.index",
  "清除索引": "Clear index",
  "继续": "Continue",
  "当前音频：": "Current audio: ",
  "推荐值：0": "Recommended: 0",
  "推荐值：3": "Recommended: 3",
  "推荐值：0.25": "Recommended: 0.25",
  "推荐值：0.33": "Recommended: 0.33",
  "推荐值：48000": "Recommended: 48000",
  "推荐值：6.0": "Recommended: 6.0",
  "推荐值：0.0": "Recommended: 0",
  "推荐值：默认开启": "Recommended: enabled by default",
  "推荐值：默认开启；保留区：60–2500 Hz": "Recommended: enabled; preserve range: 60–2500 Hz",
  "推荐值：0.5 到 0.7，稳妥从 0.6 开始": "Recommended: 0.5–0.7; start at 0.6",
  "音频推理推荐值：0；实时推理推荐值：35 dB": "Audio conversion: 0; realtime: 35 dB",
  "推荐值：10 秒；范围：0 到 60 秒": "Recommended: 10 seconds; range: 0–60 seconds",
  "推荐值：3 秒；范围：0 到 10 秒": "Recommended: 3 seconds; range: 0–10 seconds",
  "改变整体音高，范围 -24 到 24 半音。调高适合男声转女声或目标声音更高；调低适合女声转男声或目标声音更低。优先在 -4 到 +4 半音内微调，幅度太大容易失真。": "Changes pitch from -24 to +24 semitones. Small adjustments (around -4 to +4) usually sound more natural; large shifts can distort the voice.",
  "通过共振峰偏移改变声线粗细和性别感，范围 -4 到 4。调高更细、更亮；调低更粗、更厚。它和 Pitch 可以共存：Pitch 调音调高低，Formant 调声线粗细。": "Changes vocal resonance from -4 to +4. Pitch changes note height; formant changes vocal character and thickness.",
  "控制检索特征参与程度。调高更像目标音色，但更容易带出底噪和毛刺；调低更干净稳定，但相似度会下降。": "Controls how strongly index features affect the result. Higher values may improve similarity but add noise; lower values may sound cleaner.",
  "平滑音高波动，减少抖动、破音和细碎毛刺。调高会更平稳，但可能抹掉细节；调低会保留更多细节，但更容易抖。": "Smooths pitch fluctuations. Higher values reduce jitter but may remove detail.",
  "控制输出保留多少原音的响度起伏。调高更平稳；调低更保留原始情绪和力度。原音底噪明显时不要调得太低。": "Controls how much of the original volume envelope is retained. Lower values preserve more of the original dynamics.",
  "保护齿音、呼吸声和清辅音，减少发糊和吞字。调高更清晰但不够像；调低更像目标音色，但更容易糊。": "Protects consonants and breaths. Higher values can improve clarity but reduce voice similarity.",
  "只在处理时生效，不改原始录音文件。0 表示不过滤；更适合压低麦克风底噪、空窗噪声和残留低电平杂音。门限过高会吞掉气声、尾音和弱音，断续时先降低 Noise Gate。": "Applies only to processed audio; the original recording is unchanged. Higher thresholds reduce background noise but may cut off quiet breaths and word endings.",
  "处理时输入和输出都生效，不改原始录音文件。用于压低底噪、突刺、电流感、包络噪声和刺耳齿音，尽量保住尾音与弱音；如果人声被压得太干，可以关闭。": "Applies to processed input and output; the original recording is unchanged. Reduces background noise and harsh sibilance while preserving quiet details.",
  "只在处理时生效，不改原始录音文件。50–60 Hz 以下轻收低频轰鸣；60–2500 Hz 保持主体；2500–4500 Hz 保留咬字清晰度并逐步收高频；4500 Hz 以上用柔和高架衰减压毛刺，避免声音发闷。二次录制的人声会带扬声器、房间和麦克风噪声，这个开关用于清理明显越界的低频轰鸣和高频毛刺。": "Applies to processed audio only. Reduces low-frequency rumble and harsh high-frequency artifacts while preserving speech clarity.",
  "决定导出音频规格。默认使用 48000，便于和模型输出及常见视频音频流程保持一致。": "Sets the export audio format. The default is 48 kHz.",
  "采样长度": "Chunk length",
  "实时推理每次处理的音频块长度。调大更稳但延迟更高；调小延迟更低，但更容易卡顿或音色不稳定。": "Length of each realtime audio chunk. Longer chunks may be steadier but increase latency.",
  "淡入淡出长度": "Crossfade length",
  "实时推理块之间的衔接长度。调高能减少断裂和爆音，但会增加拖尾；调低响应更快，但更容易听到接缝。": "Smooths transitions between realtime chunks. Higher values reduce clicks but can add trailing audio.",
  "额外推理时长": "Extra inference context",
  "给实时推理保留的上下文长度。调高更稳定，但会增加延迟和计算量；设备性能不足时应适当降低。": "Additional context for realtime inference. Higher values may improve stability but increase latency and processing load.",
  "延时缓冲": "Delay buffer",
  "实时推理会先缓存一段输出再播放。调高更稳但延迟更长；调到 0 会尽快播放，设备性能不足时更容易断续。": "Realtime output is buffered before playback. More buffering may improve stability but increases latency.",
  "播放延迟": "Playback delay",
  "变声器悬浮窗在正常播放和试听前显示倒计时。0 秒表示立即播放；需要留出切回目标应用或准备录入环境时可调高。": "The voice-changer floating control counts down before playback. Set to 0 for immediate playback.",
  "中断生成": "Stop generation",
  "需要停止时手动触发": "Use this control when you need to stop a task",
  "离线生成时可点红色“终止生成”。变声器橙色处理阶段可长按悬浮按钮中断。": "During offline conversion, use Stop Generation. During voice-changer processing, long-press the floating control to cancel.",
  "稳定": "stable",
  "灵敏": "Sensitive",
  "极灵敏": "Very sensitive",
  "实时检测中": "Detecting pitch",
  "检测失败：$error": "Detection failed: $error",
  "已将当前音高设为相对音高基准 0": "Current pitch set as relative reference 0",
  "音高检测设置": "Pitch detection settings",
  "基准音高（留空默认 C4）": "Reference pitch (leave blank for C4)",
  "图表 Y 轴模式": "Chart Y-axis mode",
  "相对半音值": "Relative semitones",
  "频率 Hz": "Frequency (Hz)",
  "音名（A2/C4）": "Note name (A2/C4)",
  "检测灵敏度": "Detection sensitivity",
  "取消": "Cancel",
  "基准音高格式无效，请使用 C4 / F#3 这类格式": "Invalid reference pitch. Use a format such as C4 or F#3.",
  "保存": "Save",
  "音高实时曲线": "Live pitch chart",
  "音名": "Note",
  "半音": "semitones",
  "将当前音高设为相对 0": "Set current pitch as relative zero",
  "锁定当前音高": "Lock current pitch",
  "手机端限制": "Android limitations",
  "这个页面仅供演示。": "This screen is experimental and is not a reliable realtime feature yet.",
  "手机端实时推理性能和系统音频能力限制很大。": "Realtime inference is heavily limited by phone performance and Android audio routing.",
  "当前无法指定输入输出设备。": "Input and output audio devices cannot currently be selected.",
  "实际效果可能大约每 6 秒卡一次，没有实际用途。": "Audio may stutter about every six seconds; this feature is not ready for dependable use.",
  "知道了": "Got it",
  "正在停止实时推理": "Stopping realtime inference",
  "已停止": "Stopped",
  "正在启动实时推理": "Starting realtime inference",
  "实时推理失败：$error": "Realtime inference failed: $error",
  "实时推理中": "Realtime inference running",
  "启动失败：$e": "Startup failed: $e",
  "状态：$_status": "Status: $_status",
  "选择 .onnx 模型": "Select .onnx model",
  "更换 .onnx 模型": "Change .onnx model",
  "延时缓冲：": "Delay buffer: ",
  "音频采样率": "Audio sample rate",
  "采样长度：": "Chunk length: ",
  "淡入淡出长度：": "Crossfade length: ",
  "额外推理时长：": "Extra inference context: ",
  "停止实时推理": "Stop realtime inference",
  "启动实时推理": "Start realtime inference",
  "Ultimate RVC 生成音频": "Audio generated by Red's Ultimate RVC",
  "这是 Ultimate RVC 生成的音频。": "This audio was generated by Red's Ultimate RVC.",
  "分享失败：$e": "Share failed: $e",
  "已保存：$savedPath": "Saved: $savedPath",
  "保存失败：$e": "Save failed: $e",
  "生成结果": "Conversion result",
  "音频已生成": "Audio generated",
  "暂停": "Pause",
  "播放": "Play",
  "分享": "Share",
  "选择音频失败：$e": "Audio selection failed: $e",
  "录音失败：$e": "Recording failed: $e",
  "选择音频": "Select audio",
  "已选择：": "Selected: ",
  "支持：MP3、WAV、M4A、FLAC、OGG": "Supported formats: MP3, WAV, M4A, FLAC, OGG",
  "更换音频": "Change audio",
  "清除音频": "Clear audio",
  "停止录音": "Stop recording",
  "直接录音": "Record audio",
  "录音时长：": "Recording duration: ",
  "请先选择 .onnx 音色模型": "Please select an .onnx voice model first",
  "录制模式": "Recording mode",
  "灰色：待机。点一下开始录音，长按关闭悬浮窗。": "Gray: idle. Tap to start recording; long-press to close the floating control.",
  "绿色：录音中，并显示录制时长。点一下停止录音并开始处理，长按取消录音并回到灰色。": "Green: recording. Tap to stop and process; long-press to cancel and return to idle.",
  "橙色：处理中，并显示处理进度。点一下进入亮黄色暂停态，长按取消处理并清空临时文件，回到灰色初始态。": "Orange: processing. Tap to pause; long-press to cancel and clear temporary files.",
  "亮黄色：处理已暂停。点一下继续处理，长按放弃本轮处理并清空临时文件，回到灰色初始态。": "Yellow: paused. Tap to resume; long-press to discard this session and clear temporary files.",
  "蓝色：处理完成，显示处理后总时长。点一下进入天蓝色试听倒计时。": "Blue: processing complete. Tap to start the preview countdown.",
  "蓝色长按：结束本轮并清理文件，回到灰色。": "Long-press blue to end the session and clean up its files.",
  "天蓝色：显示播放或试听倒计时。": "Light blue: playback or preview countdown.",
  "红色：试听播放中，显示剩余时间。点一下暂停并变成青绿色，再点一下继续后恢复红色，长按直接结束试听。": "Red: preview playing. Tap to pause; tap again to resume; long-press to end the preview.",
  "青绿色：播放已暂停。": "Teal: playback paused.",
  "蓝色和红色：都可以双击保存处理后的音频。": "Double-tap blue or red to save the converted audio.",
  "蓝色和红色：都可以三击保存本轮原始录音。": "Triple-tap blue or red to save the original recording.",
  "手势一触发会先弹出提示，再执行保存、暂停、继续、取消等耗时操作。": "A short notice appears before save, pause, resume or cancel actions.",
  "录制和处理会占用推理资源；如果音频推理或实时推理正在运行，点击开始录音会提示暂时不能用。": "Recording and conversion share inference resources. Recording is unavailable while another inference task is running.",
  "音色模型": "Voice model",
  "索引文件": "Index file",
  "移除索引": "Remove index",
  "处理声线参数": "Voice processing controls",
  "悬浮控制": "Floating control",
  "关闭悬浮窗": "Close floating control",
  "打开悬浮窗": "Open floating control",
  "RVC 初始化失败：${e.message}": "RVC initialization failed: ${e.message}",
  "检查模型失败：${e.message}": "Model check failed: ${e.message}",
  "显示提示失败：${e.message}": "Could not display notice: ${e.message}",
  "RVC 推理失败：${e.message}": "RVC inference failed: ${e.message}",
  "终止生成失败：${e.message}": "Could not stop generation: ${e.message}",
  "获取版本失败：${e.message}": "Could not get version: ${e.message}",
  "开始录音失败：${e.message}": "Could not start recording: ${e.message}",
  "启动实时推理失败：${e.message}": "Could not start realtime inference: ${e.message}",
  "停止实时推理失败：${e.message}": "Could not stop realtime inference: ${e.message}",
  "停止录音失败：${e.message}": "Could not stop recording: ${e.message}",
  "保存失败：${e.message}": "Save failed: ${e.message}",
  "读取音频时长失败：${e.message}": "Could not read audio duration: ${e.message}",
  "转换失败：${e.message}": "Conversion failed: ${e.message}",
  "启动变声器失败：${e.message}": "Could not start voice changer: ${e.message}",
  "停止变声器失败：${e.message}": "Could not stop voice changer: ${e.message}",
  "退出全屏": "Exit full screen",
  "清空曲线": "Clear chart",
  "放大图表": "Enlarge chart",
  "时间": "Time",
  "暂无数据": "No data yet",
  "相对半音值：": "Relative semitones: ",
  "输入音频": "Input audio",
  "当前音频": "Current audio",
  "音高": "Pitch",
  "音调": "Pitch",
  "推荐值": "Recommended",
  "样本": "sample",
  "时长": "duration",
  "麦克风权限": "microphone permission",
  "需要": "required",
  "实时": "realtime",
  "推理": "inference",
  "模型": "model",
  "索引": "index",
  "选择": "Select",
  "更换": "Change",
  "清除": "Clear",
  "已选择": "Selected",
  "正在": "In progress",
  "停止": "Stop",
  "恢复": "Restore",
  "默认": "default",
  "处理": "Processing",
  "录音": "recording",
  "曲线": "chart",
  "锁定": "Lock",
  "频率": "Frequency",
  "关闭": "Close",
  "打开": "Open",
  "悬浮窗": "floating control",
  "本轮": "this session",
  "清空": "clear",
  "临时文件": "temporary files",
  "延迟": "latency",
  "秒": "sec",
  "失败": "failed",
  "错误": "error",
  "已": "Done",
  "当前": "current",
  "设置": "settings",
  "相对": "relative",
  "基准": "reference",
  "检测": "detection",
  "启动": "Start",
  "退出": "Exit",
  "按钮": "button",
  "权限": "permission",
  "格式": "format",
  "无效": "invalid",
  "请": "Please",
  "使用": "Use",
  "图表": "chart",
  "输入": "input",
  "输出": "output",
  "缓冲": "buffer",
  "颜色": "color",
  "结束": "End",
  "显示": "show",
  "长按": "Long-press",
  "点击": "Tap",
  "双击": "Double-tap",
  "三击": "Triple-tap",
  "状态": "Status",
  "手机端": "Android",
  "限制": "limitations",
  "演示": "demo",
  "没有": "no",
  "实际": "actual",
  "无法": "cannot",
  "为什么": "Why",
  "转换": "conversion",
  "教程": "guide",
  "电脑": "computer",
  "上传": "upload",
  "标准": "standard",
  "读取": "read",
  "先": "first",
  "范围": "range",
  "改变": "change",
  "整体": "overall",
  "调高": "increase",
  "调低": "decrease",
  "适合": "suitable",
  "优先": "prefer",
  "微调": "fine-tune",
  "幅度": "amount",
  "太大": "too large",
  "容易": "likely",
  "失真": "distortion",
  "通过": "using",
  "共振峰": "formant",
  "偏移": "shift",
  "声线": "voice character",
  "粗细": "thickness",
  "性别感": "gender character",
  "更细": "thinner",
  "更亮": "brighter",
  "更粗": "thicker",
  "更厚": "fuller",
  "它和": "It and",
  "可以": "can",
  "共存": "coexist",
  "调": "adjust",
  "控制": "Controls",
  "参与": "participation",
  "程度": "level",
  "更像": "more similar",
  "目标": "target",
  "但": "but",
  "带出": "introduce",
  "底噪": "background noise",
  "毛刺": "artifacts",
  "更干净": "cleaner",
  "相似度": "similarity",
  "平滑": "smooth",
  "波动": "fluctuation",
  "减少": "reduce",
  "抖动": "jitter",
  "破音": "crackling",
  "细碎": "small",
  "可能": "may",
  "抹掉": "remove",
  "细节": "detail",
  "保留": "preserve",
  "多少": "how much",
  "原音": "original audio",
  "响度": "loudness",
  "起伏": "variation",
  "更平稳": "steadier",
  "情绪": "expression",
  "力度": "intensity",
  "明显": "noticeable",
  "不要": "do not",
  "保护": "protect",
  "齿音": "sibilance",
  "呼吸声": "breaths",
  "清辅音": "unvoiced consonants",
  "发糊": "muddiness",
  "吞字": "swallowed words",
  "清晰": "clear",
  "不够": "less",
  "容易糊": "may sound muddy",
  "门限": "threshold",
  "过高": "too high",
  "会": "may",
  "吞掉": "cut off",
  "气声": "breaths",
  "尾音": "word endings",
  "弱音": "quiet sounds",
  "断续": "intermittent",
  "降低": "lower",
  "开启": "enabled",
  "处理时": "during processing",
  "输入和输出": "input and output",
  "用于": "used to",
  "压低": "reduce",
  "突刺": "transients",
  "电流感": "electrical noise",
  "包络噪声": "envelope noise",
  "刺耳": "harsh",
  "尽量": "as much as possible",
  "如果": "if",
  "人声": "voice",
  "太干": "too dry",
  "可以关闭": "can be turned off",
  "保留区": "preserve range",
  "以下": "below",
  "保持主体": "preserve the core",
  "保留咬字清晰度": "preserve speech clarity",
  "逐步收高频": "gradually reduce high frequencies",
  "以上": "above",
  "柔和": "gentle",
  "高架衰减": "high-shelf attenuation",
  "避免": "avoid",
  "发闷": "muffled sound",
  "二次录制": "re-recorded",
  "会带": "may include",
  "扬声器": "speaker",
  "房间": "room",
  "麦克风噪声": "microphone noise",
  "这个开关": "This switch",
  "用于清理": "helps clean",
  "明显越界": "out-of-range",
  "低频轰鸣": "low-frequency rumble",
  "高频毛刺": "high-frequency artifacts",
  "决定": "Determines",
  "导出": "export",
  "规格": "format",
  "便于": "to help",
  "模型输出": "model output",
  "常见": "common",
  "视频音频流程": "video and audio workflows",
  "每次": "each time",
  "音频块": "audio chunk",
  "调大": "increase",
  "更稳": "more stable",
  "延迟更高": "higher latency",
  "调小": "decrease",
  "延迟更低": "lower latency",
  "卡顿": "stuttering",
  "音色不稳定": "unstable voice tone",
  "块之间": "between chunks",
  "衔接": "transition",
  "减少断裂": "reduce breaks",
  "爆音": "pops",
  "拖尾": "trailing audio",
  "响应更快": "faster response",
  "接缝": "seams",
  "保留的上下文长度": "reserved context length",
  "更稳定": "more stable",
  "增加": "increase",
  "计算量": "processing load",
  "设备性能不足时": "on lower-powered devices",
  "适当降低": "reduce as needed",
  "先缓存": "buffers first",
  "一段输出再播放": "output before playback",
  "更稳但": "more stable but",
  "尽快播放": "play as soon as possible",
  "更容易断续": "more likely to stutter",
  "悬浮窗在正常播放": "floating control before playback",
  "显示倒计时": "shows a countdown",
  "立即播放": "play immediately",
  "需要留出": "allow time",
  "切回目标应用": "switch back to the target app",
  "准备录入环境": "prepare the recording environment",
  "手动触发": "trigger manually",
  "离线生成时": "during offline conversion",
  "可点红色": "tap the red",
  "橙色处理阶段": "orange processing state",
  "可长按": "long-press to",
  "中断": "stop",
  "当前音高": "current pitch",
  "设为": "set as",
  "相对音高基准": "relative pitch reference",
  "留空默认": "leave blank for default",
  "格式无效": "format is invalid",
  "请使用": "use",
  "这类格式": "format",
  "将当前音高": "Set current pitch",
  "设为相对 0": "as relative zero",
  "灰色": "Gray",
  "待机": "idle",
  "点一下": "Tap once",
  "开始录音": "start recording",
  "长按关闭": "long-press to close",
  "绿色": "Green",
  "录音中": "recording",
  "并显示录制时长": "and shows recording time",
  "停止录音并开始处理": "stop recording and process",
  "取消录音并回到灰色": "cancel recording and return to idle",
  "橙色": "Orange",
  "处理中": "processing",
  "并显示处理进度": "and shows progress",
  "进入亮黄色暂停态": "pause",
  "取消处理并清空临时文件": "cancel and clear temporary files",
  "回到灰色初始态": "return to idle",
  "亮黄色": "Yellow",
  "处理已暂停": "processing paused",
  "继续处理": "resume processing",
  "放弃本轮处理": "discard this session",
  "蓝色": "Blue",
  "处理完成": "processing complete",
  "显示处理后总时长": "shows converted duration",
  "进入天蓝色试听倒计时": "start the preview countdown",
  "蓝色长按": "Long-press blue",
  "结束本轮并清理文件": "end this session and clean up files",
  "天蓝色": "Light blue",
  "显示播放或试听倒计时": "shows playback or preview countdown",
  "红色": "Red",
  "试听播放中": "preview playing",
  "显示剩余时间": "shows time remaining",
  "暂停并变成青绿色": "pause and turn teal",
  "再点一下继续后恢复红色": "tap again to resume",
  "长按直接结束试听": "long-press to end the preview",
  "青绿色": "Teal",
  "播放已暂停": "playback paused",
  "蓝色和红色": "Blue and red",
  "都可以双击保存处理后的音频": "can be double-tapped to save converted audio",
  "都可以三击保存本轮原始录音": "can be triple-tapped to save the original recording",
  "手势一触发": "When a gesture is triggered",
  "先弹出提示": "a notice appears first",
  "再执行": "before running",
  "保存、暂停、继续、取消": "save, pause, resume or cancel",
  "等耗时操作": "long-running actions",
  "录制和处理": "Recording and conversion",
  "会占用推理资源": "use inference resources",
  "如果音频推理或实时推理正在运行": "if audio or realtime inference is running",
  "点击开始录音": "tapping Record",
  "会提示暂时不能用": "will show that recording is unavailable",
  "显示提示失败": "Could not display notice",
  "读取音频时长失败": "Could not read audio duration"
}
for dart in (root / "lib").rglob("*.dart"):
    t = dart.read_text(encoding="utf-8")
    for a, b in sorted(translations.items(), key=lambda item: len(item[0]), reverse=True):
        t = t.replace(a, b)
    write(dart, t)

# Fail the build rather than shipping any untranslated CJK UI strings.
string_literal = re.compile(r"""(?s)(?:r)?(['"])(?:\\\\.|(?!\\1).)*?\\1""")
for dart in (root / "lib").rglob("*.dart"):
    t = dart.read_text(encoding="utf-8")
    for match in string_literal.finditer(t):
        if re.search(r"[\\u3400-\\u9fff]", match.group(0)):
            line = t.count("\\n", 0, match.start()) + 1
            raise RuntimeError(f"Non-English UI string remains in {dart}:{line}: {match.group(0)[:120]}")

