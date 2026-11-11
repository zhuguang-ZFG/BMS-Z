"""PCB 校样：单位一致的简化模型与明确的适用边界。"""
from __future__ import annotations

import math

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER,
    BLUE,
    GREEN,
    INK2,
    PAPER,
    RED,
    RULE,
    box,
    header,
    text,
)
from scripts.visuals.scenes.handdrawn_wave3 import varrow


def resonance_hz(inductance_h: float, capacitance_f: float) -> float:
    if min(inductance_h, capacitance_f) <= 0:
        raise ValueError('L、C 必须为正')
    return 1 / (2 * math.pi * math.sqrt(inductance_h * capacitance_f))


def via_inductance_nh(height_mm: float, diameter_mm: float) -> float:
    if min(height_mm, diameter_mm) <= 0:
        raise ValueError('过孔尺寸必须为正')
    # This empirical expression uses inches, not millimetres.
    return 5.08 * height_mm / 25.4 * (math.log(4 * height_mm / diameter_mm) + 1)


def parallel_inductance(self_nh: float, mutual_nh: float, count: int) -> float:
    """Identical branches, equal currents and equal pairwise mutual inductance."""
    if count < 1 or self_nh <= 0 or not 0 <= mutual_nh <= self_nh:
        raise ValueError('本示意仅支持正自感、非负互感与正整数支路数')
    return (self_nh + (count - 1) * mutual_nh) / count


def decap_resonance():
    p = [header('同一电容，谐振点随回路电感移动',
                '示意 C = 100 nF；忽略 ESR，L 是完整支路的串联电感。')]
    x0, x1, y0 = 230, 890, 540
    p += [text(70, 155, 'L / nH', 24, weight='700'),
          text(560, 592, '理想串联谐振频率 f₀ / MHz', 24, anchor='middle')]
    p.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="{INK2}" stroke-width="2"/>')
    for mhz in (0, 5, 10, 15):
        x = x0 + mhz / 18 * (x1-x0)
        p += [f'<line x1="{x}" y1="180" x2="{x}" y2="545" stroke="{RULE}" stroke-dasharray="4 5"/>',
              text(x, 572, str(mhz), 22, anchor='middle')]
    for i, nh in enumerate((1, 5, 8, 10)):
        mhz = resonance_hz(nh * 1e-9, 100e-9) / 1e6
        y = 210 + i * 86
        x = x0 + mhz / 18 * (x1-x0)
        p += [text(100, y+8, str(nh), 26, anchor='middle', weight='700'),
              f'<line x1="{x0}" y1="{y}" x2="{x}" y2="{y}" stroke="{BLUE}" stroke-width="4"/>',
              f'<circle cx="{x}" cy="{y}" r="7" fill="{PAPER}" stroke="{BLUE}" stroke-width="3"/>',
              text(x+18, y+8, f'{mhz:.2f}', 23, colour=BLUE, weight='700')]
    p += [text(60, 635, 'f₀ = 1 / (2π√LC)；实际阻抗还含 ESR、平面与其他电容。', 22),
          text(60, 674, '高于 f₀ 呈感性，不等于完全失去去耦作用；须对照目标阻抗。', 22, colour=INK2)]
    return p


def via_parallel():
    inductance = via_inductance_nh(1.6, .3)
    p = [header('四个过孔并联，不能只背四分之一',
                '示意 h = 1.6 mm、d = 0.3 mm；经验式算单孔 L ≈ 1.299 nH。')]
    p.append(text(60, 145, '相同支路、均匀分流；每对过孔互感均为 M', 23, colour=INK2))
    for y in (210, 410):
        p.append(f'<line x1="120" y1="{y}" x2="880" y2="{y}" stroke="{INK2}" stroke-width="3"/>')
    for i in range(4):
        x = 200 + 200*i
        p += [varrow(x, 220, x, 270, BLUE, 3),
              box(x-54, 280, 108, 72), text(x, 326, 'L', 28, anchor='middle'),
              f'<line x1="{x}" y1="352" x2="{x}" y2="410" stroke="{INK2}" stroke-width="3"/>']
    p.append(text(500, 460, 'L等效 = [L + (N−1)M] / N，N = 4', 26, anchor='middle', weight='700'))
    p += [text(70, 522, f'忽略互感 M = 0 → {parallel_inductance(inductance, 0, 4):.3f} nH', 24, colour=GREEN),
          text(70, 568, f'示意 M = L/2 → {parallel_inductance(inductance, inductance/2, 4):.3f} nH', 24, colour=RED),
          text(60, 628, '实际电感取决于孔间距和回流几何；载流能力另核孔铜、温升与分流。', 22),
          text(60, 668, '信号换层同时安排参考面的连接，不能只数信号过孔。', 22, colour=INK2)]
    return p


def line_flight():
    p = [header('看边沿传播时间，不只看时钟频率',
                '示意速度 v = 15 cm/ns；t飞行 = l/v，筛查线取 t飞行 = tr/6。')]
    for y, tr, colour in ((180, 1, BLUE), (390, 20, AMBER)):
        p += [text(60, y, f'边沿 tr = {tr} ns', 26, colour=colour, weight='700'),
              text(60, y+46, f'筛查长度 l = {15*tr/6:g} cm', 24)]
        for i in range(7):
            x = 420 + i*75
            p.append(f'<line x1="{x}" y1="{y+12}" x2="{x}" y2="{y+40}" stroke="{INK2}" stroke-width="2"/>')
        p += [f'<line x1="420" y1="{y+26}" x2="870" y2="{y+26}" stroke="{INK2}" stroke-width="2"/>',
              f'<rect x="420" y="{y+13}" width="75" height="26" fill="{colour}" opacity="0.5"/>',
              text(420, y+82, '0', 22, anchor='middle'),
              text(495, y+82, 'tr/6', 22, anchor='middle'),
              text(870, y+82, 'tr', 22, anchor='middle')]
    p += [text(60, 560, '两条轴分别按各自 tr 归一化，彩段都是六分之一。', 22, colour=INK2),
          text(60, 614, '这是启动传输线分析的经验筛查，不是安全或协议合规分界。', 22),
          text(60, 660, '串联端接：驱动器输出电阻 + 串阻 ≈ Z₀；同时核负载与分支。', 22)]
    return p


def filter_modes():
    p = [header('先辨电流方向，再选择滤波网络',
                '定义两根线的正方向都从源指向负载；箭头表示同一时刻。')]
    for x, common, colour in ((50, False, BLUE), (520, True, RED)):
        p.append(box(x, 145, 430, 370))
        p.append(text(x+24, 188, '共模：同向' if common else '差模：反向', 26, colour=colour, weight='700'))
        p += [box(x+24, 240, 64, 150), text(x+56, 320, '源', 24, anchor='middle'),
              box(x+340, 240, 64, 150), text(x+372, 320, '载', 24, anchor='middle')]
        p.append(varrow(x+94, 270, x+332, 270, colour, 3))
        p.append(varrow(x+94 if common else x+332, 360,
                           x+332 if common else x+94, 360, colour, 3))
        if common:
            p.append(varrow(x+332, 425, x+94, 425, INK2, 2))
        p.append(text(x+215, 474, '经寄生/机壳路径返回' if common else '在线对内闭合',
                      22, anchor='middle', colour=INK2))
    p += [text(60, 560, 'Icm = (I1+I2)/2；Idm = (I1−I2)/2。', 24, weight='700'),
          text(60, 602, '同向穿钳的两根线测得 I1+I2 = 2Icm；差模理想抵消。', 22),
          text(60, 642, '差模：跨线电容与串联阻抗；共模：扼流圈与受控回流路径。', 22),
          text(60, 678, '市电滤波器须另核安规等级、隔离和漏电流；不统一指定 Y 电容值。', 22, colour=INK2)]
    return p


def microstrip_width_mm(z_ohm: float, height_mm: float,
                        thickness_mm: float = .035, er: float = 4.2) -> float:
    """Algebraic inversion of the stated IPC-2141 approximation, not a solver."""
    return (5.98 * height_mm / math.exp(z_ohm * math.sqrt(er+1.41)/87)
            - thickness_mm) / .8


def impedance_geometry():
    p = [header('同一阻抗，线宽随叠层改变',
                '示意 50 Ω 微带：εr = 4.2、铜厚 0.035 mm；使用同一近似式。')]
    for x, h, colour in ((50, 1.6, BLUE), (520, .2, GREEN)):
        w = microstrip_width_mm(50, h)
        p += [box(x, 150, 430, 360),
              text(x+24, 192, f'参考面距离 h = {h:g} mm', 24, colour=colour, weight='700'),
              text(x+215, 260, f'w ≈ {w:.3f} mm', 28, anchor='middle', weight='700'),
              f'<rect x="{x+130}" y="300" width="170" height="14" fill="{colour}"/>',
              f'<rect x="{x+60}" y="320" width="310" height="70" fill="{PAPER}" stroke="{RULE}"/>',
              f'<line x1="{x+60}" y1="398" x2="{x+370}" y2="398" stroke="{INK2}" stroke-width="6"/>',
              text(x+215, 448, '信号铜 → 介质 → 参考面', 22, anchor='middle', colour=INK2),
              text(x+215, 486, '剖面示意，不按尺寸比例', 22, anchor='middle', colour=INK2)]
    p += [text(60, 562, 'Z₀ ≈ 87/√(εr+1.41) × ln[5.98h/(0.8w+t)]', 24),
          text(60, 610, '双层板也能控阻抗；粗线占空间，须与板厂确认实际叠层与公差。', 22),
          text(60, 658, '差分阻抗还取决于线间耦合，不能由这条单端公式直接推出。', 22, colour=INK2)]
    return p


def input_filter():
    p = [header('输入滤波：先算谐振，再查阻尼与交互',
                '示意 C入 = C出 = 10 µF、L = 1 µH；不承诺固定插入损耗。')]
    p += [box(50, 220, 140, 100), text(120, 278, '电源', 26, anchor='middle'),
          box(770, 220, 180, 100), text(860, 278, 'Buck', 26, anchor='middle'),
          f'<path d="M190 250 H440 M560 250 H770 M120 320 V420 H860 V320" fill="none" stroke="{INK2}" stroke-width="3"/>',
          box(440, 224, 120, 52), text(500, 259, 'L', 24, anchor='middle')]
    for x, name in ((300, 'C入'), (670, 'C出')):
        p += [f'<path d="M{x} 250 V320 M{x-32} 320 H{x+32} M{x-32} 338 H{x+32} M{x} 338 V420" '
              f'fill="none" stroke="{BLUE}" stroke-width="3"/>',
              text(x+42, 350, name, 23, colour=BLUE)]
    f0 = resonance_hz(1e-6, 10e-6) / 1000
    p += [text(60, 470, f'理想低源阻时，L 与 C出 的 f₀ ≈ {f0:.2f} kHz', 24, weight='700'),
          text(60, 520, '目标：500 kHz 衰减 ≥40 dB；需带源阻、负载、ESR/ESL 验证。', 22),
          text(60, 566, '不是两级各 20 dB/dec 的保证；谐振峰可能反而放大噪声。', 22, colour=RED),
          text(60, 612, '闭环 Buck 可呈负增量输入阻抗；核对滤波器输出阻抗与阻尼。', 22),
          text(60, 658, '再检查电感偏置/温升、电容有效容值与启动波形。', 22, colour=INK2)]
    return p


def esd_path():
    p = [header('TVS 的引线电感也会产生电压',
                '示意 di/dt = 30 A/ns；V = L·di/dt 只估算该路径的电感压降。')]
    for y, nh, colour in ((190, 50, RED), (310, 5, AMBER), (430, 1, BLUE)):
        p += [text(60, y+8, f'{nh:g} nH', 24, weight='700'),
              f'<rect x="240" y="{y-12}" width="{nh/50*600}" height="20" fill="{colour}"/>',
              text(240+nh/50*600+16, y+8, f'{nh*30:g} V', 24, colour=colour)]
    p += [text(60, 510, '50 nH → 1500 V；5 nH → 150 V；每减 1 nH，模型压降减 30 V。', 22),
          text(60, 558, '8 cm 对 50–80 nH、5 mm 对 3–5 nH 只是示例几何。', 22),
          text(60, 606, 'TVS 靠近接口，先规划放电回路；不能仅按长度保证芯片端残压。', 22),
          text(60, 654, '实际残压还含 TVS 动态特性、分流与回路耦合，需 ESD 实测。', 22, colour=INK2)]
    return p


def return_area():
    p = [header('回流绕远，几何面积怎样改变',
                '同一条 5 cm 走线；矩形回路仅作面积示意，不按图上尺寸比例。')]
    for x, height, area, colour in ((50, '1 mm', '.5', BLUE), (520, '3 cm', '15', RED)):
        p.append(box(x, 150, 430, 350))
        p.append(text(x+215, 196, '紧邻参考面' if area=='.5' else '绕路回流', 26, anchor='middle', colour=colour))
        p.append(varrow(x+80, 270, x+345, 270, colour, 3))
        p.append(varrow(x+345, 375, x+80, 375, colour, 3))
        p.append(f'<path d="M{x+75} 270 V375 M{x+350} 270 V375" stroke="{colour}" stroke-width="2" fill="none"/>')
        p += [text(x+215, 250, '5 cm', 22, anchor='middle'),
              text(x+215, 336, height, 24, anchor='middle'),
              text(x+215, 456, f'A = {area} cm²', 26, anchor='middle', weight='700')]
    p += [text(60, 550, '面积比 30：相同频率、相同小环电流，远场幅值比也为 30。', 22),
          text(60, 596, '20 log₁₀(30) ≈ 29.54 dB；不是近场探头读数的必然变化。', 22),
          text(60, 642, '回路电感还取决于导体宽度、间距与形状，不能只按面积倍增。', 22, colour=INK2)]
    return p


SCENES = {
    'ch15-esd-path-v2': {
        'draw': esd_path, 'title': '放电路径的电感压降', 'anchor': '15.6',
        'alt': '固定电流变化率 30A/ns，串联电感 50、5、1nH 对应 1500、150、30V 压降；柱长按电感比例。此模型不等于芯片残压或通过认证的保证。',
    },
    'ch15-return-area-v2': {
        'draw': return_area, 'title': '回流面积与小环远场', 'anchor': '15.7',
        'alt': '同一条 5cm 走线，回程距离示意 1mm 或 3cm，矩形面积为 0.5或15平方厘米。固定频率和电流的小环远场幅值比30，即29.54dB；不据此推算电感或近场探头读数。',
    },
    'ch15-impedance-geometry-v2': {
        'draw': impedance_geometry, 'title': '微带线宽与叠层', 'anchor': '15.3',
        'alt': '同一 50 欧姆微带近似式，介电常数 4.2、铜厚 0.035mm；参考面距离 1.6mm 与 0.2mm 时线宽约 3.022mm 与 0.339mm。剖面不按比例；双层板可控阻抗，差分阻抗需另算耦合。',
    },
    'ch15-input-filter-v2': {
        'draw': input_filter, 'title': 'Buck 输入滤波的验证边界', 'anchor': '15.6',
        'alt': '电源经 C-L-C 滤波接 Buck，两只电容各 10µF、电感 1µH；理想低源阻时 L 与输出侧电容谐振约 50.33kHz。500kHz 衰减至少 40dB 是待验证目标，不是 LC 选值的保证。',
    },
    'ch15-decap-resonance-v2': {
        'draw': decap_resonance, 'title': '去耦支路的谐振频率', 'anchor': '15.1',
        'alt': '同一 100nF 电容，串联电感 1、5、8、10nH 的理想谐振频率分别约 15.92、7.12、5.63、5.03MHz；轴从零起，实际去耦还需比较 ESR 与目标阻抗。',
    },
    'ch15-via-parallel': {
        'draw': via_parallel, 'title': '过孔并联与互感', 'anchor': '15.3',
        'alt': '四支路并联示意：1.6mm 长、0.3mm 孔径的单孔经验电感约 1.299nH。均匀分流且忽略互感时四并约 0.325nH，示意每对互感为自感一半时约 0.812nH；载流能力另核。',
    },
    'ch15-line-flight-v2': {
        'draw': line_flight, 'title': '边沿与传播延迟', 'anchor': '15.3',
        'alt': '传播速度示意 15cm/ns，1ns 与 20ns 边沿的六分之一传播长度分别为 2.5cm、50cm；两条归一时间轴显示同样的六分之一比例，不作为协议合规保证。',
    },
    'ch15-filter-modes-v2': {
        'draw': filter_modes, 'title': '共模与差模的电流路径', 'anchor': '15.6',
        'alt': '左图差模两线电流反向，右图共模同向经寄生或机壳路径返回。两线同向穿过电流钳测到代数和等于两倍共模分量；不同模态使用不同滤波和回流设计。',
    },
}
for meta in SCENES.values():
    meta.update(chapter=15, source='docs/p3-02-ch15.md', renderer='handdrawn')
