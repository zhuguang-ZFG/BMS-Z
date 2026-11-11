#!/usr/bin/env python3
"""§8.6 电荷注入：Qch 分成两路，Ch=10pF 上落 10mV = 20 LSB。"""
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
        width=960, height=620, duration=8.0,
        beats=(
            Beat("导通蓄水", 0.0, 1.8, "EN 高：沟道里存下 Qch=0.2pC", BLUE),
            Beat("关断分账", 1.8, 3.8, "EN 拉低：一半电荷挤进 Chold，一半泄回源侧", AMBER),
            Beat("台阶10mV", 3.8, 5.8, "0.2pC 的一半落到 10pF：ΔV=10mV", RED),
            Beat("20个LSB", 5.8, 8.0, "2.048V/12 位、1LSB=500µV，10mV 就是 20 个 LSB", GREEN, hold=True),
        ),
        title="电荷注入：一包电荷的两个出口",
        subtitle="源侧阻抗决定分账；高阻直采按全额记账",
    )
    persistent = "\n".join((
        f'<rect x="48" y="96" width="864" height="330" rx="14" fill="#f6eedb" stroke="{RULE}" stroke-width="1.4"/>',
        f'<text x="76" y="128" font-size="12" fill="{MUTED}">传输门与保持电容</text>',
        f'<line x1="110" y1="250" x2="360" y2="250" stroke="{INK}" stroke-width="2.4"/>',
        f'<rect x="360" y="210" width="120" height="80" rx="10" fill="{BLUE_T}" stroke="{BLUE}" stroke-width="2"/>',
        f'<text x="420" y="250" text-anchor="middle" font-size="14" font-weight="bold" fill="{BLUE}">开关</text>',
        f'<text x="420" y="272" text-anchor="middle" font-size="11" fill="{MUTED}">EN 控制</text>',
        f'<line x1="480" y1="250" x2="720" y2="250" stroke="{INK}" stroke-width="2.4"/>',
        f'<line x1="720" y1="250" x2="720" y2="330" stroke="{INK}" stroke-width="2"/>',
        f'<line x1="680" y1="330" x2="760" y2="330" stroke="{INK}" stroke-width="3"/>',
        f'<line x1="680" y1="350" x2="760" y2="350" stroke="{INK}" stroke-width="3"/>',
        f'<text x="770" y="346" font-size="12" fill="{MUTED}">Chold=10pF</text>',
        f'<text x="110" y="230" font-size="12" fill="{MUTED}">源侧</text>',
    ))
    layers = [
        Layer(None, persistent),
        Layer("导通蓄水", "\n".join((
            f'<ellipse cx="420" cy="250" rx="34" ry="22" fill="{AMBER_T}" stroke="{AMBER}" stroke-width="2"/>',
            f'<text x="420" y="254" text-anchor="middle" font-size="11" font-weight="bold" fill="{AMBER}">Qch</text>',
            f'<text x="470" y="196" font-size="12.5" fill="{INK}">0.2pC 存在沟道里</text>',
        )), (0, -4)),
        Layer("关断分账", "\n".join((
            f'<path d="M420,250 C380,300 300,320 180,320" fill="none" stroke="{BLUE}" stroke-width="7" opacity=".75"/>',
            f'<path d="M420,250 C500,300 600,320 700,320" fill="none" stroke="{AMBER}" stroke-width="4" opacity=".85"/>',
            f'<text x="180" y="344" font-size="12" fill="{BLUE}">泄回源侧（低阻越多）</text>',
            f'<text x="560" y="344" font-size="12" fill="{AMBER}">挤进 Chold</text>',
        )), (0, -4)),
        Layer("台阶10mV", "\n".join((
            f'<rect x="96" y="446" width="400" height="120" rx="10" fill="{RED_T}" stroke="{RED}" stroke-width="1.6"/>',
            f'<text x="120" y="478" font-size="13" font-weight="bold" fill="{RED}">ΔV = Q / (2·Chold)</text>',
            f'<text x="120" y="508" font-size="12.5" fill="{INK}">0.2pC 的一半 ÷ 10pF</text>',
            f'<text x="120" y="540" font-size="16" font-weight="bold" fill="{RED}">= 10mV</text>',
        )), (0, -4)),
        Layer("20个LSB", "\n".join((
            f'<rect x="520" y="446" width="392" height="120" rx="10" fill="{GREEN_T}" stroke="{GREEN}" stroke-width="1.8"/>',
            f'<text x="544" y="478" font-size="13" font-weight="bold" fill="{GREEN}">2.048V / 12 位</text>',
            f'<text x="544" y="506" font-size="12.5" fill="{INK}">1LSB = 500µV</text>',
            f'<text x="544" y="540" font-size="16" font-weight="bold" fill="{GREEN}">10mV = 20 个 LSB</text>',
        )), (0, -4)),
    ]
    return tl, layers


if __name__ == "__main__":
    tl, layers = scene()
    write(tl, layers, SCRIPTS.parent / "assets" / "svg-v2", "ch08-charge-injection-v2")
