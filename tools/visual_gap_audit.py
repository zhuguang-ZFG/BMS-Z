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

FIGURE_RE = re.compile(r"<figure\b.*?</figure>", re.I | re.S)
EVIDENCE_RES = (
    FIGURE_RE,
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
    re.compile(r"^\x60\x60\x60[^\r\n]*\r?\n.*?^\x60\x60\x60\s*$", re.M | re.S),
    re.compile(r"^\*\*(?:教学算例|算一笔)[^*]*\*\*.*$", re.M),
    re.compile(
        r"^\$\$\s*\r?\n"
        r"(?=(?:(?!^\$\$\s*$)[\s\S])*?\d)"
        r"(?:(?!^\$\$\s*$)[\s\S])*?^\$\$\s*$",
        re.M,
    ),
)
HEADING_RE = re.compile(r"^#{1,2}\s+(.+)$", re.M)
EXERCISE_RE = re.compile(r"^## 练习\s*$", re.M)
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
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

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
