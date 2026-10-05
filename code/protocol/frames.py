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
        """组帧：元信息 + 数据 + CRC。

        载荷超过 MAX_LEN 必须显式拒绝：len 是单字节且解析器拒收 > MAX_LEN
        的帧，放行等于组出"自己的解析器认不出"的帧（往返不一致）；再大还会
        抛出 `bytes must be in range(0, 256)` 这种与协议无关的费解报错。
        """
        if len(self.data) > MAX_LEN:
            raise ValueError(
                f"数据域 {len(self.data)} 字节超过协议上限 MAX_LEN={MAX_LEN}"
            )
        body = bytes([self.addr, self.cmd, len(self.data)]) + self.data
        return HEADER + body + bytes([crc8_atm(body)])

    # ---- 字段级解码示例：约定电压 = raw16(大端) × 1mV ----
    def cell_voltage_mv(self, cell_index: int) -> int:
        """命令 0x03 响应的数据域布局：[cell0_H, cell0_L, cell1_H, cell1_L, ...]"""
        if self.cmd != 0x03:
            raise ValueError(f"cmd=0x{self.cmd:02X} 不是电压查询响应")
        off = cell_index * 2
        # 负数下标必须显式拒绝：Python 的负索引会从尾部回绕，cell_index=-1
        # 不拦就会"读到"最后一串的值——静默读错比抛异常危险得多
        if off < 0 or off + 1 >= len(self.data):
            raise IndexError(f"cell_index={cell_index} 超出数据域（{len(self.data)} 字节）")
        return (self.data[off] << 8) | self.data[off + 1]


class FrameParser:
    """逐字节接收，以有界缓冲保存候选帧，CRC 失败时从下一字节重新找帧头。

    feed() 每次至多返回一帧。上层确认帧间超时或流结束时调用 flush()，
    取回滞留好帧并丢弃残片；普通串口 read() 分块不是超时，不要逐块 flush。
    长度仍合法的残帧与未收齐的好帧无法仅凭字节区分，必须等此边界或 CRC。
    """

    def __init__(self):
        self._buf = bytearray()
        # 统计：调试与现场复盘的"第一现场"（教程：坏帧要计数，别静默吞掉）
        self.frames_ok = 0
        self.frames_bad_crc = 0
        self.frames_bad_len = 0
        self.frames_incomplete = 0       # 只在明确超时／结束后计数
        self.resyncs = 0

    def feed(self, byte: int) -> Frame | None:
        """喂一个字节；返回最早的完整好帧，否则 None。待收缓冲小于最大帧长。"""
        self._buf.append(byte)
        return self._extract_frame()

    def _extract_frame(self, *, final: bool = False) -> Frame | None:
        while self._buf:
            # 找帧头。尚未收齐时只保留末尾 AA，避免吞掉跨分块的 AA 55。
            start = self._buf.find(HEADER)
            if start < 0:
                keep = 1 if not final and self._buf[-1] == HEADER[0] else 0
                drop = len(self._buf) - keep
                if drop:
                    self.resyncs += 1
                    del self._buf[:drop]
                return None
            if start:
                self.resyncs += 1
                del self._buf[:start]

            # 收元信息，再按 len 等待数据和 CRC。合法帧内的 AA 55 不抢占当前帧。
            if len(self._buf) < 5:
                if final:
                    self.frames_incomplete += 1
                    self._buf.clear()
                return None
            size = self._buf[4]
            if size > MAX_LEN:
                self.frames_bad_len += 1
                del self._buf[0]         # 只排除已知坏帧头，余下字节全部重新参与同步
                continue
            total = 6 + size
            if len(self._buf) < total:
                if final:
                    self.frames_incomplete += 1
                    del self._buf[0]
                    continue            # 超时确认残帧后，找回缓冲中被它遮住的好帧
                return None

            if crc8_atm(self._buf[2:total - 1]) != self._buf[total - 1]:
                self.frames_bad_crc += 1
                del self._buf[0]
                continue
            frame = Frame(self._buf[2], self._buf[3], bytes(self._buf[5:total - 1]))
            del self._buf[:total]
            self.frames_ok += 1
            return frame
        return None

    def flush(self) -> list[Frame]:
        """仅在明确超时／流结束时调用：取出剩余好帧、丢弃残片，统计不清零。"""
        frames = []
        while (frame := self._extract_frame(final=True)) is not None:
            frames.append(frame)
        return frames


def parse_stream(stream: bytes) -> tuple[list[Frame], FrameParser]:
    """解析一段已结束的字节流（含末尾 flush），返回帧列表和统计。"""
    parser = FrameParser()
    frames = [f for b in stream if (f := parser.feed(b)) is not None]
    frames.extend(parser.flush())
    return frames, parser
