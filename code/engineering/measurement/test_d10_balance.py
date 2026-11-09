"""D10 balancing arithmetic and the three-differences discipline."""

import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d10_balance", HERE / "d10_balance.py")
assert spec is not None and spec.loader is not None
d10 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d10
spec.loader.exec_module(d10)


def test_bleed_current_heat_and_time():
    assert d10.bleed_ma() == pytest.approx(35.0)
    assert d10.bleed_heat_w() == pytest.approx(3.5 * 3.5 / 100, rel=1e-6)
    assert d10.balance_time_h(0.05, 35.0) == pytest.approx(1.429, abs=1e-3)
    report = d10.build_report()
    assert report["bleed"]["balance_0p05Ah_min"] == pytest.approx(85.7, abs=0.1)
    with pytest.raises(ValueError):
        d10.balance_time_h(-0.1, 35.0)


def test_voltage_difference_is_not_soc_difference_across_regions():
    diff = d10.three_differences()["voltage_vs_soc"]
    assert diff["implied_soc_diff_pp"] == pytest.approx(25.0)
    assert "不能跨区间" in diff["reading"]


def test_capacity_weak_cell_is_unbalanceable():
    diff = d10.three_differences()["soc_vs_capacity"]
    assert diff["balanceable"] is False
    assert "永远在" in diff["reading"]


def test_measurement_pause_marks_valid_samples():
    pause = d10.measurement_pause()
    assert pause["valid_fraction"] == pytest.approx(0.5)
    assert pause["cycle_ms"] == pytest.approx(40.0)
    assert "标记无效" in pause["marking_rule"]


def test_report_identity_marks_teaching():
    report = d10.build_report()
    assert report["scenario_id"] == d10.SCENARIO_ID
    assert "teaching" in report["identity"]
