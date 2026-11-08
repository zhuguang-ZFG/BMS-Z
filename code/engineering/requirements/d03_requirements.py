"""Teaching exercises for D03: requirements quantification and the weakest-cell counterexample.

Scenario ``D03-weakest-cell`` (E04 light part, synthetic): a 16s pack whose *average*
cell voltage comfortably meets the limit while one cell violates it. Also the
requirements-completeness checklist and a measurement/estimation/protection
responsibility split used as the C1 budget draft seed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCENARIO_ID = "D03-weakest-cell"

CELL_LIMITS_V = {"discharge_min_v": 3.30, "charge_max_v": 3.65}

# Teaching pack: 15 healthy cells + one weak cell (synthetic distribution).
FROZEN_CELLS_V = [3.36, 3.38, 3.37, 3.39, 3.36, 3.38, 3.37, 3.40,
                  3.36, 3.38, 3.37, 3.39, 3.36, 3.38, 3.37, 3.28]

REQUIRED_SPEC_FIELDS = [
    "chemistry",
    "series_count",
    "parallel_count",
    "voltage_window_v",
    "soc_window",
    "temperature_window_c",
    "current_or_power_profile",
    "lifetime_target",
    "consistency_requirement",
    "measurement_responsibility",
    "estimation_responsibility",
    "protection_responsibility",
]


def pack_summary(cells_v: list[float]) -> dict:
    if not cells_v:
        raise ValueError("cells must be nonempty")
    avg = sum(cells_v) / len(cells_v)
    return {
        "cells": len(cells_v),
        "average_v": round(avg, 4),
        "weakest_v": round(min(cells_v), 4),
        "strongest_v": round(max(cells_v), 4),
        "spread_mv": round((max(cells_v) - min(cells_v)) * 1000, 2),
    }


def discharge_check(cells_v: list[float], limit_v: float = CELL_LIMITS_V["discharge_min_v"]) -> dict:
    """Average-vs-weakest verdict; the mean passing while a cell fails is the lesson."""
    summary = pack_summary(cells_v)
    violations = [i for i, v in enumerate(cells_v) if v < limit_v]
    return {
        **summary,
        "limit_v": limit_v,
        "average_passes": summary["average_v"] >= limit_v,
        "weakest_passes": summary["weakest_v"] >= limit_v,
        "violating_cells": violations,
        "conclusion": (
            "整包均值达标但单节越限：均值不能代表最弱单节" if violations and summary["average_v"] >= limit_v
            else "全部通过" if not violations else "均值也未达标"
        ),
    }


def missing_spec_fields(spec: dict) -> list[str]:
    """A requirement is quantified only if the field exists and is not a placeholder."""
    missing = []
    for field in REQUIRED_SPEC_FIELDS:
        value = spec.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    return missing


def responsibility_split() -> dict:
    """测量/估计/保护职责分解（C1 预算初稿的种子，S1/S2/S3 的交接口径）。"""
    return {
        "measurement": "给出每个量的值、时刻与有效位（S1：误差界与采样时刻）",
        "estimation": "给出不可测状态的估计与不确定度（S2：参数与 SOC 的区间报告）",
        "protection": "给出越限时的动作与时限（S3/S8：确认、锁存与许可门）",
        "rule": "同一职责只归一个所有者；跨界必须走显式接口与证据",
    }


def build_report() -> dict:
    check = discharge_check(FROZEN_CELLS_V)
    return {
        "scenario_id": SCENARIO_ID,
        "identity": "synthetic teaching distribution; not a measured pack",
        "cell_limits_v": CELL_LIMITS_V,
        "discharge_check": check,
        "required_spec_fields": REQUIRED_SPEC_FIELDS,
        "responsibility_split": responsibility_split(),
        "conclusion": check["conclusion"],
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
