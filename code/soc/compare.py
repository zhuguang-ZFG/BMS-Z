"""对比实验：同样的"有缺陷输入"喂给三种 SOC 估算器，看谁贴得住真值。

运行：
    cd code/soc
    python3 compare.py            # 打印 RMSE 对比表
    python3 compare.py --plot     # 额外输出 soc_comparison.png
    python3 compare.py --sweep    # 参数失配表：哪个参数写错更要命（第 10 章与共学第九天引用它）

实验设计（对应阶段 4 §4.10 动手任务 1）：
    真值：10Ah Thevenin 电芯跑一段"上电静置 + 放电 + 脉冲 + 静置 + CC-CV"工况；
    传感器缺陷（三个估算器共享，公平起见）：
      - 初始 SOC 错 -10 个百分点          —— 上电初始值本来就不可靠，校准点存在的理由
      - 电流：+2mA 零漂 + 噪声        —— 安时积分漂移的元凶
      - 电压：5mV 噪声                 —— 观测噪声
      - 容量：按 9.5Ah 假定（低估 5%） —— 分母本来就不知道准确值
    注意（最好情形）：EKF 拿到的 R0/R1/C1 与 OCV 曲线和真值完全相同，
    所以它的 RMSE 不能外推到真实电芯（参数未知且会变）。
    --sweep 换掉最后这条"最好情形"：真值仍标称，只把 EKF 侧参数写错，
    量出"错在电阻上滤波器当场喊、错在容量上它慢慢兜"。
"""
from __future__ import annotations

import sys

import numpy as np

from cell_model import TheveninCell, drive_cycle
from estimators import CoulombOnly, CoulombWithResets, EKFEstimator

DT_S = 1.0
N_STEPS = 17000          # 约 4.7 小时（上电静置 + 放电 + 静置 + CC-CV 充电）
Q_TRUE_AH = 10.0
Q_ASSUMED_AH = 9.5       # 容量估错 5%（老化/标定误差的现实）
I_OFFSET_A = 0.002       # 电流零漂 +2mA
I_NOISE_A = 0.02         # 电流噪声 σ=20mA
V_NOISE_V = 0.005        # 电压噪声 σ=5mV
R0, R1, C1 = 0.020, 0.015, 3000.0


def run(seed: int = 42):
    """返回每步结束时的真值与估计值；第 k 项对应 (k+1)*DT_S 秒。"""
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
        v_true = cell.step(i_true, DT_S)
        soc_true[k] = cell.soc           # 与 est.step 返回值同属本步结束时刻

        # 传感器视角：真值 + 缺陷
        i_meas = i_true + I_OFFSET_A + rng.normal(0.0, I_NOISE_A)
        v_meas = v_true + rng.normal(0.0, V_NOISE_V)

        for name, est in estimators.items():
            soc_est[name][k] = est.step(i_meas, v_meas, DT_S)

    return soc_true, soc_est


def measure_soc_error(r0: float, r1: float, c1: float, q_ah: float,
                      seed: int = 42) -> tuple[float, float]:
    """返回 (RMSE %, 末端误差 %)：真值电芯始终标称，只换 EKF 侧的参数与容量。

    传感器缺陷、工况与 run() 完全一致，所以这张表只回答一个问题：
    同样的观测、同样的偏差输入下，EKF 对哪个参数错最不能忍。
    """
    rng = np.random.default_rng(seed)
    cell = TheveninCell(Q_TRUE_AH, R0, R1, C1, soc0=0.8)
    current_cmd = drive_cycle(N_STEPS, DT_S, seed)
    estimator = EKFEstimator(0.7, q_ah, r0, r1, c1)
    errors = np.empty(N_STEPS)
    for k in range(N_STEPS):
        i_true = current_cmd[k]
        v_true = cell.step(i_true, DT_S)
        i_meas = i_true + I_OFFSET_A + rng.normal(0.0, I_NOISE_A)
        v_meas = v_true + rng.normal(0.0, V_NOISE_V)
        errors[k] = estimator.step(i_meas, v_meas, DT_S) - cell.soc
    return 100 * float(np.sqrt(np.mean(errors ** 2))), 100 * float(errors[-1])


# 参数失配表：第 10 章「BMS-Z 的合成对照」与共学第九天引用的 41.51% / 36.14% / 1.00%
# 就出自这里（tests/test_compare_sweep.py 钉住这三个数）。字面 grep 找不到它们——
# 它们是算出来的，所以改动估计器或这组接线时必须让测试先红。
PARAM_SWEEP = [
    ("出厂 R0=20mΩ", 0.020, 0.015, 3000.0, Q_ASSUMED_AH),
    ("R0 十倍 200mΩ", 0.200, 0.015, 3000.0, Q_ASSUMED_AH),
    ("R1 十倍 150mΩ", 0.020, 0.150, 3000.0, Q_ASSUMED_AH),
    ("C1 十倍 30000F", 0.020, 0.015, 30000.0, Q_ASSUMED_AH),
    ("容量砍半 5.0Ah", 0.020, 0.015, 3000.0, 5.0),
    ("容量 11Ah", 0.020, 0.015, 3000.0, 11.0),
]


def print_sweep() -> None:
    print(f"参数失配：真值电芯标称 R0={R0} / R1={R1} / C1={C1:.0f}、容量 {Q_TRUE_AH}Ah，")
    print(f"只把 EKF 侧写错；同 seed 42、同 {N_STEPS * DT_S / 3600:.1f}h 工况、同传感器缺陷\n")
    print(f"{'参数':<18}{'RMSE':>10}{'末端误差':>12}")
    print("-" * 40)
    for name, r0, r1, c1, q_ah in PARAM_SWEEP:
        rmse, end = measure_soc_error(r0, r1, c1, q_ah)
        print(f"{name:<18}{rmse:>9.2f}%{end:>11.2f}%")
    print("\n读法：电阻错就崩（R0/R1 直接乘在瞬态电流上，工况里到处是阶跃），")
    print("C1 与容量错几乎不动（滤波每拍用电压观测把它拉回来）——观测只能钉住它看得见的量。")


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
    print("\n注：EKF 使用与真值相同的 R0/R1/C1 与 OCV（最好情形），其 RMSE 不能外推到真实电芯。")

    if "--sweep" in sys.argv:
        print()
        print_sweep()
        return

    if "--plot" in sys.argv:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        t_h = (np.arange(N_STEPS) + 1) * DT_S / 3600.0
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
