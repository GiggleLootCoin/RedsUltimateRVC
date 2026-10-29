import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

class FullRvcScreen extends StatefulWidget {
  const FullRvcScreen({super.key});
  @override State<FullRvcScreen> createState() => _FullRvcScreenState();
}

class _FullRvcScreenState extends State<FullRvcScreen> {
  late final WebViewController _controller;
  bool _loading = true;
  static const String _url = 'https://hf.co/spaces/Giggle-Loot/RedsUltimateRVC';

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0xFF07070A))
      ..setNavigationDelegate(NavigationDelegate(
        onPageStarted: (_) { if (mounted) setState(() => _loading = true); },
        onPageFinished: (_) { if (mounted) setState(() => _loading = false); },
        onWebResourceError: (error) {
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('FULL RVC ENGINE: ' + error.description)));
        },
      ))
      ..loadRequest(Uri.parse(_url));
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: const Color(0xFF07070A),
    appBar: AppBar(title: const Text("RED'S ULTIMATE RVC ❤️ — FULL ENGINE"), actions: [
      IconButton(onPressed: () => _controller.reload(), icon: const Icon(Icons.refresh), tooltip: 'Reload engine'),
    ]),
    body: Stack(children: [WebViewWidget(controller: _controller), if (_loading) const LinearProgressIndicator(minHeight: 3)]),
  );
}