"""Wave 13 手绘草图：薄章补图（ch5 推挽直通与 AB 偏置、ch9 7805 四本账、
ch10 555 反推与 50% 占空比、ch11 两级放大器余量）。

每张图的数字只取对应 anchor 小节：ch5 取 5.6 的直通与管耗算例，
ch9 取 9.4 的四本账与升级路径，ch10 取 10.4 的反推与占空比三条路，
ch11 取 11.11 的指标对账。
"""
from __future__ import annotations

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK, INK2, PAPER, RED, RULE, arrow, box, header, text,
)


def astable_reverse_design():
    parts = [header('按目标反推元件：38kHz 怎么落到货架上',
                    '先定电容，再解总电阻，最后用 E 系列凑——回算一遍才算交付。')]
    parts.append(box(50, 130, 430, 330, fill=PAPER))
    parts.append(text(74, 172, '五步反推', 24, colour=BLUE, weight='700'))
    parts.append(text(74, 214, '① 目标：38 kHz 载波，占空比约 50%', 22, colour=INK2))
    parts.append(text(74, 250, '② 取 C=1 nF（COG）', 22, colour=INK2))
    parts.append(text(74, 286, '③ 解总电阻 R1+2R2 ≈ 37.9 kΩ', 22, colour=INK2))
    parts.append(text(74, 322, '④ 近 50% 要 R1 ≪ R2，取 R1=1 kΩ', 22, colour=INK2))
    parts.append(text(74, 358, '⑤ 则 R2 ≈ 18.4 kΩ，取 18 kΩ', 22, colour=INK2))
    parts.append(f'<line x1="80" y1="386" x2="450" y2="386" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(74, 428, 'R1 的下限由放电管电流定', 22, colour=AMBER, weight='700'))
    parts.append(box(520, 130, 430, 330, fill=PAPER))
    parts.append(text(544, 172, '回算：交付前的最后一步', 24, colour=GREEN, weight='700'))
    parts.append(text(544, 218, '实际频率', 22, colour=INK2))
    parts.append(text(926, 220, '38.9 kHz', 28, colour=GREEN, anchor='end', weight='700'))
    parts.append(text(544, 266, '实际占空比', 22, colour=INK2))
    parts.append(text(926, 268, '51.4%', 28, colour=GREEN, anchor='end', weight='700'))
    parts.append(f'<line x1="550" y1="296" x2="920" y2="296" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(544, 338, '偏差能不能收？', 24, colour=BLUE, weight='700'))
    parts.append(text(544, 378, '接收头带宽 ±2 kHz 级', 22, colour=INK2))
    parts.append(text(544, 414, '对占空比更不敏感', 22, colour=INK2))
    parts.append(text(544, 450, '所以遥控器敢用 RC 振荡器', 22, colour=AMBER, weight='700'))
    parts.append(box(50, 486, 900, 130, fill=PAPER))
    parts.append(text(76, 528, '超窗了怎么办：18 kΩ 换 16.9 kΩ+1.5 kΩ 串联，', 24,
                      colour=INK, weight='700'))
    parts.append(text(76, 564, '或者上一只多圈电位器修调。', 24, colour=INK, weight='700'))
    parts.append(text(76, 600, '式子给的是起点，E 系列与回算才是落地的两道手续。', 22, colour=INK2))
    return parts


def duty_cycle_fifty():
    parts = [header('想要准 50%：三条路与两个极端',
                    '标准接法充电走 R1+R2、放电只走 R2，占空比数学上永远 >50%。')]
    rows = [
        ('① 二极管抄近路', 'R2 两端并一只二极管，充电只走 R1、放电走 R2',
         '取 R1=R2 即 50%；代价是约 0.6 V 正向压降缩窄摆幅', 146, GREEN),
        ('② 单电阻回授', '去掉 R1，用 R 从 OUT 直接给 C 充放电',
         '充放时间常数天然相等；双极版高电平低 1.4 V 是隐患', 254, BLUE),
        ('③ 干脆换拓扑', '高一倍频率振荡，再 D 触发器二分频',
         '占空比由结构保证，与 RC 无关', 362, AMBER),
    ]
    for label, how, cost, y, colour in rows:
        parts.append(box(50, y, 900, 96, fill=PAPER, stroke=colour))
        parts.append(text(74, y + 38, label, 26, colour=colour, weight='700'))
        parts.append(text(300, y + 38, how, 22, colour=INK))
        parts.append(text(300, y + 76, cost, 22, colour=INK2))
    parts.append(box(50, 478, 900, 150, fill=PAPER, stroke=RED))
    parts.append(text(74, 520, '两个极端的代价是同一条教训', 26, colour=RED, weight='700'))
    parts.append(text(74, 562, '逼近 100%：R2 顶着放电管电流下限、R1 受漏电流上限，99% 已是实用极限', 22,
                      colour=INK2))
    parts.append(text(74, 598, '逼近 50%：R1=100 Ω、12 V 时峰值 120 mA 直灌放电管，芯片发热、频率漂移', 22,
                      colour=INK2))
    return parts


def shoot_through_ledger():
    parts = [header('受控 AB 偏置，不等于异常贯通',
                    '正常负载与故障回路分别建模；短路电阻仅为量级示意。')]
    parts.append(box(50, 130, 430, 300, fill=PAPER, stroke=GREEN))
    parts.append(text(74, 172, '正常半周：轮流值班', 24, colour=GREEN, weight='700'))
    parts.append(text(74, 214, '8Ω 负载、±12V，理想峰值 12V', 22, colour=INK2))
    parts.append(text(74, 258, '峰值电流', 22, colour=INK2))
    parts.append(text(456, 260, '1.5A', 28, colour=GREEN, anchor='end', weight='700'))
    parts.append(text(74, 304, '输出功率', 22, colour=INK2))
    parts.append(text(456, 306, '9W', 28, colour=GREEN, anchor='end', weight='700'))
    parts.append(text(74, 350, 'B 类效率上限', 22, colour=INK2))
    parts.append(text(456, 352, '78.5%', 28, colour=GREEN, anchor='end', weight='700'))
    parts.append(text(74, 408, '电流只流过一只管子与负载', 22, colour=INK2))
    parts.append(box(520, 130, 430, 300, fill=PAPER, stroke=RED))
    parts.append(text(544, 172, '异常贯通：回路假设 1 Ω', 24, colour=RED, weight='700'))
    parts.append(text(544, 214, '+12V 经 Q1→Q2→−12V 直接短路', 22, colour=INK2))
    parts.append(text(544, 258, '假定两管各分担 0.5 Ω', 22, colour=INK2))
    parts.append(text(544, 304, '短路电流', 22, colour=INK2))
    parts.append(text(926, 306, '24A', 28, colour=RED, anchor='end', weight='700'))
    parts.append(text(544, 350, '每管示意功耗', 22, colour=INK2))
    parts.append(text(926, 352, '288W', 28, colour=RED, anchor='end', weight='700'))
    parts.append(text(544, 408, '偏置错、时序错、上电瞬间都会触发', 22, colour=INK2))
    parts.append(arrow(486, 280, 514, 280, colour=RED))
    parts.append(box(50, 456, 900, 170, fill=PAPER))
    parts.append(text(76, 498, '总计 24 V × 24 A = 576 W；若均分，每管 288 W。', 26,
                      colour=RED, weight='700'))
    parts.append(text(76, 540, '实际电流按驱动、器件特性与保护计算；用 SOA 校核持续时间。', 22,
                      colour=INK2))
    parts.append(text(76, 582, 'AB 允许受控静态重叠；防的是偏置过大与热失控。', 24,
                      colour=GREEN, weight='700'))
    return parts


def ab_bias_thermal():
    parts = [header('AB 类偏置怎么钉住：热耦合与散热器两笔账',
                    '偏置不是调一次就完事；它必须跟着功率管的温度自己收紧。')]
    parts.append(box(50, 130, 430, 330, fill=PAPER))
    parts.append(text(74, 172, '偏置账：可调电池 + 热耦合', 24, colour=BLUE, weight='700'))
    parts.append(text(74, 212, '一只晶体管配两个电阻', 22, colour=INK2))
    parts.append(text(74, 320, '基极间偏置', 22, colour=INK2))
    parts.append(text(74, 248, '两只 0.6 V 结加射极压降', 22, colour=INK2))
    parts.append(text(456, 320, '约 1.213V', 28, colour=BLUE, anchor='end', weight='700'))
    parts.append(text(74, 284, '20 mA；每管射极串 0.33 Ω', 22, colour=INK2))
    parts.append(f'<line x1="80" y1="348" x2="450" y2="348" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(74, 384, '倍增管贴在功率管散热器上', 22, colour=INK2))
    parts.append(text(74, 418, '单结温度系数', 22, colour=INK2))
    parts.append(text(456, 420, '−2mV/℃', 28, colour=GREEN, anchor='end', weight='700'))
    parts.append(text(74, 452, '功率管一热，偏置自动收紧', 22, colour=GREEN, weight='700'))
    parts.append(box(520, 130, 430, 330, fill=PAPER))
    parts.append(text(544, 172, '散热账：按结温倒推热阻', 24, colour=RED, weight='700'))
    parts.append(text(544, 214, '理想 B 类：每管最大平均耗散', 22, colour=INK2))
    parts.append(text(544, 252, '±12 V、8 Ω 时', 22, colour=INK2))
    parts.append(text(926, 254, '1.824W', 28, colour=AMBER, anchor='end', weight='700'))
    parts.append(text(544, 292, '教学总热阻取 65℃/W', 22, colour=INK2))
    parts.append(text(544, 330, '温升 118.6℃，环境 25℃', 22, colour=INK2))
    parts.append(text(926, 356, '143.6℃', 28, colour=RED, anchor='end', weight='700'))
    parts.append(f'<line x1="550" y1="368" x2="920" y2="368" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(544, 388, '允许结温 105℃、环境 40℃', 22, colour=INK2))
    parts.append(text(544, 424, '总热阻须 ≤35.6℃/W', 26, colour=GREEN, weight='700'))
    parts.append(text(544, 452, '还须扣结壳及界面热阻', 22, colour=GREEN))
    parts.append(box(50, 486, 900, 130, fill=PAPER))
    parts.append(text(76, 528, '热耦合与射极反馈共同限制静态电流；冷态和热态都须实测。', 24,
                      colour=RED, weight='700'))
    parts.append(text(76, 566, '静态电流量级是经验值：中小功率每管 20~50mA，让交接处轻微重叠导通。', 22,
                      colour=INK2))
    parts.append(text(76, 602, '射极各串 0.22~0.47Ω 提供反馈和电流检测，不能单独保护短路。',
                      22, colour=INK2))
    return parts


def ldo_four_accounts():
    parts = [header('7805 的四种死法，是四本不同的账',
                    '同一颗芯片，热、纹波、稳定性、上电各有各的判据与解法。')]
    accounts = [
        ('① 热账', 'P=(VIN−5V)×I；12V→5V@300mA = 2.1W', '无散热片必热关断', 134, RED),
        ('② 纹波账', '输入谷值必须 ≥ VOUT+VDROP', '100Hz 纹波跌破压差线就下垂', 222, AMBER),
        ('③ 稳定性账', 'AMS1117 的环路补偿依赖输出电容 ESR', '出窗口就振荡', 310, BLUE),
        ('④ 上电账', '大压差 + 快上电，调整管未及时响应', '过冲 >10% 持续 µs 级', 398, GREEN),
    ]
    for label, how, judge, y, colour in accounts:
        parts.append(box(50, y, 900, 78, fill=PAPER, stroke=colour))
        parts.append(text(74, y + 34, label, 26, colour=colour, weight='700'))
        parts.append(text(240, y + 34, how, 22, colour=INK))
        parts.append(text(240, y + 66, judge, 22, colour=INK2))
    parts.append(box(50, 492, 900, 136, fill=PAPER, stroke=GREEN))
    parts.append(text(74, 528, '升级路径与经验分界', 26, colour=GREEN, weight='700'))
    parts.append(text(74, 566, '降输入：Buck 到 7.5V，功耗减 2/3；换 DCDC：效率 85%–95%，2.1W 变 0.3W',
                      22, colour=INK2))
    parts.append(text(74, 602, '压差×电流 >1W 就别让线性稳压硬扛；<0.3W 时线性全面占优', 22,
                      colour=RED, weight='700'))
    return parts


def two_stage_margin():
    parts = [header('两级放大器交付前对账：四项指标各剩多少余量',
                    '四项全过，但余量不是平均分配的——最薄的两项决定这版能不能发。')]
    rows = [
        ('电压增益', '≥60 dB（1000 倍）', '1037 倍 = 60.3 dB', '+0.3 dB', 150, RED),
        ('输入电阻', '≥10 kΩ', '13.0 k ∥ 110 k = 11.6 kΩ', '过线', 238, GREEN),
        ('输出电阻', '≤100 Ω', '射随器给到约 29 Ω', '富余', 326, GREEN),
        ('带宽', '≥100 kHz', '两极点叠加约 110 kHz', '刚过线', 414, RED),
    ]
    for label, spec, actual, margin, y, colour in rows:
        parts.append(box(50, y, 900, 78, fill=PAPER, stroke=colour))
        parts.append(text(74, y + 34, label, 26, colour=INK, weight='700'))
        parts.append(text(240, y + 34, spec, 22, colour=INK2))
        parts.append(text(470, y + 34, actual, 22, colour=INK))
        parts.append(text(926, y + 36, margin, 26, colour=colour, anchor='end', weight='700'))
    parts.append(box(50, 508, 900, 120, fill=PAPER))
    parts.append(text(76, 550, '最薄的是增益与带宽：β 一漂移，两项可能齐破。', 26,
                      colour=RED, weight='700'))
    parts.append(text(76, 588, '源阻真是 10 kΩ 且没有偏置电阻分流时，第一极点掉到约 75 kHz——', 22,
                      colour=INK2))
    parts.append(text(76, 620, '要么第一级改 cascode 拆掉米勒桥，要么降第一级增益、分给第二级。', 22,
                      colour=INK2))
    return parts


SCENES = {
    'ch10-astable-reverse-design': {
        'draw': astable_reverse_design, 'title': '按 38kHz 目标反推 555 元件值',
        'anchor': '10.4', 'chapter': 10, 'source': 'docs/p1-11-ch10.md',
        'alt': '手绘 555 反推两栏：左栏列五步，目标 38 千赫载波占空比约 50%，取电容 1 纳法 COG，解总电阻 R1 加 2R2 约 37.9 千欧，近 50% 要求 R1 远小于 R2 故取 R1 等于 1 千欧，则 R2 约 18.4 千欧取 18 千欧，并注明 R1 的下限由放电管电流定；右栏回算实际频率 38.9 千赫、实际占空比 51.4%，并写接收头带宽 ±2 千赫级、对占空比更不敏感，所以遥控器敢用 RC 振荡器。底部写超窗了把 18 千欧换 16.9 千欧加 1.5 千欧串联，或上一只多圈电位器修调，式子给的是起点、E 系列与回算才是落地手续。',
    },
    'ch10-duty-fifty-paths': {
        'draw': duty_cycle_fifty, 'title': '准 50% 占空比的三条路与两个极端',
        'anchor': '10.4', 'chapter': 10, 'source': 'docs/p1-11-ch10.md',
        'alt': '手绘三行对照：第一行二极管抄近路，R2 两端并一只二极管充电只走 R1、放电走 R2，取 R1 等于 R2 即 50%，代价是约 0.6 伏正向压降缩窄摆幅；第二行单电阻回授，去掉 R1 用 R 从输出脚直接给电容充放电，充放时间常数天然相等，双极版高电平低 1.4 伏是隐患；第三行干脆换拓扑，高一倍频率振荡再 D 触发器二分频，占空比由结构保证与 RC 无关。底部红框写两个极端的代价是同一条教训：逼近 100% 时 R2 顶着放电管电流下限、R1 受漏电流上限，99% 已是实用极限；逼近 50% 时 R1 等于 100 欧、12 伏时峰值 120 毫安直灌放电管，芯片发热、频率漂移。',
    },
    'ch05-shoot-through-ledger': {
        'draw': shoot_through_ledger, 'title': '推挽正常半周与直通的电流功率对账',
        'anchor': '5.6', 'chapter': 5, 'source': 'docs/p1-06-ch5.md',
        'alt': '正常理想 B 类输出峰值一点五安、负载九瓦；故障假设二十四伏跨在一欧回路上，二十四安，总功率五百七十六瓦。若两管均分，每管二百八十八瓦，实际按驱动、保护和 SOA 核查。AB 类允许受控静态重叠。',
    },
    'ch05-ab-bias-thermal': {
        'draw': ab_bias_thermal, 'title': 'AB 类偏置的热耦合与散热器两笔账',
        'anchor': '5.6', 'chapter': 5, 'source': 'docs/p1-06-ch5.md',
        'alt': '单结互补射随器的偏置为两只零点六伏结压降加射极电阻压降，二十毫安、两只零点三三欧合计约一点二一三伏。正负十二伏、八欧理想 B 类每管最大耗散一点八二四瓦；热阻六十五摄氏度每瓦、环境二十五度，结温约一百四十三点六度。',
    },
    'ch09-ldo-four-accounts': {
        'draw': ldo_four_accounts, 'title': '7805 四种死法对应的四本账',
        'anchor': '9.4', 'chapter': 9, 'source': 'docs/p1-10-ch9.md',
        'alt': '手绘四行账：热账写功耗等于输入减 5 伏再乘电流，12 伏降 5 伏带 300 毫安是 2.1 瓦，无散热片必热关断；纹波账写输入谷值必须大于等于输出加压差，100 赫兹纹波跌破压差线就下垂；稳定性账写 AMS1117 的环路补偿依赖输出电容 ESR，出窗口就振荡；上电账写大压差加快上电时调整管未及时响应，过冲超过 10% 且持续微秒级。底部一行写升级路径与经验分界：降输入 Buck 到 7.5 伏功耗减三分之二，换 DCDC 效率 85% 到 95%、2.1 瓦变 0.3 瓦；压差乘电流大于 1 瓦就别让线性稳压硬扛，小于 0.3 瓦时线性全面占优。',
    },
    'ch11-two-stage-margin': {
        'draw': two_stage_margin, 'title': '两级放大器四项指标的余量对账',
        'anchor': '11.11', 'chapter': 11, 'source': 'docs/p2-01-ch11.md',
        'alt': '手绘四行对账表：电压增益要求大于等于 60 分贝即 1000 倍，实得 1037 倍即 60.3 分贝，余量只有正 0.3 分贝；输入电阻要求大于等于 10 千欧，实得 13.0 千欧并联 110 千欧等于 11.6 千欧，余量正 1.6 千欧；输出电阻要求小于等于 100 欧，射随器给到约 29 欧，富余；带宽要求大于等于 100 千赫，两极点叠加约 110 千赫，刚过线。底部写最薄的是增益与带宽，β 一漂移两项可能齐破；源阻真是 10 千欧且没有偏置电阻分流时第一极点掉到约 75 千赫，要么第一级改 cascode 拆掉米勒桥，要么降第一级增益分给第二级。',
    },
}

# Use source-bound reference/regulator models for historical batch rebuilds.
from scripts.visuals.scenes.ch09_reference_figures import SCENES as _ch09_corrected

from scripts.visuals.scenes.ch10_reference_figures import SCENES as _ch10_corrected
for _aid in ['ch10-astable-reverse-design', 'ch10-duty-fifty-paths']:
    SCENES[_aid] = _ch10_corrected[_aid]
SCENES['ch09-ldo-four-accounts'] = _ch09_corrected['ch09-ldo-four-accounts']

# Corrected chapter 11 model and visual contract.
from scripts.visuals.scenes.ch11_reference_figures import SCENES as _ch11_corrected
SCENES['ch11-two-stage-margin'] = _ch11_corrected['ch11-two-stage-margin']
