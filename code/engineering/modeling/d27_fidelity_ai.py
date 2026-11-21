"""D27 reference implementation: fidelity ladder + AI-assistance provenance.

Teaching slice ``D27-fidelity-ai``: P6.1 binds requirements to evidence
"without granting product qualification". Two disciplines, one module:

1. 保真阶梯 (fidelity ladder): models are ranked by what they may claim.
   Every level carries an explicit 外推禁止 list — patterns a claim must not
   contain at that level. Grounding: the source-adoption table puts D27 on
   OS01 (PyBaMM, frozen runnable version against independent reference) and
   OS08 (BLAST, condition-domain/extrapolation limits enter the contract).

2. AI 辅助留痕 (AI-assistance provenance): AI output may accelerate drafting,
   it is never evidence. Every AI-assisted artifact must carry a named human
   reviewer, a task boundary statement with teeth (必须含 不能/不证明/边界/
   待验/不适用), and a repo-relative artifact path that exists.

Audit rules over AI records:
- A1 ``unreviewed_ai_output``: reviewer empty — anonymous AI output is banned.
- A2 ``missing_artifact``: the artifact path does not exist in the repo.
- A3 ``boundary_without_teeth``: boundary statement lacks an explicit
  boundary word — "随便看看" is not a boundary.

Only the standard library is used so the chapter can be recomputed end to end.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCENARIO_ID = "D27-fidelity-ai"
GENERATOR = "d27_fidelity_ai.py v1 (standard library)"

BOUNDARY_WORD = re.compile(r"不能|不代表|不证明|边界|待验|不适用")

# Level-independent forbiddens: no model at ANY fidelity may make these
# claims. Per-level lists add restrictions on top of this floor.
GLOBAL_FORBIDDEN = ("寿命预测", "保修", "产线放行", "功能安全结论", "安全结论")

FIDELITY_LADDER: list[dict] = [
    {
        "name": "解析教学模型",
        "domain": "一阶端电压/RC 教学算例，机理示意与公式推导",
        "calibration": "不需要（教学常数明示来源）",
        "extrapolation_forbidden": ["寿命预测", "料号级定量", "保修", "产线"],
    },
    {
        "name": "集总参数",
        "domain": "曲线级 OCV/内阻/短时时常数拟合，滤波器整定与仿真对照",
        "calibration": "需要独立留出数据（B05/D14 纪律）",
        "extrapolation_forbidden": ["十年寿命", "外推到未标定温度谱", "直接等同实测"],
    },
    {
        "name": "分布式热耦合",
        "domain": "单体间温差与冷却路径的整包级热行为",
        "calibration": "需要实测温度谱对照与网格/容差研究",
        "extrapolation_forbidden": ["老化真值", "几何变化充老化结论", "安全结论"],
    },
    {
        "name": "场模型",
        "domain": "电极/电解质空间分布的机理级研究",
        "calibration": "需要独立参考实现与参数来源链（OS01 合同）",
        "extrapolation_forbidden": ["直接等同实测", "未经标定的产品宣称", "跳过独立参考"],
    },
]


def fidelity_ladder() -> list[dict]:
    return [dict(level, extrapolation_forbidden=list(level["extrapolation_forbidden"]))
            for level in FIDELITY_LADDER]


def check_claim(level_name: str, claim_text: str) -> list[dict]:
    """Match a claim against the global floor + its ladder level's forbiddens."""
    findings = [
        {"kind": "claim_exceeds_fidelity", "severity": "error", "unit": level_name,
         "detail": f"claim contains globally forbidden pattern {pat!r}"}
        for pat in GLOBAL_FORBIDDEN if pat in claim_text
    ]
    level = next((lvl for lvl in FIDELITY_LADDER if lvl["name"] == level_name), None)
    if level is None:
        findings.append({"kind": "unknown_fidelity_level", "severity": "error",
                         "detail": f"level {level_name!r} not in ladder"})
        return findings
    findings.extend(
        {"kind": "claim_exceeds_fidelity", "severity": "error", "unit": level_name,
         "detail": f"claim contains forbidden pattern {pat!r} for level {level_name!r}"}
        for pat in level["extrapolation_forbidden"] if pat in claim_text
    )
    return findings


SEED_AI_RECORDS: list[dict] = [
    {
        "task": "起草 D27 章节的保真阶梯表述",
        "tool": "LLM",
        "reviewer": "本书作者（人类）",
        "date": "2026-11-18",
        "artifact": "bms-book/engineering/D27-高保真模型与AI辅助.md",
        "boundary": "AI 只参与起草措辞；阶梯结构、外推禁止项与全部断言由人审定，AI 输出不能作为任何 claim 的证据",
    },
    {
        "task": "Book II 工程深研登记落地（D21–D28、R01–R04 登记对齐）",
        "tool": "LLM",
        "reviewer": "本书作者（人类）",
        "date": "2026-11-20",
        "artifact": "bms-book/engineering/D27-高保真模型与AI辅助.md",
        "boundary": "AI 只起草与登记措辞；D21–D28、R01–R04 的身份登记与断言由人审阅，AI 输出不能作为任何 claim 的证据",
    },
]


def seed_ai_records() -> list[dict]:
    return [dict(record) for record in SEED_AI_RECORDS]


def audit_ai_records(root: Path, records: list[dict]) -> dict:
    findings: list[dict] = []
    for record in records:
        rid = record.get("task", "?")[:24]
        if not record.get("reviewer", "").strip():
            findings.append({"kind": "unreviewed_ai_output", "severity": "error", "unit": rid,
                             "detail": "anonymous AI output is banned"})
        artifact = record.get("artifact", "")
        if not artifact or not (root / artifact).is_file():
            findings.append({"kind": "missing_artifact", "severity": "error", "unit": rid,
                             "detail": f"artifact {artifact!r} not found"})
        if not BOUNDARY_WORD.search(record.get("boundary", "")):
            findings.append({"kind": "boundary_without_teeth", "severity": "error", "unit": rid,
                             "detail": "boundary statement lacks an explicit boundary word"})
    errors = [f for f in findings if f["severity"] == "error"]
    return {
        "scenario_id": SCENARIO_ID,
        "generator": GENERATOR,
        "counts": {"records": len(records), "findings": len(findings), "errors": len(errors)},
        "findings": findings,
        "verdict": "fail" if errors else "pass",
        "boundary": "AI 输出永远不是证据；验证责任在人，留痕只证明责任链存在。",
    }


def build_report(root: Path) -> dict:
    return {
        "scenario_id": SCENARIO_ID,
        "generator": GENERATOR,
        "ladder_levels": len(fidelity_ladder()),
        "ai_audit": audit_ai_records(root, seed_ai_records()),
    }


def write_artifacts(root: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "fidelity_audit.json").write_text(
        json.dumps(build_report(root), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--out", type=Path, help="write fidelity_audit.json")
    args = parser.parse_args(argv)
    try:
        if args.out:
            write_artifacts(args.root, args.out)
        else:
            print(json.dumps(build_report(args.root)["ai_audit"]["counts"],
                             ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(f"d27_fidelity_ai: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
