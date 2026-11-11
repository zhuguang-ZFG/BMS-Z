"""D08 reaction windows, blind windows, hysteresis, and feedback timeout."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d08_protection_timing", HERE / "d08_protection_timing.py"
)
assert spec is not None and spec.loader is not None
d08 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d08
spec.loader.exec_module(d08)


def test_reaction_window_scales_with_fault_phase():
    best = d08.reaction_window_ms(0.0)
    worst = d08.reaction_window_ms(d08.SCAN_MS)
    typical = d08.reaction_window_ms(5.0)
    assert best["total_ms"] == pytest.approx(62.0)
    assert typical["total_ms"] == pytest.approx(67.0)
    assert worst["total_ms"] == pytest.approx(72.263)
    assert worst["total_ms"] - best["total_ms"] == pytest.approx(d08.SCAN_MS, rel=1e-4)
    with pytest.raises(ValueError):
        d08.reaction_window_ms(d08.SCAN_MS + 1.0)


def test_confirm_window_suppresses_glitch_but_blinds_short_faults():
    g = d08.glitch_vs_fault()
    assert g["confirm_window_ms"] == pytest.approx(40.0)
    assert g["blind_window_ms"] == pytest.approx(60.0)
    assert g["glitch_survives"] is False, "8 ms 毛刺必须被抑制"
    assert g["real_fault_detected"] is False, (
        "25 ms 真实故障同样漏检——盲区是同一个窗的另一面"
    )


def test_hysteresis_turns_chatter_into_one_latch():
    h = d08.hysteresis_chatter()
    assert h["threshold_a"] == pytest.approx(50.0)
    assert h["release_a"] == pytest.approx(45.0)
    assert h["actions_without_hysteresis"] == pytest.approx(12)
    assert h["actions_with_hysteresis"] == pytest.approx(1)


def test_feedback_timeout_is_a_fault():
    assert d08.feedback_timeout(100.0, 112.0)["within_window"] is True
    late = d08.feedback_timeout(100.0, 125.0)
    assert late["within_window"] is False
    assert "锁存" in late["verdict"]
    never = d08.feedback_timeout(100.0, None)
    assert never["within_window"] is False
    with pytest.raises(ValueError):
        d08.feedback_timeout(-1.0, 0.0)


def test_report_extends_s1_frozen_budget():
    report = d08.build_report()
    assert report["window_worst_ms"] == pytest.approx(72.263)
    assert "10.26337" in report["identity"]
    assert report["feedback"]["never"]["within_window"] is False


# --- D08-fault-replay：统一状态机 + 规定故障集 + 可重放日志 ---

CSV_HEADER = "seq,t_ms,current_a,link_up,crc_ok,fb_delta_ms,clear"


def _write_log(tmp_path, rows, name="log.csv"):
    p = tmp_path / name
    p.write_text(CSV_HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return p


def _row(seq, t, i=10.0, link=1, crc=1, fb="", clear=0):
    return f"{seq},{t},{i},{link},{crc},{fb},{clear}"


def test_replay_normal_sequence_reaches_normal_without_faults(tmp_path):
    p = _write_log(tmp_path, [_row(i, (i - 1) * 20) for i in range(1, 6)])
    r = d08.replay_log(p)
    assert r["faults"] == []
    assert r["final_state"] == "NORMAL"
    assert r["transitions"][0]["to_state"] == "NORMAL"
    assert len(r["transitions"]) == 1  # 只有 INIT→NORMAL 一次转移


def test_crc_error_latches_fault_and_blocks_release_without_clear(tmp_path):
    p = _write_log(
        tmp_path,
        [
            _row(1, 0),
            _row(2, 20, crc=0),  # CRC 坏帧 → 锁存
            _row(3, 40),  # 好帧但没有 clear：不得用旧数据放行
            _row(4, 60),
        ],
    )
    r = d08.replay_log(p)
    assert [f["fault"] for f in r["faults"]] == ["CRC_ERROR"]
    assert r["final_state"] == "FAULT"
    fault_transition = r["transitions"][1]
    assert fault_transition["action"] == "inhibit_all"
    assert fault_transition["to_state"] == "FAULT"


def test_disconnect_latches_inhibit_all(tmp_path):
    p = _write_log(tmp_path, [_row(1, 0), _row(2, 20, link=0), _row(3, 40)])
    r = d08.replay_log(p)
    assert [f["fault"] for f in r["faults"]] == ["DISCONNECT"]
    assert r["transitions"][1]["action"] == "inhibit_all"
    assert r["final_state"] == "FAULT"


def test_stale_data_after_gap_latches(tmp_path):
    rows = [_row(1, 0), _row(2, 20), _row(3, 200)]  # 间隔 180 ms > 100 ms 上限
    p = _write_log(tmp_path, rows)
    r = d08.replay_log(p)
    assert [f["fault"] for f in r["faults"]] == ["STALE_DATA"]
    assert r["final_state"] == "FAULT"


def test_sequence_regression_latches_reset_anomaly(tmp_path):
    p = _write_log(tmp_path, [_row(1, 0), _row(2, 20), _row(1, 40), _row(2, 60)])
    r = d08.replay_log(p)
    assert [f["fault"] for f in r["faults"]] == ["RESET_ANOMALY"]
    assert r["final_state"] == "FAULT"


def test_time_regression_latches_reset_anomaly(tmp_path):
    p = _write_log(tmp_path, [_row(1, 100), _row(2, 90)])
    r = d08.replay_log(p)
    assert [f["fault"] for f in r["faults"]] == ["RESET_ANOMALY"]


def test_feedback_timeout_latches(tmp_path):
    p = _write_log(
        tmp_path,
        [
            _row(1, 0),
            _row(2, 20, fb=25.0),  # 超窗 → 锁存
            _row(3, 40, clear=1),
            _row(4, 60, clear=1),
            _row(5, 80, clear=1),  # 恢复到 NORMAL
            _row(6, 100, fb=-1),  # 命令发出但反馈永远没到 → 再次锁存
        ],
    )
    r = d08.replay_log(p)
    assert [f["fault"] for f in r["faults"]] == ["FEEDBACK_TIMEOUT", "FEEDBACK_TIMEOUT"]
    assert r["transitions"][1]["action"] == "inhibit_all"
    assert r["final_state"] == "FAULT"


def test_ocd_confirm_trip_opens_discharge_and_release_needs_below_45(tmp_path):
    p = _write_log(
        tmp_path,
        [
            _row(1, 0),
            _row(2, 20, i=52.0),
            _row(3, 40, i=52.0),  # 连续 3 拍超 50 A 才动作
            _row(4, 60, i=52.0),
            _row(5, 80, i=46.0, clear=1),  # 46 > 45 释放阈值：恢复前提不满足
            _row(6, 100, i=44.0, clear=1),
            _row(7, 120, i=44.0, clear=1),
            _row(8, 140, i=44.0, clear=1),
        ],
    )
    r = d08.replay_log(p)
    assert [f["fault"] for f in r["faults"]] == ["OCD"]
    trip = r["transitions"][1]
    assert trip["action"] == "open_discharge"  # 断放留充，与固件方向性一致
    assert r["final_state"] == "NORMAL"


def test_glitch_current_does_not_trip(tmp_path):
    p = _write_log(
        tmp_path,
        [_row(1, 0), _row(2, 20, i=52.0), _row(3, 40, i=10.0), _row(4, 60, i=52.0)],
    )
    r = d08.replay_log(p)
    assert r["faults"] == []
    assert r["final_state"] == "NORMAL"


def test_recovery_requires_clear_plus_k_valid_frames(tmp_path):
    p = _write_log(
        tmp_path,
        [
            _row(1, 0),
            _row(2, 20, crc=0),  # 锁存 CRC_ERROR
            _row(3, 40, clear=1),  # 恢复计数 1
            _row(4, 60, crc=0, clear=1),  # 恢复途中坏帧：计数清零，仍 FAULT
            _row(5, 80, clear=1),  # 重新计数 1
            _row(6, 100, clear=1),  # 2
            _row(7, 120, clear=1),  # 3 → NORMAL
        ],
    )
    r = d08.replay_log(p)
    assert [f["fault"] for f in r["faults"]] == ["CRC_ERROR"]
    assert r["final_state"] == "NORMAL"
    assert len(r["transitions"]) == 3  # INIT→NORMAL, NORMAL→FAULT, FAULT→NORMAL


def test_replay_rejects_nonfinite_current(tmp_path):
    p = _write_log(tmp_path, [_row(1, 0), _row(2, 20, i="nan")])
    with pytest.raises(ValueError, match="非有限|finite"):
        d08.replay_log(p)


def test_transition_table_contract_rows_complete():
    table = d08.transition_table()
    assert table, "状态转移表不能为空"
    for row in table:
        for key in ("transition", "input", "deadline", "action", "recovery"):
            assert row.get(key), f"转移 {row.get('transition')} 缺 {key}"
    names = {row["transition"] for row in table}
    assert {"INIT→NORMAL", "NORMAL→FAULT", "FAULT→NORMAL"} <= names


def test_crc_latched_overcurrent_blocks_recovery(tmp_path):
    # CRC 锁存后出现过流：三帧 52 A + clear=1 不得放行；电流回到迟滞释放线下才恢复
    rows = [_row(1, 0), _row(2, 20, crc=0)]  # NORMAL → CRC 锁存
    rows += [_row(s, t, i=52.0, clear=1) for s, t in ((3, 80), (4, 140), (5, 200))]
    r = d08.replay_log(_write_log(tmp_path, rows))
    assert r["final_state"] == "FAULT"
    assert [t["trigger"] for t in r["transitions"]] == ["FIRST_VALID_FRAME", "CRC_ERROR"]
    assert r["output_events"][-1]["mask"] == "inhibit_all"  # 完整性锁存不被 OCD 降级
    rows += [_row(s, t, i=44.0, clear=1) for s, t in ((6, 260), (7, 320), (8, 380))]
    r = d08.replay_log(_write_log(tmp_path, rows))
    assert r["final_state"] == "NORMAL"
    assert r["transitions"][-1]["trigger"] == "RECOVERED"
    assert r["faults"] == [{"fault": "CRC_ERROR", "tick": 2, "t_ms": 20.0}]  # 首现场不改写


def test_ocd_latched_crc_escalates_output_mask(tmp_path):
    # OCD 锁存后输入帧失效：输出必须升级为 inhibit_all，状态与首现场快照不变
    rows = [_row(1, 0)]
    rows += [_row(s, t, i=52.0) for s, t in ((2, 60), (3, 120), (4, 180))]  # 锁存 OCD
    rows.append(_row(5, 240, i=52.0, crc=0))  # 锁存期内 CRC 活动故障
    r = d08.replay_log(_write_log(tmp_path, rows))
    assert r["final_state"] == "FAULT"
    assert r["faults"] == [{"fault": "OCD", "tick": 4, "t_ms": 180.0}]
    assert [e["mask"] for e in r["output_events"]] == [
        "normal_path",
        "open_discharge",
        "inhibit_all",
    ]  # 锁存期内输出随活动故障升级
    assert r["output_events"][-1]["active_fault"] == "CRC_ERROR"
    rows += [_row(s, t, i=44.0, crc=0, clear=1) for s, t in ((6, 300), (7, 360), (8, 420))]
    assert d08.replay_log(_write_log(tmp_path, rows))["final_state"] == "FAULT"


def test_mask_escalation_latched_until_recovery(tmp_path):
    # OCD 锁存 → CRC 升级 inhibit_all → 好帧但无 clear：掩码不得降回 open_discharge
    rows = [_row(1, 0)]
    rows += [_row(s, t, i=52.0) for s, t in ((2, 60), (3, 120), (4, 180))]  # 锁存 OCD
    rows.append(_row(5, 240, i=52.0, crc=0))  # 活动 CRC：升级 inhibit_all
    rows.append(_row(6, 300, i=44.0, clear=0))  # 好帧、无 clear、电流已回释放线下
    r = d08.replay_log(_write_log(tmp_path, rows))
    assert r["final_state"] == "FAULT"
    assert [e["mask"] for e in r["output_events"]] == [
        "normal_path",
        "open_discharge",
        "inhibit_all",
    ]  # 升级后锁存：第 6 拍好帧不产生降级事件
    assert len(r["transitions"]) == 2  # 未满足恢复条件，无 FAULT→NORMAL
    rows += [_row(s, t, i=44.0, clear=1) for s, t in ((7, 360), (8, 420), (9, 480))]
    r = d08.replay_log(_write_log(tmp_path, rows))
    assert r["final_state"] == "NORMAL"
    assert r["output_events"][-1]["mask"] == "normal_path"  # 恢复才复位掩码


def test_cli_replay_missing_file_exit2(tmp_path, capsys):
    rc = d08.main(["--replay", str(tmp_path / "absent.csv"), "--out", str(tmp_path / "o")])
    assert rc == 2


def test_cli_replay_writes_transitions_and_report(tmp_path):
    log = _write_log(tmp_path, [_row(1, 0), _row(2, 20, crc=0), _row(3, 40)])
    out = tmp_path / "out"
    rc = d08.main(["--replay", str(log), "--out", str(out)])
    assert rc == 0
    assert (out / "transitions.csv").exists()
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["fault_replay"]["faults"] == ["CRC_ERROR"]
    assert report["fault_replay"]["final_state"] == "FAULT"
    # 旧场景字段不回归
    assert report["window_worst_ms"] == pytest.approx(72.263)


def test_default_report_includes_fault_replay_demo():
    report = d08.build_report()
    demo = report["fault_replay"]
    assert demo["scenario_id"] == "D08-fault-replay"
    assert demo["final_state"] == "NORMAL"
    assert demo["recoveries"] == 6
    assert set(demo["faults"]) == {
        "CRC_ERROR",
        "DISCONNECT",
        "STALE_DATA",
        "RESET_ANOMALY",
        "FEEDBACK_TIMEOUT",
        "OCD",
    }
