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
STATUSES = {"planned", "active", "gap"}
# SPEC v2.5 §9.2：13 条骨干 KP 的 id 冻结，删除或改名都会让历史链接与跨媒介映射失效。
# SPEC v2.5 §9.1：主线页至少覆盖到 L3（手算/跑通），所以骨干 KP 的 L3 入口必须落在
# 下面这 18 篇主线页里；完整讲义只作查阅，不算主线覆盖。
MAINLINE_PAGES = frozenset({
    "stage-0-主线-电池.md",
    "stage-0-主线-充电与电量.md",
    "stage-1-认识BMS.md",
    "stage-2-主线-单节保护板.md",
    "stage-2-主线-多节与接口.md",
    "stage-2-主线-实测与验收.md",
    "stage-3-主线-AFE与采样.md",
    "stage-3-主线-固件与功率开关.md",
    "stage-3-主线-PCB调试与验收.md",
    "stage-4-主线-SOC估算.md",
    "stage-4-主线-SOH与SOP.md",
    "stage-4-主线-模型与校正.md",
    "stage-5-主线-CAN与外部接口.md",
    "stage-5-主线-串口与Modbus.md",
    "stage-5-主线-协议逆向与安全.md",
    "stage-6-主线-量产与毕业.md",
    "stage-6-主线-高压与安全.md",
    "stage-7-BMS与AI.md",
})
LADDER_LEVELS = ("L1", "L2", "L3", "L4", "L5")
LADDER_FIELDS = ("goal", "entry_path", "retrieve_task", "pass_check", "media")
MASTERY_EVIDENCE = {"日志", "手算纸", "仿真输出", "照片"}
BACKBONE_IDS = (
    "three-probes",
    "load-voltage-drop",
    "overcharge-chain",
    "weakest-cell",
    "protection-debounce",
    "measurement-budget",
    "soc-drift",
    "ocv-trust",
    "hppc-identification",
    "sop-minimum",
    "protocol-resync",
    "precharge-evidence",
    "ai-boundary",
)


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


def _load_docs_module():
    """复用 check_docs 的锚点算法，避免第二套 slug 规则漂移。"""
    import importlib.util

    path = ROOT / ".github" / "scripts" / "check_docs.py"
    spec = importlib.util.spec_from_file_location("check_docs", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_entry_path(errors: list[str], concept_id: str, level: str, value: str, docs) -> None:
    path_text, _, anchor = value.partition("#")
    page = ROOT / path_text
    if not page.is_file():
        fail(errors, f"{concept_id}.{level}: 入口不存在：{value}")
        return
    if anchor and anchor not in docs.anchors_of(page):
        fail(errors, f"{concept_id}.{level}: 入口锚点不存在：{value}")


def check_ladder(errors: list[str], concept: dict[str, Any], docs) -> None:
    concept_id = concept["id"]
    for field in ("title", "bloom_ceiling", "mastery_evidence", "next", "ladder"):
        if field not in concept:
            fail(errors, f"{concept_id}: 骨干 KP 缺字段 {field}")
            return
    title = str(concept["title"]).strip()
    if not title or len(title) > 20:
        fail(errors, f"{concept_id}: title 必须是 1–20 字")
    stage_ref = concept.get("stage")
    stage_path = Path(stage_ref["path"]) if isinstance(stage_ref, dict) and stage_ref.get("path") else None
    if stage_path is None:
        fail(errors, f"{concept_id}: 缺 stage.path，无法判定「先懂」入口")
    elif stage_path.parent != Path("docs/stages") or stage_path.name not in MAINLINE_PAGES:
        # SPEC §6 W1「完整页只作查阅」：骨干 KP 的「先懂」入口必须是主线页，不能回漂到完整讲义。
        fail(errors, f"{concept_id}: stage.path 必须是主线页，当前 {stage_path.as_posix()}")
    ceiling = concept["bloom_ceiling"]
    if ceiling not in LADDER_LEVELS:
        fail(errors, f"{concept_id}: bloom_ceiling 必须是 L1–L5")
    elif int(ceiling[1]) < 3:
        fail(errors, f"{concept_id}: 主线 bloom_ceiling 必须 ≥ L3（当前 {ceiling}）")
    evidence = concept["mastery_evidence"]
    if not isinstance(evidence, list) or not evidence:
        fail(errors, f"{concept_id}: mastery_evidence 至少一项")
    else:
        for item in evidence:
            if item not in MASTERY_EVIDENCE:
                fail(errors, f"{concept_id}: mastery_evidence 含未知类型 {item!r}")
    if not isinstance(concept["next"], list):
        fail(errors, f"{concept_id}: next 必须是数组")
    ladder = concept["ladder"]
    if not isinstance(ladder, dict):
        fail(errors, f"{concept_id}: ladder 必须是对象")
        return
    if set(ladder) != set(LADDER_LEVELS):
        fail(errors, f"{concept_id}: ladder 必须恰好含 L1–L5，当前 {sorted(ladder)}")
        return
    for level in LADDER_LEVELS:
        node = ladder[level]
        if not isinstance(node, dict):
            fail(errors, f"{concept_id}.{level}: 必须是对象")
            continue
        missing = [field for field in LADDER_FIELDS if field not in node]
        if missing:
            fail(errors, f"{concept_id}.{level}: 缺字段 {missing}")
            continue
        for field in ("goal", "entry_path", "retrieve_task", "pass_check"):
            if not isinstance(node[field], str) or not node[field].strip():
                fail(errors, f"{concept_id}.{level}: {field} 不能为空")
        entry = node["entry_path"]
        if isinstance(entry, str) and entry.strip():
            check_entry_path(errors, concept_id, level, entry, docs)
            if level == "L3":
                page = Path(entry.partition("#")[0])
                if page.parent != Path("docs/stages") or page.name not in MAINLINE_PAGES:
                    fail(
                        errors,
                        f"{concept_id}.L3: 入口必须落在主线页，当前 {page.as_posix()}",
                    )
        media = node["media"]
        if not isinstance(media, list) or not media:
            fail(errors, f"{concept_id}.{level}: media 至少一项")
        else:
            for item in media:
                existing_path(errors, concept_id, f"{level} 媒介", item)


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

    missing = [concept_id for concept_id in BACKBONE_IDS if concept_id not in concepts]
    if missing:
        fail(errors, "骨干 KP 缺失或 id 被删：" + ", ".join(missing))
    else:
        docs = _load_docs_module()
        for concept_id in BACKBONE_IDS:
            check_ladder(errors, concepts[concept_id], docs)

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
        next_ids = row.get("next")
        if isinstance(next_ids, list):
            for next_id in next_ids:
                if next_id not in concepts:
                    fail(errors, f"{concept_id}: next 指向未知 KP {next_id!r}")
                if next_id == concept_id:
                    fail(errors, f"{concept_id}: next 不能指向自己")
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
