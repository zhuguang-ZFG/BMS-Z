#!/usr/bin/env python3
"""改写正文后，确认没有把图依赖的数字弄丢。

正文小节同时是插图的事实来源：`visual-manifest.yml` 的 `source_facts` 指向
`docs/pX-YY-chN.md#A.B`，`scripts/visual_fidelity.py` 要求图上每个数字 token
都逐字出现在该小节原文里。改写句子可以拆长句、换措辞，但一旦删掉某个数字，
对应的图就失去来源。

本脚本对比工作区与某个 git 版本（默认 HEAD），报告：
  1. 被图引用的小节里消失的数字 token —— 必须为空；
  2. 受影响的图 id，方便定位。

用法：
    python scripts/check_prose_safety.py              # 对比 HEAD
    python scripts/check_prose_safety.py --ref main
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "docs" / "superpowers" / "visual" / "visual-manifest.yml"

sys.path.insert(0, str(ROOT / "scripts"))
from visual_fidelity import source_excerpt  # noqa: E402

NUM = re.compile(r"\d+(?:\.\d+)?")


def git_show(ref: str, path: str) -> str | None:
    r = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT,
                       capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", "replace")


def excerpt_from_text(text: str, anchor: str) -> str:
    """复刻 source_excerpt 的切段规则，但作用在给定文本上。"""
    lines = text.splitlines()
    start = None
    depth = 0
    for i, line in enumerate(lines):
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if not m:
            continue
        head = m.group(2)
        if start is None:
            if re.match(rf"^{re.escape(anchor)}(\s|$|[^\d.])", head):
                start = i
                depth = len(m.group(1))
            continue
        if len(m.group(1)) <= depth:
            return "\n".join(lines[start : i])
    if start is None:
        return ""
    return "\n".join(lines[start:])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", default="HEAD")
    args = ap.parse_args(argv)

    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}
    used: dict[str, list[str]] = defaultdict(list)
    for a in data.get("assets") or []:
        for s in a.get("source_facts") or []:
            used[s].append(a["id"])

    problems = 0
    checked = 0
    for ref_spec, ids in sorted(used.items()):
        if "#" not in ref_spec:
            continue
        rel, anchor = ref_spec.split("#", 1)
        now_path = ROOT / rel
        if not now_path.exists():
            print(f"FAIL 文件不存在 {rel}（图：{', '.join(ids)}）")
            problems += 1
            continue
        old_text = git_show(args.ref, rel)
        if old_text is None:
            continue
        old = excerpt_from_text(old_text, anchor)
        if not old:
            continue
        try:
            new = source_excerpt(ROOT, ref_spec)
        except Exception as exc:  # 小节标题被改掉也算缺陷
            print(f"FAIL 取不到小节 {ref_spec}：{exc}（图：{', '.join(ids)}）")
            problems += 1
            continue
        checked += 1
        lost = [t for t in dict.fromkeys(NUM.findall(old)) if t not in new]
        if lost:
            problems += 1
            print(f"FAIL {ref_spec} 丢失数字 {lost}")
            print(f"     受影响的图：{', '.join(ids)}")

    print(f"\n对比 {args.ref}：检查 {checked} 个被图引用的小节，"
          f"{'无缺陷' if not problems else f'{problems} 项缺陷'}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
