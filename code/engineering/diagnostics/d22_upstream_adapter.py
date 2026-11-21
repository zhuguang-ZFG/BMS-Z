"""D22 upstream adapter: translate D19 frame decisions and D21 record-chain
findings into D22 evaluation events.

Thin integration slice (declared boundaries, not end-to-end proof):

- ``events_from_decision_rows`` consumes D19 per-frame decision rows
  (``d19_bus_data.run_scenario(...)["rows"]`` or a decisions CSV with
  ``DECISION_COLUMNS``). Mapping is per monitor, by evidence class:
  ``stale_data`` ← accepted rows (pass), freshness-class rejections
  (``reason`` in ``late``/``duplicate``/``gap_too_large``/``ambiguous``), and
  age-timeout rows (explicit ``stale_data == True``); integrity/identity/
  session rejections (``identity``/``crc``/``session``) and
  ``resync_observation`` rows emit no ``stale_data`` event — they are not
  staleness evaluations (``axis_boundary = integrity_rejection_is_not_staleness``).
  Unknown reasons are contract violations. ``missing_slots`` ← the row's
  explicit ``missing_slots`` count (nonzero = fail). Allowed decision values
  are exactly D19's: accept / reject / resync_observation.
- ``events_from_chain_report`` consumes a D21 ``build_report`` dict.
  Quarantined rows and sequence-gap boundaries (re-derived from
  normalized + quarantined rows, the same data D21 used) each become one
  ``missing_slots`` ``ok=False`` event at that row's ``t_ms``. D21's
  ``time_gaps_ms`` summary is NOT consumed: it carries intervals without
  absolute timestamps (``axis_boundary = gap_intervals_without_absolute_time``).
- Measurements the upstream did not make stay ``None``; the adapter never
  fabricates pack voltage/current for freeze frames.

Everything else about D22 (debounce counts, FAULT latch, flash gating) is
unchanged and still owned by ``d22_diagnostics.py``.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

DECISION_VALUES = ("accept", "reject", "resync_observation")
# D19 classify_counter 的新鲜度拒收类别；identity/crc/session 属完整性/身份/会话，不构成陈旧度评估
FRESHNESS_REASONS = ("late", "duplicate", "gap_too_large", "ambiguous")
NON_STALENESS_REASONS = ("identity", "crc", "session")

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

REQUIRED_DECISION_FIELDS = ("t_ms", "decision", "stale_data", "missing_slots")


def _strict_bool(value: object, field: str, row: dict) -> bool:
    """D19 stale_data 是 bool；CSV 路径给字符串，只认字面 True/False。"""
    if isinstance(value, bool):
        return value
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"{field} must be True/False, got {value!r}: {row}")


def _strict_count(value: object, field: str, row: dict) -> int:
    """D19 missing_slots 是非负整数；CSV 路径给字符串，负值与畸形一律拒绝。"""
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a non-negative int, got {value!r}: {row}")
    try:
        count = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a non-negative int, got {value!r}: {row}") from exc
    if count < 0:
        raise ValueError(f"{field} must be a non-negative int, got {value!r}: {row}")
    return count


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def events_from_decision_rows(rows: list[dict]) -> list[dict]:
    """D19 decision rows -> ``stale_data`` / ``missing_slots`` evaluation events."""
    events: list[dict] = []
    for row in rows:
        missing = [field for field in REQUIRED_DECISION_FIELDS if field not in row]
        if missing:
            raise ValueError(f"decision row missing {missing}: {row}")
        decision = str(row["decision"])
        if decision not in DECISION_VALUES:
            raise ValueError(f"decision value {decision!r} not in {DECISION_VALUES}: {row}")

        def base(source: dict, monitor: str, ok: bool) -> dict:
            return {
                "t_ms": float(source["t_ms"]),
                "monitor": monitor,
                "ok": ok,
                "soc_pp": _optional_float(source.get("soc_pp")),
                "pack_v_mv": None,
                "pack_current_a": None,
                "counter": _optional_int(source.get("counter")),
                "session": _optional_int(source.get("session")),
                "image_gen": None,
            }

        # 陈旧度证据按类别分派：accept=通过；新鲜度拒收或老化超时=失败；
        # 完整性/身份/会话与重同步行不是陈旧度评估，跳过；未知 reason 拒绝
        stale_flag = _strict_bool(row["stale_data"], "stale_data", row)
        missing_count = _strict_count(row["missing_slots"], "missing_slots", row)
        reason = row.get("reason")
        if decision == "accept":
            events.append(base(row, "stale_data", not stale_flag))
        elif stale_flag or reason in FRESHNESS_REASONS:
            events.append(base(row, "stale_data", False))
        elif reason in NON_STALENESS_REASONS or decision == "resync_observation":
            pass
        else:
            raise ValueError(f"unsupported reject reason {reason!r}: {row}")
        events.append(base(row, "missing_slots", missing_count == 0))
    events.sort(key=lambda event: (float(event["t_ms"]), str(event["monitor"])))
    return events


def events_from_chain_report(report: dict) -> list[dict]:
    """D21 build_report dict -> ``missing_slots`` evaluation events."""
    try:
        quarantine = report["quarantine"]
        normalized = report["normalized_records"]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"chain report missing quarantine/normalized_records: {exc}") from exc
    events: list[dict] = []

    def missing_event(row: dict, reason: str) -> dict:
        return {
            "t_ms": float(row["t_ms"]),
            "monitor": "missing_slots",
            "ok": False,
            "soc_pp": None,
            "pack_v_mv": None,
            "pack_current_a": None,
            "counter": _optional_int(row.get("record_seq")),
            "session": None,
            "image_gen": None,
            "_reason": reason,
        }

    for row in quarantine:
        events.append(missing_event(row, "quarantine"))
    rows_by_source: dict[str, list[dict]] = {}
    for row in list(normalized) + list(quarantine):
        rows_by_source.setdefault(str(row["source_id"]), []).append(row)
    for rows in rows_by_source.values():
        rows.sort(key=lambda item: int(item["record_seq"]))
        previous = None
        for row in rows:
            if previous is not None and int(row["record_seq"]) - int(previous["record_seq"]) > 1:
                events.append(missing_event(row, "sequence_gap"))
            previous = row
    events.sort(key=lambda event: (event["t_ms"], event["monitor"], event["_reason"]))
    return events


def merge_events(*streams: list[dict]) -> list[dict]:
    """Deterministic merge across upstream streams: t_ms, then monitor."""
    merged = [event for stream in streams for event in stream]
    merged.sort(key=lambda event: (float(event["t_ms"]), str(event["monitor"])))
    return merged


def write_events_csv(events: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EVENT_COLUMNS)
        writer.writeheader()
        for event in events:
            writer.writerow({column: event.get(column, "") for column in EVENT_COLUMNS})


def load_decisions_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "decision" not in reader.fieldnames:
            raise ValueError(f"decisions header must include a decision column, got {reader.fieldnames}")
        return list(reader)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions", type=Path, help="D19 decisions CSV (DECISION_COLUMNS)")
    parser.add_argument("--out", type=Path, help="write D22 events CSV (nine-column contract)")
    args = parser.parse_args(argv)
    try:
        events: list[dict] = []
        if args.decisions:
            events.extend(events_from_decision_rows(load_decisions_csv(args.decisions)))
        events = merge_events(events)
        if args.out:
            write_events_csv(events, args.out)
        else:
            print(f"{len(events)} events")
    except (OSError, ValueError) as exc:
        print(f"d22_upstream_adapter: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
