#!/usr/bin/env python3
"""19 章的「教材化」章首元数据：难度分级、精读时长、白话导读。

为什么单独一个模块：这三样是**跨页面**的一致性数据——
「从零开始最短路径」页按难度排顺序，章首的难度卡按同一张表渲染，
Python 侧的测试按同一张表核对。数据只能有一份，否则迟早对不上。

文本方向：`docs/` 是唯一内容源，所以这里不生成页面，只生成章首那一小块
（`render_block`），由 `--write` 写回 19 个 `docs/p*-ch*.md`，`--check` 核对
是否漂移。排版位置固定为「场景之后、先修/目标之前」：先把人带进情境
（场景），再告诉他这一章多难、用大白话说讲什么（难度 + 白话），最后才是
考核目标与先修链接。

白话导读的正文来自 `analog-book/book/intuition.py`（印刷版章首的同一条），
不在这里重写一遍：两份文案迟早会分叉。缺了它，网页版章首有、纸质版没有，
或者反过来。

用法::

    python scripts/curriculum.py --check   # CI / 测试：文档与数据是否一致
    python scripts/curriculum.py --write   # 改完上面的表格后刷新 19 个章首
"""
from __future__ import annotations

import argparse
import importlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BOOK = ROOT / "analog-book"
if str(BOOK) not in sys.path:            # 与测试同一套 sys.path 约定
    sys.path.insert(0, str(BOOK))

# The book package lives below analog-book (not an importable package name).
# Resolve it after adding that directory, matching the book build entry points.
CHAPTER_LEADS: dict[int, str] = importlib.import_module("book.intuition").CHAPTER_LEADS

# 难度分级：按「读懂需要的前置」而不是按篇来分。同一篇里也会跨级
# （第 6 章运放是 L2，第 7 章比较器又是 L1：它只用到第 0 章的阈值直觉）。
LEVELS: dict[str, str] = {
    "L0": "零基础",
    "L1": "入门",
    "L2": "进阶",
    "L3": "深入",
}

# chapter -> (文件名, 等级, 精读分钟)。分钟数 = 正文汉字数 / 300 取整到 5 分钟，
# 下限 5；测试会按同样的口径重算并允许 ±5 分钟误差，防止正文改长了标签还写老数字。
CHAPTER_META: dict[int, tuple[str, str, int]] = {
    0: ("p1-01-ch0.md", "L0", 25),
    1: ("p1-02-ch1.md", "L1", 30),
    2: ("p1-03-ch2.md", "L1", 40),
    3: ("p1-04-ch3.md", "L1", 40),
    4: ("p1-05-ch4.md", "L1", 30),
    5: ("p1-06-ch5.md", "L1", 35),
    6: ("p1-07-ch6.md", "L2", 30),
    7: ("p1-08-ch7.md", "L1", 40),
    8: ("p1-09-ch8.md", "L1", 60),
    9: ("p1-10-ch9.md", "L2", 30),
    10: ("p1-11-ch10.md", "L1", 45),
    11: ("p2-01-ch11.md", "L2", 35),
    12: ("p2-02-ch12.md", "L2", 15),
    13: ("p2-03-ch13.md", "L3", 30),
    14: ("p3-01-ch14.md", "L2", 20),
    15: ("p3-02-ch15.md", "L2", 45),
    16: ("p4-01-ch16.md", "L2", 35),
    17: ("p4-02-ch17.md", "L1", 35),
    18: ("p4-03-ch18.md", "L3", 40),
}

# 章首块的两种标志：难度（level）与白话（lead）。纯文本标签，无 emoji（v3.72）。
LEVEL_MARK = "> **难度**："
LEAD_MARK = "> **白话**："
SCENE_RE = re.compile(r"^> \*\*场景\*\*：(?:.+)$", re.M)
SECTION_RE = re.compile(r"^### ", re.M)


def chapter_number(filename: str) -> int:
    match = re.search(r"-ch(\d+)\.md$", filename)
    if match is None:
        raise ValueError(f"不是章文件: {filename}")
    return int(match.group(1))


def lead(chapter: int) -> str:
    try:
        return CHAPTER_LEADS[chapter]
    except KeyError:
        raise KeyError(f"第 {chapter} 章没有白话导读（book/intuition.py）") from None


def level_label(chapter: int) -> str:
    code = CHAPTER_META[chapter][1]
    return f"{code} {LEVELS[code]}"


def section_count(text: str) -> int:
    return len(SECTION_RE.findall(text))


def render_block(chapter: int, text: str) -> str:
    """渲染「难度 + 白话」两行引用块；`text` 用来数节数。"""
    _file, _level, minutes = CHAPTER_META[chapter]
    sections = section_count(text)
    return (f"{LEVEL_MARK}{level_label(chapter)}，{sections} 节，"
            f"精读约 {minutes} 分钟\n>\n{LEAD_MARK}{lead(chapter)}\n")


def insert_block(text: str, chapter: int) -> str:
    """把章首块放到场景之后；已存在则原位替换（幂等）。

    按行处理而不是整段正则：块与「**先修** / **学完你应能**」是相邻的两个
    引用块，多一个或少一个空行就会把它们粘成一片（Markdown 只认 `>` 前缀）。
    """
    lines = text.split("\n")

    # 1) 摘掉旧块（🎚 / > / 🗣 三行 + 紧跟的一个空行）
    kept: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith(LEVEL_MARK):
            j = i + 1
            if j < len(lines) and lines[j].strip() == ">":
                j += 1
            if j < len(lines) and lines[j].startswith(LEAD_MARK):
                j += 1
            i = j + 1 if j < len(lines) and lines[j].strip() == "" else j
            continue
        kept.append(lines[i])
        i += 1
    lines = kept

    # 2) 插到场景行之后（场景与块之间、块与下文之间各留一个空行）
    scene = next((k for k, line in enumerate(lines)
                  if line.startswith("> **场景**：")), None)
    if scene is None:
        raise ValueError(f"第 {chapter} 章缺少场景开场（> **场景**：…）")

    block = render_block(chapter, "\n".join(lines)).rstrip("\n").split("\n")
    insert_at = scene + 1
    while insert_at < len(lines) and lines[insert_at].strip() == "":
        insert_at += 1
    return "\n".join(lines[:scene + 1] + [""] + block + [""]
                      + lines[insert_at:])


def apply() -> dict[str, str]:
    """返回 {文件名: 期望内容}（不改盘）。"""
    out: dict[str, str] = {}
    for chapter, (filename, _level, _minutes) in CHAPTER_META.items():
        path = DOCS / filename
        text = path.read_text(encoding="utf-8")
        out[filename] = insert_block(text, chapter)
    return out


def drift() -> list[str]:
    changed = []
    for filename, expected in apply().items():
        if (DOCS / filename).read_text(encoding="utf-8") != expected:
            changed.append(filename)
    return sorted(changed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="核对章首块是否漂移")
    group.add_argument("--write", action="store_true", help="写回 19 个章文件")
    args = parser.parse_args(argv)

    if args.write:
        for filename, expected in apply().items():
            (DOCS / filename).write_text(expected, encoding="utf-8", newline="\n")
        print(f"写入 {len(CHAPTER_META)} 个章首块")
        return 0
    changed = drift()
    if changed:
        print("章首块与 scripts/curriculum.py 不一致：")
        for name in changed:
            print(f"  - docs/{name}")
        return 1
    print(f"{len(CHAPTER_META)} 章章首块一致（L0–L3 分级 + 白话导读）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
