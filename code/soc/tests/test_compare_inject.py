"""compare.simulate_ekf 受控注入的回归：钉住书第 17 章 17.3 节与图 17-2 引用的数。

运行：cd code/soc && python3 -m pytest tests/ -q

这些数字是算出来的，字面 grep 不到。尤其电压偏置那一组：EKF 把 +50 mV 读成
“SOC 高了约 6 个百分点”，残差在 SOC 被钳到 100% 之前几乎为零——
如果有人把它改回“残差整体平移”，这里先红。
"""
from __future__ import annotations

import numpy as np
import pytest

import compare


def _trace(r0: float = 0.020, q_ah: float = 9.5, v_bias_v: float = 0.0):
    return compare.simulate_ekf(r0, 0.015, 3000.0, q_ah, v_bias_v=v_bias_v)


def _summary(trace) -> tuple[float, float, float]:
    inn, cur = trace["innovation_mv"], trace["current_a"]
    load = np.abs(cur) > 1.0
    return (float(np.median(np.abs(inn))), float(inn.mean()),
            float(np.corrcoef(inn[load], cur[load])[0, 1]))


@pytest.mark.parametrize(("kwargs", "expected"), [
    ({}, (3.64, 0.06, -0.004)),
    ({"r0": 0.200}, (6.41, 9.76, -0.288)),
    ({"v_bias_v": 0.050}, (4.25, 3.99, 0.060)),
    ({"q_ah": 5.0}, (3.64, 0.01, -0.062)),
])
def test_inject_table_matches_documented_values(kwargs, expected):
    """共学第 3 天那张四行表：新息中位、新息均值（mV）、与电流的相关。"""
    median, mean, corr = _summary(_trace(**kwargs))
    assert (round(median, 2), round(mean, 2), round(corr, 3)) == expected


def test_r0_residual_grows_with_discharge_current():
    """R0 十倍：残差随电流大小单调变大——参数错“跟着电流走”。"""
    trace = _trace(r0=0.200)
    inn, cur = trace["innovation_mv"], trace["current_a"]
    medians = [float(np.median(inn[np.abs(cur - level) < 0.5])) for level in (-6, -5, -4, -3)]
    assert [round(m) for m in medians] == [679, 538, 354, 230]


def test_voltage_bias_is_absorbed_into_soc_until_saturation():
    """+50 mV 偏置：先被读成 SOC 偏高约 6 个百分点，残差只在 SOC 钳到 100% 后才冒出来。"""
    trace = _trace(v_bias_v=0.050)
    inn = trace["innovation_mv"]
    soc_err_pp = 100 * (trace["soc_est"] - trace["soc_true"])
    sat = int(np.argmax(trace["soc_est"] >= 1.0))

    assert sat == 14916
    assert round(float(trace["soc_true"][sat]), 3) == 0.951
    assert round(float(soc_err_pp[1800:8300].mean()), 1) == 6.0   # 放电段
    assert abs(float(inn[:sat].mean())) < 0.05                      # 饱和前：残差均值 ≈ 0
    assert round(float(inn[sat:].mean()), 1) == 32.5                # 饱和后：一下子冒出来
    assert float(inn[sat:].sum() / inn.sum()) > 0.99                # 3.99 mV 的均值几乎全来自这一段


def test_negative_voltage_bias_stays_silent_when_soc_never_clamps():
    """−50 mV：SOC 一路偏低约 6.2 个百分点，本工况撞不到 0%，三个诊断数和“都对”几乎一样。"""
    trace = _trace(v_bias_v=-0.050)
    median, mean, corr = _summary(trace)
    soc_err_pp = 100 * (trace["soc_est"] - trace["soc_true"])

    assert (round(median, 2), round(mean, 2), round(corr, 3)) == (3.64, -0.0, -0.002)
    assert round(float(soc_err_pp[1800:8300].mean()), 1) == -6.2
    assert float(trace["soc_est"].min()) > 0.3
