#!/usr/bin/env python3
"""把 book/glossary.md 渲染成印刷/单文件 HTML 里的共享术语表（设计 §10.1）。"""
from __future__ import annotations

import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "book" / "glossary.md"


def rows() -> list[list[str]]:
    rows = []
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().replace("\\|", "|")
                 for cell in line.strip().strip("|").split("|")]
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        rows.append(cells)
    return rows


def render() -> str:
    data = rows()
    header = "".join(f"<th>{html.escape(cell)}</th>" for cell in data[0])
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>"
        for row in data[1:]
    )
    return (
        '<h2 id="shared-glossary">共享术语表（卷一 + 卷二）</h2>'
        f'<p>两卷合并共 {len(data) - 1} 条；定义以各卷正文为准，'
        "「相关条目」只做导航。分册收录完整表，单卷读者也能查到另一卷的术语。</p>"
        f'<table class="shared-glossary"><caption>表 S-1　两卷共享术语</caption>'
        f"<thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>"
    )
