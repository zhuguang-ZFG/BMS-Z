#!/usr/bin/env python3
"""Pack capacity is pinned by the weakest cell; teaching numbers are synthetic."""
from __future__ import annotations


def pack_capacity_ah(cells_ah: list[float]) -> float:
    """Series cells must each pass the same charge, so Ah do not add."""
    if not cells_ah or any(capacity <= 0 for capacity in cells_ah):
        raise ValueError("need at least one positive cell capacity")
    return min(cells_ah)


def dead_capacity_ah(cells_ah: list[float]) -> list[float]:
    """What every healthy cell leaves unused once the weakest one is empty."""
    usable = pack_capacity_ah(cells_ah)
    return [capacity - usable for capacity in cells_ah]


def pack_energy_wh(cells_ah: list[float], cell_voltage_v: float) -> float:
    """Block voltage is cells x cell voltage, charge is the weakest cell."""
    if cell_voltage_v <= 0:
        raise ValueError("cell voltage must be positive")
    return pack_capacity_ah(cells_ah) * len(cells_ah) * cell_voltage_v


def mirror_weakest_ah(average_ah: float, spread_ah: float) -> float:
    """Only valid when the spread sits symmetrically around the average."""
    if spread_ah < 0 or average_ah - spread_ah / 2 <= 0:
        raise ValueError("spread must leave a positive weakest cell")
    return average_ah - spread_ah / 2


def voltage_verdict(voltages_v: list[float], uvp_v: float) -> dict:
    """Average voltage hides the cell that trips protection."""
    if not voltages_v:
        raise ValueError("need at least one cell voltage")
    average = sum(voltages_v) / len(voltages_v)
    weakest = min(voltages_v)
    return {
        "average_v": average,
        "weakest_v": weakest,
        "average_would_release": average > uvp_v,
        "weakest_trips": weakest <= uvp_v,
        "release": weakest > uvp_v,
    }


def main() -> None:
    sample = [3.500] * 15 + [2.750]
    uvp = 2.800
    verdict = voltage_verdict(sample, uvp)

    four = [35.0, 50.0, 50.0, 50.0]
    usable = pack_capacity_ah(four)
    dead = dead_capacity_ah(four)
    dead_wh = [value * 3.2 for value in dead]

    symmetric = mirror_weakest_ah(2.00, 0.40)
    asymmetric = pack_capacity_ah([2.10, 2.00, 1.95, 1.80])
    wrong_shift = 2.00 - 0.30 / 2

    lfp = [50.0] * 11 + [46.0]
    lfp_energy = pack_energy_wh(lfp, 3.2)

    print(f"16 串样例：平均 {verdict['average_v']:.3f} V，最弱 {verdict['weakest_v']:.3f} V，UVP {uvp:.3f} V")
    print(
        "  按平均值判 → "
        + ("放行" if verdict["average_would_release"] else "保护")
        + "；按最弱单体判 → "
        + ("保护" if verdict["weakest_trips"] else "放行")
        + f"；结论 {'放行' if verdict['release'] else '禁止继续放电'}"
    )
    print(f"木桶 4 节 {four} Ah：整包可用 {usable:.0f} Ah，各节闲置 {', '.join(f'{value:.0f}' for value in dead)} Ah")
    print(f"  闲置容量按 3.2 V 折算，每节少放 {', '.join(f'{value:.0f}' for value in dead_wh)} Wh（串联能量按节累加）")
    print(f"对称极差：平均 2.00 Ah、极差 0.40 Ah → 最弱 {symmetric:.2f} Ah")
    print(f"不对称 2.10/2.00/1.95/1.80 Ah：最小值 {asymmetric:.2f} Ah；用平均减半个极差会错算成 {wrong_shift:.2f} Ah")
    print(f"12 串铁锂 11×50 Ah + 1×46 Ah：可用 {pack_capacity_ah(lfp):.0f} Ah，能量约 {lfp_energy:.1f} Wh ≈ {lfp_energy / 1000:.2f} kWh")

    assert verdict["average_would_release"] and verdict["weakest_trips"]
    assert not verdict["release"]
    assert usable == 35.0 and dead == [0.0, 15.0, 15.0, 15.0]
    assert dead_wh[1:] == [48.0, 48.0, 48.0]
    assert symmetric == 1.80 and asymmetric == 1.80 and wrong_shift > asymmetric
    assert pack_capacity_ah(lfp) == 46.0
    assert abs(lfp_energy - 1766.4) < 1e-9
    for bad in ([], [0.0]):
        try:
            pack_capacity_ah(bad)
        except ValueError:
            continue
        raise AssertionError("空列表或非正容量必须被拒绝")
    print("checks passed: 平均判据失效、串联 Ah 不再相加、对称公式的适用边界、12 串容量档差")


if __name__ == "__main__":
    main()
