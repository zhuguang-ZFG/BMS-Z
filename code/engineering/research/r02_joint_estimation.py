"""R02 reference implementation: joint-estimation uncertainty contract.

Teaching slice ``R02-joint-estimation``: a joint-estimation claim ("jointly
estimated SOC and RC parameters") is only as strong as the contract it
carries. This module pins that contract from the source-adoption table:

- OS02 (PyBOP): fit and validation must enter the contract as separate
  windows; track cost and optimisation results; standard-library benchmark
  first — no dependency on installing the library (P4 G02).
- EDU01 (UCCS/Plett): cited formulas must carry their assumptions and a
  real locator (page / section / equation number), not just a paper name.

Contract rules (validate_report):
- C1 ``fit_validation_overlap``: fit and validation windows must be
  disjoint — overlap is leakage, not validation.
- C2 ``missing_validation_window``: an estimate without a held-out window
  is a fit, not an estimate.
- C3 ``missing_uncertainty``: every estimate must carry a positive std —
  a point estimate alone is not an uncertainty claim.
- C4 ``empty_assumptions``: the assumption list must be non-empty.
- C5 ``uncited_formula``: every source citation needs a locator.
- C6 ``external_dependency`` (warning): declaring an external library is
  allowed but flagged — the teaching benchmark stays standard-library only.

evaluate(report, observation) fails closed per check: validation-window
residual within tolerance, and every estimate's std must sit inside its
tolerance band (observed std_within_tolerance must cover all estimates).

Only the standard library is used so the chapter can be recomputed end to end.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCENARIO_ID = "R02-joint-estimation"
GENERATOR = "r02_joint_estimation.py v1 (standard library)"

SEED_REPORT: dict = {
    "method_id": "joint-EKF-teaching",
    "synthetic": True,
    "external_lib": None,
    "fit_window_ids": ["pulse-1"],
    "validation_window_ids": ["pulse-2"],
    "estimates": {
        "R0": {"value": 0.0012, "std": 0.0001},
        "R1": {"value": 0.0021, "std": 0.0004},
        "C1": {"value": 18000.0, "std": 900.0},
    },
    "tolerance_residual": 0.005,
    "assumptions": [
        "窗内 OCV-SOC 曲线分段线性",
        "R/C 参数在双脉冲间保持不变",
        "电流测量无偏、噪声零均值",
    ],
    "source_citations": [
        {"id": "EDU01", "locator": "讲义第4章 式(4.12) 联合EKF更新"},
        {"id": "OS02", "locator": "multipulse notebook 拟合/验证切分"},
    ],
    "boundary": "教学值合同：真实联合估计须替换真数据与外部基准，本种子只钉纪律形状。",
}

SEED_OBSERVATION: dict = {
    "max_abs_residual": 0.0018,
    "std_within_tolerance": {"R0": True, "R1": True, "C1": True},
}


def seed_report() -> dict:
    return json.loads(json.dumps(SEED_REPORT, ensure_ascii=False))


def seed_observation() -> dict:
    return json.loads(json.dumps(SEED_OBSERVATION, ensure_ascii=False))


def validate_report(report: dict) -> list[dict]:
    findings: list[dict] = []
    fit = set(report.get("fit_window_ids", []))
    val = list(report.get("validation_window_ids", []))
    if not val:
        findings.append({"kind": "missing_validation_window", "severity": "error",
                         "detail": "an estimate without a held-out window is a fit, not an estimate"})
    overlap = sorted(fit & set(val))
    if overlap:
        findings.append({"kind": "fit_validation_overlap", "severity": "error",
                         "detail": f"fit/validation windows overlap on {overlap!r} — leakage"})
    for name, est in report.get("estimates", {}).items():
        std = est.get("std")
        if std is None or std <= 0:
            findings.append({"kind": "missing_uncertainty", "severity": "error",
                             "detail": f"estimate {name!r} needs a positive std"})
    if not report.get("assumptions"):
        findings.append({"kind": "empty_assumptions", "severity": "error",
                         "detail": "assumption list must be non-empty"})
    for cite in report.get("source_citations", []):
        if not cite.get("locator", "").strip():
            findings.append({"kind": "uncited_formula", "severity": "error",
                             "detail": f"citation {cite.get('id')!r} needs a page/section/equation locator"})
    if report.get("external_lib"):
        findings.append({"kind": "external_dependency", "severity": "error",
                         "detail": f"external library {report['external_lib']!r} declared; "
                                   "teaching contract requires a standard-library benchmark"})
    return findings


def evaluate(report: dict, observation: dict) -> dict:
    """Per-check fail-closed evaluation on the held-out window.

    Evaluation is gated on the contract itself: any error-level validation
    finding (or an empty estimates table) fails closed — an invalid contract
    cannot produce a passing estimate.
    """
    findings = validate_report(report)
    checks = {
        "contract_valid": not any(f["severity"] == "error" for f in findings),
        "has_estimates": bool(report.get("estimates")),
        "validation_residual": abs(observation.get("max_abs_residual", float("inf")))
        <= report.get("tolerance_residual", 0.0),
    }
    within = observation.get("std_within_tolerance", {})
    checks["uncertainty_band"] = all(within.get(name) is True
                                     for name in report.get("estimates", {}))
    verdict = "pass" if all(checks.values()) else "fail"
    return {
        "scenario_id": SCENARIO_ID,
        "checks": checks,
        "verdict": verdict,
        "boundary": "pass 只证明在留出验证窗内残差与不确定度达标，不证明参数在窗外观测条件下成立。",
    }


def build_report() -> dict:
    report = seed_report()
    return {
        "scenario_id": SCENARIO_ID,
        "generator": GENERATOR,
        "report": report,
        "validation": validate_report(report),
        "evaluation": evaluate(report, seed_observation()),
    }


def write_artifacts(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "joint_estimation.json").write_text(
        json.dumps(build_report(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write joint_estimation.json")
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
        print(f"r02_joint_estimation: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
