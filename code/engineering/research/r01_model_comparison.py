"""R01 reference implementation: electrochemical model comparison protocol.

Teaching slice ``R01-model-comparison``: research claims like "model X agrees
with reference Y" are only as strong as the comparison protocol. This module
pins the protocol that the source-adoption table demands for OS01 (PyBaMM:
frozen runnable version, grid/tolerance study, independent reference, energy
integral cross-check) and CASE01 (PyBaMM#5072/5205: analytic ODE baseline
covering endpoint / discontinuous-event / both-sides cases, and an explicit
answer to whether the original MWE is actually reproduced).

Protocol rules (validate_spec):
- P1 ``unfrozen_model``: frozen_version must name a pinned version/commit.
- P2 ``missing_tolerance`` / ``bad_tolerance``: v_rel and q_abs tolerances
  must exist and be positive.
- P3 ``unknown_reference_kind``: reference must be analytic or
  independent_impl — "same authors' other run" is not a reference.
- P4 ``incomplete_event_baseline``: event_cases must cover endpoint,
  discontinuity, and both_sides (CASE01 三件套).
- P5 ``bad_mwe_status``: reproduces_mwe is three-valued yes/no/unknown;
  "unknown" is an honest answer, "maybe" is not an answer.

evaluate(spec, observation) fails closed per check: voltage error, capacity
error, energy integral, and every declared event case must pass. A missing
event case in the observation fails — silence is not a pass.

Only the standard library is used so the chapter can be recomputed end to end.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCENARIO_ID = "R01-model-comparison"
GENERATOR = "r01_model_comparison.py v1 (standard library)"

REQUIRED_EVENT_CASES = ("endpoint", "discontinuity", "both_sides")
ALLOWED_REFERENCE_KINDS = ("analytic", "independent_impl")
ALLOWED_MWE_STATUS = ("yes", "no", "unknown")
# P1 pin discipline: a real frozen version is a release tag (v23.4 /
# 23.4) or a 40-hex commit. Anything else only passes if the spec declares
# itself synthetic — a placeholder must never masquerade as a frozen version.
PIN_PATTERNS = (
    re.compile(r"^v?\d+\.\d+(\.\d+)?([+-][0-9A-Za-z.+-]+)?$"),
    re.compile(r"^[0-9a-f]{40}$"),
)

SEED_SPEC: dict = {
    "model_id": "SPMe-teaching",
    "frozen_version": "pybamm-teach-0.x-frozen-2026-11",
    "synthetic": True,
    "tolerances": {"v_rel": 0.01, "q_abs": 0.002},
    "reference": {"kind": "analytic", "id": "D02-analytic-OCV-RC"},
    "energy_integral": True,
    "event_cases": ["endpoint", "discontinuity", "both_sides"],
    "reproduces_mwe": "unknown",
    "pybamm_integration": "unverified",
    "boundary": "教学值协议：真实对比须换 OS01 冻结版本与独立参考实现，本种子只钉纪律形状。",
}

SEED_OBSERVATION: dict = {
    "max_v_rel_err": 0.0042,
    "max_q_abs_err": 0.0009,
    "energy_err_ok": True,
    "event_cases_passed": ["endpoint", "discontinuity", "both_sides"],
}


def seed_spec() -> dict:
    return json.loads(json.dumps(SEED_SPEC, ensure_ascii=False))


def seed_observation() -> dict:
    return json.loads(json.dumps(SEED_OBSERVATION, ensure_ascii=False))


def validate_spec(spec: dict) -> list[dict]:
    findings: list[dict] = []
    frozen = spec.get("frozen_version", "").strip()
    if not frozen:
        findings.append({"kind": "unfrozen_model", "severity": "error",
                         "detail": "frozen_version must pin a version/commit"})
    elif not any(p.match(frozen) for p in PIN_PATTERNS) and spec.get("synthetic") is not True:
        findings.append({"kind": "placeholder_version", "severity": "error",
                         "detail": f"{frozen!r} is not a release tag or 40-hex commit; "
                                   "declare synthetic=True (strict boolean) or pin a real version"})
    tolerances = spec.get("tolerances", {})
    for key in ("v_rel", "q_abs"):
        if key not in tolerances:
            findings.append({"kind": "missing_tolerance", "severity": "error",
                             "detail": f"tolerance {key!r} missing"})
        elif tolerances[key] <= 0:
            findings.append({"kind": "bad_tolerance", "severity": "error",
                             "detail": f"tolerance {key!r} must be positive"})
    if spec.get("reference", {}).get("kind") not in ALLOWED_REFERENCE_KINDS:
        findings.append({"kind": "unknown_reference_kind", "severity": "error",
                         "detail": "reference.kind must be analytic or independent_impl"})
    missing_events = [c for c in REQUIRED_EVENT_CASES
                      if c not in spec.get("event_cases", [])]
    if missing_events:
        findings.append({"kind": "incomplete_event_baseline", "severity": "error",
                         "detail": f"event_cases missing {missing_events!r}"})
    if spec.get("reproduces_mwe") not in ALLOWED_MWE_STATUS:
        findings.append({"kind": "bad_mwe_status", "severity": "error",
                         "detail": "reproduces_mwe must be yes/no/unknown — maybe is not an answer"})
    return findings


def evaluate(spec: dict, observation: dict) -> dict:
    """Per-check fail-closed evaluation against the declared tolerances.

    Gated on the protocol itself: any error-level validation finding (or no
    declared event cases) fails closed — an invalid protocol cannot pass.
    """
    findings = validate_spec(spec)
    declared = spec.get("event_cases", [])
    checks = {
        "protocol_valid": not any(f["severity"] == "error" for f in findings),
        "has_event_cases": bool(declared),
        "v_rel": observation.get("max_v_rel_err", float("inf")) <= spec.get("tolerances", {}).get("v_rel", 0.0),
        "q_abs": observation.get("max_q_abs_err", float("inf")) <= spec.get("tolerances", {}).get("q_abs", 0.0),
        "energy_integral": bool(observation.get("energy_err_ok", False))
        if spec.get("energy_integral") else True,
    }
    passed = set(observation.get("event_cases_passed", []))
    checks["event_cases"] = all(c in passed for c in declared)
    verdict = "pass" if all(checks.values()) else "fail"
    return {
        "scenario_id": SCENARIO_ID,
        "checks": checks,
        "verdict": verdict,
        "boundary": "pass 只证明在此容差下与指定参考一致，不证明模型在声明域外成立。",
    }


def build_report() -> dict:
    spec = seed_spec()
    return {
        "scenario_id": SCENARIO_ID,
        "generator": GENERATOR,
        "spec": spec,
        "validation": validate_spec(spec),
        "evaluation": evaluate(spec, seed_observation()),
    }


def write_artifacts(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "model_comparison.json").write_text(
        json.dumps(build_report(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write model_comparison.json")
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
        print(f"r01_model_comparison: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
