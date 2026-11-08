"""Structural checks for D01 figures (mechanism sketches, hand-authored)."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[2] / "bms-book" / "engineering" / "assets" / "d01-cell"


def load(name: str) -> tuple[ET.Element, str]:
    path = ASSETS / name
    assert path.is_file(), f"缺图 {name}（先跑 make_d01_figures.py）"
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(text), text


@pytest.mark.parametrize("name", ["D01-F1-cross-section.svg", "D01-F2-time-scales.svg"])
def test_svg_is_wellformed_with_identity(name):
    root, text = load(name)
    assert root.get("role") == "img"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert root.find("svg:title", ns) is not None
    assert root.find("svg:desc", ns) is not None
    assert 'class="bg"' in text and 'class="title"' in text


def test_f1_shows_two_carrier_paths_and_four_terms():
    _root, text = load("D01-F1-cross-section.svg")
    assert 'class="electron"' in text, "电子外电路路径必须存在"
    assert 'class="ion"' in text, "锂离子路径必须存在"
    for term in ("U_ocv", "I·R_Ω", "η_ct", "η_conc"):
        assert term in text, f"端电压四项缺 {term}"
    assert "隔膜" in text and "集流体" in text


def test_f2_uses_log_axis_with_three_bands():
    _root, text = load("D01-F2-time-scales.svg")
    assert "10^-6 s" in text and "1 s" in text and "10^4 s" in text
    for band in ("欧姆极化", "电荷转移", "浓差极化"):
        assert band in text, f"时间尺度缺 {band}"


def test_figures_do_not_name_specific_vendors():
    for name in ("D01-F1-cross-section.svg", "D01-F2-time-scales.svg"):
        _root, text = load(name)
        for vendor in ("宁德", "比亚迪", "松下", "Samsung", "CATL"):
            assert vendor not in text, f"机制示意图不得标注厂商：{vendor}"
