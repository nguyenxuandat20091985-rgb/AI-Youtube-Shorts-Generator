# THAO ANH AI Autopilot Setup

This repository can generate a Short and schedule it on YouTube after credentials are configured. The workflow is kept on a feature branch until reviewed and merged into the default branch.

## Required GitHub Actions secrets

- `GROQ_API_KEY`: Groq API key for topic/script/metadata generation.
- `PEXELS_API_KEY`: Pexels API key for portrait stock footage.
- `YOUTUBE_CLIENT_ID`: OAuth 2.0 client ID for a Google Cloud project.
- `YOUTUBE_CLIENT_SECRET`: OAuth 2.0 client secret.
- `YOUTUBE_REFRESH_TOKEN`: refresh token authorized for the intended YouTube channel.

Optional repository variables:

- `GROQ_MODEL`: model available to the Groq account; code defaults to `openai/gpt-oss-20b`.
- `EDGE_TTS_VOICE`: defaults to `vi-VN-HoaiMyNeural`.

Never put API keys or refresh tokens in repository files, commits, issue comments, or logs.

## One-time YouTube OAuth setup

1. In Google Cloud Console, create/select a project and enable **YouTube Data API v3**.
2. Configure the OAuth consent screen and create an OAuth client for a one-time local authorization flow.
3. Authorize the Google account that owns the intended THAO ANH AI channel with the `youtube.upload` scope.
4. Obtain a refresh token through a trusted local OAuth flow. Do not paste the refresh token into chat or commit it.
5. Add the three YouTube values as GitHub Actions secrets.
6. Confirm the channel identity in YouTube Studio before enabling unattended publishing.

An OAuth app in testing mode may issue refresh tokens that expire or be limited. Review Google's current consent-screen and verification requirements. Some API projects may have upload restrictions until compliance/audit requirements are satisfied.

## Schedule

The workflow starts at 11:30 UTC (18:30 Vietnam time) and requests publication 60 minutes later, approximately 19:30 Vietnam time. GitHub scheduled workflows run only from the repository's default branch, so this workflow will not run on schedule until merged into `Main`.

## Safeguards and limitations

- The pipeline should fail instead of uploading when generation, metadata validation, or rendering fails.
- The publisher uploads as private and sets `publishAt` for scheduled release.
- YouTube API quota, OAuth validity, Pexels availability, Groq limits, Edge-TTS availability, and runner duration can interrupt a run.
- A video is considered uploaded only when the YouTube API returns a video ID.
- Before unattended runs, test with a private or unlisted video and verify the correct channel in YouTube Studio.
