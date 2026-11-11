"""Wave 19 手绘草图：ch15 §15.2 接地——全书最后一个零图大空档（14002 字符）。

四张图的数字只取 15.2 小节原文；几何只表达分层与量级，不编码虚假数值。
印刷闸下限：1000px 画幅 @138mm 版心，8.5pt 对应 21.8px，正文一律 ≥22。
"""
from __future__ import annotations

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK, INK2, PAPER, RED, RULE, arrow, box, header, text,
)


def _bar(x, y, w, h, colour):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" '
            f'fill="{colour}" stroke="{INK}" stroke-width="1.4"/>')


def _larrow(x1, y1, x2, y2, colour=INK2, width=2.5):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour}" '
            f'stroke-width="{width}" stroke-linecap="round"/>'
            f'<polygon points="{x2},{y2} {x2 + 10},{y2 - 5} {x2 + 10},{y2 + 5}" fill="{colour}"/>')


def _dashed(parts, d, colour=RED, width=2.5, dash='7 5'):
    parts.append(f'<path d="{d}" stroke="{colour}" stroke-width="{width}" '
                 f'fill="none" stroke-dasharray="{dash}" stroke-linecap="round"/>')


def _rows(x, y0, gap, lines, size=22, colour=INK, anchor=None):
    out = []
    for i, line in enumerate(lines):
        c = colour if not isinstance(line, tuple) else line[1]
        s = line if isinstance(line, str) else line[0]
        out.append(text(x, y0 + i * gap, s, size,
                        colour=c if isinstance(line, tuple) else colour,
                        anchor=anchor or 'start'))
    return out


def return_mirror():
    parts = [header('高频回流是镜像电流',
                    '它不认识 GND 符号，只认电感最小的路：布线前先问这条信号的回家路通不通。')]
    parts.append(box(56, 126, 424, 304, fill=PAPER))
    parts.append(text(268, 162, '完整地平面', 26, anchor='middle', weight='700'))
    parts.append(_bar(120, 200, 300, 14, BLUE))
    parts.append(text(470, 214, '信号', 24, colour=BLUE, anchor='end'))
    parts.append(arrow(150, 190, 400, 190, BLUE, 2))
    parts.append(_bar(100, 330, 340, 16, INK))
    parts.append(_larrow(400, 312, 150, 312, GREEN, 2.5))
    parts.append(text(268, 292, '回流紧贴正下方', 22, colour=GREEN, anchor='middle'))
    parts.append(text(268, 372, '离地 0.2mm：集中在 ±1mm 内', 22, colour=INK2, anchor='middle'))
    parts.append(text(268, 408, '介质越薄，贴得越紧', 22, colour=INK2, anchor='middle'))
    parts.append(box(520, 126, 424, 304, fill=PAPER))
    parts.append(text(732, 162, '地平面开槽：桥被拆了', 26, colour=RED, anchor='middle', weight='700'))
    parts.append(_bar(570, 200, 250, 14, BLUE))
    parts.append(_bar(570, 330, 150, 16, INK))
    parts.append(_bar(790, 330, 130, 16, INK))
    parts.append(text(745, 348, '槽', 24, colour=RED, anchor='middle', weight='700'))
    _dashed(parts, 'M700,224 L700,318 Q700,392 745,392 Q790,392 790,318 L790,224')
    parts.append(arrow(748, 398, 786, 398, RED, 2))
    parts.append(text(732, 268, '绕路 = 大环路 = 天线', 24, colour=RED, anchor='middle', weight='700'))
    parts.append(text(732, 412, '离地 1mm 时回流铺开 ±5mm', 22, colour=INK2, anchor='middle'))
    parts.append(box(56, 456, 888, 214, fill=PAPER, stroke=INK2))
    parts.append(text(500, 492, '判据是回路围了多大，不是地通不通', 26, anchor='middle', weight='700'))
    parts.append(f'<line x1="90" y1="512" x2="910" y2="512" stroke="{RULE}" stroke-width="1.5"/>')
    parts.extend(_rows(90, 546, 42, [
        '低频拐弯省电阻，高频拐弯省电感',
        '反焊盘挤成奶酪缝：过孔排之间留横向铜通道，宽度至少等于孔距',
        ('万不得已跨分割：缝上并 1000pF–10nF，环路缩到电容两侧——补救不是方案', INK2),
    ]))
    return parts


def ground_bounce_ledger():
    parts = [header('地弹与精度：一笔一笔可复算的账',
                    '回流压在共享路径上的每一毫伏，都会叠在逻辑阈值和 ADC 的最低位上。')]
    cards = [
        (56, '回路电感账', [
            '线宽 0.25mm 离地 1mm', '电感 300~400nH/m', '5cm 走线 ≈15~20nH',
            '2ns 摆 3.3V、10pF 负载', ('V = L×di/dt ≈125mV', RED)], GREEN),
        (366, '总线的量级', [
            'di/dt ≈8.3mA/ns', 'I ≈16.5mA 峰值', '32 位总线同时翻转',
            '共享 1nH 就够', ('上百 mV 参考晃动', RED)], AMBER),
        (676, '基准的精度账', [
            '16 bit、3.3V 满量程', '1 LSB = 50µV', '10mΩ×5mA 脉冲电流',
            ('50µV 误差恰好吃掉一格', RED), '基准地独立回'], BLUE),
    ]
    for x, title, lines, colour in cards:
        parts.append(box(x, 126, 268, 300, fill=PAPER))
        parts.append(text(x + 134, 160, title, 25, colour=colour, anchor='middle', weight='700'))
        parts.append(f'<line x1="{x + 22}" y1="180" x2="{x + 246}" y2="180" stroke="{RULE}" stroke-width="1.5"/>')
        for i, line in enumerate(lines):
            s, c = (line, INK) if isinstance(line, str) else line
            parts.append(text(x + 134, 220 + i * 42, s, 22, colour=c,
                              anchor='middle', weight='700' if c == RED else '400'))
    parts.append(box(56, 452, 888, 218, fill=PAPER, stroke=INK2))
    parts.append(text(500, 488, '地弹怎么咬穿阈值', 26, anchor='middle', weight='700'))
    parts.append(f'<line x1="90" y1="508" x2="910" y2="508" stroke="{RULE}" stroke-width="1.5"/>')
    parts.extend(_rows(90, 542, 42, [
        'CMOS 低阈值约 0.3×VDD（3.3V 系统约 1V）；200mV 地弹即可咬穿 200mV 余量',
        '封装引线 2~10nH：64 脚给 8 对电源地，是把电感并到 1nH 以下，不是浪费',
        ('对策：去耦贴脸、多地过孔、安培级回路不共用一条返回支路', INK2),
    ]))
    return parts


def grounding_freq_split():
    parts = [header('频段决定接地策略',
                    '「一点接地」与「完整地平面」两派各执一词却都对——说的不是同一个频段。')]
    segs = [
        (56, 300, '单点（星形）', '1MHz 以下：电感可忽略', '各支路互不干扰', '#f0e3c2', AMBER),
        (356, 288, '混合区', '1MHz~10MHz', '电源大电流走单点\n信号回路走平面', '#e3e8dc', GREEN),
        (644, 300, '多点（平面）', '10MHz 以上：「点」失效', '让接地阻抗处处最小', '#dce4e8', BLUE),
    ]
    for x, w, name, band, note, fill, accent in segs:
        parts.append(f'<rect x="{x}" y="126" width="{w}" height="168" rx="8" fill="{fill}" stroke="{INK}" stroke-width="1.5"/>')
        parts.append(text(x + w / 2, 158, name, 26, colour=accent, anchor='middle', weight='700'))
        parts.append(text(x + w / 2, 192, band, 22, colour=INK, anchor='middle'))
        for j, line in enumerate(note.split('\n')):
            parts.append(text(x + w / 2, 224 + j * 30, line, 22, colour=INK2, anchor='middle'))
    _dashed(parts, 'M300,112 L300,300', colour=RED, width=2, dash='5 4')
    parts.append(text(300, 320, '100kHz 起星形隔离度快速退化', 22, colour=RED, anchor='middle'))
    parts.append(box(56, 348, 888, 322, fill=PAPER, stroke=INK2))
    parts.append(text(500, 384, '判据与验证', 26, anchor='middle', weight='700'))
    parts.append(f'<line x1="90" y1="404" x2="910" y2="404" stroke="{RULE}" stroke-width="1.5"/>')
    parts.extend(_rows(90, 442, 54, [
        '板长小于波长的 1/20 才当集总系统：单点才有效；超过就是分布系统，必须平面思维',
        '10cm 的板在 150MHz 处恰为 1/20——任何数字边沿都携带几十 MHz 以上成分',
        '缝合过孔：板边、晶振、接口按 5~10mm 打，空旷区可放宽到 20mm',
        ('首板实测：短地弹簧针量最远两个地测试点的交流压，几十 mV 尖峰即共享路径电感', INK2),
    ]))
    return parts


def stackup_and_bridge():
    parts = [header('叠层与跨分割：参考平面决定一切',
                    '信号层与其参考面的距离，决定回流贴得多紧、辐射有多大——比层数本身重要。')]
    stacks = [
        (56, '四层：信号—地—电源—信号', [
            ('信号', BLUE, 14), ('地', INK, 16), ('电源', AMBER, 16), ('信号', BLUE, 14)],
         '两种信号层各参考一地一电：跨层回流经去耦电容换平面，电容贴着换层过孔放', GREEN),
        (520, '六层：信号—地—信号—电源—地—信号', [
            ('信号', BLUE, 10), ('地', INK, 12), ('信号', BLUE, 10), ('电源', AMBER, 12),
            ('地', INK, 12), ('信号', BLUE, 10)],
         '每个信号层都配相邻参考平面：高速设计的甜点', BLUE),
    ]
    for x, title, layers, note, accent in stacks:
        parts.append(box(x, 126, 424, 336, fill=PAPER))
        parts.append(text(x + 212, 158, title, 23, colour=accent, anchor='middle', weight='700'))
        y = 184
        for name, colour, h in layers:
            parts.append(_bar(x + 46, y, 268, h, colour))
            parts.append(text(x + 330, y + h - 4, name, 24, colour=colour, anchor='start'))
            y += h + 12
        for j, chunk in enumerate([note[i:i + 17] for i in range(0, len(note), 17)]):
            parts.append(text(x + 212, 372 + j * 32, chunk, 22, colour=INK, anchor='middle'))
    parts.append(box(56, 488, 888, 182, fill=PAPER, stroke=INK2))
    parts.append(text(500, 522, '跨分割的补救与纪律', 26, anchor='middle', weight='700'))
    parts.append(f'<line x1="90" y1="540" x2="910" y2="540" stroke="{RULE}" stroke-width="1.5"/>')
    parts.extend(_rows(90, 574, 42, [
        '信号不许跨缝：必须跨就差分或光耦/磁隔离；半吊子分割比不割更糟（绕路＋缝隙天线）',
        '隔离两侧通信：缝下并 1000pF–10nF 小桥；Y 安规件容值受漏电流限制',
        ('双层板只剩一面地：尽量完整、不开槽，就是它的生存策略', INK2),
    ]))
    return parts


SCENES = {
    'ch15-return-mirror': {
        'draw': return_mirror,
        'title': '高频回流的镜像路',
        'anchor': '15.2 接地——模拟工程师的终极命题', 'chapter': 15,
        'source': 'docs/p3-02-ch15.md',
        'alt': '剖面对照：完整地平面时回流电流紧贴信号线正下方（离地 0.2mm 集中在 ±1mm 内、'
               '离地 1mm 铺开 ±5mm）；地平面开槽后回流被迫绕槽端走，环路撑大成为辐射天线。'
               '底部给出反焊盘奶酪缝的铜通道规则与 1000pF–10nF 跨分割桥接电容的补救定位。'},
    'ch15-ground-bounce-ledger': {
        'draw': ground_bounce_ledger,
        'title': '地弹与精度三笔账',
        'anchor': '15.2 接地——模拟工程师的终极命题', 'chapter': 15,
        'source': 'docs/p3-02-ch15.md',
        'alt': '三张账卡：0.25mm 线宽离地 1mm 的回路电感 300~400nH/m，5cm 约 15~20nH，'
               '2ns 摆 3.3V 时 V=L×di/dt 约 125mV；32 位总线同翻转共享 1nH 即上百 mV 晃动；'
               '16 bit 3.3V 满量程 1 LSB=50µV，10mΩ 共享铜上 5mA 脉冲刚好吃掉一格。'
               '下方说明 0.3×VDD 阈值被 200mV 地弹咬穿的链条与三条板级对策。'},
    'ch15-ground-freq-split': {
        'draw': grounding_freq_split,
        'title': '接地策略的频段分工',
        'anchor': '15.2 接地——模拟工程师的终极命题', 'chapter': 15,
        'source': 'docs/p3-02-ch15.md',
        'alt': '频段横条：1MHz 以下单点星形有效、1MHz 到 10MHz 电源走单点信号走平面、'
               '10MHz 以上只剩多点平面，100kHz 起星形隔离度快速退化。下方四条判据：'
               '板长小于波长的 1/20 才当集总（10cm 板在 150MHz 恰为 1/20）、'
               '缝合过孔板边晶振 5~10mm 空旷区 20mm、首板量最远两地测试点交流压。'},
    'ch15-stackup-bridge': {
        'draw': stackup_and_bridge,
        'title': '叠层与跨分割补救',
        'anchor': '15.2 接地——模拟工程师的终极命题', 'chapter': 15,
        'source': 'docs/p3-02-ch15.md',
        'alt': '两种常见叠层剖面：四层信号-地-电源-信号，跨层回流经去耦电容换平面、电容贴换层过孔；'
               '六层信号-地-信号-电源-地-信号，每个信号层配相邻参考面是高速甜点。'
               '下方给出分割纪律：信号不许跨缝，隔离两侧通信并 1000pF–10nF 桥、选 Y 电容安规件。'},
}
