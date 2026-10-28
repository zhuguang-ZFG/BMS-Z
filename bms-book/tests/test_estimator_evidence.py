"""Numerical contracts for the estimator calculations readers reproduce."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1] / "code"


def load(name):
    # These modules have no import-time experiments; dataclass needs registration.
    import sys
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("scale", [1.0, 1e-7])
def test_joseph_covariance_matches_independent_information_form(scale):
    module = load("ekf_soc")
    prior = np.array([[0.01, 0.0003], [0.0003, 0.0001]]) * scale
    observation = np.array([[0.8, 1.0]])
    variance = 2.5e-5 * scale
    gain = prior @ observation.T / (observation @ prior @ observation.T + variance)
    updated = np.array(module.joseph_covariance(
        *prior.ravel(), *gain.ravel(), *observation.ravel(), variance,
    )).reshape(2, 2)
    # Posterior precision = prior precision + measurement precision.
    reference = np.linalg.inv(np.linalg.inv(prior) + observation.T @ observation / variance)
    np.testing.assert_allclose(updated, reference, rtol=1e-11, atol=1e-18)
    assert np.linalg.eigvalsh(updated).min() > 0


def test_published_first_ticks_match_the_chapter_tables():
    """钉住第 27 章 §27.2 两张表里逐格引用的数字。

    表 27-2：新息、自报尺度、K0、采信比例 K0·C0、NIS；
    表 27-3：协方差非对角项与相关系数。
    改了 ekf_soc 的初值、噪声或更新式，这里会先红，提醒同步改正文的数字。
    """
    module = load("ekf_soc")
    ticks = module.first_ticks(4)
    assert [t.k for t in ticks] == [0, 1, 2, 3]

    # 表 27-2（毫伏与无量纲量按正文给出的位数核对）
    expected = [
        # residual_mV, sqrt(S)_mV, K0, K0*C0, NIS
        (+84.404, 81.482, 1.2163, 0.982, 1.0730),
        (-0.527, 8.029, 0.9344, 0.883, 0.0043),
        (+1.531, 6.519, 0.6497, 0.612, 0.0552),
    ]
    for tick, (residual_mv, sigma_mv, k0, kh, nis) in zip(ticks, expected, strict=False):
        assert tick.residual_v * 1000 == pytest.approx(residual_mv, abs=5e-4)
        assert np.sqrt(tick.s_var) * 1000 == pytest.approx(sigma_mv, abs=5e-4)
        assert tick.k_soc == pytest.approx(k0, abs=5e-5)
        assert tick.kh == pytest.approx(kh, abs=5e-4)
        assert tick.nis == pytest.approx(nis, abs=5e-5)

    # 正文的叙事主张：第 0 拍把 10 个百分点的初值错误一次还掉。
    first = ticks[0]
    assert first.soc_predicted == pytest.approx(0.699861, abs=5e-7)
    assert first.k_soc * first.residual_v == pytest.approx(0.102659, abs=5e-7)
    assert first.soc_updated == pytest.approx(0.802520, abs=5e-7)
    assert abs(first.soc_updated - first.soc_true) < 0.003
    # 第 0 拍的 NIS 落在 1 附近——「错得理所应当」，不是参数坏了。
    assert 0.5 < first.nis < 2.0

    # 表 27-3：P 的非对角项从 0 起步，一拍之后就学出强负相关。
    assert first.p01 == pytest.approx(-1.1503e-4, rel=1e-4)
    correlations = [t.correlation for t in ticks]
    assert correlations == pytest.approx([-0.8876, -0.9320, -0.9475, -0.9538], abs=5e-5)
    # 负号是物理决定的：OCV 与极化同时被一只电压表看到，一高必须一低。
    assert all(c < 0 for c in correlations)
    # det P = P00·P11·(1−ρ²) —— 正文用它说明 |ρ|→1 时矩阵趋奇异。
    last = ticks[-1]
    assert last.p00 * last.p11 - last.p01 ** 2 == pytest.approx(
        last.p00 * last.p11 * (1 - last.correlation ** 2), rel=1e-9,
    )
    with pytest.raises(ValueError):
        module.first_ticks(0)


def test_correlation_deepens_then_relaxes_instead_of_approaching_minus_one():
    """表 27-3 的趋势：先深到 −0.954，再回松、稳在 −0.46 附近。

    只看前四拍会误以为「越来越难分」，于是把一个瞬态写成结论——初稿正是这么写的。
    """
    module = load("ekf_soc")
    ticks = module.first_ticks(400)
    published = {0: -0.8876, 1: -0.9320, 3: -0.9538, 5: -0.9565, 10: -0.9475,
                 30: -0.8490, 100: -0.4837, 399: -0.4633}
    for k, rho in published.items():
        assert ticks[k].correlation == pytest.approx(rho, abs=5e-5), f"第 {k} 拍"
    deepest = min(range(len(ticks)), key=lambda k: ticks[k].correlation)
    assert deepest == 5, "最深处在第 5 拍（表里标的那一行），不是一路走向 −1"
    assert ticks[-1].correlation > ticks[deepest].correlation + 0.4, "之后必须明显回松"


def test_covariance_recursion_ignores_current_and_measurement():
    """正文的反直觉结论：P 的轨迹只由 A、C、Q、R 决定，与 I、z 无关。

    初稿曾写「来一段电流阶跃，相关就会松开」——实测 demo 的两次阶跃
    （第 1200、1800 拍）处 ρ 一动不动，那句话是错的。这里把正确的版本钉住：
    单独跑协方差递推（不喂电流、不喂测量、冻结斜率）能复现稳态 ρ。
    """
    module = load("ekf_soc")
    ticks = module.first_ticks(1900)
    # demo 的电流在第 1200 拍由 −5 A 跳到 0、第 1800 拍由 0 跳到 +4 A。
    # 不是严格不变：C=[dOCV/dSOC,1] 跟着 SOC 走，而 SOC 受电流影响，所以 ρ 会在
    # 第 6 位小数上动一点——这正是正文末尾声明的那条近似边界。量级上可忽略。
    for step in (1200, 1800):
        before, after = ticks[step - 1].correlation, ticks[step + 1].correlation
        assert after == pytest.approx(before, abs=1e-4), f"第 {step} 拍阶跃处 ρ 不应有可见变化"
        assert abs(after - before) > 0, "也不会是严格相等：C 随工作点变"

    # 只用 A、C、Q、R 跑协方差递推，复现稳态 ρ。
    a = float(np.exp(-1.0 / (0.016 * 2200.0)))
    r_var, q00, q11 = 2.5e-5, 2e-6, 1e-7
    slope = 0.8074
    p00, p01, p10, p11 = 1e-2, 0.0, 0.0, 1e-4
    for _ in range(400):
        p00, p01, p10, p11 = p00 + q00, p01 * a, p10 * a, p11 * a * a + q11
        s = slope * (p00 * slope + p01) + (p10 * slope + p11) + r_var
        k0, k1 = (p00 * slope + p01) / s, (p10 * slope + p11) / s
        p00, p01, p10, p11 = module.joseph_covariance(
            p00, p01, p10, p11, k0, k1, slope, 1.0, r_var,
        )
    data_free_rho = p01 / np.sqrt(p00 * p11)
    assert data_free_rho == pytest.approx(-0.4657, abs=5e-5)
    # 与整段带数据运行的稳态相符（正文据此说 P 可离线预算）。
    assert ticks[1899].correlation == pytest.approx(data_free_rho, abs=0.02)


def test_observability_determinant_is_not_the_correlation_claim():
    """正文刻意分开的两件事：结构可观测（det O）与证据分离度（ρ）。

    同一组参数下 det O = H(a−1) ≈ −0.0264 不为零，而 ρ 已到 −0.95：
    「相关系数高」不等于「不可观测」，§27.2 末尾那段就是为了拦住这个误读。
    """
    module = load("ekf_soc")
    ticks = module.first_ticks(4)
    a = np.exp(-1.0 / (0.016 * 2200.0))
    slope = module.docv(ticks[2].soc_predicted)
    determinant = slope * (a - 1.0)
    assert determinant == pytest.approx(-0.0264, abs=5e-5)
    assert determinant != 0  # 结构上可分
    assert ticks[-1].correlation < -0.9  # 证据上还没分开
    assert abs(determinant) > 1e-3, "det O 不接近零，正文不能说成不可观测"


def test_capacity_uncertainty_includes_endpoint_covariance():
    module = load("estimator_evidence")
    _, independent = module.capacity_sigma(0.72, 0.4, 0.02, 0.01, 0.01)
    _, common_offset = module.capacity_sigma(0.72, 0.4, 0.02, 0.01, 0.01, correlation=1)
    # Perfectly shared endpoint error cancels in the SOC difference.
    assert common_offset == pytest.approx(0.02 / 0.4)
    assert independent > common_offset
    with pytest.raises(ValueError):
        module.capacity_sigma(0.72, 0, 0.02, 0.01, 0.01)
