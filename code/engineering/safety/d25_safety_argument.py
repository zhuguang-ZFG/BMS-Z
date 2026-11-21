"""D25 reference implementation: safety argument structure + evidence-gap ledger.

Teaching slice ``D25-safety-argument``: P6.1 binds requirements to evidence
"without granting product qualification". A safety argument is a bipartite
graph: claims are supported by executable evidence, or blocked by DECLARED
gaps — a claim with neither is silent, and silence is the one thing a safety
argument must not contain.

Grounding: the source-adoption table's SRC06 row promises exactly this shape —
"可交完整论证结构和缺证据表". D25 delivers that structure as a method
artifact on THIS repository's own claims. It is not a standards compliance
argument: SRC06 (standard applicability, EOL/in-service records) is itself a
declared gap.

Audit rules over the argument graph:

- S1 ``silent_claim``: a claim with neither evidence nor gaps.
- S2 ``unresolved_evidence``: an evidence name that does not resolve to a
  ``def <name>(`` in any repository test file — fabricated evidence names are
  findings, not typos to forgive.
- S3 ``malformed_gap``: a gap missing blocking_source_id/owner/status, whose
  blocking_source_id is not an adopted source id (OS/DATA/EDU/CASE/SRC), or
  whose status is outside the allowed vocabulary.

The evidence-gap ledger is the actionable half: every gap names what it
blocks, which adopted source would close it, an owner, and a status. A gap
with no owner is a wish, not a plan.

Only the standard library is used so the chapter can be recomputed end to end.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCENARIO_ID = "D25-safety-argument"
GENERATOR = "d25_safety_argument.py v1 (standard library)"

ADOPTED_SOURCE_ID = re.compile(r"\b(?:OS\d{2}|DATA01|EDU01|CASE01|SRC\d{2})\b")
ALLOWED_GAP_STATUS = ("待补", "进行中", "已闭合", "不阻塞")

TEST_DEF = re.compile(r"def (test_[A-Za-z0-9_]+)\(")

SEED_ARGUMENT: dict = {
    "claims": [
        {
            "id": "A01",
            "statement": "传感链卡值失效时功率级仍被断开：FMEA 显式记录该模式，监控通道锁存故障且须服务清除",
            "evidence": [
                "test_fmea_declares_common_supply_gap_with_residual_risk",
                "test_safety_dtc_fault_latch_requires_service_clear",
            ],
            "gaps": ["G01", "G02"],
        },
        {
            "id": "A02",
            "statement": "总线永久静默只降不升：第 3 拍转 degraded 后绝不自行恢复，恢复须显式清除而非事后帧触发",
            "evidence": [
                "test_silent_bus_degrades_without_any_frame",
                "test_advance_to_never_recovers_in_degraded",
            ],
            "gaps": ["G02"],
        },
        {
            "id": "A03",
            "statement": "安全相关结论可复现：同一记录链重演得同一结果，换源重演被拒",
            "evidence": [
                "test_lineage_metadata_rejects_replay_with_different_source",
                "test_rejects_time_rollback_duplicate_sequence_bad_unit_and_unknown_field",
            ],
            "gaps": ["G02"],
        },
    ],
    "gaps": [
        {
            "id": "G01",
            "blocks": ["A01"],
            "what": "产品级保护阈值与诊断覆盖率的定量闭合",
            "blocking_source_id": "SRC01",
            "owner": "电芯资料线",
            "status": "待补",
            "next_action": "选定具体电芯料号，取手册修订与 OCV/温度原始数据，按 D03 的 12 字段回填阈值并做最弱单节定量闭合，签核后把状态推进为已闭合",
        },
        {
            "id": "G02",
            "blocks": ["A01", "A02", "A03"],
            "what": "标准适用性裁定、EOL 与在役原始记录链",
            "blocking_source_id": "SRC06",
            "owner": "系统安全线",
            "status": "待补",
            "next_action": "先裁定应用与标准适用性，再取得合法版本的具体条款，建立需求/测试/配置链与 EOL/在役原始记录，缺证据表原样随附论证引用",
        },
    ],
}


def build_argument() -> dict:
    """Return a deep copy of the seed safety argument (teaching values)."""
    return json.loads(json.dumps(SEED_ARGUMENT, ensure_ascii=False))


def _repo_test_defs(root: Path) -> set[str]:
    defs: set[str] = set()
    code_root = root / "code"
    if not code_root.is_dir():
        return defs
    for path in code_root.rglob("test_*.py"):
        try:
            defs.update(TEST_DEF.findall(path.read_text(encoding="utf-8")))
        except OSError:
            continue
    return defs


def _adopted_source_ids(root: Path) -> set[str]:
    table = root / "docs" / "superpowers" / "plans" / "bms-depth" / "source-adoption.md"
    if not table.is_file():
        return set()
    return set(ADOPTED_SOURCE_ID.findall(table.read_text(encoding="utf-8")))


def audit_argument(root: Path, graph: dict) -> dict:
    """Run S1–S3 over the argument graph and return findings + verdict."""
    test_defs = _repo_test_defs(root)
    adopted_ids = _adopted_source_ids(root)
    findings: list[dict] = []
    claims = graph.get("claims", [])
    gaps = graph.get("gaps", [])
    gap_ids = {g.get("id") for g in gaps}

    evidence_total = 0
    for claim in claims:
        cid = claim.get("id", "?")
        evidence = claim.get("evidence", [])
        claim_gaps = [g for g in claim.get("gaps", []) if g]
        evidence_total += len(evidence)
        # S1 silence
        if not evidence and not claim_gaps:
            findings.append({
                "kind": "silent_claim", "severity": "error", "unit": cid,
                "detail": "claim has neither evidence nor declared gaps",
            })
        # dangling gap reference
        for gid in claim_gaps:
            if gid not in gap_ids:
                findings.append({
                    "kind": "malformed_gap", "severity": "error", "unit": cid,
                    "detail": f"claim references undeclared gap {gid!r}",
                })
        # S2 fabricated evidence
        for name in evidence:
            if name not in test_defs:
                findings.append({
                    "kind": "unresolved_evidence", "severity": "error", "unit": cid,
                    "detail": f"evidence {name!r} not found as a test def under code/",
                })

    claimed_gap_refs = {gid for claim in claims for gid in claim.get("gaps", []) if gid}
    for gap in gaps:
        gid = gap.get("id", "?")
        source_id = gap.get("blocking_source_id", "")
        owner = gap.get("owner", "")
        status = gap.get("status", "")
        source_ok = bool(source_id) and source_id in adopted_ids
        next_action = gap.get("next_action", "")
        if not source_ok or not owner or status not in ALLOWED_GAP_STATUS or not next_action:
            findings.append({
                "kind": "malformed_gap", "severity": "error", "unit": gid,
                "detail": "gap needs adopted blocking_source_id, owner, allowed status, next_action",
            })
        if gid not in claimed_gap_refs:
            findings.append({
                "kind": "orphan_gap", "severity": "error", "unit": gid,
                "detail": "gap declared but blocks no claim",
            })
        if not gap.get("blocks"):
            findings.append({
                "kind": "malformed_gap", "severity": "error", "unit": gid,
                "detail": "gap.blocks is empty",
            })

    # S4 symmetric closure: claim.gaps <-> gap.blocks must agree both ways,
    # otherwise the ledger and the argument graph silently drift apart.
    claim_gaps: dict[str, list[str]] = {}
    for claim in claims:
        cid = claim.get("id", "?")
        claim_gaps[cid] = [g for g in claim.get("gaps", []) if g]
    for claim in claims:
        cid = claim.get("id", "?")
        for gid in claim_gaps.get(cid, []):
            gap = next((g for g in gaps if g.get("id") == gid), None)
            if gap is not None and cid not in gap.get("blocks", []):
                findings.append({
                    "kind": "asymmetric_gap", "severity": "error", "unit": cid,
                    "detail": f"claim declares gap {gid!r} but gap.blocks omits {cid!r}",
                })
    for gap in gaps:
        gid = gap.get("id", "?")
        for cid in gap.get("blocks", []):
            if cid not in claim_gaps or gid not in claim_gaps.get(cid, []):
                findings.append({
                    "kind": "asymmetric_gap", "severity": "error", "unit": gid,
                    "detail": f"gap blocks {cid!r} but that claim does not declare {gid!r}",
                })

    errors = [f for f in findings if f["severity"] == "error"]
    return {
        "scenario_id": SCENARIO_ID,
        "generator": GENERATOR,
        "counts": {
            "claims": len(claims),
            "gaps": len(gaps),
            "evidence": evidence_total,
            "findings": len(findings),
            "errors": len(errors),
        },
        "findings": findings,
        "verdict": "fail" if errors else "pass",
        "boundary": "论证结构完整 ≠ 标准符合；SRC06 本身是声明缺口，不是已备证据。",
    }


def evidence_gap_ledger(graph: dict) -> list[dict]:
    """The actionable缺证据表: sorted gaps with owner, status, and blocks."""
    rows = []
    for gap in graph.get("gaps", []):
        rows.append({
            "id": gap.get("id", "?"),
            "what": gap.get("what", ""),
            "blocks": gap.get("blocks", []),
            "blocking_source_id": gap.get("blocking_source_id", ""),
            "owner": gap.get("owner", ""),
            "status": gap.get("status", ""),
            "next_action": gap.get("next_action", ""),
        })
    rows.sort(key=lambda r: r["id"])
    return rows


def write_artifacts(root: Path, graph: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    audit = audit_argument(root, graph)
    (out_dir / "safety_argument.json").write_text(
        json.dumps({**audit, "argument": graph}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "evidence_gap_ledger.json").write_text(
        json.dumps(evidence_gap_ledger(graph), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--out", type=Path, help="write safety_argument.json + evidence_gap_ledger.json")
    args = parser.parse_args(argv)
    try:
        graph = build_argument()
        audit = audit_argument(args.root, graph)
        if args.out:
            write_artifacts(args.root, graph, args.out)
        else:
            print(json.dumps(audit["counts"], ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(f"d25_safety_argument: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
