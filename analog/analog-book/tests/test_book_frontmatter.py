#!/usr/bin/env python3
"""前置/后置页：元数据、目录、图表目录、索引与版权安全文案。"""
import re
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import frontmatter  # noqa: E402

MANIFEST = {
    "title": "通往模拟电路之路", "subtitle": "从欧姆定律到芯片内部结构",
    "edition": "第一版", "version": "2.0.0-draft.1", "date": "2026-10-25",
    "author": "zhuguang-ZFG 与贡献者", "license": "CC BY-SA 4.0",
    "site_url": "https://example.test/book/",
    "repository": "https://example.test/repo",
    "release": {"edition_status": "draft"},
}


class FrontPageTests(unittest.TestCase):
    def test_half_title_and_title_page(self):
        half = frontmatter.half_title(MANIFEST)
        self.assertIn("通往模拟电路之路", half)
        self.assertIn("第一版", half)
        self.assertNotIn("000", half)
        self.assertEqual(1, half.count("<h1"),
                         "半书名页必须恰好一个 h1，供 PDF 定位页首")
        self.assertIn('<h1 class="book-title">', half)
        title = frontmatter.title_page(MANIFEST)
        self.assertIn("从欧姆定律到芯片内部结构", title)
        self.assertIn("zhuguang-ZFG", title)
        self.assertIn("2.0.0-draft.1", title)

    def test_copyright_has_license_safety_and_no_fake_isbn(self):
        page = frontmatter.copyright_page(MANIFEST)
        for text in ("CC BY-SA 4.0", "SIL Open Font License", "安全", "仿真",
                     "草稿", "185×260", "勘误"):
            self.assertIn(text, page)
        self.assertNotIn("ISBN", page)
        self.assertNotIn("条码", page)


class TocTests(unittest.TestCase):
    def test_three_levels_links_and_placeholders(self):
        entries = [
            {"level": 1, "title": "第一篇 基础", "anchor": "part-i", "kind": "part"},
            {"level": 2, "title": "第 0 章 电路直觉", "anchor": "page-p1-01-ch0",
             "kind": "chapter"},
            {"level": 3, "title": "0.1 电压与电位", "anchor": "p1-01-ch0--s1",
             "kind": "section"},
        ]
        page = frontmatter.render_toc(entries)
        self.assertIn('id="book-toc"', page)
        self.assertEqual(3, page.count('class="toc-page">000</span>'))
        self.assertIn('href="#p1-01-ch0--s1"', page)
        self.assertIn("toc-level-3", page)

    def test_list_of_figures(self):
        entries = [{"number": "图 2-1", "title": "整流波形",
                    "caption": "图 2-1　整流波形（含滤波电容与负载变化）",
                    "anchor": "p1-03-ch2--fig-1"}]
        page = frontmatter.render_list("插图目录", "list-of-figures", entries, "图")
        self.assertIn('id="list-of-figures"', page)
        self.assertIn("图 2-1", page)
        self.assertIn("整流波形", page)
        self.assertNotIn("含滤波电容与负载变化", page)
        self.assertIn('class="toc-page">000</span>', page)


class StructurePageTests(unittest.TestCase):
    def test_part_and_appendix_openers(self):
        part = {"id": "I", "title": "基础", "subtitle": "先建立电路直觉",
                "intro": "从电压、电流与无源元件开始。",
                "units": [{"title": "电路直觉与无源世界"}]}
        html = frontmatter.part_opener(part)
        self.assertIn('id="part-i"', html)
        self.assertIn("第I篇", html)
        self.assertIn("基础", html)
        appendix = {"id": "B", "title": "公式与设计速查",
                    "intro": "把全书常用公式收在一处。"}
        html = frontmatter.appendix_opener(appendix)
        self.assertIn('id="appendix-b"', html)
        self.assertIn("附录 B", html)

    def test_part_opener_embeds_art_and_unit_cards(self):
        part = {
            "id": "II", "title": "器件", "subtitle": "从 PN 结到 555",
            "intro": "从二极管到 555。",
            "units": [
                {"title": "分立器件",
                 "chapters": ["p1-03-ch2.md", "p1-04-ch3.md",
                              "p1-05-ch4.md", "p1-06-ch5.md"]},
                {"title": "模拟集成器件",
                 "chapters": ["p1-07-ch6.md", "p1-08-ch7.md",
                              "p1-09-ch8.md", "p1-10-ch9.md",
                              "p1-11-ch10.md"]},
            ],
        }
        art = '<svg class="part-art-svg" viewBox="0 0 1 1"></svg>'
        html = frontmatter.part_opener(part, art)
        self.assertIn('<div class="part-art" aria-hidden="true">' + art, html)
        self.assertIn('id="part-ii"', html)
        self.assertIn("U01", html)
        self.assertIn("U02", html)
        self.assertIn("CH 02–05", html)
        self.assertIn("CH 06–10", html)
        self.assertIn("4 章", html)
        self.assertIn("5 章", html)
        self.assertIn("读法 · L1 直觉", html)
        self.assertIn("PART II", html)
        self.assertIn("READING LAYERS", html)
        heading = re.search(
            r'<h1[^>]*class="part-heading"[^>]*>(.*?)</h1>', html, re.S)
        self.assertIsNotNone(heading)
        self.assertEqual(
            "第II篇器件", re.sub(r"<[^>]+>", "", heading.group(1)),
            "PDF 大纲依赖篇标题恰好为「第N篇＋篇名」，两段 span 间不得有空白")

    def test_unit_meta_only_prints_contiguous_chapter_ranges(self):
        def unit_meta(chapters):
            part = {"id": "I", "title": "基础",
                    "units": [{"title": "单元", "chapters": chapters}]}
            page = frontmatter.part_opener(part)
            values = re.findall(r'<p class="unit-meta">([^<]*)</p>', page)
            self.assertEqual(1, len(values), chapters)
            return values[0]

        self.assertEqual("CH 00 · 1 章", unit_meta(["p1-01-ch0.md"]))
        self.assertEqual("2 章", unit_meta(["p1-01-ch0.md", "p2-01-notes.md"]))
        self.assertEqual("2 章", unit_meta(["p1-01-ch0.md", "p1-02-ch2.md"]))

    def test_part_opener_without_art_keeps_empty_plate(self):
        part = {"id": "I", "title": "基础", "subtitle": "先建立电路直觉",
                "intro": "从电压、电流与无源元件开始。",
                "units": [{"title": "电路直觉与无源世界",
                           "chapters": ["p1-01-ch0.md", "p1-02-ch1.md"]}]}
        html = frontmatter.part_opener(part)
        self.assertIn('<div class="part-art" aria-hidden="true"></div>', html)
        self.assertNotIn("<svg", html)


class BackMatterTests(unittest.TestCase):
    def test_empty_bibliography_is_honest_draft_note(self):
        page = frontmatter.render_bibliography([])
        self.assertIn('id="bibliography"', page)
        self.assertIn("草稿", page)
        self.assertNotIn("TODO", page)

    def test_bibliography_is_numbered_and_sorted(self):
        refs = [
            {"id": "b", "authors": "B", "title": "Beta", "year": 2020,
             "publisher": "P", "edition": "", "isbn_or_url": "u", "chapters": [1]},
            {"id": "a", "authors": "A", "title": "Alpha", "year": 2019,
             "publisher": "P", "edition": "", "isbn_or_url": "u", "chapters": [0]},
        ]
        page = frontmatter.render_bibliography(refs)
        self.assertLess(page.index("Alpha"), page.index("Beta"))
        self.assertIn("[1]", page)
        self.assertIn("第 1 章", page)

    def test_index_two_column_primary_bold_and_multiple_pages(self):
        sections = [("M", [{
            "term": "米勒效应", "english": "Miller effect",
            "primary": "page-p1-05-ch4",
            "anchors": ["page-p1-05-ch4", "p1-05-ch4--miller"],
            "see_also": [],
        }])]
        page = frontmatter.render_index(sections)
        self.assertIn("index-columns", page)
        self.assertIn("<strong>米勒效应</strong>", page)
        self.assertEqual(2, page.count('class="index-page">000</span>'))
        self.assertIn("Miller effect", page)

    def test_colophon_lists_production_facts(self):
        page = frontmatter.colophon(MANIFEST, {"pages": 500, "spine_mm": 26.0})
        for text in ("500", "26.0", "Chromium", "PyMuPDF", "SIL Open Font License"):
            self.assertIn(text, page)

    def test_colophon_defers_physical_pagination_until_pdf_facts(self):
        page = frontmatter.colophon(MANIFEST, {"pages": 77})
        self.assertIn("77 个逻辑页", page)
        self.assertIn("最终 PDF 与 PRINT-SPEC.md", page)
        self.assertNotIn("书脊厚度约", page)


if __name__ == "__main__":
    unittest.main()
