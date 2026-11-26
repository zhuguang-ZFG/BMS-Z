#!/usr/bin/env python3
"""Chapter 27: covariance propagation and signed innovation contributions.

These are synthetic calculations, not measured battery accuracy. The controlled
traces change the operating point without clipping SOC or claiming that more
excitation necessarily improves estimation. Only standard-library dependencies.
"""
from __future__ import annotations

import json
import math

from ekf_soc import docv, first_ticks, joseph_covariance, ocv

A_RC = math.exp(-1.0 / 35.2)
Q_SOC, Q_RC, R_VOLT = 2e-6, 1e-7, 2.5e-5


def prediction_example() -> dict[str, float]:
    """Return one prediction where the two variances move in opposite directions."""
    urc_after = A_RC * A_RC * 1e-4 + Q_RC
    return {
        "soc_variance_before": 0.01, "soc_variance_after": 0.01 + Q_SOC,
        "urc_variance_before": 1e-4, "urc_variance_after": urc_after,
        "urc_sigma_before_mv": 10.0, "urc_sigma_after_mv": math.sqrt(urc_after) * 1000,
    }


def innovation_allocations() -> list[dict[str, float | int]]:
    """Project the published first three state corrections into voltage space."""
    p00, p01, p11 = 0.01, 0.0, 1e-4
    rows = []
    for tick in first_ticks(3):
        h = docv(tick.soc_predicted)
        p00, p01, p11 = p00 + Q_SOC, A_RC * p01, A_RC * A_RC * p11 + Q_RC
        k_rc = (p01 * h + p11) / tick.s_var
        soc_share, urc_share = h * tick.k_soc, k_rc  # C1 = 1 in this model.
        rows.append({
            "k": tick.k, "residual_mv": tick.residual_v * 1000,
            "s_var": tick.s_var, "soc_share": soc_share, "urc_share": urc_share,
            "total_share": soc_share + urc_share, "nis": tick.nis,
        })
        p00, p01, p11 = tick.p00, tick.p01, tick.p11
    return rows


def controlled_trace(current: float, residual: float, *, fixed_c: bool,
                     count: int = 120) -> list[dict]:
    """Run a bounded synthetic trace with an imposed voltage innovation.

    With fixed_c, both OCV and its derivative use the same linear model.
    Otherwise they use the book's nonlinear curve. Voltage is constructed from
    each prediction plus residual: this isolates dependence, not accuracy.
    """
    if not all(math.isfinite(v) for v in (current, residual)) or count < 1:
        raise ValueError("finite inputs and a positive sample count are required")
    soc, urc = 0.80, 0.0
    p00, p01, p10, p11 = 0.01, 0.0, 0.0, 1e-4
    rows = []
    curve = (lambda s: 3.2 + 0.8 * s) if fixed_c else ocv
    for k in range(count):
        soc += current / 36000.0
        urc = A_RC * urc + 0.016 * (1 - A_RC) * current
        if not 0 < soc < 1:
            raise ValueError("this comparison requires SOC strictly inside (0, 1)")
        h = 0.8 if fixed_c else docv(soc)
        p00, p01, p10, p11 = (
            p00 + Q_SOC, A_RC * p01, A_RC * p10, A_RC * A_RC * p11 + Q_RC,
        )
        predicted_voltage = curve(soc) + 0.033 * current + urc
        measured_voltage = predicted_voltage + residual
        innovation = measured_voltage - predicted_voltage
        s = h * (p00 * h + p01) + p10 * h + p11 + R_VOLT
        k0, k1 = (p00 * h + p01) / s, (p10 * h + p11) / s
        soc += k0 * innovation
        urc += k1 * innovation
        if not 0 < soc < 1:
            raise ValueError("this comparison requires SOC strictly inside (0, 1)")
        p00, p01, p10, p11 = joseph_covariance(
            p00, p01, p10, p11, k0, k1, h, 1.0, R_VOLT,
        )
        rows.append({"k": k, "soc": soc, "slope": h,
                     "covariance": [[p00, p01], [p10, p11]]})
    return rows


def dependency_comparison(fixed_c: bool, varied: str) -> dict:
    """Compare one input at a time; report each variance in its own units."""
    if varied not in {"current", "voltage"}:
        raise ValueError("varied must be current or voltage")
    baseline = controlled_trace(-2.0, 0.002, fixed_c=fixed_c)
    changed = controlled_trace(12.0 if varied == "current" else -2.0,
                               0.004 if varied == "voltage" else 0.002, fixed_c=fixed_c)
    return {
        "fixed_c": fixed_c, "varied": varied, "samples": len(baseline),
        "max_soc_variance_difference": max(
            abs(a["covariance"][0][0] - b["covariance"][0][0])
            for a, b in zip(baseline, changed, strict=True)),
        "max_urc_variance_difference": max(
            abs(a["covariance"][1][1] - b["covariance"][1][1])
            for a, b in zip(baseline, changed, strict=True)),
        "final_soc": [baseline[-1]["soc"], changed[-1]["soc"]],
    }


def main() -> None:
    """Print the chapter's independently checkable numerical evidence as JSON."""
    prediction = prediction_example()
    allocation = innovation_allocations()
    comparisons = [dependency_comparison(fixed, varied)
                   for fixed in (True, False) for varied in ("current", "voltage")]
    assert prediction["soc_variance_after"] > prediction["soc_variance_before"]
    assert prediction["urc_variance_after"] < prediction["urc_variance_before"]
    assert allocation[1]["urc_share"] < 0
    for row in allocation:
        assert math.isclose(row["total_share"], 1 - R_VOLT / row["s_var"], abs_tol=1e-12)
    for row in comparisons:
        assert (row["max_soc_variance_difference"] == 0) == row["fixed_c"]
    print(json.dumps({"prediction": prediction, "allocation": allocation,
                      "dependencies": comparisons}, indent=2))


if __name__ == "__main__":
    main()
