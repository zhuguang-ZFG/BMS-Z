"""D06 first-order return-path estimates and their reading discipline."""
import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d06_return_path", HERE / "d06_return_path.py"
)
assert spec is not None and spec.loader is not None
d06 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d06
spec.loader.exec_module(d06)


def test_ground_bounce_scales_with_l_di_dt():
    assert d06.ground_bounce_mv() == pytest.approx(2000.0)
    assert d06.ground_bounce_mv(di_a=10.0) == pytest.approx(1000.0)
    assert d06.ground_bounce_mv(loop_l_h=50e-9) == pytest.approx(1000.0)
    with pytest.raises(ValueError):
        d06.ground_bounce_mv(dt_s=0.0)


def test_kelvin_error_dominates_at_shunt_scale():
    assert d06.kelvin_error_pct() == pytest.approx(97.09, abs=0.01)
    assert d06.kelvin_error_mv() == pytest.approx(1000.0)
    # 四线读法：引线不进测量回路 → 只剩分流器本身
    assert d06.kelvin_error_pct(lead_ohm=0.0) == pytest.approx(0.0)
    with pytest.raises(ValueError):
        d06.kelvin_error_pct(shunt_ohm=0.0)


def test_capacitive_injection_is_hundreds_of_ma():
    assert d06.capacitive_injection_ua() == pytest.approx(0.1 * 1e6, rel=1e-6)
    assert d06.capacitive_injection_ua(couple_c_f=5e-12) == pytest.approx(50_000.0, rel=1e-6)
    with pytest.raises(ValueError):
        d06.capacitive_injection_ua(dv_dt_v_per_s=-1.0)


def test_report_marks_simulation_is_not_emc_test():
    report = d06.build_report()
    assert report["scenario_id"] == d06.SCENARIO_ID
    assert "not an EMC test" in report["identity"]
    assert len(report["reading"]) == 3
    assert "模拟不冒充" in report["conclusion"]
