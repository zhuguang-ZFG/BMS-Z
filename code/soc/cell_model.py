"""Thevenin 等效电路电池模型 + 合成数据生成。

对应教程：阶段 4 §4.4（等效电路模型）、电路详解 ② §8。
符号约定与教程一致：**充电 I > 0，放电 I < 0**。
模型：U = OCV(SOC) + I*R0 + U_rc
      dU_rc/dt = -U_rc/(R1*C1) + I/C1   （离散形式见 TheveninCell.step）
"""
from __future__ import annotations

import numpy as np

# ---- OCV-SOC 曲线（NCM 风格，单调递增） ------------------------------------
# 形状参考教程 ocv-soc-curve.svg：低 SOC 快速爬升 → 中段近似线性 → 高 SOC 再抬头。
# 真实产品用分温度点的查表插值；这里用解析函数只是为了仿真方便。

def ocv(soc) -> np.ndarray:
    """开路电压 (V)。soc ∈ [0, 1]，支持标量或数组。"""
    soc = np.clip(np.asarray(soc, dtype=float), 0.0, 1.0)
    return (
        3.2
        + 0.8 * soc
        + 0.20 * np.tanh((soc - 0.05) * 30.0)
        + 0.05 * np.tanh((soc - 0.90) * 15.0)
    )


def docv_dsoc(soc) -> np.ndarray:
    """OCV 对 SOC 的导数 (V)。EKF 的观测矩阵 C 需要它。"""
    soc = np.clip(np.asarray(soc, dtype=float), 0.0, 1.0)
    return (
        0.8
        + 0.20 * 30.0 * (1.0 - np.tanh((soc - 0.05) * 30.0) ** 2)
        + 0.05 * 15.0 * (1.0 - np.tanh((soc - 0.90) * 15.0) ** 2)
    )


class TheveninCell:
    """一阶 RC（Thevenin）电芯模型——仿真里的"真值"来源。"""

    def __init__(self, q_ah: float, r0: float, r1: float, c1: float,
                 soc0: float = 0.8):
        self.q_ah = q_ah          # 满充容量 (Ah)
        self.r0 = r0              # 欧姆内阻 (Ω)：电流一加立刻出现的压降
        self.r1 = r1              # 极化电阻 (Ω)
        self.c1 = c1              # 极化电容 (F)
        self.soc = soc0           # SOC ∈ [0, 1]
        self.u_rc = 0.0           # RC 环节电压 (V)，放电时为负

    def step(self, current_a: float, dt_s: float) -> float:
        """推进 dt 秒，返回端电压 (V)。I>0 充电。"""
        a = np.exp(-dt_s / (self.r1 * self.c1))
        # 离散递推：U_rc' = a*U_rc + R1*(1-a)*I
        self.u_rc = a * self.u_rc + self.r1 * (1.0 - a) * current_a
        # 安时积分：dt(s) → h。q_ah<=0 直接除零——容量为 0 是标定事故，不静默。
        self.soc += current_a * (dt_s / 3600.0) / self.q_ah
        self.soc = float(np.clip(self.soc, 0.0, 1.0))
        return self.terminal_voltage(current_a)

    def terminal_voltage(self, current_a: float) -> float:
        return ocv(self.soc) + current_a * self.r0 + self.u_rc


def drive_cycle(n_steps: int, dt_s: float, seed: int = 42) -> np.ndarray:
    """生成一个工况电流序列 (A)：上电静置 → 放电+脉冲 → 静置 → CC-CV 充满。

    针对 10Ah 电芯设计（需 n_steps ≥ 17000）：
      段 0（0–1800s）：上电静置 30 分钟——教程 §4.2"上电 OCV 交叉验证"的
        窗口。初始 SOC 误差在这里被第一个锚点就地消化，而不是拖着它
        跑完整段放电（共享错误段会淹没锚点价值的度量）；
      段 1（1800–8300s）：0.2C 基础放电（-2A）+ 随机脉冲负载；
      段 2（8300–10100s）：静置 30 分钟——极化回弹窗口，OCV 校准用；
      段 3（10100–14850s）：CC 恒流充电 +4A；
      段 4（14850s–）：CV 段电流指数衰减——序列末尾天然带"满充校准点"。
    能量账：放 ≈ -3.9Ah，充 ≈ +5.9Ah，从 SOC 0.8 出发不触底、**末端触顶**。
    触顶是刻意的：满充锚点的语义是"CV 截止时电芯必然真满"——若末尾没
    充满，锚点在真值 <1 处提前复位到 1.0 反而注入误差（本仓库曾经的
    教训：CC 只到 12800s 时锚点在真值 0.975 处触发）。
    """
    rng = np.random.default_rng(seed)
    t = np.arange(n_steps) * dt_s
    current = np.zeros(n_steps)

    # 段 0：上电静置（保持 0）

    # 段 1：放电 + 脉冲
    discharge = (t >= 1800.0) & (t < 8300.0)
    current[discharge] = -2.0
    pulse_mask = discharge & (rng.random(n_steps) < 0.05)
    current[pulse_mask] = -2.0 - rng.uniform(1.0, 4.0, pulse_mask.sum())

    # 段 2：静置（保持 0）

    # 段 3：CC 恒流充电
    cc = (t >= 10100.0) & (t < 14850.0)
    current[cc] = 4.0

    # 段 4：CV 段——电流指数衰减模拟恒压收尾
    cv = t >= 14850.0
    t_c = t[cv] - 14850.0
    current[cv] = 4.0 * np.exp(-t_c / 600.0) + 0.01

    return current
