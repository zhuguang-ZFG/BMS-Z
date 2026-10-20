"""教学用帧闸门：从字节流里切帧、校验 CRC，并统计坏帧。

帧格式与 code/protocol 同形，但这是独立的教学夹具：
不导入、不修改 code/protocol，也不代表任何真实产品的协议。
"""
from __future__ import annotations

HEADER = b"\xAA\x55"
MAX_PAYLOAD = 64


def crc8_atm(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def build_frame(addr: int, cmd: int, data: bytes) -> bytes:
    body = bytes([addr, cmd, len(data)]) + data
    return HEADER + body + bytes([crc8_atm(body)])


class FrameGate:
    def __init__(self) -> None:
        self.frames: list[tuple[int, int, str]] = []
        self.bad_crc = 0
        self.bad_len = 0

    def feed(self, data: bytes) -> list[tuple[int, int, str]]:
        buf = bytearray(data)
        out: list[tuple[int, int, str]] = []
        while True:
            start = buf.find(HEADER)
            if start < 0:
                break
            del buf[:start]
            if len(buf) < 5:
                break
            size = buf[4]
            if size >= MAX_PAYLOAD:
                self.bad_len += 1
                del buf[0]
                continue
            total = 6 + size
            if len(buf) < total:
                break
            if crc8_atm(bytes(buf[2:total - 1])) != buf[total - 1]:
                del buf[:total]
                continue
            try:
                payload = bytes(buf[5:total - 1]).decode("ascii")
            except UnicodeDecodeError:
                del buf[:total]
                continue
            out.append((buf[2], buf[3], payload))
            del buf[:total]
        self.frames.extend(out)
        return out

    def summary(self) -> str:
        import pandas as pd

        rows = pd.DataFrame(self.frames, columns=["addr", "cmd", "payload"])
        return rows.to_string(index=False)
