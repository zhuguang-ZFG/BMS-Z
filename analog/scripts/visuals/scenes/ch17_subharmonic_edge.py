#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§17.4 次谐波边界动画（A4 失效边界）：占空比推过 50% → 一宽一窄 → 补偿。

数字回对正文：50%（"占空比超过 50% 时电感电流扰动被逐周期放大"）。
变换型动画：滑标/波形演变重画在各拍层；static 只显结论帧。
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
RED_T, BLUE_T, GREEN_T, AMBER_T, PURPLE_T = "#f6e7e1", "#e6eff3", "#e8efe6", "#f7eedb", "#efe8ee"
INK, INK2, MUTED, RULE = "#16202b", "#37424e", "#5b666f", "#c9bb9d"


def scene():
    tl = Timeline(
        width=960, height=620, duration=9.5,
        beats=(
            Beat("旋钮在40%", 0.0, 1.5, "起点：占空比 40%，电流环工作正常，SW 波形规整", BLUE),
            Beat("推过50%", 1.5, 3.2, "负载加重，占空比推到 55%——越过临界点", AMBER),
            Beat("一宽一窄", 3.2, 5.0, "电感电流扰动被逐周期放大：SW 波形一宽一窄交替，周期翻倍", RED),
            Beat("纹波半频", 5.0, 6.5, "输出纹波出现开关频率一半的分量——次谐波振荡的指纹", PURPLE),
            Beat("斜坡补偿", 6.5, 8.0, "对策：给电流环叠一个下斜坡，把放大系数压回 1 以下", BLUE),
            Beat("边界指纹", 8.0, 9.5, "一过 50% 就振、降到 50% 以下就好——调高输入电压一分钟判明", GREEN, hold=True),
        ),
        title="次谐波振荡：50% 占空比边界",
        subtitle="占空比一过 50% 就振、降到 50% 以下就好——这是它的指纹",
    )
    persistent = "\n".join((
        # 占空比滑标底座
        f'<rect x="56" y="92" width="380" height="120" rx="12" fill="#f6eedb" stroke="{RULE}" stroke-width="1.4"/>',
        f'<text x="80" y="122" font-size="12.5" font-weight="bold" fill="{INK2}">占空比旋钮</text>',
        f'<line x1="90" y1="176" x2="402" y2="176" stroke="{RULE}" stroke-width="2.4"/>',
        f'<line x1="266" y1="150" x2="266" y2="200" stroke="{RED}" stroke-width="1.6" stroke-dasharray="4,3"/>',
        f'<text x="266" y="214" text-anchor="middle" font-size="11" fill="{RED}">50% 临界</text>',
        # SW 波形窗
        f'<rect x="460" y="92" width="440" height="220" rx="12" fill="#f6eedb" stroke="{RULE}" stroke-width="1.4"/>',
        f'<text x="484" y="120" font-size="11.5" fill="{MUTED}">SW 节点波形</text>',
        f'<line x1="484" y1="290" x2="876" y2="290" stroke="{RULE}" stroke-width="1.2"/>',
    ))
    wave_regular = f'<path d="M484,290 l30,-44 l30,44 l30,-44 l30,44 l30,-44 l30,44 l30,-44 l30,44 l30,-44 l30,44 l30,-44 l30,44 l30,-44" fill="none" stroke="{BLUE}" stroke-width="2.2"/>'
    wave_wide_narrow = f'<path d="M484,290 l56,-64 l36,64 l56,-64 l36,64 l56,-64 l36,64 l56,-64 l36,64 l56,-64 l36,64" fill="none" stroke="{RED}" stroke-width="2.6"/>'
    knob_40 = "\n".join((
        f'<circle cx="182" cy="176" r="13" fill="{BLUE_T}" stroke="{BLUE}" stroke-width="2.4"/>',
        f'<text x="182" y="144" text-anchor="middle" font-size="13" font-weight="bold" fill="{BLUE}">40%</text>',
    ))
    layers = [
        Layer(None, persistent),
        Layer("旋钮在40%", "\n".join((knob_40, wave_regular)), (0, -6)),
        Layer("推过50%", "\n".join((
            f'<circle cx="310" cy="176" r="13" fill="{AMBER_T}" stroke="{AMBER}" stroke-width="2.4"/>',
            f'<text x="310" y="144" text-anchor="middle" font-size="13" font-weight="bold" fill="{AMBER}">55%</text>',
            f'<path d="M484,290 l24,-52 l24,52 l24,-52 l24,52 l24,-52 l24,52 l24,-52 l24,52 l24,-52 l24,52 l24,-52 l24,52 l24,-52" fill="none" stroke="{AMBER}" stroke-width="2.4"/>',
        )), (0, -6)),
    ] + _beat_layers(wave_regular, wave_wide_narrow, knob_40)
    return tl, layers


def _beat_layers(wave_regular, wave_wide_narrow, knob_40):
    return [
        Layer("一宽一窄", "\n".join((
            wave_wide_narrow,
            f'<text x="600" y="132" font-size="12.5" font-weight="bold" fill="{RED}">一宽一窄交替 · 周期翻倍</text>',
        )), (0, -6)),
        Layer("纹波半频", "\n".join((
            wave_wide_narrow,
            f'<rect x="460" y="330" width="440" height="100" rx="12" fill="#f6eedb" stroke="{RULE}" stroke-width="1.4"/>',
            f'<line x1="484" y1="400" x2="876" y2="400" stroke="{RULE}" stroke-width="1.2"/>',
            f'<line x1="620" y1="356" x2="620" y2="416" stroke="{PURPLE}" stroke-width="2"/>',
            f'<text x="612" y="424" text-anchor="middle" font-size="11" fill="{PURPLE}">f_sw / 2</text>',
            f'<circle cx="740" cy="400" r="5" fill="{PURPLE}"/>',
            f'<text x="736" y="424" text-anchor="middle" font-size="11" fill="{MUTED}">f_sw</text>',
            f'<text x="484" y="352" font-size="11.5" font-weight="bold" fill="{PURPLE}">输出纹波频谱：出现半频分量</text>',
        )), (0, -6)),
        Layer("斜坡补偿", "\n".join((
            wave_wide_narrow,
            f'<text x="600" y="132" font-size="12" fill="{RED}">待修：一宽一窄</text>',
            f'<rect x="56" y="330" width="380" height="100" rx="12" fill="{BLUE_T}" stroke="{BLUE}" stroke-width="1.8"/>',
            f'<line x1="80" y1="410" x2="410" y2="410" stroke="{RULE}" stroke-width="1.2"/>',
            f'<path d="M80,410 L410,352" fill="none" stroke="{BLUE}" stroke-width="2.4"/>',
            f'<text x="80" y="352" font-size="12" font-weight="bold" fill="{BLUE}">下斜坡压回放大系数 &lt; 1</text>',
            f'<text x="80" y="444" font-size="11.5" fill="{MUTED}">人为叠加，抵消逐周期放大</text>',
        )), (0, -6)),
        Layer("边界指纹", "\n".join((
            knob_40,
            wave_regular,
            f'<text x="600" y="132" font-size="12.5" font-weight="bold" fill="{GREEN}">降到 50% 以下：波形恢复规整</text>',
            f'<rect x="56" y="452" width="840" height="120" rx="12" fill="{GREEN_T}" stroke="{GREEN}" stroke-width="2"/>',
            f'<text x="84" y="488" font-size="14" font-weight="bold" fill="{GREEN}">边界指纹：占空比一过 50% 就振，降到 50% 以下就好</text>',
            f'<text x="84" y="516" font-size="12.5" fill="{INK}">一分钟验证：调高输入电压（减小占空比），看振荡是否消失。</text>',
            f'<text x="84" y="540" font-size="12.5" fill="{INK}">消失即次谐波振荡——加斜坡补偿或降低环路增益。</text>',
        )), (0, -4)),
    ]


if __name__ == "__main__":
    tl, layers = scene()
    write(tl, layers, SCRIPTS.parent / "assets" / "svg-v2", "ch17-subharmonic-edge")
