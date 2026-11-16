# Genuine neural RVC training

Red's Ultimate RVC now has an optional **real RVC v2 training workflow**. It uses the pinned upstream RVC PyTorch training engine to preprocess audio, extract pitch and HuBERT features, optimize the generator and discriminator networks, save an inference-ready checkpoint, and build a FAISS retrieval index.

## Important device and privacy facts

- The Galaxy A12 app still prepares and exports datasets locally; it does not run PyTorch neural training on the handset.
- The actual training runs on a GitHub-hosted CPU runner. It is free for this public-repository workflow, but CPU training can take hours and the job has a six-hour limit. There is no GPU acceleration.
- The workflow needs a direct HTTPS link to the exported ZIP. The link is supplied as a workflow input and the audio is downloaded to the runner. Do not use recordings you consider private or confidential with this hosted route.
- The workflow downloads public HuBERT and RVC pretrained weights from the upstream model repository. The resulting voice model is packaged as a ZIP containing an inference-ready `.pth`, its retrieval `.index`, and training metadata.
- The training workflow does not upload the raw dataset as an artifact. Only the finished model package is retained for 14 days.
- Use only audio you own or have permission to use.

## Run it from Android

1. In Red's Ultimate RVC, open **Voice Dataset Lab**, add or record your samples, choose **Prepare Local Dataset**, then **Export / Share Dataset Files**.
2. Upload that ZIP to a file host that can provide a direct HTTPS download URL. Use a temporary link if the host supports it.
3. Open [Train a genuine RVC voice model](https://github.com/GiggleLootCoin/RedsUltimateRVC/actions/workflows/train-rvc-cpu.yml).
4. Choose **Run workflow**, paste the direct HTTPS ZIP link, enter a voice name, and choose 5, 10, 20, or 40 epochs.
5. When the run succeeds, open its **Artifacts** section and download the trained voice ZIP.
6. Extract the ZIP on Android and import the `.pth` model into the app. The trained `.index` is included for use with compatible RVC interfaces, but the app's current native PTH conversion path does not yet blend a retrieval index. The app's PTH runtime accepts the supported RVC v2 768-dimensional / 100-fps profile; verify compatibility before relying on a newly trained model.

## Training configuration

- Upstream source pinned to `RVC-Project/Retrieval-based-Voice-Conversion-WebUI` commit `81eed5e8f68b6bed1789f682fe78cdd324495afc`.
- RVC v2, 48 kHz, F0-enabled model.
- CPU pitch extraction (Parselmouth), CPU HuBERT features, batch size 1, reduced DataLoader workers/prefetch, no CUDA.
- Epoch choices: 5, 10, 20, or 40. Five epochs is a smoke/initial run, not a promise of production-quality voice similarity. More epochs may improve fit but increase time and overfitting risk.
- Retrieval index is built from the same training feature set.

This is genuine neural model training, not merely dataset preparation. The hosted CPU route is an optional workaround; it is not on-device or offline training.
