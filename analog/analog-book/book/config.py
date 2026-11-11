from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parent.parent
ROOT = BOOK_DIR.parent
DOCS = ROOT / "docs"
SITE_DIR = ROOT / "build" / "site"
DIST_DIR = BOOK_DIR / "dist" / "print"  # 16K 产物；A4 1.0 仍在 dist/ 根
MANIFEST_PATH = BOOK_DIR / "manifest.json"
FONTS_DIR = BOOK_DIR / "fonts"
DATA_DIR = BOOK_DIR / "data"
STYLES_DIR = BOOK_DIR / "styles"
STATIC_DIR = BOOK_DIR / "static"
COVER_DIR = BOOK_DIR / "cover"

OUTPUT_NAME = "analog-circuit-book.html"
PDF_NAME = "analog-circuit-book.pdf"
COVER_PDF_NAME = "cover.pdf"
COVER_PREVIEW_NAME = "cover-preview.png"
MODEL_NAME = "book-model.json"
SAMPLE_HTML_NAME = "sample.html"
SAMPLE_PDF_NAME = "sample.pdf"
SAMPLE_REPORT_NAME = "sample-report.json"

HTML_TARGET_BYTES = 60 * 1024 * 1024
MAX_HTML_BYTES = 80 * 1024 * 1024
MAX_PDF_BYTES = 100 * 1024 * 1024

TRIM_WIDTH_MM = 185.0
TRIM_HEIGHT_MM = 260.0
TEXT_WIDTH_MM = 145.0
TEXT_HEIGHT_MM = 218.0
BLEED_MM = 3.0
