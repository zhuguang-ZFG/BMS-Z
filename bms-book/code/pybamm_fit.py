#!/usr/bin/env python3
"""Grade a first-order Thevenin ECM against a synthetic SPMe-flavored judge.

Judge (NOT PyBaMM, honest label): four-term OCV + R0*I + one diffusion RC
whose polarization resistance and time constant grow at both SOC ends, the
textbook behavior of charge transfer and solid-state diffusion there. The
cell starts rested, runs a charge leg up and a discharge leg down, with
1 mV noise from a fixed seed. The Thevenin is fitted by least squares on
the platform core (as a BMS calibrates on a mid-SOC HPPC), then graded in
the three SOC windows. Run: python code/pybamm_fit.py
"""

from __future__ import annotations

import math

import numpy as np

DT = 1.0            # s, one tick
Q_AH = 2.5          # Ah, teaching cell
CAP_C = Q_AH * 3600.0
R0 = 0.030          # Ohm, constant
R1_MID = 0.020      # Ohm, polarization resistance in the platform window
R1_END = 0.040      # Ohm, polarization resistance at both SOC ends
TAU_MID = 300.0     # s, diffusion time constant in the platform window
TAU_END = 900.0     # s, diffusion time constant at both SOC ends
SOC0 = 0.16         # rested start (charge = positive)
SEED = 42
NOISE_V = 1e-3      # 1 mV


def ocv_four_terms(soc: np.ndarray) -> np.ndarray:
    """Same four-term family as chapter 10: base + slope + two tanh bends."""
    return (3.2 + 0.8 * soc
            + 0.10 * np.tanh(10.0 * (soc - 0.2))
            - 0.05 * np.tanh(15.0 * (0.9 - soc)))


def end_ramp(soc: np.ndarray) -> np.ndarray:
    """0 in the platform core, 1 outside the 0.2 / 0.8 window edges."""
    low = np.clip((0.2 - soc) / 0.02, 0.0, 1.0)
    high = np.clip((soc - 0.8) / 0.02, 0.0, 1.0)
    return low + high


def synth_judge() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Synthetic terminal voltage over a charge leg and a discharge leg."""
    leg_up = int(0.77 * CAP_C / 2.30)    # mean 2.30 A
    leg_dn = int(0.91 * CAP_C / 2.30)
    current = np.empty(leg_up + leg_dn)
    for k in range(leg_up):              # charge: 0.16 -> 0.93
        current[k] = 3.5 if k % 600 < 150 else 1.9
    for k in range(leg_up, leg_up + leg_dn):  # discharge: 0.93 -> 0.02
        current[k] = -3.5 if (k - leg_up) % 600 < 150 else -1.9
    soc = SOC0 + np.cumsum(current) * DT / CAP_C

    ramp = end_ramp(soc)
    r1 = R1_MID + (R1_END - R1_MID) * ramp
    v_rc = np.zeros_like(current)
    for k in range(1, len(current)):
        tau = TAU_MID + (TAU_END - TAU_MID) * ramp[k]
        a = math.exp(-DT / tau)
        v_rc[k] = a * v_rc[k - 1] + r1[k] * (1.0 - a) * current[k - 1]

    rng = np.random.default_rng(SEED)
    v_clean = ocv_four_terms(soc) + R0 * current + v_rc
    v_meas = v_clean + rng.normal(0.0, NOISE_V, size=len(current))
    return current, soc, v_meas


def fit_thevenin(soc: np.ndarray, current: np.ndarray,
                 v_meas: np.ndarray, tau_grid: np.ndarray):
    """Least squares on the platform core over a tau grid.

    Basis: [OCV(soc), I, rc_unit] - OCV is taken from the judge's four-term
    curve, as a BMS takes it from a bench test; R0, R1 and tau are fitted.
    """
    cal = (soc >= 0.3) & (soc <= 0.7)
    ocv_col = ocv_four_terms(soc)
    best = None
    for tau in tau_grid:
        a = math.exp(-DT / tau)
        u = np.zeros_like(current)
        for k in range(1, len(current)):
            u[k] = a * u[k - 1] + (1.0 - a) * current[k - 1]
        basis = np.column_stack([ocv_col, current, u])
        coef, *_ = np.linalg.lstsq(basis[cal], v_meas[cal], rcond=None)
        resid = v_meas - basis @ coef
        sse_cal = float(np.sum(resid[cal] ** 2))
        if best is None or sse_cal < best[0]:
            best = (sse_cal, float(tau), coef, resid)
    assert best is not None
    return best


def main() -> None:
    current, soc, v_meas = synth_judge()
    print("synthetic SPMe-flavored judge (NOT a PyBaMM run; teaching values)")
    print(f"drive: {len(current)} s charge+discharge legs, "
          f"soc {soc[0]:.2f} -> {soc.max():.2f} -> {soc[-1]:.2f}, "
          f"noise 1 mV, seed {SEED}")
    print("fit: first-order Thevenin by least squares, platform core only")

    tau_grid = np.arange(60.0, 1201.0, 10.0)
    _, tau_est, coef, resid = fit_thevenin(soc, current, v_meas, tau_grid)
    scale = float(coef[0])
    r0_est, r1_est = float(coef[1]), float(coef[2])

    print(f"OCV scale est {scale:.4f} (true 1.0000), "
          f"R0 est {r0_est*1e3:6.2f} mOhm (true {R0*1e3:.2f}), "
          f"R1 est {r1_est*1e3:6.2f} mOhm (mid true {R1_MID*1e3:.2f}), "
          f"tau est {tau_est:.0f} s (mid true {TAU_MID:.0f})")

    windows = [("soc<0.20       ", soc < 0.2),
               ("0.20<=soc<=0.80", (soc >= 0.2) & (soc <= 0.8)),
               ("soc>0.80       ", soc > 0.8)]
    rmses = []
    for name, mask in windows:
        rmse = float(np.sqrt(np.mean(resid[mask] ** 2))) * 1e3
        rmses.append(rmse)
        print(f"RMSE {name}: {rmse:6.2f} mV  (n={int(np.count_nonzero(mask))})")
    low, mid, high = rmses
    print(f"ends are {0.5 * (low + high) / mid:.1f}x the platform window "
          f"on average -> structure hides at the SOC ends")

    assert 0.995 < scale < 1.005, "OCV scale diverged"
    assert 28e-3 < r0_est < 32e-3, "R0 fit diverged"
    assert 17e-3 < r1_est < 23e-3, "R1 fit diverged"
    assert 250.0 < tau_est < 500.0, "tau fit diverged"
    assert mid < low / 3.0 and mid < high / 3.0, "window contrast missing"
    print("[PASS] platform fit converged; its RMSE < 1/3 of both ends, so "
          "the constant-parameter ECM fails at the SOC ends")


if __name__ == "__main__":
    main()
