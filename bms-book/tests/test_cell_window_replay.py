"""Regression checks for chapter 3's voltage-to-SOC unit conversion."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "cell_window_replay",
    Path(__file__).resolve().parents[1] / "code" / "cell_window_replay.py",
)
assert spec is not None
assert spec.loader is not None
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


def test_voltage_window_gap_keeps_absolute_and_relative_units_separate():
    gap_v, gap_percent = replay.voltage_window_gap_v(4.20, 3.65)
    assert gap_v == pytest.approx(0.55)
    assert gap_percent == pytest.approx(100 * 0.55 / 3.65)


@pytest.mark.parametrize(
    "detector,cutoff",
    [(3.65, 3.65), (3.60, 3.65), (4.20, 0.0), (float("nan"), 3.65)],
)
def test_voltage_window_gap_rejects_invalid_inputs(detector, cutoff):
    with pytest.raises(ValueError):
        replay.voltage_window_gap_v(detector, cutoff)


def test_slope_conversion_returns_percentage_points_not_relative_percent():
    assert replay.soc_uncertainty_pp(20.0, 0.75) == pytest.approx(20.0 / 0.75)
    assert replay.soc_uncertainty_pp(2.0, 0.75) == pytest.approx(2.0 / 0.75)
    assert replay.soc_uncertainty_pp(20.0, 10.0) == pytest.approx(2.0)


def test_relative_soc_error_requires_an_explicit_reference_soc():
    uncertainty_pp = replay.soc_uncertainty_pp(20.0, 0.75)
    assert replay.relative_soc_error_percent(uncertainty_pp, 50.0) == pytest.approx(100 * uncertainty_pp / 50.0)
    assert replay.relative_soc_error_percent(2.0, 50.0) == pytest.approx(4.0)


def test_relative_error_rejects_negative_uncertainty():
    with pytest.raises(ValueError):
        replay.relative_soc_error_percent(-1.0, 50.0)


@pytest.mark.parametrize("slope", [0.0, -0.75, float("nan"), float("inf")])
def test_nonpositive_or_nonfinite_slope_is_rejected(slope):
    with pytest.raises(ValueError):
        replay.soc_uncertainty_pp(20.0, slope)


@pytest.mark.parametrize("error", [-1.0, float("nan"), float("inf")])
def test_negative_or_nonfinite_voltage_error_is_rejected(error):
    with pytest.raises(ValueError):
        replay.soc_uncertainty_pp(error, 0.75)


@pytest.mark.parametrize("soc", [0.0, -1.0, 100.1, float("nan"), float("inf")])
def test_relative_error_rejects_an_invalid_reference_soc(soc):
    with pytest.raises(ValueError):
        replay.relative_soc_error_percent(20.0, soc)


def test_default_replay_prints_both_units_and_the_four_chapter_results(capsys):
    replay.main()
    output = capsys.readouterr().out
    assert "26.7 个百分点" in output
    assert "SOC=50.0% 时约合 53.3% 相对误差" in output
    assert "0.5C @ 50 Ah = 25 A" in output
    assert "10 A 在 10 Ah 上是 1.0C，在 50 Ah 上是 0.2C" in output
    assert "16 串 × 3.65 V = 58.4 V" in output
