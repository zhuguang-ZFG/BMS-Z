"""D19 bus boundary, frame lifecycle, and counter-window contract."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d19_bus_data", HERE / "d19_bus_data.py")
assert spec is not None and spec.loader is not None
d19 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d19
spec.loader.exec_module(d19)


@pytest.fixture(scope="module")
def report():
    return d19.build_report()


def test_crc_reference_vector_and_golden_frame(report):
    # 先用已知向量证明 CRC 程序本身对：0x29B1 是 CRC-16/CCITT-FALSE 的标准检查值
    assert d19.crc16_ccitt_false(b"123456789") == 0x29B1
    assert report["frame"]["crc_check_input"] == "123456789"
    golden = report["frame"]["golden"]
    assert golden["payload_hex"] == "1000c80000784b78"
    assert golden["covered_hex"] == "018f081000c80000784b78"
    assert golden["crc_hex"] == "46FA"
    assert golden["wire_hex"] == "018f081000c80000784b7846fa"
    decoded = golden["decoded"]
    assert decoded["session"] == 1
    assert decoded["counter"] == 0
    assert decoded["pack_v"] == pytest.approx(51.2)
    assert decoded["current_a"] == pytest.approx(12.0)
    assert decoded["temp_c"] == 35
    assert decoded["soc_pp"] == pytest.approx(60.0)


def test_encoding_roundtrip_and_bounds():
    payload = d19.encode_payload(5, 2, pack_mv=50000, current_da=-25, temp_c=10, soc_pp=42.5)
    decoded = d19.decode_signals(payload)
    assert decoded["counter"] == 5
    assert decoded["session"] == 2
    assert decoded["pack_mv"] == 50000
    assert decoded["current_a"] == pytest.approx(-2.5)  # 负号只出现一次：放电为正
    assert decoded["temp_c"] == 10
    assert decoded["soc_pp"] == pytest.approx(42.5)
    with pytest.raises(ValueError):
        d19.encode_payload(16, 1)
    with pytest.raises(ValueError):
        d19.encode_payload(0, 16)
    with pytest.raises(ValueError):
        d19.encode_payload(0, 0, pack_mv=70000)
    with pytest.raises(ValueError):
        d19.encode_payload(0, 0, current_da=40000)
    with pytest.raises(ValueError):
        d19.encode_payload(0, 0, temp_c=-41)
    with pytest.raises(ValueError):
        d19.encode_payload(0, 0, soc_pp=200.0)
    with pytest.raises(ValueError):
        d19.decode_signals(b"\x00\x01")


def test_bit_budget_and_timing_frozen(report):
    timing = report["timing"]
    assert timing["bit_time_us"] == pytest.approx(2.0)
    assert timing["nominal_bits"] == 111
    assert timing["stuffable_bits"] == 98
    # 最坏填充 1 + floor((98−5)/4) = 24；135 位 × 2 µs = 270 µs
    assert timing["worst_stuff_bits"] == 24
    assert timing["worst_bits"] == 135
    assert timing["nominal_frame_us"] == pytest.approx(222.0)
    assert timing["worst_frame_us"] == pytest.approx(270.0)
    # 对照：整段填充区同值（全 0）只有 19 个填充位，它不是最坏情形
    assert timing["uniform_region_stuff_bits"] == 19
    assert timing["uniform_region_frame_us"] == pytest.approx(260.0)
    assert timing["bus_load_pct"] == pytest.approx(1.35)
    budget = timing["timeout_budget_ms"]
    assert budget["total"] == pytest.approx(100.0)
    assert budget["period"] + budget["jitter"] + budget["transport"] + budget["margin"] == 100.0
    assert timing["frame_timeout_ms"] == pytest.approx(100.0)
    assert timing["uart_baud"] == 115200
    assert timing["uart_bits_per_char"] == 10
    assert timing["modbus_silence_chars"] == pytest.approx(3.5)
    assert timing["uart_10bit_char_ms_at_115200"] == pytest.approx(0.086806)
    assert timing["modbus_3_5_char_ms_at_115200"] == pytest.approx(0.303819)


def test_bit_levels_and_lifecycle_table(report):
    levels = report["frame"]["bit_levels"]
    assert levels["dominant"]["logic"] == 0
    assert levels["dominant"]["diff_v"] == pytest.approx(2.0)
    assert levels["recessive"]["logic"] == 1
    assert levels["recessive"]["diff_v"] == pytest.approx(0.0)
    stages = report["judgement_chain"]["stages"]
    assert [s["stage"] for s in stages] == [
        "arrival",
        "identity",
        "integrity",
        "session",
        "counter",
        "publish",
    ]
    assert report["judgement_chain"]["order"] == ["identity", "crc", "session", "counter"]
    assert report["judgement_chain"]["short_circuit"] is True
    assert report["window"]["forward_window"] == 2
    assert report["window"]["backward_window"] == 0
    assert report["window"]["degrade_after_missing"] == 3
    assert report["window"]["recovery_frames"] == 3


def test_classify_counter_edges():
    assert d19.classify_counter(9, 9) == (0, "duplicate")
    assert d19.classify_counter(9, 10) == (1, "in_window")
    assert d19.classify_counter(15, 1) == (2, "in_window")
    assert d19.classify_counter(15, 2) == (3, "gap_too_large")
    assert d19.classify_counter(15, 3) == (4, "gap_too_large")
    assert d19.classify_counter(0, 8) == (8, "ambiguous")
    assert d19.classify_counter(0, 9) == (9, "late")
    assert d19.classify_counter(9, 7) == (14, "late")
    with pytest.raises(ValueError):
        d19.classify_counter(0, 1, window=8)


def test_stale_replay_legal_crc_rejected(report):
    case = report["counterexamples"]["stale_replay"]
    assert case["crc_all_valid"] is True
    assert case["identical_bytes_to_seq_8"] is True
    assert case["delta"] == 14
    assert case["kind"] == "late"
    assert case["rejected_by_reason"] == {"late": 3}
    assert case["accepted_before_replay"] == 10
    assert case["accepted_after_replay"] == 10
    assert case["last_trusted_unchanged"] is True


def test_wrap_boundary_three_cases(report):
    cases = {row["case"]: row for row in report["counterexamples"]["wrap"]["cases"]}
    assert cases["wrap_15_to_0"]["final_delta"] == 1
    assert cases["wrap_15_to_0"]["last_decision"] == "accept"
    assert cases["wrap_15_to_0"]["accepted"] == 5
    assert cases["wrap_15_to_1"]["final_delta"] == 2
    assert cases["wrap_15_to_1"]["last_decision"] == "accept"
    assert cases["wrap_15_to_1"]["accepted"] == 5
    assert cases["wrap_15_to_2"]["final_delta"] == 3
    assert cases["wrap_15_to_2"]["last_decision"] == "reject"
    assert cases["wrap_15_to_2"]["last_reason"] == "gap_too_large"
    assert cases["wrap_15_to_2"]["accepted"] == 4
    assert cases["wrap_15_to_2"]["rejected"] == 1


def test_out_of_order_uses_last_accepted_basis(report):
    case = report["counterexamples"]["out_of_order"]
    assert case["sequence"] == [5, 7, 6]
    assert case["decisions"] == ["accept", "accept", "reject"]
    assert case["reasons"] == ["", "", "late"]
    # 6 相对 5 只有 +1（窗内），但 7 已先被接受 → 对最后已接受帧的模差是 15
    assert case["delta_6_vs_5"] == 1
    assert case["delta_6_vs_7"] == 15
    assert case["accepted"] == 2
    assert case["rejected"] == 1
    assert case["final_counter"] == 7


def test_bus_recovery_transitions_frozen(report):
    case = report["counterexamples"]["bus_recovery"]
    assert case["missing_slots"] == 5
    assert case["timeout_events"] == 1
    assert case["degrade_threshold"] == 3
    assert case["recovery_frames"] == 3
    assert case["entered_at_seq"] == 4
    assert case["entered_at_t_ms"] == pytest.approx(160.0)
    assert case["exited_at_seq"] == 7
    assert case["exited_at_t_ms"] == pytest.approx(220.0)
    assert case["degraded_arrivals"] == 4
    assert case["decisions"] == [
        "accept",
        "accept",
        "accept",
        "reject",
        "resync_observation",
        "resync_observation",
        "accept",
    ]
    assert case["reasons"][3] == "gap_too_large"
    assert case["reasons"][-1] == "recovered"
    assert case["accepted"] == 4
    assert case["rejected"] == 1
    assert case["resync_observations"] == 2
    assert case["final_counter"] == 11


def test_duplicate_and_cross_session(report):
    duplicate = report["counterexamples"]["duplicate"]
    assert duplicate["delta"] == 0
    assert duplicate["kind"] == "duplicate"
    assert duplicate["accepted"] == 4
    assert duplicate["rejected_by_reason"] == {"duplicate": 1}
    assert duplicate["published_updates"] == 4
    cross = report["counterexamples"]["cross_session"]
    # 会话门在计数器门之前：delta=1 本来会被窗口接受
    assert cross["delta_would_be"] == 1
    assert cross["window_would_accept"] is True
    assert cross["reasons"][4] == "session"
    assert cross["decisions"] == ["accept", "accept", "accept", "accept", "reject", "accept"]
    assert cross["rejected_by_reason"] == {"session": 1}
    assert cross["accepted"] == 5


def test_crc_short_circuit_order_pinned(report):
    case = report["counterexamples"]["crc_short_circuit"]
    assert case["reject_reason"] == "crc"
    assert case["counter_evaluated"] is False
    assert case["checks_evaluated"] == ["identity", "crc"]
    assert case["rejected_by_reason"] == {"crc": 1}


def test_default_scenario_frozen(report):
    replay = report["replay"]
    assert report["scenario_id"] == "D19-bus-lifecycle"
    assert replay["scenario_id"] == "D19-frame-replay"
    assert replay["frames"] == 29
    assert replay["accepted"] == 20
    assert replay["rejected"] == 7
    assert replay["resync_observations"] == 2
    assert replay["published_updates"] == 20
    assert replay["held_frames"] == 9
    assert replay["missing_slots"] == 5
    assert replay["timeout_events"] == 1
    assert replay["stale_data_events"] == 3
    assert replay["rejected_by_reason"] == {
        "crc": 1,
        "gap_too_large": 2,
        "late": 3,
        "session": 1,
    }
    assert replay["final_state"] == "normal"
    assert replay["final_counter"] == 11
    assert replay["last_trusted_soc_pp"] == pytest.approx(65.5)
    transitions = [(t["seq"], t["from"], t["to"], t["source"]) for t in replay["transitions"]]
    assert transitions == [
        (1, "init", "normal", "frame"),
        (26, "normal", "degraded", "frame"),
        (29, "degraded", "normal", "frame"),
    ]
    # 默认视界 = 末帧时刻：不追加静默尾，因此既有冻结数字不变
    assert replay["horizon_ms"] == pytest.approx(660.0)
    assert replay["clock_missing_slots"] == 0
    assert replay["silent_degraded_at_ms"] is None
    assert replay["clock_events"] == []


def test_receiver_holds_last_trusted_value_while_degraded():
    scenario = d19.run_scenario(d19.default_arrivals())
    rows = scenario["rows"]
    assert isinstance(rows, list)
    # seq 25（counter 2）之后进入丢帧区：发布值停在 61.0，直到恢复帧才更新
    assert rows[23]["counter"] == 2
    assert rows[23]["published_soc_pp"] == pytest.approx(61.0)
    for index in (24, 25, 26, 27):
        assert rows[index]["published_soc_pp"] == pytest.approx(61.0)
    assert rows[27]["decision"] == "resync_observation"
    assert rows[28]["decision"] == "accept"
    assert rows[28]["reason"] == "recovered"
    assert rows[28]["published_soc_pp"] == pytest.approx(65.5)
    assert rows[3]["timeout_flag"] is False
    assert rows[25]["timeout_flag"] is True
    # 数据年龄：帧到了不等于数据新。140/160/180 ms 三拍持续过期；恢复帧 200 ms 但发布新值
    assert rows[25]["data_age_ms"] == pytest.approx(140.0)
    assert rows[26]["data_age_ms"] == pytest.approx(160.0)
    assert rows[27]["data_age_ms"] == pytest.approx(180.0)
    assert rows[28]["data_age_ms"] == pytest.approx(200.0)
    assert [rows[index]["stale_data"] for index in (25, 26, 27)] == [True, True, True]
    assert rows[28]["stale_data"] is False
    assert rows[24]["data_age_ms"] == pytest.approx(20.0)


def test_degraded_anchor_never_uses_untrusted_counter():
    frames = [d19.arrival(0.0, 0, seq=1), d19.arrival(20.0, 1, seq=2), d19.arrival(40.0, 2, seq=3)]
    payload = d19.synthetic_payload(8)
    frames.append(
        d19.Frame(
            seq=4,
            t_ms=160.0,
            msg_id=d19.MSG_ID,
            dlc=d19.DLC,
            payload=payload,
            crc_rx=d19.frame_crc(d19.MSG_ID, d19.DLC, payload) ^ 1,
        )
    )
    frames += [d19.arrival(180.0, 9, seq=5), d19.arrival(200.0, 10, seq=6), d19.arrival(220.0, 11, seq=7)]
    scenario = d19.run_scenario(frames)
    rows = scenario["rows"]
    assert isinstance(rows, list)
    assert rows[3]["reason"] == "crc"
    assert rows[3]["state_after"] == "degraded"
    # 入口帧 CRC 坏，它的计数器 8 不可信：锚取最后可信计数 2，第一拍观察差值 9−2=7
    assert rows[4]["resync_delta"] == 7
    assert rows[6]["decision"] == "accept"
    assert rows[6]["reason"] == "recovered"
    assert scenario["final_state"] == "normal"


def test_load_frames_rejects_bad_csv(tmp_path):
    good_row = "0,1000c80000784b78"
    bad_cases = {
        "header.csv": "t_s,data\n" + good_row + "\n",
        "no_data.csv": "seq\n0\n",
        "unknown.csv": "seq,data,extra\n" + good_row + ",x\n",
        "nonfinite.csv": "seq,t_ms,data\n" + "".join(
            f"{index},{'nan' if index == 3 else index * 20},1000c80000784b78\n"
            for index in range(12)
        ),
        "regress.csv": "seq,t_ms,data\n" + "".join(
            f"{index},{100 if index == 3 else index * 20},1000c80000784b78\n"
            for index in range(12)
        ),
        "short_data.csv": "seq,data\n" + "".join(
            f"{index},1000c80000784b7\n" for index in range(12)
        ),
        "few.csv": "seq,data\n" + good_row + "\n",
        "extra_field.csv": "seq,data\n" + "".join(
            f"{index},1000c80000784b78,x\n" for index in range(12)
        ),
        "bad_crc.csv": "seq,crc_hex,data\n" + "".join(
            f"{index},ZZZZ,1000c80000784b78\n" for index in range(12)
        ),
    }
    for name, content in bad_cases.items():
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        with pytest.raises(ValueError):
            d19.load_frames(path)


def test_replay_roundtrip_and_determinism(tmp_path):
    frames = d19.default_arrivals()
    assert len(frames) == 29
    csv_path = tmp_path / "frames.csv"
    d19.write_frames_csv(frames, csv_path)
    loaded = d19.load_frames(csv_path)
    assert [f.payload for f in loaded] == [f.payload for f in frames]
    first = d19.run_scenario(frames)
    second = d19.run_scenario(frames)
    assert first == second
    replayed = d19.run_scenario(loaded)
    assert d19.summarize(first) == d19.summarize(replayed)
    assert first["rows"] == replayed["rows"]
    # 坏 CRC 帧随 CSV 带出去，回放时同样被拒（不会被「重算 CRC」洗白）
    assert any(frame.crc_rx is not None for frame in loaded)
    assert replayed["rejected_by_reason"]["crc"] == 1


def test_cli_default_export_and_rejections(tmp_path):
    out = tmp_path / "out"
    assert d19.main(["--out", str(out)]) == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["scenario_id"] == "D19-bus-lifecycle"
    assert report["replay"]["scenario_id"] == "D19-frame-replay"
    assert "BmsInputs" in report["firmware_boundary"]
    assert "SRC05" in report["boundary"]
    assert (out / "frames.csv").exists()
    assert (out / "decisions.csv").exists()
    # 导出的 CSV 用同一状态机回放：工件逐字节一致
    replay_out = tmp_path / "replay"
    assert d19.main(["--frames", str(out / "frames.csv"), "--out", str(replay_out)]) == 0
    assert (replay_out / "decisions.csv").read_text(encoding="utf-8") == (
        out / "decisions.csv"
    ).read_text(encoding="utf-8")
    replay_report = json.loads((replay_out / "report.json").read_text(encoding="utf-8"))
    assert replay_report["replay"]["rejected_by_reason"] == {
        "crc": 1,
        "gap_too_large": 2,
        "late": 3,
        "session": 1,
    }
    assert d19.main(["--frames", str(tmp_path / "absent.csv")]) == 2
    bad = tmp_path / "bad.csv"
    bad.write_text("t_s,data\n0,1000c80000784b78\n", encoding="utf-8")
    assert d19.main(["--frames", str(bad)]) == 2

def test_silent_bus_degrades_without_any_frame():
    frames = [
        d19.arrival(index * d19.FRAME_PERIOD_MS, index, seq=index + 1)
        for index in range(5)
    ]
    scenario = d19.run_scenario(frames, horizon_ms=180.0)
    assert len(scenario["rows"]) == 5  # 视界内没有任何新帧
    assert scenario["silent_degraded_at_ms"] == pytest.approx(140.0)
    assert scenario["final_state"] == "degraded"
    assert scenario["clock_missing_slots"] == 5
    clock = [item for item in scenario["transitions"] if item["source"] == "clock"]
    assert len(clock) == 1
    assert clock[0]["seq"] is None
    assert clock[0]["t_ms"] == pytest.approx(140.0)
    assert clock[0]["reason"] == "silent_bus"
    assert scenario["accepted"] == 5
    assert scenario["published_updates"] == 5


def test_degrade_timestamp_is_condition_time_not_call_time():
    receiver = d19.FrameReceiver()
    for index in range(5):
        receiver.feed(d19.arrival(index * d19.FRAME_PERIOD_MS, index, seq=index + 1))
    # 很晚才推进时钟：转移时间必须回填到条件首次成立的 140 ms，而不是调用时刻
    result = receiver.advance_to(500.0)
    assert result["degraded_at_ms"] == pytest.approx(140.0)
    assert receiver.transitions[-1]["t_ms"] == pytest.approx(140.0)
    assert receiver.transitions[-1]["source"] == "clock"


def test_advance_to_never_recovers_in_degraded():
    receiver = d19.FrameReceiver()
    for index in range(5):
        receiver.feed(d19.arrival(index * d19.FRAME_PERIOD_MS, index, seq=index + 1))
    receiver.advance_to(180.0)
    assert receiver.state == "degraded"
    transitions = len(receiver.transitions)
    second = receiver.advance_to(400.0)
    assert second["degraded_at_ms"] is None
    assert receiver.state == "degraded"  # 恢复只能靠真实帧
    assert len(receiver.transitions) == transitions
    assert receiver.counts["clock_missing_slots"] == 16


def test_default_scenario_silent_tail_frozen(report):
    silent = report["silent_bus"]
    assert silent["case"] == "silent_bus_after_last_frame"
    assert silent["last_frame_ms"] == pytest.approx(660.0)
    assert silent["horizon_ms"] == pytest.approx(760.0)
    assert silent["deadline_ms"] == pytest.approx(720.0)
    assert silent["degrades_at_ms"] == pytest.approx(720.0)
    assert silent["clock_missing_slots"] == 5
    assert silent["state_at_horizon"] == "degraded"
    assert silent["accepted"] == 20
    assert silent["rejected"] == 7
    assert silent["published_updates"] == 20
    assert silent["last_trusted_soc_pp"] == pytest.approx(65.5)
    assert silent["frames_after_last"] == 0
    assert len(silent["transitions"]) == 1
    assert silent["transitions"][0]["source"] == "clock"
    assert silent["transitions"][0]["t_ms"] == pytest.approx(720.0)


def test_cli_horizon_ms(tmp_path):
    out = tmp_path / "h"
    assert d19.main(["--out", str(out), "--horizon-ms", "760"]) == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["replay"]["final_state"] == "degraded"
    assert report["replay"]["silent_degraded_at_ms"] == pytest.approx(720.0)
    assert report["replay"]["clock_missing_slots"] == 5
    default_out = tmp_path / "d"
    assert d19.main(["--out", str(default_out)]) == 0
    # 静默尾只影响状态与转移，逐帧判定行不变
    assert (out / "decisions.csv").read_text(encoding="utf-8") == (
        default_out / "decisions.csv"
    ).read_text(encoding="utf-8")
    # 视界早于末帧：拒绝
    assert d19.main(["--horizon-ms", "100"]) == 2
