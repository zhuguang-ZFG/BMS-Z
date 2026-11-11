"""Teaching experiments for D18: CC/CV charge control and charge permission.

D18「充电控制与许可」的可执行证据模块。三件事：

1. **许可链**：充电电流 = min(充电器能力, 温度充电地图, SOP 窗口约束, 绝对电流帽)。
   SOP 窗口约束按与 D17 共享的语义合同实现：电压余量（OCV + 两条 RC 的窗末端电压
   不越 V_max）、SOC 余量（D12 口径）、热契约（D16 的稳态芯限电流）、绝对上限；
   窗口分级 10/30/60/600 s 与「持续」档，每档报告谁在限、其余余量、窗末端电压 ×
   允许电流的功率边界。
2. **控制环**：CC 段执行许可电流；端电压到墙转 CV——电压环不是另一套方程，它就是
   1 s 窗的电压余量（控制周期即承诺窗）；CV 段电流衰减到 0.05C 以下并连续保持
   30 s 才判截止。截止证据三元同时记账：taper 电流、时间上限、温度/析锂边界。
3. **反例对与账**：0 °C 同一快充工况，无温度地图（1.3C 直接灌进析锂禁区）vs 有地图
   （0.2C 被压住、停在 0.80 等加热）；能量账（Ah/Wh 积分、OCV-SOC 一致性、静置
   反查与表计偏置）；老化联动（D15 的 AF 温度换算作为内容结论，数值自算）。

教学身份：电芯参数（Q、OCV 折线、R0/R1/R2、V_max）、充电地图形状、热契约
（R_th/C_th/R_heat/芯限）、截止阈值、时间上限与表计偏置全部是教学值，与第 11 章
CC-CV 算例同源；**不认定为任何电芯手册、器件实测、HIL 或真人评审结论**。真实
许可必须回电芯手册（SRC04）并登记数据身份（B05）后重算。

边界（必须与正文同页）：固件 `BmsInputs` 只有 cell_mv/current_ma/temp_c10/
charger_present，`Bms` 输出只有 charge_mos_on，`BmsConfig` 只有 full_mv 与
full_cutoff_ma 的满充判据；没有温度分档充电地图、没有预测窗 SOP、没有析锂边界
状态、也没有充电电流请求/许可字段。本单元的许可链是教学补全，不证明固件已实现。

场景：``D18-cccv-charge``（默认 CC/CV 与反例对）与 ``D18-charge-replay``
（回放审计：把一条记录轨迹逐拍对照许可链）。
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import cast

SCENARIO_ID = "D18-cccv-charge"
REPLAY_SCENARIO_ID = "D18-charge-replay"

# --- 教学电芯（与第 11 章 CC-CV 算例同源：2 Ah、1C、4.20 V、0.05C 截止）---
Q_AH = 2.0
OCV_BASE_V = 3.50
OCV_SLOPE_LOW_V_PER_SOC = 0.70   # 中段斜率（教学值）
OCV_KNEE_Z = 0.80
OCV_KNEE_V = 4.06                # 3.50 + 0.70 × 0.80
OCV_SLOPE_TOP_V_PER_SOC = 0.887  # 顶部抬升（教学值）
V_MAX_V = 4.20
R0_OHM = 0.050
R1_OHM = 0.020
C1_F = 1500.0                    # τ1 = 30 s
TAU1_S = 30.0
R2_OHM = 0.005
C2_F = 200.0                     # τ2 = 1 s
TAU2_S = 1.0
DT_S = 1.0
Z0 = 0.05
Z_FENCE = 0.98                   # SOP 的 SOC 余量上端（协议保留，不是 z = 1.0 的满填充）

# --- 热契约（D16 接口：芯限、等效发热电阻、两节点退化为单节点用于持续电流）---
C_TH_J_PER_K = 156.0             # C_core + C_case
R_TH_K_PER_W = 5.5               # R_cs + R_sa
R_HEAT_OHM = 0.09                # 等效发热电阻（含极耳/连接损耗，与电压模型 R0+R1+R2=0.075 不同）
T_LIMIT_C = 70.0
AMBIENT_C = 25.0

# --- 许可与协议（教学值）---
CHARGER_A = 3.0                  # 充电器能力
ABS_CHARGE_A = 2.6               # 电芯绝对充电电流上限（1.3C）
AUX_LOAD_A = 0.4                 # 附件/车载负载电流（教学值；默认场景为 0）
CABLE_OHM = 0.25                 # 充电器到电芯的线缆电阻（教学值；仅假满充反例使用）
FULL_SOC_MIN = 0.94              # 满充锚点的 SOC 交叉核对下限（taper 之外的独立证据）
MAP_COLD_MAX_C = 10.0
MAP_FULL_MAX_C = 45.0
MAP_HOT_MAX_C = 55.0
MAP_COLD_RATE = 0.2
MAP_FULL_RATE = 1.0
MAP_HOT_RATE = 0.5
PLATING_T_C = 10.0               # 低温 + 高 SOC 的析锂禁区
PLATING_Z = 0.80
TAPER_A = 0.05 * Q_AH            # 0.10 A
TAPER_CONFIRM_S = 30.0
TIME_LIMIT_S = 9000.0            # 2.5 h 协议上限（默认场景在 4530 s 就 taper 截止）
CONTROL_WINDOW_S = 1.0           # 控制周期即承诺窗：1 s 窗的电压余量就是 CV 电压环
WINDOW_TIERS_S = (10.0, 30.0, 60.0, 600.0)
METER_BIAS_A = 0.02              # 电流表计偏置（教学值）
REST_AFTER_S = 600.0             # 截止后静置：OCV 反查的条件（D12 静置门）

# --- 老化联动（D15 内容结论：高温快充加速老化；数值自算）---
EA_KJ_PER_MOL = 30.0
GAS_CONSTANT_J_PER_MOL_K = 8.314462618
T_REF_C = 25.0

# --- 回放数据合同 ---
REPLAY_COLUMNS = ["t_s", "current_a", "v_meas", "temp_c"]
REPLAY_MAX_GAP_S = 60.0
REPLAY_MIN_SAMPLES = 20
REPLAY_TOL_A = 1e-3
REPLAY_TEMP_MIN_C = -40.0
REPLAY_TEMP_MAX_C = 85.0
REPLAY_V_MIN_V = 2.50
REPLAY_V_MAX_V = 4.50


def _num(value: object) -> float:
    """从 report 字典里取回数值（pyright 友好，同时是运行时契约检查）。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"期望数值，得到 {type(value).__name__}")
    return float(value)


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(f"期望字符串，得到 {type(value).__name__}")
    return value


def ocv_v(z: float) -> float:
    """教学 OCV 折线：中段 0.70 V/SOC，0.80 以上 0.887 V/SOC。"""
    if not math.isfinite(z) or not 0.0 <= z <= 1.0:
        raise ValueError(f"SOC 必须在 [0, 1] 内，实际 {z}")
    if z <= OCV_KNEE_Z:
        return OCV_BASE_V + OCV_SLOPE_LOW_V_PER_SOC * z
    return OCV_KNEE_V + OCV_SLOPE_TOP_V_PER_SOC * (z - OCV_KNEE_Z)


def soc_from_ocv_v(voltage_v: float) -> float:
    """OCV 反查 SOC。只用于静置电压；越出教学 OCV 表范围一律拒绝，不外推。"""
    if not math.isfinite(voltage_v):
        raise ValueError("电压非有限，不能反查 SOC")
    if voltage_v < OCV_BASE_V or voltage_v > OCV_KNEE_V + OCV_SLOPE_TOP_V_PER_SOC * 0.2:
        raise ValueError(f"电压 {voltage_v:.4f} V 越出教学 OCV 表范围，不反查")
    if voltage_v <= OCV_KNEE_V:
        return (voltage_v - OCV_BASE_V) / OCV_SLOPE_LOW_V_PER_SOC
    return OCV_KNEE_Z + (voltage_v - OCV_KNEE_V) / OCV_SLOPE_TOP_V_PER_SOC


def ocv_energy_wh(z0: float, z1: float) -> float:
    """∫ OCV dQ = Q·∫ OCV dz（Wh）。解析式，与逐帧积分互为独立核对。"""
    if not 0.0 <= z0 <= z1 <= 1.0:
        raise ValueError(f"SOC 区间非法：{z0} → {z1}")
    if z1 <= OCV_KNEE_Z:
        return Q_AH * (
            OCV_BASE_V * (z1 - z0)
            + 0.5 * OCV_SLOPE_LOW_V_PER_SOC * (z1 * z1 - z0 * z0)
        )
    if z0 >= OCV_KNEE_Z:
        d = z1 - OCV_KNEE_Z
        return Q_AH * (OCV_KNEE_V * (z1 - z0) + 0.5 * OCV_SLOPE_TOP_V_PER_SOC * d * d)
    low = OCV_BASE_V * (OCV_KNEE_Z - z0) + 0.5 * OCV_SLOPE_LOW_V_PER_SOC * (
        OCV_KNEE_Z * OCV_KNEE_Z - z0 * z0
    )
    d = z1 - OCV_KNEE_Z
    high = OCV_KNEE_V * d + 0.5 * OCV_SLOPE_TOP_V_PER_SOC * d * d
    return Q_AH * (low + high)


def heat_w(current_a: float) -> float:
    """等效发热：P = I²·R_heat（全进单热节点；忽略熵热与均流）。"""
    return current_a * current_a * R_HEAT_OHM


def charge_map_a(temp_c: float) -> float:
    """温度充电地图（教学值，LFP 形：冰点以下停、低温降额、常温满额、高温收回）。

    取格不插值；禁充边界不能被插值跨越成正电流（第 11 章 §11.4 的坑）。
    """
    if not math.isfinite(temp_c):
        raise ValueError("温度非有限，不能查充电地图")
    if temp_c < 0.0:
        return 0.0
    if temp_c < MAP_COLD_MAX_C:
        return MAP_COLD_RATE * Q_AH
    if temp_c < MAP_FULL_MAX_C:
        return MAP_FULL_RATE * Q_AH
    if temp_c < MAP_HOT_MAX_C:
        return MAP_HOT_RATE * Q_AH
    return 0.0


def plating_forbidden(temp_c: float, z: float) -> bool:
    """析锂禁区：低温（< 10 °C）且高 SOC（≥ 0.80）时不允许正充电电流。

    这是独立于温度地图的**否决项**：地图形状是分档近似，禁区不能被插值绕过。
    """
    return temp_c < PLATING_T_C and z >= PLATING_Z


def thermal_window_current_a(temp_c: float, window_s: float) -> float:
    """热契约：窗内芯温不越限的最大恒流。window_s = inf 即 D16 的持续电流。

    T(t) = T_amb + (T0−T_amb)e^{−t/τ} + I²·R_heat·R_th(1−e^{−t/τ})，
    解出 I。分子非正时返回 0（已到限或环境超限，禁止开方后当许可）。
    """
    if not (window_s > 0.0):
        raise ValueError(f"窗口必须为正，实际 {window_s}")
    if not math.isfinite(temp_c):
        raise ValueError("温度非有限，不能算热契约")
    headroom_k = T_LIMIT_C - temp_c
    if headroom_k <= 0.0:
        return 0.0
    factor = 1.0 if math.isinf(window_s) else 1.0 - math.exp(-window_s / (R_TH_K_PER_W * C_TH_J_PER_K))
    if factor <= 0.0:
        raise ValueError("窗口过短，热契约无法定义")
    return math.sqrt(headroom_k / (R_HEAT_OHM * R_TH_K_PER_W * factor))


def predicted_terminal_v(
    z: float,
    vp1: float,
    vp2: float,
    current_a: float,
    window_s: float,
    aux_a: float = 0.0,
    cable_ohm: float = 0.0,
) -> float:
    """窗末端电压：OCV 随窗内安时推进，两条 RC 按 ZOH 精确推进。

    ``cable_ohm > 0`` 时返回充电器侧端电压（电芯端电压 + (i + aux)·R_cable），
    因为闭环调压点在充电器出口；``aux_a`` 是附件/车载负载的分流。
    """
    if math.isinf(window_s):
        return (
            ocv_v(z)
            + current_a * (R0_OHM + R1_OHM + R2_OHM)
            + (current_a + aux_a) * cable_ohm
        )
    a1 = math.exp(-window_s / TAU1_S)
    a2 = math.exp(-window_s / TAU2_S)
    z_end = min(1.0, z + current_a * window_s / (3600.0 * Q_AH))
    return (
        ocv_v(z_end)
        + current_a * R0_OHM
        + vp1 * a1
        + R1_OHM * (1.0 - a1) * current_a
        + vp2 * a2
        + R2_OHM * (1.0 - a2) * current_a
        + (current_a + aux_a) * cable_ohm
    )


def voltage_charge_limit_a(
    z: float,
    vp1: float,
    vp2: float,
    window_s: float,
    absolute_a: float = ABS_CHARGE_A,
    aux_a: float = 0.0,
    cable_ohm: float = 0.0,
) -> float:
    """电压余量：窗末端电压不越 V_max 的最大净电流（单调，二分）。

    充电方向 OCV 随 SOC 单调上升，窗末是窗内最坏点（本模型无温度反馈项）。
    ``aux_a``/``cable_ohm`` 把约束落在充电器出口：线缆压降随总电流变化。
    """
    if predicted_terminal_v(z, vp1, vp2, 0.0, window_s, aux_a, cable_ohm) >= V_MAX_V:
        return 0.0
    lo, hi = 0.0, 4.0 * absolute_a
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        if predicted_terminal_v(z, vp1, vp2, mid, window_s, aux_a, cable_ohm) <= V_MAX_V:
            lo = mid
        else:
            hi = mid
    return lo


def sop_charge_limit(
    z: float,
    vp1: float,
    vp2: float,
    temp_c: float,
    window_s: float,
    absolute_a: float = ABS_CHARGE_A,
    aux_a: float = 0.0,
    cable_ohm: float = 0.0,
) -> dict[str, object]:
    """共享语义合同的简化 SOP（充电方向）：四约束取最弱环。

    有限窗：电压余量 ∩ SOC 余量 ∩ 热窗 ∩ 绝对上限。
    ``window_s = inf``（持续档）：只留热契约 ∩ 绝对上限——∞ 窗的 SOC 余量按定义
    恒为 0、窗末端电压无意义，硬套会得到一个假的「许可为零」。
    """
    components: dict[str, float] = {}
    if math.isinf(window_s):
        # 持续档：∞ 窗的 SOC 余量恒为 0、窗末端电压无意义，二者不套；
        # 但「持续」不等于「瞬时电压墙不存在」——电压余量按最短的 1 s 窗算。
        components["voltage"] = voltage_charge_limit_a(
            z, vp1, vp2, DT_S, absolute_a, aux_a, cable_ohm
        )
        components["thermal"] = thermal_window_current_a(temp_c, window_s)
        components["absolute"] = absolute_a
    else:
        components["voltage"] = voltage_charge_limit_a(
            z, vp1, vp2, window_s, absolute_a, aux_a, cable_ohm
        )
        components["soc"] = max(0.0, Z_FENCE - z) * 3600.0 * Q_AH / window_s
        components["thermal"] = thermal_window_current_a(temp_c, window_s)
        components["absolute"] = absolute_a
    binding = _first_binding(components, ("voltage", "soc", "thermal", "absolute"))
    limit = components[binding]
    out: dict[str, object] = {
        "window_s": window_s,
        "limit_a": limit,
        "binding": binding,
        "power_w": predicted_terminal_v(z, vp1, vp2, limit, window_s, aux_a, cable_ohm)
        * limit,
    }
    for key in ("voltage", "soc", "thermal", "absolute"):
        out[f"{key}_a"] = components.get(key)
    return out


def _first_binding(components: dict[str, float], order: tuple[str, ...]) -> str:
    """按声明顺序取最弱环（浮点 min 的平局也按顺序，保证确定性）。"""
    limit = min(components.values())
    for key in order:
        if key in components and components[key] == limit:
            return key
    raise ValueError("约束表为空")


def charge_permission(
    z: float,
    vp1: float,
    vp2: float,
    temp_c: float,
    window_s: float = CONTROL_WINDOW_S,
    charger_a: float | None = CHARGER_A,
    temperature_permission: bool = True,
    absolute_a: float = ABS_CHARGE_A,
    aux_a: float = 0.0,
    cable_ohm: float = 0.0,
) -> dict[str, object]:
    """一整拍许可：充电器 / 地图 / 析锂否决 / SOP 四分量，逐项给余量。

    ``i_net = i_cmd − i_aux``：限制的是电芯实际吃到的净电流，充电器能力要先
    扣掉附件分流（``charger − aux``）；电压约束落在充电器出口（含线缆压降）。
    ``charger_a = None`` 表示充电器能力未知（回放审计只审地图、析锂与 SOP），
    该项不参与 min，也不出现在余量表里。
    """
    sop = sop_charge_limit(z, vp1, vp2, temp_c, window_s, absolute_a, aux_a, cable_ohm)
    components: dict[str, float] = {
        "sop_voltage": _num(sop["voltage_a"]),
        "sop_soc": _num(sop["soc_a"]),
        "sop_thermal": _num(sop["thermal_a"]),
        "absolute": _num(sop["absolute_a"]),
    }
    if charger_a is not None:
        components["charger"] = max(0.0, charger_a - aux_a)
    if temperature_permission:
        components["map"] = charge_map_a(temp_c)
        if plating_forbidden(temp_c, z):
            components["plating"] = 0.0
    binding = _first_binding(
        components,
        ("charger", "map", "plating", "sop_voltage", "sop_soc", "sop_thermal", "absolute"),
    )
    limit = components[binding]
    return {
        "z": z,
        "temp_c": temp_c,
        "window_s": window_s,
        "limit_a": limit,
        "net_limit_a": limit,
        "charger_current_a": limit + (0.0 if charger_a is None else aux_a),
        "binding": binding,
        "power_w": predicted_terminal_v(z, vp1, vp2, limit, window_s, aux_a, cable_ohm) * limit,
        "components": components,
        "margins_a": {key: value - limit for key, value in components.items()},
        "sop": sop,
        "temperature_permission": temperature_permission,
        "charger_audited": charger_a is not None,
        "aux_a": aux_a,
        "cable_ohm": cable_ohm,
    }


def simulate_charge(
    z0: float = Z0,
    ambient_c: float = AMBIENT_C,
    charger_a: float = CHARGER_A,
    duration_s: float = TIME_LIMIT_S,
    temperature_permission: bool = True,
    control_window_s: float = CONTROL_WINDOW_S,
    dt_s: float = DT_S,
    taper_confirm_s: float = TAPER_CONFIRM_S,
    aux_a: float = 0.0,
    cable_ohm: float = 0.0,
) -> dict[str, object]:
    """CC/CV 控制环：每拍许可 = min(充电器, 地图, 析锂否决, SOP 四分量)。

    端电压不是被「钳」住，而是被 1 s 窗的电压余量挡住——控制周期即承诺窗。
    电芯模型（SOC 积分、端电压、CV 切换、taper）一律用净电流 ``i_net = i_cmd − aux``；
    充电器侧另记 ``i_cmd`` 与 ``v_charger`` 两本账。截止 = CV 段净电流 < 0.05C
    连续 taper_confirm_s；时间上限独立记账。
    """
    if not 0.0 <= z0 <= Z_FENCE:
        raise ValueError(f"初值 SOC 必须在 [0, {Z_FENCE}] 内，实际 {z0}")
    if dt_s <= 0.0 or control_window_s <= 0.0:
        raise ValueError("步长与窗口必须为正")
    if aux_a < 0.0 or cable_ohm < 0.0:
        raise ValueError("附件电流与线缆电阻不能为负")
    z = z0
    vp1 = 0.0
    vp2 = 0.0
    temp = ambient_c
    a1 = math.exp(-dt_s / TAU1_S)
    a2 = math.exp(-dt_s / TAU2_S)
    tau_th = R_TH_K_PER_W * C_TH_J_PER_K
    frames: list[dict[str, float]] = []
    modes: list[str] = []
    bindings: list[str] = []
    counts: dict[str, int] = {}
    ah = 0.0
    ah_charger = 0.0
    wh_port = 0.0
    wh_charger = 0.0
    wh_ocv = 0.0
    wh_ohmic = 0.0
    wh_rc = 0.0
    taper_run = 0.0
    taper_start_t: float | None = None
    ended_by = "time_limit"
    n_steps = int(round(duration_s / dt_s))
    v_prev = ocv_v(z)
    ocv_prev = v_prev
    vp_prev = 0.0
    i_last = 0.0
    t_end = 0.0
    for step in range(n_steps + 1):
        t = step * dt_s
        perm = charge_permission(
            z,
            vp1,
            vp2,
            temp,
            control_window_s,
            charger_a,
            temperature_permission,
            aux_a=aux_a,
            cable_ohm=cable_ohm,
        )
        i_net = _num(perm["limit_a"])
        i_cmd = i_net + aux_a
        binding = _text(perm["binding"])
        if i_net <= 1e-12:
            mode = "hold"
        elif binding == "sop_voltage":
            mode = "cv"
        else:
            mode = "cc"
        v = ocv_v(z) + i_net * R0_OHM + vp1 + vp2
        v_chg = v + i_cmd * cable_ohm
        frames.append(
            {
                "t_s": t,
                "z": z,
                "i_a": i_net,
                "i_charger_a": i_cmd,
                "v": v,
                "v_charger": v_chg,
                "temp_c": temp,
                "vp1": vp1,
                "vp2": vp2,
                "plating": 1.0 if (plating_forbidden(temp, z) and i_net > 0.0) else 0.0,
            }
        )
        modes.append(mode)
        bindings.append(binding)
        counts[binding] = counts.get(binding, 0) + 1
        i_last = i_net
        t_end = t
        if mode == "cv" and i_net < TAPER_A:
            if taper_start_t is None:
                taper_start_t = t
            taper_run = t - taper_start_t
        else:
            taper_start_t = None
            taper_run = 0.0
        if taper_run >= taper_confirm_s - 1e-9:
            ended_by = "taper"
            break
        if step == n_steps:
            ended_by = "time_limit"
            break
        # 应用一步（ZOH 精确）：电学状态、SOC、热节点全部用电芯侧净电流
        v_prev = v
        ocv_prev = ocv_v(z)
        vp_prev = vp1 + vp2
        z_next = z + i_net * dt_s / (3600.0 * Q_AH)
        vp1_next = a1 * vp1 + R1_OHM * (1.0 - a1) * i_net
        vp2_next = a2 * vp2 + R2_OHM * (1.0 - a2) * i_net
        v_next = ocv_v(z_next) + i_net * R0_OHM + vp1_next + vp2_next
        wh_port += 0.5 * (v_prev + v_next) * i_net * dt_s / 3600.0
        # 充电器侧能量：同一梯形电压 × 总电流 + 线缆损耗 i_cmd²·R_cable
        wh_charger += 0.5 * (v_prev + v_next) * i_cmd * dt_s / 3600.0
        wh_charger += i_cmd * i_cmd * cable_ohm * dt_s / 3600.0
        wh_ocv += 0.5 * (ocv_prev + ocv_v(z_next)) * i_net * dt_s / 3600.0
        wh_ohmic += i_net * i_net * R0_OHM * dt_s / 3600.0
        wh_rc += 0.5 * (vp_prev + vp1_next + vp2_next) * i_net * dt_s / 3600.0
        ah += i_net * dt_s / 3600.0
        ah_charger += i_cmd * dt_s / 3600.0
        z = z_next
        vp1 = vp1_next
        vp2 = vp2_next
        t_ss = ambient_c + heat_w(i_net) * R_TH_K_PER_W
        temp = t_ss + (temp - t_ss) * math.exp(-dt_s / tau_th)
    v_max = max(frame["v"] for frame in frames)
    v_charger_max = max(frame["v_charger"] for frame in frames)
    temp_max = max(frame["temp_c"] for frame in frames)
    temp_min = min(frame["temp_c"] for frame in frames)
    return {
        "frames": frames,
        "modes": modes,
        "bindings": bindings,
        "binding_counts": counts,
        "z_start": z0,
        "z_end": z,
        "t_end": t_end,
        "i_end": i_last,
        "vp1_end": vp1,
        "vp2_end": vp2,
        "temp_end": temp,
        "ah": ah,
        "ah_charger": ah_charger,
        "wh_port": wh_port,
        "wh_charger": wh_charger,
        "wh_ocv": wh_ocv,
        "wh_ohmic": wh_ohmic,
        "wh_rc": wh_rc,
        "v_max": v_max,
        "v_charger_max": v_charger_max,
        "v_cutoff": frames[-1]["v"],
        "temp_max": temp_max,
        "temp_min": temp_min,
        "ended_by": ended_by,
        "duration_s": duration_s,
        "ambient_c": ambient_c,
        "charger_a": charger_a,
        "temperature_permission": temperature_permission,
        "control_window_s": control_window_s,
        "aux_a": aux_a,
        "cable_ohm": cable_ohm,
    }


def _frames_of(run: dict[str, object]) -> list[dict[str, float]]:
    return cast(list[dict[str, float]], run["frames"])


def _strs_of(run: dict[str, object], key: str) -> list[str]:
    return cast(list[str], run[key])


def rest_voltage(run: dict[str, object], rest_s: float = REST_AFTER_S) -> dict[str, float]:
    """截止后静置：两条 RC 按各自的 τ 衰减，端电压回到 OCV（D12 的静置门）。"""
    vp1 = _num(run["vp1_end"])
    vp2 = _num(run["vp2_end"])
    z = _num(run["z_end"])
    v_start = ocv_v(z) + vp1 + vp2
    vp1 *= math.exp(-rest_s / TAU1_S)
    vp2 *= math.exp(-rest_s / TAU2_S)
    v_end = ocv_v(z) + vp1 + vp2
    return {
        "rest_s": rest_s,
        "v_start_v": v_start,
        "v_end_v": v_end,
        "v_ocv_v": ocv_v(z),
        "gap_mv": (v_start - v_end) * 1000.0,
    }


def summarize_run(run: dict[str, object]) -> dict[str, object]:
    """轨迹摘要：CC/CV 分段、切换点、安时分配、峰值、谁在限。"""
    frames = _frames_of(run)
    modes = _strs_of(run, "modes")
    z_start = _num(run["z_start"])
    z_end = _num(run["z_end"])
    t_end = _num(run["t_end"])
    ah_total = (z_end - z_start) * Q_AH
    cv_at = [idx for idx, mode in enumerate(modes) if mode == "cv"]
    z_sw = frames[cv_at[0]]["z"] if cv_at else None
    t_sw = frames[cv_at[0]]["t_s"] if cv_at else None
    v_sw = frames[cv_at[0]]["v"] if cv_at else None
    ah_cc = (z_sw - z_start) * Q_AH if z_sw is not None else ah_total
    ah_cv = ah_total - ah_cc
    t_cv = t_end - _num(t_sw) if t_sw is not None else 0.0
    plating = [frame for frame in frames if frame["plating"] > 0.0]
    counts = cast(dict[str, int], run["binding_counts"])
    return {
        "t_end_s": round(t_end, 3),
        "t_cc_s": round(_num(t_sw), 3) if t_sw is not None else round(t_end, 3),
        "t_cv_s": round(t_cv, 3),
        "cc_time_pct": round((_num(t_sw) if t_sw is not None else t_end) / t_end * 100.0, 2),
        "cv_time_pct": round(t_cv / t_end * 100.0, 2),
        "z_start": round(z_start, 6),
        "z_end": round(z_end, 6),
        "z_switch": round(_num(z_sw), 6) if z_sw is not None else None,
        "t_switch_s": round(_num(t_sw), 3) if t_sw is not None else None,
        "v_switch_v": round(_num(v_sw), 6) if v_sw is not None else None,
        "ah_total": round(ah_total, 6),
        "ah_cc": round(ah_cc, 6),
        "ah_cv": round(ah_cv, 6),
        "ah_cv_pct": round(ah_cv / ah_total * 100.0, 2),
        "i_end_a": round(_num(run["i_end"]), 6),
        "v_max_v": round(_num(run["v_max"]), 6),
        "temp_max_c": round(_num(run["temp_max"]), 4),
        "temp_min_c": round(_num(run["temp_min"]), 4),
        "binding_counts": dict(sorted(counts.items())),
        "plating_frames": len(plating),
        "plating_ah": round(sum(f["i_a"] for f in frames if f["plating"] > 0.0) * DT_S / 3600.0, 6),
        "first_plating_t_s": (
            round(next(f["t_s"] for f in frames if f["plating"] > 0.0), 3) if plating else None
        ),
        "ended_by": _text(run["ended_by"]),
        "ambient_c": _num(run["ambient_c"]),
        "temperature_permission": bool(run["temperature_permission"]),
        "control_window_s": _num(run["control_window_s"]),
        "aux_a": round(_num(run["aux_a"]), 6),
        "ah_charger": round(_num(run["ah_charger"]), 6),
        "wh_charger": round(_num(run["wh_charger"]), 6),
        "wh_cell": round(_num(run["wh_port"]), 6),
        "ah_gap": round(_num(run["ah_charger"]) - ah_total, 6),
        "wh_gap": round(_num(run["wh_charger"]) - _num(run["wh_port"]), 6),
        "v_charger_max_v": round(_num(run["v_charger_max"]), 6),
    }


def cutoff_evidence(run: dict[str, object]) -> dict[str, object]:
    """截止证据三元：taper / 时间上限 / 温度与析锂边界。锚点只在三元同时成立时有效。"""
    summary = summarize_run(run)
    t_end = _num(summary["t_end_s"])
    ended_by = _text(summary["ended_by"])
    plating_frames = int(_num(summary["plating_frames"]))
    temp_max = _num(summary["temp_max_c"])
    z_end = _num(summary["z_end"])
    taper_reached = ended_by == "taper"
    time_reached = ended_by == "time_limit"
    soc_meets = z_end >= FULL_SOC_MIN
    anchor = taper_reached and plating_frames == 0 and temp_max < T_LIMIT_C and soc_meets
    if anchor:
        note = "taper 截止 + 未触时间上限 + 无温度/析锂越界 + SOC 达标：满充锚点成立"
    elif plating_frames > 0:
        note = "taper 只证明 CV 条件满足，不证明充电合规：轨迹在析锂禁区内仍有正电流"
    elif time_reached and "plating" in cast(dict[str, int], summary["binding_counts"]):
        note = "停在析锂边界 0.80 等加热；时间上限到不是满充，续充必须先升温"
    elif time_reached:
        note = "时间上限不是满充证据：未等到的 taper 不能替满充锚点"
    elif taper_reached and not soc_meets:
        note = "taper 成立但 SOC 未达标：截止证据不足以证明充满（假满充）"
    else:
        note = "三元未同时成立，不置满充锚点"
    return {
        "taper": {
            "threshold_a": TAPER_A,
            "confirm_s": TAPER_CONFIRM_S,
            "reached": taper_reached,
            "t_s": t_end if taper_reached else None,
            "i_end_a": summary["i_end_a"],
        },
        "time_limit": {
            "limit_s": _num(run["duration_s"]),
            "reached": time_reached,
            "t_s": t_end,
        },
        "temperature": {
            "core_limit_c": T_LIMIT_C,
            "max_cell_c": temp_max,
            "min_cell_c": summary["temp_min_c"],
            "plating_veto_c": PLATING_T_C,
            "plating_veto_z": PLATING_Z,
            "plating_frames": plating_frames,
            "plating_ah": summary["plating_ah"],
            "veto_fired": plating_frames > 0 or "plating" in cast(dict[str, int], summary["binding_counts"]),
        },
        "ended_by": ended_by,
        "soc": {
            "z_end": round(z_end, 6),
            "full_soc_min": FULL_SOC_MIN,
            "meets": soc_meets,
            "note": "taper + 电压截止可与低 SOC 同时成立（附件/上游限流反例）：锚点必须带 SOC 交叉核对",
        },
        "full_charge_anchor": anchor,
        "note": note,
    }


def energy_account(run: dict[str, object]) -> dict[str, object]:
    """能量账：Ah/Wh 积分、OCV 化学能（逐帧 vs 解析）、损耗分解、表计与 OCV 反查。"""
    frames = _frames_of(run)
    z_start = _num(run["z_start"])
    z_end = _num(run["z_end"])
    ah_in = (z_end - z_start) * Q_AH
    wh_port = _num(run["wh_port"])
    wh_ocv = _num(run["wh_ocv"])
    wh_ohmic = _num(run["wh_ohmic"])
    wh_rc = _num(run["wh_rc"])
    analytic = ocv_energy_wh(z_start, z_end)
    rest = rest_voltage(run)
    v_rest = rest["v_end_v"]
    z_ocv = soc_from_ocv_v(v_rest)
    z_meter = z_start + (ah_in + METER_BIAS_A * _num(run["t_end"]) / 3600.0) / Q_AH
    z_loaded = soc_from_ocv_v(_num(run["v_cutoff"]))
    return {
        "ah_in": round(ah_in, 6),
        "ah_from_soc": round((z_end - z_start) * Q_AH, 6),
        "ah_residual": round(ah_in - (z_end - z_start) * Q_AH, 9),
        "wh_port": round(wh_port, 6),
        "wh_ocv_integrated": round(wh_ocv, 6),
        "wh_ocv_analytic": round(analytic, 6),
        "wh_ocv_residual": round(wh_ocv - analytic, 9),
        "wh_ohmic_r0": round(wh_ohmic, 6),
        "wh_rc_branch": round(wh_rc, 6),
        "wh_decomposition_residual": round(wh_port - wh_ocv - wh_ohmic - wh_rc, 9),
        "loss_wh": round(wh_port - wh_ocv, 6),
        "loss_pct": round((wh_port - wh_ocv) / wh_port * 100.0, 4),
        "mean_terminal_v": round(wh_port / ah_in, 6),
        "rest": {key: round(value, 6) for key, value in rest.items()},
        "meter": {
            "bias_a": METER_BIAS_A,
            "z_meter": round(z_meter, 6),
            "z_true": round(z_end, 6),
            "z_ocv": round(z_ocv, 6),
            "deviation_pp": round((z_meter - z_ocv) * 100.0, 4),
            "loaded_inversion_pp": round((z_loaded - z_end) * 100.0, 4),
        },
        "frame_count": len(frames),
    }


def window_effect() -> dict[str, object]:
    """控制窗从 1 s 放到 60 s：许可提前降流，峰值电压与截止点怎么移。"""
    narrow = summarize_run(simulate_charge(control_window_s=CONTROL_WINDOW_S))
    wide = summarize_run(simulate_charge(control_window_s=60.0))
    return {
        "control_period_s": DT_S,
        "narrow_1s": {
            "z_switch": narrow["z_switch"],
            "t_switch_s": narrow["t_switch_s"],
            "v_switch_v": narrow["v_switch_v"],
            "v_max_v": narrow["v_max_v"],
            "t_end_s": narrow["t_end_s"],
            "z_end": narrow["z_end"],
        },
        "wide_60s": {
            "z_switch": wide["z_switch"],
            "t_switch_s": wide["t_switch_s"],
            "v_switch_v": wide["v_switch_v"],
            "v_max_v": wide["v_max_v"],
            "t_end_s": wide["t_end_s"],
            "z_end": wide["z_end"],
        },
        "delta": {
            "z_switch_pp": round((_num(wide["z_switch"]) - _num(narrow["z_switch"])) * 100.0, 4),
            "v_max_mv": round((_num(wide["v_max_v"]) - _num(narrow["v_max_v"])) * 1000.0, 4),
            "t_end_s": round(_num(wide["t_end_s"]) - _num(narrow["t_end_s"]), 3),
            "z_end_pp": round((_num(wide["z_end"]) - _num(narrow["z_end"])) * 100.0, 4),
        },
        "note": "窗越长，许可越早看见窗末的 OCV 抬升；代价是峰值电压留了余量、总时长变长",
    }


def sop_window_table() -> list[dict[str, object]]:
    """SOP 分级表：同一状态在 10/30/60/600 s 与持续档下的四约束、最弱环与功率。"""
    probes = (
        ("rested_z0.05", 0.05, 25.0),
        ("rested_z0.90", 0.90, 25.0),
        ("rested_z0.95", 0.95, 25.0),
    )
    rows: list[dict[str, object]] = []
    for name, z, temp in probes:
        for window in WINDOW_TIERS_S:
            sop = sop_charge_limit(z, 0.0, 0.0, temp, window)
            rows.append(_sop_row(name, z, temp, window, sop))
        steady = sop_charge_limit(z, 0.0, 0.0, temp, math.inf)
        rows.append(_sop_row(name, z, temp, math.inf, steady))
    # 假想把电流帽放宽到 10 A：只有低 SOC + 高温的角落热契约才会露头
    # （真实 1.3C 帽下它永远不是最弱环，见报告 conclusion 的 3.5–4.5 倍余量）
    for temp in (30.0, 45.0, 60.0):
        sop = sop_charge_limit(0.10, 0.0, 0.0, temp, math.inf, absolute_a=10.0)
        rows.append(_sop_row("unmasked_z0.10", 0.10, temp, math.inf, sop))
    return rows


def _sop_row(
    probe: str, z: float, temp_c: float, window_s: float, sop: dict[str, object]
) -> dict[str, object]:
    return {
        "probe": probe,
        "z": z,
        "temp_c": temp_c,
        "window_s": "sustained" if math.isinf(window_s) else window_s,
        "voltage_a": _maybe_round(sop["voltage_a"]),
        "soc_a": _maybe_round(sop["soc_a"]),
        "thermal_a": _maybe_round(sop["thermal_a"]),
        "absolute_a": _maybe_round(sop["absolute_a"]),
        "limit_a": round(_num(sop["limit_a"]), 4),
        "binding": _text(sop["binding"]),
        "power_w": round(_num(sop["power_w"]), 4),
    }


def _maybe_round(value: object) -> float | None:
    if value is None:
        return None
    return round(_num(value), 4)


def permission_probes() -> list[dict[str, object]]:
    """min 语义证据：三种工况各自让充电器 / 地图 / SOP 成为最弱环，另加析锂否决。"""
    cases = (
        ("small_charger_1.5a", 0.05, 25.0, 1.5, CONTROL_WINDOW_S),
        ("map_1c_at_25c", 0.05, 25.0, CHARGER_A, CONTROL_WINDOW_S),
        ("sop_voltage_near_full", 0.90, 25.0, CHARGER_A, 60.0),
        ("plating_veto_cold", 0.85, 5.0, CHARGER_A, CONTROL_WINDOW_S),
    )
    rows: list[dict[str, object]] = []
    for name, z, temp, charger, window in cases:
        perm = charge_permission(z, 0.0, 0.0, temp, window, charger)
        rows.append(
            {
                "case": name,
                "z": z,
                "temp_c": temp,
                "window_s": window,
                "charger_a": charger,
                "limit_a": round(_num(perm["limit_a"]), 6),
                "binding": _text(perm["binding"]),
                "components_a": {
                    key: round(value, 6)
                    for key, value in cast(dict[str, float], perm["components"]).items()
                },
                "margins_a": {
                    key: round(value, 6)
                    for key, value in cast(dict[str, float], perm["margins_a"]).items()
                },
            }
        )
    return rows


def charge_map_table() -> list[dict[str, object]]:
    """温度地图取格 + 析锂否决：同一张表里看「地图给多少」与「许可实际给多少」。"""
    rows: list[dict[str, object]] = []
    for temp in (-5.0, 0.0, 5.0, 10.0, 25.0, 44.9, 45.0, 50.0, 55.0):
        map_a = charge_map_a(temp)
        perm = charge_permission(0.85, 0.0, 0.0, temp, CONTROL_WINDOW_S)
        rows.append(
            {
                "temp_c": temp,
                "map_a": round(map_a, 4),
                "map_rate_c": round(map_a / Q_AH, 4),
                "plating_veto": plating_forbidden(temp, 0.85),
                "permission_a_at_z0.85": round(_num(perm["limit_a"]), 6),
                "binding": _text(perm["binding"]),
            }
        )
    return rows


def counterexample_pair() -> dict[str, object]:
    """同一快充工况（0 °C、SOC 0.62、充电器 3 A、20 min 上限）的两个版本。"""
    duration = 6000.0
    no_map = simulate_charge(
        z0=0.62, ambient_c=0.0, duration_s=duration, temperature_permission=False
    )
    with_map = simulate_charge(
        z0=0.62, ambient_c=0.0, duration_s=duration, temperature_permission=True
    )
    no_sum = summarize_run(no_map)
    map_sum = summarize_run(with_map)
    extra_ah = _num(no_sum["ah_total"]) - _num(map_sum["ah_total"])
    plating_ah = _num(no_sum["plating_ah"])
    return {
        "condition": {
            "z0": 0.62,
            "ambient_c": 0.0,
            "charger_a": CHARGER_A,
            "duration_s": duration,
            "plating_veto": f"T < {PLATING_T_C} °C 且 z ≥ {PLATING_Z}",
        },
        "without_map": {
            **no_sum,
            "cutoff": cutoff_evidence(no_map),
            "max_current_in_plating_zone_a": round(
                max((f["i_a"] for f in _frames_of(no_map) if f["plating"] > 0.0), default=0.0), 6
            ),
        },
        "with_map": {
            **map_sum,
            "cutoff": cutoff_evidence(with_map),
        },
        "delta": {
            "extra_ah_without_map": round(extra_ah, 6),
            "extra_soc_pp": round((_num(no_sum["z_end"]) - _num(map_sum["z_end"])) * 100.0, 4),
            "plating_ah_without_map": round(plating_ah, 6),
            "plating_share_of_extra_pct": round(plating_ah / extra_ah * 100.0, 4),
            "time_ratio": round(_num(no_sum["t_end_s"]) / _num(map_sum["t_end_s"]), 4),
            "max_current_in_plating_zone_a": round(
                max((f["i_a"] for f in _frames_of(no_map) if f["plating"] > 0.0), default=0.0), 6
            ),
        },
        "note": (
            "无地图那一版多充的安时几乎全部落在析锂禁区内：许可链少了温度输入，"
            "控制器就看不见 0 °C 这个事实；有地图那一版被 0.2C 压住，到 0.80 停住等加热。"
            "两案截止 SOC 相同（本模型 OCV/内阻不随温度变），差别只在许可与时间。"
        ),
    }


def arrhenius_factor(temp_c: float) -> float:
    """D15 的温度换算 AF(T) = exp(Ea/R·(1/T_ref − 1/T))，Ea 为教学占位值。"""
    t_k = temp_c + 273.15
    t_ref_k = T_REF_C + 273.15
    return math.exp(
        EA_KJ_PER_MOL * 1000.0 / GAS_CONSTANT_J_PER_MOL_K * (1.0 / t_ref_k - 1.0 / t_k)
    )


def aging_coupling() -> dict[str, object]:
    """D15 联动：同样充满一次，45 °C 的时间与 AF 各自贡献多少老化暴露。"""
    base = simulate_charge()
    hot = simulate_charge(ambient_c=45.0)
    base_sum = summarize_run(base)
    hot_sum = summarize_run(hot)
    af45 = arrhenius_factor(45.0)
    base_exposure = _num(base_sum["t_end_s"]) * 1.0
    hot_exposure = _num(hot_sum["t_end_s"]) * af45
    return {
        "source": "D15：AF(T)=exp(Ea/R(1/T_ref−1/T))，Ea=30 kJ/mol 教学占位值（内容结论）",
        "ea_kj_per_mol": EA_KJ_PER_MOL,
        "af_25_c": round(arrhenius_factor(25.0), 4),
        "af_35_c": round(arrhenius_factor(35.0), 4),
        "af_45_c": round(af45, 4),
        "same_charge_25c": {
            "t_end_s": base_sum["t_end_s"],
            "ah_total": base_sum["ah_total"],
            "equivalent_s": round(base_exposure, 3),
            "equivalent_s_per_ah": round(base_exposure / _num(base_sum["ah_total"]), 3),
        },
        "same_charge_45c": {
            "t_end_s": hot_sum["t_end_s"],
            "ah_total": hot_sum["ah_total"],
            "equivalent_s": round(hot_exposure, 3),
            "equivalent_s_per_ah": round(hot_exposure / _num(hot_sum["ah_total"]), 3),
            "cutoff_ended_by": hot_sum["ended_by"],
        },
        "exposure_ratio": round(hot_exposure / base_exposure, 4),
        "note": (
            "45 °C 下地图把 CC 从 1C 收到 0.5C，时间乘以约 2.1，AF 再乘 2.14，"
            "同样的充满事件折算成约 3.5 倍 25 °C 老化暴露。AF 只是把温度史折算到"
            "同一参考温度的换算率，不是本电芯的寿命拟合；真实快充寿命必须回 D15/OS08 的"
            "多温度老化数据。"
        ),
    }


def build_trace_rows(
    run: dict[str, object], rest_s: float = 120.0, tail_rest_s: float = REST_AFTER_S
) -> list[dict[str, float]]:
    """把一次仿真变成可回放的记录轨迹：静置头 + 充电段 + 静置尾（供 OCV 反查）。"""
    frames = _frames_of(run)
    z0 = _num(run["z_start"])
    ambient = _num(run["ambient_c"])
    rows: list[dict[str, float]] = []
    n_rest = int(round(rest_s / DT_S))
    for step in range(n_rest):
        rows.append(
            {"t_s": step * DT_S, "current_a": 0.0, "v_meas": ocv_v(z0), "temp_c": ambient}
        )
    offset = rest_s
    # 记录的最后一拍电流没有再走完一步（运行在那一拍停住），不进记录：否则回放
    # 审计会把它多算一整拍，静置段第一步就出现 mV 级台阶。
    for frame in frames[:-1]:
        rows.append(
            {
                "t_s": offset + frame["t_s"],
                "current_a": frame["i_a"],
                "v_meas": frame["v"],
                "temp_c": frame["temp_c"],
            }
        )
    vp1 = _num(run["vp1_end"])
    vp2 = _num(run["vp2_end"])
    z_end = _num(run["z_end"])
    temp_end = _num(run["temp_end"])
    a1 = math.exp(-DT_S / TAU1_S)
    a2 = math.exp(-DT_S / TAU2_S)
    tau_th = R_TH_K_PER_W * C_TH_J_PER_K
    # 静置段第一拍 = 末态本身（OCV + 残余极化），之后两条 RC 各自衰减到 0。
    rows.append(
        {
            "t_s": offset + _num(run["t_end"]),
            "current_a": 0.0,
            "v_meas": ocv_v(z_end) + vp1 + vp2,
            "temp_c": temp_end,
        }
    )
    n_tail = int(round(tail_rest_s / DT_S))
    for step in range(n_tail - 1):
        vp1 *= a1
        vp2 *= a2
        temp = ambient + (temp_end - ambient) * math.exp(-(step + 1) * DT_S / tau_th)
        rows.append(
            {
                "t_s": offset + _num(run["t_end"]) + (step + 1) * DT_S,
                "current_a": 0.0,
                "v_meas": ocv_v(z_end) + vp1 + vp2,
                "temp_c": temp,
            }
        )
    return rows


def write_trace_csv(rows: list[dict[str, float]], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=REPLAY_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: round(row[key], 6) for key in REPLAY_COLUMNS})


def load_replay(path: Path) -> list[dict[str, float]]:
    """回放数据合同：错表头/缺列/非有限/时间回退/采样过疏/越界/首拍非静置一律拒绝。"""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != REPLAY_COLUMNS:
            raise ValueError(f"表头必须为 {','.join(REPLAY_COLUMNS)}，得到 {reader.fieldnames}")
        rows: list[dict[str, float]] = []
        last_t: float | None = None
        for lineno, raw_row in enumerate(reader, start=2):
            if None in raw_row or any(value is None for value in raw_row.values()):
                raise ValueError(f"第 {lineno} 行列数不足")
            parsed: dict[str, float] = {}
            for key in REPLAY_COLUMNS:
                raw = raw_row[key]
                if raw is None:
                    raise ValueError(f"第 {lineno} 行缺列 {key}")
                try:
                    value = float(raw)
                except ValueError as exc:
                    raise ValueError(f"第 {lineno} 行 {key} 无法解析: {raw!r}") from exc
                if not math.isfinite(value):
                    raise ValueError(f"第 {lineno} 行 {key} 非有限")
                parsed[key] = value
            if not 0.0 <= parsed["current_a"] <= ABS_CHARGE_A:
                raise ValueError(
                    f"第 {lineno} 行电流 {parsed['current_a']} A 越出 [0, {ABS_CHARGE_A}]"
                )
            if not REPLAY_TEMP_MIN_C <= parsed["temp_c"] <= REPLAY_TEMP_MAX_C:
                raise ValueError(f"第 {lineno} 行温度越出 [{REPLAY_TEMP_MIN_C}, {REPLAY_TEMP_MAX_C}] °C")
            if not REPLAY_V_MIN_V <= parsed["v_meas"] <= REPLAY_V_MAX_V:
                raise ValueError(f"第 {lineno} 行电压越出 [{REPLAY_V_MIN_V}, {REPLAY_V_MAX_V}] V")
            t_s = parsed["t_s"]
            if last_t is not None:
                gap = t_s - last_t
                if gap <= 0.0:
                    raise ValueError(f"第 {lineno} 行 t_s 未严格递增")
                if gap > REPLAY_MAX_GAP_S:
                    raise ValueError(
                        f"第 {lineno} 行采样间隔 {gap:.1f} s 超过 {REPLAY_MAX_GAP_S:.0f} s 上限"
                    )
            last_t = t_s
            rows.append(parsed)
    if len(rows) < REPLAY_MIN_SAMPLES:
        raise ValueError(f"样本数 {len(rows)} 少于 {REPLAY_MIN_SAMPLES}")
    if rows[0]["current_a"] > 0.0:
        raise ValueError("回放必须从静置开始（首拍电流必须为 0），否则无法用 OCV 定初值")
    try:
        soc_from_ocv_v(rows[0]["v_meas"])
    except ValueError as exc:
        raise ValueError(f"首拍静置电压不能反查 SOC：{exc}") from exc
    return rows


def audit_replay(rows: list[dict[str, float]], source: str) -> dict[str, object]:
    """逐拍审计：许可（不含未知的充电器能力）、析锂、电压一致性、安时能量账。"""
    z0 = soc_from_ocv_v(rows[0]["v_meas"])
    z = z0
    vp1 = 0.0
    vp2 = 0.0
    over_frames = 0
    over_ah = 0.0
    worst_over = 0.0
    first_over_t: float | None = None
    plating_frames = 0
    plating_ah = 0.0
    max_plating_i = 0.0
    voltage_over = 0
    counts: dict[str, int] = {}
    residuals: list[float] = []
    ah = 0.0
    wh = 0.0
    v_prev = rows[0]["v_meas"]
    for idx in range(len(rows) - 1):
        row = rows[idx]
        nxt = rows[idx + 1]
        dt = nxt["t_s"] - row["t_s"]
        i = row["current_a"]
        temp = row["temp_c"]
        perm = charge_permission(z, vp1, vp2, temp, CONTROL_WINDOW_S, charger_a=None)
        limit = _num(perm["limit_a"])
        binding = _text(perm["binding"])
        counts[binding] = counts.get(binding, 0) + 1
        if i > limit + REPLAY_TOL_A:
            over_frames += 1
            over_ah += (i - limit) * dt / 3600.0
            worst_over = max(worst_over, i - limit)
            if first_over_t is None:
                first_over_t = row["t_s"]
        if plating_forbidden(temp, z) and i > 0.0:
            plating_frames += 1
            plating_ah += i * dt / 3600.0
            max_plating_i = max(max_plating_i, i)
        if row["v_meas"] > V_MAX_V + 1e-3:
            voltage_over += 1
        v_model = ocv_v(z) + i * R0_OHM + vp1 + vp2
        residuals.append((v_model - row["v_meas"]) * 1000.0)
        ah += i * dt / 3600.0
        wh += 0.5 * (v_prev + row["v_meas"]) * i * dt / 3600.0
        v_prev = row["v_meas"]
        a1 = math.exp(-dt / TAU1_S)
        a2 = math.exp(-dt / TAU2_S)
        z = z + i * dt / (3600.0 * Q_AH)
        vp1 = a1 * vp1 + R1_OHM * (1.0 - a1) * i
        vp2 = a2 * vp2 + R2_OHM * (1.0 - a2) * i
    z_coulomb = z0 + ah / Q_AH
    rest_frames, v_last, max_temp = _tail_rest_gate(rows)
    taper_ok, taper_covered = _taper_gate(rows)
    z_ocv: float | None = None
    if rest_frames >= 5:
        try:
            z_ocv = soc_from_ocv_v(v_last)
        except ValueError:
            z_ocv = None
    deviation = None if z_ocv is None else (z_coulomb - z_ocv) * 100.0
    rms = math.sqrt(sum(e * e for e in residuals) / len(residuals))
    max_abs = max(abs(e) for e in residuals)
    anchor = taper_ok and plating_frames == 0 and max_temp < T_LIMIT_C
    return {
        "scenario_id": REPLAY_SCENARIO_ID,
        "source": source,
        "samples": len(rows),
        "duration_s": round(rows[-1]["t_s"] - rows[0]["t_s"], 3),
        "initial": {
            "z_from_ocv": round(z0, 6),
            "v_rest_v": round(rows[0]["v_meas"], 6),
            "note": "首拍必须静置：OCV 是唯一不依赖积分历史的绝对参照（D12）",
        },
        "permission_audit": {
            "audited_components": [
                "map",
                "plating",
                "sop_voltage",
                "sop_soc",
                "sop_thermal",
                "absolute",
            ],
            "charger_component": "未审计（记录的充电器能力未知）",
            "tolerance_a": REPLAY_TOL_A,
            "over_permission_frames": over_frames,
            "over_permission_ah": round(over_ah, 6),
            "worst_over_a": round(worst_over, 6),
            "first_over_t_s": first_over_t,
            "binding_counts": dict(sorted(counts.items())),
        },
        "plating_audit": {
            "frames": plating_frames,
            "ah": round(plating_ah, 6),
            "max_current_a": round(max_plating_i, 6),
            "rule": f"T < {PLATING_T_C} °C 且 z ≥ {PLATING_Z} 时正电流即违章",
        },
        "voltage_consistency": {
            "rms_mv": round(rms, 6),
            "max_abs_mv": round(max_abs, 6),
            "final_mv": round(residuals[-1], 6),
            "voltage_over_frames": voltage_over,
            "v_over_limit_v": V_MAX_V,
            "note": "模型 V=OCV(z)+I·R0+vp 与记录 v_meas 的差；内置模板由本模型生成，残差是构造性的",
        },
        "energy": {
            "ah_in": round(ah, 6),
            "wh_in": round(wh, 6),
            "mean_v": round(wh / ah, 6) if ah > 0.0 else None,
        },
        "soc_consistency": {
            "z_coulomb": round(z_coulomb, 6),
            "z_ocv": None if z_ocv is None else round(z_ocv, 6),
            "deviation_pp": None if deviation is None else round(deviation, 4),
            "rest_gate": (
                "末段静置拍数不足 5，不做 OCV 反查（D12 静置门）"
                if rest_frames < 5
                else "末段静置反查"
            ),
        },
        "cutoff": {
            "taper_threshold_a": TAPER_A,
            "confirm_s": TAPER_CONFIRM_S,
            "taper_satisfied": taper_ok,
            "covered_s": taper_covered,
            "max_temp_c": round(max_temp, 4),
        },
        "full_charge_anchor": anchor,
        "note": (
            "回放只审记录轨迹能证明的东西：许可是否被越过、是否在析锂区充电、"
            "记录电压与模型是否一致。它不证明真实电芯的许可正确——那要回电芯手册与"
            "受控台架（SRC04）。"
        ),
    }


def _tail_rest_gate(rows: list[dict[str, float]]) -> tuple[int, float, float]:
    """末段静置拍数、末拍电压与全程最高温（OCV 反查的静置门）。"""
    n = 0
    idx = len(rows) - 1
    while idx >= 0 and rows[idx]["current_a"] <= 1e-9:
        n += 1
        idx -= 1
    v_last = rows[-1]["v_meas"]
    max_temp = max(row["temp_c"] for row in rows)
    return n, v_last, max_temp


def _taper_gate(rows: list[dict[str, float]]) -> tuple[bool, float]:
    """末段充电拍是否连续低于 taper 阈值且覆盖 ≥ 30 s（taper 截止的记录侧核对）。"""
    last_charge: int | None = None
    for idx in range(len(rows) - 1, -1, -1):
        if rows[idx]["current_a"] > 1e-3:
            last_charge = idx
            break
    if last_charge is None:
        return False, 0.0
    first_below: int | None = None
    idx = last_charge
    while idx >= 0 and rows[idx]["current_a"] > 1e-3:
        if rows[idx]["current_a"] >= TAPER_A:
            break
        first_below = idx
        idx -= 1
    if first_below is None:
        return False, 0.0
    dt = rows[last_charge]["t_s"] - rows[max(last_charge - 1, 0)]["t_s"]
    covered = rows[last_charge]["t_s"] - rows[first_below]["t_s"] + dt
    return covered >= TAPER_CONFIRM_S - 1e-9, round(covered, 3)


def two_account_scan(run: dict[str, object], budget_ah: float) -> dict[str, object]:
    """两本账：充电器侧（i_cmd）与电芯侧（i_net）的安时/能量差，及预算命中点。"""
    frames = _frames_of(run)
    ah_chg = 0.0
    ah_cell = 0.0
    hit: dict[str, float | None] = {"t_hit_s": None, "z_at_hit": None, "ah_cell_at_hit": None}
    for idx in range(len(frames) - 1):
        frame = frames[idx]
        prev_chg = ah_chg
        prev_cell = ah_cell
        ah_chg += frame["i_charger_a"] * DT_S / 3600.0
        ah_cell += frame["i_a"] * DT_S / 3600.0
        if hit["t_hit_s"] is None and ah_chg >= budget_ah:
            span = ah_chg - prev_chg
            frac = (budget_ah - prev_chg) / span if span > 1e-15 else 0.0
            nxt = frames[idx + 1]
            hit = {
                "t_hit_s": round(frame["t_s"] + frac * DT_S, 3),
                "z_at_hit": round(frame["z"] + frac * (nxt["z"] - frame["z"]), 6),
                "ah_cell_at_hit": round(prev_cell + frac * (ah_cell - prev_cell), 6),
            }
    return {
        "budget_ah": round(budget_ah, 6),
        "ah_charger_total": round(ah_chg, 6),
        "ah_cell_total": round(ah_cell, 6),
        **hit,
    }


def net_current_section(aux_run: dict[str, object], baseline: dict[str, object]) -> dict[str, object]:
    """净电流口径：电芯模型用 i_net，充电器侧另记 i_cmd；两本账的差是附件耗电。"""
    summary = summarize_run(aux_run)
    budget_ah = _num(baseline["ah_total"])
    scan = two_account_scan(aux_run, budget_ah)
    ah_gap = _num(summary["ah_gap"])
    wh_gap = _num(summary["wh_gap"])
    return {
        "aux_load_a": AUX_LOAD_A,
        "definition": (
            "i_net = i_cmd − i_aux：SOC 积分、端电压、CV 切换与 taper 判定一律用电芯"
            "净电流；充电器能力先扣附件分流（charger − aux），电压/电流限制落在电芯侧"
        ),
        "accounting": (
            "充电器侧 Ah/Wh 用 i_cmd 与充电器侧端电压积分（含 i_cmd²·R_cable）；"
            "电芯侧用 i_net；差值 = 附件耗电与线缆损耗，不是电芯的电荷"
        ),
        "run": {
            "condition": {
                "z0": _num(summary["z_start"]),
                "ambient_c": _num(summary["ambient_c"]),
                "charger_a": _num(aux_run["charger_a"]),
                "aux_load_a": AUX_LOAD_A,
                "cable_ohm": 0.0,
                "duration_s": _num(aux_run["duration_s"]),
            },
            "t_end_s": summary["t_end_s"],
            "z_end": summary["z_end"],
            "ended_by": summary["ended_by"],
            "i_end_a": summary["i_end_a"],
            "ah_cell": summary["ah_total"],
            "ah_charger": summary["ah_charger"],
            "wh_cell": summary["wh_cell"],
            "wh_charger": summary["wh_charger"],
            "ah_gap": summary["ah_gap"],
            "wh_gap": summary["wh_gap"],
            "ah_gap_pct_of_charger": round(ah_gap / _num(summary["ah_charger"]) * 100.0, 4),
            "wh_gap_pct_of_charger": round(wh_gap / _num(summary["wh_charger"]) * 100.0, 4),
            "binding_counts": summary["binding_counts"],
            "temp_max_c": summary["temp_max_c"],
        },
        "budget": {
            "budget_ah": scan["budget_ah"],
            "basis": "满充预算 = 默认轨迹的电芯侧安时（0.05 → 0.9497）",
            "t_hit_s": scan["t_hit_s"],
            "z_at_hit": scan["z_at_hit"],
            "ah_cell_at_hit": scan["ah_cell_at_hit"],
            "soc_gap_pp_vs_default": (
                round((_num(baseline["z_end"]) - _num(scan["z_at_hit"])) * 100.0, 4)
                if scan["z_at_hit"] is not None
                else None
            ),
            "note": "充电器侧安时先到满充预算，电芯 SOC 还差一截：预算账不是电荷账",
        },
        "note": (
            "默认场景 aux = 0，既有冻结数字不变；本节的 0.4 A 附件为教学值，"
            "不认定为整车负载或线束参数"
        ),
    }


def false_full_section(
    limited_run: dict[str, object],
    aux_run: dict[str, object],
    baseline: dict[str, object],
) -> dict[str, object]:
    """假满充反例：上游限流 + 线缆压降（电压/taper 成立但 SOC 低），附件分账。"""
    limited = summarize_run(limited_run)
    limited_cut = cutoff_evidence(limited_run)
    taper_block = cast(dict[str, object], limited_cut["taper"])
    soc_block = cast(dict[str, object], limited_cut["soc"])
    aux_summary = summarize_run(aux_run)
    budget_ah = _num(baseline["ah_total"])
    scan = two_account_scan(aux_run, budget_ah)
    baseline_z = _num(baseline["z_end"])
    z_hit = _num(scan["z_at_hit"]) if scan["z_at_hit"] is not None else None
    return {
        "upstream_limit": {
            "condition": {
                "z0": _num(limited["z_start"]),
                "ambient_c": _num(limited["ambient_c"]),
                "charger_a": _num(limited_run["charger_a"]),
                "aux_load_a": AUX_LOAD_A,
                "cable_ohm": CABLE_OHM,
                "duration_s": _num(limited_run["duration_s"]),
                "regulation_point": "充电器出口调 4.2 V；电芯端电压 = 出口电压 − i_cmd·R_cable",
            },
            "t_end_s": limited["t_end_s"],
            "z_end": limited["z_end"],
            "z_switch": limited["z_switch"],
            "t_switch_s": limited["t_switch_s"],
            "ah_total": limited["ah_total"],
            "ended_by": limited["ended_by"],
            "taper_t_s": None if taper_block["t_s"] is None else _num(taper_block["t_s"]),
            "taper_i_end_a": _num(taper_block["i_end_a"]),
            "v_cell_max_v": limited["v_max_v"],
            "v_charger_max_v": limited["v_charger_max_v"],
            "v_drop_mv": round(
                (_num(limited["v_charger_max_v"]) - _num(limited["v_max_v"])) * 1000.0, 4
            ),
            "soc_meets": bool(soc_block["meets"]),
            "full_charge_anchor": bool(limited_cut["full_charge_anchor"]),
            "soc_gap_pp_vs_default": round((baseline_z - _num(limited["z_end"])) * 100.0, 4),
            "binding_counts": limited["binding_counts"],
            "note": (
                "充电器侧电压到 4.2 V、taper 也成立，电芯却只到 0.8x：线缆压降让电芯"
                "提前进入 CV，截止证据必须带 SOC/能量交叉核对"
            ),
        },
        "aux_load": {
            "condition": {
                "z0": _num(aux_summary["z_start"]),
                "ambient_c": _num(aux_summary["ambient_c"]),
                "charger_a": _num(aux_run["charger_a"]),
                "aux_load_a": AUX_LOAD_A,
                "cable_ohm": 0.0,
                "duration_s": _num(aux_run["duration_s"]),
            },
            "budget_ah": scan["budget_ah"],
            "t_budget_hit_s": scan["t_hit_s"],
            "z_at_budget": scan["z_at_hit"],
            "ah_cell_at_budget": scan["ah_cell_at_hit"],
            "t_end_s": aux_summary["t_end_s"],
            "ended_by": aux_summary["ended_by"],
            "ah_charger_total": aux_summary["ah_charger"],
            "ah_cell_total": aux_summary["ah_total"],
            "ah_gap": aux_summary["ah_gap"],
            "wh_charger_total": aux_summary["wh_charger"],
            "wh_cell_total": aux_summary["wh_cell"],
            "wh_gap": aux_summary["wh_gap"],
            "soc_gap_pp_vs_default": round(
                (baseline_z - z_hit) * 100.0 if z_hit is not None else 0.0, 4
            ),
            "note": (
                "CC 段附件分走 0.4 A：充电器侧安时先满足满充预算，电芯 SOC 只到 0.8x；"
                "两本账的差是附件耗电，不是电芯的电荷"
            ),
        },
        "note": (
            "两案都说明：taper + 电压截止成立 ≠ 真满。本模块的教学模型不生成电芯"
            "许可；真实许可与满充判据必须回电芯手册与受控台架（SRC04）"
        ),
    }


def build_net_current_rows(run: dict[str, object]) -> list[dict[str, float]]:
    """附件场景轨迹：充电器侧与电芯侧两套电流/电压。"""
    return [
        {
            "t_s": frame["t_s"],
            "i_charger_a": frame["i_charger_a"],
            "i_net_a": frame["i_a"],
            "v_cell_v": frame["v"],
            "v_charger_v": frame["v_charger"],
            "temp_c": frame["temp_c"],
            "z": frame["z"],
        }
        for frame in _frames_of(run)
    ]


def write_net_current_csv(rows: list[dict[str, float]], path: Path) -> None:
    columns = ["t_s", "i_charger_a", "i_net_a", "v_cell_v", "v_charger_v", "temp_c", "z"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: round(row[key], 6) for key in columns})


def build_report(
    user_replay: dict[str, object] | None = None,
) -> dict[str, object]:
    """默认场景的完整报告；回放审计始终包含内置模板与反例两条轨迹。"""
    default_run = simulate_charge()
    default_sum = summarize_run(default_run)
    no_map_run = simulate_charge(
        z0=0.62, ambient_c=0.0, duration_s=6000.0, temperature_permission=False
    )
    aux_run = simulate_charge(aux_a=AUX_LOAD_A)
    limited_run = simulate_charge(
        charger_a=1.0, aux_a=AUX_LOAD_A, cable_ohm=CABLE_OHM, duration_s=15000.0
    )
    template_rows = build_trace_rows(default_run)
    counterexample_rows = build_trace_rows(no_map_run)
    replay: dict[str, object] = {
        "scenario_id": REPLAY_SCENARIO_ID,
        "contract": {
            "columns": REPLAY_COLUMNS,
            "max_gap_s": REPLAY_MAX_GAP_S,
            "min_samples": REPLAY_MIN_SAMPLES,
            "current_range_a": [0.0, ABS_CHARGE_A],
            "temperature_range_c": [REPLAY_TEMP_MIN_C, REPLAY_TEMP_MAX_C],
            "voltage_range_v": [REPLAY_V_MIN_V, REPLAY_V_MAX_V],
            "first_sample_must_be_rest": True,
            "rejects": "缺文件/错表头/缺列/非有限/时间回退/采样过疏/越界/首拍非静置 → exit 2",
        },
        "template": audit_replay(template_rows, "内置模板：默认 CC/CV 轨迹"),
        "counterexample": audit_replay(counterexample_rows, "内置反例：0 °C 无地图轨迹"),
    }
    if user_replay is not None:
        replay["user"] = user_replay
    return {
        "scenario_id": SCENARIO_ID,
        "identity": (
            "teaching CC/CV charge control and charge-permission chain; cell, map, thermal, "
            "OCV, taper and meter values are teaching placeholders — not a cell datasheet, "
            "not device measurement, not HIL, not human review"
        ),
        "cell": {
            "q_ah": Q_AH,
            "ocv_base_v": OCV_BASE_V,
            "ocv_slope_low_v_per_soc": OCV_SLOPE_LOW_V_PER_SOC,
            "ocv_knee_z": OCV_KNEE_Z,
            "ocv_slope_top_v_per_soc": OCV_SLOPE_TOP_V_PER_SOC,
            "v_max_v": V_MAX_V,
            "r0_ohm": R0_OHM,
            "r1_ohm": R1_OHM,
            "tau1_s": TAU1_S,
            "r2_ohm": R2_OHM,
            "tau2_s": TAU2_S,
            "z0": Z0,
            "dt_s": DT_S,
        },
        "permission_chain": {
            "charger_a": CHARGER_A,
            "absolute_a": ABS_CHARGE_A,
            "map": "温度分档教学地图：<0 停、0–10 0.2C、10–45 1C、45–55 0.5C、≥55 停",
            "plating_veto": f"T < {PLATING_T_C} °C 且 z ≥ {PLATING_Z} 时许可为 0（独立否决项）",
            "taper": {"threshold_a": TAPER_A, "confirm_s": TAPER_CONFIRM_S},
            "time_limit_s": TIME_LIMIT_S,
            "control_window_s": CONTROL_WINDOW_S,
            "soc_fence": Z_FENCE,
        },
        "charge_map": charge_map_table(),
        "sop_windows": sop_window_table(),
        "permission_probes": permission_probes(),
        "trajectory": default_sum,
        "window_effect": window_effect(),
        "cutoff_evidence": cutoff_evidence(default_run),
        "energy_account": energy_account(default_run),
        "plating_counterexample": counterexample_pair(),
        "net_current": net_current_section(aux_run, default_sum),
        "false_full": false_full_section(limited_run, aux_run, default_sum),
        "aging_coupling": aging_coupling(),
        "replay": replay,
        "boundary": {
            "teaching_values": (
                "Q、OCV 折线、R0/R1/R2、V_max、地图形状、C_th/R_th/R_heat、芯限、taper、"
                "时间上限、表计偏置均为教学值，与第 11 章 CC-CV 算例同源"
            ),
            "not_claimed": (
                "不认定为电芯手册、器件实测、热仿真验收、HIL 或真人评审；"
                "不证明任何具体电芯在该温度下可以这样充"
            ),
            "map_not_permission": (
                "地图形状取自第 11 章 stage-4 §4.7b 的教学示意（2 Ah 电芯、1C 档），"
                "不是电芯手册；真实许可必须回电芯手册（SRC04）"
            ),
            "firmware_gap": (
                "BmsInputs 只有 cell_mv/current_ma/temp_c10/charger_present（无时间戳/质量位）；"
                "Bms 输出只有 charge_mos_on（无充电电流请求/许可字段）；BmsConfig 只有 "
                "full_mv/full_cutoff_ma 的满充判据（无温度分档地图、无预测窗 SOP、无析锂"
                "边界状态）——本单元的许可链是教学补全，不证明固件已实现"
            ),
            "actuator": (
                "假设充电器在一个控制周期内跟踪许可电流；充电机响应延迟、报文刷新与"
                "过期需求值未建模（第 11 章 §11.4 的延迟预算不在此闭合）"
            ),
            "temperature_model": (
                "单热节点（C_th=156 J/K、R_th=5.5 K/W、R_heat=0.09 Ω）；D16 的两节点"
                "芯-壳梯度与 NTC 滞后不在本模块内，热契约用其持续电流口径"
            ),
            "net_current": (
                "i_net = i_cmd − i_aux：许可链限制的是电芯净电流，充电器侧另记 i_cmd；"
                "附件电流 0.4 A 与线缆电阻 0.25 Ω 为教学值，不认定为整车负载或线束参数；"
                "教学模型不生成电芯许可"
            ),
            "false_full": (
                "上游限流 + 线缆压降、附件耗电都能让 taper 与电压截止同时成立而 SOC 未满："
                "满充锚点必须带 SOC/能量交叉核对；教学反例不证明任何真实充电机/线束的行为"
            ),
        },
        "conclusion": (
            "充电许可不是一条曲线而是一条链：本单元的默认轨迹上地图在 CC 段在限，"
            "电压余量在 CV 段在限，热契约始终有 3.5–4.5 倍余量；截止必须三元同时成立，"
            "taper 单独成立不证明合规。0 °C 反例里无地图方案多充的 0.30 Ah 全部落在"
            "析锂禁区，有地图方案以 0.2C 停在 0.80 等加热——差别不在算法，在许可链"
            "有没有温度输入。"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 与轨迹 CSV 的目录")
    parser.add_argument(
        "--data",
        type=Path,
        help=f"回放 CSV（{','.join(REPLAY_COLUMNS)}）；首拍必须静置",
    )
    args = parser.parse_args(argv)

    user_replay: dict[str, object] | None = None
    if args.data is not None:
        try:
            rows = load_replay(args.data)
        except (OSError, ValueError) as exc:
            print(f"回放数据拒绝：{exc}", file=sys.stderr)
            return 2
        user_replay = audit_replay(rows, f"用户 CSV：{args.data.name}")

    report = build_report(user_replay=user_replay)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(text + "\n", encoding="utf-8")
        default_run = simulate_charge()
        no_map_run = simulate_charge(
            z0=0.62, ambient_c=0.0, duration_s=6000.0, temperature_permission=False
        )
        write_trace_csv(build_trace_rows(default_run), args.out / "charge_trace.csv")
        write_trace_csv(build_trace_rows(no_map_run), args.out / "counterexample.csv")
        write_trace_csv(build_trace_rows(default_run), args.out / "replay_template.csv")
        aux_run = simulate_charge(aux_a=AUX_LOAD_A)
        write_net_current_csv(build_net_current_rows(aux_run), args.out / "net_current.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
