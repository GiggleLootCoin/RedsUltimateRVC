# Direct RVC PTH import — implementation and limits

Status: native Android ARM64 library compiles and a real public RVC v2 checkpoint loads. APK packaging and device-level end-to-end acceptance remain pending.

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
- Standard FAISS .index retrieval or .mobile.index retrieval.
- Multi-speaker selection beyond the native engine's default speaker path.

The model library may retain source files, but only a compatible .pth checkpoint can run through the native PTH route. The existing ONNX route remains available for compatible ONNX voice models.

## Safety and memory requirements

- Treat .pth as untrusted input. Bound archive entries, uncompressed sizes, tensor dimensions, pickle stack depth, memo size and all offsets.
- Allow only the supported checkpoint reconstruction operations; never execute arbitrary pickle globals or Python code.
- Run inference in a cancellable background thread.
- Use temporary output files and publish a result only after a complete valid WAV has been written.
- Keep models, songs, stems and generated audio on-device.
- Keep audio length bounded until chunked processing and low-memory device testing are complete.

## Verification completed

- The native parser loaded a real public RVC v2 .pth checkpoint in CI.
- The native Android ARM64 PTH shared library compiled successfully.
- The runtime is linked against the app's ONNX Runtime 1.28.0 feature-extraction library.
- The Flutter bridge and song-cover screen have a native PTH route in source.

## Still required before calling it complete

1. Build and package the final ARM64 APK with the PTH library.
2. Run Flutter analysis and widget/unit tests on the integrated app.
3. Run an end-to-end conversion with a real 768-dimensional, 100-fps RVC v2 PTH checkpoint and real audio.
4. Verify the output is non-silent, genuinely converted, duration-aligned and mixed with the original accompaniment.
5. Implement and test standard FAISS retrieval before claiming .index support.
6. Test on a physical Samsung Galaxy A12: peak memory, elapsed time, heat, cancellation, low-storage behaviour and a full-length song.

Do not call direct PTH support complete until steps 1–4 pass. Do not call the Galaxy A12 supported until step 6 passes.
