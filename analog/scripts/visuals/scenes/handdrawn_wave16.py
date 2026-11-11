"""Wave 16 手绘草图：五处零图或仅一图的长而密小节。

每张图的数字只取对应 anchor 小节：ch11 取 11.7 四拍与增益/CMRR 算账，
ch2 取 2.12 桥堆四数、结温账与桥式均流，ch4 取 4.5 热阻链与四种测量自欺，
ch1 取 1.5 的 Q 定义、中波/FM 对比与峰值阻抗，
ch2 取 2.13 五个二极管故障案例压成的三步顺序。
"""
from __future__ import annotations

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK, INK2, PAPER, RED, RULE, arrow, box, header, text,
)


def _down_arrow(x: float, y1: float, y2: float, colour: str = INK2) -> list[str]:
    """竖直向下的箭头：arrow() 只画右向，向下须手写。"""
    return [
        f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2 - 11}" '
        f'stroke="{colour}" stroke-width="2.5" stroke-linecap="round"/>',
        f'<polygon points="{x},{y2} {x - 6},{y2 - 12} {x + 6},{y2 - 12}" fill="{colour}"/>',
    ]


def diffpair_four_beats():
    parts = [header('差分对的四拍：尾电流只准重新分配',
                    '尾电流 1 mA、集电极电阻 10 kΩ。共模想同时多要，挪不动；差模一多一少，正好挪得动。')]

    beats = [
        ('① 两边同升（共模）', '尾电流锁死在 1 mA，谁也多拿不走', '输出差 = 0', BLUE),
        ('② 一升一降（差模）', '各 ±10 mV，总量仍是 1 mA，只在两管间重分', '≈ 2ΔI·R_C', GREEN),
        ('③ 尾节点自举', 'Q1 想抬、Q2 想压，正好抵消，R_tail 上没有交流', '对差模隐身', INK),
        ('④ 共模的真实泄漏', 'R_tail 有限、两管不可能完全匹配，泄漏从这进', '失配 1% → 60 dB', AMBER),
    ]
    y = 126
    for label, detail, value, colour in beats:
        parts.append(box(50, y, 900, 84, fill=PAPER, stroke=colour))
        parts.append(text(76, y + 38, label, 24, colour=colour, weight='700'))
        parts.append(text(76, y + 70, detail, 22, colour=INK2))
        parts.append(text(926, y + 54, value, 22, colour=colour, anchor='end', weight='700'))
        y += 98

    parts.append(box(50, 518, 900, 156, fill=PAPER, stroke=RED))
    parts.append(text(76, 556, '算一笔（单端输出）', 24, colour=RED, weight='700'))
    parts.append(text(76, 594, 'I_tail = 1 mA、R_C = 10 kΩ、r_e = 26 mV / 0.5 mA = 52 Ω', 22, colour=INK2))
    parts.append(text(76, 626, 'A_dm = 10 kΩ / 104 Ω ≈ 96，约 40 dB', 22, colour=INK2))
    parts.append(text(76, 658, 'R_tail = 1 MΩ → A_cm ≈ 0.005 → CMRR ≈ 86 dB；提到 10 MΩ 再涨 20 dB',
                      22, colour=INK2))
    return parts


def bridge_junction_ledger():
    parts = [header('桥堆与整流管：四个数，一本热账',
                    '单管连续 1 A：结温 122 °C，余量 3 °C；桥堆四管损耗另算。')]

    parts.append(box(50, 130, 430, 300, fill=PAPER, stroke=BLUE))
    parts.append(text(74, 170, '桥堆看四个数', 24, colour=BLUE, weight='700'))
    parts.append(text(74, 212, 'V_RRM：至少 2 倍峰值反压', 22, colour=INK2))
    parts.append(text(74, 244, '230 Vrms → 325 V；选 800~1000 V', 22, colour=INK2))
    parts.append(text(74, 290, 'I_F(AV)：按壳温降额，常见标 100 °C', 22, colour=INK2))
    parts.append(text(74, 336, 'I_FSM：8.3 ms 半正弦的单次值', 22, colour=INK2))
    parts.append(text(74, 382, '热阻：按封装整体看，不能乘四', 22, colour=INK2))
    parts.append(text(74, 414, '四只封一起，互相加热', 22, colour=AMBER, weight='700'))

    parts.append(box(520, 130, 430, 300, fill=PAPER, stroke=GREEN))
    parts.append(text(544, 170, '单管：R_θJA = 80 °C/W', 24, colour=GREEN, weight='700'))
    parts.append(text(544, 212, 'P = 0.9 V × 1 A = 0.9 W', 22, colour=INK2))
    parts.append(text(544, 244, 'T_j = 50 + 0.9 × 80', 22, colour=INK2))
    parts.append(text(926, 246, '122 °C', 24, colour=RED, anchor='end', weight='700'))
    parts.append(text(544, 290, '降到 0.6 A：P = 0.54 W', 22, colour=INK2))
    parts.append(text(926, 292, '93 °C', 24, colour=GREEN, anchor='end', weight='700'))
    parts.append(text(544, 336, '换 V_F = 0.5 V 肖特基', 22, colour=INK2))
    parts.append(text(926, 338, '90 °C', 24, colour=GREEN, anchor='end', weight='700'))
    parts.append(f'<line x1="550" y1="360" x2="920" y2="360" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(544, 400, '环境 60 °C、仍 1 A', 22, colour=INK2))
    parts.append(text(926, 402, '132 °C 超限', 24, colour=RED, anchor='end', weight='700'))

    parts.append(box(50, 450, 900, 104, fill=PAPER, stroke=AMBER))
    parts.append(text(76, 488, '桥式里每只管子的平均电流只有负载的一半', 24, colour=AMBER, weight='700'))
    parts.append(text(76, 526, '1 A 负载、每只平均 0.5 A；四只各 0.45 W，总损耗为 1.8 W',
                      22, colour=INK2))

    parts.append(box(50, 574, 900, 100, fill=PAPER, stroke=RED))
    parts.append(text(76, 612, '别把单只管子的热阻套到桥堆上', 24, colour=RED, weight='700'))
    parts.append(text(76, 650, '25 °C 下标称的 1 A，装进封闭机箱不成立；要查降额曲线，或加散热片',
                      22, colour=INK2))
    return parts


def thermal_chain_ledger():
    parts = [header('热失效：先把热阻链的账算清',
                    '导通 0.75 W 加开关 3.5 W 共 4.25 W。靠 PCB 敷铜散热，温升算出来 255 °C。')]

    parts.append(box(50, 126, 900, 132, fill=PAPER, stroke=RED))
    parts.append(text(76, 164, 'T_J = T_A + P × (R_θJC + R_θCS + R_θSA)', 24, colour=RED, weight='700'))
    parts.append(text(76, 202, '导通 0.75 W 加开关 3.5 W，共', 22, colour=INK2))
    parts.append(text(926, 204, '4.25 W', 26, colour=RED, anchor='end', weight='700'))
    parts.append(text(76, 238, '只靠 PCB 敷铜，R_θJA 按 60 °C/W 估 → 温升 255 °C，150 或 175 °C 都挡不住',
                      22, colour=INK2))

    parts.append(box(50, 272, 900, 86, fill=PAPER, stroke=BLUE))
    parts.append(text(76, 310, '两条降额示例（按产品要求另定）', 24, colour=BLUE, weight='700'))
    parts.append(text(76, 344, '持续结温压在 125 °C 以下；V_DS 峰值压在额定的 80% 以内', 22, colour=INK2))

    parts.append(box(50, 372, 900, 150, fill=PAPER, stroke=AMBER))
    parts.append(text(76, 410, '测量环节也会骗你：四个自欺现场', 24, colour=AMBER, weight='700'))
    parts.append(text(76, 446, '20 mm 探头地线环路可能引入振铃，先缩短回路后复测', 22, colour=INK2))
    parts.append(text(76, 478, '电流探头与电压通道的延迟差，让损耗积分偏大或偏小', 22, colour=INK2))
    parts.append(text(76, 510, 'R_DS(on) 要通已知电流四线测；误导通看 V_GS，耐压看 V_DS', 22, colour=INK2))

    parts.append(box(50, 536, 900, 72, fill=PAPER, stroke=GREEN))
    parts.append(text(76, 578, '孤立短脉冲用 Z_θJC(t)；重复脉冲还须累计热量，边界条件保持一致',
                      22, colour=GREEN, weight='700'))

    parts.append(box(50, 622, 900, 62, fill=PAPER))
    parts.append(text(76, 660, '雪崩不是免费保险：100 nH × 0.5 A/ns 就是 50 V，直接叠在母线上',
                      22, colour=INK, weight='700'))
    return parts


def q_selectivity_map():
    parts = [header('Q 是挑频率的锐度，不是越高越好',
                    'Q 高不等于更好：选台要尖，电源滤波要钝，两头差两个数量级。')]

    parts.append(box(50, 126, 900, 88, fill=PAPER, stroke=BLUE))
    parts.append(text(76, 164, 'Q = f0 / BW，BW 是半功率带宽', 24, colour=BLUE, weight='700'))
    parts.append(text(76, 196, '峰又尖又窄就是高 Q；峰钝就是低 Q。Q 还能实测：扫频找 f0 与两个 −3 dB 点',
                      22, colour=INK2))

    parts.append(box(50, 228, 430, 272, fill=PAPER, stroke=GREEN))
    parts.append(text(74, 268, '选台要多窄', 24, colour=GREEN, weight='700'))
    parts.append(text(74, 306, '中波：载波 1 MHz、带宽 5 kHz', 22, colour=INK2))
    parts.append(text(456, 340, '→ Q = 200', 24, colour=GREEN, anchor='end', weight='700'))
    parts.append(text(74, 382, 'FM：载波 100 MHz、带宽 150 kHz', 22, colour=INK2))
    parts.append(text(456, 416, '→ Q ≈ 667', 24, colour=GREEN, anchor='end', weight='700'))
    parts.append(f'<line x1="82" y1="438" x2="448" y2="438" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(74, 474, '频率越高，高 Q 越难做', 22, colour=AMBER, weight='700'))

    parts.append(box(520, 228, 430, 272, fill=PAPER, stroke=RED))
    parts.append(text(544, 268, '峰值阻抗也是有限的', 24, colour=RED, weight='700'))
    parts.append(text(544, 306, 'L = 10 µH、C = 100 pF、r = 1 Ω', 22, colour=INK2))
    parts.append(text(544, 348, '谐振频率', 22, colour=INK2))
    parts.append(text(926, 350, '5.0 MHz', 24, colour=INK, anchor='end', weight='700'))
    parts.append(text(544, 390, '峰值阻抗', 22, colour=INK2))
    parts.append(text(926, 392, '100 kΩ', 24, colour=RED, anchor='end', weight='700'))
    parts.append(f'<line x1="550" y1="414" x2="920" y2="414" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(544, 448, '理想并联无穷大，实际被 r 压成 L/(rC)', 22, colour=INK2))

    parts.append(box(50, 514, 900, 86, fill=PAPER, stroke=AMBER))
    parts.append(text(76, 552, '谐振网络里谁最差谁定 Q', 24, colour=AMBER, weight='700'))
    parts.append(text(76, 586, '电感的 DCR 与磁芯损耗通常是短板；想提 Q，先修最差的那个元件', 22, colour=INK2))

    parts.append(box(50, 610, 900, 84, fill=PAPER))
    parts.append(text(76, 648, '调谐用可变电容，不用可变电感', 24, colour=INK, weight='700'))
    parts.append(text(76, 680, '电容可做多联同轴、磨损小、Q 高；磁芯旋进旋出，机械寿命与一致性都差',
                      22, colour=INK2))
    return parts


def diode_fault_order():
    parts = [header('二极管排故：先方向，再压降，最后散热',
                    '五个现象，一条顺序：先查方向，再查压降，最后查散热。')]

    parts.append(box(50, 126, 900, 96, fill=PAPER, stroke=RED))
    parts.append(text(76, 166, '① 先查方向：是不是接反、该导通时没导通', 24, colour=RED, weight='700'))
    parts.append(text(76, 202, '纹波频率从 100 Hz 变成 50 Hz → 桥臂里一只开路', 22, colour=INK2))

    parts.extend(_down_arrow(500, 222, 250, RED))

    parts.append(box(50, 250, 900, 96, fill=PAPER, stroke=AMBER))
    parts.append(text(76, 290, '② 再查压降：是不是把 0.7 V 用错了地方', 24, colour=AMBER, weight='700'))
    parts.append(text(76, 326, 'TVS 的 V_RWM 选低，正常信号的峰值就让它微导通', 22, colour=INK2))

    parts.extend(_down_arrow(500, 346, 374, AMBER))

    parts.append(box(50, 374, 900, 96, fill=PAPER, stroke=GREEN))
    parts.append(text(76, 414, '③ 最后查散热：结温有没有超', 24, colour=GREEN, weight='700'))
    parts.append(text(76, 450, '纹波 2 V 变 4 V、电容温热 → ESR 升高，纹波电流在它上面发热',
                      22, colour=INK2))

    parts.append(box(50, 494, 900, 88, fill=PAPER, stroke=BLUE))
    parts.append(text(76, 532, '顺序不能反', 24, colour=BLUE, weight='700'))
    parts.append(text(76, 566, '方向错了，后面量什么都是错的；压降错了，散热算得再准也救不回来',
                      22, colour=INK2))

    parts.append(box(50, 598, 900, 86, fill=PAPER))
    parts.append(text(76, 636, '三件事按顺序走，大多数故障不用猜', 24, colour=INK, weight='700'))
    parts.append(text(76, 670, '每个现象都配一条一分钟验证，比凭经验换件快得多', 22, colour=INK2))
    return parts


SCENES = {
    'ch11-diffpair-four-beats': {
        'draw': diffpair_four_beats, 'title': '差分对的四拍：尾电流只准重新分配',
        'anchor': '11.7', 'chapter': 11, 'source': 'docs/p2-01-ch11.md',
        'alt': '手绘差分对四拍。四行横框自上而下：第一行两边同升是共模，尾电流锁死在 1 毫安，'
               '谁也多拿不走，输出差为零；第二行一升一降是差模，各正负 10 毫伏，'
               '总量仍是 1 毫安，只在两管之间重新分配，输出差约等于 2 倍电流增量乘集电极电阻；'
               '第三行尾节点自举，一只管子想抬、另一只想压，正好抵消，尾电流源上没有交流，对差模隐身；'
               '第四行共模的真实泄漏，尾电流源有限、两管不可能完全匹配，失配 1% 就把共模抑制比拉到 60 分贝。'
               '底部红框算账：尾电流 1 毫安、集电极电阻 10 千欧、发射极小信号电阻 26 毫伏除 0.5 毫安得 52 欧，'
               '差模增益 10 千欧除 104 欧约 96、约 40 分贝；'
               '尾电流源 1 兆欧时共模增益约 0.005，共模抑制比约 86 分贝，提到 10 兆欧再涨 20 分贝。',
    },
    'ch02-bridge-junction-ledger': {
        'draw': bridge_junction_ledger, 'title': '桥堆与整流管的四个数与结温账',
        'anchor': '2.12', 'chapter': 2, 'source': 'docs/p1-03-ch2.md',
        'alt': '手绘桥堆两栏加热账。左蓝框桥堆看四个数：反向耐压至少 2 倍峰值反压，'
               '市电 230 伏有效值峰值 325 伏，所以按两倍余量选 800 到 1000 伏；平均电流要按壳温降额，常见标 100 摄氏度；'
               '浪涌电流是 8.3 毫秒半正弦的单次值；热阻要按封装整体看，不能拿单只乘四，四只封在一起互相加热。'
               '右绿框单管连续导通的结温账，热阻按 80 摄氏度每瓦：功耗 0.9 伏乘 1 安得 0.9 瓦，结温 50 加 0.9 乘 80 得 122 摄氏度；'
               '降到 0.6 安功耗 0.54 瓦，结温 93 摄氏度；换 0.5 伏肖特基，90 摄氏度；'
               '环境升到 60 摄氏度仍 1 安，132 摄氏度已经超限。'
               '下方琥珀框写桥式里每只管子的平均电流只有负载的一半：1 安负载每只导通半周、平均 0.5 安，'
               '四只各 0.45 瓦、总损耗为 1.8 瓦。底部红框写别把单只管子的热阻套到桥堆上，'
               '25 摄氏度下标称的 1 安装进封闭机箱不成立。',
    },
    'ch04-thermal-chain-ledger': {
        'draw': thermal_chain_ledger, 'title': '热失效的热阻链与四种测量自欺',
        'anchor': '4.5', 'chapter': 4, 'source': 'docs/p1-05-ch4.md',
        'alt': '手绘热失效账。顶部红框写结温等于环境温度加功耗乘三级热阻之和；'
               '导通 0.75 瓦加开关 3.5 瓦共 4.25 瓦，只靠电路板敷铜、热阻按 60 摄氏度每瓦估，'
               '温升 255 摄氏度，150 或 175 摄氏度的额定都挡不住。'
               '蓝框两条降额示例：结温 125 摄氏度以下、漏源峰值在额定 80% 以内，具体按产品要求另定。'
               '琥珀框列测量边界：20 毫米探头地线环路可能引入振铃，先缩短后复测；'
               '电流探头与电压通道的延迟差让损耗积分偏大或偏小；导通电阻要通已知电流四线测；'
               '误导通看栅源电压与热态阈值，耐压看漏源峰值。'
               '绿框写孤立短脉冲看瞬态热阻，重复脉冲还须累计热量，保持相同热边界条件。'
               '底部写雪崩不是免费保险：100 纳亨乘 0.5 安每纳秒就是 50 伏，直接叠在母线上。',
    },
    'ch01-q-selectivity-map': {
        'draw': q_selectivity_map, 'title': 'Q 是挑频率的锐度，不是越高越好',
        'anchor': '1.5', 'chapter': 1, 'source': 'docs/p1-02-ch1.md',
        'alt': '手绘品质因数两栏。顶部蓝框给定义：Q 等于谐振频率除以半功率带宽，峰又尖又窄是高 Q；'
               'Q 还能实测，扫频找谐振峰与两个下降 3 分贝的点。'
               '左绿框按给定半功率带宽计算：中波载波 1 兆赫、带宽 5 千赫，Q 等于 200；'
               '调频载波 100 兆赫、带宽 150 千赫，Q 约 667；频率越高做出高 Q 越难，损耗与寄生随频率一起涨。'
               '右红框峰值阻抗也是有限的：电感 10 微亨、电容 100 皮法、电阻 1 欧，谐振频率 5.0 兆赫，'
               '峰值阻抗 100 千欧；理想并联回路阻抗无穷大，实际被电感电阻压成电感除电阻乘电容。'
               '下方琥珀框写谐振网络里谁最差谁定 Q，电感的直流电阻与磁芯损耗通常是短板。'
               '底部写调谐用可变电容不用可变电感：电容可做多联同轴、磨损小、Q 高。',
    },
    'ch02-diode-fault-order': {
        'draw': diode_fault_order, 'title': '二极管排故的三步顺序',
        'anchor': '2.13', 'chapter': 2, 'source': 'docs/p1-03-ch2.md',
        'alt': '手绘二极管排故三步，三个框之间用实心向下箭头相连。'
               '第一步红框先查方向：是不是接反、是不是该导通时没导通，'
               '现象是纹波频率从 100 赫兹变成 50 赫兹，说明桥臂里一只开路。'
               '第二步琥珀框再查压降：是不是把 0.7 伏用错了地方，'
               '比如瞬态抑制二极管的关断电压选低，正常信号的峰值就让它微导通。'
               '第三步绿框最后查散热：结温有没有超，'
               '现象是纹波从 2 伏变 4 伏、电容温热，因为等效串联电阻升高、纹波电流在它上面发热。'
               '下方蓝框写顺序不能反：方向错了后面量什么都是错的，压降错了散热算得再准也救不回来。'
               '底部写三件事按顺序走，大多数故障不用猜。',
    },
}

# Corrected chapter 11 model and visual contract.
from scripts.visuals.scenes.ch11_reference_figures import SCENES as _ch11_corrected
SCENES['ch11-diffpair-four-beats'] = _ch11_corrected['ch11-diffpair-four-beats']
