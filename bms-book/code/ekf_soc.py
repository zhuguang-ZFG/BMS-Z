#!/usr/bin/env python3
"""Two-state EKF for SOC estimation (teaching demo).

State: x = [SOC, U_rc]. Model: Thevenin (R0 + one RC branch).
Convention: charge current is positive (same as BMS-Z).

Run: python code/ekf_soc.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def ocv(soc: float) -> float:
    soc = min(max(soc, 0.0), 1.0)
    return (
        3.2
        + 0.8 * soc
        + 0.20 * math.tanh((soc - 0.05) * 30.0)
        + 0.05 * math.tanh((soc - 0.90) * 15.0)
    )


def docv(soc: float) -> float:
    soc = min(max(soc, 0.0), 1.0)
    t1 = math.tanh((soc - 0.05) * 30.0)
    t2 = math.tanh((soc - 0.90) * 15.0)
    return 0.8 + 0.20 * 30.0 * (1 - t1 * t1) + 0.05 * 15.0 * (1 - t2 * t2)


@dataclass
class Params:
    q_ah: float
    r0: float
    r1: float
    c1: float

    @property
    def tau(self) -> float:
        return self.r1 * self.c1


def profile(t: float) -> float:
    """A 1-hour cycle: 20 min discharge (5 A), 10 min rest, 20 min charge (4 A), 10 min rest."""
    if t < 1200:
        return -5.0
    if t < 1800:
        return 0.0
    if t < 3000:
        return 4.0
    return 0.0


def rmse(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b, strict=True)) / len(a))


def joseph_covariance(p00: float, p01: float, p10: float, p11: float,
                      k0: float, k1: float, c0: float, c1: float,
                      r_var: float) -> tuple[float, float, float, float]:
    """Joseph-form covariance update for a two-state, scalar observation."""
    m00, m01 = 1 - k0 * c0, -k0 * c1
    m10, m11 = -k1 * c0, 1 - k1 * c1
    t00, t01 = m00 * p00 + m01 * p10, m00 * p01 + m01 * p11
    t10, t11 = m10 * p00 + m11 * p10, m10 * p01 + m11 * p11
    return (
        t00 * m00 + t01 * m01 + r_var * k0 * k0,
        t00 * m10 + t01 * m11 + r_var * k0 * k1,
        t10 * m00 + t11 * m01 + r_var * k1 * k0,
        t10 * m10 + t11 * m11 + r_var * k1 * k1,
    )


def run() -> tuple[float, float, float]:
    dt = 1.0
    n = 3600
    true = Params(9.5, 0.033, 0.016, 2200.0)
    model = Params(10.0, 0.033, 0.016, 2200.0)
    bias = 0.002  # +2 mA current-sensor bias

    soc_true = 0.80
    urc_true = 0.0
    soc_coulomb = 0.70
    soc_ekf = 0.70
    urc_ekf = 0.0
    p00, p01, p10, p11 = 1e-2, 0.0, 0.0, 1e-4
    q00, q11 = 2e-6, 1e-7
    r_var = 2.5e-5

    err_coulomb: list[float] = []
    err_ekf: list[float] = []
    a = math.exp(-dt / model.tau)

    for k in range(n):
        t = k * dt
        i_true = profile(t)
        i_meas = i_true + bias

        # true cell
        soc_true += i_true * dt / 3600.0 / true.q_ah
        urc_true = math.exp(-dt / true.tau) * urc_true + true.r1 * (1 - math.exp(-dt / true.tau)) * i_true
        v_meas = ocv(soc_true) + true.r0 * i_true + urc_true + 0.005 * math.sin(k * 0.7)

        # pure coulomb counter (biased current, wrong capacity)
        soc_coulomb += i_meas * dt / 3600.0 / model.q_ah

        # EKF predict
        soc_ekf = soc_ekf + dt / 3600.0 / model.q_ah * i_meas
        urc_ekf = a * urc_ekf + model.r1 * (1 - a) * i_meas
        # P = A P A^T + Q, A = diag(1, a)
        p00 = p00 + q00
        p01 = p01 * a
        p10 = p10 * a
        p11 = p11 * a * a + q11

        # EKF update
        c0 = docv(soc_ekf)
        c1 = 1.0
        v_pred = ocv(soc_ekf) + model.r0 * i_meas + urc_ekf
        s = c0 * (p00 * c0 + p01 * c1) + c1 * (p10 * c0 + p11 * c1) + r_var
        k0 = (p00 * c0 + p01 * c1) / s
        k1 = (p10 * c0 + p11 * c1) / s
        residual = v_meas - v_pred
        soc_ekf += k0 * residual
        urc_ekf += k1 * residual

        # Joseph form: P = (I - K C) P (I - K C)^T + K R K^T.
        p00, p01, p10, p11 = joseph_covariance(
            p00, p01, p10, p11, k0, k1, c0, c1, r_var,
        )
        assert all(math.isfinite(value) for value in (p00, p01, p10, p11))
        assert p00 >= 0 and p11 >= 0
        assert math.isclose(p01, p10, rel_tol=1e-10, abs_tol=1e-14)
        assert p00 * p11 - p01 * p10 >= -1e-18
        soc_ekf = min(max(soc_ekf, 0.0), 1.0)

        if k >= 300:
            err_coulomb.append(soc_coulomb - soc_true)
            err_ekf.append(soc_ekf - soc_true)

    return (
        rmse(err_coulomb, [0.0] * len(err_coulomb)) * 100,
        rmse(err_ekf, [0.0] * len(err_ekf)) * 100,
        soc_true,
    )


@dataclass
class Tick:
    """One traced EKF tick, for the walkthrough table in 第 27 章 §27.2."""

    k: int
    soc_predicted: float
    residual_v: float
    s_var: float
    k_soc: float      # K's first entry, in SOC per volt
    kh: float         # K0 * C0, dimensionless share of the residual taken
    soc_updated: float
    soc_true: float
    nis: float
    p00: float
    p01: float
    p11: float

    @property
    def correlation(self) -> float:
        """Correlation between the SOC and polarisation errors after the update."""
        spread = math.sqrt(self.p00 * self.p11)
        if spread == 0:
            raise ValueError("correlation is undefined for a degenerate covariance")
        return self.p01 / spread


def first_ticks(count: int = 4) -> list[Tick]:
    """Re-run the opening ticks of run() and report every published intermediate.

    书里 §27.2 的两张表（新息/尺度/采信比例、协方差非对角项）逐格引用这里的返回值。
    刻意与 run() 用同一组初值与同一套更新式，但不改 run()：§27.4 的 RMSE 结论
    依赖 run() 的逐字节行为，两者各自独立可复算。
    """
    if count < 1:
        raise ValueError("count must be at least 1")
    dt = 1.0
    true = Params(9.5, 0.033, 0.016, 2200.0)
    model = Params(10.0, 0.033, 0.016, 2200.0)
    bias = 0.002

    soc_true, urc_true = 0.80, 0.0
    soc_ekf, urc_ekf = 0.70, 0.0
    p00, p01, p10, p11 = 1e-2, 0.0, 0.0, 1e-4
    q00, q11 = 2e-6, 1e-7
    r_var = 2.5e-5
    a = math.exp(-dt / model.tau)
    at = math.exp(-dt / true.tau)

    ticks: list[Tick] = []
    for k in range(count):
        i_true = profile(k * dt)
        i_meas = i_true + bias

        soc_true += i_true * dt / 3600.0 / true.q_ah
        urc_true = at * urc_true + true.r1 * (1 - at) * i_true
        v_meas = ocv(soc_true) + true.r0 * i_true + urc_true + 0.005 * math.sin(k * 0.7)

        soc_pre = soc_ekf + dt / 3600.0 / model.q_ah * i_meas
        urc_pre = a * urc_ekf + model.r1 * (1 - a) * i_meas
        p00, p01, p10, p11 = p00 + q00, p01 * a, p10 * a, p11 * a * a + q11

        c0, c1 = docv(soc_pre), 1.0
        residual = v_meas - (ocv(soc_pre) + model.r0 * i_meas + urc_pre)
        s = c0 * (p00 * c0 + p01 * c1) + c1 * (p10 * c0 + p11 * c1) + r_var
        k0 = (p00 * c0 + p01 * c1) / s
        k1 = (p10 * c0 + p11 * c1) / s
        soc_ekf = min(max(soc_pre + k0 * residual, 0.0), 1.0)
        urc_ekf = urc_pre + k1 * residual
        p00, p01, p10, p11 = joseph_covariance(
            p00, p01, p10, p11, k0, k1, c0, c1, r_var,
        )
        ticks.append(Tick(
            k=k, soc_predicted=soc_pre, residual_v=residual, s_var=s,
            k_soc=k0, kh=k0 * c0, soc_updated=soc_ekf, soc_true=soc_true,
            nis=residual * residual / s, p00=p00, p01=p01, p11=p11,
        ))
    return ticks


def main() -> None:
    c_rmse, e_rmse, final_true = run()
    print(f"true final SOC: {final_true * 100:.2f}%")
    print(f"coulomb RMSE:   {c_rmse:.4f}%")
    print(f"EKF RMSE:       {e_rmse:.4f}%")
    assert e_rmse < c_rmse / 2, "EKF should beat pure coulomb counting"
    assert e_rmse < 2.0, "EKF should stay within 2% on this synthetic case"
    print("checks passed: EKF beats coulomb by >2x and stays under 2%")

    print("\nfirst ticks (第 27 章 §27.2 的两张表):")
    print(f"{'k':>2} {'z-h/mV':>9} {'sqrt(S)/mV':>11} {'K0':>8} {'K0*C0':>7} "
          f"{'NIS':>7} {'SOC':>9} {'rho':>8}")
    for tick in first_ticks():
        print(f"{tick.k:>2} {tick.residual_v * 1000:>+9.3f} "
              f"{math.sqrt(tick.s_var) * 1000:>11.3f} {tick.k_soc:>8.4f} "
              f"{tick.kh:>7.3f} {tick.nis:>7.4f} {tick.soc_updated:>9.6f} "
              f"{tick.correlation:>+8.4f}")


if __name__ == "__main__":
    main()
