import os
import shutil


def test_ffmpeg_available():
    assert shutil.which("ffmpeg"), "FFmpeg must be installed and available on PATH"


def test_brain_default_model():
    # Import should not require an API call.
    from modules.brain import DEFAULT_MODEL
    assert DEFAULT_MODEL == "openai/gpt-oss-20b"


def test_required_project_dirs():
    for path in ("assets", "modules"):
        assert os.path.isdir(path), f"Missing project directory: {path}"
