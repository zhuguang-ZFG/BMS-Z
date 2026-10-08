"""HPPC 脉冲参数辨识合成演示：从电压响应反推 R0、R1、C1。

对应教程：阶段 4 §4.4（等效电路模型的参数来源）与 §4.10 任务 2。
任务 2 要求用真实电池或公开数据集做 HPPC 辨识——动手部分仓库不代做；
本脚本提供同构的合成演示：TheveninCell 当"真电池"，打标准脉冲、加测量
噪声，再按 §4.4 的物理一步一步把三个参数反推回来，最后与真值对账。

辨识三步（就是 §4.4 那张电压响应曲线的读法）：

1. R0：脉冲起始瞬间的电压跳变 ÷ 电流跳变——"立刻的压降"（欧姆内阻）；
2. τ = R1·C1：拟合脉冲后静置段的指数回弹（网格搜索 τ + 线性最小二乘，
   不依赖 scipy，也让你看清"拟合"到底在最小化什么）；
3. R1：由回弹幅值反解——脉冲只持续 10s，U_rc 充不到稳态，要除以
   (1 - exp(-T/τ)) 修正；C1 = τ / R1。

与真实 HPPC 的两点差异（真实实验对应环节在任务 2 原文）：

- 真实实验在同一颗电池上放点到下一个 SOC 点再打脉冲；这里每个 SOC 点
  直接初始化一颗新电池，跳过中间放电段，把注意力集中在脉冲→拟合闭环；
- 真实数据还有温度漂移与接触阻抗，这里只有电压/电流测量噪声
  （σ = 1mV / 5mA，典型手持表量级）。

运行：cd code/soc && python3 hppc_demo.py
退出码 0 = 全部 SOC 点辨识误差在容差内；1 = 超差（打印超差项）。

---- 真实数据适配说明（阶段 4 §4.10 任务 2 的"地图"，不是代做） ----

实验与数据是你的；下面只是把 identify_one 的三步接到真实采集文件上时
必须自己处理的四件事：

1. 数据整形：整理成三列 t(s), I(A), U(V)，电流符号按本仓库约定
   （充电 > 0）。真实 HPPC 是连续记录，用 |I| > 0.5C 检出脉冲沿，
   切出「脉冲前 1s 基线 + 脉冲段 + 脉冲后静置段」三元组；
2. 静置窗长按你的 τ 定，不要照抄 120s：窗长 ≥ 3–4 倍你预期的 τ，
   否则回到本脚本注释里那个 40s 病态（窗长不够时 K 与 A 分不开）；
3. 温度是真数据特有的坑：实验期间电芯温度漂 1°C，OCV 与内阻都在动，
   长静置窗会拟合出假 τ——对策是每个脉冲段独立估计 offset（本脚本的
   二维 lstsq 已经这么做），并记录每段温度做 sanity check；
4. R0 的物理边界：跳变法测到的 R0 含接触阻抗与线损——四线制（开尔文
   接法）才能把电芯本体与夹具分开；采样率 ≥10Hz，否则跳变沿被滤波，
   R0 系统性偏大。

接口复用：fit_relaxation(t, u) 与跳变均值法原样可用——把你的段数据喂
进去即可；SOC 点归属用脉冲前 OCV 反查（你的 OCV 表，或本仓库 ocv()）。
"""
from __future__ import annotations

import sys

import numpy as np

from cell_model import TheveninCell

# ---- 实验配置（与教程口径一致：充电 I > 0，放电 I < 0） --------------------
Q_AH = 3.0            # 电芯容量 (Ah)，18650 量级
I_PULSE = -3.0        # 放电脉冲电流 (A) = 1C
T_PULSE = 10.0        # 脉冲时长 (s)，HPPC 标准值
T_REST = 120.0        # 脉冲后静置 (s)：须覆盖约 3 个 τ 回弹才可辨识——车规 HPPC
                      # 的 40s 是为"10s 电阻"快测设计的，拿来拟合 τ 会病态（本脚本
                      # 实测：40s 窗下渐近线与幅值互相"抢"噪声，R1 误差达 77%）
DT = 0.1              # 采样间隔 (s)，10 Hz 手持表量级
V_NOISE = 1e-3        # 电压噪声 σ (V)
I_NOISE = 5e-3        # 电流噪声 σ (A)
SEED = 20261005

# 各 SOC 点的"真值"（18650 NCM 典型量级：低 SOC 内阻抬头、极化加重）
SOC_POINTS = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2])
TRUE_R0 = np.array([26, 27, 28, 30, 33, 37, 42, 48]) * 1e-3   # Ω
TRUE_R1 = np.array([12, 12, 13, 14, 16, 18, 21, 24]) * 1e-3   # Ω
TRUE_C1 = np.array([3000, 2800, 2600, 2400, 2200, 2000, 1800, 1600])  # F
# → τ = R1·C1 ≈ 34–38s，恰好在网格搜索区间中段

# 自验收容差（相对误差）：噪声 σ 与网格分辨率 0.5s 决定，见 main() 的对账表
TOL_R0, TOL_R1, TOL_C1 = 0.10, 0.15, 0.20


def simulate_pulse(soc0: float, r0: float, r1: float, c1: float,
                   noise: bool = True, seed: int = SEED):
    """在一个 SOC 点打一次"静置→放电脉冲→静置"，返回采样序列。

    返回 (t, u, i, n_pre, n_pulse)：t/u/i 为全长数组；前 n_pre 点是脉冲前
    静置，其后 n_pulse 点是脉冲段，剩余为脉冲后静置段。
    """
    rng = np.random.default_rng(seed)
    cell = TheveninCell(Q_AH, r0, r1, c1, soc0=soc0)
    n_pre = int(10.0 / DT)                    # 脉冲前静置 10s（记录基线）
    n_pulse = int(T_PULSE / DT)
    n_rest = int(T_REST / DT)
    n_total = n_pre + n_pulse + n_rest

    t = np.arange(n_total) * DT
    i = np.zeros(n_total)
    i[n_pre:n_pre + n_pulse] = I_PULSE
    if noise:
        i = i + rng.normal(0.0, I_NOISE, n_total)

    u = np.empty(n_total)
    for k in range(n_total):
        u[k] = cell.step(float(i[k]), DT)
        if noise:
            u[k] += rng.normal(0.0, V_NOISE)
    return t, u, i, n_pre, n_pulse


def fit_relaxation(t_rel: np.ndarray, u_rel: np.ndarray, *, tau_grid=None):
    """网格搜索 τ + 二维线性最小二乘拟合 U(t) = K + A·exp(-t/τ)。

    返回 (tau, amp, offset)。τ 给定时 exp(-t/τ) 已知，问题退化为对
    K、A 的线性最小二乘——这就是"非线性拟合"最朴素的做法：只把非线性
    的那一维拿出来扫。

    窗口必须够长本方法才成立：40s 窗（车规 10s 电阻快测的配套静置）里
    exp(-t/τ) 衰减不到 1/3，与常数基高度相关，K 与 A 互相"抢"噪声
    （实测 R1 误差 77%）；120s ≈ 3.4 个 τ 后两者可分。反过来把 K 钉死在
    末段均值也不行——残尾 3% 的偏置会耦进 τ（实测无噪声 τ 被吸到 30.5/33.6，
    再经 (1-exp(-T/τ)) 修正放大成 R1 的 -9% 系统误差）。
    """
    grid = np.asarray(np.arange(5.0, 120.0, 0.5) if tau_grid is None else tau_grid)
    if grid.ndim != 1 or not len(grid) or not np.all(np.isfinite(grid)) or np.any(grid <= 0):
        raise ValueError("tau_grid 必须是一维有限正数序列")
    best = (np.inf, 0.0, 0.0, 0.0)
    for tau in grid:
        basis = np.column_stack([np.ones_like(t_rel), np.exp(-t_rel / tau)])
        coef, *_ = np.linalg.lstsq(basis, u_rel, rcond=None)
        rss = float(np.sum((u_rel - basis @ coef) ** 2))
        if rss < best[0]:
            best = (rss, tau, float(coef[1]), float(coef[0]))
    _, tau, amp, offset = best
    return tau, amp, offset


def identify_one(soc0: float, r0: float, r1: float, c1: float,
                 noise: bool = True, seed: int = SEED):
    """单 SOC 点完整辨识，返回 (r0_est, r1_est, c1_est, tau_est)。"""
    t, u, i, n_pre, n_pulse = simulate_pulse(soc0, r0, r1, c1, noise, seed)

    # 第 1 步：R0 = 跳变电压 / 跳变电流。取脉冲前 1s 均值当基线、
    # 脉冲后前 3 个采样（0.3s）均值当跳变后值——噪声下比单点稳。
    u_base = float(np.mean(u[n_pre - 10:n_pre]))
    u_jump = float(np.mean(u[n_pre:n_pre + 3]))
    i_jump = float(np.mean(i[n_pre:n_pre + 3]))
    r0_est = (u_base - u_jump) / abs(i_jump)

    # 第 2、3 步：静置段指数回弹 → τ、幅值 → R1、C1。
    t_rel = t[n_pre + n_pulse:] - t[n_pre + n_pulse]
    u_rel = u[n_pre + n_pulse:]
    tau, amp, _offset = fit_relaxation(t_rel, u_rel)
    # amp = U_rc(T_pulse) = I·R1·(1 - exp(-T_pulse/τ))，放电 I<0 故 amp<0。
    charge_factor = 1.0 - np.exp(-T_PULSE / tau)
    r1_est = abs(amp) / (abs(I_PULSE) * charge_factor)
    c1_est = tau / r1_est
    return r0_est, r1_est, c1_est, tau


def main() -> int:
    print(f"HPPC 合成辨识：{len(SOC_POINTS)} 个 SOC 点，脉冲 {I_PULSE}A×{T_PULSE}s，"
          f"静置 {T_REST}s，噪声 σ={V_NOISE * 1e3:.0f}mV/{I_NOISE * 1e3:.0f}mA")
    header = (f"{'SOC':>5} | {'R0 真/估 (mΩ)':>17} | {'R1 真/估 (mΩ)':>17} | "
              f"{'C1 真/估 (F)':>17} | {'误差 R0/R1/C1':>18}")
    print(header)
    print("-" * len(header))

    worst = {"R0": 0.0, "R1": 0.0, "C1": 0.0}
    fails = []
    for k, soc in enumerate(SOC_POINTS):
        r0e, r1e, c1e, _tau = identify_one(
            float(soc), TRUE_R0[k], TRUE_R1[k], TRUE_C1[k], seed=SEED + k)
        err = {"R0": abs(r0e - TRUE_R0[k]) / TRUE_R0[k],
               "R1": abs(r1e - TRUE_R1[k]) / TRUE_R1[k],
               "C1": abs(c1e - TRUE_C1[k]) / TRUE_C1[k]}
        for key in worst:
            worst[key] = max(worst[key], err[key])
        print(f"{soc:>5.1f} | {TRUE_R0[k] * 1e3:>7.1f}/{r0e * 1e3:<7.1f} | "
              f"{TRUE_R1[k] * 1e3:>7.1f}/{r1e * 1e3:<7.1f} | "
              f"{TRUE_C1[k]:>8.0f}/{c1e:<8.0f} | "
              f"{err['R0']:>5.1%}/{err['R1']:>5.1%}/{err['C1']:>5.1%}")
        if err["R0"] > TOL_R0 or err["R1"] > TOL_R1 or err["C1"] > TOL_C1:
            fails.append(float(soc))

    print(f"\n最差相对误差：R0 {worst['R0']:.1%}（容差 {TOL_R0:.0%}）、"
          f"R1 {worst['R1']:.1%}（容差 {TOL_R1:.0%}）、"
          f"C1 {worst['C1']:.1%}（容差 {TOL_C1:.0%}）")
    if fails:
        print(f"FAIL：SOC 点 {fails} 超差")
        return 1
    print("PASS：全部 SOC 点在容差内——方法闭环成立；换真实数据时流程相同，"
          "只是数据源从 TheveninCell 换成你的采集文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
