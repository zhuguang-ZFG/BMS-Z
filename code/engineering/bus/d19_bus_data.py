"""Teaching experiments for D19: bus boundary and end-to-end data.

D19「总线与端到端数据」的可执行证据模块。四件事：

1. 帧的生命周期：位/字节 → 物理信号 → 身份 → 完整性（CRC）→ 会话 → 计数器窗口 →
   交付或保持；每一步给出失败原因码与动作。
2. 计数器窗口语义：4 bit 滚动计数、窗口 +2（只向前开）；回绕、重复、乱序、旧帧各
   按「对最后已接受帧的模差」判定，不按到达顺序判定。
3. 反例：CRC 全对的旧帧、15→2 的回绕越窗、5,7,6 的乱序、连续丢 5 帧后的降级与
   恢复拍数——四个反例的判定与计数全部冻结在本模块的报告里。
4. 回放合同：`--frames` 读入用户 CSV（至少 `seq,data` 两列），重算 CRC、重跑同一
   状态机；缺文件/错表头/缺列/非有限/时间回退/越界/样本不足一律 exit 2。

教学身份：位时间、位填充上界、差分电平、超时预算、编码因子都是教学值，用于展示
传输边界与判定链的结构；它们不认定为任何收发器手册、总线一致性测试、器件实测或
在环（HIL）证据。真实总线时序与 CRC 口径必须按具体协议与实测波形取得（SRC05）。
CRC 只证明「这段字节在传输中没有被改坏」，**不证明新鲜度**：一帧逐字节相同的旧帧
可以 CRC 全对。

边界（必须与正文同页）：固件 `BmsInputs`（code/firmware/bms.h）只有
`cell_mv[]/current_ma/temp_c10/charger_present`，没有时间戳、没有质量位、没有
计数器/会话字段——固件层面没有地方存放「这是第几帧、上次可信值何时更新」，本模块
的窗口判定、超时账与降级保持是教学补全，不证明固件已实现新鲜度门。`code/protocol/`
是协议维护源（CRC 基准向量与帧解析器的家），本模块不 import 它：帧格式按教材口径
独立实现，不能当作任何厂商协议的解析器。
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

SCENARIO_ID = "D19-bus-lifecycle"
REPLAY_SCENARIO_ID = "D19-frame-replay"

# --- 教学帧：CAN 2.0A 风格数据帧（ID 11 bit、DLC 8、载荷 8 B、CRC-16 覆盖）---
MSG_ID = 0x18F
DLC = 8
PAYLOAD_BYTES = DLC
COUNTER_BITS = 4
SESSION_BITS = 4
COUNTER_MODULUS = 1 << COUNTER_BITS
COUNTER_WINDOW = 2          # 只向前开：delta ∈ {1, 2} 接受
SESSION_BITS_MASK = (1 << SESSION_BITS) - 1

# --- 时基与超时预算（教学值）---
BIT_RATE_KBPS = 500.0
BIT_TIME_US = 1000.0 / BIT_RATE_KBPS          # 2.0 µs/bit
SAMPLE_POINT_PCT = 75.0
FRAME_PERIOD_MS = 20.0
FRAME_TIMEOUT_MS = 100.0
# t_timeout ≥ t_period + t_jitter + t_transport + t_margin（书 18.3 的口径）
TIMEOUT_BUDGET_MS = {
    "period": 20.0,
    "jitter": 5.0,
    "transport": 25.0,
    "margin": 50.0,
}
DEGRADE_AFTER_MISSING = 3    # 连续丢 ≥3 帧进入 degraded
RECOVERY_FRAMES = 3          # 连续 3 拍（观察计数连续）退出 degraded
SILENT_TAIL_PERIODS = 5      # 默认场景的静默视界：末帧后 +5 拍（教学值）

# --- CAN 2.0A 数据帧位预算（教学算术）---
CAN_SOF_BITS = 1
CAN_ID_BITS = 11
CAN_RTR_BITS = 1
CAN_IDE_BITS = 1
CAN_R0_BITS = 1
CAN_DLC_BITS = 4
CAN_CRC_BITS = 15
CAN_CRC_DELIM_BITS = 1
CAN_ACK_BITS = 2
CAN_EOF_BITS = 7
CAN_IFS_BITS = 3
DATA_BITS = PAYLOAD_BYTES * 8
# 位填充作用于 SOF..CRC 序列；CRC 定界符之后的字段不参与填充。
STUFFABLE_BITS = (
    CAN_SOF_BITS
    + CAN_ID_BITS
    + CAN_RTR_BITS
    + CAN_IDE_BITS
    + CAN_R0_BITS
    + CAN_DLC_BITS
    + DATA_BITS
    + CAN_CRC_BITS
)
NOMINAL_BITS = (
    STUFFABLE_BITS + CAN_CRC_DELIM_BITS + CAN_ACK_BITS + CAN_EOF_BITS + CAN_IFS_BITS
)
# 最坏填充：5 位相同 → 插 1 位反相；此后每 4 位即可再次凑满 5 位（填充位自身入计数）。
WORST_STUFF_BITS = 1 + (STUFFABLE_BITS - 5) // 4
WORST_BITS = NOMINAL_BITS + WORST_STUFF_BITS
# 对照：整段填充区同值（例如全 0）时的填充数——它不是最坏，只是最常见。
UNIFORM_REGION_STUFF_BITS = STUFFABLE_BITS // 5

# --- CRC-16/CCITT-FALSE（poly 0x1021, init 0xFFFF, 不反射, 无 xorout）---
CRC16_POLY = 0x1021
CRC16_INIT = 0xFFFF
CRC16_CHECK_VALUE = 0x29B1  # "123456789" 的检查值，防「参数记错」

# --- 物理层与编码（教学口径）---
BIT_LEVELS: dict[str, dict[str, float | int]] = {
    "dominant": {"logic": 0, "can_h_v": 3.5, "can_l_v": 1.5, "diff_v": 2.0},
    "recessive": {"logic": 1, "can_h_v": 2.5, "can_l_v": 2.5, "diff_v": 0.0},
}

# 载荷 8 B 的信号编码表：字节位置 / 位段 / 因子 / 偏移 / 单位。
SIGNAL_ENCODING: list[dict[str, object]] = [
    {
        "signal": "session",
        "bytes": "0[7:4]",
        "bits": 4,
        "lsb_value": 1.0,
        "offset": 0.0,
        "unit": "session id",
        "example_raw": 1,
        "example_value": 1.0,
    },
    {
        "signal": "counter",
        "bytes": "0[3:0]",
        "bits": 4,
        "lsb_value": 1.0,
        "offset": 0.0,
        "unit": "count",
        "example_raw": 0,
        "example_value": 0.0,
    },
    {
        "signal": "status",
        "bytes": "1",
        "bits": 8,
        "lsb_value": 1.0,
        "offset": 0.0,
        "unit": "flags(bit0 degraded_local, bit1 charger_present, bit2 init)",
        "example_raw": 0,
        "example_value": 0.0,
    },
    {
        "signal": "pack_mv",
        "bytes": "2..3 (BE)",
        "bits": 16,
        "lsb_value": 1.0,
        "offset": 0.0,
        "unit": "mV",
        "example_raw": 51200,
        "example_value": 51200.0,
    },
    {
        "signal": "current_da",
        "bytes": "4..5 (BE, signed)",
        "bits": 16,
        "lsb_value": 0.1,
        "offset": 0.0,
        "unit": "A",
        "example_raw": 120,
        "example_value": 12.0,
    },
    {
        "signal": "temp_c",
        "bytes": "6",
        "bits": 8,
        "lsb_value": 1.0,
        "offset": -40.0,
        "unit": "degC",
        "example_raw": 75,
        "example_value": 35.0,
    },
    {
        "signal": "soc_pp",
        "bytes": "7",
        "bits": 8,
        "lsb_value": 0.5,
        "offset": 0.0,
        "unit": "%",
        "example_raw": 120,
        "example_value": 60.0,
    },
]

# 帧生命周期的六段：每段只回答一个问题，失败即短路并记账。
LIFECYCLE_STAGES: list[dict[str, str]] = [
    {
        "stage": "arrival",
        "question": "这一拍到底有没有帧？",
        "failure": "timeout / missing slot",
        "action": "保持上次可信值并置超时标志；丢帧数按到达间隔计",
    },
    {
        "stage": "identity",
        "question": "msg_id 与 DLC 是目标报文吗？",
        "failure": "identity",
        "action": "拒绝；计数器不推进",
    },
    {
        "stage": "integrity",
        "question": "CRC 对得上吗？",
        "failure": "crc",
        "action": "拒绝；字段不再解释（CRC 不过就不该读它的位）",
    },
    {
        "stage": "session",
        "question": "是本次上电生命周期的帧吗？",
        "failure": "session",
        "action": "拒绝；受控重同步需要带外证据，本模块不自动采纳",
    },
    {
        "stage": "counter",
        "question": "序号在窗口内吗？",
        "failure": "duplicate / late / gap_too_large / ambiguous",
        "action": "拒绝；degraded 内改走连续计数重同步",
    },
    {
        "stage": "publish",
        "question": "这个值现在能交付吗？",
        "failure": "degraded",
        "action": "保持上次可信值；恢复正常后才更新",
    },
]

REJECT_REASONS = (
    "identity",
    "crc",
    "session",
    "duplicate",
    "late",
    "gap_too_large",
    "ambiguous",
)

# --- D19-frame-replay：回放数据合同（至少 seq,data 两列）---
REQUIRED_FRAME_COLUMNS = ["seq", "data"]
OPTIONAL_FRAME_COLUMNS = ["t_ms", "crc_hex"]
MIN_FRAMES = 10
DECISION_COLUMNS = [
    "seq",
    "t_ms",
    "counter",
    "session",
    "crc_ok",
    "delta",
    "resync_delta",
    "decision",
    "reason",
    "state_after",
    "checks_evaluated",
    "soc_pp",
    "published_soc_pp",
    "data_age_ms",
    "stale_data",
    "missing_slots",
    "timeout_flag",
]


def _as_int(value: object) -> int:
    """从解码字典取整数（pyright 友好，同时是运行时契约检查）。"""
    if not isinstance(value, int):
        raise TypeError(f"期望整数，得到 {type(value).__name__}")
    return value


def _as_float(value: object) -> float:
    """从解码字典取数值（pyright 友好，同时是运行时契约检查）。"""
    if not isinstance(value, (int, float)):
        raise TypeError(f"期望数值，得到 {type(value).__name__}")
    return float(value)


# --- 编码层：CRC / 载荷 / 物理信号 ---

def crc16_ccitt_false(data: bytes) -> int:
    """CRC-16/CCITT-FALSE：poly 0x1021、init 0xFFFF、不反射、无 xorout。"""
    crc = CRC16_INIT
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ CRC16_POLY) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def crc_covered_bytes(msg_id: int, dlc: int, payload: bytes) -> bytes:
    """CRC 覆盖域：msg_id 两字节大端 + DLC + 全部载荷。

    覆盖 DLC 与整段载荷（不是只覆盖 payload）：长度字段也是判断「该读几位」的输入，
    只校验载荷会让「截短/加长」这类改动绕过完整性检查。
    """
    if not 0 <= msg_id <= 0x7FF:
        raise ValueError(f"msg_id 越界: {msg_id}")
    if not 0 <= dlc <= 64:
        raise ValueError(f"dlc 越界: {dlc}")
    return bytes([(msg_id >> 8) & 0xFF, msg_id & 0xFF, dlc]) + payload


def frame_crc(msg_id: int, dlc: int, payload: bytes) -> int:
    return crc16_ccitt_false(crc_covered_bytes(msg_id, dlc, payload))


def encode_payload(
    counter: int,
    session: int,
    *,
    pack_mv: int = 51200,
    current_da: int = 120,
    temp_c: int = 35,
    soc_pp: float = 60.0,
    status: int = 0,
) -> bytes:
    """按编码表把物理信号打包成 8 B 载荷；越界一律 ValueError，不静默截断。"""
    if not 0 <= counter < COUNTER_MODULUS:
        raise ValueError(f"counter 越界: {counter}")
    if not 0 <= session <= SESSION_BITS_MASK:
        raise ValueError(f"session 越界: {session}")
    if not 0 <= pack_mv <= 0xFFFF:
        raise ValueError(f"pack_mv 越界: {pack_mv}")
    if not -0x8000 <= current_da <= 0x7FFF:
        raise ValueError(f"current_da 越界: {current_da}")
    if not -40 <= temp_c <= 215:
        raise ValueError(f"temp_c 越界: {temp_c}")
    soc_raw = round(soc_pp / 0.5)
    if not 0 <= soc_raw <= 0xFF:
        raise ValueError(f"soc_pp 越界: {soc_pp}")
    if not 0 <= status <= 0xFF:
        raise ValueError(f"status 越界: {status}")
    return bytes(
        [
            ((session & SESSION_BITS_MASK) << 4) | (counter & 0x0F),
            status & 0xFF,
            (pack_mv >> 8) & 0xFF,
            pack_mv & 0xFF,
            (current_da >> 8) & 0xFF,
            current_da & 0xFF,
            temp_c + 40,
            soc_raw,
        ]
    )


def decode_signals(payload: bytes) -> dict[str, object]:
    """把 8 B 载荷还原成物理信号（与 encode_payload 互逆）。"""
    if len(payload) != PAYLOAD_BYTES:
        raise ValueError(f"载荷长度必须为 {PAYLOAD_BYTES} B，得到 {len(payload)}")
    pack_mv = int.from_bytes(payload[2:4], "big")
    current_da = int.from_bytes(payload[4:6], "big", signed=True)
    status = payload[1]
    return {
        "session": payload[0] >> 4,
        "counter": payload[0] & 0x0F,
        "status": status,
        "degraded_local": bool(status & 0x01),
        "charger_present": bool(status & 0x02),
        "init": bool(status & 0x04),
        "pack_mv": pack_mv,
        "pack_v": round(pack_mv / 1000.0, 3),
        "current_da": current_da,
        "current_a": round(current_da / 10.0, 1),
        "temp_c": payload[6] - 40,
        "soc_pp": payload[7] * 0.5,
    }


def timing_report() -> dict[str, object]:
    """位/字节到时间的换算：CAN 帧长上界与 UART/Modbus 字符时间对照。"""
    return {
        "bit_rate_kbps": BIT_RATE_KBPS,
        "bit_time_us": round(BIT_TIME_US, 6),
        "sample_point_pct": SAMPLE_POINT_PCT,
        "nominal_bits": NOMINAL_BITS,
        "stuffable_bits": STUFFABLE_BITS,
        "worst_stuff_bits": WORST_STUFF_BITS,
        "worst_bits": WORST_BITS,
        "nominal_frame_us": round(NOMINAL_BITS * BIT_TIME_US, 6),
        "worst_frame_us": round(WORST_BITS * BIT_TIME_US, 6),
        "uniform_region_stuff_bits": UNIFORM_REGION_STUFF_BITS,
        "uniform_region_frame_us": round(
            (NOMINAL_BITS + UNIFORM_REGION_STUFF_BITS) * BIT_TIME_US, 6
        ),
        "period_ms": FRAME_PERIOD_MS,
        "bus_load_pct": round(WORST_BITS * BIT_TIME_US / (FRAME_PERIOD_MS * 1000.0) * 100.0, 4),
        "frame_timeout_ms": FRAME_TIMEOUT_MS,
        "timeout_budget_ms": {
            **TIMEOUT_BUDGET_MS,
            "total": round(sum(TIMEOUT_BUDGET_MS.values()), 4),
        },
        "uart_baud": 115200,
        "uart_bits_per_char": 10,
        "modbus_silence_chars": 3.5,
        "uart_10bit_char_ms_at_115200": round(10.0 / 115200 * 1000.0, 6),
        "modbus_3_5_char_ms_at_115200": round(3.5 * 10.0 / 115200 * 1000.0, 6),
    }


# --- 帧与接收端状态机 ---

@dataclass(frozen=True)
class Frame:
    """一帧到达的完整记录：seq/t_ms 是接收侧观察，其余是线上字节。"""

    seq: int
    t_ms: float
    msg_id: int
    dlc: int
    payload: bytes
    crc_rx: int | None = None  # None = 没有独立的 CRC 副本（按完整处理）


def wire_bytes(frame: Frame) -> bytes:
    """线上字节：msg_id(2B BE) | dlc | payload | crc(2B BE)。"""
    crc = frame_crc(frame.msg_id, frame.dlc, frame.payload)
    return crc_covered_bytes(frame.msg_id, frame.dlc, frame.payload) + crc.to_bytes(2, "big")


def synthetic_payload(counter: int, session: int = 1) -> bytes:
    """确定性的合成载荷：只由 counter/session 决定，因此重放帧与旧帧逐字节相同。"""
    return encode_payload(
        counter,
        session,
        pack_mv=51200 + counter * 10,
        current_da=120 + counter,
        temp_c=35,
        soc_pp=60.0 + counter * 0.5,
    )


def arrival(
    t_ms: float,
    counter: int,
    *,
    session: int = 1,
    seq: int = 0,
    crc_rx: int | None = None,
    msg_id: int = MSG_ID,
    dlc: int = DLC,
) -> Frame:
    payload = synthetic_payload(counter, session)
    return Frame(
        seq=seq,
        t_ms=float(t_ms),
        msg_id=msg_id,
        dlc=dlc,
        payload=payload,
        crc_rx=crc_rx,
    )


def classify_counter(last: int, counter: int, window: int = COUNTER_WINDOW) -> tuple[int, str]:
    """对最后已接受计数做模差分类；窗口只向前开（后向差值与迟到不可区分）。"""
    if not 0 <= window < COUNTER_MODULUS // 2:
        raise ValueError(f"窗口越界: {window}")
    delta = (counter - last) % COUNTER_MODULUS
    if delta == 0:
        return delta, "duplicate"
    if delta <= window:
        return delta, "in_window"
    if delta <= COUNTER_MODULUS // 2 - 1:
        return delta, "gap_too_large"
    if delta == COUNTER_MODULUS // 2:
        return delta, "ambiguous"
    return delta, "late"


@dataclass
class FrameReceiver:
    """接收端状态机：完整性（CRC）→ 身份 → 会话 → 计数器窗口 → 交付/保持。"""

    expected_msg_id: int = MSG_ID
    window: int = COUNTER_WINDOW
    period_ms: float = FRAME_PERIOD_MS
    timeout_ms: float = FRAME_TIMEOUT_MS
    degrade_after_missing: int = DEGRADE_AFTER_MISSING
    recovery_frames: int = RECOVERY_FRAMES
    state: str = "init"
    session: int | None = None
    last_counter: int | None = None
    last_arrival_t: float | None = None
    last_accepted_t: float | None = None
    last_trusted_soc_pp: float | None = None
    published_soc_pp: float | None = None
    recovery_anchor: int | None = None
    recovery_hits: int = 0
    missing_streak: int = 0
    timeout_flag: bool = False
    clock_ms: float = 0.0
    silence_counted: int = 0
    counts: dict[str, int] = field(
        default_factory=lambda: {
            "accepted": 0,
            "rejected": 0,
            "resync_observations": 0,
            "missing_slots": 0,
            "clock_missing_slots": 0,
            "timeout_events": 0,
            "stale_data_events": 0,
            "published_updates": 0,
        }
    )
    reasons: dict[str, int] = field(default_factory=dict)
    transitions: list[dict[str, object]] = field(default_factory=list)

    # -- 内部记录 --
    def _reject(self, reason: str) -> None:
        self.counts["rejected"] += 1
        self.reasons[reason] = self.reasons.get(reason, 0) + 1

    def _transition(
        self,
        seq: int | None,
        t_ms: float,
        to_state: str,
        reason: str,
        source: str = "frame",
    ) -> None:
        self.transitions.append(
            {
                "seq": seq,
                "t_ms": t_ms,
                "from": self.state,
                "to": to_state,
                "reason": reason,
                "source": source,
            }
        )
        self.state = to_state

    def _missing_slots(self, t_ms: float) -> int:
        if self.last_arrival_t is None:
            return 0
        gap = t_ms - self.last_arrival_t
        if gap <= 0.0:
            raise ValueError(f"时间回退：t_ms={t_ms} 不大于上一帧 {self.last_arrival_t}")
        return max(0, int(round(gap / self.period_ms)) - 1)

    def advance_to(self, now_ms: float) -> dict[str, object]:
        """按时钟推进（不依赖帧到达）：丢拍累计、条件首次成立即降级，且绝不自行恢复。

        超时是**时钟属性**，不是帧属性：总线在最后一帧后永久静默时，接收端仍必须在
        deadline 上转 degraded。转移时间戳取条件首次成立的时钟时刻
        （last_arrival + 需要的拍数 × period），不是调用 advance_to 的时刻。
        """
        if not math.isfinite(now_ms):
            raise ValueError(f"时钟非有限: {now_ms!r}")
        if now_ms < 0.0:
            raise ValueError(f"时钟为负: {now_ms}")
        if now_ms < self.clock_ms:
            raise ValueError(f"时钟回退: {now_ms} < {self.clock_ms}")
        if self.last_arrival_t is not None and now_ms < self.last_arrival_t:
            raise ValueError(f"时钟早于最后一帧: {now_ms} < {self.last_arrival_t}")
        self.clock_ms = now_ms
        if self.last_arrival_t is None:
            return {
                "now_ms": now_ms,
                "slots": 0,
                "degraded_at_ms": None,
                "state": self.state,
            }
        gap = now_ms - self.last_arrival_t
        slots = int(math.floor(gap / self.period_ms + 1e-9))
        delta = slots - self.silence_counted
        if delta > 0:
            self.counts["clock_missing_slots"] += delta
            self.silence_counted = slots
        streak = self.missing_streak + slots
        degraded_at: float | None = None
        if streak >= self.degrade_after_missing and self.state != "degraded":
            need = max(0, self.degrade_after_missing - self.missing_streak)
            degraded_at = self.last_arrival_t + need * self.period_ms
            if degraded_at > now_ms:
                degraded_at = now_ms
            self._transition(None, degraded_at, "degraded", "silent_bus", "clock")
            self.recovery_anchor = self.last_counter
            self.recovery_hits = 0
            self.timeout_flag = True
        return {
            "now_ms": now_ms,
            "slots": slots,
            "degraded_at_ms": degraded_at,
            "state": self.state,
        }

    def feed(self, frame: Frame) -> dict[str, object]:
        """处理一帧到达，返回逐帧判定记录（也是 decisions.csv 的一行）。"""
        if len(frame.payload) != PAYLOAD_BYTES:
            raise ValueError(f"载荷长度必须为 {PAYLOAD_BYTES} B，得到 {len(frame.payload)}")

        if frame.t_ms < self.clock_ms:
            raise ValueError(f"帧时间早于已推进的时钟: {frame.t_ms} < {self.clock_ms}")
        signals = decode_signals(frame.payload)
        counter = _as_int(signals["counter"])
        session = _as_int(signals["session"])
        soc_pp = _as_float(signals["soc_pp"])

        data_age_ms: float | None = (
            None if self.last_accepted_t is None else frame.t_ms - self.last_accepted_t
        )
        missing = self._missing_slots(frame.t_ms)
        if self.last_arrival_t is not None and frame.t_ms - self.last_arrival_t > self.timeout_ms:
            self.counts["timeout_events"] += 1
            self.timeout_flag = True
        self.counts["missing_slots"] += missing
        self.missing_streak = self.missing_streak + missing if missing > 0 else 0

        checks: list[str] = []
        delta: int | None = None
        resync_delta: int | None = None
        crc_ok: bool | None = None
        decision = "accept"
        reason = ""
        publish = False

        # 1) 身份：msg_id 与 DLC。
        checks.append("identity")
        if frame.msg_id != self.expected_msg_id or frame.dlc != PAYLOAD_BYTES:
            decision, reason = "reject", "identity"
        else:
            # 2) 完整性：CRC 不过就不再解释任何字段（短路在这里，测试钉住）。
            checks.append("crc")
            computed = frame_crc(frame.msg_id, frame.dlc, frame.payload)
            crc_ok = frame.crc_rx is None or frame.crc_rx == computed
            if not crc_ok:
                decision, reason = "reject", "crc"
            else:
                # 3) 会话：首次收到即学习；此后不匹配一律拒（重同步需带外证据）。
                checks.append("session")
                if self.session is None:
                    self.session = session
                    session_ok = True
                else:
                    session_ok = session == self.session
                if not session_ok:
                    decision, reason = "reject", "session"
                else:
                    # 4) 计数器：正常态按窗口；degraded 态按观察到的连续计数重同步。
                    checks.append("counter")
                    last = self.last_counter
                    if last is not None:
                        delta = (counter - last) % COUNTER_MODULUS
                    if self.state == "degraded":
                        anchor = self.recovery_anchor
                        if anchor is not None:
                            resync_delta = (counter - anchor) % COUNTER_MODULUS
                        if anchor is not None and resync_delta == 1:
                            self.recovery_hits += 1
                        else:
                            self.recovery_hits = 1
                        self.recovery_anchor = counter
                        if self.recovery_hits >= self.recovery_frames:
                            decision, reason, publish = "accept", "recovered", True
                            self.timeout_flag = False
                            self._transition(
                                frame.seq, frame.t_ms, "normal", "recovery_frames"
                            )
                            self.recovery_anchor = None
                            self.recovery_hits = 0
                        else:
                            decision, reason = "resync_observation", "awaiting_consecutive"
                    elif last is None:
                        publish = True
                    else:
                        kind = classify_counter(last, counter, self.window)[1]
                        if kind == "in_window":
                            publish = True
                        else:
                            decision, reason = "reject", kind

        stale_data = (
            data_age_ms is not None and data_age_ms > self.timeout_ms and not publish
        )
        if stale_data:
            self.counts["stale_data_events"] += 1

        if publish:
            self.counts["accepted"] += 1
            self.last_counter = counter
            self.last_accepted_t = frame.t_ms
            self.last_trusted_soc_pp = soc_pp
            self.published_soc_pp = self.last_trusted_soc_pp
            self.counts["published_updates"] += 1
            if self.state == "init":
                self._transition(frame.seq, frame.t_ms, "normal", "first_valid_frame")
        elif decision == "resync_observation":
            self.counts["resync_observations"] += 1
        else:
            self._reject(reason)

        self.last_arrival_t = frame.t_ms
        self.silence_counted = 0
        if self.missing_streak >= self.degrade_after_missing and self.state != "degraded":
            self._transition(frame.seq, frame.t_ms, "degraded", "missing_slots")
            # 重同步锚只能取可信计数：坏 CRC 的帧连自己的计数器都不该被相信。
            self.recovery_anchor = counter if crc_ok is True else self.last_counter
            self.recovery_hits = 0
            self.timeout_flag = True

        return {
            "seq": frame.seq,
            "t_ms": frame.t_ms,
            "counter": counter,
            "session": session,
            "crc_ok": crc_ok,
            "delta": delta,
            "resync_delta": resync_delta,
            "decision": decision,
            "reason": reason,
            "state_after": self.state,
            "checks_evaluated": checks,
            "soc_pp": soc_pp,
            "published_soc_pp": self.published_soc_pp,
            "data_age_ms": data_age_ms,
            "stale_data": stale_data,
            "missing_slots": missing,
            "timeout_flag": self.timeout_flag,
        }


def run_scenario(frames: list[Frame], horizon_ms: float | None = None) -> dict[str, object]:
    """把一串到达喂给同一台接收机，并在视界终点按时钟推进（不依赖帧到达）。

    horizon_ms 缺省 = 末帧时刻（回放合同：观测到最后一帧为止，不追加静默尾）；
    显式给出时必须在末帧之后或同时，advance_to 会生成 clock 来源的合成转移事件。
    """
    if not frames:
        raise ValueError("至少需要一帧")
    receiver = FrameReceiver()
    rows = [receiver.feed(frame) for frame in frames]
    last_t = frames[-1].t_ms
    if horizon_ms is None:
        horizon_ms = last_t
    if not math.isfinite(horizon_ms):
        raise ValueError(f"视界非有限: {horizon_ms!r}")
    if horizon_ms < last_t:
        raise ValueError(f"视界早于末帧: {horizon_ms} < {last_t}")
    clock = receiver.advance_to(horizon_ms)
    return {
        "scenario_id": REPLAY_SCENARIO_ID,
        "frames": len(rows),
        "accepted": receiver.counts["accepted"],
        "rejected": receiver.counts["rejected"],
        "resync_observations": receiver.counts["resync_observations"],
        "published_updates": receiver.counts["published_updates"],
        "held_frames": len(rows) - receiver.counts["published_updates"],
        "missing_slots": receiver.counts["missing_slots"],
        "timeout_events": receiver.counts["timeout_events"],
        "stale_data_events": receiver.counts["stale_data_events"],
        "rejected_by_reason": dict(sorted(receiver.reasons.items())),
        "final_state": receiver.state,
        "final_counter": receiver.last_counter,
        "last_trusted_soc_pp": receiver.last_trusted_soc_pp,
        "horizon_ms": horizon_ms,
        "clock_missing_slots": receiver.counts["clock_missing_slots"],
        "silent_degraded_at_ms": clock["degraded_at_ms"],
        "clock_events": [
            item for item in receiver.transitions if item["source"] == "clock"
        ],
        "transitions": list(receiver.transitions),
        "rows": rows,
    }


def summarize(scenario: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in scenario.items() if key != "rows"}


# --- 反例（SPEC 反例列四项 + 两个补充判定）---

def stale_replay_case() -> dict[str, object]:
    """反例 1：CRC 全对的旧帧——计数器落后窗口，必须拒绝。"""
    fresh = [arrival(index * FRAME_PERIOD_MS, index, seq=index + 1) for index in range(10)]
    replays = [
        arrival(200.0, 7, seq=11),
        arrival(220.0, 7, seq=12),
        arrival(240.0, 7, seq=13),
    ]
    result = summarize(run_scenario(fresh + replays))
    delta, kind = classify_counter(9, 7)
    return {
        "counterexample": "legal_crc_stale_replay",
        "last_accepted_counter": 9,
        "replay_counter": 7,
        "delta": delta,
        "kind": kind,
        "replay_frames": 3,
        "rejected_by_reason": result["rejected_by_reason"],
        "accepted_before_replay": 10,
        "accepted_after_replay": result["accepted"],
        "identical_bytes_to_seq_8": fresh[7].payload == replays[0].payload,
        "crc_all_valid": all(
            frame.crc_rx is None
            or frame.crc_rx == frame_crc(frame.msg_id, frame.dlc, frame.payload)
            for frame in replays
        ),
        "last_trusted_unchanged": result["published_updates"] == 10,
        "verdict": "CRC 全对、字节与旧帧完全相同，仍然拒收：完整性不提供新鲜度",
    }


def wrap_boundary_cases() -> dict[str, object]:
    """反例 2：4 bit 回绕——15→0 与 15→1 接受，15→2 拒绝（窗口 +2）。"""
    cases: list[dict[str, object]] = []
    for target in (0, 1, 2):
        frames = [
            arrival(index * FRAME_PERIOD_MS, value, seq=index + 1)
            for index, value in enumerate([12, 13, 14, 15, target])
        ]
        result = run_scenario(frames)
        rows = result["rows"]
        assert isinstance(rows, list)
        last = rows[-1]
        assert isinstance(last, dict)
        delta, kind = classify_counter(15, target)
        cases.append(
            {
                "case": f"wrap_15_to_{target}",
                "sequence": [12, 13, 14, 15, target],
                "final_delta": delta,
                "kind": kind,
                "accepted": result["accepted"],
                "rejected": result["rejected"],
                "last_decision": last["decision"],
                "last_reason": last["reason"],
            }
        )
    return {
        "counterexample": "counter_wrap_boundary",
        "window": COUNTER_WINDOW,
        "cases": cases,
        "verdict": "模差不看数字大小：15→0 是 +1、15→2 是 +3；回绕不是倒退",
    }


def out_of_order_case() -> dict[str, object]:
    """反例 3：到达序 5,7,6——窗口以最后已接受帧为基准，不按到达顺序。"""
    frames = [
        arrival(index * FRAME_PERIOD_MS, value, seq=index + 1)
        for index, value in enumerate([5, 7, 6])
    ]
    result = run_scenario(frames)
    delta_6_vs_5, _ = classify_counter(5, 6)
    delta_6_vs_7, kind = classify_counter(7, 6)
    rows = result["rows"]
    assert isinstance(rows, list)
    return {
        "counterexample": "out_of_order",
        "sequence": [5, 7, 6],
        "decisions": [row["decision"] for row in rows],
        "reasons": [row["reason"] for row in rows],
        "delta_6_vs_5": delta_6_vs_5,
        "delta_6_vs_7": delta_6_vs_7,
        "kind_6_vs_7": kind,
        "accepted": result["accepted"],
        "rejected": result["rejected"],
        "final_counter": result["final_counter"],
        "verdict": "6 相对 5 仍在 +1 窗内，但 7 已先被接受；窗口基准换人后 6 变成迟到",
    }


def bus_recovery_case() -> dict[str, object]:
    """反例 4：连续丢 5 帧 → degraded；连续 3 拍观察计数连续 → 退出。"""
    frames = [
        arrival(0.0, 0, seq=1),
        arrival(20.0, 1, seq=2),
        arrival(40.0, 2, seq=3),
        arrival(160.0, 8, seq=4),   # 间隔 120 ms：丢 5 拍、超时 1 次
        arrival(180.0, 9, seq=5),
        arrival(200.0, 10, seq=6),
        arrival(220.0, 11, seq=7),
    ]
    result = run_scenario(frames)
    rows = result["rows"]
    assert isinstance(rows, list)
    transitions = result["transitions"]
    assert isinstance(transitions, list)
    entry = next(
        item for item in transitions if isinstance(item, dict) and item["to"] == "degraded"
    )
    exited = next(
        item for item in transitions if isinstance(item, dict) and item["from"] == "degraded"
    )
    entered_seq = _as_int(entry["seq"])
    exited_seq = _as_int(exited["seq"])
    return {
        "counterexample": "bus_recovery",
        "missing_slots": result["missing_slots"],
        "timeout_events": result["timeout_events"],
        "degrade_threshold": DEGRADE_AFTER_MISSING,
        "recovery_frames": RECOVERY_FRAMES,
        "entered_at_seq": entered_seq,
        "entered_at_t_ms": entry["t_ms"],
        "exited_at_seq": exited_seq,
        "exited_at_t_ms": exited["t_ms"],
        "degraded_arrivals": exited_seq - entered_seq + 1,
        "decisions": [row["decision"] for row in rows],
        "reasons": [row["reason"] for row in rows],
        "accepted": result["accepted"],
        "rejected": result["rejected"],
        "resync_observations": result["resync_observations"],
        "final_counter": result["final_counter"],
        "verdict": "丢帧由到达间隔计数、计数器缺口只判窗口；恢复要看 3 拍连续计数，不看 1 帧",
    }


def silent_bus_case(horizon_periods: int = SILENT_TAIL_PERIODS) -> dict[str, object]:
    """时钟驱动反例：最后一帧之后再无输入，deadline 命中即降级，视界终点仍 degraded。"""
    frames = default_arrivals()
    last_t = frames[-1].t_ms
    horizon = last_t + horizon_periods * FRAME_PERIOD_MS
    result = summarize(run_scenario(frames, horizon_ms=horizon))
    degraded_at = result["silent_degraded_at_ms"]
    if degraded_at is None:
        raise ValueError("静默视界内未触发降级")
    transitions = result["transitions"]
    assert isinstance(transitions, list)
    clock_events = [item for item in transitions if item["source"] == "clock"]
    return {
        "case": "silent_bus_after_last_frame",
        "last_frame_ms": last_t,
        "horizon_ms": horizon,
        "silence_periods": horizon_periods,
        "degrade_after_missing": DEGRADE_AFTER_MISSING,
        "deadline_ms": last_t + DEGRADE_AFTER_MISSING * FRAME_PERIOD_MS,
        "degrades_at_ms": degraded_at,
        "clock_missing_slots": result["clock_missing_slots"],
        "accepted": result["accepted"],
        "rejected": result["rejected"],
        "published_updates": result["published_updates"],
        "last_trusted_soc_pp": result["last_trusted_soc_pp"],
        "state_at_horizon": result["final_state"],
        "frames_after_last": 0,
        "transitions": clock_events,
        "verdict": (
            "最后一帧后无任何输入：接收端按时钟在 deadline 降级，视界终点仍 degraded，"
            "恢复只能靠真实帧；超时是时钟属性，不是帧属性"
        ),
    }


def duplicate_case() -> dict[str, object]:
    """补充：同一计数器重复到达（delta 0）必须拒绝，不能刷新可信值。"""
    frames = [arrival(index * FRAME_PERIOD_MS, index, seq=index + 1) for index in range(4)]
    frames.append(arrival(80.0, 3, seq=5))
    result = run_scenario(frames)
    delta, kind = classify_counter(3, 3)
    return {
        "counterexample": "duplicate_counter",
        "delta": delta,
        "kind": kind,
        "accepted": result["accepted"],
        "rejected_by_reason": result["rejected_by_reason"],
        "published_updates": result["published_updates"],
        "verdict": "重复帧不推进计数器、不刷新数据年龄",
    }


def cross_session_case() -> dict[str, object]:
    """补充：计数器在窗内但会话不同（疑似上一次上电的帧）——会话门先拦。"""
    frames = [arrival(index * FRAME_PERIOD_MS, index, seq=index + 1) for index in range(4)]
    frames.append(arrival(80.0, 4, session=2, seq=5))
    frames.append(arrival(100.0, 4, session=1, seq=6))
    result = run_scenario(frames)
    rows = result["rows"]
    assert isinstance(rows, list)
    return {
        "counterexample": "cross_session",
        "delta_would_be": classify_counter(3, 4)[0],
        "window_would_accept": classify_counter(3, 4)[1] == "in_window",
        "decisions": [row["decision"] for row in rows],
        "reasons": [row["reason"] for row in rows],
        "accepted": result["accepted"],
        "rejected_by_reason": result["rejected_by_reason"],
        "verdict": "计数器窗内也不够：跨上电生命周期的旧帧必须由会话字段拦下",
    }


def crc_short_circuit_case() -> dict[str, object]:
    """短路顺序：CRC 不过就不解释计数器；旧帧 + 坏 CRC 只记 crc 一次。"""
    frames = [arrival(index * FRAME_PERIOD_MS, index, seq=index + 1) for index in range(10)]
    stale = arrival(200.0, 7, seq=11)
    corrupt = Frame(
        seq=12,
        t_ms=220.0,
        msg_id=MSG_ID,
        dlc=DLC,
        payload=stale.payload,
        crc_rx=frame_crc(stale.msg_id, stale.dlc, stale.payload) ^ 0x0001,
    )
    result = run_scenario(frames + [corrupt])
    rows = result["rows"]
    assert isinstance(rows, list)
    row = rows[-1]
    assert isinstance(row, dict)
    checks = row["checks_evaluated"]
    assert isinstance(checks, list)
    return {
        "counterexample": "crc_short_circuit",
        "reject_reason": row["reason"],
        "counter_evaluated": "counter" in checks,
        "checks_evaluated": checks,
        "rejected_by_reason": result["rejected_by_reason"],
        "verdict": "短路顺序 identity→crc→session→counter：坏 CRC 的旧帧只记 crc，不重复记账",
    }


# --- 默认场景：正常段 + 旧帧 + 坏 CRC + 跨会话 + 回绕 + 缺口 + 总线恢复 ---

def default_arrivals() -> list[Frame]:
    """确定性到达脚本（29 帧）：不读时钟、不用随机源。"""
    frames: list[Frame] = []

    def add(t_ms: float, counter: int, *, session: int = 1, crc_rx: int | None = None) -> None:
        payload = synthetic_payload(counter, session)
        frames.append(
            Frame(
                seq=len(frames) + 1,
                t_ms=float(t_ms),
                msg_id=MSG_ID,
                dlc=DLC,
                payload=payload,
                crc_rx=crc_rx,
            )
        )

    for index in range(10):                      # seq 1–10：正常段，计数器 0..9
        add(index * FRAME_PERIOD_MS, index)
    for t_ms in (200.0, 220.0, 240.0):           # seq 11–13：旧帧重放（计数器 7）
        add(t_ms, 7)
    bad_crc = frame_crc(MSG_ID, DLC, synthetic_payload(10, 1)) ^ 0x0001
    add(260.0, 10, crc_rx=bad_crc)               # seq 14：CRC 坏，其余判据都对
    add(280.0, 10)                               # seq 15：同一计数器的好帧
    add(300.0, 11, session=2)                    # seq 16：跨会话
    add(320.0, 11)                               # seq 17：本会话
    for offset, counter in enumerate((12, 13, 14, 15, 0, 1, 2)):  # seq 18–24：回绕跨越
        add(340.0 + offset * FRAME_PERIOD_MS, counter)
    add(480.0, 5)                                # seq 25：跳号 +3（缺口）
    add(600.0, 8)                                # seq 26：静默 120 ms → degraded
    add(620.0, 9)                                # seq 27：重同步观察 1
    add(640.0, 10)                               # seq 28：重同步观察 2
    add(660.0, 11)                               # seq 29：第 3 拍 → 退出并接受
    return frames


def golden_frame() -> dict[str, object]:
    """首帧（计数器 0、会话 1）的线上字节与解码结果：编码表的可复算样例。"""
    frame = default_arrivals()[0]
    crc = frame_crc(frame.msg_id, frame.dlc, frame.payload)
    return {
        "msg_id": frame.msg_id,
        "msg_id_hex": f"0x{frame.msg_id:03X}",
        "dlc": frame.dlc,
        "payload_hex": frame.payload.hex(),
        "covered_hex": crc_covered_bytes(frame.msg_id, frame.dlc, frame.payload).hex(),
        "crc_hex": f"{crc:04X}",
        "wire_hex": wire_bytes(frame).hex(),
        "decoded": decode_signals(frame.payload),
    }


# --- 回放合同：CSV 读写与拒绝路径 ---

def write_frames_csv(frames: list[Frame], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=REQUIRED_FRAME_COLUMNS + OPTIONAL_FRAME_COLUMNS
        )
        writer.writeheader()
        for frame in frames:
            crc = frame_crc(frame.msg_id, frame.dlc, frame.payload)
            writer.writerow(
                {
                    "seq": frame.seq,
                    "t_ms": round(frame.t_ms, 6),
                    "data": frame.payload.hex(),
                    "crc_hex": f"{frame.crc_rx if frame.crc_rx is not None else crc:04X}",
                }
            )


def write_decisions_csv(rows: list[dict[str, object]], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DECISION_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            record = dict(row)
            checks = record.get("checks_evaluated")
            record["checks_evaluated"] = (
                "|".join(str(item) for item in checks) if isinstance(checks, list) else ""
            )
            writer.writerow({key: record[key] for key in DECISION_COLUMNS})


def _parse_int(raw: str, lineno: int, name: str) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"第 {lineno} 行 {name} 无法解析: {raw!r}") from exc
    return value


def _parse_crc(raw: str, lineno: int) -> int:
    text = raw.strip()
    if len(text) != 4:
        raise ValueError(f"第 {lineno} 行 crc_hex 必须 4 位十六进制，得到 {raw!r}")
    try:
        value = int(text, 16)
    except ValueError as exc:
        raise ValueError(f"第 {lineno} 行 crc_hex 无法解析: {raw!r}") from exc
    if not 0 <= value <= 0xFFFF:
        raise ValueError(f"第 {lineno} 行 crc_hex 越界: {raw!r}")
    return value


def load_frames(path: Path) -> list[Frame]:
    """读取帧序列 CSV：至少 seq,data；可选 t_ms,crc_hex。

    拒绝：缺文件 / 错表头 / 未知列 / 缺列 / 非有限 / 时间回退 / 越界 / 样本不足。
    """
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            raise ValueError("表头缺失")
        missing = [name for name in REQUIRED_FRAME_COLUMNS if name not in fieldnames]
        if missing:
            raise ValueError(
                f"缺列 {missing}：表头必须至少包含 {','.join(REQUIRED_FRAME_COLUMNS)}，"
                f"实际 {fieldnames}"
            )
        unknown = [
            name for name in fieldnames
            if name not in REQUIRED_FRAME_COLUMNS + OPTIONAL_FRAME_COLUMNS
        ]
        if unknown:
            raise ValueError(f"未知列 {unknown}（只允许 {OPTIONAL_FRAME_COLUMNS} 作为可选列）")
        frames: list[Frame] = []
        last_seq: int | None = None
        last_t: float | None = None
        for lineno, row in enumerate(reader, start=2):
            if None in row or any(row.get(name) is None for name in fieldnames):
                raise ValueError(f"第 {lineno} 行列数与表头不一致")
            seq = _parse_int(row["seq"], lineno, "seq")
            if seq < 0:
                raise ValueError(f"第 {lineno} 行 seq 越界: {seq}")
            if last_seq is not None and seq <= last_seq:
                raise ValueError(f"第 {lineno} 行 seq 未严格递增: {seq} <= {last_seq}")
            data = row["data"].strip()
            if len(data) != PAYLOAD_BYTES * 2:
                raise ValueError(
                    f"第 {lineno} 行 data 长度越界：要求 {PAYLOAD_BYTES * 2} 个十六进制字符，"
                    f"得到 {len(data)}"
                )
            try:
                payload = bytes.fromhex(data)
            except ValueError as exc:
                raise ValueError(f"第 {lineno} 行 data 非十六进制: {data!r}") from exc
            t_ms = last_t + FRAME_PERIOD_MS if last_t is not None else seq * FRAME_PERIOD_MS
            if "t_ms" in fieldnames:
                raw_t = row["t_ms"]
                if raw_t is None or raw_t.strip() == "":
                    raise ValueError(f"第 {lineno} 行 t_ms 为空")
                try:
                    t_ms = float(raw_t)
                except ValueError as exc:
                    raise ValueError(f"第 {lineno} 行 t_ms 无法解析: {raw_t!r}") from exc
                if not math.isfinite(t_ms):
                    raise ValueError(f"第 {lineno} 行 t_ms 非有限: {raw_t!r}")
                if t_ms < 0.0:
                    raise ValueError(f"第 {lineno} 行 t_ms 越界: {t_ms}")
                if last_t is not None and t_ms <= last_t:
                    raise ValueError(f"第 {lineno} 行 t_ms 回退: {t_ms} <= {last_t}")
            crc_rx: int | None = None
            if "crc_hex" in fieldnames:
                raw_crc = row["crc_hex"]
                if raw_crc is None or raw_crc.strip() == "":
                    raise ValueError(f"第 {lineno} 行 crc_hex 为空")
                crc_rx = _parse_crc(raw_crc, lineno)
            last_seq = seq
            last_t = t_ms
            frames.append(
                Frame(
                    seq=seq,
                    t_ms=t_ms,
                    msg_id=MSG_ID,
                    dlc=PAYLOAD_BYTES,
                    payload=payload,
                    crc_rx=crc_rx,
                )
            )
    if len(frames) < MIN_FRAMES:
        raise ValueError(f"样本不足：{len(frames)} 帧 < 下限 {MIN_FRAMES}")
    return frames


# --- 报告 ---

def build_report(scenario: dict[str, object] | None = None) -> dict[str, object]:
    """把帧格式、窗口、反例与默认回放合成一份报告（与文档 D19.6 逐位一致）。"""
    if scenario is None:
        scenario = run_scenario(default_arrivals())
    summary = summarize(scenario)
    return {
        "scenario_id": SCENARIO_ID,
        "identity": (
            "teaching CAN-style frame on a synthetic arrival script; bit timing, stuffing "
            "bound, transceiver levels, timeout budget and signal scales are teaching values — "
            "not device measurements, not bus conformance tests, not HIL evidence"
        ),
        "frame": {
            "msg_id": MSG_ID,
            "msg_id_hex": f"0x{MSG_ID:03X}",
            "dlc": DLC,
            "payload_bytes": PAYLOAD_BYTES,
            "crc": "CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF, no reflect, no xorout)",
            "crc_check_input": "123456789",
            "crc_check_value_123456789": f"0x{CRC16_CHECK_VALUE:04X}",
            "crc_covered": "msg_id(2B BE) | dlc | payload[8]",
            "counter": "payload byte0 bits 3..0, 4 bit rolling",
            "session": "payload byte0 bits 7..4, 4 bit session",
            "encoding": SIGNAL_ENCODING,
            "bit_levels": BIT_LEVELS,
            "golden": golden_frame(),
        },
        "timing": timing_report(),
        "window": {
            "counter_bits": COUNTER_BITS,
            "counter_modulus": COUNTER_MODULUS,
            "forward_window": COUNTER_WINDOW,
            "backward_window": 0,
            "session_bits": SESSION_BITS,
            "degrade_after_missing": DEGRADE_AFTER_MISSING,
            "recovery_frames": RECOVERY_FRAMES,
            "frame_period_ms": FRAME_PERIOD_MS,
            "frame_timeout_ms": FRAME_TIMEOUT_MS,
            "delta_rules": {
                "0": "duplicate → reject",
                "1-2": "accept",
                "3-7": "gap_too_large → reject",
                "8": "ambiguous → reject",
                "9-15": "late → reject",
            },
        },
        "judgement_chain": {
            "order": ["identity", "crc", "session", "counter"],
            "short_circuit": True,
            "reason": "字段不可信就不解释字段：CRC 不过时计数器不参与判定，只记一次 crc",
            "stages": LIFECYCLE_STAGES,
        },
        "counterexamples": {
            "stale_replay": stale_replay_case(),
            "wrap": wrap_boundary_cases(),
            "out_of_order": out_of_order_case(),
            "bus_recovery": bus_recovery_case(),
            "duplicate": duplicate_case(),
            "cross_session": cross_session_case(),
            "crc_short_circuit": crc_short_circuit_case(),
        },
        "silent_bus": silent_bus_case(),
        "replay": {
            **summary,
            "identity": (
                "synthetic arrival script replayed through the same receiver; "
                "decision rows are deterministic and byte-for-byte reproducible"
            ),
        },
        "crc_scope": (
            "CRC 只证明完整性：同一帧逐字节重放时 CRC 仍然全对；"
            "新鲜度必须由计数器窗口、会话与到达时间另行判定"
        ),
        "boundary": (
            "教学参数（位时间、填充上界、差分电平、超时预算、编码因子）不认定为器件实测、"
            "总线一致性测试或 HIL 证据；真实总线时序与协议口径闭合于 SRC05，本模块的帧格式"
            "不是任何厂商协议的解析器"
        ),
        "firmware_boundary": (
            "固件 BmsInputs 只有 cell_mv[]/current_ma/temp_c10/charger_present，无时间戳、"
            "无质量位、无计数器/会话字段：固件中没有地方存放帧年龄与帧序号，本模块的窗口"
            "判定、超时账与降级保持是教学补全，不证明固件已实现新鲜度门"
        ),
        "protocol_boundary": (
            "code/protocol 是协议维护源（CRC 基准向量、帧解析器与测试的家），本模块不 import "
            "它；帧布局只按教材口径自洽，换厂商协议必须重取 CRC 参数、字节序与缩放"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 等工件的目录")
    parser.add_argument(
        "--frames",
        type=Path,
        help=f"帧序列 CSV（至少 {','.join(REQUIRED_FRAME_COLUMNS)} 两列）；缺省用内置合成到达脚本",
    )
    parser.add_argument(
        "--horizon-ms",
        type=float,
        help="仿真视界（ms，必须不早于末帧）；缺省=末帧时刻，不追加静默尾",
    )
    args = parser.parse_args(argv)

    if args.frames is not None:
        try:
            frames = load_frames(args.frames)
        except (OSError, ValueError) as exc:
            print(f"帧序列拒绝：{exc}", file=sys.stderr)
            return 2
    else:
        frames = default_arrivals()
    try:
        scenario = run_scenario(frames, horizon_ms=args.horizon_ms)
        report = build_report(scenario)
    except (OSError, ValueError) as exc:
        print(f"帧序列拒绝：{exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        write_frames_csv(frames, args.out / "frames.csv")
        rows = scenario["rows"]
        if not isinstance(rows, list):
            raise TypeError("回放结果缺少逐帧 rows")
        write_decisions_csv(rows, args.out / "decisions.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
