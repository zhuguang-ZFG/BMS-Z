"""Structural contracts for S3 precharge figures; geometry stays a user-eye check."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ASSETS = ROOT / "bms-book" / "engineering" / "assets" / "s3-precharge"

spec = importlib.util.spec_from_file_location("make_s3_figures", HERE / "make_s3_figures.py")
assert spec is not None and spec.loader is not None
maker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = maker
spec.loader.exec_module(maker)


def test_generated_files_match_builder_output():
    targets = maker.build_targets()
    assert len(targets) == 5
    for name, content in targets.items():
        path = ASSETS / name
        assert path.exists()
        assert path.read_text(encoding="utf-8") == content


@pytest.mark.parametrize(
    "name",
    [
        "S3-F1-current-paths.svg",
        "S3-F2-energy-account.svg",
        "S3-F3-state-timeline.svg",
        "S3-F4-validity-evidence.svg",
        "S3-F5-device-limits.svg",
    ],
)
def test_s3_svgs_have_title_role_and_no_inline_fill(name):
    raw = (ASSETS / name).read_text(encoding="utf-8")
    assert 'role="img"' in raw
    assert "<title>" in raw and "<desc>" in raw
    assert 'fill="#' not in raw and 'fill="' not in raw


def test_f2_anchors_95_percent_and_energy_identity():
    raw = (ASSETS / "S3-F2-energy-account.svg").read_text(encoding="utf-8")
    for anchor in ("0.50927", "152", "79.8", "72.2", "160", "80"):
        assert anchor in raw


def test_f5_anchors_inrush_and_residual_current():
    raw = (ASSETS / "S3-F5-device-limits.svg").read_text(encoding="utf-8")
    for anchor in ("2.35294", "0.118", "1000"):
        assert anchor in raw


def test_f3_keeps_four_signal_rows():
    raw = (ASSETS / "S3-F3-state-timeline.svg").read_text(encoding="utf-8")
    for label in ("命令", "辅助触点", "母线", "环路电流", "故障"):
        assert label in raw


def test_referenced_images_have_valid_relative_urls():
    for svg in ASSETS.glob("*.svg"):
        assert len(svg.read_bytes()) > 500
