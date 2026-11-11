#!/usr/bin/env python3
"""整包重做总闸残余扫描：契约、套话、引用库、SVG 数量、双源目录、五线数值抽检。

任一项不过即退出码 1；本脚本只聚合既有闸，不自行放宽阈值。
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "video"))

CHAPTER_FILES = [
    "docs/p1-01-ch0.md", "docs/p1-02-ch1.md", "docs/p1-03-ch2.md", "docs/p1-04-ch3.md",
    "docs/p1-05-ch4.md", "docs/p1-06-ch5.md", "docs/p1-07-ch6.md", "docs/p1-08-ch7.md",
    "docs/p1-09-ch8.md", "docs/p1-10-ch9.md", "docs/p1-11-ch10.md", "docs/p2-01-ch11.md",
    "docs/p2-02-ch12.md", "docs/p2-03-ch13.md", "docs/p3-01-ch14.md", "docs/p3-02-ch15.md",
    "docs/p4-01-ch16.md", "docs/p4-02-ch17.md", "docs/p4-03-ch18.md",
]
CHAPTER_NUM = {"ch1": 1, "ch12": 12, "ch16": 16}


def check_contract() -> list[str]:
    import check_chapter_contract
    issues = []
    for f in CHAPTER_FILES:
        p = ROOT / f
        result = check_chapter_contract.scan_chapter(p)
        if not all(result.values()):
            issues.append(f"契约未过：{f} {result}")
    return issues


def check_slop() -> list[str]:
    import check_ai_slop
    wl = check_ai_slop.load_whitelist(
        ROOT / "docs/superpowers/templates/humanizer-whitelist.md")
    issues = []
    for f in CHAPTER_FILES:
        text = (ROOT / f).read_text(encoding="utf-8")
        for ln, s in check_ai_slop.scan_text(text, wl):
            issues.append(f"套话残留：{f}:{ln}: {s}")
    return issues


def check_references() -> list[str]:
    import check_references
    issues = check_references.validate(
        ROOT / "analog-book/data/references.yml",
        ROOT / "analog-book/data/sources.yml")
    issues += check_references.scan_chapters([ROOT / f for f in CHAPTER_FILES])
    return [f"引用库：{e}" for e in issues]


def check_svg_floor() -> list[str]:
    svg_dir = ROOT / "assets" / "svg"
    files = sorted(svg_dir.glob("*.svg"))
    issues = []
    if len(files) < 150:
        issues.append(f"SVG 仅 {len(files)} 张（扩量闸 ≥150）")
    skin = 0
    for p in files:
        if 'id="bgL"' in p.read_text(encoding="utf-8"):
            skin += 1
    if skin != len(files):
        issues.append(f"SVG 纸墨皮肤不齐：{skin}/{len(files)} 缺 id=bgL（疑手改产物）")
    return issues


def check_no_parallel_tree(root: Path = ROOT, names: tuple = ("book-manuscript", "book_draft", "docs-book", "manuscript-zh")) -> list[str]:
    issues = []
    for bad in names:
        if (root / bad).exists():
            issues.append(f"发现疑似平行书稿目录：{bad}/（spec §3 废止）")
    return issues


def check_five_line_sample(ep_dir: Path = ROOT / "video" / "shots") -> list[str]:
    """抽检 ch1 / ch12 / ch16：章内口诀与总表、EP 分镜、社媒样例一致。"""
    registry = (ROOT / "docs/p8-11-s8-11.md").read_text(encoding="utf-8")
    issues = []
    for ch, number in CHAPTER_NUM.items():
        doc = (ROOT / next(f for f in CHAPTER_FILES if f.endswith(f"-{ch}.md"))).read_text(encoding="utf-8")
        motto = re.search(r'^> \*\*口诀\*\*：(.+)$', doc, re.M)
        row = re.search(
            rf"\|\s*\[第 {number} 章\]\(p[\d-]+-{ch}\.md#{ch}\)\s*\|([^|]+)\|([^|]+)\|",
            registry)
        if not motto or not row:
            issues.append(f"{ch}: 缺少章内口诀或总表行")
            continue
        title, sentence = (cell.strip() for cell in row.groups())
        if motto.group(1).strip().rstrip('。') not in {
                sentence.rstrip('。'), (title + '——' + sentence).rstrip('。')}:
            issues.append(f"{ch}: 章内口诀与总表不同源")
    social = (ROOT / "docs/superpowers/examples/social/ch16-debug.md").read_text(encoding="utf-8")
    if "一次只改一个变量" not in social:
        issues.append("社媒样例 ch16 未引用口诀卡")
    ep_checks = {
        "ep04-divider.json": [("12V 分压", "ch0 例 0-1"), ("等于 4V", "ch0 例 0-1")],
        "ep05-probe.json": [("9.1 微秒", "ch16 例 16-1"), ("17.5k", "ch16 例 16-1"), ("161k", "ch16 例 16-1")],
        "ep02-virtual-short.json": [("0.5 伏每微秒", "ch7 迟滞预算")],
        "ep07-pullup.json": [("890 欧", "ch5 上拉计算"), ("820", "ch5 上拉计算")],
        "ep09-electrolytic.json": [("32000 小时", "ch1 寿命账"), ("3.7 年", "ch1 寿命账")],
        "ep13-buck.json": [("0.88 安", "ch13 Buck 算例"), ("7.4 毫伏", "ch13 Buck 算例")],
    }
    for fname, needles in ep_checks.items():
        text = (ep_dir / fname).read_text(encoding="utf-8")
        for needle, source in needles:
            if needle not in text:
                issues.append(f"{fname} 与正典数值不一致：缺「{needle}」（{source}）")
    return issues


def main() -> int:
    checks = [
        ("章节契约", check_contract),
        ("套话闸", check_slop),
        ("引用库", check_references),
        ("SVG 扩量与皮肤", check_svg_floor),
        ("双源目录探测", check_no_parallel_tree),
        ("五线数值抽检", check_five_line_sample),
    ]
    failures = 0
    for name, fn in checks:
        issues = fn()
        status = "OK" if not issues else f"FAIL（{len(issues)}）"
        print(f"[{status}] {name}")
        for i in issues:
            print(f"  - {i}")
        failures += len(issues)
    print("remake-ship 残余扫描：", "通过" if not failures else f"{failures} 项未过")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
