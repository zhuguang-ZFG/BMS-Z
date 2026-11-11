"""Structural contracts for S3 precharge figures; geometry stays a user-eye check."""
from __future__ import annotations

import importlib.util
import math
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ASSETS = ROOT / "bms-book" / "engineering" / "assets" / "s3-precharge"

spec = importlib.util.spec_from_file_location("make_s3_figures", HERE / "make_s3_figures.py")
assert spec is not None and spec.loader is not None
maker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = maker
spec.loader.exec_module(maker)


def test_generated_files_match_builder_output():
    targets = maker.build_targets()
    assert len(targets) == 5
    for name, content in targets.items():
        path = ASSETS / name
        assert path.exists()
        assert path.read_text(encoding="utf-8") == content


@pytest.mark.parametrize(
    "name",
    [
        "S3-F1-current-paths.svg",
        "S3-F2-energy-account.svg",
        "S3-F3-state-timeline.svg",
        "S3-F4-validity-evidence.svg",
        "S3-F5-device-limits.svg",
    ],
)
def test_s3_svgs_have_accessible_identity(name):
    raw = (ASSETS / name).read_text(encoding="utf-8")
    assert 'role="img"' in raw
    assert "<title>" in raw and "<desc>" in raw


def test_f2_anchors_95_percent_and_energy_identity():
    raw = (ASSETS / "S3-F2-energy-account.svg").read_text(encoding="utf-8")
    for anchor in ("0.50927", "152", "79.8", "72.2", "160", "80"):
        assert anchor in raw


def test_f5_anchors_inrush_and_residual_current():
    raw = (ASSETS / "S3-F5-device-limits.svg").read_text(encoding="utf-8")
    for anchor in ("2.35294", "0.118", "1000"):
        assert anchor in raw




SVG = {"svg": "http://www.w3.org/2000/svg"}


def _f1_panels():
    root = ET.fromstring((ASSETS / "S3-F1-current-paths.svg").read_text(encoding="utf-8"))
    panels = {state: root.find(f"svg:g[@id='f1-{state}']", SVG) for state in ("precharge", "main", "discharge")}
    assert all(panel is not None for panel in panels.values()), "三个状态必须各有实际电路面板"
    return root, panels


def _point(element, x="cx", y="cy"):
    return float(element.attrib[x]), float(element.attrib[y])


def _component(panel, name):
    element = panel.find(f".//*[@id='{panel.attrib['id']}-{name}']")
    assert element is not None, name
    return element


def _conductor_graph(panel, omit_resistor=None):
    """Trace drawn wires and resistor terminals, not a parallel metadata netlist."""
    segments = [
        (_point(line, "x1", "y1"), _point(line, "x2", "y2"))
        for line in panel.findall(".//svg:line", SVG)
        if "wire" in line.get("class", "").split()
    ]
    for name in ("Rpre", "Rd"):
        if name == omit_resistor:
            continue
        group = panel.find(f".//*[@id='{panel.attrib['id']}-{name}']")
        if group is None:
            continue
        rect = group.find("svg:rect", SVG)
        assert rect is not None
        x, y = _point(rect, "x", "y")
        width, height = float(rect.attrib["width"]), float(rect.attrib["height"])
        if width > height:
            segments.append(((x, y + height / 2), (x + width, y + height / 2)))
        else:
            segments.append(((x + width / 2, y), (x + width / 2, y + height)))
    points = {point for segment in segments for point in segment}
    points.update(_point(circle) for circle in panel.findall(".//svg:circle", SVG))
    graph = {point: set() for point in points}
    for start, end in segments:
        dx, dy = end[0] - start[0], end[1] - start[1]
        on_segment = [
            point for point in points
            if abs((point[0] - start[0]) * dy - (point[1] - start[1]) * dx) < 1e-6
            and min(start[0], end[0]) <= point[0] <= max(start[0], end[0])
            and min(start[1], end[1]) <= point[1] <= max(start[1], end[1])
        ]
        on_segment.sort(key=lambda point: (point[0] - start[0]) * dx + (point[1] - start[1]) * dy)
        for left, right in zip(on_segment, on_segment[1:], strict=False):
            graph[left].add(right)
            graph[right].add(left)
    return graph


def _connected(graph, start, end):
    if start not in graph or end not in graph:
        return False
    pending, seen = [start], set()
    while pending:
        point = pending.pop()
        if point == end:
            return True
        if point not in seen:
            seen.add(point)
            pending.extend(graph[point] - seen)
    return False


def test_f1_drawn_circuit_has_parallel_feeds_and_capacitor_discharge():
    _root, panels = _f1_panels()
    for state, panel in panels.items():
        source = panel.find("svg:circle[@class='box']", SVG)
        assert source is not None, "须从实际电源符号端子追馈电路径"
        cx, cy = _point(source)
        radius = float(source.attrib["r"])
        source_p, source_n = (cx, cy - radius), (cx, cy + radius)
        bus_p = _point(_component(panel, "bus-positive"))
        bus_n = _point(_component(panel, "bus-negative"))
        assert source_p != source_n and bus_p != bus_n
        graph = _conductor_graph(panel)
        assert _connected(graph, source_n, bus_n), "本模型负端共线"
        assert not _connected(graph, source_p, source_n), "不得短接电源两端"
        assert _connected(graph, source_p, bus_p) == (state != "discharge")
        assert _connected(graph, bus_p, bus_n) == (state == "discharge")
        without_precharge_resistor = _conductor_graph(panel, omit_resistor="Rpre")
        assert _connected(without_precharge_resistor, source_p, bus_p) == (state == "main"), "预充不得绕过 Rpre；主路须独立于 Rpre"
        without_discharge_resistor = _conductor_graph(panel, omit_resistor="Rd")
        assert not _connected(without_discharge_resistor, bus_p, bus_n), "泄放不得绕过 Rd"
        capacitor = _component(panel, "C")
        plates = capacitor.findall("svg:line", SVG)
        assert len(plates) == 2
        assert float(plates[0].attrib["y1"]) != float(plates[1].attrib["y1"])
        for plate, terminal in zip(plates, (bus_p, bus_n), strict=False):
            midpoint = ((float(plate.attrib["x1"]) + float(plate.attrib["x2"])) / 2, float(plate.attrib["y1"]))
            assert _connected(graph, terminal, midpoint), "电容两片须分别接到母线正负端"


def test_f1_open_contacts_have_a_real_visible_gap():
    _root, panels = _f1_panels()
    expected = {
        "precharge": {"Kmain": False, "Kpre": True, "Kd": False},
        "main": {"Kmain": True, "Kpre": False, "Kd": False},
        "discharge": {"Kmain": False, "Kpre": False, "Kd": True},
    }
    for state, switches in expected.items():
        for name, closed in switches.items():
            contact = _component(panels[state], name)
            terminals = contact.findall("svg:circle", SVG)
            assert len(terminals) == 2
            left, right = map(_point, terminals)
            assert _connected(_conductor_graph(contact), left, right) == closed
            blade = contact.find("svg:line", SVG)
            assert blade is not None
            start, end = _point(blade, "x1", "y1"), _point(blade, "x2", "y2")
            dx, dy = end[0] - start[0], end[1] - start[1]
            squared_length = dx * dx + dy * dy
            assert squared_length > 0
            fraction = max(0, min(1, ((right[0] - start[0]) * dx + (right[1] - start[1]) * dy) / squared_length))
            closest = (start[0] + fraction * dx, start[1] + fraction * dy)
            gap = math.dist(closest, right)
            assert gap == 0 if closed else gap >= 12


def test_f1_key_labels_remain_large_at_reading_widths():
    root, _panels = _f1_panels()
    width = float(root.attrib["viewBox"].split()[2])
    css = "\n".join(element.text or "" for element in root.findall("svg:style", SVG))
    sizes = {
        name: float(size)
        for name, size in re.findall(r"\.([\w-]+)\s*\{[^}]*?font\s*:[^;]*?(\d+(?:\.\d+)?)px", css)
    }
    for viewport in (390, 820):
        scale = min(1, (viewport - 40) / width)
        for label in root.findall(".//svg:text", SVG):
            classes = label.get("class", "").split()
            font_size = next(sizes[name] for name in reversed(classes) if name in sizes)
            minimum = 12 if "f1-note" in classes else 14
            assert font_size * scale >= minimum
