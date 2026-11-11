"""D16 lumped thermal network, sensor placement, and identification contract."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d16_thermal", HERE / "d16_thermal.py")
assert spec is not None and spec.loader is not None
d16 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d16
spec.loader.exec_module(d16)


@pytest.fixture(scope="module")
def report():
    return d16.build_report()


def test_network_modes_and_steady_state_frozen(report):
    assert report["modes"]["tau_fast_s"] == pytest.approx(76.9506)
    assert report["modes"]["tau_slow_s"] == pytest.approx(421.0494)
    ss = report["steady_state_10a"]
    assert ss["core_c"] == pytest.approx(79.5)
    assert ss["core_case_gap_k"] == pytest.approx(27.0)  # P·R_cs = 9 W × 3 K/W


def test_silent_band_core_over_limit_no_sensor_trips(report):
    # 沉默带反例：10 A 恒流下芯温超芯限 8.45 K，壳温与全部测点都未到阈
    ce = report["counterexample_structural"]
    assert ce["core_over_limit_k"] == pytest.approx(8.4471)
    assert ce["case_margin_k"] == pytest.approx(8.2828)
    assert ce["any_sensor_tripped"] is False
    band = report["silent_band"]
    assert band["current_low_a"] == pytest.approx(8.9893, rel=1e-3)
    assert band["gap_at_case_trip_k"] == pytest.approx(36.0)


def test_step_response_lag_fractions_frozen(report):
    lag = report["counterexample_lag"]["sensors"]
    assert lag["tab_bonded"]["fraction_of_core"] == pytest.approx(0.0725)
    assert lag["pcb_remote"]["fraction_of_core"] == pytest.approx(0.0137)


def test_divider_vs_lag_runs_and_freezes_detection_times(report):
    # 回归：divider_vs_lag 曾引用未注册测点直接 ValueError（CLI 默认场景 exit 2）
    dv = report["divider_vs_lag"]
    assert dv["perfect_divider_slow_ntc"]["detect_since_step_s"] == pytest.approx(509.0)
    assert dv["divider_0_92_fast_ntc"]["detect_since_step_s"] == pytest.approx(555.0)
    # 热分压 0.92 让目标温度永远差一截，再快的 NTC 也补不回来——分压主导检测时刻
    assert dv["perfect_divider_slow_ntc"]["detect_since_step_s"] < dv[
        "divider_0_92_fast_ntc"
    ]["detect_since_step_s"]


def test_sensor_step_rejects_unknown_placement():
    with pytest.raises(ValueError, match="未知测点"):
        d16.sensor_step(30.0, 60.0, 30.0, "not_a_sensor")
    # 显式传入 placements 表时不查全局注册表（divider_vs_lag 的合法路径）
    out = d16.sensor_step(30.0, 60.0, 30.0, "custom", placements={"custom": (10.0, 1.0)})
    assert out == pytest.approx(30.0 + 30.0 * (1.0 - pow(2.718281828459045, -1.0 / 10.0)), rel=1e-3)


def test_trip_delay_s_analytic_properties():
    assert d16.trip_delay_s(30.0, 50.0, 10.0, 40.0) == pytest.approx(6.9315, rel=1e-3)
    assert d16.trip_delay_s(30.0, 40.0, 10.0, 40.0) == float("inf")  # 目标不高于阈
    assert d16.trip_delay_s(45.0, 50.0, 10.0, 40.0) == 0.0  # 起点已过阈
    with pytest.raises(ValueError):
        d16.trip_delay_s(30.0, 50.0, 0.0, 40.0)


def test_trip_budget_thermal_chain_dwarfs_d08_window(report):
    budget = report["trip_budget"]
    assert budget["thermal_trip_s"] == pytest.approx(593.0)
    assert budget["d08_worst_ms"] == pytest.approx(72.263)
    assert budget["ratio"] == pytest.approx(8206.1, rel=1e-3)  # 热链路是电气链的千倍级


def test_sop_current_decreases_with_ambient(report):
    assert report["sop"]["ambient_30_a"] == pytest.approx(8.9893, rel=1e-3)
    assert report["sop"]["ambient_45_a"] == pytest.approx(7.1067, rel=1e-3)
    assert report["sop"]["ambient_45_a"] < report["sop"]["ambient_30_a"]
    with pytest.raises(ValueError):
        d16.sop_sustained_current_a(d16.CORE_LIMIT_C)


def test_placement_improvement_frozen(report):
    rows = {r["sensor"]: r for r in report["placement_improvement"]}
    assert rows["tab_bonded"]["underestimate_gain_k"] == pytest.approx(9.5083)
    assert rows["case_side"]["underestimate_gain_k"] == pytest.approx(7.6709)
    # 基准测点在整段工况内从未到阈：改进量只衡量「测到壳温」的忠实度
    assert rows["tab_bonded"]["baseline_never_tripped"] is True


def test_identification_frozen_and_short_window_boundary_flagged(report):
    ident = report["identification"]
    full = ident["full_window"]
    assert full["r_th_k_per_w"] == pytest.approx(2.626597)
    assert full["tau_s"] == pytest.approx(568.082)
    assert full["tau_at_grid_edge"] is False
    # 短窗把 τ 推到网格上沿：必须报边界，不得当成估计值
    short = ident["short_window"]
    assert short["tau_at_grid_edge"] is True
    # 留出工况（11 A / 35 °C，不参与辨识）验证 RMS 冻结
    assert ident["validation"]["rms_k"] == pytest.approx(0.9977)
    assert "held out" in ident["validation_profile"]


def test_load_identification_rejects_bad_csv(tmp_path):
    hdr = ",".join(d16.IDENT_COLUMNS)
    good = "0,5.0,30.0,30.0,30.0,30.0\n"
    bad_cases = {
        "hdr.csv": "t_s,q_w\n0,1.0\n",
        "nonfinite.csv": hdr + "\n0,inf,30.0,30.0,30.0,30.0\n",
        "gap.csv": hdr + "\n" + good + "120,5.0,30.0,30.0,30.0,30.0\n",  # 间隔 120 s > 60 s
        "time_back.csv": hdr + "\n" + good + "0,5.0,30.0,30.0,30.0,30.0\n",
        "few.csv": hdr + "\n" + good,  # 少于 20 样本
        "negative_q.csv": hdr + "\n0,-1.0,30.0,30.0,30.0,30.0\n",
    }
    for name, content in bad_cases.items():
        p = tmp_path / name
        p.write_text(content + "\n", encoding="utf-8")
        with pytest.raises(ValueError):
            d16.load_identification(p)


def test_cli_default_export_and_rejections(tmp_path):
    out = tmp_path / "out"
    rc = d16.main(["--out", str(out)])
    assert rc == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["scenario_id"] == "D16-thermal"
    assert report["identification"]["scenario_id"] == "D16-thermal-identification"
    assert (out / "thermal_log.csv").exists()
    assert (out / "identification.csv").exists()
    # 旧场景字段不回归：报告必须同时带固件边界
    assert "BmsInputs" in report["firmware_boundary"]
    assert d16.main(["--data", str(tmp_path / "absent.csv")]) == 2
    bad = tmp_path / "bad.csv"
    bad.write_text("t_s,q_w\n0,1.0\n", encoding="utf-8")
    assert d16.main(["--data", str(bad)]) == 2
