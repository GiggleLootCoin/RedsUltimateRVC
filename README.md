# Red's Ultimate RVC ❤️🎧🎤

A branded ARM64 Android RVC voice-conversion app based on the open-source Ultimate RVC Mobile engine by Sharl210.

## What is included

- On-device RVC inference with compatible ONNX voice models.
- Audio conversion controls, progress, resumable chunk processing and generated-audio playback/export.
- Android's unfiltered file picker for supported model and audio imports.
- Model library storage for ONNX models and source files.
- Compatible `.mobile.index` import and format validation.
- Offline Spleeter vocal/accompaniment separation for 16-bit PCM WAV input, followed by local RVC ONNX vocal conversion and mix-back into a song-cover WAV.
- Voice Changer and experimental realtime modules.
- Voice Dataset Lab for recording, importing, organising and exporting samples.
- English interface, Red's original logo artwork and creator-channel link.
- No mandatory cloud inference, subscription or paid service.

The app targets Android ARM64 (API 24+). Performance and memory use depend heavily on the handset. The Samsung Galaxy A12 has not been certified by physical-device testing in CI.

## Important feature boundaries

These are deliberate capability disclosures, not hidden menu items:

| Feature | Current status |
|---|---|
| ONNX RVC inference | Included; compatible RVC v2 ONNX models only |
| `.pth` / `.pt` import | Can be stored; not runnable by the Android inference engine |
| PTH-to-ONNX conversion on phone | Not included; a real Android-compatible export engine is still needed |
| Standard FAISS `.index` conversion | Not included on Android |
| `.mobile.index` | Supported if it matches the mobile feature-table format |
| Voice model training | Not included; Dataset Lab only prepares and exports samples |
| Vocal separation / song-cover pipeline | Integrated on the development branch with bundled Spleeter models; 16-bit PCM WAV input only. Galaxy A12 runtime QA is still required |
| Realtime RVC | Experimental; Android routing and performance may stutter |

Changing a file extension does not convert a model or index. The model-conversion screen and Index Tools screen explain these limits rather than pretending a conversion happened.

## Native RVC engine prototype

The native migration branch now includes a JNI bridge to the MIT-licensed RVC-GGML C++ inference core. GitHub Actions has successfully cross-compiled both the complete inference core and the JNI shared library for Android ARM64 using the NDK CPU backend. The bridge accepts HuBERT, RMVPE, voice-model and optional retrieval-index GGUF files and processes WAV audio locally.

The native migration branch now packages the compiled ARM64 JNI library into an engineering APK and exposes a dedicated native conversion screen. The screen accepts HuBERT GGUF, RMVPE GGUF, a voice GGUF, an optional index GGUF and a WAV input. This exercises the native inference route without asking the user to supply ONNX voice models. It is still **not raw .pth support**: the upstream exporter requires Python, PyTorch, NumPy and `gguf` (plus FAISS for standard index files), and has not been ported into the Android app. No real model/audio or Galaxy A12 runtime test has passed yet.

## Native migration branch warning

The `feature/native-ncnn-rvc-backend` branch builds an installable engineering APK artifact with the native GGUF runtime packaged and a dedicated conversion screen. It is not an ONNX-free release: the existing ONNX pipeline remains available as a fallback, while the native route uses GGUF. The APK is not published as a public release until real model/audio and Galaxy A12 acceptance tests pass. Raw `.pth` files still need an exporter step; importing one does not make it directly runnable.

## Build and automated checks

GitHub Actions builds the ARM64 APK, compiles the Sherpa-ONNX C API for offline Spleeter separation, bundles the two separation ONNX models, and runs:

1. Flutter static analysis.
2. Flutter widget/unit tests.
3. Upstream Python static regression tests.
4. APK zip alignment and signature verification.
5. Checks that required offline HuBERT and RMVPE ONNX assets are packaged.
6. SHA-256 generation for the APK.

Workflow: [Build Red's Ultimate RVC](https://github.com/GiggleLootCoin/RedsUltimateRVC/actions/workflows/build-apk.yml)

A passing CI build proves compilation and the listed automated checks; it does not replace installation and runtime testing on a physical Galaxy A12. Source separation is computationally heavy: do not treat the Galaxy A12 as certified until a full-length song has been processed without an out-of-memory failure, thermal shutdown or audio corruption.

## Persistent Android signing (important for updates)

Without a private persistent keystore, GitHub Actions uses its temporary runner debug key. That is suitable for a test install, but a later APK may have a different signature and Android may refuse an in-place update. You may need to uninstall the previous test APK first.

To enable stable updates, create one private Android keystore and keep it safe. Never commit it to this public repository.

Create the keystore in a trusted environment with Java's `keytool`:

```sh
keytool -genkeypair -v -keystore red-rvc-release.jks -alias red-rvc -keyalg RSA -keysize 2048 -validity 10000
```

Base64-encode the keystore as one uninterrupted line, then open this repository's **Settings → Secrets and variables → Actions** on GitHub and add these repository secrets:

- `RED_RVC_KEYSTORE_BASE64` — the one-line Base64 keystore contents.
- `RED_RVC_STORE_PASSWORD` — keystore password.
- `RED_RVC_KEY_ALIAS` — normally `red-rvc`.
- `RED_RVC_KEY_PASSWORD` — key password.

The workflow validates the key and signs subsequent APKs with it automatically. Keep a secure backup of the keystore and passwords. If they are lost, future APKs cannot update installations signed with that key.

## Credits and licence

The local Android inference implementation is based on [Ultimate RVC Mobile](https://github.com/Sharl210/ultimate-rvc-mobile) by Sharl210. This repository is a separate branded distribution and does not claim ownership of the underlying inference implementation. Refer to the upstream repository and its licence for the engine's terms.
