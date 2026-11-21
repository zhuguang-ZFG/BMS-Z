"""Regression tests for the D28 design-review slice."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import d28_design_review as d28

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]




def _rerun_with_provenance(root: Path, drop: int = 0) -> dict:
    """在役复核员本地执行复跑命令的包（带来源，非 fresh 子进程）。"""
    import json as _json
    packet = json.loads(_json.dumps(d28.build_review_packet(root), ensure_ascii=False))
    if drop:
        packet["linked_claims"] = packet["linked_claims"][:-drop]
    packet["provenance"] = {
        "command": "python code/engineering/review/d28_design_review.py --out <dir>",
        "produced_by": "独立复核员（教学角色，须与作者不同人）",
    }
    return packet

def test_seed_packet_passes_review_with_frozen_counts():
    packet = d28.build_review_packet(REPO_ROOT)
    review = d28.audit_review(REPO_ROOT, packet, rerun_packet=_rerun_with_provenance(REPO_ROOT))
    assert review["counts"]["decisions"] == 1
    assert review["counts"]["linked_claims"] == 2
    assert review["counts"]["findings"] == 0
    assert review["verdict"] == "pass"


def test_reviewer_must_not_be_author():
    packet = d28.build_review_packet(REPO_ROOT)
    packet["reviewer"] = packet["author"]
    review = d28.audit_review(REPO_ROOT, packet)
    assert any(f["kind"] == "reviewer_not_independent" for f in review["findings"])
    assert review["verdict"] == "fail"


def test_reviewer_boundary_restatement_needs_teeth():
    packet = d28.build_review_packet(REPO_ROOT)
    packet["reviewer_boundary"] = "看过了，没问题"
    review = d28.audit_review(REPO_ROOT, packet)
    assert any(f["kind"] == "boundary_without_teeth" for f in review["findings"])


def test_decision_statement_passes_global_fidelity_floor():
    packet = d28.build_review_packet(REPO_ROOT)
    packet["decision_statement"] = "本设计直接给出功能安全结论"
    review = d28.audit_review(REPO_ROOT, packet)
    assert any(f["kind"] == "decision_exceeds_fidelity" for f in review["findings"])
    assert review["verdict"] == "fail"


def test_rerun_confirmation_must_match_packet_claims():
    """独立复核的硬动作：复跑后链接的 claim 集合不许少。"""
    packet = d28.build_review_packet(REPO_ROOT)
    rerun = _rerun_with_provenance(REPO_ROOT)
    rerun["linked_claims"] = rerun["linked_claims"][:1]
    review = d28.audit_review(REPO_ROOT, packet, rerun_packet=rerun)
    assert any(f["kind"] == "rerun_diverged" for f in review["findings"])
    assert review["verdict"] == "fail"


def test_no_rerun_at_all_fails_closed():
    packet = d28.build_review_packet(REPO_ROOT)
    review = d28.audit_review(REPO_ROOT, packet)
    assert any(f["kind"] == "rerun_evidence_missing" for f in review["findings"])
    assert review["verdict"] == "fail"


def test_rerun_without_command_provenance_fails_closed():
    packet = d28.build_review_packet(REPO_ROOT)
    rerun = d28.build_review_packet(REPO_ROOT)
    rerun["provenance"] = {"command": "", "produced_by": "someone"}
    review = d28.audit_review(REPO_ROOT, packet, rerun_packet=rerun)
    assert any(f["kind"] == "rerun_evidence_missing" for f in review["findings"])


def test_rerun_produced_by_author_is_not_independent():
    packet = d28.build_review_packet(REPO_ROOT)
    rerun = _rerun_with_provenance(REPO_ROOT)
    rerun["provenance"]["produced_by"] = packet["author"]
    review = d28.audit_review(REPO_ROOT, packet, rerun_packet=rerun)
    assert any(f["kind"] == "rerun_not_independent" for f in review["findings"])


def test_fresh_process_rerun_passes(tmp_path):
    packet = d28.build_review_packet(REPO_ROOT)
    rerun = d28.run_fresh_review(REPO_ROOT, tmp_path)
    review = d28.audit_review(REPO_ROOT, packet, rerun_packet=rerun)
    assert review["verdict"] == "pass"


def test_unlinked_claim_reference_is_found():
    packet = d28.build_review_packet(REPO_ROOT)
    packet["linked_claims"].append("NOPE-C99")
    review = d28.audit_review(REPO_ROOT, packet)
    assert any(f["kind"] == "unknown_claim_ref" for f in review["findings"])


def test_cli_default_export(tmp_path):
    result = subprocess.run(
        [sys.executable, str(HERE / "d28_design_review.py"), "--out", str(tmp_path)],
        capture_output=True, text=True, cwd=str(HERE), check=False,
    )
    assert result.returncode == 0, result.stderr
    review = json.loads((tmp_path / "review_audit.json").read_text(encoding="utf-8"))
    assert review["verdict"] == "pass"
    packet = json.loads((tmp_path / "review_packet.json").read_text(encoding="utf-8"))
    assert packet["decision_id"] == "D28-D1"
