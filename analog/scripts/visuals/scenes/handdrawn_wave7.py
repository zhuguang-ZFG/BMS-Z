"""Wave 7：一阶正弦幅值响应下的五倍带宽经验规则。"""
from __future__ import annotations

import math

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, GREEN, INK2, PAPER, RED, RULE, box, header, text,
)


def bandwidth_five():
    parts = [header('五倍带宽：先说清测的是什么',
                    '示意一阶低通测正弦；不是任意方波与振铃的保真保证。')]
    for x, ratio, colour in ((50, 1, RED), (520, 5, GREEN)):
        gain = 1 / math.sqrt(1 + (1 / ratio) ** 2)
        parts.append(box(x, 136, 430, 330, fill=PAPER))
        parts.append(text(x + 24, 180, f'带宽 / 信号频率 = {ratio}', 25,
                          colour=colour, weight='700'))
        parts.append(f'<line x1="{x + 36}" y1="310" x2="{x + 394}" y2="310" '
                     f'stroke="{RULE}" stroke-width="1.6"/>')
        for amplitude, stroke, dash in ((1, INK2, '6 5'), (gain, colour, 'none')):
            # Phase aligned to compare amplitudes only, explicitly labelled below.
            points = [(x + 36 + 358 * i / 160,
                       310 - 70 * amplitude * math.sin(4 * math.pi * i / 160))
                      for i in range(161)]
            path = 'M' + ' L'.join(f'{px:.2f},{py:.2f}' for px, py in points)
            parts.append(f'<path d="{path}" fill="none" stroke="{stroke}" '
                         f'stroke-width="3" stroke-dasharray="{dash}"/>')
        parts.append(text(x + 215, 423, f'幅值比 {gain:.4f}', 24,
                          colour=colour, anchor='middle', weight='700'))
    parts.append(text(60, 493, '虚线输入，实线测得；相位对齐，只比较幅值。', 22, colour=INK2))
    parts.append(box(60, 516, 880, 76, fill=PAPER))
    parts.append(text(88, 550, '|H(f)| = 1 / √[1 + (f/B)²]；B 是测量链带宽。', 23))
    parts.append(text(88, 580, '五倍时误差约 1.94%；探头、示波器级联还会增加误差。', 22, colour=INK2))
    parts.append(text(60, 628, '测边沿应核对上升时间；测振铃须保留相关高频分量。', 22, weight='700'))
    parts.append(text(60, 664, '20 MHz 限带适合规定带宽的纹波测量，不代表高频尖峰消失。',
                      22, colour=AMBER))
    return parts


SCENES = {
    'ch16-bandwidth-five': {
        'draw': bandwidth_five, 'title': '示波器带宽五倍规则', 'anchor': '16.6',
        'chapter': 16, 'source': 'docs/p4-01-ch16.md',
        'alt': '一阶低通正弦幅值比较：测量链带宽与信号频率之比为 1 时幅值比 0.7071，为 5 时幅值比 0.9806，误差约 1.94%。虚线输入、实线测得，已对齐相位仅比较幅值；20 MHz 限带不代表高频尖峰消失。',
    },
}
