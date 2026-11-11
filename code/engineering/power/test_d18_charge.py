"""D18 charge permission chain, CC/CV loop, cutoff triad, and replay contract."""

import importlib.util
import json
import math
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d18_charge", HERE / "d18_charge.py")
assert spec is not None and spec.loader is not None
d18 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d18
spec.loader.exec_module(d18)


@pytest.fixture(scope="module")
def report():
    return d18.build_report()


@pytest.fixture(scope="module")
def run():
    return d18.simulate_charge()


def test_ocv_piecewise_and_inverse():
    assert d18.ocv_v(0.0) == pytest.approx(3.50)
    assert d18.ocv_v(0.80) == pytest.approx(4.06)
    assert d18.ocv_v(1.0) == pytest.approx(4.2374)
    for z in (0.0, 0.3, 0.8, 0.95, 1.0):
        assert d18.soc_from_ocv_v(d18.ocv_v(z)) == pytest.approx(z)
    with pytest.raises(ValueError):
        d18.ocv_v(1.01)
    with pytest.raises(ValueError):
        d18.soc_from_ocv_v(4.30)  # 越出教学 OCV 表，不外推


def test_thermal_contract_matches_d16_numbers():
    # D16 契约：稳态芯温不越限的持续电流，30 °C 8.99 A / 45 °C 7.11 A
    assert d18.thermal_window_current_a(30.0, math.inf) == pytest.approx(8.9893, rel=1e-4)
    assert d18.thermal_window_current_a(45.0, math.inf) == pytest.approx(7.1067, rel=1e-4)
    assert d18.thermal_window_current_a(70.0, math.inf) == 0.0
    # 窗口越短，同一个温度允许的电流越大（热惯性）
    short = d18.thermal_window_current_a(25.0, 10.0)
    long = d18.thermal_window_current_a(25.0, 600.0)
    assert short > long > d18.thermal_window_current_a(25.0, math.inf)


def test_charge_map_bands_and_plating_veto():
    assert d18.charge_map_a(-5.0) == 0.0
    assert d18.charge_map_a(5.0) == pytest.approx(0.4)
    assert d18.charge_map_a(10.0) == pytest.approx(2.0)
    assert d18.charge_map_a(44.9) == pytest.approx(2.0)
    assert d18.charge_map_a(45.0) == pytest.approx(1.0)
    assert d18.charge_map_a(55.0) == 0.0
    # 析锂禁区是独立否决项：地图给 0.4 A，禁区给 0
    assert d18.plating_forbidden(5.0, 0.80) is True
    assert d18.plating_forbidden(5.0, 0.79) is False
    assert d18.plating_forbidden(10.0, 0.85) is False
    cold = d18.charge_permission(0.85, 0.0, 0.0, 5.0)
    assert cold["binding"] == "plating"
    assert cold["limit_a"] == 0.0
    assert cold["components"]["map"] == pytest.approx(0.4)


def test_min_semantics_three_bindings(report):
    probes = {row["case"]: row for row in report["permission_probes"]}
    assert probes["small_charger_1.5a"]["binding"] == "charger"
    assert probes["small_charger_1.5a"]["limit_a"] == pytest.approx(1.5)
    assert probes["map_1c_at_25c"]["binding"] == "map"
    assert probes["map_1c_at_25c"]["limit_a"] == pytest.approx(2.0)
    assert probes["sop_voltage_near_full"]["binding"] == "sop_voltage"
    assert probes["sop_voltage_near_full"]["limit_a"] == pytest.approx(0.643785)
    assert probes["plating_veto_cold"]["binding"] == "plating"
    # 在限项余量为 0，其余项按声明顺序给出正余量
    row = probes["map_1c_at_25c"]
    assert row["margins_a"]["map"] == pytest.approx(0.0)
    assert row["margins_a"]["charger"] == pytest.approx(1.0)
    assert row["margins_a"]["sop_voltage"] == pytest.approx(8.4)


def test_sop_window_tiers_and_thermal_only_when_unmasked(report):
    rows = [r for r in report["sop_windows"] if r["probe"] == "rested_z0.90"]
    finite = [r for r in rows if r["window_s"] != "sustained"]
    voltages = [r["voltage_a"] for r in finite]
    assert voltages == sorted(voltages, reverse=True)  # 窗越长，电压余量越紧
    assert [r["window_s"] for r in finite] == [10.0, 30.0, 60.0, 600.0]
    for row in finite:
        assert row["binding"] == "voltage"
    # 1.3C 帽下热契约永远不是最弱环；只有放宽电流帽的低 SOC + 高温角才露头
    unmasked = [r for r in report["sop_windows"] if r["probe"] == "unmasked_z0.10"]
    assert [r["binding"] for r in unmasked] == ["thermal", "thermal", "thermal"]
    assert [r["limit_a"] for r in unmasked] == pytest.approx([8.9893, 7.1067, 4.4947])
    sustained_low = [r for r in report["sop_windows"] if r["probe"] == "rested_z0.05"]
    assert sustained_low[-1]["window_s"] == "sustained"
    assert sustained_low[-1]["binding"] == "absolute"


def test_default_trajectory_frozen(report):
    t = report["trajectory"]
    assert t["t_end_s"] == pytest.approx(4531.0)
    assert t["t_cc_s"] == pytest.approx(2648.0)
    assert t["t_cv_s"] == pytest.approx(1883.0)
    assert t["cc_time_pct"] == pytest.approx(58.44)
    assert t["cv_time_pct"] == pytest.approx(41.56)
    assert t["z_end"] == pytest.approx(0.949672)
    assert t["ah_total"] == pytest.approx(1.799343)
    assert t["ah_cc"] == pytest.approx(1.471111)
    assert t["ah_cv"] == pytest.approx(0.328232)
    assert t["ah_cv_pct"] == pytest.approx(18.24)  # CV 占 41.6% 时间，只收 18.2% 电量
    assert t["i_end_a"] == pytest.approx(0.095113)
    assert t["v_max_v"] == pytest.approx(4.199992)
    assert t["temp_max_c"] == pytest.approx(26.8903)
    assert t["binding_counts"] == {"map": 2648, "sop_voltage": 1884}
    assert t["plating_frames"] == 0
    assert t["ended_by"] == "taper"


def test_cc_to_cv_switch_is_voltage_component(run):
    modes = run["modes"]
    bindings = run["bindings"]
    frames = run["frames"]
    switch_t = 2648
    assert modes[switch_t - 1] == "cc"
    assert bindings[switch_t - 1] == "map"
    assert modes[switch_t] == "cv"
    assert bindings[switch_t] == "sop_voltage"
    assert frames[switch_t]["v"] == pytest.approx(4.199812)
    assert frames[switch_t]["z"] == pytest.approx(0.785556)
    # 电压环就是 1 s 窗的电压余量：端电压一次也没有越过 4.20 V
    assert max(f["v"] for f in frames) <= d18.V_MAX_V + 1e-9


def test_taper_cutoff_evidence_triad(report):
    cutoff = report["cutoff_evidence"]
    assert cutoff["taper"]["reached"] is True
    assert cutoff["taper"]["t_s"] == pytest.approx(4531.0)
    assert cutoff["taper"]["i_end_a"] < d18.TAPER_A
    assert cutoff["time_limit"]["reached"] is False
    assert cutoff["time_limit"]["limit_s"] == pytest.approx(9000.0)
    assert cutoff["temperature"]["plating_frames"] == 0
    assert cutoff["ended_by"] == "taper"
    assert cutoff["full_charge_anchor"] is True


def test_time_limit_path_is_not_full_charge(report):
    with_map = report["plating_counterexample"]["with_map"]
    cutoff = with_map["cutoff"]
    assert with_map["ended_by"] == "time_limit"
    assert with_map["t_end_s"] == pytest.approx(6000.0)
    assert cutoff["taper"]["reached"] is False
    assert cutoff["full_charge_anchor"] is False
    assert "析锂" in cutoff["note"]
    assert with_map["binding_counts"]["plating"] == 2761
    assert with_map["z_end"] == pytest.approx(0.8)


def test_counterexample_pair_quantified(report):
    cx = report["plating_counterexample"]
    no_map = cx["without_map"]
    assert no_map["plating_frames"] == 1829
    assert no_map["plating_ah"] == pytest.approx(0.298923)
    assert no_map["first_plating_t_s"] == pytest.approx(540.0)
    assert no_map["max_current_in_plating_zone_a"] == pytest.approx(1.841131)
    assert no_map["cutoff"]["full_charge_anchor"] is False
    assert "不证明充电合规" in no_map["cutoff"]["note"]
    delta = cx["delta"]
    assert delta["extra_ah_without_map"] == pytest.approx(0.299344)
    assert delta["plating_share_of_extra_pct"] == pytest.approx(99.8594)
    assert delta["extra_soc_pp"] == pytest.approx(14.9672)
    assert delta["time_ratio"] == pytest.approx(0.3947)


def test_energy_account_consistency(report):
    e = report["energy_account"]
    assert e["ah_in"] == pytest.approx(1.799343)
    assert abs(e["ah_residual"]) < 1e-9
    assert abs(e["wh_ocv_residual"]) < 1e-6  # 逐帧积分 vs OCV 解析积分
    assert abs(e["wh_decomposition_residual"]) < 1e-9  # 端口 = 化学能 + 欧姆 + RC
    assert e["wh_port"] == pytest.approx(7.177663)
    assert e["wh_ocv_analytic"] == pytest.approx(6.931455)
    assert e["loss_pct"] == pytest.approx(3.4302)
    assert e["mean_terminal_v"] == pytest.approx(3.989046)
    assert e["rest"]["gap_mv"] == pytest.approx(2.47781)
    meter = e["meter"]
    assert meter["deviation_pp"] == pytest.approx(1.2586)  # 20 mA 偏置 × 4531 s
    assert meter["loaded_inversion_pp"] == pytest.approx(0.8155)  # 带载电压不能当 OCV


def test_window_effect_60s(report):
    w = report["window_effect"]
    assert w["narrow_1s"]["z_switch"] == pytest.approx(0.785556)
    assert w["wide_60s"]["z_switch"] == pytest.approx(0.769167)
    assert w["delta"]["z_switch_pp"] == pytest.approx(-1.6389)
    assert w["delta"]["v_max_mv"] == pytest.approx(-0.619)
    assert w["delta"]["t_end_s"] == pytest.approx(103.0)
    assert w["wide_60s"]["v_max_v"] < w["narrow_1s"]["v_max_v"]


def test_aging_coupling(report):
    aging = report["aging_coupling"]
    assert aging["af_45_c"] == pytest.approx(2.1399)  # 与 D15 冻结值一致
    assert aging["af_35_c"] == pytest.approx(1.481)
    assert aging["same_charge_25c"]["t_end_s"] == pytest.approx(4531.0)
    assert aging["same_charge_45c"]["t_end_s"] == pytest.approx(7370.0)
    assert aging["same_charge_45c"]["cutoff_ended_by"] == "taper"
    assert aging["exposure_ratio"] == pytest.approx(3.4807)


def test_replay_template_audit_clean(report):
    template = report["replay"]["template"]
    assert template["scenario_id"] == "D18-charge-replay"
    assert template["permission_audit"]["over_permission_frames"] == 0
    assert template["permission_audit"]["over_permission_ah"] == 0.0
    assert template["plating_audit"]["frames"] == 0
    assert template["voltage_consistency"]["max_abs_mv"] < 1e-9
    assert template["soc_consistency"]["deviation_pp"] == pytest.approx(0.0, abs=1e-6)
    assert template["cutoff"]["taper_satisfied"] is True
    assert template["cutoff"]["covered_s"] == pytest.approx(30.0)
    assert template["full_charge_anchor"] is True


def test_replay_counterexample_flags_violations(report):
    audit = report["replay"]["counterexample"]
    assert audit["permission_audit"]["over_permission_frames"] == 2368
    assert audit["permission_audit"]["over_permission_ah"] == pytest.approx(0.599344)
    assert audit["permission_audit"]["worst_over_a"] == pytest.approx(2.2)
    assert audit["permission_audit"]["first_over_t_s"] == pytest.approx(120.0)
    assert audit["plating_audit"]["frames"] == 1828
    assert audit["plating_audit"]["ah"] == pytest.approx(0.298897)
    assert audit["voltage_consistency"]["voltage_over_frames"] == 0
    assert audit["full_charge_anchor"] is False  # taper 成立，但析锂段在先


def test_replay_csv_roundtrip_and_determinism(tmp_path):
    run = d18.simulate_charge()
    rows = d18.build_trace_rows(run)
    path = tmp_path / "trace.csv"
    d18.write_trace_csv(rows, path)
    loaded = d18.load_replay(path)
    assert len(loaded) == len(rows)
    first = d18.audit_replay(loaded, "roundtrip")
    second = d18.audit_replay(loaded, "roundtrip")
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["permission_audit"]["over_permission_frames"] == 0
    assert first["cutoff"]["taper_satisfied"] is True


def test_load_replay_rejects_bad_csv(tmp_path):
    header = ",".join(d18.REPLAY_COLUMNS)
    base = [header] + [f"{k},0.0,3.600,25.0" for k in range(25)]
    good = "\n".join(base) + "\n"
    valid = tmp_path / "good.csv"
    valid.write_text(good, encoding="utf-8")
    assert len(d18.load_replay(valid)) == 25

    bad_cases = {
        "header.csv": "t_s,current_a\n0,0.0\n",
        "nonfinite.csv": "\n".join(base[:-1] + ["24.0,0.0,inf,25.0"]) + "\n",
        "missing_col.csv": "\n".join([header] + ["0,0.0,3.600" for _ in range(25)]) + "\n",
        "time_back.csv": "\n".join(base + ["24.0,0.0,3.600,25.0"]) + "\n",
        "gap.csv": "\n".join(base + ["120.0,0.0,3.600,25.0"]) + "\n",
        "few.csv": "\n".join(base[:6]) + "\n",
        "current_over.csv": "\n".join(base + ["25.0,3.0,3.700,25.0"]) + "\n",
        "temp_over.csv": "\n".join(base + ["25.0,0.0,3.600,-50.0"]) + "\n",
        "volt_over.csv": "\n".join(base + ["25.0,0.0,5.000,25.0"]) + "\n",
        "not_rest.csv": "\n".join([header] + ["0.0,1.0,3.600,25.0"]
                                  + [f"{k},0.0,3.600,25.0" for k in range(1, 25)]) + "\n",
        "unparseable.csv": "\n".join(base + ["25.0,abc,3.600,25.0"]) + "\n",
    }
    for name, content in bad_cases.items():
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        with pytest.raises(ValueError):
            d18.load_replay(path)


def test_net_current_semantics():
    # 充电器能力先扣附件：3.0 A − 0.4 A = 2.6 A 的净电流帽，地图 2.0 A 更紧
    perm = d18.charge_permission(0.05, 0.0, 0.0, 25.0, 1.0, 3.0, True, aux_a=0.4)
    assert perm["components"]["charger"] == pytest.approx(2.6)
    assert perm["limit_a"] == pytest.approx(2.0)
    assert perm["binding"] == "map"
    assert perm["charger_current_a"] == pytest.approx(2.4)  # i_cmd = i_net + aux
    # 小充电器：1.0 A 总电流扣 0.4 A 附件后只剩 0.6 A 净电流，在限项是 charger
    small = d18.charge_permission(0.05, 0.0, 0.0, 25.0, 1.0, 1.0, True, aux_a=0.4)
    assert small["binding"] == "charger"
    assert small["limit_a"] == pytest.approx(0.6)
    assert small["charger_current_a"] == pytest.approx(1.0)
    # 默认 aux = 0：charger 分量就是充电器能力，既有语义不变
    plain = d18.charge_permission(0.05, 0.0, 0.0, 25.0, 1.0, 3.0, True)
    assert plain["components"]["charger"] == pytest.approx(3.0)
    assert plain["charger_current_a"] == pytest.approx(plain["limit_a"])


def test_zero_aux_keeps_two_accounts_equal(run):
    summ = d18.summarize_run(run)
    assert summ["aux_a"] == 0.0
    assert summ["ah_charger"] == summ["ah_total"]
    assert summ["ah_gap"] == 0.0
    assert summ["wh_gap"] == 0.0
    assert summ["v_charger_max_v"] == summ["v_max_v"]


def test_net_current_two_accounts(report):
    net = report["net_current"]
    assert net["aux_load_a"] == pytest.approx(0.4)
    run = net["run"]
    assert run["t_end_s"] == pytest.approx(4531.0)
    assert run["z_end"] == pytest.approx(0.949672)
    assert run["ah_cell"] == pytest.approx(1.799343)
    assert run["ah_charger"] == pytest.approx(2.302788)
    assert run["wh_cell"] == pytest.approx(7.177663)
    assert run["wh_charger"] == pytest.approx(9.216211)
    assert run["ah_gap"] == pytest.approx(0.503444)  # = 0.4 A × 4531 s / 3600
    assert run["ah_gap"] == pytest.approx(0.4 * 4531.0 / 3600.0, abs=1e-6)
    assert run["wh_gap"] == pytest.approx(2.038548)
    assert run["ah_gap_pct_of_charger"] == pytest.approx(21.8624)
    assert run["wh_gap_pct_of_charger"] == pytest.approx(22.1192)
    assert run["ended_by"] == "taper"
    assert run["binding_counts"] == {"map": 2648, "sop_voltage": 1884}


def test_net_current_budget_illusion(report):
    net = report["net_current"]
    budget = net["budget"]
    assert budget["budget_ah"] == pytest.approx(1.799343)
    assert budget["t_hit_s"] == pytest.approx(2700.742)
    assert budget["z_at_hit"] == pytest.approx(0.79963)
    assert budget["ah_cell_at_hit"] == pytest.approx(1.499261)
    assert budget["soc_gap_pp_vs_default"] == pytest.approx(15.0042)
    # 同一个 0.4 A 附件场景在假满充反例里给出相同数字（两个视图同一本账）
    aux = report["false_full"]["aux_load"]
    assert aux["t_budget_hit_s"] == budget["t_hit_s"]
    assert aux["z_at_budget"] == budget["z_at_hit"]
    assert aux["ah_gap"] == net["run"]["ah_gap"]
    assert aux["wh_gap"] == net["run"]["wh_gap"]


def test_false_full_upstream_limit(report):
    up = report["false_full"]["upstream_limit"]
    assert up["condition"]["charger_a"] == pytest.approx(1.0)
    assert up["condition"]["aux_load_a"] == pytest.approx(0.4)
    assert up["condition"]["cable_ohm"] == pytest.approx(0.25)
    assert up["t_end_s"] == pytest.approx(12218.0)
    assert up["z_end"] == pytest.approx(0.808838)
    assert up["z_switch"] == pytest.approx(0.5785)  # 低 SOC 就进 CV
    assert up["t_switch_s"] == pytest.approx(6342.0)
    assert up["ended_by"] == "taper"
    assert up["taper_t_s"] == pytest.approx(12218.0)
    assert up["taper_i_end_a"] == pytest.approx(0.09885)
    # 充电器出口到 4.2 V，电芯端只有 4.075 V：124.7 mV 的线缆压降
    assert up["v_charger_max_v"] == pytest.approx(4.199989)
    assert up["v_cell_max_v"] == pytest.approx(4.075276)
    assert up["v_drop_mv"] == pytest.approx(124.713)
    assert up["soc_meets"] is False
    assert up["full_charge_anchor"] is False
    assert up["soc_gap_pp_vs_default"] == pytest.approx(14.0834)
    assert up["binding_counts"] == {"charger": 6342, "sop_voltage": 5877}


def test_anchor_requires_soc_cross_check():
    run = d18.simulate_charge(
        charger_a=1.0, aux_a=d18.AUX_LOAD_A, cable_ohm=d18.CABLE_OHM, duration_s=15000.0
    )
    cutoff = d18.cutoff_evidence(run)
    assert cutoff["taper"]["reached"] is True
    assert cutoff["temperature"]["plating_frames"] == 0
    assert cutoff["soc"]["meets"] is False
    assert cutoff["full_charge_anchor"] is False
    assert "假满充" in cutoff["note"]
    scan_a = d18.two_account_scan(run, 1.799343)
    scan_b = d18.two_account_scan(run, 1.799343)
    assert scan_a == scan_b


def test_cli_default_export_and_rejections(tmp_path):
    out = tmp_path / "out"
    assert d18.main(["--out", str(out)]) == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["scenario_id"] == "D18-cccv-charge"
    assert report["replay"]["scenario_id"] == "D18-charge-replay"
    for name in ("charge_trace.csv", "counterexample.csv", "replay_template.csv",
                 "net_current.csv"):
        assert (out / name).exists()
    net_lines = (out / "net_current.csv").read_text(encoding="utf-8").splitlines()
    assert net_lines[0] == "t_s,i_charger_a,i_net_a,v_cell_v,v_charger_v,temp_c,z"
    assert len(net_lines) == 4533  # 4532 帧 + 表头
    assert "BmsInputs" in report["boundary"]["firmware_gap"]
    # 拒绝路径：缺文件 / 错表头 / 首拍非静置
    assert d18.main(["--data", str(tmp_path / "absent.csv")]) == 2
    bad = tmp_path / "bad.csv"
    bad.write_text("t_s,current_a\n0,0\n", encoding="utf-8")
    assert d18.main(["--data", str(bad)]) == 2


def test_cli_replay_user_csv(tmp_path):
    run = d18.simulate_charge()
    csv_path = tmp_path / "user.csv"
    d18.write_trace_csv(d18.build_trace_rows(run), csv_path)
    out = tmp_path / "out"
    assert d18.main(["--data", str(csv_path), "--out", str(out)]) == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    user = report["replay"]["user"]
    assert user["scenario_id"] == "D18-charge-replay"
    assert "user.csv" in user["source"]
    assert user["permission_audit"]["over_permission_frames"] == 0
    assert user["full_charge_anchor"] is True
