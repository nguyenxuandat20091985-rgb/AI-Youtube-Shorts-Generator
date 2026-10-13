# THAO ANH AI Autopilot Setup

This repository's THAO ANH AI autopilot workflow is merged into the default branch (`Main`). It can generate a Short and schedule it on YouTube after the required GitHub Actions secrets are configured.

## Required GitHub Actions secrets

- `GROQ_API_KEY`: Groq API key for topic/script/metadata generation.
- `PEXELS_API_KEY`: Pexels API key for portrait stock footage.
- `YOUTUBE_CLIENT_ID`: OAuth 2.0 client ID for a Google Cloud project.
- `YOUTUBE_CLIENT_SECRET`: OAuth 2.0 client secret.
- `YOUTUBE_REFRESH_TOKEN`: refresh token authorized for the intended YouTube channel.
- `YOUTUBE_EXPECTED_CHANNEL_ID`: exact channel ID allowed to receive uploads; the uploader stops if OAuth resolves to another channel.

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

The workflow starts at 11:30 UTC (18:30 Vietnam time). After rendering, the publisher targets the next 19:30 Vietnam-time slot and advances to the following day if the current slot is less than 15 minutes away. GitHub scheduled workflows run from the repository's default branch (`Main`). The workflow is present there, but runs safely skip generation or publishing when required secrets are missing.

## Safeguards and limitations

- The pipeline should fail instead of uploading when generation, metadata validation, or rendering fails.
- The publisher uploads as private and sets `publishAt` for scheduled release.
- YouTube API quota, OAuth validity, Pexels availability, Groq limits, Edge-TTS availability, and runner duration can interrupt a run.
- A video is considered uploaded only when the YouTube API returns a video ID.
- Before unattended runs, test with a private or unlisted video and verify the correct channel in YouTube Studio.


## First-run checklist (Android-friendly)

1. Open [repository Actions secrets](https://github.com/nguyenxuandat20091985-rgb/AI-Youtube-Shorts-Generator/settings/secrets/actions).
2. Add `GROQ_API_KEY` and `PEXELS_API_KEY` to enable video generation.
3. Add `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`, and `YOUTUBE_EXPECTED_CHANNEL_ID` to enable YouTube scheduling. Choose the exact channel in YouTube Studio first; never guess the channel ID.
4. Open [Actions](https://github.com/nguyenxuandat20091985-rgb/AI-Youtube-Shorts-Generator/actions/workflows/thao-anh-ai-autopilot.yml) → **THAO ANH AI - Daily Shorts Autopilot** → **Run workflow**. Keep `publish=false` for the first run to inspect the MP4 artifact before enabling uploads.
5. If the first artifact is valid, run again with `publish=true`. Confirm the returned Short URL and scheduled time in the run log and YouTube Studio.

Do not paste API keys, client secrets, or refresh tokens into chat, source code, commits, or workflow logs. If a first run reports missing configuration, add the missing values through GitHub Settings and rerun.
