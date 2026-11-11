"""Wave 3 手绘草图：预测、目检、四线法、结温与交换法。

数字全部来自对应章节正文：18.1（60 秒目检、1 Ω/1 A/1 V、0.3 Ω 表笔）、
18.2（2.5 V、±2 V、69 ms、140 ms、20%）、14.2（Tj 每升 10 °C 失效率约翻倍）。
"""
from __future__ import annotations

from scripts import handraw
from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK, INK2, PAPER, RED, RULE, arrow, box, header, text,
)

FONT = handraw.HAND_FONT


def varrow(x1, y1, x2, y2, colour=INK2, width=2.5):
    """带三角箭头的直线；方向由端点决定。"""
    dx, dy = x2 - x1, y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / length, dy / length
    bx, by = x2 - ux * 12, y2 - uy * 12
    px, py = -uy * 5, ux * 5
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour}" '
            f'stroke-width="{width}" stroke-linecap="round"/>'
            f'<polygon points="{x2},{y2} {bx + px},{by + py} {bx - px},{by - py}" fill="{colour}"/>')


def predict_before_probe():
    parts = [header('下探头之前，先把波形写在纸上',
                    '预测直流、交流、时间尺度；偏差超过 20% 就停手改模型。')]
    parts.append(box(48, 122, 410, 470, fill=PAPER))
    parts.append(text(76, 168, '预测三行', 27, colour=AMBER, weight='700'))
    rows = [
        ('直流电平', '2.5 V'),
        ('交流幅度', '±2 V'),
        ('时间尺度', '69 ms'),
        ('波形形状', '先陡后缓'),
    ]
    for i, (label, value) in enumerate(rows):
        y = 226 + i * 78
        parts.append(text(78, y, label, 23, colour=INK2))
        parts.append(text(240, y, value, 26, weight='700'))
        parts.append(f'<line x1="76" y1="{y + 18}" x2="430" y2="{y + 18}" stroke="{RULE}" stroke-width="1.3"/>')
    parts.append(text(76, 562, '心里“大概有谱”不算预测。', 22, colour=INK2))

    parts.append(box(542, 122, 410, 470, fill=PAPER))
    parts.append(text(570, 168, '实测对账', 27, colour=BLUE, weight='700'))
    parts.append(text(570, 230, '量到 140 ms', 27, weight='700'))
    parts.append(text(570, 284, '与预测差 2 倍', 24, colour=RED))
    parts.append(text(570, 336, '> 20% → 停手', 26, colour=RED, weight='700'))
    parts.append(text(570, 388, '不继续测，先改模型', 23, colour=INK2))
    parts.append(text(570, 452, '嫌犯收窄到两个：', 22, colour=INK2))
    parts.append(text(570, 490, '电容翻倍 / 漏电阻', 24, weight='700'))
    parts.append(text(570, 548, '下一步只做区分实验。', 22, colour=INK2))
    parts.append(varrow(474, 340, 524, 340, AMBER, 3))
    parts.append(box(140, 616, 720, 48, fill=PAPER))
    parts.append(text(500, 648, '预测与实测的差，就是假设空间收窄的方向。', 24, anchor='middle', weight='700'))
    return parts


def first_minute():
    parts = [header('60 秒目检：先做最笨的检查',
                    '保险丝是证人，不是耗材；接插件是另一个高发区。')]
    parts.append(box(48, 122, 430, 492, fill=PAPER))
    parts.append(text(74, 166, '六件事，逐项打勾', 26, colour=AMBER, weight='700'))
    checks = ['保险丝断没断', '插座有没有电', '开关打在哪个档', '线序对不对',
              '芯片方向插反没', '跳线帽在该在的位置']
    for i, item in enumerate(checks):
        y = 224 + i * 60
        parts.append(f'<rect x="76" y="{y - 22}" width="24" height="24" rx="3" fill="none" stroke="{INK2}" stroke-width="2"/>')
        parts.append(text(116, y, item, 23))
    parts.append(text(74, 586, '目检不高级，但能拦下“根本没通电”。', 22, colour=INK2))

    parts.append(box(520, 122, 432, 220, fill=PAPER))
    parts.append(text(546, 166, '保险丝烧了', 26, colour=RED, weight='700'))
    parts.append(text(546, 210, '先查下游短路', 23))
    parts.append(text(546, 246, '断电测负载对地电阻', 22, colour=INK2))
    parts.append(text(546, 282, '别急着换新送命', 23, colour=RED))

    parts.append(box(520, 370, 432, 244, fill=PAPER))
    parts.append(text(546, 414, '触点 1 Ω', 26, colour=AMBER, weight='700'))
    parts.append(text(546, 458, '1 A 电流吃掉 1 V', 23))
    parts.append(text(546, 494, '5 V 后级只剩 4 V', 23))
    parts.append(text(546, 544, '先拨插复测，再谈芯片', 22, colour=INK2))
    parts.append(text(546, 584, '别反复重上电“试试”。', 22, colour=INK2))
    parts.append(box(140, 636, 720, 40, fill=PAPER))
    parts.append(text(500, 663, '让证人说话，再动烙铁。', 24, anchor='middle', weight='700'))
    return parts


def four_wire():
    parts = [header('两线法把表笔电阻也算进去',
                    '测小电阻先短接表笔记底数；四线法把电流与电压分开。')]
    parts.append(box(48, 122, 432, 450, fill=PAPER))
    parts.append(text(74, 164, '两线法', 26, colour=AMBER, weight='700'))
    parts.append(text(74, 212, '表笔底数 0.3 Ω', 23))
    parts.append(text(74, 250, '量一段地线读到 0.8 Ω', 23))
    parts.append(text(74, 288, '真实只有约 0.5 Ω', 24, colour=GREEN, weight='700'))
    parts.append(text(74, 344, '表笔和接触电阻一起进了读数', 22, colour=INK2))
    parts.append(text(74, 382, '不扣底数，会把好地判成坏地', 22, colour=INK2))
    parts.append(box(74, 420, 370, 110, fill=PAPER))
    parts.append(text(96, 456, '读数 0.8 Ω − 底数 0.3 Ω', 22))
    parts.append(text(96, 496, '= 真实 0.5 Ω', 25, colour=GREEN, weight='700'))

    parts.append(box(520, 122, 432, 450, fill=PAPER))
    parts.append(text(546, 164, '四线法', 26, colour=BLUE, weight='700'))
    parts.append(f'<rect x="570" y="220" width="120" height="70" rx="5" fill="{PAPER}" stroke="{INK2}" stroke-width="2"/>')
    parts.append(text(630, 263, 'R', 30, anchor='middle', weight='700'))
    parts.append(text(546, 340, '强制电流 I', 22, colour=INK2))
    parts.append(varrow(700, 240, 804, 240, AMBER, 3))
    parts.append(text(752, 222, 'I', 23, colour=AMBER, anchor='middle', weight='700'))
    parts.append(text(546, 400, '单独测 R 两端电压 V', 22, colour=INK2))
    parts.append(text(546, 446, '表笔压降不进 V 回路', 22, colour=BLUE))
    parts.append(text(546, 492, '0.3 Ω 被请出读数', 23, weight='700'))
    parts.append(text(546, 538, '小电阻、接地阻抗、接触电阻', 22, colour=INK2))
    parts.append(box(140, 608, 720, 52, fill=PAPER))
    parts.append(text(500, 641, '先扣表笔，再判接触；两线法只适合“看一眼通断”。', 23, anchor='middle', weight='700'))
    return parts


def arrhenius():
    parts = [header('结温每升 10 °C，失效率约翻倍',
                    '热设计不是先挑散热片，是从允许结温倒推。')]
    parts.append(box(60, 128, 360, 240, fill=PAPER))
    parts.append(text(88, 172, '工作结温 Tj', 24, colour=INK2))
    parts.append(f'<rect x="88" y="206" width="284" height="30" rx="6" fill="{PAPER}" stroke="{RULE}" stroke-width="1.4"/>')
    parts.append(f'<rect x="88" y="206" width="170" height="30" rx="6" fill="{AMBER}" opacity=".45"/>')
    parts.append(text(88, 282, '再升 10 °C', 23, colour=RED))
    parts.append(text(88, 330, '失效率约 2×', 27, colour=RED, weight='700'))

    parts.append(box(470, 128, 480, 240, fill=PAPER))
    parts.append(text(496, 170, '从允许结温倒推', 24, colour=BLUE, weight='700'))
    chain = ['Tj 上限', 'Rθ', '功耗 P', '面积']
    for i, label in enumerate(chain):
        x = 496 + i * 108
        parts.append(box(x, 218, 92, 62, fill=PAPER))
        parts.append(text(x + 46, 256, label, 22, anchor='middle', weight='700'))
        if i < len(chain) - 1:
            parts.append(varrow(x + 96, 249, x + 104, 249, INK2, 2))
    parts.append(text(496, 322, '先定上限，再算热阻与面积。', 22, colour=INK2))

    parts.append(box(60, 402, 890, 176, fill=PAPER))
    parts.append(text(88, 444, '两条路，结果不同', 24, colour=AMBER, weight='700'))
    parts.append(text(88, 490, '先选散热片 → 结温可能仍超', 23))
    parts.append(text(88, 528, '先定 Tj 上限 → 反推 Rθ 与功耗预算', 23, colour=GREEN, weight='700'))
    parts.append(text(88, 560, '热设计是计算链，不是选型手感。', 22, colour=INK2))

    parts.append(box(140, 614, 720, 46, fill=PAPER))
    parts.append(text(500, 645, '温度是寿命的乘数；降 10 °C，失效率约减半。', 23, anchor='middle', weight='700'))
    return parts


def swap_discipline():
    parts = [header('交换法：让故障跟人走，还是跟板走',
                    '交换前拍照，交换中防静电，交换后一次只换一个部件。')]
    parts.append(box(60, 126, 370, 300, fill=PAPER))
    parts.append(text(86, 170, '好板 A', 26, colour=GREEN, weight='700'))
    parts.append(text(86, 212, '已知工作正常', 22, colour=INK2))
    parts.append(box(120, 248, 250, 120, fill=PAPER))
    parts.append(text(245, 292, '可疑部件', 23, anchor='middle'))
    parts.append(text(245, 330, '拆下 / 装回', 22, colour=INK2, anchor='middle'))

    parts.append(box(60, 456, 370, 150, fill=PAPER))
    parts.append(text(86, 496, '坏板 B', 26, colour=RED, weight='700'))
    parts.append(text(86, 538, '故障稳定复现', 22, colour=INK2))
    parts.append(text(86, 576, '交换后看故障跟谁走', 22, colour=INK2))

    parts.append(varrow(438, 300, 528, 300, AMBER, 3))
    parts.append(text(490, 280, '只换一件', 22, colour=AMBER, anchor='middle', weight='700'))

    parts.append(box(550, 126, 400, 240, fill=PAPER))
    parts.append(text(576, 170, '故障跟件走', 26, colour=RED, weight='700'))
    parts.append(text(576, 214, '→ 部件坏', 24))
    parts.append(text(576, 254, '更换该部件', 22, colour=INK2))
    parts.append(text(576, 294, '再跑边界回归', 22, colour=INK2))

    parts.append(box(550, 390, 400, 216, fill=PAPER))
    parts.append(text(576, 434, '故障跟板走', 26, colour=BLUE, weight='700'))
    parts.append(text(576, 478, '→ 板级设计/工艺问题', 23))
    parts.append(text(576, 518, '回到布局、焊接、时序', 22, colour=INK2))
    parts.append(text(576, 558, '别再换第三个部件', 22, colour=INK2))

    rules = ['① 交换前拍照记录', '② 防静电腕带', '③ 一次只换一个部件']
    for i, rule in enumerate(rules):
        parts.append(text(60 + i * 300, 650, rule, 22, weight='700'))
    return parts


SCENES = {
    'ch18-predict-before-probe': {
        'draw': predict_before_probe, 'title': '下探头前先预测', 'anchor': '18.2',
        'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '手绘对账本：左栏预测直流 2.5 V、交流正负 2 V、时间尺度 69 ms、波形先陡后缓；右栏实测 140 ms，偏差超过 20% 就停手改模型，嫌犯收窄到电容翻倍或漏电阻。',
    },
    'ch18-first-minute': {
        'draw': first_minute, 'title': '60 秒目检', 'anchor': '18.1',
        'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '手绘 60 秒目检单：保险丝、插座、开关、线序、芯片方向、跳线帽六项打勾；右侧写保险丝烧断先查下游短路，触点 1 欧姆在 1 安培下吃掉 1 伏，让 5 伏后级只剩 4 伏。',
    },
    'ch18-four-wire': {
        'draw': four_wire, 'title': '两线法与四线法', 'anchor': '18.1',
        'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '手绘测量对照：两线法表笔底数 0.3 欧姆，量地线读到 0.8 欧姆，扣底数后真实约 0.5 欧姆；四线法用独立回路强制电流、单独测电阻两端电压，让表笔压降不进入读数。',
    },
    'ch14-arrhenius-ten-degree': {
        'draw': arrhenius, 'title': '结温与失效率', 'anchor': '14.2',
        'chapter': 14, 'source': 'docs/p3-01-ch14.md',
        'alt': '手绘结温账：工作结温再升 10 摄氏度，失效率约翻倍；右侧是从允许结温倒推热阻、功耗与散热面积的链条，底部写温度是寿命的乘数。',
    },
    'ch18-swap-discipline': {
        'draw': swap_discipline, 'title': '交换法三条纪律', 'anchor': '18.1',
        'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '手绘交换法：好板 A 与坏板 B 之间只交换一个可疑部件；如果故障跟件走就是部件坏，跟板走就是板级设计或工艺问题；三条纪律是交换前拍照、戴防静电腕带、一次只换一个部件。',
    },
}
