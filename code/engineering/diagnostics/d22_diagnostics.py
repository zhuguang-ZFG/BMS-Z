#!/usr/bin/env python3
"""D22 diagnostics, flashing, and lifecycle: DTC debounce is per-evaluation
fault confirmation — deliberately not the D19 frame-recovery count semantics."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

SCENARIO_ID = "D22-dtc-lifecycle"
AXIS_BOUNDARY = "evaluation_count_not_frame_count"

EVENT_COLUMNS = [
    "t_ms",
    "monitor",
    "ok",
    "soc_pp",
    "pack_v_mv",
    "pack_current_a",
    "counter",
    "session",
    "image_gen",
]

MONITOR_CONFIG: dict[str, dict[str, object]] = {
    "stale_data": {"confirm": 3, "heal": 5, "cls": "quality"},
    "missing_slots": {"confirm": 3, "heal": 5, "cls": "safety"},
}

SUPPORTED_GEN_RANGE = (41, 42)
SERVICE_CLEAR = "__service_clear__"
PROGRAMMING_ENTER = "__programming_enter__"
PROGRAMMING_EXIT = "__programming_exit__"
FLASH = "__flash__"
SPECIAL_MONITORS = {SERVICE_CLEAR, PROGRAMMING_ENTER, PROGRAMMING_EXIT, FLASH}


def default_events() -> list[dict[str, object]]:
    """Deterministic evaluation stream: quality DTC confirms, safety DTC
    latches FAULT, service clear + heals walk the lifecycle back to NORMAL,
    then a programming session flashes gen 42."""

    def ev(t, monitor, ok, soc, mv, ma, counter, session=1, image_gen=None):
        return {
            "t_ms": float(t),
            "monitor": monitor,
            "ok": ok,
            "soc_pp": float(soc),
            "pack_v_mv": float(mv),
            "pack_current_a": float(ma),
            "counter": counter,
            "session": session,
            "image_gen": image_gen,
        }

    rows: list[dict[str, object]] = []
    rows += [
        ev(20, "stale_data", False, 60.5, 51250, 12000, 1),
        ev(40, "stale_data", False, 60.8, 51280, 12100, 2),
        ev(60, "stale_data", False, 61.0, 51300, 12200, 3),
    ]
    rows += [
        ev(80, "missing_slots", False, 61.2, 51320, 12300, 4),
        ev(100, "missing_slots", False, 61.4, 51340, 12400, 5),
        ev(120, "missing_slots", False, 61.6, 51360, 12500, 6),
    ]
    rows += [ev(t, "stale_data", True, 61.8 + i * 0.1, 51380, 12600, 7 + i) for i, t in enumerate((140, 160, 180, 200, 220))]
    rows.append(ev(240, SERVICE_CLEAR, True, 62.5, 51400, 12700, 12))
    rows += [ev(t, "missing_slots", True, 62.8 + i * 0.1, 51420, 12800, 13 + i) for i, t in enumerate((260, 280, 300, 320, 340))]
    rows.append(ev(360, PROGRAMMING_ENTER, True, 63.5, 51450, 12900, 18))
    rows.append(ev(370, FLASH, True, 63.5, 51450, 12900, 18, image_gen=42))
    rows.append(ev(380, PROGRAMMING_EXIT, True, 63.6, 51460, 12910, 18))
    return rows


def load_events(path: Path) -> list[dict[str, object]]:
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != EVENT_COLUMNS:
            raise ValueError(f"events header must be {EVENT_COLUMNS}")
        rows = []
        for raw in reader:
            try:
                t_ms = float(raw["t_ms"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"bad event row: {raw}") from exc
            ok_raw = raw["ok"]
            if ok_raw not in ("True", "False"):
                raise ValueError(f"bad ok cell: {ok_raw!r} (must be exactly True or False)")
            ok = ok_raw == "True"
            # 可选列允许空单元格 = 上游未提供；绝不编造测量值
            def _opt_float(cell: object) -> float | None:
                return float(cell) if cell not in (None, "") else None

            def _opt_int(cell: object) -> int | None:
                return int(cell) if cell not in (None, "") else None

            rows.append(
                {
                    "t_ms": t_ms,
                    "monitor": raw["monitor"],
                    "ok": ok,
                    "soc_pp": _opt_float(raw.get("soc_pp")),
                    "pack_v_mv": _opt_float(raw.get("pack_v_mv")),
                    "pack_current_a": _opt_float(raw.get("pack_current_a")),
                    "counter": _opt_int(raw.get("counter")),
                    "session": _opt_int(raw.get("session")),
                    "image_gen": _opt_int(raw.get("image_gen")),
                }
            )
        return rows


def flash(session: str, image_gen: int, *, stored_gen: int, supported: tuple[int, int]) -> dict[str, object]:
    if session != "PROGRAMMING":
        return {"accepted": False, "reason": "session", "stored_gen_after": stored_gen}
    if not (supported[0] <= image_gen <= supported[1]):
        return {"accepted": False, "reason": "range", "stored_gen_after": stored_gen}
    return {"accepted": True, "reason": "", "stored_gen_after": image_gen}


def _new_monitor(name: str) -> dict[str, object]:
    cfg = MONITOR_CONFIG[name]
    return {
        "monitor": name,
        "cls": cfg["cls"],
        "state": "pending",
        "fail_count": 0,
        "pass_count": 0,
        "confirm_evals": cfg["confirm"],
        "heal_evals": cfg["heal"],
        "confirmed_at_ms": None,
        "healed_at_ms": None,
        "freeze_frame": None,
    }


def build_report(events: list[dict[str, object]], *, storage_crc_ok: bool = True) -> dict[str, object]:
    for event in events:
        monitor = str(event["monitor"])
        if monitor not in MONITOR_CONFIG and monitor not in SPECIAL_MONITORS:
            raise ValueError(f"unknown monitor: {monitor}")

    self_test = "pass" if storage_crc_ok else "defaults"
    stored_gen = 41 if storage_crc_ok else 0

    monitors = {name: _new_monitor(name) for name in MONITOR_CONFIG}
    transitions: list[dict[str, object]] = []
    freeze_frames: list[dict[str, object]] = []
    flash_result: dict[str, object] = {"requested": False, "accepted": False, "reason": "not_requested", "stored_gen_after": stored_gen}

    state = "INIT"
    stored = {"gen": stored_gen}
    programming_return = "NORMAL"

    def move(t_ms: float, to: str, trigger: str) -> None:
        nonlocal state
        transitions.append({"t_ms": t_ms, "from": state, "to": to, "trigger": trigger})
        state = to

    if storage_crc_ok:
        move(0.0, "NORMAL", "self_test_pass")
    else:
        move(0.0, "NORMAL", "self_test_defaults")

    session = "NORMAL"

    def active_quality() -> bool:
        return any(
            m["cls"] == "quality" and m["state"] in ("active", "healing") for m in monitors.values()
        )

    def active_safety() -> bool:
        return any(
            m["cls"] == "safety" and m["state"] in ("active", "healing") for m in monitors.values()
        )

    previous_event_t_ms: float | None = None
    for event in events:
        t_ms = float(event["t_ms"])
        monitor = str(event["monitor"])
        ok = bool(event["ok"])
        if previous_event_t_ms is not None and t_ms < previous_event_t_ms:
            raise ValueError(f"time rollback: t_ms {t_ms} after {previous_event_t_ms}")
        previous_event_t_ms = t_ms

        if monitor == SERVICE_CLEAR:
            if state == "FAULT":
                move(t_ms, "DEGRADED", "service_clear")
            for m in monitors.values():
                if m["cls"] == "safety" and m["state"] in ("active", "healing"):
                    m["state"] = "healing"
                    m["pass_count"] = 0
            continue
        if monitor == PROGRAMMING_ENTER:
            if state in ("NORMAL", "FAULT"):
                programming_return = state
                move(t_ms, "PROGRAMMING", "programming_request")
                session = "PROGRAMMING"
            continue
        if monitor == PROGRAMMING_EXIT:
            if state == "PROGRAMMING":
                # 退出回到进入前状态：FAULT 锁存不解，刷写不许当绕行通道
                move(t_ms, programming_return, "programming_exit_self_test_pass")
                session = "NORMAL"
            continue
        if monitor == FLASH:
            image_gen = event.get("image_gen")
            if image_gen is None:
                raise ValueError(f"flash event requires image_gen: {event}")
            if self_test != "pass":
                flash_result = {"requested": True, "accepted": False, "reason": "self_test", "stored_gen_after": stored["gen"]}
                continue
            flash_result = dict(
                flash(session, int(image_gen), stored_gen=stored["gen"], supported=SUPPORTED_GEN_RANGE)
            )
            flash_result["requested"] = True
            if flash_result["accepted"]:
                stored["gen"] = int(flash_result["stored_gen_after"])
            continue

        m = monitors[monitor]
        cfg = MONITOR_CONFIG[monitor]
        if ok:
            m["pass_count"] = int(m["pass_count"]) + 1  # type: ignore[arg-type]
            m["fail_count"] = 0
            if m["state"] in ("pending", "active", "healing"):
                if int(m["pass_count"]) >= int(cfg["heal"]):
                    m["state"] = "cleared"
                    m["healed_at_ms"] = t_ms
                    if state == "DEGRADED" and not active_quality() and not active_safety():
                        move(t_ms, "NORMAL", f"{monitor}_healed")
        else:
            m["fail_count"] = int(m["fail_count"]) + 1  # type: ignore[arg-type]
            m["pass_count"] = 0
            if m["state"] in ("pending", "healing", "cleared"):
                if int(m["fail_count"]) >= int(cfg["confirm"]):
                    m["state"] = "active"
                    m["confirmed_at_ms"] = t_ms
                    frame = {
                        "monitor": monitor,
                        "t_ms": t_ms,
                        "soc_pp": event["soc_pp"],
                        "pack_v_mv": event["pack_v_mv"],
                        "pack_current_a": event["pack_current_a"],
                        "counter": event["counter"],
                        "session": event["session"],
                    }
                    m["freeze_frame"] = frame
                    freeze_frames.append(frame)
                    if m["cls"] == "safety":
                        if state != "FAULT":
                            move(t_ms, "FAULT", f"{monitor}_confirmed")
                    elif state == "NORMAL":
                        move(t_ms, "DEGRADED", f"{monitor}_confirmed")

    dtcs = [
        {
            "monitor": name,
            "cls": m["cls"],
            "state": m["state"],
            "confirm_evals": m["confirm_evals"],
            "heal_evals": m["heal_evals"],
            "confirmed_at_ms": m["confirmed_at_ms"],
            "healed_at_ms": m["healed_at_ms"],
        }
        for name, m in monitors.items()
    ]
    counts = {
        "events": len(events),
        "dtcs": len(dtcs),
        "dtcs_confirmed": sum(1 for m in monitors.values() if m["confirmed_at_ms"] is not None),
        "dtcs_cleared": sum(1 for m in monitors.values() if m["state"] == "cleared"),
        "freeze_frames": len(freeze_frames),
        "lifecycle_transitions": len(transitions),
    }
    return {
        "scenario_id": SCENARIO_ID,
        "self_test": self_test,
        "stored_gen": stored["gen"],
        "axis_boundary": AXIS_BOUNDARY,
        "dtcs": dtcs,
        "freeze_frames": freeze_frames,
        "lifecycle": {"transitions": transitions, "final_state": state},
        "flash": flash_result,
        "counts": counts,
        "boundary": (
            "合成诊断教学切片：DTC 去抖按评估次数记账，冻结帧取确认当次；"
            "不复用 D19 恢复拍数、不证明真实 UDS/刷写或 HIL 验收。"
        ),
    }


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_artifacts(report: dict[str, object], events: list[dict[str, object]], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    _write_csv(out / "events.csv", EVENT_COLUMNS, events)
    _write_csv(
        out / "dtcs.csv",
        ["monitor", "cls", "state", "confirm_evals", "heal_evals", "confirmed_at_ms", "healed_at_ms"],
        report["dtcs"],  # type: ignore[arg-type]
    )
    _write_csv(
        out / "lifecycle_log.csv",
        ["t_ms", "from", "to", "trigger"],
        report["lifecycle"]["transitions"],  # type: ignore[index]
    )
    _write_csv(out / "freeze_frames.csv", ["monitor", "t_ms", "soc_pp", "pack_v_mv", "pack_current_a", "counter", "session"], report["freeze_frames"])  # type: ignore[arg-type]
    (out / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, help="evaluation CSV; default uses the built-in synthetic script")
    parser.add_argument("--out", type=Path, help="write report.json, events.csv, dtcs.csv, lifecycle_log.csv, freeze_frames.csv")
    args = parser.parse_args(argv)
    try:
        events = load_events(args.events) if args.events else default_events()
        report = build_report(events)
        if args.out:
            write_artifacts(report, events, args.out)
        else:
            print(json.dumps(report["counts"], ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(f"d22_diagnostics: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
