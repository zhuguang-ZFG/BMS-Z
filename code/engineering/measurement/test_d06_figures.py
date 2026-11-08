"""Structural checks for D06 figures."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[2] / "bms-book" / "engineering" / "assets" / "d06-pcb"


def load(name: str) -> tuple[ET.Element, str]:
    path = ASSETS / name
    assert path.is_file(), f"缺图 {name}（先跑 make_d06_figures.py）"
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(text), text


@pytest.mark.parametrize(
    "name", ["D06-F1-return-path.svg", "D06-F2-kelvin-isolation.svg"]
)
def test_svg_is_wellformed_with_identity(name):
    root, text = load(name)
    assert root.get("role") == "img"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert root.find("svg:title", ns) is not None
    assert root.find("svg:desc", ns) is not None
    assert 'class="bg"' in text and 'class="title"' in text


def test_f1_shows_shared_vs_separate_return_with_bounce():
    _root, text = load("D06-F1-return-path.svg")
    assert "共用回流" in text and "改回流路径" in text
    assert "2000 mV" in text and "100 nH" in text
    assert 'class="bad"' in text and 'class="good"' in text


def test_f2_shows_kelvin_error_and_isolation_path():
    _root, text = load("D06-F2-kelvin-isolation.svg")
    assert "97.09%" in text and "300 µΩ" in text and "10 mΩ" in text
    assert "寄生 C 10 pF" in text and "100 mA" in text
    assert "受控返回" in text, "隔离必须画出受控共模路径"
