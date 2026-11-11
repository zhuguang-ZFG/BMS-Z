"""Teaching experiments for D15: SOH definition family, synthetic aging paths,
Arrhenius temperature acceleration, and capacity-estimation holdout.

Frozen teaching chain (extends D11/D12, discipline from B05):

* SOH is not one number. Capacity-type ``SOH_C`` (charge retention), power-type
  ``SOH_P`` (ohmic power capability, ``P_max ~ 1/R``) and energy-type ``SOH_E``
  (charge times loaded-voltage retention) are defined separately and evaluated
  on the same aged cell.
* Aging is synthetic: SEI calendar loss ``k_cal*sqrt(t_eq)`` plus cycle loss
  ``k_cyc*N_eq``, with equivalent exposure accumulated through an Arrhenius
  factor ``AF(T) = exp(Ea/R * (1/T_ref - 1/T))``. ``Ea = 30 kJ/mol`` is a
  teaching placeholder, not a fitted value for this cell.
* Capacity estimation uses ``Q_hat = dQ / dSOC`` with dSOC inferred from
  rest-gated OCV endpoints. Calibration samples (25 C) and one held-out
  temperature point (45 C) are split before looking; the held-out failure is
  reported as-is (B05), not tuned away.

All numbers are synthetic. They are not cell measurements, hardware-in-the-loop
results, or human acceptance. The firmware ``BmsInputs`` struct only carries
``cell_mv/current_ma/temp_c10/charger_present`` -- no timestamp, quality,
cycle-count, or charge-throughput field -- so SOH inputs must come from an
upper layer with a registered data identity.

Scenarios: ``D15-soh-aging`` (definitions, aging path, counterexample) and
``D15-capacity-holdout`` (calibration/validation segments).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

SCENARIO_ID = "D15-soh-aging"
CAPACITY_SCENARIO_ID = "D15-capacity-holdout"

# --- 老化轨迹：合成参数（教学值，不是本电芯实测/拟合） ---

Q_RATED_AH = 2.0
R0_OHM = 0.020
V_NOM_V = 3.7
RATED_CURRENT_A = 10.0
EOL_SOH_PCT = 80.0
MODEL_VALID_MIN_SOH_PCT = 60.0
MODEL_VALID_MAX_RES_GROWTH_PCT = 200.0

EA_KJ_PER_MOL = 30.0          # 教学占位值：文献常见 20-60 kJ/mol，本电芯未测
GAS_CONSTANT_J_PER_MOL_K = 8.314462618
T_REF_C = 25.0
TEMP_MIN_C = -20.0
TEMP_MAX_C = 80.0
MAX_CYCLES_PER_DAY = 20.0
MAX_TOTAL_DAYS = 20000.0

K_CAL_CAP_PCT_SQRT_DAY = 0.35   # SEI 型：容量损失 %/sqrt(等效天)
K_CYC_CAP_PCT_CYCLE = 0.01      # 循环型：容量损失 %/等效循环
K_CAL_RES_PCT_SQRT_DAY = 0.50   # 内阻增长 %/sqrt(等效天)
K_CYC_RES_PCT_CYCLE = 0.02      # 内阻增长 %/等效循环

EOL_CHECK_TEMPS_C = (25.0, 35.0, 45.0)

# --- 容量估计：标定/留出数据 ---

CAP_Q_TRUE_AH = 1.80
CAP_CAL_TOL_PCT = 3.0
CAP_METER_ERROR_MV = 0.5
CAP_OCV_TEMP_COEFF_MV_PER_K = 0.3   # 教学简化：固定电压偏移，未建模 SOC 依赖
CAP_T_REF_C = 25.0
CAP_SEGMENT_COLUMNS = [
    "segment_id",
    "role",
    "temp_c",
    "soc_start_pp",
    "soc_end_pp",
    "delta_q_ah",
    "v_start_v",
    "v_end_v",
    "true_soc_start_pp",
    "true_soc_end_pp",
]
CAP_ROLES = ("calibration", "validation")

HISTORY_COLUMNS = ["day_start", "day_end", "cycles_per_day", "temp_c"]


def arrhenius_factor(temp_c: float) -> float:
    """``AF(T) = exp(Ea/R * (1/T_ref - 1/T))``，Ea 用教学占位值 30 kJ/mol。"""
    if not math.isfinite(temp_c) or not TEMP_MIN_C <= temp_c <= TEMP_MAX_C:
        raise ValueError(
            f"温度必须在 [{TEMP_MIN_C}, {TEMP_MAX_C}] C 内，实际 {temp_c}"
        )
    t_k = temp_c + 273.15
    t_ref_k = T_REF_C + 273.15
    exponent = (
        EA_KJ_PER_MOL * 1000.0 / GAS_CONSTANT_J_PER_MOL_K
        * (1.0 / t_ref_k - 1.0 / t_k)
    )
    return math.exp(exponent)


def ocv_v(soc_fraction: float) -> float:
    """25 C 教学 OCV：>=60% 斜率 0.8 V/SOC，以下平台 0.08，连续于 3.68 V。"""
    if not 0.0 <= soc_fraction <= 1.0:
        raise ValueError("SOC must be within [0, 1]")
    if soc_fraction >= 0.6:
        return 3.2 + 0.8 * soc_fraction
    return 3.68 + 0.08 * (soc_fraction - 0.6)


def ocv_slope(soc_fraction: float) -> float:
    if not 0.0 <= soc_fraction <= 1.0:
        raise ValueError("SOC must be within [0, 1]")
    return 0.8 if soc_fraction >= 0.6 else 0.08


def soc_from_ocv(v: float) -> float:
    """用 25 C 表反查 SOC（估计器只看得见电压，没有真值列）。"""
    if not math.isfinite(v):
        raise ValueError("voltage must be finite")
    if v >= 3.68:
        return (v - 3.2) / 0.8
    return 0.6 + (v - 3.68) / 0.08


def endpoint_soc_residual_pp(voltage_error_mv: float, slope_v_per_soc: float) -> float:
    """端点电压误差折算成 SOC 残差：同样的 mV 在平坦支被放大 10 倍。"""
    if slope_v_per_soc <= 0.0:
        raise ValueError("slope must be positive")
    return voltage_error_mv / (slope_v_per_soc * 1000.0) * 100.0


def simulate_aging(history: list[dict]) -> dict:
    """按温度分段累计等效暴露，返回容量/功率/能量三型 SOH。

    ``history`` 每项：``days``、``cycles_per_day``、``temp_c``。日历项按
    ``sqrt(等效天)``，循环项按 ``等效循环`` 线性；Arrhenius 把每段的温度
    折算成 25 C 等效暴露。模型无拐点、无恢复、无路径依赖（除等效暴露），
    超出 ``MODEL_VALID_MIN_SOH_PCT`` 后只作外推标记，不是寿命预测。
    """
    if not history:
        raise ValueError("老化历史为空")
    total_days = 0.0
    total_cycles = 0.0
    eq_days = 0.0
    eq_cycles = 0.0
    for index, segment in enumerate(history, start=1):
        try:
            days = float(segment["days"])
            cycles_per_day = float(segment["cycles_per_day"])
            temp_c = float(segment["temp_c"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"第 {index} 段历史缺少 days/cycles_per_day/temp_c") from exc
        if not all(math.isfinite(x) for x in (days, cycles_per_day, temp_c)):
            raise ValueError(f"第 {index} 段历史存在非有限值")
        if days <= 0.0:
            raise ValueError(f"第 {index} 段 days 必须为正")
        if not 0.0 <= cycles_per_day <= MAX_CYCLES_PER_DAY:
            raise ValueError(
                f"第 {index} 段 cycles_per_day 必须在 [0, {MAX_CYCLES_PER_DAY}] 内"
            )
        af = arrhenius_factor(temp_c)
        total_days += days
        total_cycles += days * cycles_per_day
        eq_days += days * af
        eq_cycles += days * cycles_per_day * af
    if total_days > MAX_TOTAL_DAYS:
        raise ValueError(f"总天数超过模型有效域上限 {MAX_TOTAL_DAYS}")

    calendar_loss = K_CAL_CAP_PCT_SQRT_DAY * math.sqrt(eq_days)
    cycle_loss = K_CYC_CAP_PCT_CYCLE * eq_cycles
    capacity_loss = calendar_loss + cycle_loss
    resistance_growth = (
        K_CAL_RES_PCT_SQRT_DAY * math.sqrt(eq_days) + K_CYC_RES_PCT_CYCLE * eq_cycles
    )

    soh_capacity = 100.0 - capacity_loss
    soh_power = 100.0 / (1.0 + resistance_growth / 100.0)
    r_now = R0_OHM * (1.0 + resistance_growth / 100.0)
    v_load_bol = V_NOM_V - RATED_CURRENT_A * R0_OHM
    v_load_now = V_NOM_V - RATED_CURRENT_A * r_now
    voltage_retention = max(v_load_now, 0.0) / v_load_bol
    soh_energy = soh_capacity * voltage_retention
    in_valid_domain = (
        soh_capacity >= MODEL_VALID_MIN_SOH_PCT
        and resistance_growth <= MODEL_VALID_MAX_RES_GROWTH_PCT
    )

    return {
        "days": round(total_days, 4),
        "cycles": round(total_cycles, 4),
        "equivalent_days_at_25c": round(eq_days, 4),
        "equivalent_cycles_at_25c": round(eq_cycles, 4),
        "calendar_capacity_loss_pp": round(calendar_loss, 4),
        "cycle_capacity_loss_pp": round(cycle_loss, 4),
        "capacity_loss_pp": round(capacity_loss, 4),
        "resistance_growth_pct": round(resistance_growth, 4),
        "soh_capacity_pct": round(soh_capacity, 4),
        "soh_power_pct": round(soh_power, 4),
        "soh_energy_pct": round(soh_energy, 4),
        "in_valid_domain": in_valid_domain,
    }


def generate_history() -> list[dict]:
    """内置合成老化史：35 C、1 循环/天、730 天（两年）。"""
    return [{"days": 730.0, "cycles_per_day": 1.0, "temp_c": 35.0}]


def eol_age_days(temp_c: float, cycles_per_day: float = 1.0) -> dict:
    """容量型 SOH 首次跌破 80% 的年龄（二分；只对固定温度史有意义）。"""
    def capacity_soh(age_days: float) -> float:
        state = simulate_aging(
            [{"days": age_days, "cycles_per_day": cycles_per_day, "temp_c": temp_c}]
        )
        return float(state["soh_capacity_pct"])

    if capacity_soh(MAX_TOTAL_DAYS) >= EOL_SOH_PCT:
        raise ValueError("模型有效域内未跌破 EOL，不能外推寿命")
    low, high = 0.0, MAX_TOTAL_DAYS
    for _ in range(80):
        mid = (low + high) / 2.0
        if capacity_soh(mid) >= EOL_SOH_PCT:
            low = mid
        else:
            high = mid
    age = (low + high) / 2.0
    return {
        "temp_c": temp_c,
        "cycles_per_day": cycles_per_day,
        "age_days": round(age, 2),
        "cycles": round(age * cycles_per_day, 2),
        "state": simulate_aging(
            [{"days": age, "cycles_per_day": cycles_per_day, "temp_c": temp_c}]
        ),
    }


def cycle_count_counterexample() -> dict:
    """反例：同一循环数、不同温度史，25 C 循环数查表系统性高估 SOH。"""
    phase_days = 365.0
    cycles_per_day = 1.0
    cold = simulate_aging(
        [{"days": phase_days, "cycles_per_day": cycles_per_day, "temp_c": 25.0}] * 2
    )
    hot = simulate_aging(
        [
            {"days": phase_days, "cycles_per_day": cycles_per_day, "temp_c": 25.0},
            {"days": phase_days, "cycles_per_day": cycles_per_day, "temp_c": 45.0},
        ]
    )
    naive_soh = float(cold["soh_capacity_pct"])
    hot_soh = float(hot["soh_capacity_pct"])
    bias_pp = naive_soh - hot_soh
    bias_cycle_pp = float(hot["cycle_capacity_loss_pp"]) - float(
        cold["cycle_capacity_loss_pp"]
    )
    bias_calendar_pp = float(hot["calendar_capacity_loss_pp"]) - float(
        cold["calendar_capacity_loss_pp"]
    )
    return {
        "phase_days": phase_days,
        "cycles_per_day": cycles_per_day,
        "cycles_total": cold["cycles"],
        "cold_all_25c_soh_pct": round(naive_soh, 4),
        "hot_25c_then_45c_soh_pct": round(hot_soh, 4),
        "naive_cycle_lookup_soh_pct": round(naive_soh, 4),
        "bias_pp": round(bias_pp, 4),
        "bias_from_cycle_pp": round(bias_cycle_pp, 4),
        "bias_from_calendar_pp": round(bias_calendar_pp, 4),
        "af_45c": round(arrhenius_factor(45.0), 4),
        "conclusion": (
            "循环计数器只记录 N，不记录 N 是在什么温度下发生的。同一 730 循环，"
            f"25 C 全程 SOH {naive_soh:.2f}%，后半程 45 C 只有 {hot_soh:.2f}%——"
            f"按 25 C 查表系统性高估 {bias_pp:.2f} pp（循环加速 {bias_cycle_pp:.2f} pp、"
            f"日历加速 {bias_calendar_pp:.2f} pp）；温度加权后的等效循环才是老化输入，"
            "循环数本身不是 SOH"
        ),
    }


# --- 容量估计：Q = dQ / dSOC，端点 OCV 反查 ---

def generate_capacity_segments(
    meter_error_mv: float = CAP_METER_ERROR_MV,
    temp_coeff_mv_per_k: float = CAP_OCV_TEMP_COEFF_MV_PER_K,
) -> list[dict]:
    """内置合成标定/留出数据：25 C 三段标定，45 C 一段留出。

    生成器烘焙表计偏移与温度引起的 OCV 偏移；估计器只读 ``v_start_v`` /
    ``v_end_v`` / ``delta_q_ah``，真值 SOC 列只用于评分。
    """
    specs = [
        ("C1_90_30", "calibration", 25.0, 90.0, 30.0),
        ("C2_85_35", "calibration", 25.0, 85.0, 35.0),
        ("C3_80_40", "calibration", 25.0, 80.0, 40.0),
        ("V1_90_30_45C", "validation", 45.0, 90.0, 30.0),
    ]
    segments = []
    for segment_id, role, temp_c, start_pp, end_pp in specs:
        delta_soc_pp = start_pp - end_pp
        delta_q_ah = CAP_Q_TRUE_AH * delta_soc_pp / 100.0
        temp_shift_v = temp_coeff_mv_per_k * (temp_c - CAP_T_REF_C) / 1000.0
        meter_v = meter_error_mv / 1000.0
        segments.append(
            {
                "segment_id": segment_id,
                "role": role,
                "temp_c": temp_c,
                "soc_start_pp": start_pp,
                "soc_end_pp": end_pp,
                "delta_q_ah": delta_q_ah,
                "v_start_v": ocv_v(start_pp / 100.0) - temp_shift_v + meter_v,
                "v_end_v": ocv_v(end_pp / 100.0) - temp_shift_v + meter_v,
                "true_soc_start_pp": start_pp,
                "true_soc_end_pp": end_pp,
            }
        )
    return segments


def estimate_capacity_ah(segment: dict) -> dict:
    """从一段放电的电荷量与端点电压估计容量；不读真值 SOC 列。"""
    inferred_start = soc_from_ocv(float(segment["v_start_v"]))
    inferred_end = soc_from_ocv(float(segment["v_end_v"]))
    if not (0.0 <= inferred_start <= 1.0 and 0.0 <= inferred_end <= 1.0):
        raise ValueError(
            f"{segment['segment_id']}: 端点电压反查 SOC 超出 [0, 100] pp，"
            "OCV 表与数据温度/单位不匹配"
        )
    delta_soc_pp = (inferred_start - inferred_end) * 100.0
    if delta_soc_pp <= 0.0:
        raise ValueError(
            f"{segment['segment_id']}: 端点电压反推的 dSOC 非正（{delta_soc_pp:.4f} pp）"
        )
    return {
        "segment_id": segment["segment_id"],
        "role": segment["role"],
        "inferred_soc_start_pp": round(inferred_start * 100.0, 4),
        "inferred_soc_end_pp": round(inferred_end * 100.0, 4),
        "inferred_delta_soc_pp": round(delta_soc_pp, 4),
        "capacity_ah": float(segment["delta_q_ah"]) / (delta_soc_pp / 100.0),
    }


def evaluate_capacity_segments(segments: list[dict]) -> dict:
    """标定/留出评估：先固定切分再评分；留出失败原样保留。"""
    if not segments:
        raise ValueError("容量标定数据为空")
    calibration = [s for s in segments if s["role"] == "calibration"]
    validation = [s for s in segments if s["role"] == "validation"]
    if not calibration or not validation:
        raise ValueError("数据必须同时含 calibration 与 validation 样本")
    cal_temps = sorted({float(s["temp_c"]) for s in calibration})
    val_temps = sorted({float(s["temp_c"]) for s in validation})
    leakage = bool(set(cal_temps) & set(val_temps))

    rows = []
    for segment in segments:
        estimate = estimate_capacity_ah(segment)
        true_delta_pp = float(segment["true_soc_start_pp"]) - float(
            segment["true_soc_end_pp"]
        )
        if true_delta_pp <= 0.0:
            raise ValueError(f"{segment['segment_id']}: 真值 dSOC 必须为正")
        q_true = float(segment["delta_q_ah"]) / (true_delta_pp / 100.0)
        error_pct = (estimate["capacity_ah"] - q_true) / q_true * 100.0
        rows.append(
            {
                **estimate,
                "temp_c": float(segment["temp_c"]),
                "q_true_ah": round(q_true, 4),
                "q_estimate_ah": round(estimate["capacity_ah"], 4),
                "error_pct": round(error_pct, 4),
            }
        )

    calibration_rows = [r for r in rows if r["role"] == "calibration"]
    validation_rows = [r for r in rows if r["role"] == "validation"]
    calibration_max_abs = max(abs(r["error_pct"]) for r in calibration_rows)
    calibration_passed = calibration_max_abs <= CAP_CAL_TOL_PCT
    validation_max_abs = max(abs(r["error_pct"]) for r in validation_rows)
    validation_passed = validation_max_abs <= CAP_CAL_TOL_PCT and not leakage

    # 泄漏反事实：用留出点反推温度偏移再评分（构造性抹平，不能算验证）。
    corrected_errors = []
    for segment in validation:
        shift = CAP_OCV_TEMP_COEFF_MV_PER_K * (
            float(segment["temp_c"]) - CAP_T_REF_C
        ) / 1000.0
        corrected = {
            **segment,
            "v_start_v": float(segment["v_start_v"]) + shift,
            "v_end_v": float(segment["v_end_v"]) + shift,
        }
        corrected_errors.append(
            float(estimate_capacity_ah(corrected)["capacity_ah"])
        )
    corrected_validation_errors = []
    for segment, corrected_capacity in zip(
        validation, corrected_errors, strict=True
    ):
        true_delta_pp = float(segment["true_soc_start_pp"]) - float(
            segment["true_soc_end_pp"]
        )
        q_true = float(segment["delta_q_ah"]) / (true_delta_pp / 100.0)
        corrected_validation_errors.append(
            abs((corrected_capacity - q_true) / q_true * 100.0)
        )
    leakage_counterfactual_error = max(corrected_validation_errors)

    return {
        "scenario_id": CAPACITY_SCENARIO_ID,
        "segments": rows,
        "split": {
            "calibration_temps_c": cal_temps,
            "validation_temps_c": val_temps,
            "split_fixed_before_looking": True,
            "holdout_used_for_tuning": leakage,
            "leakage": leakage,
        },
        "calibration": {
            "count": len(calibration_rows),
            "max_abs_error_pct": round(calibration_max_abs, 4),
            "tolerance_pct": CAP_CAL_TOL_PCT,
            "passed": calibration_passed,
        },
        "validation": {
            "count": len(validation_rows),
            "max_abs_error_pct": round(validation_max_abs, 4),
            "tolerance_pct": CAP_CAL_TOL_PCT,
            "passed": validation_passed,
            "failure_kept": not validation_passed,
            "reason": (
                "45 C 留出点未参与任何调参；用 25 C OCV 表反查时，6 mV 温度偏移"
                "在 0.8 与 0.08 两支上折算成 0.75 pp 与 7.5 pp 端点残差，"
                "dSOC 被放大，容量被低估约 9.35%"
                if not validation_passed
                else "留出点在容差内"
            ),
        },
        "leakage_counterfactual": {
            "error_pct": round(leakage_counterfactual_error, 4),
            "verdict": (
                "把留出点的温度偏移反推回来，误差被构造性压到标定水平；"
                "这是泄漏演示，不是留出验证，不能据此声称 45 C 可估"
            ),
        },
        "requirements": _capacity_requirements(),
        "identity": {
            "source": "built-in synthetic generator (D15 teaching)",
            "version": "d15-segments/1",
            "units": "Q in Ah, SOC in pp, voltage in V, temperature in C",
            "conditions": (
                "constant 1 A discharge, rest-gated OCV endpoints, "
                "25 C calibration vs 45 C held-out validation"
            ),
            "rows": len(segments),
            "boundary": "合成数据；不是电芯实测，不构成容量验收或寿命承诺",
        },
    }


def _capacity_requirements() -> list[dict]:
    meter_flat = endpoint_soc_residual_pp(CAP_METER_ERROR_MV, 0.08)
    meter_steep = endpoint_soc_residual_pp(CAP_METER_ERROR_MV, 0.8)
    window_errors = {
        f"{window}_pp": round(
            (1.0 / (1.0 - (meter_flat - meter_steep) / window) - 1.0) * 100.0, 4
        )
        for window in (40.0, 50.0, 60.0)
    }
    polarization_residual_pp = endpoint_soc_residual_pp(5.0, 0.08)
    polarization_error_pct = (
        1.0 / (1.0 - polarization_residual_pp / 60.0) - 1.0
    ) * 100.0
    return [
        {
            "id": "R1",
            "requirement": "数据身份五字段：来源、版本、单位、工况、行数/边界（B05）",
            "evidence": "identity 段登记合成来源/版本/单位/温度与静置条件/行数；摘要不等于数据正确",
        },
        {
            "id": "R2",
            "requirement": "先切分后看：标定温度与留出温度在查看结果前固定",
            "evidence": "标定 {25 C} 与留出 {45 C} 分离；leakage=false；留出失败原样保留",
        },
        {
            "id": "R3",
            "requirement": "端点必须过静置门：带载端电压不是 OCV",
            "evidence": (
                "5 mV 极化残差在 0.08 平坦支折算 6.25 pp；60 pp 窗口上"
                f"容量误差 {polarization_error_pct:.2f}%"
            ),
        },
        {
            "id": "R4",
            "requirement": "温度必须进入 OCV 表身份；单一温度标定不许可外推",
            "evidence": "25 C 表用于 45 C 留出点，容量误差约 -9.35%，判失败",
        },
        {
            "id": "R5",
            "requirement": "放电窗口要够大：端点 SOC 残差按窗口放大",
            "evidence": (
                f"{CAP_METER_ERROR_MV} mV 在两支上折算 {meter_steep:.4f}/"
                f"{meter_flat:.4f} pp；40/50/60 pp 窗口误差 "
                f"{window_errors['40.0_pp']:.2f}/{window_errors['50.0_pp']:.2f}/"
                f"{window_errors['60.0_pp']:.2f}%"
            ),
        },
        {
            "id": "R6",
            "requirement": "电流计必须校准：dQ 直接进分子",
            "evidence": "0.5% 增益误差直接变 0.5% 容量误差；20 mA 偏置 1 h 在 1.8 Ah 上约 1.11%",
        },
    ]


def load_capacity_segments(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != CAP_SEGMENT_COLUMNS:
            raise ValueError(
                f"表头必须为 {','.join(CAP_SEGMENT_COLUMNS)}，实际 {reader.fieldnames}"
            )
        segments = []
        seen_ids = set()
        for lineno, row in enumerate(reader, start=2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"第 {lineno} 行列数不足")
            segment_id = (row["segment_id"] or "").strip()
            role = (row["role"] or "").strip()
            if not segment_id:
                raise ValueError(f"第 {lineno} 行 segment_id 为空")
            if segment_id in seen_ids:
                raise ValueError(f"第 {lineno} 行 segment_id 重复: {segment_id}")
            if role not in CAP_ROLES:
                raise ValueError(f"第 {lineno} 行 role 必须为 {CAP_ROLES}，实际 {role!r}")
            try:
                values = {
                    key: float(row[key])
                    for key in CAP_SEGMENT_COLUMNS
                    if key not in {"segment_id", "role"}
                }
            except ValueError as exc:
                raise ValueError(f"第 {lineno} 行字段无法解析: {exc}") from exc
            if not all(math.isfinite(v) for v in values.values()):
                raise ValueError(f"第 {lineno} 行存在非有限值")
            temp_c = values["temp_c"]
            if not TEMP_MIN_C <= temp_c <= TEMP_MAX_C:
                raise ValueError(f"第 {lineno} 行 temp_c 超出模型有效域")
            start_pp = values["soc_start_pp"]
            end_pp = values["soc_end_pp"]
            if not 0.0 <= end_pp < start_pp <= 100.0:
                raise ValueError(f"第 {lineno} 行必须满足 0 <= soc_end < soc_start <= 100")
            if values["delta_q_ah"] <= 0.0:
                raise ValueError(f"第 {lineno} 行 delta_q_ah 必须为正")
            for key in ("v_start_v", "v_end_v"):
                if not 2.0 <= values[key] <= 5.0:
                    raise ValueError(f"第 {lineno} 行 {key} 超出 [2, 5] V")
            if values["true_soc_end_pp"] >= values["true_soc_start_pp"]:
                raise ValueError(f"第 {lineno} 行真值 SOC 未按放电方向递减")
            segments.append(
                {"segment_id": segment_id, "role": role, **values}
            )
            seen_ids.add(segment_id)
    if not segments:
        raise ValueError("容量标定数据为空")
    if not any(s["role"] == "calibration" for s in segments):
        raise ValueError("缺少 calibration 样本")
    if not any(s["role"] == "validation" for s in segments):
        raise ValueError("缺少 validation 样本")
    return segments


def load_history(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != HISTORY_COLUMNS:
            raise ValueError(
                f"表头必须为 {','.join(HISTORY_COLUMNS)}，实际 {reader.fieldnames}"
            )
        history = []
        last_end: float | None = None
        for lineno, row in enumerate(reader, start=2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"第 {lineno} 行列数不足")
            try:
                day_start = float(row["day_start"])
                day_end = float(row["day_end"])
                cycles_per_day = float(row["cycles_per_day"])
                temp_c = float(row["temp_c"])
            except ValueError as exc:
                raise ValueError(f"第 {lineno} 行字段无法解析: {exc}") from exc
            if not all(
                math.isfinite(x) for x in (day_start, day_end, cycles_per_day, temp_c)
            ):
                raise ValueError(f"第 {lineno} 行存在非有限值")
            expected_start = last_end if last_end is not None else 0.0
            if not math.isclose(day_start, expected_start, abs_tol=1e-6):
                raise ValueError(f"第 {lineno} 行时间不连续（必须从 0 起首尾相接）")
            if day_end <= day_start:
                raise ValueError(f"第 {lineno} 行 day_end 必须大于 day_start")
            if not 0.0 <= cycles_per_day <= MAX_CYCLES_PER_DAY:
                raise ValueError(f"第 {lineno} 行 cycles_per_day 超出有效域")
            if not TEMP_MIN_C <= temp_c <= TEMP_MAX_C:
                raise ValueError(f"第 {lineno} 行 temp_c 超出有效域")
            history.append(
                {
                    "days": day_end - day_start,
                    "cycles_per_day": cycles_per_day,
                    "temp_c": temp_c,
                }
            )
            last_end = day_end
    if not history:
        raise ValueError("老化历史为空")
    # 复用 simulate_aging 的总量/有效域校验
    simulate_aging(history)
    return history


def write_history_csv(history: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=HISTORY_COLUMNS)
        writer.writeheader()
        cursor = 0.0
        for segment in history:
            start = cursor
            cursor += float(segment["days"])
            writer.writerow(
                {
                    "day_start": round(start, 6),
                    "day_end": round(cursor, 6),
                    "cycles_per_day": segment["cycles_per_day"],
                    "temp_c": segment["temp_c"],
                }
            )


def write_capacity_segments(segments: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CAP_SEGMENT_COLUMNS)
        writer.writeheader()
        for segment in segments:
            writer.writerow({key: segment[key] for key in CAP_SEGMENT_COLUMNS})


def write_capacity_estimates(evaluation: dict, path: Path) -> None:
    fields = [
        "segment_id",
        "role",
        "temp_c",
        "q_true_ah",
        "q_estimate_ah",
        "error_pct",
    ]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in evaluation["segments"]:
            writer.writerow({key: row[key] for key in fields})


def build_report(
    history: list[dict] | None = None,
    segments: list[dict] | None = None,
) -> dict:
    if history is None:
        history = generate_history()
    if segments is None:
        segments = generate_capacity_segments()
    state = simulate_aging(history)
    eol = []
    for temp_c in EOL_CHECK_TEMPS_C:
        point = eol_age_days(temp_c)
        eol.append(
            {
                "temp_c": temp_c,
                "age_days": point["age_days"],
                "cycles": point["cycles"],
            }
        )
    capacity = evaluate_capacity_segments(segments)
    return {
        "scenario_id": SCENARIO_ID,
        "identity": (
            "teaching chain extending D11/D12 with B05 split discipline; "
            "synthetic aging and synthetic capacity segments; not a cell measurement, "
            "not HIL, not human acceptance"
        ),
        "arrhenius": {
            "ea_kj_per_mol": EA_KJ_PER_MOL,
            "gas_constant_j_per_mol_k": GAS_CONSTANT_J_PER_MOL_K,
            "t_ref_c": T_REF_C,
            "source": (
                "教学占位值：Ea=30 kJ/mol 落在文献常见 20-60 kJ/mol 区间内，"
                "不是本电芯拟合结果；真实寿命模型必须在多温度老化数据上拟合 Ea，"
                "并登记数据身份（B05）"
            ),
            "factors": [
                {"temp_c": temp, "af": round(arrhenius_factor(temp), 4)}
                for temp in EOL_CHECK_TEMPS_C
            ],
        },
        "soh_definitions": {
            "capacity": "SOH_C = Q_now / Q_rated * 100（容量型，单位 %）",
            "power": (
                "SOH_P = R_rated / R_now * 100（功率型；固定电压窗下 P_max ~ 1/R，"
                "不是峰值功率实测）"
            ),
            "energy": (
                "SOH_E = SOH_C * (V_loaded_now / V_loaded_BOL)（能量型；额定电流下的"
                "可用电压保持率，不是容量型的同义词）"
            ),
            "eol_threshold_pct": EOL_SOH_PCT,
            "warning": (
                "三种 SOH 在同一时刻可以差数个百分点；只写 SOH=xx% 而不写定义族、"
                "温度、倍率与 EOL 阈值，结论不可复算"
            ),
        },
        "aging": {
            "history": [
                {
                    "days": round(float(segment["days"]), 4),
                    "cycles_per_day": segment["cycles_per_day"],
                    "temp_c": segment["temp_c"],
                    "arrhenius_factor": round(
                        arrhenius_factor(float(segment["temp_c"])), 4
                    ),
                }
                for segment in history
            ],
            "state": state,
            "eol": {"soh_capacity_pct": EOL_SOH_PCT, "points": eol},
            "model": (
                "容量损失 = k_cal*sqrt(t_eq) + k_cyc*N_eq；内阻增长同结构；"
                "t_eq/N_eq 为按 Arrhenius 折算到 25 C 的等效暴露"
            ),
        },
        "cycle_count_counterexample": cycle_count_counterexample(),
        "capacity_holdout": capacity,
        "boundaries": {
            "placeholder_not_estimate": (
                "Ea=30 kJ/mol、k_cal/k_cyc、初始内阻 20 mOhm、额定 2 Ah 都是教学占位值；"
                "它们只展示机制与量级，不能当作本电芯参数、寿命预测、质保承诺或设计余量"
            ),
            "valid_domain_not_permission": (
                "模型只在合成设定与已登记温度/倍率/循环史内成立；25 C 标定不许可 45 C，"
                "45 C 留出失败就是反证。留出点不得回拟合，失败必须原样报告"
            ),
            "single_soh_ambiguous": (
                f"容量型 {state['soh_capacity_pct']:.2f}%、功率型 "
                f"{state['soh_power_pct']:.2f}%、能量型 {state['soh_energy_pct']:.2f}% "
                "是同一颗合成电芯同一时刻的三个答案；单一 SOH 数字缺少定义族，"
                "不能用于许可、质保或寿命结论"
            ),
            "firmware_inputs": (
                "固件 BmsInputs 只有 cell_mv/current_ma/temp_c10/charger_present，"
                "没有时间戳、质量/新鲜度字段、循环计数或累计电荷；SOH 的输入必须由"
                "上层提供并登记身份，不能把一帧瞬时读数当老化估计"
            ),
        },
        "conclusion": (
            f"SOH 先写定义族：同一时刻容量型 {state['soh_capacity_pct']:.2f}、"
            f"功率型 {state['soh_power_pct']:.2f}、能量型 "
            f"{state['soh_energy_pct']:.2f}；老化输入是温度加权的等效暴露，"
            "不是循环计数；容量标定必须标定/留出温度分离，45 C 留出失败原样保留"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 等工件的目录")
    parser.add_argument(
        "--history",
        type=Path,
        help="老化历史 CSV（day_start,day_end,cycles_per_day,temp_c）；缺省用内置合成史",
    )
    parser.add_argument(
        "--segments",
        type=Path,
        help="容量标定/留出 CSV；缺省用内置合成段",
    )
    args = parser.parse_args(argv)

    if args.history:
        try:
            history = load_history(args.history)
        except (OSError, ValueError) as exc:
            print(f"history 拒绝：{exc}", file=sys.stderr)
            return 2
    else:
        history = generate_history()
    if args.segments:
        try:
            segments = load_capacity_segments(args.segments)
        except (OSError, ValueError) as exc:
            print(f"segments 拒绝：{exc}", file=sys.stderr)
            return 2
    else:
        segments = generate_capacity_segments()

    try:
        report = build_report(history=history, segments=segments)
    except ValueError as exc:
        print(f"计算拒绝：{exc}", file=sys.stderr)
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        write_history_csv(history, args.out / "history.csv")
        write_capacity_segments(segments, args.out / "capacity_segments.csv")
        write_capacity_estimates(
            report["capacity_holdout"], args.out / "capacity_estimates.csv"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
