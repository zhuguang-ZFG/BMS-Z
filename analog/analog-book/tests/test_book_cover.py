#!/usr/bin/env python3
"""封面：书脊公式、尺寸、出血、裁切线、二维码与无假 ISBN。"""
import copy
import hashlib
import math
import re
import sys
import tempfile
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import config  # noqa: E402
from book.cover import (build_cover, cover_html, cover_size_mm,  # noqa: E402
                        inspect_cover, qr_svg, spine_mm)

try:
    import fitz
except ImportError:  # pragma: no cover
    fitz = None

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

MANIFEST = {
    "title": "通往模拟电路之路",
    "subtitle": "从欧姆定律到芯片内部结构",
    "edition": "第一版", "version": "2.0.0-draft.1", "date": "2026-10-25",
    "author": "zhuguang-ZFG 与贡献者", "license": "CC BY-SA 4.0",
    "site_url": "https://example.test/analog/",
    "repository": "https://github.com/example/analog",
    "trim": {"width_mm": 185, "height_mm": 260},
    "cover": {
        "bleed_mm": 3, "crop_marks": True, "paper_caliper_mm": 0.10,
        "spine_allowance_mm": 1.0, "isbn_area": False,
        "back_cover": {
            "blurb": "从欧姆定律、PN 结与 MOSFET 出发，一路走到放大、稳压、"
                     "信号链与 PCB。每个模型都说明适用边界，关键结论配可复现"
                     "仿真、实测记录与故障速查。",
            "audience": "电子、自动化、通信与嵌入式方向的学生和工程师；"
                        "也适合需要补齐模拟基础的软件与系统工程师。",
            "highlights": ["19 章完整知识链", "三层读法", "可复现仿真",
                           "实测实验", "故障速查与索引"],
            "structure": [
                {"title": "第一篇 基础",
                 "scope": "电路直觉、无源元件与基本定律"},
                {"title": "第二篇 器件",
                 "scope": "二极管、BJT、MOSFET 与运放内部"},
                {"title": "第三篇 拓扑",
                 "scope": "放大、比较、电源、定时与信号产生"},
                {"title": "第四篇 设计",
                 "scope": "设计方法、参数容差与 PCB 实战"},
                {"title": "第五篇 调试",
                 "scope": "排故五步、故障速查与大师心法"},
            ],
        },
    },
    "release": {"edition_status": "draft"},
}


def visible_text(markup: str) -> str:
    """去掉标签后归一化空白，便于校验拆成多段的文案。"""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", markup)).strip()


def contrast_ratio(foreground: str, background: str) -> float:
    """WCAG 2.x 相对亮度对比度，如 "#52606d" 对 "#fffdf8"。"""
    def luminance(value: str) -> float:
        channels = [int(value[index:index + 2], 16) / 255
                    for index in (1, 3, 5)]
        linear = [channel / 12.92 if channel <= .03928
                  else ((channel + .055) / 1.055) ** 2.4
                  for channel in channels]
        return .2126 * linear[0] + .7152 * linear[1] + .0722 * linear[2]

    lighter, darker = sorted((luminance(foreground), luminance(background)),
                             reverse=True)
    return (lighter + .05) / (darker + .05)


class SpineTests(unittest.TestCase):
    def test_spine_formula_uses_final_page_count(self):
        self.assertEqual(31.0, spine_mm(600, MANIFEST))
        self.assertEqual(33.5, spine_mm(650, MANIFEST))
        self.assertEqual(26.0, spine_mm(500, MANIFEST))

    def test_cover_size_includes_two_trim_panels_and_bleed(self):
        width, height = cover_size_mm(650, MANIFEST)
        self.assertAlmostEqual(409.5, width, places=2)
        self.assertAlmostEqual(266.0, height, places=2)

    def test_cover_size_rejects_zero_pages(self):
        with self.assertRaises(ValueError):
            cover_size_mm(0, MANIFEST)

    def test_spine_six_mm_boundary_toggles_spine_text(self):
        self.assertEqual(5.95, spine_mm(99, MANIFEST))
        self.assertEqual(6.0, spine_mm(100, MANIFEST))
        thin = cover_html(MANIFEST, 99)
        self.assertIn('class="cover-panel cover-spine is-thin"', thin)
        self.assertNotIn('class="spine-text"', thin)
        full = cover_html(MANIFEST, 100)
        self.assertNotIn("cover-spine is-thin", full)
        self.assertIn('class="spine-text"', full)


class CoverHtmlTests(unittest.TestCase):
    def setUp(self):
        self.html = cover_html(MANIFEST, 650)

    def test_three_panels_and_title(self):
        for value in ('class="cover-panel cover-back"',
                      'class="cover-panel cover-spine"',
                      'class="cover-panel cover-front"',
                      "通往模拟电路之路", "从欧姆定律到芯片内部结构",
                      "zhuguang-ZFG 与贡献者", "第一版"):
            self.assertIn(value, self.html)

    def test_has_eight_crop_marks_and_bleed(self):
        self.assertEqual(8, self.html.count('<line class="crop-mark"'))
        self.assertIn("3mm", (config.COVER_DIR / "cover.css").read_text(
            encoding="utf-8").replace("__BLEED__", "3"))

    def test_crop_mark_halos_share_crop_coordinates(self):
        pattern = re.compile(r'x1="([^"]+)" y1="([^"]+)" '
                             r'x2="([^"]+)" y2="([^"]+)"')
        halos = re.findall(r'<line class="crop-mark-halo"[^>]*/>', self.html)
        marks = re.findall(r'<line class="crop-mark"[^>]*/>', self.html)
        self.assertEqual(8, len(halos))
        self.assertEqual(8, len(marks))
        self.assertEqual([pattern.search(line).groups() for line in marks],
                         [pattern.search(line).groups() for line in halos])
        # 垫底线必须先绘制，黑芯才能压在上面。
        self.assertLess(self.html.rindex('class="crop-mark-halo"'),
                        self.html.index('class="crop-mark"'))
        css = (config.COVER_DIR / "cover.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.crop-mark-halo\s*\{[^}]*#fffdf8")
        self.assertRegex(css, r"\.crop-mark\s*\{[^}]*stroke-width:\s*\.18")

    def test_crop_geometry_stays_on_bleed_lines_and_short(self):
        width, height = cover_size_mm(650, MANIFEST)
        bleed = MANIFEST["cover"]["bleed_mm"]
        marks = re.findall(
            r'<line class="crop-mark" x1="([\d.]+)" y1="([\d.]+)" '
            r'x2="([\d.]+)" y2="([\d.]+)"/>', self.html)
        self.assertEqual(8, len(marks))
        for values in marks:
            x1, y1, x2, y2 = (float(value) for value in values)
            on_vertical = (
                abs(x1 - bleed) < 1e-6 and abs(x2 - bleed) < 1e-6) or (
                abs(x1 - (width - bleed)) < 1e-6
                and abs(x2 - (width - bleed)) < 1e-6)
            on_horizontal = (
                abs(y1 - bleed) < 1e-6 and abs(y2 - bleed) < 1e-6) or (
                abs(y1 - (height - bleed)) < 1e-6
                and abs(y2 - (height - bleed)) < 1e-6)
            self.assertTrue(on_vertical or on_horizontal,
                            f"裁切线偏离出血线: {values}")
            self.assertLessEqual(math.hypot(x2 - x1, y2 - y1), 2.5,
                                 f"裁切线超长: {values}")

    def test_crop_marks_switch_off_removes_marks_and_halos(self):
        manifest = copy.deepcopy(MANIFEST)
        manifest["cover"]["crop_marks"] = False
        html = cover_html(manifest, 650)
        self.assertNotIn('<line class="crop-mark"', html)
        self.assertNotIn('<line class="crop-mark-halo"', html)
        self.assertNotIn('class="cover-marks"', html)
        # 关掉裁切线不应影响其余版面。
        self.assertIn('class="cover-panel cover-back"', html)
        self.assertIn('class="cover-panel cover-front"', html)
        self.assertIn("通往模拟电路之路", html)
        self.assertIn('data-qr="site"', html)

    def test_spine_is_vertical_and_can_be_thin(self):
        css = (config.COVER_DIR / "cover.css").read_text(encoding="utf-8")
        self.assertIn("writing-mode: vertical-rl", css)
        thin = cover_html(MANIFEST, 80)
        self.assertIn('class="cover-panel cover-spine is-thin"', thin)
        self.assertNotIn('class="spine-text"', thin)

    def test_back_cover_has_blurb_structure_qr_and_blank_isbn(self):
        for text in ("从欧姆定律、PN 结与 MOSFET 出发",
                     "电子、自动化、通信与嵌入式方向",
                     "三层读法", "直觉层", "推导层", "工程层",
                     "五篇", "第一篇", "第二篇", "第三篇",
                     "第四篇", "第五篇",
                     "读 → 算 → 仿 → 测 → 排",
                     "ISBN / 条码预留区（留空）",
                     'data-qr="site"', 'data-qr="repo"'):
            self.assertIn(text, self.html)
        self.assertNotRegex(self.html, r"ISBN[^<]{0,16}\d{10,13}")
        self.assertNotIn("978-", self.html)

    def test_isbn_area_stays_blank_and_reserved(self):
        area = re.search(r'<div class="isbn-area">.*?</div>', self.html,
                         re.S)
        self.assertIsNotNone(area)
        markup = area.group(0)
        self.assertNotIn("<svg", markup)
        self.assertNotIn("data-qr", markup)
        self.assertIsNone(re.search(r"\d{10,13}", markup))
        self.assertIn("ISBN / 条码预留区（留空）", markup)
        css = (config.COVER_DIR / "cover.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.isbn-area\s*\{[^}]*dashed")

    def test_qr_is_inline_vector_and_no_remote_assets(self):
        svg = qr_svg(MANIFEST["site_url"])
        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("path", svg)
        self.assertNotIn("<image", svg)
        forbidden = (r'src="http|href="http|url\(http'
                     r"|<script|<image|<iframe")
        self.assertIsNone(re.search(forbidden, self.html, re.IGNORECASE))

    def test_all_ids_are_unique_and_qr_ids_are_stable(self):
        ids = re.findall(r'id="([^"]+)"', self.html)
        duplicates = sorted({value for value in ids if ids.count(value) > 1})
        self.assertEqual([], duplicates)
        qr_ids = {"qr-path-" + hashlib.sha256(
            MANIFEST[key].encode("utf-8")).hexdigest()[:10]
            for key in ("site_url", "repository")}
        self.assertEqual(2, len(qr_ids))
        self.assertTrue(qr_ids.issubset(ids))
        self.assertIn("cover-sketch", ids)

    def test_cover_art_is_inlined(self):
        self.assertIn("cover-sketch", self.html)
        self.assertIn("<svg", self.html)

    def test_cover_art_is_inlined_exactly_once(self):
        self.assertEqual(1, self.html.count('id="cover-sketch"'))

    def test_cover_art_is_static_ink_not_template_decor(self):
        self.assertNotIn("<animate", self.html)
        self.assertNotIn("<linearGradient", self.html)
        self.assertNotIn("<radialGradient", self.html)
        self.assertNotIn('filter="url(', self.html)
        self.assertNotIn("<pattern", self.html)
        self.assertNotIn('fill="url(', self.html)

    def test_front_header_and_single_spec_line(self):
        for text in ("ANALOG CIRCUIT ROADMAP",
                     "19 章 · 5 篇 · 三层读法 · 16K 全彩"):
            self.assertIn(text, self.html)
        self.assertNotIn("16K · 全彩印刷", self.html)
        self.assertNotIn("FIG. 0", self.html)
        self.assertNotIn("阅读路径", self.html)
        self.assertNotIn("READING PATHS", self.html)
        self.assertNotIn("spec-strip", self.html)
        self.assertNotIn("front-caption", self.html)

    def test_back_reading_layers_and_structure(self):
        visible = visible_text(self.html)
        for text in ("三层读法", "直觉层 先看见电流怎么走",
                     "推导层 把模型算到能下手",
                     "工程层 仿真、实测与排故闭环",
                     "五篇", "第一篇 基础", "第二篇 器件",
                     "第三篇 拓扑", "第四篇 设计", "第五篇 调试",
                     "电路直觉、无源元件与基本定律",
                     "二极管、BJT、MOSFET 与运放内部",
                     "放大、比较、电源、定时与信号产生",
                     "设计方法、参数容差与 PCB 实战",
                     "排故五步、故障速查与大师心法",
                     "读 → 算 → 仿 → 测 → 排",
                     "每章沿这条路线走完一轮",
                     "185 × 260 mm · 全彩 · 胶装"):
            self.assertIn(text, visible)
        self.assertNotIn("配套资源", visible)
        self.assertNotIn("5 步", visible)
        self.assertNotIn("4 项", visible)

    def test_structure_section_omitted_when_absent(self):
        manifest = copy.deepcopy(MANIFEST)
        del manifest["cover"]["back_cover"]["structure"]
        html = cover_html(manifest, 650)
        self.assertNotIn("五篇", html)
        self.assertIn("三层读法", html)
        self.assertIn("读 → 算 → 仿 → 测 → 排", html)
        # 没有结构数据时退化为要点索引，不能让背封中缝空掉。
        self.assertIn("本书要点", html)
        self.assertIn("19 章完整知识链", html)

    def test_spine_author_rotates_instead_of_stacking(self):
        css = (config.COVER_DIR / "cover.css").read_text(encoding="utf-8")
        self.assertIn("text-orientation: mixed", css)

    def test_low_contrast_labels_are_raised(self):
        css = (config.COVER_DIR / "cover.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.front-spec\s*\{[^}]*#a9b7c6")
        self.assertRegex(css, r"\.back-kicker\s*\{[^}]*#b45309")
        self.assertNotIn("#8a94a0", css)
        self.assertAlmostEqual(
            6.35, contrast_ratio("#52606d", "#fffdf8"), delta=0.01)
        self.assertGreater(contrast_ratio("#a9b7c6", "#0e1b2b"), 7.0)
        self.assertGreater(contrast_ratio("#f2b84b", "#0e1b2b"), 7.0)
        author_rule = re.search(r"\.spine-author\s*\{([^}]*)\}", css)
        self.assertIsNotNone(author_rule)
        self.assertNotIn("opacity", author_rule.group(1))
        self.assertIn("font-size: 8.5pt", author_rule.group(1))
        self.assertIn("letter-spacing: .08em", author_rule.group(1))


@unittest.skipIf(fitz is None or sync_playwright is None,
                 "需要 PyMuPDF 与 Playwright")
class CoverBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.out = Path(cls.tmp.name) / "dist"
        cls.html_path, cls.pdf_path, cls.png_path = build_cover(
            cls.out, 650, MANIFEST)

    def test_pdf_size_and_single_page(self):
        report = inspect_cover(self.pdf_path, 650, MANIFEST)
        self.assertEqual([], report["problems"])
        self.assertEqual(1, report["pages"])
        width, height = report["size_mm"]
        self.assertAlmostEqual(409.5, width, delta=0.5)
        self.assertAlmostEqual(266.0, height, delta=0.5)

    def test_preview_is_150dpi(self):
        doc = fitz.open(self.pdf_path)
        try:
            pix = doc[0].get_pixmap(dpi=150)
            expected_width = round(409.5 / 25.4 * 150)
            self.assertAlmostEqual(expected_width, pix.width, delta=3)
            self.assertTrue(self.png_path.is_file())
            self.assertGreater(self.png_path.stat().st_size, 50_000)
        finally:
            doc.close()

    def test_text_survives_printing(self):
        doc = fitz.open(self.pdf_path)
        try:
            text = doc[0].get_text()
        finally:
            doc.close()
        for value in ("通往模拟电路之路", "从欧姆定律到芯片内部结构",
                      "zhuguang-ZFG 与贡献者", "ISBN / 条码预留区"):
            self.assertIn(value, text)

    def test_build_refuses_wrong_page_count(self):
        with self.assertRaises(ValueError):
            build_cover(self.out / "bad", 0, MANIFEST)


if __name__ == "__main__":
    unittest.main()
