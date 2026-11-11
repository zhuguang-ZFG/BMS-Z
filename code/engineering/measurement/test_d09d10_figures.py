"""Structural checks for D09 and D10 figures."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def load(sub: str, name: str) -> tuple[ET.Element, str]:
    path = HERE.parents[2] / "bms-book" / "engineering" / "assets" / sub / name
    assert path.is_file(), f"缺图 {name}（先跑 make_d09d10_figures.py）"
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(text), text


@pytest.mark.parametrize(
    "sub,name",
    [
        ("d09-safety", "D09-F1-common-supply.svg"),
        ("d09-safety", "D09-F2-matrix-fmea.svg"),
        ("d10-balance", "D10-F1-bleed-window.svg"),
        ("d10-balance", "D10-F2-three-diffs.svg"),
    ],
)
def test_svg_is_wellformed_with_identity(sub, name):
    root, text = load(sub, name)
    assert root.get("role") == "img"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert root.find("svg:title", ns) is not None
    assert root.find("svg:desc", ns) is not None






def test_f10_1_bleed_three_accounts_and_duty():
    _root, text = load("d10-balance", "D10-F1-bleed-window.svg")
    assert "35 mA" in text and "0.122 W" in text and "85.7 min" in text


def test_f10_2_three_differences_rows():
    _root, text = load("d10-balance", "D10-F2-three-diffs.svg")
    for token in ("电压差", "SOC 差", "容量差"):
        assert token in text
    assert "25 pp" in text and "2.5 pp" in text
