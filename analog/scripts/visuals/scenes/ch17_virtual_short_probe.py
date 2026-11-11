#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§17.2 虚短探针动画（A5 操作演示）：先量 V- → 再量 V+ → 压差 8mV → 判读。

数字回对正文：8mV。
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(SCRIPTS.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPTS.parent))

from scripts.visuals.render import Layer, write  # noqa: E402
from scripts.visuals.timeline import Beat, Timeline  # noqa: E402

RED, BLUE, AMBER, GREEN = "#a8321f", "#1f5d7a", "#a4630f", "#3d6b4a"
RED_T, BLUE_T, GREEN_T, AMBER_T = "#f6e7e1", "#e6eff3", "#e8efe6", "#f7eedb"
INK, INK2, MUTED, RULE = "#16202b", "#37424e", "#5b666f", "#c9bb9d"


def scene():
    tl = Timeline(
        width=960, height=860, duration=7.5,
        beats=(
            Beat("认脚", 0.0, 1.5, "先沿原理图核对负反馈，再量输入端与输出工况", BLUE),
            Beat("量V-", 1.5, 3.0, "同一静态工况：表笔落 V-，读数 2.500V", BLUE),
            Beat("量V+", 3.0, 4.5, "保持工况不变：表笔落 V+，读数 2.508V", RED),
            Beat("算压差", 4.5, 6.0, "2.508 − 2.500 = 8mV：先记读数，不急着判合格", AMBER),
            Beat("判读", 6.0, 7.5, "小压差只是线索；核前提、算误差、再看输出响应", AMBER, hold=True),
        ),
        title="虚短探针：沿反馈回路核对读数",
        subtitle="两输入相差 8mV，还要核前提、算误差、看输出",
    )
    persistent = "\n".join((
        f'<rect x="56" y="92" width="564" height="410" rx="12" fill="#f6eedb" stroke="{RULE}" stroke-width="1.6"/>',
        f'<text x="80" y="126" font-size="22" fill="{INK2}">反相级：按原理图核对</text>',
        f'<polygon points="320,245 320,365 490,305" fill="#fdf8ea" stroke="{INK2}" stroke-width="2.4"/>',
        f'<line x1="80" y1="275" x2="150" y2="275" stroke="{INK}" stroke-width="2.4"/>',
        f'<rect x="150" y="259" width="70" height="32" fill="#fdf8ea" stroke="{INK}" stroke-width="2"/>',
        f'<line x1="220" y1="275" x2="320" y2="275" stroke="{INK}" stroke-width="2.4"/>',
        f'<text x="80" y="244" font-size="22" fill="{INK2}">信号</text>',
        f'<text x="160" y="320" font-size="22" fill="{INK2}">Rin</text>',
        f'<line x1="80" y1="335" x2="320" y2="335" stroke="{INK}" stroke-width="2.4"/>',
        f'<text x="80" y="372" font-size="22" fill="{INK2}">参考点</text>',
        f'<text x="335" y="282" font-size="22" font-weight="bold" fill="{INK}">−</text>',
        f'<text x="335" y="344" font-size="22" font-weight="bold" fill="{INK}">+</text>',
        f'<text x="382" y="312" font-size="22" fill="{MUTED}">运放</text>',
        f'<text x="246" y="306" font-size="22" fill="{BLUE}">V−</text>',
        f'<text x="270" y="372" font-size="22" fill="{RED}">V+</text>',
        f'<line x1="490" y1="305" x2="592" y2="305" stroke="{INK}" stroke-width="2.4"/>',
        f'<text x="510" y="340" font-size="22" fill="{INK2}">Vout</text>',
        # 反馈支路必须从输出节点经 Rf 回到反相端，不能碰到同相端。
        f'<polyline points="562,305 562,180 460,180" fill="none" stroke="{GREEN}" stroke-width="2.6"/>',
        f'<rect data-component="Rf" x="390" y="164" width="70" height="32" fill="#fdf8ea" stroke="{GREEN}" stroke-width="2.2"/>',
        f'<polyline points="390,180 270,180 270,275" fill="none" stroke="{GREEN}" stroke-width="2.6"/>',
        f'<circle cx="562" cy="305" r="4" fill="{GREEN}"/>',
        f'<circle cx="270" cy="275" r="4" fill="{GREEN}"/>',
        f'<text x="350" y="224" font-size="22" fill="{GREEN}">Rf：先核通断</text>',
        f'<text x="80" y="438" font-size="22" fill="{INK}">回路按原理图示意，通断尚需核对。</text>',
        f'<text x="80" y="476" font-size="22" fill="{INK}">先量供电、输出，再读输入压差。</text>',
        f'<rect x="644" y="92" width="280" height="190" rx="12" fill="#f6eedb" stroke="{RULE}" stroke-width="1.6"/>',
        f'<text x="666" y="126" font-size="22" font-weight="bold" fill="{INK2}">万用表：同一工况</text>',
    ))

    def readings(v_minus, v_plus, color_minus=MUTED, color_plus=MUTED):
        return "\n".join((
            f'<text x="666" y="172" font-size="24" font-weight="bold" fill="{color_minus}">V−：{v_minus}</text>',
            f'<text x="666" y="220" font-size="24" font-weight="bold" fill="{color_plus}">V+：{v_plus}</text>',
        ))

    gap_box = "\n".join((
        f'<rect x="644" y="304" width="280" height="158" rx="12" fill="{AMBER_T}" stroke="{AMBER}" stroke-width="1.8"/>',
        f'<text x="666" y="338" font-size="22" fill="{AMBER}">两次读数相减</text>',
        f'<text x="666" y="376" font-size="22" fill="{INK}">2.508 − 2.500</text>',
        f'<text x="666" y="422" font-size="26" font-weight="bold" fill="{AMBER}">= 8mV（读数）</text>',
    ))
    complete_readings = readings("2.500V", "2.508V", BLUE, RED)
    verdict = "\n".join((
        f'<rect x="56" y="530" width="868" height="250" rx="12" fill="{AMBER_T}" stroke="{AMBER}" stroke-width="2"/>',
        f'<text x="80" y="568" font-size="26" font-weight="bold" fill="{AMBER}">8mV 是线索，不是通用合格线</text>',
        f'<text x="80" y="610" font-size="22" fill="{INK}">先核供电、共模与输出摆幅；负反馈是否闭合？</text>',
        f'<text x="80" y="648" font-size="22" fill="{INK}">再按失调、开环增益和仪器误差估算应有压差。</text>',
        f'<text x="80" y="686" font-size="22" fill="{INK}">最后看小信号能否沿反馈规律传到输出。</text>',
        f'<text x="80" y="738" font-size="22" font-weight="bold" fill="{RED}">输入接近，不等于增益正确，也不能排除振荡。</text>',
    ))
    layers = [
        Layer(None, persistent),
        Layer("认脚", readings("—", "—")),
        Layer("量V-", "\n".join((
            f'<circle cx="300" cy="275" r="9" fill="{BLUE_T}" stroke="{BLUE}" stroke-width="2"/>',
            readings("2.500V", "—", BLUE),
        ))),
        Layer("量V+", "\n".join((
            f'<circle cx="300" cy="335" r="9" fill="{RED_T}" stroke="{RED}" stroke-width="2"/>',
            complete_readings,
        ))),
        Layer("算压差", "\n".join((complete_readings, gap_box))),
        Layer("判读", "\n".join((complete_readings, gap_box, verdict))),
    ]
    return tl, layers




if __name__ == "__main__":
    tl, layers = scene()
    write(tl, layers, SCRIPTS.parent / "assets" / "svg-v2", "ch17-virtual-short-probe")
