"""球扩散（SPM 中段）演示的回归测试。运行：cd code/soc && python3 -m pytest tests/ -q

这些测试故意**不复用**被测脚本里的闭式：权重用另一套梯形积出来、三对角解用 numpy 稠密解
对拍、弛豫速率用对数斜率量。锚点如果被改错，得靠另一条独立路径发现，而不是同一条公式
自证自。慢的那个（跑 main）把整份打印里的数字全钉住——文档页引用的是这些数，不是示意图。
"""
import math

import numpy as np
import pytest

import spm_demo as S


def _trap(y, h):
    """独立实现的等距梯形（不借被测模块的 integral）。"""
    return float(h * (y.sum() - 0.5 * (y[0] + y[-1])))


def _roots(n):
    m = np.arange(1, n + 1, dtype=float)
    return S.tan_roots(n), m


def test_roots_are_really_roots_of_tan_x_minus_x():
    """前 30 个根：残差归零，且严格落在 (mπ, mπ+π/2) 里——跨过极点会收到渐近线上的假根。"""
    x, m = _roots(30)
    assert np.max(np.abs(np.tan(x) - x)) < 1e-7
    assert np.all(x > m * math.pi) and np.all(x < m * math.pi + math.pi / 2)
    assert np.all(np.diff(x) > 0)


def test_first_time_constant_is_sphere_not_slab():
    """x₁=4.4934 而不是 π：把 1/π² 当第一时间常数会把弛豫说成 2.05 倍长。"""
    assert S.XS[0] == pytest.approx(4.4934094579, abs=1e-9)
    assert S.X2[0] / math.pi ** 2 == pytest.approx(2.045749, rel=1e-5)
    assert 1.0 / S.X2[0] == pytest.approx(0.0495279, rel=1e-5)


@pytest.mark.parametrize("k", [0, 1, 4, 17])
def test_modal_weight_reproduced_by_independent_quadrature(k):
    """φₖ=sin(xₖξ)/ξ 的模长、投影、均值三条积分各自积出来，必须闭合到 2/xₖ²。

    第三条（⟨φₖ⟩=0）是「每个衰减模态不搬动总锂」的数学形式：停流后可掉的只有表面−均值。
    """
    x = float(S.XS[k])
    xi = np.linspace(0.0, 1.0, 200_001)
    h = xi[1] - xi[0]
    sin_xi = np.sin(x * xi)
    norm = _trap(sin_xi ** 2, h)                              # ∫ξ²φ² = ∫sin²
    proj = _trap(xi * (xi ** 2 / 2 - 0.3) * sin_xi, h)        # ⟨v, φ⟩
    mean = 3.0 * _trap(xi * sin_xi, h)                        # ⟨φ⟩
    assert norm == pytest.approx(x * x / (2 * (1 + x * x)), rel=1e-8)
    assert proj == pytest.approx(math.cos(x) / x, rel=1e-5)
    assert abs(mean) < 1e-9
    assert proj / norm * math.sin(x) == pytest.approx(S.W[k], rel=1e-5)


def test_weight_sum_is_the_steady_surface_excess():
    """Σ2/xₖ² = 1/5：锚点 4 收敛到锚点 2，两条独立闭式互相钉。"""
    tail = 2.0 / (math.pi ** 2 * (S.N_MODES + 0.5))
    assert S.W.sum() + tail == pytest.approx(0.2, abs=2e-4)


@pytest.mark.parametrize("k", [200, 1000])
def test_series_truncation_error_is_predictable(k):
    """切在第 K 项漏 2/(π²K)，与 t* 几乎无关——参考值自带的尾，不是格式的错。"""
    pred = 2.0 / (math.pi ** 2 * k)
    meas = S.surface_rise(1e-4) - S.trunc_surface(k, 1e-4)
    assert meas == pytest.approx(pred, rel=0.05)


@pytest.mark.parametrize("n", [20, 80, 200])
def test_telescope_identity_is_exact_not_convergent(n):
    """d⟨u⟩/dt* 恰为 3：这是算子的恒等式（精确格体积 + 望远镜求和），与格数无关。"""
    dg, up, lo, src, vol = S.sphere_operator(n, 1.0)
    L = np.diag(dg) + np.diag(up, 1) + np.diag(lo, -1)
    net = float(np.dot(vol, L @ np.linspace(0.1, 1.0, n) + src)) / vol.sum()
    assert net == pytest.approx(3.0, rel=0, abs=1e-10)
    assert vol.sum() == pytest.approx(1.0 / 3.0, rel=0, abs=1e-12)


def test_no_flux_step_conserves_lithium():
    """零通量推进不许动总锂——闭合颗粒的锂没处去，这是 [7] 那条可观测量的物理根据。"""
    u0 = np.linspace(0.0, 1.0, 60) ** 2
    d = S.Diffuser(60, 1e-3, None)
    u = d.advance(u0.copy(), 500)
    assert S.Diffuser.mean(u, d.vol) == pytest.approx(
        S.Diffuser.mean(u0, d.vol), rel=0, abs=1e-12)


def test_thomas_matches_dense_solve():
    """自写三对角 + 整步 CN 装配，必须和 numpy 稠密解一致到机器精度。

    前向消元的乘数用 a_i/B_{i-1} 还是原始 a_i，取决于 x 有没有提前除过主元；混用会留下
    1e-5 的相对误差，单步看不出，几千步硬模态一放大就炸。这一条就是那次的保险。
    """
    n, dt = 12, 2e-4
    dg, up, lo, src, vol = S.sphere_operator(n, 1.0)
    L = np.diag(dg) + np.diag(up, 1) + np.diag(lo, -1)
    u = np.linspace(0.05, 0.95, n)
    rhs = u + 0.5 * dt * (L @ u) + dt * src        # CN：源项整步计，不是半步
    got = S.Diffuser(n, dt, 1.0).advance(u, 1)
    assert got == pytest.approx(np.linalg.solve(np.eye(n) - 0.5 * dt * L, rhs),
                               rel=0, abs=1e-14)


def test_march_marks_agrees_with_single_march():
    """多行共步推进和单行推进必须逐位相同（线性、行间不耦合）。"""
    marks = (5e-3, 2e-2)
    got = S.march_marks(40, marks, dt=5e-4)
    for w in marks:
        u, vol, _ = S.march(40, w, dt=5e-4)
        assert got[w] == pytest.approx(
            S.surface_of(u, 40, 1.0) - S.Diffuser.mean(u, vol), rel=0, abs=1e-15)


def test_march_marks_rejects_off_grid_times():
    """时刻不是 dt 的整数倍就报错：静默 overshoot 会把「读到的时刻」和「要的时刻」读歪。"""
    with pytest.raises(ValueError):
        S.march_marks(40, (1e-1,), dt=3e-4)


def test_surface_of_reads_the_face_not_the_centre():
    """面值 = 格心 + (dξ/2)·通量，这是**定义级**的等式；零通量时不补。"""
    u = np.linspace(0.0, 1.0, 200)
    assert S.surface_of(u, 200, 1.0) - u[-1] == pytest.approx(0.5 / 200, rel=0, abs=1e-15)
    assert S.surface_of(u, 200, None) == u[-1]


def test_steady_shape_matches_two_closed_forms():
    """定常态：表面−均值 → 1/5、中心−均值 → −3/10、均值 → 3t*（三个数各管一段）。"""
    u, vol, _ = S.march(40, 4.0, dt=2e-3)
    cbar = S.Diffuser.mean(u, vol)
    assert S.surface_of(u, 40, 1.0) - cbar == pytest.approx(0.2, abs=3e-3)
    assert u[0] - cbar == pytest.approx(-0.3, abs=8e-3)
    assert cbar == pytest.approx(12.0, rel=0, abs=1e-9)


def test_short_time_is_sqrt_and_origin_slope_diverges():
    """S ~ 2√(t*/π) − 3t*：起点是 √t 不是一次方；S' ~ 1/√(πt*) 发散，越短越陡。"""
    def ratio(w):
        return (S.surface_rise(w) + 3.0 * w) / (2.0 * math.sqrt(w / math.pi))

    r_big, r_small = ratio(1e-4), ratio(1e-6)
    assert abs(r_big - 1.0) < 0.02
    assert abs(r_small - 1.0) < abs(r_big - 1.0)          # 越接近 0 越贴 √t
    assert S.surface_slope(1e-6) * math.sqrt(math.pi * 1e-6) == pytest.approx(1.0, abs=0.01)
    assert S.surface_slope(1e-6) > 3.0 * S.surface_slope(1e-4)

    # 「拟合不上前段」的定量版本：把首条支路缩放到同一个定常态，它在原点的斜率是
    # W₁·x₁²（有限），而扩散是 1/√(πt*)——t* 越小，差距越大，调参救不了。
    one_rc_slope = S.trunc_surface(1, 1e-9) / 1e-9
    assert one_rc_slope == pytest.approx(S.W[0] * S.X2[0], rel=1e-6)
    assert S.surface_slope(1e-9) / one_rc_slope > 200.0


def test_rc_ladder_cannot_reach_the_front():
    """1 阶只到 13.6%、2 阶不到三成；要到 90% 得 20 条以上支路——「前段拟合不上」是结构问题。"""
    exact = S.surface_rise(5e-3)
    assert S.trunc_surface(1, 5e-3) / exact < 0.35
    assert S.trunc_surface(2, 5e-3) / exact < 0.35
    assert S.trunc_surface(16, 5e-3) < S.trunc_surface(17, 5e-3) < exact
    k90 = next(k for k in range(1, 500) if S.trunc_surface(k, 5e-3) > 0.9 * exact)
    assert k90 > 20


def test_relaxation_rate_is_x1_squared():
    """停流弛豫的对数斜率 = x₁²（不是 π²），且首模态只带约一半幅度。"""
    u, vol, _ = S.march(40, 4.0, dt=2e-3)
    s0 = S.surface_of(u, 40, 1.0) - S.Diffuser.mean(u, vol)
    d = S.Diffuser(40, 1e-3, None)
    hist = []
    tacc = 0.0
    for want in (0.4, 0.8):
        u = d.advance(u, int(round((want - tacc) / d.dt)))
        tacc = want
        hist.append((S.surface_of(u, 40, None) - S.Diffuser.mean(u, d.vol)) / s0)
    slope = math.log(hist[0] / hist[1]) / 0.4
    assert slope == pytest.approx(S.X2[0], rel=0.05)
    assert abs(slope / math.pi ** 2 - 1.0) > 0.5
    assert S.W[0] / S.W.sum() == pytest.approx(0.4953, rel=1e-3)


def test_alpha_back_solve_round_trip():
    """射线斜率与常相位指数是同一个数的两张脸：slope=tan(απ/2) ⇔ α=(2/π)arctan(slope)。
    [8] 用这条把「读到的斜率」翻译成「会被当成 CPE 证据的 α」，反解必须自洽。"""
    for alpha in (0.5, 0.45, 0.40, 0.30):
        slope = math.tan(alpha * math.pi / 2)
        assert (2 / math.pi) * math.atan(slope) == pytest.approx(alpha, rel=1e-9)


def test_randles_alpha_half_is_the_svg_formula():
    """α=0.5 时 (jω)^−α 的写法必须逐点精确回到 SVG 注释那行 Zw=σ(1−i)/√ω。

    归一化系数 A=σ√2 不是凑的：(jω)^−1/2=(1−i)/(√2·√w)。[8] 要把「理想扩散」和
    「分数阶扩散」画在同一张图上比，两条曲线必须共轴，否则比的是刻度不是物理。
    """
    for f in (2000.0, 4.58, 0.2658, 0.02, 2e-5):
        w = 2 * math.pi * f
        zw = S.EIS_SIGMA * (1 - 1j) / math.sqrt(w)
        ref = S.EIS_R0 + 1.0 / (1.0 / (S.EIS_RCT + zw) + 1j * w * S.EIS_CDL)
        assert S.randles(f) == pytest.approx(ref, rel=0, abs=1e-15)


def test_animation_beats_are_on_that_curve():
    """图上那四拍的坐标是这条公式画的：用稠密扫描独立反查频率，对拍被测的二分。"""
    fs = np.geomspace(1e-3, 2e3, 200_000)
    re = np.array([S.randles(f).real * 1e3 for f in fs])
    for target, (want_re, want_im) in ((63.94, (63.9, 7.2)), (76.73, (76.7, 17.2))):
        f_dense = fs[int(np.argmin(abs(re - target)))]
        assert S.find_freq_by_re(target) == pytest.approx(f_dense, rel=2e-3)
        z = S.randles(S.find_freq_by_re(target))
        assert z.real * 1e3 == pytest.approx(want_re, abs=0.05)
        assert -z.imag * 1e3 == pytest.approx(want_im, abs=0.1)


def test_semicircle_apex_is_a_local_maximum():
    """半圆顶是局部极大，不是全频段 −Im 的最大值——后者在最低频那一拍，是尾巴。

    上一版本仓库的核对脚本就踩过这个：把尾巴末端当圆顶。Warburg 还会把圆顶往
    低频推、把虚部抬高，所以「1/(2πRC)」和「Rct/2」只是纯 RC 的近似。
    """
    f_leave = S.find_freq_by_re(63.94)
    apex = max(np.geomspace(2000.0, f_leave, 20_000), key=lambda f: -S.randles(f).imag)
    assert apex == pytest.approx(4.6, rel=0.02)
    assert -S.randles(apex).imag * 1e3 == pytest.approx(20.6, abs=0.2)
    assert apex < 1 / (2 * math.pi * S.EIS_RCT * S.EIS_CDL)
    assert -S.randles(apex).imag * 1e3 > S.EIS_RCT / 2 * 1e3


def test_tail_slope_is_a_window_read_not_a_component():
    """同一条理想扩散曲线，只改扫描下沿：斜率单调升、始终不到 1、千倍窗后 >0.99。

    这钉住 [8] 的核心断言——「0.94」既不是元件值也不是新物理，是窗口读数。
    """
    f_leave, f_end = S.find_freq_by_re(63.94), S.find_freq_by_re(76.73)
    series = [S.tail_slope(f_leave, f_end / m) for m in (1, 3, 10, 30, 100, 300, 1000)]
    assert all(a < b < 1.0 for a, b in zip(series[:-1], series[1:], strict=True))
    assert series[0] == pytest.approx(0.782, abs=0.01)
    assert series[2] == pytest.approx(0.937, abs=0.01)
    assert series[-1] > 0.99
    fake_alpha = (2 / math.pi) * math.atan(series[0])
    assert 0.40 < fake_alpha < 0.45       # 图那段窗会「测」出 α≈0.42 的假 CPE


def test_fractional_branch_caps_below_one():
    """真 α≠0.5 的签名是封顶：宽窗下斜率停在 tan(απ/2)，回不到 1，也和理想扩散分得开。"""
    f_leave, f_end = S.find_freq_by_re(63.94), S.find_freq_by_re(76.73)
    asymptote = math.tan(0.45 * math.pi / 2)
    capped = S.tail_slope(f_leave, f_end / 1000, alpha=0.45)
    assert capped == pytest.approx(asymptote, rel=0.02)
    assert capped < 0.9
    assert S.tail_slope(f_leave, f_end / 1000) - capped > 0.1


def test_cli_exit_code_contract():
    """脚本 docstring 承诺：18 项自验收全过退出码 0。文档页引用的每个数都出自这份打印。"""
    assert S.main() == 0
