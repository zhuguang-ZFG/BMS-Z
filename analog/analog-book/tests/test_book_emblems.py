#!/usr/bin/env python3
"""19 枚手绘单线章徽：文件齐全、安全、足够小，能直接内联进章首舞台。"""
import re
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
ART = BOOK / "static" / "illustrations"
sys.path.insert(0, str(BOOK))

from book import illustrations  # noqa: E402

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


class ChapterArtWiringTests(unittest.TestCase):
    """chapter_art 装载：章号映射、缺文件告警不抛错、19 枚真实文件全可装。"""

    # 与 assemble.CHAPTER_STEMS 同一份真实章源映射（保持本测试不依赖构建栈）。
    STEMS = ["p1-01-ch0", "p1-02-ch1", "p1-03-ch2", "p1-04-ch3",
             "p1-05-ch4", "p1-06-ch5", "p1-07-ch6", "p1-08-ch7",
             "p1-09-ch8", "p1-10-ch9", "p1-11-ch10", "p2-01-ch11",
             "p2-02-ch12", "p2-03-ch13", "p3-01-ch14", "p3-02-ch15",
             "p4-01-ch16", "p4-02-ch17", "p4-03-ch18"]

    def test_chapter_art_maps_stem_to_zero_padded_emblem(self):
        self.assertEqual(
            (ART / "ch00.svg").read_text(encoding="utf-8").strip(),
            illustrations.chapter_art("p1-01-ch0"))
        self.assertEqual(
            (ART / "ch10.svg").read_text(encoding="utf-8").strip(),
            illustrations.chapter_art("p1-11-ch10"))

    def test_chapter_art_loads_all_nineteen_real_emblems(self):
        for stem in self.STEMS:
            with self.subTest(stem=stem):
                svg = illustrations.chapter_art(stem)
                self.assertTrue(svg.startswith("<svg"), stem)
                self.assertIn('viewBox="0 0 64 64"', svg, stem)
                self.assertIn('stroke="currentColor"', svg, stem)
                self.assertIn("</svg>", svg, stem)

    def test_chapter_art_warns_instead_of_raising_for_missing_file(self):
        warnings: list[str] = []
        self.assertEqual("", illustrations.chapter_art("p9-99-ch99", warnings))
        self.assertEqual(1, len(warnings))
        self.assertIn("ch99.svg", warnings[0])
        self.assertEqual("", illustrations.chapter_art("p9-99-ch99"))

    def test_chapter_art_returns_empty_for_non_chapter_stems(self):
        self.assertEqual("", illustrations.chapter_art("p0-07-toc"))
        self.assertEqual("", illustrations.chapter_art("p1-00-part1"))
        self.assertEqual("", illustrations.chapter_art(""))


if __name__ == "__main__":
    unittest.main()
