"""HPPC 辨识演示的回归测试。运行：cd code/soc && python3 -m pytest tests/ -q"""
import math

import hppc_demo


def test_noiseless_identification_is_tight():
    """无噪声时辨识应几乎精确——拟合结构本身的正确性（排除噪声因素）。"""
    r0e, r1e, c1e, _tau = hppc_demo.identify_one(
        0.6, hppc_demo.TRUE_R0[3], hppc_demo.TRUE_R1[3],
        hppc_demo.TRUE_C1[3], noise=False)
    assert abs(r0e - hppc_demo.TRUE_R0[3]) / hppc_demo.TRUE_R0[3] < 0.03
    assert abs(r1e - hppc_demo.TRUE_R1[3]) / hppc_demo.TRUE_R1[3] < 0.03
    assert abs(c1e - hppc_demo.TRUE_C1[3]) / hppc_demo.TRUE_C1[3] < 0.05


def test_noisy_identification_within_demo_tolerances():
    """带噪全程：8 个 SOC 点全部落在脚本自验收容差内（确定性种子）。"""
    for k, soc in enumerate(hppc_demo.SOC_POINTS):
        r0e, r1e, c1e, _tau = hppc_demo.identify_one(
            float(soc), hppc_demo.TRUE_R0[k], hppc_demo.TRUE_R1[k],
            hppc_demo.TRUE_C1[k], seed=hppc_demo.SEED + k)
        assert abs(r0e - hppc_demo.TRUE_R0[k]) / hppc_demo.TRUE_R0[k] \
            <= hppc_demo.TOL_R0, f"SOC={soc} R0 超差"
        assert abs(r1e - hppc_demo.TRUE_R1[k]) / hppc_demo.TRUE_R1[k] \
            <= hppc_demo.TOL_R1, f"SOC={soc} R1 超差"
        assert abs(c1e - hppc_demo.TRUE_C1[k]) / hppc_demo.TRUE_C1[k] \
            <= hppc_demo.TOL_C1, f"SOC={soc} C1 超差"


def test_cli_exit_code_contract():
    """脚本 docstring 承诺：退出码 0 = 全部点在容差内。锁住这个契约。"""
    assert hppc_demo.main() == 0


def _relaxation(seed: int = hppc_demo.SEED):
    """SOC 0.5 点的脉冲后静置段，从 0 s 起算。"""
    t, u, _i, n_pre, n_pulse = hppc_demo.simulate_pulse(
        0.5, 33e-3, 16e-3, 2200, seed=seed)
    start = n_pre + n_pulse
    return t[start:] - t[start], u[start:]


def _r1_estimate(tau: float, amp: float) -> float:
    """amp = I·R1·(1-exp(-T_pulse/τ))，反解 R1（五天第 2 天的那笔账）。"""
    factor = 1.0 - math.exp(-hppc_demo.T_PULSE / tau)
    return abs(amp) / (abs(hppc_demo.I_PULSE) * factor)


def test_short_rest_window_breaks_identifiability():
    """钉住第 3 天坑①的教学断言：**同一份**带噪曲线，窗长从 120s 砍到 40s，
    修正后的 R1 必须显著劣化（实测 0.1% → 19.3%），全程窗还得在自验收容差内。
    它防的是「静置要覆盖 3 个 τ」这条口径被改掉后演示悄悄不再展示病态。
    整段把 T_REST 改短是另一回事——那会改动噪声序列、让 8 个 SOC 点的容差表自己超差，
    由 test_cli_exit_code_contract 兜底，不在本条射程内。"""
    t_rel, u_rel = _relaxation()
    r1_true = 16e-3
    tau_full, amp_full, _ = hppc_demo.fit_relaxation(t_rel, u_rel)
    tau_short, amp_short, _ = hppc_demo.fit_relaxation(
        t_rel[t_rel <= 40.0], u_rel[t_rel <= 40.0])
    err_full = abs(_r1_estimate(tau_full, amp_full) - r1_true) / r1_true
    err_short = abs(_r1_estimate(tau_short, amp_short) - r1_true) / r1_true
    assert err_full <= hppc_demo.TOL_R1, f"全程窗自己都超差了：{err_full:.1%}"
    assert err_short > 5.0 * err_full, (
        f"40s 窗没坏到全程窗的 5 倍（{err_short:.1%} vs {err_full:.1%}）"
        "——「静置要覆盖 3 个 τ」这条口径失效了")


def test_voltage_drift_impersonates_a_long_tau():
    """真数据最贵的坑：缓慢漂移会被吸成长 τ。同一份曲线叠 0.1 mV/s 线性
    漂移，τ 估计必须被拉到真值两倍以上（实测顶到网格上界）。
    fit_relaxation 故意不去趋势——哪天加了去趋势，先改五天第 5 天的说法。"""
    t_rel, u_rel = _relaxation()
    tau_clean, _, _ = hppc_demo.fit_relaxation(t_rel, u_rel)
    tau_drift, _, _ = hppc_demo.fit_relaxation(t_rel, u_rel - 0.1e-3 * t_rel)
    assert tau_drift > 2.0 * tau_clean, (
        f"漂移只把 τ 从 {tau_clean:.1f}s 拉到 {tau_drift:.1f}s，"
        "与五天第 5 天「漂移冒充长 τ」的说法不符")


def test_r0_jump_window_stays_rc_free():
    """R0 只吃脉冲后 0.3s，τ≈35s 的 RC 那时还没起步：换成 2.0s 窗口再算，
    两次的差必须远小于 R0 容差，且都贴着真值。RC 一旦漏进「瞬时」窗口，
    整张 SOC 表的 R0 会一起往上漂。"""
    t, u, i, n_pre, _n_pulse = hppc_demo.simulate_pulse(0.5, 33e-3, 16e-3, 2200)
    base = sum(u[n_pre - 10:n_pre]) / 10.0

    def r0_from(n_samples: int) -> float:
        jump = sum(u[n_pre:n_pre + n_samples]) / n_samples
        i_jump = sum(i[n_pre:n_pre + n_samples]) / n_samples
        return (base - jump) / abs(i_jump)

    r0_fast, r0_slow = r0_from(3), r0_from(20)
    assert abs(r0_fast - r0_slow) < 1.5e-3, (
        f"0.3s 与 2.0s 窗口差 {abs(r0_fast - r0_slow) * 1e3:.2f} mΩ——RC 漏进了跳变窗")
    for value in (r0_fast, r0_slow):
        assert abs(value - 33e-3) / 33e-3 <= hppc_demo.TOL_R0
