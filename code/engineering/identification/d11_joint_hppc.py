#!/usr/bin/env python3
"""D11: fit training pulses, freeze RC parameters, predict independent tails.

Discharge current is positive. All scenes are synthetic 1RC experiments with
zero initial polarization. OCV/capacity/initial SOC are declared calibration
inputs, not quantities identified from the relaxation tail. The default path
uses only the standard library; --scipy cross-checks the same training SSE.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import json
import math
from pathlib import Path
import random
from statistics import fmean
from collections.abc import Sequence

SCENARIO_ID = "D11-joint-hppc"
TAU_GRID = tuple(t * .5 for t in range(2, 241))
R1_BOUNDS = (.001, .1)
NOISE_SIGMA_V = .0001
Tail = tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class Pulse:
    """Measured protocol and independently provided initial SOC."""
    pulse_id: str
    z0: float
    current_a: float
    pulse_s: float
    noise_seed: int
    rest_s: float = 180.
    dt_s: float = .5


@dataclass(frozen=True)
class Calibration:
    """Independent calibration, exact only in this teaching scene."""
    q_ah: float = 2.
    ocv0_v: float = 3.6
    ocv_slope: float = .8
    source: str = "declared synthetic OCV/Q calibration; initial SOC in protocol"


@dataclass(frozen=True)
class Truth:
    """Generator-only RC parameters; never passed to a fitter or predictor."""
    r1_ohm: float = .015
    tau_s: float = 45.


@dataclass(frozen=True)
class Observation:
    """One complete relaxation tail: seconds since current removal, volts."""
    pulse: Pulse
    tail: Tail


@dataclass(frozen=True)
class Prediction:
    """Frozen voltage prediction made before observing validation voltage."""
    pulse_id: str
    tail: Tail


TRAIN_PULSES = (Pulse("A", .60, 2., 10., 11), Pulse("B", .40, -1.5, 20., 17))
VALIDATION_PULSES = (Pulse("C", .50, 1.5, 15., 23), Pulse("D", .70, -1., 25., 29))


def _positive(*values: float) -> None:
    if any(not math.isfinite(x) or x <= 0 for x in values):
        raise ValueError("expected finite positive values")


def _protocol(pulse: Pulse) -> tuple[float, ...]:
    _positive(pulse.pulse_s, pulse.rest_s, pulse.dt_s)
    if not pulse.pulse_id or not math.isfinite(pulse.current_a) or pulse.current_a == 0:
        raise ValueError("pulse requires an ID and finite nonzero excitation")
    if not math.isfinite(pulse.z0) or not 0 <= pulse.z0 <= 1:
        raise ValueError("initial SOC must be in [0, 1]")
    count = pulse.rest_s / pulse.dt_s
    if count < 2 or not math.isclose(count, round(count), abs_tol=1e-9):
        raise ValueError("rest duration must contain an integer number of at least two steps")
    return tuple(n * pulse.dt_s for n in range(round(count) + 1))


def calibrated_k(pulse: Pulse, calibration: Calibration) -> float:
    """OCV after the pulse; capacity/OCV are supplied, not tail-fit results."""
    _positive(calibration.q_ah)
    if not all(math.isfinite(x) for x in (calibration.ocv0_v, calibration.ocv_slope)):
        raise ValueError("nonfinite calibration")
    z_end = pulse.z0 - pulse.current_a * pulse.pulse_s / (3600 * calibration.q_ah)
    if not 0 <= z_end <= 1:
        raise ValueError("post-pulse SOC outside calibration domain")
    return calibration.ocv0_v + calibration.ocv_slope * (z_end - .5)


def _h(pulse: Pulse, tau: float, t: float) -> float:
    return pulse.current_a * math.expm1(-pulse.pulse_s / tau) * math.exp(-t / tau)


def simulate_tail(pulse: Pulse, truth: Truth, calibration: Calibration,
                  *, noise_sigma_v: float = 0.) -> Observation:
    """Generate a synthetic tail from the exact zero-initial-polarization model."""
    times = _protocol(pulse)
    _positive(truth.r1_ohm, truth.tau_s)
    if not math.isfinite(noise_sigma_v) or noise_sigma_v < 0:
        raise ValueError("noise sigma must be finite and nonnegative")
    k = calibrated_k(pulse, calibration)
    rng = random.Random(pulse.noise_seed)
    return Observation(pulse, tuple((t, k + truth.r1_ohm * _h(pulse, truth.tau_s, t)
                                    + rng.gauss(0., noise_sigma_v)) for t in times))


def _tail(tail: Sequence[tuple[float, float]]) -> None:
    if len(tail) < 3 or any(not math.isfinite(t) or not math.isfinite(v) or t < 0 for t, v in tail):
        raise ValueError("tail needs at least three finite samples at nonnegative times")
    if any(t2 <= t1 for (t1, _), (t2, _) in zip(tail, tail[1:], strict=False)):
        raise ValueError("tail times must strictly increase")


def _grid(grid: Sequence[float]) -> None:
    if not grid:
        raise ValueError("empty tau grid")
    _positive(*grid)
    if any(b <= a for a, b in zip(grid, grid[1:], strict=False)):
        raise ValueError("tau grid must strictly increase")


def fit_kat(tail: Sequence[tuple[float, float]], grid: Sequence[float]) -> dict:
    """Fit local K/A on each tau; a single-point evaluation is not a search."""
    _tail(tail)
    _grid(grid)
    ym = fmean(v for _, v in tail)
    best = None
    for tau in grid:
        xs = [math.exp(-t / tau) for t, _ in tail]
        xm = fmean(xs)
        denom = math.fsum((x - xm) ** 2 for x in xs)
        if denom <= 1e-18:
            continue
        a = math.fsum((x - xm) * (v - ym) for x, (_, v) in zip(xs, tail, strict=True)) / denom
        k = ym - a * xm
        sse = math.fsum((v - k - a * x) ** 2 for x, (_, v) in zip(xs, tail, strict=True))
        if best is None or sse < best["sse"]:
            best = {"sse": sse, "tau": tau, "K": k, "A": a,
                    "boundary_hit": len(grid) > 1 and tau in (grid[0], grid[-1]),
                    "rms_mv": math.sqrt(sse / len(tail)) * 1000}
    if best is None:
        raise ValueError("tail has insufficient exponential curvature")
    return best


def r1_from_amplitude(a_v: float, i_pulse_a: float, *, tau_s: float, pulse_s: float) -> float:
    """Invert A=-I R1 (1-exp(-tp/tau)) using the fitted tau and actual protocol."""
    _positive(tau_s, pulse_s)
    if not math.isfinite(a_v) or not math.isfinite(i_pulse_a) or i_pulse_a == 0:
        raise ValueError("finite amplitude and nonzero current required")
    r1 = a_v / (i_pulse_a * math.expm1(-pulse_s / tau_s))
    _positive(r1)
    return r1


def _training(observations: Sequence[Observation]) -> None:
    if not observations:
        raise ValueError("empty training data")
    ids = [obs.pulse.pulse_id for obs in observations]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate training pulse IDs")
    for obs in observations:
        _protocol(obs.pulse)
        _tail(obs.tail)


def _fit_result(observations: Sequence[Observation], tau: float, r1: float,
                ks: Sequence[float], tau_bounds: tuple[float, float]) -> dict:
    per_pulse = {}
    total_sse = 0.
    for obs, k in zip(observations, ks, strict=True):
        sse = math.fsum((v - k - r1 * _h(obs.pulse, tau, t)) ** 2 for t, v in obs.tail)
        total_sse += sse
        per_pulse[obs.pulse.pulse_id] = {"K": k, "A": r1 * _h(obs.pulse, tau, 0.),
                                        "rms_mv": math.sqrt(sse / len(obs.tail)) * 1000}
    tau_hit = tau_bounds[0] != tau_bounds[1] and any(math.isclose(tau, b, abs_tol=1e-6) for b in tau_bounds)
    r1_hit = any(math.isclose(r1, b, abs_tol=1e-10) for b in R1_BOUNDS)
    return {"tau": float(tau), "r1_ohm": float(r1), "c1_f": float(tau / r1),
            "sse": total_sse, "rms_mv": math.sqrt(total_sse / sum(len(o.tail) for o in observations)) * 1000,
            "per_pulse": per_pulse, "training_ids": [o.pulse.pulse_id for o in observations],
            "tau_bounds_s": list(tau_bounds), "r1_bounds_ohm": list(R1_BOUNDS),
            "tau_boundary_hit": tau_hit, "r1_boundary_hit": r1_hit,
            "boundary_hit": tau_hit or r1_hit}


def joint_fit(observations: Sequence[Observation], *, grid: Sequence[float] = TAU_GRID) -> dict:
    """Training-only SSE: shared R1/tau, one free local K per pulse."""
    _training(observations)
    _grid(grid)
    best = None
    means = [fmean(v for _, v in obs.tail) for obs in observations]
    for tau in grid:
        hs = [[_h(obs.pulse, tau, t) for t, _ in obs.tail] for obs in observations]
        hmeans = [fmean(h) for h in hs]
        denominator = math.fsum((h - hm) ** 2 for values, hm in zip(hs, hmeans, strict=True) for h in values)
        if denominator <= 1e-18:
            continue
        numerator = math.fsum((h - hm) * (v - vm)
                              for obs, values, hm, vm in zip(observations, hs, hmeans, means, strict=True)
                              for h, (_, v) in zip(values, obs.tail, strict=True))
        raw_r1 = numerator / denominator
        if raw_r1 <= 0:
            continue
        r1 = min(R1_BOUNDS[1], max(R1_BOUNDS[0], raw_r1))
        ks = [vm - r1 * hm for vm, hm in zip(means, hmeans, strict=True)]
        fit = _fit_result(observations, tau, r1, ks, (grid[0], grid[-1]))
        if best is None or fit["sse"] < best["sse"]:
            best = fit
    if best is None:
        raise ValueError("insufficient excitation or nonpositive resistance")
    return best


def scipy_joint_fit(observations: Sequence[Observation], *, tau_bounds: tuple[float, float] = (1., 120.)) -> dict:
    """Reuse SciPy least_squares on exactly the grid baseline's training SSE."""
    _training(observations)
    _grid(tau_bounds)
    if len(tau_bounds) != 2:
        raise ValueError("two tau bounds required")
    # Validate excitation/physical sign before entering the bounded optimizer.
    joint_fit(observations, grid=tau_bounds)
    from scipy.optimize import least_squares

    def residual(params):
        tau, r1, *ks = params
        return [k + r1 * _h(obs.pulse, tau, t) - v
                for obs, k in zip(observations, ks, strict=True) for t, v in obs.tail]

    n = len(observations)
    result = least_squares(
        residual, [fmean(tau_bounds), .02, *[fmean(v for _, v in o.tail) for o in observations]],
        bounds=([tau_bounds[0], R1_BOUNDS[0], *[-math.inf] * n],
                [tau_bounds[1], R1_BOUNDS[1], *[math.inf] * n]),
        x_scale=[40., .02, *[4.] * n], ftol=1e-12, xtol=1e-12, gtol=1e-12,
    )
    fit = _fit_result(observations, result.x[0], result.x[1], result.x[2:], tau_bounds)
    fit.update(success=bool(result.success), status=int(result.status), message=str(result.message))
    if not result.success:
        raise ValueError(f"SciPy did not converge: {result.message}")
    return fit


def predict_tail(fit: dict, pulse: Pulse, calibration: Calibration) -> Prediction:
    """Predict without access to generator truth or validation voltage."""
    if pulse.pulse_id in fit["training_ids"]:
        raise ValueError("validation pulse appears in training IDs")
    times = _protocol(pulse)
    tau, r1 = fit["tau"], fit["r1_ohm"]
    _positive(tau, r1)
    k = calibrated_k(pulse, calibration)
    return Prediction(pulse.pulse_id, tuple((t, k + r1 * _h(pulse, tau, t)) for t in times))


def score_prediction(prediction: Prediction, observation: Observation) -> float:
    """Only this step reads held-out voltage; reject misaligned comparisons."""
    _tail(prediction.tail)
    _tail(observation.tail)
    if prediction.pulse_id != observation.pulse.pulse_id or [t for t, _ in prediction.tail] != [t for t, _ in observation.tail]:
        raise ValueError("prediction and observation pulse/time grids differ")
    return math.sqrt(math.fsum((v - p) ** 2 for (_, p), (_, v)
                              in zip(prediction.tail, observation.tail, strict=True)) / len(prediction.tail)) * 1000


def _validation(fit: dict, calibration: Calibration, truth: Truth, noise: float) -> dict:
    # Freeze all predictions before generating or accessing validation voltage.
    predictions = [predict_tail(fit, p, calibration) for p in VALIDATION_PULSES]
    observed = [simulate_tail(p, truth, calibration, noise_sigma_v=noise) for p in VALIDATION_PULSES]
    pulses = {}
    for prediction, obs in zip(predictions, observed, strict=True):
        pulses[prediction.pulse_id] = {"rmse_mv": score_prediction(prediction, obs),
            "trace": [{"t_s": t, "predicted_v": pv, "observed_v": v, "residual_mv": (v - pv) * 1000}
                      for (t, pv), (_, v) in zip(prediction.tail, obs.tail, strict=True)][::10]}
    return {"fit": fit, "validation_rmse_mv": math.sqrt(fmean(p["rmse_mv"] ** 2 for p in pulses.values())),
            "validation": pulses}


def _local_k_counterexample(calibration: Calibration, truth: Truth) -> dict:
    a = TRAIN_PULSES[0]
    b = replace(a, pulse_id="old-B", z0=.4, noise_seed=17)
    oa, ob = (simulate_tail(p, truth, calibration) for p in (a, b))
    fit = fit_kat(oa.tail, TAU_GRID)
    # Deliberately wrong transport of K, labeled as a counterexample.
    pred = Prediction(b.pulse_id, tuple((t, fit["K"] + fit["A"] * math.exp(-t / fit["tau"])) for t, _ in ob.tail))
    return {"identity": "noiseless same-protocol local-K transfer", "training_rmse_mv": fit["rms_mv"],
            "transferred_k_rmse_mv": score_prediction(pred, ob), "K_a_v": fit["K"],
            "K_b_v": calibrated_k(b, calibration), "tau_s": fit["tau"]}


def build_report(*, include_scipy: bool = False) -> dict:
    """Run predetermined synthetic scenes; do not select seeds from scores."""
    calibration, truth = Calibration(), Truth()
    clean = tuple(simulate_tail(p, truth, calibration) for p in TRAIN_PULSES)
    noisy = tuple(simulate_tail(p, truth, calibration, noise_sigma_v=NOISE_SIGMA_V) for p in TRAIN_PULSES)
    clean_fit, noisy_fit = joint_fit(clean), joint_fit(noisy)
    report = {
        "schema_version": 2, "scenario_id": SCENARIO_ID,
        "identity": "synthetic 1RC extension of S2; OS02 is a separate real-data reference, not reproduced here",
        "convention": "discharge positive; zero initial polarization; equal-weight complete 180 s tails",
        "truth_for_generation_only": asdict(truth), "calibration": asdict(calibration),
        "noise_sigma_mv": NOISE_SIGMA_V * 1000,
        "split": {"training": [p.pulse_id for p in TRAIN_PULSES], "validation": [p.pulse_id for p in VALIDATION_PULSES]},
        "protocols": [asdict(p) for p in (*TRAIN_PULSES, *VALIDATION_PULSES)],
        "local_k_counterexample": _local_k_counterexample(calibration, truth),
        "noiseless": _validation(clean_fit, calibration, truth, 0.),
        "noisy": _validation(noisy_fit, calibration, truth, NOISE_SIGMA_V),
        "mismatch": {**_validation(noisy_fit, calibration, replace(truth, tau_s=70.), NOISE_SIGMA_V),
                     "validation_truth_tau_s": 70., "identity": "constructed model mismatch; frozen training fit"},
        "conclusion": "训练回代、局部K搬用与独立预测分开评分；小训练残差不保证跨工况有效。",
    }
    if include_scipy:
        report["scipy"] = _validation(scipy_joint_fit(noisy), calibration, truth, NOISE_SIGMA_V)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 的目录")
    parser.add_argument("--scipy", action="store_true", help="同训练目标的 SciPy 交叉核对")
    args = parser.parse_args()
    try:
        report = build_report(include_scipy=args.scipy)
    except ImportError as exc:
        parser.exit(2, f"SciPy 核对需要依赖：pip install -r bms-book/requirements.txt ({exc})\n")
    payload = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    print(payload, end="")
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
