#!/usr/bin/env python3
"""章节契约静态扫描：六槽 / 口诀 / hero 图 / 数值例 / 验收清单。

用法：python scripts/check_chapter_contract.py docs/p1-02-ch1.md [more.md ...]
任一章五字段非全 True 时退出码为 1。
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path

SLOTS = ("hook", "intuition", "quant", "limits", "lab", "selfcheck")
# 每槽的中文标题候选（章内出现任一即算该槽在场）
SLOT_TITLE_HINTS = {
    "hook": ("钩子", "现象"),
    "intuition": ("直觉",),
    "quant": ("定量",),
    "limits": ("失效", "边界"),
    "lab": ("动手", "验证"),
    "selfcheck": ("自检",),
}
ASSET_REF = re.compile(r"assets/(?:figures|svg)(?:-v2)?/[^\s\"')\]]+")
UNIT_NUM = re.compile(
    r"\d[\d.,]*\s*(?:[kKMmµunp]?(?:Ω|ohm|Ohm|V|A|F|H|Hz|s|W|%)|kHz|MHz|ms|µs|us|ns|kΩ|MΩ|mV|mA|µA|µF|nF|pF)"
)
CHECKBOX = re.compile(r"^\s*- \[ \]")


def _slot_present(text: str, slot: str) -> bool:
    if f"<!-- slot:{slot} -->" in text or f"<!-- slot:{slot}-->" in text:
        return True
    return any(h in text for h in SLOT_TITLE_HINTS[slot])


def scan_chapter(path) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()

    slots = all(_slot_present(text, s) for s in SLOTS)

    motto = ("> **口诀**" in text) or ("> **一点就懂**" in text)

    asset_lines = [i for i, ln in enumerate(lines) if ASSET_REF.search(ln)]
    has_fig_q = any("**图问**" in ln for ln in lines)
    near_question = any(
        "？" in lines[j] or "?" in lines[j]
        for i in asset_lines
        for j in range(max(0, i - 2), min(len(lines), i + 3))
    )
    hero_fig = bool(asset_lines) and (has_fig_q or near_question)

    numeric_example = ("**算一笔**" in text) or any(
        (("=" in ln) or ("≈" in ln)) and UNIT_NUM.search(ln) for ln in lines
    )

    acceptance = False
    for i, ln in enumerate(lines):
        if ln.strip().startswith("### 验收清单"):
            window = []
            for sub in lines[i + 1:]:
                if sub.startswith("#"):
                    break
                window.append(sub)
            if sum(1 for w in window if CHECKBOX.match(w)) >= 2:
                acceptance = True
            break

    return {
        "slots": slots,
        "motto": motto,
        "hero_fig": hero_fig,
        "numeric_example": numeric_example,
        "acceptance": acceptance,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", type=Path)
    args = ap.parse_args()
    code = 0
    for p in args.paths:
        result = scan_chapter(p)
        ok = all(result.values())
        print(f"{p}: {'OK' if ok else 'FAIL'} {result}")
        if not ok:
            code = 1
    return code


if __name__ == "__main__":
    raise SystemExit(main())
