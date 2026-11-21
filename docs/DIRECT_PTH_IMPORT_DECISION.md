# Direct RVC PTH import — implementation and limits

Status (15 November 2026): native Android ARM64 library compiles; a real public RVC v2 checkpoint loads; CI end-to-end conversion with real PTH + bundled feature models + generated PCM WAV succeeds; the PTH runtime is integrated into and packaged in the ARM64 APK. Full song-cover quality and physical-device acceptance remain pending.

## User-facing contract

Red's Ultimate RVC must let a user select a compatible trained RVC voice checkpoint directly. The user must not be required to supply an ONNX voice checkpoint. The app must reject unsupported checkpoint variants clearly and must never mark a stored file as runnable merely because its extension is accepted.

The song-cover path must decode a song, separate vocals and accompaniment, convert the vocal stem with the selected voice, mix it back and export playable audio locally.

## Implemented architecture

1. Android imports the original .pth file into app-private storage.
2. The native C checkpoint reader parses the PyTorch checkpoint and loads the RVC model tensors.
3. The native PTH runtime validates the checkpoint profile before inference.
4. ContentVec/HuBERT and RMVPE feature extraction use the app's bundled ONNX models through ONNX Runtime 1.28.0.
5. The native C RVC inference engine consumes the extracted 768-dimensional content features and pitch features and produces converted PCM audio.
6. The app mixes converted vocals with the separated accompaniment.

This is direct PTH voice-model inference; it does not export the user's voice checkpoint to ONNX. ONNX Runtime remains a dependency for the bundled feature extractors and source-separation pipeline.

## Supported profile and current exclusions

The native PTH route currently accepts only:
- RVC v2 F0 checkpoints.
- 768-dimensional content features.
- 100-fps frame rate.
- 32 kHz, 40 kHz or 48 kHz model output rates.
- Standard PyTorch ZIP/pickle checkpoint structures supported by the restricted native parser.

The following are not currently supported by the PTH inference route:
- RVC v1 / 256-dimensional models.
- Non-standard frame rates such as 187 fps.
- No-F0 checkpoints.
- Arbitrary .pt snapshots, training checkpoints or ZIP archives.
- Standard FAISS .index retrieval or .mobile.index retrieval on the direct PTH route. The app now includes an on-device converter for compatible 768-dimensional RVC v2 indexes used by the ONNX route.
- Multi-speaker selection beyond the native engine's default speaker path.

The model library may retain source files, but only a compatible .pth checkpoint can run through the native PTH route. The existing ONNX route remains available for compatible ONNX voice models.

## Safety and memory requirements

- Treat .pth as untrusted input. Bound archive entries, uncompressed sizes, tensor dimensions, pickle stack depth, memo size and all offsets.
- Allow only the supported checkpoint reconstruction operations; never execute arbitrary pickle globals or Python code.
- Run inference in a cancellable background thread.
- Use temporary output files and publish a result only after a complete valid WAV has been written.
- Keep models, songs, stems and generated audio on-device.
- Native inference now processes 15-second centres with one-second context and a short overlap to reduce feature-tensor memory; peak-memory and low-memory device testing remain outstanding.

## Verification completed

- The native parser loaded a real public RVC v2 .pth checkpoint in CI.
- CI ran the native conversion end-to-end with the real checkpoint, ContentVec/HuBERT and RMVPE feature models, and generated PCM WAV input; it produced a valid, non-empty WAV.
- The native Android ARM64 PTH shared library compiled and was integrated into the APK.
- The runtime is linked against the app's ONNX Runtime 1.28.0 feature-extraction library.
- Flutter analysis, widget/unit tests, project regression tests, APK alignment/signature and packaged-library checks passed.

## Still required before calling it complete

1. Run a full-song cover acceptance test using a real user-selected compatible PTH checkpoint and real song audio; verify converted vocals, duration alignment, accompaniment preservation and playable export.
2. Implement and test standard FAISS retrieval inside the direct PTH route before claiming index blending for PTH. The standalone on-device converter already prepares compatible 768-dimensional indexes for the ONNX route. Index retrieval is optional; PTH conversion must remain usable without an index.
3. Test on a physical Samsung Galaxy A12: peak memory, elapsed time, heat, cancellation, low-storage behaviour and a full-length song.

Do not call direct PTH support complete until steps 1–4 pass. Do not call the Galaxy A12 supported until step 6 passes.
