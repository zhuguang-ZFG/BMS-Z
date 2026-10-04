"""对比实验：同样的"有缺陷输入"喂给三种 SOC 估算器，看谁贴得住真值。

运行：
    cd code/soc
    python3 compare.py            # 打印 RMSE 对比表
    python3 compare.py --plot     # 额外输出 soc_comparison.png

实验设计（对应阶段 4 §4.10 动手任务 1）：
    真值：10Ah Thevenin 电芯跑一段"放电 + 脉冲 + 静置 + CC-CV"工况；
    传感器缺陷（三个估算器共享，公平起见）：
      - 初始 SOC 错 -10 个百分点          —— 上电初始值本来就不可靠，校准点存在的理由
      - 电流：+2mA 零漂 + 噪声        —— 安时积分漂移的元凶
      - 电压：5mV 噪声                 —— 观测噪声
      - 容量：按 9.5Ah 假定（低估 5%） —— 分母本来就不知道准确值
"""
from __future__ import annotations

import sys

import numpy as np

from cell_model import TheveninCell, drive_cycle
from estimators import CoulombOnly, CoulombWithResets, EKFEstimator

DT_S = 1.0
N_STEPS = 16000          # 约 4.4 小时（放电 + 静置 + CC-CV 充电）
Q_TRUE_AH = 10.0
Q_ASSUMED_AH = 9.5       # 容量估错 5%（老化/标定误差的现实）
I_OFFSET_A = 0.002       # 电流零漂 +2mA
I_NOISE_A = 0.02         # 电流噪声 σ=20mA
V_NOISE_V = 0.005        # 电压噪声 σ=5mV
R0, R1, C1 = 0.020, 0.015, 3000.0


def run(seed: int = 42):
    rng = np.random.default_rng(seed)
    cell = TheveninCell(Q_TRUE_AH, R0, R1, C1, soc0=0.8)
    current_cmd = drive_cycle(N_STEPS, DT_S, seed)

    estimators = {
        # 初始 SOC 全部给错（0.7 vs 真值 0.8）：校准点类估算器靠锚点自我纠正，
        # 纯积分只能带着这个误差漂到工况结束
        "纯安时积分": CoulombOnly(0.7, Q_ASSUMED_AH),
        "积分+校准点": CoulombWithResets(0.7, Q_ASSUMED_AH),
        "Thevenin+EKF": EKFEstimator(0.7, Q_ASSUMED_AH, R0, R1, C1),
    }
    soc_true = np.empty(N_STEPS)
    soc_est = {name: np.empty(N_STEPS) for name in estimators}

    for k in range(N_STEPS):
        i_true = current_cmd[k]
        soc_true[k] = cell.soc
        v_true = cell.step(i_true, DT_S)

        # 传感器视角：真值 + 缺陷
        i_meas = i_true + I_OFFSET_A + rng.normal(0.0, I_NOISE_A)
        v_meas = v_true + rng.normal(0.0, V_NOISE_V)

        for name, est in estimators.items():
            soc_est[name][k] = est.step(i_meas, v_meas, DT_S)

    return soc_true, soc_est


def main() -> None:
    # Windows 终端默认 GBK：避免中文输出乱码
    if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    soc_true, soc_est = run()
    print(f"工况：{N_STEPS * DT_S / 3600:.1f}h ｜ 容量假定 {Q_ASSUMED_AH}Ah（真值 "
          f"{Q_TRUE_AH}Ah）｜ 电流零漂 +{I_OFFSET_A * 1000:.0f}mA ｜ 初始 SOC 0.7（真值 0.8）\n")
    print(f"{'估算器':<14}{'RMSE':>10}{'末端误差':>12}")
    print("-" * 38)
    for name, est in soc_est.items():
        err = est - soc_true
        rmse = float(np.sqrt(np.mean(err ** 2)))
        print(f"{name:<14}{rmse:>9.2%}{err[-1]:>11.2%}")

    if "--plot" in sys.argv:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        t_h = np.arange(N_STEPS) * DT_S / 3600.0
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(t_h, soc_true * 100, color="gray", lw=2, label="真值")
        for name, est in soc_est.items():
            ax.plot(t_h, est * 100, lw=1, label=name)
        ax.set_xlabel("时间 (h)")
        ax.set_ylabel("SOC (%)")
        ax.set_title("三种 SOC 估算器 vs 真值（初始 SOC 错 -10%、零漂 +2mA、容量低估 5%）")
        ax.legend()
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig("soc_comparison.png", dpi=150)
        print("\n已输出 soc_comparison.png")


if __name__ == "__main__":
    main()
