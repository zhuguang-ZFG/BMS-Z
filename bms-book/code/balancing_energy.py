#!/usr/bin/env python3
"""Passive vs active balancing: the two energy accounts of ch.9.5 (teaching demo).

Task: make up a 1 Ah imbalance between two cells (synthetic teaching values).
Account 1 (passive): bleed the high cell through R = 100 ohm at U = 4.0 V.
Account 2 (active): shuttle the charge in with I = 2 A, converter eta = 0.85.

Run: python code/balancing_energy.py
"""

from __future__ import annotations

U_CELL = 4.0        # V, cell voltage during balancing (synthetic)
R_BLEED = 100.0     # ohm, passive bleed resistor
DQ_AH = 1.0         # Ah, imbalance to correct
I_ACTIVE = 2.0      # A, active balancing current
ETA_ACTIVE = 0.85   # -, active converter efficiency (80-90% band)


def passive_account() -> tuple[float, float, float]:
    """Return (current A, time h, energy burned Wh)."""
    i = U_CELL / R_BLEED
    t = DQ_AH / i
    p = U_CELL * U_CELL / R_BLEED  # = i*i*R_BLEED
    return i, t, p * t


def active_account() -> tuple[float, float, float]:
    """Return (current A, time h, energy lost Wh)."""
    t = DQ_AH / I_ACTIVE
    e_delivered = U_CELL * DQ_AH
    e_drawn = e_delivered / ETA_ACTIVE
    return I_ACTIVE, t, e_drawn - e_delivered


def main() -> None:
    i_p, t_p, e_p = passive_account()
    i_a, t_a, e_a = active_account()

    print("balancing energy accounts (synthetic teaching values)")
    print(f"task: move {DQ_AH:.1f} Ah back into the weak cell at {U_CELL:.1f} V")
    print()
    print(f"{'':12s} {'I(A)':>6s} {'time(h)':>8s} {'energy(Wh)':>10s}")
    print(f"{'passive':12s} {i_p:6.2f} {t_p:8.1f} {e_p:10.1f}  (all burned as heat)")
    print(f"{'active':12s} {i_a:6.2f} {t_a:8.1f} {e_a:10.1f}  (conversion loss, eta=0.85)")
    print()
    print(f"speed:  active is {t_p / t_a:.0f}x faster")
    print(f"energy: passive burns {e_p / e_a:.1f}x the active loss")

    assert abs(t_p - 25.0) < 0.05, "passive should need 25.0 h for 1 Ah at 40 mA"
    assert abs(t_a - 0.5) < 0.05, "active should need 0.5 h for 1 Ah at 2 A"
    assert abs(e_p - 4.0) < 0.05, "passive should burn 4.0 Wh"
    assert abs(e_a - 0.7) < 0.05, "active should lose about 0.7 Wh"
    print("[PASS] passive 25.0 h / 4.0 Wh vs active 0.5 h / 0.7 Wh")


if __name__ == "__main__":
    main()
