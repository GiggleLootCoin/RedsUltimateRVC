import 'package:flutter/material.dart';

/// Honest index compatibility guide. This screen does not pretend to convert
/// FAISS files: the bundled Android inference engine reads mobile feature tables.
class IndexConverterScreen extends StatelessWidget {
  const IndexConverterScreen({super.key});

  static const _red = Color(0xFFFF334F);
  static const _panel = Color(0xFF121218);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF07070A),
      appBar: AppBar(
        title: const Text('INDEX TOOLS'),
        centerTitle: true,
        backgroundColor: const Color(0xFF09090D),
      ),
      body: ListView(
        padding: const EdgeInsets.all(18),
        children: [
          const Icon(Icons.storage_rounded, color: _red, size: 54),
          const SizedBox(height: 14),
          const Text(
            'MOBILE INDEX COMPATIBILITY',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 10),
          _info(
            'SUPPORTED ON THIS PHONE',
            'A compatible .mobile.index feature table. Choose it in the optional Index field on the audio conversion screen.',
          ),
          _info(
            'STANDARD .index FILES',
            'Standard RVC/FAISS .index files are not converted by this Android app yet. Importing or renaming one does not make it compatible.',
          ),
          _info(
            'WHAT IS STILL NEEDED',
            'A tested Android-compatible FAISS reader and converter is required before standard .index conversion can be offered directly on this phone.',
          ),
          _info(
            'FORMAT CHECK',
            'The inference engine checks the mobile index header, feature count and data length before using it. Invalid or incomplete files should be rejected.',
          ),
          const SizedBox(height: 8),
          const Text(
            'No model or audio file is uploaded from this screen.',
            style: TextStyle(color: Color(0xFFB7B7C1), height: 1.4),
          ),
        ],
      ),
    );
  }

  static Widget _info(String title, String body) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _panel,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF382027)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(
            color: _red, fontWeight: FontWeight.w900, letterSpacing: .5,
          )),
          const SizedBox(height: 7),
          Text(body, style: const TextStyle(
            color: Color(0xFFD0D0D8), height: 1.4,
          )),
        ],
      ),
    );
  }
}
