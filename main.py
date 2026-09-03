import asyncio
import os
import shutil

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


async def main():
    print("🚀 STARTING AUTOMATION...")

    try:
        brain = ContentBrain()
        topic = brain.get_trending_topic()
        script = brain.generate_script(topic)
        if not script:
            raise RuntimeError("Script generation failed.")

        audio_engine = AudioEngine()
        script = await audio_engine.process_script(script)

        asset_manager = AssetManager()
        assets_map = asset_manager.get_videos(script)
        if not assets_map:
            raise RuntimeError("No usable stock-video assets were downloaded.")

        composer = Composer()
        final_scene_paths = composer.render_all_scenes(script, assets_map)
        if not final_scene_paths:
            raise RuntimeError("No scenes could be rendered.")

        output_path = composer.concatenate_with_transitions(final_scene_paths)
        if not output_path or not os.path.isfile(output_path):
            raise RuntimeError("Final video was not created.")

        print(f"🎉 DONE: {output_path}")
        return output_path
    except Exception as exc:
        print(f"❌ PIPELINE FAILED: {exc}")
        return None
    finally:
        clean_cache()


if __name__ == "__main__":
    asyncio.run(main())
