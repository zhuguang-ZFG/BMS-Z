"""D12 SOC baseline bookkeeping and OCV calibration conditions."""
import importlib.util
import json
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


# --- D12-profile-replay：时间序列回放 + 独立工况 + 可执行校正 ---

def test_profile_replay_frozen_chain():
    r = d12.replay_profile(d12.generate_profile())
    # 库仑计：初值偏高 10 pp + 0.05 A 偏置（含静置段）+ 容量高估 5%，1 h 放电末误差冻结
    assert r["coulomb_only"]["final_error_pp"] == pytest.approx(10.20, abs=0.01)
    assert r["coulomb_only"]["max_abs_error_pp"] >= abs(
        r["coulomb_only"]["final_error_pp"]
    )


def test_ocv_correction_steep_window_residual():
    r = d12.replay_profile(d12.generate_profile())
    w1 = r["windows"][0]
    assert w1["id"] == "W1_tune" and w1["role"] == "tune"
    assert w1["corrected"] is True
    assert w1["error_before_pp"] == pytest.approx(9.84, abs=0.01)  # t=240 静置门通过点
    assert w1["error_after_pp"] == pytest.approx(0.625, abs=0.001)
    assert w1["residual_pp"] == pytest.approx(0.625, abs=0.001)  # 5 mV / 0.8 斜率
    assert r["tuned_gain"] == pytest.approx(1.0)


def test_flat_window_held_out_and_harmful_correction_flagged():
    r = d12.replay_profile(d12.generate_profile())
    w2 = r["windows"][1]
    assert w2["id"] == "W2_validate" and w2["role"] == "validate"
    assert w2["corrected"] is True
    # 校正前轨迹已被 W1 拉回，残余误差 1.18 pp < 平坦区残差 6.25 pp：校正反而扩大误差
    assert w2["error_before_pp"] == pytest.approx(1.18, abs=0.01)
    assert w2["error_after_pp"] == pytest.approx(6.25, abs=0.01)
    assert w2["harmful"] is True
    assert w2["reliable"] is False  # 平坦区残差 6.25 pp 是陡峭区的 10 倍
    assert r["corrected"]["max_abs_error_pp"] < r["coulomb_only"]["max_abs_error_pp"]


def test_residual_is_declared_uncertainty_not_posterior_fit():
    r = d12.replay_profile(d12.generate_profile())
    w1, w2 = r["windows"]
    # 全校正后同分段内电压残差≈0，但验收残差必须仍由声明不确定度/斜率给出
    assert w1["posterior_v_residual_mv"] == pytest.approx(0.0, abs=1e-6)
    assert w2["posterior_v_residual_mv"] == pytest.approx(0.0, abs=1e-6)
    assert w1["residual_pp"] == pytest.approx(0.625, abs=0.001)
    assert w2["residual_pp"] == pytest.approx(6.25, abs=0.01)
    # 残差不随后验拟合归零：W2 reliable 仍为 False
    assert w2["reliable"] is False


def test_rest_gate_refuses_insufficient_rest():
    # 每窗只给 3 拍静置观测（<5 拍门限）：两窗都必须拒校正，corrected 与 coulomb 完全一致
    frames = []
    for t in range(0, 2701, 60):
        cur = 2.0 if 600 < t <= 2100 else 0.0
        frames.append({"t_s": float(t), "current_a": cur, "v_meas": None, "true_soc_pp": 80.0})
    for i in (0, 1, 2, 35, 36, 37):  # W1 三拍 + W2 三拍静置观测
        frames[i]["v_meas"] = 3.7
    r = d12.replay_profile(frames)
    assert all(w["corrected"] is False for w in r["windows"])
    assert all("静置" in w["reason"] for w in r["windows"])
    assert r["series"]["corrected"] == r["series"]["coulomb"]
    assert r["tuned_gain"] is None


def test_truth_edit_does_not_move_estimator():
    frames = d12.generate_profile()
    base = d12.replay_profile(frames)
    edited = [dict(f) for f in frames]
    for f in edited:
        if f["t_s"] > 2100:  # 只改验证窗参考真值
            f["true_soc_pp"] = min(100.0, f["true_soc_pp"] + 5.0)
    r = d12.replay_profile(edited)
    assert r["series"] == base["series"]  # 估计轨迹不动
    assert r["tuned_gain"] == base["tuned_gain"]
    assert r["windows"][1]["error_before_pp"] == pytest.approx(
        base["windows"][1]["error_before_pp"] - 5.0, abs=0.01
    )


def test_gain_tuned_only_on_tune_window():
    r1 = d12.replay_profile(d12.generate_profile())
    # 只影响放电分支验证窗观测的迟滞失配（烘进 v_meas）：调校增益必须不变
    r2 = d12.replay_profile(d12.generate_profile(hysteresis_mv=10.0))
    assert r1["tuned_gain"] == pytest.approx(r2["tuned_gain"])
    assert r2["windows"][1]["error_after_pp"] != pytest.approx(
        r1["windows"][1]["error_after_pp"]
    )


def test_replay_deterministic_and_csv_roundtrip(tmp_path):
    frames = d12.generate_profile()
    a = d12.replay_profile(frames)
    p = tmp_path / "profile.csv"
    d12.write_profile_csv(frames, p)
    b = d12.replay_profile(d12.load_profile(p))
    assert a == b


def test_replay_rejects_bad_profile(tmp_path):
    hdr = "t_s,current_a,v_meas,true_soc_pp"
    bad_cases = {
        "missing_col.csv": hdr + "\n0,0,3.6\n",
        "nonfinite.csv": hdr + "\n0,nan,,80\n",
        "bad_vmeas.csv": hdr + "\n0,0,inf,80\n",
        "time_back.csv": hdr + "\n10,0,,80\n5,0,,80\n",
        "soc_range.csv": hdr + "\n0,0,,120\n",
    }
    for name, content in bad_cases.items():
        p = tmp_path / name
        p.write_text(content + "\n", encoding="utf-8")
        with pytest.raises(ValueError):
            d12.replay_profile(d12.load_profile(p))


def test_cli_profile_replay_writes_series_and_report(tmp_path):
    out = tmp_path / "out"
    rc = d12.main(["--out", str(out)])
    assert rc == 0
    assert (out / "profile.csv").exists()
    assert (out / "soc_series.csv").exists()
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    replay = report["profile_replay"]
    assert replay["scenario_id"] == "D12-profile-replay"
    assert replay["windows"][1]["reliable"] is False
    # 旧场景字段不回归
    assert report["bias_drift_pp_per_h"] == pytest.approx(2.5)


def test_cli_profile_missing_file_exit2(tmp_path):
    rc = d12.main(["--profile", str(tmp_path / "absent.csv"), "--out", str(tmp_path / "o")])
    assert rc == 2
