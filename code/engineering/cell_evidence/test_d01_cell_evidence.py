"""D01 same-voltage counterexample: one terminal voltage, three internal states."""
import importlib.util
import math
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d01_cell_evidence", HERE / "d01_cell_evidence.py"
)
assert spec is not None and spec.loader is not None
d01 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d01
spec.loader.exec_module(d01)

SCENARIO_ID = d01.SCENARIO_ID
build_report = d01.build_report
frozen_states = d01.frozen_states
ocv = d01.ocv
terminal_voltage = d01.terminal_voltage


def test_scenario_identity_is_synthetic_and_marks_src01_gap():
    report = build_report()
    assert report["scenario_id"] == SCENARIO_ID
    assert "SRC01" in report["identity"] and "not cell data" in report["identity"]


def test_three_states_share_one_terminal_voltage():
    states = frozen_states()
    assert len(states) == 3
    voltages = {s["v"] for s in states}
    assert len(voltages) == 1, f"教学状态漂移：{voltages}"
    assert math.isclose(states[0]["v"], 3.28, abs_tol=1e-9)


def test_same_voltage_hides_a_70pp_soc_spread():
    report = build_report()
    assert report["soc_spread_pp"] == pytest.approx(70.0)
    zs = sorted(s["z"] for s in report["states"])
    assert zs == [0.20, 0.55, 0.90]


def test_internal_terms_differ_under_the_same_reading():
    states = frozen_states()
    ocv_values = {s["ocv_v"] for s in states}
    ir_drops = {round(s["load_a"] * s["resistance_ohm"], 4) for s in states}
    assert len(ocv_values) == 3, "三个状态的 OCV 必须不同"
    assert len(ir_drops) >= 2, "内阻压降必须能区分至少两个状态"


def test_ocv_is_monotone_and_bounded():
    samples = [ocv(i / 100) for i in range(101)]
    assert samples == sorted(samples)
    assert 3.00 <= samples[0] and samples[-1] <= 3.45


def test_terminal_voltage_rejects_negative_resistance_or_polarization():
    with pytest.raises(ValueError):
        terminal_voltage(0.5, 1.0, -0.01, 0.0)
    with pytest.raises(ValueError):
        terminal_voltage(0.5, 1.0, 0.01, -0.001)
    with pytest.raises(ValueError):
        ocv(1.2)
