"""Wave 4 手绘草图：元件失效签名、温度手段、仪器信任链、复盘分栏、热焊盘。"""
from __future__ import annotations

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK, INK2, PAPER, RED, RULE, arrow, box, header, text,
)
from scripts.visuals.scenes.handdrawn_wave3 import varrow


def component_signatures():
    parts = [header('元件很少“莫名其妙”地坏',
                    '每种元件都有自己的失效签名；先认签名，再拆焊。')]
    cards = [
        ('电阻烧毁', '开路', '过流先烧电阻体', AMBER),
        ('电容失效', '短路 / 漏电', '电解干涸、介质击穿', BLUE),
        ('半导体过压', '结击穿', 'EOS 与静电各有现场', RED),
        ('MLCC 偏压', '容量缩水', '满压可能只剩标称一半', GREEN),
    ]
    for i, (head, sig, note, colour) in enumerate(cards):
        x = 60 + (i % 2) * 460
        y = 140 + (i // 2) * 220
        parts.append(box(x, y, 420, 190, fill=PAPER))
        parts.append(text(x + 26, y + 48, head, 26, colour=colour, weight='700'))
        parts.append(text(x + 26, y + 96, sig, 30, weight='700'))
        parts.append(text(x + 26, y + 142, note, 22, colour=INK2))
        parts.append(f'<circle cx="{x + 380}" cy="{y + 44}" r="18" fill="none" stroke="{colour}" stroke-width="2"/>')
    parts.append(text(60, 596, '参数漂移型失效不上电也能骗人：', 23, colour=INK2))
    parts.append(text(60, 634, '容量要带实际偏压核，离线电桥量的是“标称”。', 23, weight='700'))
    parts.append(box(600, 590, 340, 52, fill=PAPER))
    parts.append(text(770, 624, '先认签名，再动烙铁。', 22, anchor='middle', weight='700'))
    return parts


def temp_spray():
    parts = [header('温度手段：先感知，再逐片降温',
                    '温敏故障在常温万用表下隐身，一喷冷雾就现形。')]
    steps = [
        ('① 手背感知', '只限低压或电池供电', GREEN),
        ('② 冷却喷剂', '逐片降温看故障是否回来', BLUE),
        ('③ 锁定温敏件', '记录温度与复现边界', AMBER),
    ]
    for i, (head, note, colour) in enumerate(steps):
        x = 60 + i * 310
        parts.append(box(x, 150, 280, 190, fill=PAPER))
        parts.append(text(x + 24, 198, head, 25, colour=colour, weight='700'))
        parts.append(text(x + 24, 248, note, 22, colour=INK2))
        parts.append(text(x + 24, 300, '一次只动一个位置', 22, colour=INK2))
        if i < 2:
            parts.append(varrow(x + 286, 245, x + 304, 245, INK2, 2.5))

    parts.append(box(60, 390, 880, 150, fill=PAPER))
    parts.append(text(88, 432, '安全边界', 25, colour=RED, weight='700'))
    parts.append(text(88, 474, '市电侧与高压电容附近：只用喷剂和红外测温，绝不伸手。', 23))
    parts.append(text(88, 512, '冷雾会凝露；带电板先断电，等表面干燥再上电。', 22, colour=INK2))

    parts.append(box(140, 592, 720, 52, fill=PAPER))
    parts.append(text(500, 625, '温度是变量，不是结论；消失与回来都要记录。', 23, anchor='middle', weight='700'))
    return parts


def instrument_trust():
    parts = [header('仪器也要先“自证清白”',
                    '探头、万用表、电源、焊台，开工前先用已知信号对一遍。')]
    parts.append(box(48, 126, 470, 480, fill=PAPER))
    parts.append(text(74, 170, '六道保险里的四道', 25, colour=AMBER, weight='700'))
    rows = [
        ('探头负载', '高阻节点先用 ×10'),
        ('电流档', '测完立刻插回电压孔'),
        ('首次上电', '低压板按负载设置限流'),
        ('接地探头', '确认参考地，先地夹后探针'),
    ]
    for i, (head, note) in enumerate(rows):
        y = 226 + i * 86
        parts.append(text(74, y, head, 23, weight='700'))
        parts.append(text(74, y + 34, note, 22, colour=INK2))
        parts.append(f'<line x1="74" y1="{y + 52}" x2="492" y2="{y + 52}" stroke="{RULE}" stroke-width="1.3"/>')

    parts.append(box(558, 126, 394, 224, fill=PAPER))
    parts.append(text(584, 170, '坑一：自动量程', 24, colour=RED, weight='700'))
    parts.append(text(584, 212, '跳变信号来回换档', 22, colour=INK2))
    parts.append(text(584, 250, '读数迟迟不稳', 22, colour=INK2))
    parts.append(text(584, 292, '急的时候手动定档', 23, weight='700'))

    parts.append(box(558, 382, 394, 224, fill=PAPER))
    parts.append(text(584, 426, '坑二：电流档压降', 24, colour=RED, weight='700'))
    parts.append(text(584, 468, '示例：µA 档内阻 100 Ω', 22, colour=INK2))
    parts.append(text(584, 506, '示例：mA 档内阻 2 Ω', 22, colour=INK2))
    parts.append(text(584, 548, '测 100 mA 吃掉近 0.2 V', 22, weight='700'))

    parts.append(box(140, 632, 720, 42, fill=PAPER))
    parts.append(text(500, 661, '先证明仪器可信，再相信读数。', 23, anchor='middle', weight='700'))
    return parts


def postmortem_split():
    parts = [header('复盘先把“根因”和“触发条件”分开',
                    '根因是本来就存在的缺陷；触发条件只是把它暴露出来的那阵风。')]
    parts.append(text(72, 150, '根因（设计 / 工艺缺陷）', 24, colour=RED, weight='700'))
    parts.append(text(548, 150, '触发条件（那阵风）', 24, colour=BLUE, weight='700'))
    rows = [
        ('A 环路相位裕度不足', '低温让 MLCC 容值再降'),
        ('B 晶振线与 SW 平行 6 mm', '关盖温升 23 °C + 高 dV/dt'),
        ('C BGA 焊球虚焊', '热循环、振动、拍桌子'),
    ]
    for i, (root, trigger) in enumerate(rows):
        y = 190 + i * 128
        parts.append(box(60, y, 440, 100, fill=PAPER))
        parts.append(box(520, y, 420, 100, fill=PAPER))
        parts.append(text(84, y + 42, root, 22, weight='700'))
        parts.append(text(544, y + 42, trigger, 22, colour=INK2))
        parts.append(varrow(500, y + 50, 516, y + 50, AMBER, 2.5))

    parts.append(box(60, 590, 880, 76, fill=PAPER))
    parts.append(text(88, 622, '把老化温度从 -20 °C 改成 0 °C，板子“好了”，缺陷还在。', 22))
    parts.append(text(88, 652, '根因不改，换个触发条件它还会回来。', 22, colour=RED, weight='700'))
    return parts


def thermal_relief():
    parts = [header('热焊盘：手工焊要隔离，大电流要直通',
                    '同一块铺铜，两种焊盘；别让自动连接规则替你分。')]
    parts.append(box(60, 140, 420, 420, fill=PAPER))
    parts.append(text(86, 184, '花孔（thermal relief）', 24, colour=AMBER, weight='700'))
    parts.append(f'<circle cx="270" cy="330" r="92" fill="{PAPER}" stroke="{INK2}" stroke-width="3"/>')
    parts.append(f'<circle cx="270" cy="330" r="34" fill="{AMBER}" opacity=".55" stroke="{INK2}" stroke-width="2"/>')
    for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        parts.append(f'<line x1="{270 + dx * 34}" y1="{330 + dy * 34}" x2="{270 + dx * 96}" y2="{330 + dy * 96}" stroke="{AMBER}" stroke-width="10"/>')
    parts.append(text(86, 470, '四条细桥限热，350 °C 才焊得动', 22, colour=INK2))
    parts.append(text(86, 512, '适合手工焊的插件/通孔', 22, weight='700'))

    parts.append(box(520, 140, 420, 420, fill=PAPER))
    parts.append(text(546, 184, '直连（direct connect）', 24, colour=BLUE, weight='700'))
    parts.append(f'<rect x="600" y="252" width="260" height="160" rx="8" fill="{BLUE}" opacity=".28" stroke="{INK2}" stroke-width="2"/>')
    parts.append(f'<rect x="690" y="310" width="80" height="44" rx="5" fill="{PAPER}" stroke="{INK2}" stroke-width="2"/>')
    parts.append(text(730, 470, '整片铜直接连，热被铜皮瞬间导走', 22, colour=INK2, anchor='middle'))
    parts.append(text(730, 512, '大电流路径、电源入口', 22, weight='700', anchor='middle'))

    parts.append(box(60, 596, 880, 60, fill=PAPER))
    parts.append(text(500, 633, '同一个封装库，两类焊盘分开命名；别指望铺铜规则替你分清。', 22, anchor='middle', weight='700'))
    return parts


SCENES = {
    'ch18-component-signatures': {
        'draw': component_signatures, 'title': '元件失效签名', 'anchor': '18.1',
        'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '手绘四张失效签名卡：电阻过流烧毁开路、电容短路或漏电、半导体过压击穿、MLCC 在直流偏压下容量缩水；底部提示参数漂移型失效要带实际偏压核对容量。',
    },
    'ch18-temp-spray': {
        'draw': temp_spray, 'title': '温度手段与安全边界', 'anchor': '18.1',
        'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '手绘三步温度定位：手背感知只限低压或电池供电，冷却喷剂逐片降温看故障是否回来，锁定温敏件并记录边界；下方强调市电与高压电容附近只用喷剂和红外测温，绝不伸手。',
    },
    'ch16-instrument-trust': {
        'draw': instrument_trust, 'title': '仪器信任链', 'anchor': '16.3',
        'chapter': 16, 'source': 'docs/p4-01-ch16.md',
        'alt': '仪器检查单：高阻节点先用乘十档、测完电流插回电压孔、低压板按负载设置限流；普通接地探头确认参考地后先地夹后探针。右栏示例内阻为微安档 100 欧姆、毫安档 2 欧姆；100 毫安流过 2 欧姆会产生 0.2 伏压降，实际值查仪表手册。',
    },
    'ch16-postmortem-split': {
        'draw': postmortem_split, 'title': '根因与触发条件', 'anchor': '16.8',
        'chapter': 16, 'source': 'docs/p4-01-ch16.md',
        'alt': '手绘复盘分栏：左栏根因分别是环路相位裕度不足、晶振线与开关节点平行 6 毫米、BGA 焊球虚焊；右栏触发条件分别是低温让 MLCC 容值再降、关盖温升 23 摄氏度与高 dV/dt、热循环振动与拍桌子。',
    },
    'ch15-thermal-relief': {
        'draw': thermal_relief, 'title': '热焊盘的两难', 'anchor': '15.4',
        'chapter': 15, 'source': 'docs/p3-02-ch15.md',
        'alt': '手绘两种焊盘：花孔用四条细桥连接铺铜，限制散热，手工烙铁 350 摄氏度才焊得动；直连焊盘整片铜相连，适合大电流与电源入口。底部要求同一封装库把两类焊盘分开命名。',
    },
}
