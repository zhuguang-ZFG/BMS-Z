#!/usr/bin/env python3
"""轻量文档一致性：SVG 数量、关键 code 路径、Markdown 相对文件链接存在性。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


def main() -> int:
    assets = ROOT / "docs" / "circuits" / "assets"
    svgs = list(assets.glob("*.svg"))
    if len(svgs) != 20:
        print(f"FAIL: expected 20 SVGs in {assets}, found {len(svgs)}")
        return 1
    print(f"ok: {len(svgs)} SVGs")

    for rel in ("code/soc", "code/protocol", "code/firmware", "code/README.md"):
        if not (ROOT / rel).exists():
            print(f"FAIL: missing {rel}")
            return 1
    print("ok: code packages present")

    missing: list[str] = []
    checked = 0
    for md in ROOT.rglob("*.md"):
        if ".git" in md.parts:
            continue
        text = md.read_text(encoding="utf-8")
        for _label, raw in LINK_RE.findall(text):
            url = raw.strip().split()[0]
            if url.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_part = url.split("#", 1)[0]
            if not path_part:
                continue
            target = (md.parent / path_part).resolve()
            try:
                target.relative_to(ROOT)
            except ValueError:
                continue
            checked += 1
            if not target.exists():
                missing.append(f"{md.relative_to(ROOT).as_posix()}: {url}")

    if missing:
        print("FAIL: broken relative links:")
        print("\n".join(missing[:50]))
        return 1
    print(f"ok: {checked} relative file links exist")
    return 0


if __name__ == "__main__":
    sys.exit(main())
