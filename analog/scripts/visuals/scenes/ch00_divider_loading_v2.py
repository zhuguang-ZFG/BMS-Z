#!/usr/bin/env python3
"""§0.3 分压器带载：空载 6V → 挂 10kΩ → 4V 与输出电阻。"""
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
            Beat("空载", 0.0, 2.0, "12V 经 10kΩ 与 10kΩ 分压，输出 6.000V。", BLUE),
            Beat("挂载", 2.0, 4.2, "接上 10kΩ 负载：下臂变成 10kΩ∥10kΩ=5kΩ。", GREEN),
            Beat("塌陷", 4.2, 6.6, "输出跌到 4.000V，相对空载标称值误差 −33.3%。", RED),
            Beat("判据", 6.6, 9.0, "输出电阻 5kΩ；后级输入阻抗至少高一个数量级。", AMBER, hold=True),
        ),
        title="分压器一挂负载就塌",
        subtitle="空载公式只描述开路；带载后下臂被并联，输出由输出电阻决定",
    )
    persistent = "\n".join((
        f'<rect x="48" y="96" width="864" height="420" rx="14" fill="#f6eedb" stroke="{RULE}" stroke-width="1.4"/>',
        # source
        f'<circle cx="96" cy="300" r="28" fill="{BLUE_T}" stroke="{BLUE}" stroke-width="2"/>',
        f'<text x="96" y="295" text-anchor="middle" font-size="13" font-weight="bold" fill="{BLUE}">12V</text>',
        f'<text x="96" y="313" text-anchor="middle" font-size="10" fill="{MUTED}">源</text>',
        # top rail and R1
        f'<line x1="96" y1="272" x2="96" y2="196" stroke="{INK}" stroke-width="2.4"/>',
        f'<line x1="96" y1="196" x2="206" y2="196" stroke="{INK}" stroke-width="2.4"/>',
        f'<line x1="206" y1="196" x2="206" y2="206" stroke="{INK}" stroke-width="2.4"/>',
        f'<rect x="190" y="206" width="32" height="64" rx="3" fill="#fdf8ea" stroke="{INK}" stroke-width="2"/>',
        f'<text x="238" y="232" font-size="12" font-weight="bold" fill="{INK}">R1 10kΩ</text>',
        f'<line x1="206" y1="270" x2="206" y2="330" stroke="{INK}" stroke-width="2.4"/>',
        # R2
        f'<rect x="190" y="330" width="32" height="64" rx="3" fill="#fdf8ea" stroke="{INK}" stroke-width="2"/>',
        f'<text x="238" y="356" font-size="12" font-weight="bold" fill="{INK}">R2 10kΩ</text>',
        f'<line x1="206" y1="394" x2="206" y2="424" stroke="{INK}" stroke-width="2.4"/>',
        f'<line x1="182" y1="424" x2="230" y2="424" stroke="{INK}" stroke-width="2.4"/>',
        f'<line x1="190" y1="434" x2="222" y2="434" stroke="{MUTED}" stroke-width="2"/>',
        f'<line x1="198" y1="444" x2="214" y2="444" stroke="{MUTED}" stroke-width="2"/>',
        f'<line x1="96" y1="328" x2="96" y2="424" stroke="{INK}" stroke-width="2.4"/>',
        f'<line x1="96" y1="424" x2="182" y2="424" stroke="{INK}" stroke-width="2.4"/>',
        # output node
        f'<line x1="206" y1="300" x2="640" y2="300" stroke="{INK}" stroke-width="2.4"/>',
        f'<circle cx="206" cy="300" r="4.5" fill="{INK}"/>',
        f'<text x="300" y="286" font-size="12" font-weight="bold" fill="{INK}">Vout</text>',
        # load branch placeholder
        f'<line x1="640" y1="300" x2="640" y2="340" stroke="{RULE}" stroke-width="2" stroke-dasharray="6,5"/>',
        f'<text x="656" y="330" font-size="11" fill="{MUTED}">RL</text>',
    ))
    layers = [
        Layer(None, persistent),
        Layer("空载", "\n".join((
            f'<rect x="500" y="168" width="300" height="86" rx="10" fill="{BLUE_T}" stroke="{BLUE}" stroke-width="1.6"/>',
            f'<text x="520" y="198" font-size="14" font-weight="bold" fill="{BLUE}">空载：只有串联电流</text>',
            f'<text x="520" y="222" font-size="12.5" fill="{INK}">Vout = 12 × 10k/(10k+10k)</text>',
            f'<text x="520" y="244" font-size="17" font-weight="bold" fill="{BLUE}">= 6.000V</text>',
        )), (0, -4)),
        Layer("挂载", "\n".join((
            f'<line x1="640" y1="340" x2="640" y2="380" stroke="{INK}" stroke-width="2.4"/>',
            f'<rect x="624" y="380" width="32" height="46" rx="3" fill="#fdf8ea" stroke="{GREEN}" stroke-width="2"/>',
            f'<line x1="640" y1="426" x2="640" y2="448" stroke="{INK}" stroke-width="2.4"/>',
            f'<line x1="620" y1="448" x2="660" y2="448" stroke="{INK}" stroke-width="2.4"/>',
            f'<text x="670" y="404" font-size="12" font-weight="bold" fill="{GREEN}">RL 10kΩ 接入</text>',
            f'<rect x="500" y="168" width="300" height="66" rx="10" fill="{GREEN_T}" stroke="{GREEN}" stroke-width="1.6"/>',
            f'<text x="520" y="198" font-size="14" font-weight="bold" fill="{GREEN}">下臂被并联</text>',
            f'<text x="520" y="222" font-size="12.5" fill="{INK}">R2∥RL = 10k∥10k = 5kΩ</text>',
        )), (0, -4)),
        Layer("塌陷", "\n".join((
            f'<rect x="500" y="250" width="300" height="70" rx="10" fill="{RED_T}" stroke="{RED}" stroke-width="1.6"/>',
            f'<text x="520" y="278" font-size="13" font-weight="bold" fill="{RED}">带载输出</text>',
            f'<text x="520" y="302" font-size="15" font-weight="bold" fill="{RED}">12 × 5k/(10k+5k) = 4.000V</text>',
            f'<text x="500" y="348" font-size="13" fill="{RED}">(4−6)/6 = −33.3%</text>',
            f'<text x="500" y="374" font-size="11.5" fill="{MUTED}">电压指针矮了三分之一。</text>',
        )), (0, -4)),
        Layer("判据", "\n".join((
            # 结论拍保留负载支路：否则「下臂被并联」在图上只剩一根虚线和 RL 两个字。
            f'<line x1="640" y1="300" x2="640" y2="380" stroke="{INK}" stroke-width="2.4"/>',
            f'<rect x="624" y="380" width="32" height="46" rx="3" fill="#fdf8ea" stroke="{GREEN}" stroke-width="2"/>',
            f'<line x1="640" y1="426" x2="640" y2="448" stroke="{INK}" stroke-width="2.4"/>',
            f'<line x1="620" y1="448" x2="660" y2="448" stroke="{INK}" stroke-width="2.4"/>',
            f'<text x="670" y="404" font-size="12" font-weight="bold" fill="{GREEN}">RL 10kΩ</text>',
            f'<rect x="500" y="168" width="340" height="118" rx="10" fill="{AMBER_T}" stroke="{AMBER}" stroke-width="1.6"/>',
            f'<text x="520" y="198" font-size="13" font-weight="bold" fill="{AMBER}">带载能力看输出电阻</text>',
            f'<text x="520" y="224" font-size="12.5" fill="{INK}">Rout = R1∥R2 = 5kΩ</text>',
            f'<text x="520" y="248" font-size="12.5" fill="{INK}">RL 只比 Rout 大两倍，误差已 1/3</text>',
            f'<text x="520" y="272" font-size="12" font-weight="bold" fill="{AMBER}">后级输入 ≥10×Rout</text>',
        )), (0, -4)),
    ]
    return tl, layers


if __name__ == "__main__":
    tl, layers = scene()
    write(tl, layers, SCRIPTS.parent / "assets" / "svg-v2", "ch00-divider-loading-v2")
