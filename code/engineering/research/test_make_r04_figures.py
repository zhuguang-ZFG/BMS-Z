"""Structural checks on the generated R04 figure.

The correction contract gate (S1–S6) and the feedback-consistency
evaluation are teaching content; the test pins the visible tokens so the
generated SVG can not silently drift from the chapter prose.
"""
import importlib.util
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ASSETS = ROOT / "bms-book" / "engineering" / "assets" / "r04-safety"

spec = importlib.util.spec_from_file_location("make_r04_figures", HERE / "make_r04_figures.py")
assert spec is not None and spec.loader is not None
maker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = maker
spec.loader.exec_module(maker)


def test_r04_svg_is_wellformed_with_identity():
    root = ET.fromstring(maker.build_svg())
    assert root.tag.rsplit("}", 1)[-1] == "svg"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    title = root.find("svg:title", ns)
    desc = root.find("svg:desc", ns)
    assert title is not None and title.text and title.text.strip()
    assert desc is not None and desc.text and desc.text.strip()


def test_r04_gate_and_evaluation_tokens():
    text = maker.build_svg()
    for token in (
        "纠偏合同校验门 S1–S6",
        "S1 清旗/复位/重新许可不得同效 · S2 三动作必填",
        "S3 反应命令带身份 · S4 反馈带来源信号",
        "S6 每个声明迁移有显式测试映射",
        "清旗=复位=重新许可 → 混淆通道：这不是恢复，是复读",
        "OS07 未闭合前所有安全宣称保持教学/待验身份",
    ):
        assert token in text


def test_generated_file_matches_builder_output():
    target = ASSETS / "R04-F1-correction-gate.svg"
    assert target.is_file()
    assert target.read_text(encoding="utf-8") == maker.build_svg()
