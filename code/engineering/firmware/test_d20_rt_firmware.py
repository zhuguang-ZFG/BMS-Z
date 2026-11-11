"""D20 real-time firmware lanes, snapshot epoch, watchdog, and parameter A/B slots."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d20_rt_firmware", HERE / "d20_rt_firmware.py")
assert spec is not None and spec.loader is not None
d20 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d20
spec.loader.exec_module(d20)


@pytest.fixture(scope="module")
def report():
    return d20.build_report()


@pytest.fixture(scope="module")
def trace_rows():
    return d20.simulate_schedule()


def _write_trace(path: Path, rows: list[list[object]]) -> Path:
    header = ",".join(d20.TRACE_COLUMNS)
    lines = [header]
    for row in rows:
        lines.append(",".join(str(value) for value in row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _row_int(rows: list[list[object]], index: int, column: int) -> int:
    value = rows[index][column]
    assert isinstance(value, int)
    return value


def _raw_trace() -> list[list[object]]:
    return [
        [
            row["job"],
            row["lane"],
            row["release_us"],
            row["start_us"],
            row["finish_us"],
            row["exec_us"],
        ]
        for row in d20.simulate_schedule()
    ]


def test_schedule_is_deterministic_and_injection_is_pinned(trace_rows):
    assert trace_rows == d20.simulate_schedule()
    tick37 = next(
        row for row in trace_rows if row["lane"] == "fast" and row["index"] == d20.OVERRUN_TICK
    )
    assert tick37["release_us"] == 380_000
    assert tick37["exec_us"] == 14_000
    assert tick37["response_us"] == 16_000


def test_lane_wcet_and_jitter_frozen(report):
    fast = report["lanes"]["fast"]
    assert fast["jobs"] == 60
    assert fast["wcet_us"] == 14_000
    assert fast["wcet_nominal_us"] == 5_230
    assert fast["max_start_jitter_us"] == 6_130
    assert fast["max_nominal_start_jitter_us"] == 1_970
    assert fast["max_response_us"] == 16_000
    assert fast["max_nominal_response_us"] == 7_735
    assert fast["deadline_miss_ticks"] == [37, 38]
    assert fast["load"] == pytest.approx(0.5145)
    slow = report["lanes"]["slow"]
    assert slow["wcet_us"] == 13_100
    assert slow["max_start_jitter_us"] == 7_735
    assert slow["max_response_us"] == 38_375
    assert slow["deadline_miss_ticks"] == []
    isr = report["lanes"]["isr"]
    assert isr["wcet_us"] == 160
    assert isr["max_start_jitter_us"] == 0
    assert isr["max_response_us"] == 160
    table = {row["lane"]: row for row in report["wcet_jitter"]}
    assert table["fast"]["headroom_us"] == 4_770
    assert table["slow"]["headroom_us"] == 26_900
    assert table["isr"]["headroom_us"] == 40


def test_rta_bounds_frozen(report):
    nominal = report["rta"]["nominal"]
    assert nominal["fast_response_us"] == 6_350
    assert nominal["slow_response_us"] == 47_330
    assert nominal["slow_bounded"] is True
    assert nominal["fast_deadline_ok"] is True
    overrun = report["rta"]["overrun_probe"]
    assert overrun["fast_response_us"] == 16_720
    assert overrun["fast_deadline_ok"] is False
    assert overrun["slow_response_us"] is None
    assert overrun["slow_bounded"] is False


def test_watchdog_chain_frozen(report):
    watchdog = report["watchdog"]
    assert watchdog["timeout_us"] == 35_000
    assert watchdog["feeds"] == 58
    assert watchdog["withheld_count"] == 2
    withheld = watchdog["withheld"]
    assert [item["tick"] for item in withheld] == [37, 38]
    assert [item["t_us"] for item in withheld] == [396_000, 401_970]
    assert [item["response_us"] for item in withheld] == [16_000, 11_970]
    assert all(item["snapshot_complete"] for item in withheld)
    assert watchdog["max_gap_us"] == 31_985
    assert watchdog["margin_us"] == 3_015
    assert watchdog["reset"] is False
    assert watchdog["final_state"] == "RUN"
    assert [item["stage"] for item in watchdog["transitions"]] == ["boot", "deadline", "recovery"]
    assert watchdog["transitions"][1]["t_us"] == 390_000
    assert watchdog["transitions"][2]["t_us"] == 425_750
    timeout = report["timeout"]
    assert timeout["deadline_miss_ticks"] == [37, 38]
    assert timeout["withheld_feeds"] == 2
    assert timeout["late_complete_snapshots"] == 2
    assert timeout["max_feed_gap_us"] == 31_985
    assert timeout["watchdog_margin_us"] == 3_015
    assert timeout["reset"] is False
    assert timeout["recovery_t_us"] == 425_750
    assert [(item["stage"], item["tick"]) for item in timeout["chain"]] == [
        ("wcet", 37),
        ("deadline", 37),
        ("watchdog", 37),
        ("deadline", 38),
        ("watchdog", 38),
        ("recovery", None),
    ]


def test_watchdog_reset_probe(report):
    probe = report["watchdog"]["reset_probe"]
    assert probe["overrun_ticks"] == [37, 38]
    assert probe["max_gap_us"] == 53_365
    assert probe["reset_at_us"] == 410_750
    assert probe["final_state"] == "RESET"
    assert probe["withheld_count"] == 4


def test_watchdog_feed_rule_requires_complete_snapshot(trace_rows):
    assert d20.snapshot_round_complete(trace_rows, 37) is True
    without_five = [
        row
        for row in trace_rows
        if not (row["lane"] == "isr" and row["index"] == 5)
    ]
    assert d20.snapshot_round_complete(without_five, 0) is False
    audit = d20.watchdog_audit(trace_rows)
    withheld_ticks = [item["tick"] for item in audit["withheld"]]
    assert withheld_ticks == [37, 38]
    assert all(item["reason"] == "deadline_miss" for item in audit["withheld"])
    assert audit["feed_count"] == 58


def test_naive_snapshot_mixing_frozen(report):
    naive = report["snapshot"]["naive"]
    assert naive["frames"] == 40
    assert naive["mixed_frames"] == 40
    assert naive["mixed_ratio"] == 1.0
    assert naive["max_field_skew_samples"] == 1
    assert naive["first_mixed"]["frame"] == 0
    assert naive["first_mixed"]["sources"] == [0, 1, 1, 1, 1]
    assert naive["first_mixed"]["mixed_fields"] == [
        "current_ma",
        "temp_c10",
        "charger_present",
        "isr_seq",
    ]
    sign = naive["sign_flip_evidence"]
    assert sign["frame"] == 8
    assert sign["cell_mv_source"] == 8
    assert sign["current_ma_source"] == 9
    assert sign["cell_mv"] == 3_710
    assert sign["current_ma"] == -30_000
    assert sign["current_step_ma"] == -48_000
    assert sign["frame_isr_seq"] == 9


def test_epoch_snapshot_zero_mixing(report):
    epoch = report["snapshot"]["epoch"]
    assert epoch["frames"] == 40
    assert epoch["mixed_frames"] == 0
    assert epoch["stale_frames"] == 40
    assert epoch["max_staleness_us"] == 9_900
    assert epoch["retries"] == 0
    assert epoch["reader_copy_us"] == 6_000
    assert epoch["writer_copy_us"] == 9_200
    assert epoch["publish_offset_us"] == 9_600
    assert epoch["safety"]["safe"] is True
    assert epoch["safety"]["margin_us"] == 4_000


def test_double_buffer_safety_condition():
    safe = d20.double_buffer_safe(6_000, 10_000)
    assert safe == {
        "reader_copy_us": 6_000,
        "writer_period_us": 10_000,
        "safe": True,
        "margin_us": 4_000,
    }
    unsafe = d20.double_buffer_safe(12_000, 10_000)
    assert unsafe["safe"] is False
    assert unsafe["margin_us"] == -2_000
    rows = d20.snapshot_frame_rows()
    naive_rows = [row for row in rows if row["scheme"] == "naive"]
    epoch_rows = [row for row in rows if row["scheme"] == "epoch"]
    assert len(naive_rows) == 40
    assert len(epoch_rows) == 40
    assert all(row["mixed"] is True for row in naive_rows)
    assert all(row["mixed"] is False for row in epoch_rows)
    assert all(row["stale"] is True for row in epoch_rows)


def test_crc_known_answer_and_slot_roundtrip():
    assert d20.crc16_ccitt(b"123456789") == 0x29B1
    raw = d20.encode_slot(d20.DEFAULT_PARAMS, d20.BASE_GEN)
    assert len(raw) == 20
    slot = d20.decode_slot(raw)
    assert slot["valid"] is True
    assert slot["gen"] == 41
    assert slot["values"] == d20.DEFAULT_PARAMS
    assert slot["stored_crc"] == 14_330
    short = d20.decode_slot(b"BZ")
    assert short["valid"] is False
    assert short["failure_stage"] == "crc"


def test_parameter_selection_tie_prefers_a():
    raw = d20.encode_slot(d20.DEFAULT_PARAMS, d20.BASE_GEN)
    selected = d20.select_params(raw, raw)
    assert selected["selected"] == "a"
    assert selected["selected_gen"] == 41
    assert selected["status"] == "healthy"


def test_mid_write_reset_recovery(report):
    recovery = report["params"]["mid_write_recovery"]
    boot1 = recovery["boot1"]
    assert boot1["selected"] == "a"
    assert boot1["selected_gen"] == 41
    assert boot1["status"] == "degraded"
    assert boot1["params"]["ot_c10"] == 600
    assert boot1["degraded"][0]["reason"] == "slot_b_crc_rejected"
    slot_b = boot1["slots"]["b"]
    assert slot_b["gen"] == 42
    assert slot_b["magic_ok"] is False
    assert slot_b["crc_ok"] is False
    assert slot_b["failure_stage"] == "crc"
    assert slot_b["stored_crc"] == 14_330
    assert slot_b["computed_crc"] == 22_051
    assert slot_b["values"]["ot_c10"] == 550
    assert slot_b["values"]["ocp_ma"] == 30_000
    assert boot1["naive"]["selected"] == "b"
    assert boot1["naive"]["selected_gen"] == 42
    assert boot1["naive"]["params"]["ot_c10"] == 550
    assert boot1["naive"]["params"]["ocp_ma"] == 30_000
    assert recovery["counter_after_boot1"] == 41
    assert recovery["counter_after_repair"] == 41
    assert recovery["intended_gen_lost"] == 42
    assert recovery["boots_to_healthy"] == 2
    boot2 = recovery["boot2"]
    assert boot2["selected"] == "a"
    assert boot2["selected_gen"] == 41
    assert boot2["status"] == "healthy"
    torn = report["params"]["torn_fields"]
    assert torn["ot_c10_intended"] == 550
    assert torn["ot_c10_torn"] == 550
    assert torn["ocp_ma_torn"] == 30_000


def test_crc_bitflip_falls_back_to_a(report):
    case = next(item for item in report["params"]["cases"] if item["case"] == "crc_bitflip")
    assert case["status"] == "degraded"
    assert case["selected"] == "a"
    assert case["selected_gen"] == 41
    assert case["slots"]["b"]["crc_ok"] is False
    assert case["slots"]["b"]["failure_stage"] == "crc"
    assert case["params"]["ot_c10"] == 600
    assert case["naive"]["params"]["ot_c10"] == 2_598
    evidence = report["params"]["bitflip_evidence"]
    assert evidence["ot_c10_robust"] == 600
    assert evidence["ot_c10_naive"] == 2_598
    assert evidence["naive_selected_gen"] == 42
    recovery = report["params"]["crc_bitflip_recovery"]
    assert recovery["boot1_selected"] == "a"
    assert recovery["boot1_gen"] == 41
    assert recovery["boot1_status"] == "degraded"
    assert recovery["boot2_selected"] == "a"
    assert recovery["boot2_gen"] == 41
    assert recovery["boot2_status"] == "healthy"


def test_boot_chain_version_range_defaults(report):
    cases = {item["case"]: item for item in report["params"]["cases"]}
    healthy = cases["healthy_both_valid"]
    assert healthy["selected"] == "b"
    assert healthy["selected_gen"] == 42
    assert healthy["status"] == "healthy"
    assert healthy["params"]["ot_c10"] == 550
    version = cases["version_mismatch"]
    assert version["slots"]["b"]["schema"] == 3
    assert version["slots"]["b"]["crc_ok"] is True
    assert version["degraded"][0]["stage"] == "version"
    assert version["degraded"][0]["reason"] == "slot_b_version_rejected"
    assert version["selected_gen"] == 41
    ranged = cases["range_fail"]
    assert ranged["slots"]["b"]["crc_ok"] is True
    assert ranged["degraded"][0]["stage"] == "range"
    assert ranged["degraded"][0]["reason"] == "slot_b_range_rejected"
    assert ranged["degraded"][0]["detail"] == ["ovp_mv=5000 越界 [4000, 4300]"]
    assert ranged["naive"]["params"]["ovp_mv"] == 5_000
    both = cases["both_bad"]
    assert both["selected"] is None
    assert both["selected_gen"] == 0
    assert both["params"] == d20.DEFAULT_PARAMS
    assert both["degraded"][-1]["reason"] == "all_slots_invalid_defaults"
    chain = {item["case"]: item for item in report["params"]["boot_chain"]}
    assert chain["healthy_both_valid"]["stage"] == "ok"
    assert chain["mid_write_reset"]["stage"] == "crc"
    assert chain["version_mismatch"]["stage"] == "version"
    assert chain["range_fail"]["stage"] == "range"
    assert chain["both_bad"]["stage"] == "defaults"


def test_d19_counter_rule_frozen(report):
    assert d20.sequence_state(1, 14, 16)["state"] == "gap"
    assert d20.sequence_state(1, 14, 16)["missing"] == 2
    assert d20.sequence_state(15, 0, 16)["state"] == "late_or_reset"
    assert d20.sequence_state(15, 15, 16)["state"] == "repeat"
    assert d20.sequence_state(8, 0, 16)["state"] == "ambiguous"
    assert d20.sequence_state(0, 14, 16)["missing"] == 1
    probes = report["interfaces"]["d19"]["probes"]
    assert probes[0]["delta"] == 3
    assert probes[0]["missing"] == 2
    assert report["interfaces"]["d19"]["frame_counter_modulus"] == 16
    assert report["interfaces"]["d19"]["snapshot_epoch_modulus"] == 65_536


def test_interfaces_d08_d17_frozen(report):
    d08 = report["interfaces"]["d08"]
    assert d08["electrical_window_ms"] == 72.263
    assert d08["d08_scheduling_term_ms"] == 5.0
    assert d08["fast_max_nominal_start_jitter_ms"] == 1.97
    assert d08["within_d08_scheduling_term"] is True
    assert d08["window_unchanged"] is True
    d17 = report["interfaces"]["d17"]
    assert d17["estimate_wcet_us"] == 8_000
    assert d17["slow_lane_budget_us"] == 40_000
    assert d17["share_of_slow_budget"] == 0.2
    assert d17["slow_lane_headroom_us"] == 32_000
    assert d17["slow_observed_wcet_us"] == 13_100


def test_identity_and_boundary_declared(report):
    assert report["scenario_id"] == "D20-rt-scheduling"
    assert report["replay"]["scenario_id"] == "D20-trace-replay"
    assert report["replay"]["verdict"] == "deadline_miss"
    assert "不是实测 WCET" in report["identity"]
    boundary = report["boundary"]
    assert boundary["bms_inputs_fields"] == [
        "cell_mv[]",
        "current_ma",
        "temp_c10",
        "charger_present",
    ]
    assert "timestamp" in boundary["missing_fields"]
    assert "quality_bit" in boundary["missing_fields"]
    assert "BmsInputs" in boundary["firmware_gap"]
    assert "没有" in boundary["firmware_gap"]
    assert "软件在环" in boundary["no_hardware"]
    assert "33-实时固件与数据所有权.md" in boundary["book_layer_gap"]
    assert "尚缺" in boundary["book_layer_gap"]
    assert "不虚构" in boundary["book_layer_gap"]


def test_cli_default_export(tmp_path):
    out = tmp_path / "out"
    assert d20.main(["--out", str(out)]) == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report == d20.build_report()
    assert report["scenario_id"] == "D20-rt-scheduling"
    trace = (out / "task_trace.csv").read_text(encoding="utf-8").splitlines()
    assert trace[0] == "job,lane,release_us,start_us,finish_us,exec_us"
    assert len(trace) == 667
    frames = (out / "snapshot_frames.csv").read_text(encoding="utf-8").splitlines()
    assert frames[0] == (
        "scheme,frame,start_us,cell_mv_source,current_ma_source,temp_c10_source,"
        "charger_source,isr_seq_source,mixed,stale"
    )
    assert len(frames) == 81
    params = (out / "param_boot.csv").read_text(encoding="utf-8").splitlines()
    assert params[0] == (
        "case,slot,stage,gen,crc_ok,schema,selected,selected_gen,status"
    )
    assert len(params) == 13


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_file",
        "bad_header",
        "missing_column",
        "non_finite",
        "time_regression",
        "overlap",
        "exec_out_of_bounds",
        "unknown_lane",
        "too_few_rows",
        "missing_slow_lane",
        "duplicate_job",
    ],
)
def test_cli_rejects_bad_trace(tmp_path, mutation):
    rows = _raw_trace()
    target = tmp_path / f"{mutation}.csv"
    if mutation == "missing_file":
        path = tmp_path / "absent.csv"
    else:
        if mutation == "bad_header":
            path = tmp_path / f"{mutation}.csv"
            path.write_text(
                "job,lane,release_us,start_us,finish_us,exec_ms\n"
                + "\n".join(",".join(str(value) for value in row) for row in rows[:40])
                + "\n",
                encoding="utf-8",
            )
        elif mutation == "missing_column":
            path = tmp_path / f"{mutation}.csv"
            path.write_text(
                "job,lane,release_us,start_us,finish_us\n"
                + "\n".join(",".join(str(value) for value in row[:5]) for row in rows[:40])
                + "\n",
                encoding="utf-8",
            )
        elif mutation == "non_finite":
            rows[2][5] = "nan"
            path = _write_trace(target, rows)
        elif mutation == "time_regression":
            fast_indices = [index for index, row in enumerate(rows) if row[1] == "fast"]
            rows[fast_indices[1]][2] = _row_int(rows, fast_indices[0], 2) - 1
            path = _write_trace(target, rows)
        elif mutation == "overlap":
            fast_indices = [index for index, row in enumerate(rows) if row[1] == "fast"]
            rows[fast_indices[0]][4] = _row_int(rows, fast_indices[1], 3) + 5_000
            path = _write_trace(target, rows)
        elif mutation == "exec_out_of_bounds":
            fast_indices = [index for index, row in enumerate(rows) if row[1] == "fast"]
            rows[fast_indices[0]][5] = 300_000
            rows[fast_indices[0]][4] = _row_int(rows, fast_indices[0], 3) + 300_000
            path = _write_trace(target, rows)
        elif mutation == "unknown_lane":
            rows[1][1] = "uart"
            path = _write_trace(target, rows)
        elif mutation == "too_few_rows":
            path = _write_trace(target, rows[:3])
        elif mutation == "missing_slow_lane":
            path = _write_trace(target, [row for row in rows if row[1] != "slow"])
        else:  # duplicate_job
            rows[1][0] = rows[0][0]
            path = _write_trace(target, rows)
    assert d20.main(["--trace", str(path)]) == 2


def test_cli_trace_replay_deterministic(tmp_path):
    trace_path = tmp_path / "task_trace.csv"
    d20.write_task_trace(d20.simulate_schedule(), trace_path)
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    assert d20.main(["--trace", str(trace_path), "--out", str(out_a)]) == 0
    assert d20.main(["--trace", str(trace_path), "--out", str(out_b)]) == 0
    text_a = (out_a / "report.json").read_text(encoding="utf-8")
    text_b = (out_b / "report.json").read_text(encoding="utf-8")
    assert text_a == text_b
    replay = json.loads(text_a)
    assert replay["scenario_id"] == "D20-trace-replay"
    assert replay["verdict"] == "deadline_miss"
    assert replay["lanes"]["fast"]["wcet_us"] == 14_000
    assert replay["lanes"]["fast"]["deadline_miss_ticks"] == [37, 38]
    assert replay["lanes"]["slow"]["wcet_us"] == 13_100
    assert replay["watchdog"]["feeds"] == 58
    assert replay["watchdog"]["withheld_count"] == 2
    assert replay["watchdog"]["max_gap_us"] == 31_985
    assert replay["watchdog"]["reset_at_us"] is None
    assert "不能由本回放证明" in replay["note"]
