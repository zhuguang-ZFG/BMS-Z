"""Checks that the overcharge-chain practice never swaps the three voltage numbers."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('overcharge_chain', Path(__file__).resolve().parents[1] / 'code/overcharge_chain.py')
chain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chain)


def test_chain_has_five_ordered_acts_ending_in_thermal_runaway():
    steps = chain.chain_steps()
    assert len(steps) == 5
    assert "析锂" in steps[2] and "隔膜" in steps[3] and steps[4].startswith("热失控")


def test_detector_thresholds_stay_strictly_ordered_and_bounded():
    assert chain.CUTOFF_V < chain.FIRMWARE_OVP_V < chain.DW01A_OVP_V
    assert chain.DW01A_OVP_V - chain.DW01A_TOLERANCE_V >= chain.FIRMWARE_OVP_V
    assert chain.brake_distance_mv(chain.FIRMWARE_OVP_V, chain.CUTOFF_V) == pytest.approx(50.0)
    # Worst-case DW01A low side lands on the firmware example value: the margin collapses to 50 mV.
    assert chain.brake_distance_mv(chain.DW01A_OVP_V - chain.DW01A_TOLERANCE_V, chain.CUTOFF_V) == pytest.approx(50.0)
    with pytest.raises(ValueError):
        chain.brake_distance_mv(4.20, 4.20)
    with pytest.raises(ValueError):
        chain.brake_distance_mv(4.10, 4.20)


def test_overshoot_accounting_matches_the_page():
    assert chain.overshoot_percent(0.100, 4.20) == pytest.approx(2.38, abs=0.03)
    assert chain.pack_overshoot_v(0.100, 16) == pytest.approx(1.6)
    assert chain.pack_overshoot_v(0.100, 1) == pytest.approx(0.1)
    with pytest.raises(ValueError):
        chain.pack_overshoot_v(0.100, 0)


def test_delay_slip_is_small_in_ah_but_the_red_line_is_voltage():
    slipped = chain.charge_added_mah(50.0, 1.0)
    assert slipped == pytest.approx(13.9, abs=0.05)
    assert chain.soc_slip_percent(slipped, 50.0) == pytest.approx(0.0278, abs=1e-3)
    assert chain.soc_slip_percent(slipped, 50.0) < 0.1
    with pytest.raises(ValueError):
        chain.charge_added_mah(-1.0, 1.0)
    with pytest.raises(ValueError):
        chain.soc_slip_percent(1.0, 0.0)
