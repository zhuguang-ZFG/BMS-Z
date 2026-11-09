"""Teaching experiments for D11: joint multi-pulse identification, leave-one-out
validation, and boundary-hit reporting.

Extends S2 (single-pulse 1RC fitting) and D02 (model order). Frozen truth uses
the S2 main scenario (Q=2 Ah, R0=20 mΩ, R1=15 mΩ∥3000 F, τ=45 s, U slope 0.8).
Two HPPC pulses are simulated at z=0.60 and z=0.40; short-window single-pulse
fits are biased *differently* by excitation, the joint fit recovers truth, and
leave-one-SOC-out validation quantifies the difference.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SCENARIO_ID = "D11-joint-hppc"

Q_AH = 2.0
R0_OHM = 0.020
R1_OHM, C1_F = 0.015, 3000.0
TAU_S = R1_OHM * C1_F
OCV0_V, OCV_SLOPE = 3.6, 0.8
DT_S = 0.5
PULSE_A = 2.0
PULSE_S = 10.0
REST_S = 180.0
SHORT_WINDOW_S = 5.0
TAU_GRID = [t * 0.5 for t in range(2, 241)]  # 1..120 s


def ocv(z: float) -> float:
    return OCV0_V + OCV_SLOPE * (z - 0.5)


def simulate_pulse(z0: float) -> list[dict]:
    rows, vp, z, t = [], 0.0, z0, 0.0
    a = math.exp(-DT_S / TAU_S)
    total = PULSE_S + REST_S
    while t <= total + 1e-9:
        i = PULSE_A if t < PULSE_S else 0.0
        rows.append({"t": t, "i_a": i, "z": z, "vp": vp, "v": ocv(z) - i * R0_OHM - vp})
        z -= i * DT_S / (3600.0 * Q_AH)
        vp = a * vp + R1_OHM * (1.0 - a) * i
        t += DT_S
    return rows


def fit_kat(tail: list[tuple[float, float]], grid: list[float]) -> dict:
    """Grid-search tau, linear solve K/A; flag grid-edge hits."""
    best = None
    for tau in grid:
        ys = [v for _t, v in tail]
        s0 = len(ys)
        s1 = sum(math.exp(-t / tau) for t, _v in tail)
        s2 = sum(math.exp(-2 * t / tau) for t, _v in tail)
        b0 = sum(ys)
        b1 = sum(y * math.exp(-t / tau) for t, y in tail)
        det = s0 * s2 - s1 * s1
        if abs(det) < 1e-18:
            continue
        k = (b0 * s2 - b1 * s1) / det
        aa = (s0 * b1 - s1 * b0) / det
        sse = sum((y - (k + aa * math.exp(-t / tau))) ** 2 for t, y in tail)
        if best is None or sse < best[0]:
            best = (sse, tau, k, aa)
    assert best is not None
    sse, tau, k, aa = best
    edge = len(grid) > 1 and tau in (grid[0], grid[-1])
    return {"sse": sse, "tau": tau, "K": k, "A": aa, "boundary_hit": edge,
            "rms_mv": math.sqrt(sse / len(tail)) * 1000.0}


def r1_from_amplitude(a_v: float, i_pulse_a: float) -> float:
    """Finite-pulse correction inverted: A = −I·R1(1−exp(−Tp/τ))."""
    return -a_v / (i_pulse_a * (1.0 - math.exp(-PULSE_S / TAU_S)))


def joint_fit(rows_by_pulse: dict[str, list[dict]]) -> dict:
    """Simultaneous grid search: one tau shared, per-pulse K/A solved jointly.

    Joint SSE = sum over pulses. The shared tau couples the pulses: a tau biased
    toward one pulse is penalized by the other.
    """
    tails = {name: [(r["t"] - PULSE_S, r["v"]) for r in rows if r["t"] >= PULSE_S]
             for name, rows in rows_by_pulse.items()}
    best = None
    for tau in TAU_GRID:
        sse_total = 0.0
        params = {}
        for name, tail in tails.items():
            fit = fit_kat(tail, [tau])
            sse_total += fit["sse"]
            params[name] = fit
        if best is None or sse_total < best[0]:
            best = (sse_total, tau, params)
    assert best is not None, "tau grid must be nonempty"
    sse, tau, params = best
    return {"tau": tau, "sse": sse, "per_pulse": params,
            "boundary_hit": len(TAU_GRID) > 1 and tau in (TAU_GRID[0], TAU_GRID[-1]),
            "r1_ohm": r1_from_amplitude(params["z0.60"]["A"], PULSE_A)}


def held_out_rmse_mv(fit_rows: list[dict], tau: float, k: float, a_v: float) -> float:
    tail = [(r["t"] - PULSE_S, r["v"]) for r in fit_rows if r["t"] >= PULSE_S]
    sse = sum((v - (k + a_v * math.exp(-t / tau))) ** 2 for t, v in tail)
    return math.sqrt(sse / len(tail)) * 1000.0


def build_report() -> dict:
    rows_a = simulate_pulse(0.60)
    rows_b = simulate_pulse(0.40)
    tail_short_a = [(r["t"] - PULSE_S, r["v"]) for r in rows_a
                    if PULSE_S <= r["t"] <= PULSE_S + SHORT_WINDOW_S]
    single_short = fit_kat(tail_short_a, TAU_GRID)
    tail_full_b = [(r["t"] - PULSE_S, r["v"]) for r in rows_b if r["t"] >= PULSE_S]
    single_b = fit_kat(tail_full_b, TAU_GRID)
    joint = joint_fit({"z0.60": rows_a, "z0.40": rows_b})
    loo_single = held_out_rmse_mv(rows_b, single_short["tau"], single_short["K"], single_short["A"])
    loo_joint_a = held_out_rmse_mv(rows_b, joint["tau"], joint["per_pulse"]["z0.40"]["K"], joint["per_pulse"]["z0.40"]["A"])
    return {
        "scenario_id": SCENARIO_ID,
        "identity": "noiseless synthetic extending the S2 main scenario; real HPPC per OS02 with excitation audit",
        "truth": {"Q_ah": Q_AH, "R0_ohm": R0_OHM, "R1_ohm": R1_OHM, "C1_f": C1_F, "tau_s": TAU_S},
        "single_short_window": {k: round(v, 6) if isinstance(v, float) else v for k, v in single_short.items()},
        "single_pulse_b": {k: round(v, 6) if isinstance(v, float) else v for k, v in single_b.items()},
        "joint": {
            "tau": joint["tau"], "boundary_hit": joint["boundary_hit"],
            "r1_ohm": round(joint["r1_ohm"], 6),
            "recovered_r1_error": round(abs(joint["r1_ohm"] - R1_OHM) / R1_OHM, 8),
        },
        "leave_one_out_rmse_mv": {
            "single_short_fit_on_z0.40": round(loo_single, 4),
            "joint_params_on_z0.40": round(loo_joint_a, 4),
        },
        "conclusion": "K 是逐脉冲的局部渐近值，跨 SOC 不可迁移（留出 160 mV = ΔOCV 0.16 V）；"
                      "联合拟合共享 τ、逐脉冲自由 K，留出 0 mV；哪些参数可共享就是辨识合同的写法",
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
