import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your Groq API key."
        )
    return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")


class ContentBrain:
    """Generate a topic and validated scene plan using Groq's OpenAI-compatible API."""

    def __init__(self):
        self.client = _get_client()
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    def get_trending_topic(self):
        prompt = (
            "Give exactly one specific, factual, engaging topic for a short documentary. "
            "Prefer a surprising science, history, technology, nature, or current-interest fact. "
            "Return ONLY the topic name, with no quotes, bullets, or explanation."
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=80,
        )
        topic = (response.choices[0].message.content or "").strip().strip('"')
        if not topic:
            raise RuntimeError("The AI returned an empty topic.")
        print(f"🎯 Selected Topic: {topic}")
        return topic

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
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2200,
        )
        raw_text = (response.choices[0].message.content or "").strip()
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()

        match = re.search(r"\[.*\]", clean_text, re.DOTALL)
        if match:
            clean_text = match.group(0)

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
                return None
            text = str(scene.get("text", "")).strip()
            visual_1 = str(scene.get("visual_1", "")).strip()
            visual_2 = str(scene.get("visual_2", visual_1)).strip()
            if not text or not visual_1:
                print(f"❌ Scene {index} is missing text or visual_1.")
                return None
            normalized.append({
                "id": index,
                "text": text,
                "visual_1": visual_1,
                "visual_2": visual_2 or visual_1,
                "mood": str(scene.get("mood", "intriguing")).strip(),
            })

        return normalized


if __name__ == "__main__":
    brain = ContentBrain()
    topic = brain.get_trending_topic()
    script = brain.generate_script(topic)
    if script:
        with open("script.json", "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2, ensure_ascii=False)
        print("✅ Script saved to script.json")
