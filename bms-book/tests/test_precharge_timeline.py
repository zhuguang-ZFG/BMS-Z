"""Analytic RC checks and counterexamples to voltage-only contactor conclusions."""
import importlib.util
import math
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('precharge_timeline', Path(__file__).resolve().parents[1] / 'code/precharge_timeline.py')
precharge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(precharge)

PACK, CAP, RES = 400.0, 0.001, 170.0


def test_time_constant_initial_current_and_asymptotic_resistor_heat():
    assert precharge.time_constant_s(RES, CAP) == pytest.approx(0.17)
    assert precharge.surge_current_a(PACK, RES) == pytest.approx(400 / 170)
    assert precharge.pulse_energy_j(CAP, PACK) == pytest.approx(80.0)
    assert precharge.pulse_energy_j(2 * CAP, PACK) == pytest.approx(160.0)
    assert precharge.pulse_energy_j(CAP, 2 * PACK) == pytest.approx(320.0)


def test_curve_starts_at_zero_and_rise_time_distinguishes_90_from_95_percent():
    assert precharge.bus_voltage_v(0.0, PACK, RES, CAP) == 0.0
    samples = [precharge.bus_voltage_v(t, PACK, RES, CAP) for t in (0.0, 0.05, 0.17, 0.51, 5.0)]
    assert samples == sorted(samples)
    assert samples[2] == pytest.approx(400 * (1 - math.exp(-1)))
    assert samples[3] == pytest.approx(400 * (1 - math.exp(-3)))
    assert precharge.rise_time_s(0.9, RES, CAP) == pytest.approx(0.391439465809)
    assert precharge.rise_time_s(0.95, RES, CAP) == pytest.approx(0.509274486504)
    for ratio in (0.5, 0.9, 0.95, 0.99):
        elapsed = precharge.rise_time_s(ratio, RES, CAP)
        assert precharge.bus_voltage_v(elapsed, PACK, RES, CAP) == pytest.approx(PACK * ratio)


def test_energy_is_split_between_resistor_and_capacitor_not_transferred_from_capacitor():
    elapsed = precharge.rise_time_s(0.95, RES, CAP)
    ledger = precharge.energy_ledger_j(elapsed, PACK, RES, CAP)
    assert ledger['source_j'] == pytest.approx(152.0)
    assert ledger['resistor_j'] == pytest.approx(79.8)
    assert ledger['capacitor_j'] == pytest.approx(72.2)
    assert ledger['source_j'] == pytest.approx(ledger['resistor_j'] + ledger['capacitor_increase_j'])
    steady = precharge.energy_ledger_j(100 * RES * CAP, PACK, RES, CAP)
    assert steady['source_j'] == pytest.approx(160.0)
    assert steady['resistor_j'] == pytest.approx(80.0)
    assert steady['capacitor_j'] == pytest.approx(80.0)


@pytest.mark.parametrize('initial', [0.0, 100.0, 200.0, 380.0, PACK])
@pytest.mark.parametrize('elapsed', [0.0, 0.05, 0.17, 5.0])
def test_initial_residual_charge_changes_surge_and_preserves_energy_balance(initial, elapsed):
    assert precharge.bus_voltage_v(0, PACK, RES, CAP, initial) == pytest.approx(initial)
    assert precharge.surge_current_a(PACK, RES, initial) == pytest.approx((PACK - initial) / RES)
    ledger = precharge.energy_ledger_j(elapsed, PACK, RES, CAP, initial)
    assert ledger['source_j'] == pytest.approx(ledger['resistor_j'] + ledger['capacitor_increase_j'], abs=1e-12)
    assert ledger['capacitor_j'] == pytest.approx(ledger['capacitor_initial_j'] + ledger['capacitor_increase_j'])
    assert precharge.pulse_energy_j(CAP, PACK, initial) == pytest.approx(0.5 * CAP * (PACK - initial) ** 2)


def test_residual_charge_alone_passes_voltage_condition_but_never_authorizes_closing():
    # A residual 380 V at t=0 has no observed precharge rise or verified contactor state.
    bus = precharge.bus_voltage_v(0, PACK, RES, CAP, 380.0)
    verdict = precharge.close_verdict(PACK, bus)
    assert verdict['voltage_condition_met'] is True
    assert verdict['allowed'] is False
    # Even an arbitrary low ratio must not turn a 40 V measurement into a command.
    assert precharge.close_verdict(PACK, 40.0, ratio=0.1)['allowed'] is False
    assert precharge.close_verdict(PACK, PACK)['allowed'] is False


def test_low_voltage_or_overpack_reading_cannot_identify_root_cause_or_allow_closing():
    for bus in (0.0, 40.0, 379.0, 410.0):
        verdict = precharge.close_verdict(PACK, bus)
        assert verdict['voltage_condition_met'] is False
        assert verdict['allowed'] is False
        assert '禁止合 K1' in verdict['reason']
    assert '不能确定根因' in precharge.close_verdict(PACK, 40.0)['reason']


def test_live_bus_is_an_observation_requiring_investigation_not_a_weld_diagnosis():
    # All these physically different situations can present the same single reading.
    residual = precharge.bus_voltage_v(0, PACK, RES, CAP, 380.0)
    for reading in (residual, 380.0, PACK):  # residual / external source / closed path
        assert precharge.bus_requires_investigation(PACK, reading) is True
    assert precharge.bus_requires_investigation(PACK, 0.0) is False
    assert precharge.bus_requires_investigation(PACK, 0.2 * PACK) is False
    assert precharge.bus_requires_investigation(PACK, 0.2 * PACK + 1.0) is True


@pytest.mark.parametrize('invalid', [float('nan'), float('inf'), -float('inf')])
def test_nonfinite_measurements_never_become_permission_or_healthy_observations(invalid):
    for fn in (precharge.close_verdict, precharge.bus_requires_investigation):
        with pytest.raises(ValueError):
            fn(PACK, invalid)
        with pytest.raises(ValueError):
            fn(invalid, 380.0)
        with pytest.raises(ValueError):
            fn(PACK, 380.0, ratio=invalid)


@pytest.mark.parametrize('ratio', [0.0, 1.0, -0.2, 1.5])
def test_invalid_ratios_are_rejected(ratio):
    with pytest.raises(ValueError):
        precharge.rise_time_s(ratio, RES, CAP)
    with pytest.raises(ValueError):
        precharge.close_verdict(PACK, 380, ratio)


@pytest.mark.parametrize('resistance,capacitance', [(0.0, CAP), (RES, 0.0), (-1.0, CAP), (float('nan'), CAP)])
def test_invalid_passives_are_rejected(resistance, capacitance):
    with pytest.raises(ValueError):
        precharge.time_constant_s(resistance, capacitance)


def test_negative_time_and_unmodeled_reverse_charge_are_rejected():
    with pytest.raises(ValueError):
        precharge.bus_voltage_v(-0.01, PACK, RES, CAP)
    with pytest.raises(ValueError):
        precharge.bus_voltage_v(0, PACK, RES, CAP, PACK + 1)
