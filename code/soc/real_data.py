"""NASA RW3 实测实验：准静态 OCV / RC 标定 → 独立随机负载回放 → 误差报告。

python code/soc/real_data.py --plot
默认读取随仓库附带的 CC BY 4.0 实测 CSV，无网络、无 scipy 运行依赖。
SOC 参考是由测量电流和标定容量计算的，不能作为独立 SOC 真值或精度认证。
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np

from cell_model import ocv
from estimators import CoulombOnly, EKFEstimator
from hppc_demo import fit_relaxation
from prepare_nasa import FIELDS, SELECTION

DATA = Path(__file__).parent / "data/nasa_rw3"
NUMERIC = FIELDS[1:]


def load_data(directory: Path) -> tuple[dict[str, dict[str, np.ndarray]], dict]:
    """拒绝坏哈希、NaN、时间倒退或被截断的样本；不偷偷排序、补值或改单位。"""
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    path = directory / "samples.csv"
    if hashlib.sha256(path.read_bytes()).hexdigest() != metadata["csv_sha256"]:
        raise ValueError("CSV SHA-256 与 metadata.json 不符，请重新导出原始数据")
    groups = {name: {key: [] for key in NUMERIC} for name in SELECTION}
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError("CSV 列名或顺序错误，单位须为 s / A / V / °C")
        for line, row in enumerate(reader, 2):
            if row["series"] not in groups:
                raise ValueError(f"第 {line} 行包含未知数据分组")
            for key in NUMERIC:
                value = float(row[key])
                if not np.isfinite(value):
                    raise ValueError(f"第 {line} 行 {key} 不是有限数")
                groups[row["series"]][key].append(value)
    result = {}
    for name, group in groups.items():
        arrays = {key: np.asarray(values) for key, values in group.items()}
        n = len(arrays["time_s"])
        if n != metadata["rows"][name] or n < 3:
            raise ValueError(f"{name} 样本缺失")
        if arrays["time_s"][0] != 0 or np.any(np.diff(arrays["time_s"]) <= 0):
            raise ValueError(f"{name} 时间须从 0 开始并严格递增")
        if np.any(arrays["current_a"] > 0.01):
            raise ValueError(f"{name} 是放电/静置样本，电流方向应为充正放负")
        if np.any((arrays["voltage_v"] < 2) | (arrays["voltage_v"] > 5)):
            raise ValueError(f"{name} 单体电压不在本数据集范围，请检查 V / mV 单位")
        if list(dict.fromkeys(arrays["source_step"].tolist())) != SELECTION[name]:
            raise ValueError(f"{name} 的原始步骤与实验划分不符")
        result[name] = arrays
    return result, metadata


def cumulative_ah(group: dict[str, np.ndarray]) -> np.ndarray:
    """梯形积分：保留变采样间隔；第一条是观测起点，积分为零。"""
    current, time = group["current_a"], group["time_s"]
    increments = (current[:-1] + current[1:]) * 0.5 * np.diff(time) / 3600
    return np.r_[0.0, np.cumsum(increments)]


@dataclass
class OCVTable:
    soc: np.ndarray
    volts: np.ndarray

    def voltage(self, soc: float) -> float:
        return float(np.interp(soc, self.soc, self.volts))

    def slope(self, soc: float) -> float:
        k = int(np.clip(np.searchsorted(self.soc, soc, side="right") - 1, 0, len(self.soc) - 2))
        return float((self.volts[k + 1] - self.volts[k]) / (self.soc[k + 1] - self.soc[k]))


def calibrate(groups: dict) -> tuple[dict, OCVTable]:
    # 这三个标定分组是唯一输入；validation 的电压、温度和参考 SOC 不参与拟合。
    low, capacity, pulse = (groups[name] for name in ("ocv", "capacity", "pulse"))
    q_low = -float(cumulative_ah(low)[-1])
    q_ref = -float(cumulative_ah(capacity)[-1])
    if q_low <= 0 or q_ref <= 0:
        raise ValueError("标定容量必须为正，请检查电流方向与时间")
    low_soc = 1.0 + cumulative_ah(low) / q_low
    unique_soc, indices = np.unique(low_soc[::-1], return_index=True)
    knots = np.linspace(0, 1, 21)
    values = np.interp(knots, unique_soc, low["voltage_v"][::-1][indices])
    table = OCVTable(knots, np.maximum.accumulate(values))
    before, on, after = (pulse["source_step"] == k for k in (5, 6, 7))
    current = float(np.mean(pulse["current_a"][on]))
    r0_on = (float(pulse["voltage_v"][on][0]) - float(pulse["voltage_v"][before][-1])) / current
    r0_off = (float(pulse["voltage_v"][after][0]) - float(pulse["voltage_v"][on][-1])) / -current
    r0 = (r0_on + r0_off) / 2
    time = pulse["time_s"][after] - pulse["time_s"][after][0]
    grid = np.geomspace(1.0, 1000.0, 300)
    tau, amplitude, offset = fit_relaxation(time, pulse["voltage_v"][after], tau_grid=grid)
    if tau in (grid[0], grid[-1]):
        raise ValueError("静置拟合命中 τ 搜索边界，需要重新检查辨识窗与模型")
    # 使用实际时间戳计算脉冲长度；600 秒实验不是标准 10 秒 HPPC。
    duration = float(pulse["time_s"][after][0] - pulse["time_s"][on][0])
    r1 = amplitude / (current * (1 - np.exp(-duration / tau)))
    if r0 <= 0 or r1 <= 0:
        raise ValueError("辨识得到非正电阻，不能继续套入模型")
    fitted = offset + amplitude * np.exp(-time / tau)
    params = dict(capacity_ah=q_ref, low_current_capacity_ah=q_low, r0_ohm=r0,
                  r1_ohm=float(r1), c1_f=float(tau / r1), tau_s=float(tau),
                  r0_on_ohm=r0_on, r0_off_ohm=r0_off,
                  relaxation_rmse_mv=float(np.sqrt(np.mean((fitted - pulse["voltage_v"][after]) ** 2)) * 1000),
                  pulse_duration_s=duration, ocv_soc=knots.tolist(), ocv_v=table.volts.tolist(),
                  calibration_steps=[0, 2, 5, 6, 7], validation_steps=SELECTION["validation"],
                  note="Low-current terminal voltage approximates OCV; one high-SOC pulse gives constant RC parameters.")
    return params, table


def metrics(estimate: np.ndarray, reference: np.ndarray, time: np.ndarray) -> dict:
    error = estimate - reference
    # 时间加权，避免某段采样更密就自动获得更大权重；误差单位是 SOC 百分点。
    mse = np.sum((error[:-1] ** 2 + error[1:] ** 2) * 0.5 * np.diff(time)) / (time[-1] - time[0])
    return dict(rmse_pp=float(np.sqrt(mse) * 100), max_abs_pp=float(np.max(np.abs(error)) * 100),
                end_error_pp=float(error[-1] * 100))


def evaluate(groups: dict, params: dict, table: OCVTable, *, initial_soc: float = 0.9,
             current_offset_a: float = 0.0, resistance_scale: float = 1.0) -> tuple[dict, dict]:
    if not np.isfinite(initial_soc) or not 0 <= initial_soc <= 1:
        raise ValueError("initial_soc 必须在 [0, 1]")
    if not np.isfinite(current_offset_a) or not np.isfinite(resistance_scale) or resistance_scale <= 0:
        raise ValueError("电流偏置必须有限，电阻倍率必须为有限正数")
    validation = groups["validation"]
    time, measured = validation["time_s"], validation["current_a"]
    q = params["capacity_ah"]
    # 起点接续原始 step31 满充，SOC=1 是边界假设。计算参考不喂给任何估算器。
    reference = 1 + cumulative_ah(validation) / q
    current = measured + current_offset_a
    estimators = {
        "coulomb": CoulombOnly(initial_soc, q),
        "ekf_generic": EKFEstimator(initial_soc, q, 0.020, 0.015, 3000.0, r_volt=0.020 ** 2),
        "ekf_calibrated": EKFEstimator(initial_soc, q, params["r0_ohm"] * resistance_scale,
                                       params["r1_ohm"] * resistance_scale, params["c1_f"],
                                       r_volt=0.020 ** 2, ocv_func=table.voltage, docv_func=table.slope),
    }
    estimates = {name: [initial_soc] for name in estimators}
    predicted = {"generic": [float(ocv(1)) + 0.020 * measured[0]],
                 "calibrated": [table.voltage(1) + params["r0_ohm"] * measured[0]]}
    urc = dict(generic=0.0, calibrated=0.0)
    for k in range(1, len(time)):
        dt = float(time[k] - time[k - 1])
        mean_current = float((current[k - 1] + current[k]) / 2)
        for name, estimator in estimators.items():
            kwargs = {} if name == "coulomb" else {"voltage_current_a": float(current[k])}
            estimates[name].append(estimator.step(mean_current, float(validation["voltage_v"][k]), dt, **kwargs))
        # 开环电压检查使用计算参考 SOC；不声称是独立的盲测 SOC 预测。
        for name, r0, r1, c1, curve in (
            ("generic", 0.020, 0.015, 3000.0, ocv),
            ("calibrated", params["r0_ohm"], params["r1_ohm"], params["c1_f"], table.voltage),
        ):
            a = np.exp(-dt / (r1 * c1))
            urc[name] = a * urc[name] + r1 * (1 - a) * (measured[k - 1] + measured[k]) / 2
            predicted[name].append(float(curve(reference[k])) + r0 * measured[k] + urc[name])
    traces = dict(time_s=time, current_a=measured, voltage_v=validation["voltage_v"],
                  temperature_c=validation["temperature_c"], soc_reference=reference,
                  **{name: np.asarray(values) for name, values in estimates.items()},
                  **{f"voltage_{name}": np.asarray(values) for name, values in predicted.items()})
    report = dict(
        kind="measured_nasa_rw3_replay", samples=len(time), duration_s=float(time[-1]),
        initial_soc=initial_soc, current_offset_a=current_offset_a, resistance_scale=resistance_scale,
        reference_kind="coulomb_reference_from_same_measured_current_and_separate_calibration_capacity",
        independent_soc_truth=False, model_fitted_on_validation=False,
        metrics={name: metrics(np.asarray(values), reference, time) for name, values in estimates.items()},
        voltage_rmse_mv={name: metrics(np.asarray(values), validation["voltage_v"], time)["rmse_pp"] * 10
                         for name, values in predicted.items()},
        reference_end_soc=float(reference[-1]),
        validation_temperature_c=[float(validation["temperature_c"].min()), float(validation["temperature_c"].max())],
    )
    if not all(np.all(np.isfinite(values)) for values in traces.values()):
        raise ValueError("回放产生非有限结果")
    return traces, report


def run(data: Path, output: Path, *, plot: bool = False, initial_soc: float = 0.9,
        current_offset_a: float = 0.0, resistance_scale: float = 1.0) -> dict:
    groups, provenance = load_data(data)
    params, table = calibrate(groups)
    traces, report = evaluate(groups, params, table, initial_soc=initial_soc,
                              current_offset_a=current_offset_a, resistance_scale=resistance_scale)
    report["source_record"] = provenance["source_record"]
    report["csv_sha256"] = provenance["csv_sha256"]
    output.mkdir(parents=True, exist_ok=True)
    with (output / "trace.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(traces)
        writer.writerows(zip(*traces.values(), strict=True))
    for name, content in (("calibration", params), ("report", report)):
        (output / f"{name}.json").write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
    if plot:
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
        fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
        minutes = traces["time_s"] / 60
        axes[0].plot(minutes, traces["soc_reference"] * 100, "k--", label="Coulomb reference (not ground truth)")
        for name in report["metrics"]:
            axes[0].plot(minutes, traces[name] * 100, label=name)
        axes[0].set_ylabel("SOC (%)")
        axes[1].plot(minutes, traces["voltage_v"], label="Measured")
        axes[1].plot(minutes, traces["voltage_generic"], label="Generic model")
        axes[1].plot(minutes, traces["voltage_calibrated"], label="Calibrated model")
        axes[1].set_ylabel("Cell voltage (V)")
        axes[2].plot(minutes, traces["current_a"], label="Measured current (charge positive)")
        axes[2].set_ylabel("Current (A)")
        axes[2].set_xlabel("Time (min)")
        for ax in axes:
            ax.legend(fontsize=8)
            ax.grid(alpha=0.25)
        fig.suptitle("NASA RW3 — held-out random discharge; CC BY 4.0")
        fig.tight_layout()
        fig.savefig(output / "comparison.png", dpi=130)
        plt.close(fig)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "real-data-output")
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--initial-soc", type=float, default=0.9)
    parser.add_argument("--current-offset-a", type=float, default=0.0)
    parser.add_argument("--resistance-scale", type=float, default=1.0)
    args = parser.parse_args()
    try:
        report = run(args.data, args.out, plot=args.plot, initial_soc=args.initial_soc,
                     current_offset_a=args.current_offset_a, resistance_scale=args.resistance_scale)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(2, f"Real-data experiment failed: {exc}\n")
    print(json.dumps(report, indent=2))
    print(f"Output: {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
