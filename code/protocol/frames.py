"""教学用 BMS 帧协议 + 逐字节状态机解析器。

对应教程：阶段 5 §5.2（UART 帧结构）与 §5.6（解析器五条军规）。

帧格式采用教程里的"典型抽象"（不是任何一家的真实协议——
真实协议请对照 syssi 仓库源码逐字节读）：

    AA 55 | addr | cmd | len | data[len] | crc8
    帧头    地址   命令  长度  数据        CRC-8/ATM（覆盖 addr..data）

解析器军规（教程 §5.6 第 5 步）：
  1. 状态机逐字节接收：找帧头 → 收元信息 → 收数据 → 验 CRC；
  2. 坏帧（CRC 错 / 长度非法）丢弃并计数——绝不因一帧坏数据死机；
  3. 垃圾前缀能重新同步（在字节流中重新找到帧头）；
  4. 支持一个字节一个字节地喂（UART 中断里就是这么来的）；
  5. 字段解出后按协议约定换算物理量（raw × factor + offset）。
"""
from __future__ import annotations

from dataclasses import dataclass

from crc import crc8_atm

HEADER = bytes([0xAA, 0x55])
MAX_LEN = 64


@dataclass
class Frame:
    addr: int
    cmd: int
    data: bytes

    def to_bytes(self) -> bytes:
        """组帧：元信息 + 数据 + CRC。"""
        body = bytes([self.addr, self.cmd, len(self.data)]) + self.data
        return HEADER + body + bytes([crc8_atm(body)])

    # ---- 字段级解码示例：约定电压 = raw16(大端) × 1mV ----
    def cell_voltage_mv(self, cell_index: int) -> int:
        """命令 0x03 响应的数据域布局：[cell0_H, cell0_L, cell1_H, cell1_L, ...]"""
        if self.cmd != 0x03:
            raise ValueError(f"cmd=0x{self.cmd:02X} 不是电压查询响应")
        off = cell_index * 2
        return (self.data[off] << 8) | self.data[off + 1]


class FrameParser:
    """逐字节状态机。用法：for b in stream: frame = parser.feed(b)。"""

    def __init__(self):
        self._state = "header0"
        self._addr = self._cmd = self._len = 0
        self._buf = bytearray()
        # 统计：调试与现场复盘的"第一现场"（教程：坏帧要计数，别静默吞掉）
        self.frames_ok = 0
        self.frames_bad_crc = 0
        self.frames_bad_len = 0
        self.resyncs = 0

    def feed(self, byte: int) -> Frame | None:
        """喂一个字节；凑齐且 CRC 正确时返回 Frame，否则 None。"""
        if self._state == "header0":
            if byte == HEADER[0]:
                self._state = "header1"
            return None

        if self._state == "header1":
            if byte == HEADER[1]:
                self._state = "addr"
            else:
                # 不是期望的第二帧头：可能 AA 本身就是数据里的字节，退回重找
                self.resyncs += 1
                self._state = "header0" if byte != HEADER[0] else "header1"
            return None

        if self._state == "addr":
            self._addr = byte
            self._state = "cmd"
            return None

        if self._state == "cmd":
            self._cmd = byte
            self._state = "len"
            return None

        if self._state == "len":
            if byte > MAX_LEN:
                # 长度非法：这帧必然已坏，丢帧回起点重新同步
                self.frames_bad_len += 1
                self._state = "header0"
                return None
            self._len = byte
            self._buf = bytearray()
            self._state = "data"
            return None

        if self._state == "data":
            self._buf.append(byte)
            if len(self._buf) < self._len:
                return None
            self._state = "crc"
            return None

        if self._state == "crc":
            body = bytes([self._addr, self._cmd, self._len]) + bytes(self._buf)
            self._state = "header0"
            if crc8_atm(body) == byte:
                self.frames_ok += 1
                return Frame(self._addr, self._cmd, bytes(self._buf))
            self.frames_bad_crc += 1
            return None

        raise AssertionError(f"非法状态 {self._state}")


def parse_stream(stream: bytes) -> tuple[list[Frame], FrameParser]:
    """整包喂入的便捷入口，返回 (解析出的帧列表, 含统计的解析器)。"""
    parser = FrameParser()
    frames = [f for b in stream if (f := parser.feed(b)) is not None]
    return frames, parser
