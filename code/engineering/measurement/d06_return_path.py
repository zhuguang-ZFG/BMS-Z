"""Teaching calculations for D06: shared impedance, Kelvin sensing, and coupling.

Scenario ``D06-return-path`` (synthetic): ground bounce from a switching loop,
the Kelvin error a two-wire shunt reading pays, and capacitive common-mode
injection on an isolated link. Each number is a first-order estimate whose
assumptions are printed next to it; nothing here is an EMC test result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SCENARIO_ID = "D06-return-path"

LOOP_L_H = 100e-9  # 开关节换回路寄生电感（教学值）
DI_A = 20.0  # 换流电流摆幅
DT_S = 1e-6  # 电流切换时间
SHUNT_OHM = 300e-6  # 分流器（LibreSolar bms-c1 BOM 标称值，仅作身份引用）
LEAD_OHM = 10e-3  # 两线读法的引线+接触电阻（教学值）
RATED_A = 100.0  # 额定电流（教学值）
COUPLE_C_F = 10e-12  # 隔离两侧的寄生电容（教学值）
DV_DT_V_PER_S = 10e9  # 共模 dv/dt（教学值）


def ground_bounce_mv(
    loop_l_h: float = LOOP_L_H, di_a: float = DI_A, dt_s: float = DT_S
) -> float:
    if dt_s <= 0:
        raise ValueError("dt must be positive")
    return loop_l_h * di_a / dt_s * 1000.0


def kelvin_error_pct(shunt_ohm: float = SHUNT_OHM, lead_ohm: float = LEAD_OHM) -> float:
    if shunt_ohm <= 0:
        raise ValueError("shunt must be positive")
    return lead_ohm / (shunt_ohm + lead_ohm) * 100.0


def kelvin_error_mv(
    rated_a: float = RATED_A, shunt_ohm: float = SHUNT_OHM, lead_ohm: float = LEAD_OHM
) -> float:
    if rated_a < 0:
        raise ValueError("current must be nonnegative")
    return rated_a * (lead_ohm if lead_ohm > 0 else 0.0) * 1000.0


def capacitive_injection_ua(
    couple_c_f: float = COUPLE_C_F, dv_dt_v_per_s: float = DV_DT_V_PER_S
) -> float:
    if couple_c_f < 0 or dv_dt_v_per_s < 0:
        raise ValueError("capacitance and dv/dt must be nonnegative")
    return couple_c_f * dv_dt_v_per_s * 1e6


def build_report() -> dict:
    bounce = ground_bounce_mv()
    kel_pct = kelvin_error_pct()
    kel_mv = kelvin_error_mv()
    inj_ua = capacitive_injection_ua()
    return {
        "scenario_id": SCENARIO_ID,
        "identity": "first-order teaching estimates; simulation is not an EMC test",
        "assumptions": {
            "loop_l_h": LOOP_L_H,
            "di_a": DI_A,
            "dt_s": DT_S,
            "shunt_ohm": SHUNT_OHM,
            "lead_ohm": LEAD_OHM,
            "rated_a": RATED_A,
            "couple_c_f": COUPLE_C_F,
            "dv_dt_v_per_s": DV_DT_V_PER_S,
        },
        "ground_bounce_mv": round(bounce, 2),
        "kelvin_two_wire_error_pct": round(kel_pct, 2),
        "kelvin_two_wire_error_mv_at_rated": round(kel_mv, 2),
        "capacitive_injection_ua": round(inj_ua, 2),
        "reading": [
            f"地弹：{LOOP_L_H * 1e9:.0f} nH × {DI_A:.0f} A / {DT_S * 1e6:.0f} µs = {bounce:.0f} mV——公共回路上的噪声与被测信号同量级时必须改回流，不是加滤波",
            f"Kelvin：两线读法把 {LEAD_OHM * 1e3:.0f} mΩ 引线加进 {SHUNT_OHM * 1e6:.0f} µΩ 分流器 → {kel_pct:.1f}% 误差（额定点 {kel_mv:.0f} mV）；四线读法把引线排除在测量回路外",
            f"容性注入：{COUPLE_C_F * 1e12:.0f} pF × {DV_DT_V_PER_S / 1e9:.0f} kV/µs = {inj_ua / 1000:.0f} mA 级共模电流——隔离不是断开，是给共模电流一条受控的路",
        ],
        "conclusion": "三个一阶估算说明回流/开尔文/隔离的取舍；真实 EMC 结论只能靠标准测试（模拟不冒充）",
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
