#!/usr/bin/env python3
"""篇首插图与 19 章「先建立直觉」导读。"""
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import illustrations, intuition  # noqa: E402
from book.manifest import BookError  # noqa: E402

PART_NAMES = ["part-i.svg", "part-ii.svg", "part-iii.svg", "part-iv.svg",
              "part-v.svg"]
PART_PREFIXES = ["pi-", "pii-", "piii-", "piv-", "pv-"]
FORBIDDEN_TEXT = ("$", "\\", "**", "`", "\n")


class ChapterLeadTests(unittest.TestCase):
    def test_every_chapter_has_a_plain_lead(self):
        self.assertEqual(set(range(19)), set(intuition.CHAPTER_LEADS))
        for chapter, text in sorted(intuition.CHAPTER_LEADS.items()):
            self.assertGreaterEqual(len(text), 20, chapter)
            self.assertLessEqual(len(text), 110, chapter)
            self.assertTrue(text.endswith("。"), chapter)
            for token in FORBIDDEN_TEXT:
                self.assertNotIn(token, text, (chapter, token))

    def test_leads_are_unique(self):
        leads = list(intuition.CHAPTER_LEADS.values())
        self.assertEqual(19, len(set(leads)))

    def test_chapter_lead_html_is_scoped_and_escaped(self):
        page = intuition.chapter_lead(0)
        self.assertIn('class="chapter-intuition"', page)
        self.assertIn('class="ci-no" aria-hidden="true">00<', page)
        self.assertIn('class="ci-label">先建立直觉', page)
        self.assertIn('class="ci-text"', page)
        self.assertIn(intuition.CHAPTER_LEADS[0], page)
        with self.assertRaises(BookError):
            intuition.chapter_lead(19)


class PartArtTests(unittest.TestCase):
    def test_part_art_files_cover_all_five_parts(self):
        for name in PART_NAMES:
            svg = illustrations.part_art(name)
            self.assertTrue(svg.startswith("<svg"), name)
            self.assertIn('viewBox="0 0 760 260"', svg, name)
            self.assertIn('class="part-art-svg"', svg, name)

    def test_part_art_uses_typographic_approx_and_palette_navy(self):
        foundations = illustrations.part_art("part-i.svg")
        self.assertIn(">≈<", foundations)
        self.assertNotIn(">~<", foundations)
        debug = illustrations.part_art("part-v.svg")
        self.assertNotIn("#101828", debug)

    def test_part_art_has_no_remote_or_active_content(self):
        for name in PART_NAMES:
            svg = illustrations.part_art(name)
            lowered = svg.lower()
            for token in ("<script", "<style", "<image", "<foreignobject",
                          "<iframe", "<object", "<embed", "xlink:", "data:",
                          "@import"):
                self.assertNotIn(token, lowered, (name, token))
            self.assertIsNone(re.search(r"href\s*=", lowered), name)
            self.assertIsNone(re.search(r"on[a-z]+\s*=", lowered), name)
            urls = set(re.findall(r"https?://[^\"'\s>]+", svg))
            self.assertLessEqual(urls, {"http://www.w3.org/2000/svg"}, name)
            for reference in re.findall(r"url\(([^)]*)\)", svg):
                self.assertTrue(reference.strip().startswith("#"),
                                (name, reference))

    def test_part_art_rejects_unsafe_content(self):
        cases = [
            ('<svg xmlns="http://www.w3.org/2000/svg">'
             '<script>x()</script></svg>', "不允许的内容"),
            ('<svg xmlns="http://www.w3.org/2000/svg">'
             '<style>x{}</style></svg>', "不允许的内容"),
            ('<svg xmlns="http://www.w3.org/2000/svg"><object/></svg>',
             "不允许的内容"),
            ('<svg xmlns="http://www.w3.org/2000/svg"><embed/></svg>',
             "不允许的内容"),
            ('<svg xmlns="http://www.w3.org/2000/svg">'
             '<text>xlink:x</text></svg>', "不允许的内容"),
            ('<svg xmlns="http://www.w3.org/2000/svg">'
             '<text>data:x</text></svg>', "不允许的内容"),
            ('<svg xmlns="http://www.w3.org/2000/svg">'
             '<text>@import url(x)</text></svg>', "不允许的内容"),
            ('<svg xmlns="http://www.w3.org/2000/svg" onload="x()"></svg>',
             "事件属性"),
            ('<svg xmlns="http://www.w3.org/2000/svg"/onload="x()"></svg>',
             "事件属性"),
            ('<svg xmlns="http://www.w3.org/2000/svg" '
             'title="x"onload="x()"></svg>', "事件属性"),
            ('<svg xmlns="http://www.w3.org/2000/svg">'
             '<a href="#x">x</a></svg>', "href 属性"),
            ('<svg xmlns="http://www.w3.org/2000/svg">'
             '<a href = "#x">x</a></svg>', "href 属性"),
            ('<svg xmlns="http://www.w3.org/2000/svg">'
             '<a title="x"href="javascript:alert(1)">x</a></svg>',
             "href 属性"),
            ('<svg xmlns="http://www.w3.org/2000/svg">'
             '<text>https://example.com</text></svg>', "外部 URL"),
            ('<svg xmlns="http://www.w3.org/2000/svg">'
             '<rect fill="url(x.svg#id)"/></svg>', "外部 url()"),
            ('<svg xmlns="http://www.w3.org/2000/svg">'
             '<text>中文</text></svg>', "拉丁文字"),
            ("not an svg", "不是 SVG"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(illustrations, "ART_DIR", Path(tmp)):
                path = Path(tmp) / "part-i.svg"
                for payload, fragment in cases:
                    path.write_text(payload, encoding="utf-8")
                    with self.assertRaises(BookError, msg=payload) as ctx:
                        illustrations.part_art("part-i.svg")
                    self.assertIn(fragment, str(ctx.exception), payload)
                path.unlink()
                with self.assertRaises(BookError, msg="missing file"):
                    illustrations.part_art("part-i.svg")

    def test_part_art_ids_are_unique_across_parts(self):
        seen: set[str] = set()
        for name, prefix in zip(PART_NAMES, PART_PREFIXES):
            for identifier in re.findall(r'id="([^"]+)"',
                                         illustrations.part_art(name)):
                self.assertTrue(identifier.startswith(prefix),
                                (name, identifier))
                self.assertNotIn(identifier, seen, (name, identifier))
                seen.add(identifier)

    def test_part_art_rejects_bad_names_and_missing_files(self):
        self.assertEqual("", illustrations.part_art(""))
        for name in ("../part-i.svg", "part-vi.svg", "part-i.txt",
                     "part-ix.svg", "part-i.svg/extra"):
            with self.assertRaises(BookError, msg=name):
                illustrations.part_art(name)

    def test_part_art_is_latin_only(self):
        for name in PART_NAMES:
            svg = illustrations.part_art(name)
            self.assertIsNone(re.search(r"[\u4e00-\u9fff]", svg), name)


if __name__ == "__main__":
    unittest.main()
