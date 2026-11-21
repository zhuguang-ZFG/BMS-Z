"""D23 reference implementation: precharge repetition account + insulation bridge.

Teaching slice ``D23-precharge-insulation``: the single-pulse RC precharge
account (tau, 95% time, capacitor energy) is S3's territory and is NOT
re-implemented here beyond quoting the shared numbers; D23 adds two things S3
does not cover: (1) the *repetition* thermal account that decides whether a
precharge resistor may fire again, and (2) an insulation equivalent network
(R_iso+ / R_iso- to chassis, Y-capacitance) plus a switched-reference bridge
measurement with an explicit validity window.

Every value is a teaching assumption, not a device selection. Only the
standard library is used so the chapter can be recomputed end to end.

Conventions: voltage in V, resistance in Ohm, capacitance in F, time in s,
energy in J, power in W.

Pinned identities:
- axis boundary: D23 repetition energy is the same physical account as S3
  (half C V squared at the measure fraction), S3's close-permission gating is
  not re-decided here (``axis_boundary = s3_pulse_energy_reused_not_retested``);
- insulation estimate is only a number inside [r_min_ohm, r_max_ohm] and only
  after the Y-cap window settled (``axis_boundary = estimate_validity_window``).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

SCENARIO_ID = "D23-precharge-insulation"
GENERATOR = "d23_precharge_insulation.py v1 (standard library)"

# --- precharge (numbers shared with S3's frozen account) ---
SOURCE_V = 400.0
BUS_CAPACITANCE_F = 1e-3
PRECHARGE_R_OHM = 170.0
MEASURE_FRACTION = 0.95
DEFAULT_PULSE_TIMES_S = (0.0, 5.0, 10.0)
DEFAULT_WINDOW_S = 300.0
RATING_AVG_W = 5.0
RATING_PULSE_J = 100.0

# --- insulation equivalent network ---
R_REF_OHM = 200e3
C_Y_F = 100e-9
R_ISO_PLUS_OHM = 1e6
R_ISO_MINUS_OHM = 100e3
OHM_PER_VOLT = 500.0
R_MIN_OHM = 20e3
R_MAX_OHM = 5e6
SETTLE_TAU_FACTOR = 3.0
DEFAULT_MEASURE_WINDOW_S = 0.2


def tau_s() -> float:
    return PRECHARGE_R_OHM * BUS_CAPACITANCE_F


def t_measure_s(fraction: float = MEASURE_FRACTION) -> float:
    return tau_s() * math.log(1.0 / (1.0 - fraction))


def pulse_energy_j(fraction: float = MEASURE_FRACTION) -> float:
    """Resistor dissipation for one pulse, the thermal-stress quantity.

    Charging C from 0 to ``fraction`` of V: the source supplies
    ``fraction·C·V²``, the capacitor stores ``½·C·(fraction·V)²``, and the
    difference is dissipated in the precharge resistor. S3's
    ``energy_account`` freezes supplied=152.0 J / stored=72.2 J / spent=79.8 J
    at 95% for this loop; this function returns S3's ``spent_j`` so the
    repetition account taxes the resistor, not the capacitor.
    """
    v_bus = fraction * SOURCE_V
    supplied = fraction * BUS_CAPACITANCE_F * SOURCE_V * SOURCE_V
    stored = 0.5 * BUS_CAPACITANCE_F * v_bus * v_bus
    return supplied - stored


def pulse_energy_account(fraction: float = MEASURE_FRACTION) -> dict:
    v_bus = fraction * SOURCE_V
    supplied = fraction * BUS_CAPACITANCE_F * SOURCE_V * SOURCE_V
    stored = 0.5 * BUS_CAPACITANCE_F * v_bus * v_bus
    return {
        "supplied_j": supplied,
        "cap_stored_j": stored,
        "resistor_spent_j": supplied - stored,
    }


def repetition_report(
    pulse_times_s: tuple[float, ...] = DEFAULT_PULSE_TIMES_S,
    window_s: float = DEFAULT_WINDOW_S,
    rating_avg_w: float = RATING_AVG_W,
    rating_pulse_j: float = RATING_PULSE_J,
) -> dict:
    account = pulse_energy_account()
    energy = account["resistor_spent_j"]
    count = len(pulse_times_s)
    avg_power = count * energy / window_s
    verdict = "pass"
    if energy > rating_pulse_j:
        verdict = "deny"
    elif avg_power > rating_avg_w:
        verdict = "deny"
    return {
        "source_v": SOURCE_V,
        "bus_capacitance_f": BUS_CAPACITANCE_F,
        "precharge_r_ohm": PRECHARGE_R_OHM,
        "tau_s": tau_s(),
        "t95_s": t_measure_s(),
        "measure_fraction": MEASURE_FRACTION,
        "pulse_energy_j": energy,
        "supplied_j": account["supplied_j"],
        "cap_stored_j": account["cap_stored_j"],
        "energy_source": "resistor_dissipation_supplied_minus_stored",
        "pulse_times_s": list(pulse_times_s),
        "pulse_count": count,
        "window_s": window_s,
        "avg_power_w": avg_power,
        "rating_avg_w": rating_avg_w,
        "rating_pulse_j": rating_pulse_j,
        "verdict": verdict,
    }


def insulation_report(
    r_iso_plus_ohm: float = R_ISO_PLUS_OHM,
    r_iso_minus_ohm: float = R_ISO_MINUS_OHM,
    r_ref_ohm: float = R_REF_OHM,
    c_y_f: float = C_Y_F,
    window_s: float = DEFAULT_MEASURE_WINDOW_S,
    source_v: float = SOURCE_V,
) -> dict:
    """Switched-reference bridge over the insulation equivalent network.

    Two windows: (1) rails floating, measure |v-|; (2) R_ref switched from
    chassis to the negative rail, wait window_s, measure again. The Y-cap
    makes the second window a first-order approach to the DC target with
    tau = (R_iso- || R_ref) * C_y; estimates are only valid when the window
    covers SETTLE_TAU_FACTOR * tau.
    """
    g_plus = 1.0 / r_iso_plus_ohm
    g_minus = 1.0 / r_iso_minus_ohm
    a = g_plus + g_minus
    v_minus = -source_v * g_plus / a
    # C_y 瞬态的戴维南电阻：置零理想压源后正负轨短接，三支路并联想见
    # R_th = R_iso- ∥ R_ref ∥ R_iso+（漏掉 R_iso+ 会高估 τ_y）
    r_th = 1.0 / (1.0 / r_iso_minus_ohm + 1.0 / r_ref_ohm + 1.0 / r_iso_plus_ohm)
    tau = r_th * c_y_f
    required_window = SETTLE_TAU_FACTOR * tau
    v_target = -source_v * g_plus / (a + 1.0 / r_ref_ohm)
    settle = 1.0 - math.exp(-window_s / tau)
    v_ref_meas = v_minus + (v_target - v_minus) * settle

    ratio = abs(v_ref_meas / v_minus)
    estimates_valid = True
    r_plus_est: float | None = None
    r_minus_est: float | None = None
    verdict = "pass"
    # 估计先算；所有边界都按仪表可见的估计值判定，真值不可假设已知
    if ratio >= 0.999999:
        r_plus_est = None
        r_minus_est = None
    else:
        a_est = ratio / ((1.0 - ratio) * r_ref_ohm)
        g_plus_est = a_est * abs(v_minus) / source_v
        r_plus_est = 1.0 / g_plus_est
        r_minus_est = 1.0 / (a_est - g_plus_est)
    if window_s < required_window:
        estimates_valid = False
        verdict = "window_too_short"
    elif r_plus_est is None or r_minus_est is None:
        estimates_valid = False
        verdict = "out_of_range"
    elif min(r_plus_est, r_minus_est) < R_MIN_OHM or max(r_plus_est, r_minus_est) > R_MAX_OHM:
        estimates_valid = False
        verdict = "out_of_range"
    else:
        required_min = OHM_PER_VOLT * source_v
        if min(r_plus_est, r_minus_est) < required_min:
            verdict = "isolation_fault"
    return {
        "source_v": source_v,
        "r_ref_ohm": r_ref_ohm,
        "c_y_f": c_y_f,
        "r_iso_plus_true_ohm": r_iso_plus_ohm,
        "r_iso_minus_true_ohm": r_iso_minus_ohm,
        "v_minus_v": v_minus,
        "v_minus_ref_v": v_ref_meas,
        "tau_s": tau,
        "required_window_s": required_window,
        "window_s": window_s,
        "settle_fraction": settle,
        "ohm_per_volt": OHM_PER_VOLT,
        "required_min_r_ohm": OHM_PER_VOLT * source_v,
        "r_min_ohm": R_MIN_OHM,
        "r_max_ohm": R_MAX_OHM,
        "r_iso_plus_ohm": r_plus_est,
        "r_iso_minus_ohm": r_minus_est,
        "estimates_valid": estimates_valid,
        "verdict": verdict,
    }


def default_report() -> dict:
    precharge = repetition_report()
    insulation = insulation_report()
    return {
        "scenario_id": SCENARIO_ID,
        "generator": GENERATOR,
        "config": {
            "source_v": SOURCE_V,
            "bus_capacitance_f": BUS_CAPACITANCE_F,
            "precharge_r_ohm": PRECHARGE_R_OHM,
            "r_ref_ohm": R_REF_OHM,
            "c_y_f": C_Y_F,
            "ohm_per_volt": OHM_PER_VOLT,
        },
        "precharge": precharge,
        "insulation": insulation,
        "counts": {
            "precharge_pulses": precharge["pulse_count"],
            "insulation_windows": 2,
        },
    }


def write_artifacts(report: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with open(out_dir / "precharge.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["t_s", "pulse_index"])
        for index, t_s in enumerate(report["precharge"]["pulse_times_s"], start=1):
            writer.writerow([t_s, index])
    ins = report["insulation"]
    with open(out_dir / "insulation.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["window", "v_v"])
        writer.writerow(["floating", ins["v_minus_v"]])
        writer.writerow(["with_r_ref", ins["v_minus_ref_v"]])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write report.json, precharge.csv, insulation.csv")
    args = parser.parse_args(argv)
    try:
        report = default_report()
        if args.out:
            write_artifacts(report, args.out)
        else:
            print(json.dumps(report["counts"], ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(f"d23_precharge_insulation: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
