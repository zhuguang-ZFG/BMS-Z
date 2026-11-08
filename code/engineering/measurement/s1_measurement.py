"""S1 measurement-chain reference implementation.

Teaching scenario ``S1-sense-chain``: a 16-cell pack sampled through one AFE.
All thresholds are teaching values, not product limits. Only the standard library
is used so every number in the chapter can be recomputed.

Conventions: voltage in V, current in A, time in s, SOC as a 0-1 ratio.
The engineering (new) side uses discharge-positive current; this module only
handles voltages, timings and error terms, so no current sign is involved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path

SCENARIO_ID = "S1-sense-chain"
FILTER_SCENARIO_ID = "S1-filter-post-afe"
SCAN_SCENARIO_ID = "S1-scan-settling"
GENERATOR = "s1_measurement.py v1 (standard library)"


@dataclass(frozen=True)
class ChainConfig:
    """Frozen teaching configuration for the measurement chain."""

    cells: int = 16
    tau_s: float = 100e-6  # input RC settling (first-order, teaching model)
    settle_ratio: float = 500.0  # 500 mV step to 1 mV
    settle_step_v: float = 0.5
    per_cell_overhead_s: float = 20e-6  # mux switch + conversion overhead
    sample_period_s: float = 20e-3
    task_budget_s: float = 10e-3
    confirm_samples: int = 3
    decision_s: float = 2e-3
    actuator_feedback_s: float = 15e-3
    first_high_latency_s: float = 20e-3  # physical step -> first high AFE output
    threshold_v: float = 4.2
    step_v: float = 0.2  # 4.1 V -> 4.3 V, in volts
    filter_windows: tuple[int, ...] = (1, 5, 9)
    rss_limit_mv: tuple[float, ...] = (2.0, 1.2, 0.8, 0.5)
    sigma_mv: tuple[float, float] = (0.6, 0.8)
    calibration_gain: float = 1.002
    calibration_offset_v: float = 0.012
    calibration_point_v: float = 3.7
    calibration_check_v: tuple[float, ...] = (3.0, 4.2)
    fti_window_s: float = 100e-3

    def identity(self) -> dict:
        payload = asdict(self)
        payload["filter_windows"] = list(self.filter_windows)
        return payload


def replace_config(cfg: ChainConfig, **changes) -> ChainConfig:
    return replace(cfg, **changes)


def worst_case_mv(limits_mv: tuple[float, ...]) -> float:
    """Same-sign superposition of absolute limits."""
    return math.fsum(abs(value) for value in limits_mv)


def rss_mv(sigmas_mv: tuple[float, ...]) -> float:
    """Square root of summed variances; not an absolute bound."""
    return math.sqrt(math.fsum(value * value for value in sigmas_mv))


def correlated_sigma_mv(sigma_a_mv: float, sigma_b_mv: float, rho: float) -> float:
    """Standard deviation of a sum of two sources with correlation ``rho``."""
    if not -1.0 <= rho <= 1.0:
        raise ValueError("rho must lie in [-1, 1]")
    variance = sigma_a_mv**2 + sigma_b_mv**2 + 2.0 * rho * sigma_a_mv * sigma_b_mv
    return math.sqrt(max(variance, 0.0))


def mean_variance_factor(samples: int, rho: float = 0.0) -> float:
    """Variance of the sample mean relative to one sample (exchangeable rho)."""
    if samples < 1:
        raise ValueError("samples must be >= 1")
    if not -1.0 <= rho <= 1.0:
        raise ValueError("rho must lie in [-1, 1]")
    return (1.0 + (samples - 1) * rho) / samples


def single_point_calibration(cfg: ChainConfig) -> dict:
    """Offset-only correction at one known voltage; residual at other points."""
    raw_at_cal = cfg.calibration_gain * cfg.calibration_point_v + cfg.calibration_offset_v
    correction_v = cfg.calibration_point_v - raw_at_cal
    residuals = {}
    for point in cfg.calibration_check_v:
        raw = cfg.calibration_gain * point + cfg.calibration_offset_v
        residuals[point] = raw + correction_v - point
    return {
        "correction_v": correction_v,
        "correction_mv": correction_v * 1000.0,
        "residual_v": residuals,
        "residual_mv": {point: value * 1000.0 for point, value in residuals.items()},
        "residual_scale_v_per_v": cfg.calibration_gain - 1.0,
    }


def settling_time_s(tau_s: float, ratio: float) -> float:
    """Time for a first-order response to shrink by ``ratio``."""
    if tau_s <= 0 or ratio <= 1:
        raise ValueError("tau must be positive and ratio > 1")
    return tau_s * math.log(ratio)


def settling_residual_v(step_v: float, tau_s: float, at_s: float) -> float:
    if tau_s <= 0 or at_s < 0:
        raise ValueError("tau must be positive and time non-negative")
    return abs(step_v) * math.exp(-at_s / tau_s)


def sequential_scan_s(cfg: ChainConfig) -> dict:
    """Settle plus per-cell overhead for every cell, plus the switch settling."""
    settle = settling_time_s(cfg.tau_s, cfg.settle_ratio)
    per_cell = settle + cfg.per_cell_overhead_s
    total = cfg.cells * per_cell
    return {
        "settle_per_cell_s": settle,
        "per_cell_s": per_cell,
        "total_s": total,
        "per_cell_margin_s": cfg.sample_period_s - per_cell,
        "sample_period_margin_s": cfg.sample_period_s - total,
        "total_margin_s": cfg.task_budget_s - total,
    }


def moving_average(values: list[float], window: int) -> list[float | None]:
    """Causal trailing mean; ``None`` until a full window exists."""
    if window < 1:
        raise ValueError("window must be >= 1")
    result: list[float | None] = []
    for index in range(len(values)):
        if index + 1 < window:
            result.append(None)
        else:
            chunk = values[index + 1 - window:index + 1]
            result.append(math.fsum(chunk) / window)
    return result


def center_moving_average(values: list[float], window: int) -> list[float]:
    """Non-causal comparison; uses future samples, so never valid for protection."""
    if window < 1 or window % 2 == 0:
        raise ValueError("window must be a positive odd number")
    half = window // 2
    out = []
    for index in range(len(values)):
        chunk = values[max(0, index - half):min(len(values), index + half + 1)]
        out.append(math.fsum(chunk) / len(chunk))
    return out


def first_crossing(values: Sequence[float | None], threshold: float) -> int | None:
    for index, value in enumerate(values):
        if value is not None and value >= threshold:
            return index
    return None


def filter_step_case(cfg: ChainConfig) -> dict:
    """Step 4.1 -> 4.3 V sampled every Ts; report first crossing per window.

    The step happens just after a sample; AFE output is high from the next sample.
    Only the post-AFE digital filter is modelled here.
    """
    pre = [4.1] * 12
    post = [4.3] * 40
    samples = pre + post
    first_high = 12  # first sample taken after the physical step
    rows = {}
    for window in cfg.filter_windows:
        filtered = moving_average(samples, window)
        crossing = first_crossing(filtered, cfg.threshold_v)
        if crossing is None:
            raise AssertionError("window never crosses; scenario expects a crossing")
        rows[window] = {
            "first_crossing_index": crossing,
            "delay_from_first_high_samples": crossing - first_high,
            "delay_from_first_high_s": (crossing - first_high) * cfg.sample_period_s,
        }
    centered = center_moving_average(samples, 5)
    centered_crossing = first_crossing(centered, cfg.threshold_v)
    return {
        "first_high_index": first_high,
        "windows": rows,
        "centered_window5_crossing_index": centered_crossing,
        "centered_uses_future_samples": True,
    }


def confirmation_delay_s(cfg: ChainConfig) -> float:
    if cfg.confirm_samples < 1:
        raise ValueError("confirm_samples must be >= 1")
    return (cfg.confirm_samples - 1) * cfg.sample_period_s


def feedback_budget_s(cfg: ChainConfig) -> dict:
    """Worst-case physical fault -> verified feedback for each filter window."""
    confirm = confirmation_delay_s(cfg)
    rows = {}
    for window, row in filter_step_case(cfg)["windows"].items():
        total = (
            cfg.first_high_latency_s
            + row["delay_from_first_high_s"]
            + confirm
            + cfg.decision_s
            + cfg.actuator_feedback_s
        )
        rows[window] = {
            "total_s": total,
            "within_fti": total <= cfg.fti_window_s,
        }
    return {"confirmation_s": confirm, "windows": rows}


def build_report(cfg: ChainConfig | None = None) -> dict:
    cfg = cfg or ChainConfig()
    calibration = single_point_calibration(cfg)
    scan = sequential_scan_s(cfg)
    five_tau = settling_residual_v(cfg.settle_step_v, cfg.tau_s, 5 * cfg.tau_s)
    budget = feedback_budget_s(cfg)
    return {
        "scenario_id": SCENARIO_ID,
        "filter_scenario_id": FILTER_SCENARIO_ID,
        "scan_scenario_id": SCAN_SCENARIO_ID,
        "generator": GENERATOR,
        "config": cfg.identity(),
        "worst_case_mv": worst_case_mv(cfg.rss_limit_mv),
        "rss_mv": rss_mv(cfg.rss_limit_mv),
        "rss_is_bound": False,
        "correlated_sigma_mv": {
            str(rho): correlated_sigma_mv(*cfg.sigma_mv, rho) for rho in (0.0, 0.75, 1.0)
        },
        "mean_variance_factor": {
            "independent": {str(n): mean_variance_factor(n) for n in cfg.filter_windows},
            "rho_0.5": {str(n): mean_variance_factor(n, 0.5) for n in cfg.filter_windows},
        },
        "calibration": calibration,
        "settling": {
            "settle_time_s": settling_time_s(cfg.tau_s, cfg.settle_ratio),
            "five_tau_residual_mv": five_tau * 1000.0,
        },
        "scan": scan,
        "filter": filter_step_case(cfg),
        "budget": budget,
        "limitations": [
            "All values are teaching parameters, not product limits.",
            "The RC settling model is first-order; real AFE input networks differ.",
            "Filter delay is computed after the AFE output, not from the physical step.",
            "No hardware, bench or reader evidence is included.",
        ],
    }


def write_evidence(out_dir: Path, cfg: ChainConfig | None = None) -> dict:
    cfg = cfg or ChainConfig()
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(cfg)
    digest = hashlib.sha256(
        (json.dumps(report["config"], sort_keys=True) + GENERATOR).encode("utf-8")
    ).hexdigest()
    report["config_sha256"] = "sha256:" + digest
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (out_dir / "report.json").write_text(text, encoding="utf-8")
    return json.loads(text)


def student_questions() -> list[str]:
    return [
        "把每串转换开销从 20 µs 改成 10 µs，16 串扫描还超 10 ms 吗？",
        "把确认拍数从 3 改成 2，反馈预算各窗变成多少？哪些窗进入 100 ms？",
        "若滤波窗改为 7 拍，群延迟是多少？为什么不是 7×Ts？",
        "用双点校准（3.0 V 与 4.2 V）代替单点校准，残差在 3.7 V 是多少？",
        "说明为什么把居中平均用于实时保护不合法，并给出一个反例输入。",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write report.json to this directory")
    parser.add_argument("--students", action="store_true", help="print student tasks")
    args = parser.parse_args()
    if args.students:
        for index, question in enumerate(student_questions(), 1):
            print(f"{index}. {question}")
        return 0
    if args.out:
        report = write_evidence(args.out)
        print(f"wrote {args.out / 'report.json'}  scenario={report['scenario_id']}")
        return 0
    parser.error("choose --out or --students")


if __name__ == "__main__":
    raise SystemExit(main())
