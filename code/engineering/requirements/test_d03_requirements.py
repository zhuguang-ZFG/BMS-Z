"""D03 weakest-cell counterexample and requirements completeness checks."""
import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d03_requirements", HERE / "d03_requirements.py"
)
assert spec is not None and spec.loader is not None
d03 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d03
spec.loader.exec_module(d03)


def test_frozen_pack_average_passes_but_weakest_cell_violates():
    check = d03.discharge_check(d03.FROZEN_CELLS_V)
    assert check["average_passes"] is True
    assert check["weakest_passes"] is False
    assert check["violating_cells"] == [15]
    assert check["weakest_v"] == pytest.approx(3.28)
    assert check["average_v"] == pytest.approx(3.3687, abs=1e-4)
    assert "最弱单节" in check["conclusion"]


def test_spread_is_reported_in_mv():
    summary = d03.pack_summary(d03.FROZEN_CELLS_V)
    assert summary["spread_mv"] == pytest.approx(120.0)


def test_empty_pack_is_rejected():
    with pytest.raises(ValueError):
        d03.pack_summary([])


def test_every_spec_field_is_required_and_placeholders_fail():
    full = {field: "quantified" for field in d03.REQUIRED_SPEC_FIELDS}
    assert d03.missing_spec_fields(full) == []
    full["lifetime_target"] = "  "
    assert d03.missing_spec_fields(full) == ["lifetime_target"]
    assert "consistency_requirement" in d03.missing_spec_fields({"chemistry": "LFP"})


def test_responsibility_split_names_three_owners_with_one_rule():
    split = d03.responsibility_split()
    for key in ("measurement", "estimation", "protection", "rule"):
        assert key in split and split[key]
    assert "S1" in split["measurement"] and "S2" in split["estimation"] and "S3" in split["protection"]


def test_report_identity_marks_synthetic():
    report = d03.build_report()
    assert report["scenario_id"] == d03.SCENARIO_ID
    assert "not a measured pack" in report["identity"]
