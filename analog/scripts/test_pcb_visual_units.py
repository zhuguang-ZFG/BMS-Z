"""PCB 图的单位换算回归：以铜线几何推算，不把错稿数字固化为正确值。"""
import math

import pytest
from visuals.scenes.ch15_reference_figures import (
    parallel_inductance,
    resonance_hz,
    via_inductance_nh,
)
from visuals.scenes.handdrawn_wave2 import trace_drop, trace_resistance
from visuals.scenes.handdrawn_wave17 import small_loop_field_v_m


def test_copper_trace_matches_independent_sheet_resistance():
    # 35 µm 铜约 0.485714 mΩ/square，1 cm / 0.5 mm 是 20 squares。
    sheet_ohms = 1.7e-8 / 35e-6
    expected = sheet_ohms * 20
    assert trace_resistance(0.01, 0.5e-3, 35e-6) == pytest.approx(expected)
    assert expected == pytest.approx(0.009714285714285714)
    assert trace_resistance(0.08, 0.5e-3, 35e-6) == pytest.approx(8 * expected)
    assert trace_resistance(0.08, 5e-3, 35e-6) == pytest.approx(0.8 * expected)


def test_visible_trace_drop_uses_the_model():
    svg = '\n'.join(trace_drop())
    for value in ('9.71 mΩ/cm', '77.71 mΩ', '23.31 mV', '77.71 mV'):
        assert value in svg
    assert '2.4 mV' not in svg


@pytest.mark.parametrize('dimensions', [(0, 1, 1), (1, 0, 1), (1, 1, -1)])
def test_trace_rejects_nonphysical_dimensions(dimensions):
    with pytest.raises(ValueError):
        trace_resistance(*dimensions)


def test_resonance_equal_reactance_and_inverse_square_root():
    frequency = resonance_hz(5e-9, 100e-9)
    assert frequency / 1e6 == pytest.approx(7.117625434)
    omega = 2 * math.pi * frequency
    assert omega * 5e-9 == pytest.approx(1 / (omega * 100e-9))
    assert resonance_hz(10e-9, 100e-9) == pytest.approx(frequency / math.sqrt(2))


def test_via_units_and_mutual_inductance_limits():
    single = via_inductance_nh(1.6, .3)
    assert single == pytest.approx(1.2992866543)
    # Uniformly scaling geometry scales the empirical inductance linearly.
    assert via_inductance_nh(3.2, .6) == pytest.approx(single * 2)
    assert parallel_inductance(single, 0, 4) == pytest.approx(single / 4)
    assert parallel_inductance(single, single, 4) == pytest.approx(single)
    assert parallel_inductance(single, single / 2, 4) == pytest.approx(.81205415894)


def test_small_loop_coefficient_against_free_space_model():
    # Independent eta*k^2*I*A/(4*pi*r), using rounded eta=377 ohms.
    area, frequency, current, distance = 15e-4, 100e6, .01, 3
    k = 2 * math.pi * frequency / 299792458
    independent = 377 * k**2 * current * area / (4 * math.pi * distance)
    field = small_loop_field_v_m(area, frequency, current, distance)
    assert field == pytest.approx(independent, rel=.002)
    assert field * 1e6 == pytest.approx(658)
    smaller = small_loop_field_v_m(.5e-4, frequency, current, distance)
    assert field / smaller == pytest.approx(30)
    assert 20 * math.log10(smaller * 1e6) == pytest.approx(26.822092778)


def test_legacy_wave_routes_corrected_via_to_handdrawn_canvas():
    from visuals.scenes.ch15_backlog_figures2 import FIGURES
    from visuals.scenes.ch15_reference_figures import SCENES
    assert FIGURES['ch15-via-parallel']['renderer'] == 'handdrawn'
    assert FIGURES['ch15-via-parallel']['alt'] == SCENES['ch15-via-parallel']['alt']

