# Red's Ultimate RVC — Product Redesign Blueprint

## Product definition

A standalone, Red-branded Android voice-production studio intended to provide the practical workflows of JackismyShephard's Ultimate RVC without requiring Colab, Kaggle, Hugging Face, cloud inference, subscriptions, API keys or a mandatory internet connection. The app must be honest about device limits and must never present a disabled or decorative control as a working feature.

## Required user outcomes

1. Convert speech or audio into the user's selected voice.
2. Create full-song covers: separate lead vocals from accompaniment, convert vocals, recombine and export.
3. Manage voice models and their companion assets in one library.
4. Prepare datasets and provide a real training workflow where the device can support it; never call dataset preparation training.
5. Preview, compare, trim/split, cache, resume long conversions where safe, play, save and share results.
6. Provide advanced conversion controls with sensible defaults and plain-language explanations.
7. Keep the interface English-only, premium black/crimson, responsive on Android phones and branded as Red's own product.

## Import contract — make file handling understandable

The import screen accepts ZIP, PTH, PT, ONNX, INDEX and MOBILE.INDEX, but acceptance is not the same as executable compatibility.

- ZIP is the preferred user experience: inspect it, identify its contents, validate files and build a model package automatically.
- PTH / PT: import and inspect checkpoint metadata. The app must have a real conversion path before enabling inference. Never pretend the raw checkpoint is executable by the ONNX runtime.
- ONNX: supported inference model when architecture, version and required metadata are compatible.
- INDEX: optional retrieval feature, not a standalone voice model. Standard FAISS index support requires a real compatible reader/conversion implementation.
- MOBILE.INDEX: optional companion only when it passes the mobile index format validator.
- HuBERT/ContentVec and RMVPE or equivalent feature assets are engine dependencies, not extra mysteries the user should have to find individually. Bundle compatible base assets with the app where licensing permits, and explain any genuinely model-specific missing component.

The app should show one clear status per imported package: READY, NEEDS CONVERSION, MISSING COMPANION ASSET or INVALID. Never activate Convert until a compatible voice model and required runtime assets are available. If index retrieval is absent, conversion without an index should remain possible; index must not be a mandatory gate.

## Core screens

- **Studio Home** — prominent Convert Speech/Audio and Create Song Cover actions; clear current voice selection and task status.
- **Voice Library** — import ZIP or individual files, auto-detect packages, validate, preview, rename, export and delete.
- **Convert** — choose input, voice, optional index/retrieval, pitch and protection settings; show real progress, cancel, resume where supported, preview and export.
- **Song Covers** — choose song, separate vocals locally, convert lead vocal, mix with backing, preview A/B and export. A single main action with preflight checks and exact missing-item explanations.
- **Speech Studio** — record or import speech, convert and play back.
- **Dataset & Training Lab** — record/import/clean/label/split samples, inspect dataset quality, configure and launch genuine on-device training only if a supported training backend and device profile exist. Otherwise label training unavailable on this device; never fake progress or output.
- **Audio Studio** — playback, waveform/trim/split, gain, mix, compare, cache and share.
- **Settings** — quality/speed presets, storage cleanup, privacy and diagnostics.

## Engine architecture

1. **ModelPackageInspector** — safely unpack ZIPs, prevent path traversal, inventory files, inspect metadata and produce a local manifest.
2. **ModelCompatibilityRegistry** — maps checkpoint architecture/version to a real supported backend. It must not equate extension with compatibility.
3. **ConversionBackend** — select a backend based on the imported model. ONNX inference remains one backend, not the user-facing product requirement. A genuine PTH path must be implemented and tested before PTH is marked READY.
4. **RetrievalIndexService** — optional retrieval with format detection. Missing or incompatible index falls back to conversion without retrieval if the selected voice model supports it.
5. **FeatureAssetManager** — package shared HuBERT/RMVPE assets where possible; validate checksums and keep the setup local.
6. **SongCoverPipeline** — preflight, decode, vocal separation, conversion, alignment/mix, preview/export. Each stage reports progress/errors and releases memory promptly.
7. **AudioWorkspace** — app-private project folders, safe temp cleanup, playback, trim/split, A/B compare, resumable chunks and export/share.
8. **TrainingBackend** — separate real trainer from dataset preparation. Do not advertise on-device training until model, native runtime, memory requirements and training output have passed tests on target hardware.

## Galaxy A12 safety and performance

The Galaxy A12 is a constrained ARM64 device. The current upstream ONNX approach was validated on far more powerful hardware; full-song source separation and conversion must be profiled for RAM, thermal load, duration, crash recovery and audio integrity. Use chunked processing, bounded concurrency, low-memory presets and explicit duration estimates. If a task cannot safely run on this handset, report that before starting rather than freezing or silently failing.

## Redesign implementation gates

- Gate 1: fix navigation and button state; remove mandatory index gating; add preflight diagnostics and visible error reasons.
- Gate 2: reliable ZIP inspection and model-library packaging; ONNX remains a supported backend.
- Gate 3: implement and test actual PTH/PT conversion or a compatible direct inference backend. Do not mark ready before it exists.
- Gate 4: standard FAISS index compatibility as optional retrieval; conversion must work without an index.
- Gate 5: song-cover pipeline tests with known input/output audio and objective integrity checks.
- Gate 6: genuine training backend only if a viable on-device implementation is proven; otherwise preserve a useful dataset-preparation workspace without falsely advertising training.
- Gate 7: install and run on Galaxy A12, including long-song memory/heat testing.

## Acceptance criteria

- User can import a ZIP as the normal path and gets one clear compatibility result.
- Index is optional; it never disables conversion by itself.
- Convert and Create Song Cover are enabled only when their true prerequisites are satisfied.
- Every disabled action explains exactly what is missing.
- A successful task creates a playable, saveable output file.
- Full-song processing has progress, cancellation, safe memory limits and useful error reporting.
- All advertised capabilities have automated tests and handset evidence.