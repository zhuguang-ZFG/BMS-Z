#!/usr/bin/env python3
"""Precharge timeline for 400 V / 1 mF / 170 ohm; every number is a teaching example."""
from __future__ import annotations

import math


def time_constant_s(resistance_ohm: float, capacitance_f: float) -> float:
    if resistance_ohm <= 0 or capacitance_f <= 0:
        raise ValueError("resistance and capacitance must be positive")
    return resistance_ohm * capacitance_f


def surge_current_a(pack_v: float, resistance_ohm: float) -> float:
    if resistance_ohm <= 0:
        raise ValueError("resistance must be positive")
    return pack_v / resistance_ohm


def pulse_energy_j(capacitance_f: float, pack_v: float) -> float:
    if capacitance_f <= 0 or pack_v <= 0:
        raise ValueError("capacitance and pack voltage must be positive")
    return 0.5 * capacitance_f * pack_v ** 2


def bus_voltage_v(elapsed_s: float, pack_v: float, resistance_ohm: float, capacitance_f: float) -> float:
    if elapsed_s < 0:
        raise ValueError("elapsed time must be nonnegative")
    return pack_v * (1 - math.exp(-elapsed_s / time_constant_s(resistance_ohm, capacitance_f)))


def rise_time_s(ratio: float, resistance_ohm: float, capacitance_f: float) -> float:
    if not 0 < ratio < 1:
        raise ValueError("target ratio must be strictly between 0 and 1")
    return -time_constant_s(resistance_ohm, capacitance_f) * math.log(1 - ratio)


def weld_suspect(pack_v: float, bus_v_before_precharge: float, ratio: float = 0.2) -> bool:
    """K1 open means an empty bus; a live bus before K2 closes points to a welded K1."""
    if pack_v <= 0:
        raise ValueError("pack voltage must be positive")
    return bus_v_before_precharge > ratio * pack_v


def close_verdict(pack_v: float, measured_v: float, ratio: float = 0.95) -> dict:
    """K1 may only close once the bus has come up; anything else forbids closing."""
    target = pack_v * ratio
    allowed = measured_v >= target
    if allowed:
        reason = "压差已小，可以合 K1，随后断开 K2"
    elif measured_v <= 0.2 * pack_v:
        reason = "母线基本不动：外部短路或接触器后端故障，禁止合 K1"
    else:
        reason = "升压不足（爬得太慢或漏电），超时即判故障，禁止合 K1"
    return {"target_v": target, "allowed": allowed, "reason": reason}


def main() -> None:
    pack, capacitance, resistance = 400.0, 0.001, 170.0
    tau = time_constant_s(resistance, capacitance)
    current = surge_current_a(pack, resistance)
    energy = pulse_energy_j(capacitance, pack)

    at_tau = bus_voltage_v(tau, pack, resistance, capacitance)
    at_three_tau = bus_voltage_v(3 * tau, pack, resistance, capacitance)
    t95 = rise_time_s(0.95, resistance, capacitance)

    healthy = close_verdict(pack, at_three_tau)
    early = close_verdict(pack, at_tau)
    stuck = close_verdict(pack, 40.0)
    slow = close_verdict(pack, bus_voltage_v(3 * tau, pack, resistance, 3 * capacitance))
    print(f"参数：包压 {pack:.0f} V，母线电容 {capacitance * 1e3:.0f} mF，预充电阻 {resistance:.0f} Ω（教学示例，不是实测）")
    print(f"时间常数 τ = RC = {tau:.2f} s；初始电流 I0 = U/R = {current:.2f} A；一次冲击能量 ½CU² = {energy:.0f} J")
    print(f"t = τ = {tau:.2f} s：母线 {at_tau:.0f} V（{at_tau / pack * 100:.0f}%）→ {early['reason']}")
    print(f"t = 3τ = {3 * tau:.2f} s：母线 {at_three_tau:.0f} V（{at_three_tau / pack * 100:.0f}%）→ {healthy['reason']}")
    print(f"合闸门限 95% 对应 {t95:.2f} s；控制器把超时窗口放在它之后：到点读不到 95% 就判故障")
    print(f"失败一：母线停住 {40.0:.0f} V → {stuck['reason']}")
    print(f"失败二：电容变成 3 mF（τ 变成 {3 * tau:.2f} s），同一时刻只有 "
          f"{bus_voltage_v(3 * tau, pack, resistance, 3 * capacitance):.0f} V → {slow['reason']}")
    print(f"失败三：预充前母线已读到 {380.0:.0f} V（K2 还没合）→ "
          + ("K1 粘连的证据，禁止继续流程" if weld_suspect(pack, 380.0) else "母线应为空，读数异常"))

    assert abs(tau - 0.17) < 1e-12
    assert abs(current - 400 / 170) < 1e-12
    assert abs(energy - 80.0) < 1e-9
    assert abs(at_tau - 252.8) < 0.1 and abs(at_tau / pack - (1 - math.exp(-1))) < 1e-12
    assert abs(at_three_tau - 380.1) < 0.1
    assert abs(t95 - 3 * tau) < 0.01
    assert healthy["allowed"] and not early["allowed"] and not stuck["allowed"] and not slow["allowed"]
    assert "禁止合 K1" in stuck["reason"] and "禁止合 K1" in slow["reason"]
    assert bus_voltage_v(0.0, pack, resistance, capacitance) == 0.0
    assert weld_suspect(pack, 380.0) and not weld_suspect(pack, 0.0)
    assert not weld_suspect(pack, 0.2 * pack) and weld_suspect(pack, 0.2 * pack + 1)
    for bad in ((0.0, 0.001), (170.0, 0.0)):
        try:
            time_constant_s(*bad)
        except ValueError:
            continue
        raise AssertionError("零电阻或零电容必须被拒绝")
    print("checks passed: τ、I0、80 J、τ 与 3τ 两点电压、95% 门限、超时/不上升/粘连三条判据")


if __name__ == "__main__":
    main()
