import os
import shutil
import unittest


class SmokeTests(unittest.TestCase):
    def test_ffmpeg_available(self):
        self.assertIsNotNone(shutil.which("ffmpeg"), "FFmpeg must be installed and available on PATH")

    def test_brain_default_model(self):
        from modules.brain import DEFAULT_MODEL
        self.assertEqual(DEFAULT_MODEL, "openai/gpt-oss-20b")

    def test_required_project_dirs(self):
        for path in ("assets", "modules"):
            self.assertTrue(os.path.isdir(path), f"Missing project directory: {path}")


if __name__ == "__main__":
    unittest.main()
