import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import '../services/rvc_bridge.dart';

class TrainingScreen extends StatefulWidget {
  const TrainingScreen({super.key});
  @override State<TrainingScreen> createState() => _TrainingScreenState();
}

class _TrainingScreenState extends State<TrainingScreen> {
  final RVCBridge _bridge = RVCBridge();
  final List<String> _samples = <String>[];
  bool _busy = false;
  bool _recording = false;
  String _voiceName = "Red Voice";
  String? _datasetPath;
  String _status = "Ready";

  Future<void> _addAudio() async {
    if (_busy || _recording) return;
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['wav','mp3','flac','m4a','ogg'],
      allowMultiple: true,
      withData: false,
    );
    if (result == null) return;
    final paths = result.files.map((f) => f.path).whereType<String>().where((p) => File(p).existsSync()).toList();
    if (!mounted) return;
    setState(() {
      for (final p in paths) {
        if (!_samples.contains(p)) _samples.add(p);
      }
      _status = _samples.isEmpty ? "No training audio selected" : "${_samples.length} training samples ready";
    });
  }

  Future<void> _recordSample() async {
    if (_busy) return;
    if (!_recording) {
      try {
        await _bridge.startRecording();
        if (mounted) setState(() { _recording = true; _status = "Recording training sample…"; });
      } catch (e) {
        if (mounted) setState(() => _status = "Recording failed: $e");
      }
      return;
    }
    try {
      final path = await _bridge.stopRecording();
      if (mounted) setState(() {
        _recording = false;
        if (!_samples.contains(path)) _samples.add(path);
        _status = "${_samples.length} training samples ready";
      });
    } catch (e) {
      if (mounted) setState(() { _recording = false; _status = "Recording failed: $e"; });
    }
  }

  Future<void> _prepareDataset() async {
    if (_samples.isEmpty || _busy) return;
    setState(() { _busy = true; _status = "Building local training dataset…"; });
    try {
      final docs = await getApplicationDocumentsDirectory();
      final safeName = _voiceName.trim().replaceAll(RegExp(r'[^A-Za-z0-9_-]'), '_').isEmpty
          ? "red_voice" : _voiceName.trim().replaceAll(RegExp(r'[^A-Za-z0-9_-]'), '_');
      final root = Directory('${docs.path}/rvc_training/$safeName');
      final dataset = Directory('${root.path}/dataset');
      await dataset.create(recursive: true);
      for (var i = 0; i < _samples.length; i++) {
        final src = File(_samples[i]);
        if (!await src.exists()) continue;
        final name = src.uri.pathSegments.last.replaceAll(RegExp(r'[^A-Za-z0-9._-]'), '_');
        await src.copy('${dataset.path}/${i.toString().padLeft(4, '0')}_$name');
      }
      final manifest = File('${root.path}/training_manifest.txt');
      await manifest.writeAsString(
        "RED'S ULTIMATE RVC — LOCAL TRAINING DATASET\n"
        "Voice: $safeName\n"
        "Samples: ${_samples.length}\n\n"
        "The Android RVC engine in this build can run trained ONNX models, "
        "but it does not contain an on-device RVC neural-network trainer. "
        "This workspace therefore prepares and stores your training data locally "
        "without pretending that a model was trained.\n",
      );
      if (mounted) setState(() {
        _datasetPath = root.path;
        _status = "Local dataset ready";
      });
    } catch (e) {
      if (mounted) setState(() => _status = "Dataset preparation failed: $e");
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _clear() async {
    if (_datasetPath != null) {
      final dir = Directory(_datasetPath!);
      if (await dir.exists()) await dir.delete(recursive: true);
    }
    if (mounted) setState(() { _datasetPath = null; _samples.clear(); _status = "Ready"; });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("RED'S ULTIMATE RVC — TRAINING LAB"), centerTitle: true),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 30),
        children: [
          Card(child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text("TRAINING LAB", style: TextStyle(fontSize: 23, fontWeight: FontWeight.w900)),
              const SizedBox(height: 8),
              Text("Build your voice dataset entirely on the phone. Record or import samples, organize them locally, and keep the workspace with the app.", style: Theme.of(context).textTheme.bodyMedium),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(borderRadius: BorderRadius.circular(14), color: const Color(0x221A1A1F)),
                child: const Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Icon(Icons.info_outline, color: Colors.redAccent),
                  SizedBox(width: 10),
                  Expanded(child: Text("Important: this Android engine does not include an RVC neural-network training engine. It cannot honestly create a new .pth model by itself. Trained ONNX models can be used for conversion.", style: TextStyle(fontWeight: FontWeight.w600))),
                ]),
              ),
            ]),
          )),
          const SizedBox(height: 12),
          TextField(
            controller: TextEditingController(text: _voiceName)..selection = TextSelection.collapsed(offset: _voiceName.length),
            onChanged: (v) => _voiceName = v,
            decoration: const InputDecoration(labelText: "Voice / dataset name", border: OutlineInputBorder()),
          ),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(child: ElevatedButton.icon(onPressed: _busy ? null : _recordSample, icon: Icon(_recording ? Icons.stop : Icons.mic), label: Text(_recording ? "STOP RECORDING" : "RECORD SAMPLE"))),
            const SizedBox(width: 10),
            Expanded(child: OutlinedButton.icon(onPressed: _busy || _recording ? null : _addAudio, icon: const Icon(Icons.audio_file), label: const Text("ADD AUDIO"))),
          ]),
          const SizedBox(height: 10),
          Card(child: ListTile(
            leading: Icon(_recording ? Icons.fiber_manual_record : Icons.check_circle, color: _recording ? Colors.redAccent : Colors.green),
            title: Text(_status),
            subtitle: Text("${_samples.length} sample(s) in this workspace"),
          )),
          if (_samples.isNotEmpty) Card(
            child: Column(children: _samples.take(50).map((p) => ListTile(
              dense: true,
              leading: const Icon(Icons.graphic_eq),
              title: Text(p.split('/').last, maxLines: 1, overflow: TextOverflow.ellipsis),
            )).toList()),
          ),
          const SizedBox(height: 10),
          SizedBox(height: 52, child: ElevatedButton.icon(
            onPressed: _samples.isEmpty || _busy || _recording ? null : _prepareDataset,
            icon: const Icon(Icons.folder_copy),
            label: Text(_busy ? "PREPARING…" : "BUILD LOCAL DATASET"),
          )),
          if (_datasetPath != null) ...[
            const SizedBox(height: 10),
            Card(child: ListTile(
              leading: const Icon(Icons.folder_special, color: Colors.redAccent),
              title: const Text("LOCAL DATASET READY"),
              subtitle: Text(_datasetPath!, maxLines: 2, overflow: TextOverflow.ellipsis),
            )),
          ],
          const SizedBox(height: 10),
          OutlinedButton.icon(onPressed: _busy ? null : _clear, icon: const Icon(Icons.delete_outline), label: const Text("CLEAR TRAINING WORKSPACE")),
        ],
      ),
    );
  }
}
