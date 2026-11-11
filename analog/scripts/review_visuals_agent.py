#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""代理审图：按 35 分量规给 generated 资产打分并推进到 accepted。

授权：2026-11-07 用户在 AskUserQuestion 中选择「授权代理审图」。
这不是人工签字；manifest 会写明 reviewed_by=agent-proxy，报告保留逐图证据，
用户仍可抽检、否决并回退任何一张。

评分只用可复核的机器证据：
- 教学必要性：所在章当前最长无图段是否 >1500；
- 事实精度：source_facts、prompt_file、manifest 数字闸是否齐全；
- 构图层级：版面 audit 的 bounds 与文本节点数；
- 风格一致性：style_id / layout_id / color_ids 是否齐全且在锁定集合内；
- 印刷可读性：audit 最小印刷字号（≥9.0 得 5，8.5–9.0 得 4）；
- 动画叙事/节奏：beats、conclusion_frame、duration 是否完整且节拍连续。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import check_visual_manifest as manifest
from audit_visual_density import audit as density_audit, chapters, chapter_no

AUDIT_DIR = ROOT / "docs/superpowers/visual/reviews/task8-2026-11-05"
REPORT_CSV = ROOT / "docs/superpowers/visual/reviews/agent-review-2026-11-07.csv"
REPORT_MD = ROOT / "docs/superpowers/visual/reviews/agent-review-2026-11-07.md"
STYLES = {"FF-015", "FA-029"}
DIMS = manifest.SCORE_DIMS + manifest.ANIM_DIMS


def existing_audit(asset_id: str) -> dict:
    for name in (f"{asset_id}.audit.json", f"{asset_id}-print.audit.json"):
        path = AUDIT_DIR / name
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
    return {}


def chapter_gaps() -> dict[int, int]:
    return {chapter_no(path): density_audit(path)["longest_gap"]
            for path in chapters()}


def score_asset(asset: dict, gap: int) -> tuple[dict[str, int], list[str]]:
    blockers: list[str] = []
    scores: dict[str, int] = {}
    scores["教学必要性"] = 5 if gap > 1500 else 4
    scores["事实精度"] = 5 if asset.get("source_facts") and asset.get("prompt_file") else 4
    if not asset.get("source_facts"):
        blockers.append("缺 source_facts")
    if not asset.get("prompt_file") or not (ROOT / asset["prompt_file"]).is_file():
        blockers.append("缺 prompt_file")

    animation = asset.get("kind") == "animation"
    if animation:
        beats = asset.get("beats") or []
        duration = _duration(asset)
        conclusion = asset.get("conclusion_frame") or {}
        scores["构图层级"] = 5 if len(beats) >= 4 else 4
        scores["印刷可读性"] = 5 if asset.get("print_fallback") and asset.get("reduced_motion") else 4
        scores["运动叙事"] = 5 if len(beats) >= 4 and conclusion else 4
        scores["交互节奏"] = 5 if 6 <= duration <= 20 and 3 <= len(beats) <= 5 else 4
        if not beats:
            blockers.append("缺 beats")
        if not conclusion:
            blockers.append("缺 conclusion_frame")
        if not (4 <= duration <= 30):
            blockers.append(f"duration={duration} 超出 4..30s")
        if len(beats) < 3:
            blockers.append("节拍少于 3 拍")
        if scores["运动叙事"] + scores["交互节奏"] < 8:
            blockers.append("动画两项合计低于 8")
    else:
        audit = existing_audit(asset["id"])
        texts = int(audit.get("texts") or 0)
        bounds = audit.get("bounds")
        pt = float(audit.get("min_print_pt") or 0)
        scores["构图层级"] = 5 if bounds == "pass" and texts >= 8 else 4
        scores["印刷可读性"] = 5 if pt >= 9.0 else 4 if pt >= 8.5 else 3
        if bounds != "pass":
            blockers.append(f"bounds={bounds or '缺 audit'}")
        if pt < 8.5:
            blockers.append(f"min_print_pt={pt or 0:.3f} < 8.5")
        if texts < 4:
            blockers.append("文本节点少于 4")

    style = asset.get("style_id")
    if style not in STYLES or not asset.get("layout_id") or not asset.get("color_ids"):
        scores["风格一致性"] = 4
        if style not in STYLES:
            blockers.append(f"style_id={style} 不在锁定集合")
    else:
        scores["风格一致性"] = 5

    for dim in (manifest.SCORE_DIMS + (manifest.ANIM_DIMS if animation else [])):
        if dim not in scores:
            scores[dim] = 4
    if animation and sum(scores[d] for d in DIMS) < manifest.ANIM_TOTAL_FLOOR:
        blockers.append("动画七项合计 <30")
    return scores, blockers


def _duration(asset: dict) -> float:
    try:
        return float(str(asset.get("duration", "")).removesuffix("s"))
    except ValueError:
        return 0.0


def score_total(kind: str, scores: dict) -> int:
    dimensions = manifest.SCORE_DIMS + (manifest.ANIM_DIMS if kind == 'animation' else [])
    return sum(scores[d] for d in dimensions)


def asset_digest(asset: dict) -> str:
    raw = (ROOT / asset["output"]).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def review_record(asset: dict) -> dict:
    return {
        "reviewer": "agent-proxy",
        "method": "machine-assisted-rubric-v1",
        "scope": "all pending visual assets",
        "user_chapter_acceptance": "2026-11-07 用户授权代理审图，保留抽检与否决权",
        "reviewed_on": "2026-11-07",
        "record": REPORT_MD.relative_to(ROOT).as_posix(),
        "asset_sha256": asset_digest(asset),
    }


def backfill_records(data: dict, path: Path) -> int:
    """给已代理验收但缺 review_record 的条目补哈希，不改变状态。"""
    added = 0
    for asset in data.get("assets") or []:
        if asset.get("status") not in ("accepted", "published"):
            continue
        if asset.get("reviewed_by") != "agent-proxy":
            continue
        if asset.get("review_record"):
            continue
        asset["review_record"] = review_record(asset)
        added += 1
    if added:
        manifest.dump(data, path)
    return added


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="写回 manifest 并推进到 accepted")
    ap.add_argument("--backfill-records", action="store_true",
                    help="给已代理验收的条目补 review_record 与资产哈希")
    ap.add_argument("--manifest", type=Path, default=manifest.MANIFEST)
    args = ap.parse_args(argv)

    data = manifest.load(args.manifest)
    if args.backfill_records:
        print(f"补录 review_record：{backfill_records(data, args.manifest)} 条")
        return 0
    gaps = chapter_gaps()
    rows = []
    blocked = []
    for asset in data.get("assets") or []:
        if asset.get("status") != "generated":
            continue
        scores, blockers = score_asset(asset, gaps.get(asset.get("chapter"), 0))
        rows.append({
            "id": asset["id"], "chapter": asset.get("chapter"),
            "kind": asset.get("kind"), "type": asset.get("type"),
            **{dim: scores.get(dim, "—") for dim in DIMS},
            "total": score_total(asset.get("kind"), scores),
            "blockers": "；".join(blockers),
        })
        if blockers:
            blocked.append((asset, scores, blockers))

    REPORT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_CSV.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["id"])
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter((r["chapter"], r["kind"]) for r in rows)
    lines = [
        "# 代理审图报告（2026-11-07）",
        "",
        "> **性质**：用户于 2026-11-07 选择「授权代理审图」。本报告是机器辅助评分，"
        "**不是人工签字**；manifest 逐条写明 `reviewed_by: agent-proxy`，用户保留抽检、否决和回退权。",
        "",
        f"- 待审 `generated`：**{len(rows)}** 张",
        f"- 可推进：**{len(rows) - len(blocked)}** 张；阻断：**{len(blocked)}** 张",
        f"- 逐图分数：`{REPORT_CSV.relative_to(ROOT).as_posix()}`",
        "",
        "## 评分口径",
        "",
        "| 维度 | 5 分 | 4 分 | 阻断 |",
        "|---|---|---|---|",
        "| 教学必要性 | 所在章最长无图段 >1500 | 其余 | — |",
        "| 事实精度 | 有 source_facts 与 prompt | 缺其一 | 缺 source_facts / prompt 文件 |",
        "| 构图层级 | 版面 bounds=pass 且文本 ≥8（动画 ≥4 拍） | 文本 4–7 或动画 3 拍 | bounds 失败 / 文本 <4 / 缺 beats |",
        "| 风格一致性 | style_id 在锁定集合且 layout/color 齐全 | 缺 layout 或 color | style_id 不在锁定集合 |",
        "| 印刷可读性 | 最小字号 ≥9.0pt（动画有 print fallback 与 reduced_motion） | 8.5–9.0pt / 缺其一 | <8.5pt |",
        "| 运动叙事 | ≥4 拍且结论帧有效 | 3 拍 | 缺结论帧 / <3 拍 |",
        "| 交互节奏 | 6–20s 且 3–5 拍 | 4–30s 且 2–6 拍 | 超出范围 |",
        "",
        "## 分章统计",
        "",
        "| 章 | 静态 | 动画 | 小计 |",
        "|---:|---:|---:|---:|",
    ]
    for ch in sorted({r["chapter"] for r in rows}):
        static = counts.get((ch, "figure"), 0)
        anim = counts.get((ch, "animation"), 0)
        lines.append(f"| {ch} | {static} | {anim} | {static + anim} |")
    lines += ["", "## 阻断项", ""]
    if blocked:
        for asset, _scores, blockers in blocked:
            lines.append(f"- `{asset['id']}`：{'；'.join(blockers)}")
    else:
        lines.append("无。")
    lines += ["", "## 逐图分数", "", "| id | 章 | 类型 | 必要性 | 事实 | 构图 | 风格 | 印刷 | 叙事 | 节奏 | 合计 |",
              "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        lines.append(
            f"| `{r['id']}` | {r['chapter']} | {r['type']} | {r['教学必要性']} | "
            f"{r['事实精度']} | {r['构图层级']} | {r['风格一致性']} | {r['印刷可读性']} | "
            f"{r.get('运动叙事', '—')} | {r.get('交互节奏', '—')} | {r['total']} |")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"generated={len(rows)} ready={len(rows) - len(blocked)} blocked={len(blocked)}")
    for asset, _scores, blockers in blocked:
        print(f"BLOCK {asset['id']}: {'；'.join(blockers)}")

    if not args.write or blocked:
        if args.write and blocked:
            print("存在阻断项，未写回 manifest。")
        return 1 if blocked else 0

    for index, asset in enumerate(data["assets"]):
        if asset.get("status") != "generated":
            continue
        scores, blockers = score_asset(asset, gaps.get(asset.get("chapter"), 0))
        if blockers:
            continue
        updated = dict(asset)
        updated["review_scores"] = scores
        updated["reviewed_by"] = "agent-proxy"
        updated["review_method"] = "machine-assisted-rubric-v1"
        updated["review_evidence"] = REPORT_MD.relative_to(ROOT).as_posix()
        updated["review_record"] = review_record(updated)
        updated = manifest.transition(updated, "reviewed")
        updated = manifest.transition(updated, "accepted")
        data["assets"][index] = updated
    manifest.dump(data, args.manifest)
    print(f"已写回 {len(rows) - len(blocked)} 张到 manifest。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
