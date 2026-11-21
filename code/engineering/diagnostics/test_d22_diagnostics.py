"""D22 diagnostics: DTC debounce, freeze frame, flashing session, and lifecycle."""

import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d22_diagnostics", HERE / "d22_diagnostics.py")
assert spec is not None and spec.loader is not None
d22 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d22
spec.loader.exec_module(d22)


def _write_events(path: Path, rows: list[dict[str, object]]) -> Path:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=d22.EVENT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_default_scenario_lifecycle_and_dtcs_frozen():
    report = d22.build_report(d22.default_events())

    assert report["scenario_id"] == d22.SCENARIO_ID
    assert report["self_test"] == "pass"

    dtcs = {row["monitor"]: row for row in report["dtcs"]}
    assert dtcs["stale_data"]["state"] == "cleared"
    assert dtcs["stale_data"]["confirmed_at_ms"] == 60.0
    assert dtcs["missing_slots"]["state"] == "cleared"
    assert dtcs["missing_slots"]["confirmed_at_ms"] == 120.0

    # 冻结帧钉在确认当次评估
    freeze = {row["monitor"]: row for row in report["freeze_frames"]}
    assert freeze["stale_data"]["t_ms"] == 60.0
    assert freeze["stale_data"]["soc_pp"] == pytest.approx(61.0)
    assert freeze["missing_slots"]["t_ms"] == 120.0

    transitions = [(t["t_ms"], t["from"], t["to"]) for t in report["lifecycle"]["transitions"]]
    assert (60.0, "NORMAL", "DEGRADED") in transitions
    assert (120.0, "DEGRADED", "FAULT") in transitions
    assert (240.0, "FAULT", "DEGRADED") in transitions
    assert (340.0, "DEGRADED", "NORMAL") in transitions
    assert report["lifecycle"]["final_state"] == "NORMAL"


def test_debounce_counts_are_evaluations_not_frames():
    report = d22.build_report(d22.default_events())
    dtcs = {row["monitor"]: row for row in report["dtcs"]}
    assert dtcs["stale_data"]["confirm_evals"] == 3
    assert dtcs["stale_data"]["heal_evals"] == 5
    assert dtcs["missing_slots"]["confirm_evals"] == 3
    # D19 的恢复拍数不能拿来当 D22 的去抖语义
    assert report["axis_boundary"] == "evaluation_count_not_frame_count"


def test_safety_dtc_fault_latch_requires_service_clear():
    events = [dict(e) for e in d22.default_events()]
    events = [e for e in events if e["monitor"] != "stale_data"]
    report = d22.build_report(events)
    dtcs = {row["monitor"]: row for row in report["dtcs"]}
    assert dtcs["missing_slots"]["state"] == "cleared"
    assert report["lifecycle"]["final_state"] == "NORMAL"


def test_programming_exit_from_fault_preserves_latch():
    # FAULT 锁存的机器可以进刷写维修，但退出必须回到 FAULT，不许借刷写绕行 NORMAL
    events = [e for e in d22.default_events() if float(e["t_ms"]) <= 120.0]
    events.append({"t_ms": 400.0, "monitor": "__programming_enter__", "ok": True, "soc_pp": 61.6, "pack_v_mv": 51360.0, "pack_current_a": 12500.0, "counter": 6, "session": 1, "image_gen": None})
    events.append({"t_ms": 410.0, "monitor": "__flash__", "ok": True, "soc_pp": 61.6, "pack_v_mv": 51360.0, "pack_current_a": 12500.0, "counter": 6, "session": 1, "image_gen": 42})
    events.append({"t_ms": 420.0, "monitor": "__programming_exit__", "ok": True, "soc_pp": 61.6, "pack_v_mv": 51360.0, "pack_current_a": 12500.0, "counter": 6, "session": 1, "image_gen": None})
    report = d22.build_report(events)
    assert report["lifecycle"]["final_state"] == "FAULT"
    transitions = [(t["t_ms"], t["from"], t["to"]) for t in report["lifecycle"]["transitions"]]
    assert (400.0, "FAULT", "PROGRAMMING") in transitions
    assert (420.0, "PROGRAMMING", "FAULT") in transitions
    dtcs = {row["monitor"]: row for row in report["dtcs"]}
    assert dtcs["missing_slots"]["state"] == "active"


def test_flash_rules_session_and_gen_range():
    assert d22.flash("NORMAL", 42, stored_gen=41, supported=(41, 42))["accepted"] is False
    assert d22.flash("PROGRAMMING", 43, stored_gen=41, supported=(41, 42))["accepted"] is False
    ok = d22.flash("PROGRAMMING", 42, stored_gen=41, supported=(41, 42))
    assert ok["accepted"] is True
    assert ok["stored_gen_after"] == 42


def test_self_test_failure_uses_defaults():
    report = d22.build_report(d22.default_events(), storage_crc_ok=False)
    assert report["self_test"] == "defaults"
    assert report["stored_gen"] == 0


def test_rejects_unknown_monitor_and_bad_event(tmp_path):
    bad = d22.default_events()
    bad[0]["monitor"] = "mystery"
    with pytest.raises(ValueError, match="monitor"):
        d22.build_report(bad)

    path = _write_events(tmp_path / "events.csv", d22.default_events())
    text = path.read_text(encoding="utf-8").replace("t_ms,monitor", "t,m", 1)
    broken = tmp_path / "broken.csv"
    broken.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="header"):
        d22.load_events(broken)

    rolled = [dict(e) for e in d22.default_events()]
    rolled[3]["t_ms"] = 10.0
    with pytest.raises(ValueError, match="time rollback"):
        d22.build_report(rolled)

    quiet = [
        {"t_ms": 20.0, "monitor": "stale_data", "ok": False},
        {"t_ms": 40.0, "monitor": "stale_data", "ok": False},
        {"t_ms": 30.0, "monitor": "stale_data", "ok": False},
    ]
    with pytest.raises(ValueError, match="time rollback"):
        d22.build_report(quiet)


def test_cli_default_export_and_replay_counts(tmp_path):
    out = tmp_path / "out"
    assert d22.main(["--out", str(out)]) == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    for name in ("events.csv", "dtcs.csv", "lifecycle_log.csv", "freeze_frames.csv"):
        assert (out / name).is_file(), name

    assert d22.main(["--events", str(out / "events.csv"), "--out", str(tmp_path / "replay")]) == 0
    replay = json.loads((tmp_path / "replay" / "report.json").read_text(encoding="utf-8"))
    assert replay["counts"] == report["counts"]


def test_cli_bad_events_exit_2(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("junk\n", encoding="utf-8")
    assert d22.main(["--events", str(bad)]) == 2


def test_dtc_recurrence_reconfirms_after_heal():
    # 清零后再度失败必须重新确认：治愈不是免疫证明
    events = [e for e in d22.default_events() if float(e["t_ms"]) <= 220.0]
    events += [
        {"t_ms": 260.0, "monitor": "stale_data", "ok": False, "soc_pp": 62.0, "pack_v_mv": 51400.0, "pack_current_a": 12600.0, "counter": 20, "session": 1, "image_gen": None},
        {"t_ms": 280.0, "monitor": "stale_data", "ok": False, "soc_pp": 62.1, "pack_v_mv": 51410.0, "pack_current_a": 12610.0, "counter": 21, "session": 1, "image_gen": None},
        {"t_ms": 300.0, "monitor": "stale_data", "ok": False, "soc_pp": 62.2, "pack_v_mv": 51420.0, "pack_current_a": 12620.0, "counter": 22, "session": 1, "image_gen": None},
    ]
    report = d22.build_report(events)
    dtcs = {row["monitor"]: row for row in report["dtcs"]}
    assert dtcs["stale_data"]["state"] == "active"
    assert dtcs["stale_data"]["confirmed_at_ms"] == 300.0
    stale_freezes = [f for f in report["freeze_frames"] if f["monitor"] == "stale_data"]
    assert len(stale_freezes) == 2  # 冻结帧是历史：两次确认各留一帧，旧帧不被改写
    assert stale_freezes[-1]["t_ms"] == 300.0


def test_fault_persists_without_service_clear():
    # 没有 service_clear：安全 DTC 即使治愈，FAULT 也不解锁——钥匙只有一把
    events = [e for e in d22.default_events() if e["monitor"] != "__service_clear__"]
    report = d22.build_report(events)
    assert report["lifecycle"]["final_state"] == "FAULT"
    dtcs = {row["monitor"]: row for row in report["dtcs"]}
    assert dtcs["missing_slots"]["state"] == "cleared"


def test_load_events_rejects_bad_ok_cell(tmp_path):
    rows = d22.default_events()
    path = tmp_path / "events.csv"
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=d22.EVENT_COLUMNS)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            if out["t_ms"] == 20.0:
                out["ok"] = "yes"  # 非 True/False 一律拒绝，不许静默当失败
            writer.writerow(out)
    with pytest.raises(ValueError, match="ok"):
        d22.load_events(path)


def test_flash_event_requires_image_gen():
    # 普通事件的可选列可空，但 FLASH 的 image_gen 是动作参数：空 = 合同违例，不许 TypeError
    events = [
        {"t_ms": 10.0, "monitor": "__programming_enter__", "ok": True},
        {"t_ms": 20.0, "monitor": "__flash__", "ok": True, "image_gen": None},
    ]
    with pytest.raises(ValueError, match="flash event requires image_gen"):
        d22.build_report(events)
