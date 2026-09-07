import os
import random
import time

import requests
from dotenv import load_dotenv


class AssetManager:
    def __init__(self):
        load_dotenv(override=True)
        self.api_key = os.getenv("PEXELS_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "PEXELS_API_KEY is not set. Create a .env file or set the environment variable before running."
            )
        self.base_url = "https://api.pexels.com/videos/search"
        self.headers = {"Authorization": self.api_key}
        self.assets_dir = os.path.join(os.getcwd(), "assets", "video_clips")
        os.makedirs(self.assets_dir, exist_ok=True)

    @staticmethod
    def _fallback_queries(query):
        words = [w for w in query.replace(",", " ").split() if len(w) > 2]
        candidates = []
        if words:
            candidates.append(" ".join(words[-3:]))
            candidates.append(words[-1])
        return list(dict.fromkeys(candidates))

    def search_video(self, query, duration_min=4):
        """Find a usable portrait stock clip, with retry/fallback queries."""
        query = str(query or "").strip() or "nature"
        queries = [query] + self._fallback_queries(query)

        for attempt, current_query in enumerate(queries[:3]):
            print(f"   🔍 Searching Pexels: '{current_query}'...")
            try:
                response = requests.get(
                    self.base_url,
                    headers=self.headers,
                    params={
                        "query": current_query,
                        "per_page": 8,
                        "orientation": "portrait",
                        "size": "medium",
                    },
                    timeout=20,
                )
                if response.status_code == 429:
                    print("      ⚠️ Pexels rate limit; waiting before retry...")
                    time.sleep(2)
                    continue
                response.raise_for_status()
                videos = response.json().get("videos", [])
                if not videos:
                    continue

                valid_videos = [v for v in videos if v.get("duration", 0) >= duration_min]
                selected_video = random.choice(valid_videos or videos)
                video_files = [
                    f for f in selected_video.get("video_files", [])
                    if f.get("link")
                ]
                if not video_files:
                    continue

                # Prefer a practical HD-sized source rather than an unnecessarily huge file.
                video_files.sort(
                    key=lambda f: (
                        abs((f.get("width", 0) or 0) - 1080),
                        (f.get("width", 0) or 0) * (f.get("height", 0) or 0),
                    )
                )
                return video_files[0]["link"]
            except requests.RequestException as exc:
                print(f"      ⚠️ Pexels request failed: {exc}")
                if attempt < len(queries[:3]) - 1:
                    time.sleep(1)
            except (ValueError, KeyError, TypeError) as exc:
                print(f"      ⚠️ Invalid Pexels response: {exc}")

        print(f"      ❌ No usable video found for '{query}'")
        return None

    def download_video(self, url, filename):
        """Download a video safely and atomically into the cache."""
        save_path = os.path.join(self.assets_dir, filename)
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            return save_path

        temp_path = save_path + ".part"
        try:
            with requests.get(url, stream=True, timeout=45) as response:
                response.raise_for_status()
                with open(temp_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
            if os.path.getsize(temp_path) == 0:
                raise RuntimeError("downloaded file is empty")
            os.replace(temp_path, save_path)
            return save_path
        except Exception as exc:
            print(f"      ❌ Error downloading {filename}: {exc}")
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass
            return None

    def get_videos(self, script_data):
        """Download two clips per scene and self-heal when one search fails."""
        print("🎥 Starting Double-Feature Video Download...")
        video_pairs = []

        for scene in script_data:
            scene_id = scene["id"]
            query_a = scene.get("visual_1") or scene.get("keywords") or "nature"
            query_b = scene.get("visual_2") or query_a

            path_a = None
            path_b = None
            url_a = self.search_video(query_a)
            if url_a:
                path_a = self.download_video(url_a, f"scene_{scene_id}_a.mp4")
            url_b = self.search_video(query_b)
            if url_b:
                path_b = self.download_video(url_b, f"scene_{scene_id}_b.mp4")

            if not path_a and path_b:
                path_a = path_b
                print(f"      ⚠️ Scene {scene_id}: using Clip B for both halves.")
            if not path_b and path_a:
                path_b = path_a
                print(f"      ⚠️ Scene {scene_id}: using Clip A for both halves.")

            if path_a and path_b:
                video_pairs.append((path_a, path_b))
                print(f"   ✅ Scene {scene_id} Ready (A + B).")
            else:
                print(f"   ❌ Scene {scene_id} has no usable video assets.")
                video_pairs.append(None)

        return video_pairs


if __name__ == "__main__":
    manager = AssetManager()
    print(manager.get_videos([{"id": 1, "visual_1": "city", "visual_2": "technology"}]))
