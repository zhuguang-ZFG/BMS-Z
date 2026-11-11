"""Teaching experiments for D08: reaction windows, glitch suppression, hysteresis,
and feedback timeout. Extends S1's frozen budget with scheduling and feedback.

Scenario ``D08-reaction-window``: fault phase vs scan, confirm windows, and the
"flatter curve, later action" trade with frozen numbers.
Scenario ``D08-feedback-timeout``: a command without feedback within its window
is itself a fault (OS07 feedback-identity essence).
Scenario ``D08-fault-replay``: a unified protection supervisor replayed from a
CSV log. Input-integrity faults (disconnect / CRC / reset anomaly / stale data /
feedback timeout) and electrical OCD share one latch: after any input
invalidation the supervisor must not pass with stale data (inhibit_all), and
recovery needs an explicit clear plus RECOVER_K consecutive valid frames.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

SCENARIO_ID = "D08-reaction-window"
FEEDBACK_SCENARIO_ID = "D08-feedback-timeout"
FAULT_SCENARIO_ID = "D08-fault-replay"

SCAN_MS = 10.26337  # S1 16 串扫描（继承冻结锚点）
CONFIRM_N = 3
SAMPLE_MS = 20.0
DECIDE_MS = 2.0
ACTUATE_FEEDBACK_MS = 15.0
SCHED_JITTER_MS = 5.0  # 调度抖动上界（教学值）
GLITCH_MS = 8.0  # 电源毛刺宽度
REAL_FAULT_MS = 25.0  # 真实过流持续时间
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
        "threshold_a": THRESH_A,
        "release_a": RELEASE_A,
        "noise_a": noise_a,
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


# --- D08-fault-replay：统一状态机 + 规定故障集 + 可重放日志 ---

MAX_AGE_MS = 100.0  # 输入新鲜度上限（教学值：5 个 20 ms 采样周期）
RECOVER_K = 3  # 恢复所需连续有效拍数（与 CONFIRM_N 同语义）

FAULT_DISCONNECT = "DISCONNECT"
FAULT_CRC = "CRC_ERROR"
FAULT_RESET = "RESET_ANOMALY"
FAULT_STALE = "STALE_DATA"
FAULT_FEEDBACK = "FEEDBACK_TIMEOUT"
FAULT_OCD = "OCD"

LOG_COLUMNS = ["seq", "t_ms", "current_a", "link_up", "crc_ok", "fb_delta_ms", "clear"]


def _parse_frame(row: dict[str, str], lineno: int) -> dict:
    """Parse one CSV row; reject anything ambiguous instead of guessing."""
    try:
        frame = {
            "seq": int(row["seq"]),
            "t_ms": float(row["t_ms"]),
            "current_a": float(row["current_a"]),
            "link_up": int(row["link_up"]),
            "crc_ok": int(row["crc_ok"]),
            "clear": int(row["clear"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"第 {lineno} 行字段无法解析: {exc}") from exc
    fb_raw = (row.get("fb_delta_ms") or "").strip()
    if fb_raw == "":
        frame["fb_delta_ms"] = None
    else:
        try:
            frame["fb_delta_ms"] = float(fb_raw)
        except ValueError as exc:
            raise ValueError(f"第 {lineno} 行 fb_delta_ms 无法解析: {fb_raw!r}") from exc
    for key in ("t_ms", "current_a", "fb_delta_ms"):
        if frame[key] is not None and not math.isfinite(frame[key]):
            raise ValueError(f"第 {lineno} 行 {key} 非有限: {frame[key]}")
    for key in ("link_up", "crc_ok", "clear"):
        if frame[key] not in (0, 1):
            raise ValueError(f"第 {lineno} 行 {key} 必须为 0/1: {frame[key]}")
    return frame


def load_log(path: Path) -> list[dict]:
    """Load a replay CSV; header or row shape errors are rejected."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != LOG_COLUMNS:
            raise ValueError(
                f"表头必须为 {','.join(LOG_COLUMNS)}，实际 {reader.fieldnames}"
            )
        frames = []
        for lineno, row in enumerate(reader, start=2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"第 {lineno} 行列数不足")
            frames.append(_parse_frame(row, lineno))
    return frames


def _integrity_fault(frame: dict, last_seq: int | None, last_t_ms: float | None) -> str | None:
    """First failing check wins; check order is part of the contract."""
    if frame["link_up"] != 1:
        return FAULT_DISCONNECT
    if frame["crc_ok"] != 1:
        return FAULT_CRC
    if last_seq is not None and (frame["seq"] <= last_seq or frame["t_ms"] < last_t_ms):
        return FAULT_RESET
    if last_t_ms is not None and (frame["t_ms"] - last_t_ms) > MAX_AGE_MS:
        return FAULT_STALE
    fb = frame["fb_delta_ms"]
    if fb is not None and (fb < 0 or fb > FEEDBACK_TIMEOUT_MS):
        return FAULT_FEEDBACK
    return None


def _ocd_active(frame: dict, latched: str | None) -> bool:
    """活动过流：超阈即活动；OCD 锁存后按迟滞带保持到 <45 A。"""
    return frame["current_a"] > THRESH_A or (
        latched == FAULT_OCD and frame["current_a"] >= RELEASE_A
    )


_MASK_LEVELS = {"normal_path": 0, "open_discharge": 1, "inhibit_all": 2}
_MASK_NAMES = {v: k for k, v in _MASK_LEVELS.items()}


def _output_mask(integrity: str | None, latched: str | None, state: str) -> str:
    """当拍候选掩码：完整性活动故障或完整性锁存 → inhibit_all（覆盖两个方向）；
    仅 OCD 锁存/活动 → open_discharge；NORMAL → normal_path。候选只用于升级，
    实际掩码在 FAULT 内锁存、只升不降（见 replay_frames）。"""
    if state != "FAULT":
        return "normal_path"
    if integrity is not None or (latched is not None and latched != FAULT_OCD):
        return "inhibit_all"
    return "open_discharge"


def replay_frames(frames: list[dict]) -> dict:
    """Run the unified supervisor over parsed frames.

    States: INIT → NORMAL ⇄ FAULT. Every NORMAL→FAULT transition latches the
    first fault as the scene; later frames cannot overwrite it. The output mask
    level is latched inside FAULT and only escalates (open_discharge →
    inhibit_all): once any frame has forced inhibit_all, later good frames
    without a full recovery cannot downgrade it. Recovery to NORMAL requires
    clear=1 plus RECOVER_K consecutive frames with no active fault
    (integrity-valid and no active overcurrent), so neither stale data nor a
    live overcurrent can release the latch.
    """
    state = "INIT"
    last_seq: int | None = None
    last_t_ms: float | None = None
    ocd_count = 0
    recovery_count = 0
    latched: str | None = None
    transitions: list[dict] = []
    faults: list[dict] = []
    output_events: list[dict] = []
    last_mask = "init_path"
    mask_level = 0

    for tick, frame in enumerate(frames, start=1):
        fault = _integrity_fault(frame, last_seq, last_t_ms)
        last_seq, last_t_ms = frame["seq"], frame["t_ms"]
        clear = frame["clear"] == 1

        if state == "INIT":
            if fault is not None:
                latched = fault
                faults.append({"fault": fault, "tick": tick, "t_ms": frame["t_ms"]})
                transitions.append(
                    {
                        "tick": tick,
                        "t_ms": frame["t_ms"],
                        "from_state": "INIT",
                        "to_state": "FAULT",
                        "trigger": fault,
                        "action": "inhibit_all",
                    }
                )
                state = "FAULT"
            else:
                transitions.append(
                    {
                        "tick": tick,
                        "t_ms": frame["t_ms"],
                        "from_state": "INIT",
                        "to_state": "NORMAL",
                        "trigger": "FIRST_VALID_FRAME",
                        "action": "close_normal_path",
                    }
                )
                state = "NORMAL"
        elif state == "NORMAL":
            if fault is not None:
                latched = fault
                faults.append({"fault": fault, "tick": tick, "t_ms": frame["t_ms"]})
                transitions.append(
                    {
                        "tick": tick,
                        "t_ms": frame["t_ms"],
                        "from_state": "NORMAL",
                        "to_state": "FAULT",
                        "trigger": fault,
                        "action": "inhibit_all",
                    }
                )
                state = "FAULT"
                recovery_count = 0
                ocd_count = 0
            else:
                if frame["current_a"] > THRESH_A:
                    ocd_count += 1
                    if ocd_count >= CONFIRM_N:
                        latched = FAULT_OCD
                        faults.append(
                            {"fault": FAULT_OCD, "tick": tick, "t_ms": frame["t_ms"]}
                        )
                        transitions.append(
                            {
                                "tick": tick,
                                "t_ms": frame["t_ms"],
                                "from_state": "NORMAL",
                                "to_state": "FAULT",
                                "trigger": FAULT_OCD,
                                "action": "open_discharge",
                            }
                        )
                        state = "FAULT"
                        recovery_count = 0
                        ocd_count = 0
                else:
                    ocd_count = 0
        else:
            # state == "FAULT"：首现场不改写；恢复要求无活动故障 + clear
            if fault is None and not _ocd_active(frame, latched) and clear:
                recovery_count += 1
                if recovery_count >= RECOVER_K:
                    transitions.append(
                        {
                            "tick": tick,
                            "t_ms": frame["t_ms"],
                            "from_state": "FAULT",
                            "to_state": "NORMAL",
                            "trigger": "RECOVERED",
                            "action": "restore_normal_path",
                        }
                    )
                    state = "NORMAL"
                    recovery_count = 0
                    latched = None
                    ocd_count = 0
            else:
                recovery_count = 0

        if state == "FAULT":
            # 掩码级别锁存：只升不降，升级后不因坏帧消失而降级
            mask_level = max(
                mask_level, _MASK_LEVELS[_output_mask(fault, latched, state)]
            )
            mask = _MASK_NAMES[mask_level]
        else:
            mask = "normal_path"
            mask_level = 0
        if mask != last_mask:
            output_events.append(
                {
                    "tick": tick,
                    "t_ms": frame["t_ms"],
                    "mask": mask,
                    "state": state,
                    "active_fault": fault or (latched if state == "FAULT" else None),
                }
            )
            last_mask = mask

    return {
        "frames": len(frames),
        "transitions": transitions,
        "faults": faults,
        "output_events": output_events,
        "final_state": state,
    }


def replay_log(path: Path) -> dict:
    """Replay a CSV log through the unified supervisor."""
    return replay_frames(load_log(path))


def summarize_replay(result: dict) -> dict:
    return {
        "scenario_id": FAULT_SCENARIO_ID,
        "frames": result["frames"],
        "faults": [f["fault"] for f in result["faults"]],
        "recoveries": sum(
            1 for t in result["transitions"] if t["to_state"] == "NORMAL" and t["from_state"] == "FAULT"
        ),
        "final_state": result["final_state"],
        "transition_count": len(result["transitions"]),
    }


def transition_table() -> list[dict]:
    """状态转移表：每个转移都有输入、时限、动作与恢复口径。"""
    return [
        {
            "transition": "INIT→NORMAL",
            "input": "首帧完整有效（link_up/crc_ok=1，无回退、无超龄、无反馈超时）",
            "deadline": "上电后首帧当拍",
            "action": "close_normal_path（接通正常路径；OCD 确认计数从 NORMAL 起算）",
            "recovery": "—",
        },
        {
            "transition": "NORMAL→FAULT",
            "input": "六类触发之一：断线 / CRC 错 / 序列或时间回退 / 超龄(>100 ms) / "
            "反馈超时(>20 ms 或未到) / OCD 连续 3 拍 > 50 A",
            "deadline": "完整性故障当拍锁存；OCD 需连续 3 拍确认",
            "action": "完整性故障 inhibit_all（禁止用旧数据放行）；OCD open_discharge（断放留充）",
            "recovery": "锁存至 clear=1 + 连续 3 拍无活动故障（完整性有效且无活动过流；OCD 迟滞带 ≥45 A 保持活动）",
        },
        {
            "transition": "FAULT→NORMAL",
            "input": "clear=1 且连续 3 拍无活动故障（完整有效，且无活动过流：>50 A 一律活动；OCD 锁存时 ≥45 A 仍活动）",
            "deadline": "连续 3 拍内完成，否则重新计数",
            "action": "restore_normal_path",
            "recovery": "—（回到 NORMAL；首个锁存故障是现场，不被后续故障改写）",
        },
        {
            "transition": "FAULT 内输出掩码",
            "input": "锁存期间的活动故障（完整性故障当拍活动；过流按迟滞带活动）",
            "deadline": "当拍重算，掩码变化记入 output_events",
            "action": "inhibit_all 优先于 open_discharge；升级后的掩码锁存，坏帧转好帧（无 clear）不降级",
            "recovery": "随 FAULT→NORMAL 回 normal_path",
        },
    ]


def demo_fault_log() -> list[dict]:
    """内置合成演示：六类故障各锁存一次并各恢复一次，覆盖全部转移。

    合成教学数据，不是实测日志；字段语义见 D8.4。
    """
    rows = [
        (1, 0, 10.0, 1, 1, "", 0),
        (2, 20, 10.0, 1, 1, "", 0),
        (3, 40, 10.0, 1, 1, "", 0),
        (4, 60, 10.0, 1, 1, "", 0),
        (5, 80, 10.0, 1, 1, "", 0),
        (6, 100, 10.0, 1, 0, "", 0),  # CRC_ERROR
        (7, 120, 10.0, 1, 1, "", 0),  # 无 clear：好帧也不放行
        (8, 140, 10.0, 1, 1, "", 0),
        (9, 160, 10.0, 1, 1, "", 1),
        (10, 180, 10.0, 1, 1, "", 1),
        (11, 200, 10.0, 1, 1, "", 1),  # 恢复
        (12, 220, 10.0, 0, 1, "", 0),  # DISCONNECT
        (13, 240, 10.0, 1, 1, "", 1),
        (14, 260, 10.0, 1, 1, "", 1),
        (15, 280, 10.0, 1, 1, "", 1),  # 恢复
        (16, 400, 10.0, 1, 1, "", 0),  # 间隔 120 ms > 100 ms：STALE_DATA
        (17, 420, 10.0, 1, 1, "", 1),
        (18, 440, 10.0, 1, 1, "", 1),
        (19, 460, 10.0, 1, 1, "", 1),  # 恢复
        (5, 480, 10.0, 1, 1, "", 0),  # 序列回退：RESET_ANOMALY
        (21, 500, 10.0, 1, 1, "", 1),
        (22, 520, 10.0, 1, 1, "", 1),
        (23, 540, 10.0, 1, 1, "", 1),  # 恢复
        (24, 560, 10.0, 1, 1, "25", 0),  # 反馈 25 ms > 20 ms：FEEDBACK_TIMEOUT
        (25, 580, 10.0, 1, 1, "", 1),
        (26, 600, 10.0, 1, 1, "", 1),
        (27, 620, 10.0, 1, 1, "", 1),  # 恢复
        (28, 640, 52.0, 1, 1, "", 0),
        (29, 660, 52.0, 1, 1, "", 0),
        (30, 680, 52.0, 1, 1, "", 0),  # 连续 3 拍 > 50 A：OCD，断放留充
        (31, 700, 46.0, 1, 1, "", 1),  # 46 > 45：释放前提不满足
        (32, 720, 44.0, 1, 1, "", 1),
        (33, 740, 44.0, 1, 1, "", 1),
        (34, 760, 44.0, 1, 1, "", 1),  # 恢复
        (35, 780, 10.0, 1, 1, "", 0),
        (36, 800, 10.0, 1, 1, "", 0),
    ]
    return [
        _parse_frame(
            {key: str(value) for key, value in zip(LOG_COLUMNS, row, strict=True)},
            lineno,
        )
        for lineno, row in enumerate(rows, start=2)
    ]


def write_log_csv(frames: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LOG_COLUMNS)
        writer.writeheader()
        for frame in frames:
            writer.writerow(frame)


def write_transitions_csv(result: dict, path: Path) -> None:
    fields = ["tick", "t_ms", "from_state", "to_state", "trigger", "action"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for t in result["transitions"]:
            writer.writerow({k: t[k] for k in fields})


def build_report(fault_replay: dict | None = None) -> dict:
    best = reaction_window_ms(0.0)
    worst = reaction_window_ms(SCAN_MS)
    if fault_replay is None:
        fault_replay = summarize_replay(replay_frames(demo_fault_log()))
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
        "fault_replay": fault_replay,
        "fault_replay_transition_table": transition_table(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 的目录")
    parser.add_argument(
        "--replay",
        type=Path,
        help="回放 CSV 日志（seq,t_ms,current_a,link_up,crc_ok,fb_delta_ms,clear）",
    )
    args = parser.parse_args(argv)
    demo_log: list[dict] | None = None
    if args.replay:
        try:
            result = replay_log(args.replay)
        except (OSError, ValueError) as exc:
            print(f"replay 拒绝：{exc}", file=sys.stderr)
            return 2
        report = build_report(fault_replay=summarize_replay(result))
    else:
        demo_log = demo_fault_log()
        result = replay_frames(demo_log)
        report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        write_transitions_csv(result, args.out / "transitions.csv")
        if demo_log is not None:
            write_log_csv(demo_log, args.out / "demo_log.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
