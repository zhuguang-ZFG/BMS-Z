#!/usr/bin/env python3
"""§8.4 采样保持：采样、保持、下垂、再采样四拍。"""
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
        width=960, height=620, duration=9.0,
        beats=(
            Beat("采样", 0.0, 2.0, "开关闭合：Chold 追踪 2.000V 输入", BLUE),
            Beat("保持", 2.0, 4.0, "开关断开：电容记住最后一刻的电压", GREEN),
            Beat("下垂", 4.0, 6.4, "漏流与偏流让保持电压按 I/C 缓慢下斜", AMBER),
            Beat("再采样", 6.4, 9.0, "下一周期重新闭合；droop、注入、kT/C 都记在同一个电容上", RED, hold=True),
        ),
        title="采样保持：四拍与一个电容",
        subtitle="采样相看建立，保持相看 droop；加大电容压误差也拉长时间",
    )
    persistent = "\n".join((
        f'<rect x="48" y="96" width="864" height="360" rx="14" fill="#f6eedb" stroke="{RULE}" stroke-width="1.4"/>',
        f'<text x="76" y="128" font-size="12" fill="{MUTED}">保持节点电压</text>',
        f'<line x1="110" y1="400" x2="864" y2="400" stroke="{RULE}" stroke-width="2"/>',
        f'<line x1="110" y1="400" x2="110" y2="150" stroke="{RULE}" stroke-width="2"/>',
        f'<text x="110" y="430" font-size="11" fill="{MUTED}">0</text>',
        f'<text x="470" y="430" text-anchor="middle" font-size="11" fill="{MUTED}">一个采样周期</text>',
        f'<text x="864" y="430" text-anchor="end" font-size="11" fill="{MUTED}">t</text>',
        f'<text x="80" y="180" font-size="11" fill="{MUTED}">2.000V</text>',
        f'<line x1="110" y1="180" x2="864" y2="180" stroke="{GREEN}" stroke-width="1.2" stroke-dasharray="5,5"/>',
    ))
    rise = f'<path d="M110,400 C180,400 220,300 300,240 C360,200 430,184 520,180" fill="none" stroke="{BLUE}" stroke-width="3.4"/>'
    hold = f'<path d="M520,180 L700,180" fill="none" stroke="{GREEN}" stroke-width="3.4"/>'
    droop = f'<path d="M700,180 L864,220" fill="none" stroke="{AMBER}" stroke-width="3.4"/>'

    def trace(*segments):
        # 波形必须累积：每拍只画自己那一段，结论帧就只剩空坐标轴。
        return "\n".join(segments)

    layers = [
        Layer(None, persistent),
        Layer("采样", "\n".join((
            trace(rise),
            f'<text x="310" y="250" font-size="12.5" font-weight="bold" fill="{BLUE}">8.3τ 后到 12 位</text>',
        )), (0, -4)),
        Layer("保持", "\n".join((
            trace(rise, hold),
            f'<line x1="520" y1="160" x2="520" y2="210" stroke="{GREEN}" stroke-width="2"/>',
            f'<text x="540" y="160" font-size="12" fill="{GREEN}">断开：冻结</text>',
        )), (0, -4)),
        Layer("下垂", "\n".join((
            trace(rise, hold, droop),
            f'<text x="730" y="246" font-size="12" fill="{AMBER}">droop = I/C</text>',
        )), (0, -4)),
        Layer("再采样", "\n".join((
            trace(rise, hold, droop),
            f'<line x1="864" y1="150" x2="864" y2="400" stroke="{RED}" stroke-width="1.6" stroke-dasharray="4,4"/>',
            f'<rect x="96" y="474" width="816" height="94" rx="10" fill="{RED_T}" stroke="{RED}" stroke-width="1.6"/>',
            f'<text x="120" y="506" font-size="13" font-weight="bold" fill="{RED}">一个电容，三笔账</text>',
            f'<text x="120" y="534" font-size="12.5" fill="{INK}">加大 Chold：摊注入、压 kT/C、缓 droop；代价是采集时间线性变长。</text>',
            f'<text x="120" y="556" font-size="12" fill="{MUTED}">16 位预算里，三笔判据同时收紧 16 倍。</text>',
        )), (0, -4)),
    ]
    return tl, layers


if __name__ == "__main__":
    tl, layers = scene()
    write(tl, layers, SCRIPTS.parent / "assets" / "svg-v2", "ch08-sample-hold-v2")
