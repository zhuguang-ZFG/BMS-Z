"""Teaching experiments for D21: record identity, unit transform, time alignment, and replay lineage.

This is the first implementable slice of D21.  It deliberately stays on the
engineering desk: every accepted record carries source identity, sequence,
time, unit, quality, and a lineage entry; every derived value is transformable
back to a raw record.  The numbers are synthetic teaching values, not device
logs, bus captures, or hardware evidence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any

SCENARIO_ID = "D21-record-chain"
REPLAY_SCENARIO_ID = "D21-record-replay"

RECORD_COLUMNS = [
    "source_id",
    "record_seq",
    "t_ms",
    "field",
    "raw_value",
    "unit",
    "quality",
]
QUALITIES = ("ok", "degraded", "invalid")
GRID_STEP_MS = 20.0
STALE_BUDGET_MS = 100.0

# Field-level contracts are the unit firewall: a current cannot sneak through
# a voltage unit, and a value that is plausible before scaling but absurd after
# scaling is rejected instead of being clamped into a fake valid point.
FIELD_CONTRACTS: dict[str, dict[str, Any]] = {
    "pack_v": {
        "canonical_unit": "V",
        "units": {"mV": 0.001, "V": 1.0},
        "bounds": (0.0, 1000.0),
    },
    "pack_current_a": {
        "canonical_unit": "A",
        "units": {"mA": 0.001, "dA": 0.1, "A": 1.0},
        "bounds": (-1000.0, 1000.0),
    },
    "pack_temp_c": {
        "canonical_unit": "degC",
        "units": {"c10": 0.1, "degC": 1.0},
        "bounds": (-40.0, 125.0),
    },
    "soc": {
        "canonical_unit": "fraction",
        "units": {"pp": 0.0001, "percent": 0.01, "fraction": 1.0},
        "bounds": (0.0, 1.0),
    },
    "epoch": {
        "canonical_unit": "epoch",
        "units": {"epoch": 1.0},
        "bounds": (0.0, 65535.0),
    },
}

NORMALIZED_COLUMNS = [
    "source_id",
    "record_seq",
    "t_ms",
    "field",
    "raw_value",
    "unit",
    "quality",
    "canonical_unit",
    "value",
    "quarantine_reason",
]
ALIGNED_COLUMNS = [
    "t_ms",
    "field",
    "value",
    "canonical_unit",
    "source_id",
    "source_seq",
    "source_t_ms",
    "age_ms",
    "quality",
    "deliverable",
]


def _finite_float(value: object, name: str) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _positive_int(value: object, name: str) -> int:
    try:
        number = int(str(value), 10)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if number < 0:
        raise ValueError(f"{name} must be non-negative")
    return number


def _text(value: object, name: str) -> str:
    if value is None:
        raise ValueError(f"{name} is required")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} is required")
    return text


def config_fingerprint() -> str:
    canonical = json.dumps(FIELD_CONTRACTS, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def default_records() -> list[dict[str, object]]:
    """Deterministic heterogeneous records: AFE frame fields, estimator output, and firmware epoch."""

    def row(source: str, seq: int, t_ms: float, field: str, raw: float, unit: str, quality: str = "ok") -> dict[str, object]:
        return {
            "source_id": source,
            "record_seq": seq,
            "t_ms": t_ms,
            "field": field,
            "raw_value": raw,
            "unit": unit,
            "quality": quality,
        }

    return [
        row("afe", 1, 0.0, "pack_v", 51200.0, "mV"),
        row("afe", 2, 20.0, "pack_v", 51300.0, "mV"),
        row("afe", 3, 40.0, "pack_current_a", 120.0, "dA"),
        row("afe", 4, 60.0, "soc", 6050.0, "pp", "degraded"),
        row("afe", 5, 200.0, "soc", 6100.0, "pp"),
        row("estimator", 1, 10.0, "soc", 6000.0, "pp"),
        row("estimator", 2, 30.0, "soc", 6010.0, "pp"),
        row("estimator", 3, 130.0, "soc", 6090.0, "pp", "invalid"),
        row("firmware", 1, 5.0, "epoch", 41.0, "epoch"),
        row("firmware", 2, 15.0, "epoch", 42.0, "epoch"),
        row("firmware", 3, 115.0, "epoch", 43.0, "epoch"),
    ]


def load_records(path: Path) -> list[dict[str, object]]:
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        missing = [column for column in RECORD_COLUMNS if column not in fieldnames]
        if missing:
            raise ValueError(f"missing required columns {missing}")
        rows: list[dict[str, object]] = []
        for lineno, row in enumerate(reader, start=2):
            if row.get(None):
                raise ValueError(f"line {lineno}: malformed column count")
            rows.append({column: row.get(column) for column in RECORD_COLUMNS})
    if not rows:
        raise ValueError("at least one record is required")
    return rows


def _normalize(records: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    normalized: list[dict[str, object]] = []
    quarantine: list[dict[str, object]] = []
    last_seq_by_source: dict[str, int] = {}
    last_t_by_source: dict[str, float] = {}

    for index, raw in enumerate(records, start=1):
        source = _text(raw.get("source_id"), "source_id")
        seq = _positive_int(raw.get("record_seq"), "record_seq")
        t_ms = _finite_float(raw.get("t_ms"), "t_ms")
        field = _text(raw.get("field"), "field")
        unit = _text(raw.get("unit"), "unit")
        quality = _text(raw.get("quality"), "quality")

        if t_ms < 0.0:
            raise ValueError("t_ms must be non-negative")
        if source in last_seq_by_source:
            if seq <= last_seq_by_source[source]:
                raise ValueError(f"record_seq must strictly increase per source at raw row {index}")
            if t_ms <= last_t_by_source[source]:
                raise ValueError(f"time rollback within source {source} at raw row {index}")
        last_seq_by_source[source] = seq
        last_t_by_source[source] = t_ms

        contract = FIELD_CONTRACTS.get(field)
        if contract is None:
            raise ValueError(f"unknown field {field} at raw row {index}")
        unit_scale = contract["units"].get(unit)
        if unit_scale is None:
            allowed = ", ".join(sorted(contract["units"]))
            raise ValueError(f"unit {unit} not allowed for field {field}; allowed: {allowed}")
        raw_value = _finite_float(raw.get("raw_value"), "raw_value")
        value = raw_value * float(unit_scale)
        low, high = contract["bounds"]
        if not (low <= value <= high):
            raise ValueError(
                f"transformed {field} value {value:g} {contract['canonical_unit']} outside range [{low:g}, {high:g}]"
            )
        if quality not in QUALITIES:
            raise ValueError(f"unknown quality {quality} at raw row {index}")

        record = {
            "source_id": source,
            "record_seq": seq,
            "t_ms": t_ms,
            "field": field,
            "raw_value": raw_value,
            "unit": unit,
            "quality": quality,
            "canonical_unit": contract["canonical_unit"],
            "value": value,
            "quarantine_reason": "",
        }
        if quality == "invalid":
            record["quarantine_reason"] = "invalid quality: retained for audit, excluded from alignment"
            quarantine.append(record)
        else:
            normalized.append(record)
    return normalized, quarantine


def _alignment_rows(normalized: list[dict[str, object]], grid_step_ms: float, stale_budget_ms: float) -> list[dict[str, object]]:
    if grid_step_ms <= 0.0:
        raise ValueError("grid_step_ms must be positive")
    if stale_budget_ms < 0.0:
        raise ValueError("stale_budget_ms must be non-negative")
    if not normalized:
        return []

    horizon = math.ceil(max(float(row["t_ms"]) for row in normalized) / grid_step_ms) * grid_step_ms
    by_field: dict[str, list[dict[str, object]]] = {}
    for row in normalized:
        by_field.setdefault(str(row["field"]), []).append(row)

    aligned: list[dict[str, object]] = []
    grid = 0.0
    while grid <= horizon + 1e-9:
        for field, rows in sorted(by_field.items()):
            candidates = [row for row in rows if float(row["t_ms"]) <= grid + 1e-9]
            if not candidates:
                continue
            latest = max(candidates, key=lambda row: (float(row["t_ms"]), int(row["record_seq"])))
            age_ms = grid - float(latest["t_ms"])
            quality = str(latest["quality"])
            deliverable = quality == "ok" and age_ms <= stale_budget_ms
            aligned.append(
                {
                    "t_ms": grid,
                    "field": field,
                    "value": float(latest["value"]),
                    "canonical_unit": latest["canonical_unit"],
                    "source_id": latest["source_id"],
                    "source_seq": int(latest["record_seq"]),
                    "source_t_ms": float(latest["t_ms"]),
                    "age_ms": age_ms,
                    "quality": quality,
                    "deliverable": deliverable,
                }
            )
        grid = round(grid + grid_step_ms, 9)
    return aligned


def _gap_report(normalized: list[dict[str, object]], quarantine: list[dict[str, object]]) -> tuple[dict[str, int], dict[str, list[float]]]:
    rows = sorted(normalized + quarantine, key=lambda row: (str(row["source_id"]), int(row["record_seq"])))
    sequence_gaps = {source: 0 for source in {str(row["source_id"]) for row in rows}}
    time_gaps: dict[str, list[float]] = {source: [] for source in sequence_gaps}
    last_by_source: dict[str, dict[str, object]] = {}
    for row in rows:
        source = str(row["source_id"])
        previous = last_by_source.get(source)
        if previous is not None:
            seq_gap = int(row["record_seq"]) - int(previous["record_seq"])
            if seq_gap > 1:
                sequence_gaps[source] += 1
                time_gaps[source].append(round(float(row["t_ms"]) - float(previous["t_ms"]), 9))
        last_by_source[source] = row
    return sequence_gaps, time_gaps


def build_report(
    records: list[dict[str, object]],
    *,
    source_sha: str | None = None,
    grid_step_ms: float = GRID_STEP_MS,
    stale_budget_ms: float = STALE_BUDGET_MS,
) -> dict[str, object]:
    normalized, quarantine = _normalize(records)
    aligned = _alignment_rows(normalized, grid_step_ms, stale_budget_ms)
    sequence_gaps, time_gaps = _gap_report(normalized, quarantine)
    stale_rows = sum(1 for row in aligned if float(row["age_ms"]) > stale_budget_ms)
    degraded_rows = sum(1 for row in aligned if row["quality"] == "degraded")
    delivered_rows = sum(1 for row in aligned if row["deliverable"] is True)
    return {
        "scenario_id": SCENARIO_ID,
        "replay_scenario_id": REPLAY_SCENARIO_ID,
        "source_sha256": source_sha or "",
        "config_sha256": config_fingerprint(),
        "grid_step_ms": grid_step_ms,
        "stale_budget_ms": stale_budget_ms,
        "counts": {
            "raw_records": len(records),
            "normalized_records": len(normalized),
            "quarantined_records": len(quarantine),
            "aligned_rows": len(aligned),
            "delivered_rows": delivered_rows,
            "stale_rows": stale_rows,
            "degraded_rows": degraded_rows,
        },
        "transforms": {
            field: {
                "canonical_unit": contract["canonical_unit"],
                "units": contract["units"],
                "bounds": contract["bounds"],
            }
            for field, contract in FIELD_CONTRACTS.items()
        },
        "sequence_gaps": sequence_gaps,
        "time_gaps_ms": time_gaps,
        "quarantine": quarantine,
        "normalized_records": normalized,
        "aligned_series": aligned,
        "boundary": (
            "合成记录链教学切片：只验证字段合同、单位变换、时间对齐、质量隔离与回放谱系；"
            "不证明真实总线抓包、固件日志、硬件时钟、数据库或 D22 诊断语义已验收。"
        ),
    }


def _records_csv_bytes(columns: list[str], rows: list[dict[str, object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in columns})
    return buffer.getvalue().encode("utf-8")


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    path.write_bytes(_records_csv_bytes(columns, rows))


def records_source_sha256(records: list[dict[str, object]]) -> str:
    return hashlib.sha256(_records_csv_bytes(RECORD_COLUMNS, records)).hexdigest()


def write_artifacts(
    report: dict[str, object],
    records: list[dict[str, object]],
    out: Path,
    source_path: Path | None = None,
) -> None:
    out.mkdir(parents=True, exist_ok=True)
    raw_path = out / "records.csv"
    if source_path is not None:
        # A supplied record file is the lineage source: preserve its bytes so a
        # replay against the exported artifact verifies the same identity.
        shutil.copyfile(source_path, raw_path)
    else:
        # The built-in script has no external file until this artifact exists;
        # bind lineage to the exact raw-record CSV bytes used for replay.
        raw_bytes = _records_csv_bytes(RECORD_COLUMNS, records)
        raw_path.write_bytes(raw_bytes)
        report["source_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
    _write_csv(out / "normalized_records.csv", NORMALIZED_COLUMNS, report["normalized_records"])  # type: ignore[arg-type]
    _write_csv(out / "aligned_series.csv", ALIGNED_COLUMNS, report["aligned_series"])  # type: ignore[arg-type]
    (out / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lineage = {
        "scenario_id": report["scenario_id"],
        "source_sha256": report["source_sha256"],
        "config_sha256": report["config_sha256"],
        "record_count": report["counts"]["raw_records"],  # type: ignore[index]
    }
    (out / "lineage.json").write_text(
        json.dumps(lineage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def validate_lineage(metadata_path: Path, *, source_sha: str, config_sha: str) -> None:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("source_sha256") != source_sha:
        raise ValueError("lineage source mismatch")
    if metadata.get("config_sha256") != config_sha:
        raise ValueError("lineage transform config mismatch")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, help="raw record CSV; default uses the built-in synthetic script")
    parser.add_argument("--out", type=Path, help="write report.json, records.csv, normalized_records.csv, aligned_series.csv, and lineage.json")
    parser.add_argument("--metadata", type=Path, help="lineage.json from a previous run; replay rejects source/config drift")
    parser.add_argument("--grid-step-ms", type=float, default=GRID_STEP_MS)
    parser.add_argument("--stale-budget-ms", type=float, default=STALE_BUDGET_MS)
    args = parser.parse_args(argv)

    try:
        if args.records:
            records = load_records(args.records)
            sha = source_sha256(args.records)
        else:
            records = default_records()
            sha = records_source_sha256(records)
        if args.metadata:
            validate_lineage(args.metadata, source_sha=sha, config_sha=config_fingerprint())
        report = build_report(
            records,
            source_sha=sha,
            grid_step_ms=args.grid_step_ms,
            stale_budget_ms=args.stale_budget_ms,
        )
        if args.out:
            write_artifacts(report, records, args.out, source_path=args.records)
        else:
            print(json.dumps(report["counts"], ensure_ascii=False, indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"d21_record_chain: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
