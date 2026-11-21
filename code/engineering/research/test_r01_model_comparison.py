"""Regression tests for the R01 model-comparison protocol slice."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import r01_model_comparison as r01

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]


def test_seed_spec_passes_validation_and_evaluation():
    spec = r01.seed_spec()
    findings = r01.validate_spec(spec)
    assert findings == []
    result = r01.evaluate(spec, r01.seed_observation())
    assert result["verdict"] == "pass"
    assert result["checks"]["energy_integral"] is True


def test_missing_tolerance_is_found():
    spec = r01.seed_spec()
    del spec["tolerances"]["v_rel"]
    findings = r01.validate_spec(spec)
    assert any(f["kind"] == "missing_tolerance" for f in findings)


def test_nonpositive_tolerance_is_found():
    spec = r01.seed_spec()
    spec["tolerances"]["q_abs"] = 0.0
    findings = r01.validate_spec(spec)
    assert any(f["kind"] == "bad_tolerance" for f in findings)


def test_unknown_reference_kind_is_found():
    spec = r01.seed_spec()
    spec["reference"]["kind"] = "vibes"
    findings = r01.validate_spec(spec)
    assert any(f["kind"] == "unknown_reference_kind" for f in findings)


def test_event_cases_must_cover_required_baseline():
    """CASE01 基准：端点/不连续事件/左右侧三件套缺一不可。"""
    spec = r01.seed_spec()
    spec["event_cases"] = ["endpoint"]
    findings = r01.validate_spec(spec)
    assert any(f["kind"] == "incomplete_event_baseline" for f in findings)


def test_unfrozen_version_is_found():
    spec = r01.seed_spec()
    spec["frozen_version"] = ""
    findings = r01.validate_spec(spec)
    assert any(f["kind"] == "unfrozen_model" for f in findings)


def test_release_tag_and_hex_commit_pass_p1():
    spec = r01.seed_spec()
    spec["synthetic"] = False
    spec["frozen_version"] = "v23.4.1"
    assert r01.validate_spec(spec) == []
    spec["frozen_version"] = "a" * 40
    assert r01.validate_spec(spec) == []


def test_placeholder_without_synthetic_flag_is_found():
    """advisory：占位符不许装成冻结版本——不标 synthetic 就得是真 pin。"""
    spec = r01.seed_spec()
    del spec["synthetic"]
    findings = r01.validate_spec(spec)
    assert any(f["kind"] == "placeholder_version" for f in findings)
    # 显式声明 synthetic 的合成夹具放行，且是可见豁免而非隐形后门
    spec["synthetic"] = True
    assert r01.validate_spec(spec) == []


def test_synthetic_exemption_requires_strict_boolean_true():
    """advisory：'false' 字符串、1 等真值不能静默拿到合成豁免。"""
    for bad in ("false", "True", 1, 0):
        spec = r01.seed_spec()
        spec["synthetic"] = bad
        findings = r01.validate_spec(spec)
        assert any(f["kind"] == "placeholder_version" for f in findings), bad


def test_mwe_status_must_be_three_valued():
    """CASE01：是否真重现 MWE 只有 yes/no/unknown 三值；unknown 不许写成 yes。"""
    spec = r01.seed_spec()
    spec["reproduces_mwe"] = "maybe"
    findings = r01.validate_spec(spec)
    assert any(f["kind"] == "bad_mwe_status" for f in findings)
    spec = r01.seed_spec()
    spec["reproduces_mwe"] = "unknown"
    assert r01.validate_spec(spec) == []


def test_evaluation_fails_closed_on_each_check():
    spec = r01.seed_spec()
    obs = r01.seed_observation()
    obs["energy_err_ok"] = False
    result = r01.evaluate(spec, obs)
    assert result["verdict"] == "fail"
    assert result["checks"]["energy_integral"] is False
    obs = r01.seed_observation()
    obs["max_v_rel_err"] = spec["tolerances"]["v_rel"] * 2
    assert r01.evaluate(spec, obs)["verdict"] == "fail"


def test_invalid_protocol_cannot_pass_evaluation():
    """与 R02 同类：带 error 级 findings 的协议不许产出 passing verdict。"""
    spec = r01.seed_spec()
    spec["event_cases"] = ["endpoint"]  # P4 不完整
    result = r01.evaluate(spec, r01.seed_observation())
    assert result["verdict"] == "fail"
    assert result["checks"]["protocol_valid"] is False


def test_no_declared_event_cases_cannot_pass_evaluation():
    spec = r01.seed_spec()
    spec["event_cases"] = []
    obs = {"max_v_rel_err": 0.0, "max_q_abs_err": 0.0, "energy_err_ok": True, "event_cases_passed": []}
    result = r01.evaluate(spec, obs)
    assert result["verdict"] == "fail"
    assert result["checks"]["has_event_cases"] is False


def test_observation_must_cover_all_event_cases():
    spec = r01.seed_spec()
    obs = r01.seed_observation()
    obs["event_cases_passed"] = ["endpoint"]
    result = r01.evaluate(spec, obs)
    assert result["verdict"] == "fail"


def test_cli_default_export(tmp_path):
    result = subprocess.run(
        [sys.executable, str(HERE / "r01_model_comparison.py"), "--out", str(tmp_path)],
        capture_output=True, text=True, cwd=str(HERE), check=False,
        timeout=120, stdin=subprocess.DEVNULL,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "model_comparison.json").read_text(encoding="utf-8"))
    assert report["evaluation"]["verdict"] == "pass"
