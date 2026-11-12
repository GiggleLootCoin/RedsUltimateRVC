import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class RedHomeScreen extends StatelessWidget {
  final VoidCallback onGenerate, onSongCovers, onRealtime, onVoiceChanger;
  final VoidCallback onModels, onTrain, onAudioTools, onSettings, onFullRvc, onYouTube;

  const RedHomeScreen({
    super.key,
    required this.onGenerate,
    required this.onSongCovers,
    required this.onRealtime,
    required this.onVoiceChanger,
    required this.onModels,
    required this.onTrain,
    required this.onAudioTools,
    required this.onSettings,
    required this.onFullRvc,
    required this.onYouTube,
  });

  static const _bg = Color(0xFF07080B);
  static const _surface = Color(0xFF111319);
  static const _red = Color(0xFFFF2948);
  static const _muted = Color(0xFFA5A8B2);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      appBar: AppBar(
        backgroundColor: _bg,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        titleSpacing: 18,
        title: Row(children: [
          Container(
            width: 34, height: 34,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(11),
              gradient: const LinearGradient(colors: [Color(0xFFFF3654), Color(0xFF8E001D)]),
              boxShadow: const [BoxShadow(color: Color(0x55FF2948), blurRadius: 16)],
            ),
            child: const Icon(Icons.graphic_eq_rounded, color: Colors.white, size: 21),
          ),
          const SizedBox(width: 11),
          const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text("RED'S ULTIMATE RVC", style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900, letterSpacing: .55)),
            SizedBox(height: 2),
            Text('VOICE PRODUCTION STUDIO', style: TextStyle(fontSize: 8, color: _muted, fontWeight: FontWeight.w800, letterSpacing: 1.5)),
          ]),
        ]),
        actions: [
          IconButton(
            tooltip: 'Studio settings',
            onPressed: onSettings,
            icon: const Icon(Icons.tune_rounded, color: Color(0xFFCACBD2)),
          ),
          const SizedBox(width: 7),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 30),
          children: [
            _hero(),
            const SizedBox(height: 22),
            _section('CREATE', 'Transform audio with your voice models'),
            const SizedBox(height: 11),
            _grid([
              _Action(Icons.graphic_eq_rounded, 'Audio conversion', 'Convert audio with a compatible ONNX voice', onGenerate, featured: true),
              _Action(Icons.music_video_rounded, 'Song covers', 'Convert an already-isolated vocal track', onSongCovers),
              _Action(Icons.record_voice_over_rounded, 'Voice changer', 'Record and process through a selected voice', onVoiceChanger),
              _Action(Icons.bolt_rounded, 'Realtime mode', 'Experimental; performance and routing may vary', onRealtime, warning: true),
            ]),
            const SizedBox(height: 22),
            _section('YOUR WORKSPACE', 'Manage models, samples and sound'),
            const SizedBox(height: 11),
            _grid([
              _Action(Icons.library_music_rounded, 'Voice library', 'Import and organise compatible models', onModels),
              _Action(Icons.mic_none_rounded, 'Dataset lab', 'Record, prepare and export voice samples', onTrain),
              _Action(Icons.tune_rounded, 'Audio tools', 'Inspect mobile index files and conversion settings', onAudioTools),
              _Action(Icons.dashboard_customize_rounded, 'Full RVC engine', 'Open the complete conversion workspace', onFullRvc),
            ]),
            const SizedBox(height: 18),
            _capabilityNote(),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: onYouTube,
              icon: const Icon(Icons.play_circle_outline_rounded),
              label: const Text('VISIT LITTLE RED BIG SMILE'),
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.white,
                side: const BorderSide(color: Color(0xFF49303A)),
                padding: const EdgeInsets.symmetric(vertical: 15),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
              ),
            ),
            const SizedBox(height: 12),
            const Center(
              child: Text('CREATED WITH CARE BY LITTLE RED BIG SMILE',
                style: TextStyle(color: Color(0xFF737782), fontSize: 9, fontWeight: FontWeight.w800, letterSpacing: 1.15)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _hero() => Container(
    padding: const EdgeInsets.fromLTRB(18, 18, 18, 17),
    decoration: BoxDecoration(
      borderRadius: BorderRadius.circular(25),
      border: Border.all(color: const Color(0x66FF2948)),
      gradient: const LinearGradient(
        begin: Alignment.topLeft, end: Alignment.bottomRight,
        colors: [Color(0xFF35101A), Color(0xFF171219), Color(0xFF0D1016)],
        stops: [0, .48, 1],
      ),
      boxShadow: const [BoxShadow(color: Color(0x33000000), blurRadius: 24, offset: Offset(0, 12))],
    ),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        Expanded(
          child: SizedBox(
            height: 76,
            child: SvgPicture.asset('assets/images/reds-ultimate-rvc-logo.svg',
              fit: BoxFit.contain, alignment: Alignment.centerLeft),
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
          decoration: BoxDecoration(
            color: const Color(0x2236D98A), borderRadius: BorderRadius.circular(20),
            border: Border.all(color: const Color(0x5536D98A)),
          ),
          child: const Row(children: [
            Icon(Icons.shield_outlined, color: Color(0xFF72E3A5), size: 13),
            SizedBox(width: 5),
            Text('ON-DEVICE', style: TextStyle(color: Color(0xFF9AF0BD), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: .7)),
          ]),
        ),
      ]),
      const SizedBox(height: 13),
      const Text('Your voice. Your sound.\nYour creative studio.',
        style: TextStyle(fontSize: 24, height: 1.12, fontWeight: FontWeight.w900, letterSpacing: -.65)),
      const SizedBox(height: 8),
      const Text('A focused Android workspace for local RVC voice conversion and audio creation.',
        style: TextStyle(color: Color(0xFFC0BFC8), fontSize: 12.5, height: 1.45)),
      const SizedBox(height: 15),
      const Row(children: [
        _HeroTag(Icons.lock_outline_rounded, 'PRIVATE'),
        SizedBox(width: 8),
        _HeroTag(Icons.phone_android_rounded, 'ANDROID'),
        SizedBox(width: 8),
        _HeroTag(Icons.graphic_eq_rounded, 'RVC AUDIO'),
      ]),
    ]),
  );

  Widget _section(String title, String subtitle) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(title, style: const TextStyle(color: _red, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.8)),
      const SizedBox(height: 4),
      Text(subtitle, style: const TextStyle(color: _muted, fontSize: 11.5)),
    ],
  );

  Widget _grid(List<_Action> actions) => GridView.count(
    crossAxisCount: 2, shrinkWrap: true, physics: const NeverScrollableScrollPhysics(),
    mainAxisSpacing: 10, crossAxisSpacing: 10, childAspectRatio: 1.22,
    children: actions,
  );

  Widget _capabilityNote() => Container(
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: _surface, borderRadius: BorderRadius.circular(16),
      border: Border.all(color: const Color(0xFF292D36)),
    ),
    child: const Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Icon(Icons.info_outline_rounded, color: _red, size: 19),
      SizedBox(width: 10),
      Expanded(child: Text(
        'This Android engine runs compatible ONNX voice models. PTH/PT files can be stored, but this build does not perform PTH-to-ONNX conversion or neural-network training. Dataset Lab prepares samples; it does not train a model.',
        style: TextStyle(color: Color(0xFFB7BBC5), fontSize: 11, height: 1.45),
      )),
    ]),
  );
}

class _HeroTag extends StatelessWidget {
  final IconData icon;
  final String label;
  const _HeroTag(this.icon, this.label);
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
    decoration: BoxDecoration(color: const Color(0x22FFFFFF), borderRadius: BorderRadius.circular(20)),
    child: Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(icon, size: 12, color: const Color(0xFFFF8192)),
      const SizedBox(width: 5),
      Text(label, style: const TextStyle(fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: .65)),
    ]),
  );
}

class _Action extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  final bool featured;
  final bool warning;

  const _Action(this.icon, this.title, this.subtitle, this.onTap, {this.featured = false, this.warning = false});

  @override
  Widget build(BuildContext context) {
    final accent = warning ? const Color(0xFFFFB45F) : const Color(0xFFFF3654);
    return Material(
      color: const Color(0xFF11141A),
      borderRadius: BorderRadius.circular(19),
      child: InkWell(
        borderRadius: BorderRadius.circular(19),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(13),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(19),
            gradient: featured
              ? const LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight,
                  colors: [Color(0xFF29121A), Color(0xFF11141A)])
              : null,
            border: Border.all(color: featured ? const Color(0x887C2639) : const Color(0xFF292D36)),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [
            Container(
              width: 39, height: 39,
              decoration: BoxDecoration(
                color: accent.withOpacity(.12), borderRadius: BorderRadius.circular(12),
                border: Border.all(color: accent.withOpacity(.2)),
              ),
              child: Icon(icon, color: accent, size: 21),
            ),
            const SizedBox(height: 10),
            Text(title, maxLines: 1, overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 12.5, letterSpacing: -.1)),
            const SizedBox(height: 4),
            Text(subtitle, maxLines: 2, overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: _muted, fontSize: 10.2, height: 1.25)),
          ]),
        ),
      ),
    );
  }
}
