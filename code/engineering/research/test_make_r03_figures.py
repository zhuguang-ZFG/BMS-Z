"""Structural checks on the generated R03 figure.

The domain contract gate (D1–D5) and the domain-in evaluation are teaching
content; the test pins the visible tokens so the generated SVG can not
silently drift from the chapter prose.
"""
import importlib.util
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ASSETS = ROOT / "bms-book" / "engineering" / "assets" / "r03-aging"

spec = importlib.util.spec_from_file_location("make_r03_figures", HERE / "make_r03_figures.py")
assert spec is not None and spec.loader is not None
maker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = maker
spec.loader.exec_module(maker)


def test_r03_svg_is_wellformed_with_identity():
    root = ET.fromstring(maker.build_svg())
    assert root.tag.rsplit("}", 1)[-1] == "svg"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    title = root.find("svg:title", ns)
    desc = root.find("svg:desc", ns)
    assert title is not None and title.text and title.text.strip()
    assert desc is not None and desc.text and desc.text.strip()


def test_r03_gate_and_evaluation_tokens():
    text = maker.build_svg()
    for token in (
        "域合同校验门 D1–D5",
        "D1 pack几何变化≠老化真值（OS03）",
        "D2 外部数据未核可用性→实证开放（OS08）",
        "D5 温度/SOC/C-rate 域必须声明",
        "观测条件越出声明域 → 外推：fail",
        "OS03/OS08 未闭合前所有老化宣称保持教学/待验身份",
    ):
        assert token in text


def test_generated_file_matches_builder_output():
    target = ASSETS / "R03-F1-domain-gate.svg"
    assert target.is_file()
    assert target.read_text(encoding="utf-8") == maker.build_svg()
