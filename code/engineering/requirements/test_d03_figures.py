"""Structural checks for D03 figures (mechanism diagrams, hand-authored)."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[2] / "bms-book" / "engineering" / "assets" / "d03-requirements"


def load(name: str) -> tuple[ET.Element, str]:
    path = ASSETS / name
    assert path.is_file(), f"缺图 {name}（先跑 make_d03_figures.py）"
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(text), text


@pytest.mark.parametrize(
    "name", ["D03-F1-boundary-flow.svg", "D03-F2-constraint-map.svg"]
)
def test_svg_is_wellformed_with_identity(name):
    root, text = load(name)
    assert root.get("role") == "img"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert root.find("svg:title", ns) is not None
    assert root.find("svg:desc", ns) is not None
    assert 'class="bg"' in text and 'class="title"' in text


def test_f1_shows_three_owners_and_flows():
    _root, text = load("D03-F1-boundary-flow.svg")
    for owner in ("测量", "估计", "保护"):
        assert 'class="owner"' in text and owner in text, f"缺职责 {owner}"
    assert 'class="flow"' in text, "量的流向箭头必须存在"
    assert "12 字段" in text and "规格缺项" in text


def test_f2_marks_weakest_cell_against_average():
    _root, text = load("D03-F2-constraint-map.svg")
    assert "最弱 3.28 V（越限）" in text
    assert "均值 3.3687 V" in text
    assert text.count('class="mark"') >= 2, "均值与最弱两个标记都要在电压窗上"
    for window in ("电压窗", "SOC 窗", "温度窗", "持续电流", "寿命目标"):
        assert window in text, f"缺约束窗口 {window}"
