from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
VIDEO = ROOT / "tools" / "video"


def test_microcourse_is_separate_from_eight_part_series() -> None:
    series = sorted((VIDEO / "specs").glob("*.json"))
    micros = sorted((VIDEO / "microcourses").glob("*.json"))
    assert len(series) == 8
    assert [path.stem for path in micros] == ["m01-load-voltage-drop", "m02-ocv-trust"]


def test_first_microcourse_keeps_one_input_and_two_checks() -> None:
    path = VIDEO / "microcourses" / "m01-load-voltage-drop.json"
    spec = json.loads(path.read_text(encoding="utf-8"))
    assert spec["kind"] == "microcourse"
    assert "20 A" in spec["_note"]
    assert spec["checklist"] == [
        "能算出 20 A × 20 mΩ = 0.40 V，并得到带载约 3.5 V",
        "能解释撤载回弹、低温增阻与 SOC 不会瞬时跳变的区别",
    ]
    assert len(spec["segments"]) == 5
    assert sum(len(segment["beats"]) for segment in spec["segments"]) == 12


@pytest.mark.parametrize(
    ("slug", "summary"),
    [
        ("m01-load-voltage-drop", "microcourse / 5 段 / 12 个 beat / 2 条验收"),
        ("m02-ocv-trust", "microcourse / 5 段 / 12 个 beat / 3 条验收"),
    ],
)
def test_microcourses_pass_the_real_spec_gate(slug: str, summary: str) -> None:
    result = subprocess.run(
        [sys.executable, str(VIDEO / "spec.py"), "--check", slug],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert summary in result.stdout


def test_ocv_microcourse_keeps_the_four_qualification_gates() -> None:
    spec = json.loads(
        (VIDEO / "microcourses" / "m02-ocv-trust.json").read_text(encoding="utf-8")
    )
    assert spec["checklist"] == [
        "能解释为什么 0 A 不等于下一拍就是 OCV",
        "能列出电流、变化率、温度与充放电历史四道资格门",
        "能解释 LFP 平台上 5 mV 为什么可能对应约 6.7 个百分点",
    ]
    assert spec["master_gain_db"] == -1.0
