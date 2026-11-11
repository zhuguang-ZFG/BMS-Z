import base64
import html
import re
from pathlib import Path

from fontTools.ttLib import TTFont

from . import config

FONT_FACES = [
    ("Book Serif", 400, "NotoSerifSC-Regular.woff2"),
    ("Book Serif", 700, "NotoSerifSC-Bold.woff2"),
    ("Book Sans", 400, "NotoSansSC-Regular.woff2"),
    ("Book Sans", 700, "NotoSansSC-Bold.woff2"),
    ("Book Mono", 400, "JetBrainsMono-Regular.woff2"),
]
STAMP_FONT_NAME = "BookSans-Stamp.ttf"
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2300-\u23FF\u2600-\u27BF\u2B00-\u2BFF"
    "\uFE0F\u200D]+")

def _strip_emoji(text: str) -> str:
    return EMOJI_RE.sub("", text)

def required_text(docs_dir=config.DOCS, book_dir=config.BOOK_DIR) -> str:
    chunks = []
    for path in sorted(Path(docs_dir).glob("*.md")):
        chunks.append(path.read_text(encoding="utf-8"))
    for path in sorted((Path(book_dir) / "book").glob("*.py")):
        chunks.append(path.read_text(encoding="utf-8"))
    chunks.append((Path(book_dir) / "manifest.json").read_text(encoding="utf-8"))
    data = Path(book_dir) / "data"
    if data.is_dir():
        for path in sorted(data.glob("*.yml")):
            chunks.append(path.read_text(encoding="utf-8"))
    # 站点还发布根目录页面（CONTRIBUTING/CONTRIBUTORS/CREDITS）与 build_site.py
    # 里硬写的 UI 文案（画廊/筛选/页脚等）。这些字不在 docs/*.md 里，漏掉的话
    # 子集缺字而 test_book_fonts 的覆盖率护栏却查不出来。
    for path in sorted(config.ROOT.glob("*.md")):
        chunks.append(path.read_text(encoding="utf-8"))
    chunks.append((config.ROOT / "scripts" / "build_site.py").read_text(
        encoding="utf-8"))
    for path in sorted((config.ROOT / "scripts" / "site_media").glob("*")):
        if path.suffix in {".css", ".js"}:
            chunks.append(path.read_text(encoding="utf-8"))
    for folder in ("svg", "figures", "svg-v2", "figures-v2", "storyboards-v2"):
        for path in sorted((config.ROOT / "assets" / folder).rglob("*.svg")):
            chunks.append(html.unescape(re.sub(r"<[^>]+>", " ", path.read_text(
                encoding="utf-8", errors="replace"))))
    text = _strip_emoji("\n".join(chunks))
    # EMOJI_RE 也覆盖 U+2713/U+2717，而 Task 5 会把 ✅/❌ 映射成 ✓/✗ 输出；
    # 剥离 emoji 后必须显式补回这两个字形，否则子集会缺字。
    return (text + "".join(chr(c) for c in range(32, 127))
            + "　、。“”‘’—…·×÷±≤≥≠≈∞Ωμ°℃" + "✓✗")

def missing_glyphs(font_path, text) -> set[str]:
    font = TTFont(font_path)
    cmap = set()
    for table in font["cmap"].tables:
        cmap.update(table.cmap.keys())
    return {ch for ch in set(text) if ch not in "\r\n\t" and ord(ch) not in cmap}

def font_css(fonts_dir=config.FONTS_DIR) -> str:
    faces = []
    for family, weight, name in FONT_FACES:
        raw = (Path(fonts_dir) / name).read_bytes()
        uri = base64.b64encode(raw).decode("ascii")
        faces.append(
            f'@font-face{{font-family: "{family}";'
            f'src:url(data:font/woff2;base64,{uri}) format("woff2");'
            f'font-weight: {weight};font-style:normal;font-display:block}}')
    return "\n".join(faces)

def stamp_font_path(fonts_dir=config.FONTS_DIR) -> Path:
    return Path(fonts_dir) / STAMP_FONT_NAME
