import 'package:flutter/material.dart';
import '../services/rvc_bridge.dart';

class IndexConverterScreen extends StatefulWidget {
  const IndexConverterScreen({super.key});

  @override
  State<IndexConverterScreen> createState() => _IndexConverterScreenState();
}

class _IndexConverterScreenState extends State<IndexConverterScreen> {
  final RVCBridge _bridge = RVCBridge();
  bool _busy = false;
  String _status = 'Choose a standard RVC .index file or an existing .mobile.index file.';

  Future<void> _convert() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _status = 'Open your phone files and choose an index…';
    });
    try {
      final imported = await _bridge.pickAndImportFile(kind: 'index');
      if (imported == null) return;
      final lower = imported.path.toLowerCase();
      if (lower.endsWith('.mobile.index')) {
        await _bridge.convertIndex(imported.path);
        if (mounted) {
          setState(() => _status =
              'This mobile index passed validation and is already in your index library. Select it under Models → Index.');
        }
      } else if (lower.endsWith('.index')) {
        setState(() => _status =
            'Converting locally with FAISS. Large indexes can take a while; keep Red’s Ultimate RVC open.');
        final converted = await _bridge.convertFaissIndex(imported.path);
        if (mounted) {
          final name = converted.path.split('/').last;
          setState(() => _status =
              'Conversion complete. $name has been added to your index library. Select it under Models → Index.');
        }
      } else {
        throw Exception('Choose a standard .index or .mobile.index file.');
      }
    } catch (error) {
      if (mounted) setState(() => _status = 'Conversion failed: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    const red = Color(0xFFE00022);
    return Scaffold(
      backgroundColor: const Color(0xFF08080C),
      appBar: AppBar(
        title: const Text('INDEX CONVERTER'),
        backgroundColor: const Color(0xFF101016),
        foregroundColor: Colors.white,
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(18),
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(22),
                gradient: const LinearGradient(
                  colors: [Color(0xFF290008), Color(0xFF121218)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                border: Border.all(color: red.withOpacity(.55)),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.hub_outlined, color: Color(0xFFFF405B), size: 34),
                  SizedBox(height: 12),
                  Text('Convert FAISS indexes on your phone',
                    style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w900)),
                  SizedBox(height: 8),
                  Text(
                    'A standard desktop .index file is not the same as the mobile format. This tool converts compatible 768-dimensional RVC v2 FAISS indexes into .mobile.index and adds the result to your model library.',
                    style: TextStyle(color: Color(0xFFD0D0D8), height: 1.4),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF14141B),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFF30303A)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.privacy_tip_outlined, color: Color(0xFF73D69A)),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Private and offline: conversion runs locally. Your index file is not uploaded. Keep enough free storage for the converted copy.',
                      style: TextStyle(color: Colors.white.withOpacity(.86), height: 1.35),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _busy ? null : _convert,
              icon: _busy
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.transform),
              label: Text(_busy ? 'WORKING…' : 'SELECT & CONVERT INDEX'),
              style: FilledButton.styleFrom(
                backgroundColor: red,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF101016),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF292932)),
              ),
              child: Text(_status,
                style: const TextStyle(color: Colors.white, height: 1.4)),
            ),
            const SizedBox(height: 14),
            const Text(
              'Compatibility note: this tool creates the .mobile.index copy used by ONNX inference and keeps the imported original .index in your local model library. Native PTH conversion uses that original FAISS index for retrieval blending. If you import only a .mobile.index from elsewhere, also import its original .index to enable native PTH retrieval.',
              style: TextStyle(color: Color(0xFFAAAAB6), height: 1.4, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}
