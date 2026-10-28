import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class RedHomeScreen extends StatelessWidget {
  final VoidCallback onGenerate, onSongCovers, onSpeech, onModels, onUploadDownload, onTrain, onAudio, onSettings;
  const RedHomeScreen({super.key, required this.onGenerate, required this.onSongCovers, required this.onSpeech, required this.onModels, required this.onUploadDownload, required this.onTrain, required this.onAudio, required this.onSettings});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("RED'S ULTIMATE RVC ❤️"), centerTitle: true),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(22),
              border: Border.all(color: Colors.redAccent.withOpacity(.55)),
              gradient: const LinearGradient(colors: [Color(0xFF180007), Color(0xFF09090D)]),
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              SizedBox(height: 92, child: SvgPicture.asset("assets/images/reds-ultimate-rvc-logo.svg", fit: BoxFit.contain, alignment: Alignment.centerLeft)),
              const SizedBox(height: 10),
              const Text("RED'S ULTIMATE RVC", style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
              SizedBox(height: 7),
              Text('Your voice. Your sound. Local Android voice conversion.', style: TextStyle(color: Color(0xFFCACAD2))),
            ]),
          ),
          const SizedBox(height: 16),
          GridView.count(
            crossAxisCount: 2, shrinkWrap: true, physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 10, crossAxisSpacing: 10, childAspectRatio: 1.55,
            children: [
              _button(Icons.auto_awesome, 'GENERATE', onGenerate),
              _button(Icons.music_video, 'SONG COVERS', onSongCovers),
              _button(Icons.record_voice_over, 'SPEECH', onSpeech),
              _button(Icons.library_music, 'MODELS', onModels),
              _button(Icons.upload_file, 'UPLOAD / DOWNLOAD', onUploadDownload),
              _button(Icons.model_training, 'TRAIN / CREATE MODEL', onTrain),
              _button(Icons.audiotrack, 'AUDIO', onAudio),
              _button(Icons.settings, 'SETTINGS', onSettings),
            ],
          ),
        ],
      ),
    );
  }

  Widget _button(IconData icon, String label, VoidCallback action) => ElevatedButton(
    onPressed: action,
    style: ElevatedButton.styleFrom(shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18))),
    child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
      Icon(icon, size: 28), const SizedBox(height: 6),
      Text(label, textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 12)),
    ]),
  );
}
