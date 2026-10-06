"""第 1 期可选第二题：从坏字节流里救回事先埋好的好帧。

基线是一个「CRC 错了就按声明长度整段跳过」的弱解析器。
仓库里的 FrameParser 会在失败后逐字节重扫，能看见藏在坏帧载荷里的好帧。
两套数字都是这段固定种子字节流上的仿真结果。不改 code/protocol。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code" / "protocol"))

from crc import crc8_atm  # noqa: E402
from frames import Frame, parse_stream  # noqa: E402

SEED = 20261006
BASELINE_NAME = "坏CRC整段跳过"


def _good(index: int) -> Frame:
    data = bytes([0x03, index & 0xFF, 0x10, (index * 7) & 0xFF])
    return Frame(0x20, 0x03, data)


def _junk(rng: np.random.Generator, n: int) -> bytes:
    """垃圾字节。抽到帧头首字节 AA 就换成 0x10，避免弱解析器提前咬到假帧头。"""
    raw = rng.integers(0, 256, size=n)
    raw = np.where(raw == 0xAA, 0x10, raw)
    return bytes(int(x) for x in raw)


def build_stream(seed: int = SEED) -> tuple[bytes, list[Frame]]:
    """前 4 帧露在外面；后 6 帧藏在 CRC 错误的外层载荷里。"""
    rng = np.random.default_rng(seed)
    planted: list[Frame] = []
    out = bytearray()
    for i in range(4):
        out.extend(_junk(rng, 4))
        frame = _good(i)
        out.extend(frame.to_bytes())
        planted.append(frame)
    for i in range(4, 10):
        inner = _good(i)
        payload = _junk(rng, 3) + inner.to_bytes() + _junk(rng, 2)
        outer = Frame(0x21, 0x01, payload)
        raw = bytearray(outer.to_bytes())
        raw[-1] ^= 0xFF
        out.extend(_junk(rng, 2))
        out.extend(raw)
        planted.append(inner)
    return bytes(out), planted


def weak_skip(stream: bytes) -> list[Frame]:
    """CRC 失败就跳过声明的整帧，不在载荷里重找帧头。"""
    buf = bytearray(stream)
    found: list[Frame] = []
    while True:
        start = buf.find(b"\xAA\x55")
        if start < 0 or len(buf) - start < 5:
            break
        del buf[:start]
        size = buf[4]
        if size > 64:
            del buf[0]
            continue
        total = 6 + size
        if len(buf) < total:
            break
        if crc8_atm(bytes(buf[2:total - 1])) != buf[total - 1]:
            del buf[:total]
            continue
        found.append(Frame(buf[2], buf[3], bytes(buf[5:total - 1])))
        del buf[:total]
    return found


def _key(frame: Frame) -> tuple[int, int, bytes]:
    return frame.addr, frame.cmd, frame.data


def grade(parsed: list[Frame], planted: list[Frame]) -> dict[str, int]:
    """按多重集合对上埋好的帧。多出来的帧算误收，从得分里减掉。"""
    remaining = [_key(frame) for frame in planted]
    recovered = 0
    false_accepts = 0
    for frame in parsed:
        key = _key(frame)
        if key in remaining:
            remaining.remove(key)
            recovered += 1
        else:
            false_accepts += 1
    return {
        "planted": len(planted),
        "recovered": recovered,
        "false_accepts": false_accepts,
        "score": recovered - false_accepts,
    }


def baseline_report(seed: int = SEED) -> dict[str, dict[str, int]]:
    stream, planted = build_stream(seed)
    repo_frames, _parser = parse_stream(stream)
    return {
        BASELINE_NAME: grade(weak_skip(stream), planted),
        "仓库解析器": grade(repo_frames, planted),
    }


def main() -> None:
    stream, planted = build_stream()
    report = baseline_report()
    print(f"仿真结果｜种子 {SEED}｜字节流 {len(stream)} 字节｜埋好的好帧 {len(planted)}")
    print(f"{'解析器':<16}{'救回':>6}{'误收':>6}{'得分':>6}")
    print("-" * 34)
    for name, row in report.items():
        mark = "  ← 基线，要胜过它" if name == BASELINE_NAME else "  ← 仓库参考，不是基线"
        print(f"{name:<16}{row['recovered']:>6}{row['false_accepts']:>6}{row['score']:>6}{mark}")
    print("状态：进行中。得分 = 救回的好帧数 − 误收帧数。这是字节流练习，不是在线抓包。")


if __name__ == "__main__":
    main()
