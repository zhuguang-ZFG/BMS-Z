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
    report = d09.build_report()
    assert report["latent"]["undiagnosed_100h"] == pytest.approx(1e-4)
    assert report["latent"]["ratio"] == pytest.approx(200.0)
    with pytest.raises(ValueError):
        d09.latent_exposure_per_h(lambda_per_h=-1.0)


def test_independence_matrix_only_full_cell_is_independence():
    matrix = d09.independence_matrix()
    assert len(matrix) == 4
    full = [m for m in matrix if m["coverage"] == "高" and m["isolated"]]
    assert len(full) == 1 and "完整含义" in full[0]["buys"]
    half = [m for m in matrix if m["coverage"] == "高" and not m["isolated"]]
    assert "双杀" in half[0]["buys"]


def test_common_supply_kills_backup():
    cs = d09.common_supply_counterexample()
    assert cs["failure"] == "供电轨失效"
    assert "概率为 0" in cs["result"]
    assert "失效模式逐条审" in cs["conclusion"]


def test_fmea_rows_have_controls_and_one_declared_gap():
    rows = d09.fmea_rows()
    assert len(rows) == 4
    assert all(r["control"] and r["action"] for r in rows)
    gap = [r for r in rows if "共因缺口明示" in r["control"]]
    assert len(gap) == 1, "FMEA 必须明示共因覆盖缺口，不许全绿"


def test_report_identity_marks_teaching():
    report = d09.build_report()
    assert "teaching" in report["identity"]
    assert "不藏" in report["conclusion"]
