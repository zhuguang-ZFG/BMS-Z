#!/usr/bin/env python3
"""19 枚手绘单线章徽：文件齐全、安全、足够小，能直接内联进章首舞台。"""
import re
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
ART = BOOK / "static" / "illustrations"
NAMES = [f"ch{number:02d}.svg" for number in range(19)]
ALLOWED_URLS = {"http://www.w3.org/2000/svg"}


class ChapterEmblemTests(unittest.TestCase):
    def test_nineteen_distinct_emblems_exist(self):
        for name in NAMES:
            with self.subTest(name=name):
                self.assertTrue((ART / name).is_file(), name)
        contents = [(ART / name).read_text(encoding="utf-8") for name in NAMES]
        self.assertEqual(19, len(set(contents)), "章徽不允许互相复制")

    def test_emblems_are_small_line_art_on_the_shared_canvas(self):
        for name in NAMES:
            with self.subTest(name=name):
                svg = (ART / name).read_text(encoding="utf-8")
                self.assertTrue(svg.startswith("<svg"), name)
                self.assertLess(len(svg.encode("utf-8")), 6000, name)
                self.assertIn('viewBox="0 0 64 64"', svg, name)
                self.assertIn('stroke="currentColor"', svg, name)
                self.assertIn('stroke-linecap="round"', svg, name)
                self.assertIn('stroke-width="2.1"', svg, name)
                self.assertIn("</svg>", svg, name)
                self.assertNotIn("<text", svg.lower(), f"{name} 不应带文字")
                self.assertGreaterEqual(svg.count("<path"), 2, name)

    def test_emblems_have_no_active_or_remote_content(self):
        for name in NAMES:
            with self.subTest(name=name):
                svg = (ART / name).read_text(encoding="utf-8")
                lowered = svg.lower()
                for token in ("<script", "<style", "<image", "<foreignobject",
                              "<iframe", "<object", "<embed", "xlink:", "data:",
                              "@import", "<!entity", "<!doctype"):
                    self.assertNotIn(token, lowered, (name, token))
                self.assertIsNone(re.search(r"\bid\s*=", lowered), name)
                self.assertIsNone(re.search(r"\bhref\s*=", lowered), name)
                self.assertIsNone(re.search(r"\son[a-z]+\s*=", lowered), name)
                self.assertIsNone(re.search(r"url\(", lowered), name)
                urls = set(re.findall(r"https?://[^\"'\s>]+", svg))
                self.assertLessEqual(urls, ALLOWED_URLS, name)

    def test_emblems_stay_latin_only(self):
        for name in NAMES:
            with self.subTest(name=name):
                svg = (ART / name).read_text(encoding="utf-8")
                self.assertIsNone(re.search(r"[\u4e00-\u9fff]", svg), name)


if __name__ == "__main__":
    unittest.main()
