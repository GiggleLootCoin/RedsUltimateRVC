import 'dart:io';

import 'package:audioplayers/audioplayers.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../services/rvc_bridge.dart';

/// Fully local song-cover workflow: separate the original, convert the vocal
/// stem with the selected RVC ONNX model, then mix it with the backing stem.
class SongCoverScreen extends StatefulWidget {
  final String modelPath;
  final String? indexPath;

  const SongCoverScreen({
    super.key,
    required this.modelPath,
    this.indexPath,
  });

  @override
  State<SongCoverScreen> createState() => _SongCoverScreenState();
}

class _SongCoverScreenState extends State<SongCoverScreen> {
  final RVCBridge _bridge = RVCBridge();
  final AudioPlayer _player = AudioPlayer();
  String? _inputPath;
  String? _inputName;
  String? _outputPath;
  String _status = 'Choose a song to begin.';
  double _progress = 0;
  bool _busy = false;

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  Future<void> _pickSong() async {
    if (_busy) return;
    final result = await FilePicker.platform.pickFiles(
      type: FileType.audio,
      allowMultiple: false,
      withData: false,
    );
    final path = result?.files.single.path;
    if (path == null || path.isEmpty) return;
    try {
      final imported = await _bridge.importPickedFile(
        kind: 'audio',
        sourcePath: path,
      );
      if (!mounted) return;
      setState(() {
        _inputPath = imported.path;
        _inputName = File(imported.path).uri.pathSegments.last;
        _outputPath = null;
        _progress = 0;
        _status = 'Ready to separate vocals.';
      });
    } catch (e) {
      if (mounted) _message('Could not import that audio file: $e');
    }
  }

  Future<void> _createCover() async {
    if (_busy || _inputPath == null) return;
    setState(() {
      _busy = true;
      _progress = 0;
      _outputPath = null;
      _status = 'Separating vocals and accompaniment on this phone…';
    });
    try {
      final stems = await _bridge.separateSongVocals(_inputPath!);
      final vocalsPath = stems['vocalsPath']!;
      final accompanimentPath = stems['accompanimentPath']!;
      if (!mounted) return;
      setState(() => _status = 'Converting the isolated vocals with your RVC model…');

      final convertedVocals = await _bridge.infer(
        songPath: vocalsPath,
        modelPath: widget.modelPath,
        indexPath: widget.indexPath,
        parallelChunkCount: 1,
        allowResume: false,
        onProgress: (value, status) {
          if (!mounted) return;
          setState(() {
            _progress = (value / 100).clamp(0.0, 1.0).toDouble();
            _status = status;
          });
        },
      );

      if (!mounted) return;
      setState(() => _status = 'Mixing the converted vocals with the original accompaniment…');
      final mixed = await _bridge.mixSongCover(
        convertedVocalsPath: convertedVocals,
        accompanimentPath: accompanimentPath,
        vocalGain: 1.0,
        accompanimentGain: 0.85,
      );
      if (!mounted) return;
      setState(() {
        _outputPath = mixed;
        _progress = 1;
        _status = 'Your song cover is ready.';
      });
      await _player.play(DeviceFileSource(mixed));
    } catch (e) {
      if (mounted) {
        setState(() => _status = 'Song-cover creation failed.');
        _message('Song-cover creation failed: $e');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _saveCover() async {
    final path = _outputPath;
    if (path == null) return;
    try {
      final saved = await _bridge.saveGeneratedAudio(path);
      if (mounted) _message('Saved to $saved');
    } catch (e) {
      if (mounted) _message('Could not save the song cover: $e');
    }
  }

  void _message(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF08080C),
      appBar: AppBar(
        title: const Text("RED'S SONG COVERS", style: TextStyle(fontSize: 13, fontWeight: FontWeight.w900, letterSpacing: 1.15)),
        backgroundColor: const Color(0xFF0B090D),
        surfaceTintColor: Colors.transparent,
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(18),
        children: [
          Container(
            padding: const EdgeInsets.fromLTRB(18, 19, 18, 18),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(24),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF3A101C), Color(0xFF1B1119), Color(0xFF101219)],
              ),
              border: Border.all(color: const Color(0x77FF3654)),
              boxShadow: const [BoxShadow(color: Color(0x22000000), blurRadius: 22, offset: Offset(0, 10))],
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  Icon(Icons.graphic_eq_rounded, color: Color(0xFFFF7185), size: 17),
                  SizedBox(width: 7),
                  Text('LOCAL AUDIO PRODUCTION', style: TextStyle(color: Color(0xFFFFA0AD), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
                ]),
                SizedBox(height: 11),
                Text('Make the song\nyour own.', style: TextStyle(fontSize: 25, height: 1.08, fontWeight: FontWeight.w900, letterSpacing: -.65)),
                SizedBox(height: 8),
                Text('Build a cover with your selected voice. Vocal separation, conversion and mix-back run on this phone.', style: TextStyle(color: Color(0xFFD0C7CE), fontSize: 12, height: 1.45)),
              ],
            ),
          ),
          const SizedBox(height: 18),
          _panel(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('SOURCE SONG', style: TextStyle(color: Color(0xFFFF405B), fontWeight: FontWeight.w900)),
                const SizedBox(height: 8),
                Text(_inputName ?? 'No song selected'),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: _busy ? null : _pickSong,
                  icon: const Icon(Icons.audio_file),
                  label: const Text('CHOOSE AUDIO FILE'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          _panel(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('VOICE MODEL', style: TextStyle(color: Color(0xFFFF405B), fontWeight: FontWeight.w900)),
                const SizedBox(height: 8),
                Text(File(widget.modelPath).uri.pathSegments.last),
                const SizedBox(height: 4),
                const Text('Compatible RVC v2 ONNX model', style: TextStyle(color: Color(0xFF9999A4), fontSize: 12)),
              ],
            ),
          ),
          const SizedBox(height: 18),
          Text(_status, style: const TextStyle(color: Color(0xFFD0D0D8))),
          const SizedBox(height: 10),
          LinearProgressIndicator(value: _busy ? (_progress > 0 ? _progress : null) : _progress),
          const SizedBox(height: 18),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _busy || _inputPath == null ? null : _createCover,
              icon: _busy
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.auto_awesome),
              label: Text(_busy ? 'PROCESSING LOCALLY…' : 'CREATE SONG COVER'),
            ),
          ),
          if (_outputPath != null) ...[
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () => _player.play(DeviceFileSource(_outputPath!)),
              icon: const Icon(Icons.play_arrow),
              label: const Text('PLAY RESULT'),
            ),
            OutlinedButton.icon(
              onPressed: _saveCover,
              icon: const Icon(Icons.save_alt),
              label: const Text('SAVE SONG COVER'),
            ),
          ],
          const SizedBox(height: 16),
          const Text(
            'Note: the first release uses the bundled Spleeter 2-stem model and 16-bit PCM WAV decoding. The Galaxy A12 still needs physical-device testing for memory use, speed and heat before this feature can be certified on that handset.',
            style: TextStyle(color: Color(0xFF92929D), fontSize: 12, height: 1.4),
          ),
        ],
      ),
    );
  }

  Widget _panel({required Widget child}) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF19151B), Color(0xFF111319)],
          ),
          borderRadius: BorderRadius.circular(19),
          border: Border.all(color: const Color(0xFF3A2931)),
          boxShadow: const [BoxShadow(color: Color(0x18000000), blurRadius: 16, offset: Offset(0, 7))],
        ),
        child: child,
      );
}
