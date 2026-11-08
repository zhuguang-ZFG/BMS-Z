"""Teaching experiments for D08: reaction windows, glitch suppression, hysteresis,
and feedback timeout. Extends S1's frozen budget with scheduling and feedback.

Scenario ``D08-reaction-window``: fault phase vs scan, confirm windows, and the
"flatter curve, later action" trade with frozen numbers.
Scenario ``D08-feedback-timeout``: a command without feedback within its window
is itself a fault (OS07 feedback-identity essence).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCENARIO_ID = "D08-reaction-window"
FEEDBACK_SCENARIO_ID = "D08-feedback-timeout"

SCAN_MS = 10.26337        # S1 16 串扫描（继承冻结锚点）
CONFIRM_N = 3
SAMPLE_MS = 20.0
DECIDE_MS = 2.0
ACTUATE_FEEDBACK_MS = 15.0
SCHED_JITTER_MS = 5.0     # 调度抖动上界（教学值）
GLITCH_MS = 8.0           # 电源毛刺宽度
REAL_FAULT_MS = 25.0      # 真实过流持续时间
THRESH_A = 50.0
RELEASE_A = 45.0
FEEDBACK_TIMEOUT_MS = 20.0


def reaction_window_ms(fault_phase_ms: float) -> dict:
    """Worst-case reaction from physical fault to effective feedback."""
    if not 0 <= fault_phase_ms <= SCAN_MS:
        raise ValueError("fault phase must be within one scan period")
    first_sample = fault_phase_ms
    confirm = (CONFIRM_N - 1) * SAMPLE_MS
    total = first_sample + confirm + DECIDE_MS + ACTUATE_FEEDBACK_MS + SCHED_JITTER_MS
    return {
        "fault_phase_ms": round(fault_phase_ms, 3),
        "first_sample_ms": round(first_sample, 3),
        "confirm_ms": confirm,
        "decide_ms": DECIDE_MS,
        "actuate_feedback_ms": ACTUATE_FEEDBACK_MS,
        "sched_jitter_ms": SCHED_JITTER_MS,
        "total_ms": round(total, 3),
    }


def glitch_vs_fault() -> dict:
    confirm_window = (CONFIRM_N - 1) * SAMPLE_MS
    blind_ms = confirm_window + SAMPLE_MS
    return {
        "confirm_window_ms": confirm_window,
        "blind_window_ms": blind_ms,
        "glitch_ms": GLITCH_MS,
        "glitch_survives": GLITCH_MS > confirm_window,
        "real_fault_ms": REAL_FAULT_MS,
        "real_fault_detected": REAL_FAULT_MS >= blind_ms,
        "conclusion": f"确认窗 {confirm_window:.0f} ms：{GLITCH_MS:.0f} ms 毛刺被抑制；但同一个窗是"
                      f" ~{blind_ms:.0f} ms 的盲区——{REAL_FAULT_MS:.0f} ms 真实故障同样漏检。"
                      "要抓更短的故障只能缩短确认窗，抗毛刺能力随之下降",
    }


def hysteresis_chatter(noise_a: float = 2.0, samples: int = 40) -> dict:
    """Without hysteresis, noise around the threshold re-trips; with a release
    threshold (50 A trip / 45 A release), one trip stays latched until release."""
    import random

    rng = random.Random(7)
    edges_plain = 0
    edges_hyst = 0
    latched = False
    was_above = False
    for _ in range(samples):
        reading = THRESH_A + rng.uniform(-noise_a, noise_a)
        above = reading > THRESH_A
        if above and not was_above:
            edges_plain += 1
        was_above = above
        if above and not latched:
            edges_hyst += 1  # 一次进入锁存 = 一次动作
            latched = True
        elif reading < RELEASE_A:
            latched = False
    return {
        "threshold_a": THRESH_A, "release_a": RELEASE_A, "noise_a": noise_a,
        "actions_without_hysteresis": edges_plain,
        "actions_with_hysteresis": edges_hyst,
        "conclusion": "无迟滞时阈值噪声造成多次重复动作；迟滞带（50 触发/45 释放）把一串抖动折成一次锁存",
    }


def feedback_timeout(command_ms: float, feedback_ms: float | None) -> dict:
    """A command whose feedback misses its window is itself a fault."""
    if command_ms < 0:
        raise ValueError("command time must be nonnegative")
    ok = feedback_ms is not None and (feedback_ms - command_ms) <= FEEDBACK_TIMEOUT_MS
    return {
        "command_ms": command_ms,
        "feedback_ms": feedback_ms,
        "timeout_ms": FEEDBACK_TIMEOUT_MS,
        "within_window": ok,
        "verdict": "正常" if ok else "反馈超时——按故障锁存（命令不等于动作）",
    }


def build_report() -> dict:
    best = reaction_window_ms(0.0)
    worst = reaction_window_ms(SCAN_MS)
    return {
        "scenario_id": SCENARIO_ID,
        "identity": "extends S1 frozen budget (10.26337 ms scan, N=1/5/9); teaching scheduling values",
        "window_best_ms": best["total_ms"],
        "window_worst_ms": worst["total_ms"],
        "window_typical_ms": reaction_window_ms(5.0)["total_ms"],
        "glitch_vs_fault": glitch_vs_fault(),
        "hysteresis": hysteresis_chatter(),
        "feedback": {
            "on_time": feedback_timeout(100.0, 112.0),
            "late": feedback_timeout(100.0, 125.0),
            "never": feedback_timeout(100.0, None),
        },
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
