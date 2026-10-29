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

for name in ("red_home_screen.dart", "training_screen.dart"):
    src = repo_root / "tools" / "ui" / name
    dst = root / "lib" / "screens" / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

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
pt = pt.replace("name: ultimate_rvc_mobile", "name: reds_ultimate_rvc")
if "  url_launcher:" not in pt:
    pt = pt.replace("dependencies:\n", "dependencies:\n  url_launcher: 6.2.6\n", 1)
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
                    'Your complete local voice studio for Android.',
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
              _Action(Icons.model_training, 'TRAIN / CREATE VOICE', 'Build and manage a local training workspace', onTrain),
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
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _loadLibrary();
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
      // FileType.any is intentional. Samsung's Android 12 picker can grey out
      // RVC files when a restrictive MIME/extension filter is used.
      final result = await FilePicker.platform.pickFiles(type: FileType.any, allowMultiple: false, withData: false);
      final source = result?.files.single.path;
      if (source == null || source.isEmpty) return;
      final ext = _ext(source);
      if (!['onnx', 'pth', 'pt', 'zip'].contains(ext)) {
        throw Exception('Select an RVC model: .onnx, .pth, .pt or .zip');
      }

      final imported = await _bridge.importPickedFile(kind: 'model', sourcePath: source);
      if (!_library.contains(imported.path)) _library.insert(0, imported.path);
      await _saveLibrary();

      if (!mounted) return;
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
      final result = await FilePicker.platform.pickFiles(type: FileType.any, allowMultiple: false, withData: false);
      final source = result?.files.single.path;
      if (source == null || source.isEmpty) return;
      final ext = _ext(source);
      if (!_index(source)) throw Exception('Select an RVC .index or .mobile.index file');

      final imported = await _bridge.importPickedFile(kind: 'index', sourcePath: source);
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
    widget.onModelSelected(path);
    if (mounted) setState(() {});
  }

  Future<void> _delete(String path) async {
    try {
      await _bridge.releaseImportedFile(path);
    } catch (_) {}
    _library.remove(path);
    await _saveLibrary();
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final selected = widget.selectedModelPath;
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
                selected == null ? 'No runtime voice selected' : (widget.selectedModelDisplayName ?? File(selected).uri.pathSegments.last),
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900),
              ),
              const SizedBox(height: 7),
              Text(ready ? 'READY — ONNX model can be used for conversion.' : 'Choose an ONNX model for conversion. Source RVC models can also be stored below.', style: const TextStyle(color: Color(0xFFAAAA B5))),
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
              Text(widget.selectedIndexDisplayName ?? (widget.selectedIndexPath == null ? 'No index selected' : File(widget.selectedIndexPath!).uri.pathSegments.last),
                style: const TextStyle(fontWeight: FontWeight.w800)),
              const SizedBox(height: 8),
              const Text('mobile.index is directly usable. Standard .index files can be converted with Index Tools.', style: TextStyle(color: Color(0xFF9E9EA8), height: 1.3)),
              const SizedBox(height: 12),
              OutlinedButton.icon(onPressed: _busy ? null : _pickIndex, icon: const Icon(Icons.upload_file), label: const Text('IMPORT INDEX')),
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
                    "import 'screens/pitch_detection_screen.dart';\nimport 'screens/red_home_screen.dart';\nimport 'screens/training_screen.dart';")

# Theme/branding text.
mt = mt.replace("Ultimate RVC Mobile", "Red's Ultimate RVC")
mt = mt.replace("primarySwatch: Colors.blue,", "primarySwatch: Colors.red,")
mt = mt.replace("backgroundColor: Colors.white", "backgroundColor: const Color(0xFF07070A)")
mt = mt.replace("title: Text('Ultimate RVC'", "title: const Text(\"RED'S ULTIMATE RVC\"")
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
    old_line = f"void {name}() {{\\n    setState(() => _moduleIndex = {old_index});"
    new_line = f"void {name}() {{\\n    setState(() => _moduleIndex = {new_index});"
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
drawer = r'''  Drawer _buildDrawer() {
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
          ListTile(leading: const Icon(Icons.model_training), title: const Text('Train / Create Voice'), onTap: () {
            Navigator.pop(context);
            Navigator.of(context).push(MaterialPageRoute(builder: (_) => const TrainingScreen()));
          }),
        ],
      ),
    );
  }

'''
mt = mt[:dstart] + drawer + mt[dend:]

# Fix old package imports in tests.
testdir = root / "test"
if testdir.exists():
    for dart in testdir.rglob("*.dart"):
        write(dart, dart.read_text(encoding="utf-8").replace("package:ultimate_rvc_mobile/", "package:reds_ultimate_rvc/"))

# Ensure all source strings are English enough for the user-facing screens.
for dart in (root / "lib").rglob("*.dart"):
    t = dart.read_text(encoding="utf-8")
    replacements = {
        "选择模型":"Select model", "更换模型":"Change model", "清除模型":"Clear model",
        "未选择":"Not selected", "选择音色":"Select voice", "选择索引":"Select index",
        "音频推理":"Audio Conversion", "实时推理":"Realtime RVC", "变声器模式":"Voice Changer",
        "分贝仪":"dB Meter", "音高检测":"Pitch Detection", "参数解释":"RVC Controls",
        "选择歌曲":"Select audio", "生成":"Generate", "结果":"Result",
    }
    for a,b in replacements.items():
        t = t.replace(a,b)
    write(dart,t)

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

# ---------------------------------------------------------------------------
# Android branding / app icon.
# ---------------------------------------------------------------------------
manifest = root / "android/app/src/main/AndroidManifest.xml"
if manifest.exists():
    m = manifest.read_text(encoding="utf-8")
    m = re.sub(r'android:label="[^"]+"', 'android:label="Red\'s Ultimate RVC"', m, count=1)
    if 'android:icon="@drawable/reds_ultimate_rvc_logo"' not in m:
        m = m.replace('<application', '<application android:icon="@drawable/reds_ultimate_rvc_logo"', 1)
    write(manifest,m)

# Render SVG icon into a drawable for Android.
try:
    import cairosvg
    out = root / "android/app/src/main/res/drawable/reds_ultimate_rvc_logo.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(url=str(logo), write_to=str(out), output_width=512, output_height=512)
except Exception as exc:
    raise RuntimeError(f"Could not render approved logo: {exc}")

# ---------------------------------------------------------------------------
# Final static sanity checks. Fail the build before producing an APK if the
# custom UI/navigation layer was not actually installed.
# ---------------------------------------------------------------------------
final_main = main.read_text(encoding="utf-8")
final_picker = picker.read_text(encoding="utf-8")
checks = {
    "Red dashboard": "RedHomeScreen(" in final_main,
    "Training screen": "TrainingScreen()" in final_main,
    "Dashboard first": "final moduleScreens = [" in final_main and "RedHomeScreen(" in final_main.split("final moduleScreens = [",1)[1].split("GestureDetector(",1)[0],
    "Samsung-safe model picker": "type: FileType.any" in final_picker,
    "PTH support": ".pth" in final_picker,
    "Mobile index support": ".mobile.index" in final_picker,
    "Persistent model storage": workspace.exists() and "MODEL, ImportedFileKind.INDEX" in workspace.read_text(encoding="utf-8") if workspace.exists() else False,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise RuntimeError("Finalizer sanity checks failed: " + ", ".join(failed))

# Keep main.dart in the expected package after the upstream checkout.
write(main, final_main)
