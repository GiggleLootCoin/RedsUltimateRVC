# Direct PTH backend — Android ARM64

## Goal

Provide a genuine on-device RVC v2 voice-conversion route that accepts a compatible trained .pth voice checkpoint directly. The user must not have to export the voice model to ONNX or supply separate GGUF files.

The PTH voice checkpoint is executed by the native C RVC engine. The app still uses its bundled ONNX Runtime feature models for ContentVec/HuBERT and RMVPE, and Sherpa-ONNX for local vocal separation. This is not an ONNX-free application.

## Verified engineering state (2026-11-14)

- A real public RVC v2 .pth checkpoint was loaded by the native parser in CI.
- The native PTH inference shared library compiled for Android ARM64.
- The feature-extraction path was aligned to the app's actual ContentVec and RMVPE model signatures and preprocessing.
- The Flutter method-channel bridge and song-cover UI have a direct PTH route in source.
- APK packaging and end-to-end song conversion are still being verified.
- Physical Samsung Galaxy A12 testing has not yet been completed.

## Runtime pipeline

1. Import the .pth checkpoint into app-private storage.
2. Validate the model profile and load its tensors with the restricted native PTH reader.
3. Decode the song and separate vocals/accompaniment locally.
4. Resample the vocal stem to 16 kHz for ContentVec and RMVPE.
5. Run ContentVec with its source and padding_mask inputs; repeat 50-Hz features to the 100-Hz RVC frame rate.
6. Build the RMVPE mel spectrogram with the app's 1024-point FFT, 160-sample hop, 128 mel bins, 30–8000 Hz range and matching log-energy scaling.
7. Run RMVPE pitch extraction and coarse-pitch quantisation.
8. Run the native RVC v2 generator and write a WAV at the model's sample rate.
9. Align and mix the converted vocals with the original accompaniment.

## Supported profile

- RVC v2 F0 checkpoint.
- 768-dimensional ContentVec features.
- 100-fps frame rate.
- 32 kHz, 40 kHz or 48 kHz output sample rate.

Other checkpoint dimensions/frame rates are rejected. Compatible standard FAISS `.index` files can be converted locally to `.mobile.index` for ONNX inference. The native PTH route also loads the retained original `.index` through the FAISS runtime, searches nearest neighbours for each ContentVec frame, reconstructs vectors and blends them at the selected retrieval strength. A `.mobile.index` file alone does not contain the original FAISS search structure, so native PTH retrieval needs the original `.index` alongside it. `.pt` and ZIP archives remain storage-only.

## Dependencies and licensing

- Spartacvc, Apache-2.0: native PTH checkpoint parsing and RVC C inference.
- ONNX Runtime Android 1.28.0: bundled ContentVec/HuBERT and RMVPE feature extraction.
- Sherpa-ONNX v1.13.8: local Spleeter vocal/accompaniment separation.
- The voice model, audio and output remain on-device.

## Performance and release gate

The native PTH pipeline now processes 15-second centre windows with one-second context and a short overlap to reduce peak feature-tensor memory. It retains a 10-minute input guard, but peak-memory profiling, elapsed-time measurement and low-memory Android testing are still required. A compiled native library is not proof of acceptable speed, audio quality or stability.

Before a public release:
- Package the PTH library in the APK and pass Flutter/native regression tests.
- Run a real compatible PTH voice checkpoint through the full song-cover path.
- Confirm non-silent converted vocals, correct duration, accompaniment preservation and valid WAV output.
- Run retrieval-enabled full-song acceptance with a matching PTH checkpoint and original FAISS `.index`; verify feature blending, output audio and zero-index-rate fallback.
- Test a full-length song on a physical Samsung Galaxy A12 and record memory, elapsed time, thermal behaviour, cancellation and low-storage handling.
- Keep the public release gate manual and restricted to main after acceptance.

## Guardrails

- Do not label .pt, ZIP, unsupported .pth variants or standard FAISS indexes as runnable.
- Do not claim arbitrary PTH support.
- Do not upload user voice models, recordings, stems or generated audio to a server.
- Keep all unrelated projects and repositories untouched.
