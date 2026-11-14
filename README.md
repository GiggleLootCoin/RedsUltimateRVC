# Red's Ultimate RVC ❤️🎧🎤

**Original creator, software developer, designer and maker: LittleRedBigSmile.** This is Red's original branded project and creative direction. Upstream engines and third-party components retain their own licences and notices.

A locally processed ARM64 Android RVC voice-conversion app based on the open-source Ultimate RVC Mobile project, with Red's branding and native PTH inference integration.

## What is included

- Local RVC inference using compatible ONNX voice models.
- A native C inference route for supported RVC v2 .pth voice checkpoints.
- Offline vocal/accompaniment separation, voice conversion and mix-back for song covers.
- Android file picking and a local model library.
- .mobile.index import and format validation for the existing ONNX route.
- Voice Changer and experimental realtime modules.
- A phone-local voice dataset workspace for recording, organising and exporting samples.
- English interface, Red's original logo artwork and official creator-channel link.
- No mandatory cloud inference, paid service, Kaggle or Colab.

The app targets Android ARM64 (API 24+). Performance and memory use depend on the handset. Physical Samsung Galaxy A12 acceptance testing is still outstanding.

## Model compatibility

| File / feature | Current support |
|---|---|
| Compatible RVC v2 ONNX voice model | Supported by the existing ONNX route |
| RVC v2 .pth voice model | Native route supports 768-dimensional, 100-fps F0 checkpoints at 32/40/48 kHz |
| Other .pth variants | Rejected by the native engine with a compatibility error |
| .pt and ZIP archives | May be stored in the library; not runnable |
| Standard FAISS .index | Stored only; native PTH retrieval is not implemented |
| .mobile.index | Existing ONNX route only, when the file matches the mobile format |
| Voice model training | Not included; Dataset Lab prepares and exports samples only |
| Realtime RVC | Experimental; Android routing and performance may stutter |

The native PTH route does not ask the user for an ONNX voice checkpoint and does not convert the voice checkpoint into ONNX. It uses the bundled ContentVec/HuBERT and RMVPE ONNX feature models internally, then runs the voice model through the native C RVC engine. Standard FAISS retrieval is not yet connected to this route.

Changing a file extension does not convert a model or index. Unsupported model variants must be reported as unsupported rather than marked ready.

## Song-cover processing

The intended local path is:
1. Android decodes the selected song to PCM WAV.
2. Bundled Spleeter models separate vocals and accompaniment.
3. The selected compatible ONNX or native PTH voice model converts the vocal stem.
4. The app aligns and mixes the converted vocals with the original accompaniment.
5. The resulting WAV can be played and saved.

The PTH route currently has no retrieval-index support. Long-song memory, speed, output quality and thermal behaviour still need physical-device testing on the Galaxy A12.

## Native PTH backend status

GitHub Actions has successfully:
- Loaded a real public RVC v2 .pth checkpoint with the native checkpoint parser.
- Cross-compiled the native PTH inference shared library for Android ARM64.
- Built the feature extraction path against the app's ONNX Runtime 1.28.0 library.

The remaining release checks are APK packaging, Flutter integration, a real compatible 768-dimensional/100-fps PTH song-cover conversion, and physical Samsung Galaxy A12 testing. A successful native-library compile is not proof of end-to-end audio conversion.

The native PTH implementation is based on the Apache-2.0-licensed Spartacvc C inference/checkpoint code. The app's ContentVec/HuBERT and RMVPE feature extraction uses the bundled ONNX models and ONNX Runtime.

## Build and automated checks

GitHub Actions builds the ARM64 APK, compiles the native PTH runtime and Sherpa-ONNX source-separation library, bundles the required local models, and runs:
1. Python integration and regression tests.
2. Native PTH checkpoint-loader acceptance test.
3. Android ARM64 native compilation.
4. Flutter static analysis and widget/unit tests.
5. APK alignment, signature and packaged-library checks.
6. SHA-256 generation for the APK.

Workflow: https://github.com/GiggleLootCoin/RedsUltimateRVC/actions/workflows/build-apk.yml

A passing CI build proves compilation and the listed automated checks. It does not replace installation and a full-song conversion test on a physical Galaxy A12.

## Persistent Android signing

Without a private persistent keystore, GitHub Actions uses its temporary runner debug key. That is suitable for a test install, but later APKs may have a different signature and Android may refuse an in-place update. You may need to uninstall the previous test APK first.

To enable stable updates, create one private Android keystore with Java keytool and keep it safe. Never commit it to this public repository.

Open this repository's Settings → Secrets and variables → Actions on GitHub and add these repository secrets:
- RED_RVC_KEYSTORE_BASE64 — the one-line Base64 keystore contents.
- RED_RVC_STORE_PASSWORD — keystore password.
- RED_RVC_KEY_ALIAS — normally red-rvc.
- RED_RVC_KEY_PASSWORD — key password.

The workflow validates the key and signs subsequent APKs with it automatically. Keep a secure backup of the keystore and passwords.

## Creator and third-party acknowledgements

**LittleRedBigSmile** is the original creator, project developer, designer and maker of Red's Ultimate RVC and its branded app experience.

The Android application is based on Ultimate RVC Mobile by Sharl210. The native PTH backend uses the Apache-2.0-licensed Spartacvc project. This repository does not claim ownership of upstream inference implementations.
