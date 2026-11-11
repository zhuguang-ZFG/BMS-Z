"""D15 SOH family, synthetic aging, Arrhenius acceleration, capacity holdout."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d15_soh_aging", HERE / "d15_soh_aging.py")
assert spec is not None and spec.loader is not None
d15 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d15
spec.loader.exec_module(d15)


def _write_csv(path: Path, header: list[str], rows: list[list[object]]) -> Path:
    lines = [",".join(header)]
    lines.extend(",".join(str(cell) for cell in row) for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_arrhenius_reference_and_acceleration():
    assert d15.arrhenius_factor(25.0) == pytest.approx(1.0, abs=1e-12)
    assert d15.arrhenius_factor(35.0) == pytest.approx(1.4810, abs=1e-4)
    assert d15.arrhenius_factor(45.0) == pytest.approx(2.1399, abs=1e-4)
    assert d15.arrhenius_factor(45.0) > d15.arrhenius_factor(35.0) > 1.0
    with pytest.raises(ValueError):
        d15.arrhenius_factor(-30.0)
    with pytest.raises(ValueError):
        d15.arrhenius_factor(100.0)


def test_soh_family_same_cell_three_answers():
    state = d15.simulate_aging(d15.generate_history())
    assert state["soh_capacity_pct"] == pytest.approx(77.6804, abs=5e-4)
    assert state["soh_power_pct"] == pytest.approx(72.4306, abs=5e-4)
    assert state["soh_energy_pct"] == pytest.approx(75.9908, abs=5e-4)
    assert state["soh_capacity_pct"] > state["soh_energy_pct"] > state["soh_power_pct"]
    spread = state["soh_capacity_pct"] - state["soh_power_pct"]
    assert spread == pytest.approx(5.2498, abs=1e-3)
    assert state["in_valid_domain"] is True
    # 同一时刻三种定义给出三个答案，单一 SOH 数字因此不可复算
    assert spread > 5.0


def test_calendar_sqrt_and_cycle_linear_shapes():
    short = d15.simulate_aging([{"days": 365.0, "cycles_per_day": 1.0, "temp_c": 25.0}])
    long = d15.simulate_aging([{"days": 1460.0, "cycles_per_day": 1.0, "temp_c": 25.0}])
    assert long["calendar_capacity_loss_pp"] / short["calendar_capacity_loss_pp"] == pytest.approx(2.0, rel=1e-3)
    assert long["cycle_capacity_loss_pp"] / short["cycle_capacity_loss_pp"] == pytest.approx(4.0, rel=1e-3)
    assert long["capacity_loss_pp"] == pytest.approx(
        long["calendar_capacity_loss_pp"] + long["cycle_capacity_loss_pp"], abs=1e-3
    )


def test_arrhenius_equivalent_exposure_replaces_naive_temperature():
    hot = d15.simulate_aging([{"days": 365.0, "cycles_per_day": 1.0, "temp_c": 45.0}])
    equivalent_25c = d15.simulate_aging(
        [{"days": 365.0 * d15.arrhenius_factor(45.0), "cycles_per_day": 1.0, "temp_c": 25.0}]
    )
    assert hot["capacity_loss_pp"] == pytest.approx(equivalent_25c["capacity_loss_pp"], rel=1e-3)
    assert hot["capacity_loss_pp"] > d15.simulate_aging(
        [{"days": 365.0, "cycles_per_day": 1.0, "temp_c": 25.0}]
    )["capacity_loss_pp"]


def test_eol_cycle_count_depends_on_temperature():
    counts = [d15.eol_age_days(temp)["cycles"] for temp in (25.0, 35.0, 45.0)]
    assert counts == pytest.approx([931.68, 629.08, 435.38], rel=1e-3)
    assert counts[0] > counts[1] > counts[2]
    for temp, count in zip((25.0, 35.0, 45.0), counts, strict=True):
        state = d15.simulate_aging(
            [{"days": count, "cycles_per_day": 1.0, "temp_c": temp}]
        )
        assert state["soh_capacity_pct"] == pytest.approx(d15.EOL_SOH_PCT, abs=0.02)


def test_cycle_count_counterexample_systematic_bias():
    c = d15.cycle_count_counterexample()
    assert c["cold_all_25c_soh_pct"] == pytest.approx(83.2435, abs=5e-4)
    assert c["hot_25c_then_45c_soh_pct"] == pytest.approx(76.6906, abs=5e-4)
    assert c["naive_cycle_lookup_soh_pct"] == pytest.approx(c["cold_all_25c_soh_pct"])
    assert c["bias_pp"] == pytest.approx(6.5529, abs=5e-4)
    assert c["bias_from_cycle_pp"] + c["bias_from_calendar_pp"] == pytest.approx(
        c["bias_pp"], abs=1e-3
    )
    assert c["bias_pp"] > 5.0
    assert c["hot_25c_then_45c_soh_pct"] < c["cold_all_25c_soh_pct"]
    assert "循环数本身不是 SOH" in c["conclusion"]


def test_capacity_holdout_frozen_chain():
    ev = d15.evaluate_capacity_segments(d15.generate_capacity_segments())
    assert ev["calibration"]["passed"] is True
    assert ev["calibration"]["max_abs_error_pct"] == pytest.approx(1.4263, abs=5e-4)
    assert ev["validation"]["passed"] is False
    assert ev["validation"]["failure_kept"] is True
    assert ev["validation"]["max_abs_error_pct"] == pytest.approx(9.3484, abs=5e-4)
    assert ev["split"]["leakage"] is False
    assert ev["split"]["holdout_used_for_tuning"] is False
    estimates = [row["q_estimate_ah"] for row in ev["segments"]]
    assert estimates == pytest.approx([1.8170, 1.8205, 1.8257, 1.6317], abs=5e-4)
    assert ev["segments"][-1]["error_pct"] < 0.0, "45 C 留出点必须保留低估方向"


def test_capacity_temperature_offset_is_the_failure_cause():
    blind = d15.evaluate_capacity_segments(
        d15.generate_capacity_segments(temp_coeff_mv_per_k=0.0)
    )
    assert blind["validation"]["passed"] is True
    assert blind["validation"]["max_abs_error_pct"] == pytest.approx(0.9464, abs=5e-4)
    hot = d15.evaluate_capacity_segments(d15.generate_capacity_segments())
    assert hot["validation"]["max_abs_error_pct"] > 3.0


def test_capacity_truth_edit_does_not_move_estimator():
    segments = d15.generate_capacity_segments()
    before = [d15.estimate_capacity_ah(segment)["capacity_ah"] for segment in segments]
    edited = [
        {**segment, "true_soc_start_pp": 65.0, "true_soc_end_pp": 15.0}
        for segment in segments
    ]
    after = [d15.estimate_capacity_ah(segment)["capacity_ah"] for segment in edited]
    assert after == pytest.approx(before)
    original = d15.evaluate_capacity_segments(segments)
    rescored = d15.evaluate_capacity_segments(edited)
    assert rescored["validation"]["max_abs_error_pct"] != pytest.approx(
        original["validation"]["max_abs_error_pct"]
    )


def test_capacity_leakage_counterfactual_is_not_validation():
    ev = d15.evaluate_capacity_segments(d15.generate_capacity_segments())
    assert ev["leakage_counterfactual"]["error_pct"] == pytest.approx(0.9464, abs=5e-4)
    assert "泄漏" in ev["leakage_counterfactual"]["verdict"]
    assert "不是留出验证" in ev["leakage_counterfactual"]["verdict"]


def test_shared_temperature_between_split_is_flagged_as_leakage():
    segments = d15.generate_capacity_segments()
    hot_calibration = {
        **segments[-1],
        "segment_id": "C4_45C",
        "role": "calibration",
    }
    ev = d15.evaluate_capacity_segments([*segments, hot_calibration])
    assert ev["split"]["leakage"] is True
    assert ev["validation"]["passed"] is False
    assert ev["calibration"]["passed"] is False


def test_endpoint_slope_amplification():
    assert d15.endpoint_soc_residual_pp(5.0, 0.8) == pytest.approx(0.625)
    assert d15.endpoint_soc_residual_pp(5.0, 0.08) == pytest.approx(6.25)
    assert d15.endpoint_soc_residual_pp(0.5, 0.08) == pytest.approx(0.625)
    with pytest.raises(ValueError):
        d15.endpoint_soc_residual_pp(5.0, 0.0)


def test_estimate_capacity_rejects_inverted_observations():
    bad = {
        "segment_id": "bad",
        "role": "validation",
        "temp_c": 25.0,
        "soc_start_pp": 90.0,
        "soc_end_pp": 30.0,
        "delta_q_ah": 1.08,
        "v_start_v": 3.70,
        "v_end_v": 3.72,
        "true_soc_start_pp": 90.0,
        "true_soc_end_pp": 30.0,
    }
    with pytest.raises(ValueError, match="dSOC"):
        d15.estimate_capacity_ah(bad)


def test_capacity_segments_csv_roundtrip(tmp_path):
    path = tmp_path / "segments.csv"
    segments = d15.generate_capacity_segments()
    d15.write_capacity_segments(segments, path)
    loaded = d15.load_capacity_segments(path)
    assert [s["segment_id"] for s in loaded] == [s["segment_id"] for s in segments]
    for got, expected in zip(loaded, segments, strict=True):
        assert got["role"] == expected["role"]
        assert got["temp_c"] == pytest.approx(expected["temp_c"])
        assert got["delta_q_ah"] == pytest.approx(expected["delta_q_ah"])
        assert got["v_start_v"] == pytest.approx(expected["v_start_v"])
        assert got["v_end_v"] == pytest.approx(expected["v_end_v"])
    assert d15.evaluate_capacity_segments(loaded)["validation"]["passed"] is False


def test_capacity_segments_reject_bad_files(tmp_path):
    header = ",".join(d15.CAP_SEGMENT_COLUMNS)
    good = [
        "C1,calibration,25,90,30,1.08,3.9205,3.6565,90,30",
        "V1,validation,45,90,30,1.08,3.9145,3.6505,90,30",
    ]
    assert d15.main(["--segments", str(_write_csv(tmp_path / "ok.csv", header.split(","), [good[0].split(","), good[1].split(",")]))]) == 0
    bad_cases = {
        "header.csv": ("segment_id,role\nC1,calibration\n", "表头"),
        "role.csv": (header + "\nC1,train,25,90,30,1.08,3.92,3.65,90,30\n", "role"),
        "finite.csv": (header + "\nC1,calibration,25,90,30,1.08,nan,3.65,90,30\nV1,validation,45,90,30,1.08,3.91,3.65,90,30\n", "非有限"),
        "order.csv": (header + "\nC1,calibration,25,30,90,1.08,3.65,3.92,30,90\nV1,validation,45,90,30,1.08,3.91,3.65,90,30\n", "soc_end"),
        "missing_val.csv": (header + "\nC1,calibration,25,90,30,1.08,3.92,3.65,90,30\n", "validation"),
        "empty.csv": (header + "\n", "为空"),
        "voltage.csv": (header + "\nC1,calibration,25,90,30,1.08,9.0,3.65,90,30\nV1,validation,45,90,30,1.08,3.91,3.65,90,30\n", "[2, 5]"),
        "dup.csv": (header + "\nC1,calibration,25,90,30,1.08,3.92,3.65,90,30\nC1,calibration,25,90,30,1.08,3.92,3.65,90,30\nV1,validation,45,90,30,1.08,3.91,3.65,90,30\n", "重复"),
    }
    for name, (text, _needle) in bad_cases.items():
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        with pytest.raises(ValueError):
            d15.load_capacity_segments(path)


def test_capacity_cli_rejects_bad_segments_exit2(tmp_path):
    header = ",".join(d15.CAP_SEGMENT_COLUMNS)
    path = tmp_path / "bad.csv"
    path.write_text(header + "\nC1,calibration,25,90,30,1.08,3.92,3.65,90,30\n", encoding="utf-8")
    assert d15.main(["--segments", str(path)]) == 2
    assert d15.main(["--segments", str(tmp_path / "absent.csv")]) == 2
    inverted = tmp_path / "inverted.csv"
    inverted.write_text(
        header + "\nC1,calibration,25,90,30,1.08,3.92,3.65,90,30\n"
        "V1,validation,45,90,30,1.08,3.70,3.72,90,30\n",
        encoding="utf-8",
    )
    assert d15.main(["--segments", str(inverted)]) == 2


def test_history_roundtrip_and_rejections(tmp_path):
    path = tmp_path / "history.csv"
    history = [
        {"days": 365.0, "cycles_per_day": 1.0, "temp_c": 25.0},
        {"days": 365.0, "cycles_per_day": 1.0, "temp_c": 45.0},
    ]
    d15.write_history_csv(history, path)
    loaded = d15.load_history(path)
    assert len(loaded) == len(history)
    for got, expected in zip(loaded, history, strict=True):
        assert got["days"] == pytest.approx(expected["days"])
        assert got["cycles_per_day"] == pytest.approx(expected["cycles_per_day"])
        assert got["temp_c"] == pytest.approx(expected["temp_c"])
    assert d15.simulate_aging(loaded)["soh_capacity_pct"] == pytest.approx(
        d15.cycle_count_counterexample()["hot_25c_then_45c_soh_pct"], abs=1e-3
    )

    header = ",".join(d15.HISTORY_COLUMNS)
    bad_cases = {
        "header.csv": "a,b,c\n",
        "gap.csv": header + "\n0,10,1,25\n20,30,1,25\n",
        "negative.csv": header + "\n0,10,-1,25\n",
        "temp.csv": header + "\n0,10,1,100\n",
        "nan.csv": header + "\n0,nan,1,25\n",
        "zero.csv": header + "\n0,0,1,25\n",
        "empty.csv": header + "\n",
    }
    for name, text in bad_cases.items():
        bad_path = tmp_path / name
        bad_path.write_text(text, encoding="utf-8")
        with pytest.raises(ValueError):
            d15.load_history(bad_path)


def test_invalid_aging_history_arguments():
    bad_histories = [
        [],
        [{"days": 0.0, "cycles_per_day": 1.0, "temp_c": 25.0}],
        [{"days": 1.0, "cycles_per_day": -1.0, "temp_c": 25.0}],
        [{"days": 1.0, "cycles_per_day": 21.0, "temp_c": 25.0}],
        [{"days": 1.0, "cycles_per_day": 1.0, "temp_c": 100.0}],
        [{"days": float("nan"), "cycles_per_day": 1.0, "temp_c": 25.0}],
        [{"days": 20001.0, "cycles_per_day": 1.0, "temp_c": 25.0}],
    ]
    for history in bad_histories:
        with pytest.raises(ValueError):
            d15.simulate_aging(history)


def test_cli_writes_report_history_and_estimates(tmp_path):
    out = tmp_path / "out"
    assert d15.main(["--out", str(out)]) == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["scenario_id"] == d15.SCENARIO_ID
    assert report["aging"]["state"]["soh_capacity_pct"] == pytest.approx(77.6804, abs=5e-4)
    assert report["capacity_holdout"]["validation"]["passed"] is False
    assert (out / "history.csv").is_file()
    assert (out / "capacity_segments.csv").is_file()
    estimates = (out / "capacity_estimates.csv").read_text(encoding="utf-8").splitlines()
    assert estimates[0] == "segment_id,role,temp_c,q_true_ah,q_estimate_ah,error_pct"
    assert len(estimates) == 5


def test_cli_segments_replay_matches_builtin(tmp_path):
    segments_path = tmp_path / "segments.csv"
    d15.write_capacity_segments(d15.generate_capacity_segments(), segments_path)
    out = tmp_path / "out"
    assert d15.main(["--segments", str(segments_path), "--out", str(out)]) == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["capacity_holdout"]["validation"]["max_abs_error_pct"] == pytest.approx(
        9.3484, abs=5e-4
    )
    assert report["capacity_holdout"]["split"]["validation_temps_c"] == [45.0]


def test_cli_history_replay_changes_snapshot(tmp_path):
    history_path = tmp_path / "history.csv"
    d15.write_history_csv(
        [
            {"days": 365.0, "cycles_per_day": 1.0, "temp_c": 25.0},
            {"days": 365.0, "cycles_per_day": 1.0, "temp_c": 45.0},
        ],
        history_path,
    )
    out = tmp_path / "out"
    assert d15.main(["--history", str(history_path), "--out", str(out)]) == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["aging"]["state"]["soh_capacity_pct"] == pytest.approx(76.6906, abs=5e-4)
    assert report["aging"]["state"]["equivalent_days_at_25c"] > 1000.0


def test_cli_missing_and_bad_history_exit2(tmp_path):
    assert d15.main(["--history", str(tmp_path / "absent.csv")]) == 2
    bad = tmp_path / "bad.csv"
    bad.write_text("day_start,day_end,cycles_per_day,temp_c\n0,10,1,25\n20,30,1,25\n", encoding="utf-8")
    assert d15.main(["--history", str(bad)]) == 2


def test_report_identity_and_boundaries():
    report = d15.build_report()
    identity = report["identity"].lower()
    assert "synthetic" in identity
    assert "not a cell measurement" in identity
    assert "not hil" in identity
    assert report["arrhenius"]["source"].startswith("教学占位值")
    boundaries = report["boundaries"]
    assert "不能" in boundaries["placeholder_not_estimate"]
    assert "不许可" in boundaries["valid_domain_not_permission"]
    assert "单一 SOH" in boundaries["single_soh_ambiguous"]
    assert "BmsInputs" in boundaries["firmware_inputs"]
    assert "没有时间戳" in boundaries["firmware_inputs"]
    assert "77.68" in report["conclusion"]
    assert "72.43" in report["conclusion"]
    assert "75.99" in report["conclusion"]
