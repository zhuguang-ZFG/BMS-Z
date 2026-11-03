#!/usr/bin/env python3
"""把 tools/spread/decks/<slug>/ 装配成单文件网页 PPT（含讲稿）。

源：decks/<slug>/slides.html（只写 <section class="slide"> 段落）
    decks/<slug>/notes.js（SPEAKER_NOTES 数组，顺序与 slides 一致）
    decks/<slug>/deck.json（可选：需要复制进产物的图，从仓库内引用）
产物：docs/public/spread/deck/<slug>.html

模板与演讲者模式运行时来自 guizang-ppt-skill（环境变量 GUIZANG_PPT_SKILL 可覆盖）。

用法：
    python tools/spread/build_deck.py 07-protection-tick
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "tools" / "spread" / "decks"
OUT_DIR = ROOT / "docs" / "public" / "spread" / "deck"
SKILL_DIR = Path(
    os.environ.get(
        "GUIZANG_PPT_SKILL",
        Path.home() / ".agents" / "skills" / "guizang-ppt-skill",
    )
)

NOTES_RE = re.compile(r"const SPEAKER_NOTES = \[.*?\n\];\nwindow\.__SPEAKER_NOTES__ = SPEAKER_NOTES;", re.S)


def build(slug: str) -> None:
    src = SRC_ROOT / slug
    slides_path = src / "slides.html"
    notes_path = src / "notes.js"
    for p in (slides_path, notes_path):
        if not p.exists():
            raise SystemExit(f"缺少源文件：{p}")

    template = SKILL_DIR / "assets" / "template.html"
    if not template.exists():
        raise SystemExit(f"找不到 PPT 模板：{template}")

    html = template.read_text(encoding="utf-8")
    if "<!-- SLIDES_HERE -->" not in html:
        raise SystemExit("模板缺少 SLIDES_HERE 占位")
    html = html.replace("<!-- SLIDES_HERE -->", slides_path.read_text(encoding="utf-8"), 1)

    notes = notes_path.read_text(encoding="utf-8").strip()
    if not NOTES_RE.search(html):
        raise SystemExit("模板里找不到 SPEAKER_NOTES 区块")
    html = NOTES_RE.sub(lambda m: notes, html, count=1)

    cfg_path = src / "deck.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    assets = cfg.get("assets") or {}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for dest, rel in assets.items():
        source = (ROOT / rel).resolve()
        if not source.exists():
            raise SystemExit(f"deck.json 引用的素材不存在：{rel}")
        target = OUT_DIR / "assets" / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    out = OUT_DIR / f"{slug}.html"
    out.write_text(html, encoding="utf-8")
    slides = html.count('class="slide')
    print(f"docs/public/spread/deck/{slug}.html  {out.stat().st_size:,} bytes · {slides} slides")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slug")
    args = ap.parse_args()
    build(args.slug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
