"""Check published curves and budgets against experiment data, not filenames."""
import copy
import importlib.util
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[2]
SVG = "{http://www.w3.org/2000/svg}"


def generator():
    spec = importlib.util.spec_from_file_location("grid_figures", ROOT / "tools/gen_hppc_grid_evidence.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generation_is_reproducible_and_matches_published_assets(tmp_path):
    script = ROOT / "tools/gen_hppc_grid_evidence.py"
    for folder in (tmp_path / "first", tmp_path / "second"):
        subprocess.run([sys.executable, str(script), "--out", str(folder)], check=True, cwd=ROOT)
    files = sorted((tmp_path / "first").glob("*.svg"))
    assert len(files) == 2
    for path in files:
        assert path.read_bytes() == (tmp_path / "second" / path.name).read_bytes()
        assert path.read_bytes() == (ROOT / "bms-book/assets" / path.name).read_bytes()
        tree = ET.fromstring(path.read_bytes())
        assert tree.attrib["role"] == "img"
        assert tree.find(SVG + "title").text
        assert tree.find(SVG + "desc").text
        assert "合成" in "".join(tree.itertext())


def test_curve_geometry_represents_report_samples():
    m = generator()
    report = m.build_report()
    tree = ET.fromstring(m.render_figures(report)["hppc-grid-hidden-curvature.svg"])
    curve = tree.find(f".//{SVG}polyline[@data-series='true']")
    points = [tuple(map(float, p.split(","))) for p in curve.attrib["points"].split()]
    data = report["hidden_curvature"]
    assert len(points) == len(data["curve_soc"])
    for (x, y), soc, volt in zip(points, data["curve_soc"], data["curve_true_v"], strict=True):
        # Recover physical values from the figure's explicitly labelled plot range.
        assert .4 + (x-100)/760*.2 == pytest.approx(soc, abs=1e-6)
        assert 3.50 + (440-y)/260*.20 == pytest.approx(volt, abs=1e-6)
    labels = "".join(tree.itertext())
    assert "20 mV" in labels and "SOC" in labels


def test_budget_bars_follow_report_and_preserve_node_bias():
    m = generator()
    report = m.build_report()
    changed = copy.deepcopy(report)
    changed["axis_refinement"][0]["temperature_bound_mv"] = 1.25
    changed["axis_refinement"][0]["bound_mv"] = 1.75
    for data in (report, changed):
        tree = ET.fromstring(m.render_figures(data)["hppc-grid-error-budget.svg"])
        for i, row in enumerate(data["axis_refinement"]):
            for axis, key in (("soc", "soc_bound_mv"), ("temperature", "temperature_bound_mv")):
                bar = tree.find(f".//{SVG}rect[@id='budget-{i}-{axis}']")
                assert float(bar.attrib["width"])/140 == pytest.approx(row[key])
        assert "2 mV" in "".join(tree.itertext())
    assert m.render_figures(report) != m.render_figures(changed)
