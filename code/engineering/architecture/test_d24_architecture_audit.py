"""Regression tests for the D24 architecture audit slice."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import d24_architecture_audit as d24

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]


def test_real_registry_audit_passes_with_frozen_counts():
    report = d24.audit_registry(REPO_ROOT)
    assert report["counts"]["units"] == 42
    assert report["counts"]["claims"] == 91
    assert report["counts"]["experiments"] == 35
    assert report["counts"]["figures"] == 62
    assert report["verdict"] == "pass"
    assert report["findings"] == []


def test_d24_c01_statement_matches_frozen_audit_counts():
    """claim 自述的登记计数必须与审计实读一致。

    check_engineering 的 fingerprint 只覆盖锚定章节，不哈希 statement 文本；
    这个回归把 statement 与 report.counts 绑在一起，防止自述悄悄漂移。
    """
    claims_path = REPO_ROOT / "bms-book" / "engineering" / "claims.json"
    claims = json.loads(claims_path.read_text(encoding="utf-8"))["claims"]
    claim = next(c for c in claims if c["id"] == "D24-C01")
    counts = d24.audit_registry(REPO_ROOT)["counts"]
    expected = (
        f"{counts['units']} 单元/{counts['claims']} 声明/"
        f"{counts['experiments']} 实验/{counts['figures']} 图版"
    )
    assert expected in claim["statement"], (claim["statement"], expected)


def _write_mini_registry(root: Path, manifest: dict, experiments: list | None = None) -> None:
    eng = root / "bms-book" / "engineering"
    eng.mkdir(parents=True, exist_ok=True)
    (eng / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (eng / "claims.json").write_text(
        json.dumps({"claims": manifest.pop("_claims", [])}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (eng / "experiments.json").write_text(
        json.dumps({"experiments": experiments or []}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (eng / "figures.json").write_text(json.dumps({"figures": []}, ensure_ascii=False, indent=2), encoding="utf-8")


def test_missing_prereq_reference_is_found(tmp_path):
    manifest = {
        "units": [
            {"id": "U1", "kind": "unit", "status": "locally_verified", "source": "u1.md",
             "prerequisites": ["GHOST"], "experiments": [], "figures": []},
        ]
    }
    _write_mini_registry(tmp_path, manifest)
    report = d24.audit_registry(tmp_path)
    assert report["verdict"] == "fail"
    assert any(f["kind"] == "missing_prereq" and f["unit"] == "U1" for f in report["findings"])


def test_prerequisite_cycle_is_found(tmp_path):
    manifest = {
        "units": [
            {"id": "A", "kind": "unit", "status": "planned", "prerequisites": ["B"], "experiments": [], "figures": []},
            {"id": "B", "kind": "unit", "status": "planned", "prerequisites": ["A"], "experiments": [], "figures": []},
        ]
    }
    _write_mini_registry(tmp_path, manifest)
    report = d24.audit_registry(tmp_path)
    assert report["verdict"] == "fail"
    assert any(f["kind"] == "prereq_cycle" for f in report["findings"])


def test_claim_with_neither_evidence_nor_sources_is_found(tmp_path):
    manifest = {
        "units": [
            {"id": "U1", "kind": "unit", "status": "locally_verified", "source": "u1.md",
             "prerequisites": [], "experiments": [], "figures": []},
        ],
        "_claims": [
            {"id": "U1-C01", "unit": "U1", "anchor": "U1.1", "statement": "既无证据也无来源的声明",
             "evidence": [], "source_ids": []},
        ],
    }
    _write_mini_registry(tmp_path, manifest)
    report = d24.audit_registry(tmp_path)
    assert report["verdict"] == "fail"
    assert any(f["kind"] == "ungrounded_claim" and f["unit"] == "U1-C01" for f in report["findings"])


def test_local_synthesis_claim_with_tests_but_no_sources_passes(tmp_path):
    """D03 章明示 12 字段表是结构工具：有测试证据、无外部来源是诚实的。"""
    manifest = {
        "units": [
            {"id": "U1", "kind": "unit", "status": "locally_verified", "source": "u1.md",
             "prerequisites": [], "experiments": [], "figures": []},
        ],
        "_claims": [
            {"id": "U1-C01", "unit": "U1", "anchor": "U1.1", "statement": "本地合成结构合同",
             "evidence": ["test_structure_contract"], "source_ids": []},
        ],
    }
    _write_mini_registry(tmp_path, manifest)
    report = d24.audit_registry(tmp_path)
    assert report["verdict"] == "pass"
    assert report["findings"] == []


def test_missing_experiment_script_is_found(tmp_path):
    manifest = {
        "units": [
            {"id": "U1", "kind": "unit", "status": "locally_verified", "source": "u1.md",
             "prerequisites": [], "experiments": ["E99"], "figures": []},
        ],
    }
    experiments = [
        {"id": "E99", "unit": "U1", "scenarios": [], "script": "code/nope.py", "tests": [],
         "student_tasks_anchor": "U1.4", "rejects_anchor": "U1.3", "frozen_anchor": "U1.6",
         "report_identity": "x", "source_ids": [], "acceptance": "y"},
    ]
    _write_mini_registry(tmp_path, manifest, experiments=experiments)
    report = d24.audit_registry(tmp_path)
    assert report["verdict"] == "fail"
    assert any(f["kind"] == "missing_artifact" and f["unit"] == "E99" for f in report["findings"])


def test_planned_unit_blocking_verified_unit_warns_not_fails(tmp_path):
    manifest = {
        "units": [
            {"id": "U1", "kind": "unit", "status": "planned", "prerequisites": [], "experiments": [], "figures": []},
            {"id": "U2", "kind": "unit", "status": "locally_verified", "source": "u2.md",
             "prerequisites": ["U1"], "experiments": [], "figures": []},
        ],
    }
    _write_mini_registry(tmp_path, manifest)
    report = d24.audit_registry(tmp_path)
    assert report["verdict"] == "pass"
    assert any(f["kind"] == "planned_blocks_verified" and f["severity"] == "warning" for f in report["findings"])


def test_open_source_review_protocol_is_pinned():
    protocol = d24.open_source_review_protocol()
    assert len(protocol) == 6
    dimensions = [item["dimension"] for item in protocol]
    assert dimensions == ["license", "provenance", "freshness", "debounce", "evidence", "boundaries"]
    for item in protocol:
        assert item["question"] and item["demand"]


def test_protocol_self_check_maps_each_demand_to_local_artifact():
    report = d24.protocol_self_check(REPO_ROOT)
    assert report["verdict"] == "pass"
    assert len(report["rows"]) == 6
    for row in report["rows"]:
        assert row["ok"], row["dimension"]
        assert row["path"] and row["must_contain"]
    assert report["snapshot"]["ok"]


def test_protocol_self_check_fails_on_empty_root(tmp_path):
    report = d24.protocol_self_check(tmp_path)
    assert report["verdict"] == "fail"
    assert all(not row["ok"] for row in report["rows"])
    assert not report["snapshot"]["ok"]


def test_protocol_self_check_fails_on_tampered_artifact(tmp_path):
    license_path = tmp_path / "LICENSE"
    license_path.write_text("proprietary, all rights reserved", encoding="utf-8")
    report = d24.protocol_self_check(tmp_path)
    license_row = [r for r in report["rows"] if r["dimension"] == "license"][0]
    assert license_row["artifact_present"] and license_row["content_ok"] is False
    assert report["verdict"] == "fail"


def test_protocol_self_check_fails_on_snapshot_drift(tmp_path):
    snap_dir = tmp_path / "docs" / "superpowers" / "plans"
    snap_dir.mkdir(parents=True)
    (snap_dir / "2026-11-08-bms-open-source-snapshot.json").write_text(
        '{"tampered": true}', encoding="utf-8"
    )
    report = d24.protocol_self_check(tmp_path)
    assert report["snapshot"]["ok"] is False
    assert report["verdict"] == "fail"


def test_traceability_matrix_has_one_row_per_active_claim():
    matrix = d24.traceability_matrix(REPO_ROOT)
    assert matrix["counts"]["rows"] == matrix["counts"]["active_claims"] == 91
    claim_ids = [row["claim"] for row in matrix["rows"]]
    assert len(claim_ids) == len(set(claim_ids)), "每条 active claim 恰好一行，不得静默丢弃"
    assert matrix["counts"]["unresolved_evidence"] == 0
    by_claim = {row["claim"]: row for row in matrix["rows"]}
    row = by_claim["D19-C05"]
    assert row["source_ids"] == ["SRC05"] and row["experiments"], row
    row = by_claim["D03-C02"]
    assert row["source_ids"] == [] and row["evidence"], "本地合成合同：无来源但有证据，必须可见而非隐藏"



def test_d24_doc_matrix_counts_match_report():
    """正文冻结的矩阵行数必须跟 traceability_matrix 实读一致。"""
    doc = (
        REPO_ROOT / "bms-book" / "engineering" / "D24-系统架构与开源审读.md"
    ).read_text(encoding="utf-8")
    counts = d24.traceability_matrix(REPO_ROOT)["counts"]
    expected = f"追溯矩阵 {counts['rows']} 行 = active claims {counts['active_claims']}"
    assert expected in doc, [line for line in doc.splitlines() if "追溯矩阵" in line]


def test_matrix_marks_unresolved_evidence_instead_of_dropping(tmp_path):
    manifest = {
        "units": [
            {"id": "U1", "kind": "unit", "status": "locally_verified",
             "source": "bms-book/engineering/u1.md",
             "prerequisites": [], "experiments": ["E1"], "figures": []},
        ],
        "_claims": [
            {"id": "U1-C01", "unit": "U1", "anchor": "U1.1", "statement": "证据名悬空",
             "evidence": ["test_gone"], "source_ids": ["OS07"]},
        ],
    }
    experiments = [
        {"id": "E1", "unit": "U1", "scenarios": [], "script": "s.py", "tests": ["t.py"],
         "student_tasks_anchor": "a", "rejects_anchor": "b", "frozen_anchor": "c",
         "report_identity": "x", "source_ids": [], "acceptance": "y"},
    ]
    _write_mini_registry(tmp_path, manifest, experiments=experiments)
    (tmp_path / "t.py").write_text("def test_other():\n    pass\n", encoding="utf-8")
    matrix = d24.traceability_matrix(tmp_path)
    assert matrix["counts"]["rows"] == 1
    assert matrix["rows"][0]["claim"] == "U1-C01", "行必须在，缺口可见"
    assert matrix["rows"][0]["evidence_resolved"] is False
    assert matrix["unresolved"] == ["U1-C01"]


def test_cli_writes_matrix(tmp_path):
    result = subprocess.run(
        [sys.executable, str(HERE / "d24_architecture_audit.py"),
         "--matrix", str(tmp_path / "matrix.json")],
        capture_output=True, text=True, cwd=str(HERE), check=False,
    )
    assert result.returncode == 0, result.stderr
    matrix = json.loads((tmp_path / "matrix.json").read_text(encoding="utf-8"))
    assert matrix["counts"]["rows"] == 91


def test_cli_default_audit(tmp_path):
    result = subprocess.run(
        [sys.executable, str(HERE / "d24_architecture_audit.py"), "--out", str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=str(HERE),
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "audit_report.json").read_text(encoding="utf-8"))
    assert report["verdict"] == "pass"
    assert (tmp_path / "protocol_self_check.json").is_file()
