"""Structural checks on the generated R01 figure.

The five-element gate (P1–P5) and the fail-closed evaluation contract are
teaching content; the test pins the visible tokens so the generated SVG can
not silently drift from the chapter prose.
"""
import importlib.util
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ASSETS = ROOT / "bms-book" / "engineering" / "assets" / "r01-model"

spec = importlib.util.spec_from_file_location("make_r01_figures", HERE / "make_r01_figures.py")
assert spec is not None and spec.loader is not None
maker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = maker
spec.loader.exec_module(maker)


def test_r01_svg_is_wellformed_with_identity():
    root = ET.fromstring(maker.build_svg())
    assert root.tag.rsplit("}", 1)[-1] == "svg"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    title = root.find("svg:title", ns)
    desc = root.find("svg:desc", ns)
    assert title is not None and title.text and title.text.strip()
    assert desc is not None and desc.text and desc.text.strip()


def test_r01_gate_and_evaluation_tokens():
    text = maker.build_svg()
    for token in (
        "五要素校验门 P1–P5",
        "P1 冻结版本 · P2 正容差 v_rel/q_abs",
        "P4 事件三件套 endpoint/discontinuity/both_sides",
        "P5 reproduces_mwe ∈ yes/no/unknown",
        "逐项 fail-closed",
        "观测缺事件用例 / 超容差 → 走失败通道",
        "OS01/CASE01 未复现前 reproduces_mwe 不许写 yes",
    ):
        assert token in text


def test_generated_file_matches_builder_output():
    target = ASSETS / "R01-F1-protocol-gate.svg"
    assert target.is_file()
    assert target.read_text(encoding="utf-8") == maker.build_svg()
