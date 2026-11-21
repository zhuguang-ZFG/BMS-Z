"""Regression tests for the D19/D21 -> D22 upstream adapter.

The adapter translates upstream artifacts into D22 evaluation events:
D19 per-frame decision rows drive the ``stale_data`` monitor; D21 quarantine
rows and sequence-gap boundaries drive ``missing_slots``. It never fabricates
measurements the upstream did not make (pack voltage/current stay None).
"""
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bus"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "datachain"))

import d19_bus_data as d19
import d21_record_chain as d21
import d22_diagnostics as d22
import d22_upstream_adapter as adapter

HERE = Path(__file__).resolve().parent


def _write_events_csv(path: Path, events: list[dict]) -> Path:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=d22.EVENT_COLUMNS)
        writer.writeheader()
        for event in events:
            writer.writerow({column: event.get(column, "") for column in d22.EVENT_COLUMNS})
    return path


def _replay_scenario() -> dict:
    fresh = [d19.arrival(index * d19.FRAME_PERIOD_MS, index, seq=index + 1) for index in range(10)]
    replays = [
        d19.arrival(200.0, 7, seq=11),
        d19.arrival(220.0, 7, seq=12),
        d19.arrival(240.0, 7, seq=13),
    ]
    return d19.run_scenario(fresh + replays)


def test_decision_rows_map_to_stale_data_events():
    case = _replay_scenario()
    events = adapter.events_from_decision_rows(case["rows"])
    stale_events = [event for event in events if event["monitor"] == "stale_data"]
    slot_events = [event for event in events if event["monitor"] == "missing_slots"]
    # replay 剧本每行非 accept 即 stale reject，全部构成 stale_data 评估
    assert len(stale_events) == len(case["rows"])
    assert len(slot_events) == len(case["rows"])
    ok_false = sum(1 for event in stale_events if event["ok"] is False)
    assert ok_false == case["rejected"]
    assert [event["t_ms"] for event in events] == sorted(event["t_ms"] for event in events)


def test_decision_mapping_uses_explicit_monitor_fields():
    rows = [
        {"t_ms": 10, "decision": "accept", "reason": None, "stale_data": False, "missing_slots": 0, "counter": 1, "session": 1},
        {"t_ms": 20, "decision": "reject", "reason": "late", "stale_data": False, "missing_slots": 0, "counter": 2, "session": 1},
        {"t_ms": 25, "decision": "reject", "reason": "crc", "stale_data": False, "missing_slots": 0, "counter": 3, "session": 1},
        {"t_ms": 30, "decision": "resync_observation", "reason": "awaiting_consecutive", "stale_data": False, "missing_slots": 0, "counter": 4, "session": 1},
    ]
    events = adapter.events_from_decision_rows(rows)
    stale_events = [event for event in events if event["monitor"] == "stale_data"]
    # accept=通过；late=失败；crc 拒收与 resync 行不构成陈旧度评估
    assert [(event["t_ms"], event["ok"]) for event in stale_events] == [(10.0, True), (20.0, False)]
    slot_events = [event for event in events if event["monitor"] == "missing_slots"]
    assert len(slot_events) == 4


def test_decision_rows_reject_unknown_reason():
    rows = [{"t_ms": 10, "decision": "reject", "reason": "mystery", "stale_data": False, "missing_slots": 0, "counter": 1, "session": 1}]
    with pytest.raises(ValueError, match="unsupported reject reason"):
        adapter.events_from_decision_rows(rows)


def test_csv_string_cells_map_normal_rows_to_pass():
    # CSV 路径全部是字符串："False"/"0" 不是假值陷阱——正常行必须映射为通过
    rows = [
        {"t_ms": "10", "decision": "accept", "reason": "", "stale_data": "False", "missing_slots": "0", "counter": "1", "session": "1"},
        {"t_ms": "20", "decision": "reject", "reason": "late", "stale_data": "False", "missing_slots": "0", "counter": "2", "session": "1"},
        {"t_ms": "30", "decision": "accept", "reason": "", "stale_data": "True", "missing_slots": "2", "counter": "3", "session": "1"},
    ]
    events = adapter.events_from_decision_rows(rows)
    stale = [event for event in events if event["monitor"] == "stale_data"]
    slots = [event for event in events if event["monitor"] == "missing_slots"]
    assert [(event["t_ms"], event["ok"]) for event in stale] == [(10.0, True), (20.0, False), (30.0, False)]
    assert [event["ok"] for event in slots] == [True, True, False]


def test_csv_string_cells_reject_malformed():
    good = {"t_ms": "10", "decision": "accept", "reason": "", "stale_data": "False", "missing_slots": "0"}
    for field, bad in (("stale_data", "yes"), ("missing_slots", "-1"), ("missing_slots", "two"), ("missing_slots", "True")):
        row = dict(good, **{field: bad})
        with pytest.raises(ValueError, match=field):
            adapter.events_from_decision_rows([row])


def test_fresh_crc_reject_is_not_stale_data_failure():
    # 全新计数器但 CRC 坏的帧：integrity 拒收，stale_data=False——不许误报陈旧 DTC
    frames = [
        d19.arrival(0.0, 0, seq=1),
        d19.arrival(10.0, 1, seq=2, crc_rx=0xFFFF),
        d19.arrival(20.0, 2, seq=3),
    ]
    case = d19.run_scenario(frames)
    bad_row = case["rows"][1]
    assert bad_row["decision"] == "reject"
    assert bad_row["stale_data"] is False
    events = adapter.events_from_decision_rows(case["rows"])
    stale_events = [event for event in events if event["monitor"] == "stale_data"]
    assert all(event["ok"] is True for event in stale_events)
    assert len(stale_events) == 2  # 只有两条 accept 行构成陈旧度评估


def test_decision_rows_reject_malformed():
    with pytest.raises(ValueError, match="decision row"):
        adapter.events_from_decision_rows([{"t_ms": 10, "counter": 1}])
    with pytest.raises(ValueError, match="decision value"):
        adapter.events_from_decision_rows([{"t_ms": 10, "decision": "maybe", "stale_data": False, "missing_slots": 0, "counter": 1, "session": 1}])


def test_chain_report_maps_quarantine_and_sequence_gap():
    records = [
        {"source_id": "SRC05", "record_seq": 1, "t_ms": 100, "field": "pack_v", "raw_value": "51200", "unit": "mV", "quality": "ok"},
        {"source_id": "SRC05", "record_seq": 2, "t_ms": 120, "field": "pack_v", "raw_value": "51210", "unit": "mV", "quality": "ok"},
        {"source_id": "SRC05", "record_seq": 4, "t_ms": 160, "field": "pack_v", "raw_value": "51240", "unit": "mV", "quality": "invalid"},
        {"source_id": "SRC05", "record_seq": 5, "t_ms": 180, "field": "pack_v", "raw_value": "51250", "unit": "mV", "quality": "ok"},
    ]
    report = d21.build_report(records, source_sha="0" * 64)
    events = adapter.events_from_chain_report(report)
    assert {event["monitor"] for event in events} == {"missing_slots"}
    assert all(event["ok"] is False for event in events)
    # seq 2→4 缺口落在 seq4 行（t=160，同一条 invalid 记录）+ 该记录本身被隔离 = 两事件同刻不同因
    assert len(events) == 2
    assert [event["t_ms"] for event in events] == [160.0, 160.0]
    assert {event["_reason"] for event in events} == {"quarantine", "sequence_gap"}
    with pytest.raises(ValueError, match="chain report"):
        adapter.events_from_chain_report({"counts": {}})


def test_adapter_events_drive_d22_dtc_confirmation():
    decision_rows = [
        {"t_ms": t, "decision": "reject", "reason": "late", "stale_data": False, "missing_slots": 0, "counter": index, "session": 1}
        for index, t in enumerate((20.0, 40.0, 60.0), start=1)
    ]
    events = adapter.events_from_decision_rows(decision_rows)
    report = d22.build_report(events)
    dtcs = {row["monitor"]: row for row in report["dtcs"]}
    assert dtcs["stale_data"]["state"] == "active"
    assert dtcs["stale_data"]["confirmed_at_ms"] == 60.0
    # 冻结帧允许上游未提供的测量为 null，不许编造
    freeze = [f for f in report["freeze_frames"] if f["monitor"] == "stale_data"]
    assert freeze[0]["pack_v_mv"] is None
    assert freeze[0]["pack_current_a"] is None


def test_csv_roundtrip_through_d22_contract(tmp_path):
    rows = _replay_scenario()["rows"]
    events = adapter.events_from_decision_rows(rows)
    path = _write_events_csv(tmp_path / "events.csv", events)
    loaded = d22.load_events(path)
    assert len(loaded) == len(events)
    replay = d22.build_report(loaded)
    direct = d22.build_report(events)
    assert replay["counts"] == direct["counts"]


def test_adapter_cli_writes_d22_contract_csv(tmp_path):
    decisions = tmp_path / "decisions.csv"
    with open(decisions, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=d19.DECISION_COLUMNS)
        writer.writeheader()
        for row in _replay_scenario()["rows"]:
            writer.writerow(row)
    out = tmp_path / "events.csv"
    result = subprocess.run(
        [sys.executable, str(HERE / "d22_upstream_adapter.py"), "--decisions", str(decisions), "--out", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    loaded = d22.load_events(out)
    assert len(loaded) > 0
    assert {event["monitor"] for event in loaded} == {"stale_data", "missing_slots"}
    stale = [event for event in loaded if event["monitor"] == "stale_data"]
    assert sum(1 for event in stale if event["ok"] is False) == 3  # 3 条 late reject
    assert sum(1 for event in stale if event["ok"] is True) == 10  # 正常行全 pass，不许误报


def test_adapter_cli_rejects_bad_decisions_csv(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("junk\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(HERE / "d22_upstream_adapter.py"), "--decisions", str(bad)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "decisions" in result.stderr
