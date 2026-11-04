#!/usr/bin/env python3
"""Report long stretches of book prose without figures or other evidence.

The audit is deliberately non-blocking. A long figure gap is a review hint,
not an instruction to add a decorative image. Tables, scenarios, questions,
counterexamples and runnable labs also interrupt an abstract reading stretch.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "bms-book" / "book"
STAGE_DIR = ROOT / "docs" / "stages"

FIGURE_RE = re.compile(r"<figure\b.*?</figure>", re.I | re.S)
# 阶段讲义用 Markdown 图片作插图（书稿一律 <figure>，全库 `![]()` 计数为 0，
# 所以这条规则只影响阶段页，不改书稿数字）。
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
EVIDENCE_RES = (
    FIGURE_RE,
    MD_IMAGE_RE,
    re.compile(
        r"^\|.*\|\r?\n"
        r"^\|(?:\s*:?-+:?\s*\|)+\s*\r?\n"
        r"(?:^\|.*\|\s*\r?\n?)+",
        re.M,
    ),
    re.compile(r"^::: (?:story|lab|trap)\b.*?^:::\s*$", re.M | re.S),
    re.compile(r'<section class="book-lab".*?</section>', re.I | re.S),
    re.compile(r'^<aside class="reading-bet".*?</aside>\s*$', re.I | re.M | re.S),
    re.compile(r"^(?:>\s*)?(?:\*\*)?先自己判断(?:\*\*)?.*$", re.M),
    # 阶段讲义把「先自己判断」写成 **短自测**：同一种「问题块」，书稿侧已计入，
    # 阶段页不认会把读者的自测段算成抽象段。
    re.compile(r"^\*\*短自测\*\*.*$", re.M),
    re.compile(r"^\x60\x60\x60[^\r\n]*\r?\n.*?^\x60\x60\x60\s*$", re.M | re.S),
    re.compile(r"^(?:>\s*)?\*\*(?:教学算例|算一笔)[^*]*\*\*.*$", re.M),
    re.compile(
        r"^\$\$\s*\r?\n"
        r"(?=(?:(?!^\$\$\s*$)[\s\S])*?\d)"
        r"(?:(?!^\$\$\s*$)[\s\S])*?^\$\$\s*$",
        re.M,
    ),
)
HEADING_RE = re.compile(r"^#{1,2}\s+(.+)$", re.M)
EXERCISE_RE = re.compile(r"^## 练习\s*$", re.M)
# 阶段讲义的尾部是练习类小节（书稿对应 `## 练习`）：它们是任务与勾选项，
# 不该被当作「抽象段」要求配图，所以和书稿一样在首个此类小节处截断。
STAGE_EXERCISE_RE = re.compile(
    r"^##\s+.*(?:自测题|动手任务|验收清单|毕业验收|完整自测).*$", re.M
)
MARKUP_RE = re.compile(r"<[^>]+>|!\[[^\]]*]\([^)]*\)")
PUNCTUATION_RE = re.compile(r"[\s#*_\x60>\[\](){}|:：;；,，.。!?！？—–\-]+")


@dataclass
class Gap:
    chars: int
    start: int
    end: int
    from_heading: str
    to_heading: str


@dataclass
class ChapterAudit:
    chapter: str
    chars: int
    figures: int
    evidence_marks: int
    max_figure_gap: int
    max_evidence_gap: int
    figure_gap_from: str
    figure_gap_to: str
    evidence_gap_from: str
    evidence_gap_to: str
    flags: list[str]


@dataclass
class StageAudit:
    """§C 原理简化审计的实测列：首个证据距开头 + 最大证据断层。"""

    page: str
    chars: int
    figures: int
    first_evidence: int
    max_evidence_gap: int
    gap_from: str
    gap_to: str
    flags: list[str]


def strip_frontmatter(text: str) -> str:
    """去掉 `---` YAML 头：它不是读者可见正文，计入会把「距开头」虚增。"""
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    return parts[2] if len(parts) == 3 else text


def visible_chars(text: str) -> int:
    text = MARKUP_RE.sub(" ", text)
    text = PUNCTUATION_RE.sub("", text)
    return len(text)


def merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[list[int]] = []
    for start, end in sorted(spans):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def heading_before(text: str, position: int) -> str:
    matches = list(HEADING_RE.finditer(text, 0, position))
    return matches[-1].group(1).strip() if matches else "开头"


def heading_after(text: str, position: int) -> str:
    match = HEADING_RE.search(text, position)
    return match.group(1).strip() if match else "章末"


def longest_gap(text: str, spans: list[tuple[int, int]]) -> Gap:
    best = Gap(0, 0, 0, "开头", "章末")
    cursor = 0
    for start, end in spans + [(len(text), len(text))]:
        size = visible_chars(text[cursor:start])
        if size > best.chars:
            best = Gap(
                chars=size,
                start=cursor,
                end=start,
                from_heading=heading_before(text, cursor),
                to_heading=heading_after(text, start),
            )
        cursor = end
    return best


def find_spans(text: str, patterns: tuple[re.Pattern[str], ...]) -> list[tuple[int, int]]:
    return merge_spans(
        [(match.start(), match.end()) for pattern in patterns for match in pattern.finditer(text)]
    )


def audit_chapter(
    path: Path,
    evidence_limit: int,
    figure_review_limit: int,
) -> ChapterAudit:
    text = path.read_text(encoding="utf-8")
    exercise = EXERCISE_RE.search(text)
    body = text[: exercise.start()] if exercise else text
    figure_spans = find_spans(body, (FIGURE_RE,))
    evidence_spans = find_spans(body, EVIDENCE_RES)
    figure_gap = longest_gap(body, figure_spans)
    evidence_gap = longest_gap(body, evidence_spans)
    flags: list[str] = []
    if evidence_gap.chars > evidence_limit:
        flags.append("证据断层")
    if figure_gap.chars > figure_review_limit:
        flags.append("长无图区复核")
    if len(figure_spans) < 2 and not path.name.startswith("00-"):
        flags.append("图解偏少")
    return ChapterAudit(
        chapter=path.name,
        chars=len(text),
        figures=len(figure_spans),
        evidence_marks=len(evidence_spans),
        max_figure_gap=figure_gap.chars,
        max_evidence_gap=evidence_gap.chars,
        figure_gap_from=figure_gap.from_heading,
        figure_gap_to=figure_gap.to_heading,
        evidence_gap_from=evidence_gap.from_heading,
        evidence_gap_to=evidence_gap.to_heading,
        flags=flags,
    )


def numbered_chapters() -> list[Path]:
    return sorted(path for path in BOOK_DIR.glob("*.md") if re.match(r"^\d{2}-", path.name))


def stage_pages(include_all: bool = False) -> list[Path]:
    """§C 表只列主线讲义 + stage-1 / stage-7 两个单页阶段。

    选读、完整自测与合并版长页（如 `stage-4-SOC-SOH算法.md`）不在 §C 口径内，
    用 `--all-stages` 才纳入。
    """
    pages = sorted(STAGE_DIR.glob("stage-*.md"))
    if include_all:
        return pages
    single_page = {"stage-1-认识BMS.md", "stage-7-BMS与AI.md"}
    return [p for p in pages if "-主线-" in p.name or p.name in single_page]


def audit_stage(path: Path, gap_limit: int) -> StageAudit:
    """§C 表：首个证据距开头 + 最大证据断层（frontmatter 不计入可见正文）。

    和书稿口径一致，在首个练习类小节（自测题 / 动手任务 / 验收清单 / 毕业验收）处截断：
    任务是勾选项，不该因为「没配图」被算成抽象段。
    """
    text = strip_frontmatter(path.read_text(encoding="utf-8"))
    exercise = STAGE_EXERCISE_RE.search(text)
    body = text[: exercise.start()] if exercise else text
    spans = find_spans(body, EVIDENCE_RES)
    first = spans[0][0] if spans else len(body)
    gap = longest_gap(body, spans)
    flags = ["断层超限"] if gap.chars > gap_limit else []
    return StageAudit(
        page=path.name,
        chars=visible_chars(body),
        # 图数按整页计（含练习小节里的图），与截断前口径保持一致。
        figures=len(find_spans(text, (MD_IMAGE_RE, FIGURE_RE))),
        first_evidence=visible_chars(body[:first]),
        max_evidence_gap=gap.chars,
        gap_from=gap.from_heading,
        gap_to=gap.to_heading,
        flags=flags,
    )


def print_stage_table(rows: list[StageAudit], gap_limit: int) -> None:
    print(
        "| 页面 | 图数 | 首个证据距开头 | 最大证据断层 | 断层范围 | "
        f"断层 >{gap_limit} 标记 |\n|---|---:|---:|---:|---|---|"
    )
    for row in rows:
        scope = f"{row.gap_from} → {row.gap_to}"
        flag = "是" if row.flags else "—"
        print(
            f"| [{row.page}](stages/{row.page}) | {row.figures} | "
            f"{row.first_evidence} | {row.max_evidence_gap} | {scope} | {flag} |"
        )


def print_table(rows: list[ChapterAudit], top: int) -> None:
    print(
        "| 章节 | 图数 | 最长无图区 | 最长无证据区 | 无图区范围 | 标记 |\n"
        "|---|---:|---:|---:|---|---|"
    )
    for row in rows[:top]:
        scope = f"{row.figure_gap_from} → {row.figure_gap_to}"
        flags = "、".join(row.flags) if row.flags else "—"
        print(
            f"| {row.chapter} | {row.figures} | {row.max_figure_gap} | "
            f"{row.max_evidence_gap} | {scope} | {flags} |"
        )
    print()
    print("说明：长无图区只触发人工复核；表格、现场、反例、问题和实验会截断无证据区。")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=15)
    parser.add_argument("--evidence-limit", type=int, default=1200)
    parser.add_argument("--figure-review-limit", type=int, default=3000)
    parser.add_argument(
        "--stages",
        action="store_true",
        help="按 docs/视觉缺口表.md §C 口径审计 docs/stages/*.md（首个证据距开头 + 最大证据断层）",
    )
    parser.add_argument(
        "--all-stages",
        action="store_true",
        help="--stages 时纳入选读、完整自测与合并长页（默认只审 §C 列出的主线页）",
    )
    parser.add_argument(
        "--gap-limit",
        type=int,
        default=800,
        help="§C 的「断层 >800 标记」阈值（仅 --stages）",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.stages:
        stage_rows = [
            audit_stage(path, args.gap_limit) for path in stage_pages(args.all_stages)
        ]
        if args.json:
            print(json.dumps([asdict(row) for row in stage_rows], ensure_ascii=False, indent=2))
        else:
            print_stage_table(stage_rows, args.gap_limit)
            print()
            print(
                "口径：证据 = 图片（`![]()`/`<figure>`）、表格、`::: story|lab|trap`、"
                "`book-lab` 段、`reading-bet`、`先自己判断`、代码块、教学算例/算一笔、带数字的块公式；"
                "frontmatter 不计入可见正文；在首个「自测题 / 动手任务 / 验收清单 / 毕业验收 / 完整自测」"
                "小节处截断（与书稿的 `## 练习` 同规则）；图数按整页计。"
            )
        return 0

    rows = [
        audit_chapter(path, args.evidence_limit, args.figure_review_limit)
        for path in numbered_chapters()
    ]
    rows.sort(key=lambda row: (row.max_figure_gap, row.max_evidence_gap), reverse=True)
    if args.json:
        print(json.dumps([asdict(row) for row in rows], ensure_ascii=False, indent=2))
    else:
        print_table(rows, args.top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
