"""热五天合成演示：集总热模型——稳态、时间常数、可逆热、正弦生热的低通。

对应教程：ECE5710 Notes07 中文导读（四项生热、7–4 正弦生热、ROM 低阶）、
阶段 4 §4.4（同一颗"教学电芯"的 R 家族）、阶段 6 §6.1.6（BMS 只报温度与
允许功率，冷却回路自己闭环——本演示就是"温度从哪儿来"的那一半）。

模型（集总，一格温度，Notes07 ROM 思路的教学化简）：

    C_th · dT/dt = P_ohm + P_rev − (T − T_amb) / R_th
    P_ohm = I² · R_heat          （欧姆 + 极化的电耗全变热）
    P_rev = T · (dU/dT) · I      （可逆熵热，Π = T·∂U/∂T，Notes07 7–8）

口径与全仓一致：**充电 I > 0，放电 I < 0**。熵斜率取中 SOC 段的负值——
于是同幅值电流，充电比放电凉（P_rev 吸热），"有电流就一定净发热"不成立。

教学点（跑完自己对账）：
- 稳态只由热阻决定：T_ss = T_amb + P·R_th，和容量、时间都没关系；
- 升温降温同一个 τ_th = R_th·C_th：一阶线性系统，指数到达 63.2%；
- 可逆热符号随电流翻：放电时它是第四把火，充电时它偷偷往外抽热；
- 正弦生热 → 温度是它的低通：幅值缩 1/√(1+(ωτ)²)，相位落后 arctan(ωτ)。
  D4 把熵项关掉（它已在 D3 单独量过方向），让生热是纯正弦，幅值与相位
  才量得干净。生热脉动比 τ_th 快，温度就"摸不到"它——这正是脉冲工况里
  温度探测不到的那段时间（共学第 6 页第 4 天）。

这里不接真电池。R_th/C_th/熵斜率全为合成教学示例；真实电芯的热参数
要按规格书与实测，别把这里的数写进任何产品文档。
"""
from __future__ import annotations

import math

# ---- 教学配置（合成示例；电学侧沿用 sop_demo 的教学电芯家族）----
T_AMB_C = 25.0          # 环境温度 (°C)
R_TH = 1.0              # 集总热阻 (K/W)，自然对流小软包示例
C_TH = 120.0            # 集总热容 (J/K)
TAU_TH = R_TH * C_TH    # 热时间常数 (s) = 120 s
R_HEAT = 49e-3          # 发热电阻 (Ω) = R0 + R1（33+16 mΩ，sop_demo 同族）
DSUDT = -0.4e-3         # 熵斜率 dU/dT (V/K)，中 SOC 段为负，合成示例
DT = 1.0                # 仿真步长 (s)
I_SINE_AMP = 8.0        # 正弦工况电流幅值 (A)
PERIOD_S = 600.0        # 正弦电流周期 (s)；生热纹波在 2ω，2ω·τ_th ≈ 2.5


def kelvin(t_c: float) -> float:
    return t_c + 273.15


def p_ohm(i_a: float) -> float:
    """欧姆 + 极化生热 (W)。恒为正：电流多大火多大，与方向无关。"""
    return i_a * i_a * R_HEAT


def p_rev(t_c: float, i_a: float) -> float:
    """可逆熵热 (W)：Π·I = T·(dU/dT)·I。充电 I>0 配负斜率 → 吸热。"""
    return kelvin(t_c) * DSUDT * i_a


def net_power_w(t_c: float, i_a: float, use_rev: bool = True) -> float:
    """净生热 (W) = 欧姆火 + 可逆项。教学化简：四项里析锂/副反应热在这里是 0。

    use_rev=False 只留欧姆火——D4 用它把生热做成纯正弦（2ω），相位才对得干净。
    """
    p = p_ohm(i_a)
    return p + p_rev(t_c, i_a) if use_rev else p


def steady_temp_c(i_a: float) -> float:
    """恒流稳态温度 (°C) 的解析解：(T−T_amb)/R_th = I²R + T·S·I 解出 T。"""
    s_i = DSUDT * i_a
    t_k_amb = kelvin(T_AMB_C)
    return (t_k_amb / R_TH + i_a * i_a * R_HEAT) / (1.0 / R_TH - s_i) - 273.15


def simulate(i_profile, t_end_s: float, use_rev: bool = True,
             t0_c: float | None = None):
    """前向欧拉积分 dT/dt = (P_net − (T−T_amb)/R_th)/C_th。

    i_profile 是 t→I 的函数；use_rev=False 关可逆项（D4）；t0_c 自定义初温。
    返回 [(t, T_C), ...]（含 t=0）。
    """
    t_c = T_AMB_C if t0_c is None else t0_c
    out = [(0.0, t_c)]
    n = int(round(t_end_s / DT))
    for k in range(n):
        i_a = i_profile(k * DT)
        p = net_power_w(t_c, i_a, use_rev)
        t_c += DT * (p - (t_c - T_AMB_C) / R_TH) / C_TH
        out.append(((k + 1) * DT, t_c))
    return out


def i_const(i_a: float):
    return lambda t: i_a


def i_sine(t: float) -> float:
    """均值为零的正弦工况电流。I² 展开后生热 = 直流 P_peak/2 + 2ω 纹波。"""
    return I_SINE_AMP * math.sin(2.0 * math.pi * t / PERIOD_S)


def sine_response():
    """D4：熵项关掉的纯正弦生热响应。

    跑足多个周期后取最后一个完整周期，返回 (温度均值, 幅值, 相对生热的相位滞后°)。
    相位用生热与温度的峰值时刻差量。
    """
    cycles = 8
    traj = simulate(i_sine, PERIOD_S * cycles, use_rev=False)
    tail = [p for p in traj if p[0] >= PERIOD_S * (cycles - 2)]
    heat = [(t, p_ohm(i_sine(t))) for t, _ in tail]
    temps = [t_c for _, t_c in tail]
    tmean = (max(temps) + min(temps)) / 2.0
    amp = (max(temps) - min(temps)) / 2.0
    t_pk_p = max(heat, key=lambda p: p[1])[0]
    t_pk_t = max(tail, key=lambda p: p[1])[0]
    half = PERIOD_S / 2.0  # 生热纹波周期是电流周期的一半（I²=sin² 展开）
    lag_s = (t_pk_t - t_pk_p) % half
    if lag_s > half / 2.0:
        lag_s -= half
    return tmean, amp, math.degrees(2.0 * math.pi * lag_s / half)


def analytic_sine():
    """P = P0 + Pa·sin(2ωt) 对一阶热系统的解析稳态：(均值温度, 幅值, 滞后°)。

    生热纹波频率是电流的两倍（I²=sin² 展开）：ω' = 4π/PERIOD。
    """
    p_peak = p_ohm(I_SINE_AMP)
    p0, pa = p_peak / 2.0, p_peak / 2.0
    omega = 4.0 * math.pi / PERIOD_S
    gain = R_TH / math.sqrt(1.0 + (omega * TAU_TH) ** 2)
    lag = math.degrees(math.atan(omega * TAU_TH))
    return T_AMB_C + p0 * R_TH, pa * gain, lag


def main() -> int:
    print("== 热五天演示（集总热模型，全部合成示例）==")
    print(f"τ_th = R_th·C_th = {TAU_TH:.0f} s，环境 {T_AMB_C:.1f} °C，"
          f"R_heat = {R_HEAT * 1e3:.0f} mΩ，dU/dT = {DSUDT * 1e3:.1f} mV/K")

    # D1 稳态：10 A 恒流
    i_d1 = 10.0
    ss = steady_temp_c(-i_d1)
    end1 = simulate(i_const(-i_d1), 2400.0)[-1][1]
    print(f"\n[D1 稳态] 放 10 A：解析 T_ss = {ss:.3f} °C，跑 40 min 到 {end1:.3f} °C"
          f"（P_ohm = {p_ohm(i_d1):.2f} W）")

    # D2 时间常数：τ 处到 63.2%
    traj = simulate(i_const(-i_d1), TAU_TH)
    frac = (traj[-1][1] - T_AMB_C) / (ss - T_AMB_C)
    print(f"[D2 时间常数] 一个 τ={TAU_TH:.0f} s 走到总温升的 {100 * frac:.1f}%"
          f"（理论 1−1/e = 63.2%）")

    # D3 可逆热的不对称：±10 A 同幅值
    t_charge = steady_temp_c(+i_d1)
    t_dis = steady_temp_c(-i_d1)
    print(f"[D3 可逆热] 同幅值 10 A：充到稳态 {t_charge:.3f} °C，放 {t_dis:.3f} °C"
          f"（差 {t_dis - t_charge:+.3f} K——熵项翻了个方向）")

    # D4 正弦生热的低通（熵项关）：2ω·τ ≈ 2.5
    tmean, amp, lag = sine_response()
    a_mean, a_amp, a_lag = analytic_sine()
    omega2_tau = 4.0 * math.pi * TAU_TH / PERIOD_S
    print(f"[D4 正弦] 电流周期 {PERIOD_S:.0f} s，生热纹波 2ωτ≈{omega2_tau:.1f}："
          f"仿真温幅 {amp:.4f} K vs 解析 {a_amp:.4f} K；"
          f"滞后 仿 {lag:.1f}° vs 析 {a_lag:.1f}°；均值 仿 {tmean:.3f} vs 析 {a_mean:.3f} °C")

    checks = [
        abs(end1 - ss) < 0.05,
        abs(frac - (1.0 - math.exp(-1.0))) < 0.02,
        t_dis > t_charge,                      # 放电更热：熵项方向
        p_rev(T_AMB_C, +i_d1) < 0 < p_rev(T_AMB_C, -i_d1),
        abs(amp - a_amp) / a_amp < 0.02,
        abs(lag - a_lag) < 3.0,
    ]
    for name, ok in zip(("稳态对账", "τ 指数", "充放不对称", "可逆热符号",
                         "正弦幅值", "正弦相位"), checks, strict=True):
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
