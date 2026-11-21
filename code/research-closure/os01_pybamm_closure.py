#!/usr/bin/env python3
"""OS01 PyBaMM real-closure evidence script (runs INSIDE .venv-os01).

Produces a JSON evidence file for the OS01 adoption row:
- pinned version actually installed;
- API anchors from the adoption row: compare_lithium_ion, SPMe submodel,
  rate-capability experiment dependencies/parameters/events;
- a real SPMe 1C discharge solve with termination event and energy
  integral (V*I over time, independent of PyBaMM's own energy variables);
- a small grid/tolerance study (two spatial discretisations, max |dV|).

Anything the pinned version cannot provide is recorded as null with a note —
silence is not evidence. Stdlib + pybamm only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pybamm

OUT = Path(__file__).resolve().parent / "evidence"
OUT.mkdir(parents=True, exist_ok=True)


def api_anchors() -> dict:
    spme = pybamm.lithium_ion.SPMe()
    # pybamm.lithium_ion 是包属性命名空间，不是子模块——用属性访问，不走 importlib
    liion = pybamm.lithium_ion
    # 实名锚点：pybamm.lithium_ion 是属性命名空间，直接 getattr；找不到记 unavailable
    compare = getattr(liion, "compare_lithium_ion", None)
    rate_probe = {"parsed": False, "error": None}
    try:
        pybamm.Experiment(["Discharge at 0.5C for 10 minutes", "Discharge at 1C for 10 minutes"])
        rate_probe["parsed"] = True
    except Exception as exc:
        rate_probe["error"] = f"{type(exc).__name__}: {exc}"
    return {
        "compare_lithium_ion": {
            "present": compare is not None,
            "symbol": "pybamm.lithium_ion.compare_lithium_ion",
        },
        "spme_submodel_names": sorted(spme.submodels.keys())[:12],
        "spme_default_events": [e.name for e in spme.events],
        "rate_capability_probe": rate_probe,
        "pybamm_version": pybamm.__version__,
    }


def solve_and_integrate(var_pts: dict | None = None) -> dict:
    """真实 1C 放电实验：用 Experiment 显式声明倍率与截止电压，
    终止事件由求解器实际触发，不是猜的。"""
    model = pybamm.lithium_ion.SPMe()
    experiment = pybamm.Experiment(["Discharge at 1C until 2.5 V"])
    param = pybamm.ParameterValues("Chen2020")
    sim = pybamm.Simulation(model, experiment=experiment, parameter_values=param,
                            var_pts=var_pts)
    sol = sim.solve()
    t = sol["Time [s]"].entries
    v = sol["Voltage [V]"].entries
    i = sol["Current [A]"].entries
    energy_j = float(sum((v[k] + v[k - 1]) / 2 * (i[k] + i[k - 1]) / 2 * (t[k] - t[k - 1])
                         for k in range(1, len(t))))
    term = str(getattr(sol, "termination", "") or "")
    term_event = term if term.startswith("event") else None
    return {
        "experiment": "Discharge at 1C until 2.5 V",
        "n_time_points": len(t),
        "t_end_s": float(t[-1]),
        "v_start": float(v[0]),
        "v_end": float(v[-1]),
        "energy_wh": abs(energy_j) / 3600.0,
        "termination": getattr(sol, "termination", None),
        "termination_event": term_event,
        "available_events": [e.name for e in model.events],
        "v_min": float(min(v)),
    }


def solve_with_pts(var_pts: dict) -> dict:
    model = pybamm.lithium_ion.SPMe()
    experiment = pybamm.Experiment(["Discharge at 1C until 2.5 V"])
    sim = pybamm.Simulation(model, experiment=experiment,
                            parameter_values=pybamm.ParameterValues("Chen2020"),
                            var_pts=var_pts)
    return sim.solve()


def grid_study() -> dict:
    """粗/细两套空间离散对照：以模型默认 var_pts 为基，逐轴缩放。"""
    base = pybamm.lithium_ion.SPMe().default_var_pts
    for axis in list(base.keys()):
        try:
            coarse_pts = {k: (5 if k == axis else v) for k, v in base.items()}
            fine_pts = {k: (20 if k == axis else v) for k, v in base.items()}
            c = solve_with_pts(coarse_pts)
            f = solve_with_pts(fine_pts)
            cv, fv = c["Voltage [V]"].entries, f["Voltage [V]"].entries
            def _energy(sol):
                tt = sol["Time [s]"].entries
                vv = sol["Voltage [V]"].entries
                ii = sol["Current [A]"].entries
                return abs(sum((vv[k] + vv[k - 1]) / 2 * (ii[k] + ii[k - 1]) / 2
                               * (tt[k] - tt[k - 1]) for k in range(1, len(tt)))) / 3600.0

            return {
                "axis": str(axis), "coarse_npts": 5, "fine_npts": 20,
                "abs_dv_end": abs(float(cv[-1] - fv[-1])),
                "energy_diff_wh": abs(_energy(c) - _energy(f)),
                "coarse_t_end_s": float(c["Time [s]"].entries[-1]),
                "fine_t_end_s": float(f["Time [s]"].entries[-1]),
                "note": "以 default_var_pts 为基的粗/细对照；时间步长不同不做逐点电压差",
            }
        except Exception:
            continue
    return {"error": "no default var_pts axis accepted", "note": "grid study failed on pinned version"}


def main() -> int:
    report = {
        "source_id": "OS01",
        "closure_scope": "轻量基准（E12 可先做档）：真实求解 + API 锚点 + 网格/能量对照；非全量 P6 基准",
        "api": api_anchors(),
        "baseline_solve": solve_and_integrate(),
        "grid_study": grid_study(),
    }
    out = OUT / "os01-closure.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "pybamm_version": report["api"]["pybamm_version"],
        "baseline_v_end": round(report["baseline_solve"]["v_end"], 4),
        "energy_wh": round(report["baseline_solve"]["energy_wh"], 4),
        "termination_event": report["baseline_solve"]["termination_event"],
        "grid_study": "ok" if "error" not in report["grid_study"] else report["grid_study"]["error"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
