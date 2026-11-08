"""Structural checks for D02 figures."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[2] / "bms-book" / "engineering" / "assets" / "d02-model"


def load(name: str) -> tuple[ET.Element, str]:
    path = ASSETS / name
    assert path.is_file(), f"缺图 {name}（先跑 make_d02_figures.py）"
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(text), text


@pytest.mark.parametrize("name", ["D02-F1-2rc-circuit.svg", "D02-F2-residuals.svg"])
def test_svg_is_wellformed_with_identity(name):
    root, text = load(name)
    assert root.get("role") == "img"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert root.find("svg:title", ns) is not None
    assert root.find("svg:desc", ns) is not None
    assert 'class="bg"' in text and 'class="title"' in text


def test_f1_topology_two_rc_branches_with_polarity():
    _root, text = load("D02-F1-2rc-circuit.svg")
    for token in ("R0 20 mΩ", "R1 15 mΩ", "C1 3000 F", "R2 5 mΩ", "C2 200 F"):
        assert token in text, f"缺元件标注 {token}"
    assert "τ1 = 45 s" in text and "τ2 = 1 s" in text
    assert "vp1" in text and "vp2" in text, "两条极化支路的状态名必须标出"
    assert text.count('class="wire"') >= 10, "串联拓扑的连线必须完整"


def test_f2_plots_residual_comparison_with_frozen_numbers():
    _root, text = load("D02-F2-residuals.svg")
    assert "31.5 s" in text, "1RC 偏 τ 指纹必须在图上"
    assert "45 s 与 1 s" in text, "2RC 精确命中必须在图上"
    assert "3.06 mV" in text and "0.13 mV" in text
    assert 'class="cmp"' in text and 'class="good"' in text, "两条残差曲线都要在"
    assert "残差 mV" in text
