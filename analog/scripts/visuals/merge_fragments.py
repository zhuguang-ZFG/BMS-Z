#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把子代理产出的 manifest 片段合并进 visual-manifest.yml（按 id 去重）。"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "superpowers" / "visual" / "visual-manifest.yml"


def main(argv: list[str] | None = None) -> int:
    paths = [Path(a) for a in (argv or sys.argv[1:])]
    if not paths:
        paths = sorted((ROOT / ".tmp").glob("frag-*.yml"))
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assets = data.setdefault("assets", [])
    known = {a.get("id") for a in assets}
    added = 0
    for path in paths:
        for entry in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            if entry.get("id") in known:
                print(f"skip {entry.get('id')}（已存在）")
                continue
            assets.append(entry)
            known.add(entry.get("id"))
            added += 1
            print(f"add  {entry.get('id')}")
    if added:
        MANIFEST.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100),
            encoding="utf-8")
    print(f"merged {added} 条，共 {len(assets)} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
