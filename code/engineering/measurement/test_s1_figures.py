"""Structure checks for S1 figures: parseability and embedded anchors."""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from xml.etree import ElementTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIGURES = ROOT / "bms-book" / "engineering" / "assets" / "s1-measurement"

spec = importlib.util.spec_from_file_location("make_s1_figures", HERE / "make_s1_figures.py")
assert spec is not None and spec.loader is not None
figures = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = figures
spec.loader.exec_module(figures)

NS = "{http://www.w3.org/2000/svg}"


def load(name: str) -> tuple[ElementTree.Element, str]:
    text = (FIGURES / name).read_text(encoding="utf-8")
    return ElementTree.fromstring(text), text


def test_four_figures_exist_and_match_generator():
    targets = figures.build_targets()
    assert sorted(targets) == [
        "S1-F1-sense-chain.svg",
        "S1-F2-error-budget.svg",
        "S1-F3-settling-scan.svg",
        "S1-F4-filter-budget.svg",
    ]
    for name, expected in targets.items():
        assert (FIGURES / name).read_text(encoding="utf-8") == expected


def test_every_svg_declares_title_desc_and_role():
    for name in figures.build_targets():
        root, _ = load(name)
        assert root.attrib.get("role") == "img"
        assert root.find(f"{NS}title") is not None
        assert root.find(f"{NS}desc") is not None


def test_no_inline_fill_attributes():
    for name in figures.build_targets():
        root, text = load(name)
        for node in root.iter():
            assert "fill" not in node.attrib, (name, node.tag)
        assert 'style="' not in text


def test_f2_carries_worst_and_rss_millivolts():
    _, text = load("S1-F2-error-budget.svg")
    assert "4.5" in text
    assert "2.5159" in text
    assert "1.3115" in text
    assert "1.4" in text


def test_f3_carries_settling_and_scan_ms():
    _, text = load("S1-F3-settling-scan.svg")
    assert "621.46" in text
    assert "10.26" in text
    assert "10 ms" in text


def test_f4_carries_three_windows_and_budgets():
    _, text = load("S1-F4-filter-budget.svg")
    for window in ("N=1", "N=5", "N=9"):
        assert window in text
    assert "77" in text and "117" in text and "157" in text


def test_references_are_relative_and_inside_repo():
    for name in figures.build_targets():
        _, text = load(name)
        for reference in re.findall(r"(?:href|src)=\"([^\"]+)\"", text):
            assert not reference.startswith("data:")
            assert not reference.startswith("http")


def test_f1_labels_are_readable_at_mobile_figure_width():
    root, _ = load("S1-F1-sense-chain.svg")
    width = float(root.attrib["viewBox"].split()[2])
    css = root.find(f"{NS}style").text
    sizes = {
        name: float(size)
        for name, size in re.findall(r"\.([\w-]+)\s*\{[^}]*?font\s*:[^;]*?(\d+(?:\.\d+)?)px", css)
    }
    for label in root.iter(f"{NS}text"):
        classes = label.get("class", "").split()
        font_size = next(sizes[name] for name in reversed(classes) if name in sizes)
        assert font_size * min(1, 350 / width) >= 12, label.text
