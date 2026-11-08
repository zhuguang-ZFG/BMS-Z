"""Teaching experiments for D04: the full six-term error budget.

Extends S1's four-term chain with quantization and temperature drift, plus the
two-point calibration counterexample. All teaching values; the budget table is
the C1 seed and must stay consistent with s1_measurement.py's frozen anchors.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SCENARIO_ID = "D04-six-term-budget"

# Chain teaching constants (consistent with S1 frozen anchors).
FULL_SCALE_V = 5.0
ADC_BITS = 16
PGA_GAIN = 1.0
TEMP_DRIFT_PPM_PER_C = 50.0
REF_TEMP_C = 25.0
CHECK_TEMP_C = 45.0
CELL_NOMINAL_V = 3.6
# S1 anchors this table must stay consistent with (from s1_measurement.py):
S1_WORST_BOUND_MV = 4.5
S1_RSS_MV = 2.51595


def lsb_v(
    full_scale_v: float = FULL_SCALE_V, bits: int = ADC_BITS, gain: float = PGA_GAIN
) -> float:
    if bits <= 0 or gain <= 0 or full_scale_v <= 0:
        raise ValueError("bits, gain and full scale must be positive")
    return full_scale_v / gain / (2**bits)


def quantization_bound_mv(
    full_scale_v: float = FULL_SCALE_V, bits: int = ADC_BITS
) -> float:
    """Rounding quantization is uniform in ±LSB/2; the bound is LSB/2 (one-sided)."""
    return lsb_v(full_scale_v, bits) / 2 * 1000.0


def temp_drift_mv(
    nominal_v: float = CELL_NOMINAL_V,
    delta_t_c: float = CHECK_TEMP_C - REF_TEMP_C,
    ppm_per_c: float = TEMP_DRIFT_PPM_PER_C,
) -> float:
    if delta_t_c < 0:
        raise ValueError("use the magnitude of the temperature excursion")
    return nominal_v * ppm_per_c * 1e-6 * delta_t_c * 1000.0


def two_point_calibration(
    x1: float, y1: float, x2: float, y2: float
) -> tuple[float, float]:
    """Fit correction V = g*y + b through two calibration points; reject degenerate pairs."""
    if x1 == x2:
        raise ValueError("calibration points must differ in x")
    g = (x2 - x1) / (y2 - y1)
    b = x1 - g * y1
    return g, b


def budget_rows() -> list[dict]:
    """Six-term worst-case budget (teaching values, bounds in mV).

    gain/offset/channel/temp are the S1 four sources; quantization and dynamic
    settling are added by D04. Worst-case column is the absolute bound.
    """
    return [
        {"term": "增益误差", "symbol": "g_c", "bound_mv": 2.0, "kind": "比例"},
        {"term": "固定偏置", "symbol": "b_c", "bound_mv": 1.2, "kind": "常值"},
        {"term": "通道偏置", "symbol": "b_i", "bound_mv": 0.8, "kind": "常值"},
        {
            "term": "温漂",
            "symbol": "α(T−T0)",
            "bound_mv": round(temp_drift_mv(), 3),
            "kind": "常值",
        },
        {
            "term": "量化",
            "symbol": "±LSB/2",
            "bound_mv": round(quantization_bound_mv(), 3),
            "kind": "常值",
        },
        {"term": "动态建立", "symbol": "e_dyn", "bound_mv": 0.5, "kind": "常值"},
    ]


def worst_case_mv(rows: list[dict] | None = None) -> float:
    rows = rows or budget_rows()
    return round(sum(r["bound_mv"] for r in rows), 4)


def rss_mv(rows: list[dict] | None = None) -> float:
    rows = rows or budget_rows()
    return round(math.sqrt(sum(r["bound_mv"] ** 2 for r in rows)), 5)


def build_report() -> dict:
    rows = budget_rows()
    return {
        "scenario_id": SCENARIO_ID,
        "identity": "teaching budget; S1 anchors 4.5 mV worst / 2.51595 mV RSS stay the four-term subset",
        "chain": {
            "full_scale_v": FULL_SCALE_V,
            "bits": ADC_BITS,
            "gain": PGA_GAIN,
            "lsb_uv": round(lsb_v() * 1e6, 3),
            "drift_check_temp_c": CHECK_TEMP_C,
            "ref_temp_c": REF_TEMP_C,
            "ppm_per_c": TEMP_DRIFT_PPM_PER_C,
        },
        "budget_mv": rows,
        "six_term_worst_mv": worst_case_mv(rows),
        "six_term_rss_mv": rss_mv(rows),
        "s1_subset_worst_mv": S1_WORST_BOUND_MV,
        "s1_subset_rss_mv": S1_RSS_MV,
        "conclusion": "加入量化与温漂后最坏界上移到六项之和；RSS 仍不是绝对界",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 的目录")
    args = parser.parse_args()
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
