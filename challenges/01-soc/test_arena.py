"""擂台基线必须能复现。数字变了，就先改文档里的榜单，再改这里。"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "arena_soc_score", Path(__file__).resolve().with_name("score.py")
)
_score = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_score)
BASELINE_NAME = _score.BASELINE_NAME
baseline_table = _score.baseline_table

# 2026-10-06，numpy 2.5.1，种子 20261006，5000 步。仿真结果。
EXPECTED = {
    "纯安时积分": 0.10113652313678695,
    "积分+校准点": 0.07575092473403168,
    "Thevenin+EKF": 0.0020473998238032132,
}


def test_soc_baseline_matches_recorded_run() -> None:
    table = baseline_table()
    assert set(table) == set(EXPECTED)
    for name, value in EXPECTED.items():
        assert table[name] == value
    assert table[BASELINE_NAME] > table["Thevenin+EKF"]
