#!/usr/bin/env python3
"""把 tools/spread/<slug>.md 渲染成站点可访问的一页纸传播物。

流程：归藏 page 渲染器（md + annotations.json → 单文件 HTML）→ 页脚补溯源 →
Chrome 导出 PDF 与长图 → 落到 docs/public/spread/。
源稿在 tools/spread/，产物在 docs/public/spread/，两者都不进入书内图号链。

依赖：Node 18+、guizang-page-skill（含其 node_modules 里的 puppeteer-core）。

用法：
    python tools/spread/build.py 07-protection-tick
    python tools/spread/build.py --all
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "tools" / "spread"
OUT_DIR = ROOT / "docs" / "public" / "spread"
SKILL_DIR = Path(
    os.environ.get(
        "GUIZANG_PAGE_SKILL",
        Path.home() / ".agents" / "skills" / "guizang-page-skill",
    )
)

PRECONNECT_RE = re.compile(r'\n?<link rel="preconnect" href="https://fonts\.(?:googleapis|gstatic)\.com"[^>]*>')
FOOTER_RE = re.compile(r"<footer><p>(.*?)</p></footer>")


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)


def render_slug(slug: str) -> Path:
    md = SRC_DIR / f"{slug}.md"
    anno = SRC_DIR / f"{slug}.annotations.json"
    for p in (md, anno):
        if not p.exists():
            raise SystemExit(f"缺少源文件：{p}")
    if not (SKILL_DIR / "scripts" / "render.mjs").exists():
        raise SystemExit(
            f"找不到 guizang-page-skill：{SKILL_DIR}\n"
            "用环境变量 GUIZANG_PAGE_SKILL 指向技能目录"
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = ROOT / ".tmp-spread"
    tmp.mkdir(exist_ok=True)
    html = tmp / f"{slug}.html"

    print(f"→ 渲染 {slug}")
    run(
        [
            "node",
            str(SKILL_DIR / "scripts" / "render.mjs"),
            str(md),
            str(anno),
            str(html),
            "--style",
            "magazine",
            "--theme",
            "forest-ink",
            "--embed",
        ],
        cwd=SKILL_DIR,
    )

    # 字体内置后，模板里的 preconnect 提示已经没有用途，留着会在打开页面时
    # 先连一次 fonts.googleapis.com；删掉它，产物才算真正离线可读。
    text = html.read_text(encoding="utf-8")
    text = PRECONNECT_RE.sub("", text)
    html.write_text(text, encoding="utf-8")

    # 页脚补溯源：保留技能署名，接上本书出处与日期。
    m = re.match(r"(\d+)", slug)
    chapter = str(int(m.group(1))) if m else slug
    origin = f"内容对应《BMS-Z 电池管理系统》第 {chapter} 章"
    if FOOTER_RE.search(text):
        text = FOOTER_RE.sub(
            lambda m: f"<footer><p>{m.group(1)} · {origin}</p></footer>", text
        )
        html.write_text(text, encoding="utf-8")

    print(f"→ 导出 PDF 与长图 {slug}")
    pdf = OUT_DIR / f"{slug}.pdf"
    png = OUT_DIR / f"{slug}.png"
    run(
        [
            "node",
            str(SKILL_DIR / "scripts" / "export.mjs"),
            str(html),
            "--pdf",
            str(pdf),
            "--png",
            str(png),
            "--width",
            "900",
            "--scale",
            "2",
        ],
        cwd=SKILL_DIR,
    )

    shutil.copy2(html, OUT_DIR / f"{slug}.html")
    for p in (OUT_DIR / f"{slug}.html", pdf, png):
        print(f"  {p.relative_to(ROOT)}  {p.stat().st_size:,} bytes")
    return html


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slug", nargs="?", help="源稿名，不含扩展名")
    ap.add_argument("--all", action="store_true", help="构建 tools/spread 下全部源稿")
    args = ap.parse_args()

    if args.all:
        slugs = sorted(p.stem for p in SRC_DIR.glob("*.md"))
    elif args.slug:
        slugs = [args.slug]
    else:
        ap.error("需要 <slug> 或 --all")

    for slug in slugs:
        render_slug(slug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
