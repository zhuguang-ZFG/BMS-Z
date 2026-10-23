#!/usr/bin/env python3
"""热的一阶账本：集总热模型的最小可复现实验（对应第 30 章）。

模型（合成教学参数，与 BMS-Z 的 thermal_demo.py 同族，便于对照）：

    C_th·dT/dt = P_ohm + P_rev - (T - T_amb)/R_th
    P_ohm = I²·R_heat      欧姆火：认平方，不认方向
    P_rev = T·(dU/dT)·I    熵热：充电 I>0、负熵斜率 → 吸热

参数：R_th=1.0 K/W、C_th=120 J/K（τ=120 s）、R_heat=49 mΩ、
dU/dT=-0.4 mV/K、T_amb=25 °C。口径与全书一致：**充电为正**。
全部为合成教学值，不是任何真实电芯的热参数。
"""
from __future__ import annotations

import math

T_AMB = 25.0            # 环境温度 (°C)
R_TH = 1.0              # 集总热阻 (K/W)
C_TH = 120.0            # 集总热容 (J/K)
TAU = R_TH * C_TH       # 热时间常数 (s) = 120 s
R_HEAT = 49e-3          # 发热电阻 (Ω)，R0+R1 教学家族
DSUDT = -0.4e-3         # 熵斜率 dU/dT (V/K)，中 SOC 段为负
DT = 1.0                # 仿真步长 (s)
I_AMP = 8.0             # 正弦工况电流幅值 (A)
PERIOD = 600.0          # 正弦电流周期 (s)；生热纹波在 2ω


def p_ohm(i_a: float) -> float:
    """欧姆火 (W)：恒为正，与电流方向无关。"""
    return i_a * i_a * R_HEAT


def p_rev(t_c: float, i_a: float) -> float:
    """可逆熵热 (W)：Π·I = T·(dU/dT)·I。充电 I>0 配负斜率 → 吸热。"""
    return (t_c + 273.15) * DSUDT * i_a


def net_power(t_c: float, i_a: float, use_rev: bool = True) -> float:
    """净生热 (W)。use_rev=False 只留欧姆火（E4 量相位用）。"""
    return p_ohm(i_a) + (p_rev(t_c, i_a) if use_rev else 0.0)


def steady_c(i_a: float) -> float:
    """恒流稳态 (°C) 解析解：(T-T_amb)/R = I²R + T·S·I 解出 T。"""
    s_i = DSUDT * i_a
    num = (T_AMB + 273.15) / R_TH + i_a * i_a * R_HEAT
    return num / (1.0 / R_TH - s_i) - 273.15


def simulate(i_of_t, t_end_s: float, use_rev: bool = True, t0_c: float | None = None):
    """前向欧拉积分，返回 [(t, T_°C), ...]，末点 t == t_end_s。"""
    if not math.isfinite(t_end_s) or t_end_s < 0:
        raise ValueError(f"t_end_s 必须是非负有限数，收到 {t_end_s!r}")
    t_c = T_AMB if t0_c is None else t0_c
    out = [(0.0, t_c)]
    for k in range(int(math.ceil(t_end_s / DT))):
        h = min(DT, t_end_s - k * DT)
        p = net_power(t_c, i_of_t(k * DT), use_rev)
        t_c += h * (p - (t_c - T_AMB) / R_TH) / C_TH
        out.append((min((k + 1) * DT, t_end_s), t_c))
    return out


def sine_response() -> tuple[float, float, float]:
    """E4：正弦电流（关熵项）→ (温度均值, 温幅, 相对生热的相位滞后°)。"""
    cycles = 8
    traj = simulate(lambda t: I_AMP * math.sin(2 * math.pi * t / PERIOD),
                    PERIOD * cycles, use_rev=False)
    tail = [p for p in traj if p[0] >= PERIOD * (cycles - 2)]
    temps = [t_c for _, t_c in tail]
    mean = (max(temps) + min(temps)) / 2
    amp = (max(temps) - min(temps)) / 2
    heat = [(t, p_ohm(I_AMP * math.sin(2 * math.pi * t / PERIOD))) for t, _ in tail]
    half = PERIOD / 2  # 生热纹波周期是电流周期的一半（I²=sin² 展开）
    lag = (max(tail, key=lambda p: p[1])[0] - max(heat, key=lambda p: p[1])[0]) % half
    if lag > half / 2:
        lag -= half
    return mean, amp, math.degrees(2 * math.pi * lag / half)


def analytic_sine() -> tuple[float, float, float]:
    """E4 解析稳态：P = P0 + Pa·sin(2ωt) → (均值温度, 温幅, 滞后°)。"""
    p_half = p_ohm(I_AMP) / 2
    omega = 4.0 * math.pi / PERIOD  # 纹波角频率 = 2ω
    gain = R_TH / math.sqrt(1.0 + (omega * TAU) ** 2)
    return T_AMB + p_half * R_TH, p_half * gain, math.degrees(math.atan(omega * TAU))


def main() -> int:
    i = 10.0  # 幅值
    print("== 热的一阶账本（集总模型，合成教学值）==")
    print(f"τ_th = R_th·C_th = {TAU:.0f} s；R_heat = {R_HEAT*1e3:.0f} mΩ；"
          f"dU/dT = {DSUDT*1e3:.1f} mV/K；T_amb = {T_AMB:.1f} °C")

    # E1 稳态：纯欧姆账 vs 全模型（放电）
    ss_ohm = T_AMB + p_ohm(-i) * R_TH
    ss_dis = steady_c(-i)
    print(f"\n[E1 稳态] 放 {i:.0f} A：纯欧姆账 {ss_ohm:.3f} °C，"
          f"全模型 {ss_dis:.3f} °C（熵项 +{ss_dis - ss_ohm:.3f} K）")

    # E2 时间常数：升温侧与降温侧各量一次
    up = simulate(lambda _: -i, TAU)
    frac_up = (up[-1][1] - T_AMB) / (ss_dis - T_AMB)
    hot = simulate(lambda _: -i, 2400.0)[-1][1]
    down = simulate(lambda _: 0.0, TAU, t0_c=hot)
    frac_dn = (hot - down[-1][1]) / (hot - T_AMB)
    print(f"[E2 时间常数] 一个 τ={TAU:.0f} s：升温走 {100*frac_up:.1f}%，"
          f"断电降温掉 {100*frac_dn:.1f}%（理论 1-1/e = 63.2%）；"
          f"40 min 末 {hot:.3f} °C vs 解析 {ss_dis:.3f} °C")

    # E3 充放不对称：±10 A 同幅值
    ss_chg = steady_c(+i)
    print(f"[E3 不对称] 同幅值 {i:.0f} A：充电稳态 {ss_chg:.3f} °C，"
          f"放电 {ss_dis:.3f} °C（差 {ss_dis - ss_chg:+.3f} K——熵项翻了个方向）")

    # E4 正弦生热的低通（关熵项）
    mean, amp, lag = sine_response()
    a_mean, a_amp, a_lag = analytic_sine()
    w2tau = 4.0 * math.pi * TAU / PERIOD
    print(f"[E4 低通] 正弦周期 {PERIOD:.0f} s，生热纹波 2ωτ≈{w2tau:.1f}："
          f"温幅仿 {amp:.4f} K vs 析 {a_amp:.4f} K；滞后 仿 {lag:.1f}° vs 析 {a_lag:.1f}°；"
          f"均值 仿 {mean:.3f} vs 析 {a_mean:.3f} °C")

    checks = [
        ("稳态对账", abs(hot - ss_dis) < 0.05),
        ("欧姆账缺熵项", abs((ss_dis - ss_ohm) - 1.217) < 0.01),
        ("τ 指数（升）", abs(frac_up - (1 - math.exp(-1))) < 0.02),
        ("τ 指数（降）", abs(frac_dn - (1 - math.exp(-1))) < 0.02),
        ("充放不对称", abs((ss_dis - ss_chg) - 2.424) < 0.01),
        ("正弦温幅", abs(amp - a_amp) / a_amp < 0.02),
        ("正弦相位", abs(lag - a_lag) < 3.0),
        ("正弦均值", abs(mean - a_mean) < 0.01),
    ]
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
