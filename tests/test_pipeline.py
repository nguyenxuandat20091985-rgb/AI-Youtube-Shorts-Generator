import os
import unittest
from unittest.mock import patch


class TestBrainHelpers(unittest.TestCase):
    def test_extract_json_array(self):
        from modules.brain import ContentBrain

        raw = '```json\n[{"id":1,"text":"Hello","visual_1":"city","visual_2":"street","mood":"hook"}]\n```'
        self.assertEqual(ContentBrain._extract_json_array(raw), '[{"id":1,"text":"Hello","visual_1":"city","visual_2":"street","mood":"hook"}]')

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key", "GROQ_MODEL": "openai/gpt-oss-20b"}, clear=False)
    def test_brain_normalizes_scene_ids(self):
        from modules.brain import ContentBrain

        brain = ContentBrain()
        scenes = [
            {"id": 99, "text": f"Voice line {i}", "visual_1": f"city scene {i}", "visual_2": f"road scene {i}", "mood": "hook"}
            for i in range(8)
        ]
        payload = __import__("json").dumps(scenes)
        with patch.object(brain, "_complete", return_value=payload):
            result = brain.generate_script("Test topic")
        self.assertEqual([scene["id"] for scene in result], list(range(1, 9)))
        self.assertEqual(result[1]["visual_2"], "road scene 1")


class TestAssetManagerHelpers(unittest.TestCase):
    @patch.dict(os.environ, {"PEXELS_API_KEY": "test-key"}, clear=False)
    def test_fallback_queries_are_deduplicated(self):
        from modules.asset_manager import AssetManager

        result = AssetManager._fallback_queries("melting ice lake")
        self.assertEqual(result, ["melting ice lake", "lake"])


class TestMainValidation(unittest.TestCase):
    def test_environment_validation_requires_keys_and_ffmpeg(self):
        import main

        with patch.dict(os.environ, {}, clear=True), patch("main.shutil.which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "GROQ_API_KEY"):
                main.validate_environment()

    @patch.dict(os.environ, {"GROQ_API_KEY": "x", "PEXELS_API_KEY": "y"}, clear=True)
    @patch("main.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_environment_validation_passes(self, _which):
        import main
        main.validate_environment()


if __name__ == "__main__":
    unittest.main()
