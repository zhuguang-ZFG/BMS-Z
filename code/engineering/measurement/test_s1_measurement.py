"""Narrow tests for the S1 measurement chain; numbers are teaching anchors."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("s1_measurement", HERE / "s1_measurement.py")
assert spec is not None and spec.loader is not None
s1 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = s1
spec.loader.exec_module(s1)

CFG = s1.ChainConfig()


def test_worst_case_bound_is_not_rss():
    assert s1.worst_case_mv(CFG.rss_limit_mv) == pytest.approx(4.5, abs=1e-12)
    assert s1.rss_mv(CFG.rss_limit_mv) == pytest.approx(2.51595, rel=1e-5)
    assert s1.rss_mv(CFG.rss_limit_mv) < s1.worst_case_mv(CFG.rss_limit_mv)


def test_correlation_changes_the_sum_sigma():
    assert s1.correlated_sigma_mv(0.6, 0.8, 0.0) == pytest.approx(1.0, rel=1e-12)
    assert s1.correlated_sigma_mv(0.6, 0.8, 0.75) == pytest.approx(1.31149, rel=1e-5)
    assert s1.correlated_sigma_mv(0.6, 0.8, 1.0) == pytest.approx(1.4, rel=1e-12)


def test_rho_outside_unit_interval_is_rejected():
    with pytest.raises(ValueError, match="rho"):
        s1.correlated_sigma_mv(0.6, 0.8, 1.2)


def test_mean_variance_factor_for_independent_and_correlated_noise():
    assert s1.mean_variance_factor(1) == pytest.approx(1.0)
    assert s1.mean_variance_factor(5) == pytest.approx(0.2)
    assert s1.mean_variance_factor(5, 0.5) == pytest.approx(0.6)
    assert s1.mean_variance_factor(9, 0.5) == pytest.approx(5 / 9)


def test_single_point_calibration_correction_and_residuals():
    calibration = s1.single_point_calibration(CFG)
    assert calibration["correction_mv"] == pytest.approx(-19.4, abs=1e-9)
    assert calibration["residual_mv"][3.0] == pytest.approx(-1.4, abs=1e-9)
    assert calibration["residual_mv"][4.2] == pytest.approx(1.0, abs=1e-9)
    # The correction removes the reading at the calibration point exactly.
    assert calibration["residual_mv"].get(3.7, 0.0) == pytest.approx(0.0, abs=1e-12)


def test_settling_time_and_five_tau_residual():
    assert s1.settling_time_s(100e-6, 500.0) == pytest.approx(621.4608e-6, rel=1e-6)
    residual = s1.settling_residual_v(0.5, 100e-6, 500e-6)
    assert residual * 1000 == pytest.approx(3.3689735, rel=1e-5)
    assert residual * 1000 > 1.0  # five tau is not enough for this tolerance


def test_sequential_scan_exceeds_a_ten_millisecond_task():
    scan = s1.sequential_scan_s(CFG)
    assert scan["settle_per_cell_s"] == pytest.approx(621.4608e-6, rel=1e-6)
    assert scan["total_s"] == pytest.approx(10.26337296e-3, rel=1e-7)
    assert scan["total_s"] > 10e-3
    assert scan["total_margin_s"] < 0  # over the 10 ms task before any other work
    assert scan["sample_period_margin_s"] > 0  # but it still fits the 20 ms period


def test_invalid_settling_inputs_are_rejected():
    with pytest.raises(ValueError):
        s1.settling_time_s(0.0, 500.0)
    with pytest.raises(ValueError):
        s1.settling_time_s(1e-4, 1.0)
    with pytest.raises(ValueError):
        s1.settling_residual_v(0.5, 1e-4, -1e-3)


def test_causal_moving_average_step_delays_are_zero_forty_eighty():
    case = s1.filter_step_case(CFG)
    delays = {window: row["delay_from_first_high_s"] for window, row in case["windows"].items()}
    assert delays[1] == 0.0
    assert delays[5] == pytest.approx(40e-3)
    assert delays[9] == pytest.approx(80e-3)
    assert case["first_high_index"] == 12


def test_causal_filter_does_not_use_future_samples():
    values = [0.0] * 10
    baseline = s1.moving_average(values, 3)
    changed = values[:]
    changed[-1] = 100.0
    after = s1.moving_average(changed, 3)
    assert after[:-1] == baseline[:-1]
    assert after[-1] != baseline[-1]


def test_centered_window_crosses_earlier_because_it_uses_future_samples():
    case = s1.filter_step_case(CFG)
    assert case["centered_window5_crossing_index"] == case["first_high_index"]
    assert case["windows"][5]["first_crossing_index"] > case["centered_window5_crossing_index"]


def test_confirmation_cost_is_n_minus_one_intervals():
    assert s1.confirmation_delay_s(CFG) == pytest.approx(40e-3)
    assert s1.confirmation_delay_s(s1.replace_config(CFG, confirm_samples=2)) == pytest.approx(20e-3)


def test_feedback_budget_windows_and_the_teaching_window():
    budget = s1.feedback_budget_s(CFG)
    assert budget["confirmation_s"] == pytest.approx(40e-3)
    totals = {window: row["total_s"] for window, row in budget["windows"].items()}
    assert totals[1] == pytest.approx(77e-3)
    assert totals[5] == pytest.approx(117e-3)
    assert totals[9] == pytest.approx(157e-3)
    assert budget["windows"][1]["within_fti"] is True
    assert budget["windows"][5]["within_fti"] is False
    assert budget["windows"][9]["within_fti"] is False


def test_report_is_recomputable_and_records_limits():
    report = s1.build_report(CFG)
    assert report["scenario_id"] == "S1-sense-chain"
    assert report["filter_scenario_id"] == "S1-filter-post-afe"
    assert report["scan_scenario_id"] == "S1-scan-settling"
    assert report["rss_is_bound"] is False
    assert len(report["limitations"]) >= 3


def test_write_evidence_stamps_config_digest(tmp_path):
    report = s1.write_evidence(tmp_path, CFG)
    saved = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert saved == report
    assert saved["config_sha256"].startswith("sha256:")
    assert len(saved["config_sha256"]) == len("sha256:") + 64


def test_student_questions_do_not_leak_answers():
    questions = s1.student_questions()
    assert len(questions) == 5
    joined = " ".join(questions)
    for forbidden in ("77", "117", "157", "0.077", "10.26"):
        assert forbidden not in joined
