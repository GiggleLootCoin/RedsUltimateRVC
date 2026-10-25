import 'dart:convert';
import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';

class TrainingScreen extends StatefulWidget {
  const TrainingScreen({super.key});
  @override State<TrainingScreen> createState() => _TrainingScreenState();
}
class _TrainingScreenState extends State<TrainingScreen> {
  final List<String> _files = [];
  bool _busy = false;
  String? _packagePath;
  String _name = "Red Voice";

  Future<void> _pick() async {
    final result = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['wav','mp3','flac','m4a','ogg'], allowMultiple: true, withData: false);
    if (result == null) return;
    final paths = result.files.map((f) => f.path).whereType<String>().where((p) => File(p).existsSync()).toList();
    if (mounted) setState(() { _files..clear()..addAll(paths); });
  }

  String _notebook() => jsonEncode({
    "cells": [
      {"cell_type":"markdown","metadata":{},"source":["# Red's Ultimate RVC — Voice Training\n","Upload this notebook to Kaggle, add the private red-rvc-training dataset as an Input, enable GPU, then Save & Run All."]},
      {"cell_type":"code","execution_count":null,"metadata":{},"outputs":[],"source":[
        "!git clone --depth 1 https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git /kaggle/working/rvc\n",
        "%cd /kaggle/working/rvc\n",
        "!pip install -q -r requirments_cu128_py312.txt\n",
        "!python -m pip install -q huggingface_hub\n",
        "!hf download lj1995/VoiceConversionWebUI --revision main --include 'hubert_base/*' --local-dir assets\n",
        "!hf download lj1995/VoiceConversionWebUI rmvpe.pt --revision main --local-dir assets/rmvpe\n",
        "!hf download lj1995/VoiceConversionWebUI --revision main --include 'pretrained/*' 'pretrained_v2/*' --local-dir assets\n",
        "!hf download lj1995/VoiceConversionWebUI mute.zip --revision main --local-dir .model-downloads\n",
        "!python -m zipfile -e .model-downloads/mute.zip logs"
      ]},
      {"cell_type":"code","execution_count":null,"metadata":{},"outputs":[],"source":[
        "import shutil\n",
        "src='/kaggle/input/red-rvc-training/dataset'\n",
        "dst='/kaggle/working/dataset'\n",
        "shutil.rmtree(dst, ignore_errors=True)\n",
        "shutil.copytree(src,dst)\n",
        "!python train/preprocess.py '/kaggle/working/dataset' 40000 4 'logs/red_voice' False 3.7\n",
        "!python train/dataset/extract_f0.py cuda 1 0 0 'logs/red_voice' true\n",
        "!python train/dataset/extract_hubert_feature.py cuda:0 1 0 0 'logs/red_voice' v2 true"
      ]},
      {"cell_type":"code","execution_count":null,"metadata":{},"outputs":[],"source":[
        "!python train/train.py -e 'red_voice' -sr 40k -f0 1 -bs 4 -g 0 -te 200 -se 10 -pg assets/pretrained_v2/f0G40k.pth -pd assets/pretrained_v2/f0D40k.pth -l 0 -c 0 -sw 1 -v v2\n",
        "!python train/train_index.py 'red_voice' v2 assets/indices 4 single\n",
        "print('Training complete. Check weights/ and logs/red_voice/.')"
      ]}
    ],
    "metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"}},
    "nbformat":4,"nbformat_minor":5
  });

  Future<void> _prepare() async {
    if (_files.isEmpty || _busy) return;
    setState(() => _busy = true);
    try {
      final docs = await getApplicationDocumentsDirectory();
      final root = Directory(docs.path + '/rvc_training');
      await root.create(recursive: true);
      final data = Directory(root.path + '/dataset');
      await data.create(recursive: true);
      for (final src in _files) {
        final name = File(src).uri.pathSegments.last.replaceAll(RegExp(r'[^A-Za-z0-9._-]'), '_');
        await File(src).copy(data.path + '/' + name);
      }
      final manifest = File(root.path + '/training_manifest.json');
      await manifest.writeAsString(const JsonEncoder.withIndent('  ').convert({'project': "Red's Ultimate RVC",'model': 'RVC v2 F0 40k','experiment': 'red_voice','audioFiles': 'dataset/'}));
      final notebook = File(root.path + '/Red_RVC_Kaggle_Training.ipynb');
      await notebook.writeAsString(_notebook());
      final instructions = File(root.path + '/README_KAGGLE.txt');
      await instructions.writeAsString("RED'S ULTIMATE RVC — TRAINING\n\n1. Create a PRIVATE Kaggle Dataset named red-rvc-training.\n2. Upload the dataset folder from this app's training workspace.\n3. Create a Kaggle Notebook, add that Dataset as an Input, and upload/open Red_RVC_Kaggle_Training.ipynb.\n4. Enable GPU in Notebook Settings.\n5. Save & Run All.\n\nThe phone prepares the real RVC training workflow. Kaggle performs the neural-network training.");
      if (mounted) setState(() { _packagePath = root.path; });
    } finally { if (mounted) setState(() => _busy = false); }
  }

  Future<void> _sharePackage() async {
    if (_packagePath == null) return;
    final root = Directory(_packagePath!);
    final files = <XFile>[];
    for (final name in ['training_manifest.json','Red_RVC_Kaggle_Training.ipynb','README_KAGGLE.txt']) {
      final f = File(root.path + '/' + name);
      if (await f.exists()) files.add(XFile(f.path));
    }
    for (final p in _files) if (await File(p).exists()) files.add(XFile(p));
    await Share.shareXFiles(files, subject: "Red's Ultimate RVC training package");
  }

  Future<void> _openKaggle() async => launchUrl(Uri.parse('https://www.kaggle.com/code'), mode: LaunchMode.externalApplication);

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text("RED'S ULTIMATE RVC — TRAIN"), centerTitle: true),
    body: ListView(padding: const EdgeInsets.fromLTRB(16,12,16,28), children: [
      Card(child: Padding(padding: const EdgeInsets.all(18), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
        Text('TRAIN YOUR VOICE', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
        SizedBox(height: 8),
        Text('The phone prepares the real RVC v2 training job. Free Kaggle GPU performs the heavy neural-network training instead of pretending the Galaxy A12 can do it locally.'),
      ]))),
      const SizedBox(height: 12),
      TextField(decoration: const InputDecoration(labelText: 'Voice / experiment name', border: OutlineInputBorder()), onChanged: (v) => _name = v),
      const SizedBox(height: 12),
      ElevatedButton.icon(onPressed: _busy ? null : _pick, icon: const Icon(Icons.library_add), label: const Text('ADD TRAINING AUDIO')),
      const SizedBox(height: 8),
      Text(_files.length.toString() + ' audio files selected'),
      if (_files.isNotEmpty) Card(child: Column(children: _files.take(40).map((p) => ListTile(dense: true, leading: const Icon(Icons.audio_file), title: Text(p.split('/').last, maxLines: 1, overflow: TextOverflow.ellipsis))).toList())),
      const SizedBox(height: 12),
      SizedBox(height: 52, child: ElevatedButton.icon(onPressed: _files.isEmpty || _busy ? null : _prepare, icon: const Icon(Icons.auto_awesome), label: Text(_busy ? 'PREPARING…' : 'PREPARE REAL RVC TRAINING'))),
      if (_packagePath != null) ...[
        const SizedBox(height: 12),
        Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('TRAINING PACKAGE READY', style: TextStyle(fontWeight: FontWeight.w900)),
          const SizedBox(height: 6),
          const Text('Dataset manifest + ready-to-run Kaggle notebook created.'),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(child: OutlinedButton.icon(onPressed: _sharePackage, icon: const Icon(Icons.share), label: const Text('SHARE PACKAGE'))),
            const SizedBox(width: 8),
            Expanded(child: ElevatedButton.icon(onPressed: _openKaggle, icon: const Icon(Icons.open_in_browser), label: const Text('OPEN KAGGLE'))),
          ]),
        ]))),
      ],
      const SizedBox(height: 16),
      const Text('RVC training is performed in Kaggle; the Android app remains the model/audio workspace and local ONNX inference client.', textAlign: TextAlign.center),
    ]),
  );
}
