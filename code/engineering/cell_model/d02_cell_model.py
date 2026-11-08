"""Teaching experiments for D02: model order, zero-order hold, and hysteresis.

Scenario ``D02-model-order`` (synthetic): a 2RC "true" cell is identified with a
1RC and a 2RC rest-tail fit. The 1RC fit is excellent in a late window but keeps a
systematic early-window residual — the missing fast branch. Also a hysteresis
counterexample: identical terminal voltage under charge vs discharge history maps
to two different OCVs, so SOC inversion without history is off by the hysteresis
width divided by the OCV slope.
"""
from __future__ import annotations

import argparse
import json
import math
from functools import lru_cache

from pathlib import Path

SCENARIO_ID = "D02-model-order"
HYSTERESIS_SCENARIO_ID = "D02-hysteresis-inversion"

# 2RC teaching truth (extends the S2 main scenario with a fast branch).
Q_AH = 2.0
R0_OHM = 0.020
R1_OHM, C1_F = 0.015, 3000.0   # tau1 = 45 s (S2 dominant pole)
R2_OHM, C2_F = 0.005, 200.0    # tau2 = 1 s  (fast branch new in D02)
TAU1_S = R1_OHM * C1_F
TAU2_S = R2_OHM * C2_F
OCV_SLOPE_V_PER_SOC = 0.8
Z0 = 0.60
DT_S = 0.5
PULSE_A = 2.0
PULSE_S = 10.0
REST1_S = 60.0
REST2_S = 180.0

HYSTERESIS_WIDTH_V = 0.010  # charge vs discharge OCV branch gap at z = 0.5 (teaching)


def ocv(z: float) -> float:
    return 3.6 + OCV_SLOPE_V_PER_SOC * (z - 0.5)


def simulate_2rc(pulse_a: float = PULSE_A) -> list[dict]:
    """ZOH-exact 2RC simulation: rest, pulse, long rest. Discharge positive."""
    rows = []
    vp1 = vp2 = 0.0
    z = Z0
    a1 = math.exp(-DT_S / TAU1_S)
    a2 = math.exp(-DT_S / TAU2_S)
    total_s = REST1_S + PULSE_S + REST2_S
    t = 0.0
    while t <= total_s + 1e-9:
        i = pulse_a if REST1_S <= t < REST1_S + PULSE_S else 0.0
        v = ocv(z) - i * R0_OHM - vp1 - vp2
        rows.append({"t": round(t, 3), "i_a": i, "z": z, "vp1": vp1, "vp2": vp2, "v": v})
        z = z - i * DT_S / (3600.0 * Q_AH)
        vp1 = a1 * vp1 + R1_OHM * (1.0 - a1) * i
        vp2 = a2 * vp2 + R2_OHM * (1.0 - a2) * i
        t += DT_S
    return rows


def rest_tail(rows: list[dict]) -> list[tuple[float, float]]:
    """(t_since_release, v) samples from the post-pulse rest."""
    tail = [(r["t"], r["v"]) for r in rows if r["t"] >= REST1_S + PULSE_S]
    t0 = tail[0][0]
    return [(t - t0, v) for t, v in tail]


def fit_decay(tail: list[tuple[float, float]], grids: list[list[float]]) -> dict:
    """Grid search each branch tau over its own grid; linear K/A coefficients by least squares.

    每支路一张网格：慢支路用粗 1 s 步长（命中 45 s），快支路只扫 0.5–5 s。
    全网格笛卡尔积是教学演示里付不起的账——分支网格把这个账压回来。
    """
    from itertools import product

    best: tuple[float, tuple[float, ...], list[float]] | None = None
    for tau_combo in product(*grids):
        if any(
            abs(a - b) < 1e-9
            for a, b in __import__("itertools").combinations(tau_combo, 2)
        ):
            continue
        basis = [[1.0] + [math.exp(-t / tau) for tau in tau_combo] for t, _v in tail]
        ys = [v for _t, v in tail]
        n = len(basis[0])
        btb = [
            [sum(row[i] * row[j] for row in basis) for j in range(n)]
            for i in range(n)
        ]
        bty = [
            sum(row[i] * y for row, y in zip(basis, ys, strict=True))
            for i in range(n)
        ]
        coef = solve(btb, bty)
        resid = [
            y - sum(c * b for c, b in zip(coef, row, strict=True))
            for row, y in zip(basis, ys, strict=True)
        ]
        sse = sum(r * r for r in resid)
        if best is None or sse < best[0]:
            best = (sse, tau_combo, coef)
    assert best is not None, "tau grids must be nonempty"
    sse, taus_fit, coef = best
    return {
        "sse": sse,
        "taus": list(taus_fit),
        "coef": coef,
        "rms_mv": math.sqrt(sse / len(tail)) * 1000.0,
    }


def solve(a: list[list[float]], b: list[float]) -> list[float]:
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        m[col], m[piv] = m[piv], m[col]
        if abs(m[col][col]) < 1e-18:
            raise ValueError("singular normal equations")
        for r in range(n):
            if r != col:
                fac = m[r][col] / m[col][col]
                m[r] = [x - fac * y for x, y in zip(m[r], m[col], strict=True)]
    return [m[i][n] / m[i][i] for i in range(n)]


def window_rms(tail: list[tuple[float, float]], fit: dict, t_lo: float, t_hi: float) -> float:
    taus, coef = fit["taus"], fit["coef"]
    pts = [(t, v) for t, v in tail if t_lo <= t <= t_hi]
    sse = 0.0
    for t, v in pts:
        pred = coef[0]
        for c, tau in zip(coef[1:], taus, strict=True):
            pred += c * math.exp(-t / tau)
        sse += (v - pred) ** 2
    return math.sqrt(sse / max(len(pts), 1)) * 1000.0


def hysteresis_inversion_error_pp() -> dict:
    """Charge vs discharge branch at z = 0.5: same terminal reading, two OCVs."""
    z = 0.5
    u_chg = ocv(z) + HYSTERESIS_WIDTH_V / 2
    u_dchg = ocv(z) - HYSTERESIS_WIDTH_V / 2
    # An observer that ignores hysteresis sees one voltage V; inverting with the
    # wrong branch shifts z by width / slope.
    err_pp = HYSTERESIS_WIDTH_V / OCV_SLOPE_V_PER_SOC * 100.0
    return {
        "scenario_id": HYSTERESIS_SCENARIO_ID,
        "z": z,
        "ocv_charge_v": round(u_chg, 4),
        "ocv_discharge_v": round(u_dchg, 4),
        "width_mv": HYSTERESIS_WIDTH_V * 1000.0,
        "slope_v_per_soc": OCV_SLOPE_V_PER_SOC,
        "inversion_error_pp": round(err_pp, 2),
        "conclusion": "不知充放历史时，同一电压按迟滞宽度/斜率反错 SOC",
    }


@lru_cache(maxsize=1)
def _fits() -> tuple[list[dict], list[tuple[float, float]], dict, dict]:
    rows = simulate_2rc()
    tail = rest_tail(rows)
    fit1 = fit_decay(tail, [[t * 0.5 for t in range(2, 241)]])  # 1..120 s，0.5 s 步长
    fit2 = fit_decay(
        tail,
        [
            [float(t) for t in range(5, 121)],  # 慢支路 5..120 s，1 s 步长（命中 45）
            [t * 0.25 for t in range(2, 21)],  # 快支路 0.5..5 s，0.25 s 步长（命中 1.0）
        ],
    )
    return rows, tail, fit1, fit2


def build_report() -> dict:
    rows, tail, fit1, fit2 = _fits()
    return {
        "scenario_id": SCENARIO_ID,
        "identity": "synthetic 2RC truth; extends the S2 1RC main scenario with a 1 s fast branch",
        "truth": {"Q_ah": Q_AH, "R0_ohm": R0_OHM, "R1_ohm": R1_OHM, "C1_f": C1_F,
                  "tau1_s": TAU1_S, "R2_ohm": R2_OHM, "C2_f": C2_F, "tau2_s": TAU2_S},
        "profile": {"rest1_s": REST1_S, "pulse_a": PULSE_A, "pulse_s": PULSE_S, "rest2_s": REST2_S, "dt_s": DT_S, "z0": Z0},
        "ohmic_jump_mv": round(PULSE_A * R0_OHM * 1000.0, 4),
        "fit_1rc": {k: round(v, 6) if isinstance(v, float) else v for k, v in fit1.items()},
        "fit_2rc": {k: round(v, 6) if isinstance(v, float) else v for k, v in fit2.items()},
        "window_rms_mv": {
            "1rc_early_0_5s": round(window_rms(tail, fit1, 0.0, 5.0), 4),
            "1rc_late_60_180s": round(window_rms(tail, fit1, 60.0, 180.0), 4),
            "2rc_early_0_5s": round(window_rms(tail, fit2, 0.0, 5.0), 4),
        },
        "hysteresis": hysteresis_inversion_error_pp(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 的目录")
    args = parser.parse_args()
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
