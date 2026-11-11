"""Wave 5 手绘草图：第一问与探头补偿。"""
from __future__ import annotations

import math

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK2, PAPER, RED, RULE, arrow, box, header, text,
)
from scripts.visuals.scenes.handdrawn_wave3 import varrow


def first_question():
    parts = [header('排故第一问：最近改过什么？',
                    '先问变更，再拆机；换料、改版、换环境都比“芯片坏了”更常见。')]
    parts.append(box(110, 132, 780, 108, fill=PAPER))
    parts.append(text(500, 198, '“这块板，最近动过哪里？”', 32, anchor='middle', weight='700'))
    branches = [
        ('换料 / 换厂', '电容、晶振、连接器', AMBER),
        ('改版 / 改参数', '钢网、走线、固件', BLUE),
        ('环境 / 负载', '温度、机箱、供电', GREEN),
    ]
    for i, (head, note, colour) in enumerate(branches):
        x = 64 + i * 300
        parts.append(box(x, 318, 280, 150, fill=PAPER))
        parts.append(text(x + 24, 366, head, 25, colour=colour, weight='700'))
        parts.append(text(x + 24, 412, note, 22, colour=INK2))
        parts.append(varrow(500, 244, x + 140, 310, colour, 2.5))

    parts.append(box(64, 520, 872, 96, fill=PAPER))
    parts.append(text(88, 558, '案例 A 的答案：为降成本把钽电容换成 MLCC。', 22))
    parts.append(text(88, 594, '一问就命中，绕两小时的拆焊本来可以省掉。', 22, colour=RED, weight='700'))
    parts.append(text(64, 662, '问变更不是聊天：把“什么时候、谁、改了什么”记进故障单。', 22, colour=INK2))
    return parts


def probe_compensation():
    parts = [header('探头补偿：先看方波，再信波形',
                    '机身校准方波的顶角，是探头在撒谎时最先暴露的地方。')]
    panels = [
        ('过补偿', '顶角过冲', '尖角翘起', RED),
        ('欠补偿', '顶角圆塌', '边沿变圆', AMBER),
        ('正确', '方角平顶', '平直才能测', GREEN),
    ]
    for i, (head, note, shape, colour) in enumerate(panels):
        x = 60 + i * 305
        parts.append(box(x, 140, 280, 300, fill=PAPER))
        parts.append(text(x + 24, 184, head, 26, colour=colour, weight='700'))
        parts.append(text(x + 24, 224, note, 22, colour=INK2))
        parts.append(f'<line x1="{x + 30}" y1="330" x2="{x + 250}" y2="330" stroke="{RULE}" stroke-width="1.4"/>')
        # Same input edges and settled levels in every panel. The transient
        # residue changes sign: over-compensation overshoots, under-compensation
        # approaches the plateau monotonically. Qualitative model, no time scale.
        residue = (0.3, -0.7, 0.0)[i]
        points: list[tuple[float, float]] = [(x + 40, 330), (x + 90, 330)]
        for step in range(61):
            t = step / 60
            points.append((x + 90 + 90 * t,
                           330 - 70 * (1 + residue * math.exp(-7 * t))))
        for step in range(61):
            t = step / 60
            points.append((x + 180 + 70 * t,
                           330 + 70 * residue * math.exp(-7 * t)))
        d = 'M' + ' L'.join(f'{px:.2f},{py:.2f}' for px, py in points)
        parts.append(f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="4"/>')
        parts.append(text(x + 140, 392, shape, 22, anchor='middle', weight='700'))

    parts.append(box(60, 490, 872, 100, fill=PAPER))
    parts.append(text(88, 528, '补偿没调对，看到的过冲/塌陷可能是探头自己的。', 23))
    parts.append(text(88, 566, '先把方波调成方角平顶，再讨论电路。', 23, colour=GREEN, weight='700'))
    parts.append(text(60, 646, '每个读数先报档位与补偿状态，再报数值。', 22, colour=INK2))
    return parts


SCENES = {
    'ch16-first-question': {
        'draw': first_question, 'title': '排故第一问', 'anchor': '16.1',
        'chapter': 16, 'source': 'docs/p4-01-ch16.md',
        'alt': '手绘第一问：这块板最近动过哪里；三条分支是换料换厂、改版改参数、环境负载；案例 A 的答案是降成本把钽电容换成 MLCC，一问就命中。',
    },
    'ch16-probe-compensation': {
        'draw': probe_compensation, 'title': '探头补偿三种方波', 'anchor': '16.6',
        'chapter': 16, 'source': 'docs/p4-01-ch16.md',
        'alt': '手绘三种校准方波：过补偿顶角过冲、欠补偿顶角圆塌、正确方角平顶；提示补偿没调对时，看到的过冲或塌陷可能来自探头而不是电路。',
    },
}
