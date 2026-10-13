import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from modules.youtube_publisher import schedule_time_from_now, upload_short


class TestYouTubePublisherValidation(unittest.TestCase):
    def test_schedule_time_is_in_the_future(self):
        value = schedule_time_from_now(20)
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        self.assertGreater(parsed, datetime.now(timezone.utc))

    def test_rejects_past_publish_time_before_api_call(self):
        with tempfile.NamedTemporaryFile(suffix=".mp4") as video:
            video.write(b"not-a-real-video-but-nonempty")
            video.flush()
            past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
            with self.assertRaisesRegex(ValueError, "must be in the future"):
                upload_short(
                    video.name,
                    {"title": "Test Short", "description": "Test description", "hashtags": []},
                    publish_at=past,
                )


if __name__ == "__main__":
    unittest.main()
