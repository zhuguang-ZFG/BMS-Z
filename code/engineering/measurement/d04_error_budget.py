"""Teaching experiments for D04: the full six-term error budget.

Extends S1's four-term chain with quantization and temperature drift. A separate
synthetic calibration case freezes a two-point fit before checking held-out
voltages/temperatures; it is not measured validation or the six-term budget model.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

SCENARIO_ID = "D04-six-term-budget"
CALIBRATION_SCENARIO_ID = "D04-calibration-holdout"
POINT_FIELDS = ("sample_id", "reference_v", "measured_v", "temperature_c")

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


def _error_metrics(errors_mv: list[float]) -> dict:
    return {
        "mean_error_mv": math.fsum(errors_mv) / len(errors_mv),
        "mae_mv": math.fsum(abs(error) for error in errors_mv) / len(errors_mv),
        "max_abs_error_mv": max(abs(error) for error in errors_mv),
    }


def evaluate_calibration(
    calibration: list[dict], validation: list[dict], *, limit_mv: float = 1.0
) -> dict:
    """Freeze an affine fit on two samples; evaluate only disjoint holdout IDs.

    Reference voltages must come from a declared reference, not the correction's
    own output. The caller owns provenance; this function cannot verify it.
    """
    if len(calibration) != 2 or not validation:
        raise ValueError("use exactly two calibration samples and a nonempty holdout")
    if not math.isfinite(limit_mv) or limit_mv < 0:
        raise ValueError("limit_mv must be finite and nonnegative")
    ids = [row["sample_id"] for row in calibration + validation]
    if any(not sample_id for sample_id in ids) or len(set(ids)) != len(ids):
        raise ValueError("calibration and validation sample IDs must be unique and disjoint")
    for row in calibration + validation:
        if not all(math.isfinite(row[field]) for field in POINT_FIELDS[1:]):
            raise ValueError("reference, measurement and temperature must be finite")
    low, high = calibration
    if low["measured_v"] == high["measured_v"]:
        raise ValueError("calibration needs a nonzero measurement span")
    gain, offset = two_point_calibration(
        low["reference_v"], low["measured_v"],
        high["reference_v"], high["measured_v"],
    )
    voltage_range = sorted(row["reference_v"] for row in calibration)
    checked = []
    for row in validation:
        corrected = gain * row["measured_v"] + offset
        checked.append({
            **row,
            "corrected_v": corrected,
            "raw_error_mv": (row["measured_v"] - row["reference_v"]) * 1000,
            "corrected_error_mv": (corrected - row["reference_v"]) * 1000,
            "within_calibrated_range": voltage_range[0] <= row["reference_v"] <= voltage_range[1],
        })
    before = _error_metrics([row["raw_error_mv"] for row in checked])
    after = _error_metrics([row["corrected_error_mv"] for row in checked])
    by_temperature = []
    for temperature in sorted({row["temperature_c"] for row in checked}):
        group = [row for row in checked if row["temperature_c"] == temperature]
        group_after = _error_metrics([row["corrected_error_mv"] for row in group])
        by_temperature.append({
            "temperature_c": temperature,
            "before": _error_metrics([row["raw_error_mv"] for row in group]),
            "after": group_after,
            "passed": group_after["max_abs_error_mv"] <= limit_mv,
        })
    return {
        "gain": gain,
        "offset_v": offset,
        "calibrated_voltage_range_v": voltage_range,
        "calibration_residual_max_mv": max(
            abs(gain * row["measured_v"] + offset - row["reference_v"]) * 1000
            for row in calibration
        ),
        "calibration_points": [dict(row) for row in calibration],
        "validation_points": checked,
        "metrics": {"before": before, "after": after},
        "by_temperature": by_temperature,
        "validation_limit_mv": limit_mv,
        "validation_passed": after["max_abs_error_mv"] <= limit_mv,
        "observed_underread_mv": max(0.0, -min(row["corrected_error_mv"] for row in checked)),
    }


def calibration_case(
    calibration: list[dict] | None = None, validation: list[dict] | None = None
) -> dict:
    """Default data are synthetic holdout conditions, not independent physics."""
    if (calibration is None) != (validation is None):
        raise ValueError("supply calibration and validation together")
    synthetic = calibration is None
    if calibration is None or validation is None:
        def sample(sample_id: str, voltage: float, temperature: float) -> dict:
            return {
                "sample_id": sample_id,
                "reference_v": voltage,
                "measured_v": (
                    1.002 * voltage + 0.012
                    + voltage * 50e-6 * (temperature - 25.0)
                    + 0.001 * (voltage - 3.0) * (voltage - 4.2)
                ),
                "temperature_c": temperature,
            }
        calibration = [sample("cal-low", 3.0, 25.0), sample("cal-high", 4.2, 25.0)]
        validation = [
            sample(f"holdout-{temperature:g}-{voltage:g}", voltage, temperature)
            for temperature in (5.0, 25.0, 45.0)
            for voltage in (2.8, 3.3, 3.6, 3.9, 4.3)
        ]
    result = evaluate_calibration(calibration, validation)
    return {
        "scenario_id": CALIBRATION_SCENARIO_ID,
        "data_identity": "synthetic teaching data" if synthetic else "user CSV; provenance not verified",
        "generator": (
            "y=1.002*V+0.012+V*50e-6*(T-25)+0.001*(V-3.0)*(V-4.2) [V, degC]"
            if synthetic else None
        ),
        "limitations": [
            "Holdout samples never change the fitted gain or offset.",
            "Observed residuals are not a worst-case bound or measured hardware acceptance.",
            "The synthetic generator omits quantization, noise and dynamic settling.",
            "Voltage extrapolation and temperature drift are not corrected by a two-point fit.",
        ],
        **result,
    }


def read_points(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return [
            {"sample_id": row["sample_id"], **{field: float(row[field]) for field in POINT_FIELDS[1:]}}
            for row in csv.DictReader(source)
        ]


def build_report(
    calibration: list[dict] | None = None, validation: list[dict] | None = None
) -> dict:
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
        "calibration_validation": calibration_case(calibration, validation),
        "conclusion": "加入量化与温漂后最坏界上移到六项之和；RSS 仍不是绝对界",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 的目录")
    parser.add_argument("--calibration", type=Path, help="标定 CSV（与 --validation 成对）")
    parser.add_argument("--validation", type=Path, help="独立验证 CSV，不参与拟合")
    args = parser.parse_args()
    if bool(args.calibration) != bool(args.validation):
        parser.error("--calibration and --validation must be supplied together")
    report = build_report(
        read_points(args.calibration) if args.calibration else None,
        read_points(args.validation) if args.validation else None,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        evidence = report["calibration_validation"]
        for name, key in (("calibration.csv", "calibration_points"), ("validation.csv", "validation_points")):
            points = evidence[key]
            with (args.out / name).open("w", encoding="utf-8", newline="") as output:
                writer = csv.DictWriter(output, fieldnames=list(points[0]))
                writer.writeheader()
                writer.writerows(points)
        (args.out / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
