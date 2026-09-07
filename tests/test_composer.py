import os
import shutil
import subprocess
import tempfile
import unittest

from modules.composer import Composer


class ComposerPipelineTest(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp(prefix="youtube_shorts_test_")
        self.video_a = os.path.join(self.workdir, "a.mp4")
        self.video_b = os.path.join(self.workdir, "b.mp4")
        self.audio = os.path.join(self.workdir, "voice.mp3")

        self._run_ffmpeg(
            [
                "-f", "lavfi", "-i", "color=c=blue:s=720x1280:r=30",
                "-t", "2", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", self.video_a,
            ]
        )
        self._run_ffmpeg(
            [
                "-f", "lavfi", "-i", "color=c=green:s=720x1280:r=30",
                "-t", "2", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", self.video_b,
            ]
        )
        self._run_ffmpeg(
            [
                "-f", "lavfi", "-i", "sine=frequency=880:sample_rate=44100",
                "-t", "2", "-c:a", "libmp3lame", self.audio,
            ]
        )

    def tearDown(self):
        shutil.rmtree(self.workdir, ignore_errors=True)

    @staticmethod
    def _run_ffmpeg(args):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)

    def test_render_and_concatenate_short_pipeline(self):
        composer = Composer()
        composer.temp_dir = os.path.join(self.workdir, "temp")
        composer.final_dir = os.path.join(self.workdir, "final")
        os.makedirs(composer.temp_dir, exist_ok=True)
        os.makedirs(composer.final_dir, exist_ok=True)

        scenes = [
            {"id": 1, "audio_path": self.audio, "duration": 2.0},
            {"id": 2, "audio_path": self.audio, "duration": 2.0},
        ]
        pairs = [(self.video_a, self.video_b), (self.video_b, self.video_a)]

        rendered = composer.render_all_scenes(scenes, pairs)
        self.assertEqual(len(rendered), 2)

        final_path = composer.concatenate_with_transitions(rendered, "test_short.mp4")
        self.assertTrue(final_path)
        self.assertTrue(os.path.isfile(final_path))
        self.assertGreater(os.path.getsize(final_path), 10_000)

        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=width,height,codec_type",
             "-of", "json", final_path],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn('"width": 1080', probe.stdout)
        self.assertIn('"height": 1920', probe.stdout)
        self.assertIn('"codec_type": "audio"', probe.stdout)


if __name__ == "__main__":
    unittest.main()
