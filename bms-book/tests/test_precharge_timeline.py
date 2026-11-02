"""Checks that the precharge practice forbids closing K1 on every failure path."""
import importlib.util
import math
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('precharge_timeline', Path(__file__).resolve().parents[1] / 'code/precharge_timeline.py')
precharge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(precharge)

PACK, CAP, RES = 400.0, 0.001, 170.0


def test_time_constant_surge_current_and_pulse_energy_match_the_worked_example():
    tau = precharge.time_constant_s(RES, CAP)
    assert tau == pytest.approx(0.17)
    assert precharge.surge_current_a(PACK, RES) == pytest.approx(400 / 170)
    assert precharge.pulse_energy_j(CAP, PACK) == pytest.approx(80.0)
    # Energy scales with C and with U^2, so doubling either one changes the resistor duty.
    assert precharge.pulse_energy_j(2 * CAP, PACK) == pytest.approx(160.0)
    assert precharge.pulse_energy_j(CAP, 2 * PACK) == pytest.approx(320.0)


def test_curve_starts_at_zero_rises_monotonically_and_reaches_the_pack():
    assert precharge.bus_voltage_v(0.0, PACK, RES, CAP) == 0.0
    samples = [precharge.bus_voltage_v(t, PACK, RES, CAP) for t in (0.0, 0.05, 0.17, 0.51, 5.0)]
    assert samples == sorted(samples)
    assert samples[2] == pytest.approx(400 * (1 - math.exp(-1)))
    assert samples[3] == pytest.approx(400 * (1 - math.exp(-3)))
    assert samples[4] > 395.0
    with pytest.raises(ValueError):
        precharge.bus_voltage_v(-0.01, PACK, RES, CAP)


def test_rise_time_inverts_the_curve_for_every_target_ratio():
    for ratio in (0.5, 0.9, 0.95, 0.99):
        elapsed = precharge.rise_time_s(ratio, RES, CAP)
        assert precharge.bus_voltage_v(elapsed, PACK, RES, CAP) == pytest.approx(PACK * ratio)
    assert precharge.rise_time_s(0.95, RES, CAP) == pytest.approx(3 * 0.17, abs=0.01)
    for bad in (0.0, 1.0, -0.2, 1.5):
        with pytest.raises(ValueError):
            precharge.rise_time_s(bad, RES, CAP)


def test_close_is_allowed_only_at_or_above_the_target_voltage():
    target = PACK * 0.95
    allowed = precharge.close_verdict(PACK, target)
    assert allowed['allowed'] is True and allowed['target_v'] == pytest.approx(380.0)
    assert precharge.close_verdict(PACK, target - 1.0)['allowed'] is False
    assert precharge.close_verdict(PACK, precharge.bus_voltage_v(0.17, PACK, RES, CAP))['allowed'] is False


def test_failure_paths_keep_k1_open():
    stuck = precharge.close_verdict(PACK, 40.0)
    slow = precharge.close_verdict(PACK, precharge.bus_voltage_v(0.51, PACK, RES, 3 * CAP))
    for verdict in (stuck, slow):
        assert verdict['allowed'] is False
        assert '禁止合 K1' in verdict['reason']
    # A stuck bus and a slow bus are different faults and must be named differently.
    assert stuck['reason'] != slow['reason']
    assert precharge.close_verdict(PACK, 40.0, ratio=0.1)['allowed'] is True


def test_a_live_bus_before_precharge_is_weld_evidence():
    assert precharge.weld_suspect(PACK, 0.0) is False
    assert precharge.weld_suspect(PACK, 0.2 * PACK) is False
    assert precharge.weld_suspect(PACK, 0.2 * PACK + 1.0) is True
    assert precharge.weld_suspect(PACK, 0.95 * PACK) is True
    with pytest.raises(ValueError):
        precharge.weld_suspect(0.0, 10.0)


@pytest.mark.parametrize('resistance,capacitance', [(0.0, 0.001), (170.0, 0.0), (-1.0, 0.001)])
def test_invalid_passives_are_rejected(resistance, capacitance):
    with pytest.raises(ValueError):
        precharge.time_constant_s(resistance, capacitance)
