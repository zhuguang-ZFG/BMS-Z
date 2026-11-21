"""OS01 独立积分器交叉核验：同一离散 SPMe 模型 + scipy LSODA（非 PyBaMM 求解器）。

边界（如实登记）：
- 模型/RHS 来自 PyBaMM 离散管线（EvaluatorPython，solver.process 同款通道，102 维已验证 finite）；
- **时间积分独立**：scipy `solve_ivp(method="LSODA")`（刚性自适应；短窗实测选型见
  `independent_integrate` docstring），不调用任何 PyBaMM 求解器；
- 输出对比在**状态向量**层（sol.y 同序），不构造电压/事件求值器（上游变量树在
  26.10 的求值通道受 Constant/FunctionParameter 限制，已探明并放弃）；
- 故这是「独立积分器锚点」，不是「独立模型锚点」。独立模型锚点仍缺。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pybamm
import scipy
from scipy.integrate import solve_ivp

EVIDENCE = Path(__file__).resolve().parent / "evidence" / "os01-independent-reference.json"


def build_spme_rhs():
    """Simulation 同款两段式 delayed 处理，返回 (rhs_callable, y0, capacity_Ah)。"""
    model = pybamm.lithium_ion.SPMe()
    param = pybamm.ParameterValues("Chen2020")
    capacity = float(param["Nominal cell capacity [A.h]"])
    param["Current function [A]"] = capacity  # 显式 1C 放电电流幅值
    geometry = model.default_geometry
    m2 = param.process_model(model, inplace=False, delayed_variable_processing=True)
    param.process_geometry(geometry)
    mesh = pybamm.Mesh(geometry, model.default_submesh_types, model.default_var_pts)
    built = pybamm.Discretisation(mesh, model.default_spatial_methods).process_model(
        m2, inplace=False, delayed_variable_processing=True
    )
    y0 = np.asarray(built.concatenated_initial_conditions.evaluate()).flatten()
    rhs = pybamm.EvaluatorPython(built.concatenated_rhs)
    return rhs, y0, capacity


def independent_integrate(rhs, y0, t_end, rtol=1e-9, atol=1e-11, method="LSODA", t_eval=None):
    """scipy 显式/隐式自适应积分（非 PyBaMM 求解器），0→t_end。

    t_eval 给出时由求解器 dense output 直接采样（避免事后线性插值误差）。
    方法选择依据（t∈[0,100s] 短窗实测，rtol=1e-6/atol=1e-8）：
    RK45 45399 步/26.0s（SPMe 半离散刚性，步数爆炸）；Radau 34 步/1.5s；
    LSODA 127 步/0.2s——选 LSODA。
    容差 1e-9/1e-11：使差异反映求解器间而非积分器截断。
    """
    f = lambda t, y: np.asarray(rhs(t=float(t), y=np.asarray(y))).flatten()  # noqa: E731
    sol = solve_ivp(f, (0.0, t_end), y0, method=method, rtol=rtol, atol=atol, t_eval=t_eval)
    if not sol.success:
        raise RuntimeError(f"{method} failed: {sol.message}")
    y_out = sol.y.T
    return sol.t, y_out, {"method": method, "n_steps": int(sol.t.size - 1),
                          "nfev": int(getattr(sol, "nfev", -1)),
                          "dense_sampling": bool(t_eval is not None)}


def reference_solution():
    """PyBaMM IDAKLU 参考解（显式求解器对象，rtol=1e-9/atol=1e-11，与独立积分侧对齐），1C 放电至 2.5V。

    鉴别实验：Simulation 默认求解路径输出的参考轨迹与 LSODA 交叉核验 max_rel=1.9e-4；
    显式 IDAKLUSolver(rtol=1e-6) 下 max_rel=2.3e-6、rtol=1e-10 下 4.5e-9——
    早期差异源于默认路径的求解器容差/输出插值，非独立积分器问题。
    """
    sim = pybamm.Simulation(
        pybamm.lithium_ion.SPMe(),
        experiment=pybamm.Experiment(["Discharge at 1C until 2.5 V"]),
        parameter_values=pybamm.ParameterValues("Chen2020"),
        solver=pybamm.IDAKLUSolver(rtol=1e-9, atol=1e-11),
    )
    sol = sim.solve()
    t = sol["Time [s]"].entries
    y = np.asarray(sol.y)  # (n_states, n_times)，与 concatenated_rhs 同序
    return t, y, str(getattr(sol, "termination", "") or "")


def main() -> int:
    rhs, y0, capacity = build_spme_rhs()
    t_ref, y_ref, term = reference_solution()
    t_end_ref = float(t_ref[-1])

    t_rk, y_rk, stats = independent_integrate(rhs, y0, t_end_ref, t_eval=t_ref)

    # 参考时刻由求解器 dense output 直接给出（无 np.interp 线性插值误差）
    y_rk_at_ref = y_rk
    y_ref_t = y_ref.T  # (n_times, n_states)，与独立积分采样对齐
    dy = np.abs(y_rk_at_ref - y_ref_t)
    scale = np.maximum(np.abs(y_ref_t), 1e-6)
    rel_err_t = np.max(dy / scale, axis=1)
    max_rel_err = float(rel_err_t.max())
    rel_l2 = float(np.linalg.norm(dy) / max(np.linalg.norm(y_ref_t), 1e-12))
    max_rel_pass = bool(max_rel_err < 1e-4)

    report = {
        "source_id": "OS01",
        "benchmark": "独立积分器交叉核验：同一离散 SPMe 模型 + scipy solve_ivp LSODA"
                     "（非 PyBaMM 求解器；选型实测见 independent_integrate docstring）",
        "anchor_scope": "独立时间积分（scipy LSODA，非 PyBaMM 求解器）；模型与 RHS 仍来自 PyBaMM 离散管线——非独立模型锚点",
        "state_dim": int(y0.size),
        "capacity_Ah": capacity,
        "pybamm_version": pybamm.__version__,
        "independent_integrator": {
            "integrator": "scipy solve_ivp LSODA",
            "rtol": 1e-9, "atol": 1e-11,
            "nfev": stats["nfev"],
            "n_output_intervals": stats["n_steps"],  # t_eval 输出采样区间数
            "internal_steps": "unavailable（solve_ivp 不暴露 LSODA 内部步计数）",
            "scipy_version": scipy.__version__,
            "t_end_s": float(t_rk[-1]), "n_output_points": int(len(t_rk)),
        },
        "reference": {"solver": "IDAKLU 显式 rtol=1e-9/atol=1e-11", "termination": term,
                      "t_end_s": t_end_ref, "n_times": int(len(t_ref))},
        "comparison": {
            "n_reference_times": int(len(t_ref)),
            "max_relative_state_error": max_rel_err,
            "rel_l2_states": rel_l2,
            "pass_1e-4": max_rel_pass,
            "metric": "纯相对 |dy|/max(|y_ref|,1e-6)，dense-output 采样（无插值）",
        },
        "limitations": [
            "电压/事件求值器未构造：26.10 变量树含 Constant/FunctionParameter 残留，"
            "EvaluatorPython/to_casadi 直通均不可用（已探明）",
            "独立积分器无事件定位：积分终点 t_end_ref 由 IDAKLU 参考解给定（输入约束），"
            "端点一致不构成事件触发的交叉验证",
        ],
    }
    report["all_pass"] = max_rel_pass
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["all_pass", "independent_integrator", "reference", "comparison"]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
