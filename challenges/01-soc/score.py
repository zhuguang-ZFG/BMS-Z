"""第 1 期仿真擂台：固定种子的合成工况，给纯安时积分打一个 RMSE 基线。

复用 code/soc 的 Thevenin 模型和三种教学估算器，不改那些文件。
数字是仿真结果，不是电芯实测。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# code/soc 里的模块互相用「同目录 import」。先放进路径，再按原样导入。
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code" / "soc"))

from cell_model import TheveninCell  # noqa: E402
from estimators import CoulombOnly, CoulombWithResets, EKFEstimator  # noqa: E402

SEED = 20261006
DT_S = 1.0
N_STEPS = 5000
Q_TRUE_AH = 10.0
Q_ASSUMED_AH = 9.5
SOC0_TRUE = 0.80
SOC0_EST = 0.70
I_OFFSET_A = 0.002
I_NOISE_A = 0.02
V_NOISE_V = 0.005
R0, R1, C1 = 0.020, 0.015, 3000.0
BASELINE_NAME = "纯安时积分"


def command_current(n_steps: int = N_STEPS, dt_s: float = DT_S, seed: int = SEED) -> np.ndarray:
    """合成电流 (A)：静置 → 放电加脉冲 → 长静置 → 恒流充 → 指数收尾。"""
    rng = np.random.default_rng(seed)
    t = np.arange(n_steps) * dt_s
    current = np.zeros(n_steps)
    discharge = (t >= 300.0) & (t < 1800.0)
    current[discharge] = -1.5
    pulse = discharge & (rng.random(n_steps) < 0.04)
    extra = rng.uniform(0.5, 2.0, int(pulse.sum()))
    current[pulse] = -1.5 - extra
    charge = (t >= 2800.0) & (t < 4600.0)
    current[charge] = 2.0
    taper = t >= 4600.0
    current[taper] = 2.0 * np.exp(-(t[taper] - 4600.0) / 200.0)
    return current


def simulate(seed: int = SEED):
    """返回测量电流、测量电压、真值 SOC，以及三种教学估算器的 SOC。"""
    rng = np.random.default_rng(seed + 1)
    cell = TheveninCell(Q_TRUE_AH, R0, R1, C1, soc0=SOC0_TRUE)
    i_cmd = command_current(seed=seed)
    estimators = {
        BASELINE_NAME: CoulombOnly(SOC0_EST, Q_ASSUMED_AH),
        "积分+校准点": CoulombWithResets(SOC0_EST, Q_ASSUMED_AH),
        "Thevenin+EKF": EKFEstimator(SOC0_EST, Q_ASSUMED_AH, R0, R1, C1),
    }
    i_meas = np.empty(N_STEPS)
    v_meas = np.empty(N_STEPS)
    soc_true = np.empty(N_STEPS)
    soc_est = {name: np.empty(N_STEPS) for name in estimators}
    for k in range(N_STEPS):
        v_true = cell.step(float(i_cmd[k]), DT_S)
        soc_true[k] = cell.soc
        i_meas[k] = i_cmd[k] + I_OFFSET_A + rng.normal(0.0, I_NOISE_A)
        v_meas[k] = v_true + rng.normal(0.0, V_NOISE_V)
        for name, est in estimators.items():
            soc_est[name][k] = est.step(float(i_meas[k]), float(v_meas[k]), DT_S)
    return i_meas, v_meas, soc_true, soc_est


def rmse(estimate: np.ndarray, truth: np.ndarray) -> float:
    err = np.asarray(estimate, dtype=float) - np.asarray(truth, dtype=float)
    return float(np.sqrt(np.mean(err ** 2)))


def baseline_table(seed: int = SEED) -> dict[str, float]:
    _i, _v, soc_true, soc_est = simulate(seed)
    return {name: rmse(est, soc_true) for name, est in soc_est.items()}


def main() -> None:
    table = baseline_table()
    print(
        f"仿真结果｜种子 {SEED}｜{N_STEPS} 步 × {DT_S:.0f}s｜"
        f"容量假定 {Q_ASSUMED_AH}Ah（模型 {Q_TRUE_AH}Ah）｜"
        f"初始 SOC {SOC0_EST}（模型 {SOC0_TRUE}）"
    )
    print(f"{'估算器':<16}{'RMSE':>12}")
    print("-" * 28)
    for name, value in table.items():
        mark = "  ← 基线，要胜过它" if name == BASELINE_NAME else "  ← 仓库参考，不是基线"
        print(f"{name:<16}{value:>11.6%}{mark}")
    print("状态：进行中。榜单只收这份合成工况上的仿真 RMSE，不收电芯实测。")


if __name__ == "__main__":
    main()
