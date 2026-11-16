import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.training.run_rvc_cpu_training import extract_audio_zip, safe_experiment_name, validate_epochs


def test_safe_experiment_name():
    assert safe_experiment_name("Red's Voice / 01") == "Red_s_Voice_01"


def test_validate_epochs():
    assert validate_epochs(10) == 10
    try:
        validate_epochs(7)
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported epoch count was accepted")


def test_zip_extraction_flattens_audio_and_ignores_traversal(tmp_path):
    archive_path = tmp_path / "dataset.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("nested/voice.wav", b"fake wav data")
        archive.writestr("../escape.wav", b"must not escape")
        archive.writestr("notes.txt", "not audio")
    destination = tmp_path / "audio"
    files = extract_audio_zip(archive_path, destination)
    assert len(files) == 1
    assert files[0].name == "0000.wav"
    assert files[0].read_bytes() == b"fake wav data"
    assert not (tmp_path / "escape.wav").exists()
