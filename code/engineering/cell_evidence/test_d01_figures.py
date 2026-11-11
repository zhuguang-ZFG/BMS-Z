"""Structural checks for D01 figures (mechanism sketches, hand-authored)."""

import re
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


def test_f1_shows_two_carrier_paths_and_four_terms():
    _root, text = load("D01-F1-cross-section.svg")
    for term in ("U_ocv", "I·R_Ω", "η_ct", "η_conc"):
        assert term in text, f"端电压四项缺 {term}"
    assert "隔膜" in text and "集流体" in text


def test_f1_container_rectangles_do_not_default_to_black():
    root, _text = load("D01-F1-cross-section.svg")
    ns = {"svg": "http://www.w3.org/2000/svg"}
    css = "\n".join(element.text or "" for element in root.findall("svg:style", ns))
    rules = {
        name: dict(re.findall(r"([\w-]+)\s*:\s*([^;]+)", declarations))
        for name, declarations in re.findall(r"\.([\w-]+)\s*\{([^}]+)\}", css)
    }
    containers = [
        rect for rect in root.findall("svg:rect", ns)
        if "box" in rect.get("class", "").split()
    ]
    assert len(containers) >= 5
    for rect in containers:
        style = {"fill": "#000000", "stroke": "none", "stroke-width": "1"}
        for name in rect.get("class", "").split():
            style.update(rules.get(name, {}))
        fill = style["fill"].strip()
        if fill not in ("none", "transparent"):
            assert re.fullmatch(r"#[0-9a-fA-F]{6}", fill), fill
            channels = [int(fill[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
            luminance = sum(weight * value for weight, value in zip((0.2126, 0.7152, 0.0722), linear))
            assert luminance >= 0.7, "容器不得以深填充遮住电芯层次或说明文字"
        assert style["stroke"].strip() not in ("none", "transparent")
        assert float(style["stroke-width"]) > 0


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
