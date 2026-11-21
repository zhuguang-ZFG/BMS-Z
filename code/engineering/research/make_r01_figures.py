#!/usr/bin/env python3
"""Generate R01 figure: the five-element comparison gate + fail-closed evaluation.

Static teaching diagram (no numeric inputs): claim -> spec gate (P1-P5) ->
per-check evaluation -> verdict, with the silence-is-not-a-pass lane visible.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / "bms-book" / "engineering" / "assets" / "r01-model"

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
    w, h = 900, 480
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" font-family="sans-serif">',
        "<title>模型对比五要素门与 fail-closed 评估</title>",
        "<desc>宣称先过五要素校验门（P1-P5），再进按检查项 fail-closed 的评估器；观测缺事件用例走红色失败通道——沉默不是通过。</desc>",
        '<defs><marker id="head" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#003153"/></marker>'
        '<marker id="headr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#a3322a"/></marker></defs>',
        STYLE,
        f'<rect class="bg" x="0" y="0" width="{w}" height="{h}"/>',
        '<text class="title" x="50" y="40">模型对比：五要素门 + fail-closed 评估</text>',
        '<text class="sub" x="50" y="64">"模型与参考一致"必须带齐五要素；评估按检查项失败即失败，沉默不是通过。</text>',
        # claim box
        '<rect class="box" x="50" y="110" width="180" height="72" rx="8"/>',
        '<text class="name" x="66" y="140">对比宣称</text>',
        '<text class="item" x="66" y="164">模型 X 与参考 Y 一致</text>',
        '<path class="arrow" d="M234,146 L296,146"/>',
        # gate
        '<rect class="gate" x="300" y="86" width="300" height="120" rx="8"/>',
        '<text class="red" x="316" y="112">五要素校验门 P1–P5</text>',
        '<text class="item" x="316" y="136">P1 冻结版本 · P2 正容差 v_rel/q_abs</text>',
        '<text class="item" x="316" y="158">P3 参考限 analytic / independent_impl</text>',
        '<text class="item" x="316" y="180">P4 事件三件套 endpoint/discontinuity/both_sides</text>',
        '<text class="item" x="316" y="200">P5 reproduces_mwe ∈ yes/no/unknown</text>',
        '<path class="arrow" d="M604,146 L666,146"/>',
        # evaluation
        '<rect class="box" x="670" y="86" width="190" height="120" rx="8"/>',
        '<text class="name" x="686" y="112">评估器</text>',
        '<text class="item" x="686" y="136">v_rel · q_abs · 能量积分</text>',
        '<text class="item" x="686" y="158">每个声明事件用例</text>',
        '<text class="red" x="686" y="184">逐项 fail-closed</text>',
        # fail lane
        '<path class="fail" d="M765,210 C765,300 500,300 320,250"/>',
        '<text class="red" x="470" y="300">观测缺事件用例 / 超容差 → 走失败通道</text>',
        # verdict lane
        '<path class="arrow" d="M765,210 C765,330 400,330 210,250"/>',
        '<rect class="box" x="50" y="230" width="180" height="60" rx="8"/>',
        '<text class="name" x="66" y="256">verdict</text>',
        '<text class="item" x="66" y="278">pass 只证此容差下一致</text>',
        '<text class="foot" x="50" y="440">边界：pass 不证明模型在声明域外成立；OS01/CASE01 未复现前 reproduces_mwe 不许写 yes。</text>',
        "</svg>",
    ]
    return "\n".join(parts) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "R01-F1-protocol-gate.svg"
    target.write_text(build_svg(), encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
