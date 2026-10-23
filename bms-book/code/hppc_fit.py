#!/usr/bin/env python3
"""HPPC pulse -> R0, R1, C1 recovery (teaching demo).

Synthetic cell, noise sigma_v = 1 mV, noise sigma_i = 5 mA.
Run: python code/hppc_fit.py
"""

from __future__ import annotations

import math

import numpy as np


def simulate_pulse(
    r0: float = 0.033,
    r1: float = 0.016,
    c1: float = 2200.0,
    pulse_a: float = 3.0,
    dt: float = 0.1,
    pre_s: float = 60.0,
    pulse_s: float = 10.0,
    rest_s: float = 120.0,
    seed: int = 7,
):
    rng = np.random.default_rng(seed)
    tau = r1 * c1
    n_pre = int(pre_s / dt)
    n_pulse = int(pulse_s / dt)
    n_rest = int(rest_s / dt)
    t = np.arange(n_pre + n_pulse + n_rest) * dt
    current = np.zeros_like(t)
    current[n_pre:n_pre + n_pulse] = pulse_a

    urc = np.zeros_like(t)
    for k in range(1, len(t)):
        a = math.exp(-dt / tau)
        urc[k] = a * urc[k - 1] + r1 * (1 - a) * current[k - 1]
    ocv = 3.75  # constant around SOC 0.5 for this demo
    voltage = ocv + r0 * current + urc
    voltage += rng.normal(0, 1e-3, size=len(t))
    current_meas = current + rng.normal(0, 5e-3, size=len(t))
    return t, voltage, current_meas, n_pre, n_pulse


def fit_relaxation(t_rest: np.ndarray, v_rest: np.ndarray, tau_grid=None):
    if tau_grid is None:
        tau_grid = np.arange(3.0, 120.5, 0.5)
    best = None
    for tau in tau_grid:
        basis = np.column_stack([np.ones_like(t_rest), np.exp(-t_rest / tau)])
        coef, *_ = np.linalg.lstsq(basis, v_rest, rcond=None)
        pred = basis @ coef
        sse = float(np.sum((v_rest - pred) ** 2))
        if best is None or sse < best[0]:
            best = (sse, float(tau), float(coef[0]), float(coef[1]))
    return best


def main() -> None:
    r0_true, r1_true, c1_true = 0.033, 0.016, 2200.0
    pulse_a = 3.0
    t, v, i_meas, n_pre, n_pulse = simulate_pulse(r0=r0_true, r1=r1_true, c1=c1_true)

    # R0: mean 1 s before pulse vs mean first 0.3 s of pulse
    v_pre = float(np.mean(v[n_pre - 10:n_pre]))
    v_post = float(np.mean(v[n_pre:n_pre + 3]))
    i_pre = float(np.mean(i_meas[n_pre - 10:n_pre]))
    i_post = float(np.mean(i_meas[n_pre:n_pre + 3]))
    r0_est = (v_post - v_pre) / (i_post - i_pre)

    # RC fit on the full 120 s rest
    rest = slice(n_pre + n_pulse, None)
    t_rest = t[rest] - t[n_pre + n_pulse]
    best = fit_relaxation(t_rest, v[rest])
    assert best is not None
    _, tau_est, _, amp = best
    amp_corr = amp / (1.0 - math.exp(-10.0 / tau_est))
    r1_est = amp_corr / pulse_a
    c1_est = tau_est / r1_est

    # Same data truncated to a 40 s window (the classic trap)
    mask = t_rest <= 40.0
    best40 = fit_relaxation(t_rest[mask], v[rest][mask])
    assert best40 is not None
    _, tau40, _, amp40 = best40
    r1_40 = amp40 / (1.0 - math.exp(-10.0 / tau40)) / pulse_a
    err_r1_40 = abs(r1_40 - r1_true) / r1_true * 100

    print(f"R0  true {r0_true*1e3:6.2f} mOhm  est {r0_est*1e3:6.2f} mOhm  "
          f"err {abs(r0_est-r0_true)/r0_true*100:5.2f}%")
    print(f"R1  true {r1_true*1e3:6.2f} mOhm  est {r1_est*1e3:6.2f} mOhm  "
          f"err {abs(r1_est-r1_true)/r1_true*100:5.2f}%")
    print(f"C1  true {c1_true:6.0f} F     est {c1_est:6.0f} F     "
          f"err {abs(c1_est-c1_true)/c1_true*100:5.2f}%")
    print(f"tau true {r1_true*c1_true:6.1f} s     est {tau_est:6.1f} s")
    print(f"40 s window: R1 err {err_r1_40:5.1f}% (expected worse than the 120 s fit)")

    assert abs(r0_est - r0_true) / r0_true < 0.05
    assert abs(r1_est - r1_true) / r1_true < 0.10
    assert abs(c1_est - c1_true) / c1_true < 0.10
    assert err_r1_40 > abs(r1_est - r1_true) / r1_true * 100
    print("checks passed: full-window fit recovers R0/R1/C1; 40 s window is worse")


if __name__ == "__main__":
    main()
