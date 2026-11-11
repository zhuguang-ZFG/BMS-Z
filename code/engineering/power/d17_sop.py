"""Teaching experiments for D17: multi-constraint SOP over anchored windows.

D17「SOP 与多约束」的可执行证据模块。四件事：

1. 把「未来一段时间最多允许多大电流」写成四条可计算的上限：电压墙（D02 的
   OCV + 一阶 RC，窗内端电压不越 v_min/v_max）、SOC 墙（D12 的库仑账，窗末
   不越 z_min/z_max）、热墙（D16 的稳态芯温契约）、绝对电流帽；
2. 把窗口锚定在 10/30/60/600 s 与「持续」五档上，每档取最弱环，给出哪条约束
   在限、其余余量多少、窗口末端端电压与端口功率；
3. 反例：单快照 Rint 闭式 SOP 与窗口约束 SOP 的差（峰值虚高量化），以及
   30/45 °C 温度对照（热墙降额）；
4. 工况回放：把一条电流剖面逐拍对照 60 s 窗口 SOP，给出越限证据与能量账；
   另用「整窗实际剖面 min/max」与「只看窗末」两个口径抓端点漏报（窗内换流时
   端点不是最坏点）；
5. 参数不确定性缩限：R0 ±20%、R1 ±30%、Q ±5%、R_total ±15%、OCV ±10 mV，
   每条上限在自己的最坏角点重算后取最小，给出逐档收缩量与主导参数。

教学身份：电芯参数（Q、R0、R1、C1）、电压/SOC 边界、电流帽与热参数（R_total、
芯限、环境温度）全部是教学值，不认定为任何器件实测、热仿真验收或真人评审结论；
真实 SOP 必须按本模块声明的窗口合同、以登记过身份的数据（B05）重算，并经
OS03 整包热模型与 SRC04 独立温度测点闭合。

口径：新深研约定 `I > 0` 放电、`I < 0` 充电，`V = U(z) − I·R0 − v_p`；
固件 `BmsInputs.current_ma > 0` 充电，边界处 `I_legacy = −I`，恰好一次。

边界（必须与正文同页）：固件 `BmsInputs` 只有 `cell_mv[]`、`current_ma`、
`temp_c10`、`charger_present`，没有 SOP 窗口、没有「哪条约束在限」字段，也没有
任何降额输出；本模块的多约束分解与逐窗 SOP 是教学补全，不证明固件已实现
SOP 计算或降额策略。
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

SCENARIO_ID = "D17-sop-window"
PROFILE_SCENARIO_ID = "D17-profile-replay"

# --- 教学电芯（3 Ah、老化后内阻与 D16 同一数值：电压与发热共用同一内阻）---
Q_AH = 3.0
R0_OHM = 0.090       # 欧姆内阻；同时是 D16 的 R_int（教学口径只保留一个内阻）
R1_OHM = 0.030       # 极化电阻
C1_F = 1500.0        # 极化电容
TAU1_S = R1_OHM * C1_F  # 45 s（D02 慢支路量级）

V_MIN_V = 3.00
V_MAX_V = 4.20
Z_MIN = 0.10
Z_MAX = 0.95

I_MAX_DISCHARGE_A = 20.0   # 绝对电流帽（连接器/熔断器，教学值）
I_MAX_CHARGE_A = 10.0

# --- D16 热契约：稳态芯温不越限的持续电流 sqrt((T限−T环境)/(R_total·R_int)) ---
AMBIENT_C = 30.0
HOT_AMBIENT_C = 45.0
CORE_LIMIT_C = 70.0
R_CORE_CASE_K_PER_W = 3.0
R_CASE_AMB_K_PER_W = 2.5
R_TOTAL_K_PER_W = R_CORE_CASE_K_PER_W + R_CASE_AMB_K_PER_W
R_INT_OHM = R0_OHM          # 发热内阻与电压内阻同一个教学值
C_TH_TOTAL_J_PER_K = 156.0  # D16 芯 36 + 壳 120，只用于声明热时间常数

# --- 窗口档：10/30/60/600 s 峰值档 + 持续档（持续档无窗口，SOC 墙不适用）---
WINDOWS_S: tuple[float, ...] = (10.0, 30.0, 60.0, 600.0)
SUSTAINED_TIER_ID = "sustained"
TIER_IDS: tuple[str, ...] = ("10s", "30s", "60s", "600s", SUSTAINED_TIER_ID)

DT_S = 1.0              # 全程核对步长（远小于 τ1 = 45 s 与热时间常数 858 s）
BISECT_ITERS = 60
BISECT_TOL_A = 1e-4
VOLT_EPS_V = 1e-9

# --- 参数不确定性（教学口径）：每条上限在自己的最坏角点评估，绝不取平均 ---
R0_UNCERTAINTY_PCT = 20.0       # 欧姆内阻：老化、温度、批次
R1_UNCERTAINTY_PCT = 30.0       # 极化电阻：参数辨识误差大于 R0
Q_UNCERTAINTY_PCT = 5.0         # 可用容量：健康度与温度
R_TOTAL_UNCERTAINTY_PCT = 15.0  # 热阻链：接触热阻、风速
OCV_UNCERTAINTY_MV = 10.0       # OCV：滞回、温度、老化
UNCERTAINTY_CORNER_ORDER: tuple[str, ...] = ("r0", "r1", "ocv", "q", "r_total")

# --- D17-profile-replay：工况回放合同 ---
PROFILE_COLUMNS = ["t_s", "current_a"]
PROFILE_SOC_START = 0.90
PROFILE_DT_S = 10.0
PROFILE_HORIZON_S = 60.0   # 回放时逐拍对照的 SOP 窗口
PROFILE_LIMIT_TOL_A = 0.05  # 越限判定容差：小于该差值算在包线上
MIN_PROFILE_FRAMES = 10
PROFILE_PHASES: list[tuple[float, float, float]] = [
    (0.0, 300.0, 0.0),
    (300.0, 900.0, 6.0),
    (900.0, 1200.0, 0.0),
    (1200.0, 1500.0, 12.0),
    (1500.0, 1800.0, 0.0),
]
PROFILE_AUDIT_COLUMNS = [
    "t_s", "current_a", "soc_pp", "allowed_a", "binding", "exceeded", "window_violation",
    "trajectory_min_v", "trajectory_max_v", "endpoint_v",
    "endpoint_only_violation", "endpoint_missed",
]
TIER_CSV_COLUMNS = [
    "operating_point", "direction", "soc", "ambient_c", "tier_id", "window_s",
    "allowed_a", "binding_constraint", "voltage_a", "soc_a", "thermal_a",
    "hardware_a", "v_end_v", "power_w",
]


def _num(value: object) -> float:
    """从 report 字典里取回数值（pyright 友好，同时是运行时契约检查）。"""
    if not isinstance(value, (int, float)):
        raise TypeError(f"期望数值，得到 {type(value).__name__}")
    return float(value)


def _direction_sign(direction: str) -> float:
    """放电 +1、充电 −1；未知方向直接拒绝，不猜。"""
    if direction == "discharge":
        return 1.0
    if direction == "charge":
        return -1.0
    raise ValueError(f"未知方向：{direction!r}（只接受 discharge/charge）")


def ocv_v(z: float) -> float:
    """教学 OCV 曲线（与 code/soc 同一形状）：3.2 + 0.8z + 两个端部 tanh。

    与旧接口不同，这里不做 [0,1] 限幅：越界的 z 是模型适用域之外，必须由调用方
    拒绝，不能让限幅把越界悄悄变成合法状态。
    """
    if not 0.0 <= z <= 1.0:
        raise ValueError(f"SOC 越界：{z!r}（必须在 [0,1] 内）")
    return (
        3.2
        + 0.8 * z
        + 0.2 * math.tanh((z - 0.05) * 30.0)
        + 0.05 * math.tanh((z - 0.90) * 15.0)
    )


def terminal_voltage(
    z: float,
    v_p: float,
    current_a: float,
    *,
    r0_ohm: float = R0_OHM,
    ocv_offset_v: float = 0.0,
) -> float:
    """端电压：V = U(z) + 偏移 − I·R0 − v_p（I > 0 放电）。

    偏移只用于不确定性角点（放电取负、充电取正），默认 0 时与查表口径一致。
    """
    return ocv_v(z) + ocv_offset_v - current_a * r0_ohm - v_p


def step_state(
    z: float,
    v_p: float,
    current_a: float,
    dt_s: float,
    *,
    r1_ohm: float = R1_OHM,
    q_ah: float = Q_AH,
) -> tuple[float, float]:
    """零阶保持精确一步：SOC 线性扣减，极化按 exp(−dt/τ) 递推。

    τ 随 R1 角点按 R1·C1 缩放（C1 视为固定），而不是把 τ 当独立参数。
    """
    if not math.isfinite(dt_s) or dt_s <= 0.0:
        raise ValueError(f"步长必须是正的有限数，收到 {dt_s!r}")
    if r1_ohm <= 0.0 or q_ah <= 0.0:
        raise ValueError("R1 与容量必须为正")
    z_next = z - current_a * dt_s / (3600.0 * q_ah)
    a = math.exp(-dt_s / (r1_ohm * C1_F))
    v_p_next = a * v_p + r1_ohm * (1.0 - a) * current_a
    return z_next, v_p_next


def _window_extremes(
    z0: float,
    v_p0: float,
    current_a: float,
    window_s: float,
    dt_s: float = DT_S,
    *,
    r0_ohm: float = R0_OHM,
    r1_ohm: float = R1_OHM,
    q_ah: float = Q_AH,
    ocv_offset_v: float = 0.0,
) -> tuple[float, float, float] | None:
    """窗内端电压的 (min, max, end)。SOC 越出 [0,1] 返回 None（不可行）。

    候选电流是常值，端电压在窗内至多一个内部极值；报告另用 1 s 步长全程核对，
    这里的逐拍扫描本身就是「检查全程」而不是只看窗末。关键字参数只给不确定性
    角点用，默认值与名义参数逐位相同。
    """
    z = z0
    v_p = v_p0
    v = terminal_voltage(z, v_p, current_a, r0_ohm=r0_ohm, ocv_offset_v=ocv_offset_v)
    v_min = v_max = v
    t = 0.0
    while t < window_s - 1e-9:
        h = min(dt_s, window_s - t)
        z, v_p = step_state(z, v_p, current_a, h, r1_ohm=r1_ohm, q_ah=q_ah)
        if not 0.0 <= z <= 1.0:
            return None
        t += h
        v = terminal_voltage(z, v_p, current_a, r0_ohm=r0_ohm, ocv_offset_v=ocv_offset_v)
        v_min = min(v_min, v)
        v_max = max(v_max, v)
    return v_min, v_max, v


def simulate_constant(
    z0: float,
    v_p0: float,
    current_a: float,
    window_s: float,
    dt_s: float = DT_S,
    *,
    r0_ohm: float = R0_OHM,
    r1_ohm: float = R1_OHM,
    q_ah: float = Q_AH,
    ocv_offset_v: float = 0.0,
) -> dict[str, float]:
    """常值电流整窗仿真：返回窗末状态与全程 min/max（与二分同一离散口径）。"""
    if not math.isfinite(window_s) or window_s <= 0.0:
        raise ValueError(f"窗口必须是正的有限数，收到 {window_s!r}")
    ext = _window_extremes(
        z0,
        v_p0,
        current_a,
        window_s,
        dt_s,
        r0_ohm=r0_ohm,
        r1_ohm=r1_ohm,
        q_ah=q_ah,
        ocv_offset_v=ocv_offset_v,
    )
    if ext is None:
        raise ValueError("窗口内 SOC 越出 [0,1]，该电流不可行")
    v_min, v_max, v_end = ext
    z_end = z0 - current_a * window_s / (3600.0 * q_ah)
    a = math.exp(-window_s / (r1_ohm * C1_F))
    v_p_end = a * v_p0 + r1_ohm * (1.0 - a) * current_a
    return {
        "v_min_v": v_min,
        "v_max_v": v_max,
        "v_end_v": v_end,
        "z_end": z_end,
        "v_p_end_v": v_p_end,
        "current_a": current_a,
        "window_s": window_s,
    }


def soc_window_limit_a(
    z0: float,
    direction: str,
    window_s: float,
    *,
    z_min: float = Z_MIN,
    z_max: float = Z_MAX,
    q_ah: float = Q_AH,
) -> float:
    """SOC 墙的最大电流幅值：窗末恰好停在下/上限（库仑账是线性的）。"""
    if not math.isfinite(window_s) or window_s <= 0.0:
        raise ValueError(f"窗口必须是正的有限数，收到 {window_s!r}")
    if q_ah <= 0.0:
        raise ValueError("容量必须为正")
    if direction == "discharge":
        budget_ah = (z0 - z_min) * q_ah
    elif direction == "charge":
        budget_ah = (z_max - z0) * q_ah
    else:
        raise ValueError(f"未知方向：{direction!r}")
    if budget_ah <= 0.0:
        return 0.0  # 已经贴墙或越墙：只允许零电流，不给负许可
    return budget_ah * 3600.0 / window_s


def thermal_sustained_a(
    ambient_c: float,
    *,
    core_limit_c: float = CORE_LIMIT_C,
    r_total_k_per_w: float = R_TOTAL_K_PER_W,
    r_int_ohm: float = R_INT_OHM,
) -> float:
    """D16 热契约：稳态芯温不越限的持续电流 I = √((T限−T环境)/(R_total·R_int))。

    分子非正（环境已达/超过芯限）时直接拒绝：不对负数开方后用异常值冒充许可，
    也不把「已过温」翻译成「允许某个电流」。瞬态峰值余量不在本闭式的承诺内。
    """
    rise_k = core_limit_c - ambient_c
    if rise_k <= 0.0:
        raise ValueError(
            f"环境 {ambient_c} °C 已不低于芯限 {core_limit_c} °C：热契约无正许可"
        )
    if r_total_k_per_w <= 0.0 or r_int_ohm <= 0.0:
        raise ValueError("热阻与内阻必须为正")
    return math.sqrt(rise_k / (r_total_k_per_w * r_int_ohm))


def window_voltage_limit(
    z0: float,
    v_p0: float,
    direction: str,
    window_s: float,
    *,
    hardware_a: float,
    v_min_v: float = V_MIN_V,
    v_max_v: float = V_MAX_V,
    r0_ohm: float = R0_OHM,
    r1_ohm: float = R1_OHM,
    q_ah: float = Q_AH,
    ocv_offset_v: float = 0.0,
) -> float:
    """电压墙的最大电流幅值：整窗端电压都留在 [v_min, v_max] 内。

    二分的是「候选常值电流 → 整窗前向仿真」这条单调可行性；零电流即越压时
    返回 0.0（当前状态不允许该方向电流），不返回负值或 inf。关键字参数是
    不确定性角点入口，默认值与名义参数逐位相同。
    """
    sign = _direction_sign(direction)

    def feasible(magnitude: float) -> bool:
        ext = _window_extremes(
            z0,
            v_p0,
            sign * magnitude,
            window_s,
            r0_ohm=r0_ohm,
            r1_ohm=r1_ohm,
            q_ah=q_ah,
            ocv_offset_v=ocv_offset_v,
        )
        if ext is None:
            return False
        v_min, v_max, _ = ext
        return v_min >= v_min_v - VOLT_EPS_V and v_max <= v_max_v + VOLT_EPS_V

    if not feasible(0.0):
        return 0.0
    if feasible(hardware_a):
        return hardware_a
    lo, hi = 0.0, hardware_a
    for _ in range(BISECT_ITERS):
        mid = 0.5 * (lo + hi)
        if feasible(mid):
            lo = mid
        else:
            hi = mid
        if hi - lo < BISECT_TOL_A:
            break
    return lo


def sustained_voltage_limit(
    z0: float,
    v_p0: float,
    direction: str,
    *,
    v_min_v: float = V_MIN_V,
    v_max_v: float = V_MAX_V,
    r0_ohm: float = R0_OHM,
    r1_ohm: float = R1_OHM,
    ocv_offset_v: float = 0.0,
) -> float:
    """持续档的电压界：取「施加瞬间」与「极化稳定后」两个端点里更紧的一个。

    持续档不承诺跑空：这里只问稳态压降，SOC 账由有限窗口档负责。
    """
    ocv = ocv_v(z0) + ocv_offset_v
    if direction == "discharge":
        instant = (ocv - v_p0 - v_min_v) / r0_ohm
        steady = (ocv - v_min_v) / (r0_ohm + r1_ohm)
    elif direction == "charge":
        instant = (v_max_v - ocv + v_p0) / r0_ohm
        steady = (v_max_v - ocv) / (r0_ohm + r1_ohm)
    else:
        raise ValueError(f"未知方向：{direction!r}")
    return max(0.0, min(instant, steady))


def _window_limits(
    z0: float,
    v_p0: float,
    direction: str,
    window_s: float | None,
    ambient_c: float,
    *,
    hardware_a: float,
    v_min_v: float,
    v_max_v: float,
    z_min: float,
    z_max: float,
    q_ah: float,
    r0_ohm: float,
    r1_ohm: float,
    ocv_offset_v: float,
    r_total_k_per_w: float,
) -> dict[str, float | None]:
    """给定一组参数角点，逐条给出四类上限（未取整、未取最弱环）。

    电压墙的 SOC 积分固定用名义容量 Q_AH（声明的不确定性角点只给 R0/R1/OCV）；
    容量角点只进入 SOC 墙自己的库仑账。这样每条上限都只在自己的最坏角点上评估。
    """
    if window_s is None:
        voltage = sustained_voltage_limit(
            z0,
            v_p0,
            direction,
            v_min_v=v_min_v,
            v_max_v=v_max_v,
            r0_ohm=r0_ohm,
            r1_ohm=r1_ohm,
            ocv_offset_v=ocv_offset_v,
        )
        soc: float | None = None
    else:
        voltage = window_voltage_limit(
            z0,
            v_p0,
            direction,
            window_s,
            hardware_a=hardware_a,
            v_min_v=v_min_v,
            v_max_v=v_max_v,
            r0_ohm=r0_ohm,
            r1_ohm=r1_ohm,
            ocv_offset_v=ocv_offset_v,
        )
        soc = soc_window_limit_a(
            z0, direction, window_s, z_min=z_min, z_max=z_max, q_ah=q_ah
        )
    thermal = thermal_sustained_a(ambient_c, r_total_k_per_w=r_total_k_per_w)
    # 电压墙在电流帽以内不构成限制时记 None（它没有给出比帽更紧的数），
    # 而不是把帽的值抄成「电压上限」——否则最弱环会误报成电压。
    return {
        "voltage": None if voltage >= hardware_a else voltage,
        "soc": soc,
        "thermal": thermal,
        "hardware": hardware_a,
    }


def _allowed_from(limits: dict[str, float | None]) -> float:
    """四类上限的最弱环（电流幅值）；hardware 总在，故结果非空。"""
    values = [value for value in limits.values() if value is not None]
    if not values:
        raise ValueError("四条上限全不适用：无法给出许可")
    return min(values)


def snapshot_current_a(z0: float, v_p0: float, direction: str) -> float:
    """单快照 Rint 闭式：只用此刻 OCV 与 R0 除一条代数式，看不见窗口。"""
    ocv = ocv_v(z0)
    if direction == "discharge":
        return max(0.0, (ocv - v_p0 - V_MIN_V) / R0_OHM)
    if direction == "charge":
        return max(0.0, (V_MAX_V - ocv + v_p0) / R0_OHM)
    raise ValueError(f"未知方向：{direction!r}")


def sop_tiers(
    z0: float,
    v_p0: float = 0.0,
    direction: str = "discharge",
    ambient_c: float = AMBIENT_C,
    *,
    hardware_a: float | None = None,
    v_min_v: float = V_MIN_V,
    v_max_v: float = V_MAX_V,
    z_min: float = Z_MIN,
    z_max: float = Z_MAX,
    q_ah: float = Q_AH,
) -> list[dict[str, object]]:
    """逐窗计算四条上限并取最弱环；返回每档的约束分解与余量。

    四条上限都写成「电流幅值」再取最小——不允许把某项许可取平均，也不允许
    先按方向翻符号再比较。`hardware_a` 是绝对电流帽的显式覆盖入口（缺省按
    方向取 I_MAX_DISCHARGE_A / I_MAX_CHARGE_A）。
    """
    sign = _direction_sign(direction)
    if hardware_a is None:
        hardware_a = I_MAX_DISCHARGE_A if sign > 0.0 else I_MAX_CHARGE_A
    if not math.isfinite(hardware_a) or hardware_a <= 0.0:
        raise ValueError(f"电流帽必须是正的有限数，收到 {hardware_a!r}")
    base_kwargs = {
        "hardware_a": hardware_a,
        "v_min_v": v_min_v,
        "v_max_v": v_max_v,
        "z_min": z_min,
        "z_max": z_max,
        "q_ah": q_ah,
        "r0_ohm": R0_OHM,
        "r1_ohm": R1_OHM,
        "ocv_offset_v": 0.0,
        "r_total_k_per_w": R_TOTAL_K_PER_W,
    }
    rows: list[dict[str, object]] = []
    for window_s, tier_id in zip(WINDOWS_S, TIER_IDS, strict=False):
        limits = _window_limits(
            z0, v_p0, direction, window_s, ambient_c, **base_kwargs
        )
        rows.append(
            _tier_row(
                tier_id,
                window_s,
                limits,
                z0,
                v_p0,
                direction,
                sign,
                v_min_v=v_min_v,
                v_max_v=v_max_v,
                z_min=z_min,
                z_max=z_max,
            )
        )
    # 持续档：无窗口、SOC 墙不适用，其余三条照取最弱环。
    sustained_limits = _window_limits(
        z0, v_p0, direction, None, ambient_c, **base_kwargs
    )
    rows.append(
        _tier_row(
            SUSTAINED_TIER_ID,
            None,
            sustained_limits,
            z0,
            v_p0,
            direction,
            sign,
            v_min_v=v_min_v,
            v_max_v=v_max_v,
            z_min=z_min,
            z_max=z_max,
        )
    )
    return rows


def _tier_row(
    tier_id: str,
    window_s: float | None,
    limits: dict[str, float | None],
    z0: float,
    v_p0: float,
    direction: str,
    sign: float,
    *,
    v_min_v: float,
    v_max_v: float,
    z_min: float,
    z_max: float,
) -> dict[str, object]:
    """把四条上限合成一档：最弱环、余量、窗末端电压与端口功率。"""
    binding = ""
    allowed = math.inf
    for name in ("voltage", "soc", "thermal", "hardware"):
        value = limits[name]
        if value is not None and value < allowed:
            binding, allowed = name, value
    if not binding:
        raise ValueError("四条上限全不适用：无法给出许可")
    margins: dict[str, float | None] = {}
    for name, value in limits.items():
        margins[name] = None if value is None else round(value - allowed, 4)
    signed_a = sign * allowed
    if window_s is None:
        # 持续档：端电压取稳态值（极化稳定后），min/max 取两个端点的极值。
        ocv = ocv_v(z0)
        v_steady = ocv - sign * allowed * (R0_OHM + R1_OHM) * 1.0
        v_apply = ocv - sign * allowed * R0_OHM - v_p0
        v_end = v_steady
        v_min = min(v_steady, v_apply)
        v_max = max(v_steady, v_apply)
        soc_end_pp = None
        soc_margin_pp = None
    else:
        sim = simulate_constant(z0, v_p0, signed_a, window_s)
        v_end = _num(sim["v_end_v"])
        v_min = _num(sim["v_min_v"])
        v_max = _num(sim["v_max_v"])
        z_end = _num(sim["z_end"])
        soc_end_pp = round(z_end * 100.0, 4)
        if direction == "discharge":
            soc_margin_pp = round((z_end - z_min) * 100.0, 4)
        else:
            soc_margin_pp = round((z_max - z_end) * 100.0, 4)
        # 全程核对：允许电流必须真的留在电压边界内（不是只在窗末成立）。
        # allowed == 0 时当前状态本身可能已越界（无任何正许可），此时不核对。
        limit_hi = v_max_v + 1e-6
        limit_lo = v_min_v - 1e-6
        if allowed > 0.0 and (v_min < limit_lo or v_max > limit_hi):
            raise AssertionError(
                f"{tier_id} 档电压越界：min {v_min:.9f} / max {v_max:.9f}"
            )
    return {
        "tier_id": tier_id,
        "window_s": window_s,
        "limits_a": {name: (None if value is None else round(value, 4)) for name, value in limits.items()},
        "allowed_a": round(allowed, 4),
        "signed_a": round(signed_a, 4),
        "binding_constraint": binding,
        "margins_a": margins,
        "soc_end_pp": soc_end_pp,
        "soc_margin_pp": soc_margin_pp,
        "v_end_v": round(v_end, 6),
        "v_min_v": round(v_min, 6),
        "v_max_v": round(v_max, 6),
        "power_w": round(v_end * signed_a, 4),
    }


def _tier(tiers: list[dict[str, object]], tier_id: str) -> dict[str, object]:
    for row in tiers:
        if row["tier_id"] == tier_id:
            return row
    raise KeyError(f"没有 {tier_id} 档")


def _tier_allowed(tiers: list[dict[str, object]]) -> dict[str, float]:
    return {str(row["tier_id"]): _num(row["allowed_a"]) for row in tiers}


def _tier_binding(tiers: list[dict[str, object]]) -> dict[str, str]:
    return {str(row["tier_id"]): str(row["binding_constraint"]) for row in tiers}


def _corner_values(scale: float) -> dict[str, float]:
    """声明不确定度的最坏角点；scale 是教学倍率（0 = 名义，1 = 声明值）。"""
    return {
        "r0": R0_OHM * (1.0 + R0_UNCERTAINTY_PCT / 100.0 * scale),
        "r1": R1_OHM * (1.0 + R1_UNCERTAINTY_PCT / 100.0 * scale),
        "q": Q_AH * (1.0 - Q_UNCERTAINTY_PCT / 100.0 * scale),
        "r_total": R_TOTAL_K_PER_W
        * (1.0 + R_TOTAL_UNCERTAINTY_PCT / 100.0 * scale),
    }


def _uncertainty_parameters(scale: float) -> dict[str, object]:
    return {
        "r0_pct": R0_UNCERTAINTY_PCT,
        "r1_pct": R1_UNCERTAINTY_PCT,
        "q_pct": Q_UNCERTAINTY_PCT,
        "r_total_pct": R_TOTAL_UNCERTAINTY_PCT,
        "ocv_mv": OCV_UNCERTAINTY_MV,
        "scale": scale,
        "corner_rule": (
            "电压墙：R0/R1 取高角点，放电 OCV 取低角点、充电取高角点；"
            "SOC 墙：Q 取低角点；热墙：R_total 取高角点；电流帽精确、无不确定度"
        ),
    }


def _nominal_limits(row: dict[str, object]) -> dict[str, float | None]:
    raw = row["limits_a"]
    if not isinstance(raw, dict):
        raise TypeError("tier 行缺少 limits_a")
    limits: dict[str, float | None] = {}
    for name in ("voltage", "soc", "thermal", "hardware"):
        value = raw.get(name)
        limits[name] = None if value is None else _num(value)
    return limits


def _tier_window(row: dict[str, object]) -> float | None:
    raw = row["window_s"]
    if isinstance(raw, (int, float)):
        return float(raw)
    return None


def uncertainty_report(
    z0: float,
    v_p0: float = 0.0,
    direction: str = "discharge",
    ambient_c: float = AMBIENT_C,
    *,
    scale: float = 1.0,
    hardware_a: float | None = None,
    v_min_v: float = V_MIN_V,
    v_max_v: float = V_MAX_V,
    z_min: float = Z_MIN,
    z_max: float = Z_MAX,
) -> dict[str, object]:
    """参数不确定性的缩限口径：每个上限在自己的最坏角点评估，再取最弱环。

    声明的不确定度（教学值）见 R0/R1/Q/R_total/OCV 常量。收缩只向紧的方向：
    电压墙用高 R0/R1 与最不利 OCV 偏移，SOC 墙用低 Q，热墙用高 R_total；
    绝不把不确定度取平均，也不把「标称许可」原样当成「保证许可」。

    scale 是可审计的倍率：0 时角点回到名义值（收缩为 0），1 是声明值，越大越紧。
    每个上限对自身角点的单调性保证 uncertain_a 对 scale 单调不增。
    """
    if not math.isfinite(scale) or scale < 0.0:
        raise ValueError(f"不确定度倍率必须是非负有限数，收到 {scale!r}")
    sign = _direction_sign(direction)
    if hardware_a is None:
        hardware_a = I_MAX_DISCHARGE_A if sign > 0.0 else I_MAX_CHARGE_A
    if not math.isfinite(hardware_a) or hardware_a <= 0.0:
        raise ValueError(f"电流帽必须是正的有限数，收到 {hardware_a!r}")
    corners = _corner_values(scale)
    if corners["q"] <= 0.0:
        raise ValueError("不确定度倍率过大：容量角点非正")
    # 电压墙的最不利 OCV 偏移：放电向下、充电向上
    ocv_offset_v = -sign * OCV_UNCERTAINTY_MV / 1000.0 * scale
    nominal_tiers = sop_tiers(
        z0,
        v_p0,
        direction,
        ambient_c,
        hardware_a=hardware_a,
        v_min_v=v_min_v,
        v_max_v=v_max_v,
        z_min=z_min,
        z_max=z_max,
    )
    rows: list[dict[str, object]] = []
    for nominal_row in nominal_tiers:
        tier_id = str(nominal_row["tier_id"])
        window_s = _tier_window(nominal_row)
        nominal_a = _num(nominal_row["allowed_a"])
        nominal_limits = _nominal_limits(nominal_row)
        common = {
            "hardware_a": hardware_a,
            "v_min_v": v_min_v,
            "v_max_v": v_max_v,
            "z_min": z_min,
            "z_max": z_max,
        }
        worst = _window_limits(
            z0,
            v_p0,
            direction,
            window_s,
            ambient_c,
            q_ah=corners["q"],
            r0_ohm=corners["r0"],
            r1_ohm=corners["r1"],
            ocv_offset_v=ocv_offset_v,
            r_total_k_per_w=corners["r_total"],
            **common,
        )
        uncertain_a = round(_allowed_from(worst), 4)
        binding = ""
        binding_value = math.inf
        for name in ("voltage", "soc", "thermal", "hardware"):
            value = worst[name]
            if value is not None and value < binding_value:
                binding, binding_value = name, value
        singles: dict[str, float] = {}
        for name in UNCERTAINTY_CORNER_ORDER:
            if name == "q":
                limits = dict(nominal_limits)
                limits["soc"] = (
                    None
                    if window_s is None
                    else soc_window_limit_a(
                        z0,
                        direction,
                        window_s,
                        z_min=z_min,
                        z_max=z_max,
                        q_ah=corners["q"],
                    )
                )
                single_allowed = _allowed_from(limits)
            elif name == "r_total":
                limits = dict(nominal_limits)
                limits["thermal"] = thermal_sustained_a(
                    ambient_c, r_total_k_per_w=corners["r_total"]
                )
                single_allowed = _allowed_from(limits)
            else:
                single = _window_limits(
                    z0,
                    v_p0,
                    direction,
                    window_s,
                    ambient_c,
                    q_ah=Q_AH,
                    r0_ohm=corners["r0"] if name == "r0" else R0_OHM,
                    r1_ohm=corners["r1"] if name == "r1" else R1_OHM,
                    ocv_offset_v=ocv_offset_v if name == "ocv" else 0.0,
                    r_total_k_per_w=R_TOTAL_K_PER_W,
                    **common,
                )
                single_allowed = _allowed_from(single)
            singles[name] = round(nominal_a - round(single_allowed, 4), 4)
        dominant = "none"
        dominant_shrink = 0.0
        for name in UNCERTAINTY_CORNER_ORDER:
            if singles[name] > dominant_shrink + 1e-12:
                dominant, dominant_shrink = name, singles[name]
        rows.append(
            {
                "tier_id": tier_id,
                "window_s": window_s,
                "nominal_a": round(nominal_a, 4),
                "uncertain_a": uncertain_a,
                "shrink_a": round(nominal_a - uncertain_a, 4),
                "shrink_pct_of_nominal": (
                    round((nominal_a - uncertain_a) / nominal_a * 100.0, 4)
                    if nominal_a > 0.0
                    else None
                ),
                "nominal_binding": str(nominal_row["binding_constraint"]),
                "uncertain_binding": binding,
                "dominant_parameter": dominant,
                "joint_extra_a": round(
                    (nominal_a - uncertain_a) - dominant_shrink, 4
                ),
                "per_parameter_shrink_a": singles,
            }
        )
    return {
        "parameters": _uncertainty_parameters(scale),
        "tiers": rows,
    }


def _uncertainty_operating_point(
    op_id: str,
    soc: float,
    direction: str,
    ambient_c: float,
) -> dict[str, object]:
    report = uncertainty_report(soc, 0.0, direction, ambient_c)
    return {
        "id": op_id,
        "direction": direction,
        "soc": soc,
        "ambient_c": ambient_c,
        "tiers": report["tiers"],
    }


def _operating_point(
    op_id: str,
    soc: float,
    direction: str,
    ambient_c: float,
    tiers: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "id": op_id,
        "direction": direction,
        "soc": soc,
        "v_p0_v": 0.0,
        "ambient_c": ambient_c,
        "tiers": tiers,
    }


@lru_cache(maxsize=1)
def _operating_points() -> list[dict[str, object]]:
    """三个冻结工作点：高 SOC 放电、低 SOC 放电、中 SOC 充电。"""
    return [
        _operating_point(
            "discharge_high_soc", 0.90, "discharge", AMBIENT_C,
            sop_tiers(0.90, 0.0, "discharge", AMBIENT_C),
        ),
        _operating_point(
            "discharge_low_soc", 0.15, "discharge", AMBIENT_C,
            sop_tiers(0.15, 0.0, "discharge", AMBIENT_C),
        ),
        _operating_point(
            "charge_mid_soc", 0.50, "charge", AMBIENT_C,
            sop_tiers(0.50, 0.0, "charge", AMBIENT_C),
        ),
    ]


@lru_cache(maxsize=1)
def _scenario() -> dict[str, object]:
    """冻结的 D17-sop-window 场景：三个工作点 + 反例 + 温度对照。"""
    high_tiers = sop_tiers(0.90, 0.0, "discharge", AMBIENT_C)
    low_tiers = sop_tiers(0.15, 0.0, "discharge", AMBIENT_C)
    charge_tiers = sop_tiers(0.50, 0.0, "charge", AMBIENT_C)
    hot_tiers = sop_tiers(0.90, 0.0, "discharge", HOT_AMBIENT_C)

    snapshot_high = snapshot_current_a(0.90, 0.0, "discharge")
    # 600 s 档的余量分解：1.12 V 里阻抗吃掉多少、SOC 下降吃掉多少
    limit_600 = window_voltage_limit(
        0.90, 0.0, "discharge", 600.0, hardware_a=I_MAX_DISCHARGE_A
    )
    z_end_600 = 0.90 - limit_600 * 600.0 / (3600.0 * Q_AH)
    ocv_start_600 = ocv_v(0.90)
    ocv_end_600 = ocv_v(z_end_600)
    a600 = math.exp(-600.0 / TAU1_S)
    impedance_drop_600 = limit_600 * R0_OHM + R1_OHM * (1.0 - a600) * limit_600
    ocv_drop_600 = ocv_start_600 - ocv_end_600
    snapshot_low = snapshot_current_a(0.15, 0.0, "discharge")
    window_10s_high = _num(_tier(high_tiers, "10s")["allowed_a"])
    window_60s_high = _num(_tier(high_tiers, "60s")["allowed_a"])
    window_600s_high = _num(_tier(high_tiers, "600s")["allowed_a"])
    window_600s_low = _num(_tier(low_tiers, "600s")["allowed_a"])
    sustained_30 = thermal_sustained_a(30.0)
    sustained_45 = thermal_sustained_a(45.0)
    over_10_pct = (snapshot_high / window_10s_high - 1.0) * 100.0
    over_600_pct = (snapshot_high / window_600s_high - 1.0) * 100.0
    over_low_pct = (snapshot_low / window_600s_low - 1.0) * 100.0

    return {
        "scenario_id": SCENARIO_ID,
        "identity": (
            "teaching multi-constraint SOP window model on a synthetic 3 Ah cell; cell "
            "parameters, voltage/SOC bounds, current caps and the thermal contract are "
            "teaching values — not device measurements, not thermal-simulation "
            "acceptance, not human review"
        ),
        "conventions": {
            "current_sign": "I>0 放电、I<0 充电（新深研约定）；固件 current_ma>0 充电，I_legacy = −I 恰好一次",
            "soc": "z ∈ [0,1]；报告里的 pp = 100·z",
            "power_sign": "power_w = 窗口末端端电压 × 有符号允许电流：放电为正（外送），充电为负（吸收）",
            "window_check": "候选电流为常值，二分用整窗逐拍仿真；窗末电压给功率，全程 min/max 另列",
            "weakest_link": "四条上限都写成电流幅值后取最小；不许取平均，不许先把某项许可翻符号再比较",
        },
        "cell": {
            "q_ah": Q_AH,
            "r0_ohm": R0_OHM,
            "r1_ohm": R1_OHM,
            "c1_f": C1_F,
            "tau1_s": TAU1_S,
            "v_min_v": V_MIN_V,
            "v_max_v": V_MAX_V,
            "z_min": Z_MIN,
            "z_max": Z_MAX,
            "i_max_discharge_a": I_MAX_DISCHARGE_A,
            "i_max_charge_a": I_MAX_CHARGE_A,
        },
        "thermal_contract": {
            "source": "D16 稳态闭式 sqrt((T限−T环境)/(R_total·R_int))",
            "core_limit_c": CORE_LIMIT_C,
            "r_core_case_k_per_w": R_CORE_CASE_K_PER_W,
            "r_case_amb_k_per_w": R_CASE_AMB_K_PER_W,
            "r_total_k_per_w": R_TOTAL_K_PER_W,
            "r_int_ohm": R_INT_OHM,
            "c_th_total_j_per_k": C_TH_TOTAL_J_PER_K,
            "tau_th_s": round(R_TOTAL_K_PER_W * C_TH_TOTAL_J_PER_K, 4),
            "sustained_30c_a": round(sustained_30, 4),
            "sustained_45c_a": round(sustained_45, 4),
            "r1_dissipation_included_a": round(
                math.sqrt(
                    (CORE_LIMIT_C - AMBIENT_C)
                    / (R_TOTAL_K_PER_W * (R0_OHM + R1_OHM))
                ),
                4,
            ),
            "window_scope": (
                "热墙是稳态持续电流，对每个窗口档同样适用；瞬态峰值余量不在本闭式承诺内"
            ),
        },
        "operating_points": _operating_points(),
        "counterexample_snapshot_vs_window": {
            "claim": "单快照 Rint 闭式只除一条代数式：看不见 RC 积累、OCV 随 SOC 下降、热与 SOC 墙",
            "high_soc": {
                "soc": 0.90,
                "snapshot_a": round(snapshot_high, 4),
                "window_10s_a": round(window_10s_high, 4),
                "binding_10s": _tier_binding(high_tiers)["10s"],
                "window_60s_a": round(window_60s_high, 4),
                "binding_60s": _tier_binding(high_tiers)["60s"],
                "window_600s_a": round(window_600s_high, 4),
                "binding_600s": _tier_binding(high_tiers)["600s"],
                "overstatement_10s_pct": round(over_10_pct, 4),
                "overstatement_600s_pct": round(over_600_pct, 4),
            },
            "high_soc_600s_decomposition": {
                "ocv_start_v": round(ocv_start_600, 4),
                "ocv_end_v": round(ocv_end_600, 4),
                "ocv_drop_v": round(ocv_drop_600, 4),
                "impedance_drop_v": round(impedance_drop_600, 4),
                "headroom_v": round(ocv_start_600 - V_MIN_V, 4),
                "rc_share_of_r0_at_60s_pct": round(
                    R1_OHM * (1.0 - math.exp(-60.0 / TAU1_S)) / R0_OHM * 100.0, 4
                ),
            },
            "low_soc": {
                "soc": 0.15,
                "snapshot_a": round(snapshot_low, 4),
                "window_600s_a": round(window_600s_low, 4),
                "binding_600s": _tier_binding(low_tiers)["600s"],
                "overstatement_600s_pct": round(over_low_pct, 4),
            },
        },
        "temperature_derating": {
            "ambient_30_c": {
                "sustained_a": round(sustained_30, 4),
                "tiers_a": _tier_allowed(high_tiers),
            },
            "ambient_45_c": {
                "sustained_a": round(sustained_45, 4),
                "tiers_a": _tier_allowed(hot_tiers),
            },
            "drop_pct": {
                "thermal_bound_tiers": round(
                    (1.0 - sustained_45 / sustained_30) * 100.0, 2
                ),
                "600s": round(
                    (1.0 - _num(_tier(hot_tiers, "600s")["allowed_a"]) / window_600s_high)
                    * 100.0,
                    2,
                ),
            },
            "binding_45_c": _tier_binding(hot_tiers),
            "note": (
                "温度只移动热墙在限的档位；R0/R1 在本模型不随温度变化（教学边界），"
                "真实电芯升温会同时推高内阻，电压墙也会收紧"
            ),
        },
        "uncertainty": {
            "method": (
                "每条上限只在自己的最坏角点评估（电压墙 R0/R1 高 + 最不利 OCV、"
                "SOC 墙 Q 低、热墙 R_total 高），再取最弱环；不确定度不取平均"
            ),
            "parameters": _uncertainty_parameters(1.0),
            "operating_points": [
                _uncertainty_operating_point(
                    "discharge_high_soc", 0.90, "discharge", AMBIENT_C
                ),
                _uncertainty_operating_point(
                    "discharge_low_soc", 0.15, "discharge", AMBIENT_C
                ),
                _uncertainty_operating_point(
                    "charge_mid_soc", 0.50, "charge", AMBIENT_C
                ),
            ],
            "dominant_rule": (
                "逐参数单独施加角点、其余保持名义，取收缩量最大者为该档主导参数；"
                "joint_extra_a 是联合角点比单参数最坏还多收缩的部分（非线性交互）"
            ),
            "monotone_rule": (
                "scale 越大，每档 uncertain_a 越小或不变（shrink_a 非负且不减）；"
                "scale=0 时角点回到名义值，收缩为 0"
            ),
            "teaching_point": (
                "不确定性把许可往紧的方向推，不是把上下限平均；同一档里收缩最多的"
                "参数就是该档的主导不确定度——先替换它，比笼统说「参数有误差」有用"
            ),
        },
        "charge_interface": {
            "consumer": "D18（充电许可）",
            "rule": "I_permit = min(充电器能力, 温度充电地图限值, SOP 窗口充电限值)",
            "sop_window_charge_a": _tier_allowed(charge_tiers),
            "sop_window_binding": _tier_binding(charge_tiers),
            "not_included": (
                "温度充电地图与析锂边界不在本单元建模；低温/高 SOC 的许可必须由 D18 的"
                "地图给出，不能把本单元 30 °C 的数值外推"
            ),
        },
        "conclusion": (
            f"每个窗口档取四条上限的最弱环：热墙把 30 °C 的 10/30/60 s 档压在 "
            f"{sustained_30:.2f} A，600 s 档由电压墙收紧到 {window_600s_high:.2f} A；"
            f"低 SOC 的 600 s 档由 SOC 墙压到 {window_600s_low:.2f} A。单快照闭式"
            f"在同一工况报 {snapshot_high:.2f} A，对 10 s/600 s 窗口分别高估 "
            f"{over_10_pct:.1f}%/{over_600_pct:.1f}%（低 SOC 长窗 {over_low_pct:.1f}%）——"
            "「此刻能放出多大电流」不是 SOP，SOP 是「未来这个窗口内最多允许多大」"
        ),
        "boundaries": {
            "not_device_measurement": "全部电芯与热参数为教学值，不认定为任何器件实测值",
            "not_thermal_acceptance": "热墙是 D16 稳态闭式；不构成热仿真验收，也不承诺瞬态峰值余量",
            "not_human_review": "本报告不替代真人评审、台架验收或整车标定",
            "pack_level": "单节口径；整包最弱单节、连接器与线束压降不在本单元（OS03 接口）",
            "r_temperature": "R0/R1 不随温度与老化变化；SOH 更新路径见 D15 接口",
            "charge_map": "温度充电地图与析锂边界归 D18；本单元只给 SOP 窗口充电限值",
            "firmware": (
                "固件 BmsInputs 只有 cell_mv[]/current_ma/temp_c10/charger_present，没有 SOP "
                "窗口与约束分解字段；本单元不证明固件已实现 SOP 计算或降额策略"
            ),
        },
    }


# --- D17-profile-replay：工况数据合同、逐拍包线审计与能量账 ---

def generate_profile() -> list[dict[str, float]]:
    """内置合成工况：静置 → 6 A 基载 → 静置 → 12 A 过载脉冲 → 静置（10 s 采样）。"""
    frames: list[dict[str, float]] = []
    for t_start, t_end, current in PROFILE_PHASES:
        t = t_start
        while t < t_end - 1e-9:
            frames.append({"t_s": t, "current_a": current})
            t += PROFILE_DT_S
    frames.append({"t_s": PROFILE_PHASES[-1][1], "current_a": 0.0})
    return frames


def write_profile_csv(frames: list[dict[str, float]], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=PROFILE_COLUMNS)
        writer.writeheader()
        for frame in frames:
            writer.writerow({"t_s": frame["t_s"], "current_a": frame["current_a"]})


def load_profile(path: Path) -> list[dict[str, float]]:
    """读取电流剖面，严格执行数据合同：缺文件/错表头/缺列/非有限/时间回退/样本不足一律拒绝。"""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError("表头缺失")
        missing = [name for name in PROFILE_COLUMNS if name not in reader.fieldnames]
        if missing:
            raise ValueError(
                f"缺列 {missing}：表头必须至少包含 {','.join(PROFILE_COLUMNS)}，"
                f"实际 {reader.fieldnames}"
            )
        frames: list[dict[str, float]] = []
        last_t: float | None = None
        for lineno, row in enumerate(reader, start=2):
            if None in row or any(row.get(name) is None for name in PROFILE_COLUMNS):
                raise ValueError(f"第 {lineno} 行列数不足")
            parsed: dict[str, float] = {}
            for name in PROFILE_COLUMNS:
                raw = row[name]
                try:
                    value = float(raw)
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"第 {lineno} 行 {name} 无法解析: {raw!r}") from exc
                if not math.isfinite(value):
                    raise ValueError(f"第 {lineno} 行 {name} 非有限: {raw}")
                parsed[name] = value
            t_s = parsed["t_s"]
            if t_s < 0.0:
                raise ValueError(f"第 {lineno} 行 t_s 为负: {t_s}")
            if last_t is not None and t_s <= last_t:
                raise ValueError(f"第 {lineno} 行 t_s 未严格递增: {t_s} <= {last_t}")
            last_t = t_s
            frames.append({"t_s": t_s, "current_a": parsed["current_a"]})
    if len(frames) < MIN_PROFILE_FRAMES:
        raise ValueError(f"样本不足：{len(frames)} 拍 < 下限 {MIN_PROFILE_FRAMES}")
    return frames


def write_audit_csv(rows: list[dict[str, object]], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=PROFILE_AUDIT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in PROFILE_AUDIT_COLUMNS})


def profile_window_extremes(
    z0: float,
    v_p0: float,
    frames: list[dict[str, float]],
    start_index: int,
    horizon_s: float,
) -> tuple[float, float, float] | None:
    """按剖面实际电流仿真 horizon_s，返回 (窗内 min, 窗内 max, 窗末)。

    与常值候选不同，窗内电流可以换挡/换向：端点不一定是最坏点，这正是
    endpoint_only 审计要抓的漏报。最后一个采样之后按 ZOH 延续末帧电流；
    SOC 越出 [0,1] 返回 None（不可行）。
    """
    z, v_p = z0, v_p0
    v = terminal_voltage(z, v_p, frames[start_index]["current_a"])
    v_min = v_max = v
    remaining = horizon_s
    i = start_index
    while remaining > 1e-9:
        current_a = frames[i]["current_a"]
        if i + 1 < len(frames):
            span = frames[i + 1]["t_s"] - frames[i]["t_s"]
        else:
            span = remaining
        h = min(span, remaining)
        z, v_p = step_state(z, v_p, current_a, h)
        if not 0.0 <= z <= 1.0:
            return None
        v = terminal_voltage(z, v_p, current_a)
        v_min = min(v_min, v)
        v_max = max(v_max, v)
        remaining -= h
        if h >= span - 1e-12:
            i += 1
        if i >= len(frames):
            break
    return v_min, v_max, v


def audit_profile(
    frames: list[dict[str, float]],
    *,
    horizon_s: float = PROFILE_HORIZON_S,
    ambient_c: float = AMBIENT_C,
    soc_start: float = PROFILE_SOC_START,
) -> dict[str, object]:
    """逐拍把实际电流对照「此刻状态 + 60 s 窗口」的 SOP，并记能量账。

    估计器只读 t_s/current_a；SOC 从声明的 soc_start 起按库仑账积分，极化用
    同一 ZOH 精确递推。越限判定用相对容差 PROFILE_LIMIT_TOL_A；`window_violation`
    把该拍电流当常值做整窗仿真，`endpoint_only` 则按剖面实际电流仿真整窗并另取
    窗末值——前者回答「超过许可」，后两者回答「真的越压」与「只查窗末会不会漏」。
    SOC 越出 [0,1] 属于模型适用域之外：拒绝（ValueError），不静默限幅。
    """
    if not frames:
        raise ValueError("工况为空")
    if len(frames) < MIN_PROFILE_FRAMES:
        raise ValueError(f"样本不足：{len(frames)} 拍 < 下限 {MIN_PROFILE_FRAMES}")
    if not math.isfinite(horizon_s) or horizon_s <= 0.0:
        raise ValueError(f"对照窗口必须是正的有限数，收到 {horizon_s!r}")
    z = soc_start
    v_p = 0.0
    rows: list[dict[str, object]] = []
    discharge_ah = 0.0
    charge_ah = 0.0
    energy_wh = 0.0
    peak_discharge = 0.0
    peak_charge = 0.0
    checked = 0
    over_limit = 0
    first_over: float | None = None
    max_exceed = 0.0
    max_exceed_frac = 0.0
    zero_permission = 0
    worst_t: float | None = None
    window_violations = 0
    first_window_violation: float | None = None
    binding_counts = {"voltage": 0, "soc": 0, "thermal": 0, "hardware": 0}
    min_allowed = math.inf
    # endpoint_only 审计：整窗实际剖面 vs 只看窗末
    trajectory_violations = 0
    endpoint_violations = 0
    endpoint_missed_times: list[float] = []

    for index, frame in enumerate(frames):
        t_s = frame["t_s"]
        current_a = frame["current_a"]
        if not 0.0 <= z <= 1.0:
            raise ValueError(
                f"t={t_s} s 时 SOC 越界（{z:.6f}）：该工况超过 Q 的可计账范围，拒绝给能量账"
            )
        allowed: float | None = None
        binding: str | None = None
        exceeded = False
        window_violation = False
        if current_a != 0.0:
            direction = "discharge" if current_a > 0.0 else "charge"
            tiers = sop_tiers(z, v_p, direction, ambient_c)
            row = _tier(tiers, f"{int(horizon_s)}s") if horizon_s in WINDOWS_S else None
            if row is None:
                raise ValueError(f"对照窗口 {horizon_s} s 不在冻结档位 {WINDOWS_S} 内")
            allowed = _num(row["allowed_a"])
            binding = str(row["binding_constraint"])
            magnitude = abs(current_a)
            exceeded = magnitude > allowed + PROFILE_LIMIT_TOL_A
            min_allowed = min(min_allowed, allowed)
            binding_counts[binding] = binding_counts.get(binding, 0) + 1
            checked += 1
            if exceeded:
                over_limit += 1
                if first_over is None:
                    first_over = t_s
                excess = magnitude - allowed
                if excess > max_exceed:
                    max_exceed = excess
                    worst_t = t_s
                if allowed > 0.0:
                    max_exceed_frac = max(max_exceed_frac, excess / allowed)
                else:
                    zero_permission += 1
            ext = _window_extremes(z, v_p, current_a, horizon_s)
            if ext is None:
                window_violation = True
            else:
                v_min, v_max, _ = ext
                window_violation = v_min < V_MIN_V - 1e-6 or v_max > V_MAX_V + 1e-6
            if window_violation:
                window_violations += 1
                if first_window_violation is None:
                    first_window_violation = t_s
        # 两个口径同时算：整窗实际剖面 min/max，与只看窗末的端点值。
        traj = profile_window_extremes(z, v_p, frames, index, horizon_s)
        trajectory_min: float | None
        trajectory_max: float | None
        endpoint_v: float | None
        if traj is None:
            trajectory_min = trajectory_max = endpoint_v = None
            trajectory_violation = True
            endpoint_violation = True
        else:
            trajectory_min, trajectory_max, endpoint_v = traj
            trajectory_violation = (
                trajectory_min < V_MIN_V - 1e-6 or trajectory_max > V_MAX_V + 1e-6
            )
            endpoint_violation = endpoint_v < V_MIN_V - 1e-6 or endpoint_v > V_MAX_V + 1e-6
        endpoint_missed = trajectory_violation and not endpoint_violation
        if trajectory_violation:
            trajectory_violations += 1
        if endpoint_violation:
            endpoint_violations += 1
        if endpoint_missed:
            endpoint_missed_times.append(t_s)
        rows.append(
            {
                "t_s": t_s,
                "current_a": current_a,
                "soc_pp": round(z * 100.0, 4),
                "allowed_a": None if allowed is None else round(allowed, 4),
                "binding": binding,
                "exceeded": exceeded,
                "window_violation": window_violation,
                "trajectory_min_v": (
                    None if trajectory_min is None else round(trajectory_min, 6)
                ),
                "trajectory_max_v": (
                    None if trajectory_max is None else round(trajectory_max, 6)
                ),
                "endpoint_v": None if endpoint_v is None else round(endpoint_v, 6),
                "endpoint_only_violation": endpoint_violation,
                "endpoint_missed": endpoint_missed,
            }
        )
        peak_discharge = max(peak_discharge, current_a)
        peak_charge = min(peak_charge, current_a)
        if index + 1 < len(frames):
            nxt = frames[index + 1]
            dt = nxt["t_s"] - t_s
            if not math.isfinite(dt) or dt <= 0.0:
                raise ValueError(f"第 {index + 2} 拍时间未递增：{nxt['t_s']}")
            v_now = terminal_voltage(z, v_p, current_a)
            energy_wh += v_now * current_a * dt / 3600.0
            if current_a > 0.0:
                discharge_ah += current_a * dt / 3600.0
            else:
                charge_ah += -current_a * dt / 3600.0
            z, v_p = step_state(z, v_p, current_a, dt)
    if min_allowed is math.inf:
        min_allowed = 0.0
    verdict = (
        f"{checked} 个带载拍里有 {over_limit} 拍超过 {horizon_s:g} s 窗口 SOP，"
        f"最大超出 {max_exceed:.2f} A（{max_exceed_frac * 100.0:.1f}%）；"
        f"整窗仿真确认 {window_violations} 拍真越压"
    )
    return {
        "scenario_id": PROFILE_SCENARIO_ID,
        "identity": (
            "synthetic teaching current profile replayed against the D17 60 s SOP envelope; "
            "not a device measurement, not a charger log"
        ),
        "frames": len(frames),
        "duration_s": round(frames[-1]["t_s"] - frames[0]["t_s"], 6),
        "horizon_s": horizon_s,
        "initial_soc_pp": round(soc_start * 100.0, 4),
        "soc_end_pp": round(z * 100.0, 4),
        "discharge_ah": round(discharge_ah, 6),
        "charge_ah": round(charge_ah, 6),
        "net_ah": round(discharge_ah - charge_ah, 6),
        "energy_wh": round(energy_wh, 6),
        "peak_discharge_a": round(peak_discharge, 6),
        "peak_charge_a": round(peak_charge, 6),
        "envelope": {
            "checked_frames": checked,
            "over_limit_frames": over_limit,
            "first_over_limit_t_s": first_over,
            "max_exceedance_a": round(max_exceed, 6),
            "max_exceedance_frac": round(max_exceed_frac, 6),
            "worst_t_s": worst_t,
            "window_violation_frames": window_violations,
            "first_window_violation_t_s": first_window_violation,
            "binding_counts": binding_counts,
            "min_allowed_a": round(min_allowed, 4),
            "zero_permission_frames": zero_permission,
            "tolerance_a": PROFILE_LIMIT_TOL_A,
        },
        "endpoint_only": {
            "horizon_s": horizon_s,
            "trajectory_violation_frames": trajectory_violations,
            "endpoint_violation_frames": endpoint_violations,
            "missed_frames": len(endpoint_missed_times),
            "first_missed_t_s": (
                endpoint_missed_times[0] if endpoint_missed_times else None
            ),
            "missed_t_s": endpoint_missed_times,
            "voltage_tolerance_v": 1e-6,
            "note": (
                "逐拍同时算「整窗实际剖面 min/max」与「只看窗末」；剖面在窗内换流时"
                "端点不是最坏点，只查窗末会漏报窗内越压。常流窗口两口径一致"
            ),
        },
        "verdict": verdict,
        "rows": rows,
    }


def summarize_replay(result: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in result.items() if key != "rows"}


def write_tiers_csv(operating_points: list[dict[str, object]], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=TIER_CSV_COLUMNS)
        writer.writeheader()
        for op in operating_points:
            tiers = op["tiers"]
            if not isinstance(tiers, list):
                raise TypeError("operating point 缺少 tiers 列表")
            for row in tiers:
                if not isinstance(row, dict):
                    raise TypeError("tier 行必须是字典")
                limits = row["limits_a"]
                if not isinstance(limits, dict):
                    raise TypeError("tier 行缺少 limits_a")
                writer.writerow(
                    {
                        "operating_point": op["id"],
                        "direction": op["direction"],
                        "soc": op["soc"],
                        "ambient_c": op["ambient_c"],
                        "tier_id": row["tier_id"],
                        "window_s": "" if row["window_s"] is None else row["window_s"],
                        "allowed_a": row["allowed_a"],
                        "binding_constraint": row["binding_constraint"],
                        "voltage_a": limits.get("voltage"),
                        "soc_a": "" if limits.get("soc") is None else limits.get("soc"),
                        "thermal_a": limits.get("thermal"),
                        "hardware_a": limits.get("hardware"),
                        "v_end_v": row["v_end_v"],
                        "power_w": row["power_w"],
                    }
                )


def build_report(profile_replay: dict[str, object] | None = None) -> dict[str, object]:
    if profile_replay is None:
        profile_replay = summarize_replay(audit_profile(generate_profile()))
    report = dict(_scenario())
    report["profile_replay"] = profile_replay
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 等工件的目录")
    parser.add_argument(
        "--profile",
        type=Path,
        help=f"电流剖面 CSV（至少 {','.join(PROFILE_COLUMNS)} 两列）；缺省用内置合成工况",
    )
    args = parser.parse_args(argv)

    if args.profile is not None:
        try:
            frames = load_profile(args.profile)
        except (OSError, ValueError) as exc:
            print(f"profile 拒绝：{exc}", file=sys.stderr)
            return 2
    else:
        frames = generate_profile()
    try:
        replay = audit_profile(frames)
        report = build_report(profile_replay=summarize_replay(replay))
    except (OSError, ValueError) as exc:
        print(f"profile 拒绝：{exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        write_tiers_csv(_operating_points(), args.out / "sop_tiers.csv")
        write_profile_csv(frames, args.out / "profile.csv")
        rows = replay.get("rows")
        if not isinstance(rows, list):
            raise TypeError("回放结果缺少逐拍 rows")
        write_audit_csv(rows, args.out / "profile_audit.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
