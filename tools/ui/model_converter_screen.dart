import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';

import '../services/rvc_bridge.dart';

/// Runs the native CPU RVC-GGML engine with already-exported GGUF assets.
/// This is an inference runner, not a .pth/.pt checkpoint exporter.
class ModelConverterScreen extends StatefulWidget {
  const ModelConverterScreen({super.key});

  @override
  State<ModelConverterScreen> createState() => _ModelConverterScreenState();
}

class _ModelConverterScreenState extends State<ModelConverterScreen> {
  static const _red = Color(0xFFFF334F);
  static const _bg = Color(0xFF07070A);
  static const _panel = Color(0xFF121218);

  final RVCBridge _bridge = RVCBridge();
  String? _hubertPath;
  String? _rmvpePath;
  String? _voicePath;
  String? _indexPath;
  String? _audioPath;
  String? _outputPath;
  String? _savedPath;
  String? _error;
  bool _busy = false;

  Future<String?> _pickFile({
    required String title,
    required bool gguf,
  }) async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.any,
      allowMultiple: false,
      withData: false,
    );
    if (result == null || result.files.isEmpty) return null;
    final path = result.files.single.path;
    if (path == null || path.isEmpty) {
      throw StateError('Android did not provide an accessible file path. Copy the file into local storage and try again.');
    }
    final lower = path.toLowerCase();
    final valid = gguf
        ? lower.endsWith('.gguf')
        : lower.endsWith('.wav');
    if (!valid) {
      throw StateError(gguf
          ? 'Choose a .gguf model file for $title.'
          : 'The native engine currently accepts WAV audio. Choose a .wav file.');
    }
    final file = File(path);
    if (!await file.exists() || await file.length() == 0) {
      throw StateError('The selected file is missing or empty.');
    }
    return path;
  }

  Future<void> _choose(String slot) async {
    try {
      final path = await _pickFile(
        title: slot,
        gguf: slot != 'Input audio',
      );
      if (path == null || !mounted) return;
      setState(() {
        switch (slot) {
          case 'HuBERT':
            _hubertPath = path;
            break;
          case 'RMVPE':
            _rmvpePath = path;
            break;
          case 'Voice model':
            _voicePath = path;
            break;
          case 'Retrieval index (optional)':
            _indexPath = path;
            break;
          case 'Input audio':
            _audioPath = path;
            _outputPath = null;
            _savedPath = null;
            break;
        }
        _error = null;
      });
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    }
  }

  Future<void> _convert() async {
    if (_hubertPath == null || _rmvpePath == null ||
        _voicePath == null || _audioPath == null) {
      setState(() => _error = 'Choose HuBERT, RMVPE, a voice GGUF and an input WAV first.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
      _outputPath = null;
      _savedPath = null;
    });
    try {
      final root = await getApplicationDocumentsDirectory();
      final outputDir = Directory('${root.path}/RVC Outputs');
      await outputDir.create(recursive: true);
      final output = File('${outputDir.path}/Red-RVC-${DateTime.now().millisecondsSinceEpoch}.wav');
      final result = await _bridge.convertGguf(
        hubertPath: _hubertPath!,
        rmvpePath: _rmvpePath!,
        voicePath: _voicePath!,
        indexPath: _indexPath,
        inputPath: _audioPath!,
        outputPath: output.path,
        pitch: 0,
        indexRate: _indexPath == null ? 0.0 : 0.75,
        protect: 0.33,
        rmsMixRate: 0.25,
      );
      if (!await File(result).exists() || await File(result).length() <= 44) {
        throw StateError('The native engine did not create a valid WAV output.');
      }
      if (mounted) setState(() => _outputPath = result);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _saveOutput() async {
    final path = _outputPath;
    if (path == null) return;
    try {
      final saved = await _bridge.saveGeneratedAudio(path);
      if (mounted) setState(() => _savedPath = saved);
    } catch (e) {
      if (mounted) setState(() => _error = 'Could not save the converted audio: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      appBar: AppBar(
        title: const Text("RED'S NATIVE RVC ENGINE"),
        centerTitle: true,
        backgroundColor: const Color(0xFF09090D),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(17),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF31000A), Color(0xFF151018), _bg],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(22),
              border: Border.all(color: _red.withOpacity(.5)),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.memory_rounded, color: _red, size: 38),
                SizedBox(height: 10),
                Text('ON-DEVICE GGUF INFERENCE',
                    style: TextStyle(fontSize: 19, fontWeight: FontWeight.w900)),
                SizedBox(height: 7),
                Text(
                  'Run an already-exported RVC GGUF model locally with the native C++ engine. No ONNX voice model, cloud inference, Colab or Kaggle is needed for this route. Raw .pth/.pt checkpoints still need a separate exporter.',
                  style: TextStyle(color: Color(0xFFD0D0D8), height: 1.4),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          _fileCard('HuBERT feature model', 'Required • hubert.gguf', _hubertPath,
              () => _choose('HuBERT'), Icons.graphic_eq),
          _fileCard('RMVPE pitch model', 'Required • rmvpe.gguf', _rmvpePath,
              () => _choose('RMVPE'), Icons.multiline_chart),
          _fileCard('Your voice model', 'Required • exported voice .gguf', _voicePath,
              () => _choose('Voice model'), Icons.record_voice_over),
          _fileCard('Retrieval index', 'Optional • exported index .gguf', _indexPath,
              () => _choose('Retrieval index (optional)'), Icons.storage,
              onClear: _indexPath == null ? null : () => setState(() => _indexPath = null)),
          _fileCard('Input audio', 'Required • WAV file', _audioPath,
              () => _choose('Input audio'), Icons.audio_file),
          const SizedBox(height: 10),
          if (_error != null)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF351018),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: _red.withOpacity(.6)),
              ),
              child: Text(_error!, style: const TextStyle(color: Color(0xFFFFB8C1))),
            ),
          const SizedBox(height: 12),
          SizedBox(
            height: 52,
            child: ElevatedButton.icon(
              onPressed: _busy ? null : _convert,
              icon: _busy
                  ? const SizedBox(width: 18, height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.auto_awesome),
              label: Text(_busy ? 'CONVERTING ON THIS PHONE…' : 'RUN VOICE CONVERSION'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _red,
                foregroundColor: Colors.white,
                disabledBackgroundColor: const Color(0xFF6B2631),
              ),
            ),
          ),
          if (_outputPath != null) ...[
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: _panel,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF315C3D)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(children: [
                    Icon(Icons.check_circle, color: Color(0xFF70D890)),
                    SizedBox(width: 8),
                    Text('CONVERSION FINISHED', style: TextStyle(fontWeight: FontWeight.w900)),
                  ]),
                  const SizedBox(height: 7),
                  SelectableText(_outputPath!, style: const TextStyle(color: Color(0xFFBDBDC7), fontSize: 12)),
                  const SizedBox(height: 10),
                  OutlinedButton.icon(
                    onPressed: _saveOutput,
                    icon: const Icon(Icons.save_alt),
                    label: const Text('SAVE TO MUSIC / AUDIO'),
                  ),
                  if (_savedPath != null)
                    SelectableText('Saved: $_savedPath',
                        style: const TextStyle(color: Color(0xFF70D890), fontSize: 11)),
                ],
              ),
            ),
          ],
          const SizedBox(height: 18),
          _notice(
            'ABOUT .PTH AND .INDEX FILES',
            'A raw .pth checkpoint is not executable by this native engine. It must first be exported to GGUF using the RVC-GGML exporter. A standard FAISS .index must also be exported to .index.gguf. The index is optional for conversion.',
          ),
          _notice(
            'GALAXY A12 PERFORMANCE',
            'This native engine is CPU-only in this build. Large models and long recordings may be slow or exceed available memory. Start with a short WAV sample. The app will report a real conversion error rather than create a fake output.',
          ),
        ],
      ),
    );
  }

  Widget _fileCard(String title, String hint, String? path,
      VoidCallback onPick, IconData icon, {VoidCallback? onClear}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 9),
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: _panel,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF292932)),
      ),
      child: Row(
        children: [
          Icon(icon, color: _red, size: 25),
          const SizedBox(width: 11),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
              const SizedBox(height: 3),
              Text(path == null ? hint : path.split('/').last,
                  maxLines: 2, overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: Color(0xFFAAAAB5), fontSize: 11)),
            ]),
          ),
          IconButton(onPressed: onPick, icon: const Icon(Icons.folder_open), tooltip: 'Choose file'),
          if (onClear != null)
            IconButton(onPressed: onClear, icon: const Icon(Icons.close), tooltip: 'Clear optional index'),
        ],
      ),
    );
  }

  Widget _notice(String title, String body) => Container(
    margin: const EdgeInsets.only(top: 10),
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: const Color(0xFF101016),
      borderRadius: BorderRadius.circular(15),
      border: Border.all(color: const Color(0xFF30303A)),
    ),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(title, style: const TextStyle(color: _red, fontWeight: FontWeight.w900)),
      const SizedBox(height: 6),
      Text(body, style: const TextStyle(color: Color(0xFFBDBDC7), height: 1.4, fontSize: 12)),
    ]),
  );
}
