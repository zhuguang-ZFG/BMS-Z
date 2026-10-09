"""热五天演示的回归测试。运行：cd code/soc && python3 -m pytest tests/ -q"""
import math

import pytest

import thermal_demo as th


def test_steady_state_matches_analytic():
    """恒流 40 min（20τ）后温度落在解析稳态 0.05 K 内——一阶系统该有的样子。"""
    i_a = -10.0
    ss = th.steady_temp_c(i_a)
    end = th.simulate(th.i_const(i_a), 2400.0)[-1][1]
    assert abs(end - ss) < 0.05


def test_one_tau_reaches_63_percent():
    """τ_th = R_th·C_th：一个时间常数走到总温升的 1−1/e（±2 个百分点）。"""
    i_a = -10.0
    ss = th.steady_temp_c(i_a)
    traj = th.simulate(th.i_const(i_a), th.TAU_TH)
    frac = (traj[-1][1] - th.T_AMB_C) / (ss - th.T_AMB_C)
    assert abs(frac - (1.0 - math.exp(-1.0))) < 0.02


def test_cooling_shares_the_same_tau():
    """线性系统升温降温同一个 τ：从 35 °C 断流，一个 τ 落掉总温差的 63.2%。"""
    t0 = 35.0
    traj = th.simulate(th.i_const(0.0), th.TAU_TH, use_rev=False, t0_c=t0)
    frac = (t0 - traj[-1][1]) / (t0 - th.T_AMB_C)
    assert abs(frac - (1.0 - math.exp(-1.0))) < 0.02


def test_reversible_heat_flips_sign_with_direction():
    """熵斜率为负时：充电（I>0）熵项吸热为负，放电为正——有电流不一定净发热。"""
    assert th.p_rev(th.T_AMB_C, +10.0) < 0.0 < th.p_rev(th.T_AMB_C, -10.0)
    assert th.steady_temp_c(-10.0) > th.steady_temp_c(+10.0)


def test_substep_horizon_integrates_and_matches_analytic():
    """不足一步的请求也要积分：0.4 s 在旧代码里被 round 成零步，温度停在环境值。"""
    i_a, t_end = -10.0, 0.4
    traj = th.simulate(th.i_const(i_a), t_end, use_rev=False)
    assert len(traj) == 2
    assert traj[-1][0] == t_end
    # 关掉熵项后是线性一阶系统，末温有闭式解；欧拉单步与它只差 O(dt²τ)。
    t_ss = th.T_AMB_C + th.p_ohm(i_a) * th.R_TH
    expect = t_ss + (th.T_AMB_C - t_ss) * math.exp(-t_end / th.TAU_TH)
    assert abs(traj[-1][1] - expect) < 1e-4
    assert traj[-1][1] > th.T_AMB_C + 0.01


def test_simulation_reaches_requested_horizon():
    """请求多长就积分多长：末点时间戳与步数都不许被四舍五入改动。"""
    for t_end in (100.4, 119.5, 1499.6, 2000.4, 4800.5):
        traj = th.simulate(th.i_const(-10.0), t_end)
        assert traj[-1][0] == t_end
        assert len(traj) - 1 == math.ceil(t_end / th.DT)


def test_simulation_rejects_nonsense_horizon():
    """负时长与非有限时长没有"合理的多步结果"，必须显式拒绝而不是返回单点。"""
    for bad in (-1.0, -0.4, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="t_end_s"):
            th.simulate(th.i_const(-10.0), bad)


def test_sine_amplitude_and_lag_match_first_order():
    """纯正弦生热（熵关）对一阶低通：幅值 1/√(1+(ωτ)²)，滞后 arctan(ωτ)。"""
    _mean, amp, lag = th.sine_response()
    a_mean, a_amp, a_lag = th.analytic_sine()
    assert abs(amp - a_amp) / a_amp < 0.02
    assert abs(lag - a_lag) < 3.0
    assert abs(_mean - a_mean) < 0.05


def test_ohmic_heat_is_directionless():
    """欧姆火与方向无关：±8 A 生热逐点相等（I² 的代数事实）。"""
    assert th.p_ohm(8.0) == th.p_ohm(-8.0)
    assert th.net_power_w(25.0, 8.0, use_rev=False) == \
        th.net_power_w(25.0, -8.0, use_rev=False)


def test_cli_exit_code_contract():
    """脚本自验收六项全过退出码 0。锁住这个契约。"""
    assert th.main() == 0
