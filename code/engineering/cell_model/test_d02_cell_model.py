"""D02 model-order and hysteresis counterexamples."""
import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d02_cell_model", HERE / "d02_cell_model.py"
)
assert spec is not None and spec.loader is not None
d02 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d02
spec.loader.exec_module(d02)


def test_zoh_simulation_recovers_truth_exactly_with_2rc():
    report = d02.build_report()
    fit2 = report["fit_2rc"]
    assert sorted(round(t, 3) for t in fit2["taus"]) == [1.0, 45.0]
    assert fit2["rms_mv"] < 1e-6, "无噪合成数据上 2RC 拟合应达机器精度"
    assert report["ohmic_jump_mv"] == pytest.approx(40.0)


def test_1rc_fit_is_biased_and_keeps_early_residual():
    report = d02.build_report()
    fit1 = report["fit_1rc"]
    assert round(fit1["taus"][0], 1) == 31.5, "欠模型把 τ 拉偏（真值 45 s 与 1 s 的折中）"
    windows = report["window_rms_mv"]
    assert windows["1rc_early_0_5s"] == pytest.approx(3.0565, abs=1e-3)
    assert windows["1rc_late_60_180s"] == pytest.approx(0.1317, abs=1e-3)
    assert windows["1rc_early_0_5s"] > 20 * windows["1rc_late_60_180s"]
    assert windows["2rc_early_0_5s"] < 1e-6


def test_hysteresis_inversion_error_scales_with_width_over_slope():
    h = d02.hysteresis_inversion_error_pp()
    assert h["scenario_id"] == d02.HYSTERESIS_SCENARIO_ID
    assert h["ocv_charge_v"] == pytest.approx(3.605)
    assert h["ocv_discharge_v"] == pytest.approx(3.595)
    assert h["inversion_error_pp"] == pytest.approx(1.25)
    assert h["width_mv"] == pytest.approx(10.0)


def test_pulse_soc_drop_matches_analytic():
    rows = d02.simulate_2rc()
    pulse_rows = [r for r in rows if r["i_a"] > 0]
    dz = pulse_rows[0]["z"] - pulse_rows[-1]["z"]
    # 首样本是脉冲起点的状态，末样本之前已更新 N-1 拍
    elapsed_s = (len(pulse_rows) - 1) * d02.DT_S
    expect = d02.PULSE_A * elapsed_s / (3600.0 * d02.Q_AH)
    assert dz == pytest.approx(expect)
    assert dz == pytest.approx(2.0 * 9.5 / 7200.0, abs=1e-9)


def test_rest_tail_is_monotone_recovery():
    tail = d02.rest_tail(d02.simulate_2rc())
    vs = [v for _t, v in tail]
    diffs = [b - a for a, b in zip(vs, vs[1:], strict=False)]
    assert all(d > 0 for d in diffs), "撤流后极化消退，电压单调回升"
    assert tail[0][0] == pytest.approx(0.0)


def test_report_identity_marks_synthetic_extension_of_s2():
    report = d02.build_report()
    assert report["scenario_id"] == d02.SCENARIO_ID
    assert "S2" in report["identity"] and "synthetic" in report["identity"]
    assert report["truth"]["tau1_s"] == pytest.approx(45.0)
    assert report["truth"]["tau2_s"] == pytest.approx(1.0)
