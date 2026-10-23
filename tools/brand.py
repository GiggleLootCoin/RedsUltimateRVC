import re
from pathlib import Path

root = Path("buildsrc")

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
        ("Ultimate RVC Mobile", "Red's Ultimate RVC"),
        ("Ultimate RVC", "Red's Ultimate RVC"),
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

manifest = root / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
replace_in(
    manifest,
    [
        ('android:label="Ultimate RVC Mobile"', 'android:label="Red\'s Ultimate RVC"'),
        ('android:icon="@mipmap/ic_launcher"', 'android:icon="@drawable/ic_red_logo"'),
    ],
)

# Flutter 3.16+ reads the Kotlin Gradle Plugin version from settings.gradle.
# Match the actual upstream plugin declaration rather than relying on one exact
# whitespace/quote layout, and fail the build if the required patch is absent.
settings_gradle = root / "android" / "settings.gradle"
regex_replace(
    settings_gradle,
    r'(id\s+["\']org\.jetbrains\.kotlin\.android["\']\s+version\s+["\'])[^"\']+(["\']\s+apply\s+false)',
    r'\g<1>1.9.24\2',
)

# Keep the legacy buildscript classpath aligned too. Some Gradle/plugin paths
# still inspect it even though the plugin DSL in settings.gradle is primary.
android_build = root / "android" / "build.gradle"
regex_replace(
    android_build,
    r'(org\.jetbrains\.kotlin:kotlin-gradle-plugin:)[^"\']+',
    r'\g<1>1.9.24',
)

pubspec = root / "pubspec.yaml"
replace_in(
    pubspec,
    [
        ("name: ultimate_rvc_mobile", "name: reds_ultimate_rvc"),
        ("Cross-platform RVC voice conversion app", "Red's Ultimate RVC - local Android voice conversion"),
    ],
)

gradle_props = root / "android" / "gradle.properties"
replace_in(
    gradle_props,
    [("org.gradle.java.home=/usr/lib/jvm/java-17-openjdk-amd64\n", "")],
)

icon_dir = root / "android" / "app" / "src" / "main" / "res" / "drawable"
icon_dir.mkdir(parents=True, exist_ok=True)
(icon_dir / "ic_red_logo.xml").write_text(
    """<?xml version="1.0" encoding="utf-8"?>
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
""",
    encoding="utf-8",
)
