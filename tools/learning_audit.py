#!/usr/bin/env python3
"""Report learning-design pressure across the book, stage docs, and video specs.

This is intentionally a report-only tool. It highlights likely overload and
presentation imbalance without turning editorial judgment into a CI failure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "bms-book" / "book"
STAGE_DIR = ROOT / "docs" / "stages"
VIDEO_DIR = ROOT / "tools" / "video" / "specs"
MICRO_VIDEO_DIR = ROOT / "tools" / "video" / "microcourses"
CURRICULUM = ROOT / "curriculum" / "concepts.json"


def count(pattern: str, text: str, flags: int = 0) -> int:
    return len(re.findall(pattern, text, flags))


def exercise_count(text: str) -> int:
    match = re.search(r"^## 练习\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not match:
        return 0
    return count(r"^\d+\. ", match.group(1), re.M)


def audit_book() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(BOOK_DIR.glob("[0-9][0-9]-*.md")):
        text = path.read_text(encoding="utf-8")
        chapter = path.name[:2]
        flags: list[str] = []
        chars = len(text)
        figures = count(r"<figure\b", text)
        exercises = exercise_count(text)
        if chars > 9000:
            flags.append("篇幅偏长")
        if chapter != "00" and figures < 2:
            flags.append("图解偏少")
        if chapter != "00" and exercises < 3:
            flags.append("取回练习不足")
        if chapter != "00" and "先自己判断" not in text:
            flags.append("缺少显式先判断")
        rows.append(
            {
                "file": path.relative_to(ROOT).as_posix(),
                "chapter": chapter,
                "chars": chars,
                "sections": count(r"^## ", text, re.M),
                "figures": figures,
                "tables": count(r"^\*\*表 ", text, re.M),
                "exercises": exercises,
                "flags": flags,
            }
        )
    return rows


def audit_stages() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(STAGE_DIR.glob("stage-*.md")):
        text = path.read_text(encoding="utf-8")
        chars = len(text)
        flags: list[str] = []
        if chars > 35000:
            flags.append("主线篇幅偏长，建议分必修/选读")
        rows.append(
            {
                "file": path.relative_to(ROOT).as_posix(),
                "chars": chars,
                "sections": count(r"^## ", text, re.M),
                "animation_refs": count(r"\.svg(?:[)\"'])", text),
                "flags": flags,
            }
        )
    return rows


def audit_videos() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted([*VIDEO_DIR.glob("*.json"), *MICRO_VIDEO_DIR.glob("*.json")])
    for path in paths:
        spec = json.loads(path.read_text(encoding="utf-8"))
        kind = spec.get("kind", "series")
        segments = spec.get("segments", [])
        beats = [beat for segment in segments for beat in segment.get("beats", [])]
        layouts: dict[str, int] = {}
        for beat in beats:
            layout = beat.get("layout", "unknown")
            layouts[layout] = layouts.get(layout, 0) + 1
        card_ratio = layouts.get("card", 0) / len(beats) if beats else 0.0
        flags: list[str] = []
        if kind == "series" and len(segments) > 12:
            flags.append("段落过多，优先拆微课")
        if kind == "series" and len(beats) > 80:
            flags.append("beat 过多，单集认知负担偏高")
        if len(spec.get("checklist", [])) > 6:
            flags.append("片尾清单过长")
        if card_ratio > 0.55:
            flags.append("纯卡片占比偏高")
        rows.append(
            {
                "file": path.relative_to(ROOT).as_posix(),
                "episode": spec.get("slug", path.stem),
                "kind": kind,
                "segments": len(segments),
                "beats": len(beats),
                "vo_chars": sum(len(beat.get("vo", "")) for beat in beats),
                "figure_beats": sum(1 for beat in beats if beat.get("svg")),
                "quizzes": layouts.get("quiz", 0),
                "checklist_items": len(spec.get("checklist", [])),
                "card_ratio": round(card_ratio, 3),
                "layouts": dict(sorted(layouts.items())),
                "flags": flags,
            }
        )
    return rows


def audit_curriculum() -> list[dict[str, Any]]:
    data = json.loads(CURRICULUM.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for concept in sorted(data["concepts"], key=lambda row: row["order"]):
        flags: list[str] = []
        if "practice" not in concept:
            flags.append("尚无可运行练习")
        if concept["estimated_minutes"] > 30:
            flags.append("单题时间偏长，考虑拆分")
        rows.append(
            {
                "file": concept["id"],
                "stage": concept["stage_no"],
                "minutes": concept["estimated_minutes"],
                "prerequisites": len(concept["prerequisites"]),
                "animations": len(concept["animations"]),
                "has_practice": "practice" in concept,
                "flags": flags,
            }
        )
    return rows


def build_report() -> dict[str, Any]:
    return {
        "generated_from": ".",
        "book": audit_book(),
        "stages": audit_stages(),
        "videos": audit_videos(),
        "curriculum": audit_curriculum(),
    }


def print_section(title: str, rows: list[dict[str, Any]], fields: list[str]) -> None:
    print(f"\n{title}")
    for row in rows:
        summary = " · ".join(f"{field}={row[field]}" for field in fields)
        flags = "；".join(row["flags"]) or "无明显结构风险"
        print(f"- {row['file']}: {summary} | {flags}")


def print_text(report: dict[str, Any]) -> None:
    book = report["book"]
    stages = report["stages"]
    videos = report["videos"]
    curriculum = report["curriculum"]
    print("BMS-Z 学习设计审计（报告模式，不阻断 CI）")
    print(
        f"总览：书稿 {len(book)} 章 / {sum(row['chars'] for row in book):,} 字符，"
        f"阶段教程 {len(stages)} 篇，视频 {len(videos)} 集，"
        f"核心问题 {len(curriculum)} 个。"
    )
    print_section("书稿", book, ["chars", "sections", "figures", "exercises"])
    print_section("阶段教程", stages, ["chars", "sections", "animation_refs"])
    print_section(
        "视频",
        videos,
        ["kind", "segments", "beats", "vo_chars", "figure_beats", "card_ratio"],
    )
    print_section(
        "核心问题课程图",
        curriculum,
        ["stage", "minutes", "prerequisites", "animations", "has_practice"],
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)


if __name__ == "__main__":
    main()
