#!/usr/bin/env python3
"""Byte-wise BMS frame parser with CRC-8/ATM and resync (teaching demo).

Frame: AA 55 | addr | cmd | len | data[len] | crc8
CRC covers addr..data. Run: python code/frame_parser.py
"""

from __future__ import annotations

from dataclasses import dataclass

HEADER = b"\xAA\x55"
MAX_LEN = 64


def crc8_atm(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


@dataclass
class Frame:
    addr: int
    cmd: int
    data: bytes

    def to_bytes(self) -> bytes:
        if len(self.data) > MAX_LEN:
            raise ValueError("payload too long")
        body = bytes([self.addr, self.cmd, len(self.data)]) + self.data
        return HEADER + body + bytes([crc8_atm(body)])


class FrameParser:
    def __init__(self) -> None:
        self.buf = bytearray()
        self.frames_ok = 0
        self.bad_crc = 0
        self.bad_len = 0
        self.incomplete = 0
        self.resyncs = 0

    def feed(self, byte: int) -> Frame | None:
        self.buf.append(byte)
        return self._extract(final=False)

    def _extract(self, final: bool) -> Frame | None:
        while self.buf:
            start = self.buf.find(HEADER)
            if start < 0:
                keep = 1 if not final and self.buf[-1] == HEADER[0] else 0
                drop = len(self.buf) - keep
                if drop:
                    self.resyncs += 1
                    del self.buf[:drop]
                if final and self.buf:
                    self.incomplete += 1
                    self.buf.clear()
                return None
            if start:
                self.resyncs += 1
                del self.buf[:start]
            if len(self.buf) < 5:
                if final:
                    self.incomplete += 1
                    self.buf.clear()
                return None
            size = self.buf[4]
            if size > MAX_LEN:
                self.bad_len += 1
                del self.buf[0]
                continue
            total = 6 + size
            if len(self.buf) < total:
                if final:
                    self.incomplete += 1
                    del self.buf[0]
                    continue
                return None
            if crc8_atm(bytes(self.buf[2:total - 1])) != self.buf[total - 1]:
                self.bad_crc += 1
                del self.buf[0]
                continue
            frame = Frame(self.buf[2], self.buf[3], bytes(self.buf[5:total - 1]))
            del self.buf[:total]
            self.frames_ok += 1
            return frame
        return None

    def flush(self) -> list[Frame]:
        out = []
        while (frame := self._extract(final=True)) is not None:
            out.append(frame)
        return out


def main() -> None:
    good1 = Frame(0x01, 0x03, b"\x0E\xA0\x0E\xB4").to_bytes()
    garbage = b"\x00\x11\x22"
    bad = bytearray(Frame(0x01, 0x04, b"\x2A").to_bytes())
    bad[-1] ^= 0x01
    good2 = Frame(0x02, 0x05, b"\x01\x02").to_bytes()
    tail = b"\xAA\x55\x03\x03\x10"  # header + partial body, never completed
    stream = good1 + garbage + bytes(bad) + good2 + tail

    parser = FrameParser()
    frames = [f for b in stream if (f := parser.feed(b)) is not None]
    frames.extend(parser.flush())

    print("frames:", [(hex(f.addr), hex(f.cmd), f.data.hex()) for f in frames])
    print("ok/bad_crc/bad_len/incomplete/resyncs:",
          parser.frames_ok, parser.bad_crc, parser.bad_len, parser.incomplete, parser.resyncs)

    assert len(frames) == 2
    assert frames[0].data == b"\x0E\xA0\x0E\xB4"
    assert parser.bad_crc == 1
    assert parser.incomplete == 1
    assert parser.resyncs >= 1

    # one-byte-at-a-time must produce the same frames
    parser2 = FrameParser()
    frames2 = [f for b in stream if (f := parser2.feed(b)) is not None]
    frames2.extend(parser2.flush())
    assert [f.data for f in frames2] == [f.data for f in frames]
    print("checks passed: bad CRC rejected, good frames recovered, partial tail counted")


if __name__ == "__main__":
    main()
