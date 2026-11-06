import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:archive/archive_io.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/rvc_bridge.dart';

/// Local dataset preparation only. The bundled Android RVC engine has no
/// neural-network training implementation; never present this as training.
class TrainingScreen extends StatefulWidget {
  const TrainingScreen({super.key});
  @override
  State<TrainingScreen> createState() => _TrainingScreenState();
}

class _TrainingScreenState extends State<TrainingScreen> {
  final RVCBridge _bridge = RVCBridge();
  final List<String> _samples = [];
  final TextEditingController _name = TextEditingController(text: 'Red Voice');
  bool _busy = false;
  bool _recording = false;
  String _status = 'Add clean voice samples to begin';
  String? _datasetPath;

  @override
  void initState() {
    super.initState();
    _restorePreparedDataset();
  }

  Future<void> _restorePreparedDataset() async {
    final prefs = await SharedPreferences.getInstance();
    final path = prefs.getString('red_rvc_last_dataset_path');
    final name = prefs.getString('red_rvc_last_dataset_name');
    final pendingSaved = prefs.getStringList('red_rvc_pending_recordings') ?? [];
    final pending = pendingSaved.where((p) => File(p).existsSync()).toList();
    await prefs.setStringList('red_rvc_pending_recordings', pending);
    if (!mounted) return;
    if (name != null && name.isNotEmpty) _name.text = name;
    final hasDataset = path != null && await Directory(path).exists();
    var restored = <String>[];
    if (hasDataset) {
      final audio = Directory('$path/audio');
      restored = await audio.exists()
          ? await audio.list().where((entity) => entity is File).cast<File>().map((file) => file.path).toList()
          : <String>[];
    } else {
      await prefs.remove('red_rvc_last_dataset_path');
      await prefs.remove('red_rvc_last_dataset_name');
    }
    restored.addAll(pending.where((p) => !restored.contains(p)));
    if (mounted && restored.isNotEmpty) {
      setState(() {
        _datasetPath = hasDataset ? path : null;
        _samples
          ..clear()
          ..addAll(restored);
        _status = !hasDataset
            ? 'Recovered recording sample(s). Prepare a dataset to keep them.'
            : 'Prepared dataset restored. You can export it or continue adding samples.';
      });
    }
  }

  Future<void> _rememberPendingRecording(String path) async {
    final prefs = await SharedPreferences.getInstance();
    final pending = prefs.getStringList('red_rvc_pending_recordings') ?? [];
    if (!pending.contains(path)) pending.add(path);
    await prefs.setStringList('red_rvc_pending_recordings', pending);
  }

  @override
  void dispose() {
    if (_recording) {
      unawaited(_bridge.stopRecording().then(_rememberPendingRecording).catchError((_) {}));
    }
    _name.dispose();
    super.dispose();
  }

  Future<void> _addAudio() async {
    if (_busy || _recording) return;
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.any, allowMultiple: true, withData: false,
      );
      if (result == null) return;
      final paths = result.files.map((f) => f.path).whereType<String>()
        .where((p) => File(p).existsSync())
        .where((p) => ['.wav','.flac','.mp3','.m4a','.ogg','.aac']
          .any((e) => p.toLowerCase().endsWith(e))).toList();
      if (!mounted) return;
      setState(() {
        for (final p in paths) { if (!_samples.contains(p)) _samples.add(p); }
        _status = '${_samples.length} sample(s) selected';
      });
    } catch (e) {
      if (mounted) setState(() => _status = 'Could not import audio: $e');
    }
  }

  Future<void> _recordSample() async {
    if (_busy) return;
    try {
      if (!_recording) {
        final permission = await Permission.microphone.request();
        if (!mounted) return;
        if (!permission.isGranted) {
          if (mounted) {
            setState(() => _status = permission.isPermanentlyDenied
                ? 'Microphone permission is blocked. Enable it in Android App settings.'
                : 'Microphone permission is required to record a voice sample.');
          }
          return;
        }
        await _bridge.startRecording();
        if (!mounted) {
          final path = await _bridge.stopRecording();
          await _rememberPendingRecording(path);
          return;
        }
        setState(() { _recording = true; _status = 'Recording…'; });
      } else {
        setState(() => _recording = false);
        final path = await _bridge.stopRecording();
        if (!mounted) {
          await _rememberPendingRecording(path);
          return;
        }
        setState(() {
          if (!_samples.contains(path)) _samples.add(path);
          _status = '${_samples.length} sample(s) selected';
        });
      }
    } catch (e) {
      if (mounted) setState(() { _recording = false; _status = 'Recording error: $e'; });
    }
  }

  Future<void> _prepareDataset() async {
    if (_samples.isEmpty || _busy || _recording) return;
    setState(() { _busy = true; _status = 'Copying samples into private app storage…'; });
    try {
      final docs = await getApplicationDocumentsDirectory();
      final safe = _name.text.trim().replaceAll(RegExp(r'[^A-Za-z0-9_-]'), '_');
      final root = Directory('${docs.path}/rvc_datasets/${safe.isEmpty ? 'voice' : safe}');
      final data = Directory('${root.path}/audio');
      await data.create(recursive: true);
      for (var i = 0; i < _samples.length; i++) {
        final src = File(_samples[i]);
        if (!await src.exists()) continue;
        if (src.absolute.path.startsWith(data.absolute.path + Platform.pathSeparator)) continue;
        final base = src.uri.pathSegments.last.replaceAll(RegExp(r'[^A-Za-z0-9._-]'), '_');
        await src.copy('${data.path}/${i.toString().padLeft(4, '0')}_$base');
      }
      final totalSamples = await data.list().where((entity) => entity is File).length;
      await File('${root.path}/README.txt').writeAsString(
        "RED'S ULTIMATE RVC — DATASET\nVoice: ${_name.text.trim()}\nAudio files: $totalSamples\n\nThis is prepared training data only. It has NOT trained a voice model. The bundled Android engine currently supports ONNX inference and does not contain an RVC training engine.\n",
      );
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('red_rvc_last_dataset_path', root.path);
      await prefs.setString('red_rvc_last_dataset_name', _name.text.trim());
      await prefs.remove('red_rvc_pending_recordings');
      if (mounted) setState(() {
        _datasetPath = root.path;
        _status = '$totalSamples sample(s) in the prepared dataset. No model has been trained.';
      });
    } catch (e) {
      if (mounted) setState(() => _status = 'Dataset preparation failed: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _shareDataset() async {
    if (_datasetPath == null || _busy || _recording) return;
    setState(() { _busy = true; _status = 'Preparing dataset for sharing…'; });
    try {
      final audio = Directory('$_datasetPath/audio');
      if (!await audio.exists()) throw Exception('Prepared audio folder is missing.');
      final files = await audio.list().where((entity) => entity is File).cast<File>().toList();
      if (files.isEmpty) throw Exception('There are no prepared audio samples to export.');
      final safeName = _name.text.trim().replaceAll(RegExp(r'[^A-Za-z0-9_-]'), '_');
      final zipPath = '${(await getTemporaryDirectory()).path}/${safeName.isEmpty ? 'voice' : safeName}_rvc_dataset.zip';
      final encoder = ZipFileEncoder();
      encoder.create(zipPath);
      encoder.addDirectory(audio, includeDirName: true);
      encoder.close();
      final archive = File(zipPath);
      if (!await archive.exists() || await archive.length() == 0) {
        throw Exception('Dataset ZIP could not be created.');
      }
      await Share.shareXFiles(
        [XFile(zipPath, mimeType: 'application/zip')],
        text: 'Red’s Ultimate RVC voice dataset — ${_name.text.trim()}',
      );
      if (mounted) setState(() => _status = 'Dataset exported as ${archive.uri.pathSegments.last} (${files.length} audio samples).');
    } catch (e) {
      if (mounted) setState(() => _status = 'Dataset export failed: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }


  Future<void> _openFreeTrainingNotebook() async {
    final uri = Uri.parse(
      'https://kaggle.com/kernels/welcome?src=https://github.com/juksentang/RVC-Retrieval-based-Voice-Conversion-Colab/blob/main/RVC_CLI.ipynb',
    );
    try {
      final opened = await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (mounted) {
        setState(() => _status = opened
            ? 'Opened the free Kaggle RVC training notebook. Upload your exported dataset ZIP as a Kaggle Dataset.'
            : 'Could not open Kaggle. Check your internet connection and try again.');
      }
    } catch (e) {
      if (mounted) setState(() => _status = 'Could not open Kaggle: $e');
    }
  }

  Future<void> _clear() async {
    if (_datasetPath != null) {
      final d = Directory(_datasetPath!);
      if (await d.exists()) await d.delete(recursive: true);
    }
    final prefs = await SharedPreferences.getInstance();
    final pending = prefs.getStringList('red_rvc_pending_recordings') ?? [];
    for (final path in pending) {
      try { await File(path).delete(); } catch (_) {}
    }
    await prefs.remove('red_rvc_last_dataset_path');
    await prefs.remove('red_rvc_last_dataset_name');
    await prefs.remove('red_rvc_pending_recordings');
    if (mounted) setState(() { _datasetPath = null; _samples.clear(); _status = 'Workspace cleared'; });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: const Color(0xFF07070A),
    appBar: AppBar(title: const Text("RED'S ULTIMATE RVC — VOICE LAB"), centerTitle: true),
    body: ListView(padding: const EdgeInsets.all(16), children: [
      Card(color: const Color(0xFF171117), child: const Padding(
        padding: EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('ON-PHONE DATASET WORKSPACE', style: TextStyle(fontWeight: FontWeight.w900, color: Color(0xFFFF334F))),
          SizedBox(height: 8),
          Text('Import or record clean samples and organise them privately on this phone.'),
          SizedBox(height: 10),
          Text('This phone prepares your dataset but does not train the neural network. For genuine training, use the optional Kaggle CLI notebook below. It runs the RVC training and FAISS index steps on Kaggle GPU, not on this phone. Kaggle availability and free GPU quota are controlled by Kaggle.', style: TextStyle(height: 1.35)),
        ]),
      )),
      const SizedBox(height: 12),
      TextField(controller: _name, decoration: const InputDecoration(labelText: 'Voice / dataset name', border: OutlineInputBorder())),
      const SizedBox(height: 12),
      Row(children: [
        Expanded(child: ElevatedButton.icon(onPressed: _busy ? null : _recordSample, icon: Icon(_recording ? Icons.stop : Icons.mic), label: Text(_recording ? 'STOP' : 'RECORD'))),
        const SizedBox(width: 8),
        Expanded(child: OutlinedButton.icon(onPressed: _busy || _recording ? null : _addAudio, icon: const Icon(Icons.audio_file), label: const Text('ADD AUDIO'))),
      ]),
      const SizedBox(height: 10),
      Card(color: const Color(0xFF121218), child: ListTile(
        leading: Icon(_recording ? Icons.fiber_manual_record : Icons.info_outline, color: const Color(0xFFFF334F)),
        title: Text(_status),
        subtitle: Text('${_samples.length} source sample(s)'),
      )),
      ..._samples.take(100).map((p) => ListTile(
        dense: true, leading: const Icon(Icons.graphic_eq, color: Color(0xFFFF334F)),
        title: Text(p.split('/').last, maxLines: 1, overflow: TextOverflow.ellipsis),
      )),
      const SizedBox(height: 10),
      SizedBox(height: 50, child: ElevatedButton.icon(
        onPressed: _busy || _recording || _samples.isEmpty ? null : _prepareDataset,
        icon: const Icon(Icons.folder_copy), label: Text(_busy ? 'PREPARING…' : 'PREPARE LOCAL DATASET'),
      )),
      if (_datasetPath != null) ...[
        Padding(
          padding: const EdgeInsets.only(top: 10),
          child: SelectableText('Saved privately at: $_datasetPath'),
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: 48,
          child: ElevatedButton.icon(
            onPressed: _busy || _recording ? null : _shareDataset,
            icon: const Icon(Icons.share),
            label: const Text('EXPORT / SHARE DATASET FILES'),
          ),
        ),
      ],

      const SizedBox(height: 10),
      SizedBox(
        height: 50,
        child: OutlinedButton.icon(
          onPressed: _busy || _recording ? null : _openFreeTrainingNotebook,
          icon: const Icon(Icons.cloud_outlined),
          label: const Text('OPEN FREE KAGGLE RVC TRAINER'),
        ),
      ),
      const Padding(
        padding: EdgeInsets.only(top: 6),
        child: Text(
          'Prepare your dataset above, export it as a ZIP, then upload it to Kaggle as a Dataset and attach it to the notebook. Kaggle may require account phone verification for GPU access.',
          style: TextStyle(color: Color(0xFFB7B7C1), fontSize: 12, height: 1.35),
        ),
      ),
      const SizedBox(height: 8),
      OutlinedButton.icon(onPressed: _busy || _recording ? null : _clear, icon: const Icon(Icons.delete_outline), label: const Text('CLEAR WORKSPACE')),
    ]),
  );
}
