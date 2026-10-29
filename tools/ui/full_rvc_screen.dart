import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

class FullRvcScreen extends StatefulWidget {
  final String url;
  final String title;
  const FullRvcScreen({super.key, this.url = 'https://hf.co/spaces/Giggle-Loot/RedsUltimateRVC', this.title = "RED'S ULTIMATE RVC ❤️ — FULL ENGINE"});
  @override State<FullRvcScreen> createState() => _FullRvcScreenState();
}

class _FullRvcScreenState extends State<FullRvcScreen> {
  late final WebViewController _controller;
  bool _loading = true;
  
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
      ..loadRequest(Uri.parse(widget.url));
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: const Color(0xFF07070A),
    appBar: AppBar(title: Text(widget.title), actions: [
      IconButton(onPressed: () => _controller.reload(), icon: const Icon(Icons.refresh), tooltip: 'Reload engine'),
    ]),
    body: Stack(children: [WebViewWidget(controller: _controller), if (_loading) const LinearProgressIndicator(minHeight: 3)]),
  );
}