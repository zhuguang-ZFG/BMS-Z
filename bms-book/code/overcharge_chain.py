#!/usr/bin/env python3
"""Overcharge brake distance in millivolts and milliamp-hours; teaching numbers only."""
from __future__ import annotations

CUTOFF_V = 4.20          # 充电截止（三元示例）
FIRMWARE_OVP_V = 4.25    # 教学固件示例的过充检测
DW01A_OVP_V = 4.30       # DW01A 手册典型值，±50 mV
DW01A_TOLERANCE_V = 0.05
SERIES = 16
CAPACITY_AH = 50.0
ONE_C_A = 50.0


def chain_steps() -> list[str]:
    """The five teaching acts; the real order varies, this is a compressed script."""
    return [
        "正极过度脱锂：结构坍塌，容量永久损失",
        "电解液氧化分解：产气鼓包",
        "负极析锂：金属锂长成枝晶",
        "枝晶刺穿隔膜：内部短路",
        "热失控：放热自我加速，可能蔓延到相邻电芯",
    ]


def brake_distance_mv(detector_v: float, cutoff_v: float) -> float:
    if detector_v <= cutoff_v:
        raise ValueError("detector must sit above the charger cutoff")
    return (detector_v - cutoff_v) * 1000


def overshoot_percent(delta_v: float, cutoff_v: float) -> float:
    if cutoff_v <= 0 or delta_v < 0:
        raise ValueError("cutoff must be positive and delta nonnegative")
    return delta_v / cutoff_v * 100


def pack_overshoot_v(delta_v: float, series: int) -> float:
    if series <= 0:
        raise ValueError("series count must be positive")
    return delta_v * series


def charge_added_mah(current_a: float, delay_s: float) -> float:
    if current_a < 0 or delay_s < 0:
        raise ValueError("current and delay must be nonnegative")
    return current_a * delay_s / 3.6


def soc_slip_percent(charge_mah: float, capacity_ah: float) -> float:
    if capacity_ah <= 0:
        raise ValueError("capacity must be positive")
    return charge_mah / (capacity_ah * 1000) * 100


def main() -> None:
    for index, step in enumerate(chain_steps(), 1):
        print(f"第 {index} 幕：{step}")
    print(f"三个电压数不能互替：充电截止 {CUTOFF_V:.2f} V < 教学过充检测 {FIRMWARE_OVP_V:.2f} V "
          f"< DW01A 典型 {DW01A_OVP_V:.2f} V（±{DW01A_TOLERANCE_V * 1000:.0f} mV，即 {DW01A_OVP_V - DW01A_TOLERANCE_V:.2f}–{DW01A_OVP_V + DW01A_TOLERANCE_V:.2f} V）")
    print(f"刹车距离（保护点一侧）：{brake_distance_mv(FIRMWARE_OVP_V, CUTOFF_V):.0f} mV；"
          f"DW01A 最坏下探到 {DW01A_OVP_V - DW01A_TOLERANCE_V:.2f} V 时只剩 {brake_distance_mv(DW01A_OVP_V - DW01A_TOLERANCE_V, CUTOFF_V):.0f} mV")
    print("化学上限由电芯手册给，本仓库不编数——刹车距离的电压端要拿手册填")
    delta = 0.100
    print(f"充电器每节多顶 {delta * 1000:.0f} mV：相对值 {overshoot_percent(delta, CUTOFF_V):.1f}%，"
          f"{SERIES} 串整包多 {pack_overshoot_v(delta, SERIES):.1f} V")
    delay = 1.0
    slipped = charge_added_mah(ONE_C_A, delay)
    print(f"检测延时 {delay:.0f} s、1C {ONE_C_A:.0f} A：多灌 {slipped:.1f} mAh，"
          f"占 {CAPACITY_AH:.0f} Ah 的 {soc_slip_percent(slipped, CAPACITY_AH):.3f}% SOC——Ah 上很小，越过红线的是电压")

    steps = chain_steps()
    assert len(steps) == 5 and steps[0].startswith("正极") and steps[-1].startswith("热失控")
    assert CUTOFF_V < FIRMWARE_OVP_V < DW01A_OVP_V
    assert abs(brake_distance_mv(FIRMWARE_OVP_V, CUTOFF_V) - 50.0) < 1e-9
    assert abs(brake_distance_mv(DW01A_OVP_V - DW01A_TOLERANCE_V, CUTOFF_V) - 50.0) < 1e-9
    assert abs(overshoot_percent(delta, CUTOFF_V) - 2.4) < 0.05
    assert pack_overshoot_v(delta, SERIES) == 1.6
    assert abs(charge_added_mah(ONE_C_A, delay) - 50 / 3.6) < 1e-9
    assert abs(soc_slip_percent(charge_added_mah(ONE_C_A, delay), CAPACITY_AH) - 0.0278) < 1e-3
    for bad in ((4.20, 4.20), (4.10, 4.20)):
        try:
            brake_distance_mv(*bad)
        except ValueError:
            continue
        raise AssertionError("检测电压必须高于截止电压")
    print("checks passed: 五幕顺序、三个电压档不互替、50 mV 窗口、16 串累积与延时多灌的电荷")


if __name__ == "__main__":
    main()
