#!/usr/bin/env python3
"""16K 样张必须证明版心、镜像边距回退与十类版式都不溢出。"""
import re
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))
from book import config  # noqa: E402
from book.sample import SAMPLE_SECTIONS, build_sample, inspect_sample  # noqa: E402

try:
    import fitz
except ImportError:  # pragma: no cover
    fitz = None

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None


def _channel(value: int) -> float:
    c = value / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def contrast(fg: str, bg: str) -> float:
    """WCAG 2.x 相对亮度对比度。"""
    def luminance(hex_color: str) -> float:
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
        return (0.2126 * _channel(r) + 0.7152 * _channel(g)
                + 0.0722 * _channel(b))
    high, low = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (high + 0.05) / (low + 0.05)


@unittest.skipIf(fitz is None or sync_playwright is None,
                 "需要 PyMuPDF 与 Playwright")
class SampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html, cls.pdf, cls.report = build_sample(config.DIST_DIR / "sample")

    def test_page_is_16k(self):
        doc = fitz.open(self.pdf)
        try:
            for page in doc:
                width = page.rect.width * 25.4 / 72
                height = page.rect.height * 25.4 / 72
                self.assertAlmostEqual(185, width, delta=0.5)
                self.assertAlmostEqual(260, height, delta=0.5)
        finally:
            doc.close()

    def test_ten_sections_are_present(self):
        self.assertEqual(10, len(SAMPLE_SECTIONS))
        doc = fitz.open(self.pdf)
        try:
            text = "\n".join(page.get_text() for page in doc)
        finally:
            doc.close()
        for title in SAMPLE_SECTIONS:
            self.assertIn(title, text)

    def test_text_stays_inside_145mm_text_block(self):
        report = inspect_sample(self.pdf)
        self.assertLessEqual(report["text_width_mm"], 145.5)
        self.assertGreaterEqual(report["text_width_mm"], 130)
        self.assertEqual(10, len(report["sections"]))
        self.assertIn(report["fallback"], {"mirrored", "uniform-20mm"})
        self.assertTrue((self.html.parent / "sample-report.json").is_file())

    def test_no_paint_bleeds_below_the_text_block(self):
        # Chromium 在「镜像页边距 + 分页书眉」组合下会把下一页的首行
        # 重复画到页底，必须由 .book-page 的 overflow: clip 截住。
        doc = fitz.open(self.pdf)
        try:
            for index, page in enumerate(doc):
                low = [block[4].strip() for block in page.get_text("blocks")
                       if block[4].strip()
                       and block[3] * 25.4 / 72 > 239.0]
                self.assertEqual([], low,
                                 f"第 {index + 1} 页在版心底边之外仍有绘制：{low[:3]}")
        finally:
            doc.close()

    def test_print_css_has_16k_and_typography_contract(self):
        css = (config.STYLES_DIR / "print.css").read_text(encoding="utf-8")
        self.assertIn("size: 185mm 260mm", css)
        self.assertIn("font-size: 10.5pt", css)
        self.assertIn("line-height: 17.5pt", css)
        self.assertIn("font-size: 28pt", css)
        self.assertIn(".book .half-title", css)
        self.assertIn("font-size: 8.5pt", css)
        self.assertIn("column-count: 2", css)
        self.assertIn("break-inside: avoid", css)
        self.assertIn("thead", css)
        self.assertIn("@page :left", css)
        self.assertIn("@page :right", css)
        self.assertRegex(
            css,
            r"\.book-toc \.toc-row a\s*\{[^}]*grid-template-columns:\s*auto\s+minmax\([^)]*\)\s+auto")

    def test_print_css_carries_the_paper_ink_visual_system(self):
        css = (config.STYLES_DIR / "print.css").read_text(encoding="utf-8")
        # 纸墨口径：断言的不再是某几个十六进制值，而是「纸底与三档墨的
        # 对比度下限」——换配色可以，换到看不清不行。
        paper = re.search(r"html,\s*body\s*\{[^}]*background:\s*(#[0-9a-f]{6})",
                          css).group(1)
        palette = dict(re.findall(r"(--[a-z-]+):\s*(#[0-9a-f]{6});", css))
        for token in ("--ink", "--navy", "--amber", "--rule", "--panel"):
            self.assertIn(token, palette)
        for token, floor in (("--ink", 12.0), ("--muted", 4.5),
                             ("--amber", 4.5)):
            self.assertGreaterEqual(
                contrast(palette[token], paper), floor,
                f"{token} 在纸底 {paper} 上对比度不足")
        for selector in (".runline", ".chapter-tag", ".opener-hero",
                         ".opener-art", ".stat-strip", ".chapter-plan",
                         ".equation-strip", ".figure-panel", ".corner",
                         ".reading-notes", ".selection-deck", ".part-hero",
                         ".ladder", ".part-epigraph", ".lead::first-letter",
                         ".book-callout-calc", ".book-callout-limit",
                         ".book-reveal", ".toc-title"):
            self.assertIn(selector, css)
        self.assertIn("-webkit-text-stroke", css)
        self.assertIn("background-size: 5mm 5mm", css)
        self.assertIn(".book-table thead", css)
        self.assertIn("background: var(--navy)", css)

    def test_print_css_drops_web_chrome_from_figures_and_lists(self):
        css = (config.STYLES_DIR / "print.css").read_text(encoding="utf-8")
        self.assertNotIn('content: "FIG"', css)
        self.assertIn(".book .md-typeset .demo-link", css)
        self.assertIn(".page-list_of_figures .book-toc-list", css)
        self.assertIn("min-height: 0", css)

    def test_sample_html_exercises_every_visual_component(self):
        html = self.html.read_text(encoding="utf-8")
        for marker in ("part-hero", "chapter-tag", "chapter-plan", "runline",
                       "equation-strip", "figure-panel", "reading-notes",
                       "selection-deck", "book-table", "lead",
                       "book-callout-calc", "book-callout-limit",
                       "ladder", "part-epigraph"):
            self.assertTrue(marker in html, f"缺少视觉组件: {marker}")


if __name__ == "__main__":
    unittest.main()
