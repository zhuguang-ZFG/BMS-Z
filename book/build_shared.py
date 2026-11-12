#!/usr/bin/env python3
"""共享卷首：生成两卷总目录，并校验四篇都已登记（设计 P4）。

    python book/build_shared.py           # 重新生成 02-toc.md
    python book/build_shared.py --check   # 校验目录与 manifest 同步
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "book"))

from references import ReferenceIndex  # noqa: E402

BOOK = ROOT / "book"
MANIFEST = BOOK / "manifest.json"
TOC = BOOK / "shared" / "02-toc.md"


def sort_key(chapter):
    if chapter.number.isdigit():
        return (0, int(chapter.number))
    letter = chapter.number.replace("附录", "").strip()
    return (1, letter)


def toc_markdown() -> str:
    root = json.loads(MANIFEST.read_text(encoding="utf-8"))
    index = ReferenceIndex()
    lines = ["# 两卷总目录", "",
             "> 目录按两卷 manifest 生成；章节编号与页序保留原书，不做全书连续编号。", ""]
    for volume in root["volumes"]:
        chapters = [chapter for chapter in index.chapters.values()
                    if chapter.volume == volume["id"]]
        seen, ordered = set(), []
        for chapter in sorted(chapters, key=sort_key):
            if chapter.label in seen:
                continue
            seen.add(chapter.label)
            ordered.append(chapter)
        name = "卷一" if volume["id"] == "I" else "卷二"
        lines.append(f"## {name}　{volume['title']}")
        lines.append("")
        for chapter in ordered:
            lines.append(f"- {chapter.label.split('·', 1)[-1]}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def check() -> list[str]:
    root = json.loads(MANIFEST.read_text(encoding="utf-8"))
    problems = []
    entries = root.get("shared_front_matter", [])
    if len(entries) != 4:
        problems.append(f"shared_front_matter 应为 4 篇，实际 {len(entries)}")
    for entry in entries:
        path = (ROOT / entry.get("file", "")).resolve()
        if not path.is_file() or not path.is_relative_to(BOOK / "shared"):
            problems.append(f"共享卷首文件缺失或越界：{entry.get('file')}")
    current = TOC.read_text(encoding="utf-8") if TOC.is_file() else ""
    if current != toc_markdown():
        problems.append("book/shared/02-toc.md 与两卷 manifest 不同步")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="共享卷首生成与校验")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        problems = check()
        for problem in problems:
            print(problem, file=sys.stderr)
        print(f"共享卷首：{len(problems)} 个问题")
        return 0 if not problems else 1
    TOC.write_text(toc_markdown(), encoding="utf-8")
    print(f"已生成 {TOC.relative_to(ROOT)}（{len(toc_markdown().splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
