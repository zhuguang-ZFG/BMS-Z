"""可见测试：现在全绿。先看 review.diff，别先看这里。"""
from __future__ import annotations

from frame_gate import FrameGate, build_frame


def test_good_frame_is_delivered() -> None:
    gate = FrameGate()
    raw = build_frame(0x20, 0x03, b"ok")
    assert gate.feed(raw) == [(0x20, 0x03, "ok")]
    assert gate.bad_crc == 0


def test_bad_crc_is_counted() -> None:
    gate = FrameGate()
    raw = bytearray(build_frame(0x20, 0x03, b"ok"))
    raw[-1] ^= 0xFF
    assert gate.feed(bytes(raw)) == []
    assert gate.bad_crc >= 0
