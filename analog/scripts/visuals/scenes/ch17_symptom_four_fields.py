#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§17.1 症状四空格动画（A5 操作演示）：多少/何时/多常/改了什么。

数字回对正文：3.1V / 400mV / 100Hz。累积型填空：结论拍自然呈现全态。
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

FIELDS = (
    ("偏离多少", "5V → 3.1V，差 1.9V（38%）", RED, RED_T),
    ("从何时开始", "一上电就低？带载才低？开机记录", BLUE, BLUE_T),
    ("发生多常", "偶发还是稳定复现——复现才有对照", AMBER, AMBER_T),
    ("最后改了什么", "换线/换负载/换器件——改回试试", GREEN, GREEN_T),
)


def scene():
    tl = Timeline(
        width=960, height=620, duration=9.5,
        beats=(
            Beat("症状", 0.0, 1.6, "症状卡：5V 输出只有 3.1V，纹波 400mV——先别动烙铁", RED),
            Beat("空格一", 1.6, 3.1, "偏离多少：5V→3.1V，差 1.9V（38%）", RED),
            Beat("空格二", 3.1, 4.6, "从何时开始：一上电就低，还是带载才低", BLUE),
            Beat("空格三", 4.6, 6.1, "发生多常：偶发还是稳定复现——复现才有对照", AMBER),
            Beat("空格四", 6.1, 7.6, "最后改了什么：换线/换负载/换器件，逐项改回试", GREEN),
            Beat("四空全满", 7.6, 9.5, "四空填满才许动烙铁——症状先记录，动手后没法补", GREEN, hold=True),
        ),
        title="症状四空格：动手之前先记满",
        subtitle="100Hz 纹波 400mV 的 5V 轨只有 3.1V——四个空格填满才许动烙铁",
    )
    persistent = "\n".join((
        # 症状卡（左）
        f'<rect x="56" y="92" width="330" height="150" rx="12" fill="{RED_T}" stroke="{RED}" stroke-width="2"/>',
        f'<text x="80" y="126" font-size="14" font-weight="bold" fill="{RED}">症状</text>',
        f'<text x="80" y="158" font-size="17" font-weight="bold" fill="{INK}">5V 输出只有 3.1V</text>',
        f'<text x="80" y="188" font-size="14" fill="{INK}">纹波 400mV</text>',
        f'<text x="80" y="216" font-size="12" fill="{MUTED}">先用四空格记录，再谈修理</text>',
        # 四个空格框（右，纵向列）
        *[f'<rect x="430" y="{92 + i * 108}" width="500" height="88" rx="10" fill="#fdf8ea" stroke="{RULE}" stroke-width="1.4" stroke-dasharray="7,5"/>'
          f'<text x="454" y="{92 + i * 108 + 34}" font-size="13" font-weight="bold" fill="{MUTED}">空格 {i + 1}：{FIELDS[i][0]}</text>'
          for i in range(4)],
    ))
    layers = [Layer(None, persistent)]

    def filled(count, *, frame=None):
        rows = []
        for i in range(4):
            y = 92 + i * 108
            if i >= count:  # 未填项才画占位文字：结论帧不许残留「（待填写）」。
                rows.append(f'<text x="454" y="{y + 62}" font-size="12" '
                            f'fill="{RULE}">（待填写）</text>')
                continue
            name, fill, color, tint = FIELDS[i]
            stroke, width = (GREEN, 2.4) if frame == 'done' else (color, 1.8)
            rows.append(
                f'<rect x="430" y="{y}" width="500" height="88" rx="10" '
                f'fill="{tint}" stroke="{stroke}" stroke-width="{width}"/>'
                f'<text x="454" y="{y + 34}" font-size="13" font-weight="bold" '
                f'fill="{color}">空格 {i + 1}：{name}</text>'
                f'<text x="454" y="{y + 62}" font-size="13.5" font-weight="bold" '
                f'fill="{INK}">{fill}</text>')
        return "\n".join(rows)

    # 累积型填空：每拍重画「已填好的前缀」，否则前一格的答案在下一拍就消失。
    layers.append(Layer(tl.beats[0].name, filled(0)))
    for i in range(4):
        layers.append(Layer(f"空格{'一二三四'[i]}", filled(i + 1), (10, 0)))
    layers.append(Layer("四空全满", "\n".join((
        filled(4, frame='done'),
        f'<rect x="56" y="92" width="330" height="150" rx="12" fill="none" stroke="{GREEN}" stroke-width="2.4"/>',
        f'<rect x="56" y="268" width="330" height="110" rx="12" fill="{GREEN_T}" stroke="{GREEN}" stroke-width="2"/>',
        f'<text x="80" y="304" font-size="14" font-weight="bold" fill="{GREEN}">四空全满，才有资格动手</text>',
        f'<text x="80" y="332" font-size="12" fill="{INK}">症状先记录——动手之后，</text>',
        f'<text x="80" y="354" font-size="12" fill="{INK}">这些空格再也没法补。</text>',
    )), (0, -4)))
    return tl, layers


if __name__ == "__main__":
    tl, layers = scene()
    write(tl, layers, SCRIPTS.parent / "assets" / "svg-v2", "ch17-symptom-four-fields")
