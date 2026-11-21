"""Regression tests for the D27 fidelity-ladder + AI-assistance slice."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import d27_fidelity_ai as d27

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]


def test_fidelity_ladder_is_pinned_with_forbiddens():
    ladder = d27.fidelity_ladder()
    assert len(ladder) == 4
    names = [level["name"] for level in ladder]
    assert names == ["解析教学模型", "集总参数", "分布式热耦合", "场模型"]
    for level in ladder:
        assert level["domain"], level["name"]
        assert level["extrapolation_forbidden"], f"{level['name']} 必须有外推禁止项"


def test_claim_exceeding_fidelity_is_found():
    findings = d27.check_claim("集总参数", "用本模型预测该料号十年寿命并据此定保修期")
    assert any(f["kind"] == "claim_exceeds_fidelity" for f in findings)


def test_honest_claim_passes():
    findings = d27.check_claim("集总参数", "教学时间常数集可用于滤波器整定与仿真对照")
    assert findings == []


def test_claim_at_field_level_still_respects_forbidden():
    findings = d27.check_claim("场模型", "场模型输出直接等同实测，无需标定")
    assert any(f["kind"] == "claim_exceeds_fidelity" for f in findings)


def test_ai_record_without_reviewer_is_found():
    records = [{"task": "起草 D27 小节", "tool": "LLM", "reviewer": "",
                "date": "2026-11-18", "artifact": "bms-book/engineering/D27-高保真模型与AI辅助.md",
                "boundary": "草稿，验证责任在人"}]
    audit = d27.audit_ai_records(REPO_ROOT, records)
    assert audit["verdict"] == "fail"
    assert any(f["kind"] == "unreviewed_ai_output" for f in audit["findings"])


def test_ai_record_with_missing_artifact_is_found():
    records = [{"task": "t", "tool": "LLM", "reviewer": "张三",
                "date": "2026-11-18", "artifact": "bms-book/engineering/NOPE.md",
                "boundary": "草稿，不能作为证据"}]
    audit = d27.audit_ai_records(REPO_ROOT, records)
    assert any(f["kind"] == "missing_artifact" for f in audit["findings"])


def test_ai_record_boundary_statement_needs_boundary_word():
    records = [{"task": "t", "tool": "LLM", "reviewer": "张三",
                "date": "2026-11-18", "artifact": "bms-book/engineering/D27-高保真模型与AI辅助.md",
                "boundary": "随便看看"}]
    audit = d27.audit_ai_records(REPO_ROOT, records)
    assert any(f["kind"] == "boundary_without_teeth" for f in audit["findings"])


def test_seed_records_pass_audit():
    audit = d27.audit_ai_records(REPO_ROOT, d27.seed_ai_records())
    assert audit["verdict"] == "pass"
    assert audit["counts"]["records"] == 2


def test_global_forbidden_applies_at_every_level():
    findings = d27.check_claim("场模型", "本场模型给出功能安全结论")
    assert any("globally forbidden" in f["detail"] for f in findings)
    findings = d27.check_claim("解析教学模型", "本算例支撑产线放行决策")
    assert any("globally forbidden" in f["detail"] for f in findings)


def test_field_level_honest_claim_still_passes():
    findings = d27.check_claim("场模型", "电极锂离子浓度分布仿真研究与参数敏感性")
    assert findings == []


def test_ai_artifact_never_carries_executable_evidence():
    """结构不变量：AI 辅助产物必须是文档路径，且不得出现在任何
    experiment 的 tests/script 里——AI 产物不承载可执行证据。"""
    records = d27.seed_ai_records()
    experiments = json.loads(
        (REPO_ROOT / "bms-book/engineering/experiments.json").read_text(encoding="utf-8")
    )
    exec_paths = {e["script"] for e in experiments["experiments"]}
    for e in experiments["experiments"]:
        exec_paths.update(e.get("tests", []))
    for record in records:
        artifact = record["artifact"]
        assert artifact.endswith(".md"), artifact
        assert artifact not in exec_paths, artifact


def test_d27_doc_claims_evidence_count_matches_registry():
    """正文冻结的 evidence 引用数必须跟 claims.json 实读一致。"""
    doc = (
        REPO_ROOT / "bms-book" / "engineering" / "D27-高保真模型与AI辅助.md"
    ).read_text(encoding="utf-8")
    claims = json.loads(
        (REPO_ROOT / "bms-book" / "engineering" / "claims.json").read_text(encoding="utf-8")
    )["claims"]
    total = sum(len(c.get("evidence", [])) for c in claims)
    expected = f"claims evidence 全仓 {total} 条"
    assert expected in doc, [line for line in doc.splitlines() if "claims evidence" in line]


def test_cli_default_export(tmp_path):
    result = subprocess.run(
        [sys.executable, str(HERE / "d27_fidelity_ai.py"), "--out", str(tmp_path)],
        capture_output=True, text=True, cwd=str(HERE), check=False,
    )
    assert result.returncode == 0, result.stderr
    audit = json.loads((tmp_path / "fidelity_audit.json").read_text(encoding="utf-8"))
    assert audit["ai_audit"]["verdict"] == "pass"
