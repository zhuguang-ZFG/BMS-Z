"""Visible state transitions in the illustrative protection animation.

These examples describe the drawing, not acceptance of product firmware.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from gen_handraw_control_pair import protection_state  # noqa: E402


def test_short_spike_has_cleared_before_the_reset_frame():
    during = protection_state(14.0)
    assert during.elapsed == 3.0
    assert during.closed
    after = protection_state(16.5)
    assert after.voltage < 4.25
    assert after.elapsed == 0.0
    assert after.closed
    assert after.tripped_at is None


def test_full_window_trips_but_does_not_act_early():
    before = protection_state(39.5)
    assert before.elapsed == 19.5
    assert before.closed
    assert before.tripped_at is None
    at = protection_state(40.0)
    assert at.elapsed == 20.0
    assert not at.closed
    assert at.tripped_at == 40.0


def test_cleared_timer_does_not_bypass_hysteresis():
    band = protection_state(46.0)
    assert 4.15 < band.voltage < 4.25
    assert band.elapsed == 0.0
    assert not band.closed
    assert band.tripped_at == 40.0
    recovered = protection_state(48.0)
    assert recovered.voltage < 4.15
    assert recovered.elapsed == 0.0
    assert recovered.closed
