"""R04 reference implementation: safety correction contract.

Teaching slice ``R04-safety-correction``: a safety-architecture claim
("fault F is handled") is only as strong as the correction contract it
carries. This module pins that contract from the source-adoption table:

- OS07 (foxBMS): command/feedback identity enters the correction contract;
  trace the full state machine from registry / SPS / feedback / DIAG
  callbacks, including debounce configuration and tests; distinguish
  clear-flag, reset, and re-permission as three different recovery actions.

Contract rules (validate_contract):
- S1 ``conflated_recovery``: clear_flag / reset / re_permission must differ
  in actor or effect — same-actor-same-effect is one action in a trench coat.
- S2 ``missing_recovery_action``: all three recovery actions are required.
- S3 ``missing_command_identity``: the reaction command must name its actor.
- S4 ``missing_feedback_identity``: the expected feedback must name its
  source signal.
- S5 ``missing_debounce``: debounce_ms must be present and non-negative.
- S6 ``untested_transition``: every declared state transition needs a test
  reference.

evaluate(contract, observation) is gated on the contract itself (error-level
findings or no faults fail closed), then checks per item: observed feedback
matches the declared feedback identity, and every declared transition is
covered by a test observation. 清旗、复位、重新许可混淆或缺测的"安全处理"宣称
——沉默不是通过。

Only the standard library is used so the chapter can be recomputed end to end.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCENARIO_ID = "R04-safety-correction"
GENERATOR = "r04_safety_correction.py v1 (standard library)"

RECOVERY_ACTIONS = ("clear_flag", "reset", "re_permission")

SEED_CONTRACT: dict = {
    "contract_id": "hvil-teaching",
    "synthetic": True,
    "faults": [
        {
            "fault_id": "HVIL-open",
            "detection": {"source": "HVIL 回路电流采样"},
            "reaction": {"command": "断开主正/主负继电器", "actor": "BMS 安全状态机"},
            "feedback": {"signal": "主继电器状态回读=断开", "source": "继电器辅助触点回采"},
            "recovery": {
                "clear_flag": {"actor": "诊断服务（清零故障码）", "effect": "故障码清除，状态机仍在安全态"},
                "reset": {"actor": "下电重启流程", "effect": "状态机回初始态，故障锁存重评"},
                "re_permission": {"actor": "上电自检流程", "effect": "HVIL 闭环自检通过后重新许可高压"},
            },
            "debounce_ms": 100,
            "transitions": ["fault->safe", "safe->re_permission"],
            "transition_tests": {"fault->safe": "T-hvil-open", "safe->re_permission": "T-hvil-rearm"},
            "tests": ["T-hvil-open", "T-hvil-debounce-100ms", "T-hvil-rearm"],
            "boundary": "教学值合同：真实安全宣称须接真实状态机与 HIL 测试证据，本种子只钉纪律形状。",
        },
    ],
}

SEED_OBSERVATION: dict = {
    "feedback_matches": True,
    "transitions_covered": ["fault->safe", "safe->re_permission"],
}


def seed_contract() -> dict:
    return json.loads(json.dumps(SEED_CONTRACT, ensure_ascii=False))


def seed_observation() -> dict:
    return json.loads(json.dumps(SEED_OBSERVATION, ensure_ascii=False))


def validate_contract(contract: dict) -> list[dict]:
    findings: list[dict] = []
    for fault in contract.get("faults", []):
        label = fault.get("fault_id", "?")
        reaction = fault.get("reaction", {})
        if not reaction.get("actor", "").strip():
            findings.append({"kind": "missing_command_identity", "severity": "error",
                             "detail": f"{label}: reaction command needs an actor (OS07)"})
        feedback = fault.get("feedback", {})
        if not feedback.get("source", "").strip():
            findings.append({"kind": "missing_feedback_identity", "severity": "error",
                             "detail": f"{label}: feedback needs a source signal (OS07)"})
        debounce = fault.get("debounce_ms")
        if not isinstance(debounce, int) or isinstance(debounce, bool) or debounce < 0:
            findings.append({"kind": "missing_debounce", "severity": "error",
                             "detail": f"{label}: debounce_ms must be a non-negative integer"})
        recovery = fault.get("recovery", {})
        for action in RECOVERY_ACTIONS:
            if action not in recovery:
                findings.append({"kind": "missing_recovery_action", "severity": "error",
                                 "detail": f"{label}: recovery action {action!r} missing (OS07)"})
                continue
            entry = recovery[action]
            if (not isinstance(entry, dict)
                    or not entry.get("actor", "").strip()
                    or not entry.get("effect", "").strip()):
                findings.append({"kind": "empty_recovery_action", "severity": "error",
                                 "detail": f"{label}: recovery action {action!r} needs non-empty "
                                         "actor and effect"})
        present = [(a, recovery.get(a)) for a in RECOVERY_ACTIONS
                   if a in recovery and isinstance(recovery.get(a), dict)]
        signatures = [(a, (str(v.get("actor", "")).strip(), str(v.get("effect", "")).strip()))
                      for a, v in present]
        for i in range(len(signatures)):
            for j in range(i + 1, len(signatures)):
                (a_name, a_sig), (b_name, b_sig) = signatures[i], signatures[j]
                if a_sig == b_sig:
                    findings.append({"kind": "conflated_recovery", "severity": "error",
                                     "detail": f"{label}: {a_name!r} and {b_name!r} share actor+effect "
                                             "——清旗、复位、重新许可必须区分 (OS07)"})
        transitions = fault.get("transitions", [])
        if not transitions:
            findings.append({"kind": "no_declared_transition", "severity": "error",
                             "detail": f"{label}: a handled fault needs at least one declared "
                                     "state-machine transition"})
        transition_tests = fault.get("transition_tests", {})
        declared_tests = set(fault.get("tests", []))
        for transition in transitions:
            mapped = str(transition_tests.get(transition, "")).strip()
            if not mapped:
                findings.append({"kind": "untested_transition", "severity": "error",
                                 "detail": f"{label}: transition {transition!r} has no explicit test mapping"})
            elif mapped not in declared_tests:
                findings.append({"kind": "untested_transition", "severity": "error",
                                 "detail": f"{label}: transition {transition!r} maps to {mapped!r} "
                                         "which is not in declared tests"})
    return findings


def evaluate(contract: dict, observation: dict) -> dict:
    """Per-check fail-closed evaluation, gated on the contract itself."""
    findings = validate_contract(contract)
    faults = contract.get("faults", [])
    declared = {t for f in faults for t in f.get("transitions", [])}
    has_transitions = bool(declared)
    covered = set(observation.get("transitions_covered", []))
    checks = {
        "contract_valid": not any(f["severity"] == "error" for f in findings),
        "has_faults": bool(faults),
        "has_transitions": has_transitions,
        "feedback_matches": bool(observation.get("feedback_matches", False)),
        "transitions_tested": has_transitions and all(t in covered for t in declared),
    }
    verdict = "pass" if all(checks.values()) else "fail"
    return {
        "scenario_id": SCENARIO_ID,
        "checks": checks,
        "verdict": verdict,
        "boundary": "pass 只证明教学值合同下的身份区分与测试覆盖成立，不构成功能安全等级结论。",
    }


def build_report() -> dict:
    contract = seed_contract()
    return {
        "scenario_id": SCENARIO_ID,
        "generator": GENERATOR,
        "contract": contract,
        "validation": validate_contract(contract),
        "evaluation": evaluate(contract, seed_observation()),
    }


def write_artifacts(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "safety_correction.json").write_text(
        json.dumps(build_report(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write safety_correction.json")
    args = parser.parse_args(argv)
    try:
        if args.out:
            write_artifacts(args.out)
        else:
            report = build_report()
            print(json.dumps({
                "validation_findings": len(report["validation"]),
                "evaluation_verdict": report["evaluation"]["verdict"],
            }, ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(f"r04_safety_correction: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
