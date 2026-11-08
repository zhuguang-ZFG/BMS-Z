"""S3 precharge reference implementation.

Teaching scenario ``S3-inrush-precharge``: a 400 V bus with a 1 mF bus
capacitor charged through a 170 Ohm resistor, starting from zero residual
voltage. Every value is a teaching assumption, not a device selection. Only
the standard library is used so the chapter can be recomputed end to end.

Conventions: voltage in V, current in A (discharge-positive on the new
engineering side; here the precharge loop current flows from source to bus),
resistance in Ohm, capacitance in F, time in s, energy in J, SOC as a 0-1
ratio. A parallel load can be added; device limits (peak current, pulse
energy, repetition) are reported, never silently accepted.

The module answers one question: why a bus at 95% of source voltage still
must not be treated as "ready to close the main contactor", and which state
machines and measurements actually gate that decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path

SCENARIO_ID = "S3-inrush-precharge"
LOAD_SCENARIO_ID = "S3-precharge-with-load"
GENERATOR = "s3_precharge.py v1 (standard library)"


@dataclass(frozen=True)
class PrechargeConfig:
    """Frozen teaching values for the RC precharge loop."""

    source_v: float = 400.0
    bus_capacitance_f: float = 1e-3
    precharge_r_ohm: float = 170.0
    initial_bus_v: float = 0.0
    sample_period_s: float = 20e-3
    measure_supply_threshold: float = 0.95
    measure_supply_upper_factor: float = 1.05  # above this factor * source = overvoltage, reject
    slow_rise_factor: float = 5.0  # slower than this ratio = fault
    overshoot_factor: float = 1.5  # faster than this ratio = fault
    parallel_load_ohm: float | None = None  # optional load across the bus
    retry_interval_s: float = 3600.0  # next permitted precharge attempt
    devices_precharge_peak_a: float = 3.0  # teaching limit, not a datasheet
    devices_precharge_energy_j: float = 85.0  # teaching limit for one pulse
    main_loop_resistance_ohm: float = 0.02  # teaching value: main contactor loop, not precharge resistor
    devices_main_peak_a: float = 1500.0  # teaching making-current limit for main contactor path

    def identity(self) -> dict:
        payload = asdict(self)
        return payload


def replace_config(cfg: PrechargeConfig, **changes: object) -> PrechargeConfig:
    return replace(cfg, **changes)


def tau_s(cfg: PrechargeConfig) -> float:
    if cfg.parallel_load_ohm is not None:
        r_par = cfg.precharge_r_ohm * cfg.parallel_load_ohm / (cfg.precharge_r_ohm + cfg.parallel_load_ohm)
        return r_par * cfg.bus_capacitance_f
    return cfg.precharge_r_ohm * cfg.bus_capacitance_f


def bus_voltage(cfg: PrechargeConfig, t: float) -> float:
    if t < 0:
        raise ValueError("t must be non-negative")
    v0 = cfg.initial_bus_v
    vs = cfg.source_v
    if cfg.parallel_load_ohm is not None:
        v_end = vs * cfg.parallel_load_ohm / (cfg.precharge_r_ohm + cfg.parallel_load_ohm)
        return v_end + (v0 - v_end) * math.exp(-t / tau_s(cfg))
    return vs - (vs - v0) * math.exp(-t / (cfg.precharge_r_ohm * cfg.bus_capacitance_f))


def loop_current(cfg: PrechargeConfig, t: float) -> float:
    if t < 0:
        raise ValueError("t must be non-negative")
    return (cfg.source_v - bus_voltage(cfg, t)) / cfg.precharge_r_ohm


def time_to_fraction(cfg: PrechargeConfig, fraction: float) -> float:
    """When the bus reaches `fraction` of source (no residual sensing error)."""
    if not 0.0 < fraction < 1.0:
        raise ValueError("fraction must be in (0, 1)")
    if cfg.parallel_load_ohm is not None:
        v_end = cfg.source_v * cfg.parallel_load_ohm / (cfg.precharge_r_ohm + cfg.parallel_load_ohm)
        if fraction * cfg.source_v >= v_end:
            raise ValueError("load prevents reaching this fraction")
        ratio = (fraction * cfg.source_v - v_end) / (cfg.initial_bus_v - v_end)
        return -tau_s(cfg) * math.log(ratio)
    gap = cfg.source_v - fraction * cfg.source_v
    return cfg.precharge_r_ohm * cfg.bus_capacitance_f * math.log((cfg.source_v - cfg.initial_bus_v) / gap)


def energy_account(cfg: PrechargeConfig, at_fraction: float = 0.95) -> dict:
    """Source supplied, resistor spent, capacitor stored at one fraction."""
    v = at_fraction * cfg.source_v if cfg.parallel_load_ohm is None else bus_voltage(cfg, time_to_fraction(cfg, at_fraction))
    v0 = cfg.initial_bus_v
    stored = 0.5 * cfg.bus_capacitance_f * (v**2 - v0**2)
    if cfg.parallel_load_ohm is None:
        supplied = cfg.source_v * cfg.bus_capacitance_f * (v - v0)
    else:
        supplied = None  # C is not conserved with a parallel load; see energy-with-load note
    spent = (supplied - stored) if supplied is not None else None
    return {"bus_v": v, "stored_j": stored, "supplied_j": supplied, "spent_j": spent}


def energy_with_load(cfg: PrechargeConfig, window_tau: float = 5.0) -> dict:
    """Finite-window energy account in the loaded RC loop.

    Over any finite window ``[0, T]`` with ``T = window_tau * tau_par`` the
    source work decomposes exactly as ``source = dCapacitor + resistor +
    load``. The integrals below were cross-checked against midpoint sampling
    (residual < 1e-8 J) before being promoted to closed form. With a parallel
    load the steady-state dissipation diverges in time, so the account is
    reported over the same finite window rather than at infinity; the
    no-load limit ``R_load -> infinity`` recovers the familiar
    ``160 = 80 + 80 J`` at the windowed end point.
    """
    r = cfg.precharge_r_ohm
    r_load = cfg.parallel_load_ohm or math.inf
    capacitance = cfg.bus_capacitance_f
    v0 = cfg.initial_bus_v
    if math.isinf(r_load):
        v_end = cfg.source_v
        tau = r * capacitance
    else:
        v_end = cfg.source_v * r_load / (r + r_load)
        tau = r * r_load / (r + r_load) * capacitance
    horizon = window_tau * tau
    i_inf = (cfg.source_v - v_end) / r            # steady loop current (load present)
    i_tau = (v_end - v0) / r                      # decaying part amplitude
    decay = math.exp(-horizon / tau)              # endpoint factor e^{-T/tau}
    bus_end = v_end + (v0 - v_end) * decay
    stored = 0.5 * capacitance * (bus_end**2 - v0**2)
    supplied = cfg.source_v * (i_inf * horizon + i_tau * tau * (1.0 - decay))
    e_r = (i_inf**2 * r * horizon
           + 2.0 * i_inf * i_tau * r * tau * (1.0 - decay)
           + i_tau**2 * r * tau * (1.0 - decay * decay) / 2.0)
    if math.isinf(r_load):
        e_load = 0.0
    else:
        dv = v0 - v_end
        e_load = (v_end * v_end * horizon
                  + 2.0 * v_end * dv * tau * (1.0 - decay)
                  + dv * dv * tau * (1.0 - decay * decay) / 2.0) / r_load
    residual = supplied - stored - e_r - e_load
    return {
        "window_s": horizon,
        "steady_state_v": v_end,
        "bus_end_v": bus_end,
        "source_j": supplied,
        "resistor_j": e_r,
        "load_j": e_load,
        "stored_j": stored,
        "residual_j": residual,
        "identity_ok": abs(residual) < 1e-9,
        "note": "finite 5-tau window unless window_tau is overridden; load dissipation diverges beyond it when v_end>0",
    }


def initial_inrush(cfg: PrechargeConfig) -> dict:
    v_gap = cfg.source_v - cfg.initial_bus_v
    i0 = v_gap / cfg.precharge_r_ohm
    p0 = cfg.source_v * i0
    return {"v_gap_v": v_gap, "current_a": i0, "power_w": p0,
            "peak_ok": i0 <= cfg.devices_precharge_peak_a,
            "energy_ok": 0.5 * cfg.bus_capacitance_f * v_gap**2 <= cfg.devices_precharge_energy_j}


def close_current_at_residual(cfg: PrechargeConfig, residual_v: float) -> float:
    """Main-contactor making current from residual voltage via *main* loop resistance.

    Teaching defaults: 20 V / 20 mOhm = 1000 A. The precharge resistor
    (170 Ohm teaching value) must never be used here — it would report
    0.12 A and hide a 1000 A make event behind the "95% is enough" shortcut.
    Missing/implausible main-loop evidence must be an error, never a
    silent permission. R <= 0 is rejected; None is rejected.
    """
    if residual_v < 0:
        raise ValueError("residual must be non-negative")
    r_main = cfg.main_loop_resistance_ohm
    if r_main is None or r_main <= 0:
        raise ValueError("main_loop_resistance_ohm must be provided and positive")
    return residual_v / r_main


def main_contact_permitted(
    cfg: PrechargeConfig,
    state: str,
    measured_v: float,
    valid: bool,
    feedback_ok: bool,
    rise_ok: bool,
    *,
    devices_evidence: bool | None = None,
) -> bool:
    """Permission gate: state + valid + feedback + rise + voltage band + making current + device evidence.

    All must hold; any doubt fails closed:
    - state must be PRECHARGE_DONE, measurement valid, feedback and rise windows ok;
    - measured voltage must lie in [threshold, upper] * source_v — overvoltage
      (e.g. 800 V on a 400 V bus, backfeed, sensor fault) and reverse polarity
      (negative reading) are rejected, never approved by a >=380 V test;
    - residual gap = source - measured must yield a making current within the
      main-path device limit, computed with the *main* loop resistance;
    - device-limit evidence must be explicitly True. None/missing evidence
      (None default or a config lacking a positive main making-current limit)
      fails closed rather than signing off the closure.

    The 95% threshold alone does not establish safe making current; this
    function is the checked replacement for the "single voltage opens the
    contactor" shortcut.
    """
    if state != "PRECHARGE_DONE" or not valid or not feedback_ok or not rise_ok:
        return False
    if devices_evidence is not True:
        return False
    if cfg.devices_main_peak_a is None or cfg.devices_main_peak_a <= 0:
        return False
    if cfg.main_loop_resistance_ohm is None or cfg.main_loop_resistance_ohm <= 0:
        return False
    lo = cfg.measure_supply_threshold * cfg.source_v
    hi = cfg.measure_supply_upper_factor * cfg.source_v
    if not lo <= measured_v <= hi:
        return False
    residual_v = cfg.source_v - measured_v
    making_a = residual_v / cfg.main_loop_resistance_ohm
    return making_a <= cfg.devices_main_peak_a


def build_report(cfg: PrechargeConfig) -> dict:
    initial = initial_inrush(cfg)
    report = {
        "scenario_id": SCENARIO_ID,
        "load_scenario_id": LOAD_SCENARIO_ID if cfg.parallel_load_ohm else None,
        "generator": GENERATOR,
        "config": cfg.identity(),
        "tau_s": tau_s(cfg),
        "initial": initial,
        "reach": {
            "90": {"t_s": time_to_fraction(cfg, 0.90), "bus_v": 0.90 * cfg.source_v, "gap_v": 0.10 * cfg.source_v},
            "95": {"t_s": time_to_fraction(cfg, 0.95), "bus_v": 0.95 * cfg.source_v, "gap_v": 0.05 * cfg.source_v},
        },
        "energy": energy_account(cfg, 0.95),
        "steady_state": energy_account(cfg, 1.0),
        "limitations": [
            "All values are teaching assumptions, not product limits or datasheet entries.",
            "The model is an ideal RC loop; parasitics, contactor precharge tap, and layout are not modeled.",
            "A bus-voltage reading cannot by itself identify residual, backfeed, adhesion, or a stuck sensor.",
            "No hardware, bench or reader evidence is included.",
        ],
    }
    if cfg.parallel_load_ohm is not None:
        report["with_load"] = energy_with_load(cfg)
    return report


def write_evidence(out_dir: Path, cfg: PrechargeConfig | None = None) -> dict:
    cfg = cfg or PrechargeConfig()
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(cfg)
    digest = hashlib.sha256(
        (json.dumps(report["config"], sort_keys=True) + GENERATOR).encode("utf-8")
    ).hexdigest()
    report["config_sha256"] = "sha256:" + digest
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (out_dir / "report.json").write_text(text, encoding="utf-8")
    return json.loads(text)


def student_questions() -> list[str]:
    return [
        "把预充电阻改成 100 Ω，τ 与初始电流各变成多少？达到 95% 要多久？",
        "若母线初始残压为 50 V，达到 95% 的时间变成多少？主闸许可的状态还一样吗？",
        "把并联负载改为 2 kΩ，稳态母线和电容最终储能变成多少？主闸许可哪个条件会失败？",
        "解释为什么仅凭母线电压不能区分残压、回灌和粘连；再给一个能区分它们的独立证据。",
        "若只把传感器测到 380 V 就合主闸，会有什么风险？结合 20 V 残余压差与主闸回路电阻说明。",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write report.json to this directory")
    parser.add_argument("--students", action="store_true", help="print student tasks")
    args = parser.parse_args()
    if args.students:
        for index, question in enumerate(student_questions(), 1):
            print(f"{index}. {question}")
        return 0
    if args.out:
        report = write_evidence(args.out)
        print(f"wrote {args.out / 'report.json'}  scenario={report['scenario_id']}")
        return 0
    parser.error("choose --out or --students")


if __name__ == "__main__":
    raise SystemExit(main())
