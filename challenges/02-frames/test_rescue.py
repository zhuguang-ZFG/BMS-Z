"""坏字节流这题的基线也必须能复现。"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "arena_frame_score", Path(__file__).resolve().with_name("score.py")
)
_score = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_score)
BASELINE_NAME = _score.BASELINE_NAME
baseline_report = _score.baseline_report


def test_frame_baseline_matches_recorded_run() -> None:
    report = baseline_report()
    assert report[BASELINE_NAME] == {
        "planted": 10,
        "recovered": 4,
        "false_accepts": 0,
        "score": 4,
    }
    assert report["仓库解析器"] == {
        "planted": 10,
        "recovered": 10,
        "false_accepts": 0,
        "score": 10,
    }
    assert report["仓库解析器"]["score"] > report[BASELINE_NAME]["score"]
