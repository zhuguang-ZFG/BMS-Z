"""Cross-check the teaching examples against independent matrix calculations."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]


def evidence(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "bms-book/code"))
    import ekf_covariance_evidence
    return ekf_covariance_evidence


def test_prediction_can_increase_one_variance_and_decrease_another(monkeypatch):
    result = evidence(monkeypatch).prediction_example()
    delta = np.diag([result["soc_variance_after"] - 0.01,
                     result["urc_variance_after"] - 1e-4])
    assert np.linalg.eigvalsh(delta).min() < 0 < np.linalg.eigvalsh(delta).max()
    assert result["urc_sigma_after_mv"] == pytest.approx(9.725049251067283)


def test_signed_contributions_sum_to_the_scalar_measurement_update(monkeypatch):
    rows = evidence(monkeypatch).innovation_allocations()
    for row in rows:
        assert row["soc_share"] + row["urc_share"] == pytest.approx(row["total_share"])
        assert row["total_share"] == pytest.approx(1 - 2.5e-5 / row["s_var"])
        assert 0 <= row["total_share"] < 1
    assert rows[1]["soc_share"] == pytest.approx(0.8825644490514595)
    assert rows[1]["urc_share"] == pytest.approx(-0.2704029079797509)
    assert rows[1]["total_share"] == pytest.approx(0.6121615410717085)


@pytest.mark.parametrize("fixed_c", [False, True])
@pytest.mark.parametrize("current,residual", [(-2.0, 0.002), (12.0, 0.002), (-2.0, 0.004)])
def test_controlled_trace_matches_repository_numpy_estimator(monkeypatch, fixed_c, current, residual):
    module = evidence(monkeypatch)
    monkeypatch.syspath_prepend(str(ROOT / "code/soc"))
    spec = importlib.util.spec_from_file_location("covariance_reference", ROOT / "code/soc/estimators.py")
    reference = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = reference
    spec.loader.exec_module(reference)
    kwargs = {"ocv_func": lambda s: 3.2 + 0.8 * s, "docv_func": lambda s: 0.8} if fixed_c else {}
    estimator = reference.EKFEstimator(0.80, 10.0, 0.033, 0.016, 2200.0, **kwargs)
    a = np.exp(-1 / 35.2)
    for row in module.controlled_trace(current, residual, fixed_c=fixed_c):
        soc_pred = estimator.x[0] + current / 36000
        urc_pred = a * estimator.x[1] + 0.016 * (1 - a) * current
        voltage = estimator.ocv_func(soc_pred) + 0.033 * current + urc_pred + residual
        estimator.step(current, voltage, 1.0)
        np.testing.assert_allclose(row["covariance"], estimator.P, rtol=1e-11, atol=1e-16)
        assert row["soc"] == pytest.approx(estimator.x[0], abs=1e-12)
        assert 0 < row["soc"] < 1


@pytest.mark.parametrize("varied", ["current", "voltage"])
def test_frozen_jacobian_is_the_condition_for_data_independence(monkeypatch, varied):
    module = evidence(monkeypatch)
    fixed = module.dependency_comparison(True, varied)
    nonlinear = module.dependency_comparison(False, varied)
    assert fixed["max_soc_variance_difference"] == 0
    assert fixed["max_urc_variance_difference"] == 0
    assert nonlinear["max_soc_variance_difference"] > 1e-8
    assert nonlinear["max_urc_variance_difference"] > 1e-9
