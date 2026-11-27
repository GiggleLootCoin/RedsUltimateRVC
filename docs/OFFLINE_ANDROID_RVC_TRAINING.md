# Offline RVC training on Android: compatibility and limits

## Important: this is not a one-click option for every phone

The full RVC v2 training pipeline is not lightweight. It performs audio preprocessing, F0 extraction, HuBERT feature extraction, generator/discriminator neural training, and FAISS index construction. The upstream project documents these as separate compute-heavy stages. See the upstream [training guide](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/main/docs/en/training_tips_en.md).

A community Termux/Ubuntu route exists for running RVC locally on Android. Its published requirements list approximately 6 GB RAM as a minimum and 8 GB+ as recommended, and explicitly warn that training may overheat or crash phones. The guide recommends mobile inference rather than training. See [RVC Termux Android](https://docs.aihub.gg/rvc/local/rvc-termux-android/).

## Galaxy A12 compatibility

The Galaxy A12 configuration targeted by this project has 4 GB RAM. That is below the published 6 GB minimum for the Termux route. Therefore this project does **not** advertise full offline RVC neural training on the A12 as supported or reliable. Forcing it could cause repeated process kills, severe slowdown, overheating, or failed training.

## What can be done offline on the A12

- Record and organize voice samples in the app.
- Prepare and export a local training dataset ZIP.
- Import an already-trained, compatible RVC v2 voice model.
- Run supported native PTH or ONNX conversion locally after the required model/runtime files are installed.
- Convert audio and create a song cover locally when the required vocal-separation model is already installed.

Initial downloads and model setup require internet. After the models are present, supported conversion can run offline. Do not assume every .pth file is compatible: this build's native PTH path targets a specific RVC v2 768-dimensional / 100-fps profile.

## Offline training on a more capable Android device

On an ARM64 Android phone with at least 6 GB RAM (8 GB+ recommended), the experimental route is:

1. Install Termux from its official source.
2. Install the Ubuntu environment with proot-distro.
3. Install the CPU-only Python/PyTorch dependencies and the pinned RVC training source.
4. Download HuBERT and RVC pretrained weights while online.
5. Run the full preprocessing, F0, HuBERT, PyTorch training, and FAISS-index stages locally.
6. Keep the dataset, checkpoints, model and index on local storage. Once all dependencies and weights are present, the training process itself does not need to upload the voice recordings.

Use the community guide for the exact current commands and ARM64 dependency patches: https://docs.aihub.gg/rvc/local/rvc-termux-android/

This is an experimental community setup, not a tested feature of Red's Ultimate RVC. It has not been validated on the Galaxy A12, and the project must not claim that a successful inference build proves that on-device training works.

## Private training option

The optional GitHub Actions CPU workflow in this repository is not offline: it downloads the dataset from a direct HTTPS URL and trains on a hosted runner. The repository and workflow logs are public, so do not send private or confidential voice recordings through that route. Use only recordings you own or have permission to use.

## Model acceptance checks

A trained model is not considered ready merely because a training process exits successfully. Verify that:

- The inference-ready small .pth checkpoint is exported, not a large intermediate G/D checkpoint.
- The .index was built from the same voice experiment and has compatible feature dimensions.
- The model metadata contains the expected sample rate, F0 setting, version, and feature profile.
- The Android app validates the model before enabling conversion.
- A known test WAV converts to a non-empty output WAV that can be decoded and played.
- A song-cover test completes separation, vocal conversion, mix-back, playback, and save.

No model should be labelled tested on the A12 until those checks are run on the physical handset.
