#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成视觉接触表：一页看 12~24 张图，带 manifest 元数据与评分栏。

用法：
  python scripts/build_visual_contact_sheet.py --wave ch17 \
      --out docs/superpowers/visual/reviews/contact-ch17.html
不指定 --wave 时收录 manifest 里所有非 legacy 的 figure 条目。
"""
from __future__ import annotations

import argparse
import html
import os
import sys
from pathlib import Path

import yaml
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "superpowers" / "visual" / "visual-manifest.yml"
DIMS = ["教学必要性", "事实精度", "构图层级", "风格一致性", "印刷可读性"]

CSS = """body{background:#f6eedb;color:#16202b;font-family:"Segoe UI",
"Microsoft YaHei",sans-serif;margin:24px}
h1{font-size:20px;margin:0 0 4px}p.lead{color:#5b666f;margin:0 0 20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,430px),1fr));
gap:18px}
figure{margin:0;background:#fffdf8;border:1px solid #e0d3b8;border-radius:12px;
padding:12px}
figure img{width:100%;height:auto;display:block;border-radius:8px}
figcaption{font-size:13px;line-height:1.5;margin-top:8px}
.meta{color:#5b666f;font-size:12px;margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:12px;margin-top:8px}
td,th{border:1px solid #e0d3b8;padding:2px 6px;text-align:center}
.gray{filter:grayscale(1)}.page{break-after:page;margin-bottom:36px}
.pending{padding:32px;border:1px dashed #5b666f}.proof{color:#a4441d;font-weight:bold}
"""


def rel(path: Path, destination: Path) -> str:
    return quote(Path(os.path.relpath(path.resolve(), destination.resolve().parent)).as_posix())


def card(asset: dict, destination: Path, grayscale=False) -> str:
    proof = asset.get("technical_proof")
    source = proof or (asset.get("reduced_motion") if asset.get("kind") == "animation" else None) or asset.get("output")
    out = ROOT / source if source else None
    title = asset.get("purpose") or asset.get("alt") or asset["id"]
    dims = DIMS + (["运动叙事", "交互节奏"] if asset.get("kind") == "animation" else [])
    rows = "".join(f"<th>{d}</th>" for d in dims)
    cells = "".join(f"<td>{html.escape(str((asset.get('review_scores') or {}).get(d, '待评')))}</td>" for d in dims)
    image = (f'<img src="{rel(out, destination)}" alt="{html.escape(title)}">'
             if out and out.is_file() else '<p class="pending">待生成底图</p>')
    if grayscale and out and out.is_file():
        image += f'<img class="gray" src="{rel(out, destination)}" alt="灰度对照：{html.escape(title)}">'
    if proof:
        image = '<p class="proof">仅技术校样 · 底图未生成 · 未通过风格复评</p>' + image
    return f"""<figure>
{image}
<figcaption><b>{html.escape(asset['id'])}</b> · {html.escape(title)}
<div class="meta">ch{asset['chapter']} · {html.escape(asset['type'])} · {html.escape(asset['layout_id'])}
 · {html.escape(asset['status'])}</div>
<table><tr>{rows}</tr><tr>{cells}</tr></table></figcaption>
</figure>"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wave", default="", help="只收 id 以该前缀开头的条目")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, default=MANIFEST)
    ap.add_argument("--grayscale", action="store_true")
    ap.add_argument("--page-size", type=int, choices=(12, 18, 24), default=18)
    args = ap.parse_args(argv)
    data = yaml.safe_load(args.manifest.read_text(encoding="utf-8")) or {}
    assets = [a for a in data.get("assets") or []
              if a.get("kind") in ("figure", "animation")
              and a.get("status") != "legacy-unreviewed"
              and a.get("id", "").startswith(args.wave)]
    pages = []
    for start in range(0, len(assets), args.page_size):
        cards = "\n".join(card(a, args.out, args.grayscale) for a in assets[start:start + args.page_size])
        pages.append(f"<section class='page'><div class='grid'>{cards}</div></section>")
    doc = (f"<!doctype html><html lang='zh-CN'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>视觉接触表 "
           f"{html.escape(args.wave)}</title><style>{CSS}</style>"
           f"<h1>视觉接触表 · {html.escape(args.wave or '全部新图')}"
           f"（{len(assets)} 张）</h1>"
           f"<p class='lead'>逐项打 1–5 分；任一维度 &lt;4 返工。"
           f"评分回填 visual-manifest.yml 的 review_scores。</p>"
           + "\n".join(pages) + "</html>\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(doc, encoding="utf-8")
    print(f"{len(assets)} 张 → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
