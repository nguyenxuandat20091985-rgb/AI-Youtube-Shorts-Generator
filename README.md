# 🎬 AutoShorts AI — Automated Faceless Shorts Generator

AutoShorts AI is a Python pipeline that turns a topic into a vertical short-form video: AI topic/script generation → Edge-TTS narration → Pexels stock footage → FFmpeg editing → final 9:16 MP4.

## ✨ Features

- 🧠 **AI scripting:** Groq's OpenAI-compatible API generates an 8–9 scene retention-focused script with two literal visual queries per scene.
- 🗣️ **Voiceover:** Edge-TTS with configurable voice and automatic duration detection.
- 🎞️ **Dual visuals:** Pexels portrait stock video A/B switching inside every scene.
- 🤖 **Avatar branding:** Optional avatar injection into up to two middle scenes.
- ✂️ **FFmpeg rendering:** 1080×1920 vertical output, H.264/AAC, `yuv420p`, `faststart`, and scene transitions.
- 🧹 **Safe cleanup:** Temporary audio/video files are removed only from the project's `assets` folders after each run.
- 🛡️ **Validation:** AI JSON and audio outputs are validated before rendering; failed audio scenes are removed cleanly instead of breaking scene/asset indexing.

## 📂 Project Structure

```text
AI-Youtube-Shorts-Generator/
├── assets/
│   ├── audio_clips/     # Generated narration (temporary)
│   ├── video_clips/     # Pexels downloads (temporary)
│   ├── temp/            # Intermediate renders (temporary)
│   ├── final/           # Final video output
│   └── avatar/          # Optional branding video
│       └── avatars.mp4
├── modules/
│   ├── brain.py         # Groq topic + script generation
│   ├── audio.py         # Edge-TTS narration
│   ├── asset_manager.py # Pexels search/download
│   └── composer.py      # FFmpeg scene rendering/stitching
├── main.py
├── .env.example
└── requirements.txt
```

## 🛠️ Requirements

- Python 3.10+
- FFmpeg installed and available on PATH
- Groq API key
- Pexels API key
- Internet access for Groq, Edge-TTS, and Pexels

Verify FFmpeg with:

```bash
ffmpeg -version
```

## 🚀 Setup

```bash
git clone https://github.com/nguyenxuandat20091985-rgb/AI-Youtube-Shorts-Generator.git
cd AI-Youtube-Shorts-Generator
python -m venv .venv
```

Activate the virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Create your environment file:

```bash
cp .env.example .env
```

On Windows PowerShell, use `Copy-Item .env.example .env` instead.

Set:

- `GROQ_API_KEY` — required for topic/script generation.
- `GROQ_MODEL` — optional; defaults to `llama-3.3-70b-versatile`.
- `PEXELS_API_KEY` — required for stock footage.
- `EDGE_TTS_VOICE` — optional; defaults to `en-US-AvaNeural`.

Optional avatar:

```text
assets/avatar/avatars.mp4
```

If the avatar file is absent, the pipeline simply renders stock footage.

## 🎮 Run

```bash
python main.py
```

The pipeline automatically selects a topic, generates the script, creates narration, downloads footage, renders scenes, stitches transitions, and writes:

```text
assets/final/final_short.mp4
```

Temporary audio/video/intermediate files are cleaned automatically after the run. The final output is preserved.

## 🔧 Troubleshooting

**`GROQ_API_KEY is not set`**

Copy `.env.example` to `.env` and add a valid Groq key.

**Pexels returns no usable footage**

Check the Pexels key, network connection, and search terms. The asset manager retries simplified queries and can reuse the available clip when only one side of an A/B pair is found.

**FFmpeg not found**

Install FFmpeg and make sure `ffmpeg -version` works from the same terminal used to run Python.

**Avatar is not injected**

Place the file exactly at `assets/avatar/avatars.mp4`. Avatar injection is optional and is limited to middle scenes.

**Final video playback problems**

The renderer exports H.264 video with `yuv420p` and `faststart` for broad player compatibility.

## 📜 License

MIT License.
