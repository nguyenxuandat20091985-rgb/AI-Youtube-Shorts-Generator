"""YouTube Data API uploader using a pre-authorized OAuth refresh token."""
import os
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube.upload"

def _required_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def youtube_client():
    credentials = Credentials(
        token=None,
        refresh_token=_required_env("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=_required_env("YOUTUBE_CLIENT_ID"),
        client_secret=_required_env("YOUTUBE_CLIENT_SECRET"),
        scopes=[YOUTUBE_SCOPE],
    )
    return build("youtube", "v3", credentials=credentials, cache_discovery=False)

def upload_short(video_path, metadata, publish_at=None, privacy_status="private"):
    """Upload a validated MP4; optionally schedule public release in UTC."""
    if not os.path.isfile(video_path) or os.path.getsize(video_path) == 0:
        raise RuntimeError(f"Video file is missing or empty: {video_path}")
    title = str(metadata.get("title", "")).strip()
    description = str(metadata.get("description", "")).strip()
    if not title or not description:
        raise RuntimeError("Video title and description are required before upload.")
    if privacy_status not in {"private", "unlisted", "public"}:
        raise ValueError("privacy_status must be private, unlisted, or public.")
    status = {"privacyStatus": privacy_status, "selfDeclaredMadeForKids": False}
    if publish_at:
        scheduled = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
        if scheduled.tzinfo is None:
            raise ValueError("publish_at must include a timezone.")
        if scheduled <= datetime.now(timezone.utc):
            raise ValueError("publish_at must be in the future.")
        status["privacyStatus"] = "private"
        status["publishAt"] = scheduled.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": [str(tag).lstrip("#")[:100] for tag in metadata.get("hashtags", [])][:30],
            "categoryId": "28",
            "defaultLanguage": "vi",
        },
        "status": status,
    }
    youtube = youtube_client()
    expected_channel_id = _required_env("YOUTUBE_EXPECTED_CHANNEL_ID")
    channel_response = youtube.channels().list(part="id,snippet", mine=True, maxResults=5).execute()
    channel_ids = [item.get("id") for item in channel_response.get("items", [])]
    if expected_channel_id not in channel_ids:
        raise RuntimeError(
            "Authorized YouTube account does not match YOUTUBE_EXPECTED_CHANNEL_ID. "
            "Upload was stopped to prevent publishing to the wrong channel."
        )
    print(f"Verified YouTube channel ID: {expected_channel_id}")
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(video_path, mimetype="video/mp4", resumable=True),
    )
    response = request.execute()
    video_id = response.get("id")
    return {
        "video_id": video_id,
        "url": f"https://www.youtube.com/shorts/{video_id}" if video_id else None,
        "privacy_status": response.get("status", {}).get("privacyStatus"),
        "publish_at": response.get("status", {}).get("publishAt"),
    }

def schedule_time_from_now(minutes=60):
    """Return an ISO-8601 UTC time sufficiently in the future for scheduled publishing."""
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
