"""Regression tests for the R03 aging cross-domain validation contract slice."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import r03_aging_domain as r03

HERE = Path(__file__).resolve().parent


def test_seed_claim_passes_validation_and_evaluation():
    claim = r03.seed_claim()
    findings = r03.validate_claim(claim)
    assert findings == []
    result = r03.evaluate(claim, r03.seed_observation())
    assert result["verdict"] == "pass"
    assert result["checks"]["within_domain"] is True


def test_pack_geometry_change_is_not_aging_truth():
    """OS03：pack 几何/拓扑变化不能充老化真值。"""
    claim = r03.seed_claim()
    claim["ground_truth"] = {"kind": "pack_geometry_change", "source_id": "OS03-pack-rework"}
    findings = r03.validate_claim(claim)
    assert any(f["kind"] == "geometry_not_truth" for f in findings)


def test_external_data_without_availability_check_cannot_close_claim():
    """OS08：无外部数据可用性核验，不得关闭 R03 实证。"""
    claim = r03.seed_claim()
    claim["ground_truth"] = {"kind": "external_unverified", "source_id": "OS08-blast-data"}
    findings = r03.validate_claim(claim)
    assert any(f["kind"] == "external_unverified_truth" for f in findings)


def test_unresolved_calendar_cycle_mix_is_found():
    """OS08：日历/循环分量未分离或未补偿，混合数据不许当作循环老化证据。"""
    claim = r03.seed_claim()
    claim["components"]["calendar"] = "unresolved"
    findings = r03.validate_claim(claim)
    assert any(f["kind"] == "unresolved_component_mix" for f in findings)
    claim = r03.seed_claim()
    claim["components"]["cycle"] = "unresolved"
    assert any(f["kind"] == "unresolved_component_mix" for f in r03.validate_claim(claim))


def test_empty_components_map_cannot_pass():
    """advisory(blocker)：components={} 使旧循环零迭代——空表不许 vacuous pass。"""
    claim = r03.seed_claim()
    claim["components"] = {}
    findings = r03.validate_claim(claim)
    kinds = [f["kind"] for f in findings]
    assert kinds.count("unresolved_component_mix") == 2  # calendar 与 cycle 各缺一份
    assert r03.evaluate(claim, r03.seed_observation())["verdict"] == "fail"


def test_missing_component_key_is_found():
    claim = r03.seed_claim()
    del claim["components"]["cycle"]
    findings = r03.validate_claim(claim)
    assert any(f["kind"] == "unresolved_component_mix" and "cycle" in f["detail"] for f in findings)


def test_every_model_needs_identity_and_domain_note():
    """OS08：Kokam 快算另建模型身份——每个模型给出版本与适用域注记。"""
    claim = r03.seed_claim()
    claim["models"][0]["version"] = ""
    findings = r03.validate_claim(claim)
    assert any(f["kind"] == "missing_model_identity" for f in findings)
    claim = r03.seed_claim()
    del claim["models"][0]["domain_note"]
    assert any(f["kind"] == "missing_model_identity" for f in r03.validate_claim(claim))


def test_condition_domain_must_be_declared():
    claim = r03.seed_claim()
    claim["condition_domain"] = {}
    findings = r03.validate_claim(claim)
    assert any(f["kind"] == "empty_condition_domain" for f in findings)


def test_condition_domain_axes_must_be_ordered_numeric_pairs():
    """advisory：三轴必须是 [lo,hi] 数值且 lo<hi，畸形/反向界不许进入评估。"""
    cases = [
        {"temp_c": [45.0, 15.0]},          # 反向
        {"temp_c": [15.0]},                 # 单元素
        {"temp_c": "15-45"},                # 非标量对
        {"temp_c": [15.0, "45"]},           # 非数值
        {"soc": [True, 0.9]},               # 布尔不是数
    ]
    for patch in cases:
        claim = r03.seed_claim()
        claim["condition_domain"].update(patch)
        findings = r03.validate_claim(claim)
        assert any(f["kind"] == "malformed_condition_domain" for f in findings), patch
        result = r03.evaluate(claim, r03.seed_observation())
        assert result["verdict"] == "fail", patch


def test_malformed_domain_cannot_crash_evaluation():
    claim = r03.seed_claim()
    claim["condition_domain"] = {"temp_c": 25.0}  # 标量：旧代码索引即崩
    result = r03.evaluate(claim, r03.seed_observation())
    assert result["verdict"] == "fail"
    assert result["checks"]["claim_valid"] is False


def test_field_data_without_verified_availability_cannot_close_claim():
    """advisory：field_data 只凭 kind 不够——必须 verified_availability=True（严格布尔）。"""
    claim = r03.seed_claim()
    claim["ground_truth"] = {"kind": "field_data", "source_id": "fleet-logs-x"}
    findings = r03.validate_claim(claim)
    assert any(f["kind"] == "unverified_field_data" for f in findings)
    assert r03.evaluate(claim, r03.seed_observation())["verdict"] == "fail"
    # 非布尔真值不豁免
    claim["ground_truth"]["verified_availability"] = "yes"
    assert any(f["kind"] == "unverified_field_data" for f in r03.validate_claim(claim))
    # 严格 True + 可溯源 source_id 放行
    claim["ground_truth"]["verified_availability"] = True
    assert r03.validate_claim(claim) == []


def test_field_data_traceability_requires_source_id():
    """advisory：verified_availability=True 但 source_id 为空/空白仍不许通过。"""
    for bad in ("", "   "):
        claim = r03.seed_claim()
        claim["ground_truth"] = {"kind": "field_data", "source_id": bad,
                                 "verified_availability": True}
        findings = r03.validate_claim(claim)
        assert any(f["kind"] == "untraceable_field_data" for f in findings), repr(bad)
        assert r03.evaluate(claim, r03.seed_observation())["verdict"] == "fail"


def test_observation_outside_declared_domain_fails():
    claim = r03.seed_claim()
    obs = r03.seed_observation()
    obs["conditions"]["temp_c"] = 60.0  # 声明域上限 45
    result = r03.evaluate(claim, obs)
    assert result["verdict"] == "fail"
    assert result["checks"]["within_domain"] is False


def test_invalid_claim_cannot_pass_evaluation():
    claim = r03.seed_claim()
    claim["components"]["calendar"] = "unresolved"
    result = r03.evaluate(claim, r03.seed_observation())
    assert result["verdict"] == "fail"
    assert result["checks"]["claim_valid"] is False


def test_capacity_error_tolerance_is_checked():
    claim = r03.seed_claim()
    obs = r03.seed_observation()
    obs["max_capacity_rel_err"] = claim["tolerance_capacity_rel"] * 2
    result = r03.evaluate(claim, obs)
    assert result["verdict"] == "fail"
    assert result["checks"]["capacity_error"] is False


def test_no_models_cannot_pass_evaluation():
    claim = r03.seed_claim()
    claim["models"] = []
    result = r03.evaluate(claim, r03.seed_observation())
    assert result["verdict"] == "fail"


def test_seed_is_synthetic_cell_level_truth():
    claim = r03.seed_claim()
    assert claim["synthetic"] is True
    assert claim["ground_truth"]["kind"] == "cell_level_test"


def test_cli_default_export(tmp_path):
    result = subprocess.run(
        [sys.executable, str(HERE / "r03_aging_domain.py"), "--out", str(tmp_path)],
        capture_output=True, text=True, cwd=str(HERE), check=False,
        timeout=120, stdin=subprocess.DEVNULL,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "aging_domain.json").read_text(encoding="utf-8"))
    assert report["evaluation"]["verdict"] == "pass"
    assert report["validation"] == []
