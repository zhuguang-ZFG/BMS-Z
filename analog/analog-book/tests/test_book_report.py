#!/usr/bin/env python3
"""构建报告与 PRINT-SPEC：只读事实、书脊算术、草稿门与稳定版。"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import config, report  # noqa: E402
from book.manifest import BookError  # noqa: E402

MANIFEST = {
    "title": "通往模拟电路之路",
    "edition": "第一版",
    "version": "2.0.0-draft.1",
    "source_version": "3.61",
    "date": "2026-10-25",
    "trim": {"width_mm": 185, "height_mm": 260},
    "parts": [{"id": str(i), "units": [{"chapters": [f"c{i}"]}]}
              for i in range(5)],
    "cover": {"bleed_mm": 3, "paper_caliper_mm": 0.10,
              "spine_allowance_mm": 1.0},
    "release": {"edition_status": "draft"},
}
MODEL = {
    "pages": [{"id": f"p{i}"} for i in range(77)],
    "stats": {"figures": 12, "tables": 8, "formulas": 900, "images": 200},
    "endnotes": 123,
    "audit": {"errors": [], "warnings": ["draft word count"]},
}
PDF = {"pages": 652, "body_start": 13, "bookmarks": 143,
       "size_mm": [184.83, 260.01],
       "problems": [],
       "warnings": ["草稿只检查 16K 结构项；印前全检在 Phase 5 执行"]}
COVER = {"pages": 1, "size_mm": [409.6, 266.0],
         "spine_mm": 33.6, "problems": []}


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)
        files = {
            config.OUTPUT_NAME: b"<!doctype html><title>book</title>",
            config.PDF_NAME: b"%PDF-1.7\n" + b"0" * 2048,
            config.COVER_PDF_NAME: b"%PDF-1.7\n" + b"1" * 1024,
            config.COVER_PREVIEW_NAME: b"\x89PNG\r\n\x1a\n" + b"2" * 512,
        }
        for name, payload in files.items():
            (self.out / name).write_bytes(payload)

    def write(self, manifest=MANIFEST, pdf=PDF, cover=COVER):
        return report.write_report(
            self.out, MODEL, manifest, pdf, cover,
            sample_report={"fallback": "mirrored"})

    def test_json_report_records_actual_facts(self):
        data = self.write()
        self.assertEqual(77, data["logical_pages"])
        self.assertEqual(5, data["parts"])
        self.assertEqual(652, data["pdf_pages"])
        self.assertEqual(13, data["body_start"])
        self.assertEqual(143, data["bookmarks"])
        self.assertEqual(20, data["figures"] + data["tables"])
        self.assertEqual("PDF 1.7", data["pdf_version"])
        self.assertEqual("mirrored", data["mirrored"])
        self.assertEqual(652, data["cover"]["pages"])
        self.assertEqual(33.6, data["cover"]["spine_mm"])
        self.assertEqual([409.6, 266.0], data["cover"]["size_mm"])
        self.assertEqual([184.83, 260.01], data["interior_size_mm"])
        self.assertEqual(PDF["warnings"], data["pdf_warnings"])
        self.assertIn("Phase 5", data["preflight"])
        saved = json.loads(
            (self.out / "build-report.json").read_text(encoding="utf-8"))
        self.assertEqual(data, saved)

    def test_print_spec_has_spine_math_and_no_fake_isbn(self):
        self.write()
        spec = (self.out / "PRINT-SPEC.md").read_text(encoding="utf-8")
        self.assertIn("652 / 2 × 0.10 + 1.0 = 33.60 mm", spec)
        self.assertIn("2 × 185 + 33.60 + 2 × 3 = 409.60 mm", spec)
        self.assertIn("185 × 260 mm", spec)
        self.assertIn("未申请 ISBN", spec)
        self.assertNotIn("978-", spec)
        self.assertIn("草稿", spec)
        self.assertIn("内文实际 MediaBox | 184.83 × 260.01 mm", spec)
        self.assertIn("4 的倍数：是", spec)
        self.assertIn("印前全检：未执行（Phase 5 印前门禁）", spec)
        self.assertIn("## 9 PDF 结构检查警告", spec)
        self.assertIn(PDF["warnings"][0], spec)
        self.assertIn("BookSans-Stamp.ttf", spec)
        for heading in ("开本与版心", "页数、书脊与封面", "字体与许可",
                        "打样与校对页", "尚未关闭的质量门"):
            self.assertIn(heading, spec)

    def test_print_spec_separates_nominal_cover_from_actual_mediabox(self):
        pdf = {"pages": 528, "body_start": 13, "bookmarks": 120,
               "problems": [], "warnings": []}
        cover = {"pages": 528, "size_mm": [403.27, 266.02],
                 "spine_mm": 27.4, "problems": []}
        self.write(pdf=pdf, cover=cover)
        spec = (self.out / "PRINT-SPEC.md").read_text(encoding="utf-8")
        self.assertIn("2 × 185 + 27.40 + 2 × 3 = 403.40 mm（标称）", spec)
        self.assertIn("260 + 2 × 3 = 266.00 mm（标称）", spec)
        self.assertIn("实际 MediaBox 403.27 × 266.02 mm", spec)
        self.assertNotIn("= 403.27 mm", spec)
        self.assertNotIn("= 266.02 mm", spec)

    def test_problems_block_report(self):
        broken = dict(COVER, problems=["spine mismatch"])
        with self.assertRaisesRegex(BookError, "封面结构问题"):
            self.write(cover=broken)

    def test_final_has_no_deferred_gates(self):
        final = {**MANIFEST, "release": {"edition_status": "final"}}
        data = self.write(manifest=final)
        self.assertEqual([], data["deferred"])
        spec = (self.out / "PRINT-SPEC.md").read_text(encoding="utf-8")
        self.assertIn("无（本版为稳定版）", spec)
        self.assertIn("印前全检：未执行", spec)

    def test_print_spec_geometry_matches_print_css(self):
        css = (config.BOOK_DIR / "styles" / "print.css").read_text(
            encoding="utf-8")
        page = re.search(
            r"@page\s*\{\s*size:\s*(\d+)mm\s+(\d+)mm;\s*"
            r"margin:\s*(\d+)mm\s+(\d+)mm\s+(\d+)mm;", css)
        left = re.search(
            r"@page\s*:left\s*\{\s*margin:\s*(\d+)mm\s+(\d+)mm\s+"
            r"(\d+)mm\s+(\d+)mm;", css)
        right = re.search(
            r"@page\s*:right\s*\{\s*margin:\s*(\d+)mm\s+(\d+)mm\s+"
            r"(\d+)mm\s+(\d+)mm;", css)
        self.assertIsNotNone(page)
        self.assertIsNotNone(left)
        self.assertIsNotNone(right)
        width, height, top, _right_margin, bottom = map(int, page.groups())
        left_top, inside, left_bottom, outside = map(int, left.groups())
        right_top, right_outside, right_bottom, right_inside = map(
            int, right.groups())
        self.assertEqual((top, bottom), (left_top, left_bottom))
        self.assertEqual((top, bottom), (right_top, right_bottom))
        self.assertEqual(inside, right_inside)
        self.assertEqual(outside, right_outside)
        data = self.write()
        self.assertEqual([width, height], data["trim_mm"])
        self.assertEqual([width - inside - outside, height - top - bottom],
                         data["text_block_mm"])
        self.assertEqual(
            {"top": top, "bottom": bottom,
             "inside": inside, "outside": outside},
            data["margins_mm"])

    def test_print_css_lets_long_tables_split_and_repeat_headers(self):
        css = (config.BOOK_DIR / "styles" / "print.css").read_text(
            encoding="utf-8")
        self.assertIn(
            ".book .book-table { margin: 3mm 0 0; break-inside: auto; }", css)
        self.assertIn(".book .table-wrap { break-inside: auto; }", css)
        self.assertIn("thead { display: table-header-group; }", css)
        self.assertIn("tr { break-inside: avoid; }", css)
        caption = re.search(
            r"\.book \.md-typeset \.table-caption \{[^}]*\}", css)
        self.assertIsNotNone(caption)
        self.assertIn("break-after: avoid", caption.group(0))
        self.assertNotIn("\n.book-table { break-inside: avoid; }", css,
                         "残留的低特异性规则会与跨页表冲突")

    def test_style_evidence_levels_match_reader_conventions(self):
        style = (config.BOOK_DIR / "STYLE.md").read_text(encoding="utf-8")
        conventions = (config.DOCS / "p0-11-conventions.md").read_text(
            encoding="utf-8")
        style_rows = (
            "| A | 教材、手册、厂商数据手册、应用笔记 | 给出书名/版次/章节，或厂商与文档编号 |",
            "| B | 可复现的仿真 | 给出 `assets/spice/` 下的 deck 与分析方法 |",
            "| C | 本仓库实测 | 仅限 RC、LM358、MOSFET；给 CSV、仪器条件与日期 |",
            "| D | 经验判断、工程惯例 | 明写“经验/待验证”，不冒充结论 |",
        )
        convention_rows = (
            style_rows[0],
            style_rows[1],
            "| C | 本仓库实测 | 只限 RC、LM358、MOSFET 三套实验，给 CSV、仪器条件与日期 |",
            "| D | 经验判断、工程惯例 | 用“经验上”“通常”“量级”标明 |",
        )
        for row in style_rows:
            self.assertIn(row, style)
        for row in convention_rows:
            self.assertIn(row, conventions)

    def test_report_inputs_reject_zero_byte_artifacts(self):
        from book import cli
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / config.PDF_NAME).write_bytes(b"")
            (out / config.COVER_PDF_NAME).write_bytes(b"%PDF-1.7")
            with self.assertRaisesRegex(BookError, "缺少或为空"):
                cli._report_inputs(out)
            (out / config.PDF_NAME).write_bytes(b"%PDF-1.7")
            (out / config.COVER_PDF_NAME).write_bytes(b"")
            with self.assertRaisesRegex(BookError, "缺少或为空"):
                cli._report_inputs(out)

    def test_style_guide_is_executable(self):
        text = (config.BOOK_DIR / "STYLE.md").read_text(encoding="utf-8")
        for heading in ("三层读法", "证据等级", "仿真与实测", "交稿检查"):
            self.assertIn(heading, text)


if __name__ == "__main__":
    unittest.main()
