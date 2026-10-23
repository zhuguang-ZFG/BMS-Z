#!/usr/bin/env python3
"""CC-CV：恒流恒压充电的最小可复现实验（对应第 11 章）。

模型（合成教学参数，不是任何真实电芯的规格）：

    V = OCV(s) + I·R0 + v_pol
    OCV(s) = 3.50 + 0.70·s             s ≤ 0.80（中段）
           = 4.06 + 0.887·(s - 0.80)    s > 0.80（顶部抬升：真实电芯顶部更陡）
    dv_pol/dt = (I·R1 - v_pol) / τ

参数：Q = 2 Ah、R0 = 50 mΩ、R1 = 20 mΩ、τ = 30 s。
CC 段 I = 1C = 2 A；CV 段 V 钳 4.20 V；截止 I < 0.05C = 0.1 A。
对照 BMS-Z 详解③ §1 的示意账：恒流约 1.6 Ah、恒压约 0.3 Ah。
口径与全书一致：**充电为正**。
"""
from __future__ import annotations

Q_AH = 2.0                  # 额定容量 (Ah)
I_CC = 2.0                  # 恒流段电流 (A)，1C
V_CV = 4.20                 # 恒压段钳位电压 (V)
I_CUT = 0.05 * Q_AH         # 截止电流 (A)，0.05C
R0 = 0.050                  # 欧姆内阻 (Ω)
R1 = 0.020                  # 极化内阻 (Ω)
TAU = 30.0                  # 极化时间常数 (s)
S_KINK = 0.80               # OCV 折点：转恒压时刻的 SOC
K_MID = 0.70                # 中段斜率 (V / SOC)
K_TOP = 0.887               # 顶部斜率 (V / SOC)
DT = 1.0                    # 仿真步长 (s)


def ocv(s: float) -> float:
    """教学 OCV (V)：中段 0.70 V/SOC，s>0.80 抬到 0.887 V/SOC。"""
    if s <= S_KINK:
        return 3.50 + K_MID * s
    return 3.50 + K_MID * S_KINK + K_TOP * (s - S_KINK)


def ichg_map(t_c: float, soc: float) -> float:
    """充电地图查表 (A)。示意值，出自 BMS-Z stage-4 §4.7/§4.7b（2 Ah 电芯）。

    行 = 温度窗口，列 = SOC 三档；取格不插值；≥55 °C 停充。
    """
    if t_c < 0.0 or t_c >= 55.0:
        return 0.0
    if t_c < 10.0:
        tiers = (0.2, 0.2, 0.1)
    elif t_c <= 45.0:
        tiers = (1.0, 0.5, 0.2)
    else:
        tiers = (0.5, 0.2, 0.0)
    if soc < 0.70:
        rate = tiers[0]
    elif soc < 0.90:
        rate = tiers[1]
    else:
        rate = tiers[2]
    return rate * Q_AH


def simulate_cccv(t_max_s: float = 7200.0) -> dict:
    """前向欧拉跑一次 CC-CV，返回切换/截止事件与安时账。"""
    s = 0.0
    v_pol = 0.0
    ah = 0.0
    t = 0.0
    # --- CC 段：恒流，直到端电压碰 4.20 V ---
    while t < t_max_s:
        if ocv(s) + I_CC * R0 + v_pol >= V_CV:
            break
        s += I_CC * DT / (Q_AH * 3600.0)
        v_pol += (I_CC * R1 - v_pol) / TAU * DT
        ah += I_CC * DT / 3600.0
        t += DT
    t_sw, s_sw, ah_cc = t, s, ah
    # --- CV 段：钳 4.20 V，电流自衰减，直到 < 0.05C ---
    i = I_CC
    while t < t_max_s:
        i = max(0.0, (V_CV - ocv(s) - v_pol) / R0)
        if i <= I_CUT:
            break
        s += i * DT / (Q_AH * 3600.0)
        v_pol += (i * R1 - v_pol) / TAU * DT
        ah += i * DT / 3600.0
        t += DT
    return {
        "t_sw_s": t_sw, "s_sw": s_sw, "ah_cc": ah_cc,
        "t_cut_s": t, "s_cut": s, "ah_cv": ah - ah_cc, "i_cut": i,
    }


def main() -> int:
    r = simulate_cccv()
    t_sw_min = r["t_sw_s"] / 60.0
    t_cv_min = (r["t_cut_s"] - r["t_sw_s"]) / 60.0
    frac_cv_time = t_cv_min / (r["t_cut_s"] / 60.0)
    frac_cv_ah = r["ah_cv"] / (r["ah_cc"] + r["ah_cv"])
    print("== CC-CV：恒流恒压充电（合成教学值）==")
    print(f"Q = {Q_AH:.0f} Ah；CC 段 {I_CC:.0f} A（1C）；CV 段 {V_CV:.2f} V；"
          f"截止 {I_CUT:.2f} A（0.05C）")

    print(f"\n[E1 恒流段] {t_sw_min:.0f} min 时端电压碰 {V_CV:.2f} V："
          f"SOC 才到 {r['s_sw']:.2f}，灌入 {r['ah_cc']:.2f} Ah——"
          f"电压到 4.20 V 远不等于充满")

    print(f"[E2 恒压段] 再花 {t_cv_min:.0f} min，电流从 {I_CC:.0f} A 衰到 "
          f"{r['i_cut']:.2f} A，只多收 {r['ah_cv']:.2f} Ah——"
          f"占总充入的 {100 * frac_cv_ah:.0f}%，却占总时间的 "
          f"{100 * frac_cv_time:.0f}%——最后一安时最贵")

    s_wrong = r["s_sw"]
    print(f"[E3 判据] 若把「电压到 4.20 V」当满充：SOC 锚在 {s_wrong:.2f}，"
          f"少记 {r['ah_cv']:.2f} Ah（{100 * (r['s_cut'] - s_wrong):.0f} 个百分点）；"
          f"正确判据是 CV 段电流 < 0.05C（stage-4 §4.8），触发时真值 "
          f"{r['s_cut']:.2f}，BMS 才把 SOC 校准到 100%")

    wall = (V_CV - ocv(0.95)) / (R0 + R1)
    allowed = min(ichg_map(25.0, 0.95), wall)
    print(f"[E4 充电地图] 查表示意（2 Ah，stage-4 §4.7b）："
          f"-5 °C → {ichg_map(-5.0, 0.30):.1f} A；5 °C → {ichg_map(5.0, 0.30):.1f} A；"
          f"25 °C/50% → {ichg_map(25.0, 0.50):.1f} A；50 °C/50% → "
          f"{ichg_map(50.0, 0.50):.1f} A；60 °C → {ichg_map(60.0, 0.30):.1f} A")
    print(f"          25 °C、SOC 0.95：地图给 {ichg_map(25.0, 0.95):.1f} A，"
          f"电压墙给 {wall:.2f} A——四个约束取最小，这一拍 {allowed:.2f} A，"
          f"被电压墙咬住")

    checks = [
        ("转恒压 SOC = 0.80", abs(r["s_sw"] - 0.80) < 0.005),
        ("恒流段 1.6 Ah（详解③ 示意账）", abs(r["ah_cc"] - 1.60) < 0.02),
        ("恒压段 0.3 Ah（详解③ 示意账）", abs(r["ah_cv"] - 0.30) < 0.02),
        ("截止电流 0.05C", abs(r["i_cut"] - 0.10) < 0.005),
        ("恒压段时间占比 ~37%", abs(frac_cv_time - 0.37) < 0.03),
        ("电压判据少记 0.30 Ah", abs((r["s_cut"] - s_wrong) * Q_AH - 0.30) < 0.02),
        ("地图：冰点以下 0", ichg_map(-5.0, 0.30) == 0.0),
        ("地图：0–10 °C 是 0.2C", abs(ichg_map(5.0, 0.30) - 0.40) < 1e-9),
        ("地图：常温满档 1C", abs(ichg_map(25.0, 0.50) - 2.00) < 1e-9),
        ("地图：高温降档 0.5C", abs(ichg_map(50.0, 0.50) - 1.00) < 1e-9),
        ("地图：55 °C 停充", ichg_map(60.0, 0.30) == 0.0),
        ("满充附近被电压墙咬住", abs(allowed - 0.10) < 0.01),
    ]
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
