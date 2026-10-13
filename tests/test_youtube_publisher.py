import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from modules.youtube_publisher import schedule_time_for_vietnam, upload_short


class TestYouTubePublisherValidation(unittest.TestCase):
    def test_schedule_time_targets_1930_vietnam_or_next_day(self):
        value = schedule_time_for_vietnam(19, 30)
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        local = parsed.astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
        self.assertEqual((local.hour, local.minute, local.second), (19, 30, 0))
        self.assertGreater(parsed, datetime.now(timezone.utc) + timedelta(minutes=14))

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
