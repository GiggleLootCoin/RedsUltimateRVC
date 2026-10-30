import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

class ModelConverterScreen extends StatefulWidget {
  const ModelConverterScreen({super.key});

  @override
  State<ModelConverterScreen> createState() => _ModelConverterScreenState();
}

class _ModelConverterScreenState extends State<ModelConverterScreen> {
  late final WebViewController _web;

  @override
  void initState() {
    super.initState();
    _web = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(NavigationDelegate(
        onWebResourceError: (e) {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Converter page error: ${e.description}')),
            );
          }
        },
      ))
      ..loadRequest(Uri.parse('https://voicechanger.live/tools/model-converter'));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("RED'S ULTIMATE RVC — PTH → ONNX"), centerTitle: true),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
            color: const Color(0xFF111117),
            child: const Text(
              'This converter stays inside Red’s Ultimate RVC. PTH conversion runs locally in the browser engine; your model is not uploaded. After saving the ONNX file, return to Model Library and import it.',
              style: TextStyle(fontSize: 11.5, color: Color(0xFFC0C0C9), height: 1.35),
            ),
          ),
          Expanded(child: WebViewWidget(controller: _web)),
        ],
      ),
    );
  }
}
