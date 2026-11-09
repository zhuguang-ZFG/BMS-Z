"""Teaching experiments for D12: SOC baseline bookkeeping and OCV calibration.

Frozen teaching chain (extends S2/D02): Q = 2 Ah; bias/initial/capacity errors
each propagate differently. OCV calibration conditions come from D01/D02:
rest time must outlast polarization; the OCV slope decides whether a voltage
observation can even correct SOC (flat region cannot); hysteresis branch must
match (D2.4).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCENARIO_ID = "D12-soc-baseline"

Q_AH = 2.0
BIAS_A = 0.05               # 电流传感偏置（教学值）
HOURS = 1.0
INIT_ERROR_PP = 10.0
CAPACITY_ERROR_PCT = 5.0
OCV_SLOPE_STEEP = 0.8       # V/SOC（NMC 类，教学值）
OCV_SLOPE_FLAT = 0.08       # V/SOC（LFP 平台，教学值）
HYSTERESIS_WIDTH_MV = 10.0


def bias_drift_pp(bias_a: float = BIAS_A, hours: float = HOURS, q_ah: float = Q_AH) -> float:
    if q_ah <= 0 or hours < 0:
        raise ValueError("capacity must be positive, hours nonnegative")
    return bias_a * hours * 3600.0 / (3600.0 * q_ah) * 100.0


def capacity_gain_error_pp(true_delta_pp: float = 100.0, capacity_error_pct: float = CAPACITY_ERROR_PCT) -> float:
    """容量误差是 Δz 的增益误差：同一真值变化被错除。"""
    if true_delta_pp == 0:
        return 0.0
    wrong_q = Q_AH * (1.0 + capacity_error_pct / 100.0)
    measured = true_delta_pp * Q_AH / wrong_q
    return true_delta_pp - measured


def ocv_correction_gain(slope_v_per_soc: float) -> float:
    """一阶修正强度：斜率越平，同样的电压观测对 SOC 的约束越弱（0 = 不可校正）。"""
    if slope_v_per_soc < 0:
        raise ValueError("slope must be nonnegative")
    return slope_v_per_soc


def calibration_residual_pp(voltage_error_mv: float, slope_v_per_soc: float,
                            hysteresis_mv: float = 0.0) -> float:
    """校准残差 =（电压误差 + 迟滞失配）/ 斜率；平坦区与迟滞失配都会放大或废掉校正。"""
    if slope_v_per_soc <= 0:
        raise ValueError("slope must be positive for calibration")
    return (voltage_error_mv + hysteresis_mv) / (slope_v_per_soc * 1000.0) * 100.0 * 100.0 / 100.0


def build_report() -> dict:
    return {
        "scenario_id": SCENARIO_ID,
        "identity": "teaching chain extending S2/D02; real OCV tables from SRC01",
        "bias_drift_pp_per_h": round(bias_drift_pp(), 2),
        "capacity_gain_error_pp": round(capacity_gain_error_pp(), 2),
        "init_error_pp": INIT_ERROR_PP,
        "ocv_correction": {
            "steep_region": {
                "slope": OCV_SLOPE_STEEP,
                "residual_5mv_pp": round(calibration_residual_pp(5.0, OCV_SLOPE_STEEP), 2),
            },
            "flat_region": {
                "slope": OCV_SLOPE_FLAT,
                "residual_5mv_pp": round(calibration_residual_pp(5.0, OCV_SLOPE_FLAT), 2),
            },
            "hysteresis_mismatch": {
                "slope": OCV_SLOPE_STEEP,
                "residual_0mv_with_10mv_hyst_pp": round(calibration_residual_pp(0.0, OCV_SLOPE_STEEP, HYSTERESIS_WIDTH_MV), 2),
            },
        },
        "conclusion": "偏置漂移 2.5 pp/h；容量误差是增益误差（±4.76 pp）；OCV 校正强度看斜率：5 mV 在 0.8 斜率区残差 0.62 pp、在 0.08 平坦区 6.25 pp；迟滞失配 10 mV 在 0.8 区废掉 1.25 pp",
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
