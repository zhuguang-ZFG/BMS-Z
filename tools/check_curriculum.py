#!/usr/bin/env python3
"""Validate the cross-media BMS-Z curriculum graph."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CURRICULUM = ROOT / "curriculum" / "concepts.json"
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LEVELS = {"记忆", "理解", "应用", "分析", "评价", "创造"}
DOMAINS = {"观察与保护", "测量与估算", "通信、系统与责任"}
STATUSES = {"active", "pilot", "retired"}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def existing_path(errors: list[str], concept_id: str, label: str, value: str) -> None:
    path = ROOT / value
    if not path.is_file():
        fail(errors, f"{concept_id}: {label} 不存在：{value}")


def check_video(errors: list[str], concept: dict[str, Any]) -> None:
    video = concept["video"]
    spec_path = ROOT / video["spec"]
    existing_path(errors, concept["id"], "视频分镜", video["spec"])
    if not spec_path.is_file():
        return
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    segment_ids = {segment.get("id") for segment in spec.get("segments", [])}
    if video["segment"] not in segment_ids:
        fail(
            errors,
            f"{concept['id']}: 视频段 {video['segment']!r} 不在 {video['spec']} 中",
        )


def check_cycle(errors: list[str], concepts: dict[str, dict[str, Any]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(concept_id: str, trail: list[str]) -> None:
        if concept_id in visited:
            return
        if concept_id in visiting:
            start = trail.index(concept_id)
            fail(errors, "先修关系成环：" + " → ".join(trail[start:] + [concept_id]))
            return
        visiting.add(concept_id)
        for prerequisite in concepts[concept_id]["prerequisites"]:
            if prerequisite in concepts:
                visit(prerequisite, trail + [concept_id])
        visiting.remove(concept_id)
        visited.add(concept_id)

    for concept_id in concepts:
        visit(concept_id, [])


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = data.get("concepts")
    if not isinstance(rows, list) or not rows:
        return ["concepts 必须是非空数组"]

    concepts: dict[str, dict[str, Any]] = {}
    orders: set[int] = set()
    required = {
        "id",
        "order",
        "stage_no",
        "domain",
        "level",
        "difficulty",
        "status",
        "question",
        "precheck",
        "answer",
        "deliverable",
        "teaching",
        "estimated_minutes",
        "prerequisites",
        "stage",
        "book",
        "animations",
        "video",
        "checkpoint",
    }
    for row in rows:
        if not isinstance(row, dict):
            fail(errors, "concepts 中出现非对象条目")
            continue
        missing = required - row.keys()
        concept_id = str(row.get("id", "(missing)"))
        if missing:
            fail(errors, f"{concept_id}: 缺字段 {sorted(missing)}")
            continue
        if not ID_RE.fullmatch(concept_id):
            fail(errors, f"{concept_id}: id 必须是小写 kebab-case")
        if concept_id in concepts:
            fail(errors, f"重复 id：{concept_id}")
        concepts[concept_id] = row
        if row["order"] in orders:
            fail(errors, f"重复 order：{row['order']}")
        orders.add(row["order"])
        if row["level"] not in LEVELS:
            fail(errors, f"{concept_id}: 未知层级 {row['level']!r}")
        if row["domain"] not in DOMAINS:
            fail(errors, f"{concept_id}: 未知领域 {row['domain']!r}")
        if row["status"] not in STATUSES:
            fail(errors, f"{concept_id}: 未知状态 {row['status']!r}")
        if not isinstance(row["difficulty"], int) or not 1 <= row["difficulty"] <= 3:
            fail(errors, f"{concept_id}: difficulty 必须是 1–3")
        if not isinstance(row["estimated_minutes"], int) or row["estimated_minutes"] <= 0:
            fail(errors, f"{concept_id}: estimated_minutes 必须是正整数")
        if not isinstance(row["stage_no"], int) or not 0 <= row["stage_no"] <= 7:
            fail(errors, f"{concept_id}: stage_no 必须在 0–7")
        if not str(row["question"]).endswith(("？", "?")):
            fail(errors, f"{concept_id}: question 应以问号结尾")
        teaching = row["teaching"]
        if not isinstance(teaching, dict) or not {"hook", "worked_example", "misconception"} <= teaching.keys():
            fail(errors, f"{concept_id}: teaching 必须含 hook / worked_example / misconception")
        else:
            for field in ("hook", "worked_example", "misconception"):
                if not str(teaching[field]).strip():
                    fail(errors, f"{concept_id}: teaching.{field} 不能为空")
        for field in ("stage", "book"):
            ref = row[field]
            if not isinstance(ref, dict) or not {"path", "label"} <= ref.keys():
                fail(errors, f"{concept_id}: {field} 必须含 path 与 label")
            else:
                existing_path(errors, concept_id, field, ref["path"])
        if not isinstance(row["animations"], list) or not row["animations"]:
            fail(errors, f"{concept_id}: 至少登记一张动画")
        else:
            for animation in row["animations"]:
                existing_path(errors, concept_id, "动画", animation)
        check_video(errors, row)
        practice = row.get("practice")
        if practice is not None:
            if not isinstance(practice, dict) or not {"path", "command", "proof"} <= practice.keys():
                fail(errors, f"{concept_id}: practice 必须含 path / command / proof")
            else:
                existing_path(errors, concept_id, "练习", practice["path"])

    for concept_id, row in concepts.items():
        prerequisites = row["prerequisites"]
        if not isinstance(prerequisites, list):
            fail(errors, f"{concept_id}: prerequisites 必须是数组")
            continue
        for prerequisite in prerequisites:
            if prerequisite not in concepts:
                fail(errors, f"{concept_id}: 未知先修 {prerequisite!r}")
            if prerequisite == concept_id:
                fail(errors, f"{concept_id}: 不能把自己列为先修")
    check_cycle(errors, concepts)
    if not errors:
        sys.path.insert(0, str(ROOT / "tools"))
        import gen_curriculum_pages

        expected = gen_curriculum_pages.render(data)
        output = ROOT / "docs" / "核心问题地图.md"
        actual = output.read_text(encoding="utf-8") if output.is_file() else ""
        if actual != expected:
            fail(errors, "docs/核心问题地图.md 与 curriculum/concepts.json 不一致；运行生成器")
    return errors


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    data = json.loads(CURRICULUM.read_text(encoding="utf-8"))
    errors = validate(data)
    if errors:
        print(f"FAIL ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    concepts = data["concepts"]
    practices = sum("practice" in concept for concept in concepts)
    animations = sum(len(concept["animations"]) for concept in concepts)
    print(
        f"PASS：{len(concepts)} 个核心问题 / {animations} 个动画映射 / "
        f"{practices} 个可运行练习 / 先修关系无环"
    )


if __name__ == "__main__":
    main()
