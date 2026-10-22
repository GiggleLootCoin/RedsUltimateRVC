# Red's Ultimate RVC ❤️🎧🎤

A branded Android build of Red's Ultimate RVC.

## Goals

- Local RVC voice conversion
- Long-audio processing with recovery/chunking
- Android file picker for audio, ONNX voice models and indexes
- Pitch, index rate, protect, RMS, formant and other RVC controls
- Playback, saving and sharing of generated audio
- Progress and recovery
- No mandatory cloud inference
- No Replit
- No ZeroGPU requirement
- No subscription required for the app itself
- Red's Ultimate RVC branding

## Model note

The mobile inference engine uses ONNX voice models. Standard RVC .pth models normally need to be exported or converted to ONNX before local Android inference. Standard FAISS indexes may likewise need mobile conversion.

## Build

The GitHub Actions workflow builds an ARM64 release APK using the open-source local RVC mobile engine as its implementation base, then applies the Red's Ultimate RVC branding layer.

The target is Android ARM64 devices such as the Samsung Galaxy A12.

## Credits

The local mobile inference implementation is based on the open-source Ultimate RVC Mobile project by Sharl210. This repository is a separate branded distribution and does not claim ownership of the underlying inference implementation.

Original project: https://github.com/Sharl210/ultimate-rvc-mobile
