from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
VIDEO = ROOT / "tools" / "video"
BOILERPLATE = re.compile(
    r"值得注意(?:的是)?|需要注意(?:的是)?|不难发现|显而易见|"
    r"总而言之|综上所述|本章将|接下来我们|让我们"
)
CONTRAST_FRAME = re.compile(r"不是[^。！？\n]{0,80}而是")


def test_microcourse_is_separate_from_eight_part_series() -> None:
    series = sorted((VIDEO / "specs").glob("*.json"))
    micros = sorted(
        path for path in (VIDEO / "microcourses").glob("*.json")
        if not path.name.endswith(".FACTS.json")
    )
    assert len(series) == 8
    assert [path.stem for path in micros] == [
        "m01-load-voltage-drop",
        "m02-ocv-trust",
        "m03-protection-line",
    ]


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
        ("m03-protection-line", "microcourse / 5 段 / 12 个 beat / 3 条验收"),
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


@pytest.mark.parametrize(
    "slug", ["m01-load-voltage-drop", "m02-ocv-trust", "m03-protection-line"]
)
def test_every_microcourse_beat_points_to_a_real_fact(slug: str) -> None:
    spec = json.loads((VIDEO / "microcourses" / f"{slug}.json").read_text(encoding="utf-8"))
    ledger_path = ROOT / spec["facts_file"]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert ledger["slug"] == slug

    facts = {row["id"]: row for row in ledger["facts"]}
    assert facts
    used: set[str] = set()
    for segment in spec["segments"]:
        for beat in segment["beats"]:
            assert beat.get("facts"), f"{slug}/{segment['id']} 有 beat 没有事实引用"
            assert set(beat["facts"]) <= set(facts)
            used.update(beat["facts"])
    assert used == set(facts), f"{slug} 有孤儿事实：{set(facts) - used}"

    for fact in facts.values():
        assert fact["claim"].strip()
        assert fact["sources"]
        for source in fact["sources"]:
            if "path" in source:
                assert (ROOT / source["path"]).is_file(), source
            else:
                assert source["url"].startswith(("https://", "http://")), source
            assert source["locator"].strip()


@pytest.mark.parametrize(
    "slug", ["m01-load-voltage-drop", "m02-ocv-trust", "m03-protection-line"]
)
def test_microcourses_share_the_notebook_margin_visual_system(slug: str) -> None:
    spec = json.loads((VIDEO / "microcourses" / f"{slug}.json").read_text(encoding="utf-8"))
    assert spec["visual_system"] == {
        "style_id": "FH-022",
        "style_name": "Notebook Margin Cartoon",
        "palette": ["C-06", "C-27", "C-29"],
        "direction": spec["visual_system"]["direction"],
    }
    assert spec["visual_system"]["direction"].strip()


def test_third_microcourse_separates_action_line_command_and_feedback() -> None:
    spec = json.loads(
        (VIDEO / "microcourses" / "m03-protection-line.json").read_text(encoding="utf-8")
    )
    assert spec["checklist"] == [
        "能区分正常充电截止、保护动作线与化学边界，并说明数值来源",
        "能沿 tick 46/48/49 分开首次越线、禁充命令和电流反馈",
        "能复算 57 ms、77 ms 与 23 ms，并解释短路为什么不等三拍",
    ]
    assert len(spec["segments"]) == 5
    assert sum(len(segment["beats"]) for segment in spec["segments"]) == 12


@pytest.mark.parametrize(
    "slug", ["m01-load-voltage-drop", "m02-ocv-trust", "m03-protection-line"]
)
def test_microcourse_voiceovers_avoid_template_clusters(slug: str) -> None:
    spec = json.loads((VIDEO / "microcourses" / f"{slug}.json").read_text(encoding="utf-8"))
    voiceover = "\n".join(
        beat["vo"] for segment in spec["segments"] for beat in segment["beats"]
    )
    assert not BOILERPLATE.findall(voiceover)
    assert len(CONTRAST_FRAME.findall(voiceover)) < 3
