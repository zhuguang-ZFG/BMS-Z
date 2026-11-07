"""Six editable mechanisms for course lessons 13–18; no raster generation here."""
from __future__ import annotations

import argparse
import math

from generate_course_sketches import (
    OUT, RED, arrow, cell_vertical, dot, finish, line, path,
    resistor, shell, text, validate_svg,
)


def charger_dial(cx, label, value, quantity):
    return [text(cx, 240, label, 48),
            path(f'M{cx-220} 285 Q{cx-225} 274 {cx-205} 275 L{cx+205} 275 Q{cx+223} 276 {cx+220} 296 '
                 f'L{cx+218} 525 Q{cx+220} 545 {cx+200} 543 L{cx-202} 545 Q{cx-224} 545 {cx-222} 525 Z', 4),
            path(f'M{cx-75} 388 C{cx-73} 294 {cx+77} 293 {cx+80} 388 C{cx+84} 486 {cx-76} 488 {cx-75} 388', 5),
            line(cx, 388, cx+42, 341, 6), dot(cx, 388, 7), text(cx, 510, value, 48),
            text(cx, 605, quantity, 42)]


def charge_phases():
    s = shell('充电后段，改为稳住电压',
              '充电器先恒流CC，此例记录的电流为负1安培；随后恒压CV。两只旋钮分别表示调节电流与电压。下方为非实测曲线：电压先升后保持，电流幅度先恒定后减小。未将保护阈值作为正常控制目标。', 'IG-004')
    s += charger_dial(380, 'CC · 恒流', '−1 A', '调电流')
    s += charger_dial(1060, 'CV · 恒压', 'V', '调电压')
    s += [arrow(655, 401, 785, 401, width=6),
          arrow(180, 812, 1300, 812, width=3), line(180, 812, 180, 656, 3),
          text(125, 725, 'V', 44), text(1300, 864, 't', 40),
          path('M200 788 Q440 773 700 690 L1260 690', 6),
          line(700, 660, 700, 973, 3, dash='8 10'),
          text(420, 697, 'CC', 40), text(1050, 771, 'CV', 40),
          line(180, 971, 1300, 971, 3), line(180, 971, 180, 865, 3),
          text(120, 923, '|I|', 40), path('M200 879 L700 879 Q858 883 970 936 Q1120 966 1260 966', 6),
          text(720, 625, '曲线示意', 36)]
    return finish(s)


def balance_path():
    s = shell('旁路泄放，电量变成热',
              '单节两端并接受控开关和泄放电阻，常规电流沿电芯正端进入闭合开关及电阻，再回负端。单节4伏、泄放0.05安培，电阻发热0.20瓦；去掉0.10安时需连续导通2小时。本图仅为单节旁路，没有把电量转入另一节。', 'IG-002')
    s += [cell_vertical(390, 388, 240, 170),
          line(390, 340, 950, 340), line(950, 340, 950, 420),
          dot(950, 420, 9), line(950, 430, 950, 500, 6), dot(950, 510, 9),
          line(950, 520, 950, 590), resistor(950, 590, 950, 730),
          line(950, 730, 950, 810), line(950, 810, 390, 810), line(390, 810, 390, 658),
          text(200, 545, '4.0 V', 44), text(1135, 477, '开关闭合', 40),
          arrow(620, 340, 780, 340, width=6), text(700, 290, '0.05 A', 48),
          arrow(950, 530, 950, 570, width=5), arrow(720, 810, 540, 810, width=5),
          text(1130, 666, '电阻', 42), text(1135, 750, '0.20 W', 48),
          path('M1004 608 Q1033 587 1012 561', 3),
          path('M1037 628 Q1067 605 1046 577', 3),
          text(720, 930, '0.10 Ah / 0.05 A = 2 h', 52)]
    return finish(s)


def weakest_cell():
    s = shell('同样一半，最少的那节先到限',
              '四节容量依次2、2、1.8、2安时，SOC均为0.5，剩余可用电量分别1、1、0.9、1安时。以相同Ah刻度画四节长度；第三节0.9安时先到简化可用电量下端。这是Ah比较，不是电压或能量长短。', 'IG-004')
    s += [text(720, 230, 'SOC = 0.50', 48), text(245, 340, '容量', 40),
          text(1120, 340, '可用电量', 40)]
    ys = (430, 570, 710, 850)
    for index, (y, capacity, remaining) in enumerate(zip(ys, (2, 2, 1.8, 2), (1, 1, .9, 1), strict=True), 1):
        end = 480+remaining*620
        s += [text(130, y+17, str(index), 40), text(295, y+17, f'{capacity:g} Ah', 44),
              path(f'M480 {y-43} L1100 {y-43} L1100 {y+43} L480 {y+43} Z', 3),
              line(484, y, end-4, y, 26, opacity=.22), line(end, y-43, end, y+43, 6),
              text(1215, y+17, f'{remaining:g} Ah', 44)]
    s += [line(1038, 376, 1038, 904, 3, dash='7 10'),
          text(720, 968, '整包最多继续通过 0.9 Ah', 48)]
    return finish(s)


def bracket(x1, x2, y, label):
    return [path(f'M{x1} {y-18} L{x1} {y} L{x2} {y} L{x2} {y-18}', 3),
            text((x1+x2)/2, y+62, label, 36)]


def byte_order():
    s = shell('先到低位，再合成物理量',
              '完整教学记录八字节为da39 1efb ff01 b431。电压字段低位da先放，值218；高位39后放，值57。按57乘256加218得到14810毫伏，再除1000得到14.81伏。未提前展示独立练习的解码答案。', 'IG-002')
    values = ('da', '39', '1e', 'fb', 'ff', '01', 'b4', '31')
    start, width = 160, 140
    for index, value in enumerate(values):
        left, cx = start+index*width, start+index*width+width/2
        s += [text(cx, 242, str(index), 36),
              path(f'M{left} 292 L{left+width-8} 292 L{left+width-8} 412 L{left} 412 Z', 4),
              text(cx, 372, value, 52)]
    s += bracket(160, 432, 454, '电压') + bracket(440, 712, 454, '电流')
    s += bracket(720, 852, 454, '序号') + bracket(860, 992, 454, '质量') + bracket(1000, 1272, 454, 'CRC')
    s += [path('M225 426 L225 565 L385 565', 4, dash='8 10'),
          arrow(385, 565, 385, 581, width=4, dash='8 10'),
          path('M370 426 L370 548 L1025 548', 4, dash='8 10'),
          arrow(1025, 548, 1025, 581, width=4, dash='8 10'),
          text(385, 705, 'da = 218', 48), text(1025, 705, '39 = 57', 48),
          text(385, 622, '低位先到', 40), text(1025, 622, '高位后到', 40),
          text(720, 826, '57 × 256 + 218 = 14810 mV', 48),
          arrow(720, 854, 720, 895, width=5), text(720, 972, '14810 / 1000 = 14.81 V', 48)]
    return finish(s)


def frame_checks():
    s = shell('重算后比较，只让有效记录前进',
              '收到的八字节记录分成前六字节数据与后两字节CRC。接收端对前六字节重算得到0x31b4，与小端尾部b431还原出的0x31b4比较；相同后继续质量范围与序号检查，不同则拒收，只有全部有效才更新成功记录。没有演示独立练习的序号答案。', 'IG-008')
    s += [path('M180 225 L840 225 L840 355 L180 355 Z', 4),
          path('M905 225 L1270 225 L1270 355 L905 355 Z', 4),
          text(510, 304, 'da 39 1e fb ff 01', 48), text(1090, 304, 'b4 31', 48),
          text(510, 418, '前六字节重算', 40), text(1090, 418, '尾部小端还原', 40),
          arrow(510, 443, 510, 489, width=4), arrow(1090, 443, 1090, 489, width=4),
          text(510, 558, '0x31b4', 48), text(1090, 558, '0x31b4', 48),
          path('M720 575 L855 657 L720 738 L585 657 Z', 4), text(720, 680, '=', 52),
          arrow(560, 574, 624, 608, width=4), arrow(1030, 574, 815, 624, width=4),
          arrow(605, 706, 345, 797, color=RED, width=5), text(345, 891, '不同：拒收', 44, color=RED),
          line(275, 795, 315, 835, 5, RED), line(315, 795, 275, 835, 5, RED),
          arrow(828, 707, 1075, 775, width=5), text(1190, 808, '相同', 40),
          text(1030, 875, '质量 / 范围 / 序号', 40),
          arrow(1030, 898, 1030, 920, width=4), text(1040, 969, '全有效才更新', 36)]
    return finish(s)


def two_clocks():
    s = shell('采样新，不等于请求新',
              '两条独立记录共用已对齐的本地时间轴。时间点为示意，横向间距不按比例。采样在2.00、2.20、2.30、2.31秒均继续更新；远程有效接收停在2.00秒。远程年龄在2.30秒为0.30秒且端点有效，到2.31秒为0.31秒，超过上限而禁止使能。', 'IG-008')
    xs = (300, 650, 1000, 1240)
    times = ('2.00 s', '2.20 s', '2.30 s', '2.31 s')
    s += [text(720, 188, '时间点示意，间距不按比例', 36),
          text(180, 365, '采样', 42), text(180, 650, '接收', 42),
          arrow(265, 420, 1310, 420, width=4), arrow(265, 705, 1310, 705, width=4)]
    for x, label in zip(xs, times, strict=True):
        s += [text(x, 273, label, 44), line(x, 298, x, 384, 3, dash='7 10'),
              dot(x, 420, 9), path(f'M{x-15} 480 L{x-1} 494 L{x+24} 463', 4)]
    s += [dot(300, 705, 10), text(300, 798, '最后有效', 40),
          line(320, 705, 1290, 705, 3, dash='8 11'),
          text(845, 605, '一直未更新', 40), text(1000, 798, '0.30 s', 44),
          text(1240, 798, '0.31 s', 44),
          path('M981 853 L996 868 L1021 834', 4), text(1000, 937, '含端点', 40),
          line(1220, 841, 1260, 881, 5, RED), line(1260, 841, 1220, 881, 5, RED),
          text(1240, 937, '过期', 40, color=RED),
          text(590, 945, '年龄 = 现在 − 最后有效接收', 36)]
    return finish(s)


DRAWINGS = {
    '13-charge-phases.svg': charge_phases,
    '14-balance-path.svg': balance_path,
    '15-weakest-cell.svg': weakest_cell,
    '16-byte-order.svg': byte_order,
    '17-frame-checks.svg': frame_checks,
    '18-two-clocks.svg': two_clocks,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    assert math.isclose(.1/.05, 2) and math.isclose(4*.05, .2)
    assert math.isclose(min(q*.5 for q in (2, 2, 1.8, 2)), .9)
    assert 57*256+218 == 14810
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
    print(f'{"checked" if args.check else "generated"} 6/6 charge and communication sketches')


if __name__ == '__main__':
    main()
