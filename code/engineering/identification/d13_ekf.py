"""Teaching experiments for D13: one full EKF round by hand vs code, innovation
whitening and gating, the mismatch comparison against coulomb counting, and the
flat-region counterexample where no filter can rescue the estimate.

Frozen chain (extends S2/D11/D12): a 2-state EKF over [SOC z, current bias b] on
the D12 piecewise OCV table (0.8 V/SOC at or above 60%, 0.08 V/SOC below). The
predict step is D12's coulomb bookkeeping (Q hat and the 50 mA bias convention);
the update step is D12's OCV calibration, but the correction is set by P, H and R
instead of a hand-picked gain. Units: z in SOC fraction (displayed in pp), b in
A, voltages in V, and covariance entries in their own per-state units (B03: raw
determinants across mixed units are not comparable).

Synthetic boundary: the profile is generated here with deterministic Irwin-Hall
meter noise. Nothing in this module is a device measurement, a real OCV table,
or human acceptance; SRC01 is still open. The firmware BmsInputs snapshot
(code/firmware/bms.h) carries only cell_mv/current_ma/temp_c10/charger_present,
with no timestamp or quality field, so observation freshness/quality semantics
stay outside this filter.

Load frames carry no OCV observation (D12 contract: a loaded terminal voltage is
not an OCV), so the filter runs prediction-only through the discharge and can
only update during rest.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

SCENARIO_ID = "D13-ekf-round"
REPLAY_SCENARIO_ID = "D13-ekf-replay"

Q_AH = 2.0
OCV_SLOPE = 0.8          # V/SOC, steep teaching segment (same as D12)
OCV_SLOPE_FLAT = 0.08    # V/SOC, LFP-like plateau (same as D12)
OCV_KNEE = 0.6           # SOC where the piecewise table changes slope (D12)
DT_S = 0.5
TRUE_BIAS_A = 0.05

# --- D13-ekf-replay: D12 four-column profile semantics -----------------------
# current_a is the *sensor reading* here (physical current + 50 mA bias), because
# the bias is a filter state, not a hidden constant. true_soc_pp is generated
# from the physical current and is only used for scoring.
PROFILE_COLUMNS = ["t_s", "current_a", "v_meas", "true_soc_pp"]
PROFILE_DT_S = 60.0
PROFILE_REST_S = 600.0
PROFILE_LOAD_FROM_S = 600.0
PROFILE_LOAD_TO_S = 1260.0     # 11 min at 2 A: 80% -> 61.67%, stays in the steep segment
PROFILE_END_S = 1860.0
PROFILE_DISCHARGE_A = 2.0
PROFILE_INIT_SOC_PP = 80.0
PROFILE_INIT_ERROR_PP = 10.0
PROFILE_Q_TRUE_AH = 2.0
PROFILE_Q_HAT_AH = 2.1         # +5% capacity scale error (same teaching value as D12)
PROFILE_BIAS_A = 0.05
METER_SIGMA_MV = 5.0
R_V = (METER_SIGMA_MV / 1000.0) ** 2
Q_Z = (0.1 / 100.0) ** 2       # (0.1 pp per 60 s frame)^2
Q_B = (0.001) ** 2             # (1 mA per 60 s frame)^2
P0_SOC_VAR = (PROFILE_INIT_ERROR_PP / 100.0) ** 2
P0_BIAS_VAR = (PROFILE_BIAS_A) ** 2
GATE_SIGMA = 3.0

# Flat-region counterexample: 55% start, +50% capacity error, +10 mV OCV table
# offset and a grossly inflated Q_z. The innovation gate cannot see this.
FLAT_INIT_SOC_PP = 55.0
FLAT_INIT_ERROR_PP = 1.0
FLAT_LOAD_TO_S = 1800.0
FLAT_END_S = 9600.0    # 2 h 40 min final rest: the filter converges onto the wrong OCV line
FLAT_DISCHARGE_A = 1.0
FLAT_Q_HAT_AH = 3.0
FLAT_OCV_OFFSET_V = 0.010
FLAT_Q_Z = Q_Z                 # process noise stays nominal here; the wrong Q-hat is the capacity


def predict(state: list[float], p: list[list[float]], i_meas_a: float,
            q_z: float, q_b: float, slope: float = OCV_SLOPE,
            dt_s: float = DT_S, capacity_ah: float = Q_AH
            ) -> tuple[list[float], list[list[float]], float]:
    """Predict one step; returns (state_pred, p_pred, predicted_voltage).

    State = [z, b]. Dynamics: z = z - (i_meas - b) dt/(3600 Q); b = b (random walk).
    Process noise q_z/q_b is added once per call (per frame), matching the frozen
    hand test; callers with a different frame period pass their own q values.

    教学测量模型用**偏差形式**：工作点（3.6 V 与欧姆项）已从测量中扣除，
    测量只看见斜率项 y = slope·z + 噪声——这是为了让滤波机制在零均值附近演示，
    工作点扣除本身是 D12 校准合同的前提，不是省略。回放工况不用这个返回值，
    而是用 ocv_v(z_pred) 单独算预测电压。
    """
    z, b = state
    f01 = dt_s / (3600.0 * capacity_ah)
    z_pred = z - (i_meas_a - b) * f01
    b_pred = b
    f = [[1.0, f01], [0.0, 1.0]]
    p_pred = [
        [f[0][0] * (f[0][0] * p[0][0] + f[0][1] * p[1][0]) + f[0][1] * (f[0][0] * p[0][1] + f[0][1] * p[1][1]) + q_z,
         f[0][0] * p[0][1] + f[0][1] * p[1][1]],
        [f[0][0] * p[1][0] + f[0][1] * p[1][1],
         f[1][0] * p[0][1] + f[1][1] * p[1][1] + q_b],
    ]
    return [z_pred, b_pred], p_pred, slope * z_pred


def ocv(z: float, slope: float = OCV_SLOPE) -> float:
    return 3.6 + slope * (z - 0.5)


def ocv_v(soc_fraction: float) -> float:
    """D12's piecewise OCV: 0.8 V/SOC at or above 60%, 0.08 below (continuous)."""
    if soc_fraction >= OCV_KNEE:
        return 3.2 + OCV_SLOPE * soc_fraction
    return 3.2 + OCV_SLOPE * OCV_KNEE + OCV_SLOPE_FLAT * (soc_fraction - OCV_KNEE)


def ocv_slope(soc_fraction: float) -> float:
    return OCV_SLOPE if soc_fraction >= OCV_KNEE else OCV_SLOPE_FLAT


def kalman_step(state_pred: list[float], p_pred: list[list[float]], innovation: float,
                h: list[float], r_v: float
                ) -> tuple[list[float], list[list[float]], float, list[float]]:
    """Core update from a precomputed innovation; returns (state, p, s, gain)."""
    s = (h[0] * (p_pred[0][0] * h[0] + p_pred[0][1] * h[1])
         + h[1] * (p_pred[1][0] * h[0] + p_pred[1][1] * h[1]) + r_v)
    k = [
        (p_pred[0][0] * h[0] + p_pred[0][1] * h[1]) / s,
        (p_pred[1][0] * h[0] + p_pred[1][1] * h[1]) / s,
    ]
    z_new = state_pred[0] + k[0] * innovation
    b_new = state_pred[1] + k[1] * innovation
    p_new = [
        [(1 - k[0] * h[0]) * p_pred[0][0] - k[0] * h[1] * p_pred[1][0],
         (1 - k[0] * h[0]) * p_pred[0][1] - k[0] * h[1] * p_pred[1][1]],
        [-k[1] * h[0] * p_pred[0][0] + (1 - k[1] * h[1]) * p_pred[1][0],
         -k[1] * h[0] * p_pred[0][1] + (1 - k[1] * h[1]) * p_pred[1][1]],
    ]
    return [z_new, b_new], p_new, s, k


def update(state_pred: list[float], p_pred: list[list[float]], v_meas: float,
           v_pred: float, h: list[float], r_v: float
           ) -> tuple[list[float], list[list[float]], float, float]:
    """Kalman update; returns (state, p, innovation, k_gain[0])."""
    innovation = v_meas - v_pred
    state, p_new, _s, k = kalman_step(state_pred, p_pred, innovation, h, r_v)
    return state, p_new, innovation, k[0]


def is_positive_definite_2x2(p: list[list[float]]) -> bool:
    return p[0][0] > 0 and p[0][0] * p[1][1] - p[0][1] * p[1][0] > 0


def one_round_hand() -> dict:
    """Hand-computed round with round numbers; code path must reproduce it point by point."""
    state = [0.50, 0.0]
    p = [[0.0025, 0.0], [0.0, 0.0001]]  # z 方差 (0.05 SOC)^2；b 方差 (0.01 A)^2
    q_z = 1e-8
    q_b = 1e-8
    h = [OCV_SLOPE, 0.0]
    r_v = (0.002) ** 2  # 2 mV 测量方差
    state_p, p_p, v_p = predict(state, p, 2.0, q_z, q_b)
    v_meas_dev = OCV_SLOPE * 0.50 + 0.004  # 偏差形式：真值 0.50 的斜率项 + 4 mV
    z_u, p_u, innov, k0 = update(state_p, p_p, v_meas_dev, v_p, h, r_v)

    # 手算路径：同一组公式的标量展开（不经过矩阵函数），用于逐点对拍。
    f01 = DT_S / (3600.0 * Q_AH)
    z_pred_h = 0.50 - 2.0 * f01
    p00_pred_h = 0.0025 + f01 * f01 * 0.0001 + q_z
    p01_pred_h = f01 * 0.0001
    p11_pred_h = 0.0001 + q_b
    v_pred_h = OCV_SLOPE * z_pred_h
    innov_h = v_meas_dev - v_pred_h
    s_h = OCV_SLOPE * OCV_SLOPE * p00_pred_h + r_v
    k0_h = OCV_SLOPE * p00_pred_h / s_h
    k1_h = OCV_SLOPE * p01_pred_h / s_h
    z_post_h = z_pred_h + k0_h * innov_h
    p00_post_h = (1.0 - k0_h * OCV_SLOPE) * p00_pred_h
    p01_post_h = (1.0 - k0_h * OCV_SLOPE) * p01_pred_h
    p11_post_h = -k1_h * OCV_SLOPE * p01_pred_h + p11_pred_h

    hand = {
        "z_pred": z_pred_h,
        "p00_pred": p00_pred_h,
        "p01_pred": p01_pred_h,
        "p11_pred": p11_pred_h,
        "innovation_v": innov_h,
        "s": s_h,
        "k0": k0_h,
        "k1": k1_h,
        "z_post": z_post_h,
        "p00_post": p00_post_h,
        "p01_post": p01_post_h,
        "p11_post": p11_post_h,
    }
    code = {
        "z_pred": state_p[0],
        "p00_pred": p_p[0][0],
        "p01_pred": p_p[0][1],
        "p11_pred": p_p[1][1],
        "innovation_v": innov,
        "s": h[0] * (p_p[0][0] * h[0] + p_p[0][1] * h[1]) + r_v,
        "k0": k0,
        "k1": (p_p[1][0] * h[0] + p_p[1][1] * h[1])
        / (h[0] * (p_p[0][0] * h[0] + p_p[0][1] * h[1]) + r_v),
        "z_post": z_u[0],
        "p00_post": p_u[0][0],
        "p01_post": p_u[0][1],
        "p11_post": p_u[1][1],
    }
    diffs = {key: abs(hand[key] - code[key]) for key in hand}
    return {
        "predicted_v": round(v_p, 6),
        "innovation_mv": round(innov * 1000, 4),
        "k_soc_per_v": round(k0, 4),
        "z_after": round(z_u[0], 6),
        "p00_after": round(p_u[0][0], 8),
        "pd": is_positive_definite_2x2(p_u),
        "expected_z_jump_pp": round(0.004 / OCV_SLOPE * 100, 3),
        "hand": {k: round(v, 12) for k, v in hand.items()},
        "code": {k: round(v, 12) for k, v in code.items()},
        "max_abs_diff": max(diffs.values()),
        "checkpoints": {k: v <= 1e-9 for k, v in diffs.items()},
    }


def convergence_from_wrong_init() -> dict:
    """Wrong initial SOC converges via updates; wrong bias needs excitation."""
    z_true, b_true = 0.60, TRUE_BIAS_A
    state = [0.50, 0.0]
    p = [[0.01, 0.0], [0.0, 0.0004]]
    h = [OCV_SLOPE, 0.0]
    r_v = (0.002) ** 2
    zs = []
    for k in range(40):
        i = 2.0 if k < 20 else -2.0  # 前半放电后半充电，激励偏置可观
        # 测量与预测步对齐到同一时刻：先推进真值，再生成测量
        z_true -= (i - b_true) * DT_S / (3600 * Q_AH)
        v_meas = OCV_SLOPE * z_true  # 偏差形式测量
        state_p, p_p, v_p = predict(state, p, i, 1e-8, 1e-8)
        state, p, innov, _k = update(state_p, p_p, v_meas, v_p, h, r_v)
        zs.append(round(state[0], 4))
    return {
        "z_final": zs[-1],
        "z_final_error_pp": round((zs[-1] - z_true) * 100, 3),
        "b_final_a": round(state[1], 5),
        "b_final_error_ma": round((state[1] - b_true) * 1000, 2),
        "rested_zero_input": False,
        "conclusion": "交替电流激励下初值误差收敛；偏置在本组 Q/R 与采样下基本不收敛，D14 讨论激励强度与信噪比条件",
    }


def bad_qr_behaviour() -> dict:
    """R 设 0：滤波器相信观测，过程噪声无处安放；Q 设 0 且初值错：永不收敛。"""
    state = [0.50, 0.0]
    p = [[0.0025, 0.0], [0.0, 0.0001]]
    h = [OCV_SLOPE, 0.0]
    z_true = 0.60
    zs_r0 = []
    for _k in range(20):
        v_meas = OCV_SLOPE * z_true  # 偏差形式测量
        state_p, p_p, v_p = predict(state, p, 0.0, 1e-8, 1e-8)
        state, p, innov, _k2 = update(state_p, p_p, v_meas, v_p, h, 1e-12)
        zs_r0.append(round(state[0], 4))
    p_trace_after = round(p[0][0] + p[1][1], 8)
    return {
        "r_zero_z_path": zs_r0[:3] + zs_r0[-3:],
        "p_trace_after_r0": p_trace_after,
        "conclusion": "R→0 让协方差塌缩（P 迹 → 0），滤波器锁死初值；Q/R 是结构与激励的账，不是调参旋钮",
    }


# --- 回放工况：D12 四列合同 + 两状态 EKF -------------------------------------


def meter_noise_mv(index: int, sigma_mv: float = METER_SIGMA_MV) -> float:
    """Deterministic Irwin-Hall noise: 12 LCG uniforms minus 6, scaled by sigma.

    Deterministic on purpose: every frozen number in the book must be reproducible
    from the repository alone (no RNG version dependence).
    """
    x = (0x2545F491 + index * 0x9E3779B1) & 0x7FFFFFFF
    total = 0.0
    for _ in range(12):
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        total += (x + 0.5) / 0x80000000
    return (total - 6.0) * sigma_mv


def generate_profile(*, init_soc_pp: float = PROFILE_INIT_SOC_PP,
                     load_from_s: float = PROFILE_LOAD_FROM_S,
                     load_to_s: float = PROFILE_LOAD_TO_S,
                     end_s: float = PROFILE_END_S,
                     discharge_a: float = PROFILE_DISCHARGE_A,
                     capacity_ah: float = PROFILE_Q_TRUE_AH,
                     bias_a: float = PROFILE_BIAS_A,
                     meter_sigma_mv: float = METER_SIGMA_MV) -> list[dict]:
    """内置合成工况：静置 → 恒流放电 → 静置，D12 四列格式。

    current_a 是传感器读数（物理电流 + bias_a），因为偏置是待估计状态；
    true_soc_pp 由物理电流积分，只用于评分。负载拍 v_meas 为空（端电压不是
    OCV），静置拍 v_meas = 真值 OCV + 确定性表计噪声。合成数据，不是实测。
    """
    frames = []
    true_soc = init_soc_pp
    noise_index = 0
    steps = int(round(end_s / PROFILE_DT_S)) + 1
    for i in range(steps):
        t = i * PROFILE_DT_S
        i_true = discharge_a if load_from_s < t <= load_to_s else 0.0
        if i > 0:
            true_soc -= i_true * PROFILE_DT_S / 3600.0 / capacity_ah * 100.0
        current_meas = i_true + bias_a
        if i_true > 0:
            v_meas = None
        else:
            v_meas = ocv_v(true_soc / 100.0) + meter_noise_mv(noise_index, meter_sigma_mv) / 1000.0
            noise_index += 1
        frames.append(
            {"t_s": t, "current_a": current_meas, "v_meas": v_meas, "true_soc_pp": true_soc}
        )
    return frames


def load_profile(path: Path) -> list[dict]:
    """Load a four-column profile; every malformed input is a ValueError (CLI exit 2)."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != PROFILE_COLUMNS:
            raise ValueError(
                f"表头必须为 {','.join(PROFILE_COLUMNS)}，实际 {reader.fieldnames}"
            )
        frames = []
        last_t: float | None = None
        for lineno, row in enumerate(reader, start=2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"第 {lineno} 行列数不足")
            try:
                t_s = float(row["t_s"])
                current_a = float(row["current_a"])
                true_soc_pp = float(row["true_soc_pp"])
            except ValueError as exc:
                raise ValueError(f"第 {lineno} 行字段无法解析: {exc}") from exc
            v_raw = (row["v_meas"] or "").strip()
            v_meas: float | None = None
            if v_raw != "":
                try:
                    v_meas = float(v_raw)
                except ValueError as exc:
                    raise ValueError(f"第 {lineno} 行 v_meas 无法解析: {v_raw!r}") from exc
                if not math.isfinite(v_meas):
                    raise ValueError(f"第 {lineno} 行 v_meas 非有限: {v_raw}")
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
                    "v_meas": v_meas,
                    "true_soc_pp": true_soc_pp,
                }
            )
    if not frames:
        raise ValueError("工况为空")
    return frames


def write_profile_csv(frames: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=PROFILE_COLUMNS)
        writer.writeheader()
        for frame in frames:
            writer.writerow(frame)


def write_series_csv(rows: list[dict], coulomb: list[dict], path: Path) -> None:
    fields = ["t_s", "true_soc_pp", "coulomb_soc_pp", "ekf_soc_pp", "innovation_mv", "rejected"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row, c in zip(rows, coulomb, strict=True):
            writer.writerow(
                {
                    "t_s": row["t_s"],
                    "true_soc_pp": round(row["true_soc_pp"], 4),
                    "coulomb_soc_pp": round(c["z_pp"], 4),
                    "ekf_soc_pp": round(row["z_pp"], 4),
                    "innovation_mv": "" if row["innovation_mv"] is None else round(row["innovation_mv"], 4),
                    "rejected": int(row["rejected"]),
                }
            )


def _metrics(rows: list[dict], frames: list[dict]) -> dict:
    errors = [row["z_pp"] - frame["true_soc_pp"]
              for row, frame in zip(rows, frames, strict=True)]
    return {
        "final_error_pp": round(errors[-1], 4),
        "mean_abs_error_pp": round(sum(abs(e) for e in errors) / len(errors), 4),
        "max_abs_error_pp": round(max(abs(e) for e in errors), 4),
        "rms_error_pp": round(math.sqrt(sum(e * e for e in errors) / len(errors)), 4),
    }


def run_coulomb(frames: list[dict], *, capacity_ah: float = PROFILE_Q_HAT_AH,
                initial_soc_pp: float | None = None) -> dict:
    """Pure coulomb bookkeeping on the same measured current (no OCV update)."""
    if initial_soc_pp is None:
        initial_soc_pp = PROFILE_INIT_SOC_PP - PROFILE_INIT_ERROR_PP
    z = initial_soc_pp
    rows = []
    last_t: float | None = None
    for frame in frames:
        dt = 0.0 if last_t is None else frame["t_s"] - last_t
        z -= frame["current_a"] * dt / 3600.0 / capacity_ah * 100.0
        rows.append({"t_s": frame["t_s"], "z_pp": z})
        last_t = frame["t_s"]
    return {"rows": rows, "metrics": _metrics(rows, frames)}


def run_ekf(frames: list[dict], *, capacity_ah: float = PROFILE_Q_HAT_AH,
            initial_soc_pp: float | None = None, initial_bias_a: float = 0.0,
            q_z: float = Q_Z, q_b: float = Q_B, r_v: float = R_V,
            p0_soc_var: float = P0_SOC_VAR, p0_bias_var: float = P0_BIAS_VAR,
            ocv_offset_v: float = 0.0, gate_sigma: float | None = GATE_SIGMA) -> dict:
    """Replay the profile with a 2-state EKF; rest frames update, load frames predict only.

    The innovation gate is a normalized test: |innovation| / sqrt(S) > gate_sigma
    rejects the observation and leaves the state at its prediction. gate_sigma=None
    disables the gate (used only to show what an outlier would do).
    """
    if initial_soc_pp is None:
        initial_soc_pp = PROFILE_INIT_SOC_PP - PROFILE_INIT_ERROR_PP
    state: list[float] = [initial_soc_pp / 100.0, initial_bias_a]
    p: list[list[float]] = [[p0_soc_var, 0.0], [0.0, p0_bias_var]]
    rows = []
    last_t: float | None = None
    updates = 0
    rejected = 0
    for frame in frames:
        dt = 0.0 if last_t is None else frame["t_s"] - last_t
        state_pred, p_pred, _v_dev = predict(
            state, p, frame["current_a"], q_z, q_b, dt_s=dt, capacity_ah=capacity_ah
        )
        innovation_v: float | None = None
        innovation_sigma_v: float | None = None
        normalized: float | None = None
        updated = False
        gate_rejected = False
        s = 0.0
        v_meas = frame["v_meas"]
        if v_meas is not None:
            v_pred = ocv_v(state_pred[0]) + ocv_offset_v
            innovation = v_meas - v_pred
            h = [ocv_slope(state_pred[0]), 0.0]
            s = h[0] * h[0] * p_pred[0][0] + r_v
            sigma_v = math.sqrt(s)
            norm = innovation / sigma_v
            if gate_sigma is not None and abs(norm) > gate_sigma:
                gate_rejected = True
                rejected += 1
                state = state_pred
                p = p_pred
            else:
                state, p, s, _gain = kalman_step(state_pred, p_pred, innovation, h, r_v)
                updated = True
                updates += 1
            innovation_v = innovation
            innovation_sigma_v = sigma_v
            normalized = norm
        else:
            state = state_pred
            p = p_pred
        rows.append(
            {
                "t_s": frame["t_s"],
                "true_soc_pp": frame["true_soc_pp"],
                "z_pp": state[0] * 100.0,
                "z_pred_pp": state_pred[0] * 100.0,
                "bias_a": state[1],
                "innovation_mv": None if innovation_v is None else innovation_v * 1000.0,
                "innovation_sigma_mv": None if innovation_sigma_v is None else innovation_sigma_v * 1000.0,
                "normalized_innovation": normalized,
                "updated": updated,
                "rejected": gate_rejected,
            }
        )
        last_t = frame["t_s"]
    shifts = [abs(row["z_pp"] - row["z_pred_pp"]) for row in rows if row["updated"]]
    settled_shifts = shifts[3:] if len(shifts) > 3 else shifts
    return {
        "rows": rows,
        "metrics": _metrics(rows, frames),
        "updates": updates,
        "rejected": rejected,
        "final_bias_a": state[1],
        "max_update_shift_pp": round(max(shifts) if shifts else 0.0, 4),
        "settled_max_update_shift_pp": round(max(settled_shifts) if settled_shifts else 0.0, 4),
        "pd_final": is_positive_definite_2x2(p),
        "capacity_ah": capacity_ah,
        "r_v": r_v,
        "q_z": q_z,
        "ocv_offset_v": ocv_offset_v,
        "gate_sigma": gate_sigma,
    }


def summarize_run(result: dict) -> dict:
    return {k: v for k, v in result.items() if k not in ("rows",)}


# --- 新息白化：χ²（NIS）区间 + 一阶自相关 -------------------------------


def chi2_quantile_wilson_hilferty(df: int, z: float) -> float:
    """Wilson-Hilferty approximation of the chi-square quantile (no scipy)."""
    if df <= 0:
        raise ValueError("df must be positive")
    factor = 2.0 / (9.0 * df)
    return df * (1.0 - factor + z * math.sqrt(factor)) ** 3


def innovation_whitening(result: dict) -> dict:
    """NIS/whitening test on normalized innovations of updated frames.

    Under a model-matched filter, nu_k = innovation_k / sqrt(S_k) is ~N(0, 1):
    the sum of nu_k^2 lies inside the 95% chi-square band, the mean is near 0 and
    the lag-1 autocorrelation is near 0. Passing this test means the filter's own
    uncertainty story is self-consistent; it does NOT mean the model is right.
    """
    norms = [
        row["normalized_innovation"]
        for row in result["rows"]
        if row["updated"] and row["normalized_innovation"] is not None
    ]
    n = len(norms)
    if n < 4:
        raise ValueError("至少需要 4 个更新帧才能做白化检验")
    mean = sum(norms) / n
    centered = [(x - mean) ** 2 for x in norms]
    denom = sum(centered)
    std = math.sqrt(denom / (n - 1))
    nis_sum = sum(x * x for x in norms)
    low = chi2_quantile_wilson_hilferty(n, -1.959964)
    high = chi2_quantile_wilson_hilferty(n, 1.959964)
    ar1 = (
        sum((norms[i] - mean) * (norms[i - 1] - mean) for i in range(1, n)) / denom
        if denom > 0.0
        else 0.0
    )
    return {
        "n": n,
        "mean": round(mean, 4),
        "std": round(std, 4),
        "nis_sum": round(nis_sum, 4),
        "nis_mean": round(nis_sum / n, 4),
        "chi2_95_low": round(low, 4),
        "chi2_95_high": round(high, 4),
        "ar1": round(ar1, 4),
        "within_95": low <= nis_sum <= high,
        "white": low <= nis_sum <= high and abs(mean) <= 2.0 / math.sqrt(n),
    }


def whitening_run(frames: list[dict] | None = None) -> dict:
    """Model-matched control run: true capacity, zero bias, honest R and P0."""
    if frames is None:
        frames = generate_profile(bias_a=0.0)
    return run_ekf(
        frames,
        capacity_ah=PROFILE_Q_TRUE_AH,
        initial_bias_a=0.0,
        q_b=0.0,
        p0_bias_var=0.0,
        gate_sigma=None,
    )


# --- 失配对比：EKF vs 纯库仑计 ------------------------------------------------


def mismatch_comparison(frames: list[dict] | None = None) -> dict:
    """Same frames, same estimator parameters; only the update step differs."""
    if frames is None:
        frames = generate_profile()
    init = PROFILE_INIT_SOC_PP - PROFILE_INIT_ERROR_PP
    variants = {
        "coulomb_only": run_coulomb(frames, initial_soc_pp=init)["metrics"],
        "ekf_nominal": run_ekf(frames)["metrics"],
        "ekf_capacity_fixed": run_ekf(frames, capacity_ah=PROFILE_Q_TRUE_AH)["metrics"],
        "ekf_bias_frozen": run_ekf(frames, q_b=0.0, p0_bias_var=0.0)["metrics"],
        "ekf_ocv_offset_10mv": run_ekf(frames, ocv_offset_v=0.010)["metrics"],
    }
    return {
        "frames": len(frames),
        "variants": variants,
        "conclusion": (
            "静置段 EKF 把容量/偏置造成的漂移拉回观测；OCV 表偏移 10 mV 在 0.8 斜率区只值 1.25 pp，"
            "但它会稳定地把估计拉到表的那条线上——错误在表不在滤波器"
        ),
    }


# --- 边界反例：平坦区 + 错误 Q̂ + OCV 表偏移 ---------------------------------


def flat_region_counterexample() -> dict:
    """Flat plateau, +50% capacity error, +10 mV OCV table offset, nominal Q_z.

    The filter cannot tell an OCV-table offset from a SOC error: in the plateau
    the same 10 mV is worth 12.5 pp, so the estimate is dragged onto the wrong
    line. The innovation is white afterwards because the filter has absorbed the
    model error into the state -- whitening is not correctness. No sensor bias
    here, so the coulomb-only drift isolates the capacity error.
    """
    frames = generate_profile(
        init_soc_pp=FLAT_INIT_SOC_PP,
        load_from_s=PROFILE_LOAD_FROM_S,
        load_to_s=FLAT_LOAD_TO_S,
        end_s=FLAT_END_S,
        discharge_a=FLAT_DISCHARGE_A,
        bias_a=0.0,  # isolate the capacity error: no sensor bias in the counterexample
    )
    init = FLAT_INIT_SOC_PP - FLAT_INIT_ERROR_PP
    coulomb = run_coulomb(frames, capacity_ah=FLAT_Q_HAT_AH, initial_soc_pp=init)
    ekf = run_ekf(
        frames,
        capacity_ah=FLAT_Q_HAT_AH,
        initial_soc_pp=init,
        q_z=FLAT_Q_Z,
        ocv_offset_v=FLAT_OCV_OFFSET_V,
    )
    whitening = innovation_whitening(ekf)
    ekf_final = ekf["metrics"]["final_error_pp"]
    coulomb_final = coulomb["metrics"]["final_error_pp"]
    return {
        "frames": len(frames),
        "true_slope": OCV_SLOPE_FLAT,
        "ocv_offset_mv": FLAT_OCV_OFFSET_V * 1000.0,
        "capacity_error_pct": (FLAT_Q_HAT_AH / PROFILE_Q_TRUE_AH - 1.0) * 100.0,
        "q_z": FLAT_Q_Z,
        "coulomb_only": coulomb["metrics"],
        "ekf": ekf["metrics"],
        "whitening": whitening,
        "rejected": ekf["rejected"],
        "max_update_shift_pp": ekf["max_update_shift_pp"],
        "settled_max_update_shift_pp": ekf["settled_max_update_shift_pp"],
        "harmful": abs(ekf_final) > abs(coulomb_final),
        "conclusion": (
            "平坦区 10 mV 表偏移 = 12.5 pp：首次更新把估计一次拉走 10.5 pp，"
            "随后收敛到错的 OCV 线上并停在那里；新息白化、门限不报警——新息白不等于模型对"
        ),
    }


def build_report(profile_replay: dict | None = None) -> dict:
    frames = generate_profile()
    nominal = run_ekf(frames)
    coulomb = run_coulomb(frames)
    report = {
        "scenario_id": SCENARIO_ID,
        "identity": (
            "teaching EKF mechanics on the S2/D11/D12 chain; units documented per cell; "
            "synthetic scenario, not device measurement or human acceptance"
        ),
        "hand_round": one_round_hand(),
        "convergence": convergence_from_wrong_init(),
        "bad_qr": bad_qr_behaviour(),
        "replay": {
            "scenario_id": REPLAY_SCENARIO_ID,
            "frames": len(frames),
            "coulomb_only": coulomb["metrics"],
            "ekf": nominal["metrics"],
            "updates": nominal["updates"],
            "rejected": nominal["rejected"],
            "final_bias_a": round(nominal["final_bias_a"], 5),
            "max_update_shift_pp": nominal["max_update_shift_pp"],
            "settled_max_update_shift_pp": nominal["settled_max_update_shift_pp"],
        },
        "mismatch": mismatch_comparison(frames),
        "whitening": innovation_whitening(whitening_run()),
        "boundary": flat_region_counterexample(),
    }
    if profile_replay is not None:
        report["profile_replay"] = profile_replay
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 等工件的目录")
    parser.add_argument(
        "--profile",
        type=Path,
        help="回放工况 CSV（t_s,current_a,v_meas,true_soc_pp）；缺省用内置合成工况",
    )
    args = parser.parse_args(argv)
    frames: list[dict] | None = None
    replay: dict | None = None
    if args.profile:
        try:
            frames = load_profile(args.profile)
        except (OSError, ValueError) as exc:
            print(f"profile 拒绝：{exc}", file=sys.stderr)
            return 2
        result = run_ekf(frames)
        replay = summarize_run(result)
    else:
        frames = generate_profile()
        result = run_ekf(frames)
    report = build_report(profile_replay=replay)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        write_profile_csv(frames, args.out / "profile.csv")
        write_series_csv(result["rows"], run_coulomb(frames)["rows"],
                         args.out / "ekf_series.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
