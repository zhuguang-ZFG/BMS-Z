"""Regression tests for D23 precharge repetition + insulation bridge slice."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import d23_precharge_insulation as d23

HERE = Path(__file__).resolve().parent


def test_pulse_account_matches_defaults():
    rep = d23.default_report()
    pc = rep["precharge"]
    assert pc["tau_s"] == pytest.approx(0.17)
    assert pc["t95_s"] == pytest.approx(0.5093, abs=1e-3)
    # 热应力按电阻耗散：supplied 152.0 − stored 72.2 = spent 79.8（与 S3 energy_account 一致）
    assert pc["supplied_j"] == pytest.approx(152.0, abs=0.05)
    assert pc["cap_stored_j"] == pytest.approx(72.2, abs=0.05)
    assert pc["pulse_energy_j"] == pytest.approx(79.8, abs=0.05)
    assert pc["avg_power_w"] == pytest.approx(0.798, abs=0.005)
    assert pc["verdict"] == "pass"
    assert pc["energy_source"] == "resistor_dissipation_supplied_minus_stored"


def test_repetition_over_rate_denied():
    over = d23.repetition_report(pulse_times_s=(0.0, 2.0, 4.0, 6.0, 8.0, 10.0), window_s=60.0)
    assert over["pulse_count"] == 6
    assert over["avg_power_w"] == pytest.approx(7.98, abs=0.01)
    assert over["verdict"] == "deny"


def test_repetition_under_rate_passes():
    ok = d23.repetition_report(pulse_times_s=(0.0, 5.0, 10.0), window_s=300.0)
    assert ok["avg_power_w"] == pytest.approx(0.798, abs=0.005)
    assert ok["verdict"] == "pass"


def test_pulse_energy_over_rating_denied():
    over = d23.repetition_report(pulse_times_s=(0.0,), window_s=300.0, rating_pulse_j=50.0)
    assert over["verdict"] == "deny"


def test_bridge_recovers_fault_resistance():
    ins = d23.insulation_report()
    assert ins["required_min_r_ohm"] == 200000.0
    assert ins["r_iso_minus_ohm"] == pytest.approx(100e3, rel=5e-3)
    assert ins["r_iso_plus_ohm"] == pytest.approx(1e6, rel=5e-3)
    assert ins["v_minus_v"] == pytest.approx(-36.36, abs=0.01)
    assert ins["verdict"] == "isolation_fault"


def test_healthy_network_passes():
    healthy = d23.insulation_report(r_iso_plus_ohm=1e6, r_iso_minus_ohm=1e6)
    assert healthy["verdict"] == "pass"
    assert healthy["r_iso_minus_ohm"] == pytest.approx(1e6, rel=5e-3)


def test_short_window_y_cap_biases_estimate():
    short = d23.insulation_report(window_s=0.005)
    assert short["tau_s"] == pytest.approx(6.25e-3, abs=1e-5)
    assert short["required_window_s"] == pytest.approx(0.01875, abs=1e-4)
    assert short["verdict"] == "window_too_short"
    assert short["estimates_valid"] is False
    assert short["r_iso_minus_ohm"] == pytest.approx(45.7e3, rel=0.02)
    assert abs(short["r_iso_minus_ohm"] - 100e3) > 30e3  # 不许把偏估当真值放行


def test_out_of_range_not_a_number():
    big = d23.insulation_report(r_iso_plus_ohm=10e6, r_iso_minus_ohm=10e6)
    assert big["verdict"] == "out_of_range"
    assert big["estimates_valid"] is False


def test_counts_and_config_identity():
    rep = d23.default_report()
    assert rep["counts"]["precharge_pulses"] == 3
    assert rep["counts"]["insulation_windows"] == 2
    assert rep["config"]["source_v"] == 400.0
    assert rep["config"]["c_y_f"] == 100e-9
    assert rep["scenario_id"] == d23.SCENARIO_ID


def test_cli_default_export(tmp_path):
    out = tmp_path / "out"
    result = subprocess.run(
        [sys.executable, str(HERE / "d23_precharge_insulation.py"), "--out", str(out)],
        capture_output=True,
        text=True,
        cwd=str(HERE),
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    for name in ("precharge.csv", "insulation.csv"):
        assert (out / name).is_file(), name
    assert report["counts"]["precharge_pulses"] == 3
    assert report["precharge"]["cap_stored_j"] == pytest.approx(72.2, abs=0.05)
    assert report["precharge"]["pulse_energy_j"] == pytest.approx(79.8, abs=0.05)
