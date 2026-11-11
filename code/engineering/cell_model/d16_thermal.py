"""Teaching experiments for D16: lumped thermal network and sensor placement.

D16「热模型与测点」的可执行证据模块。三件事：

1. 集总参数热网络（电芯 → 壳体/散热器 → 环境，两节点 = 两条 RC）；
2. 测点选择：NTC 贴在何处、测到的为什么是壳温而不是芯温、测点滞后与
   保护阈值的关系（与 D08 时间预算的接口）；
3. 热参数（R_th/C_th）的辨识数据要求与留出验证。

教学身份：全部热参数（R_th、C_th、芯温上限、壳温阈值、NTC 时间常数与热
分压）都是教学值，用于展示「壳温测点看不见芯温」的结构性偏差；它们不认定为
任何器件实测值、热仿真验收结论或真人评审结论。真实 R_th/C_th 必须按本模块
声明的辨识合同从实测数据取得（B05 数据身份纪律）。

边界（必须与正文同页）：固件 `BmsInputs`（code/firmware/bms.h）只有一个
`temp_c10`、无时间戳、无质量位、无测点身份字段——固件层面既无法区分
「传感器滞后」与「热惯性」，也无法同时携带壳温/芯温两条链；本模块的两节点
模型与多测点对比是教学补全，不证明固件已实现热状态估计。
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

SCENARIO_ID = "D16-thermal"
DATA_SCENARIO_ID = "D16-thermal-identification"

# --- 两节点热网络（教学值：电芯 = 芯节点，壳体/散热器 = 壳节点，环境 = 边界）---
R_INT_OHM = 0.09             # 老化后直流内阻（D15 接口），发热全部落在芯节点
C_CORE_J_PER_K = 36.0        # 芯（卷芯 + 极耳）热容
R_CORE_CASE_K_PER_W = 3.0    # 芯 → 壳 传导热阻
C_CASE_J_PER_K = 120.0       # 壳体/散热器热容
R_CASE_AMB_K_PER_W = 2.5     # 壳 → 环境 对流热阻
R_TOTAL_K_PER_W = R_CORE_CASE_K_PER_W + R_CASE_AMB_K_PER_W
AMBIENT_C = 30.0
CORE_LIMIT_C = 70.0          # 芯温保护限（教学值）
CASE_OT_C = 60.0             # 壳温 OT 阈值（对应固件 ot_c10 = 600）
DT_S = 1.0                   # 仿真步长（远小于最快模态，见 modes()）

# 测点候选：名字 → (NTC 自身一阶时间常数 τ_s, 热分压系数)。
# 热分压系数 < 1 表示测点与电芯之间隔了 PCB 铜箔/空气，只看到壳温升的一部分。
SENSOR_PLACEMENTS: dict[str, tuple[float, float]] = {
    "tab_bonded": (10.0, 1.0),     # 极耳根部：贴得最近
    "case_side": (45.0, 0.92),     # 壳侧：典型贴装
    "pcb_remote": (120.0, 0.45),   # PCB 远端：本单元的反例测点
}

# 工况：(t_start_s, t_end_s, current_a, 角色名)。电流 >0 放电；发热不区分方向。
PHASES: list[tuple[float, float, float, str]] = [
    (0.0, 300.0, 0.0, "settle"),
    (300.0, 1800.0, 10.0, "silent_10a"),
    (1800.0, 2700.0, 13.0, "overload_13a"),
    (2700.0, 3300.0, 0.0, "cool_down"),
]

SILENT_PHASE = (300.0, 1799.0)
STEP_TIME_S = 1800.0
SHORT_WINDOW_S = 200.0   # 短窗辨识：只看阶跃前 200 s（约 2.6 个快模态）

# D08 冻结的最坏反应窗（d08_protection_timing.py：相位 + 确认 + 判决 + 执行 + 调度），
# 只覆盖电气链；拿它当 OT 的总预算会低估热链路的秒–分钟级惯性。
D08_WORST_WINDOW_MS = 72.263

# 辨识数据合同（load_identification 强制执行）
IDENT_COLUMNS = ["t_s", "q_w", "t_case_c", "t_ntc_c", "t_core_c", "ambient_c"]
IDENT_Q_TOLERANCE = 0.01     # 辨识窗内发热功率必须恒定（1%）
IDENT_MAX_GAP_S = 60.0       # 最大采样间隔：超过即拒（数据要求，不是提示）
IDENT_MIN_SAMPLES = 20
# τ 网格：5 s → 5102 s（1.02 倍步进）。命中上沿要报告「边界」，不得当成估计值。
TAU_GRID = [5.0 * (1.02**i) for i in range(351)]
LOG_COLUMNS = [
    "t_s", "current_a", "q_w", "core_c", "case_c",
    "ntc_tab_bonded_c", "ntc_case_side_c", "ntc_pcb_remote_c",
]


def _num(value: object) -> float:
    """从 report 字典里取回数值（pyright 友好，同时是运行时契约检查）。"""
    if not isinstance(value, (int, float)):
        raise TypeError(f"期望数值，得到 {type(value).__name__}")
    return float(value)


def heat_w(current_a: float, r_int_ohm: float = R_INT_OHM) -> float:
    """焦耳热：P = I²·R。教学口径里全部发热进芯节点（忽略熵热与均流）。"""
    if r_int_ohm <= 0:
        raise ValueError("内阻必须为正")
    return current_a * current_a * r_int_ohm


def _network_matrix() -> list[list[float]]:
    g_cs = 1.0 / R_CORE_CASE_K_PER_W
    g_sa = 1.0 / R_CASE_AMB_K_PER_W
    return [
        [-g_cs / C_CORE_J_PER_K, g_cs / C_CORE_J_PER_K],
        [g_cs / C_CASE_J_PER_K, -(g_cs + g_sa) / C_CASE_J_PER_K],
    ]


def _solve2(a: list[list[float]], b: list[float]) -> list[float]:
    det = a[0][0] * a[1][1] - a[0][1] * a[1][0]
    if abs(det) < 1e-15:
        raise ValueError("热网络矩阵退化")
    return [
        (b[0] * a[1][1] - a[0][1] * b[1]) / det,
        (a[0][0] * b[1] - b[0] * a[1][0]) / det,
    ]


def _expm2(a: list[list[float]], t: float) -> list[list[float]]:
    """2×2 实矩阵指数：exp(σt)[cosh(θt)I + sinh(θt)/θ·(A−σI)]。"""
    sigma = 0.5 * (a[0][0] + a[1][1])
    det = a[0][0] * a[1][1] - a[0][1] * a[1][0]
    theta = math.sqrt(max(sigma * sigma - det, 0.0))
    exp_s = math.exp(sigma * t)
    if theta < 1e-12:
        return [[exp_s, 0.0], [0.0, exp_s]]
    sh = math.sinh(theta * t) / theta
    ch = math.cosh(theta * t)
    return [
        [exp_s * (ch + (a[0][0] - sigma) * sh), exp_s * a[0][1] * sh],
        [exp_s * a[1][0] * sh, exp_s * (ch + (a[1][1] - sigma) * sh)],
    ]


def step_network(
    core_c: float, case_c: float, q_w: float, ambient_c: float, dt_s: float = DT_S
) -> tuple[float, float]:
    """零阶保持精确一步：先解稳态，再让偏差按 exp(A·dt) 衰减。"""
    if dt_s <= 0:
        raise ValueError("步长必须为正")
    a = _network_matrix()
    g_sa = 1.0 / R_CASE_AMB_K_PER_W
    b = [q_w / C_CORE_J_PER_K, ambient_c * g_sa / C_CASE_J_PER_K]
    x_ss = _solve2(a, [-b[0], -b[1]])
    phi = _expm2(a, dt_s)
    d0 = core_c - x_ss[0]
    d1 = case_c - x_ss[1]
    return (
        x_ss[0] + phi[0][0] * d0 + phi[0][1] * d1,
        x_ss[1] + phi[1][0] * d0 + phi[1][1] * d1,
    )


def steady_state(i_a: float, ambient_c: float = AMBIENT_C) -> dict[str, float]:
    """稳态闭式：芯-壳梯度 = P·R_cs，总升 = P·(R_cs + R_sa)。"""
    p_w = heat_w(i_a)
    gap_k = p_w * R_CORE_CASE_K_PER_W
    rise_k = p_w * R_TOTAL_K_PER_W
    return {
        "current_a": i_a,
        "power_w": p_w,
        "core_case_gap_k": gap_k,
        "total_rise_k": rise_k,
        "core_c": ambient_c + rise_k,
        "case_c": ambient_c + p_w * R_CASE_AMB_K_PER_W,
    }


def modes() -> dict[str, float]:
    """两节点网络的两个模态时间常数（特征值的负倒数）。"""
    a = _network_matrix()
    sigma = 0.5 * (a[0][0] + a[1][1])
    det = a[0][0] * a[1][1] - a[0][1] * a[1][0]
    theta = math.sqrt(max(sigma * sigma - det, 0.0))
    return {
        "tau_fast_s": -1.0 / (sigma - theta),
        "tau_slow_s": -1.0 / (sigma + theta),
        "tau_fast_analytic_s": C_CORE_J_PER_K * R_CORE_CASE_K_PER_W,
    }


def silent_band(ambient_c: float = AMBIENT_C) -> dict[str, float]:
    """「芯温超限而壳温未越阈」的电流带。

    下沿：稳态芯温刚好到芯限（P = (限−环境)/(R_cs+R_sa)）；
    上沿：稳态壳温刚好到壳阈（P = (阈−环境)/R_sa）——低于它壳温永不越阈。
    上沿处壳温越阈瞬间的芯温 = 阈 + P·R_cs（准稳态）。
    """
    p_low = (CORE_LIMIT_C - ambient_c) / R_TOTAL_K_PER_W
    p_high = (CASE_OT_C - ambient_c) / R_CASE_AMB_K_PER_W
    if p_low <= 0 or p_high <= 0:
        raise ValueError("环境温度已高于限值，沉默带无定义")
    if p_high <= p_low:
        raise ValueError("阈值组合下不存在沉默带（壳阈先到）")
    return {
        "ambient_c": ambient_c,
        "power_low_w": p_low,
        "power_high_w": p_high,
        "current_low_a": math.sqrt(p_low / R_INT_OHM),
        "current_high_a": math.sqrt(p_high / R_INT_OHM),
        "core_at_case_trip_c": CASE_OT_C + p_high * R_CORE_CASE_K_PER_W,
        "gap_at_case_trip_k": p_high * R_CORE_CASE_K_PER_W,
    }


def sop_sustained_current_a(ambient_c: float) -> float:
    """D17 接口：稳态芯温不越限的持续电流 I = √((限−环境)/((R_cs+R_sa)·R_int))。"""
    if ambient_c >= CORE_LIMIT_C:
        raise ValueError("环境温度已到芯限，SOP 为零")
    return math.sqrt((CORE_LIMIT_C - ambient_c) / (R_TOTAL_K_PER_W * R_INT_OHM))


def sensor_step(
    reading_c: float,
    case_c: float,
    ambient_c: float,
    placement: str,
    dt_s: float = DT_S,
    placements: dict[str, tuple[float, float]] | None = None,
) -> float:
    """测点一步更新：先按热分压取目标温度，再走 NTC 自身一阶惯性。"""
    table = SENSOR_PLACEMENTS if placements is None else placements
    if placement not in table:
        raise ValueError(f"未知测点: {placement}")
    tau_s, gain = table[placement]
    target_c = ambient_c + gain * (case_c - ambient_c)
    return target_c + (reading_c - target_c) * math.exp(-dt_s / tau_s)


def simulate(
    phases: list[tuple[float, float, float, str]] | None = None,
    ambient_c: float = AMBIENT_C,
    dt_s: float = DT_S,
    placements: dict[str, tuple[float, float]] | None = None,
) -> list[dict[str, float]]:
    """按工况分段积分两节点网络，并同步推进各测点的读数。"""
    if phases is None:
        phases = PHASES
    sensors = SENSOR_PLACEMENTS if placements is None else placements
    core_c = ambient_c
    case_c = ambient_c
    readings = {name: ambient_c for name in sensors}
    frames: list[dict[str, float]] = []
    for t_start, t_end, i_a, _role in phases:
        t = t_start
        # 半开区间 [start, end)：每拍只属于一个工况，阶跃时刻落在下一段的首帧。
        while t < t_end - 1e-9:
            q_w = heat_w(i_a)
            frame: dict[str, float] = {
                "t_s": t,
                "current_a": i_a,
                "q_w": q_w,
                "core_c": core_c,
                "case_c": case_c,
                "ambient_c": ambient_c,
            }
            for name in sensors:
                readings[name] = sensor_step(readings[name], case_c, ambient_c, name, dt_s, sensors)
                frame[f"ntc_{name}_c"] = readings[name]
            frames.append(frame)
            core_c, case_c = step_network(core_c, case_c, q_w, ambient_c, dt_s)
            t += dt_s
    return frames


def _first_crossing(
    frames: list[dict[str, float]], key: str, threshold_c: float
) -> dict[str, float] | None:
    for frame in frames:
        if frame[key] >= threshold_c:
            return frame
    return None


def sensor_metrics(frames: list[dict[str, float]]) -> dict[str, object]:
    """各测点的读数质量：越阈时刻、峰值、以及在芯限穿越瞬间的欠估。"""
    core_trip = _first_crossing(frames, "core_c", CORE_LIMIT_C)
    sensors: dict[str, dict[str, object]] = {}
    for name in SENSOR_PLACEMENTS:
        key = f"ntc_{name}_c"
        peak_frame = max(frames, key=lambda f: f[key])
        trip = _first_crossing(frames, key, CASE_OT_C)
        row: dict[str, object] = {
            "tau_s": SENSOR_PLACEMENTS[name][0],
            "gain": SENSOR_PLACEMENTS[name][1],
            "peak_c": round(peak_frame[key], 4),
            "peak_underestimate_k": round(peak_frame["core_c"] - peak_frame[key], 4),
            "detect_s": None if trip is None else round(trip["t_s"], 4),
        }
        if core_trip is not None:
            row["reading_at_core_trip_c"] = round(core_trip[key], 4)
            row["underestimate_at_core_trip_k"] = round(core_trip["core_c"] - core_trip[key], 4)
        sensors[name] = row
    return {
        "core_trip_s": None if core_trip is None else round(core_trip["t_s"], 4),
        "core_peak_c": round(max(f["core_c"] for f in frames), 4),
        "case_peak_c": round(max(f["case_c"] for f in frames), 4),
        "sensors": sensors,
    }


def silent_trip_counterexample(frames: list[dict[str, float]]) -> dict[str, object]:
    """反例 A（结构性）：沉默带工况里芯温越限、三个测点无一越阈。"""
    lo, hi = SILENT_PHASE
    phase = [f for f in frames if lo <= f["t_s"] <= hi]
    core_peak = max(f["core_c"] for f in phase)
    case_peak = max(f["case_c"] for f in phase)
    trips = {
        name: any(f[f"ntc_{name}_c"] >= CASE_OT_C for f in phase)
        for name in SENSOR_PLACEMENTS
    }
    return {
        "phase": "silent_10a",
        "duration_s": round(len(phase) * DT_S, 4),
        "current_a": phase[0]["current_a"],
        "power_w": round(phase[0]["q_w"], 4),
        "core_peak_c": round(core_peak, 4),
        "case_peak_c": round(case_peak, 4),
        "core_limit_c": CORE_LIMIT_C,
        "case_ot_c": CASE_OT_C,
        "core_over_limit_k": round(core_peak - CORE_LIMIT_C, 4),
        "case_margin_k": round(CASE_OT_C - case_peak, 4),
        "any_sensor_tripped": any(trips.values()),
        "sensor_trips": trips,
    }


def step_response(
    frames: list[dict[str, float]], window_s: float = 60.0, t_step_s: float = STEP_TIME_S
) -> dict[str, object]:
    """反例 B（滞后性）：负载阶跃后 window_s 内芯温与各测点各升了多少。"""
    start = next(f for f in frames if f["t_s"] == t_step_s)
    later = next(f for f in frames if f["t_s"] == t_step_s + window_s)
    core_rise = later["core_c"] - start["core_c"]
    sensors: dict[str, dict[str, float]] = {}
    for name in SENSOR_PLACEMENTS:
        key = f"ntc_{name}_c"
        rise = later[key] - start[key]
        sensors[name] = {
            "rise_k": round(rise, 4),
            "fraction_of_core": round(rise / core_rise, 4) if core_rise else 0.0,
        }
    return {
        "t_step_s": t_step_s,
        "window_s": window_s,
        "step_current_a": later["current_a"],
        "core_rise_k": round(core_rise, 4),
        "sensors": sensors,
    }


def placement_improvement(frames: list[dict[str, float]]) -> list[dict[str, object]]:
    """测点位置改进量：以 pcb_remote 为基准比较「芯限穿越瞬间的读数欠估」。"""
    metrics = sensor_metrics(frames)
    sensors = metrics["sensors"]
    if not isinstance(sensors, dict):
        raise TypeError("sensor_metrics 结构异常")
    base = sensors["pcb_remote"]
    if not isinstance(base, dict):
        raise TypeError("sensor_metrics 结构异常")
    base_deficit = _num(base["underestimate_at_core_trip_k"])
    base_detect = base["detect_s"]
    rows: list[dict[str, object]] = []
    for name in ("tab_bonded", "case_side"):
        row = sensors[name]
        if not isinstance(row, dict):
            raise TypeError("sensor_metrics 结构异常")
        detect = row["detect_s"]
        delay_gain: float | None = None
        if isinstance(base_detect, (int, float)) and isinstance(detect, (int, float)):
            delay_gain = round(float(base_detect) - float(detect), 4)
        rows.append(
            {
                "sensor": name,
                "detect_s": detect,
                "detect_since_step_s": (
                    None if not isinstance(detect, (int, float)) else round(float(detect) - STEP_TIME_S, 4)
                ),
                "baseline_detect_s": base_detect,
                "baseline_never_tripped": base_detect is None,
                "detect_gain_s": delay_gain,
                "underestimate_at_core_trip_k": row["underestimate_at_core_trip_k"],
                "baseline_underestimate_at_core_trip_k": base["underestimate_at_core_trip_k"],
                "underestimate_gain_k": round(
                    base_deficit - _num(row["underestimate_at_core_trip_k"]), 4
                ),
            }
        )
    return rows


def divider_vs_lag() -> dict[str, object]:
    """拆开「热分压」与「时间常数」各自的代价：两个只改一个因素的假想测点。"""
    variants = {
        "perfect_divider_slow_ntc": (120.0, 1.0),
        "divider_0_92_fast_ntc": (10.0, 0.92),
    }
    frames = simulate(placements=variants)
    out: dict[str, object] = {}
    for name, (tau_s, gain) in variants.items():
        trip = _first_crossing(frames, f"ntc_{name}_c", CASE_OT_C)
        out[name] = {
            "tau_s": tau_s,
            "gain": gain,
            "detect_since_step_s": None if trip is None else round(trip["t_s"] - STEP_TIME_S, 4),
        }
    return out


def trip_delay_s(t_start_c: float, t_target_c: float, tau_s: float, threshold_c: float) -> float:
    """一阶传感器到阈值的延迟：t = −τ·ln(1 − (阈−初值)/(目标−初值))。

    D08 接口口径：OT 判决时刻 = 热网络把壳温推到阈值的时间 + 本函数 + 去抖拍数×Δt。
    目标温度不高于阈值时永不触发（返回 inf）。
    """
    if tau_s <= 0:
        raise ValueError("时间常数必须为正")
    if t_target_c <= threshold_c:
        return math.inf
    if t_start_c >= threshold_c:
        return 0.0
    frac = (threshold_c - t_start_c) / (t_target_c - t_start_c)
    return -tau_s * math.log(1.0 - frac)


def thermal_budget(frames: list[dict[str, float]]) -> dict[str, float]:
    """热保护时间预算的分解：热网络先到阈，NTC 滞后再加，D08 电气链只占毫秒。"""
    case_trip = _first_crossing(frames, "case_c", CASE_OT_C)
    ntc_trip = _first_crossing(frames, "ntc_case_side_c", CASE_OT_C)
    if case_trip is None or ntc_trip is None:
        raise ValueError("工况内壳温/壳侧测点未越阈，无法给预算")
    network_s = case_trip["t_s"] - STEP_TIME_S
    sensor_s = ntc_trip["t_s"] - case_trip["t_s"]
    total_s = ntc_trip["t_s"] - STEP_TIME_S
    return {
        "network_s": round(network_s, 4),
        "sensor_s": round(sensor_s, 4),
        "thermal_trip_s": round(total_s, 4),
        "d08_worst_ms": D08_WORST_WINDOW_MS,
        "ratio": round(total_s * 1000.0 / D08_WORST_WINDOW_MS, 1),
    }


# --- D16-thermal-identification：辨识数据合同、盲区与留出验证 ---

def generate_log(
    ambient_c: float = AMBIENT_C,
    current_a: float = 8.0,
    rest_s: float = 300.0,
    load_s: float = 1800.0,
    tail_s: float = 600.0,
) -> list[dict[str, float]]:
    """合成阶跃日志：静置 → 恒流（发热恒定，供辨识）→ 撤载。"""
    phases = [
        (0.0, rest_s, 0.0, "rest"),
        (rest_s, rest_s + load_s, current_a, "load"),
        (rest_s + load_s, rest_s + load_s + tail_s, 0.0, "tail"),
    ]
    frames = simulate(phases, ambient_c=ambient_c)
    for frame in frames:
        # 辨识合同列名：t_case_c/t_ntc_c 是测量列，t_core_c 只用于评分。
        frame["t_case_c"] = frame["case_c"]
        frame["t_ntc_c"] = frame["ntc_case_side_c"]
        frame["t_core_c"] = frame["core_c"]
    return frames


def write_log_csv(frames: list[dict[str, float]], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LOG_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for frame in frames:
            writer.writerow({k: round(frame[k], 6) for k in LOG_COLUMNS})


def write_ident_csv(frames: list[dict[str, float]], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=IDENT_COLUMNS)
        writer.writeheader()
        for frame in frames:
            writer.writerow(
                {
                    "t_s": round(frame["t_s"], 6),
                    "q_w": round(frame["q_w"], 6),
                    "t_case_c": round(frame["case_c"], 6),
                    "t_ntc_c": round(frame["ntc_case_side_c"], 6),
                    "t_core_c": round(frame["core_c"], 6),
                    "ambient_c": round(frame["ambient_c"], 6),
                }
            )


def load_identification(path: Path) -> list[dict[str, float]]:
    """读取辨识 CSV，严格执行数据合同：错表头/缺列/非有限/时间回退/采样过疏一律拒绝。"""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != IDENT_COLUMNS:
            raise ValueError(
                f"表头必须为 {','.join(IDENT_COLUMNS)}，得到 {reader.fieldnames}"
            )
        frames: list[dict[str, float]] = []
        last_t: float | None = None
        for lineno, row in enumerate(reader, start=2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"第 {lineno} 行列数不足")
            parsed: dict[str, float] = {}
            for key in IDENT_COLUMNS:
                raw = row[key]
                if raw is None:
                    raise ValueError(f"第 {lineno} 行缺列 {key}")
                try:
                    value = float(raw)
                except ValueError as exc:
                    raise ValueError(f"第 {lineno} 行 {key} 无法解析: {raw!r}") from exc
                if not math.isfinite(value):
                    raise ValueError(f"第 {lineno} 行 {key} 非有限")
                parsed[key] = value
            if parsed["q_w"] < 0.0:
                raise ValueError(f"第 {lineno} 行 q_w 为负")
            if parsed["ambient_c"] <= -273.15:
                raise ValueError(f"第 {lineno} 行 ambient_c 低于绝对零度")
            t_s = parsed["t_s"]
            if last_t is not None:
                gap = t_s - last_t
                if gap <= 0.0:
                    raise ValueError(f"第 {lineno} 行 t_s 未严格递增")
                if gap > IDENT_MAX_GAP_S:
                    raise ValueError(
                        f"第 {lineno} 行采样间隔 {gap:.1f} s 超过 {IDENT_MAX_GAP_S:.0f} s 上限"
                    )
            last_t = t_s
            frames.append(parsed)
    if len(frames) < IDENT_MIN_SAMPLES:
        raise ValueError(f"样本数 {len(frames)} 少于 {IDENT_MIN_SAMPLES}")
    return frames


def _grid_fit(
    samples: list[tuple[float, float]], tau_grid: list[float]
) -> tuple[float, float, float]:
    """一阶模型 T = T₀ + A(1−e^{−t/τ})：τ 网格搜索 + A 线性最小二乘。"""
    t0, temp0 = samples[0]
    best: tuple[float, float, float] | None = None
    for tau in tau_grid:
        weights = [1.0 - math.exp(-(t - t0) / tau) for t, _temp in samples]
        denom = sum(w * w for w in weights)
        if denom <= 1e-12:
            continue
        amp = (
            sum(
                w * (temp - temp0)
                for w, (_t, temp) in zip(weights, samples, strict=True)
            )
            / denom
        )
        sse = sum(
            (temp - temp0 - amp * w) ** 2
            for w, (_t, temp) in zip(weights, samples, strict=True)
        )
        rms = math.sqrt(sse / len(samples))
        if best is None or rms < best[2]:
            best = (tau, amp, rms)
    if best is None:
        raise ValueError("拟合失败：退化数据")
    return best


def identify_one_node(
    frames: list[dict[str, float]],
    t_from: float,
    t_to: float,
    column: str = "t_case_c",
) -> dict[str, object]:
    """从一段恒功率阶跃辨识一阶集总模型 (R_th, τ, C_th)。

    column 只允许测量列（t_case_c / t_ntc_c）。t_core_c 是评分用的独立真值，
    辨识器不得读取——有回归测试钉住（改真值列不移动辨识结果）。
    """
    if column not in ("t_case_c", "t_ntc_c"):
        raise ValueError("辨识只能使用测量列（t_case_c / t_ntc_c）")
    window = [f for f in frames if t_from <= f["t_s"] <= t_to]
    if len(window) < IDENT_MIN_SAMPLES:
        raise ValueError("辨识窗样本不足")
    q_values = [f["q_w"] for f in window]
    q_mean = sum(q_values) / len(q_values)
    if q_mean <= 0.0:
        raise ValueError("辨识窗内没有发热，无法辨识")
    if max(abs(q - q_mean) for q in q_values) > IDENT_Q_TOLERANCE * q_mean:
        raise ValueError("辨识窗内发热功率不恒定（数据合同要求恒功率阶跃）")
    samples = [(f["t_s"], f[column]) for f in window]
    tau, amp, rms = _grid_fit(samples, TAU_GRID)
    r_th = amp / q_mean
    return {
        "column": column,
        "window_s": round(t_to - t_from, 4),
        "samples": len(window),
        "power_w": round(q_mean, 6),
        "r_th_k_per_w": round(r_th, 6),
        "tau_s": round(tau, 4),
        "c_th_j_per_k": round(tau / r_th, 4),
        "rms_k": round(rms, 6),
        "tau_at_grid_edge": tau >= 0.95 * TAU_GRID[-1],
    }


def naive_steady_state_r(
    frames: list[dict[str, float]], t_from: float, t_to: float, column: str = "t_case_c"
) -> dict[str, object]:
    """两点口径（最常见的误用）：把窗末温升当稳态 → R̂ = ΔT/P。

    窗口短于 3τ 时这个数无条件偏小——它衡量的是「你等了多久」，不是「热阻多大」。
    """
    if column not in ("t_case_c", "t_ntc_c"):
        raise ValueError("只能用测量列")
    window = [f for f in frames if t_from <= f["t_s"] <= t_to]
    if len(window) < IDENT_MIN_SAMPLES:
        raise ValueError("窗内样本不足")
    rise_k = window[-1][column] - window[0][column]
    q_mean = sum(f["q_w"] for f in window) / len(window)
    if q_mean <= 0.0:
        raise ValueError("窗内没有发热")
    return {
        "column": column,
        "window_s": round(t_to - t_from, 4),
        "rise_k": round(rise_k, 6),
        "r_th_k_per_w": round(rise_k / q_mean, 6),
    }


def predict_case(frames: list[dict[str, float]], r_th: float, tau_s: float) -> list[float]:
    """一阶模型前向预测壳温（逐帧精确步进），从首帧实测值起推。"""
    if r_th <= 0 or tau_s <= 0:
        raise ValueError("模型参数必须为正")
    temp = frames[0]["t_case_c"]
    out = [temp]
    for prev, frame in zip(frames, frames[1:], strict=False):
        dt = frame["t_s"] - prev["t_s"]
        target = frame["ambient_c"] + frame["q_w"] * r_th
        temp = target + (temp - target) * math.exp(-dt / tau_s)
        out.append(temp)
    return out


def validate_model(
    frames: list[dict[str, float]], params: dict[str, object]
) -> dict[str, float]:
    """留出验证：独立工况上的一阶模型预测误差（只读测量列）。"""
    predicted = predict_case(frames, _num(params["r_th_k_per_w"]), _num(params["tau_s"]))
    errors = [p - f["t_case_c"] for p, f in zip(predicted, frames, strict=True)]
    return {
        "frames": float(len(frames)),
        "rms_k": round(math.sqrt(sum(e * e for e in errors) / len(errors)), 4),
        "max_abs_k": round(max(abs(e) for e in errors), 4),
        "final_error_k": round(errors[-1], 4),
    }


def _constant_power_window(frames: list[dict[str, float]]) -> tuple[float, float]:
    """数据合同：辨识窗必须取自最长的一段恒功率区间（自动定位阶跃段）。"""
    best: tuple[int, int] | None = None
    start = 0
    for i in range(1, len(frames) + 1):
        breaks = (
            i == len(frames)
            or frames[i]["q_w"] <= 0.0
            or abs(frames[i]["q_w"] - frames[start]["q_w"])
            > IDENT_Q_TOLERANCE * max(frames[start]["q_w"], 1e-12)
        )
        if not breaks:
            continue
        if frames[start]["q_w"] > 0.0 and (best is None or i - start > best[1] - best[0]):
            best = (start, i)
        start = i
    if best is None:
        raise ValueError("数据中没有恒功率区间，无法辨识热参数")
    return frames[best[0]]["t_s"], frames[best[1] - 1]["t_s"]


def identify_report(
    ident_frames: list[dict[str, float]] | None = None,
    valid_frames: list[dict[str, float]] | None = None,
) -> dict[str, object]:
    """辨识 / 盲区 / 数据要求 / 留出验证的完整账本。"""
    if ident_frames is None:
        ident_frames = generate_log()
    if valid_frames is None:
        valid_frames = generate_log(
            ambient_c=35.0, current_a=11.0, rest_s=120.0, load_s=1200.0, tail_s=300.0
        )

    t_load, t_load_end = _constant_power_window(ident_frames)
    short_end = min(t_load + SHORT_WINDOW_S, t_load_end)
    full = identify_one_node(ident_frames, t_load, t_load_end, "t_case_c")
    full_ntc = identify_one_node(ident_frames, t_load, t_load_end, "t_ntc_c")
    short = identify_one_node(ident_frames, t_load, short_end, "t_case_c")
    naive_short = naive_steady_state_r(ident_frames, t_load, short_end, "t_case_c")
    naive_full = naive_steady_state_r(ident_frames, t_load, t_load_end, "t_case_c")
    coarse_frames = [f for f in ident_frames if f["t_s"] % 60.0 == 0.0]
    c_load, c_load_end = _constant_power_window(coarse_frames)
    coarse = identify_one_node(coarse_frames, c_load, c_load_end, "t_case_c")
    quantised = [{**f, "t_case_c": round(f["t_case_c"] * 10.0) / 10.0} for f in ident_frames]
    quant = identify_one_node(quantised, t_load, t_load_end, "t_case_c")
    return {
        "scenario_id": DATA_SCENARIO_ID,
        "identity": (
            "synthetic teaching step response; R_th/C_th are teaching values, "
            "not measured hardware"
        ),
        "true_parameters": {
            "r_core_case_k_per_w": R_CORE_CASE_K_PER_W,
            "r_case_amb_k_per_w": R_CASE_AMB_K_PER_W,
            "r_total_k_per_w": R_TOTAL_K_PER_W,
            "c_core_j_per_k": C_CORE_J_PER_K,
            "c_case_j_per_k": C_CASE_J_PER_K,
        },
        "full_window": full,
        "full_window_on_ntc": full_ntc,
        "ntc_tau_inflation_s": round(_num(full_ntc["tau_s"]) - _num(full["tau_s"]), 4),
        "naive_at_short_window": naive_short,
        "naive_at_full_window": naive_full,
        "short_window": short,
        "coarse_sampling": coarse,
        "quantised_0_1k": quant,
        "dt_required_for_fast_mode_s": round(modes()["tau_fast_s"] / 10.0, 4),
        "validation": validate_model(valid_frames, full),
        "validation_profile": "11 A / ambient 35 °C, held out from identification",
        "unobservable_core_gap_k": round(R_CORE_CASE_K_PER_W * heat_w(11.0), 4),
        "conclusion": (
            "壳温数据辨识出的是壳→环境那一段热阻（≈R_sa），芯→壳那一段在稳态不可见；"
            "短窗把 R_th 与 τ 一起推到退化边界，贴壳 NTC 的滞后几乎原样加进 τ"
        ),
    }


def build_report(
    metrics: dict[str, object] | None = None,
    identification: dict[str, object] | None = None,
    frames: list[dict[str, float]] | None = None,
) -> dict[str, object]:
    if frames is None:
        frames = simulate()
    if metrics is None:
        metrics = sensor_metrics(frames)
    if identification is None:
        identification = identify_report()
    return {
        "scenario_id": SCENARIO_ID,
        "identity": (
            "teaching lumped-parameter thermal chain; R_th/C_th, core limit, case threshold, "
            "NTC tau and divider are teaching values — not device measurements, not "
            "thermal-simulation acceptance"
        ),
        "network": {
            "r_int_ohm": R_INT_OHM,
            "c_core_j_per_k": C_CORE_J_PER_K,
            "r_core_case_k_per_w": R_CORE_CASE_K_PER_W,
            "c_case_j_per_k": C_CASE_J_PER_K,
            "r_case_amb_k_per_w": R_CASE_AMB_K_PER_W,
            "r_total_k_per_w": R_TOTAL_K_PER_W,
            "ambient_c": AMBIENT_C,
            "core_limit_c": CORE_LIMIT_C,
            "case_ot_c": CASE_OT_C,
            "dt_s": DT_S,
        },
        "modes": {k: round(v, 4) for k, v in modes().items()},
        "steady_state_10a": {k: round(v, 4) for k, v in steady_state(10.0).items()},
        "silent_band": {k: round(v, 4) for k, v in silent_band().items()},
        "counterexample_structural": silent_trip_counterexample(frames),
        "counterexample_lag": step_response(frames),
        "divider_vs_lag": divider_vs_lag(),
        "sensor_metrics": metrics,
        "placement_improvement": placement_improvement(frames),
        "trip_budget": thermal_budget(frames),
        "sop": {
            "ambient_30_a": round(sop_sustained_current_a(30.0), 4),
            "ambient_45_a": round(sop_sustained_current_a(45.0), 4),
        },
        "identification": identification,
        "conclusion": (
            "壳温测点量的是壳：芯-壳梯度（P·R_cs）与 NTC 自身滞后叠加，使 60 °C 壳阈"
            "在沉默带内永不触发；测点位置改善的是「测到壳温」的忠实度，改善不了"
            "「壳≠芯」的结构性偏差"
        ),
        "firmware_boundary": (
            "固件 BmsInputs 只有单个 temp_c10、无时间戳/质量位/测点身份：固件层面无法"
            "区分传感器滞后与热惯性，也无法同时携带壳温与芯温两条链；两节点模型与"
            "多测点对比是教学补全，不证明固件已实现热状态估计"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 等工件的目录")
    parser.add_argument(
        "--data",
        type=Path,
        help=f"辨识 CSV（{','.join(IDENT_COLUMNS)}）；缺省用内置合成阶跃",
    )
    args = parser.parse_args(argv)

    ident_frames: list[dict[str, float]] | None = None
    if args.data is not None:
        try:
            ident_frames = load_identification(args.data)
        except (OSError, ValueError) as exc:
            print(f"辨识数据拒绝：{exc}", file=sys.stderr)
            return 2
    if ident_frames is None:
        ident_frames = generate_log()

    identification = identify_report(ident_frames=ident_frames)
    report = None
    try:
        identification = identify_report(ident_frames=ident_frames)
        report = build_report(identification=identification)
    except ValueError as exc:
        print(f"辨识数据拒绝：{exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        write_log_csv(simulate(), args.out / "thermal_log.csv")
        write_ident_csv(ident_frames, args.out / "identification.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
