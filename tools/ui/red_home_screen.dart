import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class RedHomeScreen extends StatelessWidget {
  final VoidCallback onGenerate, onSongCovers, onRealtime, onVoiceChanger, onModels, onTrain, onAudioTools, onSettings, onFullRvc;
  const RedHomeScreen({super.key, required this.onGenerate, required this.onSongCovers, required this.onRealtime, required this.onVoiceChanger, required this.onModels, required this.onTrain, required this.onAudioTools, required this.onSettings, required this.onFullRvc});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF07070A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF09090D),
        elevation: 0,
        title: const Text("RED'S ULTIMATE RVC ❤️", style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: .3)),
        centerTitle: true,
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 30),
          children: [
            Container(
              padding: const EdgeInsets.fromLTRB(18, 18, 18, 20),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(26),
                border: Border.all(color: const Color(0xFFE00022).withOpacity(.65), width: 1.2),
                gradient: const LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: [Color(0xFF300009), Color(0xFF0D0D13), Color(0xFF07070A)]),
                boxShadow: const [BoxShadow(color: Color(0x66000000), blurRadius: 24, offset: Offset(0, 12))],
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                SizedBox(height: 112, width: double.infinity, child: SvgPicture.asset('assets/images/reds-ultimate-rvc-logo.svg', fit: BoxFit.contain, alignment: Alignment.centerLeft)),
                const SizedBox(height: 8),
                const Text("RED'S ULTIMATE RVC ❤️🎧🎤", style: TextStyle(fontSize: 23, fontWeight: FontWeight.w900)),
                const SizedBox(height: 6),
                const Text('Your complete voice studio — built for your Android phone.', style: TextStyle(color: Color(0xFFC8C8D1), height: 1.3)),
                const SizedBox(height: 14),
                Row(children: const [Icon(Icons.lock_outline, size: 17, color: Color(0xFF67E38D)), SizedBox(width: 7), Text('PHONE • PRIVATE • READY TO CREATE', style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.w900, letterSpacing: .7))]),
              ]),
            ),
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.all(15),
              decoration: BoxDecoration(borderRadius: BorderRadius.circular(19), color: const Color(0xFF121218), border: Border.all(color: const Color(0xFF3A171D))),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('❤️ This Project Created With Love 💯❤️ By LittleRedBigSmile', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 12.5)),
                const SizedBox(height: 7),
                const Text('Full RVC mode is available inside the app for source RVC models and the complete conversion workflow.', style: TextStyle(color: Color(0xFF9F9FAA), fontSize: 11.5, height: 1.3)),
                const SizedBox(height: 11),
                SizedBox(width: double.infinity, child: ElevatedButton.icon(onPressed: onFullRvc, icon: const Icon(Icons.open_in_new, size: 18), label: const Text('OPEN FULL RVC ENGINE'))),
              ]),
            ),
            const SizedBox(height: 18),
            _section('CREATE & CONVERT'),
            _grid([
              _Action(Icons.graphic_eq, 'CONVERT AUDIO', 'Voice conversion with full RVC controls', onGenerate),
              _Action(Icons.music_video, 'SONG COVERS', 'Full-length songs and finished output', onSongCovers),
              _Action(Icons.settings_voice, 'REALTIME RVC', 'Live microphone conversion', onRealtime),
              _Action(Icons.record_voice_over, 'VOICE CHANGER', 'Record through the selected voice', onVoiceChanger),
            ]),
            const SizedBox(height: 16),
            _section('VOICES & TOOLS'),
            _grid([
              _Action(Icons.library_music, 'MODEL LIBRARY', 'Import and manage voices', onModels),
              _Action(Icons.model_training, 'TRAIN / CREATE VOICE', 'Prepare and manage voice datasets', onTrain),
              _Action(Icons.tune, 'AUDIO TOOLS', 'Indexes, pitch and level tools', onAudioTools),
              _Action(Icons.settings, 'RVC CONTROLS', 'Pitch, F0, index, RMS and protection', onSettings),
            ]),
            const SizedBox(height: 18),
            const Text('Everything shown here stays inside the app. Phone-local conversion is used whenever the selected model is mobile-ready; the Full RVC Engine is also contained inside this app window for source-model workflows.', style: TextStyle(color: Color(0xFF8F8F9A), fontSize: 11.5, height: 1.35)),
          ],
        ),
      ),
    );
  }

  Widget _section(String title) => Padding(padding: const EdgeInsets.only(left: 3, bottom: 9), child: Text(title, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w900, letterSpacing: 1.25, color: Color(0xFFFF334F))));
  Widget _grid(List<_Action> actions) => GridView.count(crossAxisCount: 2, shrinkWrap: true, physics: const NeverScrollableScrollPhysics(), mainAxisSpacing: 10, crossAxisSpacing: 10, childAspectRatio: 1.34, children: actions);
}

class _Action extends StatelessWidget {
  final IconData icon; final String title; final String subtitle; final VoidCallback onTap;
  const _Action(this.icon, this.title, this.subtitle, this.onTap);
  @override
  Widget build(BuildContext context) => Material(
    color: const Color(0xFF111117),
    borderRadius: BorderRadius.circular(20),
    child: InkWell(
      borderRadius: BorderRadius.circular(20), onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(13),
        decoration: BoxDecoration(borderRadius: BorderRadius.circular(20), border: Border.all(color: const Color(0xFF292932))),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [
          Container(width: 42, height: 42, decoration: BoxDecoration(color: const Color(0x22FF334F), borderRadius: BorderRadius.circular(13)), child: Icon(icon, color: const Color(0xFFFF334F), size: 23)),
          const SizedBox(height: 9),
          Text(title, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 12.5)),
          const SizedBox(height: 4),
          Text(subtitle, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Color(0xFF92929D), fontSize: 10.5, height: 1.2)),
        ]),
      ),
    ),
  );
}
