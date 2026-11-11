"""Wave 12 手绘草图：薄章补图（ch1 电解寿命/降容乘法、ch4 dv/dt 误导通、
ch6 压摆率与全功率带宽、ch7 上拉三账与阈值预算）。

每张图的数字只取对应 anchor 小节：ch1 取 1.7 的寿命与降容算例，
ch4 取 4.3 的 dv/dt 误导通量级，ch6 取 6.7 的压摆/建立时间，
ch7 取 7.2 的上拉三步与误差预算。
"""
from __future__ import annotations

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK, INK2, PAPER, RED, RULE, arrow, box, header, text,
)


def electrolytic_life():
    parts = [header('10°C 翻倍法则：2000 小时能变 3.7 年',
                    '厂商给的是 L0 小时 @ T0；降温一档翻一倍，纹波发热反着吃回去。')]
    parts.append(box(50, 130, 430, 300, fill=PAPER))
    parts.append(text(74, 170, '温度每降 10°C，寿命翻一倍', 24, colour=GREEN, weight='700'))
    parts.append(box(86, 190, 372, 80, fill=PAPER, stroke=RED))
    parts.append(text(106, 224, '手册条件　105°C', 22, colour=INK2))
    parts.append(text(106, 256, '2000h', 28, colour=RED, weight='700'))
    parts.append(arrow(152, 276, 152, 308, colour=AMBER))
    parts.append(text(176, 300, '每 10°C 翻一倍，共 4 次', 22, colour=AMBER, weight='700'))
    parts.append(box(86, 316, 372, 80, fill=PAPER, stroke=GREEN))
    parts.append(text(106, 350, '实际工况　65°C', 22, colour=INK2))
    parts.append(text(106, 382, '32000h', 28, colour=GREEN, weight='700'))
    parts.append(text(74, 418, '约 3.7 年连续通电', 22, colour=INK2))
    parts.append(box(520, 130, 430, 300, fill=PAPER))
    parts.append(text(544, 172, '纹波电流从另一头吃回来', 24, colour=RED, weight='700'))
    parts.append(text(544, 216, '纹波在 ESR 上发热', 22, colour=INK2))
    parts.append(text(544, 254, '这份热直接进寿命公式的 T', 22, colour=INK2))
    parts.append(arrow(560, 282, 700, 282, colour=RED))
    parts.append(text(716, 290, '超额 30%', 22, colour=RED, weight='700'))
    parts.append(text(544, 330, '芯温升高 5~10°C', 24, colour=RED, weight='700'))
    parts.append(text(544, 368, '寿命当场腰斩', 24, colour=RED, weight='700'))
    parts.append(text(544, 412, '先按纹波电流与温升选系列，再选容量', 22, colour=INK2))
    parts.append(box(50, 456, 900, 104, fill=PAPER))
    parts.append(text(76, 496, '想长寿：把 L0 提到 5000~10000h，或换固态 / 聚合物。', 24,
                      colour=GREEN, weight='700'))
    parts.append(text(76, 532, '顺序反了，电容会先被自己的 ESR 煮熟。', 22, colour=INK2))
    parts.append(text(500, 622, '开关电源里第一个坏的总是电解电容：环境温度与自发热，它两样都吃。',
                      22, colour=AMBER, anchor='middle', weight='700'))
    return parts


def derating_product():
    parts = [header('最坏情况预算是乘法，不是加法',
                    '标称容量有测试条件；温度、偏压、老化三项各打八折，只剩一半上下。')]
    parts.append(box(50, 130, 430, 250, fill=PAPER))
    parts.append(text(74, 172, 'Buck 输出 3.3V / 2A', 24, colour=BLUE, weight='700'))
    parts.append(text(74, 206, '500kHz，电感纹波 0.6A', 22, colour=INK2))
    parts.append(text(74, 238, '22µF X5R 0805', 22, colour=INK2))
    parts.append(f'<line x1="80" y1="262" x2="450" y2="262" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(74, 294, '按标称 22µF', 22, colour=INK2))
    parts.append(text(300, 294, '6.8mV', 26, colour=GREEN, weight='700'))
    parts.append(text(74, 330, '偏压下只剩约 10µF', 22, colour=INK2))
    parts.append(text(300, 330, '15mV', 26, colour=RED, weight='700'))
    parts.append(text(74, 362, '同样电感纹波，容性纹波翻了一倍多', 22, colour=AMBER))
    parts.append(box(520, 130, 430, 250, fill=PAPER))
    parts.append(text(544, 172, '三项保持率相乘', 24, colour=RED, weight='700'))
    parts.append(text(544, 212, '温度保持率', 22, colour=INK2))
    parts.append(text(544, 250, '偏压保持率', 22, colour=INK2))
    parts.append(text(544, 288, '老化保持率', 22, colour=INK2))
    for y in (205, 243, 281):
        parts.append(text(800, y + 7, '× 八折', 22, colour=AMBER, weight='700'))
    parts.append(f'<line x1="544" y1="306" x2="926" y2="306" stroke="{RULE}" '
                 f'stroke-width="2"/>')
    parts.append(text(544, 344, '10µF X5R 服役三年', 22, colour=INK2))
    parts.append(text(800, 344, '剩一半', 26, colour=RED, anchor='middle', weight='700'))
    parts.append(text(544, 372, '老化每十倍时程跌约 1%~2%', 22, colour=INK2))
    parts.append(box(50, 406, 900, 154, fill=PAPER))
    parts.append(text(76, 446, '所以才有「标称 10µF 按 5µF 设计」这条惯例', 24,
                      colour=GREEN, weight='700'))
    parts.append(text(76, 482, '不是悲观，是把乘法提前算好。', 22, colour=INK2))
    parts.append(text(76, 520, 'X7R 的 ±15% 是全温范围的总窗口，高低温两头各占一半；', 22,
                      colour=INK2))
    parts.append(text(76, 548, '回流焊的高温会把老化时钟归零重新计时。', 22, colour=INK2))
    return parts


def dvdt_false_turnon():
    parts = [header('半桥直通：栅极是被 dv/dt 灌开的',
                    '上管开通把开关节点拉向母线，下管的 Cgd 把位移电流灌进自己的栅极。')]
    parts.append(box(50, 130, 430, 290, fill=PAPER))
    parts.append(text(74, 172, '位移电流怎么来的', 24, colour=RED, weight='700'))
    parts.append(f'<line x1="150" y1="210" x2="150" y2="290" stroke="{INK2}" stroke-width="3"/>')
    parts.append(f'<line x1="150" y1="290" x2="150" y2="380" stroke="{INK2}" stroke-width="3"/>')
    parts.append(text(166, 226, '上管开通', 22, colour=INK2))
    parts.append(arrow(200, 290, 300, 240, colour=RED))
    parts.append(text(312, 236, '20V/ns', 24, colour=RED, weight='700'))
    parts.append(text(166, 320, '下管本该关断', 22, colour=INK2))
    parts.append(f'<line x1="300" y1="300" x2="300" y2="340" stroke="{BLUE}" stroke-width="4"/>')
    parts.append(f'<line x1="314" y1="300" x2="314" y2="340" stroke="{BLUE}" stroke-width="4"/>')
    parts.append(text(330, 326, 'Crss 50pF', 22, colour=BLUE, weight='700'))
    parts.append(text(74, 400, '50pF × 20V/ns 给出 1A 瞬态电流', 22, colour=RED, weight='700'))
    parts.append(box(520, 130, 430, 290, fill=PAPER))
    parts.append(text(544, 172, '这 1A 落在哪', 24, colour=AMBER, weight='700'))
    parts.append(text(544, 216, '关断回路阻抗 10Ω', 22, colour=INK2))
    parts.append(text(544, 254, '压降可达 10V 量级', 24, colour=RED, weight='700'))
    parts.append(text(544, 292, '足以把管子重新打开', 22, colour=RED))
    parts.append(f'<line x1="544" y1="312" x2="926" y2="312" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(544, 350, '更保守的上界用电容分压估', 22, colour=INK2))
    parts.append(text(544, 388, '400V × 50pF/(50+1000)pF ≈ 19V', 22, colour=AMBER, weight='700'))
    parts.append(text(544, 414, '实际 Crss 随 VDS 升高急剧缩小', 22, colour=INK2))
    parts.append(box(50, 446, 900, 114, fill=PAPER))
    parts.append(text(76, 486, '对策三条：减小关断回路阻抗、负压关断、选带米勒钳位的驱动器。', 24,
                      colour=GREEN, weight='700'))
    parts.append(text(76, 522, '余量必须按最高结温下的 VTH 核对——结温越高，门槛越低。', 22,
                      colour=INK2))
    parts.append(text(76, 550, '米勒钳位的做法是低电平时把栅极短接到源。', 22, colour=INK2))
    parts.append(text(500, 622, '方向明确：dv/dt 越陡，灌进栅极的电流越大。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def slew_vs_gbw():
    from scripts.visuals.scenes.ch06_reference_figures import SCENES as corrected
    return corrected['ch06-slew-vs-gbw']['draw']()


def pullup_three_accounts():
    parts = [header('开集电极上拉：一只电阻挂在三本账上',
                    '速度、低电平、噪声同时被它定；先定窗口，再取值，最后回代。')]
    parts.append(box(50, 126, 900, 196, fill=PAPER))
    cols = [
        (86, '速度账', GREEN, ['上升沿充总线与负载电容', 'tr ≈ 2.2RC', 'R 越小沿越快']),
        (386, '低电平账', RED, ['IOL = Vpullup / R', '电流全进输出管，下限 6mA',
                                '灌得越多 VOL 越高']),
        (686, '噪声账', BLUE, ['R 越小节点阻抗越低', '抗串扰越好', '高速开漏总线用强上拉']),
    ]
    for x, title_text, colour, lines in cols:
        parts.append(text(x, 168, title_text, 26, colour=colour, weight='700'))
        for index, line in enumerate(lines):
            parts.append(text(x, 212 + index * 34, line, 22, colour=INK2))
    parts.append(f'<line x1="366" y1="140" x2="366" y2="308" stroke="{RULE}" stroke-width="2"/>')
    parts.append(f'<line x1="666" y1="140" x2="666" y2="308" stroke="{RULE}" stroke-width="2"/>')
    parts.append(box(50, 342, 430, 180, fill=PAPER))
    parts.append(text(74, 382, '两个取值的对照', 24, colour=AMBER, weight='700'))
    parts.append(text(74, 424, '4.7kΩ 上拉到 5V', 22, colour=GREEN, weight='700'))
    parts.append(text(74, 456, '灌 1.06mA，VOL 约 0.1~0.2V', 22, colour=INK2))
    parts.append(text(74, 488, '330Ω 上拉到 12V：灌 36mA', 22, colour=RED, weight='700'))
    parts.append(text(74, 516, 'VOL 可能接近 1V', 22, colour=RED, weight='700'))
    parts.append(box(520, 342, 430, 180, fill=PAPER))
    parts.append(text(544, 382, '三步定值（5V、50pF、沿快于 1µs）', 22, colour=GREEN,
                      weight='700'))
    parts.append(text(544, 420, '① 由沿定上限　R ≤ 9.1kΩ', 22, colour=INK2))
    parts.append(text(544, 454, '② 由灌电流定下限　R ≥ 2.5kΩ', 22, colour=INK2))
    parts.append(text(544, 488, '③ 取 4.7kΩ 回代　tr ≈ 0.52µs', 22, colour=AMBER, weight='700'))
    parts.append(text(500, 580, '沿是快了，低电平却脏了——三本账不能只记一本。', 24,
                      colour=RED, anchor='middle', weight='700'))
    parts.append(text(500, 626, '开集电极输出管是逻辑器件，不是功率器件。', 22,
                      colour=INK2, anchor='middle'))
    return parts


def threshold_budget():
    parts = [header('判决点不准，很少是比较器的错',
                    '5V 分压得 2.5V 基准、两只 1% 电阻：电阻容差是失调的十倍。')]
    parts.append(box(50, 130, 900, 244, fill=PAPER))
    bars = [
        ('电阻容差　分压比最坏偏差 ±2%', '±50mV', 186, RED, 520),
        ('器件失调　手册保证最大值', '±5mV', 248, AMBER, 120),
        ('偏流失调　25nA × 49kΩ', '1.2mV', 310, BLUE, 60),
    ]
    for label, value, y, colour, width in bars:
        parts.append(text(74, y - 8, label, 22, colour=INK2))
        parts.append(f'<rect x="74" y="{y + 4}" width="{width}" height="22" rx="5" '
                     f'fill="{colour}" opacity="0.72"/>')
        parts.append(text(926, y + 24, value, 24, colour=colour, anchor='end', weight='700'))
    parts.append(text(74, 364, '先压最大那项，再谈下一项——误差预算永远按这个顺序', 22,
                      colour=GREEN, weight='700'))
    parts.append(box(50, 384, 430, 176, fill=PAPER))
    parts.append(text(74, 424, '偏流那一项怎么消', 24, colour=BLUE, weight='700'))
    parts.append(text(74, 464, 'PNP 输入级，偏流从管脚流出来', 22, colour=INK2))
    parts.append(text(74, 496, '基准侧源阻 50kΩ、信号侧 1kΩ', 22, colour=INK2))
    parts.append(text(74, 530, '进误差的是差值，不是绝对值', 22, colour=AMBER, weight='700'))
    parts.append(box(520, 384, 430, 176, fill=PAPER))
    parts.append(text(544, 424, '两条修法', 24, colour=GREEN, weight='700'))
    parts.append(text(544, 464, '① 让两侧看到的源阻尽量相等', 22, colour=INK2))
    parts.append(text(544, 496, '② 换 CMOS 输入的比较器', 22, colour=INK2))
    parts.append(text(544, 530, '偏流到 pA 级，这一项直接消失', 22, colour=AMBER, weight='700'))
    parts.append(text(500, 622, '常见误设计：挑低失调器件，却用 5% 分压电阻。', 22,
                      colour=RED, anchor='middle', weight='700'))
    return parts


SCENES = {
    'ch01-electrolytic-life': {
        'draw': electrolytic_life, 'title': '10°C 翻倍法则下的电解电容寿命账',
        'anchor': '1.7', 'chapter': 1, 'source': 'docs/p1-02-ch1.md',
        'alt': '手绘电解电容寿命两栏：左栏画两级对照，手册条件 105 摄氏度 2000 小时，实际工况 65 摄氏度；每降 10 摄氏度翻一倍、共翻 4 次，得 32000 小时，约合 3.7 年连续通电；右栏写纹波电流在 ESR 上发热，这份热直接进寿命公式的温度项，超额 30% 让芯温升高 5 到 10 摄氏度、寿命当场腰斩。底部写想长寿把额定寿命提到 5000 到 10000 小时或换固态聚合物，顺序反了电容会先被自己的 ESR 煮熟。',
    },
    'ch01-derating-product': {
        'draw': derating_product, 'title': '降容是乘法：三项八折只剩一半',
        'anchor': '1.7', 'chapter': 1, 'source': 'docs/p1-02-ch1.md',
        'alt': '手绘降容两栏：左栏算 Buck 输出 3.3 伏 2 安、500 千赫、电感纹波 0.6 安、22 微法 X5R 0805，按标称算纹波 6.8 毫伏，偏压下只剩约 10 微法时纹波 15 毫伏；右栏把温度、偏压、老化三项保持率各打八折相乘，10 微法 X5R 服役三年只剩一半，老化每十倍时程跌约百分之一到二。底部写标称 10 微法按 5 微法设计不是悲观，X7R 的正负 15% 是全温总窗口，回流焊会把老化时钟归零。',
    },
    'ch04-dvdt-false-turnon': {
        'draw': dvdt_false_turnon, 'title': 'dv/dt 误导通的定量图像',
        'anchor': '4.3', 'chapter': 4, 'source': 'docs/p1-05-ch4.md',
        'alt': '手绘半桥 dv/dt 误导通两栏：左栏画上管开通把开关节点以 20 伏每纳秒拉向母线，下管 50 皮法的反向传输电容把位移电流灌进栅极，50 皮法乘 20 伏每纳秒给出 1 安瞬态电流；右栏算这 1 安落在 10 欧关断回路阻抗上，压降可达 10 伏量级，足以重新打开管子，更保守的上界用电容分压估 400 伏乘 50 皮法除以 50 加 1000 皮法，约 19 伏。底部给三条对策：减小关断回路阻抗、负压关断、选带米勒钳位的驱动器，余量按最高结温下的阈值电压核对。',
    },
    'ch06-slew-vs-gbw': {
        'draw': slew_vs_gbw, 'title': '压摆率与全功率带宽的两套物理',
        'anchor': '6.7', 'chapter': 6, 'source': 'docs/p1-07-ch6.md',
        'alt': '手绘运放阶跃两栏：左栏把 0.5 伏每微秒的直线爬坡与只受增益带宽限制的灰色虚线画在一起，2 微秒压摆段把总建立时间从约 1.1 微秒拖到 2.6 微秒；右栏算全功率带宽，输出 10 伏峰峰值正弦时 741 只有 16 千赫，NE5532 的 9 伏每微秒给到 286 千赫，收尾段时间常数 0.16 微秒，进 0.1% 要 6.9 倍时间常数约 1.1 微秒、12 位要 8.3 倍。底部写压摆期输入级饱和、环路增益归零，负反馈不在岗；过冲是免费的相位裕度读数，60 度几乎无过冲、30 度已剧烈振铃。',
    },
    'ch07-pullup-three-accounts': {
        'draw': pullup_three_accounts, 'title': '上拉电阻同时挂在三本账上',
        'anchor': '7.2', 'chapter': 7, 'source': 'docs/p1-08-ch7.md',
        'alt': '手绘开集电极上拉三栏：速度账写上升沿约 2.2RC、电阻越小沿越快；低电平账写灌电流等于上拉电压除以电阻、手册保证下限 6 毫安、灌得越多低电平越高；噪声账写电阻越小节点阻抗越低、抗串扰越好。下排左栏对照 4.7 千欧上拉到 5 伏灌 1.06 毫安、低电平约 0.1 到 0.2 伏，330 欧上拉到 12 伏灌 36 毫安、低电平可能接近 1 伏；右栏给三步定值：由沿定上限不超过 9.1 千欧、由灌电流定下限不低于 2.5 千欧、取 4.7 千欧回代上升沿约 0.52 微秒。',
    },
    'ch07-threshold-budget': {
        'draw': threshold_budget, 'title': '阈值精度的误差预算排序',
        'anchor': '7.2', 'chapter': 7, 'source': 'docs/p1-08-ch7.md',
        'alt': '手绘阈值误差预算条形图：电阻容差让分压比最坏偏差正负 2%、基准偏正负 50 毫伏，条形最长；器件失调手册保证最大正负 5 毫伏；偏流失调 25 纳安乘 49 千欧约 1.2 毫伏，条形最短。下排左栏写 PNP 输入级偏流从管脚流出来，基准侧源阻 50 千欧、信号侧 1 千欧，进误差的是差值不是绝对值；右栏给两条修法：让两侧源阻尽量相等，或换 CMOS 输入比较器让偏流降到皮安级。底部写常见误设计是挑低失调器件却用 5% 分压电阻。',
    },
}

# Keep historical batch entry points aligned with corrected chapter models.
from scripts.visuals.scenes.ch06_reference_figures import SCENES as _ch06_corrected
SCENES['ch06-slew-vs-gbw'] = _ch06_corrected['ch06-slew-vs-gbw']

# Preserve corrected comparator models in historical batch entry points.
from scripts.visuals.scenes.ch07_reference_figures import SCENES as _ch07_corrected
SCENES['ch07-pullup-three-accounts'] = _ch07_corrected['ch07-pullup-three-accounts']
SCENES['ch07-threshold-budget'] = _ch07_corrected['ch07-threshold-budget']
