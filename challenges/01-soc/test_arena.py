"""擂台基线必须能复现。数字变了，就先改文档里的榜单，再改这里。"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "arena_soc_score", Path(__file__).resolve().with_name("score.py")
)
_score = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_score)
BASELINE_NAME = _score.BASELINE_NAME
REFERENCE_NAME = _score.REFERENCE_NAME
baseline_table = _score.baseline_table
noisy_table = _score.noisy_table
tier_name = _score.tier_name
score_estimator = _score.score_estimator
TIER_EKF = _score.TIER_EKF
TIER_BASELINE = _score.TIER_BASELINE
TIER_NONE = _score.TIER_NONE

# 2026-10-06，种子 20261006，5000 步。钉住的是这条序列的 RMSE。
# 不同平台 / numpy 的舍入可能差最后一位，比较用 rel=1e-9、abs=1e-12。
EXPECTED = {
    "纯安时积分": 0.10113652313678695,
    "积分+校准点": 0.07575092473403168,
    "Thevenin+EKF": 0.0020473998238032132,
}
# 更吵档：同一条电流，噪声种子 20261102，电流 0.08 A，电压 0.020 V。
# 积分+校准点与纯安时相同：噪声让静置锚点和满充锚点都没触发。
EXPECTED_NOISY = {
    "纯安时积分": 0.10118287272800866,
    "积分+校准点": 0.10118287272800866,
    "Thevenin+EKF": 0.007979331151068879,
}


def test_soc_baseline_matches_recorded_run() -> None:
    table = baseline_table()
    assert set(table) == set(EXPECTED)
    for name, value in EXPECTED.items():
        assert table[name] == pytest.approx(value, rel=1e-9, abs=1e-12)
    assert table[BASELINE_NAME] > table[REFERENCE_NAME]


def test_noisy_thresholds_come_from_the_scorer() -> None:
    table = noisy_table()
    assert set(table) == set(EXPECTED_NOISY)
    for name, value in EXPECTED_NOISY.items():
        assert table[name] == pytest.approx(value, rel=1e-9, abs=1e-12)
    assert table[BASELINE_NAME] > table[REFERENCE_NAME]


def test_tier_names_use_strict_less_than() -> None:
    baseline = EXPECTED[BASELINE_NAME]
    reference = EXPECTED[REFERENCE_NAME]
    assert tier_name(baseline, baseline, reference) == TIER_NONE
    assert tier_name(reference, baseline, reference) == TIER_BASELINE
    assert tier_name((baseline + reference) / 2, baseline, reference) == TIER_BASELINE
    assert tier_name(reference * 0.5, baseline, reference) == TIER_EKF


def test_plugin_template_ties_the_baseline() -> None:
    plugin = Path(__file__).resolve().with_name("my_estimator.py")
    scored = score_estimator(f"{plugin}:MyEstimator")
    assert scored["public"]["rmse"] == pytest.approx(
        EXPECTED[BASELINE_NAME], rel=1e-9, abs=1e-12
    )
    assert scored["public"]["tier"] == TIER_NONE
    assert scored["noisy"]["rmse"] == pytest.approx(
        EXPECTED_NOISY[BASELINE_NAME], rel=1e-9, abs=1e-12
    )
    assert scored["noisy"]["tier"] == TIER_NONE
    assert scored["public"]["baseline"] == pytest.approx(
        EXPECTED[BASELINE_NAME], rel=1e-9, abs=1e-12
    )
    assert scored["public"]["reference"] == pytest.approx(
        EXPECTED[REFERENCE_NAME], rel=1e-9, abs=1e-12
    )


def test_plugin_path_can_beat_repo_ekf(tmp_path: Path) -> None:
    """用题面里公开的模型容量和起点，应当严格小于仓库那份带错容量的 EKF。"""
    code_soc = Path(__file__).resolve().parents[2] / "code" / "soc"
    plugin = tmp_path / "tuned_ekf.py"
    plugin.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(code_soc)!r})\n"
        "from estimators import EKFEstimator\n"
        "class TunedEKF:\n"
        "    def __init__(self):\n"
        "        self.inner = EKFEstimator(0.80, 10.0, 0.020, 0.015, 3000.0)\n"
        "    def step(self, current_a, v_meas, dt_s):\n"
        "        return self.inner.step(float(current_a), float(v_meas), float(dt_s))\n",
        encoding="utf-8",
    )
    scored = score_estimator(f"{plugin}:TunedEKF")
    assert scored["public"]["rmse"] < EXPECTED[REFERENCE_NAME]
    assert scored["public"]["tier"] == TIER_EKF
    assert scored["noisy"]["rmse"] < EXPECTED_NOISY[REFERENCE_NAME]
    assert scored["noisy"]["tier"] == TIER_EKF


def test_estimator_spec_needs_a_class_name() -> None:
    try:
        _score.load_estimator_class("my_estimator.py")
    except ValueError:
        return
    raise AssertionError("缺少类名时应当拒绝")
