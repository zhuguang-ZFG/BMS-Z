"""Checks that the three-probes practice keeps single-probe conclusions open."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('probe_ambiguity', Path(__file__).resolve().parents[1] / 'code/probe_ambiguity.py')
probes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probes)

CURRENT, MEASURED = -20.0, 3.30


def test_nernst_shape_matches_the_stage_zero_page():
    assert probes.ocv_v(0.50) == pytest.approx(3.70)
    assert probes.ocv_v(0.08) == pytest.approx(3.505, abs=1e-3)
    assert probes.ocv_v(0.92) == pytest.approx(3.895, abs=1e-3)
    assert probes.ocv_v(0.5) < probes.ocv_v(0.6) < probes.ocv_v(0.92)
    assert probes.slope_v_per_percent(0.50) * 1000 == pytest.approx(3.2)
    assert probes.slope_v_per_percent(0.90) * 1000 > probes.slope_v_per_percent(0.50) * 1000
    for bad in (0.0, 1.0, -0.5, 1.5):
        with pytest.raises(ValueError):
            probes.ocv_v(bad)


def test_one_terminal_reading_has_several_state_explanations():
    candidates = probes.soc_candidates(MEASURED, CURRENT, [0.30, 0.50, 0.70, 0.92])
    assert len(candidates) == 4
    for soc, r0 in candidates:
        assert probes.terminal_v(probes.ocv_v(soc), CURRENT, r0) == pytest.approx(MEASURED)
    resistances = [r0 for _, r0 in candidates]
    assert resistances == sorted(resistances)
    assert resistances[0] > 0


def test_sign_convention_follows_the_repo():
    # Charging is positive: terminal sits above OCV; discharging below.
    assert probes.terminal_v(3.70, 10.0, 0.020) == pytest.approx(3.90)
    assert probes.terminal_v(3.70, -10.0, 0.020) == pytest.approx(3.50)
    with pytest.raises(ValueError):
        probes.terminal_v(3.70, 10.0, -0.020)


def test_resting_reading_resolves_the_ambiguity():
    candidates = probes.soc_candidates(MEASURED, CURRENT, [0.30, 0.50, 0.70, 0.92])
    resting = [probes.ocv_v(soc) for soc, _ in candidates]
    assert len(set(resting)) == len(resting)
    assert resting[0] < resting[-1]
    # With I = 0 the resistance information is gone, which is the honest limit.
    with pytest.raises(ValueError):
        probes.implied_r0(3.70, 3.70, 0.0)
    # A reading that would need negative resistance refutes the guessed state.
    with pytest.raises(ValueError):
        probes.implied_r0(probes.ocv_v(0.92), MEASURED, 10.0)
