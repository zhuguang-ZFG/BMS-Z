"""Structural checks for D04 figures."""
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[2] / "bms-book" / "engineering" / "assets" / "d04-measurement"


def load(name: str) -> tuple[ET.Element, str]:
    path = ASSETS / name
    assert path.is_file(), f"缺图 {name}（先跑 make_d04_figures.py）"
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(text), text


@pytest.mark.parametrize("name", ["D04-F1-sense-chain.svg", "D04-F2-budget.svg"])
def test_svg_is_wellformed_with_identity(name):
    root, text = load(name)
    assert root.get("role") == "img"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert root.find("svg:title", ns) is not None
    assert root.find("svg:desc", ns) is not None
    assert 'class="bg"' in text and 'class="title"' in text


def test_f1_chain_marks_two_new_terms_in_red():
    _root, text = load("D04-F1-sense-chain.svg")
    for token in ("增益 g_c", "偏置 b_c+b_i", "温漂 α(T−T0)", "量化 ±LSB/2", "建立 e_dyn"):
        assert token in text, f"缺链路环节 {token}"
    assert 'class="box-new"' in text, "新增两项必须用红色标记"
    assert "3.6 mV" in text and "0.038 mV" in text
    assert "8.138 mV" in text and "4.3922 mV" in text


def test_f2_budget_comparison_shows_both_scales():
    _root, text = load("D04-F2-budget.svg")
    assert "S1 四项上界" in text and "六项上界" in text
    assert "4.5 mV" in text and "8.138 mV" in text
    assert "2.51595 mV" in text and "4.3922 mV" in text
    assert text.count("非绝对界") >= 2, "两个 RSS 都必须标注非绝对界"
