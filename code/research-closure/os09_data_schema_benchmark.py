"""OS09 battery-data-toolkit S9 基准：schema / 单位 / 符号启发式与显式转换分离（不依赖上游库）。

契约（research.md OS09 + snapshot BDT01-BDT04）：
- RawData 原始电流约定「充电为正」；原始循环能量字段用 J，CycleLevelData 能量字段用 Wh。
- schema 校验只检查字段存在/单调性，不等于物理校准；启发式只报警，不得静默翻转符号。
- 必填源字段缺失 → fail-closed 拒收并列缺项；符号/容量矛盾只警告；时间戳非严格递增 → 拒收。
- 显式声明 current_sign 走转换路径（记录来源），与启发式警告路径分离；声明后恒号警告清除。

本基准用 numpy 独立复算，作为 E09/DATA01 变换与身份合同的验收基线。
"""
import json
import platform
from pathlib import Path

import numpy as np

EVIDENCE = Path(__file__).parent / "evidence" / "os09-data-schema-benchmark.json"

# BMS 必填源字段（定义于本适配器，schema 通过不等于物理正确）
REQUIRED_SOURCE_FIELDS = ["timestamp_s", "current_A", "voltage_V", "temperature_C"]
CAPACITY_CHOICE = ("capacity_Ah", "energy_Wh")  # 二选一，至少其一
MIN_SAMPLES = 5  # 符号启发式最少样本数，低于此只警告不下结论
TOL = 1e-9


# ---------------------------------------------------------------------------
# 1. RawData 最小 schema
# ---------------------------------------------------------------------------
def validate_schema(record):
    """返回 accepted 与缺项清单；缺任何必填字段即 fail-closed。"""
    missing = [f for f in REQUIRED_SOURCE_FIELDS if f not in record]
    if not (set(CAPACITY_CHOICE) & record.keys()):
        missing.append("capacity_Ah|energy_Wh")
    return {"accepted": len(missing) == 0, "missing": missing}


# ---------------------------------------------------------------------------
# 2. 符号 / 单位启发式（与显式转换分离）
# ---------------------------------------------------------------------------
def screen_heuristics(table, declared_sign=None):
    """启发式：只产生 warnings / 拒收，绝不修改数据。

    declared_sign 非 None 表示用户已显式声明符号约定 → 恒号警告(a)被清除，
    因为歧义由元数据解决，无需猜测（转换路径另走 convert_current_sign）。
    """
    warnings = []
    t = np.asarray(table["timestamp_s"], dtype=float)
    cur = np.asarray(table["current_A"], dtype=float)
    cap_key = "capacity_Ah" if "capacity_Ah" in table else "energy_Wh"
    cap = np.asarray(table[cap_key], dtype=float)

    # (c) 时间戳非严格递增（数据缺陷 → 拒收）
    ts_ok = len(t) >= 2 and bool(np.all(np.diff(t) > 0))
    rejected = not ts_ok
    reject_reason = None if ts_ok else "timestamp_not_strictly_increasing"

    # 数据不足：启发式无法下结论 → 仅警告
    if len(cur) < MIN_SAMPLES:
        warnings.append("insufficient_data_for_sign_heuristic")
    else:
        # (a) 电流符号全程恒定非零（疑似未标放电符号 → 警告，不拒收）
        if declared_sign is None and (bool(np.all(cur > 0)) or bool(np.all(cur < 0))):
            warnings.append("current_sign_constant_nonzero")

        # (b) 容量列与充电为正约定的矛盾：
        #     充电(i>0)时容量应升、放电(i<0)时容量应降；反向则警告。
        if len(cap) == len(cur) and len(cur) >= 2:
            dcap = np.diff(cap)
            imid = 0.5 * (cur[:-1] + cur[1:])
            conflict = int(np.count_nonzero(((imid > 0) & (dcap < 0)) | ((imid < 0) & (dcap > 0))))
            if conflict:
                warnings.append("capacity_current_convention_conflict")
        else:
            warnings.append("insufficient_data_for_capacity_heuristic")

    return {
        "accepted": not rejected,
        "rejected": rejected,
        "reject_reason": reject_reason,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# 3. 显式转换路径（与警告路径分离，带来源记录）
# ---------------------------------------------------------------------------
def convert_current_sign(current, declared_sign):
    """把声明的电流约定转换到规范「充电为正」；返回 (电流, 变换名)。"""
    c = np.asarray(current, dtype=float)
    if declared_sign == "charge_positive":
        return c, "identity"
    if declared_sign == "discharge_negative":
        # discharge<0 等价于 charge>0，已是规范方向
        return c, "identity (discharge<0 == charge>0 canonical)"
    if declared_sign == "discharge_positive":
        return -c, "negate"
    raise ValueError(f"unknown current_sign: {declared_sign}")


# ---------------------------------------------------------------------------
# 4. CycleLevelData 聚合 + 单位（J→Wh）
# ---------------------------------------------------------------------------
def joules_to_wh(j):
    return j / 3600.0


def aggregate_cycles(table, nominal_capacity_Ah):
    """按电流符号的连续段聚合容量吞吐、能量(J/Wh)、平均倍率。"""
    t = np.asarray(table["timestamp_s"], dtype=float)
    cur = np.asarray(table["current_A"], dtype=float)
    volt = np.asarray(table["voltage_V"], dtype=float)
    dt = np.diff(t)                     # 每段秒数
    i = cur[:-1]                        # 每段电流
    v = volt[:-1]
    ah = np.abs(i) * dt / 3600.0        # 每段 Ah
    joule = np.abs(i) * v * dt          # 每段 J
    wh = joule / 3600.0                 # J → Wh
    sign = np.where(i > 0, 1, np.where(i < 0, -1, 0))

    segments = []
    start = 0
    for k in range(1, len(sign) + 1):
        if k == len(sign) or sign[k] != sign[start]:
            s = sign[start]
            seg = {
                "kind": "charge" if s > 0 else "discharge" if s < 0 else "rest",
                "start_interval": start,
                "end_interval": k - 1,
                "capacity_throughput_Ah": float(ah[start:k].sum()),
                "duration_s": float(dt[start:k].sum()),
                "energy_J": float(joule[start:k].sum()),
                "energy_Wh": float(wh[start:k].sum()),
            }
            seg["avg_current_A"] = seg["capacity_throughput_Ah"] * 3600.0 / seg["duration_s"]
            seg["avg_c_rate"] = seg["avg_current_A"] / nominal_capacity_Ah
            segments.append(seg)
            start = k
    return segments


def main():
    result = {
        "source_id": "OS09",
        "benchmark": "S9 schema/单位/符号启发式与显式转换分离（不依赖 battery-data-toolkit）",
        "python": platform.python_version(),
        "required_source_fields": REQUIRED_SOURCE_FIELDS,
        "capacity_choice": list(CAPACITY_CHOICE),
        "raw_current_convention": "charge_positive",
        "raw_cycle_energy_unit": "J",
        "cycle_level_energy_unit": "Wh",
    }

    # ---- 1. schema 必填字段检测 ----
    full = {
        "timestamp_s": [0.0, 1.0], "current_A": [1.0, -1.0],
        "voltage_V": [3.7, 3.7], "temperature_C": [25.0, 25.0],
        "capacity_Ah": [5.0, 5.0],
    }
    energy_only = dict(full)
    energy_only.pop("capacity_Ah")
    energy_only["energy_Wh"] = [18.5, 18.5]
    broken = dict(full)
    for k in ("current_A", "temperature_C", "capacity_Ah", "energy_Wh"):
        broken.pop(k, None)
    s_full = validate_schema(full)
    s_energy = validate_schema(energy_only)
    s_broken = validate_schema(broken)
    result["schema"] = {
        "full_accepted": s_full["accepted"],
        "energy_only_accepted": s_energy["accepted"],
        "broken_rejected": not s_broken["accepted"],
        "broken_missing": s_broken["missing"],
        "missing_lists_all": bool(
            {"current_A", "temperature_C", "capacity_Ah|energy_Wh"} <= set(s_broken["missing"])
        ),
        "pass": bool(s_full["accepted"] and s_energy["accepted"] and not s_broken["accepted"]
                     and {"current_A", "temperature_C", "capacity_Ah|energy_Wh"} <= set(s_broken["missing"])),
    }

    # ---- 2. 启发式：(a)(b) 只警告，(c) 拒收 ----
    good_ts = np.arange(MIN_SAMPLES + 1, dtype=float) * 1.0
    # (a) 恒正电流（疑似未标放电符号）
    const_pos = {
        "timestamp_s": good_ts, "current_A": np.full(MIN_SAMPLES + 1, 2.0),
        "voltage_V": np.full(MIN_SAMPLES + 1, 3.7),
        "capacity_Ah": np.linspace(5.0, 4.0, MIN_SAMPLES + 1),
        "temperature_C": np.full(MIN_SAMPLES + 1, 25.0),
    }
    # (b) 符号交替但容量全程递减（充电时容量反降 → 矛盾）
    conflict = {
        "timestamp_s": np.arange(7, dtype=float),
        "current_A": np.array([2.0, 2.0, -2.0, -2.0, 2.0, 2.0, 2.0]),
        "voltage_V": np.full(7, 3.7),
        "capacity_Ah": np.array([5.0, 4.8, 4.6, 4.4, 4.2, 4.0, 3.8]),
        "temperature_C": np.full(7, 25.0),
    }
    # 一致数据：充电容量升、放电容量降 → 无警告
    consistent = {
        "timestamp_s": np.arange(5, dtype=float),
        "current_A": np.array([2.0, 2.0, -2.0, -2.0, -2.0]),
        "voltage_V": np.full(5, 3.7),
        "capacity_Ah": np.array([4.0, 4.1, 4.2, 4.1, 4.0]),
        "temperature_C": np.full(5, 25.0),
    }
    # (c) 时间戳重复 + 回退 → 拒收
    bad_ts = dict(consistent)
    bad_ts["timestamp_s"] = np.array([0.0, 1.0, 1.0, 3.0, 2.0])
    # 数据不足分支 → 只警告
    short = {k: np.asarray(v)[:3] for k, v in consistent.items()}

    h_a = screen_heuristics(const_pos)
    h_b = screen_heuristics(conflict)
    h_ok = screen_heuristics(consistent)
    h_c = screen_heuristics(bad_ts)
    h_short = screen_heuristics(short)
    result["heuristics"] = {
        "a_const_sign_warn_only": {
            "accepted": h_a["accepted"], "warnings": h_a["warnings"],
            "pass": bool(h_a["accepted"] and "current_sign_constant_nonzero" in h_a["warnings"]),
        },
        "b_capacity_conflict_warn_only": {
            "accepted": h_b["accepted"], "warnings": h_b["warnings"],
            "pass": bool(h_b["accepted"] and "capacity_current_convention_conflict" in h_b["warnings"]),
        },
        "consistent_no_warning": {
            "accepted": h_ok["accepted"], "warnings": h_ok["warnings"],
            "pass": bool(h_ok["accepted"] and not h_ok["warnings"]),
        },
        "c_timestamp_reject": {
            "rejected": h_c["rejected"], "reason": h_c["reject_reason"],
            "pass": bool(h_c["rejected"] and h_c["reject_reason"] == "timestamp_not_strictly_increasing"),
        },
        "insufficient_data_warn_only": {
            "accepted": h_short["accepted"], "warnings": h_short["warnings"],
            "pass": bool(h_short["accepted"] and "insufficient_data_for_sign_heuristic" in h_short["warnings"]),
        },
    }
    result["heuristics"]["pass"] = bool(all(
        v["pass"] for k, v in result["heuristics"].items() if isinstance(v, dict)
    ))

    # ---- 3. 显式转换清除 (a) 警告；转换路径与警告路径分离 ----
    conv_cur, conv_name = convert_current_sign(const_pos["current_A"], "discharge_negative")
    h_conv = screen_heuristics(const_pos, declared_sign="discharge_negative")
    flip_cur, flip_name = convert_current_sign(np.array([1.0, -2.0]), "discharge_positive")
    result["explicit_conversion"] = {
        "declared_sign": "discharge_negative",
        "transform": conv_name,
        "a_warning_cleared": "current_sign_constant_nonzero" not in h_conv["warnings"],
        "still_accepted": h_conv["accepted"],
        "numeric_identity_to_canonical": bool(np.allclose(conv_cur, const_pos["current_A"])),
        "discharge_positive_transform": flip_name,
        "discharge_positive_negates": bool(np.allclose(flip_cur, np.array([-1.0, 2.0]))),
        "pass": bool(
            "current_sign_constant_nonzero" not in h_conv["warnings"]
            and h_conv["accepted"]
            and np.allclose(conv_cur, const_pos["current_A"])
            and np.allclose(flip_cur, np.array([-1.0, 2.0]))
        ),
    }

    # ---- 4. CycleLevelData 聚合手算对照 ----
    nominal = 5.0  # Ah 额定容量
    t = np.arange(13, dtype=float) * 600.0                       # 0..7200s, 12 段各 600s
    cur = np.array([2.0] * 4 + [-3.0] * 4 + [1.0] * 5)          # 段：充4 放4 充4(12 段用索引0-11)
    volt = np.full(13, 3.7)
    raw = {
        "timestamp_s": t, "current_A": cur, "voltage_V": volt,
        "capacity_Ah": np.full(13, nominal), "temperature_C": np.full(13, 25.0),
    }
    segs = aggregate_cycles(raw, nominal)

    # 手算：每段 4 个间隔 × dt=600s
    hand_ah = [4 * 2 * 600 / 3600, 4 * 3 * 600 / 3600, 4 * 1 * 600 / 3600]  # [4/3, 2, 2/3]
    hand_j = [4 * 2 * 3.7 * 600, 4 * 3 * 3.7 * 600, 4 * 1 * 3.7 * 600]
    hand_wh = [j / 3600.0 for j in hand_j]
    hand_cr = [2 / nominal, 3 / nominal, 1 / nominal]
    hand_kind = ["charge", "discharge", "charge"]
    per_seg_ah_ok = all(abs(segs[k]["capacity_throughput_Ah"] - hand_ah[k]) < TOL for k in range(3))
    per_seg_j_ok = all(abs(segs[k]["energy_J"] - hand_j[k]) < TOL for k in range(3))
    per_seg_wh_ok = all(abs(segs[k]["energy_Wh"] - hand_wh[k]) < TOL for k in range(3))
    per_seg_cr_ok = all(abs(segs[k]["avg_c_rate"] - hand_cr[k]) < TOL for k in range(3))
    kind_ok = [segs[k]["kind"] == hand_kind[k] for k in range(3)]

    chg_total = sum(s["capacity_throughput_Ah"] for s in segs if s["kind"] == "charge")
    dis_total = sum(s["capacity_throughput_Ah"] for s in segs if s["kind"] == "discharge")
    hand_chg, hand_dis = hand_ah[0] + hand_ah[2], hand_ah[1]

    result["cycle_aggregation"] = {
        "nominal_capacity_Ah": nominal,
        "segments": [
            {
                "kind": s["kind"],
                "capacity_throughput_Ah": s["capacity_throughput_Ah"],
                "energy_J": s["energy_J"],
                "energy_Wh": s["energy_Wh"],
                "avg_current_A": s["avg_current_A"],
                "avg_c_rate": s["avg_c_rate"],
            }
            for s in segs
        ],
        "hand_capacity_Ah": hand_ah,
        "hand_energy_Wh": hand_wh,
        "hand_avg_c_rate": hand_cr,
        "per_seg_capacity_match": per_seg_ah_ok,
        "per_seg_energy_J_match": per_seg_j_ok,
        "per_seg_energy_Wh_match": per_seg_wh_ok,
        "per_seg_c_rate_match": per_seg_cr_ok,
        "segment_kinds_match": all(kind_ok),
        "charge_total_Ah": chg_total,
        "discharge_total_Ah": dis_total,
        "hand_charge_total_Ah": hand_chg,
        "hand_discharge_total_Ah": hand_dis,
        "totals_match": bool(abs(chg_total - hand_chg) < TOL and abs(dis_total - hand_dis) < TOL),
        "unit_J3600_to_Wh": joules_to_wh(3600.0),
        "unit_26640J_to_Wh": joules_to_wh(26640.0),
        "pass": bool(per_seg_ah_ok and per_seg_j_ok and per_seg_wh_ok and per_seg_cr_ok
                     and all(kind_ok) and abs(chg_total - hand_chg) < TOL
                     and abs(dis_total - hand_dis) < TOL
                     and abs(joules_to_wh(3600.0) - 1.0) < TOL
                     and abs(joules_to_wh(26640.0) - 7.4) < TOL),
    }

    result["all_pass"] = bool(
        result["schema"]["pass"]
        and result["heuristics"]["pass"]
        and result["explicit_conversion"]["pass"]
        and result["cycle_aggregation"]["pass"]
    )
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in
                      ["all_pass", "schema", "heuristics", "explicit_conversion", "cycle_aggregation"]},
                     ensure_ascii=False, indent=1))
    assert result["all_pass"], "OS09 benchmark check failed"


if __name__ == "__main__":
    main()
