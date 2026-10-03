"""帧解析器测试：好帧、坏 CRC、垃圾前缀、逐字节喂入、数据域里的伪帧头。"""
import pytest

from frames import HEADER, Frame, FrameParser, parse_stream


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
