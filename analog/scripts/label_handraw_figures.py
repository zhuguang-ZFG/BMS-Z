#!/usr/bin/env python3
"""给 figures-v2 的 handraw 手绘血统补齐无障碍与技术标记。

Task 5 的 overlay 合成（`technical-overlay-v1`）自带 title/desc；2026-11-05 起
经用户授权新增 `python-handraw-v1` 血统：场景脚本直接画纸面皮肤整图，历来缺
`<title>`/`<desc>`/`data-composition`。本工具从各图在
`docs/superpowers/visual/reviews/**` 的 composition JSON（title 与 alt 与
manifest 同源）把这些标记补进 SVG 根元素，只动元数据、不动任何图面字节，
幂等可重跑（波次重建后需要再跑一次）。

用法：`python scripts/label_handraw_figures.py`（--check 只报告不落盘）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from html import escape
from pathlib import Path

from defusedxml import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "assets" / "figures-v2"
REVIEWS = ROOT / "docs" / "superpowers" / "visual" / "reviews"
MARKER = "python-handraw-v1"
SVG_NS = "{http://www.w3.org/2000/svg}"


def load_specs() -> dict[str, dict]:
    specs: dict[str, dict] = {}
    for path in REVIEWS.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        out = data.get("output") or ""
        if out.startswith("assets/figures-v2/") and data.get("title") and data.get("alt"):
            stem = Path(out).stem
            if stem not in specs or path.stat().st_size >= specs[stem]["_path"].stat().st_size:
                data["_path"] = path
                specs[stem] = data
    return specs


def label(raw: str, spec: dict) -> str:
    open_tag = re.search(r"<svg\b[^>]*>", raw)
    if not open_tag:
        raise ValueError("缺少 <svg> 起始标签")
    tag = open_tag.group(0)
    if "data-composition" in tag:
        return raw
    closing = "/>" if tag.endswith("/>") else ">"
    attrs = tag[:-len(closing)]
    existing_ids = set(re.findall(r'\bid="([^"]+)"', raw))
    title_id = "title" if "title" not in existing_ids and "desc" not in existing_ids else "fig-title"
    desc_id = "title".replace("title", "desc") if title_id == "title" else "fig-desc"
    labelled = (' role="img" aria-labelledby="%s %s"' % (title_id, desc_id)
                if "role=" not in attrs else "")
    new_tag = (f'<svg{attrs[4:]} data-composition="{MARKER}"{labelled}{closing}\n'
               f'<title id="{title_id}">{escape(spec["title"])}</title>'
               f'<desc id="{desc_id}">{escape(spec["alt"])}</desc>')
    return raw[:open_tag.start()] + new_tag + raw[open_tag.end():]


def preserve_review_for_labels(asset: dict, before: str, after: str, spec: dict) -> bool:
    """Carry a review only across the exact nonvisual label() transformation."""
    record = asset.get('review_record') or {}
    old_hash = hashlib.sha256(before.replace('\r\n', '\n').encode()).hexdigest()
    if asset.get('status') not in {'accepted', 'published'} or record.get('asset_sha256') != old_hash:
        return False
    expected = label(before, spec)
    if expected != after:
        return False
    new_hash = hashlib.sha256(after.replace('\r\n', '\n').encode()).hexdigest()
    record.setdefault('metadata_amendments', []).append({
        'before_sha256': old_hash, 'after_sha256': new_hash,
        'method': 'label_handraw_figures.label: exact title/desc/root-attribute insertion; drawing bytes unchanged',
    })
    record['asset_sha256'] = new_hash
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="只报告待标定文件，不写入")
    args = ap.parse_args(argv)

    specs = load_specs()
    import check_visual_manifest as manifest
    data = manifest.load()
    by_output = {a['output']: a for a in data['assets']}
    amended = 0
    changed: list[Path] = []
    unlabelled: list[Path] = []
    missing: list[str] = []
    for path in sorted(FIGURES.glob("*.svg")):
        root = ET.parse(path).getroot()
        if root is None:
            raise ValueError(f"SVG 缺少根元素: {path}")
        if root.get("data-composition"):
            continue
        stem = re.sub(r"-print$", "", path.stem)
        spec = specs.get(stem)
        if spec is None:
            missing.append(path.name)
            continue
        raw = path.read_text(encoding="utf-8")
        out = label(raw, spec)
        if out == raw:
            unlabelled.append(path)
            continue
        probe = ET.fromstring(out)
        assert probe.find(f"{SVG_NS}title") is not None
        assert probe.find(f"{SVG_NS}desc") is not None
        changed.append(path)
        if not args.check:
            asset = by_output.get(path.relative_to(ROOT).as_posix())
            if asset is not None:
                amended += preserve_review_for_labels(asset, raw, out, spec)
            path.write_text(out, encoding="utf-8")

    if amended:
        manifest.dump(data)
        print(f"保留 {amended} 份原图审阅；逐项记录仅元数据变更的前后哈希。")
    print(f"handraw 标定：{len(changed)} 个文件"
          f"{'（--check 未落盘）' if args.check else ''}")
    if missing:
        print(f"缺 composition JSON：{len(missing)} 个: {missing[:10]}")
    if unlabelled:
        print(f"已带标记被跳过：{len(unlabelled)} 个")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
