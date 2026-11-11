#!/usr/bin/env python3
from __future__ import annotations
import argparse
import re
from pathlib import Path

FAKE_CONTRAST = re.compile(r"不是[^。；\n]{0,40}而是|与其说[^。；\n]{0,40}不如说")
EMPTY_PHRASES = ("值得注意的是", "在本章中我们将", "综上所述", "总而言之，")


def scan_text(text: str, whitelist: list[str]) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        if any(w and w in line for w in whitelist):
            continue
        if FAKE_CONTRAST.search(line):
            hits.append((i, line.strip()))
        for p in EMPTY_PHRASES:
            if p in line:
                hits.append((i, line.strip()))
    return hits


def load_whitelist(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [ln[2:].strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.startswith("- ")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--whitelist", type=Path,
                    default=Path("docs/superpowers/templates/humanizer-whitelist.md"))
    args = ap.parse_args()
    wl = load_whitelist(args.whitelist)
    code = 0
    for p in args.paths:
        for ln, s in scan_text(p.read_text(encoding="utf-8"), wl):
            print(f"{p}:{ln}: {s}")
            code = 1
    return code


if __name__ == "__main__":
    raise SystemExit(main())
