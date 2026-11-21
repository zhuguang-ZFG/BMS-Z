"""Content checks for the D23 figure: every label the chapter cites must be
present and the numbers must match d23_precharge_insulation defaults."""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SVG = HERE.parents[2] / "bms-book" / "engineering" / "assets" / "d23-hv" / "D23-F1-precharge-insulation.svg"


def _module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_figure_exists_with_required_content():
    text = SVG.read_text(encoding="utf-8")
    for needle in (
        "D23-F1",
        "τ = 0.17 s",
        "t95 = 0.509 s",
        "supplied 152.0 J",
        "stored 72.2 J",
        "spent 79.8 J",
        "0.80 W",
        "7.98 W",
        "脉冲 @ 0/5/10 s",
        "R_iso+ = 1 MΩ",
        "R_iso− = 100 kΩ",
        "R_ref = 200 kΩ",
        "C_y = 100 nF",
        "36.36 V",
        "25.0 V",
        "τ_y = 6.25 ms",
        "3τ_y = 18.75 ms",
        "500 Ω/V → 200 kΩ",
    ):
        assert needle in text, needle
    assert text.count("<svg") == 1
    # 属性合法性：无残留 f-string 占位（CSS 块的花括号除外）
    for bad in ("x2y", "{energy", "{tau", "{t95", "{ins", "{pulse"):
        assert bad not in text, bad


def test_figure_numbers_match_module():
    d23 = _module("d23_precharge_insulation", HERE / "d23_precharge_insulation.py")
    text = SVG.read_text(encoding="utf-8")
    assert f"τ = {d23.tau_s():.2f} s" in text
    assert f"t95 = {d23.t_measure_s():.3f} s" in text
    assert f"{d23.pulse_energy_j():.1f} J" in text
    rep = d23.repetition_report()
    assert re.search(rf"{rep['avg_power_w']:.2f} W", text)
