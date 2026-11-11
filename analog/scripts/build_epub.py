#!/usr/bin/env python3
"""EPUB3 本地产物：复用整书装配链，图片落文件、公式预渲染为 SVG。

与 A4 PDF 同源（analog-book 的 manifest + 站点产物），差异有三：

1. 图片不内联 data URI——阅读器对 data URI 支持参差，资产全部落
   `OEBPS/`，V2 图按 manifest 取印刷回退（纸面皮肤静态图，未过审图会
   与 PDF 一样被 `visual_asset_path` 拦下）；
2. 公式在 Playwright + MathJax（fontCache=local，每个 SVG 自包含）里
   预排版，落 `OEBPS/math/`，阅读器无需执行 JS；
3. XHTML 严格序列化（bs4 xml formatter），void 元素自闭合，构建后过
   lxml 良构校验与内部链接完备性检查。

用法：`python scripts/build_epub.py`（默认复用 build/site；`--rebuild-site` 先重建）。
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
import uuid
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "analog-book"
sys.path.insert(0, str(BOOK_DIR))

import build_book as bb  # noqa: E402

SITE = ROOT / "build" / "site"
DIST = BOOK_DIR / "dist"
OUTPUT = "analog-circuit-book.epub"
UID = 'urn:uuid:' + str(uuid.uuid5(uuid.NAMESPACE_URL,
    'https://github.com/zhuguang-ZFG/analog-circuit-roadmap/book'))
MIME_TEXT = {".svg": "image/svg+xml", ".png": "image/png", ".gif": "image/gif",
             ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
             ".woff2": "font/woff2", ".txt": "text/plain"}

TYPESET_JS = """
async (html) => {
  document.body.innerHTML = html;
  document.querySelectorAll('.arithmatex').forEach(
      el => el.setAttribute('data-tex', el.textContent.trim()));
  await MathJax.typesetPromise([document.body]);
  const svgs = [];
  document.querySelectorAll('.arithmatex').forEach(el => {
    const tex = el.getAttribute('data-tex') || '';
    const c = el.querySelector('mjx-container');
    const svg = c && c.querySelector('svg');
    if (!svg) { el.textContent = tex; return; }
    const display = c.getAttribute('display') === 'true';
    svgs.push(svg.outerHTML);
    const img = document.createElement('img');
    img.setAttribute('class', display ? 'math math-display' : 'math');
    img.setAttribute('src', '@@MATH' + (svgs.length - 1) + '@@');
    img.setAttribute('alt', tex);
    img.setAttribute('style', 'width:' + (svg.getAttribute('width') || 'auto')
        + ';height:' + (svg.getAttribute('height') || 'auto') + ';');
    (display ? el : c).replaceWith(img);
  });
  return {html: document.body.innerHTML, svgs};
}
"""

CSS = """@font-face{font-family:"Noto Serif SC";font-weight:400;
src:url("../fonts/NotoSerifSC-Regular.woff2") format("woff2");}
@font-face{font-family:"Noto Serif SC";font-weight:700;
src:url("../fonts/NotoSerifSC-Bold.woff2") format("woff2");}
@font-face{font-family:"JetBrains Mono";font-weight:400;
src:url("../fonts/JetBrainsMono-Regular.woff2") format("woff2");}
body{font-family:"Noto Serif SC",serif;color:#16202b;
background:#fdf8ea;line-height:1.75;margin:0 1.2em;}
h1,h2,h3,h4{color:#16202b;line-height:1.35;margin:1.4em 0 .6em;}
h1{font-size:1.5em;border-bottom:2px solid #a4630f;padding-bottom:.3em;}
h2{font-size:1.25em;}h3{font-size:1.1em;}
a{color:#1f5d7a;text-decoration:none;}
img{max-width:100%;height:auto;}
img.math{vertical-align:-0.45em;}
img.math-display{display:block;margin:.8em auto;}
.math-fallback{font-family:"JetBrains Mono",monospace;font-size:.85em;color:#a8321f;}
figure{margin:1.2em 0;text-align:center;}
figcaption{font-size:.85em;color:#37424e;margin-top:.4em;text-align:center;}
pre{font-family:"JetBrains Mono",monospace;font-size:.8em;
background:#f6eedb;border:1px solid #e0d3b8;border-radius:6px;
padding:.7em;white-space:pre-wrap;word-break:break-word;overflow-wrap:break-word;}
code{font-family:"JetBrains Mono",monospace;font-size:.9em;
background:#f6eedb;border-radius:4px;padding:0 .25em;}
pre code{background:none;padding:0;border:none;}
table{border-collapse:collapse;width:100%;font-size:.8em;margin:1em 0;}
th,td{border:1px solid #c9bb9d;padding:.4em .55em;text-align:left;vertical-align:top;}
th{background:#f6eedb;}
blockquote{margin:1em 0;padding:.4em 1em;border-left:4px solid #a4630f;
background:#f6eedb;color:#37424e;}
details{margin:1em 0;border:1px solid #e0d3b8;border-radius:8px;padding:.6em;}
summary{font-weight:700;color:#1f5d7a;cursor:pointer;}
hr{border:none;border-top:2px solid #e0d3b8;margin:1.6em 0;}
ul,ol{padding-left:1.6em;}
nav ol{list-style:none;padding-left:0;}
nav li{margin:.35em 0;}
"""


def flatten_pages(parts: list[dict]) -> list[dict]:
    pages = [page for part in parts for page in part["pages"]]
    files: dict[str, str] = {}
    for index, page in enumerate(pages):
        files[page["stem"]] = f"{index:03d}-{page['stem']}.xhtml"
    for page in pages:
        page["file"] = files[page["stem"]]
    return pages


def rewrite_book_links(fragment: str, files: dict[str, str]) -> str:
    """整书内锚点 `#page-{stem}` / `#{stem}--{anchor}` 改为跨文件链接。"""
    def repl(match: re.Match) -> str:
        target = match.group(1)
        href = '#' + target
        if target == "book-toc":
            return 'href="../nav.xhtml#toc"'
        if target.startswith("page-"):
            stem = target[5:]
            return f'href="{files[stem]}"' if stem in files else match.group(0)
        stem = target.split("--", 1)[0]
        if stem in files:
            return f'href="{files[stem]}{href}"'
        return match.group(0)

    return re.sub(r'href="#(?!#)([^"]+)"', repl, fragment)


def fileize_images(fragment: str, site_dir: Path,
                   assets: dict[str, bytes]) -> str:
    fragment = bb._use_reduced_motion_picture(fragment)

    def source(match: re.Match) -> str:
        rel = match.group(2)
        path = bb._asset_path(rel, site_dir)
        # V2 图会被换成印刷回退（后缀可能不同），落包名必须跟真实文件一致，
        # 否则 .webp 的 media-type 里装着 SVG 字节。
        try:
            rel = str(path.relative_to(ROOT.resolve())).replace("\\", "/")
        except ValueError:
            rel = f"{Path(match.group(2)).parent}/{path.name}"
        assets[rel] = path.read_bytes()
        return f'{match.group(1)}="../{rel}"'

    fragment = re.sub(r'(?<![\w-])(src)="(assets/[^"]+)"', source, fragment)
    fragment = re.sub(r'(?<![\w-])(srcset)="(assets/[^"]+)"', source, fragment)
    remote = re.search(r'(?<![\w-])(?:src|srcset)="(https?://[^"]+)"', fragment)
    if remote:
        raise bb.BookError(f"EPUB 内仍有远程图片: {remote.group(1)}")
    return fragment


def inline_mermaid_as_file(fragment: str, assets: dict[str, bytes]) -> str:
    """走 bb.replace_mermaid 的源码一致性校验，但把内联 SVG 落成文件。"""
    replaced = bb.replace_mermaid(fragment)
    if replaced == fragment:
        return fragment
    blob = (BOOK_DIR / "static" / "roadmap.svg").read_bytes()
    assets["static/roadmap.svg"] = blob
    return re.sub(r'<figure class="book-roadmap">.*?</figure>',
                  '<figure class="book-roadmap"><img src="../static/roadmap.svg"'
                  ' alt="模拟电路学习路线图"/></figure>',
                  replaced, flags=re.S)


def typeset(pages: list[dict], assets: dict[str, bytes]) -> dict[str, int]:
    from playwright.sync_api import sync_playwright

    mathjax = ROOT / "assets" / "vendor" / "mathjax-svg" / "tex-svg-full.js"
    if not mathjax.is_file():
        raise bb.BookError(f"缺少 MathJax SVG 包: {mathjax}")
    config = re.search(r"<script>(.*?)</script>", bb.MATHJAX_CONFIG, re.S).group(1)
    shell = ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
             "<script>" + config + "</script></head><body></body></html>")
    stats = {"formulas": 0, "unique": 0}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.set_default_timeout(600000)
            page.set_content(shell)
            page.add_script_tag(path=str(mathjax))
            page.evaluate("() => MathJax.startup.promise")
            for item in pages:
                result = page.evaluate(TYPESET_JS, item["html"])
                html = result["html"]
                for i, svg in enumerate(result["svgs"]):
                    digest = hashlib.sha256(svg.encode("utf-8")).hexdigest()[:20]
                    name = f"math/{digest}.svg"
                    if name not in assets:
                        assets[name] = svg.encode("utf-8")
                        stats["unique"] += 1
                    html = html.replace(f"@@MATH{i}@@", f"../{name}", 1)
                    stats["formulas"] += 1
                if "@@MATH" in html:
                    raise bb.BookError(f"{item['stem']}: 公式占位符未替换干净")
                item["html"] = html
        finally:
            browser.close()
    return stats


def xhtml(title: str, body: str, head_extra: str = "") -> str:
    """lxml 以 HTML 规则解析、以 XML 规则序列化：void 元素自动自闭合。"""
    import lxml.etree as LET
    import lxml.html as LH

    fragment = LH.fragment_fromstring(body, create_parent="div")
    inner = LET.tostring(fragment, method="xml", encoding="unicode").strip()
    if inner == "<div/>":
        inner = ""
    elif inner.startswith("<div>") and inner.endswith("</div>"):
        inner = inner[5:-6]
    else:
        raise bb.BookError(f"序列化包装异常: {inner[:80]}")
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE html>\n'
            '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN" lang="zh-CN">\n'
            f'<head><meta charset="utf-8"/><title>{escape(title)}</title>'
            '<link rel="stylesheet" type="text/css" href="../css/book.css"/>'
            f'{head_extra}</head>\n<body>\n{inner}\n</body>\n</html>\n')


def nav_doc(parts: list[dict]) -> str:
    rows = []
    for part in parts:
        rows.append(f'<li><span class="part">{escape(part["title"])}</span><ol>')
        rows.extend(f'<li><a href="text/{page["file"]}">{escape(page["title"])}</a></li>'
                    for page in part["pages"])
        rows.append("</ol></li>")
    return ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
            '<html xmlns="http://www.w3.org/1999/xhtml" '
            'xmlns:epub="http://www.idpf.org/2007/epub" xml:lang="zh-CN">\n'
            '<head><meta charset="utf-8"/><title>目录</title>'
            '<link rel="stylesheet" type="text/css" href="css/book.css"/></head>\n'
            '<body><nav epub:type="toc" id="toc"><h1>全书目录</h1>'
            '<ol>' + "".join(rows) + '</ol></nav></body></html>\n')


def mime_for(rel: str) -> str:
    mime = MIME_TEXT.get(Path(rel).suffix.lower())
    if mime is None:
        raise bb.BookError(f"EPUB 不支持的资产类型: {rel}")
    return mime


def opf(meta: dict, pages: list[dict], assets: dict[str, bytes]) -> str:
    text_items = [(f"page-{i}", f"text/{p['file']}", p["title"])
                  for i, p in enumerate(pages)]
    lines = []
    spine = []

    def item(iid: str, href: str, mime: str, props: str | None = None) -> None:
        attr = f' properties="{props}"' if props else ""
        lines.append(f'    <item id="{iid}" href="{href}" media-type="{mime}"{attr}/>')

    item("nav", "nav.xhtml", "application/xhtml+xml", "nav")
    spine.append("nav")
    item("ncx", "toc.ncx", "application/x-dtbncx+xml")
    item("css", "css/book.css", "text/css")
    item("cover", "images/cover.png", "image/png", "cover-image")
    for iid, href, _title in text_items:
        item(iid, href, "application/xhtml+xml")
        spine.append(iid)
    for n, rel in enumerate(sorted(assets)):
        item(f"asset-{n}", rel, mime_for(rel))
    manifest_body = "\n".join(lines)
    spine_body = "\n".join(f'    <itemref idref="{i}"/>' for i in spine)
    return f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="{meta['language']}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">{UID}</dc:identifier>
    <dc:title id="main-title">{escape(meta['title'])}</dc:title>
    <meta refines="#main-title" property="title-type">main</meta>
    <dc:title id="subtitle">{escape(meta['subtitle'])}</dc:title>
    <meta refines="#subtitle" property="title-type">subtitle</meta>
    <dc:language>{meta['language']}</dc:language>
    <dc:creator>{escape(meta['author'])}</dc:creator>
    <dc:date>{meta['date']}</dc:date>
    <dc:rights>{escape(meta['license'])}</dc:rights>
    <meta property="dcterms:modified">{meta['date']}T00:00:00Z</meta>
    <link rel="canonical" href="{escape(meta['site_url'])}"/>
  </metadata>
  <manifest>
{manifest_body}
  </manifest>
  <spine toc="ncx">
{spine_body}
  </spine>
</package>
'''


def ncx(meta: dict, pages: list[dict]) -> str:
    points = [f'    <navPoint id="nav" playOrder="1">'
              f'<navLabel><text>全书目录</text></navLabel>'
              f'<content src="nav.xhtml"/></navPoint>']
    for order, page in enumerate(pages, start=2):
        points.append(f'    <navPoint id="p{order}" playOrder="{order}">'
                      f'<navLabel><text>{escape(page["title"])}</text></navLabel>'
                      f'<content src="text/{page["file"]}"/></navPoint>')
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
            f'  <head><meta name="dtb:uid" content="{UID}"/></head>\n'
            f'  <docTitle><text>{escape(meta["title"])}</text></docTitle>\n'
            '  <navMap>\n' + "\n".join(points) + "\n  </navMap>\n</ncx>\n")


def render_cover() -> bytes:
    from playwright.sync_api import sync_playwright

    html = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
html,body{margin:0;width:1080px;height:1440px;}
body{background:linear-gradient(180deg,#fdf8ea,#f6eedb);color:#16202b;
font-family:"Noto Serif SC","Microsoft YaHei",serif;display:flex;
flex-direction:column;justify-content:center;padding:0 110px;box-sizing:border-box;}
.rule{height:6px;background:#a4630f;border-radius:3px;width:220px;margin:34px 0;}
h1{font-size:88px;line-height:1.3;margin:0;}
.sub{font-size:34px;color:#37424e;margin-top:26px;line-height:1.7;}
.tag{font-size:26px;color:#8b8272;margin-top:64px;}
</style></head><body>
<div class="rule"></div>
<h1>通往模拟电路<br/>之路</h1>
<div class="sub">从欧姆定律到芯片内部结构</div>
<div class="tag">视觉优先彻底改造稿 · 2026-11</div>
</body></html>"""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1080, "height": 1440})
            page.set_content(html)
            page.evaluate("() => document.fonts.ready")
            return page.screenshot(type="png")
        finally:
            browser.close()


def package(out_path: Path, meta: dict, parts: list[dict], pages: list[dict],
            assets: dict[str, bytes], cover: bytes) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip",
                    compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml",
                    '<?xml version="1.0"?>\n'
                    '<container version="1.0" '
                    'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                    '<rootfiles><rootfile full-path="OEBPS/content.opf" '
                    'media-type="application/oebps-package+xml"/></rootfiles>'
                    "</container>\n")
        zf.writestr("OEBPS/content.opf", opf(meta, pages, assets))
        zf.writestr("OEBPS/toc.ncx", ncx(meta, pages))
        zf.writestr("OEBPS/css/book.css", CSS)
        zf.writestr("OEBPS/nav.xhtml", nav_doc(parts))
        zf.writestr("OEBPS/images/cover.png", cover)
        for page in pages:
            zf.writestr(f"OEBPS/text/{page['file']}",
                        xhtml(page["title"], page["html"]))
        for rel, blob in assets.items():
            zf.writestr(f"OEBPS/{rel}", blob)


def validate(out_path: Path) -> None:
    from epub_validation import EpubError, validate_epub

    try:
        report = validate_epub(out_path)
    except EpubError as exc:
        raise bb.BookError(str(exc)) from exc
    print(f'epub audit {report}')


def posix_normalize(path: str) -> str:
    parts: list[str] = []
    for seg in path.split("/"):
        if seg == "..":
            parts.pop()
        elif seg not in (".", ""):
            parts.append(seg)
    return "/".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rebuild-site", action="store_true",
                    help="先跑 mkdocs 重建 build/site")
    ap.add_argument("--out", type=Path, default=DIST / OUTPUT)
    args = ap.parse_args()

    meta = bb.load_manifest()
    if args.rebuild_site or not (SITE / "index.html").is_file():
        bb.build_site(SITE)
    bb.validate_manifest(meta, SITE)
    parts = bb.manuscript(meta, SITE)
    pages = flatten_pages(parts)

    assets: dict[str, bytes] = {}
    for font in ("NotoSerifSC-Regular.woff2", "NotoSerifSC-Bold.woff2",
                 "JetBrainsMono-Regular.woff2"):
        assets[f"fonts/{font}"] = (BOOK_DIR / "fonts" / font).read_bytes()
    for lic in ("OFL-NotoSerifSC.txt", "OFL-JetBrainsMono.txt"):
        assets[f"fonts/{lic}"] = (BOOK_DIR / "fonts" / lic).read_bytes()

    files = {p["stem"]: p["file"] for p in pages}
    stems = set(files)
    for page in pages:
        html = inline_mermaid_as_file(page["html"], assets)
        html = bb.rewrite_links(html, page["stem"], stems, meta)
        html = rewrite_book_links(html, files)
        html = fileize_images(html, SITE, assets)
        page["html"] = html

    stats = typeset(pages, assets)
    cover = render_cover()
    package(args.out, meta, parts, pages, assets, cover)
    validate(args.out)

    size = args.out.stat().st_size
    sha = hashlib.sha256(args.out.read_bytes()).hexdigest()
    print(f"epub  {args.out} ({size:,} bytes, {len(pages)} pages, "
          f"{len(assets)} assets, {stats['formulas']} formulas "
          f"({stats['unique']} unique svg))")
    print(f"sha256 {sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
