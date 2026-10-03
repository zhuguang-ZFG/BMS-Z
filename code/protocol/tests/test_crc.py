"""CRC 基准测试——教程 §5.6："先用已知帧验证你的 CRC 程序本身是对的"。

基准向量来源：
  - "123456789" 各算法的 check 值：crccalc.com 公布的标准校验值；
  - Modbus 帧 01 03 00 00 00 0A + CRC C5 CD：Modbus 官方协议文档示例。
"""
from crc import (CRC8_ATM, CRC8_MAXIM, CRC16_MODBUS, CRC16_CCITT_FALSE,
                 crc, crc8_atm, crc16_modbus)

CHECK_INPUT = b"123456789"


def test_crc8_atm_check_vector():
    assert crc(CHECK_INPUT, CRC8_ATM) == 0xF4


def test_crc8_maxim_check_vector():
    assert crc(CHECK_INPUT, CRC8_MAXIM) == 0xA1


def test_crc16_modbus_check_vector():
    assert crc(CHECK_INPUT, CRC16_MODBUS) == 0x4B37


def test_crc16_ccitt_false_check_vector():
    assert crc(CHECK_INPUT, CRC16_CCITT_FALSE) == 0x29B1


def test_modbus_real_frame():
    """真实 Modbus 帧：01 03 00 00 00 0A，CRC=0xCDC5，线上低字节先发（C5 CD）。"""
    frame_body = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x0A])
    value = crc16_modbus(frame_body)
    assert value == 0xCDC5
    # Modbus 线上字节序：低字节在前
    wire = frame_body + bytes([value & 0xFF, value >> 8])
    assert wire == bytes.fromhex("01030000000AC5CD")
    # 接收端验证惯例：对"数据+CRC"整段再算一遍，结果为 0 即帧完好
    assert crc16_modbus(wire) == 0x0000


def test_single_byte_error_is_detected():
    """CRC 的意义：帧里翻转任何一字节的任一比特，都应被检出。"""
    body = bytes([0x01, 0x03, 0x02, 0x12, 0x34])
    good = crc8_atm(body)
    for i in range(len(body)):
        for bit in range(8):
            corrupted = bytearray(body)
            corrupted[i] ^= 1 << bit
            assert crc8_atm(corrupted) != good, f"第 {i} 字节第 {bit} 位翻转未被检出"
