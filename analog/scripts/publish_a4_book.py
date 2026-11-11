#!/usr/bin/env python3
"""Copy the built offline book into the Pages site tree."""
import argparse
import html
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HTML = ROOT / "analog-book" / "dist" / "analog-circuit-book.html"
DEFAULT_PDF = ROOT / "analog-book" / "dist" / "analog-circuit-book.pdf"
DEFAULT_SITE = ROOT / "build" / "site"
COVER_ART = ROOT / "analog-book" / "static" / "cover-art.svg"
OG_IMAGE = ROOT / "assets" / "og-cover.png"
BOOK_DIR_NAME = "book"
REPOSITORY = "https://github.com/zhuguang-ZFG/analog-circuit-roadmap"
SITE_URL = "https://aliyun-hutuji.donglicao.com/analog-circuit-roadmap/"
BOOK_URL = SITE_URL + BOOK_DIR_NAME + "/"
OG_WIDTH, OG_HEIGHT = 1200, 630

FAVICON = "data:image/svg+xml," + quote(
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
    "<rect width='32' height='32' rx='7' fill='#1f2933'/>"
    "<path d='M5 16h6l3-6 4 12 3-6h6' fill='none' stroke='#f0c38a' "
    "stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'/></svg>")

LANDING_CSS = """
:root {
  color-scheme: light dark;
  --paper: #fffdf8; --ink: #1f2933; --muted: #52606d; --brand: #b45309;
  --line: #d9e2ec; --card: #fff; --shadow: 0 24px 60px rgba(31, 41, 51, .14);
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--paper); color: var(--ink); line-height: 1.7;
  font-family: -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei",
    "Noto Sans CJK SC", sans-serif;
}
a { color: var(--brand); }
main { max-width: 1040px; margin: 0 auto; padding: 7vh 24px 64px; }
.hero {
  display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(260px, .85fr);
  gap: clamp(28px, 5vw, 64px); align-items: center;
}
.kicker { margin: 0 0 10px; color: var(--brand); font-size: 14px; letter-spacing: .14em; }
h1 {
  margin: 0 0 10px; font-size: clamp(2.6rem, 8vw, 4.2rem);
  line-height: 1.05; letter-spacing: -.01em;
}
.meta { margin: 0 0 18px; color: var(--muted); font-size: 14px; font-variant-numeric: tabular-nums; }
.lede { margin: 0 0 26px; max-width: 46ch; font-size: 17px; }
kbd {
  padding: 1px 5px; border: 1px solid var(--line); border-radius: 4px;
  background: var(--card); font: inherit; font-size: .85em;
}
.stats {
  list-style: none; margin: 0; padding: 0; display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px;
}
.stats li {
  padding: 12px 10px; border: 1px solid var(--line); border-radius: 10px;
  background: var(--card); text-align: center;
}
.stats strong {
  display: block; color: var(--ink); font-size: 22px; line-height: 1.2;
  font-variant-numeric: tabular-nums;
}
.stats span { display: block; margin-top: 2px; color: var(--muted); font-size: 12px; }
.cover-card {
  justify-self: center; width: min(100%, 340px); padding: 18px 18px 22px;
  background: #fffdf8; border: 1px solid #e3dbcc; border-radius: 16px;
  box-shadow: var(--shadow); text-align: center; color: #1f2933;
}
.cover-card svg { display: block; width: 100%; height: auto; margin-bottom: 14px; }
.cover-title { margin: 0; font-size: 24px; line-height: 1.25; letter-spacing: .02em; }
.cover-author { margin: 4px 0 0; color: #b45309; font-size: 13px; font-weight: 600; letter-spacing: .04em; }
.cover-meta { margin: 6px 0 0; color: #52606d; font-size: 13px; }
.downloads { margin-top: clamp(36px, 6vw, 64px); }
.downloads h2 { margin: 0 0 14px; font-size: 22px; }
.formats {
  display: grid; gap: 12px; grid-template-columns: repeat(2, minmax(0, 1fr));
}
.format {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 18px; padding: 18px 20px; border: 1px solid var(--line);
  border-radius: 12px; background: var(--card); color: var(--ink);
  text-decoration: none;
}
.format:hover { border-color: var(--brand); }
.format strong { display: flex; align-items: center; gap: 8px; font-size: 17px; }
.tag {
  padding: 1px 7px; border-radius: 999px; background: #fdf3e3;
  color: #b45309; font-size: 11px; font-weight: 600;
}
.format p { margin: 6px 0 0; color: var(--muted); font-size: 13px; line-height: 1.5; }
.size { flex: none; color: var(--muted); font-size: 14px; font-variant-numeric: tabular-nums; }
.note { margin: 22px 0 0; color: var(--muted); font-size: 13px; }
.back {
  display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center;
  margin-top: 30px; color: var(--muted); font-size: 14px;
}
.back a { font-weight: 600; text-decoration: none; }
.back a:hover { text-decoration: underline; }
a:focus-visible { outline: 2px solid var(--brand); outline-offset: 3px; border-radius: 4px; }
@media (max-width: 820px) {
  main { padding-top: 5vh; }
  .hero { grid-template-columns: 1fr; }
  .cover-card { order: -1; width: min(100%, 300px); }
  .formats { grid-template-columns: 1fr; }
}
@media (max-width: 420px) {
  .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (prefers-color-scheme: dark) {
  :root {
    --paper: #14181d; --ink: #e8edf2; --muted: #9aa7b4; --brand: #f0c38a;
    --line: #323c47; --card: #1d232b; --shadow: 0 24px 60px rgba(0, 0, 0, .45);
  }
  .cover-card { box-shadow: 0 24px 60px rgba(0, 0, 0, .5); }
  .tag { background: #3a2d1c; color: #f0c38a; }
}
"""


def _meta(document: str, name: str) -> str:
    match = re.search(
        r'<meta name="%s" content="([^"]*)"' % re.escape(name), document)
    return html.unescape(match.group(1)) if match else ""


def _human_size(size: int) -> str:
    if size >= 1024 * 1024:
        return "%.1f MB" % (size / (1024 * 1024))
    return "%d KB" % max(1, round(size / 1024))


def _stats(document: str) -> list[tuple[str, str]]:
    pages = document.count('class="book-page"')
    parts = len(set(re.findall(r'data-part-title="([^"]*)"', document)))
    images = document.count("<img ")
    formulas = document.count('class="arithmatex"')
    return [
        (f"{pages:,}", "页正文"),
        (f"{parts:,}", "篇结构"),
        (f"{images:,}", "张图表"),
        (f"{formulas:,}", "个公式"),
    ]


def _cover_art() -> str:
    if not COVER_ART.is_file():
        raise FileNotFoundError(f"封面插图不存在: {COVER_ART}")
    return COVER_ART.read_text(encoding="utf-8")


def _landing(version: str, date: str, html_name: str, pdf_name: str,
             html_size: int, pdf_size: int, stats: list[tuple[str, str]],
             art: str, author: str) -> str:
    meta = " · ".join(part for part in (
        ("版本 " + version) if version else "", date) if part)
    meta_html = f'<p class="meta">{html.escape(meta)}</p>' if meta else ""
    stats_html = "".join(
        f"<li><strong>{html.escape(value)}</strong><span>{html.escape(label)}</span></li>"
        for value, label in stats)
    pages = stats[0][0] if stats else ""
    description = html.escape(
        f"《通往模拟电路之路》离线整书：{pages} 页正文，单文件 HTML 与 A4 PDF，"
        "断网可读，内置全文搜索。", quote=True)
    share_title = "离线整书 · 通往模拟电路之路"
    canonical = html.escape(BOOK_URL, quote=True)
    share_image = html.escape(BOOK_URL + OG_IMAGE.name, quote=True)
    author_html = (f'<p class="cover-author">{html.escape(author)}</p>'
                   if author else "")
    author_meta = (f'<meta name="author" content="{html.escape(author, quote=True)}">'
                   if author else "")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="description" content="{description}">
{author_meta}
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="通往模拟电路之路">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{share_title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="{share_image}">
<meta property="og:image:width" content="{OG_WIDTH}">
<meta property="og:image:height" content="{OG_HEIGHT}">
<meta property="og:image:alt" content="《通往模拟电路之路》离线整书封面">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{share_title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{share_image}">
<meta name="theme-color" content="#fffdf8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#14181d" media="(prefers-color-scheme: dark)">
<link rel="icon" href="{FAVICON}">
<title>{share_title}</title>
<style>{LANDING_CSS}</style>
</head>
<body>
<main>
<section class="hero">
<div class="copy">
<p class="kicker">通往模拟电路之路</p>
<h1>离线整书</h1>
{meta_html}
<p class="lede">单文件 HTML 与 A4 PDF，同一本书的两种读法。断网也能排版公式、运行计算器、按 <kbd>Ctrl</kbd> + <kbd>K</kbd> 搜索全书。</p>
<ul class="stats">{stats_html}</ul>
</div>
<div class="cover-card" aria-hidden="true">
{art}
<p class="cover-title">通往模拟电路之路</p>
{author_html}
<p class="cover-meta">版本 {html.escape(version or date)}</p>
</div>
</section>
<section class="downloads" aria-labelledby="formats-title">
<h2 id="formats-title">选择格式</h2>
<div class="formats">
<a class="format" href="{html.escape(html_name)}">
<div><strong>单文件 HTML <span class="tag">推荐</span></strong><p>断网可读 · 动画与计算器可用 · Ctrl+K 全文搜索</p></div>
<span class="size">{_human_size(html_size)}</span>
</a>
<a class="format" href="{html.escape(pdf_name)}">
<div><strong>A4 PDF</strong><p>适合打印与批注 · 书签跳转 · 页眉与印刷页码</p></div>
<span class="size">{_human_size(pdf_size)}</span>
</a>
</div>
</section>
<p class="note">每次 main 分支构建自动更新 · 内容许可 CC BY-SA 4.0</p>
<footer class="back">
<a href="../index.html">返回在线站</a><span aria-hidden="true">·</span>
<a href="{REPOSITORY}">GitHub 仓库</a>
</footer>
</main>
</body>
</html>
"""


def publish(html_path: Path, pdf_path: Path, site_dir: Path) -> Path:
    for path in (html_path, pdf_path):
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"整书产物不存在或为空: {path}")
    if not (site_dir / "index.html").is_file():
        raise FileNotFoundError(f"站点产物不存在，请先构建站点: {site_dir}")
    if not OG_IMAGE.is_file():
        raise FileNotFoundError(f"社交分享图不存在: {OG_IMAGE}")
    target = site_dir / BOOK_DIR_NAME
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(html_path, target / html_path.name)
    shutil.copy2(pdf_path, target / pdf_path.name)
    shutil.copy2(OG_IMAGE, target / OG_IMAGE.name)
    document = html_path.read_text(encoding="utf-8")
    version = _meta(document, "book-version")
    date = _meta(document, "book-date")
    author = _meta(document, "book-author")
    (target / "index.html").write_text(
        _landing(version, date, html_path.name, pdf_path.name,
                 html_path.stat().st_size, pdf_path.stat().st_size,
                 _stats(document), _cover_art(), author),
        encoding="utf-8", newline="\n")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--site-dir", type=Path, default=DEFAULT_SITE)
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        target = publish(args.html, args.pdf, args.site_dir)
    except FileNotFoundError as exc:
        print(f"publish error: {exc}", file=sys.stderr)
        return 1
    print(f"published {target} ({args.html.name}, {args.pdf.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
