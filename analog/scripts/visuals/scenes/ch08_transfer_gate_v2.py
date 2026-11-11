#!/usr/bin/env python3
"""§8.1 传输门动画：单管缺口 → 互补并联 → 双向。"""
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

RED, BLUE, GREEN, AMBER = "#a8321f", "#1f5d7a", "#3d6b4a", "#a4630f"
RED_T, BLUE_T, GREEN_T, AMBER_T = "#f6e7e1", "#e6eff3", "#e8efe6", "#f7eedb"
INK, MUTED, RULE = "#16202b", "#5b666f", "#c9bb9d"


def scene():
    tl = Timeline(
        width=960, height=660, duration=8.0,
        beats=(
            Beat("零水位", 0.0, 1.6, "VIN=0V：N 管 20Ω，P 管未导通", BLUE),
            Beat("顶到4V", 1.6, 3.4, "单 N 在 4V 截止；互补的 P 管接管高段", AMBER),
            Beat("互补并联", 3.4, 5.6, "P 管接管高段，包络 20→26.7→20Ω 覆盖全摆幅", GREEN),
            Beat("双向与边界", 5.6, 8.0, "单 N 的 4V 看下游门限；互补并联覆盖 0~5V，且可双向", RED, hold=True),
        ),
        title="传输门：谁行谁上",
        subtitle="R_ON–VIN：同一阈值模型、同一坐标；1~4V 为并联平台",
    )
    left, right, top, bottom, resistance_limit = 104, 620, 160, 470, 80

    def px(voltage):
        return left + voltage / 5 * (right - left)

    def ry(resistance):
        return bottom - resistance / resistance_limit * (bottom - top)

    def rn(voltage):
        return 80 / (4 - voltage) if voltage < 4 else None

    def rp(voltage):
        return 80 / (voltage - 1) if voltage > 1 else None

    def parallel(voltage):
        # 截止管电导为零，不以任意大电阻代替；1~4V 两管电导和恒为 3/80。
        conductance = (max(4 - voltage, 0) + max(voltage - 1, 0)) / 80
        return 1 / conductance

    def curve(model, colour, width, dash=''):
        points = []
        for step in range(101):
            voltage = step / 20
            resistance = model(voltage)
            if resistance is not None and resistance <= resistance_limit:
                points.append(f'{px(voltage):.2f},{ry(resistance):.2f}')
        style = f' stroke-dasharray="{dash}"' if dash else ''
        return (f'<polyline points="{" ".join(points)}" fill="none" '
                f'stroke="{colour}" stroke-width="{width}"{style}/>')

    n_curve = curve(rn, BLUE, 2.4)
    p_curve = curve(rp, AMBER, 2.4, '7,5')
    parallel_curve = curve(parallel, GREEN, 3.6)
    axes = [
        f'<rect x="48" y="92" width="864" height="440" rx="14" fill="#f6eedb" stroke="{RULE}" stroke-width="1.4"/>',
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="{RULE}" stroke-width="2"/>',
        f'<line x1="{left}" y1="{bottom}" x2="{left}" y2="{top}" stroke="{RULE}" stroke-width="2"/>',
        f'<text x="88" y="144" text-anchor="end" font-size="12" fill="{MUTED}">R_ON</text>',
        f'<text x="{left}" y="500" text-anchor="middle" font-size="12" fill="{MUTED}">0V</text>',
        f'<text x="{px(1):.2f}" y="500" text-anchor="middle" font-size="11" fill="{MUTED}">1V</text>',
        f'<text x="{right}" y="500" text-anchor="middle" font-size="12" fill="{MUTED}">5V</text>',
        f'<line x1="{px(4):.2f}" y1="{top}" x2="{px(4):.2f}" y2="500" stroke="{AMBER}" stroke-width="1.4" stroke-dasharray="5,4"/>',
        f'<text x="{px(4):.2f}" y="522" text-anchor="middle" font-size="11" fill="{AMBER}">4V</text>',
        f'<line x1="{px(2.5):.2f}" y1="{top}" x2="{px(2.5):.2f}" y2="500" stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="3,5"/>',
        f'<text x="{px(2.5):.2f}" y="522" text-anchor="middle" font-size="11" fill="{MUTED}">2.5V 门限</text>',
        f'<rect x="48" y="544" width="864" height="48" rx="10" fill="{BLUE_T}" stroke="{BLUE}" stroke-width="1.2"/>',
        f'<text x="72" y="575" font-size="12.5" fill="{INK}">教学模型：VDD=5V，VTH=1V，R0=80Ω·V；超出纵轴的曲线段省略，不含体效应。</text>',
    ]
    for resistance, label in ((0, '0Ω'), (20, '20Ω'), (80 / 3, '26.7Ω'), (80, '80Ω')):
        y = ry(resistance)
        if resistance:
            axes.append(f'<line x1="{left}" y1="{y:.2f}" x2="{right}" y2="{y:.2f}" '
                        f'stroke="{RULE}" stroke-width="1" stroke-dasharray="4,4"/>')
        axes.append(f'<text x="88" y="{y + 4:.2f}" text-anchor="end" '
                    f'font-size="11" fill="{MUTED}">{label}</text>')

    legend = '\n'.join((
        f'<text x="120" y="126" font-size="12" fill="{BLUE}">N 管：实线</text>',
        f'<text x="284" y="126" font-size="12" fill="{AMBER}">P 管：虚线</text>',
        f'<text x="452" y="126" font-size="12" font-weight="bold" fill="{GREEN}">并联：粗线</text>',
    ))
    envelope = '\n'.join((
        legend, n_curve, p_curve, parallel_curve,
        f'<text x="{px(2.5):.2f}" y="342" text-anchor="middle" font-size="13" '
        f'font-weight="bold" fill="{GREEN}">并联平台 26.7Ω</text>',
    ))
    layers = [
        Layer(None, '\n'.join(axes)),
        Layer("零水位", '\n'.join((
            n_curve,
            f'<circle cx="{px(0):.2f}" cy="{ry(20):.2f}" r="6" fill="{BLUE}"/>',
            f'<text x="680" y="176" font-size="14" font-weight="bold" fill="{BLUE}">VIN=0V</text>',
            f'<text x="680" y="210" font-size="13" fill="{BLUE}">N 管：20Ω</text>',
            f'<text x="680" y="242" font-size="12" fill="{MUTED}">P 管未导通</text>',
        ))),
        Layer("顶到4V", '\n'.join((
            n_curve,
            f'<text x="680" y="176" font-size="14" font-weight="bold" fill="{AMBER}">单 N 的阈值缺口</text>',
            f'<text x="680" y="210" font-size="12" fill="{INK}">VDD − VTH = 4V</text>',
            f'<text x="680" y="242" font-size="12" fill="{AMBER}">接近 4V：R_ON→∞</text>',
            f'<text x="680" y="274" font-size="12" fill="{INK}">高段交给 P 管</text>',
        ))),
        Layer("互补并联", '\n'.join((
            envelope,
            f'<text x="680" y="176" font-size="14" font-weight="bold" fill="{GREEN}">互补接力</text>',
            f'<text x="680" y="210" font-size="12" fill="{INK}">0V / 5V：20Ω</text>',
            f'<text x="680" y="242" font-size="12" fill="{GREEN}">1~4V：26.7Ω</text>',
            f'<text x="680" y="306" font-size="12" fill="{INK}">实际选型按手册峰值</text>',
        ))),
        Layer("双向与边界", '\n'.join((
            envelope,
            f'<rect x="660" y="108" width="244" height="208" rx="10" fill="{RED_T}" stroke="{RED}" stroke-width="1.6"/>',
            f'<text x="680" y="138" font-size="13" font-weight="bold" fill="{RED}">单 N 的 4V 够不够？</text>',
            f'<text x="680" y="172" font-size="12" fill="{INK}">CMOS 门限 2.5V：够用</text>',
            f'<text x="680" y="202" font-size="12" fill="{INK}">轨到轨 ADC：不够</text>',
            f'<text x="680" y="264" font-size="12" font-weight="bold" fill="{RED}">这不是并联传输门上限</text>',
            f'<rect x="660" y="332" width="244" height="160" rx="10" fill="{GREEN_T}" stroke="{GREEN}" stroke-width="1.6"/>',
            f'<text x="680" y="362" font-size="13" font-weight="bold" fill="{GREEN}">并联覆盖 0~5V</text>',
            f'<text x="680" y="394" font-size="12" fill="{INK}">包络 20→26.7→20Ω</text>',
            f'<path d="M708,430 L852,430 M708,430 L720,422 M708,430 L720,438 M852,430 L840,422 M852,430 L840,438" '
            f'stroke="{RED}" stroke-width="2.4" fill="none"/>',
            f'<text x="780" y="466" text-anchor="middle" font-size="12" fill="{RED}">源漏对称：双向</text>',
        ))),
    ]
    return tl, layers


if __name__ == "__main__":
    tl, layers = scene()
    write(tl, layers, SCRIPTS.parent / "assets" / "svg-v2", "ch08-transfer-gate-v2")
