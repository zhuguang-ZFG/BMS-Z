"""D05 MUX settling, scan conflict, and in-range open-wire counterexamples."""
import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d05_mux_settling", HERE / "d05_mux_settling.py"
)
assert spec is not None and spec.loader is not None
d05 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d05
spec.loader.exec_module(d05)


def test_settling_time_for_12bit():
    t = d05.settling_time_s()
    # ln(5 / (5/4096/2)) = ln(8192) ≈ 9.0109 → 901.09 µs @ τ=100 µs
    assert t == pytest.approx(d05.TAU_S * 9.0109, rel=1e-3)
    assert t * 1e6 == pytest.approx(901.09, abs=0.5)
    assert d05.lsb_mv() == pytest.approx(5.0 / 4096 * 1000, rel=1e-4)
    with pytest.raises(ValueError):
        d05.settling_time_s(bits=0)


def test_scan_exceeds_10ms_task():
    scan = d05.scan_time_s()
    assert scan * 1000 == pytest.approx(14.73746, abs=1e-3)
    assert scan * 1000 - 10.0 == pytest.approx(4.73746, abs=1e-3)
    with pytest.raises(ValueError):
        d05.scan_time_s(channels=0)


def test_open_wire_holds_last_valid_value_in_range():
    ow = d05.open_wire_trace()
    assert ow["stuck_v"] == pytest.approx(3.280)
    assert 0.0 < ow["stuck_v"] < 5.0, "开线读数必须量程内（不是 0 V）"


def test_rest_makes_delta_and_plausibility_blind():
    ow = d05.open_wire_trace()
    assert ow["rest"]["delta_trips"] is False, "静置时卡值窗不能触发"
    pack_avg = sum(ow["rest"]["cell_trace_v"]) / len(ow["rest"]["cell_trace_v"])
    assert abs(ow["stuck_v"] - pack_avg) * 1000 < ow["delta_window_mv"], "静置时对均值也不可区分"


def test_drift_accidentally_saves_the_window_detector():
    ow = d05.open_wire_trace()
    assert ow["drift"]["delta_trips"] is True, "漂移拉大差值后卡值窗才触发——是碰巧不是设计"


def test_active_audit_catches_open_wire_regardless_of_rest():
    ow = d05.open_wire_trace()
    assert ow["audit"]["caught"] is True
    assert ow["audit"]["response_mv"] == pytest.approx(0.0)
    assert ow["audit"]["injected_bias_mv"] == pytest.approx(5.0)


def test_report_identity_marks_src02_pending():
    report = d05.build_report()
    assert report["scenario_id"] == d05.SCENARIO_ID
    assert "SRC02" in report["identity"] and "no hardware delay is invented" in report["identity"]
