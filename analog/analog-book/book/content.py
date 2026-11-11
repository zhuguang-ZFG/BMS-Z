"""站点 HTML -> 书内片段：抽取、锚点、标题、链接、图片、表格与 Mermaid。"""
from __future__ import annotations

import base64
import html
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import config
from .manifest import BookError
from .storyboard import build_storyboard
from .svg_refine import is_animated_svg, is_legacy_svg, refine_svg

ARTICLE_RE = re.compile(
    r'<article class="md-content__inner md-typeset">(.*?)</article>', re.S)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
HEADING_RE = re.compile(
    r"<h([123])(?P<attrs>[^>]*)>(?P<body>.*?)</h\1>", re.S)
HEADING_ID_RE = re.compile(
    r'<h([123])\s+id="([^"]+)"[^>]*>(.*?)</h\1>', re.S)
TAG_RE = re.compile(r"<[^>]+>")
ID_ATTR_RE = re.compile(r'(?<![\w-])(id|name)="([^"]+)"')
NUMBERED_RE = re.compile(r"^(?:\d+|[A-H])(?:\.\d+)+")
MIME = {
    ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif",
}
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "data:")
QUIZ_CHAPTER_RE = re.compile(r"quiz-ch(\d+)$")
SPECIAL_TARGETS = {
    "index": "#book-toc",
    "p0-07-toc": "#book-toc",
    "p1-00-part1": "#part-i",
    "p2-00-part2": "#part-ii",
    "p3-00-part3": "#part-iii",
    "p4-00-part4": "#part-iv",
    "p5-00-part5": "#appendix-a",
    "p6-00-part6": "#appendix-c",
    "p7-00-part7": "#appendix-d",
    "p8-00-part8": "#appendix-d",
}


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    anchor: str
    numbered: bool


@dataclass
class ContentPage:
    stem: str
    source: str
    title: str
    html: str
    headings: list[Heading] = field(default_factory=list)
    images: int = 0


def plain_text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub("", fragment))).replace(
        "\u00b6", "").strip()


def strip_visual_players(fragment: str) -> str:
    def print_player(match):
        # 网页播放器默认是结论静帧；书内改回主资产引用，由 _asset_path 选择完整分镜。
        image = re.search(r'<img\b[^>]*>', match.group("body"))
        if image is None:
            raise BookError("V2 播放器缺静态回退图")
        source = html.unescape(match.group("source"))
        return re.sub(r'\bsrc="[^"]+"', lambda _m: 'src="' + html.escape(source, quote=True) + '"', image.group(0), count=1)
    return re.sub(
        r'<div class="visual-player"[^>]*data-animation-src="(?P<source>[^"]+)"[^>]*>'
        r'(?P<body>.*?)<p class="visual-player-links">.*?</p>\s*</div>',
        print_player, fragment, flags=re.S)


def clean_fragment(fragment: str) -> str:
    fragment = strip_visual_players(fragment)
    fragment = re.sub(
        r'<a[^>]+class="md-content__button md-icon".*?</a>', "",
        fragment, flags=re.S)
    fragment = re.sub(r'<a class="headerlink".*?</a>', "", fragment, flags=re.S)
    fragment = re.sub(
        r'<div class="legacy-anchor".*?</div>', "", fragment, flags=re.S)
    fragment = re.sub(
        r"<hr\s*/?>\s*<blockquote>\s*<p>✍️ <strong>参与共建.*$", "",
        fragment, flags=re.S)
    fragment = re.sub(r"\s+data-study-video(?:=\"[^\"]*\")?", "", fragment)
    # 题库页靠 <details> 解析答案；非题库页随后由 transforms.unwrap_details 展开。
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


def namespace_ids(fragment: str, stem: str) -> str:
    prefix = stem + "--"

    def rewrite_tag(match: re.Match) -> str:
        tag = _drop_duplicate_name(match)
        return ID_ATTR_RE.sub(
            lambda m: '%s="%s%s"' % (m.group(1), prefix, m.group(2)), tag)

    return TAG_RE.sub(rewrite_tag, fragment)


def assign_heading_ids(fragment: str, stem: str) -> str:
    counters = {2: 0, 3: 0}
    used = set()
    for tag in TAG_RE.findall(fragment):
        used.update(m.group(2) for m in ID_ATTR_RE.finditer(tag)
                    if m.group(1) == "id")

    def repl(match: re.Match) -> str:
        level, attrs, body = int(match.group(1)), match.group(2), match.group(3)
        if level == 1 or re.search(r'(?<![\w-])id="[^"]+"', attrs):
            return match.group(0)
        while True:
            counters[level] += 1
            anchor = f"{stem}--h{level}-{counters[level]}"
            if anchor not in used:
                break
        used.add(anchor)
        return f'<h{level} id="{anchor}"{attrs}>{body}</h{level}>'

    return HEADING_RE.sub(repl, fragment)


def collect_headings(fragment: str) -> list[Heading]:
    result = []
    for match in HEADING_ID_RE.finditer(fragment):
        level = int(match.group(1))
        text = plain_text(match.group(3))
        result.append(Heading(
            level=level, text=text, anchor=match.group(2),
            numbered=level > 1 and bool(NUMBERED_RE.match(text))))
    return result


def _special_target(stem: str, anchor: str) -> str:
    if stem == "p5-00-part5" and anchor.startswith("demo"):
        return "#anim-" + anchor[4:]
    if stem == "p9-00-quiz":
        match = QUIZ_CHAPTER_RE.fullmatch(anchor)
        if match:
            return f"#chapter-{int(match.group(1))}--exercises"
        return "#appendix-f-answers"
    return SPECIAL_TARGETS.get(stem, "#book-toc")


def rewrite_links(fragment: str, current_stem: str, page_stems: set[str],
                  manifest: dict) -> str:
    site_url = manifest["site_url"].rstrip("/") + "/"

    def repl(match: re.Match) -> str:
        href = match.group(1)
        if not href or href == "#" or href.startswith(EXTERNAL_PREFIXES):
            return match.group(0)
        if href.startswith("#"):
            return f'href="#{current_stem}--{href[1:]}"'
        path, _, anchor = href.partition("#")
        name = path.rsplit("/", 1)[-1]
        if name.endswith(".html"):
            stem = name[:-5]
            if stem in page_stems:
                target = f"page-{stem}" if not anchor else f"{stem}--{anchor}"
                return f'href="#{target}"'
            return f'href="{_special_target(stem, anchor)}"'
        return f'href="{site_url}{href.lstrip("/")}"'

    return re.sub(r'href="([^"]+)"', repl, fragment)


def _asset_path(rel: str, site_dir: Path) -> Path:
    if rel.startswith(("assets/figures-v2/", "assets/svg-v2/")):
        manifest_path = config.ROOT / "docs/superpowers/visual/visual-manifest.yml"
        if not manifest_path.is_file():
            raise BookError("V2 印刷资产缺 visual-manifest.yml")
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        for asset in data.get("assets", []):
            derivatives = (asset.get("print_fallback"), asset.get("reduced_motion"), asset.get("storyboard"))
            if rel in derivatives and rel != asset.get("output"):
                if asset.get("kind") == "figure" and asset.get("status") not in {"accepted", "published"}:
                    raise BookError(f"V2 插图尚未通过审图: {rel}")
                break
            if rel not in (asset.get("output"), asset.get("preview")):
                continue
            fallback = asset.get("storyboard") if asset.get("kind") == "animation" else asset.get("print_fallback")
            if not fallback or fallback == rel:
                raise BookError(f"V2 资产缺独立印刷回退: {rel}")
            if asset.get("kind") == "figure" and asset.get("status") not in {"accepted", "published"}:
                raise BookError(f"V2 插图尚未通过审图: {rel}")
            target = (config.ROOT / fallback).resolve()
            if not target.is_relative_to(config.ROOT.resolve()) or not target.is_file():
                raise BookError(f"V2 印刷回退不存在或越界: {fallback}")
            return target
        else:
            raise BookError(f"V2 图片未在 manifest 登记: {rel}")
    for base in (config.ROOT, site_dir):
        candidate = (base / rel).resolve()
        if candidate.is_file():
            return candidate
    raise BookError(f"图片不存在: {rel}")


def _data_uri(path: Path, *allowed_roots: Path) -> str:
    resolved = path.resolve()
    if not resolved.is_file():
        raise BookError(f"图片不存在: {path}")
    roots = allowed_roots or (config.ROOT,)
    if not any(resolved.is_relative_to(root.resolve()) for root in roots):
        raise BookError(f"图片不在仓库或站点目录内: {path}")
    mime = MIME.get(resolved.suffix.lower())
    if mime is None:
        raise BookError(f"不支持的图片类型: {path}")
    raw = resolved.read_bytes()
    if mime == "image/svg+xml":
        text = raw.decode("utf-8-sig")
        if is_legacy_svg(text) and is_animated_svg(text):
            # 旧模板动画：印刷版出分镜（全尺寸画布 + 节拍帧 + 原字号接力字幕），
            # 接力拍字幕不再折叠成末拍（v3.88，SPEC-V4 §2.1 S2）。
            raw = build_storyboard(text, refine_svg(text)).encode("utf-8")
        else:
            raw = refine_svg(text).encode("utf-8")
    return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")


def inline_images(fragment: str, site_dir: Path) -> tuple[str, int]:
    count = 0

    def source(match: re.Match) -> str:
        nonlocal count
        count += 1
        target = _asset_path(match.group(2), site_dir)
        return f'{match.group(1)}="{_data_uri(target, config.ROOT, site_dir)}"'

    fragment = re.sub(r'(?<![\w-])(src)="(assets/[^"]+)"', source, fragment)
    fragment = re.sub(r'(?<![\w-])(srcset)="(assets/[^"]+)"', source, fragment)
    remote = re.search(r'(?<![\w-])(?:src|srcset)="(https?://[^"]+)"', fragment)
    if remote:
        raise BookError(f"书内仍有远程图片: {remote.group(1)}")
    return fragment, count


def replace_mermaid(fragment: str, docs_dir: Path = config.DOCS,
                    static_dir: Path = config.BOOK_DIR / "static") -> str:
    if '<pre class="mermaid">' not in fragment:
        return fragment
    snapshot = static_dir / "roadmap.svg"
    source_file = static_dir / "roadmap.source.txt"
    if not snapshot.is_file() or not source_file.is_file():
        raise BookError("缺少 static/roadmap.svg 或 static/roadmap.source.txt")
    doc = (docs_dir / "p0-06-roadmap.md").read_text(encoding="utf-8")
    match = re.search(r"```mermaid\n(.*?)```", doc, re.S)
    if match is None:
        raise BookError(
            "docs/p0-06-roadmap.md 缺少 mermaid 代码块")
    source = match.group(1).strip() + "\n"
    if source != source_file.read_text(encoding="utf-8"):
        raise BookError("docs/p0-06-roadmap.md 与 static/roadmap.source.txt 不一致")
    svg = snapshot.read_text(encoding="utf-8").strip()
    return re.sub(r'<pre class="mermaid">.*?</pre>',
                  '<figure class="book-roadmap">' + svg
                  + '<figcaption>六阶段学习路线与方向深化</figcaption></figure>',
                  fragment, flags=re.S)


def wrap_tables(fragment: str) -> str:
    def wrap(match: re.Match) -> str:
        before = fragment[:match.start()]
        if re.search(r'<div class="table-wrap"[^>]*>\s*$', before):
            return match.group(0)
        return f'<div class="table-wrap">{match.group(0)}</div>'

    return re.sub(r'<table(?:\s[^>]*)?>.*?</table>', wrap,
                  fragment, flags=re.S)


def extract_article(site_dir: Path, name: str) -> ContentPage:
    path = site_dir / name.replace(".md", ".html")
    page = path.read_text(encoding="utf-8")
    match = ARTICLE_RE.search(page)
    if not match:
        raise BookError(f"{path.name}: 找不到 <article>")
    fragment = clean_fragment(match.group(1))
    h1 = H1_RE.search(fragment)
    if not h1:
        raise BookError(f"{path.name}: <article> 中缺少 <h1>")
    title = plain_text(h1.group(1))
    if not title:
        raise BookError(f"{path.name}: <h1> 标题为空")
    stem = Path(name).stem
    fragment = assign_heading_ids(namespace_ids(fragment, stem), stem)
    return ContentPage(stem=stem, source=name, title=title, html=fragment,
                       headings=collect_headings(fragment))


def load_page(site_dir: Path, name: str, page_stems: set[str],
              manifest: dict) -> ContentPage:
    page = extract_article(site_dir, name)
    fragment = replace_mermaid(page.html)
    fragment = rewrite_links(fragment, page.stem, page_stems, manifest)
    fragment, images = inline_images(fragment, site_dir)
    page.html = wrap_tables(fragment)
    page.images = images
    return page
