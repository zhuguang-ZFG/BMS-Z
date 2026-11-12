#!/usr/bin/env python3
"""把 book/shared/ 的四篇共享卷首渲染成两卷产物共用的 HTML（设计 P4）。

只支持卷首用到的 Markdown 子集：标题、段落、引用、列表、粗体与行内代码。
不引入 Markdown 依赖——BMS 构建环境只装 numpy/pymupdf/pillow。
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book"
MANIFEST = BOOK / "manifest.json"


def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def _markdown(text: str) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []
    items: list[str] = []
    ordered = False

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(f"<p>{_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_list() -> None:
        if items:
            tag = "ol" if ordered else "ul"
            blocks.append(f"<{tag}>" + "".join(f"<li>{_inline(item)}</li>" for item in items)
                          + f"</{tag}>")
            items.clear()

    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        if not line:
            flush_paragraph()
            flush_list()
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", line)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            continue
        if line.strip() == "---":
            flush_paragraph()
            flush_list()
            blocks.append("<hr>")
            continue
        bullet = re.match(r"^[-*]\s+(.*)$", line)
        number = re.match(r"^\d+\.\s+(.*)$", line)
        if bullet or number:
            flush_paragraph()
            next_ordered = bool(number)
            if items and next_ordered != ordered:
                flush_list()
            ordered = next_ordered
            items.append((bullet or number).group(1))
            continue
        if line.startswith(">"):
            flush_paragraph()
            flush_list()
            blocks.append(f"<blockquote><p>{_inline(line[1:].strip())}</p></blockquote>")
            continue
        flush_list()
        paragraph.append(line.strip())
    flush_paragraph()
    flush_list()
    return "\n".join(blocks)


def render() -> str:
    root = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sections = []
    for entry in root.get("shared_front_matter", []):
        path = (ROOT / entry["file"]).resolve()
        if not path.is_file() or not path.is_relative_to(BOOK / "shared"):
            raise RuntimeError(f"共享卷首文件缺失或越界：{entry['file']}")
        stem = path.stem
        body = _markdown(path.read_text(encoding="utf-8"))
        sections.append(
            f'<section class="shared-front-page" id="shared-{html.escape(stem)}" '
            f'data-title="{html.escape(entry["title"], quote=True)}" '
            'style="break-before: page; break-after: page">'
            f'<div class="md-typeset">\n{body}\n</div></section>')
    return "\n".join(sections)
