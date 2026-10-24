import re
from pathlib import Path
import urllib.request

root = Path("buildsrc")

# Approved Red's Ultimate RVC artwork created for this project.
LOGO_URL = "https://cdn.websitepublisher.ai/custom/wid25042/images/reds-ultimate-rvc-logo.svg"
logo_svg = root / "assets" / "images" / "reds-ultimate-rvc-logo.svg"
logo_svg.parent.mkdir(parents=True, exist_ok=True)
urllib.request.urlretrieve(LOGO_URL, logo_svg)


def replace_in(path, replacements):
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")

def regex_replace(path, pattern, replacement):
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text)
    if count == 0:
        raise RuntimeError(f"Required compatibility patch did not match: {path}")
    path.write_text(updated, encoding="utf-8")

replace_in(
    root / "lib" / "main.dart",
    [
        ("Ultimate RVC Mobile", "Red\\'s Ultimate RVC"),
        ("音频推理", "Audio Conversion"),
        ("实时推理", "Realtime"),
        ("变声器模式", "Voice Changer"),
        ("分贝仪", "dB Meter"),
        ("音高检测", "Pitch Detection"),
        ("参数解释", "RVC Controls"),
        ("mobile.index 转换教程", "Index Converter"),
        ("primarySwatch: Colors.blue,", "primarySwatch: Colors.red,"),
        ("backgroundColor: Colors.white", "backgroundColor: const Color(0xFF09090D)"),
    ],
)

# Render the exact approved SVG artwork into a launcher PNG.
launcher_png = root / "android" / "app" / "src" / "main" / "res" / "drawable" / "reds_ultimate_rvc_logo.png"
launcher_png.parent.mkdir(parents=True, exist_ok=True)
try:
    import cairosvg
    cairosvg.svg2png(url=str(logo_svg), write_to=str(launcher_png), output_width=512, output_height=512)
except Exception as exc:
    raise RuntimeError(f"Could not render the approved Red's Ultimate RVC logo: {exc}")

manifest = root / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
replace_in(
    manifest,
    [
        ('android:label="Ultimate RVC Mobile"', 'android:label="Red\'s Ultimate RVC"'),
        ('android:icon="@mipmap/ic_launcher"', 'android:icon="@drawable/reds_ultimate_rvc_logo"'),
    ],
)

# The CI intentionally uses Flutter 3.24.5. Its Android template uses
# Gradle 8.3, AGP 8.1.0 and Kotlin 1.8.22. The upstream RVC project is older
# (Gradle 7.6.3 / AGP 7.3.0 / Kotlin 1.8.10), which causes Flutter's Android
# dependency validation to reject the build. Keep all three versions aligned.
settings_gradle = root / "android" / "settings.gradle"
regex_replace(
    settings_gradle,
    r'(id\s+["\']com\.android\.application["\']\s+version\s+["\'])[^"\']+(["\']\s+apply\s+false)',
    r'\g<1>8.1.0\2',
)
regex_replace(
    settings_gradle,
    r'(id\s+["\']org\.jetbrains\.kotlin\.android["\']\s+version\s+["\'])[^"\']+(["\']\s+apply\s+false)',
    r'\g<1>1.8.22\2',
)

android_build = root / "android" / "build.gradle"
regex_replace(
    android_build,
    r'(com\.android\.tools\.build:gradle:)[^"\']+',
    r'\g<1>8.1.0',
)
regex_replace(
    android_build,
    r'(org\.jetbrains\.kotlin:kotlin-gradle-plugin:)[^"\']+',
    r'\g<1>1.8.22',
)

wrapper = root / "android" / "gradle" / "wrapper" / "gradle-wrapper.properties"
regex_replace(
    wrapper,
    r'(distributionUrl=.*gradle-)[^\\/]+(-all\.zip)',
    r'\g<1>8.3\2',
)

pubspec = root / "pubspec.yaml"
replace_in(
    pubspec,
    [
        ("name: ultimate_rvc_mobile", "name: reds_ultimate_rvc"),
        ("Cross-platform RVC voice conversion app", "Red's Ultimate RVC - local Android voice conversion"),
        ("dev_dependencies:\n", "dependency_overrides:\n  win32: 5.5.5\n\ndev_dependencies:\n"),
    ],
)

# R8 fails on Flutter's optional Play Store deferred-component classes when
# shrinking this standalone APK. Red's Ultimate RVC does not use deferred
# Play Feature Delivery, so keep release shrinking off for a reliable APK.
app_gradle = root / "android" / "app" / "build.gradle"
replace_in(
    app_gradle,
    [
        ("minifyEnabled true", "minifyEnabled false"),
        ("shrinkResources true", "shrinkResources false"),
    ],
)

gradle_props = root / "android" / "gradle.properties"
replace_in(
    gradle_props,
    [("org.gradle.java.home=/usr/lib/jvm/java-17-openjdk-amd64\n", "")],
)


ui = {
"生成已中止":"Generation stopped","生成完成":"Conversion complete","初始化失败":"Initialization failed","初始化中...":"Initializing...",
"再按一次退出":"Press back again to exit","确定":"OK","音频推理":"Audio Conversion","实时推理":"Realtime Conversion","变声器模式":"Voice Changer",
"分贝仪":"dB Meter","音高检测":"Pitch Detection","参数解释":"RVC Controls","mobile.index 转换教程":"Index Converter",
"音频":"Audio","音色":"Voice Model","生成":"Convert","结果":"Result","未启动":"Ready","需要麦克风权限":"Microphone permission required",
"实时测量中":"Measuring","测量失败":"Measurement failed","已锁定":"Locked","解除锁定":"Unlock","锁定当前数值":"Lock current value",
"分贝实时曲线":"Live dB Level","清空曲线":"Clear chart","准备生成":"Ready to convert","处理出错了，请重新生成":"Processing failed. Please try again.",
"恢复进度中":"Restoring progress","无法继续":"Cannot continue","不做任何操作。":"No action was taken.","生成音频":"Convert Audio",
"输入音频：":"Input audio: ","音色模型：":"Voice model: ","索引文件：":"Index file: ","未选择":"Not selected","参数":"Parameters",
"高级参数":"Advanced","恢复默认":"Reset defaults","生成中...":"Converting...","生成用时：":"Conversion time: ","正在中止":"Stopping...",
"终止生成":"Stop conversion","重新生成":"Convert again","开始生成":"Start conversion","继续未完成":"Resume unfinished job",
"处理时间取决于音频长度":"Processing time depends on audio length.","为什么要先转换":"Why conversion is required",
"标准 RVC/FAISS .index 需要先在电脑上转换，转换后再传到手机选择。":"Standard RVC/FAISS .index files must be converted on a computer before using them here.",
"转换命令":"Conversion command","请选择 .onnx 模型文件":"Please select an .onnx model file.","请选择 mobile.index 文件":"Please select a mobile.index file.",
"选择模型失败":"Model selection failed","选择索引失败":"Index selection failed","选择音色模型":"Select voice model","已选择音色：":"Selected voice: ",
"支持：.onnx 模型":"Supported: .onnx models","更换模型":"Change model","选择模型":"Choose model","清除模型":"Clear model",
"索引文件（可选）":"Index file (optional)","支持：mobile.index 索引":"Supported: mobile.index","更换 mobile.index":"Change mobile.index",
"选择 mobile.index":"Choose mobile.index","清除索引":"Clear index","继续":"Continue","当前音频：":"Current audio: ",
"Pitch（音调设置）":"Pitch","音调设置":"Pitch","半音":"semitones","Index Rate（索引强度）":"Index Rate","Index Rate（检索特征占比）":"Index Rate",
"检索特征占比":"Feature retrieval ratio","索引强度":"Index strength","Formant（性别因子/声线粗细）":"Formant","性别因子/声线粗细":"Voice character",
"Noise Gate（噪声过滤）":"Noise Gate","噪声过滤":"Noise gate","Sample Rate（采样率）":"Sample Rate","采样率":"Sample rate",
"降噪优化":"Denoise","音域过滤":"Vocal Range Filter","只影响处理结果，不改原始录音文件":"Affects processing only; original recording is unchanged.",
"Filter Radius（音高滤波）":"Filter Radius","音高滤波":"Pitch smoothing","RMS Mix（响度混合）":"RMS Mix","响度混合":"Loudness mix",
"RMS Mix（响度因子）":"RMS Mix","响度因子":"Loudness mix","Protect（辅音保护）":"Protect","辅音保护":"Consonant protection",
"正在停止实时推理":"Stopping realtime conversion","已停止":"Stopped","请选择 .onnx 音色模型":"Please choose an .onnx voice model.",
"启动实时推理":"Start realtime conversion","停止实时推理":"Stop realtime conversion","状态：":"Status: ","音频采样率":"Audio sample rate",
"采样长度":"Chunk length","淡入淡出长度":"Crossfade length","额外推理时长":"Extra inference time","延时缓冲":"Delay buffer","播放延迟":"Playback delay",
"悬浮控制":"Floating controls","悬浮窗直径":"Overlay size","悬浮窗不透明度":"Overlay opacity","关闭悬浮窗":"Close overlay","打开悬浮窗":"Open overlay",
"录制模式":"Recording mode","处理声线参数":"Voice settings","选择 .onnx 模型":"Choose .onnx model","更换 .onnx 模型":"Change .onnx model",
"移除索引":"Remove index","分享失败":"Share failed","已保存":"Saved","保存失败":"Save failed","生成结果":"Conversion result",
"音频已生成":"Audio converted","播放":"Play","暂停":"Pause","分享":"Share","保存":"Save","选择音频失败":"Audio selection failed",
"录音失败":"Recording failed","选择音频":"Choose audio","支持：MP3、WAV、M4A、FLAC、OGG":"Supported: MP3, WAV, M4A, FLAC, OGG",
"更换音频":"Change audio","清除音频":"Clear audio","停止录音":"Stop recording","直接录音":"Record","录音时长：":"Recording time: ",
"音高检测设置":"Pitch detection settings","基准音高（留空默认 C4）":"Reference pitch (blank = C4)","图表 Y 轴模式":"Chart Y-axis mode",
"相对半音值":"Relative semitone","频率 Hz":"Frequency Hz","音名（A2/C4）":"Note name (A2/C4)","检测灵敏度":"Detection sensitivity",
"取消":"Cancel","音高实时曲线":"Live pitch","音名":"Note","相对半音值：":"Relative semitone: ","手机端限制":"Mobile limitations",
"这个页面仅供演示。":"Realtime conversion page.","手机端实时推理性能和系统音频能力限制很大。":"Realtime conversion depends on device performance and Android audio routing.",
"当前无法指定输入输出设备。":"Android does not expose selectable input/output devices here.","知道了":"Got it",
"这是 Ultimate RVC 生成的音频。":"Audio converted with Red's Ultimate RVC.","Ultimate RVC 生成音频":"Red's Ultimate RVC audio","悬浮窗":"Overlay"
}

for dart in (root / "lib").rglob("*.dart"):
    s = dart.read_text(encoding="utf-8")
    for a, b in ui.items():
        s = s.replace(a, b)
    def clean(m):
        q, body = m.group(1), m.group(2)
        body = re.sub(r"[\\u3400-\\u9fff]+", "", body).strip()
        return q + (body or "RVC") + q
    s = re.sub(r"(['\"])([^'\"\\n]*[\\u3400-\\u9fff][^'\"\\n]*)\\1", clean, s)
    dart.write_text(s, encoding="utf-8")

main = root / "lib" / "main.dart"
s = main.read_text(encoding="utf-8")
s = s.replace(
    "theme: ThemeData(",
    "theme: ThemeData(\\n"
    "        brightness: Brightness.dark,\\n"
    "        scaffoldBackgroundColor: const Color(0xFF08080C),\\n"
    "        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFFE00020), brightness: Brightness.dark),\\n"
    "        appBarTheme: const AppBarTheme(backgroundColor: Color(0xFF08080C), foregroundColor: Colors.white, elevation: 0, centerTitle: true),\\n"
    "        cardTheme: CardTheme(color: Color(0xFF121218), surfaceTintColor: Colors.transparent, elevation: 0, shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(18)), side: BorderSide(color: Color(0xFF282831)))),"
)
s = s.replace("title: 'Ultimate RVC Mobile',", "title: \"Red's Ultimate RVC\",")
main.write_text(s, encoding="utf-8")


# Final sanity scrub: the branded build must never ship untranslated CJK text.
for dart in (root / "lib").rglob("*.dart"):
    content = dart.read_text(encoding="utf-8")
    content = re.sub(r"[\\u3400-\\u9fff]+", "", content)
    dart.write_text(content, encoding="utf-8")
