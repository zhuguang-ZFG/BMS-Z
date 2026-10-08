"""SOP 双法对照合成演示：HPPC 闭式除法 vs 二分 + ESC 前向仿真。

对应教程：阶段 4 §4.7（SOP 多约束取最小）、ECE5720 Notes06 中文导读 §三/§四。
口径与全仓一致：**充电 I > 0，放电 I < 0**。本演示只算放电侧——充电侧是同型
习题（把 U_min 换 U_max、方向反号，见阶段 4 §4.7b 充电地图）。

两种方法回答同一个问题：「未来 ΔT 秒内最多允许放多大电流？」

1. HPPC 闭式（简单法）：v = OCV(z) − i·R_dis 一条代数式除出来（Notes06 §三）。
   本演示带上此刻已知的 U_RC（阶段 4 §4.7 的公式形状），但它**看不见未来**：
   既不知道 ΔT 秒里极化会继续积累，也不知道 SOC 会掉到墙下。
2. 二分 + ESC（认真法）：每猜一个电流，把一阶 RC 模型向前仿真 ΔT 秒，
   检查整窗端电压 ≥ U_min 且窗末 SOC ≥ SOC_MIN（Notes06 §四）。贵，但用的
   和 SOC 估计是同一套模型。

教学点（跑完自己对账）：
- 多约束取最小：高 SOC 电压余量充足，系统电流帽先咬——闭式解 30+ A 根本
  到不了；
- 时间窗越长越紧：极化在窗内继续积累，2s > 10s > 30s 单调下降；
- HPPC 偏乐观：只看 R0 不算极化累积，电压约束区内高估约 3%–36%（本仓
  实测值；Notes06 算例为 9.8%，量级同阶）；
- HPPC 漏 SOC 墙：贴墙工作点它照报十几安，按它放电就过放——这正是
  Notes06 §五「有的工况会过放」的可跑版。

这里不接真电池。R0/R1/C1/Q/U_min/SOC_MIN/I_MAX 都是示例值。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from cell_model import TheveninCell, ocv

# ---- 实验配置（与 hppc_demo.py 同一颗"教学电芯"家族：3 Ah、中 SOC 工作点）----
Q_AH = 3.0             # 电芯容量 (Ah)
R0 = 33e-3             # 欧姆内阻 (Ω)，hppc_demo SOC=0.5 点
R1 = 16e-3             # 极化电阻 (Ω)
C1 = 2200.0            # 极化电容 (F)，τ = R1·C1 ≈ 35 s
V_MIN = 3.0            # 放电电压下限 (V)，NCM 惯例
SOC_MIN = 0.10         # SOC 墙：窗末不许跌破（二分法独有约束）
I_MAX = 15.0           # 系统/电芯最大允许放电电流 (A)，示例值（5 C 峰值）
DT = 0.1               # 前向仿真步长 (s)
WINDOWS_S = (2.0, 10.0, 30.0)   # SOP 时间档（阶段 4 §4.7 的三档）
SOC_POINTS = (0.90, 0.70, 0.50, 0.30, 0.15, 0.12)
BISECT_TOL_A = 0.02    # 二分收敛公差 (A)
BISECT_MAX_ITER = 60   # log2(15/0.02) ≈ 10，余量充足


def fresh_cell(soc: float) -> TheveninCell:
    """静置后的电芯（U_RC = 0）——SOP 问的是"此刻"，从此刻状态出发。"""
    cell = TheveninCell(Q_AH, R0, R1, C1, soc0=soc)
    cell.u_rc = 0.0
    return cell


def hppc_current(soc: float) -> float:
    """HPPC 闭式放电电流 (A)。带此刻 U_RC（=0），只看电压这一条约束。"""
    return (float(ocv(soc)) + 0.0 - V_MIN) / R0


def simulate_window(soc: float, i_dis: float, dt_s: float):
    """以恒定放电电流 i_dis 前向仿真 dt_s 秒，返回 (整窗最低端电压, 窗末 SOC)。"""
    cell = fresh_cell(soc)
    n = int(round(dt_s / DT))
    v_min = np.inf
    for _ in range(n):
        u = cell.step(-i_dis, DT)
        v_min = min(v_min, u)
    return float(v_min), cell.soc


def _feasible(soc: float, i_dis: float, dt_s: float) -> bool:
    v_min, soc_end = simulate_window(soc, i_dis, dt_s)
    return v_min >= V_MIN and soc_end >= SOC_MIN


def bisect_current(soc: float, dt_s: float):
    """二分求最大可行放电电流 (A) 与咬住的约束名。

    电流越大电压越低、SOC 掉越多——两个约束都随电流单调变紧，二分适用。
    """
    lo, hi = 0.0, I_MAX
    if _feasible(soc, hi, dt_s):
        return I_MAX, "电流帽"
    for _ in range(BISECT_MAX_ITER):
        mid = 0.5 * (lo + hi)
        if _feasible(soc, mid, dt_s):
            lo = mid
        else:
            hi = mid
        if hi - lo < BISECT_TOL_A:
            break
    _, soc_end = simulate_window(soc, lo, dt_s)
    binding = "SOC墙" if soc_end <= SOC_MIN + 1e-3 else "电压"
    return lo, binding


def main() -> int:
    print(f"SOP 双法对照：{Q_AH:g} Ah 电芯，R0={R0*1e3:g} mΩ，R1={R1*1e3:g} mΩ，"
          f"τ={R1*C1:.0f} s；U_min={V_MIN:g} V，SOC 墙={SOC_MIN:.2f}，"
          f"电流帽={I_MAX:g} A")
    print(f"{'SOC':>5} | {'HPPC 闭式':>9} | " + " | ".join(
        f"二分 {int(t):>2}s" for t in WINDOWS_S))
    print("-" * 72)

    rows = {}
    for soc in SOC_POINTS:
        hppc = hppc_current(soc)
        cells = []
        for t in WINDOWS_S:
            i, binding = bisect_current(soc, t)
            rows[(soc, t)] = (hppc, i, binding)
            mark = {"电流帽": "帽", "电压": "压", "SOC墙": "墙"}[binding]
            cells.append(f"{i:6.2f}{mark}")
        print(f"{soc:5.2f} | {hppc:7.1f} A | " + " | ".join(
            c.ljust(9) for c in cells))

    # ---- 自验收：把教学点当断言，跑通即证明（与 pc_demo.py 同款对账）--------
    checks = {
        "hppc_not_below_bisect": all(h >= i - BISECT_TOL_A
                                     for h, i, _ in rows.values()),
        "window_longer_tighter": all(
            rows[(s, 2.0)][1] >= rows[(s, 10.0)][1] - 1e-9
            and rows[(s, 10.0)][1] >= rows[(s, 30.0)][1] - 1e-9
            for s in SOC_POINTS),
        "hppc_optimistic_where_voltage_binds": (
            rows[(0.15, 10.0)][0] > rows[(0.15, 10.0)][1]),
        "soc_wall_binds_at_low_soc_long_window": (
            rows[(0.12, 30.0)][2] == "SOC墙"),
        "current_cap_binds_at_high_soc": (
            rows[(0.90, 10.0)][2] == "电流帽"),
        "bisect_solutions_feasible": all(
            _feasible(s, i, t) for (s, t), (_, i, _) in rows.items()),
    }
    print()
    h15, b15, _ = rows[(0.15, 10.0)]
    h12, b12, _ = rows[(0.12, 30.0)]
    print(f"对账：电压约束区 HPPC 偏乐观 "
          f"{(h15 / b15 - 1) * 100:.1f}%（0.15 SOC、10 s 窗）；"
          f"SOC 墙处 HPPC 报 {h12:.1f} A、二分只给 {b12:.1f} A——"
          f"漏墙 {(h12 / b12 - 1) * 100:.0f}%，按它放电会过放。")
    for name, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    if not all(checks.values()):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
