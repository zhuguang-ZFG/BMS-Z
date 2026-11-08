"""Negative cases for the engineering registry checker: every removal or drift fails loudly."""

import json
from pathlib import Path

import pytest

from tools.check_engineering import check, ROOT

SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" role="img"><title>t</title>'
    '<desc>d</desc><rect width="10" height="10"/></svg>'
)
SCRIPT = 'SCENARIO_ID = "S1-sense-chain"\n'
TESTFILE = "def test_anchor():\n    assert True\n"


def build_tree(root: Path) -> Path:
    (root / "bms-book/bridges").mkdir(parents=True)
    (root / "bms-book/engineering/assets/s1").mkdir(parents=True)
    (root / "code/engineering/measurement").mkdir(parents=True)
    (root / "docs/superpowers/plans/bms-depth").mkdir(parents=True)
    (root / "bms-book/bridges/B01-电路与能量.md").write_text(
        "# B01\n\n## 讲解\n\n## 核对题\n", encoding="utf-8"
    )
    unit = (
        "# S1　样章\n\n本样章全是教学参数，不能替代实测与数据手册。"
        '<img src="assets/s1/S1-F1.svg" alt="图">\n\n'
        "## S1.1 误差\n\n锚 4.5 mV\n\n## S1.2 动手\n\n## S1.3 反例\n\n## S1.4 冻结\n"
    )
    (root / "bms-book/engineering/S1.md").write_text(unit, encoding="utf-8")
    (root / "bms-book/engineering/P1-先修最小包.md").write_text(
        "```mermaid\ngraph LR\n  B01[B01] --> S1[S1]\n```\n", encoding="utf-8"
    )
    (root / "docs/superpowers/plans/bms-depth/source-adoption.md").write_text(
        "| OS04 | read |\n| SRC02 | pending |\n", encoding="utf-8"
    )
    (root / "bms-book/engineering/assets/s1/S1-F1.svg").write_text(
        SVG, encoding="utf-8"
    )
    (root / "code/engineering/measurement/s1_measurement.py").write_text(
        SCRIPT, encoding="utf-8"
    )
    (root / "code/engineering/measurement/test_s1_measurement.py").write_text(
        TESTFILE, encoding="utf-8"
    )
    (root / "code/engineering/measurement/make_s1_figures.py").write_text(
        "", encoding="utf-8"
    )
    manifest = {
        "schema_version": 1,
        "units": [
            {
                "id": "B01",
                "kind": "bridge",
                "status": "locally_verified",
                "source": "bms-book/bridges/B01-电路与能量.md",
                "prerequisites": [],
                "experiments": [],
                "figures": [],
                "levels": ["core"],
                "fingerprint": None,
            },
            {
                "id": "S1",
                "kind": "sample",
                "status": "locally_verified",
                "source": "bms-book/engineering/S1.md",
                "prerequisites": ["B01"],
                "experiments": ["E01"],
                "figures": ["S1-F1"],
                "levels": ["intro", "core", "derivation", "lab"],
                "fingerprint": None,
            },
        ],
    }
    claims = {
        "schema_version": 1,
        "claims": [
            {
                "id": "S1-C01",
                "unit": "S1",
                "anchor": "S1.1",
                "statement": "锚 4.5 mV",
                "evidence": ["test_anchor"],
                "source_ids": ["OS04"],
                "fingerprint": None,
            }
        ],
    }
    figures = {
        "schema_version": 1,
        "figures": [
            {
                "id": "S1-F1",
                "unit": "S1",
                "kind": "mechanism",
                "file": "bms-book/engineering/assets/s1/S1-F1.svg",
                "generator": "code/engineering/measurement/make_s1_figures.py",
                "appears_in": "lead",
                "answers": "问",
                "fingerprint": None,
            }
        ],
    }
    experiments = {
        "schema_version": 1,
        "experiments": [
            {
                "id": "E01",
                "unit": "S1",
                "family": "测量",
                "scenarios": ["S1-sense-chain"],
                "script": "code/engineering/measurement/s1_measurement.py",
                "tests": ["code/engineering/measurement/test_s1_measurement.py"],
                "figure_generator": "code/engineering/measurement/make_s1_figures.py",
                "student_tasks_anchor": "S1.2",
                "rejects_anchor": "S1.3",
                "frozen_anchor": "S1.4",
                "source_ids": ["OS04"],
                "acceptance": "对照锚点",
            }
        ],
    }
    for name, data in (
        ("manifest.json", manifest),
        ("claims.json", claims),
        ("figures.json", figures),
        ("experiments.json", experiments),
    ):
        (root / "bms-book/engineering" / name).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    assert check(root=root, update=True) == []
    return root


def read(root: Path, name: str) -> dict:
    return json.loads((root / "bms-book/engineering" / name).read_text(encoding="utf-8"))


def write(root: Path, name: str, data: dict) -> None:
    (root / "bms-book/engineering" / name).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    return build_tree(tmp_path)


def test_real_repository_registries_pass():
    assert check(root=ROOT) == []


def test_valid_fixture_passes(tree):
    assert check(root=tree) == []


def test_prerequisite_missing_mermaid_edge_fails(tree):
    manifest = read(tree, "manifest.json")
    manifest["units"][1]["prerequisites"] = ["B01", "B05"]
    write(tree, "manifest.json", manifest)
    problems = check(root=tree)
    assert any("unknown prerequisite B05" in p for p in problems)


def test_prerequisite_cycle_fails(tree):
    pack = tree / "bms-book/engineering/P1-先修最小包.md"
    pack.write_text(
        "```mermaid\ngraph LR\n  B01[B01] --> S1[S1]\n  S1 --> B01\n```\n",
        encoding="utf-8",
    )
    manifest = read(tree, "manifest.json")
    manifest["units"][0]["prerequisites"] = ["S1"]
    write(tree, "manifest.json", manifest)
    assert any("cycle" in p for p in check(root=tree))


def test_section_drift_fails_until_update(tree):
    unit = tree / "bms-book/engineering/S1.md"
    text = unit.read_text(encoding="utf-8").replace("锚 4.5 mV", "锚 4.6 mV")
    unit.write_text(text, encoding="utf-8")
    problems = check(root=tree)
    assert any("S1-C01: anchored section drifted" in p for p in problems)
    assert any("S1: source drifted" in p for p in problems)
    assert check(root=tree, update=True) == []
    assert check(root=tree) == []


def test_removed_figure_file_fails(tree):
    (tree / "bms-book/engineering/assets/s1/S1-F1.svg").unlink()
    assert any("S1-F1: file missing" in p for p in check(root=tree))


def test_unregistered_asset_fails(tree):
    extra = tree / "bms-book/engineering/assets/s1/S1-F2-extra.svg"
    extra.write_text(SVG, encoding="utf-8")
    assert any("unregistered asset" in p for p in check(root=tree))


def test_figure_dropped_from_text_fails(tree):
    unit = tree / "bms-book/engineering/S1.md"
    unit.write_text(
        unit.read_text(encoding="utf-8").replace(
            '<img src="assets/s1/S1-F1.svg" alt="图">', ""
        ),
        encoding="utf-8",
    )
    assert any("S1-F1: S1-F1.svg not referenced" in p for p in check(root=tree))


def test_unknown_source_id_fails(tree):
    claims = read(tree, "claims.json")
    claims["claims"][0]["source_ids"] = ["OS99"]
    write(tree, "claims.json", claims)
    assert any("unknown source_id OS99" in p for p in check(root=tree))


def test_missing_evidence_test_fails(tree):
    claims = read(tree, "claims.json")
    claims["claims"][0]["evidence"] = ["test_no_such_test"]
    write(tree, "claims.json", claims)
    assert any("test_no_such_test not found" in p for p in check(root=tree))


def test_missing_anchor_fails(tree):
    claims = read(tree, "claims.json")
    claims["claims"][0]["anchor"] = "S9.9"
    write(tree, "claims.json", claims)
    assert any("S1-C01: anchor S9.9 not found" in p for p in check(root=tree))


def test_schema_version_mismatch_fails(tree):
    claims = read(tree, "claims.json")
    claims["schema_version"] = 99
    write(tree, "claims.json", claims)
    assert any("claims: schema_version" in p for p in check(root=tree))


def test_scenario_identity_must_appear(tree):
    experiments = read(tree, "experiments.json")
    experiments["experiments"][0]["scenarios"] = ["S1-ghost-scenario"]
    write(tree, "experiments.json", experiments)
    assert any("S1-ghost-scenario not found" in p for p in check(root=tree))


def test_experiment_needs_acceptance(tree):
    experiments = read(tree, "experiments.json")
    experiments["experiments"][0]["acceptance"] = ""
    write(tree, "experiments.json", experiments)
    assert any("E01: acceptance" in p for p in check(root=tree))


def set_levels(tree, uid: str, levels: list[str]) -> None:
    manifest = read(tree, "manifest.json")
    for unit in manifest["units"]:
        if unit["id"] == uid:
            unit["levels"] = levels
    write(tree, "manifest.json", manifest)


def test_levels_must_follow_ladder_order(tree):
    set_levels(tree, "S1", ["lab", "intro"])
    assert any(
        "S1: levels must be unique and in ladder order" in p for p in check(root=tree)
    )


def test_unknown_level_fails(tree):
    set_levels(tree, "B01", ["core", "supereasy"])
    assert any("unknown level supereasy" in p for p in check(root=tree))


def test_intro_needs_boundary_statement(tree):
    unit = tree / "bms-book/engineering/S1.md"
    unit.write_text(
        unit.read_text(encoding="utf-8").replace("不能替代实测与数据手册。", ""),
        encoding="utf-8",
    )
    assert any("S1: intro lead needs" in p for p in check(root=tree))


def test_core_needs_mechanism_figure(tree):
    figures = read(tree, "figures.json")
    figures["figures"][0]["kind"] = "data"
    write(tree, "figures.json", figures)
    assert any(
        "S1: core level needs at least one mechanism figure" in p
        for p in check(root=tree)
    )


def test_derivation_needs_registered_claim(tree):
    claims = read(tree, "claims.json")
    claims["claims"] = []
    write(tree, "claims.json", claims)
    assert any("S1: derivation level needs" in p for p in check(root=tree))


def test_lab_needs_registered_experiment(tree):
    experiments = read(tree, "experiments.json")
    experiments["experiments"] = []
    write(tree, "experiments.json", experiments)
    problems = check(root=tree)
    assert any("S1: lab level needs" in p for p in problems)


def test_research_level_reserved_for_r_units(tree):
    set_levels(tree, "S1", ["intro", "core", "derivation", "lab", "research"])
    assert any("research level is reserved" in p for p in check(root=tree))
