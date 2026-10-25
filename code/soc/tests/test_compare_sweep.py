"""compare.py --sweep 的回归：钉住"哪个参数写错更要命"那三个数。

运行：cd code/soc && python3 -m pytest tests/ -q

第 10 章与共学第九天都引用 R0 十倍 41.51%、R1 十倍 36.14%、C1 十倍 1.00%。
这些数字是**算出来的**，字面 grep 不到——所以钉在这里：谁改了估计器、工况
或这组接线，测试先红，比书里那几个数悄悄漂走强。
现有测试对这一点是空白的（默认路径的 EKF 用的是标称参数，永远看不到失配）。
"""
from __future__ import annotations

import pytest

import compare


def _case(name: str) -> tuple[float, float]:
    for entry in compare.PARAM_SWEEP:
        if entry[0] == name:
            return compare.measure_soc_error(*entry[1:])
    raise AssertionError(f"PARAM_SWEEP 里没有 {name}")


def test_sweep_reproduces_documented_parameter_sensitivity():
    """标称、R0 十倍、R1 十倍、C1 十倍 四行的 RMSE 与文档一致。"""
    nominal, _ = _case("出厂 R0=20mΩ")
    r0_x10, _ = _case("R0 十倍 200mΩ")
    r1_x10, _ = _case("R1 十倍 150mΩ")
    c1_x10, _ = _case("C1 十倍 30000F")

    assert nominal == pytest.approx(0.20, abs=0.01)
    assert r0_x10 == pytest.approx(41.51, abs=0.01)
    assert r1_x10 == pytest.approx(36.14, abs=0.01)
    assert c1_x10 == pytest.approx(1.00, abs=0.01)


def test_sweep_orders_resistance_above_time_constant():
    """结论的形状也要守住：电阻错 ≫ 时间常数错，容量错几乎不动。"""
    r0_x10, _ = _case("R0 十倍 200mΩ")
    r1_x10, _ = _case("R1 十倍 150mΩ")
    c1_x10, _ = _case("C1 十倍 30000F")
    half_q, _ = _case("容量砍半 5.0Ah")

    assert min(r0_x10, r1_x10) > 10 * max(c1_x10, half_q)