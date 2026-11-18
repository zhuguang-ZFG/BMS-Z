"""sketch_pass 手绘管线的回归测试。

覆盖三个已核实缺陷/风险：
1. flatten_tags 归一化：仅含空白的成对标签变自闭合后必须 XML 合法、无游离斜杠
   （旧实现把 >  captured 进组再补 /，产出 <path …>/ 游离文本且丢闭合标签）；
2. 确定性：同一原稿同一 stem 两次变换逐字节一致（快照/批处理可重入的前提）；
3. 标记防叠加：变换产物带 data-sketch 标记，already_sketched 据此跳过，
   直接对已手绘文件再跑批处理驱动不会二次抖动。
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
try:
    from sketch_pass import (
        SKETCH_MARK,
        already_sketched,
        flatten_tags,
        sketch_file,
    )
finally:
    sys.path.pop(0)

SVG_HEAD = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'


def test_flatten_empty_paired_tags_become_self_closed():
    src = (
        SVG_HEAD
        + '<path d="M0 0"></path>\n'
        + '<path d="M1 1">\n  \n</path>'
        + '<rect x="0" y="0" width="10" height="10"></rect>'
        + '<circle cx="5" cy="5" r="3"></circle>'
        + '<line x1="0" y1="0" x2="9" y2="9"></line>'
        + "</svg>"
    )
    out = flatten_tags(src)
    root = ET.fromstring(out)  # 不再抛 mismatched tag
    shapes = [el for el in root.iter() if el.tag.split("}")[-1] in {"path", "rect", "circle", "line"}]
    assert len(shapes) == 5
    assert all(el.get("d") is not None or el.tag.split("}")[-1] != "path" for el in shapes)
    # 无游离斜杠文本节点
    assert not any(el.text and el.text.strip() == "/" for el in root.iter())


def test_flatten_leaves_paired_tags_with_children_alone():
    src = SVG_HEAD + '<path d="M0 0"><circle cx="1" cy="1" r="1"/></path></svg>'
    out = flatten_tags(src)
    assert "</path>" in out  # 含子元素的成对标签不被拆开
    ET.fromstring(out)


def test_flatten_leaves_self_closed_alone():
    src = SVG_HEAD + '<path d="M0 0"/><rect x="0" y="0" width="4" height="4"/></svg>'
    assert flatten_tags(src) == src


def test_sketch_transform_is_deterministic():
    src = flatten_tags(
        SVG_HEAD
        + '<rect x="2" y="2" width="80" height="60" rx="6" fill="none" stroke="#333"/>'
        + '<circle cx="50" cy="32" r="20" fill="none" stroke="#333"/>'
        + '<path d="M10 80 L90 80" stroke="#333" fill="none"/>'
        + "</svg>"
    )
    a = sketch_file(src, "demo-stem")
    b = sketch_file(src, "demo-stem")
    assert a == b
    ET.fromstring(a)


def test_line_converted_to_wobbly_path_endpoints_fixed():
    src = flatten_tags(
        SVG_HEAD
        + '<line x1="10" y1="20" x2="90" y2="20" stroke="#333" fill="none"/>'
        + "</svg>"
    )
    out = sketch_file(src, "line-stem")
    assert "<line" not in out
    # 端点不动：M 起点与 L 终点保持原坐标（中部插入抖动细分）
    assert 'd="M10 20' in out
    assert "L90 20" in out


def test_short_line_kept_as_line():
    src = flatten_tags(
        SVG_HEAD + '<line x1="1" y1="1" x2="3" y2="3" stroke="#333"/></svg>'
    )
    out = sketch_file(src, "short-line-stem")
    assert "<line" in out  # 短于 MIN_SEG，保留利落刻度线


def test_sketch_marks_output_and_detects_it():
    src = flatten_tags(
        SVG_HEAD + '<circle cx="50" cy="50" r="20" fill="none" stroke="#333"/></svg>'
    )
    out = sketch_file(src, "mark-stem")
    assert SKETCH_MARK in out[:400]
    assert already_sketched(out)
    assert not already_sketched(src)
