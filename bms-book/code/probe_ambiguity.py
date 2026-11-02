#!/usr/bin/env python3
"""One probe cannot answer which state a cell is in; teaching numbers are synthetic."""
from __future__ import annotations

import math

V_HALF = 3.70
SLOPE = 0.080


def ocv_v(soc: float) -> float:
    """Teaching Nernst shape from stage 0: V = 3.70 + 0.080 ln(s/(1-s))."""
    if not 0 < soc < 1:
        raise ValueError("soc must lie strictly between 0 and 1")
    return V_HALF + SLOPE * math.log(soc / (1 - soc))


def slope_v_per_percent(soc: float) -> float:
    """dOCV/dsoc scaled to one percentage point of SOC."""
    if not 0 < soc < 1:
        raise ValueError("soc must lie strictly between 0 and 1")
    return SLOPE / (soc * (1 - soc)) / 100


def terminal_v(ocv: float, current_a: float, r0_ohm: float) -> float:
    """Charging current is positive, discharging negative; U = OCV + I*R0."""
    if r0_ohm < 0:
        raise ValueError("r0 must be nonnegative")
    return ocv + current_a * r0_ohm


def implied_r0(ocv: float, terminal: float, current_a: float) -> float:
    if current_a == 0:
        raise ValueError("a resting reading carries no resistance information")
    r0 = (terminal - ocv) / current_a
    if r0 < 0:
        raise ValueError("reading implies a negative resistance; the state guess is wrong")
    return r0


def soc_candidates(terminal: float, current_a: float, socs: list[float]) -> list[tuple[float, float]]:
    """Every (soc, r0) pair that reproduces one terminal-voltage reading."""
    found = []
    for soc in socs:
        try:
            found.append((soc, implied_r0(ocv_v(soc), terminal, current_a)))
        except ValueError:
            continue
    return found


def main() -> None:
    current = -20.0
    measured = 3.30
    socs = [0.30, 0.50, 0.70, 0.92]
    candidates = soc_candidates(measured, current, socs)

    print(f"只有电压探针：{current:.0f} A 放电时读到 {measured:.2f} V（教学示例，不是实测）")
    for soc, r0 in candidates:
        print(f"  SOC {soc:.0%} + 内阻 {r0 * 1000:.1f} mΩ → 也能读出 {terminal_v(ocv_v(soc), current, r0):.2f} V")
    print(f"同一读数有 {len(candidates)} 种解释：电压探针单独不能定 SOC，也不能定内阻")

    resting = [ocv_v(soc) for soc, _ in candidates]
    print(f"加电流探针并静置到 I = 0：开路电压变成 {', '.join(f'{value:.3f}' for value in resting)} V，这时读数才能落到一个 SOC 上")
    print(f"半满斜率 {slope_v_per_percent(0.50) * 1000:.1f} mV/百分点；s=0.08 → {ocv_v(0.08):.3f} V，s=0.92 → {ocv_v(0.92):.3f} V")
    print("温度探针补的是另一件事：内阻随温度和 SOH 漂移，同一 OCV 也可能来自不同的健康状态")
    print("证据表：每根探针写一行「直接读数」+「仍未确定」，行内不许把读数当结论")

    assert len(candidates) >= 2
    assert candidates[0][0] == 0.30 and candidates[-1][0] == 0.92
    for soc, r0 in candidates:
        assert abs(terminal_v(ocv_v(soc), current, r0) - measured) < 1e-12
    assert abs(ocv_v(0.50) - 3.70) < 1e-12
    assert abs(ocv_v(0.08) - 3.505) < 1e-3 and abs(ocv_v(0.92) - 3.895) < 1e-3
    assert abs(slope_v_per_percent(0.50) * 1000 - 3.2) < 1e-9
    assert len(set(round(value, 6) for value in resting)) == len(candidates)
    assert abs(terminal_v(ocv_v(0.50), 0.0, 0.020) - 3.70) < 1e-12
    for bad in (0.0, 1.0, -0.1):
        try:
            ocv_v(bad)
        except ValueError:
            continue
        raise AssertionError("SOC 必须在开区间内")
    try:
        implied_r0(3.70, 3.70, 0.0)
    except ValueError:
        pass
    else:
        raise AssertionError("静置读数不能反推内阻")
    print("checks passed: 单探针多解、静置后才可判 SOC、斜率与两点电压、静置反推内阻被拒绝")


if __name__ == "__main__":
    main()
