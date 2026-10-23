#!/usr/bin/env python3
"""Exact constant-parameter thermal and capacitor energy ledgers.

Synthetic teaching values only; no battery abuse, high-voltage control or
hardware interfaces. Charge-positive convention is irrelevant to I squared.
"""
from __future__ import annotations

import math


def thermal_step(current_a: float, resistance_ohm: float, rth_k_w: float,
                 cth_j_k: float, ambient_c: float, initial_c: float, time_s: float) -> float:
    if resistance_ohm < 0 or rth_k_w <= 0 or cth_j_k <= 0 or time_s < 0:
        raise ValueError("positive thermal parameters and nonnegative time are required")
    steady_c = ambient_c + current_a ** 2 * resistance_ohm * rth_k_w
    return steady_c + (initial_c - steady_c) * math.exp(-time_s / (rth_k_w * cth_j_k))


def thermal_current_limit(resistance_ohm: float, rth_k_w: float, cth_j_k: float,
                          ambient_c: float, initial_c: float, limit_c: float, time_s: float) -> float:
    if resistance_ohm <= 0 or rth_k_w <= 0 or cth_j_k <= 0 or time_s <= 0:
        raise ValueError("positive parameters and horizon are required")
    # If already over the temperature limit, this teaching policy disallows load.
    if initial_c > limit_c:
        return 0.0
    a = math.exp(-time_s / (rth_k_w * cth_j_k))
    numerator = limit_c - ambient_c - (initial_c - ambient_c) * a
    return math.sqrt(max(0.0, numerator) / (resistance_ohm * rth_k_w * (1 - a)))


def discharge_ledger(capacitance_f: float, voltage_v: float, target_v: float,
                     resistance_ohm: float) -> tuple[float, float, float]:
    if capacitance_f <= 0 or resistance_ohm <= 0 or not 0 < target_v < voltage_v:
        raise ValueError("positive RC and 0 < target < initial voltage are required")
    time_s = capacitance_f * resistance_ohm * math.log(voltage_v / target_v)
    released_j = capacitance_f * (voltage_v ** 2 - target_v ** 2) / 2
    peak_w = voltage_v ** 2 / resistance_ohm
    return time_s, released_j, peak_w


def main() -> None:
    # R=49 mOhm, Rth=1 K/W, Cth=120 J/K, tau=120 s. No entropy term.
    for horizon in (10, 120, 600):
        end_c = thermal_step(10, 0.049, 1, 120, 25, 25, horizon)
        limit_a = thermal_current_limit(0.049, 1, 120, 25, 25, 40, horizon)
        print(f"thermal {horizon:3d} s: 10 A -> {end_c:.3f} C; 40 C limit -> {limit_a:.3f} A")
        assert math.isclose(thermal_step(limit_a, 0.049, 1, 120, 25, 25, horizon), 40)
    assert math.isclose(thermal_step(10, 0.049, 1, 120, 25, 25, 120),
                        thermal_step(-10, 0.049, 1, 120, 25, 25, 120))
    assert thermal_current_limit(0.049, 1, 120, 25, 45, 40, 120) == 0
    for resistor in (200, 47000):
        time_s, energy_j, peak_w = discharge_ledger(0.001, 400, 60, resistor)
        print(f"discharge {resistor:5d} Ohm: {time_s:.3f} s; released {energy_j:.3f} J; peak {peak_w:.3f} W")
        assert math.isclose(400 * math.exp(-time_s / (0.001 * resistor)), 60)
        assert math.isclose(energy_j + 0.001 * 60 ** 2 / 2, 80)
    hot_start = thermal_current_limit(0.049, 1, 120, 25, 35, 40, 120)
    print(f"hot start 35 C / 120 s: {hot_start:.3f} A")
    print("checks passed: exact thermal boundary, sign symmetry and capacitor energy conservation")


if __name__ == "__main__":
    main()
