import unittest
from modules.seo import _extract_json

class TestSeoHelpers(unittest.TestCase):
    def test_extract_json_from_markdown_fence(self):
        raw = '```json\n{"title":"Thử AI","description":"Mô tả","hashtags":["#VideoAI"]}\n```'
        self.assertEqual(_extract_json(raw), '{"title":"Thử AI","description":"Mô tả","hashtags":["#VideoAI"]}')

if __name__ == "__main__":
    unittest.main()
