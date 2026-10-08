"""三种 SOC 估算器：纯安时积分 / 积分 + 校准点 / Thevenin + EKF。

对应教程：阶段 4 §4.2 / §4.3 / §4.5。
符号约定：充电 I > 0。SOC 用 [0, 1] 表示。

三个估算器接收同样的"有缺陷的"输入（电流有零漂、电压有噪声、
容量估错 5%），方便直观对比它们的抗差能力——这正是阶段 4 的主线：
积分为主干、电压做校正，分歧只在"怎么校正"。
"""
from __future__ import annotations

import numpy as np

from cell_model import ocv, docv_dsoc


class CoulombOnly:
    """方案一：纯安时积分。一行核心代码 `soc += I*dt/Q`。

    教程 §4.2 的演示对象：零漂会被一分一秒积进去，误差不收敛。
    """

    def __init__(self, soc0: float, q_assumed_ah: float):
        self.soc = soc0
        self.q = q_assumed_ah

    def step(self, current_a: float, _v_meas: float, dt_s: float) -> float:
        # q<=0 时这里除零：容量估计错成 0 是标定事故，宁可炸出来也别静默给出
        # inf 的 SOC 再被 clip 成 0/1。
        self.soc += current_a * (dt_s / 3600.0) / self.q
        self.soc = float(np.clip(self.soc, 0.0, 1.0))
        return self.soc


class CoulombWithResets:
    """方案二：安时积分 + 两个校准锚点（教程 §4.2 的工程做法）。

    - 满充校准：CV 段电流衰减到截止值 → 必然满电 → SOC 复位 1.0；
    - 静置 OCV 校准：电流近似为零持续一段时间 → 端电压可信 → 查 OCV 表复位。
    """

    def __init__(self, soc0: float, q_assumed_ah: float,
                 cv_cutoff_a: float = 0.5, v_full: float = 4.15,
                 rest_current_a: float = 0.05, rest_time_s: float = 900.0):
        self.soc = soc0
        self.q = q_assumed_ah
        self.cv_cutoff_a = cv_cutoff_a
        self.v_full = v_full
        self.rest_current_a = rest_current_a
        self.rest_time_s = rest_time_s
        self._rest_accum = 0.0

    def step(self, current_a: float, v_meas: float, dt_s: float) -> float:
        self.soc += current_a * (dt_s / 3600.0) / self.q

        # 满充校准：电压已在高位 + 电流衰减到截止值以下（CV 段尾声）
        if v_meas > self.v_full and 0.0 < current_a < self.cv_cutoff_a:
            self.soc = 1.0
            self._rest_accum = 0.0      # 充电打断静置，撤流后须重新等待 OCV 校准

        # 静置 OCV 校准：电流近似为零持续足够久 → 极化消散、电压可信。
        # 计时是双向去抖而不是"一拍超限就清零"：电流传感器有噪声时，
        # 连续 rest_time_s 秒全部合格的概率是 (1-p)^N ≈ 0——清零式计时
        # 会让这个锚点统计上永远触发不了（与固件去抖同一思想，教程 §3.4）。
        elif abs(current_a) < self.rest_current_a:
            self._rest_accum = min(self._rest_accum + dt_s, self.rest_time_s)
            if self._rest_accum >= self.rest_time_s:
                self.soc = self._ocv_to_soc(v_meas)
        else:
            self._rest_accum = max(0.0, self._rest_accum - 4.0 * dt_s)

        self.soc = float(np.clip(self.soc, 0.0, 1.0))
        return self.soc

    @staticmethod
    def _ocv_to_soc(v: float) -> float:
        """OCV 反查 SOC：单调函数二分查找（真实产品用查表插值）。"""
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2.0
            if ocv(mid) < v:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2.0


class EKFEstimator:
    """方案三：Thevenin 模型 + 扩展卡尔曼滤波（教程 §4.5）。

    状态 x = [SOC, U_rc]^T，输入 I，观测 U。
    预测步：x⁻ = f(x, I)，P⁻ = A·P·Aᵀ + Q
    更新步：K = P⁻Cᵀ(CP⁻Cᵀ+R)⁻¹，x = x⁻ + K(U_meas - g(x⁻))，P = (I-KC)P⁻

    调参直觉（教程原文）：
      Q 大 = 不信任模型 → 跟测量跑，响应快但抖；
      R 大 = 不信任测量 → 平滑但滞后。
    """

    def __init__(self, soc0: float, q_assumed_ah: float,
                 r0: float, r1: float, c1: float,
                 q_soc: float = 2e-6, q_urc: float = 1e-7,
                 r_volt: float = 2.5e-5, *, ocv_func=ocv, docv_func=docv_dsoc):
        # 合成演示保持原曲线；真实数据实验可注入自己的准静态 OCV 表及其导数。
        self.ocv_func, self.docv_func = ocv_func, docv_func
        self.x = np.array([soc0, 0.0])          # [SOC, U_rc]
        self.q_ah = q_assumed_ah
        self.r0, self.r1, self.c1 = r0, r1, c1
        self.P = np.diag([1e-2, 1e-4])
        self.Q = np.diag([q_soc, q_urc])        # 过程噪声协方差
        self.R = r_volt                          # 观测噪声方差（5mV → 2.5e-5 V²）
        # 无真值诊断量：最近一步的新息（电压残差）与其归一化平方 NIS。
        # 场上没有真值时只能听滤波器自己"喊"：新息 RMS 对参数失配敏感；
        # NIS≈1 才说明 R 与实际噪声匹配，NIS<1 表示 R 偏保守。
        self.last_innovation_v = float("nan")
        self.last_nis = float("nan")

    def step(self, current_a: float, v_meas: float, dt_s: float, *,
             voltage_current_a: float | None = None) -> float:
        a = np.exp(-dt_s / (self.r1 * self.c1))
        A = np.array([[1.0, 0.0], [0.0, a]])
        B = np.array([dt_s / 3600.0 / self.q_ah, self.r1 * (1.0 - a)])

        # 预测
        self.x = A @ self.x + B * current_a
        self.x[0] = float(np.clip(self.x[0], 0.0, 1.0))
        self.P = A @ self.P @ A.T + self.Q

        # 更新（观测方程非线性：OCV 是曲线 → EKF 在工作点线性化）
        C = np.array([self.docv_func(self.x[0]), 1.0])
        # 积分用区间平均电流；变采样实测可另传电压采样时刻的瞬时电流。
        observed_current = current_a if voltage_current_a is None else voltage_current_a
        v_pred = self.ocv_func(self.x[0]) + self.r0 * observed_current + self.x[1]
        residual = v_meas - v_pred                 # 教程说的"残差"
        S = C @ self.P @ C.T + self.R
        # 记录在更新之前：这是"这一步观测推翻了多少假设"的原话。
        self.last_innovation_v = float(residual)
        self.last_nis = float(residual * residual / S)
        K = self.P @ C.T / S
        self.x = self.x + K * residual
        self.x[0] = float(np.clip(self.x[0], 0.0, 1.0))
        self.P = (np.eye(2) - np.outer(K, C)) @ self.P
        return float(self.x[0])
