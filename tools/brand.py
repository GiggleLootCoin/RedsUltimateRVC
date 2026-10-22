from pathlib import Path

root = Path("buildsrc")

main = root / "lib" / "main.dart"
if main.exists():
    s = main.read_text(encoding="utf-8")
    replacements = {
        "Ultimate RVC Mobile": "Red's Ultimate RVC",
        "Ultimate RVC": "Red's Ultimate RVC",
        "音频推理": "Audio Conversion",
        "实时推理": "Realtime",
        "变声器模式": "Voice Changer",
        "分贝仪": "dB Meter",
        "音高检测": "Pitch Detection",
        "参数解释": "RVC Controls",
        "mobile.index 转换教程": "Index Converter",
        "primarySwatch: Colors.blue,": "primarySwatch: Colors.red,
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.redAccent, brightness: Brightness.dark),",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    s = s.replace("backgroundColor: Colors.white", "backgroundColor: const Color(0xFF09090D)")
    main.write_text(s, encoding="utf-8")

manifest = root / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
if manifest.exists():
    s = manifest.read_text(encoding="utf-8")
    s = s.replace('android:label="Ultimate RVC Mobile"', 'android:label="Red\'s Ultimate RVC"')
    s = s.replace('android:icon="@mipmap/ic_launcher"', 'android:icon="@drawable/ic_red_logo"')
    manifest.write_text(s, encoding="utf-8")

pubspec = root / "pubspec.yaml"
if pubspec.exists():
    s = pubspec.read_text(encoding="utf-8")
    s = s.replace("name: ultimate_rvc_mobile", "name: reds_ultimate_rvc")
    s = s.replace("Cross-platform RVC voice conversion app", "Red's Ultimate RVC - local Android voice conversion")
    pubspec.write_text(s, encoding="utf-8")

icon_dir = root / "android" / "app" / "src" / "main" / "res" / "drawable"
icon_dir.mkdir(parents=True, exist_ok=True)
(icon_dir / "ic_red_logo.xml").write_text('''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:fillColor="#09090D" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="#E00020" android:pathData="M18,20h72v8h-72zM23,28h62v42c0,17 -12,27 -31,27s-31,-10 -31,-27z"/>
    <path android:fillColor="#09090D" android:pathData="M37,40h34v8h-34zM37,54h34v8h-34zM43,68h22v8h-22z"/>
    <path android:fillColor="#E00020" android:pathData="M45,97c0,0 3,8 9,8s9,-8 9,-8z"/>
</vector>
''', encoding="utf-8")
