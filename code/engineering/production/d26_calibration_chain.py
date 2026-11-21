"""D26 reference implementation: calibration -> production -> in-service chain.

Teaching slice ``D26-calibration-chain``: P6.1 binds requirements to evidence
"without granting product qualification". This module models the identity
chain a real pack carries through its life, with teaching values:

- 标定 (calibration): per-channel gain/offset, each with cal id, calibration
  date and due date. History is append-only — recalibration adds a new entry,
  it never edits the old one.
- 生产 (production): a release seals serial, firmware version and the
  calibration constants. Sealed fields reject any later write.
- 在役 (in-service): the only calibration-shaped mutation allowed is
  recalibration (new entry); every service mutation appends to a tamper-evident
  audit chain (monotonic seq + prev-hash, the D21 pattern).
- 过期语义: an expired calibration blocks RELEASE and suspends ACCURACY
  CLAIMS, but never blocks function — pretending a pack stops working when a
  calibration lapses would be its own overclaim.

Boundary: real production/EOL records are SRC06 (待补). This is the chain's
mechanism and discipline, not a production record; the frozen ticket hash pins
the teaching values, real serials arrive with SRC06.

Only the standard library is used so the chapter can be recomputed end to end.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCENARIO_ID = "D26-calibration-chain"
GENERATOR = "d26_calibration_chain.py v1 (standard library)"

FROZEN_TODAY = "2026-11-18"
SEALED_FIELDS = ("serial", "firmware", "calibration_constants")
GAP_DAYS = 0  # same-day release allowed; expiry is due_on < today


def _canon(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def seed_device() -> dict:
    """Teaching-value device: 2-channel pack, calibrations fresh on FROZEN_TODAY."""
    channels = {
        "voltage": {"gain": 1.0000, "offset": 0.0, "cal_id": "CAL-2026-10",
                    "calibrated_on": "2026-10-15", "due_on": "2027-10-15",
                    "history": []},
        "current": {"gain": 0.9998, "offset": 0.05, "cal_id": "CAL-2026-10",
                    "calibrated_on": "2026-10-15", "due_on": "2027-10-15",
                    "history": []},
    }
    return {
        "serial": "TEACH-PACK-001",
        "firmware": "fw-teach-2.3.1",
        "channels": channels,
    }


def _channel_entry(device: dict, channel: str) -> dict:
    try:
        return device["channels"][channel]
    except KeyError:
        raise ValueError(f"unknown channel {channel!r}") from None


def expired_channels(device: dict, today: str) -> list[str]:
    out = []
    for name, entry in device["channels"].items():
        if entry["due_on"] < today:
            out.append(name)
    return sorted(out)


def device_status(device: dict, today: str) -> dict:
    expired = expired_channels(device, today)
    return {
        "serial": device["serial"],
        "function": "available",
        "accuracy_claim": "suspended" if expired else "available",
        "expired_channels": expired,
        "boundary": "过期标定只暂停精度宣称，功能可用性不由标定日期授予也不被其剥夺。",
    }


def sealed_payload(device: dict) -> dict:
    constants = {
        name: {"gain": entry["gain"], "offset": entry["offset"], "cal_id": entry["cal_id"]}
        for name, entry in sorted(device["channels"].items())
    }
    return {"serial": device["serial"], "firmware": device["firmware"],
            "calibration_constants": constants}


FROZEN_TICKET_HASH = _hash(_canon({
    "serial": "TEACH-PACK-001", "firmware": "fw-teach-2.3.1",
    "calibration_constants": {
        "current": {"gain": 0.9998, "offset": 0.05, "cal_id": "CAL-2026-10"},
        "voltage": {"gain": 1.0, "offset": 0.0, "cal_id": "CAL-2026-10"},
    },
}))


def release(device: dict, today: str) -> dict:
    """Production release: expired calibration blocks the release."""
    expired = expired_channels(device, today)
    if expired:
        raise ValueError(f"expired calibration blocks release: {', '.join(expired)}")
    payload = sealed_payload(device)
    return {
        "scenario_id": SCENARIO_ID,
        "serial": device["serial"],
        "released_on": today,
        "config_hash": _hash(_canon(payload)),
        "status": "released",
        "boundary": "放行单只证明教学值配置在此刻完整且未过期，不是产线放行记录。",
    }


def new_audit_chain() -> dict:
    return {"scenario_id": SCENARIO_ID, "records": []}


def _append_record(chain: dict, ts: str, op: str, field: str, detail: dict) -> None:
    prev = chain["records"][-1]["hash"] if chain["records"] else "GENESIS"
    seq = len(chain["records"]) + 1
    body = _canon({"seq": seq, "ts": ts, "op": op, "field": field,
                   "detail": detail, "prev": prev})
    chain["records"].append({"seq": seq, "ts": ts, "op": op, "field": field,
                             "detail": detail, "prev": prev, "hash": _hash(body)})


def verify_audit_chain(chain: dict) -> bool:
    prev = "GENESIS"
    for expect_seq, record in enumerate(chain["records"], start=1):
        if record["seq"] != expect_seq or record["prev"] != prev:
            return False
        body = _canon({k: record[k] for k in ("seq", "ts", "op", "field", "detail", "prev")})
        if record["hash"] != _hash(body):
            return False
        prev = record["hash"]
    return True


def verify_ticket(device: dict, ticket: dict) -> bool:
    """封存核验：现役配置重算哈希必须与放行单一致，再标定即失配。"""
    return _hash(_canon(sealed_payload(device))) == ticket.get("config_hash")


def service_write(device: dict, chain: dict, field: str, value, ts: str, op: str) -> None:
    """In-service write gate: sealed fields and calibration history are off-limits."""
    if field in SEALED_FIELDS or field.startswith("channels.") and ".gain" in field or field.startswith("channels.") and ".offset" in field:
        raise ValueError(f"sealed or append-only field {field!r}: {op} rejected")
    raise ValueError(f"field {field!r} is not service-writable in this teaching model")


def recalibrate(device: dict, chain: dict, channel: str, gain: float, offset: float,
                cal_id: str, calibrated_on: str, due_on: str, ts: str) -> None:
    """The one calibration-shaped in-service mutation: append a new entry."""
    entry = _channel_entry(device, channel)
    entry["history"].append({
        "gain": entry["gain"], "offset": entry["offset"], "cal_id": entry["cal_id"],
        "calibrated_on": entry["calibrated_on"], "due_on": entry["due_on"],
    })
    entry.update({"gain": gain, "offset": offset, "cal_id": cal_id,
                  "calibrated_on": calibrated_on, "due_on": due_on})
    _append_record(chain, ts=ts, op="recalibrate", field=f"channels.{channel}",
                   detail={"cal_id": cal_id, "due_on": due_on})


def build_report(today: str = FROZEN_TODAY) -> dict:
    device = seed_device()
    chain = new_audit_chain()
    ticket = release(device, today=today)
    return {
        "scenario_id": SCENARIO_ID,
        "generator": GENERATOR,
        "today": today,
        "device": sealed_payload(device),
        "release_ticket": ticket,
        "audit": {"records": 0, "chain_ok": verify_audit_chain(chain)},
        "boundary": "教学值链：SRC06 产线/EOL 记录待补，真实序列号与放行单随 SRC06 闭合。",
    }


def write_artifacts(out_dir: Path, today: str = FROZEN_TODAY) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(today=today)
    (out_dir / "calibration_chain.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "release_ticket.json").write_text(
        json.dumps(report["release_ticket"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--today", default=FROZEN_TODAY, help="ISO date for the frozen scenario")
    parser.add_argument("--out", type=Path, help="write calibration_chain.json + release_ticket.json")
    args = parser.parse_args(argv)
    try:
        if args.out:
            write_artifacts(args.out, today=args.today)
        else:
            report = build_report(today=args.today)
            print(json.dumps({
                "serial": report["release_ticket"]["serial"],
                "config_hash": report["release_ticket"]["config_hash"],
                "status": report["release_ticket"]["status"],
                "today": report["today"],
            }, ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(f"d26_calibration_chain: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
