#!/usr/bin/env python3
"""Assemble the engineering deep-dive product (P2.6) from the registries only.

The builder never reads docs/.vitepress/site-dist or any built artifact: unit
manuscripts, claims, figures and experiments come from the four registries in
bms-book/, Markdown rendering is delegated to bms-book/engineering/render.mjs
(the site's own createMarkdownRenderer, math included). Reading levels (P2.3)
become data-level attributes; the level toggle is a render-time filter, so
closing a shallow level never deletes technical text.

Output: a single-file engineering-book.html, engineering.epub, copied figure
assets and deterministic build-report.json (content hashes, no timestamps).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
from html import escape
from io import BytesIO
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ENGINEERING = ROOT / "bms-book/engineering"
MANIFEST = ROOT / "bms-book/engineering/manifest.json"
CLAIMS = ROOT / "bms-book/engineering/claims.json"
FIGURES = ROOT / "bms-book/engineering/figures.json"
EXPERIMENTS = ROOT / "bms-book/engineering/experiments.json"
RENDERER = ENGINEERING / "render.mjs"
LEVELS = ["intro", "core", "derivation", "lab", "research"]
BOOK_NAME = "BMS 工程深研册"
BOOK_EDITION = "已实现单元审阅版"
BOOK_TITLE = f"{BOOK_NAME}（{BOOK_EDITION}）"

COVER_CSS = """
.book-cover { color: #183830; border-top: 3px solid #285c4b; padding: 1.4em 0 1.8em; }
.cover-edition { margin: 0 0 1em; font-size: .85em; letter-spacing: .12em; }
.book-cover h1 { margin: 0; padding: 0; border: 0; color: inherit;
  font: bold 2.8em/1.14 "Noto Serif CJK SC", "Songti SC", SimSun, serif; }
.cover-scope { max-width: 35em; line-height: 1.65; margin: 1.1em 0 1.5em; }
.book-cover figure { margin: 0; }
.cover-photo { display: block; width: 100%; max-width: 36em; height: auto; margin: 0 auto; }
.book-cover figcaption { margin: .65em 0 0; font-size: .84em; line-height: 1.5; }
.cover-credit { display: block; }
.cover-status { border-top: 1px solid #a9b7ad; margin: 1.3em 0 0; padding-top: .65em;
  font-size: .85em; }
"""

GUIDE_CSS = """
.bridge-checks ul { list-style: none; padding: 0; margin: 0; }
.bridge-checks li { margin: 0; padding: .7em 0; border-top: 1px solid #b5c2b9;
  break-inside: avoid; }
.bridge-checks p { margin: 0; }
.bridge-checks p + p { margin-top: .3em; color: #46594e; font-size: .92em; }
.bridge-checks a { color: #214e42; text-underline-offset: .16em; }
.protection-sequence { list-style: none; display: flex; margin: 1.25em 0; padding: 0;
  break-inside: avoid; }
.protection-sequence li { position: relative; flex: 1; padding: .65em .45em 0 0;
  border-top: 1px solid #879e91; }
.protection-sequence li::before { content: ""; position: absolute; top: -.24em; left: 0;
  width: .4em; height: .4em; border-radius: 50%; background: #375e4c; }
.protection-sequence strong, .protection-sequence span { display: block; }
.protection-sequence span { font-size: .88em; margin-top: .18em; }
@media screen and (max-width: 32em) {
  .bridge-checks li p:first-child a { display: block; margin-bottom: .3em; }
  .protection-sequence { display: block; margin-left: .3em; }
  .protection-sequence li { padding: 0 0 .75em 1em; border: 0; border-left: 1px solid #879e91; }
  .protection-sequence li:last-child { padding-bottom: 0; }
  .protection-sequence li::before { top: .65em; left: -.24em; }
  .protection-sequence strong, .protection-sequence span { display: inline; margin-right: .5em; }
}
@media screen and (max-width: 26em) {
}
"""

PAGE_CSS = COVER_CSS + GUIDE_CSS + """
:root { --ink: #25352f; --paper: #f7f5ef; --accent: #23584d; --line: #cdd5cd; }
* { box-sizing: border-box; }
body { margin: 0 auto; max-width: 880px; padding: 24px 20px 64px; color: var(--ink);
  background: var(--paper); font: 16px/1.75 -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif;
  overflow-wrap: anywhere; }
h1 { font-size: 1.6rem; border-bottom: 2px solid var(--accent); padding-bottom: .3em; }
h2 { margin-top: 2.2em; font-size: 1.25rem; }
h3 { font-size: 1.05rem; }
code, pre { background: #efe9db; border-radius: 4px; }
code { padding: .1em .35em; overflow-wrap: anywhere; }
pre { padding: .8em 1em; overflow-x: auto; font: .9em/1.55 Consolas, "Liberation Mono", monospace; }
pre code { font-family: inherit; background: none; padding: 0; overflow-wrap: normal; }
table { display: block; max-width: 100%; overflow-x: auto; border-collapse: collapse;
  width: 100%; margin: 1em 0; font-size: .95rem; }
mjx-container[display="true"] { max-width: 100%; overflow-x: auto; overflow-y: hidden; }
mjx-container:not([display="true"]) { display: inline-block; max-width: 100%;
  overflow-x: auto; overflow-y: hidden; vertical-align: middle; }
th, td { border: 1px solid var(--line); padding: .35em .6em; text-align: left; }
img { max-width: 100%; height: auto; }
figure { margin: 1.35em 0; }
figure img { display: block; margin-inline: auto; }
figcaption { font-size: .9rem; line-height: 1.55; color: #435362; margin-top: .55em; }
a { color: var(--accent); }
.callout, .chapter-route { border: 1px solid var(--line); border-left: 4px solid var(--accent);
  background: #fbf8f1; padding: .6em 1em; margin: 1em 0; border-radius: 4px; }
.callout-title, .chapter-route__eyebrow { font-weight: 600; margin-bottom: .3em; }
.chapter-route ol { margin: .3em 0 0; padding-left: 1.3em; }
.chapter-route li > strong { margin-inline-end: .55em; }
.level-bar { position: sticky; top: 0; background: var(--paper); border-bottom: 1px solid var(--line);
  padding: .5em 0; margin-bottom: 1em; display: none; gap: .5em; align-items: center; flex-wrap: wrap; z-index: 5; }
.has-levels .level-bar { display: flex; }
.level-bar button { border: 1px solid var(--line); background: #fff; border-radius: 4px;
  padding: .25em .8em; cursor: pointer; font-size: .9rem; }
.level-bar button[aria-pressed="true"] { background: var(--accent); color: #fff; border-color: var(--accent); }
.level-note { font-size: .8rem; color: #5a6a76; }
.book-cover { background: #fffefb; padding: 1.4rem clamp(1rem, 5vw, 3.4rem) 1.25rem; }
.book-cover h1 { font-size: clamp(2.1rem, 7vw, 4rem); }
.book-cover figure { padding-top: 1rem; border-top: 1px solid #d4dcd5; }
.cover-photo { mix-blend-mode: multiply; }
.cover-credit { color: #435850; }
.cover-credit a { color: inherit; }
nav.toc { margin: 1.5em 0 3em; }
.toc h2, .book-chapter > h1 { font-family: "Noto Serif CJK SC", "Songti SC", SimSun, serif;
  color: #183830; line-height: 1.3; }
.book-chapter > h1 { margin-top: 2.2em; font-size: clamp(1.6rem, 4vw, 2.1rem);
  border-bottom: 1px solid #80998c; }
.toc h2 { margin: 0 0 .65em; font-size: 1.65rem; }
.toc > ol, .toc details ol { list-style: none; padding: 0; margin: 0; }
.toc > ol > li { position: relative; border-top: 1px solid var(--line); }
.toc-entry { display: flex; align-items: baseline; width: fit-content; max-width: 100%; padding: .52em 0;
  font-weight: 600; color: #243d35; text-decoration: none; }
.toc-code { flex: none; min-width: 2.6em; color: #765039;
  font-family: Consolas, "Liberation Mono", monospace; font-variant-numeric: tabular-nums; }
.toc-entry:hover, .toc details a:hover { text-decoration: underline; }
.toc details { padding-bottom: .6em; }
.toc summary { width: fit-content; font-size: .88em; color: #395648; cursor: pointer; }
.toc details ol { padding: .3em 0 .1em 1em; border-left: 1px solid #a9b7ad; margin: .45em 0 0 .25em; }
.toc details a { display: inline-block; padding: .18em 0; }
.book-chapter, .book-chapter :is(h1,h2,h3)[id] { scroll-margin-top: calc(var(--level-bar-height, 0px) + .75rem); }
@media screen and (min-width: 24em) {
  .toc-entry { max-width: calc(100% - 5em); }
  .toc details { padding-bottom: 0; }
  .toc summary { position: absolute; top: .6em; right: .2em; }
  .toc details ol { margin: 0 0 .8em 1em; }
}
.unit-card { border: 1px solid var(--line); border-radius: 6px; padding: 1em 1.2em; margin: 1em 0; background: #fff; }
.unit-card h2 { margin: 0 0 .3em; border: none; }
.badge { display: inline-block; border: 1px solid var(--line); border-radius: 999px;
  padding: .05em .6em; font-size: .78rem; margin-right: .35em; color: #445; }
footer { margin-top: 3em; font-size: .8rem; color: #5a6a76; border-top: 1px solid var(--line); padding-top: 1em; }
@media print {
  @page { size: A4; margin: 16mm;
    @bottom-right { content: counter(page); font: 9pt sans-serif; color: #46564d; }
  }
  @page:first { @bottom-right { content: none; } }
  body { padding: 0; background: #fff; }
  h1, h2, h3 { break-after: avoid; }
  figure, tr { break-inside: avoid; }
  figure img { max-height: 105mm; width: auto; }
  .book-cover { break-after: page; background: white; padding: 13mm 0 0; border-top-width: 2pt; }
  .cover-edition { font-size: 12pt; }
  .book-cover h1 { font-size: 44pt; margin: 10mm 0 5mm; }
  .cover-scope { font-size: 13pt; max-width: 33em; }
  .book-cover figure { padding-top: 12mm; margin: 13mm 0 0; }
  .book-cover .cover-photo { width: 158mm; max-width: 100%; max-height: none; }
  .book-cover figcaption { margin-top: 6mm; }
  .cover-status { margin-top: 9mm; }
  nav.toc { break-after: page; margin: 0; }
  .toc h2 { margin: 1mm 0 6mm; }
  .toc > ol { column-count: 2; column-gap: 10mm; }
  .toc > ol > li { break-inside: avoid; padding: 1.7mm 0; }
  .toc-entry { font-size: 10pt; line-height: 1.35; font-weight: 400;
    width: 100%; padding: 0 9mm 0 0; }
  .toc details { display: none !important; }
  .book-chapter { break-before: page; }
  .book-chapter > h1 { margin: 0 0 .85em; font-size: 23pt; }
  #prerequisites--toc { font-size: 11.5pt; line-height: 1.55; }
  #prerequisites--toc h2 { margin: 1.2em 0 .5em; }
  #prerequisites--toc h3 { margin: 1em 0 .25em; }
  #prerequisites--toc p { margin-block: .5em; }
  #prerequisites--toc .bridge-checks p { margin: 0; }
  #prerequisites--toc .bridge-checks p + p { margin-top: .3em; }
  #prerequisites--toc :is([id="prerequisites--三个概念补丁"], [id="prerequisites--依赖关系"]) {
    break-before: page; margin-top: 0; }
  .level-bar, .book-search { display: none !important; }
  [hidden] { display: revert !important; }
  pre { white-space: pre-wrap; overflow-wrap: anywhere; }
  pre code { overflow-wrap: anywhere; }
  table { display: table; table-layout: fixed; }
  th, td { overflow-wrap: anywhere; }
  mjx-container { overflow: visible !important; }
  mjx-container svg { max-width: 100%; height: auto; }
}
"""

LEVEL_JS = """
(function () {
  var RANK = { intro: 0, core: 1, derivation: 2, lab: 3, research: 4 };
  var main = document.querySelector('main');
  if (!main) return;
  var items = [];
  var chapters = main.querySelectorAll('section.book-chapter');
  for (var container of chapters.length ? chapters : [main]) {
    var current = 'intro';
    for (var node of container.children) {
      if (node.tagName === 'H2') current = node.getAttribute('data-level') || 'core';
      items.push([node, current]);
    }
  }
  var bar = document.querySelector('.level-bar');
  document.documentElement.classList.add('has-levels');
  function syncBarHeight() {
    document.documentElement.style.setProperty('--level-bar-height', bar.offsetHeight + 'px');
  }
  syncBarHeight();
  new ResizeObserver(syncBarHeight).observe(bar);
  function apply(level) {
    var max = RANK[level];
    for (var pair of Array.from(items)) {
      var el = pair[0];
      if (el.nodeType !== 1) continue;
      var rank = RANK[pair[1]];
      if (rank === undefined) continue;
      el.hidden = rank > max && el.tagName !== 'H1';
    }
    for (var btn of bar.querySelectorAll('button')) {
      btn.setAttribute('aria-pressed', String(btn.dataset.level === level));
    }
    try { localStorage.setItem('engineering-level', level); } catch (e) {}
  }
  bar.addEventListener('click', function (event) {
    var level = event.target && event.target.dataset && event.target.dataset.level;
    if (level) apply(level);
  });
  function revealSection(target, openAnswers) {
    if (!target) return;
    var start = items.findIndex(function (pair) { return pair[0] === target || pair[0].contains(target); });
    if (start < 0) return;
    while (start > 0 && items[start][0].tagName !== 'H2' && items[start][0].tagName !== 'H1') start--;
    for (var i = start; i < items.length; i++) {
      if (i > start && /^(H1|H2)$/.test(items[i][0].tagName)) break;
      items[i][0].hidden = false;
      if (openAnswers) {
        if (items[i][0].tagName === 'DETAILS') items[i][0].open = true;
        for (var answer of items[i][0].querySelectorAll('details')) answer.open = true;
      }
    }
  }
  document.addEventListener('engineering-search-navigate', function (event) {
    revealSection(document.getElementById(event.detail.id), true);
  });
  var toc = main.querySelector('nav.toc');
  if (toc) toc.addEventListener('click', function (event) {
    var link = event.target.closest('a[href^="#"]');
    if (link) revealSection(document.getElementById(link.getAttribute('href').slice(1)), false);
  });
  var saved = null;
  try { saved = localStorage.getItem('engineering-level'); } catch (e) {}
  apply(saved || 'lab');
})();
"""


def book_introduction(unit_count: int) -> str:
    photo = ROOT / "docs/circuits/assets/photos/libresolar-bms-c1.jpg"
    image = base64.b64encode(photo.read_bytes()).decode("ascii")
    return (
        f'<header class="book-cover"><p class="cover-edition">{BOOK_EDITION}</p>'
        f'<h1>{BOOK_NAME}</h1><p class="cover-scope">本版收录 {unit_count} 个工程单元。'
        '符号、单位和电流方向见《工程深研约定》，各实验的代码入口和来源列在册末。</p>'
        f'<figure><img class="cover-photo" width="1200" height="643" src="data:image/jpeg;base64,{image}" '
        'alt="Libre Solar BMS C1 电路板，右侧是成排的采样接口。">'
        '<figcaption>Libre Solar BMS C1 电路板<span class="cover-credit">摄影及来源　'
        '<a href="https://github.com/LibreSolar/bms-c1/blob/main/build/bms-c1.jpg">Libre Solar</a> · '
        '<a href="https://creativecommons.org/licenses/by-sa/4.0/deed.zh-hans">CC BY-SA 4.0</a>'
        '</span></figcaption></figure>'
        '<p class="cover-status">独立技术审查、硬件验收和读者试读仍待完成。</p></header>'
    )


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"工程装配：{path.name} 读不到或解析不了：{exc}") from exc


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def section_levels(unit: dict, claims: list[dict], experiments: list[dict]) -> dict:
    """Map heading anchor -> reading level for one unit."""
    derivation = {c["anchor"] for c in claims if c.get("unit") == unit["id"]}
    lab: set[str] = set()
    for exp in experiments:
        if exp.get("unit") != unit["id"]:
            continue
        for key in ("student_tasks_anchor", "rejects_anchor", "frozen_anchor"):
            lab.add(exp[key])
    return {anchor: "derivation" for anchor in derivation} | {
        anchor: "lab" for anchor in lab
    }


def anchor_token(text: str) -> str:
    parts = text.split()
    return parts[0] if parts else text


def tag_levels(html: str, levels: dict[str, str], default: str | None = None) -> str:
    """Label each h2 with its registered level or the chapter default."""

    def repl(match: re.Match) -> str:
        attrs, text = match.group(1), match.group(2)
        plain = re.sub(r"<[^>]+>", "", text).strip()
        level = levels.get(anchor_token(plain)) or levels.get(plain) or default
        if level and "data-level" not in attrs:
            return f'<h2{attrs} data-level="{level}">{text}</h2>'
        return match.group(0)

    return re.sub(r"<h2([^>]*)>([\s\S]*?)</h2>", repl, html)


def page_html(title: str, body: str, level_bar: bool) -> str:
    bar = ""
    if level_bar:
        buttons = "".join(
            f'<button type="button" data-level="{level}">{label}</button>'
            for level, label in [
                ("intro", "导读"),
                ("core", "核心"),
                ("derivation", "推导"),
                ("lab", "动手"),
                ("research", "研究"),
            ]
        )
        bar = (
            f'<div class="level-bar" role="group" aria-label="阅读层级">{buttons}'
            '<span class="level-note">层级只过滤显示，正文始终完整（含折叠答案与来源）</span></div>'
        )
    script = f"<script>{LEVEL_JS}</script>" if level_bar else ""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · BMS 工程深研</title>
<style>{PAGE_CSS}</style>
</head>
<body>
{bar}
<main>
{body}
</main>
{script}
</body>
</html>
"""


def book_html(title: str, body: str, introduction: str) -> str:
    """单文件工程深研书：CSS/JS/图全部内联，断网可整体搬走。"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{PAGE_CSS}</style>
</head>
<body>
{introduction}
<div class="level-bar" role="group" aria-label="阅读层级">{
        "".join(
            f'<button type="button" data-level="{level}">{label}</button>'
            for level, label in [
                ("intro", "导读"),
                ("core", "核心"),
                ("derivation", "推导"),
                ("lab", "动手"),
                ("research", "研究"),
            ]
        )
    }<span class="level-note">层级只过滤显示，正文始终完整（含折叠答案与来源）</span></div>
<main>
{body}
</main>
<script>{LEVEL_JS}</script>
</body>
</html>
"""


def _dims_from_bytes(kind: str, data: bytes) -> str:
    """从图片字节读固有尺寸（kind 为 mime 或后缀），供产物侧宽高占位。"""
    suffix = kind.lower().lstrip(".")
    if "svg" in suffix:
        m = re.search(
            r'viewBox="([\d.]+)[ \t]+([\d.]+)[ \t]+([\d.]+)[ \t]+([\d.]+)"',
            data.decode("utf-8", errors="replace"),
        )
        if m:
            return f'width="{m.group(3)}" height="{m.group(4)}" '
    if "png" in suffix and data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        import struct

        w, h = struct.unpack(">II", data[16:24])
        return f'width="{w}" height="{h}" '
    if "webp" in suffix and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        if data[12:16] == b"VP8X" and len(data) >= 30:
            w = int.from_bytes(data[24:27], "little") + 1
            h = int.from_bytes(data[27:30], "little") + 1
            return f'width="{w}" height="{h}" '
        if data[12:16] == b"VP8 " and len(data) >= 30:
            w = int.from_bytes(data[26:28], "little") & 0x3FFF
            h = int.from_bytes(data[28:30], "little") & 0x3FFF
            return f'width="{w}" height="{h}" '
        if data[12:16] == b"VP8L" and len(data) >= 25:
            bits = int.from_bytes(data[21:24], "little")
            w = (bits & 0x3FFF) + 1
            h = ((bits >> 14) & 0x3FFF) + 1
            return f'width="{w}" height="{h}" '
    return ""


def _image_dims(path: Path) -> str:
    """读图片固有尺寸。单文件书里的图一律 data URI，产物侧 check_pages 仍要求真实像素
    宽高占位（懒加载落地那一刻不把正文顶开）。"""
    try:
        return _dims_from_bytes(path.suffix, path.read_bytes())
    except OSError:
        return ""


def backfill_data_uri_dims(html: str) -> str:
    """markdown 渲染层内联出的 data URI 图只有 width 没有 height（或都没有），产物门会红；
    缺哪个补哪个——已有显示宽时按图片固有比例等比补高，没有的用固有尺寸。"""

    def repl(match: re.Match) -> str:
        attrs, uri, suffix = match.group(1), match.group(2), match.group(3)
        head = re.match(r"data:(image/[\w.+-]+);base64,", uri)
        if not head:
            return match.group(0)
        try:
            payload = base64.b64decode(uri[head.end():])
        except Exception:
            return match.group(0)
        dims = _dims_from_bytes(head.group(1), payload)
        m = re.match(r'width="([\d.]+)" height="([\d.]+)"', dims) if dims else None
        if not m:
            return match.group(0)
        nat_w, nat_h = float(m.group(1)), float(m.group(2))
        has_w = re.search(r'\bwidth="[\d.]+"', attrs + suffix)
        has_h = re.search(r'\bheight="[\d.]+"', attrs + suffix)
        parts: list[str] = []
        if has_w and not has_h:
            shown = float(re.search(r'\bwidth="([\d.]+)"', attrs + suffix).group(1))
            parts.append(f'height="{round(nat_h * shown / nat_w)}"')
        elif not has_w and not has_h:
            parts.append(f'width="{m.group(1)}"')
            parts.append(f'height="{m.group(2)}"')
        else:
            return match.group(0)
        add = " ".join(parts) + " "
        return f'<img{attrs}{add}src="{uri}"{suffix}>'

    return re.sub(r'<img\b([^>]*?)src="(data:image/[^"]+)"([^>]*)>', repl, html)


def inline_images(html: str) -> str:
    """把 assets/ 相对图片引用内联为 data URI，单文件不依赖外部文件。"""
    def repl(match: re.Match) -> str:
        attrs, src, suffix = match.group(1), match.group(2), match.group(3)
        path = ENGINEERING / src
        if not path.is_file():
            raise SystemExit(f"工程装配：单文件书嵌不进找不到的图 {src}")
        mime = {
            ".svg": "image/svg+xml",
            ".webp": "image/webp",
            ".png": "image/png",
        }.get(path.suffix.lower())
        if mime is None:
            raise SystemExit(f"工程装配：不支持的图片类型 {src}")
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        loading = "" if re.search(r"\bloading=", attrs + suffix) else 'loading="lazy" '
        dims = "" if re.search(r"\bwidth=", attrs + suffix) else _image_dims(path)
        return f'<img{attrs}{dims}{loading}src="data:{mime};base64,{encoded}"{suffix}>'

    return re.sub(r'<img\b([^>]*?)src="(assets/[^"]+)"([^>]*)>', repl, html)


def _completed_webp(payload: bytes, fmt: str) -> bytes:
    """Use the completed storyboard for print, reduced motion and EPUB."""
    from PIL import Image

    with Image.open(BytesIO(payload)) as image:
        if fmt == "WEBP" and not image.is_animated:
            return payload
        image.seek(image.n_frames - 1)
        out = BytesIO()
        image.save(out, format=fmt, **({"quality": 90} if fmt == "WEBP" else {}))
        return out.getvalue()


def add_static_posters(html: str) -> str:
    def picture(match: re.Match) -> str:
        payload = base64.b64decode(match[1])
        still = _completed_webp(payload, "WEBP")
        if still == payload:
            return match[0]
        srcset = base64.b64encode(still).decode("ascii")
        return (f'<picture><source media="print, (prefers-reduced-motion: reduce)" '
                f'srcset="data:image/webp;base64,{srcset}">{match[0]}</picture>')

    return re.sub(r'<img\b[^>]*?\bsrc="data:image/webp;base64,([^"]+)"[^>]*>', picture, html)


def prefix_ids(fragment: str, prefix: str) -> str:
    """每单元 id/锚加前缀，合书后跨章不重号。"""
    fragment = re.sub(r'id="', f'id="{prefix}--', fragment)
    fragment = re.sub(r'href="#', f'href="#{prefix}--', fragment)
    return fragment


def verify_spine(index_html: str, out: Path) -> None:
    """坏 spine 负例：书内目录锚必须逐一到得了真实标题 id。"""
    ids = set(re.findall(r'id="([^"]+)"', index_html))
    for anchor in re.findall(r'href="#([^"]+)"', index_html):
        if anchor not in ids:
            raise SystemExit(f"工程装配：坏 spine——目录锚 #{anchor} 在书内没有对应标题")


def verify_publication(out: Path) -> None:
    """P2.7 出版门（单文件书）：断链、外链资源、数学、折叠答案、来源摘要。

    整本书是一个 HTML 文件：内容链接（<a href>）允许外链可离线点开；字体、脚本、
    图片、样式必须本地自带（图片以 data URI 内联），断网阅读不破版。
    build-report.json 的来源指纹必须与当前正文源一致。
    """
    problems: list[str] = []
    book_path = out / "engineering-book.html"
    if not book_path.is_file():
        raise SystemExit(f"工程装配：出版门——单文件书缺失：{book_path}")
    text = book_path.read_text(encoding="utf-8")
    for attr, url in re.findall(r'(href|src)="([^"]+)"', text):
        if url.startswith(("http://", "https://")):
            if attr == "src" or (
                attr == "href" and re.search(r'<link[^>]+href="' + re.escape(url), text)
            ):
                problems.append(f"engineering-book.html: 外链资源 {url} 必须本地自带")
            continue
        if url.startswith(("#", "mailto:", "data:")):
            continue
        problems.append(
            f"engineering-book.html: 单文件书出现外部相对引用 {url}（应内联）"
        )
    if re.search(r'<script[^>]+src="https?://|<link[^>]+href="https?://', text):
        problems.append("engineering-book.html: 脚本/样式不得走 CDN")
    ids = set(re.findall(r'id="([^"]+)"', text))
    for anchor in re.findall(r'href="#([^"]+)"', text):
        if anchor not in ids:
            problems.append(f"engineering-book.html: 断锚 #{anchor}")
    for uid in ("s1", "s2", "s3"):
        if f"{uid}--toc" not in ids:
            problems.append(f"engineering-book.html: 缺章节 {uid}")
    if "mjx" not in text:
        problems.append("S2: 数学式未离线渲染（缺 MathJax SVG）")
    if "答案" not in text:
        problems.append("单文件书缺答案区")
    if "data:image/svg+xml;base64," not in text:
        problems.append("单文件书未内联 SVG 图")
    report_path = out / "build-report.json"
    if not report_path.is_file():
        problems.append("缺 build-report.json（来源摘要）")
    else:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        for uid, info in report.get("units", {}).items():
            source = ROOT / info["source"]
            if source.is_file() and sha256_file(source) != info["source_sha256"]:
                problems.append(f"{uid}: 出版产物的来源指纹与当前正文源不一致，须重建")
    epub = out / "engineering.epub"
    if epub.is_file():
        problems.extend(f"EPUB: {item}" for item in _epub_module().validate_epub(epub))
    if problems:
        raise SystemExit("工程装配：出版门不过——\n- " + "\n- ".join(problems))


def find_browser() -> str:
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("msedge"),
    ]
    browser = next((p for p in candidates if p and Path(p).exists()), None)
    if not browser:
        raise SystemExit("工程装配：PDF 需要 Chrome/Edge（--pdf 可跳过）")
    return browser


def print_pdfs(out: Path) -> list[str]:
    """把单文件书打印成一份 PDF（无头 Chromium，展开折叠答案后打印）。"""
    import tempfile

    browser = find_browser()
    pdf_dir = out / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    target = pdf_dir / "engineering-book.pdf"
    html = re.sub(
        r"<details\b(?![^>]*\bopen)([^>]*)>", r"<details open\1>",
        (out / "engineering-book.html").read_text(encoding="utf-8").replace('loading="lazy"', 'loading="eager"'),
    )
    try:
        import fitz
    except ImportError:
        fitz = None

    unit_ids = read_json(out / "build-report.json")["units"]

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile, tempfile.TemporaryDirectory(dir=pdf_dir) as staging:
        print_source = Path(profile) / "engineering-book-print.html"
        finished = Path(staging) / target.name

        def print_to(destination: Path, css: str) -> None:
            print_source.write_text(html.replace("</head>", f"<style media=\"print\">{css}</style></head>", 1),
                                    encoding="utf-8")
            subprocess.run(
                [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                 "--generate-pdf-document-outline", f"--user-data-dir={profile}",
                 f"--print-to-pdf={destination.resolve()}", print_source.resolve().as_uri()],
                capture_output=True, check=True, timeout=240,
            )

        print_to(finished, "")
        if fitz is not None:
            with fitz.open(finished) as document:
                document.set_metadata({"title": BOOK_TITLE, "creator": "tools/build_engineering.py --pdf"})
                document.saveIncr()
                text = "".join(page.get_text() for page in document)
                for uid in unit_ids:
                    if uid not in text:
                        raise SystemExit(f"工程装配：PDF 缺单元 {uid}，打印失败")
        finished.replace(target)
    return [target.name]


def _epub_module():
    """复用主书 EPUB 链的解析/校验能力（BookParser、validate_files、validate_epub）。"""
    import importlib.util

    path = ROOT / "bms-book" / "build_epub.py"
    spec = importlib.util.spec_from_file_location("build_epub", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"工程装配：定位不到主书 EPUB 链 {path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise SystemExit(f"工程装配：主书 EPUB 链加载失败：{exc}") from exc
    return module


def _epub_doc(
    build_epub, fragment_html: str, assets: dict, title: str
) -> tuple[bytes, list[tuple[str, str]]]:
    """把一个正文片段封成单文档 XHTML：图/MathJax 全部内嵌为本地资产。"""
    import xml.etree.ElementTree as ET

    XHTML = build_epub.XHTML
    SVG = build_epub.SVG
    q = build_epub.q

    def embed(payload: bytes, extension: str, mime: str) -> str:
        name = f"assets/{hashlib.sha256(payload).hexdigest()[:24]}.{extension}"
        assets[name] = (payload, mime)
        return name

    def normalize(parent, counter: list[int]) -> None:
        for child in list(parent):
            if child.tag == q(XHTML, "figure"):
                for caption in list(child):
                    if caption.tag == q(XHTML, "figcaption"):
                        child.remove(caption)
                        child.append(caption)
            if child.tag == q(SVG, "svg"):
                width = child.attrib.get("width", "")
                style = child.attrib.get("style", "")
                if re.fullmatch(r"[\d.]+(?:ex|em|px)", width):
                    style += f";width:{width};height:auto;"
                attrs = {
                    "src": embed(
                        build_epub.serialize_svg(child), "svg", "image/svg+xml"
                    ),
                    "alt": child.attrib.get("aria-label", "公式或机制示意图"),
                    "class": "epub-equation",
                    "style": style,
                }
                image = ET.Element(q(XHTML, "img"), attrs)
                image.tail = child.tail
                parent[list(parent).index(child)] = image
                continue
            if child.tag == q(XHTML, "img"):
                src = child.attrib.get("src", "")
                payload, mime = None, None
                data_match = re.fullmatch(
                    r"data:(image/[\w.+-]+);base64,([\s\S]+)", src
                )
                if data_match:
                    mime, encoded = data_match.groups()
                    payload = base64.b64decode(encoded, validate=True)
                elif not re.match(r"https?://", src):
                    if ".." in Path(src).parts:
                        raise SystemExit(f"工程装配：EPUB 图片路径不允许越级：{src}")
                    local = ENGINEERING / src
                    fallback = ENGINEERING / "dist" / src
                    local = local if local.is_file() else fallback
                    if not local.is_file():
                        raise SystemExit(f"工程装配：EPUB 嵌不进找不到的图 {src}")
                    payload = local.read_bytes()
                    mime = {
                        ".svg": "image/svg+xml",
                        ".webp": "image/webp",
                        ".png": "image/png",
                        ".jpg": "image/jpeg",
                    }.get(local.suffix.lower())
                if payload is None or mime is None:
                    raise SystemExit(
                        f"工程装配：EPUB 图片必须是本地文件或 data URI：{src}"
                    )
                if mime == "image/webp":
                    payload = _completed_webp(payload, "PNG")
                    mime = "image/png"
                if mime == "image/svg+xml":
                    payload = build_epub.light_svg(payload)
                extension = {
                    "image/svg+xml": "svg",
                    "image/png": "png",
                    "image/jpeg": "jpg",
                }.get(mime)
                if extension is None:
                    raise SystemExit(f"工程装配：EPUB 不支持的图片类型 {mime}")
                child.set("src", embed(payload, extension, mime))
            if child.tag == q(XHTML, "a"):
                href = child.attrib.get("href", "")
                if href.endswith("/"):
                    # 目录浏览链接在 EPUB 里没有意义：退化成纯文本，不留断链。
                    span = ET.Element(q(XHTML, "span"))
                    span.text = "".join(child.itertext()).strip()
                    parent[list(parent).index(child)] = span
                    continue
                file, separator, anchor = href.partition("#")
                if re.fullmatch(r"(?:conventions|prerequisites|sources|[bsdcr]\d+)\.html", file):
                    child.set("href", file.removesuffix(".html") + ".xhtml" + (separator + anchor if separator else ""))
            if child.tag in (q(XHTML, "h1"), q(XHTML, "h2")):
                if not child.get("id"):
                    counter[0] += 1
                    child.set("id", f"h{counter[0]:03d}")
            normalize(child, counter)

    parser = build_epub.BookParser()
    # BookParser 只认 <body> 内的内容（与主书整页输入一致）：片段先包一层。
    parser.feed(f"<body>{fragment_html}</body>")
    counter = [0]
    normalize(parser.root, counter)
    outline = [el for el in parser.root.iter() if el.tag in (q(XHTML, "h1"), q(XHTML, "h2")) and el.get("id")]
    if not outline:
        raise SystemExit(f"工程装配：EPUB 文档没有可导航标题：{title}")
    # The parent link already opens the chapter at its first heading.
    if outline[0].tag == q(XHTML, "h1"):
        outline = outline[1:]
    headings = [(el.get("id"), "".join(el.itertext()).strip()) for el in outline]

    html = ET.Element(q(XHTML, "html"), {"lang": "zh-CN"})
    head = ET.SubElement(html, q(XHTML, "head"))
    ET.SubElement(head, q(XHTML, "title")).text = title
    ET.SubElement(
        head,
        q(XHTML, "link"),
        {"rel": "stylesheet", "type": "text/css", "href": "book.css"},
    )
    body = ET.SubElement(html, q(XHTML, "body"))
    body.text = parser.root.text
    body.extend(list(parser.root))
    return build_epub.xml_bytes(html), headings


def package_epub(out: Path, fragments: dict, manifest: dict) -> Path:
    """多文档 EPUB：约定与实际登记单元，spine 与 nav 同一顺序。"""
    import xml.etree.ElementTree as ET
    import zipfile

    build_epub = _epub_module()
    q = build_epub.q
    OPF, DC, EPUB = build_epub.OPF, build_epub.DC, build_epub.EPUB
    XHTML = build_epub.XHTML

    updated = manifest.get("updated", "2026-11-08")
    docs: list[tuple[str, str, str]] = [
        (
            "title",
            "扉页",
            book_introduction(len(manifest["units"])) + f"<p>登记日期：{updated}。</p>",
        ),
        ("conventions", "工程深研约定", fragments["conventions"]["html"]),
    ]
    docs.append(("prerequisites", "先修最小包", fragments["prerequisites"]["html"]))
    for unit in manifest["units"]:
        unit_id = unit["id"]
        if unit_id not in fragments:
            continue
        fragment = fragments[unit_id]
        docs.append(
            (unit_id.lower(), f"{unit_id}　{fragment['title']}", fragment["html"])
        )
    docs.append(("sources", "来源、实验与未闭合证据", fragments["sources"]["html"]))

    assets: dict[str, tuple[bytes, str]] = {}
    files: dict[str, bytes] = {}
    nav_entries: list[tuple[str, str, list[tuple[str, str]]]] = []
    manifest_items: list[tuple[str, str, str]] = []
    spine_ids: list[str] = []
    for doc_id, title, html in docs:
        data, headings = _epub_doc(build_epub, html, assets, title)
        name = f"EPUB/{doc_id}.xhtml"
        files[name] = data
        manifest_items.append((doc_id, f"{doc_id}.xhtml", "application/xhtml+xml"))
        spine_ids.append(doc_id)
        nav_entries.append((f"{doc_id}.xhtml", title, headings))

    nav = ET.Element(q(XHTML, "html"), {"lang": "zh-CN"})
    nav_head = ET.SubElement(nav, q(XHTML, "head"))
    ET.SubElement(nav_head, q(XHTML, "title")).text = "目录"
    nav_body = ET.SubElement(nav, q(XHTML, "body"))
    toc = ET.SubElement(
        nav_body, q(XHTML, "nav"), {q(EPUB, "type"): "toc", "id": "toc"}
    )
    ET.SubElement(toc, q(XHTML, "h1")).text = "目录"
    items = ET.SubElement(toc, q(XHTML, "ol"))
    for href, title, headings in nav_entries:
        li = ET.SubElement(items, q(XHTML, "li"))
        ET.SubElement(li, q(XHTML, "a"), {"href": href}).text = title
        if not headings:
            continue
        sub = ET.SubElement(li, q(XHTML, "ol"))
        for hid, htext in headings:
            if not htext:
                continue
            sub_li = ET.SubElement(sub, q(XHTML, "li"))
            ET.SubElement(sub_li, q(XHTML, "a"), {"href": f"{href}#{hid}"}).text = htext

    container = ET.Element(
        "container",
        {"xmlns": "urn:oasis:names:tc:opendocument:xmlns:container", "version": "1.0"},
    )
    rootfiles = ET.SubElement(container, "rootfiles")
    ET.SubElement(
        rootfiles,
        "rootfile",
        {
            "full-path": "EPUB/package.opf",
            "media-type": "application/oebps-package+xml",
        },
    )
    package = ET.Element(
        q(OPF, "package"), {"version": "3.0", "unique-identifier": "book-id"}
    )
    meta = ET.SubElement(package, q(OPF, "metadata"))
    ET.SubElement(
        meta, q(DC, "identifier"), {"id": "book-id"}
    ).text = "urn:bms-z:engineering:implemented-units"
    ET.SubElement(meta, q(DC, "title")).text = BOOK_TITLE
    ET.SubElement(meta, q(DC, "creator")).text = "BMS-Z contributors"
    ET.SubElement(meta, q(DC, "language")).text = "zh-CN"
    ET.SubElement(meta, q(DC, "rights")).text = "CC BY-SA 4.0；第三方图片按原授权"
    ET.SubElement(
        meta, q(OPF, "meta"), {"property": "dcterms:modified"}
    ).text = f"{updated}T00:00:00Z"
    manifest_el = ET.SubElement(package, q(OPF, "manifest"))
    for doc_id, href, mime in manifest_items:
        ET.SubElement(
            manifest_el,
            q(OPF, "item"),
            {"id": doc_id, "href": href, "media-type": mime},
        )
    ET.SubElement(
        manifest_el,
        q(OPF, "item"),
        {
            "id": "nav",
            "href": "nav.xhtml",
            "media-type": "application/xhtml+xml",
            "properties": "nav",
        },
    )
    ET.SubElement(
        manifest_el,
        q(OPF, "item"),
        {"id": "css", "href": "book.css", "media-type": "text/css"},
    )
    ET.SubElement(manifest_el, q(OPF, "item"), {
        "id": "cover-art", "href": "cover.jpg", "media-type": "image/jpeg", "properties": "cover-image",
    })
    for index, (name, (_, mime)) in enumerate(sorted(assets.items())):
        ET.SubElement(
            manifest_el,
            q(OPF, "item"),
            {"id": f"asset-{index}", "href": name, "media-type": mime},
        )
    spine = ET.SubElement(package, q(OPF, "spine"))
    for doc_id in spine_ids:
        ET.SubElement(spine, q(OPF, "itemref"), {"idref": doc_id})

    files["META-INF/container.xml"] = build_epub.xml_bytes(container)
    files["EPUB/package.opf"] = build_epub.xml_bytes(package)
    files["EPUB/nav.xhtml"] = build_epub.xml_bytes(nav)
    files["EPUB/book.css"] = (build_epub.CSS + COVER_CSS + GUIDE_CSS).encode()
    files["EPUB/cover.jpg"] = (ENGINEERING / "cover.jpg").read_bytes()
    for name, (payload, _) in assets.items():
        files[f"EPUB/{name}"] = payload

    problems = build_epub.validate_files(files)
    if problems:
        raise SystemExit("工程装配：EPUB 合同不过——\n- " + "\n- ".join(problems[:12]))
    target = out / "engineering.epub"
    temporary = target.with_suffix(".epub.tmp")
    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            ordered = [("mimetype", b"application/epub+zip"), *sorted(files.items())]
            for name, data in ordered:
                info = zipfile.ZipInfo(name, date_time=(2026, 11, 8, 0, 0, 0))
                info.compress_type = (
                    zipfile.ZIP_STORED if name == "mimetype" else zipfile.ZIP_DEFLATED
                )
                archive.writestr(info, data)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    problems = build_epub.validate_epub(target)
    if problems:
        raise SystemExit(
            "工程装配：EPUB 出厂校验不过——\n- " + "\n- ".join(problems[:12])
        )
    return target


def build(out: Path) -> dict:
    manifest = read_json(MANIFEST)
    claims = read_json(CLAIMS)["claims"]
    figures = read_json(FIGURES)["figures"]
    experiments = read_json(EXPERIMENTS)["experiments"]
    units = [
        u
        for u in manifest["units"]
        if u.get("status") == "locally_verified" and u.get("source")
    ]
    pending = {unit["id"]: unit for unit in units}
    ordered = []
    while pending:
        ready = [u for u in pending.values() if not (set(u.get("prerequisites", [])) & pending.keys())]
        if not ready:
            raise SystemExit("工程装配：先修存在循环")
        for unit in ready:
            ordered.append(unit)
            del pending[unit["id"]]
    units = ordered
    if not units:
        raise SystemExit("工程装配：登记里没有可装配的实际单元")

    for unit in units:
        source = ROOT / unit["source"]
        if not source.is_file():
            raise SystemExit(
                f"工程装配：{unit['id']} 正文源缺失 {unit['source']}（先回写登记表）"
            )

    node = shutil.which("node")
    if node is None:
        raise SystemExit("工程装配需要 Node.js（渲染走 VitePress 解析器）")
    rendered = subprocess.run(
        [node, str(RENDERER)],
        check=True,
        capture_output=True,
        encoding="utf-8",
        timeout=180,
    )
    try:
        payload = json.loads(rendered.stdout)
        fragments = {u["id"]: u for u in payload["units"]}
    except (KeyError, json.JSONDecodeError) as exc:
        detail = rendered.stderr.strip() or rendered.stdout[:400]
        raise SystemExit(
            f"工程装配：渲染器输出解析失败：{exc}；渲染器说：{detail}"
        ) from exc

    out.mkdir(parents=True, exist_ok=True)
    report: dict = {"units": {}, "figures_copied": []}

    # 图资产：登记过的文件复制到 assets/（EPUB 与来源核对用；单文件书本身内联）
    for figure in figures:
        if figure["unit"] not in {u["id"] for u in units}:
            continue
        src = ROOT / figure["file"]
        if not src.is_file():
            raise SystemExit(f"工程装配：{figure['id']} 的文件缺失 {figure['file']}")
        dest = out / "assets" / src.parent.name / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        report["figures_copied"].append(str(dest.relative_to(out)).replace("\\", "/"))

    # 实际登记单元沿先修拓扑装配，避免 D07 先于其 D03/D05 先修。
    book_docs: list[tuple[str, str, str]] = []
    conventions = fragments.get("conventions")
    if conventions:
        book_docs.append(("conventions", conventions["title"], conventions["html"]))
    book_docs.append(("prerequisites", "先修最小包", fragments["prerequisites"]["html"]))
    for unit in units:
        fragment = fragments[unit["id"]]
        levels = section_levels(unit, claims, experiments)
        body = tag_levels(fragment["html"], levels)
        for experiment in experiments:
            if experiment["unit"] == unit["id"]:
                body += (
                    f'<p class="evidence-link">实验 {escape(experiment["id"])}：'
                    f'<a href="sources.html#{experiment["id"].lower()}">入口、来源与验收边界</a></p>'
                )
        book_docs.append((unit["id"].lower(), f"{unit['id']}　{unit['title']}", body))
        src = ROOT / unit["source"]
        report["units"][unit["id"]] = {
            "title": unit["title"],
            "levels": unit.get("levels", []),
            "source": unit["source"],
            "source_sha256": sha256_file(src),
        }
    book_docs.append(("sources", "来源、实验与未闭合证据", fragments["sources"]["html"]))

    toc_items = []
    chapters = []
    for doc_id, title, html in book_docs:
        prefixed = prefix_ids(html, doc_id)
        subsections = "".join(
            f'<li><a href="#{cid}">{re.sub(r"<[^>]+>", "", heading)}</a></li>'
            for cid, heading in re.findall(r'<h2\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</h2>', prefixed, re.S)
        )
        unit_id, separator, name = title.partition("　")
        label = f'<span class="toc-code">{escape(unit_id)}</span> {escape(name)}' if separator else escape(title)
        disclosure = (
            f'<details><summary aria-label="{escape(title)}的小节">小节</summary>'
            f'<ol>{subsections}</ol></details>'
        ) if subsections else ""
        toc_items.append(
            f'<li><a class="toc-entry" href="#{doc_id}--toc">{label}</a>{disclosure}</li>'
        )
        if not re.search(r"<h1\b", prefixed):
            prefixed = f"<h1>{escape(title)}</h1>{prefixed}"
        chapters.append(f'<section class="book-chapter" id="{doc_id}--toc">{prefixed}</section>')
    book_body = (
        '<nav class="toc" aria-label="目录"><h2>目录</h2><ol>'
        + "".join(toc_items)
        + "</ol></nav>"
        + "".join(chapters)
    )
    # 单文件书没有“目录浏览”和跨页跳转：目录链接退化为纯文本，约定链改指书内锚
    book_body = re.sub(
        r'<a([^>]*?)href="\./assets/[^"]*?/"[^>]*>([\s\S]*?)</a>',
        r"<span\1>\2</span>",
        book_body,
    )
    for doc_id, _title, _html in book_docs:
        book_body = re.sub(
            rf'href="{doc_id}\.html(?:#([^"]+))?"',
            lambda m, uid=doc_id: f'href="#{uid}--{m[1] or "toc"}"',
            book_body,
        )
    book = book_html(BOOK_TITLE, add_static_posters(backfill_data_uri_dims(inline_images(book_body))),
                     book_introduction(len(units)))
    book = book.replace('<nav class="toc"', payload["search"]["html"] + '<nav class="toc"', 1)
    book = book.replace("</body>", "<script>" + payload["search"]["script"] + "</script>\n</body>", 1)
    (out / "engineering-book.html").write_text(book, encoding="utf-8")
    for unit in units:
        report["units"][unit["id"]]["book_chars"] = len(book)
    verify_spine(book, out)

    report_path = out / "build-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    verify_publication(out)
    epub_path = package_epub(out, fragments, {**manifest, "units": units})
    report["epub"] = epub_path.name
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(ENGINEERING / "dist"), help="输出目录")
    parser.add_argument(
        "--pdf", action="store_true", help="额外打印 PDF（无头 Chrome/Edge）"
    )
    parser.add_argument("--check", metavar="DIST", help="只对已构建产物跑出版门")
    args = parser.parse_args()
    if args.check:
        verify_publication(Path(args.check))
        print(f"engineering publication gate ok: {args.check}")
        return 0
    out = Path(args.out)
    report = build(out)
    printed = print_pdfs(out) if args.pdf else []
    print(
        f"engineering book ok: {len(report['units'])} units, "
        f"{report['units'].get('S1', {}).get('book_chars', 0)} chars, "
        f"{len(report['figures_copied'])} figures inlined"
        + (f", {len(printed)} PDF" if printed else "")
        + f" -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
