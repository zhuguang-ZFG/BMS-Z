"""Teaching experiments for D20: real-time firmware lanes, snapshot ownership, parameter atomicity.

D20「实时固件与数据所有权」的可执行证据模块。四件事：

1. **调度泳道**：ISR（1 ms 采样点）、快任务（10 ms 采样/保护）、慢任务（100 ms 滤波/
   估计）组成固定优先级、可抢占的单核时间线。每条泳道有 WCET 预算、截止期、启动抖动
   与响应时间；报告给出构造时间线的实测值与固定优先级响应时间分析（RTA）上界。
2. **看门狗规则**：只有「快照完整 + 快任务未过截止期」才喂狗；超时拍不喂。看门狗
   超时 35 ms 是独立计时器，不是任务自报的计数器。
3. **快照一致性**：写侧拷贝到非活动缓冲 → 发布序号 epoch flip → 读侧取最新完整
   epoch。反例是 naive 字段级组装：读侧跨过写侧发布点，一帧混用相邻两次采样；
   epoch 方案在同一读节奏下零混用，但会如实报告「旧一拍」的陈旧帧。
4. **启动降级与参数原子性**：参数 A/B 槽 + 提交计数器 + CRC-16；写参数中途断电、
   CRC 位翻转、版本不兼容、范围越界、双槽全坏逐项降级。朴素选择器只按计数器取
   最大代数，会接受撕裂配置或把过温阈值读成 259.8 °C。

教学身份：全部 WCET、抖动、看门狗超时、故障拍号、参数代数与阈值都是构造的教学值，
不是任何硬件的实测 WCET，不是示波器/HIL 记录，也不构成功能安全论证。软件在环仿真
不烧录固件、不驱动 MOS、不证明真实调度器或看门狗行为。

边界（必须与正文同页）：固件 `BmsInputs` 只有 `cell_mv[]`、`current_ma`、`temp_c10`、
`charger_present`，没有时间戳、质量位或采样序号；固件骨架也没有任务表、看门狗与参数
A/B 槽。本单元是教学补全，不证明固件已实现双缓冲、看门狗或参数原子性。书层
`bms-book/book/33-实时固件与数据所有权.md` 尚缺，本单元只闭合工程层（SRC05），不虚构
引用。

场景：``D20-rt-scheduling``（默认时间线、反例与参数恢复）与 ``D20-trace-replay``
（回放用户任务执行 trace，审计 WCET/抖动/超时/喂狗间隔）。
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path

SCENARIO_ID = "D20-rt-scheduling"
REPLAY_SCENARIO_ID = "D20-trace-replay"

# --- 泳道合同（教学值；不是任何 MCU 的实测 WCET）---
ISR_PERIOD_US = 1_000
FAST_PERIOD_US = 10_000
SLOW_PERIOD_US = 100_000
ISR_BUDGET_US = 200
FAST_BUDGET_US = 10_000
SLOW_BUDGET_US = 40_000
ISR_DEADLINE_US = 1_000
FAST_DEADLINE_US = 10_000
SLOW_DEADLINE_US = 100_000
HORIZON_US = 600_000

# 执行时间模式（微秒）：8 拍循环 + 一拍注入超限。确定性，无随机源。
ISR_EXEC_PATTERN_US = (120, 90, 150, 110, 130, 100, 160, 140)
FAST_EXEC_PATTERN_US = (4_900, 5_010, 4_870, 5_120, 4_960, 4_890, 5_230, 4_975)
SLOW_EXEC_PATTERN_US = (11_800, 12_400, 11_250, 13_100, 12_000, 12_750, 11_600, 13_500)
OVERRUN_TICK = 37
OVERRUN_EXEC_US = 14_000          # 10 ms 预算跑到 14 ms（SPEC 反例）

# 看门狗：独立计时；喂狗间隔必须小于超时。35 ms ≈ 3.5 个快任务周期。
WATCHDOG_TIMEOUT_US = 35_000
RECOVERY_FEEDS = 3                 # 连续 3 次完整且准时的快照才退出降级

# D08 冻结的电气反应窗与其中的调度项（本单元只读，不改写）
D08_WORST_WINDOW_MS = 72.263
D08_SCHED_TERM_MS = 5.0

# D17 估计任务在慢泳道里的预算（教学值）
ESTIMATE_WCET_US = 8_000

# --- 快照与双缓冲合同 ---
SNAPSHOT_FIELD_NAMES = ("cell_mv", "current_ma", "temp_c10", "charger_present", "isr_seq")
WRITER_PERIOD_US = 10_000
FIELD_WRITE_OFFSET_US = 100       # 写侧逐字段落盘，最后一个字段在 +400 µs 完成
SNAPSHOT_FRAMES = 40
NAIVE_READER_PHASE_US = 9_500     # 读侧在每次发布之后 9.5 ms 开始组装
FRAME_FIELD_READ_OFFSET_US = 1_500
EPOCH_WRITER_COPY_US = 9_200      # 写侧拷贝 9.2 ms
EPOCH_PUBLISH_OFFSET_US = 9_600   # 发布落在读侧开始之后，留 0.4 ms 给发布本身
EPOCH_READER_COPY_US = 6_000
EPOCH_READER_PHASE_US = 9_500

# --- 参数 A/B 槽 ---
PARAM_MAGIC = b"BZ"
PARAM_SCHEMA_CURRENT = 2
PARAM_SIZE = 20
BASE_GEN = 41
NEXT_GEN = 42
DEFAULT_PARAMS: dict[str, int] = {
    "ovp_mv": 4_250,
    "uvp_mv": 2_500,
    "ot_c10": 600,
    "ocp_ma": 30_000,
}
INTENDED_PARAMS: dict[str, int] = {
    "ovp_mv": 4_250,
    "uvp_mv": 2_500,
    "ot_c10": 550,
    "ocp_ma": 32_000,
}
PARAM_RANGES: dict[str, tuple[int, int]] = {
    "ovp_mv": (4_000, 4_300),
    "uvp_mv": (2_200, 3_000),
    "ot_c10": (550, 650),
    "ocp_ma": (15_000, 40_000),
}

# --- 回放数据合同 ---
TRACE_COLUMNS = ["job", "lane", "release_us", "start_us", "finish_us", "exec_us"]
TRACE_LANES = ("isr", "fast", "slow")
TRACE_MIN_ROWS = 20
TRACE_MAX_ROWS = 100_000
TRACE_MAX_SPAN_US = 3_600_000_000
TRACE_MAX_EXEC_US = {"isr": 5_000, "fast": 200_000, "slow": 2_000_000}


def _num(value: object) -> float:
    """从 report 字典里取回数值（pyright 友好，同时是运行时契约检查）。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"期望数值，得到 {type(value).__name__}")
    return float(value)


def _int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"期望整数，得到 {type(value).__name__}")
    return value


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(f"期望字符串，得到 {type(value).__name__}")
    return value


def _ms(us: int) -> float:
    return round(us / 1000.0, 3)


def _dict_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError("期望列表")
    rows: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("期望字典列表")
        rows.append(item)
    return rows


def _dict_of(value: object) -> dict[str, dict[str, object]]:
    if not isinstance(value, dict):
        raise ValueError("期望字典")
    rows: dict[str, dict[str, object]] = {}
    for key, item in value.items():
        if not isinstance(item, dict):
            raise ValueError("期望嵌套字典")
        rows[str(key)] = item
    return rows


def _map_of(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("期望字典")
    return {str(key): item for key, item in value.items()}


def _int_dict(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        raise ValueError("期望数值字典")
    return {str(key): _int(item) for key, item in value.items()}


def _sources_of(row: dict[str, object]) -> list[int]:
    value = row["sources"]
    if not isinstance(value, list):
        raise ValueError("sources 必须是列表")
    return [_int(item) for item in value]


# --- 固定优先级可抢占单核时间线 ---

PRIORITY = {"isr": 0, "fast": 1, "slow": 2}


@dataclass
class Job:
    lane: str
    index: int
    release_us: int
    exec_us: int
    start_us: int | None = None
    finish_us: int | None = None
    remaining_us: int = 0


def _default_exec_us(lane: str, index: int) -> int:
    if lane == "isr":
        return ISR_EXEC_PATTERN_US[index % len(ISR_EXEC_PATTERN_US)]
    if lane == "fast":
        if index == OVERRUN_TICK:
            return OVERRUN_EXEC_US
        return FAST_EXEC_PATTERN_US[index % len(FAST_EXEC_PATTERN_US)]
    return SLOW_EXEC_PATTERN_US[index % len(SLOW_EXEC_PATTERN_US)]


def simulate_schedule(
    fast_overrides: dict[int, int] | None = None, horizon_us: int = HORIZON_US
) -> list[dict[str, object]]:
    """固定优先级、可抢占的单核时间线；返回每个作业的释放/启动/完成/执行时间。

    默认时间线在 ``OVERRUN_TICK`` 注入一次 14 ms 快任务；``fast_overrides`` 可再覆盖
    指定拍的执行时间（用于看门狗复位探针），不引入随机源。
    """
    overrides = fast_overrides or {}
    jobs: list[Job] = []
    for index in range(horizon_us // ISR_PERIOD_US):
        jobs.append(Job("isr", index, index * ISR_PERIOD_US, _default_exec_us("isr", index)))
    for index in range(horizon_us // FAST_PERIOD_US):
        exec_us = overrides.get(index, _default_exec_us("fast", index))
        jobs.append(Job("fast", index, (index + 1) * FAST_PERIOD_US, exec_us))
    for index in range(horizon_us // SLOW_PERIOD_US):
        jobs.append(Job("slow", index, index * SLOW_PERIOD_US, _default_exec_us("slow", index)))
    jobs.sort(key=lambda job: (job.release_us, PRIORITY[job.lane], job.index))

    pending: list[Job] = []
    running: Job | None = None
    done: list[Job] = []
    now = 0
    cursor = 0

    while cursor < len(jobs) or running is not None or pending:
        while cursor < len(jobs) and jobs[cursor].release_us <= now:
            candidate = jobs[cursor]
            candidate.remaining_us = candidate.exec_us
            pending.append(candidate)
            cursor += 1
        if running is not None and any(
            PRIORITY[job.lane] < PRIORITY[running.lane] for job in pending
        ):
            pending.append(running)
            running = None
        if running is None and pending:
            pending.sort(key=lambda job: (PRIORITY[job.lane], job.release_us, job.index))
            running = pending.pop(0)
            if running.start_us is None:
                running.start_us = now
        if running is None:
            if cursor < len(jobs):
                now = jobs[cursor].release_us
                continue
            break
        next_release = jobs[cursor].release_us if cursor < len(jobs) else None
        finish_at = now + running.remaining_us
        if next_release is not None and next_release < finish_at:
            running.remaining_us -= next_release - now
            now = next_release
        else:
            now = finish_at
            running.finish_us = now
            done.append(running)
            running = None

    rows: list[dict[str, object]] = []
    for job in sorted(done, key=lambda item: (item.release_us, PRIORITY[item.lane], item.index)):
        if job.start_us is None or job.finish_us is None:
            raise ValueError(f"作业未完成：{job.lane}[{job.index}]")
        deadline_us = {
            "isr": ISR_DEADLINE_US,
            "fast": FAST_DEADLINE_US,
            "slow": SLOW_DEADLINE_US,
        }[job.lane]
        rows.append(
            {
                "job": f"{job.lane}-{job.index:03d}",
                "lane": job.lane,
                "index": job.index,
                "release_us": job.release_us,
                "start_us": job.start_us,
                "finish_us": job.finish_us,
                "exec_us": job.exec_us,
                "response_us": job.finish_us - job.release_us,
                "start_jitter_us": job.start_us - job.release_us,
                "deadline_us": deadline_us,
            }
        )
    return rows


def _jobs_of(rows: list[dict[str, object]], lane: str) -> list[dict[str, object]]:
    return sorted([row for row in rows if _text(row["lane"]) == lane], key=lambda r: _int(r["index"]))


def snapshot_round_complete(rows: list[dict[str, object]], tick: int) -> bool:
    """快任务 tick 的 10 个 ISR 样本是否都在它完成前落地。"""
    fast = next(
        row for row in rows if _text(row["lane"]) == "fast" and _int(row["index"]) == tick
    )
    finish_us = _int(fast["finish_us"])
    window = [
        row
        for row in rows
        if _text(row["lane"]) == "isr" and tick * 10 <= _int(row["index"]) < tick * 10 + 10
    ]
    return len(window) == 10 and all(_int(row["finish_us"]) <= finish_us for row in window)


def lane_summary(rows: list[dict[str, object]], lane: str) -> dict[str, object]:
    jobs = _jobs_of(rows, lane)
    if not jobs:
        return {"jobs": 0, "present": False}
    timeout_us = {"isr": ISR_DEADLINE_US, "fast": FAST_DEADLINE_US, "slow": SLOW_DEADLINE_US}[lane]
    period_us = {"isr": ISR_PERIOD_US, "fast": FAST_PERIOD_US, "slow": SLOW_PERIOD_US}[lane]
    budget_us = {"isr": ISR_BUDGET_US, "fast": FAST_BUDGET_US, "slow": SLOW_BUDGET_US}[lane]
    fault_ticks = {OVERRUN_TICK, OVERRUN_TICK + 1}
    nominal = [row for row in jobs if _int(row["index"]) not in fault_ticks]
    wcet_us = max(_int(row["exec_us"]) for row in jobs)
    nominal_wcet_us = max(_int(row["exec_us"]) for row in nominal)
    max_jitter = max(_int(row["start_jitter_us"]) for row in jobs)
    nominal_jitter = max(_int(row["start_jitter_us"]) for row in nominal)
    max_response = max(_int(row["response_us"]) for row in jobs)
    nominal_response = max(_int(row["response_us"]) for row in nominal)
    misses = [_int(row["index"]) for row in jobs if _int(row["response_us"]) > timeout_us]
    mean_exec = sum(_int(row["exec_us"]) for row in jobs) / len(jobs)
    return {
        "present": True,
        "jobs": len(jobs),
        "period_us": period_us,
        "budget_us": budget_us,
        "deadline_us": timeout_us,
        "wcet_us": wcet_us,
        "wcet_nominal_us": nominal_wcet_us,
        "max_start_jitter_us": max_jitter,
        "max_nominal_start_jitter_us": nominal_jitter,
        "max_response_us": max_response,
        "max_nominal_response_us": nominal_response,
        "deadline_miss_ticks": misses,
        "load": round(mean_exec / period_us, 4),
    }


def response_time_analysis(fast_us: int, slow_us: int, isr_us: int) -> dict[str, object]:
    """固定优先级响应时间分析：R = C + Σ ceil(R/T_h)·C_h。

    超过 1 s 判为发散（利用率 ≥ 1 时慢任务可能永远得不到 CPU），返回 ``bounded=False``，
    不编一个有限数。
    """
    isr_response = isr_us
    fast = fast_us
    for _ in range(50):
        nxt = fast_us + _ceil_div(fast, ISR_PERIOD_US) * isr_us
        if nxt == fast:
            break
        fast = nxt
    slow = slow_us
    slow_bounded = True
    for _ in range(50):
        nxt = (
            slow_us
            + _ceil_div(slow, FAST_PERIOD_US) * fast_us
            + _ceil_div(slow, ISR_PERIOD_US) * isr_us
        )
        if nxt == slow:
            break
        if nxt > 1_000_000:
            slow_bounded = False
            break
        slow = nxt
    return {
        "isr_response_us": isr_response,
        "fast_response_us": fast,
        "fast_deadline_ok": fast <= FAST_DEADLINE_US,
        "slow_response_us": slow if slow_bounded else None,
        "slow_bounded": slow_bounded,
        "slow_deadline_ok": slow_bounded and slow <= SLOW_DEADLINE_US,
    }


def _ceil_div(a: int, b: int) -> int:
    return -(-a // b)


# --- 看门狗 ---

FEED_RULE = "只在「快照完整（10/10 ISR 样本落地）且快任务未过截止期」时喂狗；迟到或残缺拍不喂"


def watchdog_audit(
    rows: list[dict[str, object]],
    timeout_us: int = WATCHDOG_TIMEOUT_US,
    initial_state: str = "RUN",
) -> dict[str, object]:
    fast_jobs = _jobs_of(rows, "fast")
    feeds: list[dict[str, object]] = []
    withheld: list[dict[str, object]] = []
    transitions: list[dict[str, object]] = []
    state = initial_state
    if initial_state == "RUN":
        transitions.append(
            {"t_us": 0, "from": "INIT", "to": "RUN", "stage": "boot", "reason": "参数校验通过"}
        )
    last_feed: int | None = None
    consecutive = 0
    max_gap_us = 0
    reset_at_us: int | None = None
    late_complete = 0

    for row in fast_jobs:
        tick = _int(row["index"])
        finish_us = _int(row["finish_us"])
        response_us = _int(row["response_us"])
        complete = snapshot_round_complete(rows, tick)
        late = response_us > FAST_DEADLINE_US
        if late and complete:
            late_complete += 1
        if late or not complete:
            reason = "deadline_miss" if late else "snapshot_incomplete"
            withheld.append(
                {
                    "tick": tick,
                    "t_us": finish_us,
                    "reason": reason,
                    "response_us": response_us,
                    "deadline_us": FAST_DEADLINE_US,
                    "snapshot_complete": complete,
                }
            )
            consecutive = 0
            if state == "RUN":
                state = "DEGRADED"
                detected_us = _int(row["release_us"]) + FAST_DEADLINE_US if late else finish_us
                transitions.append(
                    {
                        "t_us": detected_us,
                        "from": "RUN",
                        "to": "DEGRADED",
                        "stage": "deadline" if late else "snapshot",
                        "reason": f"tick {tick} {'超时' if late else '快照不完整'}",
                    }
                )
            continue
        if last_feed is not None:
            gap_us = finish_us - last_feed
            max_gap_us = max(max_gap_us, gap_us)
            if gap_us >= timeout_us:
                reset_at_us = last_feed + timeout_us
                transitions.append(
                    {
                        "t_us": reset_at_us,
                        "from": state,
                        "to": "RESET",
                        "stage": "watchdog",
                        "reason": f"喂狗间隔 {gap_us} µs ≥ 超时 {timeout_us} µs",
                    }
                )
                state = "RESET"
                feeds.append({"tick": tick, "t_us": finish_us, "gap_us": gap_us, "accepted": False})
                break
        feeds.append({"tick": tick, "t_us": finish_us, "gap_us": None if last_feed is None else finish_us - last_feed, "accepted": True})
        last_feed = finish_us
        if state == "DEGRADED":
            consecutive += 1
            if consecutive >= RECOVERY_FEEDS:
                state = "RUN"
                transitions.append(
                    {
                        "t_us": finish_us,
                        "from": "DEGRADED",
                        "to": "RUN",
                        "stage": "recovery",
                        "reason": f"连续 {consecutive} 次完整且准时的快照",
                    }
                )
                consecutive = 0

    return {
        "feed_rule": FEED_RULE,
        "timeout_us": timeout_us,
        "feeds": feeds,
        "feed_count": len(feeds),
        "withheld": withheld,
        "withheld_count": len(withheld),
        "transitions": transitions,
        "max_gap_us": max_gap_us,
        "margin_us": timeout_us - max_gap_us,
        "reset_at_us": reset_at_us,
        "late_complete_snapshots": late_complete,
        "final_state": state,
    }


def watchdog_reset_probe() -> dict[str, object]:
    """连续两拍 14 ms：喂狗间隔跨过 35 ms，看门狗必须复位而不是继续降级。"""
    rows = simulate_schedule({OVERRUN_TICK + 1: OVERRUN_EXEC_US})
    audit = watchdog_audit(rows)
    return {
        "overrun_ticks": [OVERRUN_TICK, OVERRUN_TICK + 1],
        "max_gap_us": audit["max_gap_us"],
        "timeout_us": audit["timeout_us"],
        "reset_at_us": audit["reset_at_us"],
        "final_state": audit["final_state"],
        "withheld_count": audit["withheld_count"],
    }


# --- 快照一致性：naive 字段组装 vs 双缓冲 epoch ---

def snapshot_sample(sample_index: int) -> dict[str, object]:
    """第 k 次采样的一整帧值（确定性解析式）。"""
    return {
        "cell_mv": 3_700 + (sample_index % 7) * 10,
        "current_ma": 18_000 if sample_index < 9 else -30_000,
        "temp_c10": 250 + sample_index // 10,
        "charger_present": sample_index < 12,
        "isr_seq": sample_index,
    }


def _field_source(read_us: int, field_index: int) -> int:
    write_us = read_us - field_index * FIELD_WRITE_OFFSET_US
    return max(0, write_us // WRITER_PERIOD_US)


def _naive_frame_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for frame in range(SNAPSHOT_FRAMES):
        start_us = NAIVE_READER_PHASE_US + frame * WRITER_PERIOD_US
        sources = [
            _field_source(start_us + field * FRAME_FIELD_READ_OFFSET_US, field)
            for field in range(len(SNAPSHOT_FIELD_NAMES))
        ]
        mixed = len(set(sources)) > 1
        rows.append(
            {
                "scheme": "naive",
                "frame": frame,
                "start_us": start_us,
                "sources": sources,
                "mixed": mixed,
                "stale": False,
                "cell_mv": snapshot_sample(sources[0])["cell_mv"],
                "current_ma": snapshot_sample(sources[1])["current_ma"],
                "temp_c10": snapshot_sample(sources[2])["temp_c10"],
                "charger_present": snapshot_sample(sources[3])["charger_present"],
                "isr_seq": snapshot_sample(sources[4])["isr_seq"],
            }
        )
    return rows


def _epoch_frame_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for frame in range(1, SNAPSHOT_FRAMES + 1):
        start_us = EPOCH_READER_PHASE_US + frame * WRITER_PERIOD_US
        published = max(0, (start_us - EPOCH_PUBLISH_OFFSET_US) // WRITER_PERIOD_US)
        sources = [published] * len(SNAPSHOT_FIELD_NAMES)
        stale = start_us - (published * WRITER_PERIOD_US + EPOCH_PUBLISH_OFFSET_US)
        rows.append(
            {
                "scheme": "epoch",
                "frame": frame,
                "start_us": start_us,
                "sources": sources,
                "mixed": len(set(sources)) > 1,
                "stale": stale > 0,
                "stale_us": stale,
                "cell_mv": snapshot_sample(published)["cell_mv"],
                "current_ma": snapshot_sample(published)["current_ma"],
                "temp_c10": snapshot_sample(published)["temp_c10"],
                "charger_present": snapshot_sample(published)["charger_present"],
                "isr_seq": snapshot_sample(published)["isr_seq"],
            }
        )
    return rows


def double_buffer_safe(reader_copy_us: int, writer_period_us: int) -> dict[str, object]:
    """双缓冲的充分条件：读侧拷贝时间短于写侧一个周期。

    否则写侧可能在读侧完成前绕回同一块缓冲，epoch 发布仍成立但缓冲内容已被覆盖。
    """
    return {
        "reader_copy_us": reader_copy_us,
        "writer_period_us": writer_period_us,
        "safe": reader_copy_us < writer_period_us,
        "margin_us": writer_period_us - reader_copy_us,
    }


def snapshot_ownership() -> dict[str, object]:
    naive = _naive_frame_rows()
    epoch = _epoch_frame_rows()
    first_mixed = next(row for row in naive if row["mixed"])
    naive_mixed = [row for row in naive if row["mixed"]]
    epoch_mixed = [row for row in epoch if row["mixed"]]
    sign_frame = naive[8]
    sign_sources = _sources_of(sign_frame)
    sign_cell = snapshot_sample(sign_sources[0])
    sign_current = snapshot_sample(sign_sources[1])
    sign_cell_mv = _int(sign_cell["cell_mv"])
    sign_current_ma = _int(sign_current["current_ma"])
    sign_previous_ma = _int(snapshot_sample(sign_sources[0])["current_ma"])
    stale_rows = [row for row in epoch if row["stale"]]
    first_sources = _sources_of(first_mixed)
    return {
        "fields": list(SNAPSHOT_FIELD_NAMES),
        "writer_period_us": WRITER_PERIOD_US,
        "writer_field_offset_us": FIELD_WRITE_OFFSET_US,
        "naive": {
            "frames": len(naive),
            "mixed_frames": len(naive_mixed),
            "mixed_ratio": round(len(naive_mixed) / len(naive), 4),
            "max_field_skew_samples": max(
                max(_sources_of(row)) - min(_sources_of(row)) for row in naive
            ),
            "first_mixed": {
                "frame": first_mixed["frame"],
                "sources": first_mixed["sources"],
                "mixed_fields": [
                    name
                    for index, name in enumerate(SNAPSHOT_FIELD_NAMES)
                    if first_sources[index] != first_sources[0]
                ],
            },
            "sign_flip_evidence": {
                "frame": sign_frame["frame"],
                "cell_mv_source": sign_sources[0],
                "current_ma_source": sign_sources[1],
                "cell_mv": sign_cell_mv,
                "current_ma": sign_current_ma,
                "current_step_ma": sign_current_ma - sign_previous_ma,
                "frame_isr_seq": sign_frame["isr_seq"],
                "note": "帧自称 isr_seq=9，电压却是 8 号采样的值：无 epoch 时无法从帧内发现",
            },
        },
        "epoch": {
            "frames": len(epoch),
            "mixed_frames": len(epoch_mixed),
            "stale_frames": len(stale_rows),
            "max_staleness_us": max(_int(row["stale_us"]) for row in epoch),
            "retries": 0,
            "reader_copy_us": EPOCH_READER_COPY_US,
            "writer_copy_us": EPOCH_WRITER_COPY_US,
            "publish_offset_us": EPOCH_PUBLISH_OFFSET_US,
            "safety": double_buffer_safe(EPOCH_READER_COPY_US, WRITER_PERIOD_US),
        },
        "probes": [
            double_buffer_safe(EPOCH_READER_COPY_US, WRITER_PERIOD_US),
            double_buffer_safe(12_000, WRITER_PERIOD_US),
        ],
        "conclusion": (
            "naive 组装在 40 帧里 40 帧混用相邻采样（字段级来源可逐帧指认）；"
            "双缓冲 + epoch 在同一读节奏下 0 混用，代价是 40 帧各旧一拍（9.9 ms）且必须"
            "公开这一陈旧度"
        ),
    }


def snapshot_frame_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in _naive_frame_rows() + _epoch_frame_rows():
        sources = _sources_of(row)
        rows.append(
            {
                "scheme": row["scheme"],
                "frame": row["frame"],
                "start_us": row["start_us"],
                "cell_mv_source": sources[0],
                "current_ma_source": sources[1],
                "temp_c10_source": sources[2],
                "charger_source": sources[3],
                "isr_seq_source": sources[4],
                "mixed": row["mixed"],
                "stale": row["stale"],
            }
        )
    return rows


# --- 参数 A/B 槽、CRC 与启动降级 ---

def crc16_ccitt(data: bytes, crc: int = 0xFFFF) -> int:
    """CRC-16/CCITT-FALSE（poly 0x1021, init 0xFFFF, 不反射）。"""
    value = crc
    for byte in data:
        value ^= byte << 8
        for _ in range(8):
            if value & 0x8000:
                value = ((value << 1) ^ 0x1021) & 0xFFFF
            else:
                value = (value << 1) & 0xFFFF
    return value


def encode_slot(
    params: dict[str, int], gen: int, schema: int = PARAM_SCHEMA_CURRENT
) -> bytes:
    body = bytearray()
    body += PARAM_MAGIC
    body += schema.to_bytes(2, "big")
    body += gen.to_bytes(4, "big")
    body += int(params["ovp_mv"]).to_bytes(2, "big")
    body += int(params["uvp_mv"]).to_bytes(2, "big")
    body += int(params["ot_c10"]).to_bytes(2, "big")
    body += int(params["ocp_ma"]).to_bytes(4, "big")
    crc = crc16_ccitt(bytes(body))
    body += crc.to_bytes(2, "big")
    return bytes(body)


def _slot_values(raw: bytes) -> dict[str, int]:
    return {
        "ovp_mv": int.from_bytes(raw[8:10], "big"),
        "uvp_mv": int.from_bytes(raw[10:12], "big"),
        "ot_c10": int.from_bytes(raw[12:14], "big"),
        "ocp_ma": int.from_bytes(raw[14:18], "big"),
    }


def decode_slot(raw: bytes) -> dict[str, object]:
    """校验链 CRC → 版本 → 范围；magic 属于 CRC 覆盖的身份字段。"""
    if len(raw) != PARAM_SIZE:
        return {
            "length_ok": False,
            "magic_ok": False,
            "crc_ok": False,
            "schema": None,
            "gen": None,
            "values": {},
            "range_issues": ["长度不等于 20 字节"],
            "failure_stage": "crc",
            "valid": False,
            "stored_crc": None,
            "computed_crc": None,
        }
    magic_ok = raw[:2] == PARAM_MAGIC
    schema = int.from_bytes(raw[2:4], "big")
    gen = int.from_bytes(raw[4:8], "big")
    values = _slot_values(raw)
    stored_crc = int.from_bytes(raw[18:20], "big")
    computed_crc = crc16_ccitt(raw[:18])
    crc_ok = stored_crc == computed_crc
    range_issues = [
        f"{name}={values[name]} 越界 [{low}, {high}]"
        for name, (low, high) in PARAM_RANGES.items()
        if not low <= values[name] <= high
    ]
    schema_ok = schema == PARAM_SCHEMA_CURRENT
    if not (magic_ok and crc_ok):
        failure_stage: str | None = "crc"
    elif not schema_ok:
        failure_stage = "version"
    elif range_issues:
        failure_stage = "range"
    else:
        failure_stage = None
    return {
        "length_ok": True,
        "magic_ok": magic_ok,
        "crc_ok": crc_ok,
        "schema": schema,
        "schema_ok": schema_ok,
        "gen": gen,
        "values": values,
        "range_issues": range_issues,
        "failure_stage": failure_stage,
        "valid": failure_stage is None,
        "stored_crc": stored_crc,
        "computed_crc": computed_crc,
    }


def select_params(a_raw: bytes, b_raw: bytes) -> dict[str, object]:
    """稳健选择：只用整条校验链通过的槽；同代优先 A；全坏用安全默认值。"""
    slots = {"a": decode_slot(a_raw), "b": decode_slot(b_raw)}
    candidates: list[tuple[int, int, str, dict[str, object]]] = []
    degraded: list[dict[str, object]] = []
    for name, slot in slots.items():
        stage = slot["failure_stage"]
        if stage is None:
            candidates.append((_int(slot["gen"]), 0 if name == "a" else 1, name, slot))
        else:
            degraded.append(
                {
                    "slot": name,
                    "stage": stage,
                    "reason": f"slot_{name}_{stage}_rejected",
                    "detail": slot["range_issues"] if stage == "range" else None,
                }
            )
    if candidates:
        candidates.sort(key=lambda item: (-item[0], item[1]))
        gen, _, name, slot = candidates[0]
        params = _int_dict(slot["values"])
        return {
            "selected": name,
            "selected_gen": gen,
            "params": params,
            "status": "degraded" if degraded else "healthy",
            "degraded": degraded,
            "slots": slots,
        }
    return {
        "selected": None,
        "selected_gen": 0,
        "params": dict(DEFAULT_PARAMS),
        "status": "degraded",
        "degraded": degraded
        + [
            {
                "slot": None,
                "stage": "defaults",
                "reason": "all_slots_invalid_defaults",
                "detail": "两个槽都未通过校验链，写安全默认值",
            }
        ],
        "slots": slots,
    }


def naive_select_params(a_raw: bytes, b_raw: bytes) -> dict[str, object]:
    """反例选择器：只读计数器取最大代数，不验 CRC/版本/范围（只要求长度够）。"""
    slots: dict[str, dict[str, object]] = {}
    for name, raw in (("a", a_raw), ("b", b_raw)):
        if len(raw) != PARAM_SIZE:
            continue
        slots[name] = {
            "gen": int.from_bytes(raw[4:8], "big"),
            "schema": int.from_bytes(raw[2:4], "big"),
            "values": _slot_values(raw),
            "magic_ok": raw[:2] == PARAM_MAGIC,
            "crc_ok": int.from_bytes(raw[18:20], "big") == crc16_ccitt(raw[:18]),
        }
    if not slots:
        return {"selected": None, "selected_gen": 0, "params": dict(DEFAULT_PARAMS), "slots": {}}
    name = max(slots, key=lambda key: (_int(slots[key]["gen"]), key == "a"))
    slot = slots[name]
    return {
        "selected": name,
        "selected_gen": _int(slot["gen"]),
        "params": _int_dict(slot["values"]),
        "slots": slots,
    }


def _slot_report(slot: dict[str, object]) -> dict[str, object]:
    return {
        "valid": slot["valid"],
        "magic_ok": slot["magic_ok"],
        "crc_ok": slot["crc_ok"],
        "stored_crc": slot["stored_crc"],
        "computed_crc": slot["computed_crc"],
        "schema": slot["schema"],
        "gen": slot["gen"],
        "values": slot["values"],
        "range_issues": slot["range_issues"],
        "failure_stage": slot["failure_stage"],
    }


def _boot(case: str, a_raw: bytes, b_raw: bytes, note: str) -> dict[str, object]:
    robust = select_params(a_raw, b_raw)
    naive = naive_select_params(a_raw, b_raw)
    return {
        "case": case,
        "note": note,
        "slots": {
            "a": _slot_report(_dict_of(robust["slots"])["a"]),
            "b": _slot_report(_dict_of(robust["slots"])["b"]),
        },
        "selected": robust["selected"],
        "selected_gen": robust["selected_gen"],
        "params": robust["params"],
        "status": robust["status"],
        "degraded": robust["degraded"],
        "naive": {
            "selected": naive["selected"],
            "selected_gen": naive["selected_gen"],
            "params": naive["params"],
        },
        "diverges": naive["params"] != robust["params"] or naive["selected_gen"] != robust["selected_gen"],
    }


def _mid_write_bytes() -> bytes:
    """槽 B 先镜像 A，随后依次失效 magic → 写 payload → 写代数；在 payload 一半断电。"""
    raw = bytearray(encode_slot(DEFAULT_PARAMS, BASE_GEN))
    raw[0:2] = b"\x00\x00"                    # 1) 失效 magic
    raw[4:8] = NEXT_GEN.to_bytes(4, "big")     # 2) 代数先落盘
    raw[12:14] = (550).to_bytes(2, "big")      # 3) ot_c10 已写新值
    return bytes(raw)                          # 4) ocp/crc/magic 未完成：断电


def _bitflip_bytes() -> bytes:
    raw = bytearray(encode_slot(INTENDED_PARAMS, NEXT_GEN))
    value = int.from_bytes(raw[12:14], "big")
    raw[12:14] = (value ^ 0x0800).to_bytes(2, "big")  # ot_c10 550 → 2598（259.8 °C）
    return bytes(raw)


def _flip_crc_a() -> bytes:
    raw = bytearray(encode_slot(DEFAULT_PARAMS, BASE_GEN))
    raw[18] ^= 0x01
    return bytes(raw)


def build_param_section() -> dict[str, object]:
    a = encode_slot(DEFAULT_PARAMS, BASE_GEN)
    b = encode_slot(INTENDED_PARAMS, NEXT_GEN)
    b_version = encode_slot(INTENDED_PARAMS, NEXT_GEN, schema=3)
    b_range = encode_slot(dict(INTENDED_PARAMS, ovp_mv=5_000), NEXT_GEN)
    b_mid = _mid_write_bytes()
    b_flip = _bitflip_bytes()
    a_bad = _flip_crc_a()

    cases = [
        _boot("healthy_both_valid", a, b, "A=41、B=42 都通过校验链；取新一代 B"),
        _boot(
            "mid_write_reset",
            a,
            b_mid,
            "写 B 中途断电：magic 已失效、代数 42 已落盘、ot 写了一半、CRC 仍旧",
        ),
        _boot("crc_bitflip", a, b_flip, "B 完整但 ot 字段一位翻转，CRC 覆盖后失配"),
        _boot("version_mismatch", a, b_version, "B 的 schema=3，本固件只认 2；CRC 正确"),
        _boot("range_fail", a, b_range, "B 的 OVP=5000 mV 越出 [4000,4300]；CRC 正确"),
        _boot("both_bad", a_bad, b_flip, "A 的 CRC 翻一位、B 的 payload 翻一位：双槽全坏"),
    ]
    case_by_name = {_text(case["case"]): case for case in cases}
    mid = case_by_name["mid_write_reset"]
    repaired_b = encode_slot(DEFAULT_PARAMS, BASE_GEN)
    after_repair = _boot("after_repair", a, repaired_b, "用 A 槽内容重写 B，代数保持 41")
    defaults_case = case_by_name["both_bad"]
    mid_values = _int_dict(_dict_of(mid["slots"])["b"]["values"])
    bitflip_case = case_by_name["crc_bitflip"]
    bitflip_robust = _int_dict(bitflip_case["params"])
    bitflip_naive = _int_dict(_map_of(bitflip_case["naive"])["params"])
    return {
        "layout": {
            "magic": "2B",
            "schema": "2B",
            "gen": "4B",
            "ovp_mv": "2B",
            "uvp_mv": "2B",
            "ot_c10": "2B",
            "ocp_ma": "4B",
            "crc16": "2B（CRC-16/CCITT-FALSE，覆盖前 18 B）",
            "size_bytes": PARAM_SIZE,
        },
        "chain": "CRC → 版本 → 范围；magic 属于 CRC 覆盖的身份字段",
        "current_schema": PARAM_SCHEMA_CURRENT,
        "base_gen": BASE_GEN,
        "next_gen": NEXT_GEN,
        "cases": cases,
        "mid_write_recovery": {
            "boot1": mid,
            "boot2": after_repair,
            "counter_after_boot1": mid["selected_gen"],
            "counter_after_repair": after_repair["selected_gen"],
            "intended_gen_lost": NEXT_GEN,
            "boots_to_healthy": 2,
            "path": [
                "上电扫描 A/B：B 未通过 CRC，拒绝",
                "使用 A 槽（代数 41），状态 DEGRADED 并记录 slot_b_crc_rejected",
                "用 A 的内容重写 B（代数仍 41）",
                "再次上电：两槽一致，健康",
            ],
        },
        "defaults_boot": {
            "selected": defaults_case["selected"],
            "selected_gen": defaults_case["selected_gen"],
            "params": defaults_case["params"],
            "gen_after_repair": 1,
            "path": "双槽全坏 → 安全默认值 → 以代数 1 重写两槽",
        },
        "torn_fields": {
            "ot_c10_intended": INTENDED_PARAMS["ot_c10"],
            "ot_c10_torn": mid_values["ot_c10"],
            "ocp_ma_torn": mid_values["ocp_ma"],
            "note": "ot 已是新值、ocp 还是旧值：撕裂配置即使 CRC 不管，也不应被当成一代合法参数",
        },
        "bitflip_evidence": {
            "ot_c10_robust": bitflip_robust["ot_c10"],
            "ot_c10_naive": bitflip_naive["ot_c10"],
            "naive_selected_gen": _map_of(bitflip_case["naive"])["selected_gen"],
            "note": "朴素选择器取代数 42 的 B，把过温阈值读成 259.8 °C，OT 永不触发",
        },
        "crc_bitflip_recovery": {
            "boot1_selected": bitflip_case["selected"],
            "boot1_gen": bitflip_case["selected_gen"],
            "boot1_status": bitflip_case["status"],
            "boot2_selected": after_repair["selected"],
            "boot2_gen": after_repair["selected_gen"],
            "boot2_status": after_repair["status"],
            "path": "B CRC 失配 → 用 A（41）→ 用 A 重写 B → 两槽一致，第二次上电健康",
        },
        "boot_chain": _boot_chain(cases),
    }


def _boot_chain(cases: list[dict[str, object]]) -> list[dict[str, object]]:
    chain: list[dict[str, object]] = []
    for case in cases:
        degraded = _dict_list(case["degraded"])
        if case["selected"] is None:
            stage = "defaults"
            rejected_slot: object = None
        elif not degraded:
            stage = "ok"
            rejected_slot = None
        else:
            rejected = degraded[0]
            stage = rejected["stage"]
            rejected_slot = rejected["slot"]
        chain.append(
            {
                "case": case["case"],
                "rejected_slot": rejected_slot,
                "stage": stage,
                "status": case["status"],
                "selected": case["selected"],
                "selected_gen": case["selected_gen"],
            }
        )
    return chain


# --- D08 / D19 / D17 接口 ---

def counter_delta(new: int, old: int, modulus: int) -> int:
    return (new - old) % modulus


def sequence_state(new: int, old: int, modulus: int = 16) -> dict[str, object]:
    """D19 帧计数器与 D20 epoch 共用的模运算判新旧规则。"""
    delta = counter_delta(new, old, modulus)
    if delta == 0:
        state = "repeat"
    elif delta == 1:
        state = "continuous"
    elif delta < modulus // 2:
        state = "gap"
    elif delta == modulus // 2:
        state = "ambiguous"
    else:
        state = "late_or_reset"
    return {
        "new": new,
        "old": old,
        "modulus": modulus,
        "delta": delta,
        "state": state,
        "missing": delta - 1 if state == "gap" else 0,
    }


D19_PROBES = (
    (1, 14, 16),
    (15, 0, 16),
    (15, 15, 16),
    (8, 0, 16),
    (15, 2, 16),
    (0, 14, 16),
)


def build_interface_section(
    rows: list[dict[str, object]],
    watchdog: dict[str, object],
    params: dict[str, object],
) -> dict[str, object]:
    fast = lane_summary(rows, "fast")
    slow = lane_summary(rows, "slow")
    d08_jitter_ms = _ms(_int(fast["max_nominal_start_jitter_us"]))
    slow_headroom = SLOW_BUDGET_US - ESTIMATE_WCET_US
    return {
        "d08": {
            "electrical_window_ms": D08_WORST_WINDOW_MS,
            "d08_scheduling_term_ms": D08_SCHED_TERM_MS,
            "fast_max_nominal_start_jitter_ms": d08_jitter_ms,
            "within_d08_scheduling_term": d08_jitter_ms <= D08_SCHED_TERM_MS,
            "window_unchanged": True,
            "note": (
                "D20 不改写 D08 的 72.263 ms；快任务无故障时的启动抖动是观测值，"
                "不重新分配 D08 的 5 ms 教学调度项。注入超限的反例拍单独报告，不混进基线。"
            ),
        },
        "d19": {
            "rule": "d=(new−old) mod modulus；0=重复，1=连续，2..modulus/2−1=跳号，modulus/2=歧义，其余=迟到/复位",
            "snapshot_epoch_modulus": 65_536,
            "frame_counter_modulus": 16,
            "probes": [sequence_state(new, old, modulus) for new, old, modulus in D19_PROBES],
            "pending_example": sequence_state(1, 14, 16),
            "note": (
                "D19 的帧计数器与 D20 的快照 epoch 用同一条模运算规则；epoch 是快照身份，"
                "不是时间戳，也不能替代 CRC/身份/新鲜度检查。"
            ),
        },
        "d17": {
            "estimate_wcet_us": ESTIMATE_WCET_US,
            "slow_lane_budget_us": SLOW_BUDGET_US,
            "share_of_slow_budget": round(ESTIMATE_WCET_US / SLOW_BUDGET_US, 4),
            "slow_lane_headroom_us": slow_headroom,
            "slow_observed_wcet_us": slow["wcet_us"],
            "note": (
                "D17 的滤波/估计任务在 100 ms 慢泳道：预算 40 ms 中占 8 ms，"
                "剩 32 ms 给滤波、日志与通信；D17 改窗口集合不改变本泳道预算。"
            ),
        },
        "watchdog_timeout_us": watchdog["timeout_us"],
        "param_chain": params["chain"],
    }


# --- 报告与 CLI ---

def _timeout_section(watchdog: dict[str, object]) -> dict[str, object]:
    withheld = watchdog["withheld"]
    max_gap = _int(watchdog["max_gap_us"])
    timeout = _int(watchdog["timeout_us"])
    withhold_ticks = [_int(item["tick"]) for item in withheld]  # type: ignore[union-attr]
    chain: list[dict[str, object]] = [
        {
            "stage": "wcet",
            "tick": OVERRUN_TICK,
            "t_us": (OVERRUN_TICK + 1) * FAST_PERIOD_US,
            "detail": f"快任务 {OVERRUN_EXEC_US} µs > 预算 {FAST_BUDGET_US} µs（超出 {OVERRUN_EXEC_US - FAST_BUDGET_US} µs）",
        }
    ]
    for item in withheld:  # type: ignore[union-attr]
        chain.append(
            {
                "stage": "deadline" if item["reason"] == "deadline_miss" else "snapshot",
                "tick": item["tick"],
                "t_us": item["t_us"],
                "detail": f"response={item['response_us']} µs, snapshot_complete={item['snapshot_complete']}",
            }
        )
        chain.append(
            {
                "stage": "watchdog",
                "tick": item["tick"],
                "t_us": item["t_us"],
                "detail": "feed withheld",
            }
        )
    recovery = [
        item for item in watchdog["transitions"] if item["stage"] == "recovery"  # type: ignore[union-attr]
    ]
    if recovery:
        chain.append(
            {
                "stage": "recovery",
                "tick": None,
                "t_us": recovery[0]["t_us"],
                "detail": recovery[0]["reason"],
            }
        )
    return {
        "tick": OVERRUN_TICK,
        "release_us": (OVERRUN_TICK + 1) * FAST_PERIOD_US,
        "exec_us": OVERRUN_EXEC_US,
        "budget_us": FAST_BUDGET_US,
        "overrun_us": OVERRUN_EXEC_US - FAST_BUDGET_US,
        "deadline_miss_ticks": withhold_ticks,
        "detected_at_us": OVERRUN_TICK * FAST_PERIOD_US + FAST_DEADLINE_US,
        "withheld_feeds": _int(watchdog["withheld_count"]),
        "late_complete_snapshots": watchdog["late_complete_snapshots"],
        "max_feed_gap_us": max_gap,
        "watchdog_timeout_us": timeout,
        "watchdog_margin_us": timeout - max_gap,
        "reset": watchdog["reset_at_us"] is not None,
        "recovery_t_us": recovery[0]["t_us"] if recovery else None,
        "chain": chain,
        "propagation": [item for item in watchdog["transitions"] if item["stage"] != "boot"],  # type: ignore[union-attr]
    }


def build_report() -> dict[str, object]:
    rows = simulate_schedule()
    watchdog = watchdog_audit(rows)
    params = build_param_section()
    snapshot = snapshot_ownership()
    lanes = {lane: lane_summary(rows, lane) for lane in TRACE_LANES}
    return {
        "scenario_id": SCENARIO_ID,
        "identity": (
            "教学用实时固件模型（固定优先级可抢占单核）；WCET、抖动、看门狗超时、故障拍号、"
            "参数代数与阈值全部是构造的教学值——不是实测 WCET、不是器件测量、不是 HIL、"
            "不构成功能安全论证；未烧录固件、未驱动 MOS、未在真实硬件上观测"
        ),
        "boundary": {
            "bms_inputs_fields": ["cell_mv[]", "current_ma", "temp_c10", "charger_present"],
            "missing_fields": ["timestamp", "quality_bit", "snapshot_epoch"],
            "firmware_gap": (
                "固件 BmsInputs 只有 cell_mv[]/current_ma/temp_c10/charger_present：没有"
                "时间戳、质量位或采样序号；固件骨架也没有任务表、看门狗与参数 A/B 槽。"
                "本单元的调度、双缓冲、喂狗与参数原子性是教学补全，不证明固件已实现。"
            ),
            "no_hardware": "软件在环；未烧录、未用示波器/逻辑分析仪测量、未做 WCET 静态分析或 HIL 验收",
            "book_layer_gap": (
                "bms-book/book/33-实时固件与数据所有权.md 尚缺（书层缺口）；本单元只闭合"
                "工程层 SRC05，不虚构该书引用"
            ),
        },
        "lanes": lanes,
        "wcet_jitter": [
            {
                "lane": lane,
                "period_us": lanes[lane]["period_us"],
                "budget_us": lanes[lane]["budget_us"],
                "deadline_us": lanes[lane]["deadline_us"],
                "wcet_us": lanes[lane]["wcet_us"],
                "wcet_nominal_us": lanes[lane]["wcet_nominal_us"],
                "headroom_us": lanes[lane]["budget_us"] - lanes[lane]["wcet_nominal_us"],  # type: ignore[operator]
                "max_start_jitter_us": lanes[lane]["max_start_jitter_us"],
                "max_nominal_start_jitter_us": lanes[lane]["max_nominal_start_jitter_us"],
                "max_response_us": lanes[lane]["max_response_us"],
                "load": lanes[lane]["load"],
            }
            for lane in TRACE_LANES
        ],
        "rta": {
            "nominal": response_time_analysis(5_230, 13_500, 160),
            "overrun_probe": response_time_analysis(OVERRUN_EXEC_US, 13_500, 160),
            "note": "RTA 用各泳道名义最坏执行时间；超限探针说明单拍 14 ms 时快任务上界 16.72 ms，慢任务上界发散",
        },
        "watchdog": {
            "timeout_us": WATCHDOG_TIMEOUT_US,
            "feed_rule": FEED_RULE,
            "feeds": watchdog["feed_count"],
            "withheld_count": watchdog["withheld_count"],
            "withheld": watchdog["withheld"],
            "max_gap_us": watchdog["max_gap_us"],
            "margin_us": watchdog["margin_us"],
            "reset": watchdog["reset_at_us"] is not None,
            "reset_at_us": watchdog["reset_at_us"],
            "final_state": watchdog["final_state"],
            "transitions": watchdog["transitions"],
            "reset_probe": watchdog_reset_probe(),
        },
        "snapshot": snapshot,
        "timeout": _timeout_section(watchdog),
        "params": params,
        "interfaces": build_interface_section(rows, watchdog, params),
        "replay": replay_report(rows, source="内置 task_trace.csv（与默认时间线同源）"),
        "conclusion": (
            "一帧混用两次采样、单拍 WCET 超限、参数写一半断电，三件事故都能在软件在环里"
            "被逐拍指认：epoch 把混用降到 0，喂狗规则把一次超限传播成两次缺喂与一次降级，"
            "CRC+代数的 A/B 槽把撕裂配置挡在启动之外。它们仍是教学构造，不是硬件验收。"
        ),
    }


def load_trace(path: Path) -> list[dict[str, object]]:
    """读取任务执行 trace，严格执行数据合同；任何违约都拒绝而不是猜测。"""
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError("空文件，缺表头") from exc
        if header != TRACE_COLUMNS:
            raise ValueError(f"表头必须是 {','.join(TRACE_COLUMNS)}，得到 {','.join(header)}")
        raw_rows = list(reader)
    if not raw_rows:
        raise ValueError("没有数据行")
    if len(raw_rows) > TRACE_MAX_ROWS:
        raise ValueError(f"数据行 {len(raw_rows)} 超过上限 {TRACE_MAX_ROWS}")
    rows: list[dict[str, object]] = []
    seen_jobs: set[str] = set()
    last_release: dict[str, int] = {}
    last_finish: dict[str, int] = {}
    for line_no, raw in enumerate(raw_rows, start=2):
        if len(raw) != len(TRACE_COLUMNS):
            raise ValueError(f"第 {line_no} 行列数 {len(raw)}，应为 {len(TRACE_COLUMNS)}")
        job, lane = raw[0], raw[1]
        if lane not in TRACE_LANES:
            raise ValueError(f"第 {line_no} 行未知泳道 {lane!r}")
        if job in seen_jobs:
            raise ValueError(f"第 {line_no} 行重复 job {job!r}")
        seen_jobs.add(job)
        try:
            release_us, start_us, finish_us, exec_us = (int(value) for value in raw[2:])
        except ValueError as exc:
            raise ValueError(f"第 {line_no} 行时间列必须是整数微秒") from exc
        if release_us < 0 or start_us < 0 or finish_us < 0 or exec_us < 0:
            raise ValueError(f"第 {line_no} 行出现负时间")
        if not release_us <= start_us <= finish_us:
            raise ValueError(f"第 {line_no} 行时间顺序必须是 release ≤ start ≤ finish")
        if exec_us > finish_us - start_us:
            raise ValueError(f"第 {line_no} 行 exec 大于 start→finish 的墙钟跨度")
        if exec_us > TRACE_MAX_EXEC_US[lane]:
            raise ValueError(
                f"第 {line_no} 行 {lane} exec {exec_us} µs 超过上界 {TRACE_MAX_EXEC_US[lane]} µs"
            )
        if finish_us > TRACE_MAX_SPAN_US:
            raise ValueError(f"第 {line_no} 行时间超过 {TRACE_MAX_SPAN_US} µs 上界")
        if lane in last_release and release_us < last_release[lane]:
            raise ValueError(f"第 {line_no} 行 {lane} 释放时间回退")
        if lane in last_finish and start_us < last_finish[lane]:
            raise ValueError(f"第 {line_no} 行 {lane} 与上一作业重叠")
        last_release[lane] = release_us
        last_finish[lane] = finish_us
        deadline_us = {
            "isr": ISR_DEADLINE_US,
            "fast": FAST_DEADLINE_US,
            "slow": SLOW_DEADLINE_US,
        }[lane]
        rows.append(
            {
                "job": job,
                "lane": lane,
                "index": len([row for row in rows if row["lane"] == lane]),
                "release_us": release_us,
                "start_us": start_us,
                "finish_us": finish_us,
                "exec_us": exec_us,
                "response_us": finish_us - release_us,
                "start_jitter_us": start_us - release_us,
                "deadline_us": deadline_us,
            }
        )
    if len(rows) < TRACE_MIN_ROWS:
        raise ValueError(f"样本 {len(rows)} 少于下限 {TRACE_MIN_ROWS}")
    present = {_text(row["lane"]) for row in rows}
    missing = {"fast", "slow"} - present
    if missing:
        raise ValueError(f"缺少泳道 {','.join(sorted(missing))}")
    return rows


def replay_report(rows: list[dict[str, object]], source: str) -> dict[str, object]:
    watchdog = watchdog_audit(rows)
    lanes = {lane: lane_summary(rows, lane) for lane in TRACE_LANES}
    fast_misses = lanes["fast"]["deadline_miss_ticks"]
    return {
        "scenario_id": REPLAY_SCENARIO_ID,
        "source": source,
        "identity": (
            "回放审计：把用户任务 trace 当作已发生的执行记录，只按同一套泳道合同重算；"
            "教学阈值不变，回放不证明这些 WCET 在真实硬件上成立"
        ),
        "lanes": lanes,
        "wcet_jitter": [
            {
                "lane": lane,
                "budget_us": lanes[lane]["budget_us"],
                "wcet_us": lanes[lane]["wcet_us"],
                "max_start_jitter_us": lanes[lane]["max_start_jitter_us"],
                "max_response_us": lanes[lane]["max_response_us"],
                "deadline_miss_ticks": lanes[lane]["deadline_miss_ticks"],
            }
            for lane in TRACE_LANES
            if lanes[lane]["present"]
        ],
        "watchdog": {
            "timeout_us": watchdog["timeout_us"],
            "feed_rule": watchdog["feed_rule"],
            "feeds": watchdog["feed_count"],
            "withheld_count": watchdog["withheld_count"],
            "withheld": watchdog["withheld"],
            "max_gap_us": watchdog["max_gap_us"],
            "margin_us": watchdog["margin_us"],
            "reset_at_us": watchdog["reset_at_us"],
            "final_state": watchdog["final_state"],
        },
        "verdict": "deadline_miss" if fast_misses else "on_time",
        "note": (
            "回放只覆盖调度与喂狗；快照混用与参数 A/B 槽不在 trace 列里，不能由本回放证明"
        ),
    }


def write_task_trace(rows: list[dict[str, object]], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(TRACE_COLUMNS)
        for row in rows:
            writer.writerow(
                [
                    row["job"],
                    row["lane"],
                    row["release_us"],
                    row["start_us"],
                    row["finish_us"],
                    row["exec_us"],
                ]
            )


def write_snapshot_frames(rows: list[dict[str, object]], path: Path) -> None:
    columns = [
        "scheme",
        "frame",
        "start_us",
        "cell_mv_source",
        "current_ma_source",
        "temp_c10_source",
        "charger_source",
        "isr_seq_source",
        "mixed",
        "stale",
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(
                [
                    row["scheme"],
                    row["frame"],
                    row["start_us"],
                    row["cell_mv_source"],
                    row["current_ma_source"],
                    row["temp_c10_source"],
                    row["charger_source"],
                    row["isr_seq_source"],
                    str(row["mixed"]).lower(),
                    str(row["stale"]).lower(),
                ]
            )


def write_param_boot(params: dict[str, object], path: Path) -> None:
    columns = ["case", "slot", "stage", "gen", "crc_ok", "schema", "selected", "selected_gen", "status"]
    cases = params["cases"]
    if not isinstance(cases, list):
        raise ValueError("params.cases 结构错误")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for case in cases:
            if not isinstance(case, dict):
                continue
            slots = case["slots"]
            if not isinstance(slots, dict):
                continue
            for name in ("a", "b"):
                slot = slots[name]
                if not isinstance(slot, dict):
                    continue
                writer.writerow(
                    [
                        case["case"],
                        name,
                        slot["failure_stage"],
                        slot["gen"],
                        str(slot["crc_ok"]).lower(),
                        slot["schema"],
                        case["selected"],
                        case["selected_gen"],
                        case["status"],
                    ]
                )


def _write_default_artifacts(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    report = build_report()
    (out / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_task_trace(simulate_schedule(), out / "task_trace.csv")
    write_snapshot_frames(snapshot_frame_rows(), out / "snapshot_frames.csv")
    write_param_boot(build_param_section(), out / "param_boot.csv")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 与 CSV 工件的目录")
    parser.add_argument(
        "--trace",
        type=Path,
        help=f"回放任务执行 trace（{','.join(TRACE_COLUMNS)}）",
    )
    args = parser.parse_args(argv)

    if args.trace is not None:
        try:
            rows = load_trace(args.trace)
        except (OSError, ValueError) as exc:
            print(f"回放数据拒绝：{exc}", file=sys.stderr)
            return 2
        report = replay_report(rows, source=str(args.trace))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if args.out:
            args.out.mkdir(parents=True, exist_ok=True)
            (args.out / "report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        return 0

    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        _write_default_artifacts(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
