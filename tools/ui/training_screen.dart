import 'dart:convert';
import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';

class TrainingScreen extends StatefulWidget {
  const TrainingScreen({super.key});
  @override State<TrainingScreen> createState() => _TrainingScreenState();
}
class _TrainingScreenState extends State<TrainingScreen> {
  final List<String> _files = [];
  String? _manifestPath;
  bool _busy = false;

  Future<void> _pick() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['wav', 'mp3', 'flac', 'm4a', 'ogg'],
      allowMultiple: true, withData: false,
    );
    if (result == null) return;
    setState(() { _files..clear()..addAll(result.files.map((f) => f.path).whereType<String>()); });
  }

  Future<void> _prepare() async {
    if (_files.isEmpty || _busy) return;
    setState(() => _busy = true);
    try {
      final dir = await getApplicationDocumentsDirectory();
      final out = Directory(dir.path + '/rvc_training');
      await out.create(recursive: true);
      final file = File(out.path + '/dataset_manifest.json');
      await file.writeAsString(const JsonEncoder.withIndent('  ').convert({'format': 'rvc_training_dataset', 'createdBy': "Red's Ultimate RVC"}) + '\n' + jsonEncode(_files));
      if (mounted) setState(() => _manifestPath = file.path);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('TRAIN / MODEL LAB'), centerTitle: true),
    body: ListView(padding: const EdgeInsets.all(16), children: [
      Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
        Text('TRAIN A VOICE', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
        SizedBox(height: 8),
        Text('Import your training recordings and prepare the dataset. Full RVC neural-network training requires a GPU training environment and is not practical on the Galaxy A12 itself.'),
      ]))),
      const SizedBox(height: 12),
      ElevatedButton.icon(onPressed: _busy ? null : _pick, icon: const Icon(Icons.library_add), label: const Text('ADD TRAINING AUDIO')),
      const SizedBox(height: 10),
      Text(_files.length.toString() + ' audio files selected'),
      const SizedBox(height: 10),
      if (_files.isNotEmpty) Card(child: Padding(padding: const EdgeInsets.all(8), child: Column(children: _files.take(30).map((p) => ListTile(dense: true, leading: const Icon(Icons.audio_file), title: Text(p.split('/').last, maxLines: 1, overflow: TextOverflow.ellipsis))).toList()))),
      const SizedBox(height: 12),
      ElevatedButton.icon(onPressed: _files.isEmpty || _busy ? null : _prepare, icon: const Icon(Icons.build_circle), label: const Text('PREPARE TRAINING DATA')),
      if (_manifestPath != null) ...[
        const SizedBox(height: 12),
        Card(child: Padding(padding: const EdgeInsets.all(14), child: Text('Training dataset manifest created:\n' + _manifestPath!))),
      ],
      const SizedBox(height: 16),
      const Text('This workspace prepares training data. It does not pretend to run neural-network RVC training locally.', textAlign: TextAlign.center),
    ]),
  );
}
