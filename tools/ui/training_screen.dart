import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:path_provider/path_provider.dart';
import '../services/rvc_bridge.dart';

class TrainingScreen extends StatefulWidget {
  const TrainingScreen({super.key});
  @override State<TrainingScreen> createState() => _TrainingScreenState();
}

class _TrainingScreenState extends State<TrainingScreen> with SingleTickerProviderStateMixin {
  late final TabController _tabs;
  final RVCBridge _bridge = RVCBridge();
  final List<String> _samples = <String>[];
  bool _busy = false;
  bool _recording = false;
  String _voiceName = 'Red Voice';
  String? _datasetPath;
  String _status = 'Ready';
  late final WebViewController _trainingWeb;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 2, vsync: this);
    _trainingWeb = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(NavigationDelegate(
        onNavigationRequest: (_) => NavigationDecision.navigate,
      ))
      ..loadRequest(Uri.parse('https://nicevois.com/train-rvc-model-online'));
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  Future<void> _addAudio() async {
    if (_busy || _recording) return;
    final result = await FilePicker.platform.pickFiles(
      type: FileType.any,
      allowMultiple: true,
      withData: false,
    );
    if (result == null) return;
    final paths = result.files.map((f) => f.path).whereType<String>()
        .where((p) => File(p).existsSync())
        .where((p) => ['.wav','.mp3','.flac','.m4a','.ogg','.aac'].any((e) => p.toLowerCase().endsWith(e)))
        .toList();
    if (!mounted) return;
    setState(() {
      for (final p in paths) {
        if (!_samples.contains(p)) _samples.add(p);
      }
      _status = _samples.isEmpty ? 'No training audio selected' : '${_samples.length} training sample(s) ready';
    });
  }

  Future<void> _recordSample() async {
    if (_busy) return;
    if (!_recording) {
      try {
        await _bridge.startRecording();
        if (mounted) setState(() { _recording = true; _status = 'Recording training sample…'; });
      } catch (e) {
        if (mounted) setState(() => _status = 'Recording failed: $e');
      }
      return;
    }
    try {
      final path = await _bridge.stopRecording();
      if (mounted) setState(() {
        _recording = false;
        if (!_samples.contains(path)) _samples.add(path);
        _status = '${_samples.length} training sample(s) ready';
      });
    } catch (e) {
      if (mounted) setState(() { _recording = false; _status = 'Recording failed: $e'; });
    }
  }

  Future<void> _prepareDataset() async {
    if (_samples.isEmpty || _busy) return;
    setState(() { _busy = true; _status = 'Building local training dataset…'; });
    try {
      final docs = await getApplicationDocumentsDirectory();
      final safeName = _voiceName.trim().replaceAll(RegExp(r'[^A-Za-z0-9_-]'), '_');
      final folder = safeName.isEmpty ? 'red_voice' : safeName;
      final root = Directory('${docs.path}/rvc_training/$folder');
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
        "Voice: $folder\nSamples: ${_samples.length}\n"
        "Prepared entirely on the phone.\n"
        "Training is started from the In-App Training tab and remains inside this app window.\n",
      );
      if (mounted) setState(() { _datasetPath = root.path; _status = 'Local dataset ready'; });
    } catch (e) {
      if (mounted) setState(() => _status = 'Dataset preparation failed: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _clear() async {
    if (_datasetPath != null) {
      final dir = Directory(_datasetPath!);
      if (await dir.exists()) await dir.delete(recursive: true);
    }
    if (mounted) setState(() { _datasetPath = null; _samples.clear(); _status = 'Ready'; });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("RED'S ULTIMATE RVC — TRAINING LAB"),
        centerTitle: true,
        bottom: TabBar(
          controller: _tabs,
          tabs: const [Tab(text: 'PHONE WORKSPACE'), Tab(text: 'IN-APP TRAINING')],
        ),
      ),
      body: TabBarView(
        controller: _tabs,
        children: [
          ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 30),
            children: [
              Card(child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('PHONE TRAINING WORKSPACE', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 8),
                  const Text('Record or import your voice samples and build a clean dataset without leaving the app.'),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(borderRadius: BorderRadius.circular(14), color: const Color(0x221A1A1F)),
                    child: const Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Icon(Icons.info_outline, color: Colors.redAccent),
                      SizedBox(width: 10),
                      Expanded(child: Text('The Galaxy A12 is not a practical target for running the full RVC neural-network trainer locally. This app keeps the real training workflow inside this screen and uses the training service only for the heavy neural-network computation. You do not need to open Kaggle, Colab or another app.', style: TextStyle(fontWeight: FontWeight.w600))),
                    ]),
                  ),
                ]),
              )),
              const SizedBox(height: 12),
              TextField(
                controller: TextEditingController(text: _voiceName)..selection = TextSelection.collapsed(offset: _voiceName.length),
                onChanged: (v) => _voiceName = v,
                decoration: const InputDecoration(labelText: 'Voice / dataset name', border: OutlineInputBorder()),
              ),
              const SizedBox(height: 12),
              Row(children: [
                Expanded(child: ElevatedButton.icon(onPressed: _busy ? null : _recordSample, icon: Icon(_recording ? Icons.stop : Icons.mic), label: Text(_recording ? 'STOP RECORDING' : 'RECORD SAMPLE'))),
                const SizedBox(width: 10),
                Expanded(child: OutlinedButton.icon(onPressed: _busy || _recording ? null : _addAudio, icon: const Icon(Icons.audio_file), label: const Text('ADD AUDIO'))),
              ]),
              const SizedBox(height: 10),
              Card(child: ListTile(
                leading: Icon(_recording ? Icons.fiber_manual_record : Icons.check_circle, color: _recording ? Colors.redAccent : Colors.green),
                title: Text(_status),
                subtitle: Text('${_samples.length} sample(s) in this workspace'),
              )),
              if (_samples.isNotEmpty) Card(child: Column(children: _samples.take(50).map((p) => ListTile(
                dense: true, leading: const Icon(Icons.graphic_eq),
                title: Text(p.split('/').last, maxLines: 1, overflow: TextOverflow.ellipsis),
              )).toList())),
              const SizedBox(height: 10),
              SizedBox(height: 52, child: ElevatedButton.icon(
                onPressed: _samples.isEmpty || _busy || _recording ? null : _prepareDataset,
                icon: const Icon(Icons.folder_copy),
                label: Text(_busy ? 'PREPARING…' : 'BUILD LOCAL DATASET'),
              )),
              if (_datasetPath != null) ...[
                const SizedBox(height: 10),
                Card(child: ListTile(
                  leading: const Icon(Icons.folder_special, color: Colors.redAccent),
                  title: const Text('LOCAL DATASET READY'),
                  subtitle: Text(_datasetPath!, maxLines: 2, overflow: TextOverflow.ellipsis),
                )),
              ],
              const SizedBox(height: 10),
              OutlinedButton.icon(onPressed: _busy ? null : _clear, icon: const Icon(Icons.delete_outline), label: const Text('CLEAR TRAINING WORKSPACE')),
              const SizedBox(height: 12),
              const Text('Tip: 10–30 minutes of clean, single-speaker audio is a sensible starting dataset.'),
            ],
          ),
          Column(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                color: const Color(0xFF111117),
                child: Row(children: [
                  const Expanded(child: Text('RVC training runs inside this app screen. Internet is required because the heavy training compute runs on the in-app training service.', style: TextStyle(fontSize: 11, color: Color(0xFFB8B8C2)))),
                  IconButton(onPressed: () => _trainingWeb.reload(), icon: const Icon(Icons.refresh)),
                ]),
              ),
              const Expanded(child: _TrainingWebPlaceholder()),
            ],
          ),
        ],
      ),
    );
  }
}

class _TrainingWebPlaceholder extends StatelessWidget {
  const _TrainingWebPlaceholder();
  @override
  Widget build(BuildContext context) {
    final state = context.findAncestorStateOfType<_TrainingScreenState>();
    return WebViewWidget(controller: state!._trainingWeb);
  }
}
