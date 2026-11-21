"""R03 reference implementation: aging cross-domain validation contract.

Teaching slice ``R03-aging-domain``: an aging / degradation validation claim
("model predicts capacity fade under conditions C") is only as strong as the
domain contract it carries. This module pins that contract from the
source-adoption table:

- OS03 (liionpack): a pack geometry/topology change cannot serve as aging
  ground truth; freeze compatible dependencies; evidence per KCL/KVL node
  with the weakest link named.
- OS08 (BLAST): condition-domain and extrapolation limits enter the
  contract; calendar/cycle components must be separated or compensated;
  each model (e.g. the Kokam quick-calc) carries its own identity; without
  verified external data the empirical claim cannot be closed.

Contract rules (validate_claim):
- D1 ``geometry_not_truth``: ground truth of kind pack_geometry_change is
  rejected — geometry change is not aging truth (OS03).
- D2 ``external_unverified_truth``: ground truth of kind external_unverified
  is rejected — without an availability check the empirical claim stays open
  (OS08).
- D3 ``unresolved_component_mix``: calendar and cycle components must each
  be separated or compensated; unresolved mixing is not cycle-aging evidence.
- D4 ``missing_model_identity``: every model needs a version and a
  domain_note (Kokam 快算另建模型身份).
- D5 ``empty_condition_domain``: temp_c / soc / c_rate bounds must be
  declared — an undeclared domain invites silent extrapolation.

evaluate(claim, observation) is gated on the contract (error-level findings
or no models fail closed), then checks per item: every observed condition
inside the declared domain, and capacity error within tolerance. Extrapolate
silently and the verdict is fail.

Only the standard library is used so the chapter can be recomputed end to end.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCENARIO_ID = "R03-aging-domain"
GENERATOR = "r03_aging_domain.py v1 (standard library)"

ALLOWED_GT_KINDS = ("cell_level_test", "field_data")
ALLOWED_COMPONENT_STATES = ("separated", "compensated")
DOMAIN_AXES = ("temp_c", "soc", "c_rate")

SEED_CLAIM: dict = {
    "claim_id": "aging-fade-teaching",
    "synthetic": True,
    "condition_domain": {"temp_c": [15.0, 45.0], "soc": [0.2, 0.9], "c_rate": [0.2, 1.5]},
    "ground_truth": {"kind": "cell_level_test", "source_id": "D15-synthetic-calendar-cycle"},
    "components": {"calendar": "separated", "cycle": "separated"},
    "models": [
        {"id": "semi-empirical-fade", "version": "teach-1.0",
         "domain_note": "仅覆盖声明温度/SOC/C-rate 域内的容量衰减"},
    ],
    "tolerance_capacity_rel": 0.02,
    "boundary": "教学值合同：真实老化验证须换核过可用性的外部数据与真电芯试验，本种子只钉纪律形状。",
}

SEED_OBSERVATION: dict = {
    "conditions": {"temp_c": 25.0, "soc": 0.5, "c_rate": 0.5},
    "max_capacity_rel_err": 0.008,
}


def seed_claim() -> dict:
    return json.loads(json.dumps(SEED_CLAIM, ensure_ascii=False))


def seed_observation() -> dict:
    return json.loads(json.dumps(SEED_OBSERVATION, ensure_ascii=False))


def validate_claim(claim: dict) -> list[dict]:
    findings: list[dict] = []
    gt = claim.get("ground_truth", {})
    if gt.get("kind") == "pack_geometry_change":
        findings.append({"kind": "geometry_not_truth", "severity": "error",
                         "detail": "pack geometry/topology change is not aging ground truth (OS03)"})
    if gt.get("kind") == "external_unverified":
        findings.append({"kind": "external_unverified_truth", "severity": "error",
                         "detail": "external data without an availability check cannot close the claim (OS08)"})
    elif gt.get("kind") not in ALLOWED_GT_KINDS:
        findings.append({"kind": "unknown_ground_truth_kind", "severity": "error",
                         "detail": f"ground_truth.kind {gt.get('kind')!r} not recognised"})
    if gt.get("kind") == "field_data":
        if gt.get("verified_availability") is not True:
            findings.append({"kind": "unverified_field_data", "severity": "error",
                             "detail": "field_data needs verified_availability=True (strict boolean) "
                                       "with a traceable source — an unverified field claim cannot "
                                       "close the empirical claim (OS08)"})
        elif not gt.get("source_id", "").strip():
            findings.append({"kind": "untraceable_field_data", "severity": "error",
                             "detail": "field_data needs a non-empty traceable source_id"})
    components = claim.get("components", {})
    for comp in ("calendar", "cycle"):
        state = components.get(comp)
        if state not in ALLOWED_COMPONENT_STATES:
            findings.append({"kind": "unresolved_component_mix", "severity": "error",
                             "detail": f"component {comp!r} is {state!r}; "
                                     "calendar/cycle must both be separated or compensated (OS08)"})
    for model in claim.get("models", []):
        if not model.get("version", "").strip() or not model.get("domain_note", "").strip():
            findings.append({"kind": "missing_model_identity", "severity": "error",
                             "detail": f"model {model.get('id')!r} needs version and domain_note (OS08)"})
    domain = claim.get("condition_domain", {})
    if not domain:
        findings.append({"kind": "empty_condition_domain", "severity": "error",
                         "detail": "declare temp_c/soc/c_rate bounds — an undeclared domain invites extrapolation"})
    else:
        for axis in DOMAIN_AXES:
            bounds = domain.get(axis)
            malformed = (
                not isinstance(bounds, (list, tuple)) or len(bounds) != 2
                or not all(isinstance(b, (int, float)) and not isinstance(b, bool) for b in bounds)
            )
            if malformed:
                findings.append({"kind": "malformed_condition_domain", "severity": "error",
                                 "detail": f"domain axis {axis!r} must be [lo, hi] numerics"})
            elif bounds[0] >= bounds[1]:
                findings.append({"kind": "malformed_condition_domain", "severity": "error",
                                 "detail": f"domain axis {axis!r} has reversed or empty bounds {bounds!r}"})
    return findings


def _in_range(bounds: object, value: object) -> bool:
    if (not isinstance(bounds, (list, tuple)) or len(bounds) != 2
            or not all(isinstance(b, (int, float)) and not isinstance(b, bool) for b in bounds)
            or bounds[0] >= bounds[1]
            or not isinstance(value, (int, float)) or isinstance(value, bool)):
        return False
    return bounds[0] <= value <= bounds[1]


def evaluate(claim: dict, observation: dict) -> dict:
    """Per-check fail-closed evaluation, gated on the contract itself."""
    findings = validate_claim(claim)
    domain = claim.get("condition_domain", {})
    conditions = observation.get("conditions", {})
    within = all(_in_range(domain.get(axis), conditions.get(axis)) for axis in DOMAIN_AXES)
    checks = {
        "claim_valid": not any(f["severity"] == "error" for f in findings),
        "has_models": bool(claim.get("models")),
        "within_domain": within,
        "capacity_error": abs(observation.get("max_capacity_rel_err", float("inf")))
        <= claim.get("tolerance_capacity_rel", 0.0),
    }
    verdict = "pass" if all(checks.values()) else "fail"
    return {
        "scenario_id": SCENARIO_ID,
        "checks": checks,
        "verdict": verdict,
        "boundary": "pass 只证明观测条件落在声明域内且容量误差达标，不证明域外推成立；外部数据未核可用性前实证保持开放。",
    }


def build_report() -> dict:
    claim = seed_claim()
    return {
        "scenario_id": SCENARIO_ID,
        "generator": GENERATOR,
        "claim": claim,
        "validation": validate_claim(claim),
        "evaluation": evaluate(claim, seed_observation()),
    }


def write_artifacts(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "aging_domain.json").write_text(
        json.dumps(build_report(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write aging_domain.json")
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
        print(f"r03_aging_domain: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
