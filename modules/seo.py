"""Generate and validate Vietnamese YouTube Shorts metadata."""
import json
import os
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
DEFAULT_MODEL = "openai/gpt-oss-20b"
BRAND_HASHTAGS = ["#THAOANHAI", "#VideoAI", "#CongCuAI", "#Shorts"]

def _extract_json(raw):
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    return match.group(0) if match else cleaned

class SeoWriter:
    """Create Vietnamese title, description, and hashtags without inventing claims."""
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is required to generate video metadata.")
        self.client = Groq(api_key=api_key)
        self.model = os.getenv("GROQ_MODEL", DEFAULT_MODEL)

    def generate(self, topic, script):
        narration = " ".join(str(scene.get("text", "")) for scene in script)
        prompt = f"""
You are a careful Vietnamese YouTube Shorts SEO editor for the channel THAO ANH AI.
Create metadata for a vertical 15-40 second video about the topic below.
Topic: {topic}
Narration: {narration[:5000]}
Return only one JSON object with keys:
"title": one engaging Vietnamese title, at most 90 characters;
"description": 2-3 concise Vietnamese sentences, no fabricated statistics or guarantees;
"hashtags": an array of 4-8 relevant hashtags, each beginning with #.
Rules: accurate, natural Vietnamese; no clickbait that misrepresents the video; do not claim a tool is free unless verified; do not invent sources, prices, or features.
"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_completion_tokens=700,
        )
        raw = response.choices[0].message.content or ""
        try:
            data = json.loads(_extract_json(raw))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Could not parse SEO metadata JSON: {exc}") from exc
        title = str(data.get("title", "")).strip()
        description = str(data.get("description", "")).strip()
        hashtags = data.get("hashtags", [])
        if not title or len(title) > 100 or not description or not isinstance(hashtags, list):
            raise RuntimeError("SEO metadata failed validation.")
        normalized = []
        for tag in hashtags:
            tag = str(tag).strip()
            if tag and re.fullmatch(r"#[\wÀ-ỹ]+", tag, flags=re.UNICODE):
                if tag.lower() not in {item.lower() for item in normalized}:
                    normalized.append(tag)
        for tag in BRAND_HASHTAGS:
            if tag.lower() not in {item.lower() for item in normalized}:
                normalized.append(tag)
        return {"title": title, "description": description + "\n\n" + " ".join(normalized), "hashtags": normalized}
