#!/usr/bin/env python3
"""SOC estimation demo: Coulomb counting vs OCV correction.

Convention (same as BMS-Z): charge current is positive.
The cell model is illustrative (LFP-like OCV table, 100 Ah, no thermal
effects). Run: python code/soc_coulomb_ocv.py
"""

from bisect import bisect_left

Q_RATED_AH = 100.0
DT_S = 60.0
BIAS_A = 0.05
OCV_SOC = [0, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
OCV_V = [3.000, 3.150, 3.220, 3.260, 3.280, 3.295,
         3.305, 3.315, 3.325, 3.335, 3.360, 3.420]

# (duration_s, current_A); charge is positive, discharge is negative
PROFILE: list[tuple[float, float]] = [
    (2 * 3600, -20.0),
    (8 * 3600, 0.0),
    (1 * 3600, 10.0),
    (8 * 3600, 0.0),
    (2 * 3600, -20.0),
    (7 * 24 * 3600, 0.0),
    (1 * 3600, 10.0),
    (2 * 24 * 3600, 0.0),
]


def ocv_from_soc(soc: float) -> float:
    soc = min(max(soc, 0.0), 100.0)
    i = bisect_left(OCV_SOC, soc)
    if i == 0:
        return OCV_V[0]
    if i >= len(OCV_SOC):
        return OCV_V[-1]
    x0, x1 = OCV_SOC[i - 1], OCV_SOC[i]
    y0, y1 = OCV_V[i - 1], OCV_V[i]
    return y0 + (y1 - y0) * (soc - x0) / (x1 - x0)


def soc_from_ocv(v: float) -> float:
    v = min(max(v, OCV_V[0]), OCV_V[-1])
    i = bisect_left(OCV_V, v)
    if i == 0:
        return float(OCV_SOC[0])
    if i >= len(OCV_V):
        return float(OCV_SOC[-1])
    y0, y1 = OCV_V[i - 1], OCV_V[i]
    x0, x1 = OCV_SOC[i - 1], OCV_SOC[i]
    return x0 + (x1 - x0) * (v - y0) / (y1 - y0)


def simulate(use_ocv: bool, bias: float, q_model: float = Q_RATED_AH) -> tuple[float, float]:
    """Return (final SOC %, max |error| %)."""
    soc_true = 100.0
    soc_est = 100.0
    max_err = 0.0

    for duration, current in PROFILE:
        steps = int(duration // DT_S)
        rest_min = duration >= 3600 and abs(current) < 1e-9
        for step in range(steps):
            soc_true += current * DT_S / 3600.0 / Q_RATED_AH * 100.0
            i_meas = current + bias
            soc_est += i_meas * DT_S / 3600.0 / q_model * 100.0
            max_err = max(max_err, abs(soc_est - soc_true))
            if use_ocv and rest_min and step == steps - 1:
                soc_ocv = soc_from_ocv(ocv_from_soc(soc_true))
                soc_est = 0.7 * soc_est + 0.3 * soc_ocv
    return soc_est, max_err


def main() -> None:
    cases = [
        ("pure coulomb, no bias", False, 0.0),
        ("pure coulomb, +0.05 A bias", False, BIAS_A),
        ("OCV corrected, no bias", True, 0.0),
        ("OCV corrected, +0.05 A bias", True, BIAS_A),
        ("OCV corrected, Q model 95 Ah", True, 0.0),
    ]
    print(f"{'case':34s} {'final SOC':>10s} {'max err':>9s}")
    for name, use_ocv, bias in cases:
        q_model = 95.0 if "95" in name else Q_RATED_AH
        final, max_err = simulate(use_ocv, bias, q_model)
        print(f"{name:34s} {final:9.2f}% {max_err:8.2f}%")

    # sanity checks: bias causes drift; OCV correction bounds it
    drift, _ = simulate(False, BIAS_A)
    corrected, _ = simulate(True, BIAS_A)
    assert drift > 45.0, "positive bias should make SOC drift high"
    assert abs(corrected - 40.0) < 8.0, "OCV correction should bound the error"
    print("\nchecks passed: bias drifts; OCV correction bounds error")


if __name__ == "__main__":
    main()
