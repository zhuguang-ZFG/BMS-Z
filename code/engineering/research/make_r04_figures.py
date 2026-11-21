#!/usr/bin/env python3
"""Generate R04 figure: the safety correction-contract gate + fail-closed evaluation.

Static teaching diagram (no numeric inputs): safety claim -> correction
contract gate S1-S6 -> per-check evaluation; the conflated-recovery lane
(clear/reset/re-permission identical) drawn in red.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / "bms-book" / "engineering" / "assets" / "r04-safety"

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
    w, h = 920, 520
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" font-family="sans-serif">',
        "<title>安全纠偏合同门与 fail-closed 评估</title>",
        "<desc>安全处理宣称先过纠偏合同门 S1-S6；清旗/复位/重新许可混淆走红色通道，反馈身份不符或缺测即 fail。</desc>",
        '<defs><marker id="head" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#003153"/></marker>'
        '<marker id="headr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#a3322a"/></marker></defs>',
        STYLE,
        f'<rect class="bg" x="0" y="0" width="{w}" height="{h}"/>',
        '<text class="title" x="50" y="40">安全架构：纠偏合同 + fail-closed 评估</text>',
        '<text class="sub" x="50" y="64">命令/反馈身份进合同；清旗、复位、重新许可是三个动作，不是一个动作穿三件外套。</text>',
        # claim box
        '<rect class="box" x="50" y="120" width="190" height="72" rx="8"/>',
        '<text class="name" x="66" y="150">安全处理宣称</text>',
        '<text class="item" x="66" y="174">故障 F 已被处理</text>',
        '<path class="arrow" d="M244,156 L306,156"/>',
        # gate
        '<rect class="gate" x="310" y="86" width="330" height="150" rx="8"/>',
        '<text class="red" x="326" y="112">纠偏合同校验门 S1–S6</text>',
        '<text class="item" x="326" y="136">S1 清旗/复位/重新许可不得同效 · S2 三动作必填</text>',
        '<text class="item" x="326" y="158">S3 反应命令带身份 · S4 反馈带来源信号</text>',
        '<text class="item" x="326" y="180">S5 去抖配置非负整数毫秒</text>',
        '<text class="item" x="326" y="202">S6 每个声明迁移有显式测试映射</text>',
        '<text class="item" x="326" y="224">（OS07：registry/SPS/反馈/DIAG 全链追踪）</text>',
        '<path class="arrow" d="M644,156 L706,156"/>',
        # evaluation
        '<rect class="box" x="710" y="86" width="170" height="150" rx="8"/>',
        '<text class="name" x="726" y="112">评估器</text>',
        '<text class="item" x="726" y="136">反馈回读与身份一致</text>',
        '<text class="item" x="726" y="158">声明迁移全被测试覆盖</text>',
        '<text class="red" x="726" y="184">逐项 fail-closed</text>',
        # conflated recovery lane
        '<path class="fail" d="M475,240 C475,340 380,350 230,320"/>',
        '<text class="red" x="270" y="380">清旗=复位=重新许可 → 混淆通道：这不是恢复，是复读</text>',
        # verdict lane
        '<path class="arrow" d="M795,240 C795,390 430,390 240,330"/>',
        '<rect class="box" x="50" y="310" width="190" height="60" rx="8"/>',
        '<text class="name" x="66" y="336">verdict</text>',
        '<text class="item" x="66" y="358">pass 只证合同内身份与覆盖</text>',
        '<text class="foot" x="50" y="480">边界：pass 不构成功能安全等级结论；OS07 未闭合前所有安全宣称保持教学/待验身份。</text>',
        "</svg>",
    ]
    return "\n".join(parts) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "R04-F1-correction-gate.svg"
    target.write_text(build_svg(), encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
