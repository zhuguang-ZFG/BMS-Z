#!/usr/bin/env python3
"""§0.6 恒压源与恒流源：V-I 曲线、输出阻抗与接法。"""
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
            Beat("恒压", 0.0, 2.0, "恒压源的 V-I 是水平线：电流怎么变，电压不动。", BLUE),
            Beat("恒流", 2.0, 4.0, "恒流源的 V-I 是竖线：电压怎么变，电流不动。", GREEN),
            Beat("真实源", 4.0, 6.6, "真实源随负载电流增大而降压；斜率幅值反映输出阻抗。", AMBER),
            Beat("接法", 6.6, 9.0, "恒压源并联负载，恒流源串联负载；性格决定接法。", RED, hold=True),
        ),
        title="两种源，两条 V-I 曲线",
        subtitle="横轴电流 I、纵轴电压 V；斜率的绝对值反映输出阻抗",
    )
    ax = (f'<line x1="120" y1="420" x2="492" y2="420" stroke="{INK}" stroke-width="2"/>'
          f'<line x1="120" y1="420" x2="120" y2="140" stroke="{INK}" stroke-width="2"/>'
          f'<text x="500" y="425" font-size="13" fill="{MUTED}">I</text>'
          f'<text x="108" y="132" font-size="13" fill="{MUTED}">V</text>'
          f'<text x="300" y="448" text-anchor="middle" font-size="11" fill="{MUTED}">源电流</text>'
          f'<text x="92" y="290" text-anchor="middle" font-size="11" fill="{MUTED}" transform="rotate(-90 92 290)">端电压</text>')
    # 横轴为输出电流、纵轴为端电压；所有节拍与静态结论共用同一组曲线。
    voltage_curve = f'<line x1="120" y1="190" x2="480" y2="190" stroke="{BLUE}" stroke-width="4"/>'
    current_curve = f'<line x1="300" y1="150" x2="300" y2="410" stroke="{GREEN}" stroke-width="4"/>'
    real_curves = "\n".join((
        f'<line x1="120" y1="190" x2="470" y2="198" stroke="{AMBER}" stroke-width="3.4"/>',
        f'<line x1="120" y1="190" x2="480" y2="222" stroke="{RED}" stroke-width="3.4"/>',
    ))
    layers = [
        Layer(None, f'<rect x="48" y="96" width="864" height="420" rx="14" fill="#f6eedb" stroke="{RULE}" stroke-width="1.4"/>' + ax),
        Layer("恒压", "\n".join((
            voltage_curve,
            f'<text x="536" y="204" font-size="13" font-weight="bold" fill="{BLUE}">水平线：V 不动</text>',
            f'<text x="536" y="228" font-size="12" fill="{INK}">内阻趋近 0；短路是灾难</text>',
            f'<text x="536" y="252" font-size="12" fill="{MUTED}">常态：开路</text>',
        )), (0, -4)),
        Layer("恒流", "\n".join((
            current_curve,
            f'<text x="536" y="234" font-size="13" font-weight="bold" fill="{GREEN}">竖线：I 不动</text>',
            f'<text x="536" y="276" font-size="12" fill="{INK}">输出阻抗趋近 ∞；开路是灾难</text>',
            f'<text x="536" y="300" font-size="12" fill="{MUTED}">常态：短路</text>',
        )), (0, -4)),
        Layer("真实源", "\n".join((
            real_curves,
            f'<text x="134" y="170" font-size="11.5" fill="{AMBER}">1mΩ：5A 掉 5mV</text>',
            f'<text x="330" y="246" font-size="11.5" fill="{RED}">100mΩ：2A 掉 200mV</text>',
            f'<text x="536" y="166" font-size="10.5" fill="{MUTED}">斜率放大示意</text>',
        )), (0, -4)),
        Layer("接法", "\n".join((
            # 接法卡与曲线分栏，结论帧保留两类理想源及真实源的特性。
            voltage_curve,
            current_curve,
            real_curves,
            f'<text x="120" y="488" font-size="11.5" fill="{MUTED}">恒压：水平；恒流：竖直；斜率放大示意</text>',
            f'<rect x="512" y="150" width="304" height="100" rx="10" fill="{BLUE_T}" stroke="{BLUE}" stroke-width="1.5"/>',
            f'<text x="532" y="178" font-size="13" font-weight="bold" fill="{BLUE}">恒压源 → 负载并联</text>',
            f'<text x="532" y="202" font-size="11.5" fill="{INK}">各自独立取电流</text>',
            f'<text x="532" y="226" font-size="11.5" fill="{MUTED}">例：多路 LED 各串限流电阻</text>',
            f'<rect x="512" y="268" width="304" height="100" rx="10" fill="{GREEN_T}" stroke="{GREEN}" stroke-width="1.5"/>',
            f'<text x="532" y="296" font-size="13" font-weight="bold" fill="{GREEN}">恒流源 → 负载串联</text>',
            f'<text x="532" y="320" font-size="11.5" fill="{INK}">同一股电流穿过所有负载</text>',
            f'<text x="532" y="344" font-size="11.5" fill="{MUTED}">Ro=10MΩ：0→10V 只掉 1µA</text>',
        )), (0, -4)),
    ]
    return tl, layers


if __name__ == "__main__":
    tl, layers = scene()
    write(tl, layers, SCRIPTS.parent / "assets" / "svg-v2", "ch00-source-types-v2")
