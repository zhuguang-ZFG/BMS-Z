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
    c = drive_cycle(16000, 1.0)
    assert np.any(c < -1.9), "应包含放电段"
    assert np.any(np.abs(c) < 1e-9), "应包含静置段"
    assert np.any(c > 3.9), "应包含 CC 充电段"
    assert np.any((c > 0.0) & (c < 0.5)), "应包含 CV 电流衰减段（校准点）"


def test_coulomb_estimators_clamp_soc():
    """SOC 约定 [0, 1]：积分器不得漂出边界。"""
    hi = CoulombOnly(0.99, 1.0)
    assert hi.step(10.0, 4.2, 3600.0) == 1.0
    lo = CoulombWithResets(0.01, 1.0)
    assert lo.step(-10.0, 3.0, 3600.0) == 0.0
