"""Wave 2 手绘草图：纸墨 token + 微弯线条，几何是手工 SVG。

每张图的数字只来自对应章节正文；`ch14-derating-margin` 取表 14-2，
`ch15-trace-drop` 取 15.1 的铜电阻率与几何尺寸，统一用 SI 计算。
"""
from __future__ import annotations

from html import escape

from scripts import handraw

INK = handraw.LIGHT['ink']
INK2 = handraw.LIGHT['ink2']
PAPER = handraw.LIGHT['paper2']
RULE = handraw.LIGHT['rule']
AMBER = handraw.LIGHT['amber']
GREEN = handraw.LIGHT['green']
RED = handraw.LIGHT['red']
BLUE = handraw.LIGHT['blue']
FONT = handraw.HAND_FONT


def text(x, y, value, size=24, colour=INK, anchor='start', weight='400'):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{colour}" '
            f'font-family="{FONT}" font-weight="{weight}" text-anchor="{anchor}">'
            f'{escape(str(value))}</text>')


def box(x, y, w, h, fill=PAPER, stroke=INK2, width: float = 2):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')


def arrow(x1, y1, x2, y2, colour=INK2, width=2.5):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour}" '
            f'stroke-width="{width}" stroke-linecap="round"/>'
            f'<polygon points="{x2},{y2} {x2 - 10},{y2 - 5} {x2 - 10},{y2 + 5}" fill="{colour}"/>')


def header(title, subtitle):
    return text(52, 58, title, 38, weight='700') + text(52, 94, subtitle, 22, colour=INK2)


def assumption_tree():
    parts = [header('假设树：一个现象，两条互斥分支',
                    '先写“结果为 A 则排除 B”，再下探头；写不出判据就不做实验。')]
    parts.append(box(300, 120, 400, 64, fill=PAPER))
    parts.append(text(500, 160, '现象：输出缓慢漂移', 26, anchor='middle', weight='700'))
    parts.append(arrow(430, 184, 270, 252))
    parts.append(arrow(570, 184, 730, 252))
    parts.append(box(70, 260, 350, 190))
    parts.append(text(90, 300, '假设 A：电源轨在动', 24, colour=AMBER, weight='700'))
    parts.append(text(90, 338, '预测：VCC 随负载跌', 22, colour=INK2))
    parts.append(text(90, 374, '实验：带载测 VCC', 22, colour=INK2))
    parts.append(text(90, 410, '判据：跌幅超过规格', 22, colour=INK2))
    parts.append(box(580, 260, 350, 190))
    parts.append(text(600, 300, '假设 B：测量链在漂', 24, colour=BLUE, weight='700'))
    parts.append(text(600, 338, '预测：短接输入仍漂', 22, colour=INK2))
    parts.append(text(600, 374, '实验：短接看零点', 22, colour=INK2))
    parts.append(text(600, 410, '判据：零点自己会走', 22, colour=INK2))
    parts.append(arrow(245, 450, 380, 510))
    parts.append(arrow(755, 450, 620, 510))
    parts.append(box(160, 510, 680, 96, fill=PAPER))
    parts.append(text(500, 548, '结果为 A → 排除 B；结果为 B → 排除 A', 26, anchor='middle', weight='700'))
    parts.append(text(500, 582, '两个实验必须能区分至少两条分支', 22, colour=INK2, anchor='middle'))
    parts.append(text(52, 660, '一次只改一个变量；无效就回退，再改下一个。', 22, colour=INK2))
    return parts


def fault_record():
    parts = [header('一份能复用的故障档案',
                    '症状写用户语言，假设带可检验的预测；归档后才能按根因归类。')]
    parts.append(box(60, 112, 880, 540, fill=PAPER))
    rows = [
        ('日期 / 批次', '当天 / 批次 A'),
        ('现象', '用户原话，不写猜测'),
        ('复现条件', '温度、负载、第几次上电'),
        ('假设 + 预测', '若为真，哪个读数应为多少'),
        ('实验记录', '一次只改一个变量，无效回退'),
        ('根因', '证据链，不是“可能”'),
        ('修复', '改了什么，为什么'),
        ('回归验证', '原条件 + 边界拉偏 + 反向装回'),
    ]
    for i, (label, hint) in enumerate(rows):
        y = 168 + i * 60
        parts.append(f'<line x1="86" y1="{y + 18}" x2="914" y2="{y + 18}" stroke="{RULE}" stroke-width="1.4"/>')
        parts.append(text(92, y, label, 24, colour=AMBER, weight='700'))
        parts.append(text(300, y, hint, 22, colour=INK2))
        parts.append(f'<circle cx="886" cy="{y - 8}" r="10" fill="none" stroke="{GREEN}" stroke-width="2"/>')
    parts.append(text(92, 632, '每季度按根因归类：前三名失效模式回写成评审清单。', 22, colour=INK2))
    return parts


def two_way_validation():
    parts = [header('修复要双向验证',
                    '正向证明好件能好，反向证明坏件仍坏；缺一条，故障单不许关。')]
    panels = [
        (70, '正向', '换好件', '故障消失', GREEN),
        (370, '反向', '装回坏件', '故障复现', AMBER),
        (670, '边界拉偏', '供电 ±10%', '全温区 / 老化 ≥ 一天', BLUE),
    ]
    for x, head, line1, line2, colour in panels:
        parts.append(box(x, 160, 260, 300))
        parts.append(text(x + 130, 206, head, 28, colour=colour, anchor='middle', weight='700'))
        parts.append(f'<line x1="{x + 24}" y1="226" x2="{x + 236}" y2="226" stroke="{RULE}" stroke-width="1.6"/>')
        parts.append(text(x + 130, 286, line1, 24, anchor='middle'))
        parts.append(text(x + 130, 336, line2, 24, anchor='middle', colour=INK2))
    parts.append(arrow(334, 310, 366, 310, AMBER))
    parts.append(arrow(634, 310, 666, 310, BLUE))
    parts.append(box(140, 520, 720, 84, fill=PAPER))
    parts.append(text(500, 556, '三条都过，结论才从轶事升级为结论', 26, anchor='middle', weight='700'))
    parts.append(text(500, 588, '缺一条就关闭，现场复发一次更贵', 22, colour=INK2, anchor='middle'))
    parts.append(text(52, 660, '反向不复现，说明根因没抓到，只是被拆装暂时吓退。', 22, colour=INK2))
    return parts


def derating_margin():
    parts = [header('降额不是口号：把工作点压进绿区',
                    '表 14-2 的建议工作上限；横轴是额定值的百分比，100% 不是工作点。')]
    x0, x1 = 300, 900
    rows = [
        ('电阻功率', 60, '50–60%'),
        ('陶瓷电容', 80, '50–80%'),
        ('电解电容', 80, '≤80%'),
        ('二极管', 80, '70–80%'),
        ('MOSFET', 80, '60–80%'),
        ('连接器', 70, '50–70%'),
    ]
    parts.append(f'<line x1="{x0}" y1="560" x2="{x1}" y2="560" stroke="{INK2}" stroke-width="2"/>')
    for pct in (50, 100):
        x = x0 + (x1 - x0) * pct / 100
        parts.append(f'<line x1="{x}" y1="552" x2="{x}" y2="568" stroke="{INK2}" stroke-width="2"/>')
        parts.append(text(x, 596, f'{pct}%', 22, colour=INK2, anchor='middle'))
    for i, (label, limit, shown) in enumerate(rows):
        y = 170 + i * 64
        parts.append(text(72, y + 30, label, 24, weight='700'))
        parts.append(f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="34" rx="4" fill="{PAPER}" stroke="{RULE}" stroke-width="1.2"/>')
        parts.append(f'<rect x="{x0}" y="{y}" width="{(x1 - x0) * limit / 100:.0f}" height="34" rx="4" fill="{GREEN}" opacity=".55"/>')
        parts.append(f'<line x1="{x0 + (x1 - x0) * limit / 100:.0f}" y1="{y - 4}" x2="{x0 + (x1 - x0) * limit / 100:.0f}" y2="{y + 38}" stroke="{RED}" stroke-width="2.6"/>')
        parts.append(text(x1 + 12, y + 26, shown, 22, colour=INK2, anchor='end'))
    parts.append(text(300, 646, '上限值取表中区间的高端；具体项目以公司降额规范为准。', 22, colour=INK2))
    return parts


def trace_resistance(length_m: float, width_m: float, thickness_m: float,
                     resistivity: float = 1.7e-8) -> float:
    """Uniform copper trace, constant temperature; excludes vias and contacts."""
    if min(length_m, width_m, thickness_m, resistivity) <= 0:
        raise ValueError('走线尺寸与电阻率必须大于零')
    return resistivity * length_m / (width_m * thickness_m)


def trace_drop():
    per_cm_mohm = trace_resistance(0.01, 0.5e-3, 35e-6) * 1000
    total_mohm = trace_resistance(0.08, 0.5e-3, 35e-6) * 1000
    parts = [header('走线压降：先把毫米换成米',
                    '0.5 mm 宽、35 µm 厚；ρ = 1.7×10⁻⁸ Ω·m，忽略温升与过孔。')]
    parts.append(box(70, 150, 860, 210, fill=PAPER))
    parts.append(f'<path d="M120,270 L220,200 L320,270 L420,200 L520,270 L620,200 L820,200" '
                 f'fill="none" stroke="{AMBER}" stroke-width="6" stroke-linejoin="round"/>')
    parts.append(text(120, 320, '8 cm 长、0.5 mm 宽、1 oz 铜', 24, colour=INK2))
    parts.append(text(680, 180, f'{per_cm_mohm:.2f} mΩ/cm', 26, colour=AMBER, weight='700'))
    parts.append(arrow(760, 240, 820, 240, RED))
    parts.append(text(790, 282, '300 mA', 22, colour=RED, anchor='middle'))
    parts.append(box(70, 400, 400, 150))
    parts.append(text(96, 440, '静态：300 mA', 24, weight='700'))
    parts.append(text(96, 480, f'8 cm 总电阻 {total_mohm:.2f} mΩ', 22, colour=INK2))
    parts.append(text(96, 516, f'压降 = {total_mohm * 0.3:.2f} mV', 24, colour=GREEN, weight='700'))
    parts.append(box(530, 400, 400, 150))
    parts.append(text(556, 440, '电流升至：1 A', 24, weight='700'))
    parts.append(text(556, 480, f'同一条 {total_mohm:.2f} mΩ 路径', 22, colour=INK2))
    parts.append(text(556, 516, f'电阻压降 = {total_mohm:.2f} mV', 24, colour=RED, weight='700'))
    parts.append(text(70, 620, '这是单程电阻压降；地回路压降要另算。', 22, colour=INK2))
    parts.append(text(70, 654, '快速电流变化还叠加 L·di/dt；线宽同时核压降与温升。', 22, colour=INK2))
    return parts


SCENES = {
    'ch18-assumption-tree': {
        'draw': assumption_tree, 'title': '假设树与互斥分支', 'anchor': '18.3',
        'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '手绘假设树：现象是输出缓慢漂移，分成电源轨在动与测量链在漂两条互斥分支；每条都写预测、实验与判据，底部写明结果为 A 则排除 B、结果为 B 则排除 A。',
    },
    'ch18-fault-record': {
        'draw': fault_record, 'title': '可复用的故障档案字段', 'anchor': '18.1',
        'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '手绘故障档案卡：日期与批次、用户语言的现象、复现条件、带预测的假设、一次只改一个变量的实验记录、证据链根因、修复动作、原条件加边界拉偏的反向回归；每行右侧一个待勾选圆圈。',
    },
    'ch18-two-way-validation': {
        'draw': two_way_validation, 'title': '正向、反向与边界验证', 'anchor': '18.3',
        'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '手绘三栏：正向验证换好件后故障消失，反向验证装回坏件后故障复现，边界拉偏覆盖供电正负 10%、全温区与至少一天老化；三条都过才允许关闭故障单。',
    },
    'ch14-derating-margin': {
        'draw': derating_margin, 'title': '常用降额线', 'anchor': '14.2',
        'chapter': 14, 'source': 'docs/p3-01-ch14.md',
        'alt': '手绘横向条形图：以额定值百分比为横轴，电阻功率 50 到 60%、陶瓷电容 50 到 80%、电解电容不超过 80%、二极管 70 到 80%、MOSFET 60 到 80%、连接器 50 到 70%；绿色条表示建议工作区，红色竖线标出上限。',
    },
    'ch15-trace-drop': {
        'draw': trace_drop, 'title': '电源走线的压降账', 'anchor': '15.1',
        'chapter': 15, 'source': 'docs/p3-02-ch15.md',
        'alt': '走线电阻按电阻率乘长度除截面积计算：0.5 毫米宽、35 微米厚、8 厘米长，单程电阻 77.71 毫欧；300 毫安压降 23.31 毫伏、1 安培压降 77.71 毫伏。示例忽略温升、过孔与接触电阻，快速瞬态另加电感压降。',
    },
}
