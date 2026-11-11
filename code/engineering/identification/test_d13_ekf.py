"""D13 hand round vs code, convergence, Q/R discipline, replay, gating, whitening
and the flat-region counterexample."""
import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d13_ekf", HERE / "d13_ekf.py")
assert spec is not None and spec.loader is not None
d13 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d13
spec.loader.exec_module(d13)


def test_hand_round_matches_analytic():
    h = d13.one_round_hand()
    assert h["innovation_mv"] == pytest.approx(4.1111, abs=1e-3)
    assert h["k_soc_per_v"] == pytest.approx(1.2469, abs=1e-3)
    assert h["expected_z_jump_pp"] == pytest.approx(0.5)
    # 修正量 = K × 新息 = 1.2469 × 4.1111 mV ≈ 0.5126 pp（新息含预测项的 0.111 mV）
    z_pred = 0.5 - 2.0 * 0.5 / 7200.0
    jump_pp = (h["z_after"] - z_pred) * 100
    assert jump_pp == pytest.approx(0.5126, abs=0.001)
    assert h["pd"] is True, "更新后协方差必须保持正定"


def test_covariance_guard():
    assert d13.is_positive_definite_2x2([[0.0025, 0.0], [0.0, 0.0001]]) is True
    assert d13.is_positive_definite_2x2([[-0.1, 0.0], [0.0, 0.0001]]) is False
    assert d13.is_positive_definite_2x2([[0.1, 0.2], [0.2, 0.1]]) is False

def test_convergence_z_fast_b_slow_with_weak_excitation():
    c = d13.convergence_from_wrong_init()
    assert c["z_final_error_pp"] == pytest.approx(-0.004, abs=0.02)
    assert c["b_final_error_ma"] < -49.0, "偏置在本组参数下应基本不收敛"
    assert "D14" in c["conclusion"]


def test_r_to_zero_collapses_covariance():
    q = d13.bad_qr_behaviour()
    assert q["p_trace_after_r0"] < 2e-4, "R→0 时 P 迹必须塌缩到接近初值方差"
    assert q["r_zero_z_path"][0] == pytest.approx(0.6)
    assert "不是调参旋钮" in q["conclusion"]


def test_report_identity_marks_units():
    report = d13.build_report()
    assert report["scenario_id"] == d13.SCENARIO_ID
    assert "units documented" in report["identity"]

def test_predict_covariance_is_symmetric_and_matches_fpf():
    import numpy as np
    p = [[0.0025, 0.0010], [0.0010, 0.0004]]
    got = np.array(d13.predict([0.5, 0.02], p, 1.7, 1e-8, 2e-8)[1])
    assert np.allclose(got, got.T), "预测协方差必须对称"
    f00, f01 = 1.0, d13.DT_S / (3600.0 * d13.Q_AH)
    f = np.array([[f00, f01], [0.0, 1.0]])
    q = np.diag([1e-8, 2e-8])
    expected = f @ np.array(p) @ f.T + q
    assert np.allclose(got, expected, atol=1e-12), "预测协方差必须等于 F P F^T + Q"


# --- D13 合同：手算逐点对拍、回放冻结数字、门限、白化、边界反例 ---

def test_hand_round_point_by_point_against_scalar_hand_calc():
    h = d13.one_round_hand()
    assert all(h["checkpoints"].values()), h["checkpoints"]
    assert h["max_abs_diff"] <= 1e-9
    # 手算与代码共享同一组公式的两种展开，12 个检查点全部对齐
    assert set(h["hand"]) == set(h["code"])
    assert h["hand"]["z_pred"] == pytest.approx(0.499861111111, abs=1e-12)
    assert h["hand"]["s"] == pytest.approx(0.0016040064, abs=1e-12)
    assert h["hand"]["p00_post"] == pytest.approx(6.234414e-6, rel=1e-6)


def test_replay_frozen_chain():
    frames = d13.generate_profile()
    assert len(frames) == 32
    coulomb = d13.run_coulomb(frames)
    ekf = d13.run_ekf(frames)
    assert coulomb["metrics"]["final_error_pp"] == pytest.approx(-10.3571, abs=1e-3)
    assert coulomb["metrics"]["max_abs_error_pp"] == pytest.approx(10.3968, abs=1e-3)
    assert ekf["metrics"]["final_error_pp"] == pytest.approx(0.2598, abs=1e-3)
    assert ekf["metrics"]["max_abs_error_pp"] == pytest.approx(1.2001, abs=1e-3)
    assert ekf["updates"] == 21
    assert ekf["rejected"] == 0
    assert ekf["final_bias_a"] == pytest.approx(0.00044, abs=1e-5)
    assert ekf["pd_final"] is True
    # EKF 的最大误差必须低于纯库仑计（同一 Q̂、同一初值）
    assert ekf["metrics"]["max_abs_error_pp"] < coulomb["metrics"]["max_abs_error_pp"]


def test_mismatch_comparison_frozen():
    variants = d13.mismatch_comparison()["variants"]
    assert variants["ekf_nominal"]["final_error_pp"] == pytest.approx(0.2598, abs=1e-3)
    assert variants["ekf_capacity_fixed"]["mean_abs_error_pp"] == pytest.approx(0.2897, abs=1e-3)
    assert variants["ekf_bias_frozen"]["final_error_pp"] == pytest.approx(0.2579, abs=1e-3)
    assert variants["ekf_ocv_offset_10mv"]["final_error_pp"] == pytest.approx(-0.9904, abs=1e-3)
    # 10 mV 表偏移在 0.8 斜率区只值 1.25 pp：比平坦区的 12.5 pp 小一个数量级
    assert variants["ekf_ocv_offset_10mv"]["mean_abs_error_pp"] == pytest.approx(0.7924, abs=1e-3)


def test_whitening_passes_on_model_matched_run():
    w = d13.innovation_whitening(d13.whitening_run())
    assert w["n"] == 21
    assert w["mean"] == pytest.approx(0.1044, abs=1e-3)
    assert w["std"] == pytest.approx(0.9219, abs=1e-3)
    assert w["nis_sum"] == pytest.approx(17.2286, abs=1e-3)
    assert w["within_95"] is True
    assert w["white"] is True
    assert w["chi2_95_low"] < w["nis_sum"] < w["chi2_95_high"]


def test_gate_rejects_bad_observation_and_keeps_prediction():
    frames = d13.generate_profile()
    idx = next(
        i for i, f in enumerate(frames)
        if f["v_meas"] is not None and f["t_s"] > d13.PROFILE_LOAD_TO_S
    )
    outlier = [dict(f) for f in frames]
    outlier[idx]["v_meas"] += 0.050  # +50 mV：约 7σ，必须被门限拒绝
    blinded = [dict(f) for f in frames]
    blinded[idx]["v_meas"] = None

    gated = d13.run_ekf(outlier, gate_sigma=d13.GATE_SIGMA)
    skipped = d13.run_ekf(blinded)
    ungated = d13.run_ekf(outlier, gate_sigma=None)

    assert gated["rejected"] == 1
    assert gated["rows"][idx]["rejected"] is True
    assert gated["rows"][idx]["updated"] is False
    # 拒绝更新后必须与“该拍没有观测”逐点同轨迹，而不是被拉走
    assert [r["z_pp"] for r in gated["rows"]] == [r["z_pp"] for r in skipped["rows"]]
    # 无门限时同一坏观测在当拍就把估计拉走 3.77 pp
    shift_pp = ungated["rows"][idx]["z_pp"] - gated["rows"][idx]["z_pp"]
    assert shift_pp == pytest.approx(3.7717, abs=1e-3)
    assert abs(shift_pp) > 2.0


def test_gate_does_not_reject_good_frames():
    ekf = d13.run_ekf(d13.generate_profile())
    assert ekf["rejected"] == 0
    assert ekf["updates"] == 21


def test_flat_region_counterexample_is_harmful_but_innovations_white():
    b = d13.flat_region_counterexample()
    assert b["frames"] == 161
    assert b["harmful"] is True
    assert b["coulomb_only"]["final_error_pp"] == pytest.approx(4.5556, abs=1e-3)
    assert b["ekf"]["final_error_pp"] == pytest.approx(-13.7047, abs=1e-3)
    assert b["ekf"]["mean_abs_error_pp"] == pytest.approx(10.7127, abs=1e-3)
    assert b["max_update_shift_pp"] == pytest.approx(10.4964, abs=1e-3)
    assert b["rejected"] == 0, "错误在模型里，门限看不到"
    assert b["whitening"]["white"] is True
    assert b["whitening"]["nis_mean"] == pytest.approx(1.0671, abs=1e-3)
    assert "新息白不等于模型对" in b["conclusion"]


def test_truth_edit_does_not_move_estimator():
    frames = d13.generate_profile()
    edited = [dict(f) for f in frames]
    for f in edited:
        f["true_soc_pp"] = 100.0 - f["true_soc_pp"]  # 只动参考真值列
    a = d13.run_ekf(frames)
    b = d13.run_ekf(edited)
    assert [r["z_pp"] for r in a["rows"]] == [r["z_pp"] for r in b["rows"]]
    assert [r["normalized_innovation"] for r in a["rows"]] == [
        r["normalized_innovation"] for r in b["rows"]
    ]


def test_profile_csv_roundtrip(tmp_path):
    frames = d13.generate_profile()
    path = tmp_path / "profile.csv"
    d13.write_profile_csv(frames, path)
    loaded = d13.load_profile(path)
    assert loaded == frames
    assert [r["z_pp"] for r in d13.run_ekf(loaded)["rows"]] == [
        r["z_pp"] for r in d13.run_ekf(frames)["rows"]
    ]


def test_cli_out_writes_report_profile_and_series(tmp_path):
    out = tmp_path / "evidence"
    assert d13.main(["--out", str(out)]) == 0
    import json
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["scenario_id"] == d13.SCENARIO_ID
    assert report["replay"]["ekf"]["final_error_pp"] == pytest.approx(0.2598, abs=1e-3)
    assert report["replay"]["coulomb_only"]["final_error_pp"] == pytest.approx(-10.3571, abs=1e-3)
    lines = (out / "ekf_series.csv").read_text(encoding="utf-8").strip().splitlines()
    assert lines[0] == "t_s,true_soc_pp,coulomb_soc_pp,ekf_soc_pp,innovation_mv,rejected"
    assert len(lines) == 33  # 表头 + 32 拍
    assert (out / "profile.csv").exists()


def test_cli_profile_replay_reports_custom_run(tmp_path):
    frames = d13.generate_profile()
    path = tmp_path / "profile.csv"
    d13.write_profile_csv(frames, path)
    out = tmp_path / "replay"
    assert d13.main(["--profile", str(path), "--out", str(out)]) == 0
    import json
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["profile_replay"]["metrics"]["final_error_pp"] == pytest.approx(0.2598, abs=1e-3)
    assert report["profile_replay"]["updates"] == 21


def _write_bad_profile(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "bad.csv"
    path.write_text(body, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("header", "rows"),
    [
        ("t_s,current_a,true_soc_pp", "0,0,80\n"),
        ("t_s,current_a,v_meas,true_soc_pp", "0,0,nan,80\n"),
        ("t_s,current_a,v_meas,true_soc_pp", "60,0,3.7,80\n0,0,3.7,80\n"),
        ("t_s,current_a,v_meas,true_soc_pp", "0,0,3.7,180\n"),
    ],
)
def test_cli_rejects_bad_profile_exit2(tmp_path, header, rows):
    path = _write_bad_profile(tmp_path, header + "\n" + rows)
    assert d13.main(["--profile", str(path), "--out", str(tmp_path / "o")]) == 2


def test_cli_rejects_empty_profile_and_missing_file_exit2(tmp_path):
    empty = _write_bad_profile(tmp_path, "t_s,current_a,v_meas,true_soc_pp\n")
    assert d13.main(["--profile", str(empty)]) == 2
    assert d13.main(["--profile", str(tmp_path / "absent.csv")]) == 2
