"""Teaching demonstration for D01: identical terminal voltage, different internal states.

Scenario ``D01-same-terminal-voltage`` (synthetic, SRC01 pending): three physically
different states of one LFP-like cell are arranged to present the *same* terminal
voltage under the *same* load current. The demonstration exists to falsify the
claim "one voltage reading tells the state"; it is not cell data and must not be
cited as such.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SCENARIO_ID = "D01-same-terminal-voltage"

# LFP-like teaching OCV curve (synthetic, monotone piecewise-linear in z).
# Real OCV tables must come from a cell datasheet (SRC01) before any product use.
OCV_POINTS = [
    (0.00, 3.00),
    (0.10, 3.20),
    (0.30, 3.30),
    (0.55, 3.32),
    (0.80, 3.35),
    (0.90, 3.40),
    (1.00, 3.45),
]


def ocv(z: float) -> float:
    if not 0.0 <= z <= 1.0:
        raise ValueError("SOC z must be in [0, 1]")
    for (z0, v0), (z1, v1) in zip(OCV_POINTS, OCV_POINTS[1:], strict=False):
        if z0 <= z <= z1:
            return v0 + (v1 - v0) * (z - z0) / (z1 - z0)
    return OCV_POINTS[-1][1]


def terminal_voltage(z: float, load_a: float, resistance_ohm: float, polarization_v: float) -> float:
    """V = U(z) - I*R - v_p with the engineering-side discharge-positive sign."""
    if resistance_ohm < 0 or polarization_v < 0:
        raise ValueError("resistance and polarization must be nonnegative")
    return ocv(z) - load_a * resistance_ohm - polarization_v


def frozen_states() -> list[dict]:
    """Three states engineered to share one terminal voltage at 2.0 A load."""
    # 状态A：常温、中等SOC、新鲜内阻，无额外极化
    a = {"name": "A 常温带载", "z": 0.55, "load_a": 2.0, "resistance_ohm": 0.020, "polarization_v": 0.0}
    a["v"] = round(terminal_voltage(**{k: a[k] for k in ("z", "load_a", "resistance_ohm", "polarization_v")}), 4)
    target = a["v"]
    # 状态B：更高 SOC 但老化内阻与极化更大，压到同一端电压
    b = {"name": "B 老化带载", "z": 0.90, "load_a": 2.0, "resistance_ohm": 0.045, "polarization_v": 0.030}
    b["v"] = round(terminal_voltage(**{k: b[k] for k in ("z", "load_a", "resistance_ohm", "polarization_v")}), 4)
    if not math.isclose(b["v"], target, abs_tol=1e-4):
        raise AssertionError("teaching states drifted: B must equal A's terminal voltage")
    # 状态C：低 SOC 但低温抬升了 OCV（教学合成：OCV 随温度平移），回到同一端电压
    c = {"name": "C 低温带载", "z": 0.20, "load_a": 2.0, "resistance_ohm": 0.030, "polarization_v": 0.0,
         "ocv_shift_v": 0.090}
    c["v"] = round(terminal_voltage(c["z"], c["load_a"], c["resistance_ohm"], c["polarization_v"]) + c["ocv_shift_v"], 4)
    if not math.isclose(c["v"], target, abs_tol=1e-4):
        raise AssertionError("teaching states drifted: C must equal A's terminal voltage")
    for s in (a, b, c):
        s["ocv_v"] = round(ocv(s["z"]) + s.get("ocv_shift_v", 0.0), 4)
    return [a, b, c]


def build_report() -> dict:
    states = frozen_states()
    zs = {s["z"] for s in states}
    return {
        "scenario_id": SCENARIO_ID,
        "identity": "synthetic teaching values; SRC01 (cell datasheet) pending; not cell data",
        "states": states,
        "shared_terminal_v": states[0]["v"],
        "soc_spread_pp": round((max(zs) - min(zs)) * 100, 2),
        "conclusion": "同一端电压对应至少三个不同内部状态；单读数不定状态，必须联合OCV-温度-历史与新信息",
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
