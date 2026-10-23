#!/usr/bin/env python3
"""增量容量（dQ/dV）：两座峰上的老化指纹（对应第 15 章）。

曲线（合成教学值，出自 BMS-Z stage-4 §4.6 的示意高斯，单位 Ah/V）：

    fresh(V) = 1.20·exp(-(V-3.40)²/(2·0.04²)) + 0.70·exp(-(V-3.68)²/(2·0.05²))
    aged(V)  = 0.65 × fresh(V - 0.03)     老化：峰高 ×0.65，两座峰各右移 0.03 V

峰顶斜率为 0。温度或倍率一变，峰会搬迁——对齐工况再比高矮。
"""
from __future__ import annotations

import math

A1, MU1, S1 = 1.20, 3.40, 0.04   # 第一座峰：位置 V、高度 Ah/V、宽度 V
A2, MU2, S2 = 0.70, 3.68, 0.05   # 第二座峰
AGE_H = 0.65                      # 老化：峰高倍率
AGE_DV = 0.03                     # 老化：右移量 (V)
R_SERIES = 0.020                  # 串联内阻 (Ω)，soh-aging 教学家族 20 mΩ
I_RATE = 1.0                      # 巧用工况：+1 A 充电
V_LO, V_HI, DV = 3.20, 3.90, 0.002
NAMEPLATE = 2.00                  # 名牌容量 (Ah)
DAH = 0.02                        # 示意安时误差 (Ah)
Q_WIN, DSOC_WIN = 0.72, 0.40      # 局部充电窗口的账（stage-4 §4.6）


def ic_fresh(v: float) -> float:
    """新鲜电芯的 dQ/dV (Ah/V)：两座示意高斯。"""
    return (A1 * math.exp(-((v - MU1) ** 2) / (2 * S1 ** 2))
            + A2 * math.exp(-((v - MU2) ** 2) / (2 * S2 ** 2)))


def ic_aged(v: float) -> float:
    """老化电芯的 dQ/dV (Ah/V)：高度 ×0.65，右移 0.03 V。"""
    return AGE_H * ic_fresh(v - AGE_DV)


def make_grid() -> list[float]:
    """电压网格：3.20–3.90 V，步长 2 mV。"""
    n = int(round((V_HI - V_LO) / DV))
    return [V_LO + i * DV for i in range(n + 1)]


def find_peaks(vs: list[float], fs: list[float]) -> list[tuple[float, float, int]]:
    """局部极大 (v, 高度, 下标)，按高度降序。"""
    out = []
    for i in range(1, len(vs) - 1):
        if fs[i] > fs[i - 1] and fs[i] >= fs[i + 1]:
            out.append((vs[i], fs[i], i))
    return sorted(out, key=lambda p: -p[1])


def peak_slope(fs: list[float], i: int) -> float:
    """峰顶中心差分斜率 (Ah/V²)。"""
    return (fs[i + 1] - fs[i - 1]) / (2 * DV)


def main() -> int:
    vs = make_grid()
    fs = [ic_fresh(v) for v in vs]
    ag = [ic_aged(v) for v in vs]
    ir = [ic_fresh(v - I_RATE * R_SERIES) for v in vs]

    pf = find_peaks(vs, fs)
    pa = find_peaks(vs, ag)
    pi = find_peaks(vs, ir)

    print("== 增量容量的两座峰（合成教学值，stage-4 §4.6 示意高斯）==")
    print(f"新鲜：{MU1:.2f} V / {A1:.2f} + {MU2:.2f} V / {A2:.2f}（Ah/V）；"
          f"老化：高度 ×{AGE_H}，两峰各右移 {AGE_DV * 1e3:.0f} mV")

    print(f"\n[E1 两座峰] 新鲜：({pf[0][0]:.3f} V, {pf[0][1]:.3f})、"
          f"({pf[1][0]:.3f} V, {pf[1][1]:.3f})；峰顶斜率 "
          f"{abs(peak_slope(fs, pf[0][2])):.1e}——峰在斜率为 0 的地方")

    print(f"[E2 老化指纹] 老化：({pa[0][0]:.3f} V, {pa[0][1]:.3f})、"
          f"({pa[1][0]:.3f} V, {pa[1][1]:.3f})；高度比 "
          f"{pa[0][1] / pf[0][1]:.3f} / {pa[1][1] / pf[1][1]:.3f}，右移 "
          f"{(pa[0][0] - pf[0][0]) * 1e3:.0f} / {(pa[1][0] - pf[1][0]) * 1e3:.0f} mV")

    shift_ir = pi[0][0] - pf[0][0]
    print(f"[E3 工况污染] +1 A 充电、20 mΩ 内阻：第一峰被推到 {pi[0][0]:.3f} V"
          f"（+{shift_ir * 1e3:.0f} mV），是老化搬家 {AGE_DV * 1e3:.0f} mV 的 "
          f"{shift_ir / AGE_DV:.0%}——没扣 IR 就比峰位，会把工况当老化")

    sig5 = DAH / 0.05
    sig10 = DAH / 0.10
    sig40 = DAH / 0.40
    q_win = Q_WIN / DSOC_WIN
    print(f"[E4 窗口容量] σ_Q = 0.02/ΔSOC：5% 窗 → {sig5:.2f} Ah、10% → "
          f"{sig10:.2f}、40% → {sig40:.2f}；充 {Q_WIN:.2f} Ah 走 "
          f"{DSOC_WIN:.0%} 窗口 → Q = {q_win:.2f} Ah，"
          f"SOH = {q_win / NAMEPLATE:.0%}（示意）；5% 窗的噪声和容量同一量级，"
          f"不能当 SOH 发布")

    checks = [
        ("峰位 3.40 / 3.68 V",
         abs(pf[0][0] - MU1) < 0.001 and abs(pf[1][0] - MU2) < 0.001),
        ("峰高 1.20 / 0.70",
         abs(pf[0][1] - A1) < 0.001 and abs(pf[1][1] - A2) < 0.001),
        ("峰顶斜率为 0", abs(peak_slope(fs, pf[0][2])) < 1e-3),
        ("老化峰高 ×0.65",
         abs(pa[0][1] / pf[0][1] - AGE_H) < 0.002
         and abs(pa[1][1] / pf[1][1] - AGE_H) < 0.002),
        ("老化右移 +0.03 V",
         abs(pa[0][0] - pf[0][0] - AGE_DV) < 0.001
         and abs(pa[1][0] - pf[1][0] - AGE_DV) < 0.001),
        ("欧姆位移 20 mV", abs(shift_ir - I_RATE * R_SERIES) < 0.001),
        ("窗口 σ 0.40/0.20/0.05",
         abs(sig5 - 0.40) < 1e-9 and abs(sig10 - 0.20) < 1e-9
         and abs(sig40 - 0.05) < 1e-9),
        ("窗口容量 1.80 Ah / SOH 90%",
         abs(q_win - 1.80) < 1e-9 and abs(q_win / NAMEPLATE - 0.90) < 1e-9),
    ]
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
