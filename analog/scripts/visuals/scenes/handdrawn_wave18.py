"""Wave 18 手绘草图：555 的故障图谱与门限账，共射级的摆幅预算。

三张图的数字只取对应 anchor 小节：
ch10 取 10.3 的五站故障图谱，ch10 取 10.1 的门限与占空比账，
ch3 取 3.9 的余量-摆幅-削波方向。
"""
from __future__ import annotations

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK, INK2, PAPER, RED, RULE, box, header, text,
)


def _row(y, key, symptom, verdict):
    out = [f'<line x1="82" y1="{y - 30}" x2="918" y2="{y - 30}" stroke="{RULE}" stroke-width="1.5"/>']
    out.append(text(76, y, key, 22, colour=BLUE, weight='700'))
    out.append(text(120, y, symptom, 22, colour=INK))
    out.append(text(566, y, verdict, 22, colour=INK2))
    return out


def threes_five_fault_tree():
    parts = [header('555 的故障按波形分五站，别按猜测分',
                    '5 脚悬空会拽着两条门限一起漂；标准做法是接 10 nF 到地。')]

    parts.append(box(50, 126, 900, 76, fill=PAPER, stroke=BLUE))
    parts.append(text(76, 160, '5 脚（CTRL）直接接在内部 2/3 Vcc 的抽头上', 24, colour=BLUE, weight='700'))
    parts.append(text(76, 190, '悬空等于给高阻抽头接天线，改的正是挡块高度', 22, colour=INK2))

    parts.append(box(50, 216, 900, 312, fill=PAPER, stroke=INK2))
    parts.append(text(76, 252, '现象', 22, colour=INK2, weight='700'))
    parts.append(text(566, 252, '判据与处方', 22, colour=INK2, weight='700'))
    rows = [
        ('①', '输出常高、6 脚电压不动', '放电管没工作：7 脚虚焊、R2 开路'),
        ('②', '频率对、占空比漂', 'R1/R2 变值，或 5 脚电容漏电'),
        ('③', '频率随温度狂漂', '热风一吹变化 >5%：元件介质问题'),
        ('④', '起振迟缓、偶发停振', '电源爬升太慢；4 脚加 RC 延时'),
        ('⑤', '面包板行、焊板上不行', '寄生 2~5 pF 参与定时，按板上实测重算'),
    ]
    for i, (k, s, v) in enumerate(rows):
        parts.extend(_row(292 + i * 46, k, s, v))

    parts.append(box(50, 542, 900, 88, fill=PAPER, stroke=AMBER))
    parts.append(text(76, 578, '先量 5 脚直流电压，应恰好 2/3 Vcc', 24, colour=AMBER, weight='700'))
    parts.append(text(76, 610, '偏离就是外因；指标合格才轮到怀疑芯片', 22, colour=INK2))

    parts.append(box(50, 642, 900, 48, fill=PAPER, stroke=GREEN))
    parts.append(text(76, 672, '处方三件套：就近 100 nF + 10 µF、续流路径独立、走线不进继电器回路',
                      22, colour=GREEN, weight='700'))
    return parts


def threes_five_threshold():
    parts = [header('两条门限就是摆幅的上下限位',
                    '上限 2/3 Vcc、下限 1/3 Vcc；充放路径不对称，占空比恒大于 50%。')]

    parts.append(box(50, 126, 900, 96, fill=PAPER, stroke=BLUE))
    parts.append(text(76, 164, '三只 5 kΩ 串在电源与地之间，抽出两条门限', 24, colour=BLUE, weight='700'))
    parts.append(text(76, 200, '2/3 Vcc 进比较器 A，1/3 Vcc 进比较器 B——这就是 555 这个名字的由来',
                      22, colour=INK2))

    parts.append(box(50, 236, 430, 190, fill=PAPER, stroke=GREEN))
    parts.append(text(74, 276, '撞上限：按住', 24, colour=GREEN, weight='700'))
    parts.append(text(74, 314, '电容升到 2/3 Vcc', 22, colour=INK2))
    parts.append(text(74, 350, '比较器 A 翻转', 22, colour=INK2))
    parts.append(text(74, 386, '触发器复位、放电管导通', 22, colour=INK2))
    parts.append(box(520, 236, 430, 190, fill=PAPER, stroke=RED))
    parts.append(text(544, 276, '落下限：松手', 24, colour=RED, weight='700'))
    parts.append(text(544, 314, '电容降到 1/3 Vcc', 22, colour=INK2))
    parts.append(text(544, 350, '比较器 B 翻转', 22, colour=INK2))
    parts.append(text(544, 386, '触发器置位、放电管截止', 22, colour=INK2))

    parts.append(box(50, 440, 900, 132, fill=PAPER, stroke=AMBER))
    parts.append(text(76, 478, '所以占空比永远大于 50%', 24, colour=AMBER, weight='700'))
    parts.append(text(76, 514, '充电走 R1 + R2，放电只走 R2：进得慢、出得快', 22, colour=INK2))
    parts.append(text(76, 546, 'R1 只出现在充电支路，所以这个比值压不到 50%', 22, colour=INK2))

    parts.append(box(50, 586, 900, 104, fill=PAPER))
    parts.append(text(76, 624, '触发器只锁状态，不产生振荡', 24, colour=INK, weight='700'))
    parts.append(text(76, 660, '秋千自己会停；这一圈摆下去，能量一路向电源讨', 22, colour=INK2))
    return parts


def ce_swing_budget():
    parts = [header('摆幅由更小的那份余量决定',
                    '12 V 供电、Q 点 6 V：上行余量 6 V、下行余量 4 V，近似削波界 8.0 Vpp。')]

    parts.append(box(50, 126, 430, 176, fill=PAPER, stroke=BLUE))
    parts.append(text(74, 166, '先立地基', 24, colour=BLUE, weight='700'))
    parts.append(text(74, 204, 'V_C = 6 V、V_E = 1.8 V', 22, colour=INK2))
    parts.append(text(74, 240, 'V_B ≈ 2.5 V、I_C = 3 mA', 22, colour=INK2))
    parts.append(text(74, 276, 'V_CE ≈ 4.2 V，安静时的 Q 点', 22, colour=INK2))

    parts.append(box(520, 126, 430, 176, fill=PAPER, stroke=GREEN))
    parts.append(text(544, 166, '再数余量', 24, colour=GREEN, weight='700'))
    parts.append(text(544, 204, '向上到 12 V', 22, colour=INK2))
    parts.append(text(926, 206, '6 V', 22, colour=INK, anchor='end', weight='700'))
    parts.append(text(544, 240, '向下到 V_E + 0.2 V', 22, colour=INK2))
    parts.append(text(926, 242, '4 V', 22, colour=INK, anchor='end', weight='700'))
    parts.append(text(544, 276, '取小的那份，来回一趟', 22, colour=INK2))

    parts.append(box(50, 316, 900, 96, fill=PAPER, stroke=AMBER))
    parts.append(text(76, 354, '线性外推削波界 = 2 × min(6 V, 4 V) = 8.0 Vpp', 24, colour=AMBER, weight='700'))
    parts.append(text(76, 388, '增益 230 → 线性估计输入约 35 mVpp；指数非线性会更早出现，失真须另验',
                      22, colour=INK2))

    parts.append(box(50, 426, 900, 146, fill=PAPER, stroke=RED))
    parts.append(text(76, 464, '削波方向就是诊断方向', 24, colour=RED, weight='700'))
    parts.append(text(76, 502, '输出底部削平 = 撞饱和 = Q 点偏高', 22, colour=INK2))
    parts.append(text(926, 504, 'V_E 或 R_C 偏大', 22, colour=RED, anchor='end', weight='700'))
    parts.append(text(76, 540, '输出顶部削平 = 撞截止 = Q 点偏低', 22, colour=INK2))
    parts.append(text(926, 542, '把 V_B 往上挪', 22, colour=RED, anchor='end', weight='700'))

    parts.append(box(50, 586, 900, 104, fill=PAPER))
    parts.append(text(76, 624, 'Q 点偏置的任务，就是把两份余量尽量平分', 24, colour=INK, weight='700'))
    parts.append(text(76, 660, '先站回直流窗口，再用信号说话；顺序反了，波形分析都是白费',
                      22, colour=INK2))
    return parts


SCENES = {
    'ch10-555-fault-tree': {
        'draw': threes_five_fault_tree, 'title': '555 故障图谱五站定位',
        'anchor': '10.3', 'chapter': 10, 'source': 'docs/p1-11-ch10.md',
        'alt': '手绘 555 故障图谱。顶部蓝框写 5 脚直接接在内部 2/3 Vcc 的抽头上，'
               '悬空等于给高阻抽头接天线，改的正是挡块高度；标准做法接 10 纳法到地。'
               '中间框列五站：①输出常高、6 脚电压不动，判据是放电管没工作，7 脚虚焊或 R2 开路；'
               '②频率对、占空比漂，判据是 R1 或 R2 变值，或 5 脚电容漏电；'
               '③频率随温度狂漂，判据是热风一吹变化超过 5% 就是元件介质问题；'
               '④起振迟缓、偶发停振，判据是电源爬升太慢，4 脚加 RC 延时；'
               '⑤面包板行、焊到板上不行，判据是寄生 2 到 5 皮法参与定时，按板上实测重算。'
               '琥珀框写先量 5 脚直流电压、应恰好 2/3 Vcc，偏离就是外因，指标合格才轮到怀疑芯片。'
               '底部绿框处方三件套：就近 100 纳法加 10 微法、续流路径独立、走线不进继电器回路。',
    },
    'ch10-555-threshold-clamp': {
        'draw': threes_five_threshold, 'title': '555 的两条门限与占空比',
        'anchor': '10.1', 'chapter': 10, 'source': 'docs/p1-11-ch10.md',
        'alt': '手绘 555 门限账。顶部蓝框写三只 5 千欧电阻串在电源与地之间抽出两条门限，'
               '2/3 Vcc 进比较器 A、1/3 Vcc 进比较器 B，这就是 555 这个名字的由来。'
               '左绿框「撞上限：按住」：电容升到 2/3 Vcc，比较器 A 翻转，触发器复位、放电管导通。'
               '右红框「落下限：松手」：电容降到 1/3 Vcc，比较器 B 翻转，触发器置位、放电管截止。'
               '琥珀框写所以占空比永远大于 50%：充电走 R1 加 R2、放电只走 R2，进得慢出得快；'
               'R1 只出现在充电支路，所以这个比值压不到 50%。'
               '底部写触发器只锁状态、不产生振荡，秋千自己会停，能量一路向电源讨。',
    },
    'ch03-ce-swing-budget': {
        'draw': ce_swing_budget, 'title': '共射级的摆幅预算与削波方向',
        'anchor': '3.9', 'chapter': 3, 'source': 'docs/p1-04-ch3.md',
        'alt': '手绘共射摆幅预算。左蓝框先立地基：集电极 6 伏、发射极 1.8 伏、基极约 2.5 伏、'
               '集电极电流 3 毫安、管压降约 4.2 伏，这是安静时的 Q 点。'
               '右绿框再数余量：向上到 12 伏是 6 伏，向下到发射极加 0.2 伏是 4 伏，取小的那份。'
               '琥珀框写线性外推削波界等于 2 乘最小余量、即 8.0 Vpp；增益 230，'
               '线性估计输入约 35 mVpp；指数非线性更早出现，失真须另验。'
               '红框写削波方向就是诊断方向：输出底部削平是撞饱和、Q 点偏高，'
               '查发射极电压或集电极电阻偏大；顶部削平是撞截止、Q 点偏低，把基极电压往上挪。'
               '底部写 Q 点偏置的任务就是把两份余量尽量平分，先站回直流窗口再用信号说话。',
    },
}

# Share corrected timer diagrams with historical batches.
from scripts.visuals.scenes.ch10_reference_figures import SCENES as _ch10_corrected
for _aid in ['ch10-555-fault-tree', 'ch10-555-threshold-clamp']:
    SCENES[_aid] = _ch10_corrected[_aid]
