"""Independent integration checks for the exact teaching thermal solution."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('engineering_ledger', Path(__file__).resolve().parents[1] / 'code/engineering_ledger.py')
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


@pytest.mark.parametrize('horizon', [10, 120, 600])
def test_exact_temperature_matches_numerical_energy_balance(horizon):
    temperature = 25.0
    step = 0.01
    for _ in range(round(horizon / step)):
        temperature += step * (10 ** 2 * 0.049 - (temperature - 25) / 1) / 120
    exact = ledger.thermal_step(10, 0.049, 1, 120, 25, 25, horizon)
    assert temperature == pytest.approx(exact, abs=0.0002)


def test_thermal_limit_reaches_boundary_and_rejects_invalid_parameters():
    allowed = ledger.thermal_current_limit(0.049, 1, 120, 25, 35, 40, 120)
    assert ledger.thermal_step(allowed, 0.049, 1, 120, 25, 35, 120) == pytest.approx(40)
    with pytest.raises(ValueError):
        ledger.thermal_current_limit(0.049, 0, 120, 25, 35, 40, 120)
    with pytest.raises(ValueError):
        ledger.discharge_ledger(0.001, 400, 500, 200)
