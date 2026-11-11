"""D14 observability ranking, confident-wrong counterexample, truth-free diagnosis."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d14_observability", HERE / "d14_observability.py"
)
assert spec is not None and spec.loader is not None
d14 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d14
spec.loader.exec_module(d14)


def test_ocv_is_continuous_at_knee_and_slopes_scale():
    assert d14.ocv_mv(60.0) == pytest.approx(3680.0)
    assert d14.ocv_mv(40.0) == pytest.approx(3664.0)
    assert d14.ocv_slope_mv_per_pp(70.0) == pytest.approx(8.0)
    assert d14.ocv_slope_mv_per_pp(40.0) == pytest.approx(0.8)


def test_deterministic_noise_is_repeatable():
    a = d14.deterministic_noise(8, 5.0)
    b = d14.deterministic_noise(8, 5.0)
    assert a == b
    assert len(a) == 8
    assert d14.deterministic_noise(4, 0.0) == [0.0, 0.0, 0.0, 0.0]


def test_single_sample_crlb_slope_ranking():
    steep = d14.fisher_information([70.0])
    flat = d14.fisher_information([40.0])
    assert steep["scalar_crlb_pp_b_known"] == pytest.approx(0.625)
    assert flat["scalar_crlb_pp_b_known"] == pytest.approx(6.25)
    assert steep["fim"][0][0] / flat["fim"][0][0] == pytest.approx(100.0)
    assert flat["scalar_crlb_pp_b_known"] / steep["scalar_crlb_pp_b_known"] == pytest.approx(10.0)
    assert steep["rank"] == 1 and flat["rank"] == 1
    assert steep["crlb_z_pp"] is None and flat["crlb_b_mv"] is None


def test_single_slope_rest_never_identifies_bias():
    profiles = d14.fim_profiles()
    for name in ("rest_flat", "rest_steep", "pulse_flat"):
        profile = profiles[name]
        assert profile["rank"] == 1
        assert profile["bias_identifiable"] is False
        assert profile["crlb_z_pp"] is None
        assert profile["crlb_b_mv"] is None
        assert profile["det"] == pytest.approx(0.0, abs=1e-9)
    # 斜率 10 倍差 → 同一拍数下 CRLB 10 倍差（信息量 100 倍）
    assert profiles["rest_flat"]["scalar_crlb_pp_b_known"] == pytest.approx(0.8068715)
    assert profiles["rest_steep"]["scalar_crlb_pp_b_known"] == pytest.approx(0.08068715)
    assert (
        profiles["rest_flat"]["scalar_crlb_pp_b_known"]
        / profiles["rest_steep"]["scalar_crlb_pp_b_known"]
    ) == pytest.approx(10.0)


def test_knee_crossing_makes_soc_and_bias_rank_two():
    profile = d14.fim_profiles()["hppc_knee"]
    assert profile["rank"] == 2
    assert profile["soc_identifiable"] is True
    assert profile["bias_identifiable"] is True
    assert profile["det"] == pytest.approx(16.5888, abs=1e-6)
    assert profile["crlb_z_pp"] == pytest.approx(0.268957, abs=1e-5)
    assert profile["crlb_b_mv"] == pytest.approx(1.761207, abs=1e-5)
    assert profile["condition_number"] == pytest.approx(165.134, abs=1e-3)


def test_flat_counterexample_is_confidently_wrong():
    pair = d14.counterexample_pair()
    flat = pair["flat"]
    assert flat["final_error_pp"] == pytest.approx(10.5451, abs=0.05)
    assert flat["final_p_std_pp"] < 1.0, "协方差必须收缩"
    assert flat["overconfidence_ratio"] > 10.0, "误差必须远大于滤波自报标准差"
    assert flat["confident_wrong"] is True
    assert flat["charge_balance_mismatch"] is True
    assert flat["sum_correction_pp"] == pytest.approx(10.5451, abs=0.05)
    # NIS 可以接近 1：新息自洽不能证明 z 对
    assert flat["nis_mean"] == pytest.approx(1.01, abs=0.1)


def test_same_algorithm_recovers_on_steep_slope_but_bias_remains():
    pair = d14.counterexample_pair()
    steep = pair["steep"]
    assert steep["final_error_pp"] == pytest.approx(1.0815, abs=0.05)
    assert steep["final_p_std_pp"] < 0.1
    assert steep["confident_wrong"] is False, "1.08 pp 低于 2 pp 的自信错误门槛"
    assert steep["charge_balance_mismatch"] is False
    assert pair["recovery_ratio"] == pytest.approx(9.7504, abs=0.1)
    assert pair["residual_bias_pp_steep"] == pytest.approx(steep["final_error_pp"])
    assert pair["same_algorithm"].startswith("z-only")


def test_flat_dual_model_is_not_separable():
    multi = d14.dual_model_comparison()["flat_single_slope"]
    assert multi["separable"] is False
    assert multi["z_only"]["final_error_pp"] == pytest.approx(10.5451, abs=0.05)
    assert multi["bias_model"]["final_z_error_pp"] == pytest.approx(4.1798, abs=0.1)
    assert multi["bias_model"]["final_bias_error_mv"] == pytest.approx(-2.7752, abs=0.1)
    assert multi["bias_model"]["final_p_b_std_mv"] > 2.0, "偏置方向仍未收敛"
    assert multi["z_estimate_gap_pp"] == pytest.approx(6.3653, abs=0.1)


def test_knee_dual_model_recovers_and_heldout_is_better():
    multi = d14.dual_model_comparison()["multipoint_knee"]
    assert multi["separable"] is True
    assert multi["bias_model"]["final_z_error_pp"] == pytest.approx(0.3203, abs=0.05)
    assert multi["bias_model"]["final_bias_estimate_mv"] == pytest.approx(7.013, abs=0.05)
    assert multi["bias_model"]["final_bias_error_mv"] == pytest.approx(-0.987, abs=0.05)
    heldout = multi["heldout_final_rest"]
    assert heldout["bias_model"]["rss_mv2"] < heldout["z_only"]["rss_mv2"]
    assert heldout["bias_model"]["rss_mv2"] == pytest.approx(278.5534, abs=1.0)
    assert heldout["z_only"]["rss_mv2"] == pytest.approx(669.1671, abs=1.0)


def test_bias_direction_is_consistent_across_windows():
    direction = d14.dual_model_comparison()["bias_direction"]
    assert direction["same_sign"] is True
    assert direction["flat_estimate_mv"] == pytest.approx(5.2248, abs=0.1)
    assert direction["knee_estimate_mv"] == pytest.approx(7.013, abs=0.05)
    assert direction["flat_estimate_mv"] > 0.0
    assert direction["knee_estimate_mv"] > 0.0


def test_report_identity_and_frozen_chain():
    report = d14.build_report()
    assert report["scenario_id"] == d14.SCENARIO_ID
    assert "synthetic" in report["identity"]
    assert "not device measurement" in report["identity"]
    assert "BmsInputs" in report["identity"]
    assert report["fisher"]["single_sample"]["steep"]["scalar_crlb_pp_b_known"] == pytest.approx(0.625)
    assert report["fisher"]["single_sample"]["flat"]["scalar_crlb_pp_b_known"] == pytest.approx(6.25)
    assert report["counterexample"]["recovery_ratio"] == pytest.approx(9.7504, abs=0.1)
    assert report["truth_free_diagnostics"]["dual_model"]["multipoint_knee"]["separable"] is True


def test_profile_csv_roundtrip_and_truth_independence(tmp_path):
    frames = d14.generate_multipoint_frames()
    path = tmp_path / "profile.csv"
    d14.write_profile_csv(frames, path)
    loaded = d14.load_profile(path)
    assert len(loaded) == len(frames)
    a = d14.replay_profile(loaded, z0_pp=80.0)
    b = d14.replay_profile(d14.load_profile(path), z0_pp=80.0)
    assert [row["z_hat_pp"] for row in a["trace"]] == [row["z_hat_pp"] for row in b["trace"]]

    # 只改真值列：估计轨迹必须逐点不动（评分口径与估计口径分离）
    lines = path.read_text(encoding="utf-8").splitlines()
    edited = [lines[0]]
    for line in lines[1:]:
        parts = line.split(",")
        parts[3] = str(float(parts[3]) + 1.0)
        edited.append(",".join(parts))
    path.write_text("\n".join(edited) + "\n", encoding="utf-8")
    c = d14.replay_profile(d14.load_profile(path), z0_pp=80.0)
    assert [row["z_hat_pp"] for row in a["trace"]] == [row["z_hat_pp"] for row in c["trace"]]
    assert c["final_true_pp"] == pytest.approx(a["final_true_pp"] + 1.0)
    assert c["final_error_pp"] != pytest.approx(a["final_error_pp"])


def test_load_profile_rejects_bad_input(tmp_path):
    cases = [
        ("hdr.csv", "t_s,current_a,true_soc_pp,v_meas_mv\n0,0,50,3700\n"),
        ("nan.csv", "t_s,current_a,v_meas_mv,true_soc_pp\n0,0,nan,50\n"),
        ("time.csv", "t_s,current_a,v_meas_mv,true_soc_pp\n0,0,3700,50\n0,0,3700,50\n"),
        ("soc.csv", "t_s,current_a,v_meas_mv,true_soc_pp\n0,0,3700,101\n"),
        ("emptyobs.csv", "t_s,current_a,v_meas_mv,true_soc_pp\n0,0,,50\n"),
        ("short.csv", "t_s,current_a,v_meas_mv,true_soc_pp\n0,0,3700\n"),
    ]
    for name, text in cases:
        p = tmp_path / name
        p.write_text(text, encoding="utf-8")
        with pytest.raises(ValueError):
            d14.load_profile(p)


def test_cli_writes_report_and_artifacts(tmp_path):
    out = tmp_path / "out"
    assert d14.main(["--out", str(out)]) == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["scenario_id"] == d14.SCENARIO_ID
    assert report["counterexample"]["flat"]["final_error_pp"] == pytest.approx(10.5451, abs=0.05)
    for name in (
        "fisher_profiles.csv",
        "counterexample_flat_trace.csv",
        "counterexample_steep_trace.csv",
        "multipoint_profile.csv",
        "dual_model_bias_trace.csv",
    ):
        assert (out / name).is_file()


def test_cli_profile_replay(tmp_path):
    frames = d14.generate_rest_frames(40.0, d14.REST_FRAMES)
    path = tmp_path / "profile.csv"
    d14.write_profile_csv(frames, path)
    out = tmp_path / "out"
    assert d14.main(["--profile", str(path), "--z0", "40", "--out", str(out)]) == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    replay = report["profile_replay"]
    assert replay["scenario_id"] == d14.PROFILE_SCENARIO_ID
    assert replay["frames"] == d14.REST_FRAMES
    assert replay["final_error_pp"] == pytest.approx(10.5451, abs=0.05)
    assert replay["final_p_std_pp"] == pytest.approx(0.796579, abs=1e-5)
    assert replay["confident_wrong"] is True
    assert (out / "profile_replay_trace.csv").is_file()


def test_cli_rejects_bad_inputs(tmp_path):
    assert d14.main(["--profile", str(tmp_path / "absent.csv"), "--out", str(tmp_path / "o")]) == 2
    bad = tmp_path / "bad.csv"
    bad.write_text("t_s,current_a,v_meas_mv,true_soc_pp\n0,0,3700,101\n", encoding="utf-8")
    assert d14.main(["--profile", str(bad), "--out", str(tmp_path / "o")]) == 2
    assert d14.main(["--z0", "150"]) == 2
    assert d14.main(["--z0", "50"]) == 2
