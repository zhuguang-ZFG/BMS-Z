#!/usr/bin/env python3
"""Unbalanced-bridge insulation monitoring demo (chapter 32).

Model (synthetic teaching values, not any real pack's spec):

    Battery total voltage U; insulation resistance R+ (positive pole to
    chassis) and R- (negative pole to chassis); known bridge resistor Rb.
    Conductances: gp = 1/R+, gm = 1/R-, gb = 1/Rb.

    Measurement 1 (Rb between + pole and chassis), read U1 (+ to ground):
        U1 = U * gm / (gp + gm + gb)
    Measurement 2 (Rb between - pole and chassis), read U2 (- to ground):
        U2 = U * gp / (gp + gm + gb)

    Two equations, two unknowns, closed form (derivation):
        add and divide the two readings to get gp + gm + gb, then
        R+ = Rb * (U - U1 - U2) / U2
        R- = Rb * (U - U1 - U2) / U1        (U1 = 0 means R- = inf)

    Balanced bridge (Rb on both poles at once, midpoint Vmid) comparison:
        Vmid = U * (gm + gb) / (gp + gm + 2*gb)
    When R+ = R- the midpoint stays at exactly U/2 for ANY value, so a
    symmetric degradation is invisible to the balanced bridge.

    Y-capacitance settling: chassis-side Y caps charge through the bridge
    resistor; tau = C_Y * (Rb par (R+ + R-)), wait >= 5*tau before the
    second sample, otherwise U2 is still crawling and the solve is wrong.

Cases (400 V system; GB/T 18384 teaching threshold 100 ohm/V -> 40 kohm,
see chapter 32 for the "check the current standard text itself" caveat):
    A normal      R+ = 500 kohm, R- = inf
    B borderline  R+ = 40 kohm,  R- = inf
    C symmetric   R+ = R- = 100 kohm   (missed by balanced bridge)

Run: python code/insulation_bridge.py
"""

from __future__ import annotations

import math

U = 400.0        # pack voltage (V), synthetic teaching value
RB = 100e3       # known bridge resistor (ohm)
R_FAULT = 40e3   # insulation fault threshold: 400 V * 100 ohm/V
C_Y = 1e-6       # chassis-side Y capacitance (F)
U_HALF = U / 2.0  # balanced-bridge midpoint of a healthy symmetric system


def measure(u, rp, rm, rb):
    """Steady-state readings (U1, U2, Vmid) for an insulation pair."""
    gp = 0.0 if math.isinf(rp) else 1.0 / rp
    gm = 0.0 if math.isinf(rm) else 1.0 / rm
    gb = 1.0 / rb
    u1 = u * gm / (gp + gm + gb)                  # Rb on + pole
    u2 = u * gp / (gp + gm + gb)                  # Rb on - pole
    vmid = u * (gm + gb) / (gp + gm + 2.0 * gb)   # balanced bridge
    return u1, u2, vmid


def solve(u, u1, u2, rb):
    """Closed-form R+, R- from the two readings (see header derivation)."""
    rest = u - u1 - u2
    rp = rb * rest / u2
    rm = math.inf if u1 == 0.0 else rb * rest / u1
    return rp, rm


def fmt_r(r):
    """ASCII-safe resistance format."""
    return "    inf" if math.isinf(r) else f"{r / 1e3:7.1f}k"


def verdict(rp, rm):
    m = min(rp, rm)
    if m <= R_FAULT * (1.0 + 1e-9):   # 1e-9 absorbs float noise on the edge
        return "FAULT"
    if m <= 2.0 * R_FAULT:
        return "WARN"
    return "NORMAL"


def tau_wait(rp, rm):
    """tau = C_Y * (Rb par (R+ + R-)); recommended wait = 5*tau."""
    series = rp + rm
    req = RB if math.isinf(series) else RB * series / (RB + series)
    tau = C_Y * req
    return req, tau, 5.0 * tau


def main():
    cases = [
        ("A normal    ", 500e3, math.inf),
        ("B borderline", 40e3, math.inf),
        ("C symmetric ", 100e3, 100e3),
    ]
    print("unbalanced-bridge insulation demo (chapter 32, synthetic values)")
    print(f"U = {U:.0f} V, Rb = {RB / 1e3:.0f} kohm, "
          f"fault threshold min(R+, R-) <= {R_FAULT / 1e3:.0f} kohm "
          f"(100 ohm/V), C_Y = 1.0 uF")
    print(f"balanced-bridge baseline: healthy symmetric 1 Mohm -> "
          f"Vmid = {U_HALF:.2f} V (every symmetric pair gives the same Vmid)")
    print()
    res = {}
    wait_max = 0.0
    for name, rp_t, rm_t in cases:
        u1, u2, vmid = measure(U, rp_t, rm_t, RB)
        rp, rm = solve(U, u1, u2, RB)
        v = verdict(rp, rm)
        res[name.strip()[0]] = (rp, rm, u1, u2, vmid, v)
        req, tau, wait = tau_wait(rp_t, rm_t)
        wait_max = max(wait_max, wait)
        bal = "detected" if abs(vmid - U_HALF) > 1.0 else "MISSED"
        print(f"case {name} true R+ = {fmt_r(rp_t)} ohm, "
              f"R- = {fmt_r(rm_t)} ohm")
        print(f"  unbalanced bridge: U1 = {u1:7.2f} V, U2 = {u2:7.2f} V")
        print(f"  solved:            R+ = {fmt_r(rp)} ohm, "
              f"R- = {fmt_r(rm)} ohm -> {v}")
        print(f"  balanced bridge:   Vmid = {vmid:7.2f} V -> {bal} "
              f"(midpoint pinned at U/2 for symmetric pairs)")
        print(f"  Y-cap settling:    Req = {req / 1e3:6.1f} kohm, "
              f"tau = {1e3 * tau:6.1f} ms, wait >= 5*tau = {wait:.2f} s")
    print()
    print(f"recommended wait before the 2nd measurement: >= {wait_max:.2f} s")
    print()
    ra = res["A"]
    rb = res["B"]
    rc = res["C"]
    checks = [
        ("case A solved R+ = 500 kohm", abs(ra[0] - 500e3) < 1.0),
        ("case A R- = inf", math.isinf(ra[1])),
        ("case A verdict NORMAL", ra[5] == "NORMAL"),
        ("case B solved R+ = 40 kohm", abs(rb[0] - 40e3) < 0.1),
        ("case B verdict FAULT", rb[5] == "FAULT"),
        ("case C symmetric: U1 == U2", abs(rc[2] - rc[3]) < 1e-9),
        ("case C solved R+ = R- = 100 kohm",
         abs(rc[0] - 100e3) < 0.1 and abs(rc[1] - 100e3) < 0.1),
        ("case C MISSED by balanced bridge (Vmid pinned at U/2)",
         abs(rc[4] - U_HALF) < 0.01),
        ("case C detected by unbalanced bridge", abs(rc[0] - 100e3) < 0.1),
        ("U1 + U2 < U for every case",
         all(r[2] + r[3] < U for r in (ra, rb, rc))),
        ("wait recommendation >= 0.50 s", wait_max >= 0.5 - 1e-12),
    ]
    n_ok = 0
    for cname, ok in checks:
        n_ok += 1 if ok else 0
        print(f"  [{'PASS' if ok else 'FAIL'}] {cname}")
    all_ok = n_ok == len(checks)
    print()
    print(f"[{'PASS' if all_ok else 'FAIL'}] {n_ok}/{len(checks)} checks: "
          "balanced bridge misses symmetric degradation, "
          "unbalanced bridge catches it")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
