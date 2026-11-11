"""Teaching experiments for D12: SOC baseline bookkeeping and OCV calibration.

Frozen teaching chain (extends S2/D02): Q = 2 Ah; bias/initial/capacity errors
each propagate differently. OCV calibration conditions come from D01/D02:
rest time must outlast polarization; the OCV slope decides whether a voltage
observation can even correct SOC (flat region cannot); hysteresis branch must
match (D2.4).

Scenario ``D12-profile-replay``: a synthetic current-profile time series with
an independent truth column. Coulomb-only estimation drifts (init error +
sensor bias + capacity gain); rest-window OCV corrections are tuned on one
window and validated on a held-out window, so the report can show when
correction helps and when it harms (prior error below the window residual).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

SCENARIO_ID = "D12-soc-baseline"
PROFILE_SCENARIO_ID = "D12-profile-replay"

Q_AH = 2.0
BIAS_A = 0.05               # 电流传感偏置（教学值）
HOURS = 1.0
INIT_ERROR_PP = 10.0
CAPACITY_ERROR_PCT = 5.0
OCV_SLOPE_STEEP = 0.8       # V/SOC（NMC 类，教学值）
OCV_SLOPE_FLAT = 0.08       # V/SOC（LFP 平台，教学值）
HYSTERESIS_WIDTH_MV = 10.0


def bias_drift_pp(bias_a: float = BIAS_A, hours: float = HOURS, q_ah: float = Q_AH) -> float:
    if q_ah <= 0 or hours < 0:
        raise ValueError("capacity must be positive, hours nonnegative")
    return bias_a * hours * 3600.0 / (3600.0 * q_ah) * 100.0


def capacity_gain_error_pp(true_delta_pp: float = 100.0, capacity_error_pct: float = CAPACITY_ERROR_PCT) -> float:
    """容量误差是 Δz 的增益误差：同一真值变化被错除。"""
    if true_delta_pp == 0:
        return 0.0
    wrong_q = Q_AH * (1.0 + capacity_error_pct / 100.0)
    measured = true_delta_pp * Q_AH / wrong_q
    return true_delta_pp - measured


def ocv_correction_gain(slope_v_per_soc: float) -> float:
    """一阶修正强度：斜率越平，同样的电压观测对 SOC 的约束越弱（0 = 不可校正）。"""
    if slope_v_per_soc < 0:
        raise ValueError("slope must be nonnegative")
    return slope_v_per_soc


def calibration_residual_pp(voltage_error_mv: float, slope_v_per_soc: float,
                            hysteresis_mv: float = 0.0) -> float:
    """校准残差 =（电压误差 + 迟滞失配）/ 斜率；平坦区与迟滞失配都会放大或废掉校正。"""
    if slope_v_per_soc <= 0:
        raise ValueError("slope must be positive for calibration")
    return (voltage_error_mv + hysteresis_mv) / (slope_v_per_soc * 1000.0) * 100.0 * 100.0 / 100.0


# --- D12-profile-replay：时间序列回放 + 独立工况 + 可执行校正 ---

PROFILE_COLUMNS = ["t_s", "current_a", "v_meas", "true_soc_pp"]
PROFILE_Q_TRUE_AH = 2.0     # 真值容量（生成工况用）
PROFILE_Q_HAT_AH = 2.1      # 估计容量（+5% 教学误差，同 CAPACITY_ERROR_PCT）
PROFILE_INIT_SOC_PP = 80.0
PROFILE_INIT_ERROR_PP = 10.0  # 估计初值偏高（同 INIT_ERROR_PP）
PROFILE_BIAS_A = 0.05       # 电流传感偏置（同 BIAS_A，静置段也存在）
PROFILE_DT_S = 60.0
PROFILE_END_S = 2700.0
PROFILE_DISCHARGE_A = 2.0
PROFILE_DISCHARGE_FROM_S = 600.0
PROFILE_DISCHARGE_TO_S = 2100.0
METER_ERROR_MV = 5.0        # 校准点表计误差（教学值，由生成器烘进 v_meas）
RELIABLE_RESIDUAL_PP = 5.0  # 残差超过此值的窗口不得作为验收依据
GAIN_CANDIDATES = (0.5, 1.0)  # 只比较半校正/全校正，不自由拟合（避免把表计误差吸进增益）
REST_GATE_FRAMES = 5        # 静置门：连续 5 拍（300 s）静置且有观测才允许校正

# 静置窗（按时间段圈定，是否可校正由静置门判定）：(id, 角色, 段起 t_s, 段止 t_s)。
# W1 用于调校增益，W2 留出验证，不得反向使用。
REST_WINDOWS = [
    ("W1_tune", "tune", 0.0, PROFILE_DISCHARGE_FROM_S),
    ("W2_validate", "validate", PROFILE_DISCHARGE_TO_S, PROFILE_END_S),
]


def ocv_v(soc_fraction: float) -> float:
    """教学分段 OCV：≥60% 斜率 0.8 V/SOC，以下平台 0.08（连续）。"""
    if soc_fraction >= 0.6:
        return 3.2 + 0.8 * soc_fraction
    return 3.2 + 0.8 * 0.6 + 0.08 * (soc_fraction - 0.6)


def ocv_slope(soc_fraction: float) -> float:
    return OCV_SLOPE_STEEP if soc_fraction >= 0.6 else OCV_SLOPE_FLAT


def generate_profile(
    meter_error_mv: float = METER_ERROR_MV, hysteresis_mv: float = 0.0
) -> list[dict]:
    """内置合成工况：80% 静置 10 min → 2 A 放电 25 min（ΔSOC 41.67 pp）→ 静置 10 min。

    观测与参考分离：v_meas 是电压观测列（负载拍为空——端电压不等于 OCV，
    模型不提供该拍观测）；true_soc_pp 是评分用参考真值，回放时只是数据，
    不参与生成观测。表计误差与迟滞失配由生成器参数烘进 v_meas（放电分支
    静置窗带迟滞偏移）。合成数据，不是实测（SRC01 未闭合）。
    """
    frames = []
    true_soc = PROFILE_INIT_SOC_PP
    discharge_seen = False
    for i in range(int(PROFILE_END_S / PROFILE_DT_S) + 1):
        t = i * PROFILE_DT_S
        current = (
            PROFILE_DISCHARGE_A
            if PROFILE_DISCHARGE_FROM_S < t <= PROFILE_DISCHARGE_TO_S
            else 0.0
        )
        if i > 0:
            true_soc -= current * PROFILE_DT_S / 3600.0 / PROFILE_Q_TRUE_AH * 100.0
        if current > 0:
            discharge_seen = True
            v_meas = None  # 负载拍无端电压观测
        else:
            v_meas = (
                ocv_v(true_soc / 100.0)
                + meter_error_mv / 1000.0
                - (hysteresis_mv / 1000.0 if discharge_seen else 0.0)
            )
        frames.append(
            {"t_s": t, "current_a": current, "v_meas": v_meas, "true_soc_pp": true_soc}
        )
    return frames


def load_profile(path: Path) -> list[dict]:
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


def write_series_csv(frames: list[dict], coulomb: list[float], corrected: list[float], path: Path) -> None:
    fields = ["t_s", "true_soc_pp", "coulomb_soc_pp", "corrected_soc_pp"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for frame, c, x in zip(frames, coulomb, corrected, strict=True):
            writer.writerow(
                {
                    "t_s": frame["t_s"],
                    "true_soc_pp": round(frame["true_soc_pp"], 4),
                    "coulomb_soc_pp": round(c, 4),
                    "corrected_soc_pp": round(x, 4),
                }
            )


def _correct(soc_est_pp: float, v_meas: float) -> tuple[float, float, float]:
    """按 OCV 反演校正一帧；返回 (全校正后 SOC, 斜率, delta_pp)。"""
    slope = ocv_slope(soc_est_pp / 100.0)
    v_pred = ocv_v(soc_est_pp / 100.0)
    delta_pp = (v_meas - v_pred) / slope * 100.0
    return soc_est_pp + delta_pp, slope, delta_pp


def _rest_gate_index(frames: list[dict], start_s: float, end_s: float) -> int | None:
    """段内第一个满足静置门的帧下标：连续 REST_GATE_FRAMES 拍静置且有观测。"""
    segment = [i for i, f in enumerate(frames) if start_s <= f["t_s"] <= end_s]
    for i in segment:
        window = frames[i - REST_GATE_FRAMES + 1 : i + 1]
        if len(window) < REST_GATE_FRAMES:
            continue
        if all(f["current_a"] == 0.0 and f["v_meas"] is not None for f in window):
            return i
    return None


def replay_profile(frames: list[dict], v_uncertainty_mv: float = 5.0) -> dict:
    """回放工况：库仑计 vs 库仑计+静置窗 OCV 校正（调校/验证隔离 + 静置门）。

    估计器用 Q_hat=2.1 Ah 与含偏置电流积分；校正只读 v_meas 观测列，评分只读
    true_soc_pp 参考列——改参考真值不会移动估计轨迹。增益只在 W1 从
    GAIN_CANDIDATES 中选取（残差最小者），W2 为留出验证窗，不得反向使用。
    窗口内无连续 REST_GATE_FRAMES 拍静置观测则拒校正（corrected=false）。

    残差口径分离：residual_pp 是声明的观测不确定度 v_uncertainty_mv 经斜率
    传播的验收上限（先验，不是后验精度）；posterior_v_residual_mv 是全校正后
    电压观测与模型 OCV 的剩余差（同一线性分段内约为 0，只用于发现分段不一致）；
    error_before/after_pp 是对独立参考真值的评分。三者不得互相替代。
    """
    coulomb = [PROFILE_INIT_SOC_PP + PROFILE_INIT_ERROR_PP]
    corrected = [PROFILE_INIT_SOC_PP + PROFILE_INIT_ERROR_PP]
    for prev, frame in zip(frames, frames[1:], strict=False):
        dt = frame["t_s"] - prev["t_s"]
        measured_a = frame["current_a"] + PROFILE_BIAS_A
        drop_pp = measured_a * dt / 3600.0 / PROFILE_Q_HAT_AH * 100.0
        coulomb.append(coulomb[-1] - drop_pp)
        corrected.append(corrected[-1] - drop_pp)

    windows = []
    tuned_gain = None
    for wid, role, start_s, end_s in REST_WINDOWS:
        idx = _rest_gate_index(frames, start_s, end_s)
        if idx is None:
            windows.append(
                {
                    "id": wid,
                    "role": role,
                    "corrected": False,
                    "reason": f"段内无连续 {REST_GATE_FRAMES} 拍（{REST_GATE_FRAMES * PROFILE_DT_S:.0f} s）静置观测，拒校正",
                }
            )
            continue
        true_soc = frames[idx]["true_soc_pp"]
        v_meas = frames[idx]["v_meas"]
        est_before = corrected[idx]
        error_before = est_before - true_soc
        if role == "tune":
            tuned_gain = min(
                GAIN_CANDIDATES,
                key=lambda g: abs(est_before + g * _correct(est_before, v_meas)[2] - true_soc),
            )
            gain = tuned_gain
        else:
            if tuned_gain is None:
                raise ValueError("验证窗之前必须有调校窗（辨识/验证隔离）")
            gain = tuned_gain
        full_pp, slope, _ = _correct(est_before, v_meas)
        est_after = est_before + gain * (full_pp - est_before)
        shift = est_after - est_before
        for i in range(idx, len(corrected)):
            corrected[i] += shift
        # 残差口径：验收上限 = 声明观测不确定度 / 斜率（先验，非后验精度）
        residual_pp = v_uncertainty_mv / (slope * 1000.0) * 100.0
        # 后验电压残差：同一线性分段内约为 0，只作分段一致性诊断
        posterior_v_residual_mv = abs(v_meas - ocv_v(est_after / 100.0)) * 1000.0
        error_after = est_after - true_soc
        windows.append(
            {
                "id": wid,
                "role": role,
                "corrected": True,
                "t_s": frames[idx]["t_s"],
                "rest_frames": REST_GATE_FRAMES,
                "region": "steep" if slope == OCV_SLOPE_STEEP else "flat",
                "slope": slope,
                "gain": gain,
                "error_before_pp": round(error_before, 4),
                "error_after_pp": round(error_after, 4),
                "residual_pp": round(residual_pp, 4),
                "posterior_v_residual_mv": round(posterior_v_residual_mv, 6),
                "harmful": abs(error_after) > abs(error_before),
                "reliable": residual_pp <= RELIABLE_RESIDUAL_PP,
            }
        )

    def metrics(series: list[float]) -> dict:
        errors = [x - f["true_soc_pp"] for x, f in zip(series, frames, strict=True)]
        return {
            "final_error_pp": round(errors[-1], 4),
            "mean_abs_error_pp": round(sum(abs(e) for e in errors) / len(errors), 4),
            "max_abs_error_pp": round(max(abs(e) for e in errors), 4),
        }

    return {
        "scenario_id": PROFILE_SCENARIO_ID,
        "frames": len(frames),
        "coulomb_only": metrics(coulomb),
        "corrected": metrics(corrected),
        "windows": windows,
        "tuned_gain": tuned_gain,
        "gain_candidates": list(GAIN_CANDIDATES),
        "failure_boundary": (
            "校正只在 |校正前误差| > 该窗残差时改善；W2 校正前 1.18 pp < 平坦区残差 "
            "6.25 pp，校正反而扩大到 6.25 pp——先估残差再决定校不校正"
        ),
        "series": {"coulomb": coulomb, "corrected": corrected},
    }


def build_report(profile_replay: dict | None = None) -> dict:
    if profile_replay is None:
        profile_replay = summarize_replay(replay_profile(generate_profile()))
    return {
        "scenario_id": SCENARIO_ID,
        "identity": "teaching chain extending S2/D02; real OCV tables from SRC01",
        "bias_drift_pp_per_h": round(bias_drift_pp(), 2),
        "capacity_gain_error_pp": round(capacity_gain_error_pp(), 2),
        "init_error_pp": INIT_ERROR_PP,
        "ocv_correction": {
            "steep_region": {
                "slope": OCV_SLOPE_STEEP,
                "residual_5mv_pp": round(calibration_residual_pp(5.0, OCV_SLOPE_STEEP), 2),
            },
            "flat_region": {
                "slope": OCV_SLOPE_FLAT,
                "residual_5mv_pp": round(calibration_residual_pp(5.0, OCV_SLOPE_FLAT), 2),
            },
            "hysteresis_mismatch": {
                "slope": OCV_SLOPE_STEEP,
                "residual_0mv_with_10mv_hyst_pp": round(calibration_residual_pp(0.0, OCV_SLOPE_STEEP, HYSTERESIS_WIDTH_MV), 2),
            },
        },
        "conclusion": "偏置漂移 2.5 pp/h；容量误差是增益误差（±4.76 pp）；OCV 校正强度看斜率：5 mV 在 0.8 斜率区残差 0.62 pp、在 0.08 平坦区 6.25 pp；迟滞失配 10 mV 在 0.8 区废掉 1.25 pp",
        "profile_replay": profile_replay,
    }


def summarize_replay(result: dict) -> dict:
    return {k: v for k, v in result.items() if k != "series"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 的目录")
    parser.add_argument(
        "--profile",
        type=Path,
        help="回放工况 CSV（t_s,current_a,true_soc_pp）；缺省用内置合成工况",
    )
    args = parser.parse_args(argv)
    if args.profile:
        try:
            frames = load_profile(args.profile)
        except (OSError, ValueError) as exc:
            print(f"profile 拒绝：{exc}", file=sys.stderr)
            return 2
    else:
        frames = generate_profile()
    result = replay_profile(frames)
    report = build_report(profile_replay=summarize_replay(result))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        write_profile_csv(frames, args.out / "profile.csv")
        write_series_csv(
            frames, result["series"]["coulomb"], result["series"]["corrected"],
            args.out / "soc_series.csv",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
