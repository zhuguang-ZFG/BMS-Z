"""Teaching experiments for D10: balancing arithmetic and the three-differences
discipline (voltage / SOC / capacity are not interchangeable).

Scenario ``D10-balance-window`` (synthetic): passive bleed resistor arithmetic
(current, heat, time-to-balance), the measurement pause window with valid-sample
marking (E05 family), and the two counterexamples: voltage difference that is not
an SOC difference (flat OCV region), and a weak-capacity cell that balancing can
never fix.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SCENARIO_ID = "D10-balance-window"

BLEED_OHM = 100.0  # 旁路电阻（教学值）
CELL_V = 3.5  # 均衡点电压（教学值）
PAUSE_MS = 20.0  # 均衡关断后采样恢复窗口（教学值）
SAMPLE_MS = 20.0


def bleed_ma(v: float = CELL_V, r_ohm: float = BLEED_OHM) -> float:
    if r_ohm <= 0 or v < 0:
        raise ValueError("resistance must be positive and voltage nonnegative")
    return v / r_ohm * 1000.0


def bleed_heat_w(v: float = CELL_V, r_ohm: float = BLEED_OHM) -> float:
    if r_ohm <= 0 or v < 0:
        raise ValueError("bad arguments")
    return v * v / r_ohm


def balance_time_h(delta_ah: float, i_ma: float) -> float:
    if i_ma <= 0:
        raise ValueError("balance current must be positive")
    if delta_ah < 0:
        raise ValueError("delta Ah must be nonnegative")
    return delta_ah / (i_ma / 1000.0)


def three_differences() -> dict:
    """电压差 ≠ SOC 差（平坦区），SOC 差 ≠ 容量差（弱项修不了）。"""
    return {
        "voltage_vs_soc": {
            "case": "平坦 OCV 区（LFP 平台斜率 0.08 V/SOC）",
            "voltage_diff_mv": 20.0,
            "implied_soc_diff_pp": round(0.020 / 0.08 * 100, 2),
            "reading": "20 mV 压差在该区间对应 25 pp SOC 差；同一压差放到 0.8 斜率区间只有 2.5 pp——压差不能跨区间当 SOC 差用",
        },
        "soc_vs_capacity": {
            "case": "容量弱节 1.8 Ah vs 2.0 Ah",
            "balanceable": False,
            "reading": "均衡只能把电压/SOC 拉齐；容量差 0.2 Ah 永远在——满充时弱节先到电压上限，放电时先到下限",
        },
        "conclusion": "电压差、SOC 差、容量差是三笔不同的账；均衡只结前两笔的一部分",
    }


def measurement_pause() -> dict:
    """均衡开启时旁路电流扰动测量；有效样本必须等恢复窗口。"""
    i_ma = bleed_ma()
    cycle_ms = SAMPLE_MS + PAUSE_MS
    duty = PAUSE_MS / cycle_ms
    return {
        "bleed_ma": round(i_ma, 2),
        "pause_ms": PAUSE_MS,
        "valid_sample_ms": SAMPLE_MS,
        "cycle_ms": cycle_ms,
        "valid_fraction": round(duty, 2),
        "marking_rule": "均衡开启窗口内的样本标记无效；只用恢复后的样本做判据",
        "conclusion": f"有效样本占比 {duty:.0%}——均衡与测量分时，宁可慢不可脏",
    }


def build_report() -> dict:
    i_ma = bleed_ma()
    return {
        "scenario_id": SCENARIO_ID,
        "identity": "teaching values; real bleed current/thermal limits from SRC02/SRC04",
        "bleed": {
            "r_ohm": BLEED_OHM,
            "v": CELL_V,
            "i_ma": round(i_ma, 2),
            "heat_w": round(bleed_heat_w(), 3),
            "balance_0p05Ah_h": round(balance_time_h(0.05, i_ma), 3),
            "balance_0p05Ah_min": round(balance_time_h(0.05, i_ma) * 60, 1),
        },
        "differences": three_differences(),
        "pause": measurement_pause(),
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
