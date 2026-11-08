"""Structural checks on the generated S2 figures.

Geometry is parsed from the emitted SVG: the point is to keep the circuit
topology honest (the parallel cell must stay in series) and to keep every figure
inside one canvas. Text metrics and visual balance are audited in a browser and
remain a review step, not a test.
"""
import importlib.util
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


s2 = _load('s2_identification', 's2_identification.py')
figures = _load('make_s2_figures', 'make_s2_figures.py')

TARGETS = figures.build_targets()
EXPECTED = {
    'S2-F1-rc-polarity.svg',
    'S2-F2-common-time-axis.svg',
    'S2-F3-window-and-tau-profile.svg',
    'S2-F4-slope-sensitivity.svg',
    'S2-F5-bias-counterexample.svg',
}


def _local(tag):
    return tag.rsplit('}', 1)[-1]


def _root(name):
    return ET.fromstring(TARGETS[name])


def _lines(root):
    out = []
    for node in root.iter():
        if _local(node.tag) != 'line':
            continue
        out.append(tuple(float(node.get(key)) for key in ('x1', 'y1', 'x2', 'y2')))
    return out


def _has(lines, *wanted):
    for a, b, c, d in wanted:
        if not any(
            (x1 == a and y1 == b and x2 == c and y2 == d)
            or (x1 == c and y1 == d and x2 == a and y2 == b)
            for x1, y1, x2, y2 in lines
        ):
            return False
    return True


def test_every_figure_is_one_self_contained_svg():
    assert set(TARGETS) == EXPECTED
    for name in TARGETS:
        root = _root(name)
        assert _local(root.tag) == 'svg'
        assert root.get('role') == 'img'
        tall = name in ('S2-F1-rc-polarity.svg', 'S2-F2-common-time-axis.svg')
        assert root.get('viewBox') == ('0 0 800 566' if tall else '0 0 800 420')
        children = {_local(node.tag): node for node in root}
        title = (children['title'].text or '').strip()
        desc = (children['desc'].text or '').strip()
        assert title and desc and desc != title
        # every declared class must be defined in the inline style block
        style = next((node.text or '') for node in root if _local(node.tag) == 'style')
        for node in root.iter():
            cls = node.get('class')
            if cls:
                for token in cls.split():
                    assert f'.{token} {{' in style, (name, token)


def test_parallel_cell_stays_in_series_with_the_terminals():
    """R1||C1 must sit between R0 and the + terminal, not across the terminals.

    The cell is the ladder at x=300..430: two rungs (R1 at y=170, C1 at y=300)
    joined by two end bridges. A vertical segment from the bottom rung down to
    the negative rail would turn the cell into a shunt.
    """
    lines = _lines(_root('S2-F1-rc-polarity.svg'))
    assert _has(
        lines,
        (120.0, 170.0, 190.0, 170.0),   # source -> R0
        (254.0, 170.0, 300.0, 170.0),   # R0 -> left bridge
        (300.0, 170.0, 330.0, 170.0),   # left bridge -> R1
        (400.0, 170.0, 430.0, 170.0),   # R1 -> right bridge
        (300.0, 170.0, 300.0, 300.0),   # left bridge
        (430.0, 170.0, 430.0, 300.0),   # right bridge
        (300.0, 300.0, 348.0, 300.0),   # bottom rung, left of C1
        (372.0, 300.0, 430.0, 300.0),   # bottom rung, right of C1
        (430.0, 170.0, 560.0, 170.0),   # cell -> + terminal
        (120.0, 430.0, 560.0, 430.0),   # negative rail
        (560.0, 170.0, 660.0, 170.0),   # + terminal -> external loop
        (560.0, 430.0, 660.0, 430.0),   # - terminal -> external loop
        (660.0, 170.0, 660.0, 250.0),   # external loop, above the load
        (660.0, 330.0, 660.0, 430.0),   # external loop, below the load
    )


def test_the_cell_bottom_rung_never_reaches_the_negative_rail():
    lines = _lines(_root('S2-F1-rc-polarity.svg'))
    for x1, y1, x2, y2 in lines:
        if x1 != x2 or not 295.0 <= x1 <= 435.0:
            continue
        low, high = sorted((y1, y2))
        assert not (low < 315.0 and high > 425.0), f'shunt path at x={x1}: {y1}->{y2}'


def test_f1_marks_the_parallel_cell_as_an_equivalent_two_terminal_network():
    root = _root('S2-F1-rc-polarity.svg')
    texts = [(node.text or '') for node in root.iter() if _local(node.tag) == 'text']
    assert any('R1∥C1' in value for value in texts)
    assert any(value == 'vp' for value in texts)
    # the polarity labels of the source and of the terminals are all present
    assert sum(1 for value in texts if value == '+') == 2
    assert sum(1 for value in texts if value == '−') == 2


def _polylines(root):
    out = {}
    for node in root.iter():
        if _local(node.tag) != 'polyline':
            continue
        points = []
        for pair in (node.get('points') or '').split():
            x_text, y_text = pair.split(',')
            points.append((float(x_text), float(y_text)))
        out.setdefault(node.get('class'), []).append(points)
    return out


def test_vertical_axes_put_larger_values_higher():
    """Regression: sy() once mapped y1 to the panel bottom, drawing every rise as a fall.

    These inequalities are independent of label placement and flip if the axis is inverted.
    """
    f2 = _polylines(_root('S2-F2-common-time-axis.svg'))
    ocv = f2['ocv'][0]
    term = f2['term'][0]
    # Terminal voltage is 40 mV below OCV at the pulse start, so it must sit lower on screen.
    assert term[0][1] > ocv[0][1] + 20.0
    # 40 mV ohmic drop must be drawn above the <=6 mV polarization curve.
    assert min(y for _, y in f2['ohm'][0]) < min(y for _, y in f2['pol'][0]) - 20.0

    f3 = _polylines(_root('S2-F3-window-and-tau-profile.svg'))
    long_curve = [p for p in f3['term'][-1] if p[0] >= 470.0]
    # Residual minimization is a data claim tested in identification; rendering checks
    # the independent orientation and endpoint contract, not an arbitrary pixel window.
    assert long_curve[0][1] < max(y for _, y in long_curve) - 100.0
    sx, sy = figures.axis(10, 120, 1.0, 1.45, 470, 760, 96, 300)
    assert sx(10) == 470 and sx(120) == 760
    assert sy(1.0) == 300 and abs(sy(1.45) - 96) < 1e-12
    assert sy(1.1) > sy(1.4)

    f5 = _polylines(_root('S2-F5-bias-counterexample.svg'))
    a_curve = [p for p in f5['soc-a'][-1] if p[0] >= 470.0]
    b_curve = [p for p in f5['soc-b'][-1] if p[0] >= 470.0]
    assert sum(y for _, y in b_curve) / len(b_curve) < sum(y for _, y in a_curve) / len(a_curve) - 100.0
