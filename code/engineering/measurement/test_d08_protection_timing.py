"""D08 reaction windows, blind windows, hysteresis, and feedback timeout."""
import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d08_protection_timing", HERE / "d08_protection_timing.py"
)
assert spec is not None and spec.loader is not None
d08 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d08
spec.loader.exec_module(d08)


def test_reaction_window_scales_with_fault_phase():
    best = d08.reaction_window_ms(0.0)
    worst = d08.reaction_window_ms(d08.SCAN_MS)
    typical = d08.reaction_window_ms(5.0)
    assert best["total_ms"] == pytest.approx(62.0)
    assert typical["total_ms"] == pytest.approx(67.0)
    assert worst["total_ms"] == pytest.approx(72.263)
    assert worst["total_ms"] - best["total_ms"] == pytest.approx(d08.SCAN_MS, rel=1e-4)
    with pytest.raises(ValueError):
        d08.reaction_window_ms(d08.SCAN_MS + 1.0)


def test_confirm_window_suppresses_glitch_but_blinds_short_faults():
    g = d08.glitch_vs_fault()
    assert g["confirm_window_ms"] == pytest.approx(40.0)
    assert g["blind_window_ms"] == pytest.approx(60.0)
    assert g["glitch_survives"] is False, "8 ms 毛刺必须被抑制"
    assert g["real_fault_detected"] is False, "25 ms 真实故障同样漏检——盲区是同一个窗的另一面"


def test_hysteresis_turns_chatter_into_one_latch():
    h = d08.hysteresis_chatter()
    assert h["threshold_a"] == pytest.approx(50.0)
    assert h["release_a"] == pytest.approx(45.0)
    assert h["actions_without_hysteresis"] == pytest.approx(12)
    assert h["actions_with_hysteresis"] == pytest.approx(1)


def test_feedback_timeout_is_a_fault():
    assert d08.feedback_timeout(100.0, 112.0)["within_window"] is True
    late = d08.feedback_timeout(100.0, 125.0)
    assert late["within_window"] is False
    assert "锁存" in late["verdict"]
    never = d08.feedback_timeout(100.0, None)
    assert never["within_window"] is False
    with pytest.raises(ValueError):
        d08.feedback_timeout(-1.0, 0.0)


def test_report_extends_s1_frozen_budget():
    report = d08.build_report()
    assert report["window_worst_ms"] == pytest.approx(72.263)
    assert "10.26337" in report["identity"]
    assert report["feedback"]["never"]["within_window"] is False
