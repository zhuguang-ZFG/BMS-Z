#!/usr/bin/env python3
"""§8.2 地址跳变：011→100 的路过通道与 INH 对策。"""
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

RED, BLUE, GREEN, AMBER, PURPLE = "#a8321f", "#1f5d7a", "#3d6b4a", "#a4630f", "#6b3f63"
RED_T, BLUE_T, GREEN_T, AMBER_T = "#f6e7e1", "#e6eff3", "#e8efe6", "#f7eedb"
INK, MUTED, RULE = "#16202b", "#5b666f", "#c9bb9d"


def scene():
    tl = Timeline(
        width=960, height=660, duration=9.0,
        beats=(
            Beat("停在011", 0.0, 1.6, "当前选中通道 3：地址 011 稳定", BLUE),
            Beat("三位抢跑", 1.6, 3.4, "改到 100 时三位不同时翻转，中间态先出现", AMBER),
            Beat("路过111", 3.4, 5.2, "未禁止时，111 可能短暂接通：无关信号被采进系统", RED),
            Beat("先拉INH", 5.2, 6.8, "先把 INH 拉高全断，地址变化期间不接通任何通道", GREEN),
            Beat("等够再采", 6.8, 9.0, "释放 INH 后等接通、再等信号建立，最后才采样", PURPLE, hold=True),
        ),
        title="地址跳变的路过通道",
        subtitle="011→100 可能路过 111；INH 高电平时全部通道断开",
    )
    persistent = "\n".join((
        f'<rect x="48" y="96" width="864" height="300" rx="14" fill="#f6eedb" stroke="{RULE}" stroke-width="1.4"/>',
        f'<text x="72" y="128" font-size="12" fill="{MUTED}">三位地址时间线</text>',
        f'<line x1="96" y1="230" x2="864" y2="230" stroke="{RULE}" stroke-width="1.6"/>',
        f'<line x1="96" y1="360" x2="864" y2="360" stroke="{RULE}" stroke-width="1.2"/>',
        f'<text x="72" y="386" font-size="12" fill="{MUTED}">选中通道</text>',
        f'<text x="72" y="430" font-size="12" fill="{MUTED}">INH</text>',
        f'<line x1="96" y1="446" x2="864" y2="446" stroke="{RULE}" stroke-width="1.2"/>',
        f'<text x="480" y="480" text-anchor="middle" font-size="12" fill="{MUTED}">时间（切换沿几十 ns 级）</text>',
    ))
    def address(x, value, colour, tint):
        return (f'<rect x="{x}" y="204" width="120" height="52" rx="8" '
                f'fill="{tint}" stroke="{colour}" stroke-width="2"/>'
                f'<text x="{x + 60}" y="238" text-anchor="middle" font-size="18" '
                f'font-weight="bold" fill="{colour}">{value}</text>')

    initial_address = address(120, '011', BLUE, BLUE_T)
    address_story = "\n".join((
        initial_address,
        address(340, '111', AMBER, AMBER_T),
        address(620, '100', BLUE, BLUE_T),
        f'<text x="120" y="284" font-size="12.5" fill="{INK}">原地址</text>',
        f'<text x="340" y="284" font-size="12.5" fill="{AMBER}">一种可能的中间态</text>',
        f'<text x="620" y="284" font-size="12.5" fill="{INK}">新地址稳定</text>',
    ))
    unsafe_selection = "\n".join((
        f'<rect x="340" y="310" width="120" height="34" rx="6" fill="{RED_T}" stroke="{RED}" stroke-width="2"/>',
        f'<text x="400" y="334" text-anchor="middle" font-size="12.5" font-weight="bold" fill="{RED}">通道 7 误接通</text>',
        f'<text x="480" y="334" font-size="12" fill="{RED}">未拉 INH：无关信号短促进入</text>',
    ))
    protected_selection = "\n".join((
        f'<rect x="120" y="310" width="180" height="34" rx="6" fill="{BLUE_T}" stroke="{BLUE}" stroke-width="1.6"/>',
        f'<text x="210" y="334" text-anchor="middle" font-size="12.5" fill="{BLUE}">通道 3</text>',
        f'<rect x="300" y="310" width="480" height="34" rx="6" fill="{GREEN_T}" stroke="{GREEN}" stroke-width="2"/>',
        f'<text x="540" y="334" text-anchor="middle" font-size="12.5" font-weight="bold" fill="{GREEN}">全断：不接通任何通道</text>',
        f'<rect x="780" y="310" width="120" height="34" rx="6" fill="{BLUE_T}" stroke="{BLUE}" stroke-width="1.6"/>',
        f'<text x="840" y="334" text-anchor="middle" font-size="11" fill="{BLUE}">通道 4：接通/建立</text>',
    ))
    inh_pulse = "\n".join((
        # 地址变化前拉高，最终地址稳定后才释放；高电平区与「全断」条带对齐。
        f'<path d="M120,440 L300,440 L300,404 L780,404 L780,440 L900,440" fill="none" stroke="{GREEN}" stroke-width="3"/>',
        f'<text x="320" y="394" font-size="12.5" font-weight="bold" fill="{GREEN}">先拉 INH，再改地址；稳定后释放</text>',
        f'<line x1="848" y1="352" x2="848" y2="454" stroke="{PURPLE}" stroke-width="1.6" stroke-dasharray="4,4"/>',
        f'<text x="814" y="368" text-anchor="end" font-size="12" fill="{PURPLE}">等 ≥ t_ON</text>',
        f'<text x="856" y="368" font-size="12" fill="{PURPLE}">采样</text>',
    ))
    protected_story = "\n".join((address_story, protected_selection, inh_pulse))
    layers = [
        Layer(None, persistent),
        Layer("停在011", "\n".join((
            initial_address,
            f'<text x="120" y="284" font-size="12.5" fill="{INK}">选中通道 3，稳定</text>',
        )), (0, -4)),
        Layer("三位抢跑", address_story, (0, -4)),
        Layer("路过111", "\n".join((address_story, unsafe_selection)), (0, -4)),
        Layer("先拉INH", protected_story, (0, -4)),
        Layer("等够再采", "\n".join((
            protected_story,
            f'<rect x="96" y="500" width="816" height="76" rx="10" fill="{GREEN_T}" stroke="{GREEN}" stroke-width="1.6"/>',
            f'<text x="120" y="530" font-size="13" font-weight="bold" fill="{GREEN}">INH 拉高 → 改地址 → 地址稳定 → 释放 INH → 等够再采</text>',
            f'<text x="120" y="556" font-size="12" fill="{INK}">至少等 t_ON 接通，另留信号建立时间；格雷码只减少地址中间态。</text>',
        )), (0, -4)),
    ]
    return tl, layers


if __name__ == "__main__":
    tl, layers = scene()
    write(tl, layers, SCRIPTS.parent / "assets" / "svg-v2", "ch08-mux-address-glitch-v2")
