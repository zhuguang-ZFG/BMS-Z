"""HPPC 辨识演示的回归测试。运行：cd code/soc && python3 -m pytest tests/ -q"""
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
