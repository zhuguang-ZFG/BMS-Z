"""整书产物必须并入 Pages 站点，并生成可点开两种格式的下载页。"""
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish_a4_book import BOOK_DIR_NAME, BOOK_URL, publish  # noqa: E402

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


class PublishBookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.site = self.root / "site"
        self.site.mkdir()
        (self.site / "index.html").write_text("<!doctype html><title>site</title>", encoding="utf-8")
        self.html = self.root / "analog-circuit-book.html"
        self.html.write_text(BOOK_HTML, encoding="utf-8")
        self.pdf = self.root / "analog-circuit-book.pdf"
        self.pdf.write_bytes(b"%PDF-1.7\n" + b"0" * 4096)

    def test_copies_artifacts_and_writes_landing_page(self):
        target = publish(self.html, self.pdf, self.site)
        self.assertEqual(self.site / BOOK_DIR_NAME, target)
        self.assertTrue((target / "analog-circuit-book.html").is_file())
        self.assertTrue((target / "analog-circuit-book.pdf").is_file())
        landing = (target / "index.html").read_text(encoding="utf-8")
        self.assertIn("离线整书", landing)
        self.assertIn("1.2.3", landing)
        self.assertIn("2026-10-24", landing)
        self.assertIn('href="analog-circuit-book.html"', landing)
        self.assertIn('href="analog-circuit-book.pdf"', landing)
        self.assertIn("4 KB", landing)
        self.assertIn('href="../index.html"', landing)

    def test_landing_shows_cover_stats_and_share_metadata(self):
        target = publish(self.html, self.pdf, self.site)
        landing = (target / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="cover-card"', landing)
        self.assertIn("<svg", landing)
        self.assertIn("cover-sketch", landing)
        self.assertIn("zhuguang-ZFG 与贡献者", landing)
        self.assertIn('<meta name="author" content="zhuguang-ZFG 与贡献者">', landing)
        for label in ("页正文", "篇结构", "张图表", "个公式"):
            self.assertIn(label, landing)
        self.assertEqual(1, landing.count("<strong>2</strong>"), "两页同属一篇")
        self.assertEqual(3, landing.count("<strong>1</strong>"), "一篇、一张图、一个公式")
        self.assertIn("单文件 HTML", landing)
        self.assertIn("A4 PDF", landing)
        self.assertIn('name="description"', landing)
        self.assertIn('property="og:title"', landing)
        self.assertIn('rel="icon"', landing)
        self.assertIn("prefers-color-scheme: dark", landing)
        self.assertIn(f'<link rel="canonical" href="{BOOK_URL}">', landing)
        self.assertIn(f'property="og:url" content="{BOOK_URL}"', landing)
        self.assertIn(f'property="og:image" content="{BOOK_URL}og-cover.png"', landing)
        self.assertIn('property="og:image:width" content="1200"', landing)
        self.assertIn('property="og:image:height" content="630"', landing)
        self.assertIn('property="og:image:alt"', landing)
        self.assertIn('name="twitter:card" content="summary_large_image"', landing)
        self.assertIn(f'name="twitter:image" content="{BOOK_URL}og-cover.png"', landing)
        image = (target / "og-cover.png").read_bytes()
        self.assertEqual(b"\x89PNG\r\n\x1a\n", image[:8])
        self.assertEqual((1200, 630), struct.unpack(">II", image[16:24]))

    def test_rejects_missing_artifact(self):
        self.pdf.unlink()
        with self.assertRaises(FileNotFoundError):
            publish(self.html, self.pdf, self.site)

    def test_rejects_missing_site_index(self):
        (self.site / "index.html").unlink()
        with self.assertRaises(FileNotFoundError):
            publish(self.html, self.pdf, self.site)


if __name__ == "__main__":
    unittest.main()
