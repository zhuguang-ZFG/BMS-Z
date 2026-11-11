#!/usr/bin/env python3
"""Build the offline single-file book and A4 PDF from the MkDocs site."""
import argparse
import base64
import hashlib
import html
import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

from book.content import strip_visual_players, _asset_path as visual_asset_path

BOOK_DIR = Path(__file__).resolve().parent
ROOT = BOOK_DIR.parent
DOCS = ROOT / "docs"
PRINT_ONLY_STEMS = {"p0-11-conventions", "p0-12-symbols", "p9-15-glossary"}
SITE_DIR = ROOT / "build" / "site"
DIST_DIR = BOOK_DIR / "dist"
MANIFEST_PATH = BOOK_DIR / "manifest-a4.json"
OUTPUT_NAME = "analog-circuit-book.html"
PDF_NAME = "analog-circuit-book.pdf"
# 2026-11-10 印规修订（spec owner 批准）：A4 HTML 上限 20→24 MB。
# 背景：V4/V2 图 wave 合并入正文后实测 21.46MB，超原 20MB 冻结线 1.46MB；
# A4 仍为独立受治理输出（README + 印规 spec §5.5），不取 16K 线的 60/80MB。
MAX_HTML_BYTES = 24 * 1024 * 1024
PREFACE_LABEL = "本篇导读"

ARTICLE_RE = re.compile(
    r'<article class="md-content__inner md-typeset">(.*?)</article>', re.S)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
TAG_RE = re.compile(r"<[^>]+>")
ID_ATTR_RE = re.compile(r'(?<![\w-])(id|name)="([^"]+)"')
EMBEDDED_BLOCK_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.S)


class BookError(RuntimeError):
    pass


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def manifest_sha256() -> str:
    return hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()


def validate_manifest(manifest: dict, site_dir: Path = SITE_DIR) -> list[str]:
    files = [name for part in manifest["parts"] for name in part["files"]]
    files += manifest["appendix"]["files"]
    stems = [Path(name).stem for name in files]
    actual = ({p.stem for p in DOCS.glob("*.md")} - {"index"}
              - PRINT_ONLY_STEMS)
    problems = []
    duplicates = sorted({s for s in stems if stems.count(s) > 1})
    if duplicates:
        problems.append("重复页面: " + ", ".join(duplicates))
    if set(stems) != actual:
        problems.append(
            "清单与 docs 不一致；缺少: %s；多余: %s" % (
                sorted(actual - set(stems)), sorted(set(stems) - actual)))
    if len(stems) != 60:
        problems.append("内容页应为 60，实际 %d" % len(stems))
    for page in files:
        built = site_dir / page.replace(".md", ".html")
        if not built.is_file():
            problems.append("站点产物缺失: %s" % built)
    ids = [part["id"] for part in manifest["parts"]]
    if len(ids) != len(set(ids)):
        problems.append("篇 ID 重复")
    if problems:
        raise BookError("manifest 校验失败:\n" + "\n".join(problems))
    return stems


def build_site(site_dir: Path = SITE_DIR) -> None:
    if site_dir.resolve() != SITE_DIR.resolve():
        raise BookError("自定义站点目录只能配合 --no-build 使用")
    result = subprocess.run(
        [sys.executable, "-X", "utf8",
         str(ROOT / "scripts" / "build_site.py"), "--build"],
        cwd=ROOT)
    if result.returncode != 0:
        raise BookError("站点构建失败，整书无法继续")


def _strip_tags(fragment: str) -> str:
    return html.unescape(TAG_RE.sub("", fragment)).replace("¶", "").strip()


def _clean_fragment(fragment: str) -> str:
    fragment = strip_visual_players(fragment)
    fragment = re.sub(
        r'<a[^>]+class="md-content__button md-icon".*?</a>', "", fragment, flags=re.S)
    fragment = re.sub(
        r'<a class="headerlink".*?</a>', "", fragment, flags=re.S)
    fragment = re.sub(
        r'<div class="legacy-anchor".*?</div>', "", fragment, flags=re.S)
    fragment = re.sub(
        r"<hr\s*/?>\s*<blockquote>\s*<p>✍️ <strong>参与共建.*$", "",
        fragment, flags=re.S)
    # The book keeps video links as plain text entries (no runtime iframe player).
    fragment = re.sub(r'\s+data-study-video(?:="[^"]*")?', "", fragment)
    # Collapsed answers and indexes must be readable on paper.
    fragment = re.sub(r"<details(?![^>]*\bopen\b)", "<details open", fragment)
    fragment = fragment.replace(' loading="lazy"', "")
    return fragment.strip()


def _drop_duplicate_name(match: re.Match) -> str:
    tag = match.group(0)
    name = re.search(r'(?<![\w-])name="([^"]+)"', tag)
    if name is None:
        return tag
    value = name.group(1)
    if re.search(r'(?<![\w-])id="%s"' % re.escape(value), tag):
        return tag[:name.start()] + tag[name.end():]
    return tag


def _namespace(fragment: str, stem: str) -> str:
    # Material emits id+name pairs for code-line anchors; keep one target per anchor.
    fragment = re.sub(r"<[^>]+>", _drop_duplicate_name, fragment)
    prefix = stem + "--"
    return ID_ATTR_RE.sub(
        lambda m: '%s="%s%s"' % (m.group(1), prefix, m.group(2)),
        fragment)


def extract_article(site_dir: Path, name: str) -> tuple[str, str]:
    path = site_dir / name.replace(".md", ".html")
    page = path.read_text(encoding="utf-8")
    match = ARTICLE_RE.search(page)
    if not match:
        raise BookError(
            f'{path.name}: 找不到 <article class="md-content__inner md-typeset">')
    fragment = _clean_fragment(match.group(1))
    h1 = H1_RE.search(fragment)
    if not h1:
        raise BookError(f"{path.name}: <article> 中缺少 <h1>")
    title = re.sub(r"\s+", " ", _strip_tags(h1.group(1))).strip()
    if not title:
        raise BookError(f"{path.name}: <h1> 标题为空")
    stem = Path(name).stem
    return title, _namespace(fragment, stem)


def manuscript(manifest: dict, site_dir: Path = SITE_DIR) -> list[dict]:
    parts = []
    groups = list(manifest["parts"]) + [
        {"id": "appendix", "files": manifest["appendix"]["files"]}]
    for part in groups:
        pages = []
        for name in part["files"]:
            title, fragment = extract_article(site_dir, name)
            pages.append({"stem": Path(name).stem, "title": title, "html": fragment})
        parts.append({
            "id": part["id"],
            "title": (manifest["appendix"]["title"]
                      if part["id"] == "appendix" else pages[0]["title"]),
            "pages": pages,
        })
    return parts


EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "data:")


def rewrite_links(fragment: str, current_stem: str, book_stems: set[str],
                  manifest: dict) -> str:
    site_url = manifest["site_url"].rstrip("/") + "/"

    def repl(match: re.Match) -> str:
        href = match.group(1)
        if not href or href == "#" or href.startswith(EXTERNAL_PREFIXES):
            return match.group(0)
        path, _, anchor = href.partition("#")
        if path.startswith("#"):
            return f'href="#{current_stem}--{path[1:]}"'
        name = path.rsplit("/", 1)[-1]
        if name.endswith(".html"):
            stem = name[:-5]
            if stem == "index":
                return 'href="#book-toc"'
            if stem in book_stems:
                target = f"page-{stem}" if not anchor else f"{stem}--{anchor}"
                return f'href="#{target}"'
        if path.startswith("assets/"):
            return f'href="{site_url}{href}"'
        if path.startswith("/"):
            return f'href="{site_url}{path.lstrip("/")}{("#" + anchor) if anchor else ""}"'
        return f'href="{site_url}{href}"'

    return re.sub(r'href="([^"]+)"', repl, fragment)


CSS_FILES = ["typography", "gallery", "learning", "reading", "diag"]
BOOK_SCRIPTS = ["calc", "learning", "learning-catalog", "diag"]

MIME = {
    ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp",
}


def _material_css(site_dir: Path) -> list[Path]:
    styles = site_dir / "assets" / "stylesheets"
    found = []
    for pattern in ("main.*.min.css", "palette.*.min.css"):
        matches = sorted(styles.glob(pattern))
        if not matches:
            raise BookError(f"站点缺少样式 {pattern}")
        found.append(matches[-1])
    return found


def inline_css(site_dir: Path = SITE_DIR) -> str:
    chunks = [p.read_text(encoding="utf-8") for p in _material_css(site_dir)]
    for name in CSS_FILES:
        path = site_dir / "stylesheets" / f"{name}.css"
        if not path.is_file():
            raise BookError(f"站点缺少样式 {path.name}")
        chunks.append(path.read_text(encoding="utf-8"))
    chunks.append((BOOK_DIR / "styles" / "book.css").read_text(encoding="utf-8"))
    return "\n".join(chunks)


def inline_scripts(site_dir: Path = SITE_DIR) -> str:
    chunks = []
    for name in BOOK_SCRIPTS:
        path = site_dir / "javascripts" / f"{name}.js"
        if not path.is_file():
            raise BookError(f"站点缺少脚本 {path.name}")
        chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def inline_static(name: str) -> str:
    path = BOOK_DIR / "static" / name
    if not path.is_file():
        raise BookError(f"缺少离线脚本: {path}")
    return path.read_text(encoding="utf-8")


MATHJAX_CONFIG = r"""<script>
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"], ["$", "$"]],
    displayMath: [["\\[", "\\]"], ["$$", "$$"]],
    processEscapes: true,
    processEnvironments: true
  },
  svg: { fontCache: "local" },
  options: { ignoreHtmlClass: ".*|", processHtmlClass: "arithmatex" }
};
</script>"""


def inline_mathjax() -> str:
    mathjax = ROOT / "assets" / "vendor" / "mathjax-svg" / "tex-svg-full.js"
    if not mathjax.is_file():
        raise BookError(f"缺少 MathJax SVG 包: {mathjax}")
    return (MATHJAX_CONFIG + "<script>"
            + mathjax.read_text(encoding="utf-8") + "</script>")


def _asset_path(rel: str, site_dir: Path = SITE_DIR) -> Path:
    if rel.startswith(("assets/figures-v2/", "assets/svg-v2/")):
        return visual_asset_path(rel, site_dir)
    # 静止版 `.reduce.svg` 只由站点构建生成，仓库里没有第二份。
    for base in (ROOT, site_dir):
        candidate = (base / rel).resolve()
        if candidate.is_file():
            return candidate
    raise BookError(f"图片不存在: {rel}")


JPEG_MAX_SIDE = 900


def _shrink_jpeg(raw: bytes) -> bytes:
    """书内照片按显示宽度降采样，长边 900 px 已足够屏幕与 A4 印刷。

    原图多为 713–960 px 宽的手机/扫描件，按原字节 base64 内联会把整书
    推过 20 MB 上限；只在压缩后更小时采用，不改变公式、电路与 SVG。
    """
    with Image.open(io.BytesIO(raw)) as image:
        scale = min(1.0, JPEG_MAX_SIDE / max(image.size))
        if scale < 1.0:
            size = (round(image.width * scale), round(image.height * scale))
            image = image.resize(size, Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.convert("RGB").save(output, "JPEG", quality=80, optimize=True, progressive=True)
    compressed = output.getvalue()
    return compressed if len(compressed) < len(raw) else raw


def _data_uri(path: Path) -> str:
    resolved = path.resolve()
    if not resolved.is_file():
        raise BookError(f"图片不存在: {path}")
    if not resolved.is_relative_to(ROOT):
        raise BookError(f"图片不在仓库内: {path}")
    mime = MIME.get(resolved.suffix.lower())
    if mime is None:
        raise BookError(f"不支持的图片类型: {path}")
    raw = resolved.read_bytes()
    if mime == "image/jpeg":
        raw = _shrink_jpeg(raw)
    return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")


def _use_reduced_motion_picture(fragment: str) -> str:
    """打印书只保留 `.reduce.svg` 静止版，避免同一动画内联两份 SVG。"""
    return re.sub(
        r'<picture><source srcset="(assets/[^"]+\.reduce\.svg)" '
        r'media="\(prefers-reduced-motion: reduce\)">'
        r'<img src="assets/[^"]+\.svg"([^>]*)></picture>',
        r'<img src="\1"\2>',
        fragment,
    )


def inline_images(fragment: str, site_dir: Path = SITE_DIR) -> tuple[str, int]:
    count = 0
    fragment = _use_reduced_motion_picture(fragment)

    def source(match: re.Match) -> str:
        nonlocal count
        count += 1
        return f'{match.group(1)}="{_data_uri(_asset_path(match.group(2), site_dir))}"'

    fragment = re.sub(r'(?<![\w-])(src)="(assets/[^"]+)"', source, fragment)
    fragment = re.sub(r'(?<![\w-])(srcset)="(assets/[^"]+)"', source, fragment)
    remote = re.search(r'(?<![\w-])(?:src|srcset)="(https?://[^"]+)"', fragment)
    if remote:
        raise BookError(f"书内仍有远程图片: {remote.group(1)}")
    return fragment, count


def replace_mermaid(fragment: str) -> str:
    snapshot = BOOK_DIR / "static" / "roadmap.svg"
    source_file = BOOK_DIR / "static" / "roadmap.source.txt"
    if not snapshot.is_file() or not source_file.is_file():
        raise BookError("缺少 static/roadmap.svg 或 static/roadmap.source.txt")
    if '<pre class="mermaid">' not in fragment:
        return fragment
    doc = (DOCS / "p0-06-roadmap.md").read_text(encoding="utf-8")
    source = re.search(r"```mermaid\n(.*?)```", doc, re.S).group(1).strip() + "\n"
    if source != source_file.read_text(encoding="utf-8"):
        raise BookError(
            "docs/p0-06-roadmap.md 与 static/roadmap.source.txt 不一致；请重新生成快照")
    svg = snapshot.read_text(encoding="utf-8").strip()
    return re.sub(r'<pre class="mermaid">.*?</pre>',
                  '<figure class="book-roadmap">' + svg + "</figure>",
                  fragment, flags=re.S)


def wrap_tables(fragment: str) -> str:
    return re.sub(r'<table(?:\s[^>]*)?>.*?</table>',
                  lambda m: f'<div class="table-wrap">{m.group(0)}</div>',
                  fragment, flags=re.S)


def _page_link(page: dict, direction: str) -> str:
    if direction == "prev":
        label, title = "← 上一篇", page["title"]
        kind = "prev"
    else:
        label, title = "下一篇 →", page["title"]
        kind = "next"
    return (
        f'<a class="book-page-nav-{kind}" href="#page-{page["stem"]}" rel="{kind}">'
        f'<span class="book-page-nav-label">{label}</span>'
        f'<span class="book-page-nav-title">{html.escape(title)}</span></a>'
    )


def _page_section(page: dict, part_title: str,
                  prev_page: dict | None = None,
                  next_page: dict | None = None) -> str:
    nav = ['<nav class="book-page-nav" aria-label="翻页">']
    nav.append(_page_link(prev_page, "prev") if prev_page
               else '<span class="book-page-nav-empty" aria-hidden="true"></span>')
    nav.append('<a class="book-page-nav-toc" href="#book-toc">全书目录</a>')
    nav.append(_page_link(next_page, "next") if next_page
               else '<span class="book-page-nav-empty" aria-hidden="true"></span>')
    nav.append("</nav>")
    return (
        f'<section class="book-page" id="page-{page["stem"]}" '
        f'data-page="{page["stem"]}" data-title="{html.escape(page["title"], quote=True)}" '
        f'data-part-title="{html.escape(part_title, quote=True)}">\n'
        f'<div class="md-typeset">\n{page["html"]}\n</div>\n'
        + "".join(nav) + "\n</section>"
    )


def _cover_art() -> str:
    path = BOOK_DIR / "static" / "cover-art.svg"
    if not path.is_file():
        raise BookError(f"缺少封面插图: {path}")
    return path.read_text(encoding="utf-8")


def _cover(manifest: dict) -> str:
    return (
        '<section class="book-cover" data-part="front">'
        f'<div class="book-cover-art" aria-hidden="true">{_cover_art()}</div>'
        f'<p class="book-cover-kicker">{html.escape(manifest["subtitle"])}</p>'
        f'<h1 class="book-cover-title">{html.escape(manifest["title"])}</h1>'
        '<p class="book-cover-rule" aria-hidden="true"></p>'
        f'<p class="book-cover-author">{html.escape(manifest["author"])}</p>'
        f'<p class="book-cover-version">版本 {manifest["version"]} · {manifest["date"]}</p>'
        f'<p class="book-cover-site">{html.escape(manifest["site_url"])}</p>'
        f'<p class="book-cover-repo">{html.escape(manifest["repository"])}</p>'
        '</section>'
    )


def _copyright(manifest: dict) -> str:
    return (
        '<section class="book-copyright" data-part="front">'
        '<h1>版权与来源</h1>'
        f'<p>《{html.escape(manifest["title"])}》{manifest["version"]}，'
        f'{manifest["date"]}。作者：{html.escape(manifest["author"])}。</p>'
        f'<p>正文、SVG 动画、实验包与网表采用 {manifest["license"]} 授权；'
        '第三方照片、软件与字体的完整清单见书末「来源与许可」。</p>'
        f'<p>在线地址：{html.escape(manifest["site_url"])}<br>'
        f'仓库：{html.escape(manifest["repository"])}</p>'
        '<p>本书为离线阅读副本，内容与在线站同源；器件参数与安全操作请以厂商数据手册和实际条件为准。</p>'
        '</section>'
    )


def _toc(parts: list[dict]) -> str:
    rows = ['<section class="book-toc" id="book-toc" data-part="toc">',
            '<h1>全书目录</h1>']
    for part in parts:
        rows.append(f'<div class="book-toc-part"><h2>{html.escape(part["title"])}</h2><ul>')
        for index, page in enumerate(part["pages"]):
            label = (PREFACE_LABEL
                     if index == 0 and page["title"] == part["title"] else page["title"])
            rows.append(
                f'<li><a href="#page-{page["stem"]}">{html.escape(label)}</a></li>')
        rows.append("</ul></div>")
    rows.append("</section>")
    return "\n".join(rows)


def _svg_size(data_uri: str) -> tuple[float, float] | None:
    if not data_uri.startswith("data:image/svg+xml;base64,"):
        return None
    try:
        raw = base64.b64decode(data_uri.split(",", 1)[1]).decode("utf-8-sig")
    except (ValueError, UnicodeDecodeError):
        return None
    root = raw[:4000].split(">", 1)[0]
    width = re.search(r'\bwidth="([\d.]+)', root)
    height = re.search(r'\bheight="([\d.]+)', root)
    if width and height:
        return float(width.group(1)), float(height.group(1))
    box = re.search(r'\bviewBox="[\d.+-]+\s+[\d.+-]+\s+([\d.]+)\s+([\d.]+)"', root)
    if box:
        return float(box.group(1)), float(box.group(2))
    return None


def _shared_image(match: re.Match, css: list[str], classes: dict[str, int]) -> str:
    tag = match.group(0)
    attrs = dict(re.findall(r'([\w:-]+)="([^"]*)"', tag))
    source = attrs.get("src", "")
    if not source.startswith("data:"):
        return tag
    width = attrs.get("width")
    height = attrs.get("height")
    if width and not height:
        size = _svg_size(source)
        if size:
            height = f"{float(width) * size[1] / size[0]:.3f}".rstrip("0").rstrip(".")
    if not (width and height):
        return tag
    number = classes.get(source)
    if number is None:
        number = len(classes) + 1
        classes[source] = number
        css.append(f'.book-data-{number}{{background-image:url("{source}")}}')
    alt = html.escape(attrs.get("alt", ""), quote=True)
    names = attrs.get("class", "").split()
    names = ["book-shared-image", f"book-data-{number}", *names]
    ratio = f"{float(width):g}/{float(height):g}"
    return (f'<span class="{" ".join(names)}" role="img" '
            f'aria-label="{alt}" style="width:{float(width):g}px;'
            f'aspect-ratio:{ratio}"></span>')


def dedupe_images(parts: list[dict]) -> str:
    """同一 data URI 只保留一份：重复出现的图改为共享 CSS 背景。

    p5 篇导读画廊会把章内海报再内嵌一遍；base64 后可达数 MB。
    保留一个 CSS 规则、多次 ``<span>`` 引用，视觉与打印结果不变。
    """
    pages = [page for part in parts for page in part["pages"]]
    counts: dict[str, int] = {}
    for page in pages:
        for match in re.finditer(r'<img\b[^>]*>', page["html"]):
            src = re.search(r'\bsrc="(data:[^"]+)"', match.group(0))
            if src:
                counts[src.group(1)] = counts.get(src.group(1), 0) + 1
    shared = {uri for uri, count in counts.items() if count > 1}
    if not shared:
        return ""
    css: list[str] = []
    classes: dict[str, int] = {}

    def rewrite(match: re.Match) -> str:
        src = re.search(r'\bsrc="(data:[^"]+)"', match.group(0))
        if not src or src.group(1) not in shared:
            return match.group(0)
        return _shared_image(match, css, classes)

    for page in pages:
        page["html"] = re.sub(r'<img\b[^>]*>', rewrite, page["html"])
    if not css:
        return ""
    base = (".book-shared-image{display:block;margin:1em auto;height:auto;"
            "background-position:center;background-repeat:no-repeat;"
            "background-size:contain;max-width:100%}"
            ".gal-card .book-shared-image{width:100%!important;margin:0;"
            "background-color:#fff}")
    return base + "".join(css)


def assemble_book(manifest: dict, parts: list[dict],
                  site_dir: Path = SITE_DIR) -> str:
    render_parts = [
        {"id": part["id"], "title": part["title"],
         "pages": [dict(page) for page in part["pages"]]}
        for part in parts
    ]
    shared_css = dedupe_images(render_parts)
    body = [_cover(manifest), _copyright(manifest), _toc(render_parts)]
    ordered = [page for part in render_parts for page in part["pages"]]
    index = 0
    for part in render_parts:
        body.append(f'<section class="book-part" data-part="{part["id"]}">')
        for page in part["pages"]:
            prev_page = ordered[index - 1] if index > 0 else None
            next_page = ordered[index + 1] if index + 1 < len(ordered) else None
            body.append(_page_section(page, part["title"], prev_page, next_page))
            index += 1
        body.append("</section>")
    css = inline_css(site_dir)
    scripts = inline_scripts(site_dir)
    search = inline_static("book-search.js")
    ui = inline_static("book-ui.js")
    mathjax = inline_mathjax()
    document = f"""<!doctype html>
<html lang="{manifest["language"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>{html.escape(manifest["title"])}</title>
<meta name="book-manifest-sha256" content="{manifest_sha256()}">
<meta name="book-version" content="{manifest["version"]}">
<meta name="book-date" content="{manifest["date"]}">
<meta name="book-author" content="{html.escape(manifest["author"], quote=True)}">
<style>{css}{shared_css}</style>
</head>
<body data-md-color-scheme="default" data-md-color-primary="indigo" data-md-color-accent="indigo">
<a class="book-skip" href="#book-toc">跳到目录</a>
<div class="book-progress" id="book-progress" aria-hidden="true"></div>
<header class="book-header"><span class="book-header-title">{html.escape(manifest["title"])}</span>
<div class="book-search" id="book-search" role="search">
<label class="visually-hidden" for="book-search-input">搜索全书</label>
<input id="book-search-input" type="search" placeholder="搜索全书（Ctrl+K）" autocomplete="off" spellcheck="false" role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="book-search-results">
<div class="book-search-panel" id="book-search-panel" hidden>
<p class="book-search-status" id="book-search-status" role="status" aria-live="polite"></p>
<ul class="book-search-results" id="book-search-results" role="listbox"></ul>
</div>
</div>
<a class="book-header-toc" href="#book-toc">目录</a></header>
<main class="book">
{''.join(body)}
</main>
<footer class="book-footer">离线整书 · 由 docs/ 构建 · {manifest["license"]}</footer>
<button class="book-top" id="book-top" type="button" aria-label="回到顶部" hidden>↑</button>
{mathjax}
<script>{scripts}</script>
<script>{search}</script>
<script>{ui}</script>
</body>
</html>
"""
    return document


def audit_html(document: str, manifest: dict, parts: list[dict]) -> dict:
    pages = [page for part in parts for page in part["pages"]]
    # 内联的 MathJax/站点脚本里含有 id="..." 字面量，审计只看真正的标记。
    markup = EMBEDDED_BLOCK_RE.sub("", document)
    ids = re.findall(r'(?<![\w-])(?:id|name)="([^"]+)"', markup)
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    problems = []
    if duplicates:
        problems.append("重复 ID: " + ", ".join(duplicates[:10]))
    hrefs = re.findall(r'href="#([^"]+)"', markup)
    missing = sorted({h for h in hrefs if h not in set(ids)})
    if missing:
        problems.append("悬空锚点: " + ", ".join(missing[:10]))
    if '<script src=' in document:
        problems.append("含外部脚本")
    if 'rel="stylesheet"' in document:
        problems.append("含外部样式")
    if "<iframe" in document or "<video" in document:
        problems.append("含 iframe/video")
    remote = re.findall(r'<img[^>]+src="https?://[^"]+"', markup)
    if remote:
        problems.append("含远程图片: " + remote[0][:80])
    if document.count('class="book-page"') != len(pages):
        problems.append("页面数量与清单不一致")
    if len(document.encode("utf-8")) >= MAX_HTML_BYTES:
        problems.append(f"HTML 超过上限 {MAX_HTML_BYTES // 1024 // 1024} MB")
    images = markup.count("<img ")
    formulas = markup.count('class="arithmatex"')
    report = {"pages": len(pages), "images": images, "formulas": formulas,
              "bytes": len(document.encode("utf-8")),
              "max_asset": max((len(m) for m in re.findall(
                  r'data:[^"]+', markup)), default=0)}
    if problems:
        raise BookError("整书审计失败:\n" + "\n".join(problems))
    return report


def _prepare_pages(parts: list[dict], site_dir: Path = SITE_DIR) -> None:
    stems = {page["stem"] for part in parts for page in part["pages"]}
    manifest = load_manifest()
    for part in parts:
        for page in part["pages"]:
            page["html"] = replace_mermaid(page["html"])
            page["html"] = rewrite_links(page["html"], page["stem"], stems, manifest)
            page["html"], _ = inline_images(page["html"], site_dir)
            page["html"] = wrap_tables(page["html"])


def build_html(out_dir: Path, site_dir: Path = SITE_DIR,
               rebuild_site: bool = True) -> Path:
    manifest = load_manifest()
    if rebuild_site:
        build_site(site_dir)
    validate_manifest(manifest, site_dir)
    parts = manuscript(manifest, site_dir)
    _prepare_pages(parts, site_dir)
    document = assemble_book(manifest, parts, site_dir)
    report = audit_html(document, manifest, parts)
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / OUTPUT_NAME
    output.write_text(document, encoding="utf-8", newline="\n")
    print(f"html  {output} ({report['bytes']} bytes, {report['pages']} pages, "
          f"{report['images']} images, {report['formulas']} formulas, "
          f"max asset {report['max_asset']} bytes)")
    return output


def check_html(out_dir: Path = DIST_DIR, site_dir: Path = SITE_DIR) -> int:
    output = out_dir / OUTPUT_NAME
    if not output.is_file():
        raise BookError(f"整书产物不存在: {output}")
    document = output.read_text(encoding="utf-8")
    manifest = load_manifest()
    match = re.search(r'name="book-manifest-sha256" content="([0-9a-f]+)"', document)
    if not match or match.group(1) != manifest_sha256():
        raise BookError("整书产物与 manifest 不同步，请重新构建")
    validate_manifest(manifest, site_dir)
    parts = manuscript(manifest, site_dir)
    report = audit_html(document, manifest, parts)
    print(f"check {output} OK ({report['pages']} pages, {report['bytes']} bytes)")
    return 0


def _browser_candidates(override: str | None) -> list[Path]:
    candidates = [Path(override)] if override else []
    for command in ("msedge", "chrome", "chromium"):
        found = shutil.which(command)
        if found:
            candidates.append(Path(found))
    for raw in (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ):
        candidates.append(Path(raw))
    result, seen = [], set()
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved not in seen and resolved.is_file():
            result.append(resolved)
            seen.add(resolved)
    return result


def build_pdf(html_path: Path, browser_override: str | None = None) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise BookError(
            "PDF 需要 Playwright：pip install -r analog-book/requirements.txt") from exc
    browsers = _browser_candidates(browser_override)
    executable = browsers[0] if browsers else None
    if browser_override and executable is None:
        raise BookError(f"浏览器不存在: {browser_override}")
    output = html_path.with_name(PDF_NAME)
    raw_pdf = html_path.with_name(".analog-book.raw.pdf")
    manifest = load_manifest()
    try:
        with sync_playwright() as playwright:
            launch = {"headless": True}
            if executable:
                launch["executable_path"] = str(executable)
            browser = playwright.chromium.launch(**launch)
            try:
                context = browser.new_context(reduced_motion="reduce")
                page = context.new_page()
                page.set_default_timeout(300000)
                page.goto(html_path.resolve().as_uri(), wait_until="load")
                page.evaluate(
                    "async () => { if (document.fonts) await document.fonts.ready; }")
                page.wait_for_function(
                    "window.MathJax && MathJax.startup && MathJax.startup.promise",
                    timeout=60000)
                page.wait_for_function(
                    "document.querySelectorAll('mjx-container').length > 1000",
                    timeout=120000)
                page.wait_for_function(
                    "Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)",
                    timeout=30000)
                page.pdf(path=str(raw_pdf), print_background=True,
                         prefer_css_page_size=True, outline=True, tagged=True)
            finally:
                browser.close()
        _stamp_pdf(raw_pdf, output, manifest)
    except BookError:
        raise
    except Exception as exc:
        raise BookError(f"PDF 构建失败: {exc}") from exc
    finally:
        raw_pdf.unlink(missing_ok=True)
    print(f"pdf   {output} ({output.stat().st_size} bytes)")
    return output


def _pdf_page_titles(html_text: str) -> list[tuple[str, str]]:
    return re.findall(
        r'<section class="book-page" id="page-[^"]+" data-page="([^"]+)" data-title="([^"]+)"',
        html_text)


EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2300-\u23FF\u2600-\u27BF\u2B00-\u2BFF"
    "\uFE0F\u200D]+")


def _header_text(title: str) -> str:
    # PyMuPDF 的内置 CJK 字体无法编码 emoji，混入后会把整行写成乱码。
    return re.sub(r"\s+", " ", EMOJI_RE.sub("", title)).strip()


def _parts_with_titles(page_titles, starts):
    manifest = load_manifest()
    sizes = [len(part["files"]) for part in manifest["parts"]]
    sizes.append(len(manifest["appendix"]["files"]))
    titles = [title for _, title in page_titles]
    offset, parts = 0, []
    for number, size in enumerate(sizes):
        part_pages = page_titles[offset:offset + size]
        title = (manifest["appendix"]["title"] if number == len(sizes) - 1
                 else titles[offset])
        parts.append({"title": title, "first": offset, "pages": part_pages})
        offset += size
    return parts


def _stamp_pdf(raw_pdf: Path, output_pdf: Path, manifest: dict) -> None:
    try:
        import fitz
    except ImportError as exc:
        raise BookError(
            "PDF 需要 PyMuPDF：pip install -r analog-book/requirements.txt") from exc
    document = fitz.open(raw_pdf)
    try:
        document.set_metadata({
            "title": manifest["title"],
            "author": manifest["author"],
            "subject": manifest["subtitle"],
            "keywords": "模拟电路, STM32, 电子, 离线书, " + manifest["license"],
            "creator": "analog-circuit-roadmap/build_book.py",
        })
        # 目录页：从「全书目录」出现到首个无内部链接的页。
        toc_pages, in_toc = [], False
        for index, page in enumerate(document):
            if "全书目录" in page.get_text():
                in_toc = True
            if not in_toc:
                continue
            links = [link for link in page.get_links()
                     if isinstance(link.get("page"), int)]
            if not links:
                break
            toc_pages.append(index)
        if not toc_pages:
            raise BookError("PDF 中找不到目录页")
        body_start = min(
            link["page"] for index in toc_pages
            for link in document[index].get_links()
            if isinstance(link.get("page"), int) and link["page"] > max(toc_pages))
        # 目录页码（link 目标为 0 基页索引，打印页码从 1 开始）。
        for index in toc_pages:
            page = document[index]
            for link in page.get_links():
                target = link.get("page", -1)
                if target < body_start:
                    continue
                rect = fitz.Rect(link["from"])
                label = str(target - body_start + 1)
                width = fitz.get_text_length(label, fontname="helv", fontsize=8)
                number_x = page.rect.width - 46 - width
                if rect.x1 + 12 < number_x:
                    page.draw_line(
                        fitz.Point(rect.x1 + 5, rect.y1 - 4),
                        fitz.Point(number_x - 5, rect.y1 - 4),
                        color=(0.78, 0.80, 0.82), width=0.5,
                        dashes="[0.7 2.2] 0")
                page.insert_text(
                    fitz.Point(number_x, rect.y1 - 2),
                    label, fontname="helv", fontsize=8, color=(0.38, 0.42, 0.45))
        html_path = output_pdf.with_name(OUTPUT_NAME)
        html_text = html_path.read_text(encoding="utf-8")
        page_titles = [(stem, html.unescape(title)) for stem, title
                       in _pdf_page_titles(html_text)]
        # Chrome 只把页面 h1 收进一级大纲；正文前的封面/版权/目录已被过滤。
        outline = [entry for entry in document.get_toc()
                   if entry[0] == 1 and entry[2] > body_start]
        if len(outline) != len(page_titles):
            raise BookError(
                f"PDF 大纲 {len(outline)} 个一级标题，HTML 页面 {len(page_titles)} 个；无法定位页眉")
        starts = [entry[2] - 1 for entry in outline]
        if starts[0] != body_start or starts != sorted(starts):
            raise BookError("PDF 大纲与正文页顺序不一致")
        # 书签：篇 = 一级，页 = 二级；set_toc 的页码是 1 基物理页。
        toc = []
        for part in _parts_with_titles(page_titles, starts):
            toc.append([1, part["title"], starts[part["first"]] + 1])
            for offset, (_stem, title) in enumerate(part["pages"]):
                label = (PREFACE_LABEL if offset == 0 and title == part["title"]
                         else title)
                toc.append([2, label, starts[part["first"] + offset] + 1])
        document.set_toc(toc)
        document.set_page_labels([
            {"startpage": 0, "prefix": "", "style": "r", "firstpagenum": 1},
            {"startpage": body_start, "prefix": "", "style": "D", "firstpagenum": 1},
        ])
        # 页眉与页脚：正文从 1 开始。
        short_title = manifest["title"]
        total = max(1, document.page_count - body_start)
        section_starts = {index: _header_text(title) for (_stem, title), index
                          in zip(page_titles, starts)}
        for index in range(document.page_count):
            if index < body_start:
                continue
            page = document[index]
            printed = index - body_start + 1
            label = f"{printed} / {total}"
            width = fitz.get_text_length(label, fontname="helv", fontsize=8)
            page.insert_text(
                fitz.Point((page.rect.width - width) / 2, page.rect.height - 10),
                label, fontname="helv", fontsize=8, color=(0.38, 0.42, 0.45))
            header = short_title if printed % 2 == 1 else section_starts.get(index, "")
            if not header:
                continue
            hwidth = fitz.get_text_length(header, fontname="china-s", fontsize=7.5)
            x = 46 if printed % 2 == 1 else page.rect.width - 46 - hwidth
            page.insert_text(fitz.Point(x, 22), header, fontname="china-s",
                             fontsize=7.5, color=(0.38, 0.42, 0.45))
            page.draw_line(fitz.Point(46, 28), fitz.Point(page.rect.width - 46, 28),
                           color=(0.72, 0.74, 0.76), width=0.35)
        document.save(output_pdf, garbage=3, deflate=True)
    finally:
        document.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DIST_DIR)
    parser.add_argument("--site-dir", type=Path, default=SITE_DIR)
    parser.add_argument("--no-build", action="store_true", help="复用已有站点产物")
    parser.add_argument("--check", action="store_true", help="只审计已有整书")
    parser.add_argument("--pdf", action="store_true")
    parser.add_argument("--browser")
    args = parser.parse_args(argv)
    try:
        if args.check:
            return check_html(args.out_dir, args.site_dir)
        html_path = build_html(args.out_dir, args.site_dir, not args.no_build)
        if args.pdf:
            build_pdf(html_path, args.browser)
        return 0
    except BookError as exc:
        print(f"book build error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
