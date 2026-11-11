#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§17.1 ESR 扫描动画（A3 参数扫描）：纹波↑ → 生热 → 容量蒸发 → 闭环。

数字回对正文：100Hz / 400mV / 三成。契约见 render.Layer：
常驻层 = 骨架（电容卡、波形轴、容量条外框）；同几何演变重画在拍层。
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

RED, BLUE, AMBER, PURPLE, GREEN = "#a8321f", "#1f5d7a", "#a4630f", "#6b3f63", "#3d6b4a"
RED_T, BLUE_T, GREEN_T, AMBER_T = "#f6e7e1", "#e6eff3", "#e8efe6", "#f7eedb"
INK, INK2, MUTED, RULE = "#16202b", "#37424e", "#5b666f", "#c9bb9d"


def scene():
    tl = Timeline(
        width=960, height=660, duration=8.0,
        beats=(
            Beat("扫描对象", 0.0, 1.4, "扫描对象：输出大电解——ESR 从 0.1Ω 扫到 3Ω", BLUE),
            Beat("纹波爬升", 1.4, 3.0, "ESR 越大，100Hz 纹波越高：400mV 已经烫手", RED),
            Beat("内部生热", 3.0, 4.6, "纹波电流在电解液里生热，热积在铝壳里散不掉", AMBER),
            Beat("容量蒸发", 4.6, 6.2, "电解液被蒸干，容量只剩标称三成", PURPLE),
            Beat("闭环", 6.2, 8.0, "量 100Hz 纹波幅度 = 免费的 ESR 表——先问频率，再问幅度", GREEN, hold=True),
        ),
        title="ESR 扫描：纹波、发热与容量蒸发",
        subtitle="ESR 从 0.1Ω 扫到 3Ω（扫描端点为示意值）——先问纹波频率，再问幅度",
    )
    persistent = "\n".join((
        # 电容卡：引线 + 平行板 + 极性
        f'<rect x="60" y="90" width="300" height="240" rx="12" fill="#f6eedb" stroke="{RULE}" stroke-width="1.4"/>',
        f'<line x1="120" y1="210" x2="196" y2="210" stroke="{INK}" stroke-width="2.4"/>',
        f'<line x1="204" y1="180" x2="204" y2="240" stroke="{INK}" stroke-width="3.2"/>',
        f'<line x1="218" y1="180" x2="218" y2="240" stroke="{INK}" stroke-width="3.2"/>',
        f'<line x1="218" y1="210" x2="294" y2="210" stroke="{INK}" stroke-width="2.4"/>',
        f'<text x="176" y="172" font-size="13" fill="{RED}">+</text>',
        f'<text x="248" y="272" text-anchor="middle" font-size="13" fill="{INK2}">输出大电解</text>',
        # 波形窗：轴 + 正常基线波形（ESR=0.1Ω）
        f'<rect x="400" y="90" width="520" height="240" rx="12" fill="#f6eedb" stroke="{RULE}" stroke-width="1.4"/>',
        f'<line x1="430" y1="210" x2="890" y2="210" stroke="{RULE}" stroke-width="1" stroke-dasharray="4,4"/>',
        f'<text x="432" y="112" font-size="11" fill="{MUTED}">输出纹波 @ 100Hz</text>',
        f'<path d="M430,210 q12,-7 24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0" fill="none" stroke="{BLUE}" stroke-width="2"/>',
        # 容量条外框（常驻）
        f'<rect x="60" y="356" width="640" height="30" rx="8" fill="#fdf8ea" stroke="{RULE}" stroke-width="1.2"/>',
        f'<text x="60" y="412" font-size="12" fill="{MUTED}">实测容量 / 标称容量</text>',
        f'<text x="716" y="376" font-size="12" fill="{MUTED}">100%</text>',
    ))
    layers = [
        Layer(None, persistent),
        Layer("扫描对象", "\n".join((
            f'<rect x="80" y="106" width="260" height="40" rx="9" fill="{BLUE_T}" stroke="{BLUE}" stroke-width="1.6"/>',
            f'<text x="210" y="132" text-anchor="middle" font-size="14" font-weight="bold" fill="{BLUE}">扫描 ESR：0.1Ω → 3Ω</text>',
        )), (0, -6)),
    ] + _beat_layers()
    return tl, layers


def _beat_layers():
    red_layer = "\n".join((
        # 放大后的纹波波形（重画：ESR 升高 → 400mV）
        f'<path d="M430,210 q24,-26 48,0 t48,0 t48,0 t48,0 t48,0 t48,0 t48,0 t48,0 t48,0" fill="none" stroke="{RED}" stroke-width="2.6"/>',
        f'<line x1="826" y1="184" x2="826" y2="236" stroke="{RED}" stroke-width="1.4"/>',
        f'<text x="836" y="188" font-size="12.5" font-weight="bold" fill="{RED}">400mV</text>',
    ))
    heat_layer = "\n".join((
        # 温度计升起
        f'<rect x="318" y="150" width="16" height="150" rx="7" fill="#fdf8ea" stroke="{RULE}" stroke-width="1.2"/>',
        f'<circle cx="326" cy="310" r="13" fill="{RED_T}" stroke="{RED}" stroke-width="1.6"/>',
        f'<rect x="322" y="210" width="8" height="90" rx="4" fill="{RED}"/>',
        f'<text x="344" y="230" font-size="12.5" font-weight="bold" fill="{RED}">内部生热</text>',
    ))
    cap_layer = "\n".join((
        # 容量条缩到三成
        f'<rect x="64" y="360" width="{640 * 0.3:.0f}" height="22" rx="5" fill="{PURPLE}" opacity="0.85"/>',
        f'<text x="236" y="436" font-size="12.5" font-weight="bold" fill="{PURPLE}">只剩标称三成</text>',
    ))
    loop_layer = "\n".join((
        # 结论帧必须保留「容量只剩三成」的图形证据：否则容量条是空框。
        f'<rect x="64" y="360" width="{640 * 0.3:.0f}" height="22" rx="5" fill="{PURPLE}" opacity="0.85"/>',
        f'<text x="236" y="436" font-size="12.5" font-weight="bold" fill="{PURPLE}">只剩标称三成</text>',
        # 闭环卡：生热 → ESR↑ → 纹波↑ → 更热
        f'<rect x="60" y="452" width="840" height="120" rx="12" fill="{GREEN_T}" stroke="{GREEN}" stroke-width="1.8"/>',
        f'<text x="84" y="484" font-size="13" font-weight="bold" fill="{GREEN}">闭环：量 100Hz 纹波幅度 = 免费的 ESR 表</text>',
        f'<text x="84" y="512" font-size="12" fill="{INK}">纹波电流生热 → 热又推高 ESR → ESR 再抬纹波 → 更热</text>',
        f'<text x="84" y="536" font-size="12" font-weight="bold" fill="{AMBER}">先问频率，再问幅度——测量必须能区分候选假设</text>',
        f'<path d="M760,470 q60,40 0,80" fill="none" stroke="{GREEN}" stroke-width="1.6"/>',
        f'<polygon points="760,550 754,540 766,540" fill="{GREEN}"/>',
    ))
    return [
        Layer("纹波爬升", red_layer, (0, 6)),
        Layer("内部生热", heat_layer, (0, -6)),
        Layer("容量蒸发", cap_layer, (6, 0)),
        Layer("闭环", loop_layer, (0, -4)),
    ]


def main():
    tl, layers = scene()
    write(tl, layers, SCRIPTS.parent / "assets" / "svg-v2", "ch17-esr-sweep")


if __name__ == "__main__":
    main()
