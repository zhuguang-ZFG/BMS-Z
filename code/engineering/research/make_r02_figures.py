#!/usr/bin/env python3
"""Generate R02 figure: the joint-estimation contract gate + fail-closed evaluation.

Static teaching diagram (no numeric inputs): estimation claim -> contract
gate C1-C6 -> per-check evaluation on the held-out window, with the leakage
lane (fit/validation overlap) drawn in red.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / "bms-book" / "engineering" / "assets" / "r02-estimation"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .box { fill: #fbf8f1; stroke: #003153; stroke-width: 1.8; }
  .gate { fill: #fbf8f1; stroke: #a3322a; stroke-width: 1.8; }
  .name { fill: #003153; font: 700 15px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .red { fill: #a3322a; font: 700 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .item { fill: #4d5d63; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .arrow { stroke: #003153; stroke-width: 1.8; fill: none; marker-end: url(#head); }
  .fail { stroke: #a3322a; stroke-width: 1.8; fill: none; stroke-dasharray: 6 4; marker-end: url(#headr); }
  .foot { fill: #5c6d73; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
</style>"""


def build_svg() -> str:
    w, h = 900, 500
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" font-family="sans-serif">',
        "<title>联合估计不确定性合同门与 fail-closed 评估</title>",
        "<desc>估计宣称先过合同校验门 C1-C6，再进留出验证窗的逐项评估；拟合/验证重叠走红色泄漏通道。</desc>",
        '<defs><marker id="head" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#003153"/></marker>'
        '<marker id="headr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#a3322a"/></marker></defs>',
        STYLE,
        f'<rect class="bg" x="0" y="0" width="{w}" height="{h}"/>',
        '<text class="title" x="50" y="40">联合估计：不确定性合同 + 留出窗 fail-closed 评估</text>',
        '<text class="sub" x="50" y="64">点估计不配不确定度、拟合窗当验证窗、引用不给定位——都不是估计声称。</text>',
        # claim box
        '<rect class="box" x="50" y="120" width="180" height="72" rx="8"/>',
        '<text class="name" x="66" y="150">估计宣称</text>',
        '<text class="item" x="66" y="174">联合估计 SOC 与 RC 参数</text>',
        '<path class="arrow" d="M234,156 L296,156"/>',
        # contract gate
        '<rect class="gate" x="300" y="92" width="310" height="128" rx="8"/>',
        '<text class="red" x="316" y="118">合同校验门 C1–C6</text>',
        '<text class="item" x="316" y="140">C1 拟合窗∩验证窗=∅ · C2 验证窗必填</text>',
        '<text class="item" x="316" y="162">C3 每个估计带正 std</text>',
        '<text class="item" x="316" y="184">C4 假设列表非空 · C5 引用给定位</text>',
        '<text class="item" x="316" y="206">C6 外部库依赖只警告不放行基准</text>',
        '<path class="arrow" d="M614,156 L676,156"/>',
        # evaluation
        '<rect class="box" x="680" y="92" width="180" height="128" rx="8"/>',
        '<text class="name" x="696" y="118">评估器</text>',
        '<text class="item" x="696" y="142">留出窗最大残差</text>',
        '<text class="item" x="696" y="164">每个 std 在容差带内</text>',
        '<text class="red" x="696" y="190">逐项 fail-closed</text>',
        # leakage lane
        '<path class="fail" d="M455,224 C455,320 380,330 250,300"/>',
        '<text class="red" x="330" y="345">拟合/验证重叠 → 泄漏通道：这是拟合，不是估计</text>',
        # verdict lane
        '<path class="arrow" d="M770,224 C770,360 420,360 210,280"/>',
        '<rect class="box" x="50" y="260" width="180" height="60" rx="8"/>',
        '<text class="name" x="66" y="286">verdict</text>',
        '<text class="item" x="66" y="308">pass 只证留出窗内成立</text>',
        '<text class="foot" x="50" y="460">边界：pass 不证明参数在窗外观测条件下成立；OS02/EDU01 未复现前外部库与讲义内容保持访问状态标注。</text>',
        "</svg>",
    ]
    return "\n".join(parts) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "R02-F1-contract-gate.svg"
    target.write_text(build_svg(), encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
