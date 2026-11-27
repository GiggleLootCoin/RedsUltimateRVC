import 'package:flutter/material.dart';

/// Honest capability screen: no remote website or fake local conversion.
class ModelConverterScreen extends StatelessWidget {
  const ModelConverterScreen({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: const Color(0xFF07070A),
    appBar: AppBar(title: const Text("RED'S ULTIMATE RVC — PTH COMPATIBILITY"), centerTitle: true),
    body: ListView(padding: const EdgeInsets.all(18), children: [
      const Icon(Icons.transform, size: 54, color: Color(0xFFFF334F)),
      const SizedBox(height: 16),
      const Text('NATIVE PTH VOICE SUPPORT', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
      const SizedBox(height: 10),
      const Text(
        'Supported RVC v2 .pth voice checkpoints run directly through the native Android converter. No ONNX voice-model export, upload or intermediate conversion is required. The supported profile is 768-dimensional ContentVec features at 100 fps.',
        style: TextStyle(height: 1.45),
      ),
      const SizedBox(height: 14),
      const Text(
        'The native converter validates the checkpoint before processing. If a checkpoint is incompatible, the app reports the reason instead of asking you to export it as ONNX.',
        style: TextStyle(color: Color(0xFFB7B7C1), height: 1.4),
      ),
    ]),
  );
}
