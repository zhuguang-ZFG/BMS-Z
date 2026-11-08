"""Narrow tests for the S3 precharge RC model; all values are teaching anchors."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("s3_precharge", HERE / "s3_precharge.py")
assert spec is not None and spec.loader is not None
s3 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = s3
spec.loader.exec_module(s3)

CFG = s3.PrechargeConfig()


def test_tau_and_initial_inrush_match_the_frozen_table():
    assert s3.tau_s(CFG) == pytest.approx(0.17, abs=1e-12)
    rush = s3.initial_inrush(CFG)
    assert rush["current_a"] == pytest.approx(2.35294, rel=1e-5)
    assert rush["power_w"] == pytest.approx(941.176, rel=1e-5)
    assert rush["peak_ok"] is True
    assert rush["energy_ok"] is True


def test_reaching_90_and_95_percent_matches_the_frozen_table():
    assert s3.time_to_fraction(CFG, 0.90) == pytest.approx(0.39144, rel=1e-5)
    assert s3.time_to_fraction(CFG, 0.95) == pytest.approx(0.50927, rel=1e-5)
    assert s3.bus_voltage(CFG, s3.time_to_fraction(CFG, 0.95)) == pytest.approx(380.0, abs=1e-9)


def test_energy_account_at_95_and_at_steady_state():
    at95 = s3.energy_account(CFG, 0.95)
    assert at95["stored_j"] == pytest.approx(72.2, abs=1e-9)
    assert at95["supplied_j"] == pytest.approx(152.0, abs=1e-9)
    assert at95["spent_j"] == pytest.approx(79.8, abs=1e-9)
    steady = s3.energy_account(CFG, 1.0)
    assert steady["stored_j"] == pytest.approx(80.0, abs=1e-9)
    assert steady["spent_j"] == pytest.approx(80.0, abs=1e-9)
    # Invariant: source = resistor + capacitor in the ideal no-load loop.
    assert pytest.approx(at95["supplied_j"], rel=1e-12) == at95["stored_j"] + at95["spent_j"]


def test_bus_voltage_and_current_are_monotone_and_bounded():
    previous = -1.0
    for step in range(0, 21):
        v = s3.bus_voltage(CFG, step * 0.05)
        assert v > previous
        assert v <= CFG.source_v
        previous = v
    first = s3.loop_current(CFG, 0.0)
    last = s3.loop_current(CFG, 2.0)
    assert first == pytest.approx(2.35294, rel=1e-5)
    assert 0 < last < first


def test_residual_voltage_shortens_but_does_not_remove_the_wait():
    cfg = s3.replace_config(CFG, initial_bus_v=50.0)
    assert s3.time_to_fraction(cfg, 0.95) < s3.time_to_fraction(CFG, 0.95)
    assert s3.time_to_fraction(cfg, 0.95) > 0
    # Gate requires explicit device evidence; without it, even 380 V fails closed.
    assert s3.main_contact_permitted(cfg, "PRECHARGE_DONE", 380.0, True, True, True) is False
    assert s3.main_contact_permitted(
        cfg, "PRECHARGE_DONE", 380.0, True, True, True, devices_evidence=True
    ) is True


def test_parallel_load_has_a_lower_steady_state_and_dissipates():
    import math as _math

    cfg = s3.replace_config(CFG, parallel_load_ohm=2000.0)
    v_end = cfg.source_v * 2000.0 / 2170.0
    assert v_end == pytest.approx(368.66, abs=0.01)
    account = s3.energy_with_load(cfg)
    assert account["steady_state_v"] == pytest.approx(v_end, abs=1e-9)
    assert account["stored_j"] == pytest.approx(67.04, abs=0.05)
    assert account["load_j"] == pytest.approx(37.41, abs=0.05)
    assert account["resistor_j"] > 0
    assert account["source_j"] == pytest.approx(
        account["stored_j"] + account["resistor_j"] + account["load_j"], abs=1e-9
    )
    assert account["identity_ok"] is True
    # No-load limit recovers the known 160 = 80 + 80 J steady-state account at the window end.
    plain = s3.energy_with_load(s3.PrechargeConfig())
    assert plain["load_j"] == 0.0
    assert plain["resistor_j"] == pytest.approx(80.0, abs=0.01)
    assert plain["stored_j"] == pytest.approx(78.93, abs=0.05)  # end of 5-tau window, not infinity
    assert plain["identity_ok"] is True
    # Numeric quadrature must agree with the closed-form window account.
    tau_par = cfg.precharge_r_ohm * cfg.parallel_load_ohm / (cfg.precharge_r_ohm + cfg.parallel_load_ohm) * cfg.bus_capacitance_f
    horizon = 5.0 * tau_par
    steps = 40000
    h = horizon / steps
    e_load = 0.0
    for i in range(steps):
        vv = v_end + (cfg.initial_bus_v - v_end) * _math.exp(-(i + 0.5) * h / tau_par)
        e_load += vv * vv / cfg.parallel_load_ohm * h
    assert e_load == pytest.approx(account["load_j"], rel=1e-6)


def test_main_contact_requires_state_validity_feedback_and_rise():
    ev = {"devices_evidence": True}
    ok = s3.main_contact_permitted(CFG, "PRECHARGE_DONE", 380.0, True, True, True, **ev)
    assert ok is True
    # Each missing condition alone must block the contactor.
    assert s3.main_contact_permitted(CFG, "PRECHARGE_RUNNING", 380.0, True, True, True, **ev) is False
    assert s3.main_contact_permitted(CFG, "PRECHARGE_DONE", 380.0, False, True, True, **ev) is False
    assert s3.main_contact_permitted(CFG, "PRECHARGE_DONE", 380.0, True, False, True, **ev) is False
    assert s3.main_contact_permitted(CFG, "PRECHARGE_DONE", 380.0, True, True, False, **ev) is False
    assert s3.main_contact_permitted(CFG, "PRECHARGE_DONE", 379.9, True, True, True, **ev) is False


def test_single_voltage_reading_cannot_open_the_contactor():
    ev = {"devices_evidence": True}
    # A stuck sensor can read 380 V while the bus is at 0 V; validity must be
    # independent evidence, not the same reading restated.
    assert s3.main_contact_permitted(CFG, "PRECHARGE_DONE", 380.0, False, True, True, **ev) is False
    # Residual, backfeed and adhesion with a valid meter all satisfy the
    # voltage gate; the state machine must still block on feedback/rise.
    assert s3.main_contact_permitted(CFG, "PRECHARGE_DONE", 390.0, True, False, True, **ev) is False


def test_main_contact_rejects_overvoltage_reverse_and_excessive_residual():
    ev = {"devices_evidence": True}
    # 800 V overvoltage on a 400 V bus must never pass a >=380 V test.
    assert s3.main_contact_permitted(CFG, "PRECHARGE_DONE", 800.0, True, True, True, **ev) is False
    # Upper factor 1.05*400 = 420 V; above that is rejected.
    assert s3.main_contact_permitted(CFG, "PRECHARGE_DONE", 421.0, True, True, True, **ev) is False
    # Reverse polarity reading must fail the band.
    assert s3.main_contact_permitted(CFG, "PRECHARGE_DONE", -100.0, True, True, True, **ev) is False
    # Excess residual gap: 380 V is 20 V gap -> 1000 A <= 1500 A ok; a tighter
    # device limit must reject the same residual.
    tight = s3.replace_config(CFG, devices_main_peak_a=500.0)
    assert s3.main_contact_permitted(tight, "PRECHARGE_DONE", 380.0, True, True, True, **ev) is False
    # At 395 V gap is 5 V -> 250 A <= 500 A permitted.
    assert s3.main_contact_permitted(tight, "PRECHARGE_DONE", 395.0, True, True, True, **ev) is True


def test_main_contact_rejects_reverse_pressure_420v_500a():
    # Signed-gap bypass: 420 V measured -> residual -20 V -> -1000 A <= 500 A
    # would permit while 380 V (same amplitude, positive) is rejected.
    # Reverse/backfeed must fail closed, never via signed current comparison.
    tight = s3.replace_config(CFG, devices_main_peak_a=500.0)
    ev = {"devices_evidence": True}
    assert s3.main_contact_permitted(tight, "PRECHARGE_DONE", 380.0, True, True, True, **ev) is False
    assert s3.main_contact_permitted(tight, "PRECHARGE_DONE", 420.0, True, True, True, **ev) is False
    # Even with a generous limit, above-source must still fail (backfeed path).
    assert s3.main_contact_permitted(CFG, "PRECHARGE_DONE", 420.0, True, True, True, **ev) is False


def test_main_contact_fails_closed_without_device_evidence():
    # Default (None) is missing evidence.
    assert s3.main_contact_permitted(CFG, "PRECHARGE_DONE", 380.0, True, True, True) is False
    assert s3.main_contact_permitted(CFG, "PRECHARGE_DONE", 380.0, True, True, True, devices_evidence=False) is False
    # Missing/indeterminate main-loop evidence in config also fails closed.
    no_r = s3.replace_config(CFG, main_loop_resistance_ohm=0.0)
    assert s3.main_contact_permitted(no_r, "PRECHARGE_DONE", 380.0, True, True, True, devices_evidence=True) is False
    no_lim = s3.replace_config(CFG, devices_main_peak_a=0.0)
    assert s3.main_contact_permitted(no_lim, "PRECHARGE_DONE", 380.0, True, True, True, devices_evidence=True) is False


def test_close_current_depends_on_main_loop_resistance_not_precharge_resistor():
    # 20 V residual through the 20 mOhm main loop is 1000 A — the checked
    # replacement for the old 20/170 = 0.118 A report that blessed the
    # shortcut. The precharge resistor must never enter this calculation.
    assert s3.close_current_at_residual(CFG, 20.0) == pytest.approx(1000.0)
    assert s3.close_current_at_residual(CFG, 20.0) == pytest.approx(20 / 0.02)
    assert s3.close_current_at_residual(CFG, 5.0) == pytest.approx(250.0)
    # Missing/implausible main-loop evidence is an error, not a silent pass.
    bad = s3.replace_config(CFG, main_loop_resistance_ohm=0.0)
    with pytest.raises(ValueError):
        s3.close_current_at_residual(bad, 20.0)


def test_device_limits_are_reported_not_silently_trusted():
    tight = s3.replace_config(CFG, devices_precharge_peak_a=2.0)
    assert s3.initial_inrush(tight)["peak_ok"] is False  # 2.35 A > 2.0 A limit
    tight_e = s3.replace_config(CFG, devices_precharge_energy_j=70.0)
    assert s3.initial_inrush(tight_e)["energy_ok"] is False  # 80 J > 70 J


def test_negative_time_and_bad_fraction_are_rejected():
    with pytest.raises(ValueError):
        s3.bus_voltage(CFG, -0.1)
    with pytest.raises(ValueError):
        s3.loop_current(CFG, -0.1)
    with pytest.raises(ValueError):
        s3.time_to_fraction(CFG, 1.0)
    with pytest.raises(ValueError):
        s3.time_to_fraction(CFG, 0.0)
    with pytest.raises(ValueError):
        s3.close_current_at_residual(CFG, -5.0)


def test_report_records_scenario_and_limitations():
    report = s3.build_report(CFG)
    assert report["scenario_id"] == "S3-inrush-precharge"
    assert report["tau_s"] == pytest.approx(0.17)
    assert len(report["limitations"]) >= 3


def test_write_evidence_stamps_config_digest(tmp_path):
    report = s3.write_evidence(tmp_path, CFG)
    saved = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert saved == report
    assert saved["config_sha256"].startswith("sha256:")
    assert len(saved["config_sha256"]) == len("sha256:") + 64


def test_student_questions_do_not_leak_answers():
    questions = s3.student_questions()
    assert len(questions) == 5
    joined = " ".join(questions)
    for forbidden in ("0.39144", "0.50927", "2.35294", "368.66", "72.2", "79.8"):
        assert forbidden not in joined
