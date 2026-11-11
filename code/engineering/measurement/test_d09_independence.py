"""D09 independence claims, latent-fault arithmetic, and FMEA micro-case."""

import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d09_independence", HERE / "d09_independence.py"
)
assert spec is not None and spec.loader is not None
d09 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d09
spec.loader.exec_module(d09)


def test_latent_exposure_scales_with_diagnostic_interval():
    assert d09.latent_exposure_per_h() == pytest.approx(5e-7)
    assert d09.latent_exposure_per_h(diag_interval_h=24.0) == pytest.approx(1.2e-5)
    with pytest.raises(ValueError):
        d09.latent_exposure_per_h(lambda_per_h=-1.0)


def test_report_compares_cycle_average_probabilities():
    latent = d09.build_report()["latent"]
    assert latent["ratio"] == pytest.approx(100.0)
    assert latent["with_diag_1h"] == pytest.approx(5e-7)
    assert latent["with_diag_100h"] == pytest.approx(5e-5)
    # The end-of-100h probability remains available, but is not the ratio numerator.
    assert latent["undiagnosed_100h"] == pytest.approx(1e-4)
    assert latent["with_diag_100h"] * 2 == pytest.approx(latent["undiagnosed_100h"])




def test_report_identity_marks_teaching():
    report = d09.build_report()
    assert "teaching" in report["identity"]
