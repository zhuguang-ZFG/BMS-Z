"""Regression tests for the R04 safety correction-contract slice."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import r04_safety_correction as r04

HERE = Path(__file__).resolve().parent


def test_seed_contract_passes_validation_and_evaluation():
    contract = r04.seed_contract()
    findings = r04.validate_contract(contract)
    assert findings == []
    result = r04.evaluate(contract, r04.seed_observation())
    assert result["verdict"] == "pass"
    assert result["checks"]["feedback_matches"] is True


def test_recovery_actions_must_be_distinguished():
    """OS07：区分清旗、复位、重新许可——actor+effect 全同即混淆，多余键不洗白。"""
    contract = r04.seed_contract()
    r = contract["faults"][0]["recovery"]
    r["reset"] = {**r["clear_flag"], "note": "只是备注"}  # actor/effect 同，靠多余键规避整字典比较
    findings = r04.validate_contract(contract)
    assert any(f["kind"] == "conflated_recovery" for f in findings)


def test_recovery_actions_require_actor_and_effect():
    """advisory：{} 满足 presence 却不构成动作——actor/effect 必须非空。"""
    contract = r04.seed_contract()
    contract["faults"][0]["recovery"]["reset"] = {}
    findings = r04.validate_contract(contract)
    assert any(f["kind"] == "empty_recovery_action" for f in findings)
    assert r04.evaluate(contract, r04.seed_observation())["verdict"] == "fail"
    contract = r04.seed_contract()
    contract["faults"][0]["recovery"]["reset"] = {"actor": "下电重启流程", "effect": ""}
    assert any(f["kind"] == "empty_recovery_action" for f in r04.validate_contract(contract))


def test_all_three_recovery_actions_are_required():
    contract = r04.seed_contract()
    del contract["faults"][0]["recovery"]["re_permission"]
    findings = r04.validate_contract(contract)
    assert any(f["kind"] == "missing_recovery_action" for f in findings)


def test_command_needs_identity():
    """OS07：命令身份进入合同——谁有权发这条反应命令必须写明。"""
    contract = r04.seed_contract()
    contract["faults"][0]["reaction"]["actor"] = ""
    findings = r04.validate_contract(contract)
    assert any(f["kind"] == "missing_command_identity" for f in findings)


def test_feedback_needs_identity():
    contract = r04.seed_contract()
    del contract["faults"][0]["feedback"]["source"]
    findings = r04.validate_contract(contract)
    assert any(f["kind"] == "missing_feedback_identity" for f in findings)


def test_debounce_config_is_required():
    contract = r04.seed_contract()
    contract["faults"][0]["debounce_ms"] = None
    findings = r04.validate_contract(contract)
    assert any(f["kind"] == "missing_debounce" for f in findings)
    contract = r04.seed_contract()
    contract["faults"][0]["debounce_ms"] = -1
    assert any(f["kind"] == "missing_debounce" for f in r04.validate_contract(contract))


def test_every_declared_transition_needs_a_test():
    contract = r04.seed_contract()
    contract["faults"][0]["transition_tests"] = {}  # 声明了迁移但没有测试映射
    findings = r04.validate_contract(contract)
    assert any(f["kind"] == "untested_transition" for f in findings)


def test_transition_test_mapping_must_reference_declared_test():
    """advisory(blocker)：映射到不存在的测试 ID（bogus）不算测试覆盖。"""
    contract = r04.seed_contract()
    contract["faults"][0]["transition_tests"]["fault->safe"] = "bogus-test"
    findings = r04.validate_contract(contract)
    assert any(f["kind"] == "untested_transition" and "bogus-test" in f["detail"] for f in findings)
    assert r04.evaluate(contract, r04.seed_observation())["verdict"] == "fail"


def test_invalid_contract_cannot_pass_evaluation():
    contract = r04.seed_contract()
    contract["faults"][0]["recovery"]["reset"] = dict(contract["faults"][0]["recovery"]["clear_flag"])
    result = r04.evaluate(contract, r04.seed_observation())
    assert result["verdict"] == "fail"
    assert result["checks"]["contract_valid"] is False


def test_missing_test_coverage_cannot_pass_evaluation():
    contract = r04.seed_contract()
    obs = r04.seed_observation()
    obs["transitions_covered"] = ["fault->safe"]
    result = r04.evaluate(contract, obs)
    assert result["verdict"] == "fail"


def test_feedback_mismatch_fails():
    contract = r04.seed_contract()
    obs = r04.seed_observation()
    obs["feedback_matches"] = False
    result = r04.evaluate(contract, obs)
    assert result["verdict"] == "fail"
    assert result["checks"]["feedback_matches"] is False


def test_no_declared_transitions_cannot_pass():
    """advisory：零迁移的"已处理"宣称没有状态机——空集量化不许 vacuous pass。"""
    contract = r04.seed_contract()
    contract["faults"][0]["transitions"] = []
    contract["faults"][0]["transition_tests"] = {}
    findings = r04.validate_contract(contract)
    assert any(f["kind"] == "no_declared_transition" for f in findings)
    result = r04.evaluate(contract, r04.seed_observation())
    assert result["verdict"] == "fail"
    assert result["checks"]["has_transitions"] is False


def test_no_faults_cannot_pass_evaluation():
    contract = r04.seed_contract()
    contract["faults"] = []
    result = r04.evaluate(contract, r04.seed_observation())
    assert result["verdict"] == "fail"


def test_cli_default_export(tmp_path):
    result = subprocess.run(
        [sys.executable, str(HERE / "r04_safety_correction.py"), "--out", str(tmp_path)],
        capture_output=True, text=True, cwd=str(HERE), check=False,
        timeout=120, stdin=subprocess.DEVNULL,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "safety_correction.json").read_text(encoding="utf-8"))
    assert report["evaluation"]["verdict"] == "pass"
    assert report["validation"] == []
