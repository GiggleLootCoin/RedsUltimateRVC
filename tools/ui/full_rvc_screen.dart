import 'package:flutter/material.dart';

class FullRvcScreen extends StatelessWidget {
  final VoidCallback onConvert, onModels, onRealtime, onVoiceChanger, onTraining, onIndexTools;
  const FullRvcScreen({
    super.key, required this.onConvert, required this.onModels, required this.onRealtime,
    required this.onVoiceChanger, required this.onTraining, required this.onIndexTools,
  });

  static const _bg = Color(0xFF08090D);
  static const _red = Color(0xFFFF3654);
  static const _muted = Color(0xFFA5A8B2);

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: _bg,
    appBar: AppBar(
      backgroundColor: _bg, surfaceTintColor: Colors.transparent, elevation: 0,
      title: const Text("RVC WORKSPACE", style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900, letterSpacing: 1.1)),
      centerTitle: false,
    ),
    body: SafeArea(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 28),
        children: [
          Container(
            padding: const EdgeInsets.all(19),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(23),
              gradient: const LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight,
                colors: [Color(0xFF39101C), Color(0xFF17131A), Color(0xFF10131A)]),
              border: Border.all(color: const Color(0x77FF3654)),
            ),
            child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('VOICE PRODUCTION', style: TextStyle(color: Color(0xFFFF8798), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1.8)),
              SizedBox(height: 8),
              Text('The RVC workspace', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: -.5)),
              SizedBox(height: 7),
              Text('Choose a tool to convert audio, manage compatible voices or prepare your own dataset.',
                style: TextStyle(color: Color(0xFFC2C1CA), height: 1.4, fontSize: 12.5)),
            ]),
          ),
          const SizedBox(height: 20),
          const Text('CONVERSION', style: TextStyle(color: _red, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.6)),
          const SizedBox(height: 9),
          _Tool(Icons.graphic_eq_rounded, 'Audio conversion', 'Run local inference with a compatible ONNX voice model.', onConvert, primary: true),
          _Tool(Icons.record_voice_over_rounded, 'Voice changer', 'Record and process audio through the selected voice.', onVoiceChanger),
          _Tool(Icons.bolt_rounded, 'Realtime RVC', 'Experimental live conversion; audio routing and speed may vary.', onRealtime, caution: true),
          const SizedBox(height: 19),
          const Text('VOICE LIBRARY', style: TextStyle(color: _red, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.6)),
          const SizedBox(height: 9),
          _Tool(Icons.library_music_rounded, 'Manage voice models', 'Import and organise ONNX models and source files.', onModels),
          _Tool(Icons.folder_open_rounded, 'Dataset lab', 'Record, inspect and export voice samples. This does not train a model.', onTraining),
          _Tool(Icons.tune_rounded, 'Mobile index tools', 'Validate compatible mobile feature-table index files.', onIndexTools),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFF12151B), borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFF30333C)),
            ),
            child: const Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Icon(Icons.verified_user_outlined, color: Color(0xFF72DFA0), size: 18),
              SizedBox(width: 10),
              Expanded(child: Text(
                'Local-first: compatible ONNX conversion runs on this phone. Standard .pth/.pt conversion, neural-network training and vocal separation are not included in this release. The app will clearly identify these limitations rather than report simulated results.',
                style: TextStyle(color: Color(0xFFB9BDC7), fontSize: 11.2, height: 1.45),
              )),
            ]),
          ),
        ],
      ),
    ),
  );
}

class _Tool extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  final bool primary;
  final bool caution;
  const _Tool(this.icon, this.title, this.subtitle, this.onTap, {this.primary = false, this.caution = false});

  @override
  Widget build(BuildContext context) {
    final color = caution ? const Color(0xFFFFB45F) : const Color(0xFFFF3654);
    return Padding(
      padding: const EdgeInsets.only(bottom: 9),
      child: Material(
        color: const Color(0xFF12151B),
        borderRadius: BorderRadius.circular(17),
        child: InkWell(
          borderRadius: BorderRadius.circular(17), onTap: onTap,
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(17),
              border: Border.all(color: primary ? const Color(0x887C2639) : const Color(0xFF2B3039)),
              gradient: primary ? const LinearGradient(colors: [Color(0xFF24131A), Color(0xFF12151B)]) : null,
            ),
            child: Row(children: [
              Container(
                width: 43, height: 43,
                decoration: BoxDecoration(color: color.withOpacity(.12), borderRadius: BorderRadius.circular(13)),
                child: Icon(icon, color: color, size: 22),
              ),
              const SizedBox(width: 13),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w900)),
                const SizedBox(height: 4),
                Text(subtitle, style: const TextStyle(color: const Color(0xFFA5A8B2), fontSize: 10.8, height: 1.3)),
              ])),
              const SizedBox(width: 7),
              const Icon(Icons.chevron_right_rounded, color: Color(0xFF737782)),
            ]),
          ),
        ),
      ),
    );
  }
}
