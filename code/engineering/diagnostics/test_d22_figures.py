"""Structural and content checks for D22 figures."""

import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parents[2] / "bms-book" / "engineering" / "assets" / "d22-diagnostics"


def load(name: str) -> tuple[ET.Element, str]:
    path = ASSETS / name
    assert path.is_file(), f"缺图 {name}（先跑 make_d22_figures.py）"
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(text), text


def test_f22_1_svg_is_wellformed_with_identity():
    root, _text = load("D22-F1-lifecycle-timeline.svg")
    assert root.get("role") == "img"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert root.find("svg:title", ns) is not None
    assert root.find("svg:desc", ns) is not None


def test_f22_1_lifecycle_tokens_and_frozen_numbers():
    _root, text = load("D22-F1-lifecycle-timeline.svg")
    for token in ("stale_data 确认", "missing_slots 确认", "service_clear", "刷写 gen 42 接受"):
        assert token in text
    assert "FAULT" in text and "PROGRAMMING" in text and "DEGRADED" in text
    assert "61.0 pp" in text
    assert "session" in text and "range" in text and "self_test" in text
    assert "退出仍回 FAULT" in text
