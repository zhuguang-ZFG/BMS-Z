"""OS03 liionpack S3 轻量电路基准：可手算 2p1s / 1p2s 电阻网络（不依赖 liionpack）。

契约（source-adoption.md OS03 行 + 研究文档 E04）：
setup_circuit 式节点网络、两类拓扑、逐电芯输入映射；检查 KCL/KVL、支路电流、
最弱单节和首次约束事件。liionpack 处于维护模式且属复杂依赖——留在研究环境，
本基准用 numpy 节点分析独立复算，作为 G03 轻量电路门的验收基线。

拓扑约定（2p1s）：电芯负端共地；每支路经 link 电阻并入上母排 n_bus_hi；
母排电阻 r_bus 下接地（等效母排/连接电阻）；输出经 term 电阻到 n_out，负载电流源 n_out→地。
手算（对称特例 E=4, r=0.05, I_load=2, 两支路均分）：
  V_out = E − 1·r − 1·r_link − 2·r_bus − 2·r_term
"""
import json
import platform
from pathlib import Path

import numpy as np

EVIDENCE = Path(__file__).parent / "evidence" / "os03-circuit-benchmark.json"
V_MIN = 3.0  # 约束事件阈值（最弱单节端电压首次触及）


def solve_2p1s(cells, r_link, r_bus, r_term, i_load):
    """2p1s 节点分析。cells=[(E,r)x2]。返回节点电压 dict 与支路电流列表。

    路径：电芯负端共地；每支路经 link 电阻并入 n_bus_hi；
    n_bus_hi --r_bus--> n_bus_mid --r_term--> n_out --I_load--> gnd（母排/端子电阻串联，手算可核）。
    """
    nodes = ["n_b1", "n_b2", "n_bus_hi", "n_bus_mid", "n_out"]
    idx = {n: i for i, n in enumerate(nodes)}
    g = np.zeros((5, 5))
    b = np.zeros(5)

    def stamp_r(n1, n2, r):
        gr = 1.0 / r
        for a in (n1, n2):
            if a != "gnd":
                g[idx[a], idx[a]] += gr
        if n1 != "gnd" and n2 != "gnd":
            g[idx[n1], idx[n2]] -= gr
            g[idx[n2], idx[n1]] -= gr

    for k, (e_k, r_k) in enumerate(cells, start=1):
        n = f"n_b{k}"
        stamp_r("gnd", n, r_k)
        b[idx[n]] += e_k / r_k  # Norton 电流源注入
        stamp_r(n, "n_bus_hi", r_link)
    stamp_r("n_bus_hi", "n_bus_mid", r_bus)
    stamp_r("n_bus_mid", "n_out", r_term)
    b[idx["n_out"]] = -i_load
    v = np.linalg.solve(g, b)
    vd = dict(zip(nodes, v, strict=True))
    i_branch = [(vd[f"n_b{k}"] - vd["n_bus_hi"]) / r_link for k in (1, 2)]
    return vd, i_branch


def solve_1p2s(cells, r_link, r_bus, r_term, i_load):
    """1p2s：两电芯串联单支路。

    gnd --cell2(E2,r2)--> n_mid --cell1(E1,r1)--> n_c1 --r_link-->
    n_bus_hi --(r_bus+r_term)--> n_out --I_load--> gnd。
    cell1 的 Norton 源另一端在 n_mid，必须回流（b[n_mid] -= e1/r1）。
    """
    nodes = ["n_mid", "n_c1", "n_bus_hi", "n_out"]
    idx = {n: i for i, n in enumerate(nodes)}
    g = np.zeros((4, 4))
    b = np.zeros(4)

    def stamp_r(n1, n2, r):
        gr = 1.0 / r
        for a in (n1, n2):
            if a != "gnd":
                g[idx[a], idx[a]] += gr
        if n1 != "gnd" and n2 != "gnd":
            g[idx[n1], idx[n2]] -= gr
            g[idx[n2], idx[n1]] -= gr

    (e1, r1), (e2, r2) = cells
    stamp_r("gnd", "n_mid", r2)
    b[idx["n_mid"]] += e2 / r2
    stamp_r("n_mid", "n_c1", r1)
    b[idx["n_c1"]] += e1 / r1
    b[idx["n_mid"]] -= e1 / r1  # Norton 源回流
    stamp_r("n_c1", "n_bus_hi", r_link)
    stamp_r("n_bus_hi", "n_out", r_bus + r_term)
    b[idx["n_out"]] = -i_load
    v = np.linalg.solve(g, b)
    vd = dict(zip(nodes, v, strict=True))
    i_branch = (vd["n_bus_hi"] - vd["n_out"]) / (r_bus + r_term)
    return vd, i_branch


def kcl_residuals_2p1s(vd, cells, r_link, r_bus, r_term, i_load):
    (e1, r1), (e2, r2) = cells
    i_r1 = (vd["n_b1"] - e1) / r1
    i_r2 = (vd["n_b2"] - e2) / r2
    i_link1 = (vd["n_b1"] - vd["n_bus_hi"]) / r_link
    i_link2 = (vd["n_b2"] - vd["n_bus_hi"]) / r_link
    i_bus = (vd["n_bus_hi"] - vd["n_bus_mid"]) / r_bus
    i_term = (vd["n_bus_mid"] - vd["n_out"]) / r_term
    return {
        "n_b1": i_r1 + i_link1,
        "n_b2": i_r2 + i_link2,
        "n_bus_hi": -i_link1 - i_link2 + i_bus,
        "n_bus_mid": -i_bus + i_term,
        "n_out": i_term - i_load,
    }


def main():
    # 不对称电芯：cell2 更弱（更低 OCV、更高内阻）→ 分流更少、端电压更低
    cells = [(4.0, 0.05), (3.9, 0.06)]
    r_link, r_bus, r_term = 0.01, 0.02, 0.01
    i_load = 2.0

    result = {
        "source_id": "OS03",
        "benchmark": "S3 轻量电路：可手算 2p1s / 1p2s 电阻网络（不依赖 liionpack）",
        "python": platform.python_version(),
        "cells": [{"E": e, "r": r} for e, r in cells],
        "r_link": r_link, "r_bus": r_bus, "r_term": r_term,
    }

    # ---- 求解器自检：对称特例对手算 ----
    sym, _ = solve_2p1s([(4.0, 0.05)] * 2, r_link, r_bus, r_term, 2.0)
    hand = 4.0 - 1.0 * 0.05 - 1.0 * r_link - 2.0 * r_bus - 2.0 * r_term
    solver_self_check = bool(abs(sym["n_out"] - hand) < 1e-12)

    vd, i_branch = solve_2p1s(cells, r_link, r_bus, r_term, i_load)
    kcl = kcl_residuals_2p1s(vd, cells, r_link, r_bus, r_term, i_load)
    v_cell = [vd["n_b1"], vd["n_b2"]]  # 电芯负端共地，节点电压即端电压
    # KVL 外环：E1 − I1(r1+r_link) − I_load(r_bus+r_term) − V_out = 0（I_bus=I_term=I_load）
    kvl_loop = (cells[0][0] - i_branch[0] * cells[0][1] - i_branch[0] * r_link
                - i_load * r_bus - i_load * r_term - vd["n_out"])
    weakest = int(np.argmin(v_cell))
    result["topology_2p1s"] = {
        "solver_self_check_vs_hand": solver_self_check,
        "hand_V_out_symmetric": hand,
        "node_voltages": {k: round(float(x), 9) for k, x in vd.items()},
        "branch_currents": [float(x) for x in i_branch],
        "branch_sum_equals_load": bool(abs(sum(i_branch) - i_load) < 1e-9),
        "weaker_branch_carries_less": bool(i_branch[1] < i_branch[0]),
        "kcl_residual_max": max(abs(x) for x in kcl.values()),
        "kcl_pass": bool(max(abs(x) for x in kcl.values()) < 1e-9),
        "kvl_residual": float(kvl_loop),
        "kvl_pass": bool(abs(kvl_loop) < 1e-9),
        "cell_terminal_V": [float(x) for x in v_cell],
        "weakest_cell_index": weakest,
        "weakest_is_cell2": bool(weakest == 1),
    }

    # ---- 首次约束事件：扫描负载电流，最弱单节端电压首次触 V_MIN ----
    thresholds = []
    for k in (1, 2):
        lo, hi = 0.0, 60.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            vdm, _ = solve_2p1s(cells, r_link, r_bus, r_term, mid)
            if vdm[f"n_b{k}"] > V_MIN:
                lo = mid
            else:
                hi = mid
        thresholds.append(0.5 * (lo + hi))
    first_event_cell = int(np.argmin(thresholds))
    result["first_constraint_event"] = {
        "v_min": V_MIN,
        "i_threshold_per_cell": thresholds,
        "first_event_cell": first_event_cell,
        "first_is_weakest_cell": bool(first_event_cell == weakest),
        "pass": bool(first_event_cell == weakest and abs(thresholds[0] - thresholds[1]) > 0.5),
    }

    # ---- 1p2s：串联支路电流处处相等；手算 V_out = E1+E2 − I·ΣR ----
    vd2, ib2 = solve_1p2s(cells, r_link, r_bus, r_term, i_load)
    r_tot = cells[0][1] + cells[1][1] + r_link + r_bus + r_term
    hand2 = cells[0][0] + cells[1][0] - i_load * r_tot
    result["topology_1p2s"] = {
        "node_voltages": {k: round(float(x), 9) for k, x in vd2.items()},
        "branch_current": float(ib2),
        "series_current_equals_load": bool(abs(ib2 - i_load) < 1e-9),
        "terminal_voltage_matches_hand": bool(abs(vd2["n_out"] - hand2) < 1e-9),
        "hand_V_out": hand2,
        "kvl_pass": bool(abs(vd2["n_mid"] - (cells[1][0] - ib2 * cells[1][1])) < 1e-9),
    }

    t = result["topology_2p1s"]
    result["all_pass"] = bool(
        t["solver_self_check_vs_hand"] and t["kcl_pass"] and t["kvl_pass"]
        and t["branch_sum_equals_load"] and t["weaker_branch_carries_less"] and t["weakest_is_cell2"]
        and result["first_constraint_event"]["pass"]
        and result["topology_1p2s"]["series_current_equals_load"]
        and result["topology_1p2s"]["terminal_voltage_matches_hand"]
        and result["topology_1p2s"]["kvl_pass"]
    )
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in
                      ["all_pass", "topology_2p1s", "first_constraint_event", "topology_1p2s"]},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
