"""CRC 校验：BMS 协议逆向的"试金石"。

对应教程：阶段 5 §5.6 协议逆向方法论第 4 步——
"先用已知协议的帧验证你的 CRC 程序本身是对的，连已知帧都算不对，就别去碰未知协议。"

本模块的测试（tests/test_crc.py）就是这句话的实践：每个算法都拿
crccalc.com 公布的经典校验向量 "123456789" 和一条真实的 Modbus 帧做基准。

CRC 的五个自由度（任何一项错了结果全错，且无法从错误结果反推是哪项错）：
  width   位宽（8/16/32）
  poly    生成多项式
  init    初始值
  refin   输入是否按位反射（字节内 bit 序反转）
  refout  输出是否反射
  xorout  最终异或值
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CrcParams:
    width: int
    poly: int
    init: int
    refin: bool
    refout: bool
    xorout: int


# 常用型号速查（命名遵循 crccalc.com 目录）
CRC8_ATM = CrcParams(8, 0x07, 0x00, False, False, 0x00)     # check: 0xF4
CRC8_MAXIM = CrcParams(8, 0x31, 0x00, True, True, 0x00)     # check: 0xA1，1-Wire/不少电量计
CRC16_MODBUS = CrcParams(16, 0x8005, 0xFFFF, True, True, 0x0000)  # check: 0x4B37
CRC16_CCITT_FALSE = CrcParams(16, 0x1021, 0xFFFF, False, False, 0x0000)  # check: 0x29B1


def _reflect(value: int, width: int) -> int:
    """把 value 的低 width 位做镜像翻转。"""
    result = 0
    for _ in range(width):
        result = (result << 1) | (value & 1)
        value >>= 1
    return result


def crc(data: bytes | bytearray | list[int], params: CrcParams) -> int:
    """通用按位 CRC。教学实现，可读优先——量产代码用查表法或硬件 CRC 单元。"""
    mask = (1 << params.width) - 1
    top = 1 << (params.width - 1)
    reg = params.init & mask

    for byte in data:
        if params.refin:
            byte = _reflect(byte, 8)
        # 字节对齐到寄存器最高位（width > 8 时左移）
        reg ^= (byte << (params.width - 8)) & mask
        for _ in range(8):
            reg = ((reg << 1) ^ params.poly) & mask if reg & top else (reg << 1) & mask

    if params.refout:
        reg = _reflect(reg, params.width)
    return reg ^ params.xorout


def crc8_atm(data) -> int:
    return crc(data, CRC8_ATM)


def crc8_maxim(data) -> int:
    return crc(data, CRC8_MAXIM)


def crc16_modbus(data) -> int:
    return crc(data, CRC16_MODBUS)
