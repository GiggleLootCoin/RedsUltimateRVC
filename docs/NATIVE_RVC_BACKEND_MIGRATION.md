# Native RVC backend migration (ONNX-free target)

## Goal

Replace the current ONNX Runtime inference path with an Android-native inference backend that imports a user's real RVC v2 `.pth` checkpoint and converts audio locally. The shipped app must not require ONNX Runtime, ONNX model files, or an ONNX export step.

This is a backend replacement, not an extension rename. Do not label a checkpoint as runnable until a real conversion test passes.

## Current state verified on 2026-11-10

- The current Android pipeline loads HuBERT, RMVPE, the RVC encoder and decoder through ONNX Runtime.
- ncnn is currently only an optional decoder path; it does not replace the ONNX front end or encoder.
- The app's current inference engine expects exported model files. A file-picker acceptance of `.pth` does not make the checkpoint executable.
- The upstream Android converter inspected for reference also exports HuBERT, RMVPE and the RVC encoder to ONNX. It therefore does not satisfy this ONNX-free requirement.
- The current model converter and index converter screens are not a complete on-device `.pth` conversion solution.
- Existing CI can compile the current ONNX-based app, but that is not proof of working conversion on the target Galaxy A12.

## Target architecture

1. **Checkpoint reader and validator**
   - Read the original RVC checkpoint on-device or through a strictly local native conversion stage.
   - Validate checkpoint keys, RVC version, f0 support, sample rate, speaker embedding count and synthesizer geometry.
   - Support the final inference checkpoint from `weights/`; clearly reject training snapshots and unsupported variants.
   - Never upload private checkpoints or recordings.

2. **ONNX-free model execution**
   - Prototype direct PyTorch-to-ncnn/pnnx export for HuBERT/ContentVec, RMVPE, RVC encoder/flow and NSF-HiFiGAN decoder.
   - Run an operator-coverage audit for transformer attention, LayerNorm, convolution, transposed convolution, GRU, interpolation, STFT/mel and dynamic sequence lengths.
   - Implement missing operators natively or use a different ONNX-free runtime only if its Android ARM64 support and model parity are demonstrated.
   - Keep all inference stages on-device. ncnn is a candidate, not an assumed solution: do not ship until every stage passes parity and memory tests.

3. **Signal pipeline**
   - Resample input audio to the model's expected rate.
   - Extract 768-dimensional content features.
   - Estimate F0 and apply pitch shift / protection / unvoiced handling.
   - Run the RVC encoder/flow and NSF decoder with correct speaker conditioning.
   - Apply retrieval blending when a supported index is present.
   - Restore loudness and output WAV with chunking and crossfades to bound RAM.

4. **Index support**
   - Parse standard FAISS RVC indexes and convert vectors into the app's native retrieval format.
   - Validate 768-dimensional vectors, count, finite values, truncation and byte order.
   - Do not treat a renamed `.index` file as a converted index.

5. **Android integration**
   - Replace ONNX Runtime imports, dependencies, model assets, validation and execution in the Kotlin/native bridge.
   - Keep the UI's normal `.pth` and `.index` selection flow; provide clear compatibility errors.
   - Keep inference cancellable, progress-reporting, chunked and recoverable after interruption.
   - Target ARM64 Android 12 and low-memory Exynos devices; CPU fallback is mandatory. Vulkan is optional.

## Required proof before calling it complete

- Automated checkpoint-format tests for valid RVC v2 and rejected v1 / no-f0 / unsupported sample-rate / training snapshots.
- Numerical parity tests comparing every native stage and final converted waveform against the reference RVC PyTorch pipeline, with documented tolerances.
- Real standard FAISS index conversion and retrieval tests.
- CI build with no ONNX Runtime dependency or ONNX assets in the shipped inference path.
- APK install and end-to-end file conversion test on a physical Samsung Galaxy A12 / Exynos device, including a long file, cancellation, low-storage handling and repeated conversions.
- Confirm output is genuinely converted speech, not copied or pass-through input.
- Document APK size, peak memory, conversion speed, thermal behaviour and remaining unsupported checkpoint types.

## Guardrails

- Do not claim the ONNX-free backend is implemented until the above proof exists.
- Do not silently fall back to the old ONNX pipeline.
- Do not upload user voice models or recordings to cloud services.
- Do not change Little Red's Big Studio, RedAI or RED-LIVE.
- Preserve the existing app as a known-good baseline while the replacement backend is developed on this branch.
