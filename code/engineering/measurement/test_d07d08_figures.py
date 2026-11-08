"""Structural checks for D07 and D08 figures."""
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def load(sub: str, name: str) -> tuple[ET.Element, str]:
    path = HERE.parents[2] / "bms-book" / "engineering" / "assets" / sub / name
    assert path.is_file(), f"缺图 {name}（先跑 make_d07d08_figures.py）"
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(text), text


@pytest.mark.parametrize("sub,name", [
    ("d07-power", "D07-F1-current-paths.svg"),
    ("d07-power", "D07-F2-soa-reading.svg"),
    ("d08-protection", "D08-F1-reaction-lanes.svg"),
    ("d08-protection", "D08-F2-blind-hysteresis.svg"),
])
def test_svg_is_wellformed_with_identity(sub, name):
    root, text = load(sub, name)
    assert root.get("role") == "img"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert root.find("svg:title", ns) is not None
    assert root.find("svg:desc", ns) is not None
    assert 'class="bg"' in text and 'class="title"' in text


def test_f7_1_marks_body_diode_leak():
    _root, text = load("d07-power", "D07-F1-current-paths.svg")
    assert "体二极管照常导通" in text
    assert "背靠背" in text and "源对源" in text
    assert "35 倍" in text and "4.8 W" in text


def test_f7_2_soa_rows_and_practice_points():
    _root, text = load("d07-power", "D07-F2-soa-reading.svg")
    for row in ("DC：8 A", "1 s：10 A", "100 ms：15 A", "10 ms：30 A"):
        assert row in text, f"缺 SOA 行 {row}"
    assert "20 A / 10 ms ✓" in text
    assert "20 A / 100 ms ✗" in text


def test_f8_1_lane_durations_sum_to_worst():
    _root, text = load("d08-protection", "D08-F1-reaction-lanes.svg")
    for seg in ("故障→首样本", "确认 3 拍", "判决", "执行→反馈", "调度抖动"):
        assert seg in text, f"缺泳道 {seg}"
    assert "72.263" in text and "10.263" in text
    assert "最坏" in text and "承诺" in text


def test_f8_2_blind_window_and_hysteresis_loop():
    _root, text = load("d08-protection", "D08-F2-blind-hysteresis.svg")
    assert "8 ms 毛刺" in text and "抑制" in text
    assert "25 ms 真实故障" in text and "漏检" in text
    assert "触发 50 A" in text and "释放 45 A" in text
    assert "12 次 → 1 次" in text
    assert "盲区" in text
