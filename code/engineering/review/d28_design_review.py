"""D28 reference implementation: design review packet + independent review.

Teaching slice ``D28-design-review``: the capstone discipline. A design
decision earns trust through a review PACKET (the full evidence bundle:
decision -> linked claims -> declared gaps -> fidelity floor) and an
INDEPENDENT review with three non-negotiables:

- I1 独立性: reviewer must not be the author. Self-review is drafting.
- I2 复跑: the reviewer reruns the packet assembly; the linked-claim set of
  the rerun must equal the original. A review that only reads the packet is
  a second author.
- I3 边界复述: the reviewer's first act is restating what the decision does
  NOT do, with an explicit boundary word (不能/不证明/边界/待验/不适用).

Plus two cross-cutting gates: linked claim ids must exist in the registry,
and the decision statement itself must pass the D27 global fidelity floor —
a design decision is a claim, and claims are subject to the ladder.

The seed decision (teaching values): 预充继电器粘连检测用电流残差判据
而非单纯计时——linking D23 (precharge HV) and D22 (diagnostic latch) claims,
blocked by D25's G02 (SRC06).

Only the standard library is used so the chapter can be recomputed end to end.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

SCENARIO_ID = "D28-design-review"
GENERATOR = "d28_design_review.py v1 (standard library)"

BOUNDARY_WORD = re.compile(r"不能|不代表|不证明|边界|待验|不适用")

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("d27_fidelity_ai", HERE.parent / "modeling" / "d27_fidelity_ai.py")
assert _spec is not None and _spec.loader is not None
d27 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = d27
_spec.loader.exec_module(d27)

SEED_PACKET: dict = {
    "decision_id": "D28-D1",
    "decision_statement": "预充继电器粘连检测采用电流残差判据而非单纯计时：计时只能证明时间到了，残差异常才指向粘连",
    "author": "设计线（本书作者）",
    "reviewer": "独立复核员（教学角色，须与作者不同人）",
    "linked_claims": ["D23-C01", "D22-C01"],
    "declared_gaps": ["G02"],
    "reviewer_boundary": "本决策不证明接触器批次质量，也不替代 SRC06 的产线EOL触点检测；边界：它只规定控制器内的判据选择，待验于 HIL 粘连故障注入",
}


def build_review_packet(root: Path) -> dict:
    """Assemble the teaching decision's evidence bundle from the registries."""
    claims = json.loads((root / "bms-book/engineering/claims.json").read_text(encoding="utf-8"))["claims"]
    by_id = {c["id"]: c for c in claims}
    linked = []
    for cid in SEED_PACKET["linked_claims"]:
        claim = by_id.get(cid)
        if claim:
            linked.append({"id": cid, "unit": claim["unit"], "anchor": claim.get("anchor", ""),
                           "statement": claim["statement"], "source_ids": claim.get("source_ids", [])})
    return {
        "scenario_id": SCENARIO_ID,
        **{k: v for k, v in SEED_PACKET.items() if k != "linked_claims"},
        "linked_claims": list(SEED_PACKET["linked_claims"]),
        "resolved_claims": linked,
        "registry_claim_total": len(claims),
    }


def audit_review(root: Path, packet: dict, rerun_packet: dict | None = None) -> dict:
    """Run I1–I3 plus the cross-cutting gates over a review packet.

    I2 is fail-closed: a rerun packet without provenance (the exact rerun
    command and who produced it) is treated as no rerun at all — comparing
    two copies of the same hand-built dict proves nothing.
    """
    findings: list[dict] = []
    if not packet.get("reviewer", "").strip() or packet.get("reviewer") == packet.get("author"):
        findings.append({"kind": "reviewer_not_independent", "severity": "error",
                         "unit": packet.get("decision_id", "?"),
                         "detail": "reviewer missing or identical to author"})
    if not BOUNDARY_WORD.search(packet.get("reviewer_boundary", "")):
        findings.append({"kind": "boundary_without_teeth", "severity": "error",
                         "unit": packet.get("decision_id", "?"),
                         "detail": "reviewer boundary restatement lacks an explicit boundary word"})
    floor = d27.check_claim("集总参数", packet.get("decision_statement", ""))
    for f in floor:
        findings.append({"kind": "decision_exceeds_fidelity", "severity": "error",
                         "unit": packet.get("decision_id", "?"), "detail": f["detail"]})

    claims = json.loads((root / "bms-book/engineering/claims.json").read_text(encoding="utf-8"))["claims"]
    known = {c["id"] for c in claims}
    linked = packet.get("linked_claims", [])
    for cid in linked:
        if cid not in known:
            findings.append({"kind": "unknown_claim_ref", "severity": "error",
                             "unit": cid, "detail": "linked claim not in registry"})

    if rerun_packet is None:
        findings.append({"kind": "rerun_evidence_missing", "severity": "error",
                         "unit": packet.get("decision_id", "?"),
                         "detail": "no rerun packet supplied — I2 requires a rerun, not a reading"})
    else:
        provenance = rerun_packet.get("provenance") or {}
        command = provenance.get("command", "")
        producer = provenance.get("produced_by", "")
        if not command or "d28_design_review.py" not in command:
            findings.append({"kind": "rerun_evidence_missing", "severity": "error",
                             "unit": packet.get("decision_id", "?"),
                             "detail": "rerun packet lacks the exact rerun command provenance"})
        if not producer or producer == packet.get("author"):
            findings.append({"kind": "rerun_not_independent", "severity": "error",
                             "unit": packet.get("decision_id", "?"),
                             "detail": "rerun producer missing or identical to author"})
        if sorted(rerun_packet.get("linked_claims", [])) != sorted(linked):
            findings.append({"kind": "rerun_diverged", "severity": "error",
                             "unit": packet.get("decision_id", "?"),
                             "detail": "rerun linked-claim set differs from packet"})

    errors = [f for f in findings if f["severity"] == "error"]
    return {
        "scenario_id": SCENARIO_ID,
        "generator": GENERATOR,
        "counts": {
            "decisions": 1,
            "linked_claims": len(linked),
            "resolved_claims": len(packet.get("resolved_claims", [])),
            "findings": len(findings),
            "errors": len(errors),
        },
        "findings": findings,
        "verdict": "fail" if errors else "pass",
        "boundary": "复核 verdict pass 只证明独立性、复跑一致与边界复述存在，不升级为产品结论。",
    }


def run_fresh_review(root: Path, out_dir: Path) -> dict:
    """Real independent rerun: spawn the CLI in a fresh process and load the
    packet it wrote; provenance records command and producer. Uses
    --packet-only so the child never recurses into another rerun."""
    import subprocess

    out_dir.mkdir(parents=True, exist_ok=True)
    script = HERE / "d28_design_review.py"
    command = f"{sys.executable} {script} --root {root} --packet-only --out {out_dir}"
    result = subprocess.run(
        [sys.executable, str(script), "--root", str(root), "--packet-only", "--out", str(out_dir)],
        capture_output=True, text=True, check=False, timeout=120,
        stdin=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise RuntimeError(f"fresh rerun failed: {result.stderr.strip()}")
    packet = json.loads((out_dir / "review_packet.json").read_text(encoding="utf-8"))
    packet["provenance"] = {"command": command, "produced_by": "fresh-process(d28 CLI)"}
    return packet


def write_artifacts(root: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    import tempfile

    packet = build_review_packet(root)
    with tempfile.TemporaryDirectory() as tmp:
        rerun = run_fresh_review(root, Path(tmp))
    audit = audit_review(root, packet, rerun_packet=rerun)
    (out_dir / "review_packet.json").write_text(
        json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "review_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--out", type=Path, help="write review_packet.json + review_audit.json")
    parser.add_argument("--packet-only", action="store_true",
                        help="only assemble and write the packet (no audit, no rerun)")
    args = parser.parse_args(argv)
    try:
        if args.packet_only:
            packet = build_review_packet(args.root)
            if args.out:
                args.out.mkdir(parents=True, exist_ok=True)
                (args.out / "review_packet.json").write_text(
                    json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
            else:
                print(json.dumps({"linked_claims": len(packet["linked_claims"])},
                                 ensure_ascii=False, indent=2))
        elif args.out:
            write_artifacts(args.root, args.out)
        else:
            import tempfile

            packet = build_review_packet(args.root)
            with tempfile.TemporaryDirectory() as tmp:
                rerun = run_fresh_review(args.root, Path(tmp))
            audit = audit_review(args.root, packet, rerun_packet=rerun)
            print(json.dumps(audit["counts"], ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(f"d28_design_review: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
