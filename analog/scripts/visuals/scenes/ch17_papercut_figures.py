"""三张 FF-015 风险试片的具体构图；所有数值来自正文或明确坐标刻度。"""
from scripts.visuals.papercut import (
    PAPER, INK, SHADE, ACCENT, FACE, EDGE, sheet, text, line, arrow,
    chip, heatsink, meter, probe, soldering_iron)


def header(title, subtitle):
    return [text(78, 105, title, 52, weight='700', background=PAPER),
            text(80, 165, subtitle, 34, background=PAPER)]


def i2c():
    base = [sheet(60, 210, 920, 660), sheet(1018, 210, 366, 660), sheet(60, 920, 1324, 110)]
    labels = header('I²C 偶发失败，先查上升沿', '标准模式：上升时间 ≤ 1µs。上拉电阻越大，边沿越慢。')
    labels += [text(100, 278, 'Rp,max = tr / (0.8473 × Cb)', 41, weight='700'),
               text(102, 340, 'Rp / kΩ'), text(370, 842, '总线电容 Cb / pF')]
    x = lambda cb: 200 + cb / 400 * 690
    y = lambda rp: 770 - rp / 12 * 350
    labels += [arrow(200, 770, 940, 770), arrow(200, 770, 200, 375)]
    for value in (0, 10):
        labels += [text(176, y(value) + 10, str(value), anchor='end'), line(200, y(value), 920, y(value), SHADE, 1.5, '7 9')]
    labels += [text(x(400), 817, '400', anchor='middle')]
    points = ' '.join(f'{x(c):.2f},{y(1e6 / (.8473 * c) / 1000):.2f}' for c in range(100, 401, 2))
    labels += [f'<polyline points="{points}" stroke="{INK}" stroke-width="6" fill="none"/>',
               text(470, 422, '上限曲线'),
               line(x(400) - 13, y(10) - 13, x(400) + 13, y(10) + 13, ACCENT, 6),
               line(x(400) - 13, y(10) + 13, x(400) + 13, y(10) - 13, ACCENT, 6),
               text(590, 470, '10kΩ：超限', 36, ACCENT),
               f'<circle cx="{x(400)}" cy="{y(1e6 / (.8473 * 400) / 1000)}" r="10" fill="{FACE}" stroke="{INK}" stroke-width="5"/>',
               text(470, 730, '400pF → 约 2.9kΩ', 35),
               text(1050, 278, '上升沿等效', 36, weight='700'),
               text(1190, 355, 'VDD', anchor='middle'), line(1190, 370, 1190, 405),
               f'<rect x="1170" y="405" width="40" height="80" fill="{FACE}" stroke="{INK}" stroke-width="4"/>',
               text(1230, 450, 'Rp'), line(1190, 485, 1190, 545),
               f'<circle cx="1190" cy="545" r="6" fill="{INK}"/>',
               line(1090, 545, 1320, 545), line(1190, 545, 1190, 600),
               line(1155, 600, 1225, 600), line(1155, 620, 1225, 620),
               text(1240, 617, 'Cb'), line(1190, 620, 1190, 665),
               line(1160, 665, 1220, 665), line(1170, 677, 1210, 677), line(1180, 689, 1200, 689),
               text(1046, 760, '上升沿：电阻充电', 32), text(1046, 820, '下降沿：主动下拉', 32),
               text(94, 990, '先量边沿，再看协议；本图只核算上升时间约束。', 37, weight='700')]
    return base, labels


def thermal():
    base = [sheet(60, 210, 1324, 360), sheet(60, 615, 640, 285), sheet(744, 615, 640, 285),
            sheet(60, 930, 1324, 85), chip(155, 388, 100), sheet(490, 390, 125, 100, fill=EDGE),
            heatsink(842, 365, 180, 125)]
    labels = header('热要走完三段路，才到空气里', '同样耗散 3.5W，热阻链不同，结温估算相差很大。')
    labels += [text(100, 278, 'TJ = TA + P × (θJC + θCS + θSA)', 41, weight='700'),
               text(205, 350, '结', anchor='middle'), text(550, 350, '壳', anchor='middle'),
               text(935, 350, '散热器', anchor='middle'), text(1250, 350, '空气', anchor='middle'),
               arrow(280, 440, 460, 440, ACCENT), arrow(650, 440, 800, 440, ACCENT),
               arrow(1050, 440, 1315, 440, ACCENT),
               text(365, 535, 'θJC ≈ 3°C/W', 32, anchor='middle'),
               text(725, 535, 'θCS ≈ 1°C/W', 32, anchor='middle'),
               text(1185, 535, 'θSA ≈ 5°C/W', 32, anchor='middle'),
               text(100, 680, 'SOT-223 · θJA ≈ 60°C/W', 35, weight='700'),
               text(100, 770, '235°C', 72, ACCENT, weight='700'),
               text(100, 830, '25 + 3.5 × 60 = 235°C', 37),
               text(790, 680, 'TO-220 + 大散热器', 35, weight='700'),
               text(790, 770, '约 57°C', 72, weight='700'),
               text(790, 830, '25 + 3.5 × (3 + 1 + 5) ≈ 57°C', 32),
               text(95, 986, '结温目标 ≤125°C，另留 20°C 裕量；先核算实际封装与安装。', 32, weight='700'),
               text(80, 1064, '教学算例：TA = 25°C；热阻取正文示例值，不能代替具体器件数据。', 32, background=PAPER)]
    return base, labels


def priority():
    base = [sheet(200, 265, 560, 300), sheet(800, 265, 560, 300),
            sheet(200, 620, 560, 300), sheet(800, 620, 560, 300),
            meter(240, 325), chip(835, 330, 90), soldering_iron(830, 475),
            probe(246, 730), chip(840, 695, 95), sheet(860, 807, 60, 14, fill=EDGE)]
    labels = header('先查更可能、也更容易验证的故障', '定性决策示意：按故障概率与验证成本排序，不表示统计比例。')
    labels += [arrow(165, 920, 165, 240), text(80, 310, '高', 36, background=PAPER),
               text(80, 845, '低', 36, background=PAPER), text(80, 225, '概率', 34, background=PAPER),
               arrow(210, 955, 1380, 955), text(210, 1020, '容易验证', 36, background=PAPER),
               text(1050, 1020, '需要备料 / 拆焊', 34, background=PAPER),
               text(390, 340, '优先核验', 46, ACCENT, weight='700'),
               text(390, 415, '电源与连接', 38, weight='700'),
               text(390, 480, '先用万用表', 34), text(390, 535, '先静后动', 34),
               text(1000, 340, '先补证据', 40, weight='700'), text(1000, 420, '概率较高', 34),
               text(1000, 480, '拆焊前先测量', 34),
               text(390, 700, '快速排除', 40, weight='700'), text(390, 775, '记录结果', 34),
               text(390, 835, '缩小嫌疑范围', 34),
               text(1000, 700, '最后验证', 40, weight='700'), text(1000, 775, '概率较低', 34),
               text(1000, 835, '避免盲目换件', 34)]
    return base, labels


FIGURES = {
    'ch17-i2c-rise-time-budget': (i2c, 'I²C 上拉电阻与上升时间', '17.3', 'IG-015', 'V3'),
    'ch17-thermal-chain-audit': (thermal, '热阻链与结温估算', '17.5.1', 'IG-012', 'V3'),
    'ch17-prior-cost-matrix': (priority, '故障概率与验证成本决策图', '17.0', 'IG-014', 'V4'),
}
