import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

/// Stores source files safely without treating .pth/.pt/.zip as runnable ONNX.
class ModelLibraryScreen extends StatefulWidget {
  final ValueChanged<String>? onModelSelected;
  final ValueChanged<String?>? onIndexSelected;

  const ModelLibraryScreen({
    super.key,
    this.onModelSelected,
    this.onIndexSelected,
  });

  @override
  State<ModelLibraryScreen> createState() => _ModelLibraryScreenState();
}

class _ModelLibraryScreenState extends State<ModelLibraryScreen> {
  static const _supported = {
    '.onnx', '.pth', '.pt', '.zip', '.index', '.mobile.index',
  };
  final List<File> _files = [];
  bool _busy = false;
  String _status = 'Import voice models or source files to keep them on this phone.';

  @override
  void initState() {
    super.initState();
    _loadFiles();
  }

  Future<Directory> _libraryDirectory() async {
    final app = await getApplicationDocumentsDirectory();
    final directory = Directory('${app.path}/red_rvc_model_library');
    if (!await directory.exists()) await directory.create(recursive: true);
    return directory;
  }

  bool _isSupported(String path) {
    final lower = path.toLowerCase();
    return _supported.any(lower.endsWith);
  }

  Future<void> _loadFiles() async {
    try {
      final directory = await _libraryDirectory();
      final files = await directory.list().where((e) => e is File).cast<File>().toList();
      files.sort((a, b) => a.path.toLowerCase().compareTo(b.path.toLowerCase()));
      if (!mounted) return;
      setState(() {
        _files
          ..clear()
          ..addAll(files);
      });
    } catch (e) {
      if (mounted) setState(() => _status = 'Could not read model library: $e');
    }
  }

  Future<void> _importFiles() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _status = 'Choose model files in Android Files…';
    });
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.any,
        allowMultiple: true,
        withData: false,
      );
      if (result == null) {
        if (mounted) setState(() => _status = 'Import cancelled.');
        return;
      }
      final directory = await _libraryDirectory();
      var imported = 0;
      final skipped = <String>[];
      for (final picked in result.files) {
        final sourcePath = picked.path;
        if (sourcePath == null || !_isSupported(sourcePath) || !await File(sourcePath).exists()) {
          skipped.add(picked.name);
          continue;
        }
        final name = sourcePath.split(Platform.pathSeparator).last;
        var destination = File('${directory.path}/$name');
        if (await destination.exists()) {
          final dot = name.lastIndexOf('.');
          final base = dot > 0 ? name.substring(0, dot) : name;
          final extension = dot > 0 ? name.substring(dot) : '';
          destination = File('${directory.path}/${base}_${DateTime.now().microsecondsSinceEpoch}$extension');
        }
        await File(sourcePath).copy(destination.path);
        imported++;
      }
      await _loadFiles();
      if (mounted) {
        setState(() => _status = skipped.isEmpty
            ? 'Imported $imported file(s). Source files are stored privately on this phone.'
            : 'Imported $imported file(s). Skipped unsupported or inaccessible files: ${skipped.join(', ')}');
      }
    } catch (e) {
      if (mounted) setState(() => _status = 'Import failed: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _share(File file) async {
    try {
      await Share.shareXFiles([XFile(file.path)], text: 'Red’s Ultimate RVC model file');
    } catch (e) {
      if (mounted) setState(() => _status = 'Could not share file: $e');
    }
  }

  Future<void> _delete(File file) async {
    try {
      await file.delete();
      await _loadFiles();
      if (mounted) setState(() => _status = 'Removed ${file.uri.pathSegments.last} from this phone.');
    } catch (e) {
      if (mounted) setState(() => _status = 'Could not remove file: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF07070A),
      appBar: AppBar(
        title: const Text('MODEL LIBRARY'),
        centerTitle: true,
        backgroundColor: const Color(0xFF09090D),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _busy ? null : _importFiles,
        backgroundColor: const Color(0xFFE00022),
        icon: const Icon(Icons.add),
        label: const Text('IMPORT FILES'),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 100),
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF171117),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFF64202C)),
              ),
              child: const Text(
                'Stored privately on this phone: .onnx, .pth, .pt, .zip, .index and .mobile.index. Only compatible ONNX models can be selected for conversion. PTH/PT/ZIP files are stored as source files; this screen does not convert or train them.',
                style: TextStyle(color: Color(0xFFD4D0D5), height: 1.45),
              ),
            ),
            const SizedBox(height: 12),
            if (_busy) const LinearProgressIndicator(color: Color(0xFFFF334F)),
            Text(_status, style: const TextStyle(color: Color(0xFFB8B8C2), height: 1.4)),
            const SizedBox(height: 12),
            if (_files.isEmpty)
              const Padding(
                padding: EdgeInsets.only(top: 28),
                child: Center(child: Text('No files stored yet.', style: TextStyle(color: Color(0xFF92929D)))),
              ),
            for (final file in _files)
              Card(
                color: const Color(0xFF121218),
                child: ListTile(
                  leading: const Icon(Icons.audio_file, color: Color(0xFFFF334F)),
                  title: Text(file.uri.pathSegments.last, maxLines: 2, overflow: TextOverflow.ellipsis),
                  subtitle: Text(_sizeLabel(file.lengthSync())),
                  trailing: PopupMenuButton<String>(
                    onSelected: (value) {
                      if (value == 'share') _share(file);
                      if (value == 'delete') _delete(file);
                      if (value == 'use-model' && widget.onModelSelected != null) {
                        widget.onModelSelected!(file.path);
                        Navigator.of(context).pop();
                      }
                      if (value == 'use-index' && widget.onIndexSelected != null) {
                        widget.onIndexSelected!(file.path);
                        Navigator.of(context).pop();
                      }
                    },
                    itemBuilder: (_) {
                      final lower = file.path.toLowerCase();
                      return [
                        if (lower.endsWith('.onnx') && widget.onModelSelected != null)
                          const PopupMenuItem(value: 'use-model', child: Text('Use as active ONNX model')),
                        if (lower.endsWith('.mobile.index') && widget.onIndexSelected != null)
                          const PopupMenuItem(value: 'use-index', child: Text('Use as conversion index')),
                        const PopupMenuItem(value: 'share', child: Text('Share')),
                        const PopupMenuItem(value: 'delete', child: Text('Delete')),
                      ];
                    },
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  String _sizeLabel(int bytes) {
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}
