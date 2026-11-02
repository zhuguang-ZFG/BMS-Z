"""Checks that the weakest-cell practice keeps the pack geometry honest."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('weakest_cell_pack', Path(__file__).resolve().parents[1] / 'code/weakest_cell_pack.py')
weakest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weakest)


def test_series_capacity_is_the_weakest_cell_and_energy_follows_it():
    cells = [35.0, 50.0, 50.0, 50.0]
    assert weakest.pack_capacity_ah(cells) == 35.0
    assert weakest.pack_capacity_ah([50.0] * 11 + [46.0]) == 46.0
    assert weakest.pack_energy_wh([50.0] * 11 + [46.0], 3.2) == pytest.approx(46.0 * 12 * 3.2)
    assert weakest.pack_energy_wh(cells, 3.2) == pytest.approx(35.0 * 4 * 3.2)


def test_dead_capacity_is_zero_for_the_weakest_cell_and_positive_elsewhere():
    assert weakest.dead_capacity_ah([35.0, 50.0, 50.0, 50.0]) == [0.0, 15.0, 15.0, 15.0]
    assert weakest.dead_capacity_ah([35.0, 50.0, 50.0, 50.0])[1] * 3.2 == pytest.approx(48.0)


def test_mirror_formula_holds_only_for_symmetric_spread():
    assert weakest.mirror_weakest_ah(2.00, 0.40) == pytest.approx(1.80)
    assert weakest.mirror_weakest_ah(2.00, 0.0) == pytest.approx(2.00)
    # Asymmetric pack: the smallest cell wins and the half-spread shortcut overshoots.
    asymmetric = [2.10, 2.00, 1.95, 1.80]
    assert weakest.pack_capacity_ah(asymmetric) == 1.80
    assert weakest.mirror_weakest_ah(1.9625, 0.30) > 1.80
    with pytest.raises(ValueError):
        weakest.mirror_weakest_ah(2.00, -0.10)
    with pytest.raises(ValueError):
        weakest.mirror_weakest_ah(2.00, 4.10)


def test_average_voltage_releases_while_the_weakest_cell_must_trip():
    verdict = weakest.voltage_verdict([3.500] * 15 + [2.750], 2.800)
    assert verdict['average_v'] == pytest.approx(55.25 / 16)
    assert verdict['weakest_v'] == 2.750
    assert verdict['average_would_release'] is True
    assert verdict['weakest_trips'] is True
    assert verdict['release'] is False
    # Exactly at the threshold protection still acts: the comparison is inclusive.
    assert weakest.voltage_verdict([3.500, 2.800], 2.800)['release'] is False
    assert weakest.voltage_verdict([3.500, 2.801], 2.800)['release'] is True


@pytest.mark.parametrize('cells', [[], [0.0], [50.0, -1.0]])
def test_invalid_capacities_are_rejected(cells):
    with pytest.raises(ValueError):
        weakest.pack_capacity_ah(cells)


def test_voltage_verdict_rejects_empty_input():
    with pytest.raises(ValueError):
        weakest.voltage_verdict([], 2.800)
