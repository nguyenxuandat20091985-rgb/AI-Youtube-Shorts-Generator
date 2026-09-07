import asyncio
import os
import shutil
import shutil as _shutil

from modules.asset_manager import AssetManager
from modules.audio import AudioEngine
from modules.brain import ContentBrain
from modules.composer import Composer


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
    """Fail early with actionable messages instead of waiting for a pipeline error."""
    missing = [name for name in ("GROQ_API_KEY", "PEXELS_API_KEY") if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing environment variable(s): {', '.join(missing)}")
    if _shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg is not installed or is not available on PATH.")


async def main():
    print("🚀 STARTING AI YOUTUBE SHORTS AUTOMATION...")
    try:
        validate_environment()
        print("✅ Environment and FFmpeg checks passed.")

        brain = ContentBrain()
        topic = brain.get_trending_topic()
        script = brain.generate_script(topic)
        if not script:
            raise RuntimeError("Script generation failed.")
        print(f"✅ Script ready: {len(script)} scenes.")

        audio_engine = AudioEngine()
        script = await audio_engine.process_script(script)
        if not script:
            raise RuntimeError("Voice generation failed.")

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
        print(f"✅ Rendered scenes: {len(final_scene_paths)}.")

        output_path = composer.concatenate_with_transitions(final_scene_paths)
        if not output_path or not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("Final video was not created or is empty.")

        print(f"🎉 DONE: {output_path}")
        print(f"📦 Final size: {os.path.getsize(output_path) / (1024 * 1024):.1f} MB")
        return output_path
    except Exception as exc:
        print(f"❌ PIPELINE FAILED: {type(exc).__name__}: {exc}")
        return None
    finally:
        clean_cache()


if __name__ == "__main__":
    asyncio.run(main())
