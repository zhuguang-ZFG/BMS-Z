"""Reader-visible contracts for the chapter 11 CC-CV parameter experiments."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "code"


def load():
    name = "cccv_charge"
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_main(module):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        status = module.main()
    return status, output.getvalue()


def test_default_demo_keeps_published_values():
    module = load()
    status, output = run_main(module)

    assert status == 0
    assert "48 min" in output
    assert "29 min" in output
    assert "SOC 才到 0.80" in output
    assert output.count("[PASS]") == 12
    assert "[FAIL]" not in output


@pytest.mark.parametrize(
    ("attribute", "value", "expected"),
    [
        ("R0", 0.100, ("39 min", "51 min", "SOC 才到 0.66")),
        ("I_CUT", 0.20, ("截止 0.20 A（0.10C）", "22 min")),
        ("I_CC", 0.40, ("CC 段 0.4 A（0.2C）", "截止 0.10 A（0.05C）")),
    ],
)
def test_edited_parameter_demo_reports_current_case_and_passes(attribute, value, expected):
    module = load()
    setattr(module, attribute, value)

    status, output = run_main(module)

    assert status == 0
    assert output.count("[PASS]") == 12
    assert "[FAIL]" not in output
    for text in expected:
        assert text in output


def test_short_horizon_does_not_report_a_fake_cv_transition():
    module = load()

    result = module.simulate_cccv(t_max_s=1.0)

    assert result["t_sw_s"] == 1.0
    assert result["switched"] is False
    assert result["completed"] is False


def test_unreachable_voltage_limit_fails_without_claiming_a_transition():
    module = load()
    attribute = "I_CC"
    setattr(module, attribute, 0.0)

    status, output = run_main(module)

    assert status == 1
    assert "不能把仿真上限当作转恒压时刻" in output
    assert "120 min 内未到 4.20 V" in output
    assert "[E2 恒压段]" not in output
    assert "[FAIL] 事件完整" in output
