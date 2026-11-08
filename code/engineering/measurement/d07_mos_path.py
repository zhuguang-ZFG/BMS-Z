"""Teaching experiments for D07: back-to-back MOSFET paths, SOA reading, and
gate-drive failure modes. Teaching values throughout (SRC03 pending); the SOA
table is a synthetic stand-in for a real datasheet curve, never a selection.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SCENARIO_ID = "D07-back-to-back"
SOA_SCENARIO_ID = "D07-soa-reading"
DRIVE_SCENARIO_ID = "D07-drive-fault"

RDS_ON_OHM = 2e-3  # 单颗导通电阻（教学值，25 °C）
VF_V = 0.7  # 体二极管正向压降（教学值）
TEMP_COEFF = 1.5  # Rds_on 从 25 °C 到 125 °C 的倍率（教学值）

# 合成 SOA 表（教学替身）：(Vds, 允许电流) @ 脉冲宽度
SOA_TABLE = {
    "dc": {"vds_v": 60.0, "i_a": 8.0},
    "10ms": {"vds_v": 60.0, "i_a": 30.0},
    "100ms": {"vds_v": 60.0, "i_a": 15.0},
    "1s": {"vds_v": 60.0, "i_a": 10.0},
}
AVALANCHE_RATING_MJ = 5.0  # 雪崩能量额定（教学值）
LOOP_L_H = 10e-6  # 分断回路电感（教学值）


def body_diode_loss_w(i_a: float, vf_v: float = VF_V) -> float:
    if i_a < 0:
        raise ValueError("current must be nonnegative")
    return vf_v * i_a


def conduction_loss_w(
    i_a: float, rds_on_ohm: float = RDS_ON_OHM, temp_factor: float = 1.0
) -> float:
    if i_a < 0 or rds_on_ohm <= 0 or temp_factor <= 0:
        raise ValueError("bad arguments")
    return i_a * i_a * rds_on_ohm * temp_factor


def single_mos_blocks(charge_forbidden: bool) -> dict:
    """单颗高边 NMOS：禁充时体二极管仍放得出电；禁放时体二极管仍充得进电。"""
    return {
        "single_mos": True,
        "charge_forbidden": charge_forbidden,
        "blocked_direction": "放电→充电" if charge_forbidden else "充电→放电",
        "body_diode_leaks": True,
        "leak_path": "体二极管与阻断方向相反，永远导通一侧",
        "conclusion": "单颗 NMOS 只挡一个方向；要双向切断必须背靠背",
    }


def back_to_back_loss_ratio(i_a: float) -> dict:
    diode = body_diode_loss_w(i_a)
    rdson = conduction_loss_w(i_a)
    hot = conduction_loss_w(i_a, temp_factor=TEMP_COEFF)
    return {
        "i_a": i_a,
        "body_diode_w": round(diode, 3),
        "rds_on_w": round(rdson, 4),
        "hot_rds_on_w": round(hot, 4),
        "ratio_diode_over_rdson": round(diode / rdson, 1),
        "conclusion": f"{i_a:.0f} A 下体二极管导通 {diode:.1f} W vs Rds_on {rdson:.2f} W（差 {diode / rdson:.0f} 倍）；"
        f"125 °C 时 Rds_on ×{TEMP_COEFF} = {hot:.2f} W",
    }


def soa_check(i_a: float, vds_v: float, pulse_s: float) -> dict:
    """SOA 判读：按脉冲宽度取允许电流；只演示读表方法，不是器件选型。"""
    if i_a < 0 or vds_v <= 0 or pulse_s <= 0:
        raise ValueError("bad arguments")
    key = (
        "dc"
        if pulse_s >= 10.0
        else ("1s" if pulse_s >= 1.0 else ("100ms" if pulse_s >= 0.1 else "10ms"))
    )
    row = SOA_TABLE[key]
    within = i_a <= row["i_a"] and vds_v <= row["vds_v"]
    return {
        "point": {"i_a": i_a, "vds_v": vds_v, "pulse_s": pulse_s},
        "soa_row": row,
        "row_key": key,
        "within_soa": within,
        "conclusion": "工作点在 SOA 内"
        if within
        else f"超出 {key} 行允许电流 {row['i_a']:.0f} A",
    }


def avalanche_energy_mj(i_a: float, loop_l_h: float = LOOP_L_H) -> dict:
    e_mj = 0.5 * loop_l_h * i_a * i_a * 1000.0
    return {
        "loop_l_h": loop_l_h,
        "i_a": i_a,
        "energy_mj": round(e_mj, 3),
        "rating_mj": AVALANCHE_RATING_MJ,
        "within_rating": e_mj <= AVALANCHE_RATING_MJ,
        "conclusion": f"½LI² = {e_mj:.2f} mJ（额定 {AVALANCHE_RATING_MJ:.0f} mJ）——分断感性负载的能量必须进预算",
    }


def drive_fault_modes() -> dict:
    return {
        "scenario_id": DRIVE_SCENARIO_ID,
        "modes": [
            {
                "mode": "栅极悬空",
                "cause": "驱动器未供电/未初始化",
                "consequence": "dv/dt 经 Miller 电容误导通，半桥直通",
                "guard": "栅极下拉电阻 + 上电时序先驱动后功率",
            },
            {
                "mode": "驱动电阻过大",
                "cause": "为压 EMI 盲目加大 Rg",
                "consequence": "开关变慢，开关损耗上升、SOA 内时间变长",
                "guard": "Rg 按损耗与振铃两笔账联合选，不只为 EMI",
            },
            {
                "mode": "负压关断缺失",
                "cause": "高边关断仅靠 0 V",
                "consequence": "桥臂串扰抬升 Vgs，误导通",
                "guard": "按串扰幅值决定是否要负压关断",
            },
        ],
        "conclusion": "驱动故障的共同点：栅极不是逻辑输出，是模拟节点",
    }


def build_report() -> dict:
    return {
        "scenario_id": SCENARIO_ID,
        "identity": "teaching values; SRC03 (device datasheet) pending; SOA table is synthetic",
        "single_mos": single_mos_blocks(charge_forbidden=True),
        "loss_ratio_10a": back_to_back_loss_ratio(10.0),
        "loss_ratio_40a": back_to_back_loss_ratio(40.0),
        "soa": {
            "within": soa_check(20.0, 60.0, 0.01),
            "outside": soa_check(20.0, 60.0, 0.1),
            "dc_edge": soa_check(8.0, 60.0, 30.0),
        },
        "avalanche": avalanche_energy_mj(20.0),
        "drive_faults": drive_fault_modes(),
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
