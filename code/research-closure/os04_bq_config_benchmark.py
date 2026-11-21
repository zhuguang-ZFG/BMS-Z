"""OS04 LibreSolar/S4 基准：BQ769x2 风格保护参数链（独立实现，不依赖上游固件）。

合同（research.md OS04 行 + snapshot.json LS-FW-01/02/03）：
  保护设定经历 量化 -> 限幅 -> 写入 -> 配置对象回填；
  * 回填的是“表征值”（reg*step+offset），不是硬件寄存器回读，也不证明写入成功；
  * 回填值 != 物理量设定值（量化后必然有 <= step/2 的残差）；
  * 寄存器实际内容可与回填值不一致（NACK 重试/幽灵 ACK 后寄存器仍旧值）；
  * 通信层的 等待/重试/长度/校验和 是异常注入点，不等于实测 WCET。
本脚本用标准库 + numpy 独立复算该语义；不 import 上游 OS 库，不复用其代码。
寄存器地址/位宽/步进取自快照语义（50.6 mV、3.3 ms），为教学用示意值，
不声称与具体器件手册逐位一致。
"""
import json
import platform
from pathlib import Path

import numpy as np

EVIDENCE = Path(__file__).parent / "evidence" / "os04-bq-config-benchmark.json"

# 参数链模型（由快照 LS-FW-01 的步进语义导出；限幅为示意的受约束编码域）
V_STEP = 0.0506  # COV/CUV 电压步进 50.6 mV
V_OFFSET = 0.0
DLY_STEP = 3.3  # 延时步进 3.3 ms
DLY_OFFSET = 0.0
V_REG_MAX = 255  # 示意：受约束的电压编码上界（用于演示静默限幅）
DLY_REG_MAX = 4095
ADDR = {"OV": 0x9298, "UV": 0x929A, "OV_DLY": 0x929C}  # 示意数据存储器地址


def encode(setpoint, step, offset, reg_min, reg_max):
    """量化 + 静默限幅：reg = round((V-offset)/step) 后 clamp 到编码域。

    返回表征值 represented = clamp(reg)*step+offset 及量化/限幅证据。
    """
    raw = round((setpoint - offset) / step)
    reg = max(reg_min, min(reg_max, raw))
    represented = reg * step + offset
    return {
        "setpoint": setpoint,
        "raw_reg": raw,
        "reg": reg,
        "represented": represented,
        "quant_error": represented - setpoint,
        "clamped": reg != raw,
    }


class SimAFE:
    """模拟 BQ769x2 数据存储器寄存器文件（地址 -> 整数编码）。"""

    def __init__(self):
        self.regs = {}

    def read(self, addr):
        return self.regs.get(addr)


def iface_write(afe, addr, reg_code, *, expected_length=1, checksum=None,
                nack_attempts=0, max_retries=1, commit=True,
                bad_length=False, bad_checksum=False):
    """独立复现数据存储器写入接口的 等待/重试/长度/校验和 结构。

    故障旋钮是异常注入点，不是计时测量（不产出 WCET）。
    """
    attempts = 0
    if bad_length:
        return {"success": False, "error": "length", "attempts": attempts}
    if checksum is None:
        checksum = reg_code & 0xFF
    if bad_checksum or checksum != (reg_code & 0xFF):
        return {"success": False, "error": "checksum", "attempts": attempts}
    # expected_length 校验：本模型载荷恒为 1 字节
    if expected_length != 1:
        return {"success": False, "error": "length", "attempts": attempts}
    for _ in range(max_retries + 1):
        attempts += 1
        if attempts <= nack_attempts:
            continue  # 就绪检查 NACK -> 等待并重试
        if commit:
            afe.regs[addr] = reg_code
        return {"success": True, "error": None, "attempts": attempts,
                "committed": commit}
    return {"success": False, "error": "ready_timeout", "attempts": attempts}


def configure(afe, enc, addr, *, fault=None):
    """模拟固件配置函数：量化 -> 写入 -> 用表征值回填配置对象。

    关键：回填独立于写入返回码（这正是固件语义，也是需检查返回码的原因）。
    """
    fault = fault or {}
    result = iface_write(afe, addr, enc["reg"], **fault)
    config_backfill = enc["represented"]  # 配置对象用表征值刷新
    return result, config_backfill


def main():
    setpoints = {"OV": 4.25, "UV": 2.8, "OV_DLY": 1000.0}
    encodings = {
        "OV": encode(setpoints["OV"], V_STEP, V_OFFSET, 0, V_REG_MAX),
        "UV": encode(setpoints["UV"], V_STEP, V_OFFSET, 0, V_REG_MAX),
        "OV_DLY": encode(setpoints["OV_DLY"], DLY_STEP, DLY_OFFSET, 0, DLY_REG_MAX),
    }
    steps = {"OV": V_STEP, "UV": V_STEP, "OV_DLY": DLY_STEP}

    result = {
        "source_id": "OS04",
        "benchmark": "S4 BQ769x2 风格保护参数链：量化/限幅/写入/回填与回读一致性反例",
        "python": platform.python_version(),
        "model": {
            "v_step": V_STEP, "v_offset": V_OFFSET, "v_reg_max": V_REG_MAX,
            "delay_step": DLY_STEP, "delay_offset": DLY_OFFSET, "delay_reg_max": DLY_REG_MAX,
            "note": "步进取自 LS-FW-01 语义；地址/位宽为教学示意，非器件手册逐位复刻。",
        },
        "setpoints": setpoints,
        "encodings": encodings,
    }

    checks = {}
    # ---- 量化：往返误差 <= step/2；回填值 != 设定值 ----
    errs = np.array([abs(encodings[k]["quant_error"]) for k in setpoints])
    halves = np.array([steps[k] / 2 for k in setpoints])
    quant_all = bool(np.all(errs <= halves))
    backfill_differs = {k: bool(encodings[k]["represented"] != setpoints[k])
                        for k in setpoints}
    result["quantization"] = {
        "abs_errors": {k: abs(encodings[k]["quant_error"]) for k in setpoints},
        "half_steps": {k: steps[k] / 2 for k in setpoints},
        "all_within_half_step": quant_all,
        "backfill_differs_from_setpoint": backfill_differs,
    }
    checks["quantization_within_half_step"] = quant_all
    checks["backfill_value_differs_from_setpoint"] = bool(all(backfill_differs.values()))

    # ---- 限幅：超范围 setpoint 被静默 clamp，写入仍返回 success ----
    afe = SimAFE()
    clamp_enc = encode(20.0, V_STEP, V_OFFSET, 0, V_REG_MAX)
    clamp_write, clamp_backfill = configure(afe, clamp_enc, ADDR["OV"])
    checks["clamp_applied"] = bool(clamp_enc["clamped"] and clamp_enc["reg"] == V_REG_MAX)
    checks["clamp_silent_success"] = bool(clamp_write["success"]
                                          and clamp_backfill != clamp_enc["setpoint"])
    result["clamp"] = {
        "setpoint_V": clamp_enc["setpoint"], "raw_reg": clamp_enc["raw_reg"],
        "clamped_reg": clamp_enc["reg"], "represented_V": clamp_enc["represented"],
        "write_success": bool(clamp_write["success"]),
        "backfill_V": clamp_backfill, "silent_value_changed": bool(clamp_backfill != 20.0),
    }

    # ---- 正常写入：成功返回且寄存器回读与回填一致（此处一致是巧合，非因果） ----
    afe = SimAFE()
    normal_write, normal_backfill = configure(afe, encodings["OV"], ADDR["OV"])
    normal_readback = afe.read(ADDR["OV"])
    normal_v = None if normal_readback is None else normal_readback * V_STEP + V_OFFSET
    checks["normal_write_success_and_consistent"] = bool(
        normal_write["success"] and normal_v is not None
        and abs(normal_v - normal_backfill) < 1e-12)
    result["normal_write"] = {
        "write_success": bool(normal_write["success"]),
        "backfill_V": normal_backfill,
        "register_backfill": normal_readback,
        "readback_V": normal_v,
        "note": "回填未读取寄存器；一致性是两者恰好相等，不构成写入证据。",
    }

    # ---- 关键反例 1：幽灵 ACK（NACK 后重试返回 success，但寄存器仍旧值） ----
    phantom_enc = encode(4.30, V_STEP, V_OFFSET, 0, V_REG_MAX)
    phantom_write, phantom_backfill = configure(
        afe, phantom_enc, ADDR["OV"],
        fault={"nack_attempts": 1, "max_retries": 1, "commit": False})
    phantom_readback = afe.read(ADDR["OV"])
    phantom_v = phantom_readback * V_STEP + V_OFFSET
    result["nack_retry_counterexample"] = {
        "new_setpoint_V": phantom_enc["setpoint"],
        "backfill_V": phantom_backfill,
        "write_success": bool(phantom_write["success"]),
        "attempts": phantom_write["attempts"],
        "committed": bool(phantom_write["committed"]),
        "register_backfill": phantom_readback,
        "readback_V": phantom_v,
    }
    checks["phantom_ack_reported_success"] = bool(phantom_write["success"]
                                                  and phantom_write["attempts"] == 2)
    checks["phantom_ack_register_unchanged"] = bool(phantom_readback == encodings["OV"]["reg"])
    checks["phantom_ack_backfill_ne_readback"] = bool(abs(phantom_backfill - phantom_v) > 1e-12)
    checks["success_return_ne_readback_consistency"] = bool(
        phantom_write["success"] and abs(phantom_backfill - phantom_v) > 1e-12)

    # ---- 关键反例 2：NACK 耗尽返回失败，但忽略返回码仍回填 ----
    old_readback = afe.read(ADDR["OV"])
    fail_write, fail_backfill = configure(
        afe, phantom_enc, ADDR["OV"],
        fault={"nack_attempts": 2, "max_retries": 1})
    checks["ready_timeout_returns_failure"] = bool(
        not fail_write["success"] and fail_write["error"] == "ready_timeout")
    checks["ignored_error_backfill_ne_readback"] = bool(
        abs(fail_backfill - (afe.read(ADDR["OV"]) * V_STEP + V_OFFSET)) > 1e-12
        and afe.read(ADDR["OV"]) == old_readback)
    result["ignored_return_code"] = {
        "write_success": bool(fail_write["success"]),
        "error": fail_write["error"], "attempts": fail_write["attempts"],
        "backfill_V": fail_backfill,
        "register_backfill": afe.read(ADDR["OV"]),
    }

    # ---- 接口异常注入点：长度/校验和错误被拒；重试计数不等于 WCET ----
    bad_len = iface_write(afe, ADDR["OV"], encodings["OV"]["reg"], bad_length=True)
    bad_csum = iface_write(afe, ADDR["OV"], encodings["OV"]["reg"], bad_checksum=True)
    result["interface_injection"] = {
        "bad_length_rejected": bool(not bad_len["success"] and bad_len["error"] == "length"),
        "bad_checksum_rejected": bool(not bad_csum["success"] and bad_csum["error"] == "checksum"),
        "retry_attempts_recorded": phantom_write["attempts"],
        "wcet_claimed": False,
        "note": "等待/重试/长度/校验和是异常注入点；代码层重试常数不代表实测 WCET。",
    }
    checks["bad_length_rejected"] = result["interface_injection"]["bad_length_rejected"]
    checks["bad_checksum_rejected"] = result["interface_injection"]["bad_checksum_rejected"]
    checks["no_wcet_claimed"] = bool(result["interface_injection"]["wcet_claimed"] is False)

    result["checks"] = checks
    result["all_pass"] = bool(all(checks.values()))
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "checks": checks,
                      "quantization": result["quantization"],
                      "clamp": result["clamp"],
                      "normal_write": result["normal_write"],
                      "nack_retry_counterexample": result["nack_retry_counterexample"],
                      "ignored_return_code": result["ignored_return_code"],
                      "interface_injection": result["interface_injection"]},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
