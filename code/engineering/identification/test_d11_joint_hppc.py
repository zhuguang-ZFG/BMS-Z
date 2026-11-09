"""D11 joint multi-pulse identification and leave-one-out validation."""
import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d11_joint_hppc", HERE / "d11_joint_hppc.py"
)
assert spec is not None and spec.loader is not None
d11 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d11
spec.loader.exec_module(d11)


def test_joint_fit_recovers_truth_and_r1():
    report = d11.build_report()
    joint = report["joint"]
    assert joint["tau"] == pytest.approx(45.0)
    assert joint["r1_ohm"] == pytest.approx(0.015, rel=1e-6)
    assert joint["recovered_r1_error"] == pytest.approx(0.0, abs=1e-8)
    assert joint["boundary_hit"] is False


def test_k_is_local_asymptote_not_transferable():
    """单脉冲 K 是局部渐近值：跨 SOC 留出 160 mV = ΔOCV 0.16 V。"""
    report = d11.build_report()
    loo = report["leave_one_out_rmse_mv"]
    assert loo["single_short_fit_on_z0.40"] == pytest.approx(160.0)
    assert loo["joint_params_on_z0.40"] == pytest.approx(0.0)
    # 160 mV 恰好是两脉冲 OCV 差：0.8 V/SOC × 0.20 SOC
    assert loo["single_short_fit_on_z0.40"] == pytest.approx(d11.OCV_SLOPE * 0.20 * 1000)


def test_finite_pulse_correction_recovers_r1():
    rows = d11.simulate_pulse(0.60)
    tail = [(r["t"] - d11.PULSE_S, r["v"]) for r in rows if r["t"] >= d11.PULSE_S]
    fit = d11.fit_kat(tail, [45.0])
    r1 = d11.r1_from_amplitude(fit["A"], d11.PULSE_A)
    assert r1 == pytest.approx(0.015, rel=1e-6)


def test_boundary_hit_is_reported_not_silent():
    rows = d11.simulate_pulse(0.60)
    tail = [(r["t"] - d11.PULSE_S, r["v"]) for r in rows if r["t"] >= d11.PULSE_S]
    eval_only = d11.fit_kat(tail, [45.0])  # 单点求值不是搜索，边界标志无意义
    assert eval_only["boundary_hit"] is False
    edge_search = d11.fit_kat(tail, [45.0, 120.0])  # 最优点落在搜索边界 → 提示扩网格确认
    assert edge_search["boundary_hit"] is True
    assert edge_search["tau"] == pytest.approx(45.0)


def test_report_identity_links_s2_and_os02():
    report = d11.build_report()
    assert report["scenario_id"] == d11.SCENARIO_ID
    assert "S2" in report["identity"] and "OS02" in report["identity"]
