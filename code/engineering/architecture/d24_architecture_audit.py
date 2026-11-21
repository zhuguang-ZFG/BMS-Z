"""D24 reference implementation: architecture audit + open-source review protocol.

Teaching slice ``D24-architecture-audit``: P6.1 binds requirements to evidence
"without granting product qualification". This module is the audit half of that
discipline applied to our own engineering registry, and the same checklist is
the method for reviewing external open-source BMS repositories.

Audit rules (whole manifest, including planned units — the build only
topo-sorts the assembled subset, so these are NOT covered by the builder):

- R1 ``missing_prereq``: a unit references a prerequisite id absent from the
  manifest.
- R2 ``prereq_cycle``: the whole-manifest prerequisite graph has a cycle.
- R3 ``ungrounded_claim``: a claim with NEITHER executable evidence NOR
  source_ids. A locally synthesized structural contract (e.g. D03's 12-field
  requirements table, which its chapter declares a 结构工具) is honestly
  grounded by its tests alone; copying a sibling's source ids without
  provenance would be fabrication, not grounding.
- R4/R5 ``missing_artifact``: an experiment's script/tests file or a figure
  file is absent on disk (independent read, not trusting the builder).
- R6 ``planned_blocks_verified`` (warning): a planned unit is a prerequisite
  of a locally_verified unit — architecture risk, does not fail the audit.

The open-source review protocol is a six-question method artifact
(license / provenance / freshness / debounce / evidence / boundaries). Every
question carries a machine check: a repo-relative path that must exist and a
substring its text must contain. ``protocol_self_check`` executes those checks
for real — no auto-pass — and ``verify_snapshot`` pins the frozen open-source
snapshot (``docs/superpowers/plans/2026-11-08-bms-open-source-snapshot.json``)
by SHA-256. The protocol is a reviewing method, not a certification of any
external project.

Only the standard library is used so the chapter can be recomputed end to end.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCENARIO_ID = "D24-architecture-audit"
GENERATOR = "d24_architecture_audit.py v2 (standard library)"

SNAPSHOT_REL = "docs/superpowers/plans/2026-11-08-bms-open-source-snapshot.json"
SNAPSHOT_SHA256_16 = "252688ab4ab53800"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registries(root: Path) -> dict:
    eng = root / "bms-book" / "engineering"
    return {
        "manifest": _read_json(eng / "manifest.json"),
        "claims": _read_json(eng / "claims.json"),
        "experiments": _read_json(eng / "experiments.json"),
        "figures": _read_json(eng / "figures.json"),
    }


def audit_registry(root: Path) -> dict:
    """Run R1–R6 over the whole manifest and return findings + verdict."""
    reg = load_registries(root)
    units = reg["manifest"]["units"]
    claims = reg["claims"]["claims"]
    experiments = reg["experiments"]["experiments"]
    figures = reg["figures"]["figures"]
    findings: list[dict] = []

    ids = {unit["id"] for unit in units}
    by_id = {unit["id"]: unit for unit in units}

    # R1 missing prerequisite references
    for unit in units:
        for prereq in unit.get("prerequisites", []):
            if prereq not in ids:
                findings.append({
                    "kind": "missing_prereq",
                    "severity": "error",
                    "unit": unit["id"],
                    "detail": f"prerequisite {prereq!r} absent from manifest",
                })

    # R2 whole-manifest cycle detection (iterative DFS, three colors)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {uid: WHITE for uid in ids}
    for start in sorted(ids):
        if color[start] != WHITE:
            continue
        stack: list[tuple[str, iter]] = [(start, iter(by_id[start].get("prerequisites", [])))]
        color[start] = GRAY
        while stack:
            node, children = stack[-1]
            advanced = False
            for child in children:
                if child not in ids:
                    continue  # R1 already reported
                if color[child] == GRAY:
                    findings.append({
                        "kind": "prereq_cycle",
                        "severity": "error",
                        "unit": node,
                        "detail": f"prerequisite cycle through {child!r}",
                    })
                    continue
                if color[child] == WHITE:
                    color[child] = GRAY
                    stack.append((child, iter(by_id[child].get("prerequisites", []))))
                    advanced = True
                    break
            if not advanced:
                color[node] = BLACK
                stack.pop()

    # R3 claims grounded by neither evidence nor source_ids
    for claim in claims:
        if not claim.get("evidence") and not claim.get("source_ids"):
            findings.append({
                "kind": "ungrounded_claim",
                "severity": "error",
                "unit": claim["id"],
                "detail": "claim has neither evidence tests nor source_ids",
            })

    # R4 experiment artifacts on disk
    for exp in experiments:
        rel = exp.get("script")
        if rel and not (root / rel).is_file():
            findings.append({
                "kind": "missing_artifact",
                "severity": "error",
                "unit": exp["id"],
                "detail": f"script {rel!r} not found",
            })
        for rel in exp.get("tests", []):
            if not (root / rel).is_file():
                findings.append({
                    "kind": "missing_artifact",
                    "severity": "error",
                    "unit": exp["id"],
                    "detail": f"tests {rel!r} not found",
                })

    # R5 figure files on disk
    for figure in figures:
        rel = figure.get("file")
        if rel and not (root / rel).is_file():
            findings.append({
                "kind": "missing_artifact",
                "severity": "error",
                "unit": figure["id"],
                "detail": f"figure file {rel!r} not found",
            })

    # R6 planned unit blocking a verified unit (warning only)
    planned = {u["id"] for u in units if u.get("status") == "planned"}
    for unit in units:
        if unit.get("status") == "locally_verified":
            for prereq in unit.get("prerequisites", []):
                if prereq in planned:
                    findings.append({
                        "kind": "planned_blocks_verified",
                        "severity": "warning",
                        "unit": unit["id"],
                        "detail": f"verified unit depends on planned unit {prereq!r}",
                    })

    errors = [f for f in findings if f["severity"] == "error"]
    return {
        "scenario_id": SCENARIO_ID,
        "generator": GENERATOR,
        "counts": {
            "units": len(units),
            "claims": len(claims),
            "experiments": len(experiments),
            "figures": len(figures),
            "findings": len(findings),
            "errors": len(errors),
            "warnings": len(findings) - len(errors),
        },
        "findings": findings,
        "verdict": "fail" if errors else "pass",
    }


OPEN_SOURCE_REVIEW_PROTOCOL: list[dict] = [
    {
        "dimension": "license",
        "question": "这段代码以什么条件授予你使用权？",
        "demand": "许可证文件存在且条款与你计划的使用方式兼容",
        "check": {"path": "LICENSE", "must_contain": "CC BY-SA 4.0"},
    },
    {
        "dimension": "provenance",
        "question": "这些数字/代码从哪来，谁能改写历史？",
        "demand": "每个冻结数字有 generator 与指纹，改动即指纹漂移",
        "check": {"path": "bms-book/engineering/manifest.json", "must_contain": '"fingerprint"'},
    },
    {
        "dimension": "freshness",
        "question": "完整性通过但数据过期，系统会说什么？",
        "demand": "陈旧度判定与完整性判定分列，不以 CRC 通过冒充数据新鲜",
        "check": {"path": "code/engineering/bus/d19_bus_data.py", "must_contain": "def classify_counter"},
    },
    {
        "dimension": "debounce",
        "question": "故障确认按帧、按评估还是按时间？门限各是多少？",
        "demand": "确认/治愈门限以评估次数明示，不偷用其他状态机的拍数",
        "check": {"path": "code/engineering/diagnostics/d22_diagnostics.py", "must_contain": "MONITOR_CONFIG"},
    },
    {
        "dimension": "evidence",
        "question": "每条声明的测试名解析得到吗？",
        "demand": "声明 evidence 名称在单元测试文件内可解析",
        "check": {"path": "tools/check_engineering.py", "must_contain": "not found in"},
    },
    {
        "dimension": "boundaries",
        "question": "哪些语义被显式声明为不互替？",
        "demand": "跨单元借用处 axis_boundary 显式声明",
        "check": {"path": "bms-book/engineering/D22-诊断刷写与生命周期.md", "must_contain": "axis_boundary"},
    },
]


def open_source_review_protocol() -> list[dict]:
    return [dict(item) for item in OPEN_SOURCE_REVIEW_PROTOCOL]


def verify_snapshot(root: Path) -> dict:
    """Pin the frozen open-source snapshot by SHA-256; drift is a fail."""
    path = root / SNAPSHOT_REL
    if not path.is_file():
        return {"path": SNAPSHOT_REL, "ok": False, "detail": "snapshot missing"}
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    return {
        "path": SNAPSHOT_REL,
        "ok": digest == SNAPSHOT_SHA256_16,
        "observed_sha256_16": digest,
        "expected_sha256_16": SNAPSHOT_SHA256_16,
        "detail": "snapshot frozen" if digest == SNAPSHOT_SHA256_16 else "snapshot drifted",
    }


def protocol_self_check(root: Path) -> dict:
    """Execute every protocol check for real; any failure fails the check."""
    rows = []
    ok = True
    for item in open_source_review_protocol():
        check = item["check"]
        path = root / check["path"]
        present = path.is_file()
        content_ok = None
        if present and check.get("must_contain") is not None:
            content_ok = check["must_contain"] in path.read_text(encoding="utf-8")
        row_ok = present and (content_ok is None or content_ok)
        ok = ok and row_ok
        rows.append({
            "dimension": item["dimension"],
            "question": item["question"],
            "demand": item["demand"],
            "path": check["path"],
            "must_contain": check.get("must_contain"),
            "artifact_present": present,
            "content_ok": content_ok,
            "ok": row_ok,
        })
    snapshot = verify_snapshot(root)
    ok = ok and snapshot["ok"]
    return {
        "scenario_id": SCENARIO_ID,
        "rows": rows,
        "snapshot": snapshot,
        "verdict": "pass" if ok else "fail",
        "boundary": "协议是审读方法，不是对任何外部项目的认证；本地映射仅为工作样例。",
    }


def traceability_matrix(root: Path) -> dict:
    """Forward traceability: source -> unit -> claim -> evidence -> experiment.

    The gates validate each link in isolation; the matrix is the cross-cutting
    view that lets a reviewer (or a reader learning the discipline) walk one
    requirement end to end. One row per active claim, never silently dropped:
    a claim without resolvable evidence stays in the matrix with
    ``evidence_resolved: false`` so the gap is visible rather than hidden.
    """
    reg = load_registries(root)
    claims = reg["claims"]["claims"]
    experiments = reg["experiments"]["experiments"]
    exp_by_unit: dict[str, list[str]] = {}
    for exp in experiments:
        exp_by_unit.setdefault(exp.get("unit", ""), []).append(exp["id"])
    exp_tests: dict[str, list[str]] = {exp["id"]: exp.get("tests", []) for exp in experiments}

    rows = []
    for claim in claims:
        if claim.get("status", "active") != "active":
            continue
        uid = claim.get("unit", "")
        evidence = claim.get("evidence", [])
        resolved = True
        for name in evidence:
            found = False
            for eid in exp_by_unit.get(uid, []):
                for test_file in exp_tests.get(eid, []):
                    path = root / test_file
                    if path.is_file() and f"def {name}(" in path.read_text(encoding="utf-8"):
                        found = True
                        break
                if found:
                    break
            if not found:
                resolved = False
                break
        rows.append({
            "source_ids": claim.get("source_ids", []),
            "unit": uid,
            "claim": claim["id"],
            "anchor": claim.get("anchor", ""),
            "evidence": evidence,
            "evidence_resolved": resolved,
            "experiments": exp_by_unit.get(uid, []),
        })
    rows.sort(key=lambda r: (",".join(r["source_ids"]), r["unit"], r["claim"]))
    unresolved = [r["claim"] for r in rows if not r["evidence_resolved"] and r["evidence"]]
    return {
        "scenario_id": SCENARIO_ID,
        "counts": {
            "rows": len(rows),
            "active_claims": sum(1 for c in claims if c.get("status", "active") == "active"),
            "unresolved_evidence": len(unresolved),
        },
        "unresolved": unresolved,
        "rows": rows,
    }


def write_artifacts(report: dict, self_check: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "audit_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "protocol_self_check.json").write_text(
        json.dumps(self_check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--out", type=Path, help="write audit_report.json + protocol_self_check.json")
    parser.add_argument("--matrix", type=Path, help="write traceability_matrix.json")
    args = parser.parse_args(argv)
    try:
        report = audit_registry(args.root)
        self_check = protocol_self_check(args.root)
        if args.out:
            write_artifacts(report, self_check, args.out)
        elif args.matrix:
            args.matrix.parent.mkdir(parents=True, exist_ok=True)
            args.matrix.write_text(
                json.dumps(traceability_matrix(args.root), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"traceability matrix -> {args.matrix}")
        else:
            print(json.dumps({
                "audit": report["counts"],
                "self_check_verdict": self_check["verdict"],
            }, ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(f"d24_architecture_audit: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
