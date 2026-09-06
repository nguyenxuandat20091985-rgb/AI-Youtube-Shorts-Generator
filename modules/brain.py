import json
import os
import re

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

DEFAULT_MODEL = "openai/gpt-oss-20b"


def _get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your Groq API key."
        )
    return Groq(api_key=api_key)


class ContentBrain:
    """Generate a topic and validated scene plan using Groq."""

    def __init__(self):
        self.client = _get_client()
        self.model = os.getenv("GROQ_MODEL", DEFAULT_MODEL)

    def _complete(self, prompt, max_completion_tokens):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=max_completion_tokens,
            reasoning_effort="low",
            include_reasoning=False,
        )
        content = response.choices[0].message.content or ""
        if not content.strip():
            raise RuntimeError("The AI returned an empty response.")
        return content.strip()

    def get_trending_topic(self):
        prompt = (
            "Give exactly one specific, factual, engaging topic for a short documentary. "
            "Prefer a surprising science, history, technology, nature, or current-interest fact. "
            "Return ONLY the topic name, with no quotes, bullets, or explanation."
        )
        topic = self._complete(prompt, 512).strip('"')
        print(f"🎯 Selected Topic: {topic}")
        return topic

    @staticmethod
    def _extract_json_array(raw_text):
        clean = raw_text.replace("```json", "").replace("```", "").strip()
        match = re.search(r"\[.*\]", clean, re.DOTALL)
        return match.group(0) if match else clean

    def generate_script(self, topic):
        print(f"📝 Writing script for: {topic}...")
        prompt = f"""
You are the lead scriptwriter for a high-retention Edutainment YouTube Shorts channel.
Topic: {topic}

Create 8-9 scenes. The narration must be third-person, factual, fast-paced and concise.
Structure: Hook -> Context -> Mechanism/Explanation -> Twist -> Outro.
Every scene needs two literal, visually searchable stock-video queries.

Return ONLY a JSON array. No markdown and no commentary.
Each item MUST contain: id, text, visual_1, visual_2, mood.

Rules:
- IDs are sequential integers starting at 1.
- Each text is a complete narration sentence or short pair of sentences.
- visual_1 matches the beginning of the narration; visual_2 matches the ending/context.
- Keep visual queries concrete (people, places, objects, actions), not abstract emotions.
- Do not invent citations, URLs, statistics, or unverifiable claims.
"""
        raw_text = self._complete(prompt, 4096)
        clean_text = self._extract_json_array(raw_text)

        try:
            script_data = json.loads(clean_text)
        except json.JSONDecodeError as exc:
            print(f"❌ Error parsing JSON: {exc}")
            print(clean_text)
            return None

        if not isinstance(script_data, list) or not 8 <= len(script_data) <= 9:
            print("❌ Invalid scene count: expected 8-9 scenes.")
            return None

        normalized = []
        for index, scene in enumerate(script_data, start=1):
            if not isinstance(scene, dict):
                print(f"❌ Scene {index} is not an object.")
                return None
            text = str(scene.get("text", "")).strip()
            visual_1 = str(scene.get("visual_1", "")).strip()
            visual_2 = str(scene.get("visual_2", visual_1)).strip()
            if not text or not visual_1:
                print(f"❌ Scene {index} is missing text or visual_1.")
                return None
            normalized.append(
                {
                    "id": index,
                    "text": text,
                    "visual_1": visual_1,
                    "visual_2": visual_2 or visual_1,
                    "mood": str(scene.get("mood", "intriguing")).strip() or "intriguing",
                }
            )

        return normalized


if __name__ == "__main__":
    brain = ContentBrain()
    topic = brain.get_trending_topic()
    script = brain.generate_script(topic)
    if script:
        with open("script.json", "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2, ensure_ascii=False)
        print("✅ Script saved to script.json")
