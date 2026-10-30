# Red's Ultimate RVC — Final Android Rebuild Contract

This branch is a ground-up correction of the failed branded-upstream approach.

## Non-negotiable product requirements
- Android phone is the entire workstation. No Kaggle, Colab, PC, web dashboard, subscription, paid credits, or external conversion step.
- Target first: Samsung Galaxy A12 / Android 12 / arm64.
- Red/black polished UI using the approved Red's Ultimate RVC branding and logo. No Chinese upstream UI and no generic upstream appearance.
- Import and manage common RVC assets from Android storage: .pth, .pt, .onnx, .index, .mobile.index, and model ZIP packages.
- Never gray out valid model files in Samsung's picker. If Android MIME filtering is unreliable, use FileType.any plus in-app extension/signature validation instead of relying on the picker to filter.
- Audio import/record, model selection, index selection, conversion, progress, cancel/resume, playback, save/share, long-audio chunking.
- Local model/index preparation inside the app. A standard .index must not require the user to leave the app.
- Voice training must be a real implemented workflow, not a decorative Train button: dataset import/recording, preprocessing, feature/F0 extraction, training progress/checkpoints, resulting model management, and use of the resulting voice.
- Offline/local operation after required app assets are installed. No silent cloud fallback.
- Realtime/voice changer, dB meter, pitch detection, parameter controls, diagnostics and permission handling must either genuinely function or be clearly omitted until implemented. No fake buttons.

## Acceptance rules
1. A successful CI compile is necessary but is not proof of runtime functionality.
2. No feature may be labelled working solely because its screen exists.
3. Model formats shown as runnable must actually be accepted by the native inference path.
4. Training must execute real training code and produce a model; placeholders/sleeps/mock progress are forbidden.
5. Test fixtures and automated tests must cover model import, index import/conversion, audio import, persistence, invalid files, and native method-channel contracts.
6. The release cannot be called final until a physical Android device test checklist is completed.

## Why the previous approach failed
The current main branch downloads Sharl210/ultimate-rvc-mobile v2.0.0 at build time and mutates it with tools/brand.py. That upstream is primarily ONNX inference and contains placeholder/incomplete Python training/inference code. Patching its picker to advertise .pth/.pt/.zip did not create .pth inference or training. This rebuild must stop equating UI acceptance with engine support.

## Architecture direction
Keep proven Android-native ONNX inference components where they genuinely work, but move the product into this repository as owned source instead of a brittle build-time branding patch. Build a dedicated model manager and an on-device training engine appropriate for ARM64/mobile constraints. Use streaming/chunked preprocessing and checkpointing to stay within Galaxy A12 memory limits. Optimize for correctness and survivability over speed.

This document is the source of truth for the final rebuild.