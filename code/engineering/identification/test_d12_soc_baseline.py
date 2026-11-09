"""D12 SOC baseline bookkeeping and OCV calibration conditions."""
import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d12_soc_baseline", HERE / "d12_soc_baseline.py"
)
assert spec is not None and spec.loader is not None
d12 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d12
spec.loader.exec_module(d12)


def test_bias_drift_scales_linearly_with_time():
    assert d12.bias_drift_pp() == pytest.approx(2.5)
    assert d12.bias_drift_pp(hours=10.0) == pytest.approx(25.0)
    with pytest.raises(ValueError):
        d12.bias_drift_pp(q_ah=0.0)


def test_capacity_error_is_a_gain_error_on_delta():
    err = d12.capacity_gain_error_pp(100.0)
    assert err == pytest.approx(100.0 - 100.0 / 1.05, rel=1e-6)
    assert err == pytest.approx(4.76, abs=0.01)
    assert d12.capacity_gain_error_pp(0.0) == pytest.approx(0.0)


def test_ocv_calibration_residual_scales_with_inverse_slope():
    assert d12.calibration_residual_pp(5.0, 0.8) == pytest.approx(0.625, abs=1e-6)
    assert d12.calibration_residual_pp(5.0, 0.08) == pytest.approx(6.25, abs=1e-6)
    assert d12.calibration_residual_pp(0.0, 0.8, 10.0) == pytest.approx(1.25, abs=1e-6)
    with pytest.raises(ValueError):
        d12.calibration_residual_pp(5.0, 0.0)


def test_report_matches_frozen_chain():
    report = d12.build_report()
    assert report["bias_drift_pp_per_h"] == pytest.approx(2.5)
    assert report["ocv_correction"]["steep_region"]["residual_5mv_pp"] == pytest.approx(0.62, abs=0.01)
    assert report["ocv_correction"]["flat_region"]["residual_5mv_pp"] == pytest.approx(6.25)
    assert report["ocv_correction"]["hysteresis_mismatch"]["residual_0mv_with_10mv_hyst_pp"] == pytest.approx(1.25)
    assert report["scenario_id"] == d12.SCENARIO_ID
