import 'package:flutter/material.dart';

class FullRvcScreen extends StatelessWidget {
  final VoidCallback onConvert;
  final VoidCallback onModels;
  final VoidCallback onRealtime;
  final VoidCallback onVoiceChanger;
  final VoidCallback onTraining;
  final VoidCallback onIndexTools;

  const FullRvcScreen({
    super.key,
    required this.onConvert,
    required this.onModels,
    required this.onRealtime,
    required this.onVoiceChanger,
    required this.onTraining,
    required this.onIndexTools,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF07070A),
      appBar: AppBar(
        title: const Text("RED'S ULTIMATE RVC ❤️"),
        centerTitle: true,
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 30),
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(24),
              gradient: const LinearGradient(
                colors: [Color(0xFF310009), Color(0xFF101015)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              border: Border.all(color: Color(0x66FF334F)),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("FULL PHONE WORKSPACE", style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
                SizedBox(height: 8),
                Text(
                  "All supported RVC work is kept inside the Android app. No Kaggle, Colab or cloud inference is required for mobile-ready ONNX conversion.",
                  style: TextStyle(color: Color(0xFFC8C8D1), height: 1.35),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _button(Icons.graphic_eq, "AUDIO CONVERSION", "Convert audio with the local RVC engine.", onConvert),
          _button(Icons.library_music, "MODEL LIBRARY", "Import ONNX, PTH, PT and ZIP source models.", onModels),
          _button(Icons.settings_voice, "REALTIME RVC", "Use the local realtime voice-conversion engine.", onRealtime),
          _button(Icons.record_voice_over, "VOICE CHANGER", "Record and process through the selected voice.", onVoiceChanger),
          _button(Icons.sync_alt, "INDEX TOOLS", "Manage mobile index files and conversion tools.", onIndexTools),
          _button(Icons.model_training, "TRAIN / CREATE VOICE", "Build and manage training data directly on the phone.", onTraining),
          const SizedBox(height: 10),
          const Card(
            color: Color(0xFF111117),
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                "Important: importing a standard RVC .pth model is supported for storage, but the bundled Android inference engine runs ONNX voice models. A true RVC trainer is a separate neural-network training engine and is not present in the upstream mobile engine. This app will never claim a model was trained when it was not.",
                style: TextStyle(color: Color(0xFFAAAAB5), height: 1.35, fontSize: 12.5),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _button(IconData icon, String title, String subtitle, VoidCallback onTap) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Material(
        color: const Color(0xFF111117),
        borderRadius: BorderRadius.circular(18),
        child: InkWell(
          borderRadius: BorderRadius.circular(18),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: const Color(0x22FF334F),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Icon(icon, color: const Color(0xFFFF334F)),
                ),
                const SizedBox(width: 13),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),
                      const SizedBox(height: 4),
                      Text(subtitle, style: const TextStyle(color: Color(0xFF92929D), fontSize: 11.5)),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right, color: Color(0xFF777780)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
