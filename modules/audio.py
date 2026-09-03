import asyncio
import os

import edge_tts
from dotenv import load_dotenv
from mutagen.mp3 import MP3

load_dotenv()


class AudioEngine:
    def __init__(self, voice=None):
        self.voice = voice or os.getenv("EDGE_TTS_VOICE", "en-US-AvaNeural")
        self.output_dir = os.path.join(os.getcwd(), "assets", "audio_clips")
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_audio(self, text, output_filename, retries=3):
        output_path = os.path.join(self.output_dir, output_filename)
        for attempt in range(retries):
            try:
                communicate = edge_tts.Communicate(text, self.voice, rate="+10%")
                await communicate.save(output_path)
                if not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
                    raise RuntimeError("Edge-TTS returned an empty audio file.")
                return output_path
            except Exception as exc:
                print(f"      ⚠️ Audio Error (Attempt {attempt + 1}/{retries}): {exc}")
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except OSError:
                        pass
                if attempt < retries - 1:
                    await asyncio.sleep(2)
        raise RuntimeError(f"Failed to generate audio after {retries} attempts.")

    def get_audio_duration(self, file_path):
        try:
            duration = float(MP3(file_path).info.length)
            if duration <= 0:
                raise ValueError("Audio duration is zero.")
            return duration
        except Exception as exc:
            print(f"❌ Error reading audio length: {exc}")
            return 0.0

    async def process_script(self, script_data):
        print(f"🎙️ Starting Audio Generation for {len(script_data)} scenes...")
        successful_scenes = []
        for scene in script_data:
            scene_id = scene["id"]
            try:
                file_path = await self.generate_audio(scene["text"], f"voice_{scene_id}.mp3")
                duration = self.get_audio_duration(file_path)
                if duration <= 0:
                    raise RuntimeError("Could not determine a valid audio duration.")
                scene["audio_path"] = file_path
                scene["duration"] = duration
                successful_scenes.append(scene)
                print(f"   ✅ Scene {scene_id}: {duration:.2f}s generated.")
                await asyncio.sleep(1)
            except Exception as exc:
                print(f"   ❌ Scene {scene_id} skipped: {exc}")

        if len(successful_scenes) < 2:
            raise RuntimeError("Fewer than 2 scenes have usable audio; aborting render.")
        return successful_scenes
