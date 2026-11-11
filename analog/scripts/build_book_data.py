#!/usr/bin/env python3
"""从 docs/ 生成书内动画台账；审读表等种子只在缺失时写入。

索引（index-terms.yml）是人工策展数据，不从种子重建。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "analog-book"
DOCS = ROOT / "docs"
DATA = BOOK / "data"

DEMO_HEAD = re.compile(r'^## (5\.\d+)\s+(.+?)\s*<a id="(demo\d+)"')
# 存去 assets/ 前缀的相对路径（svg/ 或 svg-v2/），与 build_site.DEMO_IMG 同口径。
DEMO_IMG = re.compile(r'<img src="assets/(svg(?:-v2)?/[\w\-]+\.svg)"[^>]*alt="([^"]*)"')
DEMO_LINK = re.compile(r"\[(5\.\d+)\]\((?:[\w\-]+\.md)?#(demo\d+)\)")
CHAPTER_ROW = re.compile(r"^\|\s*§(\d+)\s+(第\s*\d+\s*章[^|]*?)\s*\|")
LOOK_RE = re.compile(r"\*\*看点\*\*[：:]\s*(.+)")


def _plain(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


SENTENCE_END = "。；！？"
CLAUSE_END = "，、:"
TRAILING = "、，；：,;:（→"


def _last_unmatched(text, opening, closing):
    stack = []
    for index, char in enumerate(text):
        if char == opening:
            stack.append(index)
        elif char == closing and stack:
            stack.pop()
    return stack[-1] if stack else None


def summarize(text, limit=120):
    """按句末/分句边界截断，保证摘要不切断词、公式或括号。"""
    if len(text) <= limit:
        return text
    window = text[:limit - 1]
    cut = max(window.rfind(char) for char in SENTENCE_END)
    if cut < 0:
        cut = max(window.rfind(char) for char in CLAUSE_END)
    if cut >= 0:
        summary = window[:cut + 1]
    else:
        space = max(window.rfind(char) for char in " \t")
        summary = window[:space] if space >= 0 else window
    if summary.count("$") % 2:
        summary = summary[:summary.rfind("$")]
    while summary.count("（") > summary.count("）"):
        unmatched = _last_unmatched(summary, "（", "）")
        if unmatched is None:
            break
        summary = summary[:unmatched]
    summary = summary.rstrip()
    while summary and summary[-1] in TRAILING:
        summary = summary[:-1].rstrip()
    if not summary.endswith(("。", "！", "？")):
        summary += "…"
    return summary


def build_animations():
    lines = (DOCS / "p5-00-part5.md").read_text(encoding="utf-8").splitlines()
    chapter_of = {}
    for line in lines:
        match = CHAPTER_ROW.match(line)
        if match:
            for _num, demo in DEMO_LINK.findall(line):
                chapter_of[demo] = int(match.group(1))
    items, current, body = [], None, []

    def finish():
        nonlocal current, body
        if current is None:
            return
        if not current["svg"]:
            raise SystemExit(f'{current["anchor"]}: 缺少 SVG')
        look = None
        for line in body:
            found = LOOK_RE.search(line)
            if found:
                look = _plain(found.group(1))
                break
        if not look:
            look = current["title"]
        chapter = chapter_of.get(current["anchor"])
        if chapter is None:
            raise SystemExit(f'{current["anchor"]}: 章节映射表缺少该动画')
        items.append({
            "id": f"anim-{len(items) + 1:03d}",
            "file": "p5-00-part5.md",
            "title": current["title"],
            "chapter": chapter,
            "anchor": current["anchor"],
            "one_line": summarize(look),
            "static_svg": "assets/" + current["svg"],
        })
        current, body = None, []

    for line in lines:
        match = DEMO_HEAD.match(line)
        if match:
            finish()
            current = {"num": match.group(1), "title": _plain(match.group(2)),
                       "anchor": match.group(3), "svg": ""}
            continue
        if current is not None:
            if not current["svg"]:
                image = DEMO_IMG.search(line)
                if image:
                    current["svg"] = image.group(1)
                    continue
            body.append(line)
    finish()
    # 数量闸与 scripts/test_svg_count_floor.py 同口径：只设下限不锁死总数，
    # 扩量（Task 11b）后画廊随生成器增长，不再回填硬编码数字。
    if len(items) < 150:
        raise SystemExit(f"动画少于 150 条（扩量闸下限），解析到 {len(items)}")
    for item in items:
        if not (ROOT / item["static_svg"]).is_file():
            raise SystemExit(f'缺少图片 {item["static_svg"]}')
    return items


def build_signoffs():
    return [{"chapter": i, "draft_version": "2.0.0-draft.1",
             "technical_reviewer": "", "editorial_reviewer": "",
             "safety_reviewer": "", "date": "2026-10-25", "open_issues": []}
            for i in range(19)]


def dump(path, value):
    text = yaml.safe_dump(value, allow_unicode=True, sort_keys=False, width=100)
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    animations = build_animations()
    if args.check:
        path = DATA / "animations.yml"
        if not path.is_file():
            print("缺少 animations.yml，请运行 --write", file=sys.stderr)
            return 1
        current = yaml.safe_load(path.read_text(encoding="utf-8"))
        if current != animations:
            print("animations.yml 与 p5-00-part5.md 不一致，请运行 --write", file=sys.stderr)
            return 1
        return 0
    if not args.write:
        parser.error("需要 --write 或 --check")
    dump(DATA / "animations.yml", animations)
    for name, value in (("chapter-signoff.yml", build_signoffs()),
                        ("sources.yml", []),
                        ("references.yml", [])):
        path = DATA / name
        if not path.exists():
            dump(path, value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
