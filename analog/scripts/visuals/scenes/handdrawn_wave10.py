"""Wave 10 手绘草图：二极管保护与结温、BJT 开关与组态。"""
from __future__ import annotations

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK, INK2, PAPER, RED, RULE, box, header, text,
)


def esd_chain():
    parts = [header('8kV 简化源：先分流，再限流',
                    '330Ω/150pF 近似：24.2A、223W；不代替 IEC 校准波形，100Ω 后仍灌 35mA。')]
    parts.append(text(52, 138, '8kV → TVS 9.2V → 100Ω → 芯片 5.7V', 22, colour=INK2))
    parts.append(box(50, 170, 430, 230, fill=PAPER))
    parts.append(text(74, 210, 'TVS 这一跳', 24, colour=RED, weight='700'))
    parts.append(text(74, 250, 'Ipp = (8000 − 9.2) / 330', 22))
    parts.append(text(74, 306, '= 24.2A', 40, colour=RED, weight='700'))
    parts.append(text(74, 346, 'Ppp = 9.2 × 24.2 = 223W', 22, colour=INK2))
    parts.append(text(74, 380, '选 IEC 8kV 阵列，不套 8/20µs 额定', 22, colour=INK2))
    parts.append(box(520, 170, 430, 230, fill=PAPER))
    parts.append(text(544, 210, '电阻后仍超', 24, colour=AMBER, weight='700'))
    parts.append(text(544, 250, 'Iinj = (9.2 − 5.7) / 100', 22))
    parts.append(text(544, 306, '= 35mA', 40, colour=AMBER, weight='700'))
    parts.append(text(544, 346, '要 10mA：R ≥ (9.2 − 5.7) / 0.01', 22, colour=INK2))
    parts.append(text(544, 380, '≥350Ω → 取 470Ω', 24, colour=GREEN, weight='700'))
    parts.append(box(50, 430, 900, 120, fill=PAPER))
    parts.append(text(76, 468, '100Ω 前移：总源阻 430Ω，约 18.6A、34.6kW（简化模型）。', 22,
                      colour=RED, weight='700'))
    parts.append(text(76, 504, '地回路 1nH × 24A/ns ≈ 24V，钳位形同虚设。', 22,
                      colour=INK2))
    parts.append(text(76, 536, 'TVS 泄放大能量，电阻把残压限到毫安级。', 22, colour=INK2))
    parts.append(text(500, 620, '只装 TVS 不算保护；电阻与芯片内部钳位才算收尾。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def zener_budget():
    parts = [header('稳压管炸机，多半是没串限流',
                    '12V ±10% → 5.1V，负载 0–20mA，最小稳流 5mA；先算 R，再算最坏功耗。')]
    parts.append(box(50, 150, 430, 250, fill=PAPER))
    parts.append(text(74, 192, '设计点', 25, colour=GREEN, weight='700'))
    parts.append(text(74, 236, 'R = (10.8 − 5.1) / (5 + 20)', 22))
    parts.append(text(74, 276, '= 228Ω', 32, colour=GREEN, weight='700'))
    parts.append(text(74, 316, '取 220Ω', 24, weight='700'))
    parts.append(text(74, 352, '最小稳流 5mA，负载 0–20mA', 22, colour=INK2))
    parts.append(box(520, 150, 430, 250, fill=PAPER))
    parts.append(text(544, 192, '最坏点：13.2V、空载', 24, colour=RED, weight='700'))
    parts.append(text(544, 234, 'Iz = (13.2 − 5.1) / 220', 22))
    parts.append(text(544, 270, '= 36.8mA', 28, colour=AMBER, weight='700'))
    parts.append(text(544, 308, 'Pz = 5.1 × 36.8mA', 22))
    parts.append(text(544, 344, '= 188mW', 28, colour=RED, weight='700'))
    parts.append(text(544, 378, '0.5W 管，余量 2.6×', 22, colour=INK2))
    parts.append(box(50, 430, 900, 120, fill=PAPER))
    parts.append(text(76, 472, '不串 R，直接并在 12V 上：电源当短路，瞬间烧毁。', 24,
                      colour=RED, weight='700'))
    parts.append(text(76, 510, '齐纳为稳态设计；TVS 为瞬态浪涌设计，不能互换。', 22,
                      colour=INK2))
    parts.append(text(500, 620, '先算 R，再算最坏功耗；余量不是拍脑袋。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def junction_margin():
    parts = [header('结温只剩 3°C，设计只做了一半',
                    '1A × 0.9V × 80°C/W，环境 50°C：Tj = 122°C，离 125°C 上限只差 3°C。')]
    parts.append(box(50, 150, 380, 320, fill=PAPER))
    parts.append(text(74, 192, '现在这一只', 24, colour=RED, weight='700'))
    rows = [
        ('环境', '50°C'),
        ('功耗', '0.9V × 1A'),
        ('热阻', '80°C/W'),
        ('结温', '50 + 0.9×80 = 122°C'),
    ]
    for i, (head, note) in enumerate(rows):
        y = 238 + i * 50
        parts.append(text(74, y, head, 22, colour=INK2))
        parts.append(text(160, y, note, 22, weight='700' if i == 3 else '400'))
    parts.append(text(74, 430, '余量只够环境再高 5°C。', 22, colour=INK2))
    parts.append(text(500, 250, '只剩', 22, colour=INK2, anchor='middle'))
    parts.append(text(500, 310, '3°C', 52, colour=RED, anchor='middle', weight='700'))
    parts.append(text(500, 350, '不是安全余量', 22, colour=RED, anchor='middle'))
    parts.append(box(570, 150, 380, 320, fill=PAPER))
    parts.append(text(594, 192, '上限 125°C', 24, colour=AMBER, weight='700'))
    rows = [
        ('环境再高', '5°C'),
        ('或电流再大', '10%'),
        ('结果', '就超了'),
        ('降额到 0.6A', 'Tj ≈ 93°C'),
    ]
    for i, (head, note) in enumerate(rows):
        y = 238 + i * 50
        parts.append(text(594, y, head, 22, colour=INK2))
        parts.append(text(790, y, note, 22, colour=GREEN if i == 3 else INK,
                          weight='700' if i == 3 else '400'))
    parts.append(text(594, 430, '降额、换低 VF 管、加散热片。', 22, colour=INK2))
    parts.append(box(50, 500, 900, 90, fill=PAPER))
    parts.append(text(76, 538, '8.3ms 单次浪涌不能当重复值。', 22,
                      colour=RED, weight='700'))
    parts.append(text(76, 574, '峰值功率一定带脉宽与占空比；脉冲越窄，允许峰值越高。', 22,
                      colour=INK2))
    parts.append(text(500, 640, '结温是闭环，不是单点；余量没了就降额或换封装。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def parallel_hog():
    parts = [header('两只二极管并联，越热的那只越抢电流',
                    'VF 负温度系数：电流大 → 先热 → VF 降 → 分到更多电流。')]
    parts.append(box(50, 140, 480, 360, fill=PAPER))
    parts.append(f'<line x1="100" y1="430" x2="510" y2="430" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(f'<line x1="100" y1="430" x2="100" y2="170" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(text(470, 462, 'V', 22, colour=INK2))
    parts.append(text(78, 182, 'I', 22, colour=INK2))
    parts.append(f'<path d="M140,400 C240,380 360,300 500,230" fill="none" stroke="{BLUE}" stroke-width="4"/>')
    parts.append(f'<path d="M140,400 C240,350 360,260 500,190" fill="none" stroke="{RED}" stroke-width="4"/>')
    parts.append(f'<line x1="360" y1="430" x2="360" y2="285" stroke="{AMBER}" stroke-width="2" stroke-dasharray="6,5"/>')
    parts.append(text(360, 458, '同一 V', 22, colour=AMBER, anchor='middle', weight='700'))
    parts.append(text(300, 250, '冷管', 22, colour=BLUE, weight='700'))
    parts.append(text(300, 210, '热管', 22, colour=RED, weight='700'))
    parts.append(text(104, 410, '曲线左移 = 同压下电流更大', 22, colour=INK2))
    parts.append(box(560, 150, 390, 330, fill=PAPER))
    parts.append(text(584, 192, '为什么不能直接并联', 24, weight='700'))
    rows = [
        ('二极管 / BJT', '负温度系数：热者更热'),
        ('MOSFET', '正温度系数：天生适合并联'),
        ('LED 并联', '每串一颗小电阻 = 人为正 TC'),
        ('对策', '均流电阻 / 热耦合 / 降额'),
    ]
    for i, (head, note) in enumerate(rows):
        y = 236 + i * 56
        parts.append(text(584, y, head, 22, colour=[RED, GREEN, AMBER, BLUE][i], weight='700'))
        parts.append(text(584, y + 26, note, 22, colour=INK2))
    parts.append(text(500, 560, '−2mV/°C 是趋势，不是精确常数；并联前先算均流。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    parts.append(text(52, 640, '负温度系数让强者更强；这就是并联难的原因。', 22, colour=INK2))
    return parts


def switch_budget():
    parts = [header('基极电阻拍脑袋，继电器就不吸合',
                    '5V/70mA 线圈：强制 β=10，IB=7mA，RB≈371Ω，就近取 360Ω。')]
    parts.append(box(50, 150, 430, 330, fill=PAPER))
    parts.append(text(74, 192, '按强制 β=10', 24, colour=GREEN, weight='700'))
    rows = [
        'IC = 70mA',
        'IB = 70 / 10 = 7mA',
        'RB = (3.3 − 0.7) / 7mA ≈ 371Ω',
        '取 360Ω → βforced ≈ 9.7',
        'P = 0.2V × 70mA = 14mW',
    ]
    for i, line in enumerate(rows):
        parts.append(text(74, 238 + i * 46, line, 22,
                          colour=GREEN if i == 3 else INK))
    parts.append(text(74, 456, '线圈得 4.8V，吸合余量足。', 22, colour=INK2))
    parts.append(box(520, 150, 430, 330, fill=PAPER))
    parts.append(text(544, 192, '拍脑袋 10kΩ', 24, colour=RED, weight='700'))
    rows = [
        'IB = (3.3 − 0.7) / 10kΩ',
        '= 0.26mA',
        '要吸合需 β ≥ 269',
        'β=100 时 IC 只有 26mA',
        'VCE ≈ 3.2V，P ≈ 83mW',
        '线圈只有 1.8V，不吸合',
    ]
    for i, line in enumerate(rows):
        parts.append(text(544, 238 + i * 42, line, 22,
                          colour=RED if i >= 3 else INK))
    parts.append(box(50, 510, 900, 80, fill=PAPER))
    parts.append(text(76, 548, '先按 IC 算 IB，再按 IB 算 RB；标称 β 不是饱和保证。', 22,
                      weight='700'))
    parts.append(text(76, 578, '负载越大，强制 β 越要小；20 是肌肉记忆的上限。', 22,
                      colour=INK2))
    parts.append(text(500, 650, '强制 β=10 是把余量写进电阻，不是相信管子给面子。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def low_high_side():
    parts = [header('低边开关踩在地上，高边开关浮在电源上',
                    'NPN 低边：基极只要 0.7V；NPN 高边：基极要到负载压降 + 0.7V。')]
    parts.append(box(50, 150, 430, 330, fill=PAPER))
    parts.append(text(74, 192, '低边 NPN（推荐）', 24, colour=GREEN, weight='700'))
    parts.append(f'<line x1="80" y1="225" x2="450" y2="225" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(text(400, 216, '12V', 22, colour=INK2))
    parts.append(f'<line x1="220" y1="225" x2="220" y2="250" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(box(160, 250, 120, 56, fill=PAPER))
    parts.append(text(220, 286, '负载', 22, anchor='middle'))
    parts.append(f'<line x1="220" y1="306" x2="220" y2="335" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(box(170, 335, 100, 56, fill=PAPER))
    parts.append(text(220, 371, 'NPN', 22, anchor='middle', weight='700'))
    parts.append(f'<line x1="220" y1="391" x2="220" y2="420" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(f'<line x1="196" y1="420" x2="244" y2="420" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(f'<line x1="204" y1="432" x2="236" y2="432" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(f'<line x1="170" y1="363" x2="120" y2="363" stroke="{AMBER}" stroke-width="2.5"/>')
    parts.append(text(82, 370, '0.7V', 22, colour=AMBER, weight='700'))
    parts.append(text(82, 455, '基极以地为参考：3.3V GPIO 直推。', 22, colour=INK2))
    parts.append(box(520, 150, 430, 330, fill=PAPER))
    parts.append(text(544, 192, '高边 NPN（够不着）', 24, colour=RED, weight='700'))
    parts.append(f'<line x1="550" y1="225" x2="920" y2="225" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(text(870, 216, '12V', 22, colour=INK2))
    parts.append(f'<line x1="690" y1="225" x2="690" y2="250" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(box(630, 250, 120, 56, fill=PAPER))
    parts.append(text(690, 286, 'NPN', 22, anchor='middle', weight='700'))
    parts.append(f'<line x1="690" y1="306" x2="690" y2="335" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(box(630, 335, 120, 56, fill=PAPER))
    parts.append(text(690, 371, '负载', 22, anchor='middle'))
    parts.append(f'<line x1="690" y1="391" x2="690" y2="420" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(f'<line x1="666" y1="420" x2="714" y2="420" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(f'<line x1="674" y1="432" x2="706" y2="432" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(f'<line x1="630" y1="278" x2="580" y2="278" stroke="{AMBER}" stroke-width="2.5"/>')
    parts.append(text(536, 442, '基极要抬到 负载 + 0.7V；', 22, colour=INK2))
    parts.append(text(536, 470, '3.3V GPIO 够不着。', 22, colour=INK2))
    parts.append(box(50, 510, 900, 80, fill=PAPER))
    parts.append(text(76, 548, '高边解法：PNP + 一级 NPN 预驱；3.3V 逻辑不能直推 12V。', 22,
                      weight='700'))
    parts.append(text(76, 578, '分不清高低边之前，一律低边。', 22, colour=INK2))
    parts.append(text(500, 650, '参考点决定驱动电压；低边把参考点踩在地上。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def reverse_beta():
    parts = [header('C、E 插反，β 只剩个位数',
                    '发射区重掺杂、集电区轻掺杂：结构不对称，反过来用就露底。')]
    parts.append(box(50, 150, 430, 330, fill=PAPER))
    parts.append(text(74, 192, '正常接法', 24, colour=GREEN, weight='700'))
    layers = [
        (210, 'C：轻掺杂、体积大', BLUE),
        (280, 'B：极薄、轻掺杂', AMBER),
        (350, 'E：重掺杂 N+', GREEN),
    ]
    for y, label, colour in layers:
        parts.append(box(100, y, 300, 56, fill=PAPER,
                         stroke=colour, width=2.5))
        parts.append(text(116, y + 36, label, 22, colour=colour, weight='700'))
    parts.append(f'<line x1="430" y1="370" x2="430" y2="250" stroke="{GREEN}" stroke-width="2.5"/>')
    parts.append(f'<polygon points="430,240 424,252 436,252" fill="{GREEN}"/>')
    parts.append(text(74, 440, '绝大多数电子直达 C，少数在基区复合', 22, colour=INK2))
    parts.append(box(520, 150, 430, 330, fill=PAPER))
    parts.append(text(544, 192, 'C/E 反接', 24, colour=RED, weight='700'))
    layers = [
        (210, 'E（当 C 用）', RED),
        (280, 'B', AMBER),
        (350, 'C（当 E 用）', RED),
    ]
    for y, label, colour in layers:
        parts.append(box(570, y, 300, 56, fill=PAPER,
                         stroke=colour, width=2.5))
        parts.append(text(586, y + 36, label, 22, colour=colour, weight='700'))
    parts.append(text(544, 440, '反向 β 只有 2–10；BVEBO 只有 5–7V', 22, colour=INK2))
    parts.append(box(50, 500, 900, 100, fill=PAPER))
    parts.append(text(76, 540, '结构决定：发射区重掺杂、基区极薄、集电区轻掺杂大体积。', 22,
                      weight='700'))
    parts.append(text(76, 576, '插反的症状：增益低到离谱；先量 VBE、核脚序，再怀疑管子。', 22,
                      colour=INK2))
    parts.append(text(500, 650, 'BJT 天生不对称，反接不是另一种用法。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def config_impedance():
    parts = [header('三种组态，是同一条折算律的三个方向',
                    '从发射极看，阻抗除以 (β+1)；从基极看，阻抗乘以 (β+1)。')]
    parts.append(box(60, 150, 270, 110, fill=PAPER))
    parts.append(text(84, 190, '共射 CE', 24, colour=GREEN, weight='700'))
    parts.append(text(84, 222, 'B 进 C 出', 22, colour=INK2))
    parts.append(text(84, 250, '增益高、反相', 22, colour=INK2))
    parts.append(box(670, 150, 270, 110, fill=PAPER))
    parts.append(text(694, 190, '共集 CC', 24, colour=BLUE, weight='700'))
    parts.append(text(694, 222, 'B 进 E 出', 22, colour=INK2))
    parts.append(text(694, 250, '电压 ≈1、同相', 22, colour=INK2))
    parts.append(box(365, 430, 270, 110, fill=PAPER))
    parts.append(text(389, 470, '共基 CB', 24, colour=AMBER, weight='700'))
    parts.append(text(389, 502, 'E 进 C 出', 22, colour=INK2))
    parts.append(text(389, 530, '高频、同相', 22, colour=INK2))
    parts.append(box(370, 300, 260, 90, fill=PAPER))
    parts.append(text(500, 338, '折算律 (β+1)', 24, anchor='middle', weight='700'))
    parts.append(text(500, 370, '看进去的方向', 22, colour=INK2, anchor='middle'))
    parts.append(f'<line x1="330" y1="260" x2="410" y2="300" stroke="{RULE}" stroke-width="2"/>')
    parts.append(f'<line x1="670" y1="260" x2="590" y2="300" stroke="{RULE}" stroke-width="2"/>')
    parts.append(f'<line x1="500" y1="390" x2="500" y2="430" stroke="{RULE}" stroke-width="2"/>')
    parts.append(box(50, 560, 900, 70, fill=PAPER))
    parts.append(text(76, 600, '10kΩ 源、β=100、IE=1mA：rπ≈2.6kΩ；管内看入 ≈125Ω。', 22,
                      weight='700'))
    parts.append(text(500, 660, '共射出增益、共集出电流、共基出频率。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    return parts


def early_effect():
    parts = [header('输出特性不是水平线，是微微上翘',
                    'VCE 升 → 集电结耗尽层变宽 → 有效基区变薄 → β 微升。')]
    parts.append(box(50, 140, 500, 380, fill=PAPER))
    parts.append(f'<line x1="60" y1="460" x2="510" y2="460" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(f'<line x1="100" y1="460" x2="100" y2="170" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(text(470, 490, 'VCE', 22, colour=INK2))
    parts.append(text(78, 182, 'IC', 22, colour=INK2))
    for i, (y0, colour) in enumerate([(380, BLUE), (310, GREEN), (240, AMBER)]):
        parts.append(f'<path d="M150,{y0} C280,{y0 - 4} 400,{y0 - 16} 500,{y0 - 28}" '
                     f'fill="none" stroke="{colour}" stroke-width="4"/>')
        parts.append(f'<path d="M150,{y0} L60,460" fill="none" stroke="{colour}" '
                     f'stroke-width="1.6" stroke-dasharray="5,5"/>')
    parts.append(text(56, 500, '虚线交于 −VA', 22, colour=INK2))
    parts.append(text(300, 205, '曲线间距 = β', 22, colour=INK2))
    parts.append(text(300, 235, '斜率 = 1/ro', 22, colour=INK2))
    parts.append(box(580, 150, 370, 330, fill=PAPER))
    parts.append(text(604, 192, '厄利效应', 24, colour=RED, weight='700'))
    rows = [
        ('VA', '50–100V（小信号管）'),
        ('ro = VA / IC', '1mA、VA=100V → 100kΩ'),
        ('开关 / 低频', '可当无穷大'),
        ('电流源 / 有源负载', 'ro 是精度天花板'),
    ]
    for i, (head, note) in enumerate(rows):
        y = 238 + i * 56
        parts.append(text(604, y, head, 22, colour=[AMBER, GREEN, INK2, RED][i],
                          weight='700'))
        parts.append(text(604, y + 26, note, 22, colour=INK2))
    parts.append(text(500, 570, 'VCE 一变，IC 跟着变；这就是输出阻抗的来处。', 22,
                      colour=AMBER, anchor='middle', weight='700'))
    parts.append(text(52, 640, '日常开关可忽略；做电流源时，ro 决定精度。', 22, colour=INK2))
    return parts


SCENES = {
    'ch02-esd-chain': {
        'draw': esd_chain, 'title': 'IEC 8kV 的 24A 分账', 'anchor': '2.11.3',
        'chapter': 2, 'source': 'docs/p1-03-ch2.md',
        'alt': '8 千伏简化 RC 源：330 欧、150 皮法，不代替 IEC 校准波形；TVS 钳到 9.2 伏，估算 24.2 安、223 瓦。100 欧后向芯片注入 35 毫安；10 毫安目标需至少 350 欧，选 470 欧。100 欧前移时总源阻 430 欧，约 18.6 安、34.6 千瓦。地回路 1 纳亨乘 24 安每纳秒产生 24 伏压降。',
    },
    'ch02-zener-budget': {
        'draw': zener_budget, 'title': '稳压管的限流电阻与最坏功耗', 'anchor': '2.9',
        'chapter': 2, 'source': 'docs/p1-03-ch2.md',
        'alt': '手绘两栏稳压管算账：左栏 12 伏正负 10% 降到 5.1 伏，负载 0 到 20 毫安、最小稳流 5 毫安，电阻为 10.8 减 5.1 除以 25 毫安等于 228 欧，取 220 欧；右栏最坏 13.2 伏空载，稳流 36.8 毫安、功耗 188 毫瓦，选 0.5 瓦留 2.6 倍余量。底部写不串电阻直接并在 12 伏上会瞬间烧毁。',
    },
    'ch02-junction-margin': {
        'draw': junction_margin, 'title': '结温余量只剩 3°C', 'anchor': '2.9',
        'chapter': 2, 'source': 'docs/p1-03-ch2.md',
        'alt': '手绘结温账：1 安乘 0.9 伏乘 80 摄氏度每瓦，环境 50 摄氏度，结温 122 摄氏度；上限 125 摄氏度，只剩 3 摄氏度。右侧写环境再高 5 摄氏度或电流再大 10% 就超，降额到 0.6 安后结温约 93 摄氏度。底部写 8.3 毫秒单次浪涌不能当重复值，峰值功率一定带脉宽与占空比。',
    },
    'ch02-parallel-hog': {
        'draw': parallel_hog, 'title': '并联二极管的热抢流', 'anchor': '2.9',
        'chapter': 2, 'source': 'docs/p1-03-ch2.md',
        'alt': '手绘伏安曲线：热的二极管曲线左移，同一电压下电流更大；冷的曲线在右边。右侧写二极管与 BJT 是负温度系数，热者更热；MOSFET 是正温度系数，天生适合并联；LED 每串一颗小电阻等于人为制造正温度系数。底部写负温度系数让强者更强。',
    },
    'ch03-switch-budget': {
        'draw': switch_budget, 'title': '继电器基极电阻的两笔账', 'anchor': '3.5',
        'chapter': 3, 'source': 'docs/p1-04-ch3.md',
        'alt': '手绘继电器驱动两栏：左栏 5 伏 70 毫安线圈，强制贝塔 10，基流 7 毫安，基极电阻约 371 欧取 360 欧，饱和压降 0.2 伏、功耗 14 毫瓦；右栏拍脑袋取 10 千欧，基流 0.26 毫安，要吸合需贝塔 269，贝塔 100 时只有 26 毫安，压降 3.2 伏、功耗 83 毫瓦，线圈只有 1.8 伏不吸合。',
    },
    'ch03-low-high-side': {
        'draw': low_high_side, 'title': '低边与高边开关的参考点', 'anchor': '3.5',
        'chapter': 3, 'source': 'docs/p1-04-ch3.md',
        'alt': '手绘两个开关电路：低边 NPN 的负载接 12 伏、发射极接地，基极只要 0.7 伏，3.3 伏 GPIO 可直推；高边 NPN 的集电极接 12 伏、发射极接负载，基极要抬到负载压降加 0.7 伏，3.3 伏 GPIO 够不着。底部写高边解法是 PNP 加一级 NPN 预驱。',
    },
    'ch03-reverse-beta': {
        'draw': reverse_beta, 'title': 'C/E 反接为什么β只剩个位数', 'anchor': '3.2',
        'chapter': 3, 'source': 'docs/p1-04-ch3.md',
        'alt': '手绘 BJT 三层结构对照：正常接法从下到上是重掺杂发射区、极薄轻掺杂基区、轻掺杂大体积集电区，绝大多数电子直达集电极；反接把 C 当 E、E 当 C，反向贝塔只有 2 到 10，发射结反向耐压只有 5 到 7 伏。底部写插反的症状是增益低到离谱，先量 VBE、核脚序。',
    },
    'ch03-config-impedance': {
        'draw': config_impedance, 'title': '三种组态共用一条阻抗折算律', 'anchor': '3.3',
        'chapter': 3, 'source': 'docs/p1-04-ch3.md',
        'alt': '手绘三种组态与阻抗折算律：共射反相放大，共集同相缓冲，共基输入阻抗低。从发射极看，基极回路阻抗除以贝塔加一。10 千欧源、贝塔 100、IE 1 毫安、rπ 约 2.6 千欧，从发射极看入管内约 125 欧，端口还须并联发射极电阻。',
    },
    'ch03-early-effect': {
        'draw': early_effect, 'title': '厄利效应与输出阻抗', 'anchor': '3.1',
        'chapter': 3, 'source': 'docs/p1-04-ch3.md',
        'alt': '手绘输出特性曲线：三条曲线随 VCE 升高微微上翘，向左虚线延长交于负电压 VA；曲线间距是贝塔，斜率是 1/ro。右侧写小信号管 VA 为 50 到 100 伏；1 毫安、VA 100 伏时 ro 约 100 千欧；开关和低频放大可当无穷大，电流源与有源负载里 ro 是精度天花板。',
    },
}
