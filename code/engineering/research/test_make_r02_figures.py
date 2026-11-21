"""Structural checks on the generated R02 figure.

The contract gate (C1–C6) and the held-out window fail-closed evaluation are
teaching content; the test pins the visible tokens so the generated SVG can
not silently drift from the chapter prose.
"""
import importlib.util
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ASSETS = ROOT / "bms-book" / "engineering" / "assets" / "r02-estimation"

spec = importlib.util.spec_from_file_location("make_r02_figures", HERE / "make_r02_figures.py")
assert spec is not None and spec.loader is not None
maker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = maker
spec.loader.exec_module(maker)


def test_r02_svg_is_wellformed_with_identity():
    root = ET.fromstring(maker.build_svg())
    assert root.tag.rsplit("}", 1)[-1] == "svg"
    ns = {"svg": "http://www.w3.org/2000/svg"}
    title = root.find("svg:title", ns)
    desc = root.find("svg:desc", ns)
    assert title is not None and title.text and title.text.strip()
    assert desc is not None and desc.text and desc.text.strip()


def test_r02_gate_and_evaluation_tokens():
    text = maker.build_svg()
    for token in (
        "合同校验门 C1–C6",
        "C1 拟合窗∩验证窗=∅ · C2 验证窗必填",
        "C3 每个估计带正 std",
        "C6 外部库依赖只警告不放行基准",
        "拟合/验证重叠 → 泄漏通道：这是拟合，不是估计",
        "OS02/EDU01 未复现前外部库与讲义内容保持访问状态标注",
    ):
        assert token in text


def test_generated_file_matches_builder_output():
    target = ASSETS / "R02-F1-contract-gate.svg"
    assert target.is_file()
    assert target.read_text(encoding="utf-8") == maker.build_svg()
