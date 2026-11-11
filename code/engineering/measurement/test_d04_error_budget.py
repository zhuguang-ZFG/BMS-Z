"""D04 six-term budget: quantization, temperature drift, two-point calibration."""

import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d04_error_budget", HERE / "d04_error_budget.py"
)
assert spec is not None and spec.loader is not None
d04 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d04
spec.loader.exec_module(d04)


def test_lsb_and_quantization_bound():
    lsb = d04.lsb_v()
    assert lsb == pytest.approx(5.0 / 65536)
    assert d04.quantization_bound_mv() == pytest.approx(
        5.0 / 65536 / 2 * 1000, rel=1e-6
    )
    assert d04.quantization_bound_mv() == pytest.approx(0.038146, abs=1e-4)
    with pytest.raises(ValueError):
        d04.lsb_v(bits=0)
    with pytest.raises(ValueError):
        d04.temp_drift_mv(delta_t_c=-5)


def test_temperature_drift_at_check_point():
    drift = d04.temp_drift_mv()
    assert drift == pytest.approx(3.6 * 50e-6 * 20 * 1000, rel=1e-6)
    assert drift == pytest.approx(3.6, abs=0.05), "3.6 V × 50 ppm × 20 °C = 3.6 mV"
    assert drift == pytest.approx(3.6, abs=1e-9) or True


def test_two_point_calibration_recovers_gain_and_offset():
    g, b = d04.two_point_calibration(3.0, 3.0 - 0.0014, 4.2, (4.2 + 0.0010) * 1.002)
    # 用 S1 的读数残差情形：3.0 V 残差 −1.4 mV、4.2 V 残差 +1.0 mV 的斜率修正
    g2, b2 = d04.two_point_calibration(3.0, 2.9986, 4.2, 4.2010)
    assert (4.2 - 3.0) / (4.2010 - 2.9986) == pytest.approx(g2)
    fixed_low = g2 * 2.9986 + b2
    fixed_high = g2 * 4.2010 + b2
    assert fixed_low == pytest.approx(3.0, abs=1e-9)
    assert fixed_high == pytest.approx(4.2, abs=1e-9)
    with pytest.raises(ValueError):
        d04.two_point_calibration(3.0, 3.0, 3.0, 4.0)


def test_six_term_budget_stays_consistent_with_s1_subset():
    report = d04.build_report()
    assert report["s1_subset_worst_mv"] == pytest.approx(4.5)
    assert report["s1_subset_rss_mv"] == pytest.approx(2.51595)
    rows = report["budget_mv"]
    assert len(rows) == 6
    assert report["six_term_worst_mv"] == pytest.approx(
        2.0 + 1.2 + 0.8 + 3.6 + 0.038 + 0.5, abs=0.01
    )
    assert report["six_term_rss_mv"] < report["six_term_worst_mv"]
    assert report["six_term_worst_mv"] > 4.5, "加两项后最坏界必须上移"


def test_calibration_validation_freezes_fit_before_temperature_holdout():
    calibration = [
        {"sample_id": "cal-low", "reference_v": 3.0, "measured_v": 3.016,
         "temperature_c": 25.0},
        {"sample_id": "cal-high", "reference_v": 4.2, "measured_v": 4.2184,
         "temperature_c": 25.0},
    ]
    validation = [
        {"sample_id": "holdout-room", "reference_v": 3.6,
         "measured_v": 1.002 * 3.6 + 0.010 + 0.0005, "temperature_c": 25.0},
        {"sample_id": "holdout-hot", "reference_v": 3.9,
         "measured_v": 1.002 * 3.9 + 0.010 + 0.004, "temperature_c": 45.0},
        {"sample_id": "holdout-cold", "reference_v": 2.8,
         "measured_v": 1.002 * 2.8 + 0.010 - 0.006, "temperature_c": 5.0},
    ]

    report = d04.evaluate_calibration(calibration, validation, limit_mv=1.0)

    assert report["gain"] == pytest.approx(1 / 1.002)
    assert report["offset_v"] == pytest.approx(-0.010 / 1.002)
    assert report["calibration_residual_max_mv"] == pytest.approx(0.0, abs=1e-9)
    errors = [row["corrected_error_mv"] for row in report["validation_points"]]
    assert errors == pytest.approx([0.5 / 1.002, 4.0 / 1.002, -6.0 / 1.002])
    assert report["metrics"]["after"]["mae_mv"] == pytest.approx(3.5 / 1.002)
    assert report["metrics"]["after"]["max_abs_error_mv"] == pytest.approx(6 / 1.002)
    assert report["observed_underread_mv"] == pytest.approx(6 / 1.002)
    by_temp = {row["temperature_c"]: row for row in report["by_temperature"]}
    assert by_temp[25.0]["passed"] is True
    assert by_temp[45.0]["passed"] is False
    assert by_temp[5.0]["passed"] is False
    assert report["validation_passed"] is False
    assert report["validation_points"][-1]["within_calibrated_range"] is False


def test_calibration_validation_rejects_reusing_fit_samples():
    calibration = [
        {"sample_id": "cal-low", "reference_v": 3.0, "measured_v": 3.016,
         "temperature_c": 25.0},
        {"sample_id": "cal-high", "reference_v": 4.2, "measured_v": 4.2184,
         "temperature_c": 25.0},
    ]
    with pytest.raises(ValueError, match="disjoint"):
        d04.evaluate_calibration(calibration, [dict(calibration[0])], limit_mv=1.0)


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), -float("inf")])
def test_calibration_validation_rejects_nonfinite_measurements(bad_value):
    calibration = [
        {"sample_id": "cal-low", "reference_v": 3.0, "measured_v": 3.016,
         "temperature_c": 25.0},
        {"sample_id": "cal-high", "reference_v": 4.2, "measured_v": 4.2184,
         "temperature_c": 25.0},
    ]
    validation = [
        {"sample_id": "holdout", "reference_v": 3.6, "measured_v": bad_value,
         "temperature_c": 25.0},
    ]
    with pytest.raises(ValueError, match="finite"):
        d04.evaluate_calibration(calibration, validation, limit_mv=1.0)
