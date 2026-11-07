#!/usr/bin/env python3
"""Editable mechanisms for lessons 07, 08 and 10–12; no bitmap generation.

Each drawing uses the shared FA-002 primitives and the lesson's worked example.
The independent exercises and their answers are intentionally absent.
"""
from __future__ import annotations

import math

from generate_course_sketches import (
    INK, PAPER, RED, arrow, cell_horizontal, cell_vertical, dot, finish,
    line, path, resistor, shell, text,
)


def terminal(x, y, radius=8):
    return (f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{PAPER}" '
            f'stroke="{INK}" stroke-width="4"/>')


def clock(cx, cy, radius=85):
    parts = [path(f'M{cx} {cy-radius} C{cx+radius*1.36} {cy-radius} '
                  f'{cx+radius*1.36} {cy+radius} {cx} {cy+radius} '
                  f'C{cx-radius*1.36} {cy+radius} {cx-radius*1.36} {cy-radius} '
                  f'{cx} {cy-radius}', 4)]
    for index in range(12):
        angle = index * math.pi / 6
        parts.append(line(cx + (radius - 15) * math.sin(angle),
                          cy - (radius - 15) * math.cos(angle),
                          cx + (radius - 5) * math.sin(angle),
                          cy - (radius - 5) * math.cos(angle), 3))
    parts += [line(cx, cy, cx, cy-radius*.58, 4),
              line(cx, cy, cx+radius*.38, cy+radius*.46, 4), dot(cx, cy, 6)]
    return ''.join(parts)


def cell_limits():
    s = shell('总压一样，单节未必一样',
              '两组四节串联电芯都由高阻电压表读得14.81 V。上组3.70、3.72、3.68、3.71 V；'
              '下组4.25、3.52、3.52、3.52 V，第一节达到4.20 V教学过压阈值。'
              '串联导线真实连接，电压表跨接包端；不把总压等同于单节合格。', 'IG-004')
    for cy, values, bad in [
        (350, (3.70, 3.72, 3.68, 3.71), False),
        (750, (4.25, 3.52, 3.52, 3.52), True),
    ]:
        s += [text(560, cy-125, '一节 ≥ 4.20 V' if bad else '单节 < 4.20 V', 42,
                   color=RED if bad else INK), text(1210, cy-125, '14.81 V', 48)]
        starts = (170, 440, 710, 980)
        for index, (left, value) in enumerate(zip(starts, values, strict=True)):
            s += [cell_horizontal(left, cy, width=180, height=160),
                  text(left+90, cy+25, f'{value:.2f} V', 36,
                       color=RED if bad and index == 0 else INK)]
        for left, right in zip(starts, starts[1:], strict=False):
            s.append(line(left+198, cy, right-18, cy))
        # The high-impedance voltmeter measures the two external terminals.
        s += [line(1178, cy, 1270, cy), line(1270, cy, 1270, cy+15),
              path(f'M1270 {cy+15} C1352 {cy+15} 1352 {cy+145} 1270 {cy+145} '
                   f'C1188 {cy+145} 1188 {cy+15} 1270 {cy+15}', 4),
              text(1270, cy+100, 'V', 48), line(1270, cy+145, 1270, cy+185),
              line(1270, cy+185, 100, cy+185), line(100, cy+185, 100, cy),
              line(100, cy, 152, cy)]
        if bad:
            s += [path(f'M187 {cy+56} Q260 {cy+90} 333 {cy+56}', 5, RED),
                  text(500, cy+145, '只查总压，会漏掉这一节', 38)]
    return finish(s)


def continuous_delay():
    s = shell('延时只认连续，不凑低读数',
              '图中高度表示采样后的正常或欠压判断，不是按比例绘制的电压曲线。'
              '连续分支从0.30 s读到2.95 V起计，到0.50 s满0.20 s才下令。'
              '对照分支0.40 s恢复3.68 V使未触发计时清零，0.50 s再次欠压时重新起计。', 'IG-008')
    xs = (350, 630, 910, 1190)
    times = ('0.20 s', '0.30 s', '0.40 s', '0.50 s')
    s += [text(260, 228, '连续欠压', 42), text(1000, 228, '2.95 V ≤ 3.00 V', 42)]
    for index, (x, label) in enumerate(zip(xs, times, strict=True)):
        y = 330 if index == 0 else 435
        s += [dot(x, y, 10, RED if index else INK),
              line(x, y+18, x, 475, 2, opacity=.6, dash='5 9'),
              text(x, 523, label, 36)]
    s += [text(150, 342, '正常', 36), text(150, 450, '欠压', 36),
          arrow(300, 475, 1305, 475, width=3),
          path('M350 330 L630 435', 4, dash='8 11'),
          line(630, 435, 1190, 435, 6, RED),
          path('M630 552 L630 569 Q630 583 649 583 L1171 583 Q1190 583 1190 569 L1190 552', 3),
          text(910, 652, '0.20 s → 断开', 48, color=RED)]
    # The second trace has an actual gap in its run of unsafe samples.
    s += [text(260, 735, '中途恢复', 42), text(1000, 735, '3.68 V → 清零', 42)]
    lower_ys = (800, 880, 800, 880)
    for index, (x, y, label) in enumerate(zip(xs, lower_ys, times, strict=True)):
        bad = index % 2 == 1
        s += [dot(x, y, 10, RED if bad else INK),
              line(x, y+18, x, 920, 2, opacity=.6, dash='5 9'), text(x, 972, label, 36)]
    for index in range(3):
        s.append(line(xs[index], lower_ys[index], xs[index+1], lower_ys[index+1],
                      4, dash='8 11'))
    s += [text(150, 812, '正常', 36), text(150, 895, '欠压', 36),
          arrow(300, 920, 1305, 920, width=3),
          arrow(1190, 760, 1190, 855, width=3),
          text(1210, 808, '重计', 36, anchor='start')]
    return finish(s)


def soc_ledger():
    s = shell('电量靠逐笔记账，不靠电压猜',
              '恒定1 A放电持续0.5 h，电流时间图的面积为0.5 Ah。'
              '电量账本从2 Ah扣去0.5 Ah得到1.5 Ah，除以2 Ah得SOC 75%。'
              '账本及积分面积表达电量，不把电压画成液位，不使用独立练习数据。', 'IG-008')
    s += [text(175, 265, '电流', 42), arrow(290, 510, 290, 245, width=4),
          arrow(250, 510, 1270, 510, width=4), text(195, 345, '1 A', 44),
          line(300, 310, 1100, 310, 6), line(1100, 310, 1100, 510, 4),
          line(300, 310, 300, 510, 4), text(300, 575, '0 h', 42),
          text(1100, 575, '0.5 h', 42), text(1280, 575, '时间', 36),
          text(720, 427, '0.5 Ah', 48)]
    # Hatching conveys integrated area, with clear space behind its value.
    for x in range(330, 1100, 42):
        if 515 <= x <= 925:
            s += [line(x, 330, x+20, 350, 2, opacity=.3),
                  line(x, 470, min(x+20, 1100), 490, 2, opacity=.3)]
        else:
            s.append(line(x, 330, min(x+150, 1100), 480, 2, opacity=.3))
    s += [arrow(720, 535, 720, 615, width=4),
          path('M115 658 Q406 602 720 652 Q1036 604 1325 658 '
               'L1310 922 Q1030 874 720 922 Q408 874 130 922 Z', 4),
          path('M720 652 Q708 785 720 922', 4),
          text(425, 744, '原有 2 Ah', 48), text(425, 849, '扣除 0.5 Ah', 44),
          text(1020, 744, '余 1.5 Ah', 48), text(1020, 849, '1.5 / 2 = 75%', 48),
          text(720, 987, '1 A × 0.5 h = 0.5 Ah', 48)]
    return finish(s)


def offset_drift():
    s = shell('电流没有流，账本却在扣',
              '开关已经断开，示意回路真实电流为0 A，传感器仍带+0.020 A固定偏移。'
              '5 h后多记放电0.10 Ah，对2 Ah为多扣比例+0.05，drift函数返回正。'
              '若误差定义为估计SOC减真实SOC，则为-0.05，即低估5个百分点。', 'IG-008')
    s += [cell_vertical(180, 350, 150, 110), line(180, 302, 350, 302),
          terminal(360, 302), line(370, 295, 422, 248, 5), terminal(450, 302),
          line(458, 302, 630, 302), line(630, 302, 630, 370),
          path('M630 370 C730 368 730 522 630 520 C530 522 530 370 630 370', 4),
          text(630, 465, 'A', 48), line(630, 520, 630, 680),
          line(630, 680, 180, 680), line(180, 680, 180, 530),
          text(375, 520, '实际', 42), text(375, 610, '0 A', 48),
          text(1060, 290, '+0.020 A', 48), text(1060, 373, '读数偏移', 42),
          arrow(735, 445, 900, 445, width=4, dash='8 11'),
          clock(1060, 510), text(1060, 668, '5 h', 48),
          text(720, 778, '0.020 A × 5 h = 0.10 Ah', 48),
          line(100, 815, 1340, 815, 3, opacity=.45),
          text(395, 899, 'drift = +0.05', 48), text(395, 978, '多扣比例 · 2 Ah', 42),
          text(1050, 899, '误差 −0.05', 48), text(1050, 978, '低估 5 个百分点', 42)]
    return finish(s)


def rest_voltage():
    s = shell('卸去负载，还要等电压稳定',
              '采用正文4S教学包：OCV 14.80 V、2 A、总R 0.12 Ω，最小模型带载端电压14.56 V。'
              '右侧充分静置、无电流时才读OCV。下方为不按数值比例的真实恢复形状示意：'
              '卸载时先跳变，再逐渐恢复，不能用瞬时端电压直接查静置SOC表。', 'IG-004')
    s += [text(410, 232, '带载 · 2 A', 42), text(1115, 232, '充分静置 · 0 A', 42),
          cell_vertical(170, 360, 150, 110), line(170, 312, 310, 312),
          resistor(310, 312, 450, 312), line(450, 312, 620, 312),
          line(620, 312, 620, 400), resistor(620, 400, 620, 490),
          line(620, 490, 620, 590), line(620, 590, 170, 590),
          line(170, 590, 170, 540), arrow(510, 312, 585, 312, width=4),
          text(385, 388, '0.12 Ω', 36), text(420, 505, '负载', 36),
          text(390, 675, '14.56 V', 48),
          cell_vertical(870, 360, 150, 110), line(870, 312, 1290, 312),
          line(1290, 312, 1290, 430),
          path('M1290 430 C1370 430 1370 550 1290 550 C1210 550 1210 430 1290 430', 4),
          text(1290, 511, 'V', 48), line(1290, 550, 1290, 590),
          line(1290, 590, 870, 590), line(870, 590, 870, 540),
          text(1100, 675, '14.80 V · OCV', 44),
          text(720, 760, '真实恢复 · 形状示意', 42),
          arrow(170, 930, 170, 785, width=3), text(105, 847, '电压', 36),
          arrow(170, 930, 1325, 930, width=3),
          line(190, 908, 350, 908, 4), line(350, 908, 350, 870, 5),
          path('M350 870 C430 821 545 805 690 795 C870 784 1070 783 1270 783', 5),
          line(1050, 783, 1300, 783, 2, opacity=.45, dash='8 11'),
          text(350, 980, '卸载', 42), text(925, 980, '逐渐稳定', 42),
          text(1320, 980, '时间', 36)]
    return finish(s)


DRAWINGS = {
    '07-cell-limits.svg': cell_limits,
    '08-continuous-delay.svg': continuous_delay,
    '10-soc-ledger.svg': soc_ledger,
    '11-offset-drift.svg': offset_drift,
    '12-rest-voltage.svg': rest_voltage,
}
