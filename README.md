# Red's Ultimate RVC ❤️🎧🎤

A branded ARM64 Android RVC voice-conversion app based on the open-source Ultimate RVC Mobile engine by Sharl210.

## Visual design update

The current premium mobile studio redesign uses a restrained black-and-crimson palette, clearer navigation hierarchy, refined tool cards, and explicit local-capability disclosures. The redesign preserves existing conversion and library callbacks; it does not add unsupported PTH conversion, neural-network training, or vocal separation.

## What is included

- On-device RVC inference with compatible ONNX voice models.
- Audio conversion controls, progress, resumable chunk processing and generated-audio playback/export.
- Android's unfiltered file picker for supported model and audio imports.
- Model library storage for ONNX models and source files.
- Compatible `.mobile.index` import and format validation.
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
| Vocal separation / full song-cover pipeline | Not included; provide an already-isolated vocal track |
| Realtime RVC | Experimental; Android routing and performance may stutter |

Changing a file extension does not convert a model or index. The model-conversion screen and Index Tools screen explain these limits rather than pretending a conversion happened.

## Build and automated checks

GitHub Actions builds the ARM64 APK and runs:

1. Flutter static analysis.
2. Flutter widget/unit tests.
3. Upstream Python static regression tests.
4. APK zip alignment and signature verification.
5. Checks that required offline HuBERT and RMVPE ONNX assets are packaged.
6. SHA-256 generation for the APK.

Workflow: [Build Red's Ultimate RVC](https://github.com/GiggleLootCoin/RedsUltimateRVC/actions/workflows/build-apk.yml)

A passing CI build proves compilation and the listed automated checks; it does not replace installation and runtime testing on a physical Galaxy A12.

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
