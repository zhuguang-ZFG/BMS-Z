"""D07 back-to-back MOSFET paths, SOA reading, and drive faults."""

import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d07_mos_path", HERE / "d07_mos_path.py")
assert spec is not None and spec.loader is not None
d07 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d07
spec.loader.exec_module(d07)


def test_single_mos_leaks_through_body_diode_either_way():
    for forbidden in (True, False):
        result = d07.single_mos_blocks(charge_forbidden=forbidden)
        assert result["body_diode_leaks"] is True
        assert "背靠背" in result["conclusion"]


def test_body_diode_conduction_pays_35x_rdson_at_10a():
    ratio = d07.back_to_back_loss_ratio(10.0)
    assert ratio["body_diode_w"] == pytest.approx(7.0)
    assert ratio["rds_on_w"] == pytest.approx(0.2)
    assert ratio["ratio_diode_over_rdson"] == pytest.approx(35.0)
    assert ratio["hot_rds_on_w"] == pytest.approx(0.3)


def test_rdson_temp_coefficient_matters_at_40a():
    ratio = d07.back_to_back_loss_ratio(40.0)
    assert ratio["rds_on_w"] == pytest.approx(3.2)
    assert ratio["hot_rds_on_w"] == pytest.approx(4.8)
    with pytest.raises(ValueError):
        d07.conduction_loss_w(-1.0)


def test_soa_reading_by_pulse_width():
    assert d07.soa_check(20.0, 60.0, 0.01)["within_soa"] is True
    outside = d07.soa_check(20.0, 60.0, 0.1)
    assert outside["within_soa"] is False
    assert outside["row_key"] == "100ms"
    assert "15 A" in outside["conclusion"]
    assert d07.soa_check(8.0, 60.0, 30.0)["within_soa"] is True
    with pytest.raises(ValueError):
        d07.soa_check(1.0, 0.0, 0.01)


def test_avalanche_energy_is_half_li_squared():
    a = d07.avalanche_energy_mj(20.0)
    assert a["energy_mj"] == pytest.approx(2.0)
    assert a["within_rating"] is True
    assert d07.avalanche_energy_mj(40.0)["within_rating"] is False


def test_drive_fault_modes_listed_with_guards():
    faults = d07.drive_fault_modes()
    modes = {m["mode"] for m in faults["modes"]}
    assert modes == {"栅极悬空", "驱动电阻过大", "负压关断缺失"}
    assert all(m["guard"] for m in faults["modes"])


def test_report_marks_synthetic_soa():
    report = d07.build_report()
    assert "synthetic" in report["identity"] and "SRC03" in report["identity"]
