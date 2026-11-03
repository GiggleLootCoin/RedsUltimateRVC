# Red's Ultimate RVC — Rebuild Specification

Status: architecture reset / implementation branch
Branch: rebuild/on-device-first

This is the acceptance contract for the rebuild. A feature is complete only when its end-to-end operation is implemented and tested on a physical Android device. A screen rendering or a button responding is not proof.

## Product requirements
- Genuine native Android APK; the phone is the complete user environment.
- No Kaggle, Colab, browser hand-off, external app, mandatory server, cloud inference, paid API or subscription.
- Designed first for Samsung Galaxy A12 / Android 12 / ARM64 and constrained memory/storage.
- Approved Red's Ultimate RVC identity; polished black/red interface, coherent typography, spacing, icons and navigation.
- English interface throughout; no leftover upstream-language strings.
- Import, manage, select, validate, remove and persist voice models/indexes with Android's system document picker.
- Import and record audio; convert; show real progress, cancellation and recovery; play, save and share outputs.
- Long-audio song-cover workflow with chunking and safe recovery.
- Realtime conversion and voice changer must report actual microphone/audio-route state.
- Real pitch detection, dB meter, index tools and RVC controls.
- Local voice-sample recording and dataset management.
- No fake training, conversion, progress or unsupported-format claims.

## Critical architectural finding
The current main branch is a branded layer over Sharl210/ultimate-rvc-mobile v2.0.0. Its native inference call runs in a separate Android process and uses an ONNX inference engine. It is not a general RVC PTH runtime.

The current training screen records/imports samples and copies them into a dataset folder. It does not train a neural voice model. The model-conversion screen has no local PTH-to-ONNX converter. The model library can store source files, but storage is not inference support.

## Hard technical boundary
Standard RVC training is a substantial PyTorch pipeline: audio preprocessing, content-feature extraction (typically HuBERT), F0 extraction, dataset/index construction and iterative neural-network training. The existing mobile ONNX inference engine does not provide those training operations. A Galaxy A12 is a constrained CPU/RAM device; full standard RVC training offline cannot honestly be promised at useful speed or reliability. PTH checkpoint conversion also requires the compatible model architecture and export/runtime toolchain; renaming or copying a file is not conversion.

Rules:
- Keep all implemented app operations phone-local.
- Never invoke Kaggle, Colab, web services or other apps.
- Do not claim standard RVC training or PTH conversion until a genuinely on-device implementation is integrated and physically tested.
- If standard RVC training cannot be delivered on the target hardware, disclose that limitation rather than calling dataset preparation training. Do not substitute another model family and call it RVC.

## Rebuild workstreams
1. Product/UI reset: replace the dashboard-plus-upstream-navigation patchwork with one coherent app shell. Every tile opens its real feature. No duplicate dashboard or hidden upstream screens. Preserve approved logo and black/red identity.
2. Model library: unrestricted Android document selection; safely copy content into persistent app-private storage; validate signature, size, extension, metadata and runtime compatibility; show truthful states (Ready for ONNX inference, Source checkpoint—not runnable, Invalid, Index ready, Index needs mobile conversion); rename/remove/reselect; persist across restarts. Never label PTH as ready.
3. Audio pipeline: validate inputs; stable decode/resample; chunk long audio; bounded memory; real progress; cancellation; resumable jobs; atomic outputs; playback; export through Android MediaStore; share through Android sharesheet.
4. Inference engine: local ONNX only; verify model inputs/outputs, sample rates, F0 method, index compatibility and device memory. No network dependency for inference. Add known model/audio integration tests.
5. Realtime/voice changer: test audio capture/playback routes, foreground service lifecycle, Bluetooth/wired route handling, latency, underruns, interruptions and Android 12 microphone permissions. Do not claim system-wide voice changing unless Android permits it.
6. Voice Lab: local recording/import, review, trim, rename/delete, dataset validation and storage accounting. Until a real on-device trainer exists, call this dataset preparation, not training.
7. Audio tools: implement/test pitch, dB, index conversion and controls against the inference engine. Remove controls not wired end-to-end.
8. Quality gates: Flutter analyze, unit tests, Android instrumentation tests, APK ABI/package inspection, model/audio integration tests, offline network test and physical Galaxy A12 acceptance test.

## Release acceptance checklist
- [ ] First launch opens Red dashboard, not upstream landing screen.
- [ ] Every dashboard tile navigates to its intended screen and back correctly.
- [ ] Samsung My Files selects supported model/index/audio files; imported bytes persist after reboot.
- [ ] Compatibility status is accurate; only supported ONNX models start inference.
- [ ] Known ONNX model plus sample audio completes fully offline and produces playable output.
- [ ] Long-file processing avoids memory exhaustion and can recover/cancel safely.
- [ ] Save/share produces output accessible outside app-private storage.
- [ ] Realtime and voice changer are verified on the target phone and show real state.
- [ ] Audio tools and controls demonstrably affect results.
- [ ] Dataset recording/import/management work locally.
- [ ] No training/PTH conversion claims unless implemented and tested.
- [ ] Visual review on a narrow Android screen: no clipping, overflow, generic upstream pages, untranslated text or dead controls.
- [ ] APK installs and launches on Galaxy A12 Android 12.

## Current release warning
The current v0.2.0-final-135 build is a successful CI compilation, not proof that the product requirements above are satisfied or that it passed a physical Galaxy A12 test. Do not describe it as the completed rebuild.