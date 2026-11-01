import 'package:flutter/material.dart';

/// Honest capability screen: no remote website or fake local conversion.
class ModelConverterScreen extends StatelessWidget {
  const ModelConverterScreen({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: const Color(0xFF07070A),
    appBar: AppBar(title: const Text("RED'S ULTIMATE RVC — MODEL CONVERSION"), centerTitle: true),
    body: ListView(padding: const EdgeInsets.all(18), children: [
      const Icon(Icons.transform, size: 54, color: Color(0xFFFF334F)),
      const SizedBox(height: 16),
      const Text('PTH → ONNX CONVERSION', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
      const SizedBox(height: 10),
      const Text(
        'This Android build does not yet contain a local PTH-to-ONNX conversion engine. A .pth file can be stored in Model Library, but it cannot be run by the bundled ONNX inference engine until converted.',
        style: TextStyle(height: 1.45),
      ),
      const SizedBox(height: 14),
      const Text(
        'No third-party website is opened and no model is uploaded. This screen will only offer conversion once a real on-device converter has been integrated and tested.',
        style: TextStyle(color: Color(0xFFB7B7C1), height: 1.4),
      ),
    ]),
  );
}
