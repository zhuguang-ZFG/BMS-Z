"""Teaching experiments for D09: independence claims, latent-fault arithmetic,
and an FMEA micro-case. Teaching values; real FMEDAs follow the same structure
with field failure data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SCENARIO_ID = "D09-independence-fmea"

LAMBDA_PER_H = 1e-6  # 保护通道失效率（教学值）
DIAG_INTERVAL_H = 1.0  # 诊断间隔（教学值）
EXPOSURE_UNDIAGNOSED_H = 100.0
SUPPRESSION_WINDOW_S = 0.1  # 故障反应窗口（教学值，对应 D08 百毫秒级）


def latent_exposure_per_h(
    lambda_per_h: float = LAMBDA_PER_H, diag_interval_h: float = DIAG_INTERVAL_H
) -> float:
    """Cycle-average unavailable probability ≈ λT/2 (dimensionless, λT ≪ 1).

    The public function name retains the input-rate convention; the result is
    not a rate. Assume perfect periodic detection and immediate restoration.
    """
    if lambda_per_h < 0 or diag_interval_h <= 0:
        raise ValueError("lambda must be nonnegative and interval positive")
    return lambda_per_h * diag_interval_h / 2.0


def independence_matrix() -> list[dict]:
    """诊断覆盖与共因隔离的审查提示，不代替逐项失效模式论证。"""
    return [
        {"coverage": "低", "isolated": False, "buys": "漏诊与共因风险均需补证"},
        {"coverage": "高", "isolated": False, "buys": "共因失效仍可使两路同时失效"},
        {"coverage": "低", "isolated": True, "buys": "已识别共因有隔离，未检出的随机失效仍需控制"},
        {
            "coverage": "高",
            "isolated": True,
            "buys": "对已分析模式提供覆盖与隔离证据；仍需核查残余风险",
        },
    ]


def common_supply_counterexample() -> dict:
    """双保护共用一路供电：供电失效时两路同时离线——独立性声明不成立。"""
    return {
        "claim": "双 MCU 双算法，互为备份",
        "shared": ["供电", "基准源", "传感链", "时钟"],
        "failure": "供电轨失效",
        "result": "两路同时离线，备份概率为 0",
        "fix": "独立供电 + 独立基准；传感链共用则明确写出覆盖缺口",
        "conclusion": "独立性按失效模式逐条审，不按‘有几颗芯片’审",
    }


def fmea_rows() -> list[dict]:
    """FMEA 小案例（教学值）：失效模式/后果/起因/现有控制/诊断间隔/动作。"""
    return [
        {
            "mode": "主 MCU 死机",
            "effect": "保护全停",
            "cause": "软件跑飞/时钟失效",
            "control": "独立硬件比较器通道（隔离供电）",
            "diag_h": 0.0,
            "action": "看门狗复位 + 硬件通道直断",
        },
        {
            "mode": "电流传感失效卡值",
            "effect": "过流不动作",
            "cause": "开线/偏置漂移",
            "control": "窗口稽核（D5.3）",
            "diag_h": 1.0,
            "action": "稽核失败锁存并降级",
        },
        {
            "mode": "驱动电源跌落",
            "effect": "栅极悬空误导通",
            "cause": "供电轨欠压",
            "control": "欠压锁定(UVLO) + 下拉电阻",
            "diag_h": 0.0,
            "action": "UVLO 期间禁止功率级",
        },
        {
            "mode": "传感链共因漂移",
            "effect": "双通道同向错",
            "cause": "共用基准温漂",
            "control": "无（共因缺口明示）",
            "diag_h": 24.0,
            "action": "换独立基准；闭合前写入残余风险",
        },
    ]


def build_report() -> dict:
    average_1h = latent_exposure_per_h(LAMBDA_PER_H, DIAG_INTERVAL_H)
    average_100h = latent_exposure_per_h(LAMBDA_PER_H, EXPOSURE_UNDIAGNOSED_H)
    return {
        "scenario_id": SCENARIO_ID,
        "identity": "teaching values; real FMEDA uses field failure rates",
        "latent": {
            "with_diag_1h": average_1h,
            "with_diag_100h": average_100h,
            "undiagnosed_100h": LAMBDA_PER_H * EXPOSURE_UNDIAGNOSED_H,
            "ratio": round(average_100h / average_1h, 1),
            "comparison": "cycle-average unavailable probabilities at 100h and 1h diagnostic intervals; dimensionless",
            "endpoint": "undiagnosed_100h is the end-of-100h probability without diagnosis, not the ratio numerator",
        },
        "independence": independence_matrix(),
        "common_supply": common_supply_counterexample(),
        "fmea": fmea_rows(),
        "conclusion": "诊断间隔把潜伏暴露压到 λ×T/2；独立性按失效模式逐条审，共因缺口明示不藏",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="写 report.json 的目录")
    args = parser.parse_args()
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
