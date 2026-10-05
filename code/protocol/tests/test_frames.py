"""帧解析器测试：好帧、坏 CRC、垃圾前缀、逐字节喂入、数据域里的伪帧头。"""
import pytest

from frames import HEADER, MAX_LEN, Frame, FrameParser, parse_stream


def voltage_frame(addr: int, cell_mv: list[int]) -> Frame:
    """组一条"电压查询响应"帧（cmd=0x03，大端 16bit mV）。"""
    data = b"".join(v.to_bytes(2, "big") for v in cell_mv)
    return Frame(addr, 0x03, data)


def test_roundtrip_and_decode():
    f = voltage_frame(0x01, [3650, 3652, 3649, 3651])
    frames, parser = parse_stream(f.to_bytes())
    assert len(frames) == 1
    assert frames[0].cell_voltage_mv(0) == 3650
    assert frames[0].cell_voltage_mv(3) == 3651
    assert parser.frames_ok == 1
    assert parser.frames_bad_crc == 0


def test_bad_crc_is_dropped_and_counted():
    wire = bytearray(voltage_frame(0x01, [3650]).to_bytes())
    wire[-1] ^= 0xFF                      # 破坏 CRC 字节
    frames, parser = parse_stream(bytes(wire))
    assert frames == []
    assert parser.frames_bad_crc == 1     # 坏帧必须计数，不许静默吞掉


def test_garbage_prefix_resyncs():
    stream = b"\x00\xFF\x13\x37" + voltage_frame(0x01, [3650]).to_bytes()
    frames, parser = parse_stream(stream)
    assert len(frames) == 1
    assert parser.frames_ok == 1


def test_fake_header_inside_data():
    """数据域里出现 AA 55 字节时，解析器不应误判为新帧头。"""
    f = Frame(0x01, 0x03, bytes([0xAA, 0x55, 0xAA, 0x55]))
    frames, _ = parse_stream(f.to_bytes())
    assert len(frames) == 1
    assert frames[0].data == bytes([0xAA, 0x55, 0xAA, 0x55])


def test_byte_by_byte_feeding():
    """UART 中断就是一个字节一个字节来的——解析器必须支持。"""
    wire = voltage_frame(0x02, [3650, 3651]).to_bytes()
    parser = FrameParser()
    out = [parser.feed(b) for b in wire]
    assert out[-1] is not None and out[-1].addr == 0x02
    assert all(x is None for x in out[:-1])


def test_illegal_length_dropped():
    # len 超过 MAX_LEN → 丢帧并重新同步，后面的好帧不受影响
    bad = HEADER + bytes([0x01, 0x03, 0xFF])
    good = voltage_frame(0x01, [3650]).to_bytes()
    frames, parser = parse_stream(bad + good)
    assert parser.frames_bad_len == 1
    assert len(frames) == 1


def test_bad_len_byte_reconsidered_as_header():
    """残帧停在 len 字段、而该字节正是下一条帧的帧头首字节（0xAA）时，
    重新同步不得把它一起吞掉。曾经的写法直接丢进 header0：0xAA 被丢弃后，
    后面的 55 02 03 ... 再也凑不出帧头，整条完好的帧静默消失。"""
    good = voltage_frame(0x02, [3650]).to_bytes()
    stream = HEADER + bytes([0x01, 0x03]) + good     # 残帧元信息后紧接好帧
    frames, parser = parse_stream(stream)
    assert parser.frames_bad_len == 1
    assert [f.addr for f in frames] == [0x02]
    assert frames[0].cell_voltage_mv(0) == 3650


def test_encode_rejects_payload_over_max_len():
    """组帧必须拒绝超长载荷：len 是单字节、解析器又拒收 > MAX_LEN 的帧，
    放行等于组出"自己的解析器认不出"的帧（往返不一致）。"""
    with pytest.raises(ValueError):
        Frame(0x01, 0x03, bytes(MAX_LEN + 1)).to_bytes()
    # 边界：正好 MAX_LEN 必须能往返
    frames, parser = parse_stream(Frame(0x01, 0x03, bytes(MAX_LEN)).to_bytes())
    assert len(frames) == 1
    assert parser.frames_bad_len == 0


def test_empty_payload_roundtrip():
    """len=0 合法：元信息后紧跟 CRC，不得把 CRC 字节误当成 data。"""
    f = Frame(0x01, 0x10, b"")
    wire = f.to_bytes()
    assert len(wire) == 6                          # AA 55 addr cmd len crc
    frames, parser = parse_stream(wire)
    assert len(frames) == 1
    assert frames[0].addr == 0x01 and frames[0].cmd == 0x10
    assert frames[0].data == b""
    assert parser.frames_ok == 1


def test_parser_survives_random_garbage():
    """军规：绝不因坏数据死机。随机字节流灌入不应抛异常、不应卡死。"""
    import random
    random.seed(0)
    parser = FrameParser()
    garbage = bytes(random.getrandbits(8) for _ in range(10000))
    for b in garbage:                    # 不抛异常即通过
        parser.feed(b)
    # 末尾接一条好帧，必须仍能解析出来
    good = voltage_frame(0x01, [3650]).to_bytes()
    assert [parser.feed(b) for b in good][-1] is not None


def test_decode_wrong_cmd_raises():
    f = Frame(0x01, 0x07, bytes([0x00, 0x01]))
    with pytest.raises(ValueError):
        f.cell_voltage_mv(0)


def test_decode_cell_index_out_of_range():
    f = voltage_frame(0x01, [3650])
    with pytest.raises(IndexError):
        f.cell_voltage_mv(1)


def test_decode_negative_cell_index_raises():
    """负下标不得靠 Python 负索引回绕读到尾部数据——必须抛 IndexError。"""
    f = voltage_frame(0x01, [3650])
    with pytest.raises(IndexError):
        f.cell_voltage_mv(-1)


@pytest.mark.parametrize("cut", range(1, 8))
def test_truncated_frame_does_not_swallow_next_frame(cut):
    """从帧头到 CRC 的每个截断位置都覆盖；整段结束后应找回后面的好帧。"""
    broken = voltage_frame(1, [3600]).to_bytes()[:cut]
    expected = voltage_frame(2, [3650])
    frames, parser = parse_stream(broken + expected.to_bytes())
    assert frames == [expected]
    assert parser.frames_ok == 1


def test_bad_crc_rescans_payload_and_keeps_multiple_good_frames():
    expected = [voltage_frame(2, [3650]), voltage_frame(3, [3660])]
    # 两条好帧已被损坏的外层帧当成载荷；确认外层 CRC 错后都要找回来。
    bad = bytearray(Frame(1, 3, b"".join(f.to_bytes() for f in expected)).to_bytes())
    bad[-1] ^= 0xFF
    frames, parser = parse_stream(bytes(bad))
    assert frames == expected
    assert parser.frames_bad_crc == 1


def test_valid_frame_can_contain_a_complete_valid_frame():
    """完整好帧嵌在合法载荷内也只是数据，不可抢先输出内层帧。"""
    inner = voltage_frame(2, [3650])
    outer = Frame(1, 3, inner.to_bytes())
    frames, parser = parse_stream(outer.to_bytes())
    assert frames == [outer]
    assert parser.frames_bad_crc == 0


def test_explicit_flush_recovers_after_corrupt_legal_length():
    expected = voltage_frame(2, [3650])
    stream = HEADER + bytes([1, 3, MAX_LEN]) + expected.to_bytes()
    parser = FrameParser()
    assert all(parser.feed(b) is None for b in stream)
    assert parser.flush() == [expected]      # 上层明确收到超时／流结束
    assert parser.frames_incomplete == 1
    assert parser.flush() == []
    # flush 后继续收帧，统计保留；不把旧残帧接到新帧上。
    out = [f for b in expected.to_bytes() if (f := parser.feed(b)) is not None]
    assert out == [expected]
    assert parser.frames_ok == 2


def test_missing_crc_recovers_while_streaming_without_flush():
    broken = voltage_frame(1, [3600]).to_bytes()[:-1]
    expected = voltage_frame(2, [3650])
    parser = FrameParser()
    frames = [f for b in broken + expected.to_bytes() if (f := parser.feed(b)) is not None]
    assert frames == [expected]
    assert parser.frames_bad_crc == 1


def test_receive_buffer_is_bounded_under_noise():
    """反复输入合法最大长度残头和噪声，缓冲不能随流长无限增长。"""
    import random
    rng = random.Random(17)
    parser = FrameParser()
    for _ in range(200):
        stream = HEADER + bytes([1, 3, MAX_LEN]) + rng.randbytes(91)
        for b in stream:
            parser.feed(b)
            assert len(parser._buf) < MAX_LEN + 6
    parser.flush()
    assert not parser._buf
