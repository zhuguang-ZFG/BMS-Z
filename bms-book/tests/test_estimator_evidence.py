"""Numerical contracts for the estimator calculations readers reproduce."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1] / "code"


def load(name):
    # These modules have no import-time experiments; dataclass needs registration.
    import sys
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("scale", [1.0, 1e-7])
def test_joseph_covariance_matches_independent_information_form(scale):
    module = load("ekf_soc")
    prior = np.array([[0.01, 0.0003], [0.0003, 0.0001]]) * scale
    observation = np.array([[0.8, 1.0]])
    variance = 2.5e-5 * scale
    gain = prior @ observation.T / (observation @ prior @ observation.T + variance)
    updated = np.array(module.joseph_covariance(
        *prior.ravel(), *gain.ravel(), *observation.ravel(), variance,
    )).reshape(2, 2)
    # Posterior precision = prior precision + measurement precision.
    reference = np.linalg.inv(np.linalg.inv(prior) + observation.T @ observation / variance)
    np.testing.assert_allclose(updated, reference, rtol=1e-11, atol=1e-18)
    assert np.linalg.eigvalsh(updated).min() > 0


def test_capacity_uncertainty_includes_endpoint_covariance():
    module = load("estimator_evidence")
    _, independent = module.capacity_sigma(0.72, 0.4, 0.02, 0.01, 0.01)
    _, common_offset = module.capacity_sigma(0.72, 0.4, 0.02, 0.01, 0.01, correlation=1)
    # Perfectly shared endpoint error cancels in the SOC difference.
    assert common_offset == pytest.approx(0.02 / 0.4)
    assert independent > common_offset
    with pytest.raises(ValueError):
        module.capacity_sigma(0.72, 0, 0.02, 0.01, 0.01)
