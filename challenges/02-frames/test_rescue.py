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


def test_grade_penalizes_frames_not_planted() -> None:
    """多收一帧扣一分：grade() 的误收路径在固定流上从不触发，这里直接喂数据。"""
    stream, planted = _score.build_stream()
    del stream
    extra = _score._good(99)
    report = _score.grade([*planted, extra], planted)
    assert report["planted"] == 10
    assert report["recovered"] == 10
    assert report["false_accepts"] == 1
    assert report["score"] == 9


def test_grade_counts_duplicate_frame_as_false_accept() -> None:
    """同一帧交两份：第二份不在 remaining 里，按误收扣分。"""
    _stream, planted = _score.build_stream()
    report = _score.grade([*planted, planted[0]], planted)
    assert report["recovered"] == 10
    assert report["false_accepts"] == 1
    assert report["score"] == 9
