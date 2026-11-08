#!/usr/bin/env python3
"""Ideal RC arithmetic, not a contactor controller or a weld diagnosis.

400 V / 1 mF / 170 ohm are synthetic teaching values. The constant source
charges one capacitor through one resistor; no parallel load or external
backfeed is modeled. Voltage agreement alone never authorizes K1 to close.
"""
from __future__ import annotations

import math


def _finite(*values: float) -> None:
    if not all(math.isfinite(value) for value in values):
        raise ValueError("all inputs must be finite")


def _voltages(pack_v: float, initial_bus_v: float) -> None:
    _finite(pack_v, initial_bus_v)
    if pack_v <= 0 or not 0 <= initial_bus_v <= pack_v:
        raise ValueError("this charging example requires 0 <= initial bus <= positive pack voltage")


def time_constant_s(resistance_ohm: float, capacitance_f: float) -> float:
    _finite(resistance_ohm, capacitance_f)
    if resistance_ohm <= 0 or capacitance_f <= 0:
        raise ValueError("resistance and capacitance must be positive")
    return resistance_ohm * capacitance_f


def surge_current_a(pack_v: float, resistance_ohm: float, initial_bus_v: float = 0.0) -> float:
    _voltages(pack_v, initial_bus_v)
    _finite(resistance_ohm)
    if resistance_ohm <= 0:
        raise ValueError("resistance must be positive")
    return (pack_v - initial_bus_v) / resistance_ohm


def pulse_energy_j(capacitance_f: float, pack_v: float, initial_bus_v: float = 0.0) -> float:
    """Resistor heat as t -> infinity, not capacitor energy transferred to heat."""
    _voltages(pack_v, initial_bus_v)
    _finite(capacitance_f)
    if capacitance_f <= 0:
        raise ValueError("capacitance must be positive")
    return 0.5 * capacitance_f * (pack_v - initial_bus_v) ** 2


def bus_voltage_v(elapsed_s: float, pack_v: float, resistance_ohm: float,
                  capacitance_f: float, initial_bus_v: float = 0.0) -> float:
    _voltages(pack_v, initial_bus_v)
    _finite(elapsed_s)
    if elapsed_s < 0:
        raise ValueError("elapsed time must be nonnegative")
    tau = time_constant_s(resistance_ohm, capacitance_f)
    return pack_v - (pack_v - initial_bus_v) * math.exp(-elapsed_s / tau)


def energy_ledger_j(elapsed_s: float, pack_v: float, resistance_ohm: float,
                    capacitance_f: float, initial_bus_v: float = 0.0) -> dict[str, float]:
    """Source work = resistor heat + capacitor energy increase for this ideal RC."""
    bus_v = bus_voltage_v(elapsed_s, pack_v, resistance_ohm, capacitance_f, initial_bus_v)
    tau = time_constant_s(resistance_ohm, capacitance_f)
    return {
        "source_j": pack_v * capacitance_f * (bus_v - initial_bus_v),
        "resistor_j": pulse_energy_j(capacitance_f, pack_v, initial_bus_v)
        * -math.expm1(-2 * elapsed_s / tau),
        "capacitor_initial_j": 0.5 * capacitance_f * initial_bus_v ** 2,
        "capacitor_j": 0.5 * capacitance_f * bus_v ** 2,
        "capacitor_increase_j": 0.5 * capacitance_f * (bus_v ** 2 - initial_bus_v ** 2),
    }


def rise_time_s(ratio: float, resistance_ohm: float, capacitance_f: float) -> float:
    """Time from an empty capacitor to ratio * pack voltage, with no load."""
    _finite(ratio)
    if not 0 < ratio < 1:
        raise ValueError("target ratio must be strictly between 0 and 1")
    return -time_constant_s(resistance_ohm, capacitance_f) * math.log1p(-ratio)


def bus_requires_investigation(pack_v: float, bus_v_before_precharge: float, ratio: float = 0.2) -> bool:
    """Flag a live-bus observation, not its cause; a low reading is not proof of isolation.

    Residual charge, external backfeed, a closed path, and a stuck measurement
    can produce the same reading. The ratio is illustrative, not a safety limit.
    """
    _voltages(pack_v, 0.0)
    _finite(bus_v_before_precharge, ratio)
    if bus_v_before_precharge < 0 or not 0 < ratio < 1:
        raise ValueError("nonnegative bus voltage and 0 < ratio < 1 are required")
    return bus_v_before_precharge > ratio * pack_v


def close_verdict(pack_v: float, measured_v: float, ratio: float = 0.95) -> dict:
    """Check only an illustrative voltage condition; this demo never permits closing.

    The allowed field is retained for earlier callers but now stays false.
    Valid/fresh measurements, the observed rise, independent feedback,
    protection state, timing and component limits are outside this function.
    """
    _voltages(pack_v, 0.0)
    _finite(measured_v, ratio)
    if measured_v < 0 or not 0 < ratio < 1:
        raise ValueError("nonnegative measured voltage and 0 < ratio < 1 are required")
    target = pack_v * ratio
    voltage_condition_met = target <= measured_v <= pack_v
    if measured_v > pack_v:
        reason = "母线高于包压：需核查回灌或测量等原因，禁止合 K1"
    elif voltage_condition_met:
        reason = "仅到达示例电压条件，器件限制与时序/独立反馈未验证；本算例不授权合 K1"
    else:
        reason = "未到示例电压条件，禁止合 K1；若超时则中止，单个读数不能确定根因"
    return {"target_v": target, "voltage_condition_met": voltage_condition_met,
            "allowed": False, "reason": reason}


def main() -> None:
    pack, capacitance, resistance = 400.0, 0.001, 170.0
    tau = time_constant_s(resistance, capacitance)
    current = surge_current_a(pack, resistance)
    t90 = rise_time_s(0.90, resistance, capacitance)
    t95 = rise_time_s(0.95, resistance, capacitance)
    at_tau = bus_voltage_v(tau, pack, resistance, capacitance)
    at_three_tau = bus_voltage_v(3 * tau, pack, resistance, capacitance)
    ledger = energy_ledger_j(t95, pack, resistance, capacitance)
    print(f"参数：包压 {pack:.0f} V，母线电容 {capacitance * 1e3:.0f} mF，预充电阻 {resistance:.0f} Ω（理想无负载教学模型，不是实测）")
    print(f"时间常数 τ = RC = {tau:.2f} s；初始电流 I0 = U/R = {current:.2f} A；初始功率 {pack ** 2 / resistance:.2f} W")
    print(f"从零到 90% 需 {t90:.5f} s；到 95% 需 {t95:.5f} s；3τ = {3 * tau:.2f} s 只是约 95%")
    print(f"t = τ：母线 {at_tau:.0f} V；t = 3τ：母线 {at_three_tau:.0f} V")
    print(f"到95%：源供 {ledger['source_j']:.1f} J，电阻耗 {ledger['resistor_j']:.1f} J，电容储 {ledger['capacitor_j']:.1f} J；还差 {pack * 0.05:.0f} V")
    print("理想稳态：源供160 J，电阻耗80 J，电容储80 J；不是把已储在电容里的80 J烧掉")
    for bus in (at_tau, at_three_tau, 40.0):
        print(f"母线 {bus:.1f} V → {close_verdict(pack, bus)['reason']}")
    print("预充前380 V：需调查残压、外部回灌、仍闭合的通路或测量故障；不能直接记作K1粘连")
    print("实际合闸许可还需有效采样、上升轨迹、保护/时序、独立反馈及具体器件限制；本脚本均未验证")

    assert math.isclose(tau, 0.17) and math.isclose(current, 400 / 170)
    assert math.isclose(pulse_energy_j(capacitance, pack), 80.0)
    assert math.isclose(ledger["source_j"], ledger["resistor_j"] + ledger["capacitor_increase_j"])
    assert not close_verdict(pack, at_three_tau)["allowed"]
    assert bus_requires_investigation(pack, 380.0)
    print("checks passed: RC解析、90%/95%时间、源/阻/容能量；单电压不授权合闸或确定粘连")


if __name__ == "__main__":
    main()
