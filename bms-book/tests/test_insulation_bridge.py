"""Reader-facing parameter edits for the chapter 32 insulation demo."""
from contextlib import redirect_stdout
import importlib.util
from io import StringIO
from pathlib import Path
import sys

DEMO = Path(__file__).resolve().parents[1] / "code" / "insulation_bridge.py"


def run_demo(**overrides):
    spec = importlib.util.spec_from_file_location("insulation_bridge", DEMO)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    for name, value in overrides.items():
        setattr(module, name, value)
    if "U" in overrides:
        # Editing the source constant also re-evaluates this derived constant.
        module.__dict__["U_HALF"] = module.__dict__["U"] / 2.0
    output = StringIO()
    with redirect_stdout(output):
        exit_code = module.main()
    return exit_code, output.getvalue()


def test_default_output_keeps_the_published_reference_numbers():
    exit_code, output = run_demo()

    assert exit_code == 0
    assert "U = 400 V, Rb = 100 kohm" in output
    assert "40 kohm (100 ohm/V), C_Y = 1.0 uF" in output
    assert "recommended wait before the 2nd measurement: >= 0.50 s" in output
    assert "[PASS] 11/11 checks" in output


def test_halving_bridge_resistance_recomputes_the_wait_gate():
    exit_code, output = run_demo(RB=50e3)

    assert exit_code == 0
    assert "Rb = 50 kohm" in output
    assert "recommended wait before the 2nd measurement: >= 0.25 s" in output
    assert "[PASS] 11/11 checks" in output


def test_larger_y_capacitance_is_reported_and_waits_five_seconds():
    exit_code, output = run_demo(C_Y=10e-6)

    assert exit_code == 0
    assert "C_Y = 10.0 uF" in output
    assert "recommended wait before the 2nd measurement: >= 5.00 s" in output
    assert "[PASS] 11/11 checks" in output


def test_changing_fault_threshold_changes_the_case_b_verdict():
    exit_code, output = run_demo(R_FAULT=15e3)

    assert exit_code == 0
    assert "fault threshold min(R+, R-) <= 15 kohm" in output
    case_b = output.split("case B 40kohm", 1)[1].split("case C symmetric", 1)[0]
    assert "-> NORMAL" in case_b
    assert "[PASS] 11/11 checks" in output


def test_changing_pack_voltage_reports_the_actual_ohms_per_volt():
    exit_code, output = run_demo(U=800.0)

    assert exit_code == 0
    assert "U = 800 V" in output
    assert "40 kohm (50 ohm/V)" in output
    assert "[PASS] 11/11 checks" in output
