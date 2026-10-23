#!/usr/bin/env python3
"""Row-level data audit: 8 checks over a synthetic CC-discharge log (ch.21 demo).

Builds ~40 rows (time_s, voltage_v, current_a, temperature_c) with three
injected defects, runs eight checks, and prints the hit count of each:
  1 range      voltage outside [2.500, 4.350] V
  2 step       |dV| > 0.200 V between consecutive valid samples
  3 missing    empty / non-numeric field
  4 duplicate  two consecutive rows identical on every field
  5 timestamp  off the t0 + k*dt grid by > 0.5*dt (or going backwards)
  6 stuck      >= 3 identical voltage samples while |current| > 0.5 A
  7 unit       |voltage| > 7 V (looks like mV scaled, or a unit mix)
  8 monotonic  CC discharge rising more than the 5 mV noise band

Defects (deterministic): row 15 out-of-range 4.55 V; rows 22-26 stuck at
3.295 V; row 31 timestamp 28.5 s. Every other check must stay at 0.

Run: python code/data_audit.py
"""

from __future__ import annotations

import csv
import io

DT_S = 1.0
V_MIN, V_MAX = 2.500, 4.350
STEP_LIMIT_V = 0.200
GRID_TOL_S = 0.5 * DT_S
STUCK_RUN = 3
NOISE_BAND_V = 0.005
N_ROWS = 40


def build_rows() -> list[dict[str, float]]:
    """CC discharge at -2.0 A, V = 3.300 - 0.002*k, plus 3 injected defects."""
    rows: list[dict[str, float]] = []
    for k in range(N_ROWS):
        rows.append({
            "time_s": float(k),
            "voltage_v": round(3.300 - 0.002 * k, 3),
            "current_a": -2.0,
            "temperature_c": 25.0,
        })
    rows[15]["voltage_v"] = 4.55          # defect 1: out of range
    for k in range(22, 27):
        rows[k]["voltage_v"] = 3.295      # defect 2: stuck while current flows
    rows[31]["time_s"] = 28.5             # defect 3: timestamp off grid / backwards
    return rows


def csv_roundtrip(rows: list[dict[str, float]]) -> list[list[str]]:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["time_s", "voltage_v", "current_a", "temperature_c"])
    for r in rows:
        w.writerow([r["time_s"], r["voltage_v"], r["current_a"], r["temperature_c"]])
    buf.seek(0)
    return list(csv.reader(buf))[1:]  # drop header


def audit(records: list[list[str]]) -> dict[str, list[int]]:
    hits: dict[str, list[int]] = {k: [] for k in (
        "range", "step", "missing", "duplicate", "timestamp",
        "stuck", "unit", "monotonic")}

    n = len(records)
    bad = [False] * n  # rows explained by an earlier check

    def v(i: int) -> float:
        return float(records[i][1])

    for i, rec in enumerate(records):
        if any(field.strip() == "" for field in rec):
            hits["missing"].append(i)
            bad[i] = True
            continue
        try:
            vals = [float(f) for f in rec]
        except ValueError:
            hits["missing"].append(i)
            bad[i] = True
            continue
        volt = vals[1]
        if not (V_MIN <= volt <= V_MAX):
            hits["range"].append(i)
            bad[i] = True
        if abs(volt) > 7.0:
            hits["unit"].append(i)

    # stuck runs first: rows explained by "ADC latched" skip step/monotonic
    run: list[int] = []
    for i in range(n + 1):
        same = (
            i < n
            and not bad[i]
            and run
            and v(i) == v(run[-1])
            and float(records[i][2]) == float(records[run[-1]][2])
        )
        if same:
            run.append(i)
            continue
        if len(run) >= STUCK_RUN and abs(float(records[run[-1]][2])) > 0.5:
            hits["stuck"].extend(run)
            for r in run:
                bad[r] = True
        run = [i] if i < n and not bad[i] else []

    for i in range(n):
        t = float(records[i][0])
        expected = i * DT_S
        if abs(t - expected) > GRID_TOL_S or (i > 0 and t < float(records[i - 1][0])):
            hits["timestamp"].append(i)
        if i > 0 and records[i] == records[i - 1]:
            hits["duplicate"].append(i)

    prev = -1
    for i in range(n):
        if bad[i]:
            continue
        if prev >= 0 and abs(v(i) - v(prev)) > STEP_LIMIT_V:
            hits["step"].append(i)
        if prev >= 0:
            i_now = float(records[i][2])
            dv = v(i) - v(prev)
            if abs(i_now) > 0.5 and dv > NOISE_BAND_V:
                hits["monotonic"].append(i)
        prev = i

    return hits


def main() -> None:
    records = csv_roundtrip(build_rows())
    hits = audit(records)

    print("row-level audit: 40-row CC-discharge log, 3 injected defects")
    print(f"{'check':12s} {'hits':>4s} rows")
    for name, idx in hits.items():
        print(f"{name:12s} {len(idx):4d} {idx}")
    print()

    assert hits["range"] == [15], "defect 1 (4.55 V) must be caught by range only"
    assert hits["stuck"] == [22, 23, 24, 25, 26], "defect 2 (stuck) must be caught"
    assert hits["timestamp"] == [31], "defect 3 (timestamp) must be caught"
    for name in ("step", "missing", "duplicate", "unit", "monotonic"):
        assert not hits[name], f"check '{name}' must stay silent (no false positives)"
    print("[PASS] 3/3 defects caught, 0 false positives")


if __name__ == "__main__":
    main()
