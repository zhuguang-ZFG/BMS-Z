"""Regression tests for the D25 safety-argument slice."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import d25_safety_argument as d25

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]


def test_seed_argument_passes_audit_with_frozen_counts():
    graph = d25.build_argument()
    audit = d25.audit_argument(REPO_ROOT, graph)
    assert audit["counts"]["claims"] == 3
    assert audit["counts"]["gaps"] == 2
    assert audit["counts"]["evidence"] == 6
    assert audit["counts"]["findings"] == 0
    assert audit["verdict"] == "pass"


def test_silent_claim_without_evidence_or_gap_is_found():
    graph = {"claims": [{"id": "A9", "statement": "无证据无缺口的声明", "evidence": [], "gaps": []}], "gaps": []}
    audit = d25.audit_argument(REPO_ROOT, graph)
    assert audit["verdict"] == "fail"
    assert any(f["kind"] == "silent_claim" and f["unit"] == "A9" for f in audit["findings"])


def test_unresolvable_evidence_name_is_found():
    graph = {
        "claims": [{"id": "A9", "statement": "证据名编造", "evidence": ["test_no_such_test_exists"], "gaps": []}],
        "gaps": [],
    }
    audit = d25.audit_argument(REPO_ROOT, graph)
    assert audit["verdict"] == "fail"
    assert any(f["kind"] == "unresolved_evidence" for f in audit["findings"])


def test_claim_with_declared_gap_and_no_evidence_passes():
    """缺口显式声明就是诚实的论证：无证据 + 有 gap ≠ 沉默。"""
    graph = {
        "claims": [{"id": "A9", "statement": "只有缺口的声明", "evidence": [], "gaps": ["G01"]}],
        "gaps": [{"id": "G01", "blocks": ["A9"], "blocking_source_id": "SRC06",
                  "owner": "系统组", "status": "待补",
                  "next_action": "取得 SRC06 条款并建立记录链"}],
    }
    audit = d25.audit_argument(REPO_ROOT, graph)
    assert audit["verdict"] == "pass"


def test_malformed_gap_is_found():
    graph = {
        "claims": [{"id": "A9", "statement": "x", "evidence": [], "gaps": ["G9"]}],
        "gaps": [{"id": "G9", "blocks": ["A9"], "blocking_source_id": "WISHFUL", "owner": "", "status": "待补"}],
    }
    audit = d25.audit_argument(REPO_ROOT, graph)
    assert audit["verdict"] == "fail"
    assert any(f["kind"] == "malformed_gap" and f["unit"] == "G9" for f in audit["findings"])


def test_gap_blocking_source_must_be_adopted_id():
    graph = {
        "claims": [{"id": "A9", "statement": "x", "evidence": [], "gaps": ["G9"]}],
        "gaps": [{"id": "G9", "blocks": ["A9"], "blocking_source_id": "SRC99", "owner": "组", "status": "待补"}],
    }
    audit = d25.audit_argument(REPO_ROOT, graph)
    assert audit["verdict"] == "fail"
    assert any(f["kind"] == "malformed_gap" for f in audit["findings"])


def test_evidence_gap_ledger_is_sorted_and_actionable():
    ledger = d25.evidence_gap_ledger(d25.build_argument())
    ids = [row["id"] for row in ledger]
    assert ids == sorted(ids) == ["G01", "G02"]
    for row in ledger:
        assert row["blocking_source_id"] in ("SRC01", "SRC06")
        assert row["owner"] and row["status"] == "待补"
        assert row["blocks"], "缺口必须写明阻塞哪条论证"
        assert len(row["next_action"]) >= 20, "actionable = 有具体闭合动作，不是只有责任人"


def test_gap_without_next_action_is_malformed():
    graph = {
        "claims": [{"id": "A9", "statement": "x", "evidence": [], "gaps": ["G9"]}],
        "gaps": [{"id": "G9", "blocks": ["A9"], "blocking_source_id": "SRC06",
                  "owner": "组", "status": "待补", "next_action": ""}],
    }
    audit = d25.audit_argument(REPO_ROOT, graph)
    assert audit["verdict"] == "fail"
    assert any(f["kind"] == "malformed_gap" and "next_action" in f["detail"] for f in audit["findings"])


def test_ledger_is_pure_view_and_audit_rejects_bad_status():
    """ledger 是视图不做状态词表校验；词表归 S3 管。"""
    graph = d25.build_argument()
    graph["gaps"][0]["status"] = "状态乱写"
    audit = d25.audit_argument(REPO_ROOT, graph)
    assert any(f["kind"] == "malformed_gap" for f in audit["findings"])
    assert audit["verdict"] == "fail"
    ledger = d25.evidence_gap_ledger(graph)
    assert ledger[0]["status"] == "状态乱写", "ledger 如实反映图，不替审计做决定"


def test_asymmetric_gap_claim_side_is_found():
    """claim 声明了缺口，但 gap.blocks 没有它。"""
    graph = d25.build_argument()
    graph["gaps"][0]["blocks"] = []  # G01 不再承认阻塞 A01，但 A01 仍声明 G01
    audit = d25.audit_argument(REPO_ROOT, graph)
    assert any(f["kind"] == "asymmetric_gap" for f in audit["findings"])
    assert audit["verdict"] == "fail"


def test_asymmetric_gap_ledger_side_is_found():
    """gap.blocks 加了 claim，但 claim 没声明该缺口。"""
    graph = d25.build_argument()
    graph["gaps"][1]["blocks"] = ["A01", "A02", "A03", "A09"]
    audit = d25.audit_argument(REPO_ROOT, graph)
    assert any(f["kind"] == "asymmetric_gap" and f["unit"] == "G02" for f in audit["findings"])
    assert audit["verdict"] == "fail"


def test_cli_default_export(tmp_path):
    result = subprocess.run(
        [sys.executable, str(HERE / "d25_safety_argument.py"), "--out", str(tmp_path)],
        capture_output=True, text=True, cwd=str(HERE), check=False,
    )
    assert result.returncode == 0, result.stderr
    audit = json.loads((tmp_path / "safety_argument.json").read_text(encoding="utf-8"))
    assert audit["verdict"] == "pass"
    ledger = json.loads((tmp_path / "evidence_gap_ledger.json").read_text(encoding="utf-8"))
    assert [row["id"] for row in ledger] == ["G01", "G02"]
