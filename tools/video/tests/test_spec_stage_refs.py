"""阶段页「引用清单」与动画源解析：迁移到逐帧手绘序列后仍要认得出。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "video"))

import common  # noqa: E402
import spec  # noqa: E402


def test_iter_stage_svgs_normalizes_handraw_links(tmp_path):
    """正文链 handraw/exports/<slug>.webp 时，清单仍要给出 <slug>.svg。

    回归：正则只认 `circuits/assets/*.svg` 时，换链后的阶段页对迁移过的图
    一律「不在引用清单里」，ep01/ep02 的 lint 直接判红。
    """
    doc = tmp_path / "stage-x.md"
    doc.write_text(
        "![a](../circuits/assets/plain.svg)\n"
        "![b](../circuits/handraw/exports/migrated.webp)\n"
        "![c](circuits/assets/plain.svg)\n",
        encoding="utf-8",
    )
    assert spec.iter_stage_svgs(doc) == ["plain.svg", "migrated.svg"]


def test_svg_source_falls_back_to_archive():
    """归档后的源仍要能被视频管线读到。"""
    live = common.ASSETS / "cell-inconsistency-barrel.svg"
    assert not live.exists()
    assert common.svg_source("cell-inconsistency-barrel.svg").parent.name == "archive"


def test_svg_source_prefers_live_directory():
    """还没迁移的图仍从活目录取，不要因为归档回退把两边混用。"""
    name = "c-rate.svg"
    if not (common.ASSETS / name).exists():
        pytest.skip(f"{name} 不在活目录")
    assert common.svg_source(name).parent == common.ASSETS


def test_svg_source_reports_missing():
    with pytest.raises(FileNotFoundError):
        common.svg_source("definitely-not-an-animation.svg")
