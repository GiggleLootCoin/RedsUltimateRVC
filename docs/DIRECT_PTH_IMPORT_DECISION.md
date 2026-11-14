# Direct RVC .pth import — implementation decision

Status: engineering decision; implementation and device verification are still required.

## User-facing contract

Red's Ultimate RVC must accept a normal trained RVC voice checkpoint (`.pth`) as the voice-model input. The user must not be asked to obtain or select an ONNX file. A matching standard RVC `.index` is optional. The app must report unsupported checkpoint variants accurately and must never mark a stored file as runnable merely because its extension is accepted.

The app must process a selected song into a converted-voice song: decode supported audio, separate vocals and accompaniment, convert the vocal stem, mix it back with the accompaniment, and export a playable audio file.

## Chosen implementation path

Use the existing Android RVC v2 ONNX Runtime pipeline as an internal execution detail, and add a native C++ checkpoint importer/exporter:

1. Import the original `.pth` with Android's Storage Access Framework into app-private storage.
2. Parse the PyTorch zip container and its restricted tensor-checkpoint pickle representation in C++; never execute arbitrary pickle globals or Python code.
3. Validate the checkpoint before conversion: RVC v1/v2, F0/no-F0 variant, sample rate, speaker count, required tensor names, dimensions, dtype, storage bounds, and tensor byte counts. Reject training snapshots and unknown architectures with a useful message.
4. Generate the exact RVC ONNX graph expected by the existing Android inference engine. The generated ONNX is an internal cached runtime artefact, not a file the user must supply.
5. Cache by source-file SHA-256 plus exporter version. Reuse a valid cache; invalidate it when the source or exporter changes.
6. Open the generated graph with ONNX Runtime and validate its actual input/output signature before showing the voice as READY.
7. Convert the optional standard FAISS index into the app's actual mobile retrieval format, validating vector dimension, count, finite values, and index compatibility. If conversion is unavailable or fails, allow conversion without retrieval rather than pretending the index is active.
8. Run the existing local vocal-separation → RVC conversion → instrumental mix-back path. Keep audio and models on-device.

This path is preferable to embedding Python/PyTorch on a low-memory Galaxy A12. It reuses the already-integrated Android inference runtime and avoids shipping a second full neural-network runtime. The native RVC-GGML experiment remains a separate engineering prototype; it must not be presented as the direct-`.pth` solution until a verified exporter for its complete HuBERT/RMVPE/voice/index asset set exists.

## Security and Android requirements

- Treat `.pth` as untrusted input. Bound archive entry count, total uncompressed size, tensor dimensions, pickle stack depth, memo size, and all offsets before allocation or file access.
- Allow only the small set of PyTorch checkpoint reconstruction operations needed to read tensor metadata. Reject unknown opcodes/globals; never invoke them.
- Stream tensor data from ZIP entries where possible. Do not load a full model plus duplicate full model buffers into RAM.
- Use cancellable background work, progress stages, temporary files, atomic cache publication, and cleanup after failure.
- Use Android SAF so Samsung My Files can select `.pth` and `.index` files even when extension filters grey them out.
- Do not upload voice models, source songs, stems, or generated audio to a server.
- Keep the app's existing ONNX inference code only as the internal execution engine. Do not ask the user to find, download, or manually convert ONNX models.

## Required acceptance tests

1. Valid RVC v2 F0 `.pth` checkpoint imports, exports, passes ONNX Runtime signature validation, and produces non-silent converted audio.
2. Valid RVC v2 no-F0 checkpoint is either supported end-to-end or rejected explicitly as unsupported; it must not be misidentified as F0.
3. RVC v1, malformed ZIP, malformed pickle, truncated tensor storage, impossible dimensions, unsupported dtype, and arbitrary pickle globals are rejected safely.
4. Generated ONNX output is compared numerically and audibly with the reference RVC PyTorch implementation on fixed test audio. Test both short speech and singing.
5. Optional matching FAISS index improves/changes retrieval output when enabled; missing, mismatched, and corrupt indexes are safely bypassed or rejected with a clear message.
6. End-to-end song-cover test proves the output vocals are genuinely converted, the instrumental remains present, durations are aligned, and the final WAV is playable.
7. CI builds the ARM64 APK and runs parser/exporter tests with sanitizers or equivalent bounds checks on host.
8. Physical Samsung Galaxy A12 / Exynos test records peak memory, elapsed time, thermal behaviour, cancellation, low-storage handling, and a full-song result. CI compilation alone is not device acceptance.

## Release gate

Do not call direct `.pth` support complete until tests 1–6 pass with real RVC checkpoints and audio. Do not call the Galaxy A12 supported until test 8 passes on that handset. Keep the existing known-good app baseline intact while implementing this on the native feature branch.
