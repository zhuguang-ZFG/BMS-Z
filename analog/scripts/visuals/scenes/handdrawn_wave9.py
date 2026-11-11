"""Wave 9 手绘草图：定时、电流镜、TIA、开关电容与输入级选型。"""
from __future__ import annotations

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK, INK2, PAPER, RED, RULE, box, header, text,
)


def monostable_budget():
    parts = [header('单稳态的 1.1RC，误差不止电阻电容',
                    't = 1.1RC：电阻 ±1%、薄膜电容 ±5%、阈值散差 ±2–4%；最坏 ±8–10%。')]
    parts.append(box(50, 150, 430, 240, fill=PAPER))
    parts.append(text(74, 192, 't = 1.1 × R × C', 24, weight='700'))
    parts.append(text(74, 238, '100k × 10µF', 24, colour=INK2))
    parts.append(text(74, 308, '≈ 1.1 s', 44, colour=GREEN, weight='700'))
    parts.append(text(74, 356, '这只是名义值', 22, colour=INK2))
    parts.append(box(520, 150, 430, 240, fill=PAPER))
    for i, (label, value, col) in enumerate([
            ('电阻', '±1%', INK),
            ('薄膜电容', '±5%', INK),
            ('阈值散差', '±2–4%', INK),
            ('最坏同向', '±8–10%', RED)]):
        y = 190 + i * 50
        parts.append(text(544, y, label, 23, colour=INK2))
        parts.append(text(860, y, value, 27, colour=col, anchor='end',
                          weight='700' if i == 3 else '400'))
    parts.append(box(50, 430, 900, 110, fill=PAPER))
    parts.append(text(76, 474, '要 ±1%：COG + 0.1% 电阻 + 修调。', 23, weight='700'))
    parts.append(text(76, 510, '或者直接交给数字定时器——这颗 1.1 不是精密常数。', 22, colour=INK2))
    parts.append(text(500, 620, '1.1RC 只是起点，误差要逐项加。', 22, colour=AMBER,
                      anchor='middle', weight='700'))
    return parts


def recovery_gap():
    parts = [header('恢复时间没算，第二拍就短',
                    '放电管把电容放空要 µs–几十 µs；大电容可到百 µs，连发触发会提前起算。')]
    # 正常时序
    parts.append(text(84, 170, '正常：等电容归零', 22, colour=GREEN, weight='700'))
    parts.append(f'<path d="M100,260 L100,200 L280,200 L280,260 L430,260 L430,200 L610,200 L610,260" '
                 f'fill="none" stroke="{GREEN}" stroke-width="5"/>')
    parts.append(text(190, 232, '脉宽 1.1RC', 22, colour=GREEN, anchor='middle'))
    parts.append(text(355, 286, '恢复', 22, colour=INK2, anchor='middle'))
    # 太早触发
    parts.append(text(84, 360, '太早：第二拍从半满起算', 22, colour=RED, weight='700'))
    parts.append(f'<path d="M100,450 L100,390 L280,390 L280,450 L360,450 L360,390 L520,390 L520,450" '
                 f'fill="none" stroke="{RED}" stroke-width="5"/>')
    parts.append(text(440, 376, '第二拍变短', 22, colour=RED, anchor='middle'))
    parts.append(f'<line x1="360" y1="450" x2="360" y2="300" stroke="{AMBER}" '
                 f'stroke-width="2" stroke-dasharray="5,5"/>')
    parts.append(text(360, 496, '触发来得太早', 22, colour=AMBER, anchor='middle', weight='700'))
    parts.append(box(650, 150, 300, 300, fill=PAPER))
    rows = [
        ('放电管职责', '把 C 从 2/3 Vcc 放空'),
        ('恢复量级', 'µs–几十 µs'),
        ('大电容', '>10 µF 可到百 µs'),
        ('系统约束', '间隔 > 脉宽 + 恢复'),
    ]
    for i, (head, note) in enumerate(rows):
        y = 194 + i * 66
        parts.append(text(674, y, head, 22, weight='700'))
        parts.append(text(674, y + 26, note, 22, colour=INK2))
    parts.append(text(500, 620, '第二拍不老实，先量 6 脚有没有归零。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def mirror_errors():
    parts = [header('电流镜复印的不是理想电流',
                    'β 分走基极电流，Early 效应改输出电流，Wilson 镜再补一刀。')]
    cards = [
        ('① β 分流', '参考支路先被基极电流分走一份；β 越大越准。'),
        ('② Early 效应', '输出管 VCE 一变，复制电流跟着变；Wilson 镜改进。'),
        ('③ 有源负载', '用电流镜替 Rc，单级增益可推到 >100 dB。'),
    ]
    for i, (head, note) in enumerate(cards):
        y = 160 + i * 140
        parts.append(box(50, y, 900, 110, fill=PAPER))
        parts.append(text(76, y + 42, head, 25, colour=[BLUE, AMBER, GREEN][i], weight='700'))
        parts.append(text(76, y + 78, note, 22, colour=INK2))
    parts.append(text(500, 620, '复印的是电流，不是理想；误差先看 β 与 VCE。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def tia_three_way():
    parts = [header('TIA 的三角：增益、带宽、稳定',
                    'Rf 定增益，Cj 定带宽，Cf 定稳定；三者不能同时拉满。')]
    parts.append(f'<path d="M500,210 L250,470 L750,470 Z" fill="none" stroke="{RULE}" stroke-width="3"/>')
    parts.append(box(220, 150, 560, 90, fill=PAPER))
    parts.append(text(500, 188, '增益', 23, colour=GREEN, anchor='middle', weight='700'))
    parts.append(text(500, 220, '10MΩ × 1nA = 10mV', 22, colour=INK2, anchor='middle'))
    parts.append(box(50, 430, 380, 110, fill=PAPER))
    parts.append(text(70, 468, '带宽', 23, colour=BLUE, weight='700'))
    parts.append(text(70, 500, '10pF + 1MΩ → 15.9kHz', 22, colour=INK2))
    parts.append(box(570, 430, 380, 110, fill=PAPER))
    parts.append(text(590, 468, '稳定', 23, colour=AMBER, weight='700'))
    parts.append(text(590, 500, 'Cf ≥ 0.4pF；实装 1–2pF', 22, colour=INK2))
    parts.append(text(500, 342, '三者互相拉扯', 22, colour=INK2, anchor='middle'))
    parts.append(text(500, 620, '灵敏度与带宽是同一枚硬币；稳定靠 Cf 提前压平噪声增益。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def switch_cap():
    parts = [header('1pF 加 100kHz，等于 10MΩ',
                    '开关电容把电阻绝对值换成时钟频率与电容比值；精度从元件转到晶振。')]
    parts.append(box(50, 150, 480, 240, fill=PAPER))
    parts.append(text(74, 192, 'R_eq = 1 / (f_clk × C)', 24, weight='700'))
    parts.append(text(74, 250, '1pF × 100kHz', 24, colour=INK2))
    parts.append(text(74, 320, '= 10MΩ', 44, colour=GREEN, weight='700'))
    parts.append(text(74, 360, '硅片上几乎不占面积', 22, colour=INK2))
    parts.append(box(560, 150, 390, 240, fill=PAPER))
    rows = [
        ('电容比值', '匹配到 0.1%'),
        ('时钟', '晶振准到 ppm'),
        ('精度来源', '从元件转到时钟'),
    ]
    for i, (head, note) in enumerate(rows):
        y = 194 + i * 62
        parts.append(text(584, y, head, 23, weight='700'))
        parts.append(text(584, y + 28, note, 22, colour=INK2))
    parts.append(box(50, 430, 900, 110, fill=PAPER))
    parts.append(text(76, 468, '代价一：采样 → 混叠；前面必须加抗混叠。', 22, weight='700'))
    parts.append(text(76, 500, '代价二：开关 → 电荷注入；用全差分 + dummy 抵消。', 22, colour=INK2))
    parts.append(text(76, 528, '时钟取信号带宽 50–100 倍。', 22, colour=INK2))
    parts.append(text(500, 620, '电阻的绝对值，被时钟和电容比值替换。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def input_types():
    parts = [header('输入级选型只看源阻抗',
                    '1MΩ 源：BJT 20nA → 20mV；CMOS 1pA → 1µV。差四个数量级。')]
    parts.append(box(50, 150, 420, 190, fill=PAPER))
    parts.append(text(74, 192, 'BJT 输入', 24, colour=RED, weight='700'))
    parts.append(text(74, 234, '20nA × 1MΩ', 23, colour=INK2))
    parts.append(text(74, 292, '20mV', 42, colour=RED, weight='700'))
    parts.append(text(74, 326, '每升 10°C，Ib 约翻倍', 22, colour=INK2))
    parts.append(box(530, 150, 420, 190, fill=PAPER))
    parts.append(text(554, 192, 'CMOS 输入', 24, colour=GREEN, weight='700'))
    parts.append(text(554, 234, '1pA × 1MΩ', 23, colour=INK2))
    parts.append(text(554, 292, '1µV', 42, colour=GREEN, weight='700'))
    parts.append(text(554, 326, '差四个数量级', 22, colour=INK2))
    parts.append(box(50, 380, 900, 180, fill=PAPER))
    parts.append(text(76, 422, '低源阻抗 <10kΩ', 23, colour=BLUE, weight='700'))
    parts.append(text(76, 454, '挑 en 小的 BJT', 22, colour=INK2))
    parts.append(text(420, 422, '高源阻抗 >100kΩ', 23, colour=GREEN, weight='700'))
    parts.append(text(420, 454, '挑 Ib 小的 CMOS / JFET', 22, colour=INK2))
    parts.append(text(76, 510, '中间地带：比 en 与 in×Rs 谁大；先算 Ib×Rs，再谈“低噪声”。', 22,
                      colour=INK2))
    parts.append(text(500, 620, '选型只看源阻抗，不看“低噪声”三个字。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def bias_balance():
    from scripts.visuals.scenes.ch06_reference_figures import SCENES as corrected
    return corrected['ch06-bias-balance']['draw']()


SCENES = {
    'ch10-monostable-budget': {
        'draw': monostable_budget, 'title': '单稳态 1.1RC 的误差预算', 'anchor': '10.5',
        'chapter': 10, 'source': 'docs/p1-11-ch10.md',
        'alt': '手绘左右两栏：左栏写 t 等于 1.1 乘 R 乘 C，100 千欧乘 10 微法约 1.1 秒；右栏逐项列电阻正负 1%、薄膜电容正负 5%、阈值散差正负 2 到 4%，最坏同向正负 8 到 10%。底部写要正负 1% 需 COG、0.1% 电阻与修调。',
    },
    'ch10-recovery-gap': {
        'draw': recovery_gap, 'title': '单稳态恢复时间与连发触发', 'anchor': '10.5',
        'chapter': 10, 'source': 'docs/p1-11-ch10.md',
        'alt': '手绘两行脉冲时序：正常行等电容归零后再触发，第二拍脉宽不变；太早行在恢复期内触发，第二拍从半满电容起算而变短。右侧写放电管把电容从三分之二电源放空需微秒到几十微秒，大于 10 微法可到百微秒，触发间隔要大于脉宽加恢复时间。',
    },
    'ch11-mirror-three-errors': {
        'draw': mirror_errors, 'title': '电流镜的三笔误差', 'anchor': '11.3',
        'chapter': 11, 'source': 'docs/p2-01-ch11.md',
        'alt': '手绘三张误差卡：第一张写贝塔分流，参考支路先被基极电流分走一份，贝塔越大越准；第二张写 Early 效应，输出管 VCE 一变复制电流跟着变，Wilson 镜改进；第三张写有源负载，用电流镜替 Rc 可把单级增益推到 100 分贝以上。',
    },
    'ch12-tia-three-way': {
        'draw': tia_three_way, 'title': 'TIA 的增益带宽稳定三角', 'anchor': '12.10',
        'chapter': 12, 'source': 'docs/p2-02-ch12.md',
        'alt': '手绘三角关系图：顶点是增益，10 兆欧乘 1 纳安等于 10 毫伏；左下是带宽，10 皮法加 1 兆欧得到 15.9 千赫；右下是稳定，补偿电容至少 0.4 皮法、实装 1 到 2 皮法；中心写三者互相拉扯。',
    },
    'ch12-switch-cap': {
        'draw': switch_cap, 'title': '开关电容的等效电阻', 'anchor': '12.12',
        'chapter': 12, 'source': 'docs/p2-02-ch12.md',
        'alt': '手绘左右两栏：左栏写等效电阻等于 1 除以时钟频率乘电容，1 皮法乘 100 千赫等于 10 兆欧；右栏写电容比值匹配到 0.1%、时钟准到 ppm、精度来源从元件转到时钟。底部写采样会混叠、开关会注入电荷，时钟取信号带宽 50 到 100 倍。',
    },
    'ch12-input-types': {
        'draw': input_types, 'title': '按源阻抗选输入级', 'anchor': '12.13',
        'chapter': 12, 'source': 'docs/p2-02-ch12.md',
        'alt': '手绘两张输入级卡片：BJT 输入 20 纳安乘 1 兆欧为 20 毫伏，且每升 10 摄氏度偏置电流约翻倍；CMOS 输入 1 皮安乘 1 兆欧为 1 微伏，差四个数量级。底部写低源阻抗小于 10 千欧挑 en 小的 BJT，高源阻抗大于 100 千欧挑 Ib 小的 CMOS 或 JFET。',
    },
    'ch06-bias-balance': {
        'draw': bias_balance, 'title': '输入偏置电流与平衡电阻', 'anchor': '6.3',
        'chapter': 6, 'source': 'docs/p1-07-ch6.md',
        'alt': '手绘两张误差卡：20 纳安流过 1 千欧只有 20 微伏；流过 100 千欧就是 2 毫伏。下方写平衡电阻法 R3 等于 R1 并联 R2，两输入端直流电阻相等时偏置电流压降对消，只剩失调电流；边界是偏流随温度漂，FET 输入偏置电流是皮安级。',
    },
}

# Keep historical batch entry points aligned with corrected chapter models.
from scripts.visuals.scenes.ch06_reference_figures import SCENES as _ch06_corrected
SCENES['ch06-bias-balance'] = _ch06_corrected['ch06-bias-balance']

from scripts.visuals.scenes.ch10_reference_figures import SCENES as _ch10_corrected
for _aid in ['ch10-monostable-budget', 'ch10-recovery-gap']:
    SCENES[_aid] = _ch10_corrected[_aid]

# Corrected chapter 11 model and visual contract.
from scripts.visuals.scenes.ch11_reference_figures import SCENES as _ch11_corrected
SCENES['ch11-mirror-three-errors'] = _ch11_corrected['ch11-mirror-three-errors']

# Corrected chapter 12 models and source conditions.
from scripts.visuals.scenes.ch12_reference_figures import SCENES as _ch12_corrected
SCENES['ch12-tia-three-way'] = _ch12_corrected['ch12-tia-three-way']
SCENES['ch12-switch-cap'] = _ch12_corrected['ch12-switch-cap']
SCENES['ch12-input-types'] = _ch12_corrected['ch12-input-types']
