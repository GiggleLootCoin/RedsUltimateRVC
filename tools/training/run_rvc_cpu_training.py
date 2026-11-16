#!/usr/bin/env python3
"""Run genuine single-speaker RVC v2 neural training on a CPU runner.

This uses the upstream RVC PyTorch generator/discriminator training loop.
It is not a dataset-only exporter or an inference-only model converter.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

AUDIO_EXTENSIONS = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aac", ".wma"}
MAX_ARCHIVE_BYTES = 1_073_741_824
MAX_UNPACKED_BYTES = 2_147_483_648
MAX_AUDIO_FILES = 500
MIN_AUDIO_SECONDS = 60.0


def safe_experiment_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip()).strip("_-")[:48]
    if not name:
        raise ValueError("Enter a voice name containing letters or numbers.")
    return name


def validate_epochs(value: int) -> int:
    if value not in (5, 10, 20, 40):
        raise ValueError("Choose 5, 10, 20 or 40 training epochs.")
    return value


def extract_audio_zip(archive_path: Path, destination: Path) -> list[Path]:
    if not archive_path.is_file() or archive_path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("Dataset ZIP is missing or exceeds the 1 GB download limit.")
    destination.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    total_size = 0
    with zipfile.ZipFile(archive_path) as archive:
        members = []
        for info in archive.infolist():
            path = PurePosixPath(info.filename.replace("\\", "/"))
            if info.is_dir() or path.is_absolute() or ".." in path.parts:
                continue
            if path.suffix.lower() not in AUDIO_EXTENSIONS:
                continue
            if info.file_size <= 0:
                continue
            total_size += info.file_size
            members.append(info)
        if total_size > MAX_UNPACKED_BYTES:
            raise ValueError("Unpacked audio exceeds the 2 GB workspace limit.")
        if len(members) > MAX_AUDIO_FILES:
            raise ValueError(f"Dataset has {len(members)} audio files; the limit is {MAX_AUDIO_FILES}.")
        for number, info in enumerate(members):
            suffix = Path(info.filename).suffix.lower()
            target = destination / f"{number:04d}{suffix}"
            with archive.open(info) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            if target.stat().st_size:
                extracted.append(target)
    if not extracted:
        raise ValueError("The ZIP contains no supported audio files.")
    return extracted


def audio_duration_seconds(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return max(0.0, float(result.stdout.strip()))


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def patch_cpu_loader(repo: Path) -> None:
    path = repo / "train" / "train.py"
    source = path.read_text(encoding="utf-8")
    replacements = (
        ("num_workers=4,", "num_workers=1,"),
        ("pin_memory=True,", "pin_memory=False,"),
        ("prefetch_factor=8,", "prefetch_factor=2,"),
    )
    for old, new in replacements:
        if source.count(old) != 1:
            raise RuntimeError(f"Upstream CPU loader patch anchor changed: {old}")
        source = source.replace(old, new, 1)
    path.write_text(source, encoding="utf-8")


def create_filelist(experiment: Path) -> int:
    import numpy as np

    wav_dir = experiment / "0_gt_wavs"
    feature_dir = experiment / "3_feature768"
    coarse_dir = experiment / "2a_f0"
    f0_dir = experiment / "2b-f0nsf"
    rows = []
    for wav in sorted(wav_dir.glob("*.wav")):
        stem = wav.stem
        feature = feature_dir / f"{stem}.npy"
        coarse = coarse_dir / f"{wav.name}.npy"
        continuous = f0_dir / f"{wav.name}.npy"
        if not (feature.is_file() and coarse.is_file() and continuous.is_file()):
            continue
        features = np.load(feature, mmap_mode="r", allow_pickle=False)
        f0_coarse = np.load(coarse, mmap_mode="r", allow_pickle=False)
        f0_continuous = np.load(continuous, mmap_mode="r", allow_pickle=False)
        if features.ndim != 2 or features.shape[1] != 768:
            continue
        if f0_coarse.size == 0 or f0_continuous.size == 0:
            continue
        rows.append("|".join(map(str, (wav.resolve(), feature.resolve(),
                                       coarse.resolve(), continuous.resolve(), 0))))
    if len(rows) < 2:
        raise RuntimeError(f"Only {len(rows)} valid feature/F0 records were prepared; at least 2 are required.")
    (experiment / "filelist.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"Prepared {len(rows)} aligned audio/feature/pitch records.", flush=True)
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-zip", required=True, type=Path)
    parser.add_argument("--voice-name", required=True)
    parser.add_argument("--epochs", required=True, type=int)
    parser.add_argument("--rvc-root", type=Path, default=Path("rvc-engine"))
    parser.add_argument("--output", type=Path, default=Path("training-output"))
    args = parser.parse_args()

    name = safe_experiment_name(args.voice_name)
    epochs = validate_epochs(args.epochs)
    repo = args.rvc_root.resolve()
    if not (repo / "train" / "train.py").is_file():
        raise RuntimeError("Pinned upstream RVC training source is missing.")

    workspace = Path("training-work").resolve()
    input_dir = workspace / "input"
    experiment = repo / "logs" / name
    if workspace.exists():
        shutil.rmtree(workspace)
    if experiment.exists():
        shutil.rmtree(experiment)
    workspace.mkdir(parents=True)

    audio_files = extract_audio_zip(args.dataset_zip.resolve(), input_dir)
    durations = []
    for path in audio_files:
        try:
            durations.append(audio_duration_seconds(path))
        except (subprocess.CalledProcessError, ValueError):
            print(f"Skipping unreadable audio: {path.name}", flush=True)
    total_seconds = sum(durations)
    if total_seconds < MIN_AUDIO_SECONDS:
        raise ValueError(f"Only {total_seconds:.1f} seconds of readable audio; at least 60 seconds is required.")
    print(f"Dataset: {len(durations)} readable files, {total_seconds / 60:.1f} minutes.", flush=True)
    if total_seconds < 600:
        print("Quality note: the upstream RVC project recommends about 10 minutes or more of clean voice audio.", flush=True)

    env = os.environ.copy()
    env.update({
        "OMP_NUM_THREADS": "2",
        "MKL_NUM_THREADS": "2",
        "OPENBLAS_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "PYTHONUNBUFFERED": "1",
        "CUDA_VISIBLE_DEVICES": "",
    })
    python = sys.executable

    run([python, "train/preprocess.py", str(input_dir), "48000", "2",
         str(experiment), "False", "3.7"], cwd=repo, env=env)
    gt_count = len(list((experiment / "0_gt_wavs").glob("*.wav")))
    wav16_count = len(list((experiment / "1_16k_wavs").glob("*.wav")))
    if gt_count < 2 or wav16_count < 2:
        raise RuntimeError("RVC audio preprocessing did not create enough usable training segments.")

    run([python, "train/dataset/extract_f0.py", "cpu", str(experiment), "1", "pm"],
        cwd=repo, env=env)
    run([python, "train/dataset/extract_hubert_feature.py", "cpu", "1", "0",
         str(experiment), "v2", "false"], cwd=repo, env=env)

    config_source = repo / "configs" / "v2" / "48k.json"
    if not config_source.is_file():
        raise RuntimeError("The pinned RVC v2 48 kHz training configuration is missing.")
    experiment.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config_source, experiment / "config.json")
    record_count = create_filelist(experiment)

    generator = repo / "assets" / "pretrained_v2" / "f0G48k.pth"
    discriminator = repo / "assets" / "pretrained_v2" / "f0D48k.pth"
    if not generator.is_file() or not discriminator.is_file():
        raise RuntimeError("RVC v2 48 kHz pretrained generator/discriminator weights are missing.")

    patch_cpu_loader(repo)
    run([python, "train/train.py", "-e", name, "-sr", "48k", "-f0", "1",
         "-bs", "1", "-te", str(epochs), "-se", "5",
         "-pg", str(generator), "-pd", str(discriminator),
         "-l", "1", "-c", "0", "-sw", "1", "-v", "v2"],
        cwd=repo, env=env)

    model = repo / "assets" / "weights" / f"{name}.pth"
    if not model.is_file() or model.stat().st_size < 10_000_000:
        raise RuntimeError("RVC training finished without producing a valid inference-ready .pth model.")

    index_dir = repo / "assets" / "indices"
    run([python, "train/train_index.py", name, "v2", str(index_dir), "1", "single"],
        cwd=repo, env=env)
    index_candidates = sorted((repo / "logs" / name).glob("added*.index"))
    if not index_candidates:
        raise RuntimeError("RVC training produced a model but no retrieval index.")
    index = index_candidates[-1]

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    package = output / f"{name}_RVC_v2_48k.zip"
    metadata = (
        "RED'S ULTIMATE RVC — TRAINED VOICE MODEL\n"
        f"Voice: {name}\nArchitecture: upstream RVC v2, 48 kHz, F0 enabled\n"
        f"Epochs: {epochs}\nAligned training records: {record_count}\n"
        f"Readable source audio: {total_seconds / 60:.2f} minutes\n"
        "Training: genuine PyTorch generator/discriminator optimization on CPU\n"
        "Includes: inference-ready .pth model and retrieval .index\n"
        "This was trained by the pinned upstream RVC implementation; it is not a renamed pretrained voice.\n"
    )
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(model, f"{name}.pth")
        archive.write(index, f"{name}.index")
        archive.writestr("TRAINING_INFO.txt", metadata)
    print(f"TRAINING_COMPLETE={package}", flush=True)
    print(f"MODEL_BYTES={model.stat().st_size}", flush=True)
    print(f"INDEX_BYTES={index.stat().st_size}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
