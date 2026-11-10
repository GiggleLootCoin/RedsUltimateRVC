import 'package:flutter/material.dart';

/// Capability disclosure for the ONNX-free native RVC migration.
/// This screen deliberately does not offer a fake extension rename or upload.
class ModelConverterScreen extends StatelessWidget {
  const ModelConverterScreen({super.key});

  static const _red = Color(0xFFFF334F);
  static const _muted = Color(0xFFB7B7C1);

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: const Color(0xFF07070A),
    appBar: AppBar(
      title: const Text("RED'S ULTIMATE RVC — NATIVE MODEL ENGINE"),
      centerTitle: true,
      backgroundColor: const Color(0xFF09090D),
    ),
    body: ListView(
      padding: const EdgeInsets.all(18),
      children: [
        const Icon(Icons.memory_rounded, size: 56, color: _red),
        const SizedBox(height: 16),
        const Text(
          'REAL .PTH CHECKPOINT SUPPORT',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
        ),
        const SizedBox(height: 10),
        const Text(
          'The target engine is designed to load genuine RVC .pth/.pt checkpoints directly. ONNX is not the intended model format and renaming a checkpoint will never convert it.',
          style: TextStyle(height: 1.45),
        ),
        const SizedBox(height: 18),
        _section(
          'CURRENT DEVELOPMENT STATUS',
          'The ONNX-free Android inference backend is not integrated yet. This screen does not claim that a selected checkpoint can already be converted or run.',
        ),
        _section(
          'WHY THIS TAKES MORE THAN A FILE PICKER',
          'A checkpoint contains learned weights, not a complete executable voice-conversion engine. The app still needs compatible implementations of content-feature extraction, pitch estimation, the RVC network, audio decoding and optional retrieval.',
        ),
        _section(
          'ON-DEVICE AND PRIVATE',
          'The intended workflow keeps your voice model and recordings on your phone. No third-party upload or paid conversion service is part of the plan.',
        ),
        _section(
          'WHAT WILL UNLOCK CONVERSION',
          'A validated native Android runtime must load a real RVC v2 checkpoint, process a test recording and produce measurably converted speech. Until those tests pass, conversion remains unavailable rather than pretending to work.',
        ),
        const SizedBox(height: 8),
        const Text(
          'No ONNX export is being requested here. This migration is being developed separately so the existing build remains available as a baseline.',
          style: TextStyle(color: _muted, height: 1.4),
        ),
      ],
    ),
  );

  static Widget _section(String title, String body) => Container(
    margin: const EdgeInsets.only(bottom: 12),
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: const Color(0xFF121218),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: const Color(0xFF382027)),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(
          color: _red, fontWeight: FontWeight.w900, letterSpacing: .4,
        )),
        const SizedBox(height: 7),
        Text(body, style: const TextStyle(color: Color(0xFFD0D0D8), height: 1.4)),
      ],
    ),
  );
}
