"""Teaching experiments for D05: MUX settling, scan conflict, and in-range open-wire.

Scenario ``D05-mux-settling`` (synthetic): source resistance and sampling
capacitor set the RC settle time; requiring N-bit settling sets a minimum dwell
per channel; 16 channels then collide with a 10 ms task — the same conflict S1
froze at 10.26337 ms, now derived from the input-stage physics.

Scenario ``D05-open-wire-in-range`` (synthetic): an open sense lead does not
read zero; the channel holds its last in-range value. A stuck-at detector with
a too-tight delta window misses it; a slow-drift comparison plus a dual-rail
plausibility check catches it. Teaching values only (SRC02 pending).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SCENARIO_ID = "D05-mux-settling"
OPEN_WIRE_SCENARIO_ID = "D05-open-wire-in-range"

RS_OHM = 10_000.0  # MUX 源阻抗（教学值）
CS_F = 10e-9  # 采样保持电容（教学值）
TAU_S = RS_OHM * CS_F  # 100 µs
FS_V = 5.0
BITS = 12
CHANNELS = 16
T_CONV_S = 20e-6  # 每串转换时间（S1 扫描算例的 20 µs）


def tau_s() -> float:
    return TAU_S


def lsb_mv(bits: int = BITS, fs_v: float = FS_V) -> float:
    if bits <= 0 or fs_v <= 0:
        raise ValueError("bits and full scale must be positive")
    return fs_v / (2**bits) * 1000.0


def settling_time_s(
    bits: int = BITS, fs_v: float = FS_V, tau: float = TAU_S, step_v: float = FS_V
) -> float:
    """Time for the residual to fall below LSB/2 (rounding ADC)."""
    if bits <= 0 or fs_v <= 0 or step_v <= 0:
        raise ValueError("bits, full scale and step must be positive")
    lsb_half = fs_v / (2**bits) / 2
    return tau * math.log(step_v / lsb_half)


def scan_time_s(
    channels: int = CHANNELS, bits: int = BITS, t_conv: float = T_CONV_S
) -> float:
    if channels <= 0:
        raise ValueError("channels must be positive")
    return channels * (settling_time_s(bits) + t_conv)


def open_wire_trace() -> dict:
    """In-range open wire vs three detectors (rest / drift / active audit).

    开线通道保持上次有效值 3.280 V（量程内，远非 0 V）。
    A 静置：真实电芯恒定，卡值窗与对均值 plausibility 都不触发——单看数值无法区分；
    B 漂移：真实电芯缓慢下滑，±2 mV 卡值窗触发——漂移碰巧救场；
    C 主动稽核：对该通道注入 +5.0 mV 已知偏置，开线无响应（0.0 mV）——与静置与否无关。
    """
    stuck_v = 3.280
    rest_cell = [3.280] * 7
    drift_cell = [3.279, 3.278, 3.276, 3.273, 3.270, 3.266, 3.262]
    delta_window_mv = 2.0

    def trips(trace: list[float]) -> bool:
        return any(
            abs(h - c) * 1000 > delta_window_mv
            for h, c in zip([stuck_v] * len(trace), trace, strict=True)
        )

    audit_bias_mv = 5.0
    audit_response_mv = 0.0  # 开线：注入偏置无任何响应
    return {
        "scenario_id": OPEN_WIRE_SCENARIO_ID,
        "stuck_v": stuck_v,
        "delta_window_mv": delta_window_mv,
        "rest": {"cell_trace_v": rest_cell, "delta_trips": trips(rest_cell)},
        "drift": {"cell_trace_v": drift_cell, "delta_trips": trips(drift_cell)},
        "audit": {
            "injected_bias_mv": audit_bias_mv,
            "response_mv": audit_response_mv,
            "caught": abs(audit_response_mv - audit_bias_mv) > delta_window_mv,
        },
        "conclusion": "量程内开线保持上次有效值；静置时数值/卡值窗/pack 均值都判不出，主动注入稽核与静置无关地抓住它",
    }


def build_report() -> dict:
    t_set = settling_time_s()
    t_scan = scan_time_s()
    return {
        "scenario_id": SCENARIO_ID,
        "identity": "teaching input-stage values; SRC02 (AFE datasheet) pending; no hardware delay is invented",
        "input_stage": {
            "Rs_ohm": RS_OHM,
            "Cs_f": CS_F,
            "tau_us": round(TAU_S * 1e6, 3),
            "fs_v": FS_V,
            "bits": BITS,
        },
        "lsb_mv": round(FS_V / (2**BITS) * 1000, 4),
        "settling_us": round(t_set * 1e6, 2),
        "scan_ms": round(t_scan * 1000, 5),
        "scan_over_10ms_task_ms": round(t_scan * 1000 - 10.0, 5),
        "open_wire": open_wire_trace(),
        "conclusion": "12 bit 建立要求单通道 902 µs；16 串扫描 14.75 ms 超 10 ms 任务——与 S1 同构的冲突，现在从输入级物理推出",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 的目录")
    args = parser.parse_args()
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
