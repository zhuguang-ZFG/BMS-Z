"""Regression tests for the R02 joint-estimation uncertainty contract slice."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import r02_joint_estimation as r02

HERE = Path(__file__).resolve().parent


def test_seed_report_passes_validation_and_evaluation():
    report = r02.seed_report()
    findings = r02.validate_report(report)
    assert findings == []
    result = r02.evaluate(report, r02.seed_observation())
    assert result["verdict"] == "pass"
    assert result["checks"]["validation_residual"] is True


def test_fit_and_validation_windows_must_be_disjoint():
    """OS02 合同：拟合窗与验证窗必须分离，重叠即泄漏。"""
    report = r02.seed_report()
    report["fit_window_ids"] = ["w1", "w2"]
    report["validation_window_ids"] = ["w2", "w3"]
    findings = r02.validate_report(report)
    assert any(f["kind"] == "fit_validation_overlap" for f in findings)


def test_validation_window_is_required():
    report = r02.seed_report()
    report["validation_window_ids"] = []
    findings = r02.validate_report(report)
    assert any(f["kind"] == "missing_validation_window" for f in findings)


def test_point_estimate_without_std_is_found():
    """联合估计只报点估计不报不确定度 = 没有不确定度声称的凭证。"""
    report = r02.seed_report()
    del report["estimates"]["R0"]["std"]
    findings = r02.validate_report(report)
    assert any(f["kind"] == "missing_uncertainty" for f in findings)
    report = r02.seed_report()
    report["estimates"]["R0"]["std"] = 0.0
    findings = r02.validate_report(report)
    assert any(f["kind"] == "missing_uncertainty" for f in findings)


def test_empty_assumptions_are_found():
    """EDU01：引用公式必须连同假设一起登记，空假设列表不算估计。"""
    report = r02.seed_report()
    report["assumptions"] = []
    findings = r02.validate_report(report)
    assert any(f["kind"] == "empty_assumptions" for f in findings)


def test_formula_citation_needs_locator():
    """EDU01：每个引用要给得出页/节/公式号定位，只写文献名不算引用。"""
    report = r02.seed_report()
    report["source_citations"][0]["locator"] = ""
    findings = r02.validate_report(report)
    assert any(f["kind"] == "uncited_formula" for f in findings)


def test_external_library_dependency_is_flagged():
    """OS02 P4 G02：教学合同硬约束——声明外部库依赖即 error，评估不许 pass。"""
    report = r02.seed_report()
    report["external_lib"] = "pybop"
    findings = r02.validate_report(report)
    assert any(f["kind"] == "external_dependency" and f["severity"] == "error" for f in findings)


def test_declared_external_lib_cannot_pass_evaluation():
    """advisory：声明外部依赖的合同不许产出 passing verdict（评估门只挡 error）。"""
    report = r02.seed_report()
    report["external_lib"] = "pybop"
    result = r02.evaluate(report, r02.seed_observation())
    assert result["verdict"] == "fail"
    assert result["checks"]["contract_valid"] is False


def test_evaluation_fails_closed_on_validation_residual():
    report = r02.seed_report()
    obs = r02.seed_observation()
    obs["max_abs_residual"] = report["tolerance_residual"] * 2
    result = r02.evaluate(report, obs)
    assert result["verdict"] == "fail"
    assert result["checks"]["validation_residual"] is False


def test_invalid_contract_cannot_pass_evaluation():
    """advisory：带 error 级 findings 的合同不许产出 passing verdict。"""
    report = r02.seed_report()
    report["fit_window_ids"] = ["w1"]
    report["validation_window_ids"] = ["w1"]  # C1 泄漏
    result = r02.evaluate(report, r02.seed_observation())
    assert result["verdict"] == "fail"
    assert result["checks"]["contract_valid"] is False


def test_empty_estimates_cannot_pass_evaluation():
    """advisory：空 estimates 表 + 零残差 + 零容差不许 vacuous pass。"""
    report = r02.seed_report()
    report["estimates"] = {}
    report["tolerance_residual"] = 0.0
    obs = {"max_abs_residual": 0.0, "std_within_tolerance": {}}
    result = r02.evaluate(report, obs)
    assert result["verdict"] == "fail"
    assert result["checks"]["has_estimates"] is False


def test_uncertainty_must_cover_every_estimate_in_evaluation():
    report = r02.seed_report()
    obs = r02.seed_observation()
    obs["std_within_tolerance"] = {"R0": True, "R1": False, "C1": True}
    result = r02.evaluate(report, obs)
    assert result["verdict"] == "fail"


def test_seed_is_synthetic_and_lib_free():
    report = r02.seed_report()
    assert report["synthetic"] is True
    assert report["external_lib"] is None


def test_cli_default_export(tmp_path):
    result = subprocess.run(
        [sys.executable, str(HERE / "r02_joint_estimation.py"), "--out", str(tmp_path)],
        capture_output=True, text=True, cwd=str(HERE), check=False,
        timeout=120, stdin=subprocess.DEVNULL,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "joint_estimation.json").read_text(encoding="utf-8"))
    assert report["evaluation"]["verdict"] == "pass"
    assert report["validation"] == []
