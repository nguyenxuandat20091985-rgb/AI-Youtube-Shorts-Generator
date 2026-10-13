import asyncio
import json
import os
import shutil
import sys
from datetime import datetime, timezone

from modules.asset_manager import AssetManager
from modules.audio import AudioEngine
from modules.brain import ContentBrain
from modules.composer import Composer
from modules.seo import SeoWriter


def clean_cache():
    """Delete only generated temporary assets inside this project's assets directory."""
    project_root = os.path.abspath(os.getcwd())
    assets_root = os.path.abspath(os.path.join(project_root, "assets"))
    folders_to_clean = [
        os.path.join(assets_root, "audio_clips"),
        os.path.join(assets_root, "video_clips"),
        os.path.join(assets_root, "temp"),
    ]
    print("🧹 Cleaning temporary files...")
    for folder in folders_to_clean:
        folder_abs = os.path.abspath(folder)
        if not folder_abs.startswith(assets_root + os.sep):
            print(f"🚨 SECURITY ALERT: Refusing to clean {folder_abs}")
            continue
        if not os.path.isdir(folder_abs):
            continue
        for name in os.listdir(folder_abs):
            path = os.path.join(folder_abs, name)
            try:
                if os.path.islink(path) or os.path.isfile(path):
                    os.unlink(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
            except OSError as exc:
                print(f"⚠️ Could not delete {path}: {exc}")
    print("✨ Workspace clean!")


def validate_environment():
    missing = [name for name in ("GROQ_API_KEY", "PEXELS_API_KEY") if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing environment variable(s): {', '.join(missing)}")
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg is not installed or is not available on PATH.")


def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


async def main():
    print("🚀 STARTING THAO ANH AI SHORTS AUTOMATION...")
    try:
        validate_environment()
        print("✅ Environment and FFmpeg checks passed.")

        brain = ContentBrain()
        topic = brain.get_trending_topic()
        script = brain.generate_script(topic)
        if not script:
            raise RuntimeError("Script generation failed.")
        print(f"✅ Vietnamese script ready: {len(script)} scenes.")

        audio_engine = AudioEngine()
        script = await audio_engine.process_script(script)
        if len(script) < 2:
            raise RuntimeError("Not enough usable narration scenes.")

        asset_manager = AssetManager()
        assets_map = asset_manager.get_videos(script)
        ready_assets = sum(1 for pair in assets_map if pair)
        if ready_assets == 0:
            raise RuntimeError("No usable stock-video assets were downloaded.")
        print(f"✅ Video assets ready: {ready_assets}/{len(script)} scenes.")

        composer = Composer()
        final_scene_paths = composer.render_all_scenes(script, assets_map)
        if not final_scene_paths:
            raise RuntimeError("No scenes could be rendered.")

        output_path = composer.concatenate_with_transitions(final_scene_paths)
        if not output_path or not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("Final video was not created or is empty.")

        duration = composer.get_duration(output_path)
        if not 15 <= duration <= 40:
            raise RuntimeError(
                f"Final video duration is {duration:.2f}s; Shorts production target is 15-40 seconds. "
                "The video was not uploaded."
            )

        final_dir = os.path.abspath(os.path.dirname(output_path))
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_path = os.path.join(final_dir, f"thao_anh_ai_{timestamp}.mp4")
        os.replace(output_path, unique_path)
        print(f"🎉 Video rendered and validated: {unique_path}")
        print(f"📦 Final size: {os.path.getsize(unique_path) / (1024 * 1024):.1f} MB")
        print(f"⏱️ Duration: {duration:.2f}s")

        metadata = SeoWriter().generate(topic, script)
        metadata["topic"] = topic
        metadata["duration_seconds"] = round(duration, 2)
        metadata["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
        metadata_path = os.path.splitext(unique_path)[0] + ".json"
        _save_json(metadata_path, metadata)
        print(f"🔎 SEO metadata saved: {metadata_path}")
        print(f"📝 Title: {metadata['title']}")

        if os.getenv("AUTO_PUBLISH", "false").strip().lower() == "true":
            from modules.youtube_publisher import schedule_time_for_vietnam, upload_short

            publish_at = schedule_time_for_vietnam(hour=19, minute=30)
            result = upload_short(unique_path, metadata, publish_at=publish_at, privacy_status="private")
            result["topic"] = topic
            result["title"] = metadata["title"]
            result["video_path"] = unique_path
            result_path = os.path.splitext(unique_path)[0] + "_youtube.json"
            _save_json(result_path, result)
            if not result.get("video_id"):
                raise RuntimeError("YouTube upload returned no video ID.")
            print("✅ YOUTUBE UPLOAD ACCEPTED")
            print(f"🔗 Video URL: {result.get('url')}")
            print(f"🗓️ Scheduled publication (UTC): {result.get('publish_at')}")
            print(f"📄 Upload receipt: {result_path}")
        else:
            print("ℹ️ AUTO_PUBLISH is not enabled; video and SEO metadata were saved locally.")

        return unique_path
    except Exception as exc:
        print(f"❌ PIPELINE FAILED: {type(exc).__name__}: {exc}")
        return None
    finally:
        clean_cache()


if __name__ == "__main__":
    result = asyncio.run(main())
    if not result:
        sys.exit(1)
