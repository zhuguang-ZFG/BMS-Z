"""Wave 11 手绘草图：米勒带宽、恒流源合规电压、分流电阻预算。"""
from __future__ import annotations

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK, INK2, PAPER, RED, RULE, box, header, text,
)


def miller_bandwidth():
    parts = [header('10pF 跨在增益两端，变成 1nF',
                    'Ceff = (1+A)Cbc；A=100 时 10pF 变 1.01nF，10kΩ 源阻抗把带宽压到 15.8kHz。')]
    parts.append(box(50, 150, 430, 270, fill=PAPER))
    parts.append(text(74, 192, '跨接电容被增益撬动', 24, colour=RED, weight='700'))
    parts.append(f'<line x1="100" y1="250" x2="232" y2="250" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(f'<line x1="258" y1="250" x2="420" y2="250" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(f'<line x1="238" y1="220" x2="238" y2="280" stroke="{BLUE}" stroke-width="4"/>')
    parts.append(f'<line x1="252" y1="220" x2="252" y2="280" stroke="{BLUE}" stroke-width="4"/>')
    parts.append(text(350, 215, 'Cbc 10pF', 22, colour=BLUE, weight='700'))
    parts.append(text(100, 290, '输入', 22, colour=INK2, anchor='middle'))
    parts.append(text(420, 290, '输出', 22, colour=INK2, anchor='middle'))
    parts.append(text(245, 330, 'A = 100', 24, anchor='middle', weight='700'))
    parts.append(text(245, 378, '× (1+A)', 38, colour=RED, anchor='middle', weight='700'))
    parts.append(text(245, 410, '10pF → 1.01nF', 22, anchor='middle'))
    parts.append(box(520, 150, 430, 270, fill=PAPER))
    parts.append(text(544, 192, '带宽收据', 24, colour=GREEN, weight='700'))
    parts.append(f'<line x1="570" y1="380" x2="920" y2="380" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(f'<line x1="570" y1="380" x2="570" y2="210" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(f'<path d="M580,220 L700,224 C760,226 780,250 810,300 C830,334 850,355 900,366" '
                 f'fill="none" stroke="{GREEN}" stroke-width="4"/>')
    parts.append(f'<line x1="790" y1="380" x2="790" y2="275" stroke="{AMBER}" stroke-width="2" '
                 f'stroke-dasharray="6,5"/>')
    parts.append(text(790, 405, '15.8kHz', 22, colour=AMBER, anchor='middle', weight='700'))
    parts.append(text(700, 245, '−3dB', 22, colour=AMBER, anchor='middle'))
    parts.append(text(544, 410, '10kΩ × 1.01nF', 22, colour=INK2))
    parts.append(box(50, 450, 900, 100, fill=PAPER))
    parts.append(text(76, 490, '你以为能放到 MHz；16kHz 就开始滚降。', 24,
                      colour=RED, weight='700'))
    parts.append(text(76, 524, '共基把 Cbc 一端接地，拆掉米勒桥；代价是输入阻抗只剩 re。', 22,
                      colour=INK2))
    parts.append(text(500, 620, '增益越高，米勒电容越大；带宽是借来的，要还。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def compliance_ceiling():
    parts = [header('恒流源也有天花板：合规电压',
                    '1mA、Rsense 100Ω、调整管 0.7V；负载再大，电流源就退出恒流区。')]
    cards = [
        (50, 'Vs = 2.8V', '2.0kΩ', GREEN),
        (360, 'Vs = 5V', '4.2kΩ', BLUE),
        (670, 'Vs = 12V', '11.2kΩ', AMBER),
    ]
    for x, head, value, colour in cards:
        parts.append(box(x, 150, 280, 230, fill=PAPER))
        parts.append(text(x + 24, 192, head, 26, colour=colour, weight='700'))
        parts.append(text(x + 24, 236, 'RL,max', 22, colour=INK2))
        parts.append(text(x + 24, 306, value, 44, colour=colour, weight='700'))
        parts.append(text(x + 24, 350, '1mA×RL + 0.1V + 0.7V', 22, colour=INK2))
    parts.append(box(50, 410, 900, 150, fill=PAPER))
    parts.append(text(76, 450, '4~20mA 环为什么用 24V？', 24, weight='700'))
    rows = [
        '环路 20mA × 500Ω = 10V',
        '采样 250Ω × 20mA = 5V',
        '发射器裕量 ≈ 7V；合计 ≈ 22V < 24V',
    ]
    for i, line in enumerate(rows):
        parts.append(text(76, 486 + i * 32, line, 22, colour=INK2))
    parts.append(text(500, 620, '裕量是算出来的，不是拍出来的。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def current_sense_budget():
    parts = [header('10mΩ 分流：5A 与 20A 是两笔账',
                    '5A → 50mV、0.25W；堵转 20A → 200mV、4W。精度 1% 还要 CMRR >96dB。')]
    parts.append(box(50, 150, 430, 240, fill=PAPER))
    parts.append(text(74, 192, '额定 5A', 24, colour=GREEN, weight='700'))
    parts.append(text(74, 232, 'Vshunt = 5A × 10mΩ', 22))
    parts.append(text(74, 300, '= 50mV', 44, colour=GREEN, weight='700'))
    parts.append(text(74, 340, 'P = 5² × 0.01 = 0.25W', 22, colour=INK2))
    parts.append(text(74, 372, '选 1W 的 2512 封装', 22, colour=INK2))
    parts.append(box(520, 150, 430, 240, fill=PAPER))
    parts.append(text(544, 192, '堵转 20A', 24, colour=RED, weight='700'))
    parts.append(text(544, 232, 'Vshunt = 20A × 10mΩ', 22))
    parts.append(text(544, 300, '= 200mV', 44, colour=RED, weight='700'))
    parts.append(text(544, 340, 'P = 20² × 0.01 = 4W', 22, colour=INK2))
    parts.append(text(544, 372, '热时间常数必须算', 22, colour=INK2))
    parts.append(box(50, 420, 900, 140, fill=PAPER))
    rows = [
        ('1% 精度', '总误差预算 0.5mV'),
        ('12V 共模压到 0.2mV', '需要 CMRR > 96dB'),
        ('LM358 只有 70dB', '3.8mV 误差 = 7.6%'),
    ]
    for i, (head, note) in enumerate(rows):
        y = 456 + i * 34
        parts.append(text(76, y, head, 22, colour=[GREEN, AMBER, RED][i], weight='700'))
        parts.append(text(420, y, note, 22, colour=INK2))
    parts.append(text(500, 620, '先问负载要不要共地、要不要测短路，再问精度。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


SCENES = {
    'ch11-miller-bandwidth': {
        'draw': miller_bandwidth, 'title': '米勒电容把带宽压到 15.8kHz', 'anchor': '11.5',
        'chapter': 11, 'source': 'docs/p2-01-ch11.md',
        'alt': '手绘米勒效应两栏：左栏画跨接在输入与输出之间的 10 皮法电容，增益 100 把它放大为 1 加 A 倍，等效 1.01 纳法；右栏画低通曲线，10 千欧源阻抗与 1.01 纳法把 3 分贝点压到 15.8 千赫。底部写以为能到兆赫，16 千赫就开始滚降；共基把电容一端接地，拆掉米勒桥。',
    },
    'ch13-compliance-ceiling': {
        'draw': compliance_ceiling, 'title': '恒流源的合规电压天花板', 'anchor': '13.5.1',
        'chapter': 13, 'source': 'docs/p2-03-ch13.md',
        'alt': '手绘三张恒流源负载上限卡：1 毫安恒流、采样 100 欧、调整管 0.7 伏；2.8 伏供电时最大负载 2.0 千欧，5 伏时 4.2 千欧，12 伏时 11.2 千欧。底部算 4 到 20 毫安环：环路 20 毫安乘 500 欧为 10 伏，采样 250 欧乘 20 毫安为 5 伏，加发射器裕量约 7 伏，合计约 22 伏小于 24 伏。',
    },
    'ch13-current-sense-budget': {
        'draw': current_sense_budget, 'title': '10mΩ 分流电阻的两笔账', 'anchor': '13.8',
        'chapter': 13, 'source': 'docs/p2-03-ch13.md',
        'alt': '手绘分流电阻两栏：额定 5 安时，10 毫欧上压降 50 毫伏、功耗 0.25 瓦，选 1 瓦 2512 封装；堵转 20 安时，压降 200 毫伏、功耗 4 瓦，热时间常数必须算。底部写 1% 精度总误差预算 0.5 毫伏；12 伏共模压到 0.2 毫伏需要 CMRR 大于 96 分贝；LM358 只有 70 分贝，3.8 毫伏误差等于 7.6%。',
    },
}

# Corrected chapter 11 model and visual contract.
from scripts.visuals.scenes.ch11_reference_figures import SCENES as _ch11_corrected
SCENES['ch11-miller-bandwidth'] = _ch11_corrected['ch11-miller-bandwidth']

# Chapter 13 reviewed model overrides.
from scripts.visuals.scenes.ch13_reference_figures import SCENES as _CH13_REVIEWED
for _aid in ['ch13-compliance-ceiling', 'ch13-current-sense-budget']:
    SCENES[_aid] = _CH13_REVIEWED[_aid]
