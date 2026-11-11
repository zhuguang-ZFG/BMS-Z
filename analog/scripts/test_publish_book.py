"""16K 产物生成三种格式与印刷规格下载页（Phase 5 接入 Pages）。"""
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish_book import BOOK_DIR_NAME, BOOK_URL, publish  # noqa: E402

BOOK_HTML = """<!doctype html>
<html><head>
<meta name="book-version" content="1.2.3">
<meta name="book-date" content="2026-10-24">
<meta name="book-author" content="zhuguang-ZFG 与贡献者">
</head><body>
<section class="book-page" data-part-title="第一篇"><img alt=""></section>
<section class="book-page" data-part-title="第一篇"><span class="arithmatex"></span></section>
</body></html>
"""

REPORT = {
    "schema": 1, "edition_status": "draft", "version": "1.2.3",
    "logical_pages": 2, "parts": 1, "figures": 1, "tables": 0,
    "formulas": 1, "pdf_pages": 4,
    "cover": {"spine_mm": 1.2, "size_mm": [376.0, 266.0]},
}


class PublishBookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.site = self.root / "site"
        self.site.mkdir()
        (self.site / "index.html").write_text(
            "<!doctype html><title>site</title>", encoding="utf-8")
        self.html = self.root / "analog-circuit-book.html"
        self.html.write_text(BOOK_HTML, encoding="utf-8")
        self.pdf = self.root / "analog-circuit-book.pdf"
        self.pdf.write_bytes(b"%PDF-1.7\n" + b"0" * 4096)
        self.cover_pdf = self.root / "cover.pdf"
        self.cover_pdf.write_bytes(b"%PDF-1.7\n" + b"1" * 1024)
        self.cover_preview = self.root / "cover-preview.png"
        self.cover_preview.write_bytes(b"\x89PNG\r\n\x1a\n" + b"2" * 512)
        self.print_spec = self.root / "PRINT-SPEC.md"
        self.print_spec.write_text(
            "# 印刷规格\n\n16K 185 × 260 mm\n", encoding="utf-8")
        self.report = self.root / "build-report.json"
        self.report.write_text(
            json.dumps(REPORT, ensure_ascii=False), encoding="utf-8")

    def publish(self):
        return publish(self.html, self.pdf, self.site, self.cover_pdf,
                       self.cover_preview, self.print_spec, self.report)

    def test_copies_artifacts_and_writes_landing_page(self):
        target = self.publish()
        self.assertEqual(self.site / BOOK_DIR_NAME, target)
        for name in ("analog-circuit-book.html", "analog-circuit-book.pdf",
                     "cover.pdf", "cover-preview.png", "PRINT-SPEC.md",
                     "build-report.json", "og-cover.png"):
            self.assertTrue((target / name).is_file(), name)
        landing = (target / "index.html").read_text(encoding="utf-8")
        for text in ("离线整书", "1.2.3", "2026-10-24", "16K",
                     "185 × 260 mm", "1.2 mm",
                     'href="analog-circuit-book.html"',
                     'href="analog-circuit-book.pdf"',
                     'href="cover.pdf"', 'href="PRINT-SPEC.md"',
                     'href="build-report.json"', "4 KB",
                     'href="../index.html"'):
            self.assertIn(text, landing)
        self.assertNotIn("A4 PDF", landing)

    def test_landing_shows_cover_stats_and_share_metadata(self):
        target = self.publish()
        landing = (target / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="cover-card"', landing)
        self.assertIn("<svg", landing)
        self.assertIn("cover-sketch", landing)
        self.assertIn("zhuguang-ZFG 与贡献者", landing)
        self.assertIn('<meta name="author" content="zhuguang-ZFG 与贡献者">',
                      landing)
        for label in ("个逻辑页", "篇结构", "张图表", "个公式"):
            self.assertIn(label, landing)
        self.assertEqual(1, landing.count("<strong>2</strong>"),
                         "两页同属一篇")
        self.assertEqual(3, landing.count("<strong>1</strong>"),
                         "一篇、一张图、一个公式")
        self.assertIn("单文件 HTML", landing)
        self.assertIn("16K 内文 PDF", landing)
        self.assertIn("印刷封面 PDF", landing)
        self.assertIn("印刷规格", landing)
        self.assertIn("构建报告", landing)
        self.assertIn('<img class="cover-preview" src="cover-preview.png"',
                      landing)
        self.assertIn('name="description"', landing)
        self.assertIn('property="og:title"', landing)
        self.assertIn('rel="icon"', landing)
        self.assertIn("prefers-color-scheme: dark", landing)
        self.assertIn(f'<link rel="canonical" href="{BOOK_URL}">', landing)
        self.assertIn(f'property="og:url" content="{BOOK_URL}"', landing)
        self.assertIn(
            f'property="og:image" content="{BOOK_URL}og-cover.png"', landing)
        self.assertIn('property="og:image:width" content="1200"', landing)
        self.assertIn('property="og:image:height" content="630"', landing)
        self.assertIn('property="og:image:alt"', landing)
        self.assertIn('name="twitter:card" content="summary_large_image"',
                      landing)
        self.assertIn(
            f'name="twitter:image" content="{BOOK_URL}og-cover.png"', landing)
        image = (target / "og-cover.png").read_bytes()
        self.assertEqual(b"\x89PNG\r\n\x1a\n", image[:8])
        self.assertEqual((1200, 630), struct.unpack(">II", image[16:24]))

    def test_rejects_missing_artifact(self):
        self.pdf.unlink()
        with self.assertRaises(FileNotFoundError):
            self.publish()

    def test_rejects_missing_cover(self):
        self.cover_pdf.unlink()
        with self.assertRaises(FileNotFoundError):
            self.publish()

    def test_rejects_missing_site_index(self):
        (self.site / "index.html").unlink()
        with self.assertRaises(FileNotFoundError):
            self.publish()

    def test_rejects_report_without_required_fields(self):
        self.report.write_text(json.dumps({"edition_status": "draft"}),
                               encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "构建报告缺少字段"):
            self.publish()


if __name__ == "__main__":
    unittest.main()
