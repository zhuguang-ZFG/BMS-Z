"""Wave 6 手绘草图：ADC 骑跨、回流审查、双面地网。"""
from __future__ import annotations

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK, INK2, PAPER, RED, RULE, arrow, box, header, text,
)
from scripts.visuals.scenes.handdrawn_wave3 import varrow


def adc_straddle():
    parts = [header('ADC 骑跨：分的是布局，不是地平面',
                    '模拟脚在模拟侧，数字脚在数字侧；地平面保持完整。')]
    parts.append(box(50, 132, 420, 420, fill=PAPER))
    parts.append(box(530, 132, 420, 420, fill=PAPER))
    parts.append(text(74, 176, '模拟区', 26, colour=GREEN, weight='700'))
    parts.append(text(554, 176, '数字区', 26, colour=BLUE, weight='700'))

    parts.append(box(390, 230, 220, 220, fill=PAPER))
    parts.append(text(500, 282, 'ADC', 30, anchor='middle', weight='700'))
    parts.append(text(500, 322, '芯片本体跨线', 22, colour=INK2, anchor='middle'))
    parts.append(text(500, 362, 'AGND / DGND', 22, anchor='middle'))
    parts.append(text(500, 400, '片内已连', 22, colour=INK2, anchor='middle'))

    for i, label in enumerate(['AIN', 'REF', 'AVDD']):
        y = 272 + i * 44
        parts.append(text(374, y, label, 22, colour=GREEN, anchor='end'))
        parts.append(f'<line x1="382" y1="{y - 7}" x2="404" y2="{y - 7}" stroke="{GREEN}" stroke-width="2"/>')
    for i, label in enumerate(['SPI', 'CLK', 'DVDD']):
        y = 272 + i * 44
        parts.append(text(626, y, label, 22, colour=BLUE))
        parts.append(f'<line x1="598" y1="{y - 7}" x2="620" y2="{y - 7}" stroke="{BLUE}" stroke-width="2"/>')

    parts.append(f'<line x1="500" y1="160" x2="500" y2="530" stroke="{AMBER}" stroke-width="2.5" stroke-dasharray="9,7"/>')
    parts.append(text(500, 568, '分区线', 22, colour=AMBER, anchor='middle'))
    parts.append(text(500, 598, '不是地平面分割线', 22, anchor='middle', weight='700'))
    parts.append(box(100, 618, 800, 52, fill=PAPER))
    parts.append(text(500, 651, '数字回流从 DGND 入平面，不经过模拟脚下方。', 22, anchor='middle'))
    return parts


def return_review():
    parts = [header('回流审查：每网一分钟',
                    '高亮、沿走线、查换层、查槽、不留模糊地带。')]
    rows = [
        ('① 高亮网络', '在编辑器里只亮这一根'),
        ('② 沿走线看', '想象正下方地平面的回流'),
        ('③ 到换层过孔', '旁边有没有地孔陪跑'),
        ('④ 遇槽/隔离带', '回流会不会被挤开'),
        ('⑤ 不许“应该能绕”', '模糊地带就是辐射源'),
    ]
    for i, (head, note) in enumerate(rows):
        y = 150 + i * 86
        parts.append(f'<rect x="64" y="{y - 24}" width="26" height="26" rx="3" fill="none" stroke="{INK2}" stroke-width="2"/>')
        parts.append(text(108, y, head, 23, weight='700'))
        parts.append(text(108, y + 32, note, 22, colour=INK2))
        parts.append(f'<line x1="64" y1="{y + 50}" x2="560" y2="{y + 50}" stroke="{RULE}" stroke-width="1.2"/>')

    parts.append(box(610, 150, 340, 420, fill=PAPER))
    parts.append(text(636, 194, '看一眼回路面积', 23, colour=AMBER, weight='700'))
    parts.append(f'<path d="M660,460 L660,270 L820,270 L820,460" fill="none" stroke="{GREEN}" stroke-width="3"/>')
    parts.append(f'<path d="M680,480 L680,310 L900,310 L900,480" fill="none" stroke="{RED}" stroke-width="3" stroke-dasharray="8,6"/>')
    parts.append(text(740, 256, '紧贴', 22, colour=GREEN, anchor='middle'))
    parts.append(text(820, 498, '绕远 = 天线', 22, colour=RED, anchor='middle'))
    parts.append(text(636, 540, '先改几何，再谈屏蔽。', 22, colour=INK2))

    parts.append(text(64, 630, '时钟、复位、晶振、SW、总线、接口驱动必须过一遍；慢速信号抽查。', 22, colour=INK2))
    return parts


def ground_grid():
    parts = [header('双层板没有完整平面，就做地网',
                    '网格越小，最近回程越近；网孔 20 mm 是经验上限。')]
    parts.append(box(50, 136, 420, 430, fill=PAPER))
    parts.append(text(74, 180, '四层：完整平面', 24, colour=GREEN, weight='700'))
    parts.append(f'<line x1="100" y1="250" x2="420" y2="250" stroke="{INK}" stroke-width="4"/>')
    parts.append(f'<path d="M130,250 C190,210 240,210 300,250 C350,282 390,282 410,250" fill="none" stroke="{AMBER}" stroke-width="4"/>')
    parts.append(text(120, 228, '信号', 22, colour=INK2))
    parts.append(text(120, 310, '回流贴着正下方', 22, colour=GREEN))
    parts.append(text(120, 360, '介质约 1 mm', 22, colour=INK2))
    parts.append(text(120, 410, '回路面积最小', 22, weight='700'))

    parts.append(box(520, 136, 420, 430, fill=PAPER))
    parts.append(text(544, 180, '双层：地网 + 铺铜', 24, colour=BLUE, weight='700'))
    for x in range(570, 921, 70):
        parts.append(f'<line x1="{x}" y1="236" x2="{x}" y2="486" stroke="{BLUE}" stroke-width="2" opacity=".55"/>')
    for y in range(236, 487, 70):
        parts.append(f'<line x1="560" y1="{y}" x2="910" y2="{y}" stroke="{BLUE}" stroke-width="2" opacity=".55"/>')
    for x in range(570, 921, 70):
        for y in range(236, 487, 70):
            parts.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{AMBER}"/>')
    parts.append(text(560, 524, '网孔 ≤20 mm', 22, colour=AMBER, weight='700'))
    parts.append(text(560, 558, '空白铺铜，双面打过孔缝合', 22, colour=INK2))

    parts.append(box(60, 598, 880, 58, fill=PAPER))
    parts.append(text(500, 635, '平面 1 mm 对网格 20 mm：环路电感差一个数量级，辐射差约 20 dB。', 22, anchor='middle', weight='700'))
    return parts


SCENES = {
    'ch15-adc-straddle': {
        'draw': adc_straddle, 'title': 'ADC 骑跨分区线', 'anchor': '15.1',
        'chapter': 15, 'source': 'docs/p3-02-ch15.md',
        'alt': '手绘 ADC 骑跨：芯片本体跨在模拟区与数字区的分区线上，AIN、REF、AVDD 在左，SPI、CLK、DVDD 在右；AGND 与 DGND 就近下过孔进完整地平面，数字回流不经过模拟脚下方。',
    },
    'ch15-return-review': {
        'draw': return_review, 'title': '回流审查五步', 'anchor': '15.7',
        'chapter': 15, 'source': 'docs/p3-02-ch15.md',
        'alt': '手绘回流审查单：高亮网络、沿走线想象正下方回流、到换层过孔查伴生地孔、遇槽或隔离带查回流是否被挤开、不许用“应该能绕”含糊过去；右侧对比紧贴回流与绕远形成天线。',
    },
    'ch15-ground-grid': {
        'draw': ground_grid, 'title': '双层板地网', 'anchor': '15.7',
        'chapter': 15, 'source': 'docs/p3-02-ch15.md',
        'alt': '手绘两种地：四层板完整平面，信号回流贴着正下方约 1 毫米介质；双层板用 20 毫米以内的地网加铺铜与过孔缝合，环路电感差一个数量级，辐射差约 20 dB。',
    },
}
