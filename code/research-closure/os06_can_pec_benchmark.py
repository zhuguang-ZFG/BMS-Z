"""OS06 VESC BMS firmware -> S6 benchmark: independent CAN-bitmap / PEC-silence /
permission-derating counterexamples (no upstream GPL code copied).

Contract (research plan OS06 + snapshot vesc_bms_fw observations VESC-01..08):
  * comm_can.c sends/receives a status byte whose bits 0..3 are
    is_charging / is_balancing / charge_allowed / charge_ok (VESC-02), and uses
    29-bit extended CAN IDs whose mechanical bit-map decoding is a *different*
    contract from upper-layer validity (node range, command allowed, freshness;
    VESC-03).  A frame can be packed/decoded perfectly yet be rejected upstairs.
  * LTC6813 driver accepts read groups only when their PEC matches, yet the
    open-wire check block is commented out (VESC-07); a diagnostic that exists
    by name but is not executed is an untested coverage gap.  We reproduce the
    *failure mode* with an independently authored CRC-15/PEC-style check: with
    the check disabled the very same injected corruption passes silently.
  * bms_if.c charge permission uses voltage/temperature/peer bounds and thermal
    derating reduces simultaneous balancing channels (VESC-05/06).  Permission
    (authorization) and derating (parameter clamping) are separate decisions.

This is an INDEPENDENT teaching implementation / counterexample, not a copy of
upstream GPL code.  The PEC here is a generic CRC-15 (poly 0x4599, seed 0x2B0);
per VESC-08 we do NOT claim it is byte-for-byte the upstream PEC variant.
Deterministic: fixed fields, fixed payload, fixed injection positions, no hash().
"""
import json
import platform
from pathlib import Path

import numpy as np

EVIDENCE = Path(__file__).parent / "evidence" / "os06-can-pec-benchmark.json"

# ---- deterministic constants ------------------------------------------------
SEED = 0x2B0            # CRC-15 seed (PEC family convention)
PEC_POLY = 0x4599       # x^15+x^14+x^10+x^8+x^7+x^4+x^3+1 (low 15 bits)
EXTID_MASK = 0x1FFFFFFF  # 29-bit extended CAN ID
VALID_NODES = frozenset({0, 1, 2, 3, 4, 5})   # semantic upper-layer node range
CMD_READ_STATUS = 0
CMD_WRITE_CHARGE = 1
CMD_WRITE_BALANCE = 2
CMD_SET_SOC = 3
ALLOWED_CMDS = frozenset({CMD_READ_STATUS, CMD_WRITE_CHARGE, CMD_WRITE_BALANCE})
EXPIRY_MS = 10_000      # peer-value freshness (VESC-03: 10 s expiry path)
CACHE_RECLAIM_MS = 600_000  # distinct contract (VESC-03: 10 min cache reclaim)


# ---- Part 1a: 29-bit extended-ID bit map (mechanical pack/unpack) -----------
def pack_extid(dcl, src_node, dst_node, cmd, direction):
    """Pack fields into a 29-bit extended CAN ID. Purely mechanical.

    Layout (MSB->LSB): dir(1) | dcl(4) | src(8) | dst(8) | cmd(8).
    """
    extid = (
        ((direction & 0x1) << 28)
        | ((dcl & 0xF) << 24)
        | ((src_node & 0xFF) << 16)
        | ((dst_node & 0xFF) << 8)
        | (cmd & 0xFF)
    )
    return extid & EXTID_MASK


def unpack_extid(extid):
    """Unpack a 29-bit extended CAN ID back into its fields (mechanical)."""
    return {
        "direction": (extid >> 28) & 0x1,
        "dcl": (extid >> 24) & 0xF,
        "src_node": (extid >> 16) & 0xFF,
        "dst_node": (extid >> 8) & 0xFF,
        "cmd": extid & 0xFF,
    }


def upper_validity(fields, now_ms):
    """Upper-layer validity chain: semantics + freshness, *separate* from decode.

    The mechanical bitmap decoder never looks at node range, command set, or
    sample age.  This layer does, and can reject a perfectly decoded frame.
    """
    reasons = []
    if fields["dst_node"] not in VALID_NODES:
        reasons.append("dst_node_out_of_range")
    if fields["cmd"] not in ALLOWED_CMDS:
        reasons.append("cmd_not_allowed")
    age = now_ms - fields.get("sample_ms", now_ms)
    if age > EXPIRY_MS:
        reasons.append("sample_expired")
    return {"valid": len(reasons) == 0, "reasons": reasons, "age_ms": age}


def pack_status(is_charging, is_balancing, charge_allowed, charge_ok):
    """Status byte per implemented VESC-02 layout bits 0/1/2/3."""
    return (
        (1 if is_charging else 0) << 0
        | (1 if is_balancing else 0) << 1
        | (1 if charge_allowed else 0) << 2
        | (1 if charge_ok else 0) << 3
    )


def unpack_status(byte):
    return {
        "is_charging": bool(byte & (1 << 0)),
        "is_balancing": bool(byte & (1 << 1)),
        "charge_allowed": bool(byte & (1 << 2)),
        "charge_ok": bool(byte & (1 << 3)),
    }


# ---- Part 2: independent CRC-15 / PEC-style check --------------------------
def pec15(data, poly=PEC_POLY, init=SEED):
    """Bitwise CRC-15 over bytes; 15-bit register, explicit poly/seed."""
    crc = init & 0x7FFF
    for byte in data:
        crc ^= (int(byte) & 0xFF) << 7
        for _ in range(8):
            if crc & 0x4000:
                crc = ((crc << 1) ^ poly) & 0x7FFF
            else:
                crc = (crc << 1) & 0x7FFF
    return crc & 0x7FFF


def verify_frame(frame, pec_enabled):
    """Receiver: compare recomputed PEC to the appended PEC, unless disabled.

    pec_enabled=False models the commented-out diagnostic: no comparison is
    performed, so a corrupted frame is accepted silently (the counterexample).
    """
    data = frame[:-2]
    appended = int.from_bytes(bytes(int(x) for x in frame[-2:]), "big")
    if not pec_enabled:
        return {"accepted": True, "checked": False, "computed": None,
                "reason": "PEC check disabled (diagnostic not executed)"}
    computed = pec15(data)
    ok = computed == appended
    return {"accepted": bool(ok), "checked": True, "computed": computed,
            "reason": "PEC match" if ok else "PEC mismatch"}


# ---- Part 3: permission / derating chain (independent decisions) -----------
def authorize(cmd, permission_bitmap):
    """Permission decision only; independent of derating."""
    allowed = bool((permission_bitmap >> cmd) & 1)
    return {"allowed": allowed,
            "reason": "command permitted" if allowed else "command not in permission bitmap"}

def apply_derating(param, derating_active, normal_max, derated_max):
    """Derating decision only; independent of permission."""
    limit = derated_max if derating_active else normal_max
    return min(int(param), limit)


def process_command(cmd, param, permission_bitmap, derating_active,
                    normal_max, derated_max, audit_log):
    """Chain: authorize -> (if authorized) derate -> execute; log denial."""
    auth = authorize(cmd, permission_bitmap)
    if not auth["allowed"]:
        audit_log.append({"event": "DENY", "cmd": cmd, "reason": auth["reason"]})
        return {"executed": False, "cmd": cmd, "param": None,
                "stage": "authorization", "reason": auth["reason"]}
    final_param = apply_derating(param, derating_active, normal_max, derated_max)
    audit_log.append({"event": "EXEC", "cmd": cmd, "param": final_param,
                      "derating_active": bool(derating_active)})
    return {"executed": True, "cmd": cmd, "param": final_param,
            "stage": "execute", "derating_active": bool(derating_active)}


def main():
    result = {
        "source_id": "OS06",
        "benchmark": ("VESC BMS -> S6: CAN bitmap vs validity chain, CRC15/PEC "
                      "silent failure, permission/derating chain (independent)"),
        "python": platform.python_version(),
        "upstream_ref": {
            "repo": "vedderb/vesc_bms_fw",
            "commit": "591d57dadb14d4392d4cf859a5187264a8aafed8",
            "note": ("Independent teaching implementation / counterexample; no GPL "
                     "code copied. PEC is a generic CRC-15 (poly 0x4599, seed 0x2B0), "
                     "not asserted byte-identical to the upstream PEC variant."),
        },
    }

    # ---------- Part 1: CAN bitmap vs upper-layer validity chain ----------
    good = {"direction": 0, "dcl": 3, "src_node": 1, "dst_node": 2,
            "cmd": CMD_WRITE_CHARGE, "sample_ms": 1000}
    eid_good = pack_extid(good["dcl"], good["src_node"], good["dst_node"],
                          good["cmd"], good["direction"])
    unpacked_good = unpack_extid(eid_good)
    roundtrip_ok = all(unpacked_good[k] == good[k]
                       for k in ("direction", "dcl", "src_node", "dst_node", "cmd"))
    good_valid = upper_validity({**unpacked_good, "sample_ms": good["sample_ms"]}, 5000)

    # Semantically illegal node: packs/unpacks perfectly, but chain rejects it.
    bad = dict(good, dst_node=200)  # 200 is outside VALID_NODES (0..5)
    eid_bad = pack_extid(bad["dcl"], bad["src_node"], bad["dst_node"],
                         bad["cmd"], bad["direction"])
    unpacked_bad = unpack_extid(eid_bad)
    bad_roundtrip_ok = (unpacked_bad["dst_node"] == 200)
    bad_valid = upper_validity({**unpacked_bad, "sample_ms": bad["sample_ms"]}, 5000)

    # Stale sample: mechanically fine, rejected for expiry (freshness != bitmap).
    stale_valid = upper_validity({**unpacked_good, "sample_ms": 1000}, 20_000)

    # Status byte: implemented bit2/bit3 = charge_allowed / charge_ok.
    sb = pack_status(False, True, True, False)
    su = unpack_status(sb)
    status_ok = (
        sb == 0b0000_0110
        and su["is_balancing"] is True and su["charge_allowed"] is True
        and su["is_charging"] is False and su["charge_ok"] is False
    )

    result["can_bitmap"] = {
        "extid_good": hex(eid_good),
        "extid_is_29bit": bool(eid_good <= EXTID_MASK),
        "roundtrip_fields_ok": bool(roundtrip_ok),
        "valid_frame_accepted": bool(good_valid["valid"]),
        "illegal_node_extid": hex(eid_bad),
        "illegal_node_roundtrips": bool(bad_roundtrip_ok),
        "illegal_node_reasons": bad_valid["reasons"],
        "illegal_node_rejected_by_chain": bool(not bad_valid["valid"]),
        "separation_mechanical_ok_but_semantic_rejected": bool(
            roundtrip_ok and bad_roundtrip_ok and not bad_valid["valid"]),
        "stale_sample_reasons": stale_valid["reasons"],
        "stale_sample_rejected": bool(not stale_valid["valid"]),
        "status_byte": sb,
        "status_unpacked": su,
        "status_bit2_bit3_ok": bool(status_ok),
        "cache_reclaim_ms_distinct_from_expiry_ms":
            bool(CACHE_RECLAIM_MS != EXPIRY_MS),
        "note": ("Pack/unpack is mechanical and accepts any 8-bit node; the upper "
                 "validity chain separately enforces node range, command set and "
                 "sample freshness. status bit2=charge_allowed, bit3=charge_ok "
                 "(VESC-02). Cache reclaim (10 min) is distinct from safety "
                 "freshness (10 s) (VESC-03)."),
    }

    # ---------- Part 2: CRC-15/PEC detection + silent-failure counterexample ---
    payload = np.array([0x01, 0x0A, 0x02, 0xC4, 0x00, 0x3F], dtype=np.uint8)
    pec = pec15(payload)
    frame = np.append(payload, np.array(list(pec.to_bytes(2, "big")), dtype=np.uint8))

    def corrupted(injections):
        f = frame.copy()
        for byte_idx, bit_mask in injections:
            f[byte_idx] ^= np.uint8(bit_mask)
        return f

    clean = verify_frame(frame, pec_enabled=True)
    single = corrupted([(0, 0b00000001)])                 # 1-bit flip
    two = corrupted([(1, 0b00000100), (4, 0b00100000)])   # 2 separated bits
    burst = corrupted([(2, 0b00001000 | 0b00010000)])     # 2 adjacent bits (burst)
    r_single = verify_frame(single, pec_enabled=True)
    r_two = verify_frame(two, pec_enabled=True)
    r_burst = verify_frame(burst, pec_enabled=True)
    # Counterexample: same corruptions accepted when PEC check disabled.
    r_single_off = verify_frame(single, pec_enabled=False)
    r_burst_off = verify_frame(burst, pec_enabled=False)

    result["pec"] = {
        "poly": hex(PEC_POLY),
        "seed": hex(SEED),
        "payload_hex": payload.tobytes().hex(),
        "pec_hex": hex(pec),
        "frame_hex": frame.tobytes().hex(),
        "clean_accepted": bool(clean["accepted"]),
        "single_bit_detected": bool(not r_single["accepted"]),
        "single_bit_computed": hex(r_single["computed"]),
        "two_bit_detected": bool(not r_two["accepted"]),
        "two_bit_computed": hex(r_two["computed"]),
        "burst_detected": bool(not r_burst["accepted"]),
        "burst_computed": hex(r_burst["computed"]),
        "pec_off_accepts_single_bit": bool(r_single_off["accepted"]),
        "pec_off_accepts_burst": bool(r_burst_off["accepted"]),
        "pec_off_skips_comparison": bool(not r_single_off["checked"]),
        "silent_failure_counterexample": bool(
            (not r_burst["accepted"]) and r_burst_off["accepted"]),
        "note": ("Independently authored CRC-15 detects 1-bit, 2-bit and adjacent "
                 "burst flips. With the comparison disabled (upstream open-wire "
                 "block commented out, VESC-07) the identical corruption is accepted "
                 "without any check -- a silent failure registered as counterexample."),
    }

    # ---------- Part 3: permission / derating chain ----------
    permission_bitmap = (1 << CMD_READ_STATUS) | (1 << CMD_WRITE_CHARGE)  # no SET_SOC
    audit = []
    r_unauth = process_command(CMD_SET_SOC, 2500, permission_bitmap, False,
                               3000, 1000, audit)
    r_ok = process_command(CMD_WRITE_CHARGE, 2500, permission_bitmap, False,
                           3000, 1000, audit)
    r_derate = process_command(CMD_WRITE_CHARGE, 2500, permission_bitmap, True,
                               3000, 1000, audit)
    denied_logged = any(e["event"] == "DENY" and e["cmd"] == CMD_SET_SOC for e in audit)
    # Independence, tested with real cross-calls (no self-comparison):
    # (1) 授权判定与降额标志无关：同一授权命令在 derating=False/True 下都执行，
    #     授权段结论相同（executed=True），仅执行参数被钳制不同。
    r_ok2 = process_command(CMD_WRITE_CHARGE, 2500, permission_bitmap, True,
                            3000, 1000, audit)
    auth_independent = bool(
        r_ok["executed"] and r_ok2["executed"]
        and r_ok["stage"] == "execute" and r_ok2["stage"] == "execute"
        and r_ok["param"] == 2500 and r_ok2["param"] == 1000
    )
    # (2) 降额钳制与权限位图无关：两个都授权的位图 + 同一降额标志 → 钳制结果相同。
    alt_bitmap = permission_bitmap | (1 << CMD_SET_SOC)  # 仍授权 WRITE_CHARGE，但多授权一条
    r_alt = process_command(CMD_WRITE_CHARGE, 2500, alt_bitmap, True,
                            3000, 1000, audit)
    derate_independent = bool(
        r_alt["executed"] and r_alt["param"] == 1000
        and apply_derating(2500, True, 3000, 1000) == 1000
        and apply_derating(2500, False, 3000, 1000) == 2500
    )

    result["permission_derating"] = {
        "permission_bitmap": bin(permission_bitmap),
        "unauthorized_cmd": CMD_SET_SOC,
        "unauthorized_rejected": bool(not r_unauth["executed"]),
        "unauthorized_stage": r_unauth["stage"],
        "unauthorized_reason": r_unauth["reason"],
        "denial_logged": bool(denied_logged),
        "audit_log": audit,
        "authorized_executed_param": r_ok["param"],
        "authorized_param_unchanged": bool(r_ok["executed"] and r_ok["param"] == 2500),
        "derated_executed_param": r_derate["param"],
        "derating_clamps_param": bool(
            r_derate["executed"] and r_derate["param"] == 1000
            and r_derate["param"] < r_ok["param"]),
        "permission_independent_of_derating": bool(auth_independent),
        "derating_independent_of_permission": bool(derate_independent),
        "note": ("Authorization (permission bitmap) and derating (parameter clamp) "
                 "are separate decisions and independently testable; an unauthorized "
                 "write is denied+logged, while an authorized command under a derating "
                 "flag is executed with its charge current clamped 2500->1000 mA."),
    }

    cb, pe, pd = result["can_bitmap"], result["pec"], result["permission_derating"]
    result["all_pass"] = bool(
        cb["extid_is_29bit"] and cb["roundtrip_fields_ok"] and cb["valid_frame_accepted"]
        and cb["illegal_node_roundtrips"] and cb["illegal_node_rejected_by_chain"]
        and cb["separation_mechanical_ok_but_semantic_rejected"]
        and cb["stale_sample_rejected"] and cb["status_bit2_bit3_ok"]
        and cb["cache_reclaim_ms_distinct_from_expiry_ms"]
        and pe["clean_accepted"] and pe["single_bit_detected"] and pe["two_bit_detected"]
        and pe["burst_detected"] and pe["pec_off_accepts_single_bit"]
        and pe["pec_off_accepts_burst"] and pe["pec_off_skips_comparison"]
        and pe["silent_failure_counterexample"]
        and pd["unauthorized_rejected"] and pd["denial_logged"]
        and pd["authorized_param_unchanged"] and pd["derating_clamps_param"]
        and pd["permission_independent_of_derating"]
        and pd["derating_independent_of_permission"]
    )

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in
                      ["all_pass", "can_bitmap", "pec", "permission_derating"]},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
