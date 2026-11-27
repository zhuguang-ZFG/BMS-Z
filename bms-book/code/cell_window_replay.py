#!/usr/bin/env python3
"""Replay chapter 3's four arithmetic examples with explicit SOC units.

All values are synthetic teaching examples, not cell specifications.
"""
from __future__ import annotations

import math


def _finite(*values: float) -> None:
    if not all(math.isfinite(value) for value in values):
        raise ValueError("all inputs must be finite")


def voltage_window_gap_v(detector_v: float, cutoff_v: float) -> tuple[float, float]:
    """Return the absolute voltage gap and its percentage of the cutoff voltage."""
    _finite(detector_v, cutoff_v)
    if cutoff_v <= 0 or detector_v <= cutoff_v:
        raise ValueError("cutoff must be positive and detector must sit above it")
    gap_v = detector_v - cutoff_v
    return gap_v, gap_v / cutoff_v * 100.0


def soc_uncertainty_pp(error_mv: float, slope_mv_per_percent: float) -> float:
    """Convert a local voltage error to SOC percentage points, not relative percent."""
    _finite(error_mv, slope_mv_per_percent)
    if error_mv < 0 or slope_mv_per_percent <= 0:
        raise ValueError("voltage error must be nonnegative and slope must be positive")
    return error_mv / slope_mv_per_percent


def relative_soc_error_percent(uncertainty_pp: float, soc_percent: float) -> float:
    """Convert percentage points to relative percent using an explicit SOC baseline."""
    _finite(uncertainty_pp, soc_percent)
    if uncertainty_pp < 0 or not 0 < soc_percent <= 100:
        raise ValueError("uncertainty must be nonnegative and reference SOC must lie in (0, 100]")
    return uncertainty_pp / soc_percent * 100.0


def main() -> None:
    gap_v, gap_percent = voltage_window_gap_v(4.20, 3.65)
    print(f"4.20 V - 3.65 V = {gap_v:.2f} V，占 3.65 V 的 {gap_percent:.0f}%")

    for slope_mv, error_mv in ((0.75, 20.0), (0.75, 2.0), (10.0, 20.0)):
        uncertainty_pp = soc_uncertainty_pp(error_mv, slope_mv)
        print(
            f"斜率 {slope_mv:g} mV/个百分点 + 误差 {error_mv:.0f} mV "
            f"-> SOC 不确定度约 {uncertainty_pp:.1f} 个百分点"
        )

    reference_soc = 50.0
    uncertainty_pp = soc_uncertainty_pp(20.0, 0.75)
    relative_percent = relative_soc_error_percent(uncertainty_pp, reference_soc)
    print(
        f"SOC={reference_soc:.1f}% 时约合 {relative_percent:.1f}% 相对误差；"
        "百分点与相对百分比不能混写"
    )

    for c_rate in (0.5, 1.0, 2.0):
        print(f"{c_rate}C @ 50 Ah = {c_rate * 50:.0f} A")
    print(f"10 A 在 10 Ah 上是 {10 / 10:.1f}C，在 50 Ah 上是 {10 / 50:.1f}C")
    print(f"16 串 × 3.65 V = {16 * 3.65:.1f} V")

    assert math.isclose(gap_v, 0.55) and math.isclose(gap_percent, 100 * 0.55 / 3.65)
    assert math.isclose(uncertainty_pp, 20.0 / 0.75)
    assert math.isclose(relative_percent, 100 * (20.0 / 0.75) / reference_soc)
    print("checks passed: 电压窗口、SOC 百分点与相对百分比、倍率与串联电压")


if __name__ == "__main__":
    main()
