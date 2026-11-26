"""Chapter 28: coordinate, interpolation and calibration errors are distinct.

All examples are synthetic. SciPy performs the interpolation; analytic
polynomials and a monotone counterexample establish the teaching claims.
Run from the repository root: python bms-book/code/hppc_grid_evidence.py
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import scipy
from scipy.interpolate import RegularGridInterpolator

from ekf_soc import docv, ocv


def interpolate_table(soc_nodes, temp_c_nodes, values_v, queries) -> np.ndarray:
    """Query a finite SOC × temperature table, strictly within its domain.

    Axes are increasing 1-D arrays with at least two nodes. Queries have shape
    (N, 2), SOC first, and output has shape (N,). No sorting, clipping or
    extrapolation is performed. This deliberately accepts a narrower set of
    inputs than the general SciPy API.
    """
    soc, temp, values, points = (
        np.asarray(x, dtype=float) for x in (soc_nodes, temp_c_nodes, values_v, queries)
    )
    for name, axis in (("SOC", soc), ("temperature", temp)):
        if (axis.ndim != 1 or axis.size < 2 or not np.isfinite(axis).all()
                or not np.all(np.diff(axis) > 0)):
            raise ValueError(f"{name} axis must have >=2 finite, strictly increasing nodes")
    if soc[0] < 0 or soc[-1] > 1:
        raise ValueError("SOC nodes must be fractions in [0, 1]")
    if values.shape != (soc.size, temp.size) or not np.isfinite(values).all():
        raise ValueError("values_v must be finite with shape (n_soc, n_temperature)")
    if (points.ndim != 2 or points.shape[1] != 2 or points.shape[0] == 0
            or not np.isfinite(points).all()):
        raise ValueError("queries must be a nonempty finite (N, 2) array: SOC, temperature")
    return RegularGridInterpolator(
        (soc, temp), values, method="linear", bounds_error=True
    )(points)


def bilinear_bound(h_soc: float, h_temp_c: float, m_soc2: float, m_temp2: float) -> float:
    """Return the C² bound in V using supplied uniform pure-derivative bounds.

    The function does not infer bounds from sampled differences. The bound
    applies inside one rectangular cell, to exact node values. Add a separate
    node-error bound for noisy values; coordinate errors are another term.
    """
    if not all(math.isfinite(v) for v in (h_soc, h_temp_c, m_soc2, m_temp2)):
        raise ValueError("steps and derivative bounds must be finite")
    if h_soc <= 0 or h_temp_c <= 0 or m_soc2 < 0 or m_temp2 < 0:
        raise ValueError("steps must be positive and derivative bounds nonnegative")
    return h_soc**2 * m_soc2 / 8 + h_temp_c**2 * m_temp2 / 8


def _surface(soc, temp):
    return 3.2 + .8*soc + .2*soc**2 + 1e-4*(temp-25)**2 + 1e-3*soc*(temp-25)


def _hidden_curve(soc):
    return 3.2 + .8*soc + .02*np.sin(np.pi*(soc-.4)/.1)**2


def build_report() -> dict:
    soc = np.array([.4, .5, .6])
    temp = np.array([15., 25., 35.])
    validation = np.array([.45, .55])
    nodes = _hidden_curve(soc)
    values = np.repeat(nodes[:, None], len(temp), axis=1)
    points = np.column_stack((validation, np.full(2, 25.)))
    predicted = interpolate_table(soc, temp, values, points)
    curve_soc = np.linspace(.4, .6, 401)
    curve_prediction = interpolate_table(soc, temp, values,
                                        np.column_stack((curve_soc, np.full(401, 25.))))
    linear_nodes = 3.2 + 6.8*soc
    linear_values = np.repeat(linear_nodes[:, None], len(temp), axis=1)
    linear_pred = interpolate_table(soc, temp, linear_values, points)
    refinements = []
    for hz, ht in [(.1, 10.), (.05, 10.), (.1, 5.), (.05, 5.)]:
        zs = np.linspace(.4, .6, round(.2/hz) + 1)
        ts = np.linspace(15, 35, round(20/ht) + 1)
        table = _surface(zs[:, None], ts[None, :])
        centers = np.array([(z, t) for z in (zs[:-1]+zs[1:])/2 for t in (ts[:-1]+ts[1:])/2])
        errors = interpolate_table(zs, ts, table, centers) - _surface(centers[:, 0], centers[:, 1])
        refinements.append({
            "h_soc": hz, "h_temp_c": ht, "node_count": int(table.size),
            "soc_bound_mv": 1000*hz**2*.4/8,
            "temperature_bound_mv": 1000*ht**2*.0002/8,
            "bound_mv": 1000*bilinear_bound(hz, ht, .4, .0002),
            "error_mv": float(np.max(np.abs(errors))*1000),
            "maximum_basis": "constant pure second derivatives; every cell center attains the bound",
        })
    base_values = _surface(soc[:, None], temp[None, :])
    biased = interpolate_table(soc, temp, base_values + .002, [[.45, 20.]])[0]
    domain = []
    for point in [[1.05, 25.], [.5, 40.], [.39, 25.]]:
        try:
            interpolate_table(soc, temp, base_values, [point])
        except ValueError:
            rejected = True
        else:
            rejected = False
        domain.append({"query": point, "rejected": rejected})
    return {
        "schema": 1, "synthetic": True, "scipy_version": scipy.__version__,
        "units": {"soc": "fraction", "temperature": "degree C", "values": "V", "errors": "mV"},
        "coordinate_vs_grid": {
            "grid_spacing_soc": .1, "assumed_coordinate_offset_soc": .05,
            "constant_slope_v_per_soc": 6.8,
            "steep_line_interpolation_error_mv": float(np.max(np.abs(linear_pred-(3.2+6.8*validation)))*1000),
            "coordinate_error_mv": 1000*6.8*.05,
            "nonlinear_start_soc": .05, "nonlinear_end_soc": .1,
            "nonlinear_local_linear_mv": docv(.05)*.05*1000,
            "nonlinear_finite_delta_mv": (ocv(.1)-ocv(.05))*1000,
            "qualification": "grid spacing does not imply a coordinate offset; 340 mV assumes constant slope",
        },
        "hidden_curvature": {
            "formula": "3.2 + 0.8*z + 0.02*sin(pi*(z-0.4)/0.1)^2",
            "node_soc": soc.tolist(), "node_values_v": nodes.tolist(),
            "second_difference_v": float(np.diff(nodes, n=2)[0]),
            "validation_soc": validation.tolist(), "validation_predicted_v": predicted.tolist(),
            "validation_true_v": _hidden_curve(validation).tolist(),
            "validation_residual_mv": ((_hidden_curve(validation)-predicted)*1000).tolist(),
            "derivative_lower_bound_v_per_soc": .8-.02*math.pi/.1,
            "curve_soc": curve_soc.tolist(), "curve_true_v": _hidden_curve(curve_soc).tolist(),
            "curve_predicted_v": curve_prediction.tolist(),
        },
        "axis_refinement": refinements,
        "node_error": {"constant_bias_mv": 2., "interpolation_error_mv": refinements[0]["error_mv"],
                       "total_error_mv": float((biased-_surface(.45, 20.))*1000),
                       "qualification": "constant calibration bias persists under refinement"},
        "domain_policy": {"policy": "raise ValueError outside calibrated domain; never silently clamp", "checks": domain},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    text = json.dumps(build_report(), ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
