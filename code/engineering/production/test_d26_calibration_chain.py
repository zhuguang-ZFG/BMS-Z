"""Regression tests for the D26 calibration/production/in-service slice."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import d26_calibration_chain as d26

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]


def test_seed_releases_with_frozen_ticket_hash():
    device = d26.seed_device()
    ticket = d26.release(device, today=d26.FROZEN_TODAY)
    assert ticket["serial"] == "TEACH-PACK-001"
    assert ticket["config_hash"] == d26.FROZEN_TICKET_HASH
    assert ticket["status"] == "released"


def test_expired_calibration_blocks_release():
    device = d26.seed_device()
    with pytest.raises(ValueError, match="expired calibration"):
        d26.release(device, today="2027-11-01")


def test_sealed_fields_reject_service_write():
    device = d26.seed_device()
    chain = d26.new_audit_chain()
    with pytest.raises(ValueError, match="sealed"):
        d26.service_write(device, chain, field="serial", value="HACK-9",
                          ts="2026-11-19T08:00:00", op="overwrite")


def test_recalibration_appends_history_and_keeps_old():
    device = d26.seed_device()
    chain = d26.new_audit_chain()
    d26.recalibrate(device, chain, channel="current", gain=1.001, offset=-0.2,
                    cal_id="CAL-2027-01", calibrated_on="2027-01-15", due_on="2028-01-15",
                    ts="2027-01-15T09:00:00")
    history = device["channels"]["current"]["history"]
    assert [h["cal_id"] for h in history] == ["CAL-2026-10"]
    assert device["channels"]["current"]["cal_id"] == "CAL-2027-01"
    assert d26.release(device, today="2027-02-01")["status"] == "released"


def test_calibration_history_is_append_only():
    device = d26.seed_device()
    chain = d26.new_audit_chain()
    with pytest.raises(ValueError, match="append-only"):
        d26.service_write(device, chain, field="channels.current.gain", value=9.9,
                          ts="2026-11-19T08:00:00", op="overwrite")


def test_audit_chain_detects_tampering():
    device = d26.seed_device()
    chain = d26.new_audit_chain()
    d26.recalibrate(device, chain, channel="voltage", gain=1.0002, offset=0.01,
                    cal_id="CAL-2027-02", calibrated_on="2027-02-01", due_on="2028-02-01",
                    ts="2027-02-01T09:00:00")
    chain["records"][0]["op"] = "rollback"
    assert d26.verify_audit_chain(chain) is False


def test_expired_calibration_flags_accuracy_but_not_function():
    device = d26.seed_device()
    status = d26.device_status(device, today="2027-11-01")
    assert status["function"] == "available"
    assert status["accuracy_claim"] == "suspended"
    assert status["expired_channels"] == ["current", "voltage"]


def test_service_write_appends_monotonic_records():
    device = d26.seed_device()
    chain = d26.new_audit_chain()
    d26.recalibrate(device, chain, channel="voltage", gain=1.0, offset=0.0,
                    cal_id="CAL-2027-03", calibrated_on="2027-03-01", due_on="2028-03-01",
                    ts="2027-03-01T09:00:00")
    seqs = [r["seq"] for r in chain["records"]]
    assert seqs == sorted(seqs) == list(range(1, len(seqs) + 1))
    assert d26.verify_audit_chain(chain) is True


def test_verify_ticket_matches_until_recalibration():
    device = d26.seed_device()
    ticket = d26.release(device, today=d26.FROZEN_TODAY)
    assert d26.verify_ticket(device, ticket) is True
    chain = d26.new_audit_chain()
    d26.recalibrate(device, chain, channel="voltage", gain=1.0001, offset=0.0,
                    cal_id="CAL-2027-05", calibrated_on="2027-05-01", due_on="2028-05-01",
                    ts="2027-05-01T09:00:00")
    assert d26.verify_ticket(device, ticket) is False, "再标定后旧放行单失配，封存身份不再等价于现役配置"


def test_cli_default_export(tmp_path):
    result = subprocess.run(
        [sys.executable, str(HERE / "d26_calibration_chain.py"), "--out", str(tmp_path)],
        capture_output=True, text=True, cwd=str(HERE), check=False,
    )
    assert result.returncode == 0, result.stderr
    ticket = json.loads((tmp_path / "release_ticket.json").read_text(encoding="utf-8"))
    assert ticket["config_hash"] == d26.FROZEN_TICKET_HASH
    report = json.loads((tmp_path / "calibration_chain.json").read_text(encoding="utf-8"))
    assert report["audit"]["chain_ok"] is True
