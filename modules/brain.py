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
        raise RuntimeError("GROQ_API_KEY is not set. Add it as an environment variable.")
    return Groq(api_key=api_key)


class ContentBrain:
    """Generate concise Vietnamese topics and scripts for Shorts."""

    def __init__(self):
        self.client = _get_client()
        self.model = os.getenv("GROQ_MODEL", DEFAULT_MODEL)

    def _complete(self, prompt, max_completion_tokens):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_completion_tokens=max_completion_tokens,
        )
        content = response.choices[0].message.content or ""
        if not content.strip():
            raise RuntimeError("The AI returned an empty response.")
        return content.strip()

    def get_trending_topic(self):
        """Select a timely-feeling topic; this model-only step does not verify live trends."""
        prompt = (
            "Chọn đúng một chủ đề cụ thể, hữu ích và dễ minh họa cho YouTube Shorts tiếng Việt "
            "của kênh THAO ANH AI về AI, công nghệ hoặc mẹo sáng tạo video trên điện thoại. "
            "Ưu tiên chủ đề có thể giải thích chính xác, áp dụng được, không cần số liệu mới nhất. "
            "Không tuyên bố đây là xu hướng đang tăng nếu chưa có nguồn xác minh. "
            "Chỉ trả về tên chủ đề bằng tiếng Việt, không giải thích."
        )
        topic = self._complete(prompt, 256).strip('"')
        if not topic:
            raise RuntimeError("Topic generation returned an empty topic.")
        print(f"🎯 Selected topic: {topic}")
        return topic

    @staticmethod
    def _extract_json_array(raw_text):
        clean = raw_text.replace("```json", "").replace("```", "").strip()
        match = re.search(r"\[.*\]", clean, re.DOTALL)
        return match.group(0) if match else clean

    def generate_script(self, topic):
        print(f"📝 Writing Vietnamese Short script for: {topic}...")
        prompt = f"""
Bạn là biên kịch YouTube Shorts tiếng Việt cho kênh THAO ANH AI.
Chủ đề: {topic}
Tạo 8-9 phân cảnh cho video dọc 9:16. Tổng lời thoại mục tiêu 15-40 giây khi đọc tự nhiên,
ưu tiên câu ngắn khoảng 5-10 từ mỗi cảnh. Viết tiếng Việt tự nhiên, dễ nghe, không dùng tiếng Anh
trừ tên công cụ/thuật ngữ cần thiết. Cấu trúc: hook 0-3 giây -> giải thích ngắn -> ví dụ -> kết luận/CTA.
Không bịa số liệu, nguồn, giá, tính năng hoặc tuyên bố công cụ miễn phí. Nếu là hướng dẫn công cụ,
không giả vờ đã kiểm thử một tính năng cụ thể.
Trả về CHỈ MỘT JSON array, không Markdown. Mỗi item phải có: id, text, visual_1, visual_2, mood.
id là số nguyên tuần tự bắt đầu từ 1. text là câu lời thoại tiếng Việt hoàn chỉnh.
visual_1 và visual_2 là truy vấn tìm kiếm video stock cụ thể bằng tiếng Anh, phù hợp nội dung cảnh.
mood là nhãn ngắn. Mỗi cảnh cần lời thoại ngắn để toàn video nằm trong 15-40 giây.
"""
        raw_text = self._complete(prompt, 4096)
        clean_text = self._extract_json_array(raw_text)
        try:
            script_data = json.loads(clean_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"AI script JSON parse failed: {exc}") from exc

        if not isinstance(script_data, list) or not 8 <= len(script_data) <= 9:
            raise RuntimeError("Invalid scene count: expected 8-9 scenes.")
        normalized = []
        for index, scene in enumerate(script_data, start=1):
            if not isinstance(scene, dict):
                raise RuntimeError(f"Scene {index} is not an object.")
            text = str(scene.get("text", "")).strip()
            visual_1 = str(scene.get("visual_1", "")).strip()
            visual_2 = str(scene.get("visual_2", visual_1)).strip()
            if not text or not visual_1:
                raise RuntimeError(f"Scene {index} is missing narration or visual query.")
            normalized.append({
                "id": index,
                "text": text,
                "visual_1": visual_1,
                "visual_2": visual_2 or visual_1,
                "mood": str(scene.get("mood", "engaging")).strip() or "engaging",
            })
        return normalized
