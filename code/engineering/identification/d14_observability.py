"""Teaching experiments for D14: observability and truth-free diagnosis.

Frozen teaching chain extending S2/D02/D12. Three questions are made executable:

1. **Sensitivity / Fisher information**: the same 5 mV voltage observation
   yields a SOC Cramer-Rao bound of 0.625 pp on an 0.8 V/SOC slope and
   6.25 pp on an 0.08 V/SOC flat region (100x information, 10x standard
   deviation). A steeper OCV buys precision, not identifiability.
2. **Rank / excitation**: with an unknown constant voltage bias b, the pair
   (z, b) is rank-1 observable from rest observations at one OCV slope, no
   matter how steep. A pulse that moves the operating point across the OCV
   knee changes the sensitivity ratio and makes (z, b) rank-2 observable.
   A pulse that stays inside the flat segment does not.
3. **Truth-free diagnosis**: a z-only filter on a flat rest with an 8 mV
   bias shrinks its covariance while its actual error grows to 10 pp. The
   same algorithm on a steep rest recovers 10x (1 pp) because the
   sensitivity is 10x larger; the residual 1 pp is still the unidentifiable
   bias. Innovation NIS can stay small; charge-balance mismatch and a
   bias-state model expose the missing state.

Scenario IDs: ``D14-observability`` (built-in frozen chain) and
``D14-profile-replay`` (external observation CSV replay).

All data are synthetic teaching data. They are not device measurements, not
HIL results, and not human acceptance. The firmware ``BmsInputs`` struct in
``code/firmware/bms.h`` carries only cell_mv/current_ma/temp_c10/
charger_present: it has no timestamp and no measurement-quality field, so the
freshness/quality semantics of a production estimator cannot be wired to that
struct without a new data contract.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

SCENARIO_ID = "D14-observability"
PROFILE_SCENARIO_ID = "D14-profile-replay"

Q_AH = 2.0
DT_S = 60.0
SIGMA_V_MV = 5.0

OCV_SLOPE_STEEP = 0.8      # V/SOC（NMC 类，教学值，沿用 D12）
OCV_SLOPE_FLAT = 0.08      # V/SOC（LFP 平台，教学值，沿用 D12）
OCV_KNEE_PP = 60.0         # 分段 OCV 拐点（SOC pp）
OCV_KNEE_V = 3.2 + OCV_SLOPE_STEEP * OCV_KNEE_PP / 100.0  # 3.68 V

STEEP_HIGH_PP = 80.0
STEEP_SOC_PP = 70.0
MID_SOC_PP = 55.0
FLAT_HIGH_PP = 45.0
FLAT_SOC_PP = 40.0

VOLTAGE_BIAS_MV = 8.0      # 未知常数电压偏置；平坦区折算 10 pp，陡区 1 pp
INIT_P_PP2 = 25.0          # SOC 初值方差（std 5 pp）
PROCESS_Q_PP2 = 1e-6
INIT_P_B_MV2 = 25.0        # 偏置先验方差（std 5 mV）
PROCESS_Q_B_MV2 = 1e-6

REST_FRAMES = 60
MULTIPOINT_REST_FRAMES = 10
MULTIPOINT_CURRENT_A = 2.0
MULTIPOINT_DROPS_PP = (10.0, 30.0)  # 80 -> 70 -> 40
MULTIPOINT_DROP_FRAMES = tuple(round(drop / (MULTIPOINT_CURRENT_A * DT_S / (3600.0 * Q_AH) * 100.0)) for drop in MULTIPOINT_DROPS_PP)

CONFIDENT_ERROR_PP = 2.0
OVERCONFIDENCE_FACTOR = 10.0
CHARGE_BALANCE_TOL_PP = 2.0

PROFILE_COLUMNS = ["t_s", "current_a", "v_meas_mv", "true_soc_pp"]

CONFIDENT_WRONG_REASON = (
    "平坦区斜率 0.8 mV/pp：8 mV 未建模偏置被解释成 10 pp SOC；"
    "协方差按 5 mV 噪声收缩，误差却停在偏置下限"
)
RECOVERY_REASON = (
    "陡区斜率 8 mV/pp：同一偏置只折算 1 pp；同一算法恢复 10 倍，"
    "但残余 1 pp 仍来自不可辨识的偏置"
)


def ocv_mv(z_pp: float) -> float:
    """教学分段 OCV（mV）：≥60 pp 斜率 0.8 V/SOC，以下平台 0.08，连续。"""
    if z_pp >= OCV_KNEE_PP:
        return (3.2 + OCV_SLOPE_STEEP * z_pp / 100.0) * 1000.0
    return (OCV_KNEE_V + OCV_SLOPE_FLAT * (z_pp - OCV_KNEE_PP) / 100.0) * 1000.0


def ocv_slope_mv_per_pp(z_pp: float) -> float:
    """dOCV/dz，单位 mV/pp（V/SOC 乘 10）。"""
    return (OCV_SLOPE_STEEP if z_pp >= OCV_KNEE_PP else OCV_SLOPE_FLAT) * 10.0


def deterministic_noise(n: int, sigma_mv: float = SIGMA_V_MV, seed: int = 20261110) -> list[float]:
    """确定性标准正态序列（LCG + Box-Muller），避免绑定随机库版本。"""
    if n < 0:
        raise ValueError("n must be nonnegative")
    if sigma_mv < 0:
        raise ValueError("sigma must be nonnegative")
    state = seed
    out: list[float] = []
    while len(out) < n:
        state = (1103515245 * state + 12345) % (2 ** 31)
        u1 = (state + 1.0) / (2 ** 31 + 1.0)
        state = (1103515245 * state + 12345) % (2 ** 31)
        u2 = (state + 1.0) / (2 ** 31 + 1.0)
        radius = math.sqrt(-2.0 * math.log(u1))
        out.append(sigma_mv * radius * math.cos(2.0 * math.pi * u2))
        out.append(sigma_mv * radius * math.sin(2.0 * math.pi * u2))
    return out[:n]


def fisher_information(z_values: list[float], sigma_mv: float = SIGMA_V_MV) -> dict:
    """静置观测对 [z0, b] 的 Fisher 信息矩阵（2x2）。

    观测模型 v = OCV(z0 + Δz_known) + b + n，Δz_known 由已知电流积分给出。
    灵敏度行 s = [dOCV/dz, 1]（mV/pp, mV/mV）。FIM = Σ s sᵀ / σ²。
    单一斜率时两列成正比，det=0、秩 1——斜率再陡也不能分离 z0 与 b；
    跨越拐点（斜率比变化）后秩 2，两者才可辨识。
    """
    if not z_values:
        raise ValueError("need at least one observation")
    if sigma_mv <= 0:
        raise ValueError("sigma must be positive")
    rows = [(ocv_slope_mv_per_pp(z), 1.0) for z in z_values]
    sigma2 = sigma_mv * sigma_mv
    a = sum(g * g for g, _ in rows) / sigma2
    b = sum(g for g, _ in rows) / sigma2
    c = len(rows) / sigma2
    det = a * c - b * b
    if det < 0.0 and det > -1e-12 * a * c:
        det = 0.0
    trace = a + c
    disc = max(0.0, trace * trace / 4.0 - det)
    lam_max = trace / 2.0 + math.sqrt(disc)
    lam_min = trace / 2.0 - math.sqrt(disc)
    normalized_det = det / (a * c) if a * c > 0.0 else 0.0
    rank = 2 if normalized_det > 1e-9 else 1
    crlb_z: float | None = None
    crlb_b: float | None = None
    if rank == 2 and det > 0.0:
        crlb_z = math.sqrt(c / det)
        crlb_b = math.sqrt(a / det)
    slopes = sorted({g for g, _ in rows})
    groups = []
    for slope in slopes:
        count = sum(1 for g, _ in rows if g == slope)
        groups.append(
            {
                "slope_mv_per_pp": slope,
                "samples": count,
                "scalar_crlb_pp_b_known": sigma_mv / (slope * math.sqrt(count)),
            }
        )
    scalar_crlb = None
    if len(slopes) == 1:
        scalar_crlb = sigma_mv / (slopes[0] * math.sqrt(len(rows)))
    return {
        "observations": len(z_values),
        "slope_groups": groups,
        "fim": [[a, b], [b, c]],
        "det": det,
        "normalized_det": normalized_det,
        "rank": rank,
        "soc_identifiable": rank == 2,
        "bias_identifiable": rank == 2,
        "crlb_z_pp": crlb_z,
        "crlb_b_mv": crlb_b,
        "scalar_crlb_pp_b_known": scalar_crlb,
        "min_eigenvalue": lam_min,
        "max_eigenvalue": lam_max,
        "condition_number": (lam_max / lam_min) if rank == 2 and lam_min > 0.0 else None,
    }


def _profiled_fim(name: str, z_values: list[float], description: str) -> dict:
    result = fisher_information(z_values)
    result["name"] = name
    result["description"] = description
    windows: list[dict] = []
    for z in sorted(set(z_values)):
        windows.append({"z_pp": round(z, 4), "samples": z_values.count(z)})
    result["z_windows_pp"] = windows
    result["z_span_pp"] = round(max(z_values) - min(z_values), 4)
    return result


def fim_profiles() -> dict:
    """四种静置/脉冲观测方案的可观测性排序（只用静置观测，脉冲只搬工作点）。"""
    return {
        "rest_flat": _profiled_fim(
            "rest_flat",
            [FLAT_SOC_PP] * REST_FRAMES,
            "单点平坦静置 60 拍：秩 1，斜率只决定精度",
        ),
        "rest_steep": _profiled_fim(
            "rest_steep",
            [STEEP_SOC_PP] * REST_FRAMES,
            "单点陡区静置 60 拍：秩 1，精度提高 100 倍但偏置仍不可辨识",
        ),
        "pulse_flat": _profiled_fim(
            "pulse_flat",
            [FLAT_HIGH_PP] * MULTIPOINT_REST_FRAMES + [FLAT_SOC_PP] * MULTIPOINT_REST_FRAMES,
            "平坦区内 5 pp 脉冲后的两段静置（各 10 拍）：斜率相同，秩仍 1——脉冲不等于可观测",
        ),
        "hppc_knee": _profiled_fim(
            "hppc_knee",
            [STEEP_HIGH_PP] * MULTIPOINT_REST_FRAMES
            + [STEEP_SOC_PP] * MULTIPOINT_REST_FRAMES
            + [FLAT_SOC_PP] * MULTIPOINT_REST_FRAMES,
            "跨越 OCV 拐点的多段静置（80/70/40 pp 各 10 拍）：斜率比变化，秩 2——z 与 b 同时可辨识",
        ),
    }


def generate_rest_frames(
    z_pp: float,
    n: int = REST_FRAMES,
    bias_mv: float = VOLTAGE_BIAS_MV,
    noise: list[float] | None = None,
) -> list[dict]:
    """单点静置观测：电流为 0，电压 = OCV(z) + 偏置 + 噪声。"""
    if n <= 0:
        raise ValueError("n must be positive")
    if noise is None:
        noise = deterministic_noise(n)
    if len(noise) < n:
        raise ValueError("noise shorter than requested frames")
    frames = []
    for i in range(n):
        frames.append(
            {
                "t_s": i * DT_S,
                "current_a": 0.0,
                "z_true_pp": z_pp,
                "v_meas_mv": ocv_mv(z_pp) + bias_mv + noise[i],
            }
        )
    return frames


def generate_multipoint_frames(
    z0_pp: float = STEEP_HIGH_PP,
    bias_mv: float = VOLTAGE_BIAS_MV,
    noise: list[float] | None = None,
) -> list[dict]:
    """80 pp 静置 → 10 pp 放电 → 70 pp 静置 → 30 pp 放电 → 40 pp 静置。

    只用静置拍做观测；放电拍 v_meas 为空（带载端电压不能当 OCV）。
    脉冲的作用是把工作点搬过 OCV 拐点，脉冲本身的 R0/R1 辨识属于 D11。
    """
    total_rest = 3 * MULTIPOINT_REST_FRAMES
    if noise is None:
        noise = deterministic_noise(total_rest)
    if len(noise) < total_rest:
        raise ValueError("noise shorter than requested frames")
    drop_per_frame = MULTIPOINT_CURRENT_A * DT_S / (3600.0 * Q_AH) * 100.0
    for drop, count in zip(MULTIPOINT_DROPS_PP, MULTIPOINT_DROP_FRAMES, strict=True):
        if abs(drop_per_frame * count - drop) > 1e-9:
            raise ValueError("multipoint drop configuration is inconsistent")
    frames: list[dict] = []
    t = 0.0
    z = z0_pp
    noise_i = 0
    for window in range(3):
        for _ in range(MULTIPOINT_REST_FRAMES):
            frames.append(
                {
                    "t_s": t,
                    "current_a": 0.0,
                    "z_true_pp": round(z, 6),
                    "v_meas_mv": ocv_mv(z) + bias_mv + noise[noise_i],
                }
            )
            noise_i += 1
            t += DT_S
        if window < 2:
            for _ in range(MULTIPOINT_DROP_FRAMES[window]):
                z -= drop_per_frame
                frames.append(
                    {
                        "t_s": t,
                        "current_a": MULTIPOINT_CURRENT_A,
                        "z_true_pp": round(z, 6),
                        "v_meas_mv": None,
                    }
                )
                t += DT_S
    return frames


def run_z_only(
    frames: list[dict],
    z0_pp: float,
    p0_pp2: float = INIT_P_PP2,
    q_pp2: float = PROCESS_Q_PP2,
    sigma_mv: float = SIGMA_V_MV,
) -> dict:
    """只估 SOC 的标量卡尔曼滤波；模型不含电压偏置状态。"""
    if not frames:
        raise ValueError("frames must not be empty")
    if p0_pp2 <= 0.0:
        raise ValueError("initial variance must be positive")
    z = z0_pp
    p = p0_pp2
    trace: list[dict] = []
    for i, frame in enumerate(frames):
        if i > 0:
            dt = frame["t_s"] - frames[i - 1]["t_s"]
            z -= frame["current_a"] * dt / (3600.0 * Q_AH) * 100.0
            p += q_pp2
        row = {
            "t_s": frame["t_s"],
            "current_a": frame["current_a"],
            "z_true_pp": frame["z_true_pp"],
            "z_hat_pp": z,
            "p_pp2": p,
            "p_std_pp": math.sqrt(max(p, 0.0)),
            "error_pp": z - frame["z_true_pp"],
            "v_meas_mv": frame["v_meas_mv"],
            "innovation_mv": None,
            "nis": None,
            "correction_pp": 0.0,
        }
        if frame["v_meas_mv"] is not None:
            h = ocv_slope_mv_per_pp(z)
            innovation = frame["v_meas_mv"] - ocv_mv(z)
            s = h * h * p + sigma_mv * sigma_mv
            gain = p * h / s
            correction = gain * innovation
            z += correction
            p = max(0.0, (1.0 - gain * h) * p)
            row["z_hat_pp"] = z
            row["p_pp2"] = p
            row["p_std_pp"] = math.sqrt(p)
            row["error_pp"] = z - frame["z_true_pp"]
            row["innovation_mv"] = innovation
            row["nis"] = innovation * innovation / s
            row["correction_pp"] = correction
        trace.append(row)
    return {"trace": trace, "z_final_pp": z, "p_final_pp2": p}


def run_bias_filter(
    frames: list[dict],
    z0_pp: float,
    b0_mv: float = 0.0,
    p0_z_pp2: float = INIT_P_PP2,
    p0_b_mv2: float = INIT_P_B_MV2,
    q_z_pp2: float = PROCESS_Q_PP2,
    q_b_mv2: float = PROCESS_Q_B_MV2,
    sigma_mv: float = SIGMA_V_MV,
) -> dict:
    """同时估 [z, b] 的 EKF；b 是常数电压偏置（随机游走过程噪声）。"""
    if not frames:
        raise ValueError("frames must not be empty")
    if p0_z_pp2 <= 0.0 or p0_b_mv2 <= 0.0:
        raise ValueError("initial variances must be positive")
    z = z0_pp
    b = b0_mv
    p11 = p0_z_pp2
    p12 = 0.0
    p22 = p0_b_mv2
    sigma2 = sigma_mv * sigma_mv
    trace: list[dict] = []
    for i, frame in enumerate(frames):
        if i > 0:
            dt = frame["t_s"] - frames[i - 1]["t_s"]
            z -= frame["current_a"] * dt / (3600.0 * Q_AH) * 100.0
            p11 += q_z_pp2
            p22 += q_b_mv2
        row = {
            "t_s": frame["t_s"],
            "current_a": frame["current_a"],
            "z_true_pp": frame["z_true_pp"],
            "z_hat_pp": z,
            "b_hat_mv": b,
            "p_z_std_pp": math.sqrt(max(p11, 0.0)),
            "p_b_std_mv": math.sqrt(max(p22, 0.0)),
            "error_pp": z - frame["z_true_pp"],
            "bias_error_mv": b - VOLTAGE_BIAS_MV,
            "v_meas_mv": frame["v_meas_mv"],
            "innovation_mv": None,
            "nis": None,
            "correction_z_pp": 0.0,
            "correction_b_mv": 0.0,
        }
        if frame["v_meas_mv"] is not None:
            h1 = ocv_slope_mv_per_pp(z)
            h2 = 1.0
            innovation = frame["v_meas_mv"] - (ocv_mv(z) + b)
            s = h1 * h1 * p11 + 2.0 * h1 * h2 * p12 + h2 * h2 * p22 + sigma2
            k1 = (p11 * h1 + p12 * h2) / s
            k2 = (p12 * h1 + p22 * h2) / s
            z += k1 * innovation
            b += k2 * innovation
            # Joseph form keeps P symmetric positive semidefinite.
            a11 = 1.0 - k1 * h1
            a12 = -k1 * h2
            a21 = -k2 * h1
            a22 = 1.0 - k2 * h2
            ap11 = a11 * p11 + a12 * p12
            ap12 = a11 * p12 + a12 * p22
            ap21 = a21 * p11 + a22 * p12
            ap22 = a21 * p12 + a22 * p22
            n11 = ap11 * a11 + ap12 * a12 + k1 * k1 * sigma2
            n12 = ap11 * a21 + ap12 * a22 + k1 * k2 * sigma2
            n21 = ap21 * a11 + ap22 * a12 + k2 * k1 * sigma2
            n22 = ap21 * a21 + ap22 * a22 + k2 * k2 * sigma2
            p11 = n11
            p12 = 0.5 * (n12 + n21)
            p22 = n22
            row["z_hat_pp"] = z
            row["b_hat_mv"] = b
            row["p_z_std_pp"] = math.sqrt(max(p11, 0.0))
            row["p_b_std_mv"] = math.sqrt(max(p22, 0.0))
            row["error_pp"] = z - frame["z_true_pp"]
            row["bias_error_mv"] = b - VOLTAGE_BIAS_MV
            row["innovation_mv"] = innovation
            row["nis"] = innovation * innovation / s
            row["correction_z_pp"] = k1 * innovation
            row["correction_b_mv"] = k2 * innovation
        trace.append(row)
    return {"trace": trace, "z_final_pp": z, "b_final_mv": b, "p11": p11, "p12": p12, "p22": p22}


def _lag1(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values)
    if var <= 0.0:
        return None
    cov = sum((values[i] - mean) * (values[i - 1] - mean) for i in range(1, len(values)))
    return cov / var


def summarize_z_only(result: dict, last_updates: int = 5) -> dict:
    trace = result["trace"]
    updates = [row for row in trace if row["innovation_mv"] is not None]
    if not updates:
        raise ValueError("trace has no measurement updates")
    final = trace[-1]
    innovations = [row["innovation_mv"] for row in updates]
    nis = [row["nis"] for row in updates]
    corrections = [row["correction_pp"] for row in updates]
    tail = updates[-last_updates:] if last_updates > 0 else updates
    sum_correction = sum(corrections)
    p_std = final["p_std_pp"]
    abs_error = abs(final["error_pp"])
    same_sign = max(
        sum(1 for c in corrections if c > 0.0),
        sum(1 for c in corrections if c < 0.0),
    ) / len(corrections)
    lag1 = _lag1(innovations)
    return {
        "updates": len(updates),
        "final_z_hat_pp": round(final["z_hat_pp"], 4),
        "final_true_pp": round(final["z_true_pp"], 4),
        "final_error_pp": round(final["error_pp"], 4),
        "final_p_std_pp": round(p_std, 6),
        "max_abs_error_pp": round(max(abs(row["error_pp"]) for row in trace), 4),
        "mean_abs_error_pp": round(sum(abs(row["error_pp"]) for row in trace) / len(trace), 4),
        "nis_mean": round(sum(nis) / len(nis), 4),
        "nis_tail_mean": round(sum(row["nis"] for row in tail) / len(tail), 4),
        "innovation_mean_mv": round(sum(innovations) / len(innovations), 4),
        "innovation_lag1": round(lag1, 4) if lag1 is not None else None,
        "sum_correction_pp": round(sum_correction, 4),
        "same_sign_fraction": round(same_sign, 4),
        "overconfidence_ratio": round(abs_error / p_std, 2) if p_std > 0.0 else None,
        "confident_wrong": abs_error > CONFIDENT_ERROR_PP and abs_error > OVERCONFIDENCE_FACTOR * p_std,
        "charge_balance_mismatch": abs(sum_correction) > CHARGE_BALANCE_TOL_PP,
    }


def summarize_bias_filter(result: dict, last_updates: int = 5) -> dict:
    trace = result["trace"]
    updates = [row for row in trace if row["innovation_mv"] is not None]
    if not updates:
        raise ValueError("trace has no measurement updates")
    final = trace[-1]
    rss = sum(row["innovation_mv"] ** 2 for row in updates)
    tail = updates[-last_updates:] if last_updates > 0 else updates
    tail_rss = sum(row["innovation_mv"] ** 2 for row in tail)
    return {
        "updates": len(updates),
        "final_z_hat_pp": round(final["z_hat_pp"], 4),
        "final_z_error_pp": round(final["error_pp"], 4),
        "final_bias_estimate_mv": round(final["b_hat_mv"], 4),
        "final_bias_error_mv": round(final["bias_error_mv"], 4),
        "final_p_z_std_pp": round(final["p_z_std_pp"], 6),
        "final_p_b_std_mv": round(final["p_b_std_mv"], 6),
        "rss_mv2": round(rss, 4),
        "rms_mv": round(math.sqrt(rss / len(updates)), 4),
        "tail_rms_mv": round(math.sqrt(tail_rss / len(tail)), 4),
    }


def _heldout(trace: list[dict], frames: list[dict], n_last: int = MULTIPOINT_REST_FRAMES) -> dict:
    """最后一段静置的首拍新息与 RSS：更新前的一步预测，检验拟合段之外。"""
    update_indices = [i for i, row in enumerate(trace) if row["innovation_mv"] is not None]
    if len(update_indices) < n_last:
        raise ValueError("not enough updates for held-out segment")
    selected = update_indices[-n_last:]
    first = trace[selected[0]]
    rss = sum(trace[i]["innovation_mv"] ** 2 for i in selected)
    return {
        "first_innovation_mv": round(first["innovation_mv"], 4),
        "rss_mv2": round(rss, 4),
        "rms_mv": round(math.sqrt(rss / len(selected)), 4),
        "z_true_first_pp": round(frames[selected[0]]["z_true_pp"], 4),
    }


def dual_model_comparison() -> dict:
    """平坦单点 vs 跨拐点多点：同一数据上 z-only 与 [z,b] 模型的分歧证据。"""
    flat_frames = generate_rest_frames(FLAT_SOC_PP, REST_FRAMES)
    flat_z = run_z_only(flat_frames, FLAT_SOC_PP)
    flat_b = run_bias_filter(flat_frames, FLAT_SOC_PP)
    flat_z_summary = summarize_z_only(flat_z)
    flat_b_summary = summarize_bias_filter(flat_b)
    flat_separable = (
        abs(flat_b_summary["final_bias_error_mv"]) < 2.0
        and flat_b_summary["final_p_b_std_mv"] < 2.0
        and abs(flat_b_summary["final_z_error_pp"]) < 1.0
    )

    multi_frames = generate_multipoint_frames()
    multi_z = run_z_only(multi_frames, STEEP_HIGH_PP)
    multi_b = run_bias_filter(multi_frames, STEEP_HIGH_PP)
    multi_z_summary = summarize_z_only(multi_z)
    multi_b_summary = summarize_bias_filter(multi_b)
    multi_separable = (
        abs(multi_b_summary["final_bias_error_mv"]) < 2.0
        and multi_b_summary["final_p_b_std_mv"] < 2.0
        and abs(multi_b_summary["final_z_error_pp"]) < 1.0
    )

    return {
        "bias_direction": {
            "flat_estimate_mv": flat_b_summary["final_bias_estimate_mv"],
            "knee_estimate_mv": multi_b_summary["final_bias_estimate_mv"],
            "same_sign": (flat_b_summary["final_bias_estimate_mv"] > 0.0)
            == (multi_b_summary["final_bias_estimate_mv"] > 0.0),
            "note": (
                "两个工况的 b 估计同号，支持存在常数电压偏置；平坦单斜率下幅值不可辨识，"
                "跨拐点后才收敛。方向一致不等于幅值正确，也不等于老化。"
            ),
        },
        "flat_single_slope": {
            "separable": flat_separable,
            "reason": (
                "单一斜率静置：FIM 秩 1；两模型都能把 8 mV 偏置吸收进不同的 z/b 组合，"
                "电压拟合不能判定哪一组 z 是真的"
            ),
            "z_only": flat_z_summary,
            "bias_model": flat_b_summary,
            "z_estimate_gap_pp": round(
                abs(flat_z_summary["final_z_hat_pp"] - flat_b_summary["final_z_hat_pp"]), 4
            ),
        },
        "multipoint_knee": {
            "separable": multi_separable,
            "reason": (
                "跨拐点斜率比变化：FIM 秩 2；bias 模型可把偏置与 z 同时定下来，"
                "z-only 模型在平坦段把偏置写进 SOC"
            ),
            "z_only": multi_z_summary,
            "bias_model": multi_b_summary,
            "heldout_final_rest": {
                "z_only": _heldout(multi_z["trace"], multi_frames),
                "bias_model": _heldout(multi_b["trace"], multi_frames),
            },
        },
    }


def counterexample_pair() -> dict:
    """同一 z-only 算法：平坦区自信地错，陡区恢复 10 倍。"""
    flat_frames = generate_rest_frames(FLAT_SOC_PP, REST_FRAMES)
    steep_frames = generate_rest_frames(STEEP_SOC_PP, REST_FRAMES)
    flat = summarize_z_only(run_z_only(flat_frames, FLAT_SOC_PP))
    steep = summarize_z_only(run_z_only(steep_frames, STEEP_SOC_PP))
    recovery = (
        abs(flat["final_error_pp"]) / abs(steep["final_error_pp"])
        if steep["final_error_pp"] != 0.0
        else None
    )
    return {
        "same_algorithm": "z-only scalar Kalman filter; only the operating point changes",
        "flat": {**flat, "reason": CONFIDENT_WRONG_REASON},
        "steep": {**steep, "reason": RECOVERY_REASON},
        "recovery_ratio": round(recovery, 4) if recovery is not None else None,
        "residual_bias_pp_steep": steep["final_error_pp"],
        "truth_free_conclusion": (
            f"平坦区总修正量 {flat['sum_correction_pp']} pp 超过电荷平衡容差，是主判据；"
            f"同号修正占比 {flat['same_sign_fraction']} 在噪声下只作辅助。"
            f"新息 NIS 均值 {flat['nis_mean']} 本身不足以报警。"
            f"陡区把同一偏置的 SOC 误差缩小 10 倍，但 {steep['final_error_pp']} pp 残余"
            "仍说明偏置没有被辨识，只是被斜率压小。"
        ),
    }


def load_profile(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != PROFILE_COLUMNS:
            raise ValueError(
                f"表头必须为 {','.join(PROFILE_COLUMNS)}，实际 {reader.fieldnames}"
            )
        frames = []
        last_t: float | None = None
        updates = 0
        for lineno, row in enumerate(reader, start=2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"第 {lineno} 行列数不足")
            try:
                t_s = float(row["t_s"])
                current_a = float(row["current_a"])
                true_soc_pp = float(row["true_soc_pp"])
            except ValueError as exc:
                raise ValueError(f"第 {lineno} 行字段无法解析: {exc}") from exc
            v_raw = (row["v_meas_mv"] or "").strip()
            v_meas_mv: float | None = None
            if v_raw != "":
                try:
                    v_meas_mv = float(v_raw)
                except ValueError as exc:
                    raise ValueError(f"第 {lineno} 行 v_meas_mv 无法解析: {v_raw!r}") from exc
                if not math.isfinite(v_meas_mv):
                    raise ValueError(f"第 {lineno} 行 v_meas_mv 非有限: {v_raw}")
                updates += 1
            if not all(math.isfinite(x) for x in (t_s, current_a, true_soc_pp)):
                raise ValueError(f"第 {lineno} 行存在非有限值")
            if not 0.0 <= true_soc_pp <= 100.0:
                raise ValueError(f"第 {lineno} 行 true_soc_pp 超出 [0,100]")
            if last_t is not None and t_s <= last_t:
                raise ValueError(f"第 {lineno} 行 t_s 未严格递增")
            last_t = t_s
            frames.append(
                {
                    "t_s": t_s,
                    "current_a": current_a,
                    "v_meas_mv": v_meas_mv,
                    "z_true_pp": true_soc_pp,
                }
            )
    if not frames:
        raise ValueError("工况为空")
    if updates == 0:
        raise ValueError("工况没有任何 v_meas_mv 观测")
    return frames


def write_profile_csv(frames: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=PROFILE_COLUMNS)
        writer.writeheader()
        for frame in frames:
            writer.writerow(
                {
                    "t_s": frame["t_s"],
                    "current_a": frame["current_a"],
                    "v_meas_mv": "" if frame["v_meas_mv"] is None else frame["v_meas_mv"],
                    "true_soc_pp": frame["z_true_pp"],
                }
            )


def write_trace_csv(trace: list[dict], path: Path, fields: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in trace:
            writer.writerow({key: ("" if row[key] is None else row[key]) for key in fields})


def write_fisher_csv(profiles: dict, path: Path) -> None:
    fields = [
        "name",
        "observations",
        "rank",
        "bias_identifiable",
        "det",
        "normalized_det",
        "crlb_z_pp",
        "crlb_b_mv",
        "scalar_crlb_pp_b_known",
        "min_eigenvalue",
        "max_eigenvalue",
        "condition_number",
    ]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for name, profile in profiles.items():
            row = {key: profile.get(key) for key in fields}
            row["name"] = name
            writer.writerow({key: ("" if row[key] is None else row[key]) for key in fields})


def replay_profile(frames: list[dict], z0_pp: float) -> dict:
    """用同一 z-only 滤波器回放外部观测 CSV；评分只读真值列，诊断不读。"""
    if not math.isfinite(z0_pp) or not 0.0 <= z0_pp <= 100.0:
        raise ValueError("z0 必须为 [0,100] 内的有限值")
    result = run_z_only(frames, z0_pp)
    summary = summarize_z_only(result)
    summary["scenario_id"] = PROFILE_SCENARIO_ID
    summary["frames"] = len(frames)
    summary["z0_pp"] = z0_pp
    summary["truth_used_for_scoring_only"] = True
    summary["trace"] = result["trace"]
    return summary


def summarize_profile_replay(result: dict) -> dict:
    return {k: v for k, v in result.items() if k != "trace"}


def build_report(profile_replay: dict | None = None) -> dict:
    profiles = fim_profiles()
    counter = counterexample_pair()
    single = {
        "steep": fisher_information([STEEP_SOC_PP], SIGMA_V_MV),
        "flat": fisher_information([FLAT_SOC_PP], SIGMA_V_MV),
    }
    info_ratio = (
        single["steep"]["fim"][0][0] / single["flat"]["fim"][0][0]
        if single["flat"]["fim"][0][0] > 0.0
        else None
    )
    crlb_ratio = (
        single["flat"]["scalar_crlb_pp_b_known"] / single["steep"]["scalar_crlb_pp_b_known"]
        if single["steep"]["scalar_crlb_pp_b_known"] not in (None, 0.0)
        else None
    )
    return {
        "scenario_id": SCENARIO_ID,
        "identity": (
            "synthetic teaching chain extending S2/D02/D12; not device measurement, "
            "not HIL, not human acceptance. Firmware BmsInputs has no timestamp or "
            "measurement-quality field; freshness/quality diagnosis here is model-level only."
        ),
        "model": {
            "Q_ah": Q_AH,
            "dt_s": DT_S,
            "sigma_v_mv": SIGMA_V_MV,
            "ocv_slope_steep_v_per_soc": OCV_SLOPE_STEEP,
            "ocv_slope_flat_v_per_soc": OCV_SLOPE_FLAT,
            "ocv_knee_pp": OCV_KNEE_PP,
            "voltage_bias_mv": VOLTAGE_BIAS_MV,
            "initial_p_std_pp": math.sqrt(INIT_P_PP2),
            "initial_p_b_std_mv": math.sqrt(INIT_P_B_MV2),
        },
        "fisher": {
            "single_sample": {
                "steep": single["steep"],
                "flat": single["flat"],
                "information_ratio_steep_over_flat": round(info_ratio, 4) if info_ratio else None,
                "crlb_ratio_flat_over_steep": round(crlb_ratio, 4) if crlb_ratio else None,
            },
            "profiles": profiles,
        },
        "counterexample": counter,
        "truth_free_diagnostics": {
            "flat": {
                key: counter["flat"][key]
                for key in (
                    "nis_mean",
                    "nis_tail_mean",
                    "sum_correction_pp",
                    "same_sign_fraction",
                    "charge_balance_mismatch",
                    "confident_wrong",
                )
            },
            "steep": {
                key: counter["steep"][key]
                for key in (
                    "nis_mean",
                    "nis_tail_mean",
                    "sum_correction_pp",
                    "same_sign_fraction",
                    "charge_balance_mismatch",
                    "confident_wrong",
                )
            },
            "dual_model": dual_model_comparison(),
            "boundary": (
                "新息/NIS 自洽只说明滤波器按自己的模型消化了观测；电压拟合好不等于 z 对。"
                "无真值时可用的判据是：静置段电荷平衡失配、修正同号占比、"
                "以及跨拐点双模型的分歧。它们能报警，不能单独证明哪一组 z/b 为真。"
            ),
        },
        "conclusion": (
            f"斜率决定精度：5 mV 在 0.8 V/SOC 区折算 "
            f"{single['steep']['scalar_crlb_pp_b_known']} pp，在 0.08 平坦区 "
            f"{single['flat']['scalar_crlb_pp_b_known']} pp，信息量差 100 倍。"
            "秩决定可辨识性：单一斜率的静置无论多陡都分不开 z 与 b；"
            "只有脉冲把工作点搬过拐点、斜率比变化后 (z,b) 才秩 2。"
            f"z-only 滤波器在平坦静置 + 8 mV 偏置下协方差标准差 "
            f"{counter['flat']['final_p_std_pp']} pp，误差却涨到 "
            f"{counter['flat']['final_error_pp']} pp；同一算法在陡区把误差压到 "
            f"{counter['steep']['final_error_pp']} pp，但残差仍是同一个偏置，不是辨识成功。"
        ),
        "profile_replay": summarize_profile_replay(profile_replay) if profile_replay else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 与 CSV 工件的目录")
    parser.add_argument(
        "--profile",
        type=Path,
        help="回放观测 CSV（t_s,current_a,v_meas_mv,true_soc_pp；负载拍 v_meas_mv 留空）",
    )
    parser.add_argument("--z0", type=float, default=FLAT_SOC_PP, help="回放滤波初值 SOC（pp）")
    args = parser.parse_args(argv)

    if not math.isfinite(args.z0) or not 0.0 <= args.z0 <= 100.0:
        print("z0 拒绝：必须为 [0,100] 内的有限值", file=sys.stderr)
        return 2

    profile_result: dict | None = None
    if args.profile:
        try:
            frames = load_profile(args.profile)
            profile_result = replay_profile(frames, args.z0)
        except (OSError, ValueError) as exc:
            print(f"profile 拒绝：{exc}", file=sys.stderr)
            return 2
    elif args.z0 != FLAT_SOC_PP:
        print("--z0 只在 --profile 回放时生效", file=sys.stderr)
        return 2

    report = build_report(profile_replay=profile_result)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        write_fisher_csv(report["fisher"]["profiles"], args.out / "fisher_profiles.csv")
        flat_trace = run_z_only(generate_rest_frames(FLAT_SOC_PP, REST_FRAMES), FLAT_SOC_PP)["trace"]
        steep_trace = run_z_only(generate_rest_frames(STEEP_SOC_PP, REST_FRAMES), STEEP_SOC_PP)["trace"]
        trace_fields = [
            "t_s",
            "current_a",
            "z_true_pp",
            "z_hat_pp",
            "p_std_pp",
            "error_pp",
            "v_meas_mv",
            "innovation_mv",
            "nis",
            "correction_pp",
        ]
        write_trace_csv(flat_trace, args.out / "counterexample_flat_trace.csv", trace_fields)
        write_trace_csv(steep_trace, args.out / "counterexample_steep_trace.csv", trace_fields)
        multi_frames = generate_multipoint_frames()
        write_profile_csv(multi_frames, args.out / "multipoint_profile.csv")
        multi_bias_trace = run_bias_filter(multi_frames, STEEP_HIGH_PP)["trace"]
        bias_fields = [
            "t_s",
            "current_a",
            "z_true_pp",
            "z_hat_pp",
            "b_hat_mv",
            "p_z_std_pp",
            "p_b_std_mv",
            "error_pp",
            "bias_error_mv",
            "v_meas_mv",
            "innovation_mv",
            "nis",
            "correction_z_pp",
            "correction_b_mv",
        ]
        write_trace_csv(multi_bias_trace, args.out / "dual_model_bias_trace.csv", bias_fields)
        if profile_result is not None:
            write_profile_csv(
                [
                    {
                        "t_s": row["t_s"],
                        "current_a": row["current_a"],
                        "v_meas_mv": row["v_meas_mv"],
                        "z_true_pp": row["z_true_pp"],
                    }
                    for row in profile_result["trace"]
                ],
                args.out / "profile_replay_input.csv",
            )
            write_trace_csv(
                profile_result["trace"],
                args.out / "profile_replay_trace.csv",
                trace_fields,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
