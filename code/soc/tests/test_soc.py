"""SOC 估算器测试。运行：cd code/soc && python3 -m pytest tests/ -q"""
import numpy as np

from cell_model import TheveninCell, ocv, docv_dsoc, drive_cycle
from estimators import CoulombOnly, CoulombWithResets, EKFEstimator
import compare


def test_ocv_monotonic_and_bounded():
    s = np.linspace(0.0, 1.0, 1001)
    v = np.array([ocv(x) for x in s])
    assert np.all(np.diff(v) > 0), "OCV 必须单调递增"
    assert 2.9 < v[0] < 3.1, f"SOC=0 时 OCV={v[0]:.3f} 应在 3.0V 附近"
    assert 4.1 < v[-1] < 4.3, f"SOC=1 时 OCV={v[-1]:.3f} 应在 4.2V 附近"
    assert np.all(docv_dsoc(s) > 0)


def test_cell_coulomb_consistency():
    """恒流放电工况：模型自身 SOC 变化应严格等于 I*t/Q。"""
    cell = TheveninCell(10.0, 0.02, 0.015, 3000.0, soc0=0.8)
    for _ in range(3600):            # 0.1C（-1A）放电 1 小时 → SOC 应掉 0.1
        cell.step(-1.0, 1.0)
    assert abs(cell.soc - 0.7) < 1e-9


def test_coulomb_perfect_sensor_is_accurate():
    """无零漂、容量正确时，纯安时积分没有漂移的理由。"""
    rng = np.random.default_rng(0)
    cell = TheveninCell(10.0, 0.02, 0.015, 3000.0, soc0=0.8)
    est = CoulombOnly(0.8, 10.0)
    for _ in range(7200):            # -2A 放 2 小时 = -4Ah，0.8→0.4，不触底
        i = -2.0 + rng.normal(0, 0.2)
        v = cell.step(i, 1.0)
        s = est.step(i, v, 1.0)
    assert abs(s - cell.soc) < 0.005


def test_coulomb_drifts_with_offset():
    """教程 §4.2 的核心结论：零漂让纯积分误差随时间持续累积。"""
    cell = TheveninCell(10.0, 0.02, 0.015, 3000.0, soc0=0.8)
    est = CoulombOnly(0.8, 10.0)
    err_half = err_full = None
    for k in range(36000):           # -0.5A 放 10 小时 = -5Ah，0.8→0.3
        v = cell.step(-0.5, 1.0)
        s = est.step(-0.5 + 0.010, v, 1.0)   # +10mA 零漂
        if k == 17999:
            err_half = s - cell.soc
        err_full = s - cell.soc
    # 10mA × 10h = 100mAh ≈ 10Ah 电池的 1%
    assert err_full > 0.005, "10mA 零漂 10 小时应漂出约 1% 误差"
    assert err_full > 1.5 * err_half, "漂移应随时间近似线性增长（不收敛）"


def test_ekf_beats_coulomb_on_faulty_inputs():
    """阶段 4 的验收线之一：有零漂+容量误差时 EKF 明显优于纯积分。"""
    soc_true, soc_est = compare.run()
    rmse = {
        name: float(np.sqrt(np.mean((est - soc_true) ** 2)))
        for name, est in soc_est.items()
    }
    assert rmse["Thevenin+EKF"] < rmse["纯安时积分"] * 0.6, (
        f"EKF RMSE {rmse['Thevenin+EKF']:.4f} 应显著小于纯积分 "
        f"{rmse['纯安时积分']:.4f}"
    )
    assert rmse["Thevenin+EKF"] < 0.05, "教程验收线：误差 <5%"


def test_reset_estimator_recovers_at_full_charge():
    """满充校准：CV 截止时 SOC 应被拉回 1.0 附近，清掉此前累积的漂移。"""
    soc_true, soc_est = compare.run()
    tail = soc_est["积分+校准点"][-200:]       # 工况结尾是 CV 电流衰减段
    assert tail[-1] > 0.97, "充电末端应触发满充校准"
    assert abs(tail[-1] - soc_true[-1]) < 0.05


def test_reset_estimator_beats_plain_coulomb():
    """阶段 4 主线结论：校准点必须优于纯积分。

    回归：旧工况 CC 截止偏早（真值末端 0.984，从未真满），满充锚点在真值
    0.975 处提前复位到 1.0 注入误差；叠加初始 SOC 给真值、零漂仅 2mA
    （4.4h 只积 0.09%），纯积分无错可修——校准版 RMSE 反而更高，与教程
    矛盾。修复后工况末端真触顶、估算器初始 SOC 错 -10 个百分点。 """
    soc_true, soc_est = compare.run()
    rmse = {
        name: float(np.sqrt(np.mean((est - soc_true) ** 2)))
        for name, est in soc_est.items()
    }
    assert rmse["积分+校准点"] < rmse["纯安时积分"], (
        f"校准版 RMSE {rmse['积分+校准点']:.4f} 应小于纯积分 "
        f"{rmse['纯安时积分']:.4f}——锚点必须起效"
    )
    # 满充锚点语义：末端真值必须真的到达 1.0（否则"CV 截止→必满"不成立）
    assert soc_true[-1] >= 0.999, f"工况末端真值应触顶，实际 {soc_true[-1]:.4f}"


def test_rest_anchor_collapses_initial_error():
    """锚点起效的直接证据：上电静置窗口（900s）一结束，校准版的初始
    SOC 误差必须已塌缩；纯积分没有任何机制，只能继续带着它漂。"""
    soc_true, soc_est = compare.run()
    k = 1000                      # 上电静置段（0–1800s）内，rest 锚点已触发
    cal_err = abs(soc_est["积分+校准点"][k] - soc_true[k])
    plain_err = abs(soc_est["纯安时积分"][k] - soc_true[k])
    assert cal_err < 0.02, f"rest 锚点后校准版误差应 <2%，实际 {cal_err:.3f}"
    assert plain_err > 0.05, f"纯积分应仍带初始误差 >5%，实际 {plain_err:.3f}"


def test_rest_anchor_tolerates_current_noise():
    """双向去抖计时：20mA 噪声下单拍超限不清零，静置锚点仍能触发。
    回归：清零式计时在噪声下触发概率 ≈ 0.988^900 ≈ 0。"""
    from cell_model import ocv
    est = CoulombWithResets(0.50, 10.0)
    rng = np.random.default_rng(0)
    for _ in range(1000):                 # 零电流 + σ=20mA 噪声静置
        est.step(rng.normal(0.0, 0.02), ocv(0.62), 1.0)
    assert abs(est.soc - 0.62) < 0.02, f"静置锚点应把 SOC 锚到 0.62，实际 {est.soc:.3f}"


def test_full_anchor_fires_only_at_cv_cutoff():
    """满充锚点只认"电压高位 + 衰减中的充电电流"：CV 截止才复位 1.0；
    电流为零（非充电）或仍是 CC 大电流都不得触发。"""
    est = CoulombWithResets(0.90, 10.0)
    assert est.step(0.3, 4.20, 1.0) == 1.0          # 0<0.3A<0.5A 截止, 4.20>4.15
    est = CoulombWithResets(0.90, 10.0)
    assert est.step(0.0, 4.20, 1.0) != 1.0          # 无充电电流 → 不触发
    est = CoulombWithResets(0.90, 10.0)
    assert est.step(4.0, 4.20, 1.0) != 1.0          # CC 大电流 → 不触发


def test_ekf_converges_from_wrong_initial_soc():
    """初始 SOC 给错 20 个百分点，EKF 应靠电压观测收敛回去。"""
    cell = TheveninCell(10.0, 0.02, 0.015, 3000.0, soc0=0.6)
    est = EKFEstimator(0.8, 10.0, 0.02, 0.015, 3000.0)   # 初始 SOC 错 +0.2
    rng = np.random.default_rng(7)
    for _ in range(3600):            # -2A 放 1 小时，0.6→0.4，不触底
        i = -2.0
        v = cell.step(i, 1.0)
        est.step(i + rng.normal(0, 0.01), v + rng.normal(0, 0.005), 1.0)
    assert abs(est.x[0] - cell.soc) < 0.05, "1 小时内应收敛到 5% 以内"


def test_drive_cycle_has_rest_and_charge_phases():
    c = drive_cycle(17000, 1.0)
    assert np.any(c < -1.9), "应包含放电段"
    assert np.any(np.abs(c) < 1e-9), "应包含静置段（上电静置 + 中段静置）"
    assert np.any(c > 3.9), "应包含 CC 充电段"
    assert np.any((c > 0.0) & (c < 0.5)), "应包含 CV 电流衰减段（校准点）"


def test_coulomb_estimators_clamp_soc():
    """SOC 约定 [0, 1]：积分器不得漂出边界。"""
    hi = CoulombOnly(0.99, 1.0)
    assert hi.step(10.0, 4.2, 3600.0) == 1.0
    lo = CoulombWithResets(0.01, 1.0)
    assert lo.step(-10.0, 3.0, 3600.0) == 0.0


def test_comparison_samples_truth_and_estimates_at_same_time(monkeypatch):
    """无噪声时，真值和纯积分只差已知初值，不能多出一拍电流的误差。"""
    currents = np.array([-2.0, 4.0, 0.0, -1.0])
    monkeypatch.setattr(compare, "N_STEPS", len(currents))
    monkeypatch.setattr(compare, "DT_S", 30.0)
    monkeypatch.setattr(compare, "Q_ASSUMED_AH", compare.Q_TRUE_AH)
    for name in ("I_OFFSET_A", "I_NOISE_A", "V_NOISE_V"):
        monkeypatch.setattr(compare, name, 0.0)
    monkeypatch.setattr(compare, "drive_cycle", lambda *_: currents)
    truth, estimates = compare.run()
    delta = np.cumsum(currents) * compare.DT_S / 3600.0 / compare.Q_TRUE_AH
    np.testing.assert_allclose(truth, 0.8 + delta, rtol=0, atol=1e-12)
    np.testing.assert_allclose(estimates["纯安时积分"] - truth, -0.1, rtol=0, atol=1e-12)
