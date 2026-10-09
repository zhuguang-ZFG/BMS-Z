"""SOP 双法演示的回归测试。运行：cd code/soc && python3 -m pytest tests/ -q"""
import math

import pytest

import sop_demo


def test_hppc_closed_form_matches_formula():
    """闭式解就是 (OCV − U_min)/R0：静置出发、只看电压一条约束的代数事实。"""
    soc = 0.5
    expected = (float(sop_demo.ocv(soc)) - sop_demo.V_MIN) / sop_demo.R0
    assert abs(sop_demo.hppc_current(soc) - expected) < 1e-9


@pytest.mark.parametrize("window_s", [0.04, 0.14, 0.16, 0.3])
def test_simulation_uses_exact_requested_window(window_s):
    """短于一步、非整步和整步窗口都须按实际时长满足电荷守恒与 RC 解析解。"""
    soc0, i_dis = 0.5, 10.0
    v_min, soc_end = sop_demo.simulate_window(soc0, i_dis, window_s)
    expected_soc = soc0 - i_dis * window_s / (3600.0 * sop_demo.Q_AH)
    # 静置起点恒流放电，OCV 与极化电压均单调下降，窗末就是整窗最低电压。
    expected_voltage = (
        float(sop_demo.ocv(expected_soc)) - i_dis * sop_demo.R0
        - i_dis * sop_demo.R1 * (1.0 - math.exp(
            -window_s / (sop_demo.R1 * sop_demo.C1)))
    )
    assert soc_end == pytest.approx(expected_soc, rel=0, abs=1e-12)
    assert v_min == pytest.approx(expected_voltage, rel=0, abs=1e-12)


def test_substep_window_respects_soc_charge_budget():
    """不足一步也不能绕过 SOC 墙；独立电荷账不复用被测可行性判据。"""
    soc0 = sop_demo.SOC_MIN + 1e-5
    window_s = 0.04
    current, binding = sop_demo.bisect_current(soc0, window_s)
    wall_current = (soc0 - sop_demo.SOC_MIN) * sop_demo.Q_AH * 3600.0 / window_s
    actual_soc = soc0 - current * window_s / (3600.0 * sop_demo.Q_AH)
    assert actual_soc >= sop_demo.SOC_MIN
    assert 0.0 <= wall_current - current < sop_demo.BISECT_TOL_A
    assert binding == "SOC墙"


def test_bisect_solution_is_feasible_and_maximal():
    """二分解可行（整窗电压不破线、SOC 不穿墙），再多要 0.1 A 就不可行。"""
    i, _binding = sop_demo.bisect_current(0.15, 10.0)
    assert sop_demo._feasible(0.15, i, 10.0)
    assert not sop_demo._feasible(0.15, i + 0.1, 10.0)


def test_hppc_optimistic_where_voltage_binds():
    """电压约束区内闭式法偏乐观：它不算 ΔT 窗内继续积累的极化。"""
    assert sop_demo.hppc_current(0.15) > sop_demo.bisect_current(0.15, 10.0)[0]


def test_soc_wall_invisible_to_hppc():
    """贴墙工作点：二分被 SOC 墙咬住，闭式法仍报大电流——漏墙即过放。"""
    i, binding = sop_demo.bisect_current(0.12, 30.0)
    assert binding == "SOC墙"
    assert sop_demo.hppc_current(0.12) > i


def test_longer_window_never_looser():
    """时间窗越长允许电流越小：极化随窗累积（阶段 4 §4.7 的三档单调性）。"""
    for soc in sop_demo.SOC_POINTS:
        currents = [sop_demo.bisect_current(soc, t)[0]
                    for t in sop_demo.WINDOWS_S]
        assert all(a >= b - 1e-9 for a, b in
                   zip(currents[:-1], currents[1:], strict=True)), soc

def test_current_cap_is_a_real_constraint():
    """高 SOC 电压余量充足，系统电流帽先咬——多约束取最小的可跑版。"""
    i, binding = sop_demo.bisect_current(0.90, 10.0)
    assert binding == "电流帽"
    assert i == sop_demo.I_MAX


def test_cli_exit_code_contract():
    """脚本 docstring 承诺：六项自验收全过退出码 0。锁住这个契约。"""
    assert sop_demo.main() == 0
