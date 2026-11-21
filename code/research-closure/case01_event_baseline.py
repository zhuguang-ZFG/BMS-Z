#!/usr/bin/env python3
"""CASE01 analytic ODE baseline for PyBaMM#5072/#5205 event semantics.

Hand-computable benchmark (acceptance: 端点/左右侧/重复事件):
    dy/dt = a  for t <  ts
          = b  for t >= ts ,   y(0) = 0
    analytic:  y(t) = a*t                 (t <  ts)
             y(t) = a*ts + b*(t - ts)     (t >= ts)

Cases (t_eval = [0, 3, 10]):
- before   ts=-1  : never switched      -> y(10) = a*10
- inside   ts=5   : switch inside       -> y(10) = a*5 + b*5
- endpoint ts=3   : PR #5205 regression [-5,0,1,3,3,5,10,12]@[0,3,10]->[1,3,5]:
                    ts=3 kept, right-continuous expected y(10)=a*3+b*7
- after    ts=12  : never switched      -> y(10) = a*10
- repeated ts=[1,1,3,3]: dedup to {1,3} -> y(10) = a*3 + b*7

For each case the numeric solution is compared to the analytic value at the
last t_eval. A case "passes" iff |numeric - analytic| <= tol. The script
records pybamm/solver versions, per-case deltas, and an overall verdict; it
never edits the model under test.
"""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import pybamm
import numpy as np

OUT = Path(__file__).resolve().parent / "evidence"
OUT.mkdir(parents=True, exist_ok=True)

A, B = 1.0, 3.0
T_EVAL = [0.0, 3.0, 10.0]
TOL = 1e-6


def analytic(ts_list: list[float], t: float) -> float:
    """与模型构造严格一致：rhs = A + (B-A)*|{ts <= t'}|（重复时刻按重数计）。

    负时刻切换在 t=0 已生效；重复时刻每次贡献一次独立翻转。
    """
    switches = sorted(ts_list)  # 保留重数
    y = 0.0
    prev = 0.0
    k = 0
    for ts in switches:
        if ts < 0:
            k += 1
            continue
        if ts > t:
            break
        y += (A + (B - A) * k) * (ts - prev)
        prev = ts
        k += 1
    y += (A + (B - A) * k) * (t - prev)
    return y


def numeric(ts_list: list[float], solver_kind: str) -> float:
    model = pybamm.BaseModel()
    y = pybamm.Variable("y")
    t = pybamm.t
    rhs = A
    for ts in ts_list:  # 不去重：重复时刻以重复 Heaviside 节点进入模型树
        rhs = rhs + (B - A) * (t >= ts)  # 比较式：右侧生效
    model.rhs = {y: rhs}
    model.initial_conditions = {y: pybamm.Scalar(0.0)}
    if solver_kind == "idaklu":
        solver = pybamm.IDAKLUSolver()
    else:
        solver = pybamm.CasadiSolver(mode="safe")
    solution = solver.solve(model, t_eval=np.array(T_EVAL))
    return float(solution["y"].entries[-1])


def heaviside_count(ts_list: list[float]) -> int:
    """完整性探针：直接数模型树里的 _Heaviside 节点数（pre_order 不做简化/去重）。"""
    from pybamm.expression_tree.binary_operators import _Heaviside

    model = pybamm.BaseModel()
    y = pybamm.Variable("y")
    t = pybamm.t
    rhs = A
    for ts in ts_list:
        rhs = rhs + (B - A) * (t >= ts)
    model.rhs = {y: rhs}
    model.initial_conditions = {y: pybamm.Scalar(0.0)}
    model.concatenated_rhs = pybamm.NumpyConcatenation(*model.rhs.values())
    return sum(1 for s in model.concatenated_rhs.pre_order() if isinstance(s, _Heaviside))


CASES = {
    "before": [-1.0],
    "inside": [5.0],
    "endpoint": [3.0],
    "after": [12.0],
    "repeated": [1.0, 1.0, 3.0, 3.0],
}


def main() -> int:
    solver_kind = sys.argv[1] if len(sys.argv) > 1 else "casadi"
    results = {}
    for name, ts in CASES.items():
        try:
            num = numeric(ts, solver_kind)
            ref = analytic(sorted(ts), T_EVAL[-1])
            results[name] = {"ts": ts, "numeric": num, "analytic": ref,
                             "abs_err": abs(num - ref), "pass": abs(num - ref) <= TOL}
        except Exception as exc:
            results[name] = {"ts": ts, "error": f"{type(exc).__name__}: {exc}", "pass": False}
    report = {
        "source_id": "CASE01",
        "pybamm_version": pybamm.__version__,
        "python": platform.python_version(),
        "solver": solver_kind,
        "t_eval": T_EVAL,
        "tol": TOL,
        "integrity": {name: {"declared_ts": ts, "heaviside_nodes": heaviside_count(ts),
                             "duplicates_reach_model": heaviside_count(ts) == len(ts)}
                      for name, ts in CASES.items()},
        "cases": results,
        "all_pass": all(r.get("pass") for r in results.values()),
        "boundary": "手算 ODE 基准只检验时间比较式事件的端点/去重/左右侧语义；"
                    "不重建原 issue 自定义 Yang/Basic DFN 半电池 MWE，"
                    "不证明 IDAKLU 在其它模型上的行为。",
    }
    out = OUT / f"case01-baseline-{pybamm.__version__}-{solver_kind}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pybamm": pybamm.__version__, "all_pass": report["all_pass"],
                      "cases": {k: r.get("pass") for k, r in results.items()}},
                     ensure_ascii=False, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
