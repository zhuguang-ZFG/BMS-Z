#!/usr/bin/env python3
"""Author seven editable course mechanism sketches; --check needs only the standard library.

Uses the project's self-authored SVG route, not an image-generation API.
Visual contract: FA-002 continuous ink, C-03 structure, C-15 only expiry/cutoff.
Spatial patterns follow IG-004 comparison, IG-002 annotated structure and IG-008 flow.
Raster previews are a separate review step; this source never needs a browser.
"""
from __future__ import annotations

import argparse
from html import escape
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/course/assets/sketches'
INK, PAPER, RED = '#003153', '#fffdf5', '#E34234'
WIDTH, HEIGHT = 1440, 1080


def path(d, width=5, color=INK, opacity=1, dash=''):
    dotted = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round" opacity="{opacity}"{dotted}/>')


def line(x1, y1, x2, y2, width=5, color=INK, opacity=1, dash=''):
    # The endpoint is exact: pen irregularity must not create false electrical gaps.
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    return path(f'M{x1:g} {y1:g} Q{mx+1.8:g} {my-1.6:g} {x2:g} {y2:g}', width, color, opacity, dash)


def text(x, y, label, size=42, anchor='middle', color=INK, weight='normal'):
    size = 36 if label == '原理示意 / 非实拍' else 64 if size >= 48 else 56 if size >= 40 else 44
    return (f'<text x="{x:g}" y="{y:g}" font-size="{size}" text-anchor="{anchor}" '
            f'fill="{color}" font-weight="{weight}">{escape(label)}</text>')


def dot(x, y, radius=7, color=INK):
    return f'<circle cx="{x:g}" cy="{y:g}" r="{radius}" fill="{color}"/>'


def arrow(x1, y1, x2, y2, color=INK, width=5, dash=''):
    angle = math.atan2(y2-y1, x2-x1)
    head = 17
    left = (x2-head*math.cos(angle-.52), y2-head*math.sin(angle-.52))
    right = (x2-head*math.cos(angle+.52), y2-head*math.sin(angle+.52))
    return (line(x1, y1, x2, y2, width, color, dash=dash)
            + path(f'M{left[0]:.2f} {left[1]:.2f} L{x2:g} {y2:g} L{right[0]:.2f} {right[1]:.2f}', width, color))


def resistor(x1, y1, x2, y2):
    dx, dy = x2-x1, y2-y1
    length = math.hypot(dx, dy)
    ux, uy = dx/length, dy/length
    points = [(x1, y1)]
    for i in range(1, 10):
        distance = length*i/10
        amplitude = 14 if i % 2 else -14
        points.append((x1+ux*distance-uy*amplitude, y1+uy*distance+ux*amplitude))
    points.append((x2, y2))
    return path('M' + ' L'.join(f'{x:.2f} {y:.2f}' for x, y in points), 5)


def cell_vertical(cx, top, height=210, width=130):
    """Cylinder silhouette with explicit terminals; positive at the top."""
    left, right, bottom = cx-width/2, cx+width/2, top+height
    return (path(f'M{left:g} {top+16:g} C{left-4:g} {top-3:g} {right+4:g} {top-3:g} {right:g} {top+16:g} '
                 f'L{right-2:g} {bottom-12:g} Q{cx:g} {bottom+14:g} {left+2:g} {bottom-12:g} Z')
            + path(f'M{left:g} {top+16:g} Q{cx:g} {top+34:g} {right:g} {top+16:g}', 3)
            + path(f'M{cx-20:g} {top-2:g} L{cx-20:g} {top-19:g} L{cx+20:g} {top-19:g} L{cx+20:g} {top-2:g}', 4)
            + line(cx, top-19, cx, top-48)
            + line(cx, bottom+1, cx, bottom+30)
            + text(cx+width/2+25, top+3, '+', 38)
            + text(cx+width/2+25, bottom+17, '−', 38))


def cell_horizontal(left, cy, width=180, height=190):
    """Negative at left, positive at right; outer terminals lie at left-18/right+18."""
    right, top, bottom = left+width, cy-height/2, cy+height/2
    return (path(f'M{left+12:g} {top:g} Q{left-9:g} {cy:g} {left+12:g} {bottom:g} '
                 f'L{right-12:g} {bottom-2:g} Q{right+8:g} {cy:g} {right-12:g} {top+2:g} Z')
            + path(f'M{right-18:g} {top+4:g} Q{right-35:g} {cy:g} {right-18:g} {bottom-4:g}', 3)
            + line(left-18, cy, left+2, cy)
            + line(right-1, cy, right+18, cy)
            + text(left+22, cy-44, '−', 36)
            + text(right-29, cy-44, '+', 36))


def shell(title, description, layout):
    return [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="1080" viewBox="0 0 1440 1080" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<metadata>Self-authored editable SVG; FA-002; {layout}; C-03; C-15 only for expiry/cutoff.</metadata>
<rect width="1440" height="1080" fill="{PAPER}"/>
<g font-family="KaiTi, STKaiti, serif">''', text(720, 110, title, 48, weight='bold')]


def finish(parts):
    parts += [text(720, 1034, '原理示意 / 非实拍', 34), '</g></svg>']
    return '\n'.join(parts) + '\n'


def current_and_charge():
    s = shell('电流看此刻，电量看累计',
              '闭合回路的常规电流从电芯正端经负载回到负端。同一截面持续通过1 A、累计0.5 h，即0.5 Ah；不把流速与总量混为一谈。', 'IG-004')
    s += [text(490, 230, '此刻', 44), text(1110, 230, '累计', 44)]
    # Cell endpoints: top at 330, bottom at 618.
    s += [cell_vertical(220, 378), line(220, 330, 790, 330), line(790, 330, 790, 430),
          resistor(790, 430, 790, 550), line(790, 550, 790, 700),
          line(790, 700, 220, 700), line(220, 700, 220, 618),
          text(840, 510, '负载', 36, anchor='start'), arrow(365, 330, 500, 330),
          arrow(670, 700, 525, 700), text(475, 302, '1 A', 46)]
    # A cross-section marker surrounds one and only one wire, without a branch.
    s += [path('M614 289 C650 282 651 376 615 373 C584 367 584 295 614 289', 4),
          text(618, 425, '同一截面', 36), line(618, 388, 618, 373, 3)]
    # A clock shows duration. Its hands are not electrical connections.
    s += [path('M1092 320 C1221 313 1240 534 1110 545 C976 558 956 331 1092 320', 5)]
    for i in range(12):
        a = i*math.pi/6
        s.append(line(1100+91*math.sin(a), 433-91*math.cos(a),
                      1100+101*math.sin(a), 433-101*math.cos(a), 3))
    s += [line(1100, 433, 1100, 356, 3, opacity=.6, dash='5 8'),
          line(1100, 433, 1100, 515), dot(1100, 433),
          path('M1100 298 A135 135 0 0 1 1100 568', 4),
          path('M1116 552 L1100 568 L1120 580', 4),
          text(1100, 655, '0.5 h', 48)]
    # Accumulated charge is a ruler, distinct from the flowing-current arrow.
    s += [line(940, 710, 1280, 710, 4), line(940, 695, 940, 735, 4),
          line(1280, 695, 1280, 735, 4), text(1110, 788, '0.5 Ah', 48),
          text(720, 923, '1 A × 0.5 h = 0.5 Ah', 56)]
    for x in range(960, 1280, 25):
        s.append(line(x, 694, x+12, 674, 2, opacity=.65))
    return finish(s)


def series_pack():
    s = shell('串联：电压相加，电流不分流',
              '四节电芯均为3.7 V、2 Ah，负端在左、正端在右，依次串联且经负载闭合。常规1 A电流流经每一节；整包14.8 V、2 Ah。', 'IG-002')
    s.append(text(720, 240, '四节首尾相接', 42))
    starts = (170, 440, 710, 980)
    for x in starts:
        s += [cell_horizontal(x, 465), text(x+90, 475, '3.7 V', 38), text(x+90, 532, '2 Ah', 38)]
    for a, b in zip(starts, starts[1:], strict=False):
        s += [arrow(a+198, 465, b-18, 465), text((a+198+b-18)/2, 382, '1 A', 36)]
    s += [line(1178, 465, 1310, 465), line(1310, 465, 1310, 830),
          line(1310, 830, 820, 830), resistor(820, 830, 620, 830),
          line(620, 830, 100, 830), line(100, 830, 100, 465), line(100, 465, 152, 465),
          arrow(1310, 565, 1310, 680), arrow(410, 830, 270, 830),
          text(720, 909, '负载', 40), text(1280, 409, '1 A', 40)]
    # Annotation bracket is detached from all electrical conductors.
    s += [path('M173 622 Q171 652 201 651 L1133 651 Q1160 652 1160 622', 3),
          text(720, 737, '14.8 V · 2 Ah', 56)]
    return finish(s)


def load_drop():
    s = shell('同一电池包，带载后少了哪一段？',
              '简化等效比较：静置端电压14.80 V。串联总电阻0.12 Ω，2 A放电时压降0.24 V，端电压14.56 V，电阻发热功率0.48 W；没有温升或安全阈值结论。', 'IG-004')
    s += [text(350, 238, '静置', 44), text(1070, 238, '带载 · 简化等效', 44)]
    s += [cell_vertical(180, 400), line(180, 352, 470, 352), line(470, 352, 470, 465),
          path('M470 465 C555 460 557 595 471 598 C384 601 384 470 470 465', 4),
          text(470, 552, 'V', 54), line(470, 598, 470, 700), line(470, 700, 180, 700),
          line(180, 700, 180, 640), text(350, 816, '14.80 V', 56)]
    s += [cell_vertical(835, 400), line(835, 352, 965, 352), resistor(965, 352, 1110, 352),
          line(1110, 352, 1220, 352), line(1220, 352, 1220, 465),
          resistor(1220, 465, 1220, 590), line(1220, 590, 1220, 700),
          line(1220, 700, 835, 700), line(835, 700, 835, 640),
          text(1035, 298, 'R = 0.12 Ω', 38), text(1115, 475, '2 A', 44),
          arrow(1150, 352, 1204, 352), arrow(1220, 400, 1220, 445),
          text(1134, 627, '负载', 36), text(1040, 816, '14.56 V', 56)]
    # A voltage dimension spans the external output nodes after the series R.
    s += [dot(1220, 352, 6), dot(1220, 700, 6),
          line(1265, 352, 1320, 352, 3), line(1320, 352, 1320, 700, 3),
          line(1320, 700, 1265, 700, 3), text(1320, 776, '端电压', 34),
          text(720, 894, '压降：14.80 − 14.56 = 0.24 V', 48),
          text(720, 970, 'I²R = 0.48 W', 48)]
    return finish(s)


def sum_inputs():
    s = shell('四个输入，怎样变成一个返回值？',
              '四个采样值3.70、3.72、3.68、3.71 V作为数据输入，而不是电气接线；数据箭头汇入sum(cells)计算并返回14.81 V。', 'IG-008')
    s += [text(720, 230, '输入', 44)]
    values = ('3.70 V', '3.72 V', '3.68 V', '3.71 V')
    targets = ((624, 690), (670, 650), (770, 650), (816, 690))
    for cx, label, target in zip((230, 550, 870, 1190), values, targets, strict=True):
        s += [cell_vertical(cx, 310, 175, 125), text(cx, 563, label, 44),
              arrow(cx, 595, *target, width=4, dash='9 11')]
    # Familiar addition sign: lesson 04 must not require a new sigma symbol.
    s += [line(650, 715, 790, 715, 8), line(720, 645, 720, 790, 8),
          text(720, 881, 'sum(cells)', 48), text(420, 755, '求和', 42),
          arrow(848, 718, 1010, 718, width=6),
          text(1160, 680, '返回', 40), text(1160, 776, '14.81 V', 54)]
    return finish(s)


def calibration():
    s = shell('减去固定偏移，读数移回多少？',
              '两条对齐电压刻度尺显示固定正偏移的校正：原始3.712 V减去0.012 V得到3.700 V。校正偏移并不表示全部测量误差消失；不提前给独立题答案。', 'IG-004')
    low, scale = 3.690, 32000

    def x(voltage):
        return 220+(voltage-low)*scale

    s += [text(120, 375, '原始', 40, anchor='start'), text(120, 650, '校正', 40, anchor='start')]
    for y in (440, 715):
        s.append(line(220, y, 1220, y, 4))
        for n in range(31):
            tick = 24 if n % 10 == 0 else 13 if n % 5 == 0 else 7
            s.append(line(220+n*32, y-tick, 220+n*32, y+tick, 3))
        for value in (3.700, 3.710, 3.720):
            s.append(text(x(value), y+70, f'{value:.3f}', 36))
    raw, fixed = x(3.712), x(3.700)
    s += [dot(raw, 440, 10), line(raw, 348, raw, 411, 4), text(raw, 320, '3.712 V', 48),
          dot(fixed, 715, 10), line(fixed, 605, fixed, 685, 4), text(fixed, 578, '3.700 V', 48),
          arrow(raw-12, 568, fixed+165, 568, width=4), text(1000, 630, '−0.012 V', 42),
          text(720, 911, '3.712 V − 0.012 V = 3.700 V', 50)]
    return finish(s)


def sample_age():
    s = shell('同一份采样，越等越旧',
              '同一条时间轴上采样时间固定为1.0 s。现在为1.4、1.5、1.6 s时年龄分别0.4、0.5、0.6 s；0.5 s上限含端点，因此前两点有效，最后一点过期。', 'IG-008')
    x0, scale = 220, 1600

    def x(seconds):
        return x0+(seconds-1)*scale

    s += [cell_vertical(x0, 275, 150, 110), text(x0, 515, '采样', 40),
          line(x0, 536, x0, 615, 3, dash='8 9'), text(1050, 257, '样本年龄', 44),
          arrow(145, 650, 1300, 650, width=5)]
    for i in range(7):
        cx = x(1+i*.1)
        s += [line(cx, 636, cx, 667, 3), text(cx, 728, f'{1+i*.1:.1f} s', 36)]
    s.append(dot(x0, 650, 9))
    for now, age in ((1.4, .4), (1.5, .5), (1.6, .6)):
        cx = x(now)
        expired = age > .5
        color = RED if expired else INK
        s += [text(cx, 360, '过期' if expired else '有效', 40, color=color),
              text(cx, 450, f'{age:.1f} s', 40), line(cx, 490, cx, 616, 3, color),
              dot(cx, 650, 10, color)]
        if expired:
            s += [line(cx-15, 545, cx+15, 575, 4, RED), line(cx+15, 545, cx-15, 575, 4, RED)]
        else:
            s.append(path(f'M{cx-17:g} 561 L{cx-3:g} 575 L{cx+22:g} 542', 4))
    s += [path(f'M{x0:g} 786 L{x0:g} 811 Q{x0:g} 830 {x0+22:g} 830 L{x(1.5)-20:g} 830 Q{x(1.5):g} 830 {x(1.5):g} 810 L{x(1.5):g} 786', 3),
          text((x0+x(1.5))/2, 917, '年龄 ≤ 0.5 s，含端点', 46),
          text(1240, 803, '当前时间', 34)]
    return finish(s)


def command_feedback():
    s = shell('下令断开，不等于已经断开',
              '同一时间轴：0.30 s开始欠压，0.50 s发断开命令。正常分支0.60 s反馈开，画出开路触点；卡住分支到0.70 s仍反馈闭合，画出闭合触点并锁存ACTUATOR_STUCK。', 'IG-008')
    timeline = ((180, '0.30 s'), (660, '0.50 s'), (900, '0.60 s'), (1140, '0.70 s'))
    s.append(arrow(150, 315, 1310, 315, width=5))
    for cx, label in timeline:
        s += [line(cx, 298, cx, 332, 4), text(cx, 264, label, 48), dot(cx, 315, 8)]
    s += [text(180, 402, '欠压', 42), text(660, 402, '断开命令', 42),
          line(660, 426, 660, 485, 4), dot(660, 485),
          arrow(660, 485, 805, 559, width=4, dash='8 10'),
          path('M660 485 Q600 609 619 754', 4, dash='8 10'),
          arrow(619, 754, 930, 814, width=4, dash='8 10')]
    # Normal branch: a genuinely open contact, not merely an "off" label.
    s += [text(220, 570, '正常', 42), line(790, 590, 850, 590, 5),
          f'<circle cx="850" cy="590" r="10" fill="{PAPER}" stroke="{INK}" stroke-width="4"/>',
          line(860, 584, 921, 529, 6),
          f'<circle cx="950" cy="590" r="10" fill="{PAPER}" stroke="{INK}" stroke-width="4"/>',
          line(960, 590, 1060, 590, 5), text(1210, 590, '反馈开', 42),
          line(900, 333, 900, 459, 3, dash='7 10')]
    # Fault branch: the contact stays physically bridged after an off command.
    s += [text(220, 836, '卡住', 42), line(930, 835, 1030, 835, 5),
          f'<circle cx="1030" cy="835" r="10" fill="{PAPER}" stroke="{INK}" stroke-width="4"/>',
          line(1040, 835, 1120, 835, 6, RED),
          f'<circle cx="1130" cy="835" r="10" fill="{PAPER}" stroke="{INK}" stroke-width="4"/>',
          line(1140, 835, 1250, 835, 5), text(1120, 749, '0.70 s 仍闭合', 42),
          line(1140, 335, 1140, 460, 3, dash='7 10'),
          text(940, 936, 'ACTUATOR_STUCK', 48, color=RED)]
    return finish(s)


DRAWINGS = {
    '01-current-charge.svg': current_and_charge,
    '02-series-pack.svg': series_pack,
    '03-load-drop.svg': load_drop,
    '04-sum-inputs.svg': sum_inputs,
    '05-calibration.svg': calibration,
    '06-sample-age.svg': sample_age,
    '09-command-feedback.svg': command_feedback,
}


def validate_svg(source):
    doc = ET.fromstring(source)
    assert doc.attrib['viewBox'] == '0 0 1440 1080'
    assert doc.attrib['width'] == '1440' and doc.attrib['height'] == '1080'
    ns = {'s': 'http://www.w3.org/2000/svg'}
    assert doc.find('s:title', ns) is not None and doc.find('s:desc', ns) is not None
    labels = doc.findall('.//s:text', ns)
    visible = ''.join(''.join(label.itertext()) for label in labels)
    assert len(re.findall('[\u4e00-\u9fff]', visible)) < 70, visible
    assert '原理示意 / 非实拍' in visible
    for label in labels:
        assert float(label.attrib['font-size']) >= (36 if ''.join(label.itertext()) == '原理示意 / 非实拍' else 44)
        assert 70 <= float(label.attrib['x']) <= 1350
        assert 60 <= float(label.attrib['y']) <= 1045
    assert not any(tag in source for tag in ('<script', '<image', '<foreignObject', '<animate'))
    colors = set(re.findall(r'#[0-9a-fA-F]{6}', source))
    assert colors <= {INK, PAPER, RED}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='compare generated editable sources without rendering')
    args = parser.parse_args()
    assert math.isclose(1*.5, .5)
    assert math.isclose(4*3.7, 14.8)
    assert math.isclose(2*.12, .24) and math.isclose(2**2*.12, .48)
    assert math.isclose(14.8-2*.12, 14.56)
    assert math.isclose(sum((3.70, 3.72, 3.68, 3.71)), 14.81)
    assert math.isclose(3.712-.012, 3.7)
    if not args.check:
        OUT.mkdir(parents=True, exist_ok=True)
    failures = []
    for name, draw in DRAWINGS.items():
        source = draw()
        validate_svg(source)
        target = OUT / name
        if args.check:
            if not target.exists() or target.read_text(encoding='utf-8') != source:
                failures.append(name)
        else:
            target.write_text(source, encoding='utf-8', newline='\n')
    if failures:
        raise SystemExit('Sketch drift: ' + ', '.join(failures))
    print(f'{"checked" if args.check else "generated"} {len(DRAWINGS)}/{len(DRAWINGS)} editable sketches; numerical/XML/palette/text-size contracts PASS')


if __name__ == '__main__':
    main()
