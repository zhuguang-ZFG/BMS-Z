#!/usr/bin/env python3
"""把 tools/spread/cards/<slug>/ 渲染成 3:4 传播卡（小红书图文）。

源：cards/<slug>/posters.html（只写 <section class="poster xhs"> 段落）
    cards/<slug>/card.json（主题 + 需要的图，图从仓库内其它位置引用，不复制）
产物：docs/public/spread/cards/<slug>/*.png（1080×1440）

渲染在 .tmp-cardbuild/ 里进行，仓库不留中间文件；主题与模板来自
guizang-social-card-skill（环境变量 GUIZANG_SOCIAL_SKILL 可覆盖）。

用法：
    python tools/spread/build_cards.py 07-protection-tick [--validate]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "tools" / "spread" / "cards"
OUT_ROOT = ROOT / "docs" / "public" / "spread" / "cards"
SKILL_DIR = Path(
    os.environ.get(
        "GUIZANG_SOCIAL_SKILL",
        Path.home() / ".agents" / "skills" / "guizang-social-card-skill",
    )
)

from spread_css import TASK_CSS  # noqa: E402


def build(slug: str, validate: bool) -> None:
    src = SRC_ROOT / slug
    posters_path = src / "posters.html"
    config_path = src / "card.json"
    for p in (posters_path, config_path):
        if not p.exists():
            raise SystemExit(f"缺少源文件：{p}")

    template = SKILL_DIR / "assets" / "template-editorial-card.html"
    if not template.exists():
        raise SystemExit(f"找不到 social-card 模板：{template}")

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    theme = cfg.get("theme", "ink-classic")

    work = ROOT / ".tmp-cardbuild" / slug
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    for dest, rel in (cfg.get("assets") or {}).items():
        source = (ROOT / rel).resolve()
        if not source.exists():
            raise SystemExit(f"card.json 引用的素材不存在：{rel}")
        (work / "assets").mkdir(exist_ok=True)
        shutil.copy2(source, work / "assets" / dest)

    html = template.read_text(encoding="utf-8")
    head, rest = html.rsplit("<!-- POSTERS_HERE -->", 1)
    _, _, tail = rest.partition("</main>")
    out = head + posters_path.read_text(encoding="utf-8") + "\n  </main>" + tail
    out = out.replace("</head>", "  <style>" + TASK_CSS + "  </style>\n</head>", 1)
    out = out.replace('data-theme="ink-classic"', f'data-theme="{theme}"', 1)
    (work / "index.html").write_text(out, encoding="utf-8")

    print(f"→ 渲染 {slug}")
    subprocess.run(
        ["node", str(SKILL_DIR / "scripts" / "render.mjs"), str(work)],
        cwd=str(SKILL_DIR),
        check=True,
    )

    out_dir = OUT_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    pngs = sorted((work / "output").glob("*.png"))
    if not pngs:
        raise SystemExit("渲染没有产出 PNG")
    for png in pngs:
        shutil.copy2(png, out_dir / png.name)
        print(f"  docs/public/spread/cards/{slug}/{png.name}  {png.stat().st_size:,} bytes")

    if validate:
        print(f"→ 校验 {slug}")
        subprocess.run(
            ["node", str(SKILL_DIR / "validate-social-deck.mjs"), str(work)],
            cwd=str(SKILL_DIR),
            check=True,
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slug", help="cards 下的任务目录名")
    ap.add_argument("--validate", action="store_true", help="渲染后跑 validate-social-deck")
    args = ap.parse_args()
    build(args.slug, args.validate)
    return 0


if __name__ == "__main__":
    sys.exit(main())
