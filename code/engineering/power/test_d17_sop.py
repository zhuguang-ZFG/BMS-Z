"""D17 multi-constraint SOP over anchored windows: frozen numbers and contracts."""

import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d17_sop", HERE / "d17_sop.py")
assert spec is not None and spec.loader is not None
d17 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d17
spec.loader.exec_module(d17)


@pytest.fixture(scope="module")
def report():
    return d17.build_report()


def _op(report, op_id):
    for op in report["operating_points"]:
        if op["id"] == op_id:
            return op
    raise AssertionError(f"没有工作点 {op_id}")


def _tier(op, tier_id):
    for row in op["tiers"]:
        if row["tier_id"] == tier_id:
            return row
    raise AssertionError(f"没有 {tier_id} 档")


def _unc_op(report, op_id):
    for op in report["uncertainty"]["operating_points"]:
        if op["id"] == op_id:
            return op
    raise AssertionError(f"不确定性块里没有工作点 {op_id}")


def _unc_tier(op, tier_id):
    return _tier(op, tier_id)


def test_report_matches_frozen_chain(report):
    assert report["scenario_id"] == d17.SCENARIO_ID
    assert report["scenario_id"] == "D17-sop-window"
    assert "teaching values" in report["identity"]
    assert "not device measurements" in report["identity"]
    thermal = report["thermal_contract"]
    # D16 契约：sqrt((70−30)/(5.5·0.09)) = 8.9893；45 °C 时 7.1067
    assert thermal["sustained_30c_a"] == pytest.approx(8.9893)
    assert thermal["sustained_45c_a"] == pytest.approx(7.1067)
    assert thermal["r_total_k_per_w"] == pytest.approx(5.5)
    assert thermal["r_int_ohm"] == pytest.approx(0.09)
    assert thermal["tau_th_s"] == pytest.approx(858.0)
    # 已知简化：热墙只用 D16 的单一发热内阻 0.09 Ω；把 R1 耗散也计入会降到 7.785 A
    assert thermal["r1_dissipation_included_a"] == pytest.approx(7.785)
    assert len(report["operating_points"]) == 3
    assert report["profile_replay"]["scenario_id"] == "D17-profile-replay"


def test_report_is_strict_json(report):
    # 报告里不允许出现 Infinity/NaN：它要能原样落盘并被别的工具读取
    text = json.dumps(report, ensure_ascii=False, allow_nan=False)
    assert json.loads(text)["scenario_id"] == d17.SCENARIO_ID


def test_high_soc_tiers_bind_thermal_then_voltage(report):
    op = _op(report, "discharge_high_soc")
    assert op["direction"] == "discharge"
    assert op["soc"] == pytest.approx(0.90)
    t10 = _tier(op, "10s")
    assert t10["allowed_a"] == pytest.approx(8.9893)
    assert t10["binding_constraint"] == "thermal"
    assert t10["limits_a"]["voltage"] == pytest.approx(11.4981)
    assert t10["margins_a"]["voltage"] == pytest.approx(2.5088)
    assert t10["soc_end_pp"] == pytest.approx(89.1677)
    assert t10["v_end_v"] == pytest.approx(3.244354)
    assert t10["power_w"] == pytest.approx(29.1646)

    t60 = _tier(op, "60s")
    assert t60["allowed_a"] == pytest.approx(8.9893)
    assert t60["binding_constraint"] == "thermal"
    # 60 s 档电压墙只差 0.34 A 就要反超——最弱环不是永远同一个
    assert t60["margins_a"]["voltage"] == pytest.approx(0.3419)

    t600 = _tier(op, "600s")
    assert t600["allowed_a"] == pytest.approx(6.5067)
    assert t600["binding_constraint"] == "voltage"
    assert t600["margins_a"]["thermal"] == pytest.approx(2.4826)
    assert t600["soc_end_pp"] == pytest.approx(53.8515)
    assert t600["power_w"] == pytest.approx(19.5202)

    sustained = _tier(op, "sustained")
    assert sustained["window_s"] is None
    assert sustained["allowed_a"] == pytest.approx(8.9893)
    assert sustained["binding_constraint"] == "thermal"
    assert sustained["limits_a"]["soc"] is None
    assert sustained["soc_end_pp"] is None


def test_low_soc_six_hundred_seconds_soc_wall(report):
    op = _op(report, "discharge_low_soc")
    assert op["soc"] == pytest.approx(0.15)
    assert _tier(op, "10s")["allowed_a"] == pytest.approx(4.846)
    assert _tier(op, "10s")["binding_constraint"] == "voltage"
    t600 = _tier(op, "600s")
    assert t600["allowed_a"] == pytest.approx(0.90)
    assert t600["binding_constraint"] == "soc"
    assert t600["limits_a"]["soc"] == pytest.approx(0.9)
    assert t600["limits_a"]["voltage"] == pytest.approx(1.7477)
    assert t600["soc_end_pp"] == pytest.approx(10.0)
    assert t600["soc_margin_pp"] == pytest.approx(0.0)
    assert t600["v_end_v"] == pytest.approx(3.30303)
    assert t600["power_w"] == pytest.approx(2.9727)
    # 持续档只承诺稳态压降：3.9084 A 比 600 s 档更松，因为它不算电量账
    sustained = _tier(op, "sustained")
    assert sustained["allowed_a"] == pytest.approx(3.9084)
    assert sustained["binding_constraint"] == "voltage"


def test_charge_tiers_are_voltage_bound_and_power_is_negative(report):
    op = _op(report, "charge_mid_soc")
    assert op["direction"] == "charge"
    expected = {"10s": 4.6526, "30s": 4.2126, "60s": 3.8614, "600s": 2.7361}
    for tier_id, value in expected.items():
        row = _tier(op, tier_id)
        assert row["allowed_a"] == pytest.approx(value)
        assert row["binding_constraint"] == "voltage"
        assert row["signed_a"] == pytest.approx(-value)
        assert row["power_w"] < 0.0  # 充电吸收功率：power = v_end × 有符号电流
        assert row["margins_a"]["thermal"] > 0.0
    sustained = _tier(op, "sustained")
    assert sustained["allowed_a"] == pytest.approx(3.75)
    assert sustained["v_end_v"] == pytest.approx(4.2)
    assert sustained["power_w"] == pytest.approx(-15.75)


def test_every_tier_is_weakest_link_with_nonnegative_margins(report):
    for op in report["operating_points"]:
        assert len(op["tiers"]) == len(d17.TIER_IDS) == 5
        for row in op["tiers"]:
            limits = {k: v for k, v in row["limits_a"].items() if v is not None}
            assert row["allowed_a"] == pytest.approx(min(limits.values()))
            smallest = min(limits, key=lambda name: limits[name])
            assert row["binding_constraint"] == smallest
            assert row["margins_a"][smallest] == pytest.approx(0.0)
            for name, margin in row["margins_a"].items():
                if margin is None:
                    assert row["limits_a"][name] is None
                    continue
                assert margin >= 0.0
                if name != smallest:
                    assert row["limits_a"][name] == pytest.approx(
                        row["allowed_a"] + margin, abs=1e-3
                    )
            # 功率合同：窗口末端端电压 × 有符号允许电流
            assert row["power_w"] == pytest.approx(
                row["v_end_v"] * row["signed_a"], abs=1e-3
            )


def test_weakest_link_moves_when_any_constraint_moves():
    base = {row["tier_id"]: row for row in d17.sop_tiers(0.90, 0.0, "discharge", 30.0)}
    assert base["10s"]["allowed_a"] == pytest.approx(8.9893)

    hot = {r["tier_id"]: r for r in d17.sop_tiers(0.90, 0.0, "discharge", 45.0)}
    assert hot["10s"]["allowed_a"] == pytest.approx(7.1067)
    assert hot["10s"]["binding_constraint"] == "thermal"

    capped = {r["tier_id"]: r for r in d17.sop_tiers(0.90, 0.0, "discharge", 30.0, hardware_a=5.0)}
    assert capped["10s"]["allowed_a"] == pytest.approx(5.0)
    assert capped["10s"]["binding_constraint"] == "hardware"
    assert capped["10s"]["limits_a"]["voltage"] is None  # 帽内电压墙不构成限制

    tight_soc = {
        r["tier_id"]: r
        for r in d17.sop_tiers(0.90, 0.0, "discharge", 30.0, z_min=0.899)
    }
    assert tight_soc["600s"]["allowed_a"] == pytest.approx(0.018)
    assert tight_soc["600s"]["binding_constraint"] == "soc"

    tight_voltage = {
        r["tier_id"]: r
        for r in d17.sop_tiers(0.90, 0.0, "discharge", 30.0, v_min_v=3.6)
    }
    assert tight_voltage["10s"]["allowed_a"] == pytest.approx(5.3381)
    assert tight_voltage["10s"]["binding_constraint"] == "voltage"
    # 四次改动都真的把许可压低且换了主导约束：没有一条是装饰
    assert tight_voltage["10s"]["allowed_a"] != capped["10s"]["allowed_a"]
    assert tight_soc["600s"]["allowed_a"] != base["600s"]["allowed_a"]


def test_snapshot_closed_form_overstates_window_sop(report):
    ce = report["counterexample_snapshot_vs_window"]
    high = ce["high_soc"]
    assert high["snapshot_a"] == pytest.approx(12.4444)
    assert high["window_10s_a"] == pytest.approx(8.9893)
    assert high["binding_10s"] == "thermal"
    assert high["window_600s_a"] == pytest.approx(6.5067)
    assert high["binding_600s"] == "voltage"
    assert high["overstatement_10s_pct"] == pytest.approx(38.4362)
    assert high["overstatement_600s_pct"] == pytest.approx(91.2559)
    split = ce["high_soc_600s_decomposition"]
    assert split["ocv_start_v"] == pytest.approx(4.12)
    assert split["ocv_end_v"] == pytest.approx(3.7808)
    assert split["ocv_drop_v"] == pytest.approx(0.3392)
    assert split["impedance_drop_v"] == pytest.approx(0.7808)
    assert split["headroom_v"] == pytest.approx(1.12)
    assert split["ocv_drop_v"] + split["impedance_drop_v"] == pytest.approx(1.12, abs=1e-3)
    assert split["rc_share_of_r0_at_60s_pct"] == pytest.approx(24.5468)
    low = ce["low_soc"]
    assert low["snapshot_a"] == pytest.approx(5.2112)
    assert low["window_600s_a"] == pytest.approx(0.90)
    assert low["binding_600s"] == "soc"
    assert low["overstatement_600s_pct"] == pytest.approx(479.0259)
    # 反例方向必须成立：单快照严格高于每个窗口档
    op = _op(report, "discharge_high_soc")
    for row in op["tiers"]:
        if row["window_s"] is not None:
            assert row["allowed_a"] < high["snapshot_a"]


def test_temperature_derating_only_moves_thermal_bound_tiers(report):
    derate = report["temperature_derating"]
    assert derate["ambient_30_c"]["sustained_a"] == pytest.approx(8.9893)
    assert derate["ambient_45_c"]["sustained_a"] == pytest.approx(7.1067)
    assert derate["drop_pct"]["thermal_bound_tiers"] == pytest.approx(20.94)
    assert derate["drop_pct"]["600s"] == pytest.approx(0.0)
    tiers_30 = derate["ambient_30_c"]["tiers_a"]
    tiers_45 = derate["ambient_45_c"]["tiers_a"]
    assert tiers_30["10s"] == pytest.approx(8.9893)
    assert tiers_45["10s"] == pytest.approx(7.1067)
    assert tiers_30["600s"] == pytest.approx(tiers_45["600s"])
    assert derate["binding_45_c"]["10s"] == "thermal"
    assert derate["binding_45_c"]["600s"] == "voltage"


def test_window_longer_never_looser(report):
    for op in report["operating_points"]:
        finite = [row for row in op["tiers"] if row["window_s"] is not None]
        allowed = [row["allowed_a"] for row in finite]
        assert allowed == sorted(allowed, reverse=True), (op["id"], allowed)
        sustained = _tier(op, "sustained")
        assert sustained["allowed_a"] <= _tier(op, "10s")["allowed_a"] + 1e-9


def test_thermal_contract_rejects_ambient_at_or_above_core_limit():
    assert d17.thermal_sustained_a(30.0) == pytest.approx(8.9893, abs=1e-4)
    assert d17.thermal_sustained_a(45.0) == pytest.approx(7.1067, abs=1e-4)
    with pytest.raises(ValueError, match="热契约无正许可"):
        d17.thermal_sustained_a(70.0)
    with pytest.raises(ValueError, match="热契约无正许可"):
        d17.thermal_sustained_a(80.0)


def test_zero_permission_state_is_reported_not_clamped():
    # z=0：OCV 已低于 v_min，任何正放电电流都不允许；返回 0.0，不返回 inf 或负值
    rows = d17.sop_tiers(0.0, 0.0, "discharge", 30.0)
    for row in rows:
        assert row["allowed_a"] == pytest.approx(0.0)
        assert row["power_w"] == pytest.approx(0.0)
    assert d17.ocv_v(0.0) == pytest.approx(2.968970, abs=1e-6)
    with pytest.raises(ValueError, match="SOC 越界"):
        d17.ocv_v(1.01)
    with pytest.raises(ValueError, match="未知方向"):
        d17.snapshot_current_a(0.5, 0.0, "idle")


def test_profile_envelope_flags_overload_pulse(report):
    replay = report["profile_replay"]
    assert replay["frames"] == 181
    assert replay["duration_s"] == pytest.approx(1800.0)
    assert replay["discharge_ah"] == pytest.approx(2.0)
    assert replay["peak_discharge_a"] == pytest.approx(12.0)
    assert replay["soc_end_pp"] == pytest.approx(23.3333)
    env = replay["envelope"]
    assert env["checked_frames"] == 90
    assert env["over_limit_frames"] == 30
    assert env["first_over_limit_t_s"] == pytest.approx(1200.0)
    assert env["worst_t_s"] == pytest.approx(1490.0)
    assert env["max_exceedance_a"] == pytest.approx(9.932)
    assert env["max_exceedance_frac"] == pytest.approx(4.802708)
    assert env["window_violation_frames"] == 30
    assert env["binding_counts"] == {"voltage": 87, "soc": 0, "thermal": 3, "hardware": 0}
    assert env["min_allowed_a"] == pytest.approx(2.068)


def test_uncertainty_scale_zero_is_nominal_and_monotone(report):
    params = report["uncertainty"]["parameters"]
    assert params["r0_pct"] == pytest.approx(20.0)
    assert params["r1_pct"] == pytest.approx(30.0)
    assert params["q_pct"] == pytest.approx(5.0)
    assert params["r_total_pct"] == pytest.approx(15.0)
    assert params["ocv_mv"] == pytest.approx(10.0)
    assert params["scale"] == pytest.approx(1.0)
    for op in report["uncertainty"]["operating_points"]:
        tiers = {row["tier_id"]: row for row in op["tiers"]}
        assert set(tiers) == set(d17.TIER_IDS)
        for row in op["tiers"]:
            # 收缩量非负，且与表里的两侧数字逐位一致
            assert row["shrink_a"] >= 0.0
            assert row["uncertain_a"] == pytest.approx(
                row["nominal_a"] - row["shrink_a"], abs=1e-9
            )
        # 不确定度倍率单调：scale 越大，每档 uncertain_a 越小或不变
        # scale=0 与 nominal 逐位相等，作为单调链的起点
        previous = {tid: row["nominal_a"] for tid, row in tiers.items()}
        for scale in (0.0, 0.5, 1.0, 2.0):
            scaled = d17.uncertainty_report(
                op["soc"], 0.0, op["direction"], op["ambient_c"], scale=scale
            )["tiers"]
            current = {row["tier_id"]: row["uncertain_a"] for row in scaled}
            for tid, value in current.items():
                assert value <= previous[tid] + 1e-9, (op["id"], tid, scale)
            previous = current
        # scale=0：角点回到名义值，收缩必须恰好为 0（不把噪声当收缩）
        zero = d17.uncertainty_report(
            op["soc"], 0.0, op["direction"], op["ambient_c"], scale=0.0
        )["tiers"]
        for row in zero:
            assert row["shrink_a"] == 0.0
            assert row["uncertain_a"] == row["nominal_a"]
    with pytest.raises(ValueError, match="不确定度倍率"):
        d17.uncertainty_report(0.90, 0.0, "discharge", 30.0, scale=-0.1)


def test_uncertainty_each_wall_uses_its_own_worst_corner(report):
    high = _unc_op(report, "discharge_high_soc")
    ten = _unc_tier(high, "10s")
    # 热墙只看 R_total 高角点：8.9893 / sqrt(1.15) = 8.3826
    assert ten["dominant_parameter"] == "r_total"
    assert ten["uncertain_binding"] == "thermal"
    assert ten["uncertain_a"] == pytest.approx(8.3826)
    assert ten["per_parameter_shrink_a"]["r_total"] == pytest.approx(0.6067)
    assert ten["per_parameter_shrink_a"]["r0"] == pytest.approx(0.0)
    # 60 s 档：名义在限是热，角点后电压墙反超——不确定性会换掉最弱环
    sixty = _unc_tier(high, "60s")
    assert sixty["nominal_binding"] == "thermal"
    assert sixty["uncertain_binding"] == "voltage"
    assert sixty["dominant_parameter"] == "r0"
    assert sixty["uncertain_a"] == pytest.approx(7.8658)
    assert sixty["joint_extra_a"] == pytest.approx(0.2403)
    # SOC 墙只看 Q 低角点：0.9 × (1 − 5%) = 0.855
    low = _unc_tier(_unc_op(report, "discharge_low_soc"), "600s")
    assert low["dominant_parameter"] == "q"
    assert low["uncertain_binding"] == "soc"
    assert low["uncertain_a"] == pytest.approx(0.855)
    assert low["per_parameter_shrink_a"]["q"] == pytest.approx(0.045)
    assert low["per_parameter_shrink_a"]["r_total"] == pytest.approx(0.0)
    # 充电的 OCV 高角点同样收紧电压墙：主导仍是 R0
    charge = _unc_tier(_unc_op(report, "charge_mid_soc"), "600s")
    assert charge["dominant_parameter"] == "r0"
    assert charge["uncertain_binding"] == "voltage"
    assert charge["uncertain_a"] == pytest.approx(2.2981)
    assert charge["shrink_pct_of_nominal"] == pytest.approx(16.0082)


def test_endpoint_only_misses_in_window_dip(report):
    replay = report["profile_replay"]
    endpoint = replay["endpoint_only"]
    assert endpoint["trajectory_violation_frames"] == 35
    assert endpoint["endpoint_violation_frames"] == 30
    assert endpoint["missed_frames"] == 5
    assert endpoint["first_missed_t_s"] == pytest.approx(1450.0)
    assert endpoint["missed_t_s"] == pytest.approx(
        [1450.0, 1460.0, 1470.0, 1480.0, 1490.0]
    )
    rows = d17.audit_profile(d17.generate_profile())["rows"]
    by_t = {row["t_s"]: row for row in rows}
    last = by_t[1490.0]
    # 反例帧：整窗最小值仍在 12 A 脉冲末尾，但窗末已静置恢复
    assert last["window_violation"] is True
    assert last["trajectory_min_v"] == pytest.approx(2.097118)
    assert last["endpoint_v"] == pytest.approx(3.418301)
    assert last["endpoint_only_violation"] is False
    assert last["endpoint_missed"] is True
    # 恒流窗口端点就是最坏点：两口径一致，反例只能来自窗内换流
    mid = by_t[1300.0]
    assert mid["trajectory_min_v"] == pytest.approx(mid["endpoint_v"])
    assert mid["endpoint_only_violation"] is True
    assert mid["endpoint_missed"] is False


def test_profile_audit_benign_and_deterministic(tmp_path):
    frames = [{"t_s": float(t), "current_a": 2.0 if t < 600 else 0.0} for t in range(0, 1200, 10)]
    result = d17.audit_profile(frames)
    assert result["envelope"]["checked_frames"] == 60
    assert result["envelope"]["over_limit_frames"] == 0
    assert result["envelope"]["window_violation_frames"] == 0
    assert result["discharge_ah"] == pytest.approx(2.0 * 600.0 / 3600.0)
    # 同输入同输出；写盘再读回也不改变任何一拍
    again = d17.audit_profile([dict(f) for f in frames])
    assert again == result
    path = tmp_path / "profile.csv"
    d17.write_profile_csv(frames, path)
    loaded = d17.load_profile(path)
    assert loaded == frames
    assert d17.audit_profile(loaded) == result


def test_cli_default_export_and_artifacts(tmp_path, capsys):
    out = tmp_path / "out"
    rc = d17.main(["--out", str(out)])
    assert rc == 0
    capsys.readouterr()
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["scenario_id"] == "D17-sop-window"
    assert report["profile_replay"]["envelope"]["over_limit_frames"] == 30
    # 新增两个口径必须随默认导出一起落盘
    assert report["profile_replay"]["endpoint_only"]["missed_frames"] == 5
    assert report["uncertainty"]["operating_points"][0]["tiers"][0][
        "dominant_parameter"
    ] == "r_total"
    assert (out / "sop_tiers.csv").exists()
    assert (out / "profile.csv").exists()
    assert (out / "profile_audit.csv").exists()
    lines = (out / "sop_tiers.csv").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1 + 3 * 5
    audit_lines = (out / "profile_audit.csv").read_text(encoding="utf-8").strip().splitlines()
    assert len(audit_lines) == 1 + 181
    header = audit_lines[0].split(",")
    for name in (
        "trajectory_min_v",
        "trajectory_max_v",
        "endpoint_v",
        "endpoint_only_violation",
        "endpoint_missed",
    ):
        assert name in header
    with (out / "profile_audit.csv").open(newline="", encoding="utf-8") as fh:
        audit_rows = {float(row["t_s"]): row for row in csv.DictReader(fh)}
    missed = audit_rows[1490.0]
    assert missed["endpoint_missed"] == "True"
    assert missed["endpoint_only_violation"] == "False"


def test_cli_profile_roundtrip_matches_default(tmp_path, capsys):
    frames = d17.generate_profile()
    path = tmp_path / "user_profile.csv"
    d17.write_profile_csv(frames, path)
    out = tmp_path / "replay"
    rc = d17.main(["--profile", str(path), "--out", str(out)])
    assert rc == 0
    capsys.readouterr()
    loaded = json.loads((out / "report.json").read_text(encoding="utf-8"))
    default = d17.build_report()["profile_replay"]
    assert loaded["profile_replay"] == default


def test_cli_rejections_exit_2(tmp_path, capsys):
    good = ["t_s,current_a"] + [f"{t},0" for t in range(0, 110, 10)]
    cases = {
        "bad_header": ("time,amps\n0,0\n", "缺列"),
        "missing_col": ("t_s\n" + "\n".join(str(t) for t in range(0, 110, 10)), "缺列"),
        "nonfinite": ("t_s,current_a\n0,0\n10,inf\n20,0\n30,0\n40,0\n50,0\n60,0\n70,0\n80,0\n90,0\n100,0\n", "非有限"),
        "backwards": ("t_s,current_a\n0,0\n10,0\n5,0\n20,0\n30,0\n40,0\n50,0\n60,0\n70,0\n80,0\n90,0\n", "未严格递增"),
        "sparse": ("t_s,current_a\n0,0\n10,0\n", "样本不足"),
        "overdraw": ("t_s,current_a\n0,0\n" + "\n".join(f"{t},100" for t in range(100, 1100, 100)) + "\n", "SOC 越界"),
    }
    for name, (text, needle) in cases.items():
        path = tmp_path / f"{name}.csv"
        path.write_text(text, encoding="utf-8")
        rc = d17.main(["--profile", str(path), "--out", str(tmp_path / f"o_{name}")])
        assert rc == 2, name
        err = capsys.readouterr().err
        assert "拒绝" in err
        assert needle in err, (name, err)
    assert d17.main(["--profile", str(tmp_path / "absent.csv")]) == 2
    capsys.readouterr()
    ok = tmp_path / "ok.csv"
    ok.write_text("\n".join(good) + "\n", encoding="utf-8")
    assert d17.main(["--profile", str(ok), "--out", str(tmp_path / "ok_out")]) == 0
    capsys.readouterr()
