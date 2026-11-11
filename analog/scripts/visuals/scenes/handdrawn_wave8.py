"""Wave 8 手绘草图：早期章节的选型与边界（ch1/ch4/ch5/ch7/ch9）。"""
from __future__ import annotations

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK, INK2, PAPER, RED, RULE, arrow, box, header, text,
)


def e24_ladder():
    parts = [header('算出来 3.285k，货架只有 3.3k',
                    'E24 每十倍频程 24 档，相邻档约 1.1 倍；±5% 容差把真实值收进档位窗。')]
    parts.append(box(50, 140, 420, 300, fill=PAPER))
    parts.append(text(74, 182, '算出来的值', 24, colour=AMBER, weight='700'))
    parts.append(text(74, 246, '3.285k', 46, weight='700'))
    parts.append(text(74, 300, 'E24 货架档', 24, colour=GREEN, weight='700'))
    parts.append(text(74, 364, '3.3k', 46, colour=GREEN, weight='700'))
    parts.append(text(74, 414, '误差落在 ±5% 窗内', 22, colour=INK2))
    parts.append(arrow(480, 300, 540, 300))
    parts.append(box(550, 140, 400, 300, fill=PAPER))
    for i, (head, note, col) in enumerate([
            ('24 档', '每十倍频程', INK2),
            ('约 1.1 倍', '相邻档位比', INK2),
            ('±5%', '与容差对齐', GREEN),
            ('E96 → ±1%', '需要更准时换系列', BLUE)]):
        y = 190 + i * 62
        parts.append(text(576, y, head, 26, colour=col, weight='700'))
        parts.append(text(576, y + 28, note, 22, colour=INK2))
    parts.append(box(50, 480, 900, 120, fill=PAPER))
    parts.append(text(76, 522, '先选系列再选值；货架上没有 3.285k。', 24, weight='700'))
    parts.append(text(76, 562, '需要更准：两只串并联，或用电位器校准。', 22, colour=INK2))
    parts.append(text(500, 650, '3.285k → 3.3k，不是偷懒，是按系列落档。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def gate_window():
    parts = [header('栅极保护是一扇电压窗',
                    '钳位要高于驱动、低于栅氧额定；窗口外面不是余量，是击穿。')]
    parts.append(box(50, 140, 520, 360, fill=PAPER))
    bands = [
        (176, '栅氧额定 ±20 V', RED, '#f3ddd7'),
        (276, '钳位 13–16 V', AMBER, '#f6e6d2'),
        (376, '驱动 12 V', GREEN, '#e2ebe0'),
    ]
    for y, label, col, tint in bands:
        parts.append(f'<rect x="74" y="{y}" width="470" height="70" rx="8" fill="{tint}" stroke="{col}" stroke-width="2"/>')
        parts.append(text(96, y + 44, label, 27, colour=col, weight='700'))
    parts.append(text(74, 478, '钳位动作点必须落在这两条线之间。', 22, colour=INK2))
    parts.append(box(600, 140, 350, 360, fill=PAPER))
    rows = [
        ('钳位 > 驱动', '动作电压高于 12 V'),
        ('钳位 < 额定', '又低于 ±20 V'),
        ('10 kΩ 下拉', '悬空态有直流退路'),
        ('开尔文源脚', '源极电感不进栅回路'),
    ]
    for i, (head, note) in enumerate(rows):
        y = 190 + i * 76
        parts.append(text(624, y, head, 23, weight='700'))
        parts.append(text(624, y + 28, note, 22, colour=INK2))
    parts.append(box(50, 530, 900, 76, fill=PAPER))
    parts.append(text(76, 578, '12 V 驱动选 13–16 V 钳位，别让栅氧裸奔。', 24,
                      weight='700', colour=AMBER))
    parts.append(text(500, 650, '先看窗口，再选钳位器件。', 22, colour=INK2,
                      anchor='middle'))
    return parts


def deadtime_ledger():
    parts = [header('死区不是零成本，是一笔明账',
                    '体二极管顶班期间，压降从 0.15 V 变 0.8 V；损耗按占空比照付。')]
    parts.append(box(50, 140, 500, 300, fill=PAPER))
    for i, line in enumerate([
            'P_dt ≈ V_SD × I_D',
            '× (t_d,on + t_d,off) × f_sw',
            '= 0.8 V × 5 A × 100 ns × 100 kHz',
            '≈ 0.04 W（40 mW）']):
        parts.append(text(76, 194 + i * 62, line, 25 if i < 2 else 23,
                          weight='700' if i == 3 else '400',
                          colour=AMBER if i == 3 else INK))
    parts.append(box(580, 140, 370, 300, fill=PAPER))
    parts.append(text(604, 186, '同一只管子', 24, weight='700'))
    parts.append(text(604, 232, '沟道：5 A × 30 mΩ', 22))
    parts.append(text(604, 264, '= 0.15 V', 22, colour=GREEN, weight='700'))
    parts.append(text(604, 322, '体二极管：0.8 V', 22))
    parts.append(text(604, 354, '死区里由它说了算', 22, colour=RED, weight='700'))
    parts.append(text(604, 404, '差的那截压降全是热。', 22, colour=INK2))
    parts.append(box(50, 480, 900, 100, fill=PAPER))
    parts.append(text(76, 524, '死区压到几十纳秒，但不能压到零；', 23, weight='700'))
    parts.append(text(76, 556, '须覆盖实际关断延迟与传播差，避免上下管直通。', 22, colour=INK2))
    parts.append(text(500, 650, '死区用损耗买安全，价格要算清。', 22, colour=AMBER,
                      anchor='middle'))
    return parts


def rp_power():
    parts = [header('上拉电阻自己也会发热',
                    'P = V² / R；低电平压降可忽略时，用上拉电压平方计算。')]
    parts.append(box(50, 150, 420, 240, fill=PAPER))
    parts.append(text(74, 192, '3.3² V² / 1 kΩ', 24, colour=GREEN, weight='700'))
    parts.append(text(74, 232, 'P = V² / R', 22, colour=INK2))
    parts.append(text(74, 300, '11 mW', 46, colour=GREEN, weight='700'))
    parts.append(text(74, 350, '仍按封装与温度降额', 22, colour=INK2))
    parts.append(box(530, 150, 420, 240, fill=PAPER))
    parts.append(text(554, 192, '5² V² / 100 Ω', 24, colour=RED, weight='700'))
    parts.append(text(554, 232, 'P = V² / R', 22, colour=INK2))
    parts.append(text(554, 300, '250 mW', 46, colour=RED, weight='700'))
    parts.append(text(554, 350, '超过示例额定 1/16 W', 22, colour=RED, weight='700'))
    parts.append(box(50, 430, 900, 120, fill=PAPER))
    parts.append(text(76, 474, '准确式：P = (VDD − VOL)² / Rp。', 24, weight='700'))
    parts.append(text(76, 510, '脉冲还须核对脉冲负荷；不能只按占空比算平均。', 22, colour=INK2))
    parts.append(text(500, 620, '强上拉先核封装功率，别让电阻成为新的发热点。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def tristate_handover():
    parts = [header('三态交接：先闭嘴，再转身，后开口',
                    '释放到高阻要 tDIS，使能要 tEN；窗口重叠 10 ns 就是一次微型对撞。')]
    parts.append(box(60, 220, 260, 110, fill=PAPER))
    parts.append(text(80, 264, '驱动器 A', 24, weight='700'))
    parts.append(text(80, 300, '撤销使能命令', 22, colour=INK2))
    parts.append(box(340, 220, 300, 110, fill=PAPER))
    parts.append(text(360, 264, '等待禁用传播完成', 23, colour=AMBER, weight='700'))
    parts.append(text(360, 300, 'tDIS 10–30 ns 仅作示例', 22, colour=INK2))
    parts.append(box(660, 220, 280, 110, fill=PAPER))
    parts.append(text(680, 264, '驱动器 B', 24, weight='700'))
    parts.append(text(680, 300, '使能 / 开始驱动', 22, colour=INK2))
    parts.append(arrow(324, 275, 336, 275))
    parts.append(arrow(644, 275, 656, 275))
    parts.append(box(60, 390, 880, 100, fill=PAPER))
    parts.append(text(84, 432, '重叠 10 ns：A 还没退，B 已开口', 23, colour=RED, weight='700'))
    parts.append(text(84, 464, '冲突持续时间由实际重叠决定，不能直接说成微秒级。', 22, colour=INK2))
    parts.append(box(60, 530, 880, 76, fill=PAPER))
    parts.append(text(84, 578, '同时看 OE、总线和电源电流；毛刺不是冲突的唯一证据。', 23,
                      weight='700'))
    parts.append(text(500, 650, '先撤销 OE，再转身，后开口。', 22, colour=AMBER,
                      anchor='middle'))
    return parts


def hysteresis_window():
    parts = [header('迟滞：把判决点拆成两个',
                    '上行 6.15 V 才报，下行 5.85 V 才解；305 mV 窗口盖住 120 mV 噪声。')]
    parts.append(f'<line x1="100" y1="470" x2="620" y2="470" stroke="{INK2}" stroke-width="2"/>')
    parts.append(f'<line x1="100" y1="470" x2="100" y2="180" stroke="{INK2}" stroke-width="2"/>')
    parts.append(text(600, 500, 'VIN', 22, colour=INK2, anchor='end'))
    parts.append(text(120, 170, 'VOUT', 22, colour=INK2))
    # 回环：上行在 6.15 V 翻高，下行在 5.85 V 翻低
    parts.append(f'<path d="M140,430 L480,430 L480,230 L580,230" '
                 f'fill="none" stroke="{BLUE}" stroke-width="5"/>')
    parts.append(f'<path d="M580,230 L360,230 L360,430 L140,430" '
                 f'fill="none" stroke="{BLUE}" stroke-width="5"/>')
    parts.append(arrow(250, 430, 310, 430, colour=BLUE, width=2.5))
    parts.append(f'<line x1="540" y1="230" x2="480" y2="230" stroke="{BLUE}" '
                 f'stroke-width="2.5" stroke-linecap="round"/>'
                 f'<polygon points="480,230 490,225 490,235" fill="{BLUE}"/>')
    parts.append(text(486, 222, 'VTH+ 6.15 V', 22, colour=BLUE, weight='700'))
    parts.append(text(330, 456, 'VTH− 5.85 V', 22, colour=BLUE, anchor='end', weight='700'))
    parts.append(f'<path d="M360,360 L480,360" stroke="{AMBER}" stroke-width="2" stroke-dasharray="4,4"/>')
    parts.append(text(420, 398, '305 mV', 22, colour=AMBER, anchor='middle', weight='700'))
    parts.append(box(650, 140, 300, 360, fill=PAPER))
    rows = [
        ('186', 'ΔV ≥ 2× 噪声峰峰'),
        ('248', '现场噪声 120 mV'),
        ('310', 'R2/R1 100:1'),
        ('372', '窗口约电源 1%'),
        ('434', '窗口也是判决盲区'),
    ]
    for y, line in rows:
        parts.append(text(674, int(y), line, 22, colour=INK if y != '434' else RED,
                          weight='700' if y in ('186', '434') else '400'))
    parts.append(box(50, 530, 900, 76, fill=PAPER))
    parts.append(text(74, 578, '先量噪声，再定电阻；窗口不是越大越安全。', 23, weight='700'))
    parts.append(text(500, 650, '小窗口抗扰，大窗口锁存；量变到质变。', 22, colour=AMBER,
                      anchor='middle'))
    return parts


def esr_window():
    parts = [header('LDO 的稳定区，写在一段 ESR 窗口里',
                    '老式 NPN 准 LDO 要 0.3–22 Ω；全贴 MLCC 的 5 mΩ 反而振荡。')]
    parts.append(f'<line x1="80" y1="410" x2="920" y2="410" stroke="{RULE}" stroke-width="2"/>')
    parts.append(f'<rect x="300" y="285" width="350" height="120" rx="10" fill="#e2ebe0" stroke="{GREEN}" stroke-width="2"/>')
    parts.append(text(475, 332, '稳定区 0.3–22 Ω', 26, colour=GREEN, anchor='middle', weight='700'))
    parts.append(text(475, 366, 'ESR 造出环路零点', 22, colour=INK2, anchor='middle'))
    parts.append(text(190, 332, '5 mΩ MLCC', 24, colour=RED, anchor='middle', weight='700'))
    parts.append(text(190, 366, '零点太远 → 振荡', 22, colour=RED, anchor='middle'))
    parts.append(text(790, 332, '>22 Ω', 24, colour=AMBER, anchor='middle', weight='700'))
    parts.append(text(790, 366, '零点太近 → 响应慢', 22, colour=AMBER, anchor='middle'))
    parts.append(box(50, 430, 430, 120, fill=PAPER))
    parts.append(text(74, 472, '10 µF 钽电容', 22, weight='700'))
    parts.append(text(74, 506, '是补偿的一部分，不是随便换', 22, colour=INK2))
    parts.append(box(520, 430, 430, 120, fill=PAPER))
    parts.append(text(544, 472, '10 µF MLCC', 22, weight='700'))
    parts.append(text(544, 506, '换之前先查手册的 ESR 窗口', 22, colour=INK2))
    parts.append(box(50, 570, 900, 60, fill=PAPER))
    parts.append(text(74, 610, '容量一样，不等于环路还稳；ESR 才是藏起来的参数。', 22,
                      weight='700', colour=AMBER))
    return parts


def reference_ladder():
    parts = [header('基准选型是一张精度阶梯',
                    '从 5% 稳压管到 0.3–2 ppm/°C 恒温齐纳；每往下一档，价格与功耗各涨约一个数量级。')]
    rows = [
        ('稳压二极管', '5% 级', '粗放场合', INK2),
        ('LM385 带隙', '1–3%', '10 µA 级', GREEN),
        ('TL431', '0.5–2%', '可调，分级', GREEN),
        ('REF50xx / ADR45xx', '0.05–0.1%', '3–10 ppm/°C', BLUE),
        ('LM399 埋入齐纳', '0.3–2 ppm/°C', '台表专用', AMBER),
    ]
    top, height, gap = 150, 78, 10
    parts.append(f'<line x1="40" y1="{top}" x2="40" y2="{top + 5 * (height + gap) - gap}" stroke="{RULE}" stroke-width="3"/>')
    for i, (name, precision, note, col) in enumerate(rows):
        y = top + i * (height + gap)
        parts.append(f'<line x1="40" y1="{y + height // 2}" x2="60" y2="{y + height // 2}" stroke="{RULE}" stroke-width="3"/>')
        parts.append(box(60, y, 560, height, fill=PAPER))
        parts.append(text(84, y + 32, name, 24, weight='700'))
        parts.append(text(84, y + 60, note, 22, colour=INK2))
        parts.append(text(650, y + 50, precision, 30, colour=col, weight='700'))
    parts.append(text(500, 640, '12 位配 REF50xx 是浪费，20 位配 TL431 是事故。', 23,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


SCENES = {
    'ch01-e24-ladder': {
        'draw': e24_ladder, 'title': 'E24 档位与 3.3k 的来历', 'anchor': '1.1',
        'chapter': 1, 'source': 'docs/p1-02-ch1.md',
        'alt': '手绘左右两栏：左栏算出 3.285k，落到 E24 货架档 3.3k，误差落在正负 5% 窗内；右栏列出 24 档、约 1.1 倍档比、正负 5% 容差与 E96 的正负 1%。底部写先选系列再选值，货架上没有 3.285k。',
    },
    'ch04-gate-window': {
        'draw': gate_window, 'title': '栅极保护的电压窗', 'anchor': '4.4',
        'chapter': 4, 'source': 'docs/p1-05-ch4.md',
        'alt': '手绘三条电压带：栅氧额定正负 20 伏、钳位 13 到 16 伏、驱动 12 伏；右栏写明钳位高于驱动且低于额定、栅源并 10 千欧下拉、开尔文源脚。底部写 12 伏驱动选 13 到 16 伏钳位。',
    },
    'ch04-deadtime-ledger': {
        'draw': deadtime_ledger, 'title': '死区损耗的明账', 'anchor': '4.4',
        'chapter': 4, 'source': 'docs/p1-05-ch4.md',
        'alt': '手绘公式与对照：每周期两段死区合计 100 纳秒，死区损耗等于 0.8 伏乘 5 安乘 100 纳秒乘 100 千赫，约 0.04 瓦即 40 毫瓦；同一只管子沟道压降 5 安乘 30 毫欧为 0.15 伏，体二极管为 0.8 伏。死区须覆盖实际关断延迟，不能按零设置。',
    },
    'ch05-rp-power': {
        'draw': rp_power, 'title': '上拉电阻自己的功耗', 'anchor': '5.2',
        'chapter': 5, 'source': 'docs/p1-06-ch5.md',
        'alt': '上拉电阻功率用电压平方除以电阻。低电平近零时三点三伏、一千欧约十一毫瓦；五伏、一百欧为二百五十毫瓦，超过示例四零二封装的十六分之一瓦额定。核对温度和脉冲负荷。',
    },
    'ch05-tristate-handover': {
        'draw': tristate_handover, 'title': '三态总线的交接时序', 'anchor': '5.4',
        'chapter': 5, 'source': 'docs/p1-06-ch5.md',
        'alt': '先禁用 A，等待实际禁用传播完成，再切方向和使能 B。禁用传播不等于无驱动空档；重叠十纳秒表示两路同时驱动十纳秒，须同时测使能、总线和电源电流。',
    },
    'ch07-hysteresis-window': {
        'draw': hysteresis_window, 'title': '迟滞窗口与两个阈值', 'anchor': '7.3',
        'chapter': 7, 'source': 'docs/p1-08-ch7.md',
        'alt': '手绘迟滞回环：上行阈值 6.15 伏、下行阈值 5.85 伏，窗口 305 毫伏，覆盖现场 120 毫伏噪声；右侧列出窗口至少为噪声峰峰两倍、R2 比 R1 为 100 比 1、窗口约电源 1%。底部写先量噪声再定电阻。',
    },
    'ch09-esr-window': {
        'draw': esr_window, 'title': 'LDO 的 ESR 稳定窗口', 'anchor': '9.3',
        'chapter': 9, 'source': 'docs/p1-10-ch9.md',
        'alt': '手绘 ESR 数轴：老式 NPN 准 LDO 的稳定区是 0.3 到 22 欧；左侧 5 毫欧的 MLCC 因零点太远而振荡，右侧大于 22 欧因零点太近而响应慢。底部写容量一样不等于环路还稳。',
    },
    'ch09-reference-ladder': {
        'draw': reference_ladder, 'title': '基准选型的精度阶梯', 'anchor': '9.1',
        'chapter': 9, 'source': 'docs/p1-10-ch9.md',
        'alt': '手绘五级精度阶梯：稳压二极管 5% 级、LM385 带隙 1 到 3%、TL431 0.5 到 2%、REF50xx 或 ADR45xx 0.05 到 0.1% 且 3 到 10 ppm 每摄氏度、LM399 埋入齐纳 0.3 到 2 ppm 每摄氏度。底部写 12 位配 REF50xx 是浪费，20 位配 TL431 是事故。',
    },
}

# Preserve corrected comparator models in historical batch entry points.
from scripts.visuals.scenes.ch07_reference_figures import SCENES as _ch07_corrected
SCENES['ch07-hysteresis-window'] = _ch07_corrected['ch07-hysteresis-window']

# Use source-bound reference/regulator models for historical batch rebuilds.
from scripts.visuals.scenes.ch09_reference_figures import SCENES as _ch09_corrected
SCENES['ch09-esr-window'] = _ch09_corrected['ch09-esr-window']
SCENES['ch09-reference-ladder'] = _ch09_corrected['ch09-reference-ladder']
