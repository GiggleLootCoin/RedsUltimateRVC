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
  List<String> _indexLibrary = [];
  bool _libraryLoaded = false;
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
    final savedIndexes = prefs.getStringList('red_rvc_index_library') ?? [];
    final valid = saved.where((p) => File(p).existsSync()).toList();
    final validIndexes = savedIndexes.where((p) => File(p).existsSync()).toList();
    await prefs.setStringList('red_rvc_model_library', valid);
    await prefs.setStringList('red_rvc_index_library', validIndexes);
    if (mounted) setState(() {
      _library = valid;
      _indexLibrary = validIndexes;
      _libraryLoaded = true;
    });
  }

  Future<void> _saveLibrary() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList('red_rvc_model_library', _library);
  }

  Future<void> _saveIndexLibrary() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList('red_rvc_index_library', _indexLibrary);
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
      if (_library.contains(imported.path)) {
        await _bridge.releaseImportedFile(imported.path);
      } else {
        _library.insert(0, imported.path);
      }
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
      if (_indexLibrary.contains(imported.path)) {
        await _bridge.releaseImportedFile(imported.path);
      } else {
        _indexLibrary.insert(0, imported.path);
      }
      await _saveIndexLibrary();
      if (ext == 'mobile.index') {
        await _bridge.convertIndex(imported.path);
        _selectedIndexPath = imported.path;
        _selectedIndexDisplayName = File(imported.path).uri.pathSegments.last;
        widget.onIndexSelected(imported.path);
      }
      if (mounted) setState(() {});

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(ext == 'mobile.index' ? 'mobile.index imported and ready.' : 'Standard .index stored in your Index Library. This offline Android build does not include FAISS-to-mobile conversion.')),
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

  Future<void> _useIndex(String path) async {
    if (_ext(path) != 'mobile.index') {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Standard .index files require FAISS conversion before mobile inference.'),
      ));
      return;
    }
    await _bridge.convertIndex(path);
    _selectedIndexPath = path;
    _selectedIndexDisplayName = File(path).uri.pathSegments.last;
    widget.onIndexSelected(path);
    if (mounted) setState(() {});
  }

  Future<void> _deleteIndex(String path) async {
    try {
      await _bridge.releaseImportedFile(path);
    } catch (_) {}
    _indexLibrary.remove(path);
    if (_selectedIndexPath == path) {
      _selectedIndexPath = null;
      _selectedIndexDisplayName = null;
      widget.onIndexSelected(null);
    }
    await _saveIndexLibrary();
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
                Expanded(child: ElevatedButton.icon(onPressed: _busy || !_libraryLoaded ? null : _pickModel, icon: const Icon(Icons.upload_file), label: const Text('IMPORT MODEL'))),
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
              const Text('mobile.index files can be used directly. Standard FAISS .index files require conversion, which is not included in this offline Android build.', style: TextStyle(color: Color(0xFF9E9EA8), height: 1.3)),
              const SizedBox(height: 12),
              OutlinedButton.icon(onPressed: _busy || !_libraryLoaded ? null : _pickIndex, icon: const Icon(Icons.upload_file), label: const Text('IMPORT INDEX')),
              if (_indexLibrary.isNotEmpty) ...[
                const SizedBox(height: 12),
                const Text('IMPORTED INDEX FILES', style: TextStyle(color: Color(0xFFE00022), fontSize: 11, fontWeight: FontWeight.w900)),
                ..._indexLibrary.map((p) {
                  final mobile = _ext(p) == 'mobile.index';
                  return ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: Icon(mobile ? Icons.check_circle : Icons.inventory_2,
                      color: mobile ? const Color(0xFF5DE58A) : const Color(0xFFFFA3AE)),
                    title: Text(File(p).uri.pathSegments.last, maxLines: 1, overflow: TextOverflow.ellipsis),
                    subtitle: Text(mobile ? 'MOBILE INDEX — VALIDATED WHEN SELECTED' : 'STANDARD FAISS INDEX — CONVERSION REQUIRED'),
                    trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                      if (mobile) IconButton(onPressed: () => _useIndex(p), icon: const Icon(Icons.check), tooltip: 'Use index'),
                      IconButton(onPressed: () => _deleteIndex(p), icon: const Icon(Icons.delete_outline), tooltip: 'Delete index'),
                    ]),
                  );
                }),
              ],
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
    "mobile.index 转换教程":"Index Checker",
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

# English-only UI translation pass across every Dart screen, dialog, tooltip and error.
translations ={
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
  "音频": "Audio",
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
  "稳定": "Stable",
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
  "Ultimate RVC 生成音频": "Audio generated by Red’s Ultimate RVC",
  "这是 Ultimate RVC 生成的音频。": "This audio was generated by Red’s Ultimate RVC.",
  "分享失败：$e": "Share failed: $e",
  "已保存：$savedPath": "Saved: $savedPath",
  "保存失败：$e": "Save failed: $e",
  "生成结果": "Conversion result",
  "音频已生成": "Audio generated",
  "暂停": "Pause",
  "播放": "playback",
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
  "状态：": "Status: ",
  "相对半音值：": "Relative semitones: ",
  "输入音频": "Input audio",
  "音高": "Pitch",
  "音调": "Pitch",
  "频率": "Frequency",
  "基准": "Reference",
  "图表": "Chart",
  "锁定": "Lock",
  "检测": "Detection",
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
  "当前": "current",
  "设置": "settings",
  "相对": "relative",
  "范围": "range",
  "推荐值": "Recommended",
  "权限": "permission",
  "无效": "invalid",
  "请": "Please",
  "使用": "Use",
  "时长": "duration",
  "手机端": "Android",
  "限制": "limitations",
  "教程": "guide",
  "转换": "conversion",
  "标准": "standard",
  "读取": "read",
  "输出": "output",
  "输入": "input",
  "缓冲": "buffer",
  "显示": "show",
  "长按": "Long-press",
  "点击": "Tap",
  "双击": "Double-tap",
  "三击": "Triple-tap",
  "颜色": "color",
  "结束": "End",
  "启动": "Start",
  "状态": "Status",
  "演示": "demo",
  "无法": "cannot",
  "没有": "no",
  "实际": "actual",
  "需要": "required",
  "采样": "sample",
  "移除": "Remove",
  "文件": "file",
  "按钮": "button",
  "退出": "Exit",
  "格式": "format",
  "基准音高": "Reference pitch",
  "$status，丢包 $outputChannelDropCount": "$status, dropped packets: $outputChannelDropCount",
  "$status，playback ${audioTrackStarted ? '已Start' : '待Start'}，写入 $audioTrackWriteCount/$audioTrackWrittenSamples": "$status, playback ${audioTrackStarted ? 'started' : 'waiting'}, writes $audioTrackWriteCount/$audioTrackWrittenSamples",
  "$status，推理 ${lastInferMs}ms": "$status, inference: ${lastInferMs} ms",
  "$status，峰值 入 $lastInputPeak / 原 $lastRawOutputPeak / 出 $lastOutputPeak": "$status, peak levels — input $lastInputPeak / raw $lastRawOutputPeak / output $lastOutputPeak",
  "floating control直径：": "Floating control size: ",
  "floating control不透明度：": "Floating control opacity: ",
  "$status，播放 ${audioTrackStarted ? '已启动' : '待启动'}，写入 $audioTrackWriteCount/$audioTrackWrittenSamples": "$status, playback ${audioTrackStarted ? 'started' : 'waiting'}, writes $audioTrackWriteCount/$audioTrackWrittenSamples",
  "悬浮窗直径：": "Floating control size: ",
  "悬浮窗不透明度：": "Floating control opacity: "
}
for dart in (root / "lib").rglob("*.dart"):
    t = dart.read_text(encoding="utf-8")
    for a, b in sorted(translations.items(), key=lambda item: len(item[0]), reverse=True):
        t = t.replace(a, b)
    write(dart, t)

# ---------------------------------------------------------------------------
# Persistent storage for imported models/indexes.
# ---------------------------------------------------------------------------
workspace = root / "android/app/src/main/kotlin/com/ultimatervc/mobile/TempWorkspaceManager.kt"
if workspace.exists():
    wt = workspace.read_text(encoding="utf-8")
    old = """    fun resolveImportRoot(kind: ImportedFileKind): File {
        return File(File(appCacheDir, IMPORTS_DIRECTORY_NAME), kind.directoryName).also { it.mkdirs() }
    }"""
    new = """    fun resolveImportRoot(kind: ImportedFileKind): File {
        val baseDir = when (kind) {
            ImportedFileKind.MODEL, ImportedFileKind.INDEX -> appFilesDir
            ImportedFileKind.AUDIO -> appCacheDir
        }
        return File(File(baseDir, IMPORTS_DIRECTORY_NAME), kind.directoryName).also { it.mkdirs() }
    }"""
    if old in wt:
        wt = wt.replace(old,new)
        write(workspace,wt)

# Remove upstream's machine-specific Java home. GitHub Actions supplies a valid JDK 17.
gradle_props = root / "android/gradle.properties"
if gradle_props.exists():
    gp = gradle_props.read_text(encoding="utf-8")
    gp = re.sub(r"^org\.gradle\.java\.home=.*\n?", "", gp, flags=re.M)
    write(gradle_props, gp)

# ---------------------------------------------------------------------------
# Android branding / app icon.
# ---------------------------------------------------------------------------
manifest = root / "android/app/src/main/AndroidManifest.xml"
if manifest.exists():
    m = manifest.read_text(encoding="utf-8")
    m = re.sub(r'android:label="[^"]+"', 'android:label="Red\'s Ultimate RVC"', m, count=1)
    if 'android.permission.INTERNET' not in m:
        m = m.replace('<manifest xmlns:android="http://schemas.android.com/apk/res/android">', '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n    <uses-permission android:name="android.permission.INTERNET" />', 1)
    if 'android:icon="' in m:
        m = re.sub(r'android:icon="[^"]+"', 'android:icon="@drawable/reds_ultimate_rvc_logo"', m, count=1)
    else:
        m = m.replace('<application', '<application android:icon="@drawable/reds_ultimate_rvc_logo"', 1)
    if 'android:roundIcon="' in m:
        m = re.sub(r'android:roundIcon="[^"]+"', 'android:roundIcon="@drawable/reds_ultimate_rvc_logo"', m, count=1)
    else:
        m = m.replace('android:icon="@drawable/reds_ultimate_rvc_logo"', 'android:icon="@drawable/reds_ultimate_rvc_logo" android:roundIcon="@drawable/reds_ultimate_rvc_logo"', 1)
    write(manifest,m)

# Render SVG icon into a drawable for Android.
try:
    import cairosvg
    out = root / "android/app/src/main/res/drawable/reds_ultimate_rvc_logo.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(url=str(logo), write_to=str(out), output_width=512, output_height=512)
except Exception as exc:
    raise RuntimeError(f"Could not render approved logo: {exc}")

# Ensure every custom screen referenced by the dashboard is imported in main.dart.
final_main_pre = main.read_text(encoding="utf-8")
for imp, token in [
    ("import 'screens/red_home_screen.dart';", "RedHomeScreen("),
    ("import 'screens/training_screen.dart';", "TrainingScreen("),
    ("import 'screens/full_rvc_screen.dart';", "FullRvcScreen("),
    ("import 'screens/model_converter_screen.dart';", "ModelConverterScreen("),
]:
    if token in final_main_pre and imp not in final_main_pre:
        final_main_pre = imp + "\n" + final_main_pre
write(main, final_main_pre)

# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Direct Android SAF import for RVC models and indexes.
# Samsung My Files returns content:// URIs; this avoids relying on FilePicker
# to materialize those URIs as temporary filesystem paths.
# ---------------------------------------------------------------------------
plugin = root / "android/app/src/main/kotlin/com/ultimatervc/mobile/RVCPlugin.kt"
kt = plugin.read_text(encoding="utf-8")
imports = [
    ("import android.content.ContentValues\n", "import android.app.Activity\nimport android.content.ContentValues\nimport android.content.Intent\n"),
    ("import android.provider.MediaStore\n", "import android.provider.MediaStore\nimport android.provider.OpenableColumns\n"),
    ("import io.flutter.embedding.engine.plugins.FlutterPlugin\n", "import io.flutter.embedding.engine.plugins.FlutterPlugin\nimport io.flutter.embedding.engine.plugins.activity.ActivityAware\nimport io.flutter.embedding.engine.plugins.activity.ActivityPluginBinding\n"),
    ("import io.flutter.plugin.common.MethodCall\n", "import io.flutter.plugin.common.MethodCall\nimport io.flutter.plugin.common.PluginRegistry\n"),
    ("import java.util.Locale\n", "import java.util.Locale\nimport java.util.UUID\n"),
    ("class RVCPlugin : FlutterPlugin, MethodCallHandler, StreamHandler {", "class RVCPlugin : FlutterPlugin, MethodCallHandler, StreamHandler, ActivityAware, PluginRegistry.ActivityResultListener {"),
    ("    private lateinit var appContext: Context\n", "    private lateinit var appContext: Context\n    private var activityBinding: ActivityPluginBinding? = null\n    private var pendingDocumentPickerResult: Result? = null\n    private var pendingDocumentPickerKind: String? = null\n    private val documentPickerRequestCode = 48173\n"),
    ("            \"importPickedFile\" -> importPickedFile(call, result)\n", "            \"importPickedFile\" -> importPickedFile(call, result)\n            \"pickAndImportFile\" -> pickAndImportFile(call, result)\n"),
]
for old, new in imports:
    if old not in kt:
        raise RuntimeError("SAF import patch did not match: " + old[:90])
    kt = kt.replace(old, new, 1)

activity_methods = r'''
    override fun onAttachedToActivity(binding: ActivityPluginBinding) {
        activityBinding = binding
        binding.addActivityResultListener(this)
    }

    override fun onDetachedFromActivityForConfigChanges() {
        activityBinding?.removeActivityResultListener(this)
        activityBinding = null
    }

    override fun onReattachedToActivityForConfigChanges(binding: ActivityPluginBinding) {
        activityBinding = binding
        binding.addActivityResultListener(this)
    }

    override fun onDetachedFromActivity() {
        activityBinding?.removeActivityResultListener(this)
        activityBinding = null
        pendingDocumentPickerResult?.error("PICKER_UNAVAILABLE", "Android document picker was detached.", null)
        pendingDocumentPickerResult = null
        pendingDocumentPickerKind = null
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?): Boolean {
        if (requestCode != documentPickerRequestCode) return false
        val reply = pendingDocumentPickerResult
        val kind = pendingDocumentPickerKind
        pendingDocumentPickerResult = null
        pendingDocumentPickerKind = null
        if (reply == null || kind == null) return true
        if (resultCode != Activity.RESULT_OK) {
            reply.success(null)
            return true
        }
        val uri = data?.data
        if (uri == null) {
            reply.error("PICKER_EMPTY", "Android returned no selected document.", null)
            return true
        }
        scope.launch {
            try {
                val imported = importDocumentUri(kind, uri)
                withContext(Dispatchers.Main) {
                    reply.success(mapOf(
                        "path" to imported.path,
                        "referenceCount" to imported.referenceCount,
                        "lastUpdatedAtMs" to imported.lastUpdatedAtMs,
                    ))
                }
            } catch (error: Throwable) {
                withContext(Dispatchers.Main) {
                    reply.error("PICKER_IMPORT_FAILED", error.message ?: "Could not import the selected document.", null)
                }
            }
        }
        return true
    }

    private fun pickAndImportFile(call: MethodCall, result: Result) {
        val kind = call.argument<String>("kind")
        if (kind != "model" && kind != "index") {
            result.error("INVALID_ARGUMENTS", "Import kind must be model or index.", null)
            return
        }
        val activity = activityBinding?.activity
        if (activity == null) {
            result.error("PICKER_UNAVAILABLE", "Android document picker is not attached.", null)
            return
        }
        if (pendingDocumentPickerResult != null) {
            result.error("PICKER_BUSY", "Another document selection is already open.", null)
            return
        }
        pendingDocumentPickerResult = result
        pendingDocumentPickerKind = kind
        try {
            val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE)
                type = "*/*"
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            activity.startActivityForResult(intent, documentPickerRequestCode)
        } catch (error: Throwable) {
            pendingDocumentPickerResult = null
            pendingDocumentPickerKind = null
            result.error("PICKER_LAUNCH_FAILED", error.message, null)
        }
    }

    private fun importDocumentUri(kind: String, uri: Uri): ManagedImportedFile {
        val resolver = appContext.contentResolver
        val displayName = resolver.query(
            uri,
            arrayOf(OpenableColumns.DISPLAY_NAME),
            null,
            null,
            null,
        )?.use { cursor ->
            if (cursor.moveToFirst()) {
                val column = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if (column >= 0) cursor.getString(column) else null
            } else null
        }?.takeIf { it.isNotBlank() } ?: (uri.lastPathSegment ?: "rvc_import")

        val lowerName = displayName.lowercase(Locale.ROOT)
        val valid = if (kind == "model") {
            listOf(".onnx", ".pth", ".pt", ".zip").any { lowerName.endsWith(it) }
        } else {
            lowerName.endsWith(".mobile.index") || lowerName.endsWith(".index")
        }
        require(valid) {
            if (kind == "model") "Choose an RVC model file: .onnx, .pth, .pt or .zip."
            else "Choose an RVC index file: .index or .mobile.index."
        }

        val safeName = displayName
            .replace(Regex("[^A-Za-z0-9._() -]"), "_")
            .take(180)
            .ifBlank { "rvc_import" }
        val stagingDir = File(appContext.cacheDir, "rvc_document_import_" + UUID.randomUUID().toString())
        require(stagingDir.mkdirs()) { "Could not create a temporary import folder." }
        val stagedFile = File(stagingDir, safeName)
        try {
            val input = resolver.openInputStream(uri)
                ?: error("Android could not open the selected document.")
            input.use { source ->
                stagedFile.outputStream().buffered().use { output ->
                    source.copyTo(output, 1024 * 1024)
                }
            }
            require(stagedFile.isFile && stagedFile.length() > 0L) {
                "The selected file is empty or could not be copied."
            }
            val fileKind = when (kind) {
                "model" -> ImportedFileKind.MODEL
                "index" -> ImportedFileKind.INDEX
                else -> error("Unsupported import type.")
            }
            return TempWorkspaceManager(appContext.filesDir, appContext.cacheDir)
                .importPickedFile(fileKind, stagedFile.absolutePath)
        } finally {
            stagingDir.deleteRecursively()
        }
    }
'''
needle = "    private fun importPickedFile(call: MethodCall, result: Result) {"
if kt.count(needle) != 1:
    raise RuntimeError("Native import function insertion point missing")
kt = kt.replace(needle, activity_methods + "\n" + needle, 1)
cleanup = "        scope.cancel()\n"
if cleanup not in kt:
    raise RuntimeError("Plugin cleanup insertion point missing")
kt = kt.replace(cleanup, "        pendingDocumentPickerResult?.error(\"PICKER_UNAVAILABLE\", \"App closed before import completed.\", null)\n        pendingDocumentPickerResult = null\n        pendingDocumentPickerKind = null\n        scope.cancel()\n", 1)
plugin.write_text(kt, encoding="utf-8")

bridge = root / "lib/services/rvc_bridge.dart"
bt = bridge.read_text(encoding="utf-8")
bridge_needle = """  Future<ImportedFileHandle> importPickedFile({
    required String kind,
    required String sourcePath,
  }) async {"""
bridge_method = """  /// Native Android document picker; null means the user cancelled.
  Future<ImportedFileHandle?> pickAndImportFile({required String kind}) async {
    final result = await _channel.invokeMethod<Map<dynamic, dynamic>>(
      'pickAndImportFile',
      {'kind': kind},
    );
    if (result == null) return null;
    return ImportedFileHandle.fromMap(Map<String, dynamic>.from(result));
  }

"""
if bridge_needle not in bt:
    raise RuntimeError("RVCBridge import method insertion point missing")
bt = bt.replace(bridge_needle, bridge_method + bridge_needle, 1)
bridge.write_text(bt, encoding="utf-8")

picker = root / "lib/screens/model_picker_screen.dart"
pt = picker.read_text(encoding="utf-8").replace("import 'package:file_picker/file_picker.dart';\n", "")
old_model = """      final result = await FilePicker.platform.pickFiles(
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

      final imported = await _bridge.importPickedFile(kind: 'model', sourcePath: source);"""
new_model = """      final imported = await _bridge.pickAndImportFile(kind: 'model');
      if (imported == null) return;
      final ext = _ext(imported.path);"""
old_index = """      final result = await FilePicker.platform.pickFiles(
        type: FileType.any,
        allowMultiple: false,
        withData: false,
      );
      final source = result?.files.single.path;
      if (source == null || source.isEmpty) return;
      final ext = _ext(source);
      if (!_index(source)) throw Exception('Select an RVC .index or .mobile.index file');

      final imported = await _bridge.importPickedFile(kind: 'index', sourcePath: source);"""
new_index = """      final imported = await _bridge.pickAndImportFile(kind: 'index');
      if (imported == null) return;
      final ext = _ext(imported.path);"""
old_select = """      if (ext == 'mobile.index') {
        _selectedIndexPath = imported.path;
        _selectedIndexDisplayName = File(imported.path).uri.pathSegments.last;
        widget.onIndexSelected(imported.path);
      }
      if (mounted) setState(() {});"""
new_select = old_select
for old, new in [(old_model,new_model),(old_index,new_index),(old_select,new_select)]:
    if old not in pt:
        raise RuntimeError("Model/index picker source changed; cannot apply SAF patch")
    pt = pt.replace(old,new,1)
pt = pt.replace(
    "Standard .index imported. Use Index Tools to convert it for mobile use.",
    "Standard .index stored. It is not runtime-ready; an on-phone FAISS converter is not included yet.",
    1
)
picker.write_text(pt, encoding="utf-8")


# ---------------------------------------------------------------------------
# Safe on-device RVC ZIP extraction. Supported model/index entries are streamed
# to a temporary location and imported using the persistent model manager.
# Partial installs are rolled back on any error.
# ---------------------------------------------------------------------------
kt = plugin.read_text(encoding="utf-8")
zip_import = "import java.util.UUID\n"
if "import java.util.zip.ZipInputStream" not in kt:
    if zip_import not in kt: raise RuntimeError("ZIP import position missing")
    kt = kt.replace(zip_import, zip_import + "import java.util.zip.ZipInputStream\n", 1)
handler_line = '            "pickAndImportFile" -> pickAndImportFile(call, result)\n'
if '"extractModelArchive" -> extractModelArchive(call, result)' not in kt:
    if handler_line not in kt: raise RuntimeError("ZIP method handler position missing")
    kt = kt.replace(handler_line, handler_line + '            "extractModelArchive" -> extractModelArchive(call, result)\n', 1)

zip_method = r'''
    private fun extractModelArchive(call: MethodCall, result: Result) {
        val archivePath = call.argument<String>("path")
        if (archivePath.isNullOrBlank()) {
            result.error("INVALID_ARGUMENTS", "Missing archive path.", null)
            return
        }
        val archive = File(archivePath)
        if (!archive.isFile || !archive.name.lowercase(Locale.ROOT).endsWith(".zip")) {
            result.error("INVALID_ARCHIVE", "Choose an installed ZIP model archive.", null)
            return
        }
        scope.launch {
            val manager = TempWorkspaceManager(appContext.filesDir, appContext.cacheDir)
            val staging = File(appContext.cacheDir, "rvc_zip_extract_" + UUID.randomUUID().toString())
            val imported = mutableListOf<ManagedImportedFile>()
            try {
                require(staging.mkdirs()) { "Could not create a temporary extraction folder." }
                var totalBytes = 0L
                var supportedEntries = 0
                ZipInputStream(FileInputStream(archive).buffered()).use { zip ->
                    var entry = zip.nextEntry
                    while (entry != null) {
                        if (!entry.isDirectory) {
                            val baseName = File(entry.name.replace('\\', '/')).name
                            val lower = baseName.lowercase(Locale.ROOT)
                            val fileKind = when {
                                lower.endsWith(".mobile.index") || lower.endsWith(".index") -> ImportedFileKind.INDEX
                                lower.endsWith(".onnx") || lower.endsWith(".pth") || lower.endsWith(".pt") -> ImportedFileKind.MODEL
                                else -> null
                            }
                            if (fileKind != null) {
                                supportedEntries += 1
                                require(supportedEntries <= 128) { "ZIP contains too many model/index files." }
                                val safeName = baseName
                                    .replace(Regex("[^A-Za-z0-9._() -]"), "_")
                                    .take(180)
                                    .ifBlank { "rvc_model_" + supportedEntries }
                                val entryDir = File(staging, "entry_" + supportedEntries)
                                require(entryDir.mkdirs()) { "Could not prepare a ZIP entry." }
                                val destination = File(entryDir, safeName)
                                var entryBytes = 0L
                                FileOutputStream(destination).buffered().use { output ->
                                    val buffer = ByteArray(64 * 1024)
                                    while (true) {
                                        val count = zip.read(buffer)
                                        if (count < 0) break
                                        if (count == 0) continue
                                        entryBytes += count.toLong()
                                        totalBytes += count.toLong()
                                        require(entryBytes <= 1_500_000_000L && totalBytes <= 2_000_000_000L) {
                                            "ZIP expands beyond the safe on-device import limit."
                                        }
                                        output.write(buffer, 0, count)
                                    }
                                }
                                require(entryBytes > 0L && destination.isFile) {
                                    "ZIP entry is empty: " + safeName
                                }
                                imported.add(manager.importPickedFile(fileKind, destination.absolutePath))
                            }
                        }
                        zip.closeEntry()
                        entry = zip.nextEntry
                    }
                }
                require(imported.isNotEmpty()) {
                    "ZIP contains no supported .onnx, .pth, .pt or .index files."
                }
                withContext(Dispatchers.Main) {
                    result.success(imported.map {
                        mapOf(
                            "path" to it.path,
                            "referenceCount" to it.referenceCount,
                            "lastUpdatedAtMs" to it.lastUpdatedAtMs,
                        )
                    })
                }
            } catch (error: Throwable) {
                imported.forEach { handle ->
                    runCatching {
                        val released = manager.releaseReference(handle.path)
                        if (released.referenceCount == 0) manager.deleteIfUnused(handle.path)
                    }
                }
                withContext(Dispatchers.Main) {
                    result.error("ARCHIVE_EXTRACT_FAILED", error.message ?: "Could not extract this model archive.", null)
                }
            } finally {
                staging.deleteRecursively()
            }
        }
    }
'''
zip_needle = "    private fun pickAndImportFile(call: MethodCall, result: Result) {"
if kt.count(zip_needle) != 1: raise RuntimeError("ZIP extractor insertion point missing")
if "private fun extractModelArchive" not in kt:
    kt = kt.replace(zip_needle, zip_method + "\n" + zip_needle, 1)

bt = bridge.read_text(encoding="utf-8")
pick_method_end = """  Future<ImportedFileHandle> importPickedFile({
    required String kind,
    required String sourcePath,
  }) async {"""
archive_bridge = """  /// Extracts model/index files from an installed ZIP inside app-private storage.
  Future<List<ImportedFileHandle>> extractModelArchive(String path) async {
    final result = await _channel.invokeMethod<List<dynamic>>(
      'extractModelArchive',
      {'path': path},
    );
    if (result == null) return <ImportedFileHandle>[];
    return result.map((item) => ImportedFileHandle.fromMap(
      Map<String, dynamic>.from(item as Map),
    )).toList();
  }

"""
if "Future<List<ImportedFileHandle>> extractModelArchive" not in bt:
    if pick_method_end not in bt: raise RuntimeError("ZIP bridge insertion point missing")
    bt = bt.replace(pick_method_end, archive_bridge + pick_method_end, 1)
bridge.write_text(bt, encoding="utf-8")

pt = picker.read_text(encoding="utf-8")
zip_anchor = """      final ext = _ext(imported.path);
      if (_library.contains(imported.path)) {
        await _bridge.releaseImportedFile(imported.path);
      } else {
        _library.insert(0, imported.path);
      }"""
zip_handler = """      final ext = _ext(imported.path);
      if (ext == 'zip') {
        List<ImportedFileHandle> unpacked;
        try {
          unpacked = await _bridge.extractModelArchive(imported.path);
        } finally {
          await _bridge.releaseImportedFile(imported.path);
        }
        String? readyModelPath;
        String? readyIndexPath;
        for (final item in unpacked) {
          final itemExt = _ext(item.path);
          if (['onnx', 'pth', 'pt'].contains(itemExt)) {
            if (_library.contains(item.path)) {
              await _bridge.releaseImportedFile(item.path);
            } else {
              _library.insert(0, item.path);
            }
          } else if (['index', 'mobile.index'].contains(itemExt)) {
            if (_indexLibrary.contains(item.path)) {
              await _bridge.releaseImportedFile(item.path);
            } else {
              _indexLibrary.insert(0, item.path);
            }
          }
          if (itemExt == 'onnx' && readyModelPath == null) readyModelPath = item.path;
          if (itemExt == 'mobile.index' && readyIndexPath == null) {
            try {
              await _bridge.convertIndex(item.path);
              readyIndexPath = item.path;
            } catch (_) {
              // Keep the invalid index in the library so the user can remove it.
            }
          }
        }
        if (readyModelPath != null) {
          _selectedModelPath = readyModelPath;
          _selectedModelDisplayName = readyModelPath.split('/').last;
          widget.onModelSelected(readyModelPath);
        }
        if (readyIndexPath != null) {
          _selectedIndexPath = readyIndexPath;
          _selectedIndexDisplayName = readyIndexPath.split('/').last;
          widget.onIndexSelected(readyIndexPath);
        }
        await _saveLibrary();
        await _saveIndexLibrary();
        if (!mounted) return;
        setState(() {});
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('ZIP unpacked: ' + unpacked.length.toString() + ' model/index file(s) imported. ONNX is ready for conversion; PTH/PT source files are stored for future conversion support.')),
        );
        return;
      }
      if (!_library.contains(imported.path)) _library.insert(0, imported.path);"""
if zip_anchor not in pt:
    raise RuntimeError("ZIP model callback insertion point missing")
if "extractModelArchive(imported.path)" not in pt:
    pt = pt.replace(zip_anchor, zip_handler, 1)
picker.write_text(pt,encoding="utf-8");

if "private fun extractModelArchive" not in kt or "extractModelArchive" not in bt or "extractModelArchive(imported.path)" not in pt:
    raise RuntimeError("ZIP extraction patch did not reach all layers")
plugin.write_text(kt, encoding="utf-8")


# Validate mobile.index using a bounded header read; never load/copy a large index into RAM.
plugin_text = plugin.read_text(encoding="utf-8")
old_mobile_index = "private fun convertMobileIndex(source: File): File {\n        require(source.exists()) { \"索引文件不存在\" }\n        val bytes = source.readBytes()\n        val magic = FEATURE_INDEX_MAGIC.toByteArray(Charsets.US_ASCII)\n        require(bytes.size >= magic.size + Int.SIZE_BYTES) { \"请先在 mobile.index 转换页处理标准 RVC index\" }\n        require(bytes.copyOfRange(0, magic.size).contentEquals(magic)) { \"请先在 mobile.index 转换页处理标准 RVC index\" }\n        val buffer = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)\n        buffer.position(magic.size)\n        val frameCount = buffer.int\n        require(frameCount > 0) { \"mobile.index 数据无效\" }\n        val outputDir = File(appContext.filesDir, \"indexes\")\n        outputDir.mkdirs()\n        val output = File(outputDir, source.name)\n        source.copyTo(output, overwrite = true)\n        return output\n    }"
new_mobile_index = "private fun convertMobileIndex(source: File): File {\n        require(source.isFile) { \"Index file does not exist.\" }\n        val magic = FEATURE_INDEX_MAGIC.toByteArray(Charsets.US_ASCII)\n        val header = ByteArray(magic.size + Int.SIZE_BYTES)\n        FileInputStream(source).use { input ->\n            var offset = 0\n            while (offset < header.size) {\n                val count = input.read(header, offset, header.size - offset)\n                require(count > 0) { \"The mobile index header is incomplete.\" }\n                offset += count\n            }\n        }\n        require(header.copyOfRange(0, magic.size).contentEquals(magic)) {\n            \"This is not a mobile.index file. Standard FAISS indexes need conversion first.\"\n        }\n        val frameCount = ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN).getInt(magic.size)\n        require(frameCount > 0) { \"The mobile index contains no feature vectors.\" }\n        val expectedLength = magic.size.toLong() + Int.SIZE_BYTES + frameCount.toLong() * 768L * Float.SIZE_BYTES\n        require(source.length() == expectedLength) { \"The mobile index is truncated or has an invalid feature-vector length.\" }\n        return source\n    }"
if old_mobile_index not in plugin_text:
    raise RuntimeError("Mobile index validator source changed; review before patching")
plugin_text = plugin_text.replace(old_mobile_index, new_mobile_index, 1)
plugin.write_text(plugin_text, encoding="utf-8")

# ---------------------------------------------------------------------------
# Native Android SAF audio import: one audio file for conversion and a
# multi-select audio picker for the private dataset workspace.
# ---------------------------------------------------------------------------
kt = plugin.read_text(encoding="utf-8")
handler_audio = '            "pickAndImportFile" -> pickAndImportFile(call, result)\n'
if '"pickAndImportAudioFiles" -> pickAndImportAudioFiles(result)' not in kt:
    if handler_audio not in kt: raise RuntimeError("Audio SAF handler insertion point missing")
    kt = kt.replace(handler_audio, handler_audio + '            "pickAndImportAudioFiles" -> pickAndImportAudioFiles(result)\n', 1)

# Route multi-select results through the same streaming importer.
activity_result_anchor = """        if (resultCode != Activity.RESULT_OK) {
            reply.success(null)
            return true
        }
        val uri = data?.data"""
activity_result_replacement = """        if (resultCode != Activity.RESULT_OK) {
            reply.success(null)
            return true
        }
        if (kind == "audio_multiple") {
            importMultipleAudioUris(reply, data)
            return true
        }
        val uri = data?.data"""
if activity_result_anchor not in kt: raise RuntimeError("Audio SAF activity-result insertion point missing")
kt = kt.replace(activity_result_anchor, activity_result_replacement, 1)

audio_picker_methods = r'''
    private fun pickAndImportAudioFiles(result: Result) {
        val activity = activityBinding?.activity
        if (activity == null) {
            result.error("PICKER_UNAVAILABLE", "Android document picker is not attached.", null)
            return
        }
        if (pendingDocumentPickerResult != null) {
            result.error("PICKER_BUSY", "Another document selection is already open.", null)
            return
        }
        pendingDocumentPickerResult = result
        pendingDocumentPickerKind = "audio_multiple"
        try {
            val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE)
                type = "audio/*"
                putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            activity.startActivityForResult(intent, documentPickerRequestCode)
        } catch (error: Throwable) {
            pendingDocumentPickerResult = null
            pendingDocumentPickerKind = null
            result.error("PICKER_LAUNCH_FAILED", error.message, null)
        }
    }

    private fun importMultipleAudioUris(reply: Result, data: Intent?) {
        val uris = mutableListOf<Uri>()
        val clip = data?.clipData
        if (clip != null) {
            for (i in 0 until clip.itemCount) {
                clip.getItemAt(i).uri?.let { uris.add(it) }
            }
        } else {
            data?.data?.let { uris.add(it) }
        }
        if (uris.isEmpty()) {
            reply.success(emptyList<Any>())
            return
        }
        scope.launch {
            val manager = TempWorkspaceManager(appContext.filesDir, appContext.cacheDir)
            val imported = mutableListOf<ManagedImportedFile>()
            try {
                uris.forEach { imported.add(importDocumentUri("audio", it)) }
                withContext(Dispatchers.Main) {
                    reply.success(imported.map {
                        mapOf(
                            "path" to it.path,
                            "referenceCount" to it.referenceCount,
                            "lastUpdatedAtMs" to it.lastUpdatedAtMs,
                        )
                    })
                }
            } catch (error: Throwable) {
                imported.forEach { handle ->
                    runCatching {
                        val released = manager.releaseReference(handle.path)
                        if (released.referenceCount == 0) manager.deleteIfUnused(handle.path)
                    }
                }
                withContext(Dispatchers.Main) {
                    reply.error("AUDIO_IMPORT_FAILED", error.message ?: "Could not import the selected audio.", null)
                }
            }
        }
    }
'''
audio_method_anchor = "    private fun pickAndImportFile(call: MethodCall, result: Result) {"
if "private fun pickAndImportAudioFiles" not in kt:
    if kt.count(audio_method_anchor) != 1: raise RuntimeError("Audio SAF methods insertion point missing")
    kt = kt.replace(audio_method_anchor, audio_picker_methods + "\n" + audio_method_anchor, 1)

# Single-file picker also accepts local audio. Preserve unrestricted model/index
# selection; use audio/* only for the audio path.
kt = kt.replace(
    'if (kind != "model" && kind != "index") {',
    'if (kind != "model" && kind != "index" && kind != "audio") {',
    1
)
kt = kt.replace(
    'type = "*/*"\n                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)',
    'type = if (kind == "audio") "audio/*" else "*/*"\n                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)',
    1
)

# Extend validation and destination routing for audio files.
old_valid = """        val valid = if (kind == "model") {
            listOf(".onnx", ".pth", ".pt", ".zip").any { lowerName.endsWith(it) }
        } else {
            lowerName.endsWith(".mobile.index") || lowerName.endsWith(".index")
        }
        require(valid) {
            if (kind == "model") "Choose an RVC model file: .onnx, .pth, .pt or .zip."
            else "Choose an RVC index file: .index or .mobile.index."
        }"""
new_valid = """        val valid = when (kind) {
            "model" -> listOf(".onnx", ".pth", ".pt", ".zip").any { lowerName.endsWith(it) }
            "index" -> lowerName.endsWith(".mobile.index") || lowerName.endsWith(".index")
            "audio" -> listOf(".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aac", ".aiff").any { lowerName.endsWith(it) }
            else -> false
        }
        require(valid) {
            when (kind) {
                "model" -> "Choose an RVC model file: .onnx, .pth, .pt or .zip."
                "index" -> "Choose an RVC index file: .index or .mobile.index."
                else -> "Choose an audio file: WAV, FLAC, MP3, M4A, OGG, AAC or AIFF."
            }
        }"""
if old_valid not in kt: raise RuntimeError("Audio extension validation block missing")
kt = kt.replace(old_valid, new_valid, 1)
old_kind = """            val fileKind = when (kind) {
                "model" -> ImportedFileKind.MODEL
                "index" -> ImportedFileKind.INDEX
                else -> error("Unsupported import type.")
            }"""
new_kind = """            val fileKind = when (kind) {
                "model" -> ImportedFileKind.MODEL
                "index" -> ImportedFileKind.INDEX
                "audio" -> ImportedFileKind.AUDIO
                else -> error("Unsupported import type.")
            }"""
if old_kind not in kt: raise RuntimeError("Audio destination mapping block missing")
kt = kt.replace(old_kind,new_kind,1)
plugin.write_text(kt,encoding="utf-8")

bt = bridge.read_text(encoding="utf-8")
audio_bridge = """  /// Opens Android's native multi-select audio picker and imports every selection.
  Future<List<ImportedFileHandle>> pickAndImportAudioFiles() async {
    final result = await _channel.invokeMethod<List<dynamic>>('pickAndImportAudioFiles');
    if (result == null) return <ImportedFileHandle>[];
    return result.map((item) => ImportedFileHandle.fromMap(
      Map<String, dynamic>.from(item as Map),
    )).toList();
  }

"""
if "Future<List<ImportedFileHandle>> pickAndImportAudioFiles" not in bt:
    bridge_anchor = "  Future<ImportedFileHandle?> pickAndImportFile({required String kind}) async {"
    if bridge_anchor not in bt: raise RuntimeError("Audio SAF Dart bridge insertion point missing")
    bt = bt.replace(bridge_anchor,audio_bridge+bridge_anchor,1)
bridge.write_text(bt,encoding="utf-8")

# Use the native single-file audio importer for conversion input.
song_screen = root / "lib/screens/song_picker_screen.dart"
song = song_screen.read_text(encoding="utf-8")
song = song.replace("import 'package:file_picker/file_picker.dart';\n","")
old_song = """      final result = await FilePicker.platform.pickFiles(
        type: FileType.audio,
        allowMultiple: false,
      );

      if (result != null && result.files.isNotEmpty) {
        final filePath = result.files.single.path;
        if (filePath != null) {
          await widget.onSongSelected(filePath);
        }
      }"""
new_song = """      final imported = await _rvcBridge.pickAndImportFile(kind: 'audio');
      if (imported != null) {
        await widget.onSongSelected(imported.path);
      }"""
if old_song not in song: raise RuntimeError("Song picker import callback missing")
song = song.replace(old_song,new_song,1)
song_screen.write_text(song,encoding="utf-8")

# Avoid importing an already app-managed audio file a second time.
mt = main.read_text(encoding="utf-8")
old_direct = "final useDirectPath = normalizedPath.contains('/recordings/') || normalizedPath.contains('/TEMP/');"
new_direct = "final useDirectPath = normalizedPath.contains('/recordings/') || normalizedPath.contains('/TEMP/') || normalizedPath.contains('/file_picker/audio/');"
if old_direct in mt: mt = mt.replace(old_direct,new_direct,1)
main.write_text(mt,encoding="utf-8")

# Dataset samples now use Android's native multi-select picker rather than
# temporary plugin-generated paths.
training = root / "lib/screens/training_screen.dart"
tr = training.read_text(encoding="utf-8")
tr = tr.replace("import 'package:file_picker/file_picker.dart';\n","")
tr = tr.replace("  final List<String> _samples = [];", "  final List<String> _samples = [];\n  final Set<String> _importedSamples = {};")
old_add = """      final result = await FilePicker.platform.pickFiles(
        type: FileType.any, allowMultiple: true, withData: false,
      );
      if (result == null) return;
      final paths = result.files.map((f) => f.path).whereType<String>()
        .where((p) => File(p).existsSync())
        .where((p) => ['.wav','.flac','.mp3','.m4a','.ogg','.aac']
          .any((e) => p.toLowerCase().endsWith(e))).toList();"""
new_add = """      final handles = await _bridge.pickAndImportAudioFiles();
      if (handles.isEmpty) return;
      final paths = handles.map((handle) => handle.path)
        .where((p) => File(p).existsSync()).toList();"""
if old_add not in tr: raise RuntimeError("Dataset audio import callback missing")
tr = tr.replace(old_add,new_add,1)
tr = tr.replace(
    "for (final p in paths) { if (!_samples.contains(p)) _samples.add(p); }",
    "for (final p in paths) { if (!_samples.contains(p)) _samples.add(p); _importedSamples.add(p); }",
    1
)
tr = tr.replace(
    """  Future<void> _clear() async {
    if (_datasetPath != null) {""",
    """  Future<void> _clear() async {
    for (final path in _importedSamples.toList()) {
      try { await _bridge.releaseImportedFile(path); } catch (_) {}
    }
    _importedSamples.clear();
    if (_datasetPath != null) {""",
    1
)
training.write_text(tr,encoding="utf-8")

if "pickAndImportAudioFiles" not in kt or "pickAndImportAudioFiles" not in bt or "pickAndImportAudioFiles" not in tr:
    raise RuntimeError("Audio SAF patch did not reach native, bridge and dataset UI.")



# Confirm the generated native and Dart source gets the new SAF code.
for name, check in [
    ("native Android SAF", "pickAndImportFile" in kt and "ACTION_OPEN_DOCUMENT" in kt and "ActivityAware" in kt),
    ("Dart SAF bridge", "pickAndImportFile" in bt),
    ("model screen SAF", "pickAndImportFile(kind: 'model')" in pt and "FilePicker.platform.pickFiles" not in pt),
]:
    if not check:
        raise RuntimeError("Missing required finalization component: " + name)



# ---------------------------------------------------------------------------
# Honest on-phone index tools. The native runtime can validate/install the
# mobile index signature; it cannot parse a standard FAISS .index file.
# ---------------------------------------------------------------------------
index_screen = root / "lib/screens/index_converter_screen.dart"
index_screen.write_text(r'''import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/rvc_bridge.dart';

class IndexConverterScreen extends StatefulWidget {
  const IndexConverterScreen({super.key});

  @override
  State<IndexConverterScreen> createState() => _IndexConverterScreenState();
}

class _IndexConverterScreenState extends State<IndexConverterScreen> {
  final RVCBridge _bridge = RVCBridge();
  bool _busy = false;
  String _status = 'Select a mobile.index file to validate and install.';

  Future<void> _selectAndValidate() async {
    if (_busy) return;
    setState(() { _busy = true; _status = 'Opening Android file picker…'; });
    try {
      final imported = await _bridge.pickAndImportFile(kind: 'index');
      if (imported == null) {
        if (mounted) setState(() => _status = 'No file selected.');
        return;
      }
      final name = imported.path.split('/').last;
      final prefs = await SharedPreferences.getInstance();
      final savedIndexes = prefs.getStringList('red_rvc_index_library') ?? [];
      if (savedIndexes.contains(imported.path)) {
        await _bridge.releaseImportedFile(imported.path);
      } else {
        savedIndexes.insert(0, imported.path);
        await prefs.setStringList('red_rvc_index_library', savedIndexes);
      }
      if (!name.toLowerCase().endsWith('.mobile.index')) {
        if (mounted) {
          setState(() => _status =
            '$name was stored in your Index Library, but it is a standard FAISS index. This offline Android build does not include the FAISS-to-mobile converter, so it cannot be used for inference yet.');
        }
        return;
      }
      final installed = await _bridge.convertIndex(imported.path);
      if (mounted) {
        setState(() => _status =
          'VALIDATION COMPLETE\n\n$name passed the mobile-index format check and was installed at:\n$installed');
      }
    } catch (e) {
      if (mounted) setState(() => _status = 'INDEX CHECK FAILED\n\n$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: const Color(0xFF07070A),
    appBar: AppBar(
      backgroundColor: const Color(0xFF09090D),
      title: const Text("RED'S ULTIMATE RVC — INDEX TOOLS"),
      centerTitle: true,
    ),
    body: ListView(
      padding: const EdgeInsets.all(18),
      children: [
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: const Color(0xFF111117),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: const Color(0xFF62202B)),
          ),
          child: const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.data_object, color: Color(0xFFFF334F), size: 38),
              SizedBox(height: 12),
              Text('MOBILE INDEX CHECKER', style: TextStyle(fontSize: 19, fontWeight: FontWeight.w900)),
              SizedBox(height: 8),
              Text('The on-phone inference engine accepts a mobile.index file with the URVCIDX1 signature. This tool checks and installs that mobile format locally.', style: TextStyle(height: 1.4, color: Color(0xFFD0D0D8))),
            ],
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          height: 52,
          child: ElevatedButton.icon(
            onPressed: _busy ? null : _selectAndValidate,
            icon: const Icon(Icons.folder_open),
            label: Text(_busy ? 'CHECKING…' : 'SELECT & CHECK INDEX'),
          ),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF111117),
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: const Color(0xFF292932)),
          ),
          child: SelectableText(_status, style: const TextStyle(height: 1.45)),
        ),
        const SizedBox(height: 12),
        const Text(
          'IMPORTANT: A standard desktop .index file is not the same format as mobile.index. Standard FAISS-to-mobile conversion is not implemented in this offline build. The app will store the source file but will not falsely mark it as ready for inference.',
          style: TextStyle(color: Color(0xFFFFA3AE), height: 1.4, fontSize: 12.5),
        ),
      ],
    ),
  );
}
''', encoding="utf-8")

# Final static sanity checks.

# Final static sanity checks. Fail the build before producing an APK if the
# custom UI/navigation layer was not actually installed.
# ---------------------------------------------------------------------------
final_main = main.read_text(encoding="utf-8")
final_picker = picker.read_text(encoding="utf-8")
checks = {
    "Red dashboard": "RedHomeScreen(" in final_main,
    "Training screen": (root / "lib" / "screens" / "training_screen.dart").exists() and "TrainingScreen()" in final_main,
    "Dataset recording requests microphone permission": "Permission.microphone.request()" in (root / "lib/screens/training_screen.dart").read_text(encoding="utf-8"),
    "Prepared dataset survives app restart": "red_rvc_last_dataset_path" in (root / "lib/screens/training_screen.dart").read_text(encoding="utf-8"),
    "Prepared dataset can be exported": "Share.shareXFiles" in (root / "lib/screens/training_screen.dart").read_text(encoding="utf-8"),
    "Index library is persistent and removable": "red_rvc_index_library" in final_picker and "_deleteIndex" in final_picker,
    "Index validator avoids full-file RAM copies": "val expectedLength = magic.size.toLong()" in (root / "android/app/src/main/kotlin/com/ultimatervc/mobile/RVCPlugin.kt").read_text(encoding="utf-8"),
    "Full RVC screen": (root / "lib" / "screens" / "full_rvc_screen.dart").exists() and "FullRvcScreen(" in final_main,
    "PTH conversion limitation disclosed": "PTH → ONNX conversion is not included" in final_picker,
    "Dashboard first": "final moduleScreens = [" in final_main and "RedHomeScreen(" in final_main.split("final moduleScreens = [",1)[1].split("GestureDetector(",1)[0],
    "Native Android SAF picker": "pickAndImportFile" in (root / "android/app/src/main/kotlin/com/ultimatervc/mobile/RVCPlugin.kt").read_text(encoding="utf-8") and "ACTION_OPEN_DOCUMENT" in (root / "android/app/src/main/kotlin/com/ultimatervc/mobile/RVCPlugin.kt").read_text(encoding="utf-8"),
    "Dart native SAF bridge": "pickAndImportFile" in (root / "lib/services/rvc_bridge.dart").read_text(encoding="utf-8"),
    "Model picker uses native SAF": "pickAndImportFile(kind: 'model')" in final_picker and "FilePicker.platform.pickFiles" not in final_picker,
    "PTH support": ".pth" in final_picker,
    "Mobile index support": ".mobile.index" in final_picker,
    "Index tools clearly disclose the missing FAISS converter": "FAISS-to-mobile converter" in (root / "lib/screens/index_converter_screen.dart").read_text(encoding="utf-8"),
    "ZIP archive extractor": "private fun extractModelArchive" in (root / "android/app/src/main/kotlin/com/ultimatervc/mobile/RVCPlugin.kt").read_text(encoding="utf-8") and "extractModelArchive" in (root / "lib/services/rvc_bridge.dart").read_text(encoding="utf-8") and "extractModelArchive(imported.path)" in final_picker,
    "Persistent model storage": workspace.exists() and "File(File(appFilesDir, IMPORTS_DIRECTORY_NAME)" in workspace.read_text(encoding="utf-8") and "File(File(appFilesDir, IMPORTS_DIRECTORY_NAME), REGISTRY_FILE_NAME)" in workspace.read_text(encoding="utf-8") if workspace.exists() else False,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise RuntimeError("Finalizer sanity checks failed: " + ", ".join(failed))

# ---------------------------------------------------------------------------
# Release-build hygiene: remove deprecated Flutter API usage and explicitly
# document the Play Core references that are unreachable in this standalone APK.
# This app does not declare Play Feature Delivery modules or deferred components.
# ---------------------------------------------------------------------------
final_main = main.read_text(encoding="utf-8")
old_pop = """      onPopInvoked: (didPop) {
        if (!didPop) _handleBackPressed();
      },"""
new_pop = """      onPopInvokedWithResult: (didPop, result) {
        if (!didPop) _handleBackPressed();
      },"""
if old_pop not in final_main:
    raise RuntimeError("Deprecated PopScope callback not found; review upstream Flutter API")
final_main = final_main.replace(old_pop, new_pop, 1)

write(main, final_main)

# Translate native Android runtime messages and exported folder names too.
native_translations = {
  "生成已中止": "Generation aborted",
  "无法初始化实时输入设备": "Unable to initialize realtime input device",
  "无法初始化实时输出设备": "Unable to initialize realtime output device",
  "实时采集中": "Capturing realtime audio",
  "实时音频采集失败：$read": "Realtime audio capture failed: $read",
  "实时推理中": "Realtime inference running",
  "实时输出队列繁忙": "Realtime output queue is busy",
  "实时输出中": "Realtime output active",
  "实时音频写入失败：$written": "Realtime audio write failed: $written",
  "实时音频写入未接收数据": "Realtime audio write returned no data",
  "当前有别的模式正在占用处理引擎": "Another mode is already using the processing engine",
  "缺少内置 ONNX 模型": "Bundled ONNX model is missing",
  "准备 ONNX Runtime": "Preparing ONNX Runtime",
  "完成": "Complete",
  "不支持的导入类型：$kind": "Unsupported import type: $kind",
  "不支持的 TEMP 模式：$mode": "Unsupported temporary-file mode: $mode",
  "请选择 .onnx 音色模型": "Please select an .onnx voice model",
  "实时推理已启动": "Realtime inference started",
  "正在录音": "Recording is already in progress",
  "没有正在进行的录音": "No recording is in progress",
  "录音文件不存在": "Recording file not found",
  "录音至少需要 1 秒": "Recording must be at least one second long",
  "录音文件为空": "Recording file is empty",
  "音频文件不存在": "Audio file not found",
  "无法初始化录音设备": "Unable to initialize the recording device",
  "源文件不存在": "Source file not found",
  "无法创建媒体文件": "Unable to create the media file",
  "无法写入媒体文件": "Unable to write the media file",
  "已保存在 $displayPath": "Saved to $displayPath",
  "索引文件不存在": "Index file not found",
  "请先在 mobile.index 转换页处理标准 RVC index": "This standard RVC index is not supported. Import a compatible mobile.index file.",
  "mobile.index 数据无效": "Invalid mobile.index data",
  "实时推理会话已关闭": "Realtime inference session is closed",
  "无法初始化分贝仪输入设备": "Unable to initialize the decibel meter input",
  "无法初始化音高检测输入设备": "Unable to initialize the pitch detector input",
  "未找到 CPU 频率策略": "CPU frequency policy was not found",
  "部分 CPU 频率策略应用失败": "Some CPU frequency policies could not be applied",
  "ROOT 性能方案已启用": "Root performance profile enabled",
  "未获得 root 授权": "Root access was not granted",
  "终止生成后推理进程仍未退出": "The inference process did not exit after cancellation",
  "推理进程已断开": "Inference process disconnected",
  "无法连接推理进程": "Unable to connect to the inference process",
  "推理进程连接超时": "Inference process connection timed out",
  "推理进程不可用": "Inference process is unavailable",
  "推理进程已中断": "Inference process interrupted",
  "推理进程长时间无进度": "The inference process stopped reporting progress",
  "推理进程未返回输出路径": "The inference process returned no output path",
  "无法连接实时推理进程": "Unable to connect to the realtime inference process",
  "实时推理进程连接超时": "Realtime inference process connection timed out",
  "实时推理进程不可用": "Realtime inference process is unavailable",
  "实时推理进程响应超时": "Realtime inference process response timed out",
  "模型文件不存在": "Model file not found",
  "请选择 .index 索引文件": "Please select an .index file",
  "缺少 ONNX 模型：$missingModels": "Missing ONNX model assets: $missingModels",
  "准备 CPU 推理": "Preparing CPU inference",
  "提取音色特征": "Extracting voice features",
  "估计音高": "Estimating pitch",
  "准备分块生成": "Preparing chunked conversion",
  "写入音频": "Writing audio",
  "音频分段结果为空": "Audio segmentation returned no segments",
  "准备分段处理": "Preparing segmented processing",
  "恢复分段任务": "Resuming segmented task",
  "准备分段任务": "Preparing segmented task",
  "恢复最终合并": "Restoring final audio merge",
  "第${segmentIndex + 1}/${segments.size}段：$step": "Segment ${segmentIndex + 1}/${segments.size}: $step",
  "保存进度点 ${segmentIndex + 1}": "Saving checkpoint ${segmentIndex + 1}",
  "生成完成": "Conversion complete",
  "解码音频": "Decoding audio",
  "整段后处理": "Final audio processing",
  "未找到可解码的音频轨道": "No decodable audio track was found",
  "音频格式缺少 MIME": "Audio format is missing its MIME type",
  "无法获取解码输入缓冲": "Could not access the decoder input buffer",
  "无法获取解码输出缓冲": "Could not access the decoder output buffer",
  "音频解码结果为空": "Audio decoding returned no data",
  "复用输入分片 ${segmentIndex + 1}/${segments.size}": "Reusing input segment ${segmentIndex + 1}/${segments.size}",
  "预切分输入音频 ${segmentIndex + 1}/${segments.size}": "Pre-splitting input audio ${segmentIndex + 1}/${segments.size}",
  "重建最终拼接 ${index + 1}/${segments.size}": "Rebuilding final output ${index + 1}/${segments.size}",
  "缺少分段结果：${file.name}": "Missing segment output: ${file.name}",
  "音频通道数无效": "Invalid audio channel count",
  "不支持的 PCM 编码：$pcmEncoding": "Unsupported PCM encoding: $pcmEncoding",
  "HuBERT 特征为空": "HuBERT features are empty",
  "索引格式暂不支持，请先导入 mobile.index": "This index format is not supported. Import a compatible mobile.index file.",
  "索引文件为空或格式不受支持": "Index file is empty or uses an unsupported format",
  "当前仅支持移动端转换后的 .index 特征表": "Only mobile-compatible .index feature tables are supported",
  "索引特征数量无效": "Invalid index feature count",
  "索引文件数据不完整": "Index file data is incomplete",
  "当前音色模型 ONNX 输入不符合 RVC v2 导出格式：${inputNames.joinToString()}": "The selected ONNX voice model does not match the RVC v2 export format. Inputs: ${inputNames.joinToString()}",
  "分块生成中": "Converting audio chunks",
  "导入文件不存在：$sourcePath": "Imported file not found: $sourcePath",
  "处理出错了，可点击重试": "Processing failed. Tap to retry.",
  "已关闭悬浮窗": "Floating control closed",
  "结束播放": "Playback ended",
  "正在保存处理后的音频": "Saving converted audio",
  "Download/RVC_Convert/变声器模式/processed.rvc.wav": "Download/RVC_Convert/Voice_Changer/processed.rvc.wav",
  "暂无处理后的音频": "No converted audio is available",
  "保存成功：$savedPath": "Saved successfully: $savedPath",
  "保存失败：$targetPath，${error.message}": "Could not save $targetPath: ${error.message}",
  "正在保存原始录音": "Saving original recording",
  "Download/RVC_Convert/变声器模式/recording.wav": "Download/RVC_Convert/Voice_Changer/recording.wav",
  "暂无原始录音": "No original recording is available",
  "已保存原始录音：$savedPath": "Original recording saved: $savedPath",
  "原始录音保存失败：$targetPath，${error.message}": "Could not save original recording to $targetPath: ${error.message}",
  "开始录制": "Recording started",
  "RVC处理中": "RVC processing",
  "已取消录制": "Recording cancelled",
  "正在取消处理": "Cancelling processing",
  "已取消处理": "Processing cancelled",
  "正在暂停处理，可稍后继续": "Pausing processing; you can resume later",
  "处理已停止，可点击继续处理": "Processing paused; tap to resume",
  "正在继续处理": "Resuming processing",
  "继续处理失败，请重试": "Could not resume processing. Please try again.",
  "继续处理": "Resume processing",
  "正在清空本轮处理": "Clearing this session",
  "已放弃处理": "Processing discarded",
  "准备播放": "Preparing playback",
  "准备试听": "Preparing preview",
  "已取消试听": "Preview cancelled",
  "已取消播放": "Playback cancelled",
  "暂停播放": "Pause playback",
  "继续播放": "Resume playback",
  "暂停试听": "Pause preview",
  "继续试听": "Resume preview",
  "结束试听": "End preview",
  "继续": "Resume",
  "重试": "Retry",
  "变声器模式": "Voice Changer",
  "需要开启悬浮窗权限": "Overlay permission is required",
  "处理出错": "Processing error",
  "Download/RVC_Convert/变声器模式/$displayName": "Download/RVC_Convert/Voice_Changer/$displayName",
  "/RVC_Convert/变声器模式": "/RVC_Convert/Voice_Changer",
  "原始录音不存在": "Original recording not found",
  "处理后的音频不存在": "Converted audio file not found",
  "音频写入失败：$written": "Audio write failed: $written"
}
for kotlin in (root / "android/app/src/main/kotlin").rglob("*.kt"):
    kt_text = kotlin.read_text(encoding="utf-8")
    for a, b in sorted(native_translations.items(), key=lambda item: len(item[0]), reverse=True):
        kt_text = kt_text.replace(a, b)
    kotlin.write_text(kt_text, encoding="utf-8")

# Final guard: never ship CJK text in visible Dart or native Android source.
for source_file in list((root / "lib").rglob("*.dart")) + list((root / "android/app/src/main/kotlin").rglob("*.kt")):
    source = source_file.read_text(encoding="utf-8")
    visible = re.sub(r"(?s)/\*.*?\*/", "", source)
    visible = re.sub(r"(?m)//.*$", "", visible)
    if any(0x3400 <= ord(ch) <= 0x9FFF for ch in visible):
        raise RuntimeError(f"Untranslated CJK text remains in {source_file}")

measurement_chart = root / "lib" / "widgets" / "measurement_chart_card.dart"
if measurement_chart.exists():
    chart_text = measurement_chart.read_text(encoding="utf-8")
    if "colorScheme.surfaceVariant" in chart_text:
        chart_text = chart_text.replace("colorScheme.surfaceVariant", "colorScheme.surfaceContainerHighest")
        measurement_chart.write_text(chart_text, encoding="utf-8")

proguard = root / "android" / "app" / "proguard-rules.pro"
if not proguard.exists():
    raise RuntimeError("Android ProGuard rules file missing")
proguard_text = proguard.read_text(encoding="utf-8")
playcore_rule = """
# Flutter includes optional Play Feature Delivery hooks. This standalone APK
# declares no deferred components and does not use Play Core split installation.
-dontwarn com.google.android.play.core.**
"""
if "-dontwarn com.google.android.play.core.**" not in proguard_text:
    proguard.write_text(proguard_text.rstrip() + "\n" + playcore_rule, encoding="utf-8")

if "onPopInvoked:" in main.read_text(encoding="utf-8"):
    raise RuntimeError("Deprecated PopScope callback remains in final source")
if measurement_chart.exists() and "colorScheme.surfaceVariant" in measurement_chart.read_text(encoding="utf-8"):
    raise RuntimeError("Deprecated surfaceVariant remains in final source")

# Keep main.dart in the expected package after the upstream checkout.
write(main, final_main)
