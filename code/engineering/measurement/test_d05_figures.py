"""Structural checks for D05 figures."""
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[2] / "bms-book" / "engineering" / "assets" / "d05-afe"


def load(name: str) -> tuple[ET.Element, str]:
    path = ASSETS / name
    assert path.is_file(), f"缺图 {name}（先跑 make_d05_figures.py）"
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(text), text


@pytest.mark.parametrize("name", ["D05-F1-mux-settling.svg", "D05-F2-open-wire.svg"])
def test_svg_is_wellformed_with_identity(name):
    root, text = load(name)
    assert root.get("role") == "img"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert root.find("svg:title", ns) is not None
    assert root.find("svg:desc", ns) is not None
    assert 'class="bg"' in text and 'class="title"' in text


def test_f1_shows_settling_curve_with_frozen_moments():
    _root, text = load("D05-F1-mux-settling.svg")
    assert "Rs 10 kΩ" in text and "Cs 10 nF" in text and "τ = 100 µs" in text
    assert "t = 901.09 µs" in text, "12 bit 建立时刻必须标出"
    assert "LSB/2 = 0.610 mV" in text
    assert "14.73746 ms" in text and "10 ms" in text, "扫描撞 10 ms 任务的账必须在图上"


def test_f2_marks_stuck_value_and_audit():
    _root, text = load("D05-F2-open-wire.svg")
    assert text.count("开线保持 3.280 V") >= 2, "A/B 两条时间线都要有保持值标记"
    assert "A 静置：卡值窗漏报" in text
    assert "B 漂移：卡值窗碰巧触发" in text
    assert "注入 +5.0 mV" in text and "响应 0.0 mV" in text, "主动稽核示意必须在"
    assert "碰巧不是设计" in text
