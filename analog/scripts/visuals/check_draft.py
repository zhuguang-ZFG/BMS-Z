#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新图底稿自检：视图框、标题/描述、文字越界、离线与调色板。

用法：`python scripts/visuals/check_draft.py assets/figures/ch17-xxx.svg`
底稿不含纸面层（`static_fig.py finalize` 注入）；本检查只判定内容层。
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import handraw  # noqa: E402
from test_figures import _extent_violations  # noqa: E402

# #1e293b 是模板标题行的约定色，finalize 的 retint 会换成墨色 token。
ALLOWED = {v.lower() for v in handraw.LIGHT.values()} | {
    "#ffffff", "#1e293b", "none", "transparent"}
COLOR_ATTR = re.compile(r'\b(fill|stroke|stop-color|flood-color)="([^"]+)"')
FORBIDDEN = ("<script", "<image", "<foreignObject")
EXTERNAL = re.compile(r'(?:href|src)\s*=\s*["\']https?://', re.I)
MIN_TEXT = 6


def check(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    issues = [f"{path.name}: 含 {needle}" for needle in FORBIDDEN
              if needle.lower() in text.lower()]
    if EXTERNAL.search(text):
        issues.append(f"{path.name}: 含外部链接")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return issues + [f"{path.name}: XML 解析失败 {exc}"]
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', text)
    if not vb:
        issues.append(f"{path.name}: viewBox 必须是 '0 0 W H'")
    elif (float(vb.group(1)), float(vb.group(2))) != (960.0, 680.0):
        issues.append(f"{path.name}: viewBox 需为 960x680，实为 "
                      f"{vb.group(1)}x{vb.group(2)}")
    if root.find("{http://www.w3.org/2000/svg}title") is None:
        issues.append(f"{path.name}: 缺 <title id=\"figTitle\">")
    if root.find("{http://www.w3.org/2000/svg}desc") is None:
        issues.append(f"{path.name}: 缺 <desc id=\"figDesc\">")
    if text.count("<text") < MIN_TEXT:
        issues.append(f"{path.name}: <text> 少于 {MIN_TEXT} 个")
    for m in COLOR_ATTR.finditer(text):
        val = m.group(2).strip().lower()
        if val.startswith("url(") or val in ALLOWED:
            continue
        issues.append(f"{path.name}: 非 token 色值 {m.group(1)}=\"{m.group(2)}\"")
    issues.extend(f"{path.name}: {v}" for v in _extent_violations(path))
    return issues


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    total = 0
    for name in args:
        for line in check(Path(name)):
            print("FAIL " + line)
            total += 1
    print(f"draft check: {'FAIL' if total else 'PASS'}（{total} 项）")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
