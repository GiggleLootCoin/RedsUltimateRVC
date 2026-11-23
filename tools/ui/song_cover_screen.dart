import 'dart:io';
import 'dart:convert';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/rvc_bridge.dart';

/// Fully local song-cover workflow: separate the original, convert the vocal
/// stem with a compatible ONNX or native RVC v2 PTH model, then mix it back.
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
  String? _vocalsPath;
  String? _accompanimentPath;
  String _status = 'Choose a song to begin.';
  double _progress = 0;
  double _indexRate = 0.75;
  bool _busy = false;

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  Future<void> _pickSong() async {
    if (_busy) return;
    try {
      // Use Android's native Storage Access Framework. The Flutter file picker
      // can return null filesystem paths for Samsung My Files content:// URIs.
      final importedFiles = await _bridge.pickAndImportAudioFiles();
      if (importedFiles.isEmpty) return;
      final imported = importedFiles.first;
      // This screen uses one source song. Release any additional selections so
      // their temporary import references do not remain pinned in storage.
      for (final extra in importedFiles.skip(1)) {
        await _bridge.releaseImportedFile(extra.path);
      }
      if (!mounted) return;
      setState(() {
        _inputPath = imported.path;
        _inputName = File(imported.path).uri.pathSegments.last;
        _outputPath = null;
        _vocalsPath = null;
        _accompanimentPath = null;
        _progress = 0;
        _status = 'Audio imported into the app. Ready to separate vocals.';
      });
    } catch (e) {
      if (mounted) _message('Could not import that audio file: $e');
    }
  }

  Future<Map<String, String>> _getOrCreateStems(String inputPath) async {
    final source = File(inputPath);
    final stat = await source.stat();
    final encodedPath = base64Url.encode(utf8.encode(source.absolute.path)).replaceAll('=', '');
    final cacheKey = 'rvc_song_stems_${encodedPath}_${stat.size}_${stat.modified.millisecondsSinceEpoch}';
    final prefs = await SharedPreferences.getInstance();
    final cachedVocals = prefs.getString('${cacheKey}_vocals');
    final cachedBacking = prefs.getString('${cacheKey}_backing');
    if (cachedVocals != null && cachedBacking != null &&
        await File(cachedVocals).exists() && await File(cachedBacking).exists()) {
      if (mounted) setState(() => _status = 'Reusing cached vocal and backing stems…');
      return {'vocalsPath': cachedVocals, 'accompanimentPath': cachedBacking};
    }

    final stems = await _bridge.separateSongVocals(inputPath);
    final vocals = stems['vocalsPath'];
    final backing = stems['accompanimentPath'];
    if (vocals == null || backing == null ||
        !await File(vocals).exists() || !await File(backing).exists()) {
      throw StateError('Vocal separation did not produce both usable audio stems.');
    }
    await prefs.setString('${cacheKey}_vocals', vocals);
    await prefs.setString('${cacheKey}_backing', backing);
    return {'vocalsPath': vocals, 'accompanimentPath': backing};
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
      final stems = await _getOrCreateStems(_inputPath!);
      final vocalsPath = stems['vocalsPath']!;
      final accompanimentPath = stems['accompanimentPath']!;
      if (!mounted) return;
      setState(() {
        _vocalsPath = vocalsPath;
        _accompanimentPath = accompanimentPath;
        _status = 'Vocal and accompaniment stems are ready. Converting the isolated vocals…';
      });

      final isPth = widget.modelPath.toLowerCase().endsWith('.pth');
      final String convertedVocals;
      if (isPth) {
        convertedVocals = await _bridge.convertPth(
          inputWavPath: vocalsPath,
          pthModelPath: widget.modelPath,
          indexPath: widget.indexPath,
          indexRate: _indexRate,
        );
      } else {
        convertedVocals = await _bridge.infer(
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
      }

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
        setState(() => _status = 'Song-cover creation failed: $e');
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
        title: const Text("RED'S SONG COVERS"),
        backgroundColor: const Color(0xFF09090D),
      ),
      body: ListView(
        padding: const EdgeInsets.all(18),
        children: [
          const Text(
            'MAKE A LOCAL RVC SONG COVER',
            style: TextStyle(fontSize: 21, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 9),
          const Text(
            'Choose an audio file. Android decodes it locally to PCM WAV, then the app separates vocals and accompaniment, converts the vocals with your selected ONNX or supported RVC v2 PTH voice, and mixes them back with the original music. Processing stays on this phone.',
            style: TextStyle(color: Color(0xFFBEBEC7), height: 1.45),
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
                Text(widget.modelPath.toLowerCase().endsWith('.pth') ? 'Native RVC v2 PTH • 768 dimensions / 100 fps only' : 'Compatible RVC v2 ONNX model', style: const TextStyle(color: Color(0xFF9999A4), fontSize: 12)),
              ],
            ),
          ),
          if (widget.modelPath.toLowerCase().endsWith('.pth')) ...[
            const SizedBox(height: 10),
            _panel(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('NATIVE RVC CONVERTER', style: TextStyle(color: Color(0xFFFF405B), fontWeight: FontWeight.w900)),
                const SizedBox(height: 7),
                Text(
                  widget.indexPath == null
                      ? 'Direct on-device PTH conversion is active. No ONNX export is required. Add the matching standard FAISS .index in Voice Library to enable retrieval blending.'
                      : 'Direct on-device PTH conversion with FAISS retrieval search and blending. The original .index is read locally; the voice model and song are not uploaded.',
                  style: const TextStyle(color: Color(0xFFD0D0D8), height: 1.4),
                ),
                if (widget.indexPath != null) ...[
                  const SizedBox(height: 12),
                  Text('RETRIEVAL STRENGTH  ${(_indexRate * 100).round()}%', style: const TextStyle(color: Color(0xFFFFA3AE), fontWeight: FontWeight.w800)),
                  Slider(
                    value: _indexRate,
                    min: 0,
                    max: 1,
                    divisions: 20,
                    activeColor: const Color(0xFFFF3654),
                    onChanged: _busy ? null : (value) => setState(() => _indexRate = value),
                  ),
                  const Text('Lower values preserve more of the original vocal features; higher values lean more strongly on the voice index.', style: TextStyle(color: Color(0xFFAAAAB5), fontSize: 11, height: 1.35)),
                ],
              ]),
            ),
          ],
          if (_vocalsPath != null && _accompanimentPath != null) ...[
            _panel(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('INTERMEDIATE STEMS', style: TextStyle(color: Color(0xFFFF405B), fontWeight: FontWeight.w900)),
                const SizedBox(height: 8),
                const Text('Listen to the separated parts before or after conversion.'),
                const SizedBox(height: 10),
                Row(children: [
                  Expanded(child: OutlinedButton.icon(
                    onPressed: _busy ? null : () => _player.play(DeviceFileSource(_vocalsPath!)),
                    icon: const Icon(Icons.mic), label: const Text('PLAY VOCALS'),
                  )),
                  const SizedBox(width: 8),
                  Expanded(child: OutlinedButton.icon(
                    onPressed: _busy ? null : () => _player.play(DeviceFileSource(_accompanimentPath!)),
                    icon: const Icon(Icons.music_note), label: const Text('PLAY BACKING'),
                  )),
                ]),
              ]),
            ),
            const SizedBox(height: 12),
          ],
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
          color: const Color(0xFF131319),
          borderRadius: BorderRadius.circular(17),
          border: Border.all(color: const Color(0xFF30232A)),
        ),
        child: child,
      );
}
