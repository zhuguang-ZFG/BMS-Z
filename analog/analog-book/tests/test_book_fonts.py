#!/usr/bin/env python3
"""书内字体必须覆盖全书字符，而且以 data URI 内联。"""
import base64
import json
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from book import config  # noqa: E402
from book.fonts import (FONT_FACES, font_css, missing_glyphs,  # noqa: E402
                        required_text, stamp_font_path)
import book_fixtures  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402


class FontTests(unittest.TestCase):
    def test_all_faces_exist_and_are_valid_woff2(self):
        self.assertEqual(5, len(FONT_FACES))
        for _family, _weight, name in FONT_FACES:
            path = config.FONTS_DIR / name
            self.assertTrue(path.is_file(), path)
            font = TTFont(path)
            self.assertIn("cmap", font)

    def test_serif_and_sans_cover_every_book_character(self):
        text = required_text()
        self.assertGreater(len(set(text)), 1000)
        for name in ("NotoSerifSC-Regular.woff2", "NotoSerifSC-Bold.woff2",
                     "NotoSansSC-Regular.woff2", "NotoSansSC-Bold.woff2"):
            missing = missing_glyphs(config.FONTS_DIR / name, text)
            self.assertEqual(set(), missing,
                             f"{name} 缺字: {''.join(sorted(missing))[:80]}")

    def test_serif_and_sans_cover_check_and_cross_marks(self):
        # Task 5 把 ✅/❌ 映射成 ✓/✗；EMOJI_RE 会从书稿里剥掉它们，因此
        # 四个正文子集必须显式包含这两个字形。
        for name in ("NotoSerifSC-Regular.woff2", "NotoSerifSC-Bold.woff2",
                     "NotoSansSC-Regular.woff2", "NotoSansSC-Bold.woff2"):
            missing = missing_glyphs(config.FONTS_DIR / name, "✓✗")
            self.assertEqual(set(), missing,
                             f"{name} 缺字: {''.join(sorted(missing))}")

    def test_mono_covers_ascii(self):
        missing = missing_glyphs(config.FONTS_DIR / "JetBrainsMono-Regular.woff2",
                                 "".join(chr(c) for c in range(32, 127)))
        self.assertEqual(set(), missing)

    def test_stamp_font_covers_running_titles(self):
        titles = "通往模拟电路之路目录索引参考文献第一篇基础第二篇器件第三篇拓扑第四篇设计第五篇调试"
        missing = missing_glyphs(stamp_font_path(), titles)
        self.assertEqual(set(), missing)

    def test_stamp_font_covers_schema_2_running_titles(self):
        manifest = book_fixtures.manifest()
        self.assertEqual(2, manifest["schema"])
        titles = [manifest["title"], manifest["subtitle"]]
        titles += [entry["title"] for entry in manifest["front_matter"]
                   if entry.get("title")]
        for part in manifest["parts"]:
            titles.append(part["title"])
            titles += [unit["title"] for unit in part.get("units", [])
                       if unit.get("title")]
        titles += [entry["title"] for entry in manifest["appendices"]
                   if entry.get("title")]
        titles += [entry["title"] for entry in manifest["back_matter"]
                   if entry.get("title")]
        missing = missing_glyphs(stamp_font_path(), "".join(titles))
        self.assertEqual(set(), missing,
                         f"印章字体缺字: {''.join(sorted(missing))}")

    def test_font_css_is_five_data_uris_and_no_remote(self):
        css = font_css()
        self.assertEqual(5, css.count("@font-face"))
        self.assertEqual(5, css.count("data:font/woff2;base64,"))
        # 不能用 assertNotIn("http")：base64 载荷里出现 "http" 纯属偶然
        # （换一版子集就误报）。要查的是「没有远程字体源」。
        for remote in ("url(http", "url('http", 'url("http', "@import"):
            self.assertNotIn(remote, css)
        self.assertIn('font-family: "Book Serif"', css)
        self.assertIn("font-weight: 700", css)
        for _family, _weight, name in FONT_FACES:
            raw = (config.FONTS_DIR / name).read_bytes()
            encoded = base64.b64encode(raw).decode("ascii")
            self.assertIn(encoded[:80], css)

    def test_sources_json_records_hashes_and_licenses(self):
        data = json.loads((config.FONTS_DIR / "sources.json").read_text(encoding="utf-8"))
        self.assertEqual(5, len(data["subsets"]))
        for entry in data["subsets"]:
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(entry["name"], Path(entry["name"]).name)
        for name in ("OFL-NotoSerifSC.txt", "OFL-NotoSansSC.txt",
                     "OFL-JetBrainsMono.txt"):
            self.assertTrue((config.FONTS_DIR / name).is_file())


if __name__ == "__main__":
    unittest.main()
