"""Editable mechanism sketches for the integration and engineering lessons.

Keep the shared drawing vocabulary in generate_course_sketches.  This module
only supplies drawings; the main generator owns writing and drift checks.
"""
from __future__ import annotations

from generate_course_sketches import (
    INK, PAPER, RED, arrow, dot, finish, line, path, resistor, shell, text,
)


def _circle(cx, cy, radius, width=4, color=INK):
    return (f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{PAPER}" '
            f'stroke="{color}" stroke-width="{width}"/>')


def _folder(x, y, width, height):
    return path(
        f'M{x} {y+height} L{x-3} {y+18} Q{x-3} {y} {x+18} {y} '
        f'L{x+width*.37:g} {y} L{x+width*.45:g} {y+27} L{x+width-17} {y+27} '
        f'Q{x+width} {y+27} {x+width} {y+46} L{x+width-3} {y+height} Z', 5)


def _contact(cx, cy, closed=False, color=INK):
    return (line(cx-110, cy, cx-52, cy)
            + _circle(cx-42, cy, 10)
            + line(cx-32, cy-2, cx+32 if closed else cx+23,
                   cy-2 if closed else cy-59, 6, color)
            + _circle(cx+42, cy, 10)
            + line(cx+52, cy, cx+110, cy))


def _chip(x, y, width, height):
    result = path(
        f'M{x+12} {y} L{x+width-8} {y+2} L{x+width} {y+height-5} '
        f'L{x+4} {y+height} Z', 4)
    for offset in (height*.25, height*.5, height*.75):
        result += line(x-15, y+offset, x, y+offset, 3)
        result += line(x+width, y+offset, x+width+15, y+offset, 3)
    return result


def control_loop():
    s = shell('一拍控制，先过质量门',
              '控制数据先经过质量门，可信后才更新SOC并检查保护；再经远程请求门生成开关命令。'
              '开关实际状态通过独立虚线回读保护与反馈检查，不把命令当作动作证据。', 'IG-008')
    # A sampled waveform enters a distinct quality gate before any arithmetic.
    s += [text(215, 235, '采样', 44), line(110, 420, 315, 420, 3),
          path('M112 375 L149 375 L149 335 L188 335 L188 359 L229 359 L229 319 L278 319 L278 348 L313 348', 5)]
    for x, y in ((149, 375), (188, 335), (229, 359), (278, 319)):
        s += [dot(x, y, 6)]
    s += [arrow(337, 365, 568, 365), text(720, 235, '质量门', 44),
          path('M720 278 L812 365 L720 452 L628 365 Z', 5),
          path('M680 363 L708 391 L762 332', 6), arrow(834, 365, 1075, 365),
          text(1210, 235, '更新SOC', 44)]
    # Charge is a ledger/gauge, not another rectangular text panel.
    s += [path('M1118 422 L1118 286 L1303 286 L1301 422 Z', 4),
          line(1142, 322, 1278, 322, 3), line(1142, 354, 1278, 354, 3),
          line(1142, 386, 1278, 386, 3), line(1184, 290, 1184, 419, 3),
          text(1146, 489, 'Ah', 36), text(1260, 489, 'SOC', 36),
          arrow(1210, 516, 1210, 595)]
    # Invalid data takes a short stop branch, not a bypass into the SOC stage.
    s += [arrow(720, 468, 720, 524, color=RED, width=4),
          line(695, 536, 745, 536, 7, RED),
          text(720, 592, '无效即禁用', 36, color=RED)]
    # Protection shield, request gate and a real open-contact symbol.
    s += [text(1210, 670, '保护', 44),
          path('M1136 695 Q1210 717 1284 695 L1280 752 Q1264 814 1210 841 Q1151 814 1140 752 Z', 5),
          line(1180, 760, 1240, 760, 5),
          arrow(1107, 744, 858, 744), text(720, 679, '远程门', 44),
          path('M655 703 L715 703 C823 702 823 787 715 787 L655 787 Z', 5),
          line(635, 726, 655, 726, 4), line(635, 766, 655, 766, 4),
          arrow(608, 744, 375, 744), text(235, 670, '命令', 44),
          _contact(235, 744)]
    # A separate feedback wire returns the actual contact state for checking.
    s += [dot(345, 744, 6), path('M345 744 L345 895 Q345 915 369 915 L1306 915 Q1330 915 1330 891 L1330 785', 4, dash='9 11'),
          arrow(1330, 785, 1296, 785, width=4, dash='9 11'),
          text(835, 976, '反馈回读', 44)]
    return finish(s)


def fault_origin():
    s = shell('找起因，沿三条轨迹向前看',
              '同一时间轴上的三条轨迹：0.30 s出现持续欠压；0.50 s发断开命令；'
              '反馈始终闭合，到0.70 s追加执行器卡住。最早观察到的异常是欠压，最后报错不替代起因。', 'IG-008')
    xs = (300, 750, 1200)
    s.append(arrow(240, 220, 1310, 220, width=4))
    for x, label in zip(xs, ('0.30 s', '0.50 s', '0.70 s'), strict=True):
        s += [text(x, 293, label, 48), line(x, 315, x, 854, 3, opacity=.45, dash='7 11')]
    s += [text(90, 415, '单节', 36, anchor='start'),
          line(240, 365, 300, 365), line(300, 365, 300, 440, 5, RED),
          line(300, 440, 1300, 440, 5, RED), dot(300, 440, 9, RED),
          text(530, 390, '≤3.00 V', 40, color=RED),
          path('M316 482 L316 500 L734 500 L734 482', 3),
          text(525, 557, '确认 0.20 s', 40)]
    s += [text(90, 647, '命令', 36, anchor='start'),
          line(240, 603, 750, 603), line(750, 603, 750, 683),
          line(750, 683, 1300, 683), dot(750, 683, 9),
          text(1010, 644, '断开', 40)]
    s += [text(90, 830, '反馈', 36, anchor='start'),
          line(240, 800, 1200, 800), line(1200, 800, 1300, 800, 6, RED),
          dot(1200, 800, 10, RED), text(840, 866, '仍闭合', 40),
          text(1220, 883, '卡住', 40, color=RED),
          path('M300 903 L300 926 L375 926', 3, RED),
          text(525, 976, '最早异常：欠压', 44, color=RED),
          text(1105, 976, '末尾故障：卡住', 44)]
    return finish(s)


def transfer_delivery():
    s = shell('换过条件，再交一份证据',
              '只给迁移输入，不给独立作答结果：容量从2 Ah变1.6 Ah，周期从0.10 s变0.05 s，'
              '欠压单节从第三节变第一节。先写预测，再运行，最后把输入、日志和报告放进可对照的文件夹。', 'IG-008')
    s += [text(275, 235, '容量', 44), text(720, 235, '周期', 44), text(1165, 235, '故障单节', 44)]
    # Battery capacities use the same outline: a smaller Ah value is not a
    # misleading claim that the physical drawing is a calibrated volume scale.
    for x in (135, 355):
        s += [path(f'M{x} 305 L{x+93} 305 L{x+93} 430 L{x} 430 Z', 4),
              path(f'M{x+29} 305 L{x+29} 291 L{x+64} 291 L{x+64} 305', 3)]
    s += [arrow(249, 368, 331, 368), text(180, 505, '2 Ah', 36), text(400, 505, '1.6 Ah', 36)]
    for y, step in ((320, 80), (410, 40)):
        s.append(line(560, y, 880, y, 3))
        for x in range(560, 881, step):
            s += [line(x, y-17, x, y+17, 3), dot(x, y, 4)]
    s += [arrow(720, 345, 720, 383, width=3), text(720, 505, '0.10 → 0.05 s', 36)]
    for row, bad_cell in ((322, 3), (413, 1)):
        for index in range(1, 5):
            x = 1010+(index-1)*94
            color = RED if index == bad_cell else INK
            s += [path(f'M{x} {row-25} L{x+57} {row-25} L{x+57} {row+27} L{x} {row+27} Z', 4, color),
                  line(x+15, row-34, x+42, row-34, 3, color)]
    s += [text(1170, 505, '3 → 1', 40)]
    # Three real folder silhouettes hold predictions, executable evidence and
    # the side-by-side comparison. No trip time, Ah result or SOC is exposed.
    for x, title in ((110, '预测'), (570, '运行'), (1030, '对照')):
        s += [text(x+150, 665, title, 44), _folder(x, 710, 300, 175)]
    s += [arrow(437, 801, 541, 801), arrow(897, 801, 1001, 801),
          text(260, 835, '?', 56), text(720, 835, '>_', 56),
          line(1115, 765, 1115, 856, 3), line(1220, 765, 1220, 856, 3)]
    for y in (776, 810, 844):
        s += [line(1060, y, 1100, y, 3), line(1130, y, 1205, y, 3), line(1235, y, 1300, y, 3)]
    s += [text(260, 962, '先写预期', 40), text(720, 962, '保留版本', 40),
          text(1180, 962, '输入·日志·报告', 36)]
    return finish(s)


def signal_chain():
    s = shell('从端子到开关，每段都要留证',
              '抽象信号链而非真实板卡接线：两条端子线经过电阻与电容滤波进入AFE，'
              '原始码交给MCU换算成有单位、时间和质量的数据；MCU控制驱动，驱动控制开关，实际状态独立返回MCU。', 'IG-002')
    # An abstract source with two explicit sampling nodes and a concrete RC
    # input. It is not a connection guide for a floating cell or a real AFE.
    s += [path('M112 304 Q140 290 169 305 L167 451 Q140 466 114 450 Z', 4),
          line(140, 302, 140, 252), line(140, 460, 140, 500),
          text(186, 303, '+', 34), text(186, 467, '−', 34),
          line(140, 252, 223, 252), resistor(223, 252, 320, 252),
          line(320, 252, 390, 252), line(390, 252, 390, 342), line(390, 342, 430, 342),
          line(140, 500, 390, 500), line(390, 500, 390, 464), line(390, 464, 430, 464),
          line(352, 252, 352, 368), line(326, 368, 378, 368, 4),
          line(326, 391, 378, 391, 4), line(352, 391, 352, 500),
          dot(352, 252, 6), dot(352, 500, 6),
          text(140, 611, '端子', 40), text(330, 611, '滤波', 40)]
    for x, width, title, label in ((430, 210, 'AFE', '原始码'),
                                   (730, 210, 'MCU', '换算'),
                                   (1040, 240, '驱动', '')):
        s += [_chip(x, 294, width, 240), text(x+width/2, 396, title, 48)]
        if label:
            s.append(text(x+width/2, 481, label, 36))
    s += [arrow(660, 410, 706, 410, width=4), arrow(961, 410, 1016, 410, width=4),
          text(830, 611, 'V · s · 质量', 36),
          arrow(1160, 558, 1160, 657), _contact(1160, 755),
          text(1160, 859, '开关', 44), dot(1270, 755, 6)]
    s += [path('M1270 755 L1325 755 L1325 933 L1005 933 L1005 474', 4, dash='9 11'),
          arrow(1005, 474, 955, 474, width=4, dash='9 11'), text(1005, 987, '反馈', 44)]
    return finish(s)


def timing_budget():
    s = shell('时间预算，要把等待也算上',
              '设计预算而非实测：严格0.10 s等间隔采样，最多等待0.10 s发现越线，'
              '随后确认0.20 s，额外处理不超过0.01 s，总预算0.31 s。'
              '主尺三段按时长比例绘制；允许抖动的另一种假设还需另加最多一个采样周期。', 'IG-004')
    left, right = 200, 1240
    scale = (right-left)/.31
    first, second = left+.10*scale, left+.30*scale
    s += [text(425, 250, '严格周期 0.10 s', 40), text(1060, 250, '设计预算·非实测', 36),
          text((left+first)/2, 439, '等采样', 44), text((first+second)/2, 439, '确认', 44),
          text(1223, 353, '处理', 40), text(1223, 426, '0.01 s', 36),
          line(1223, 452, (second+right)/2, 538, 3)]
    s += [path(f'M{left} 550 L{right} 550 L{right} 650 L{left} 650 Z', 4),
          line(first, 550, first, 650, 4), line(second, 550, second, 650, 4)]
    for x in range(left+18, int(first)-12, 34):
        s.append(line(x, 635, x+16, 568, 2, opacity=.55))
    for x in range(int(first)+20, int(second)-20, 42):
        s.append(line(x, 570, x+20, 635, 2, opacity=.55))
    for x in (left, first, second, right):
        s.append(line(x, 653, x, 681, 3))
    s += [text((left+first)/2, 733, '0.10 s', 48), text((first+second)/2, 733, '0.20 s', 48),
          text(720, 839, '0.10 + 0.20 + 0.01 = 0.31 s', 44)]
    s += [line(200, 941, 535, 941, 4, dash='8 10'),
          line(200, 923, 200, 959, 3), line(535, 923, 535, 959, 3),
          text(980, 957, '抖动另加 ≤0.10 s', 40)]
    return finish(s)


def engineering_paths():
    s = shell('三条工程路，先交一件作品',
              '三条工程路线汇入一个可审查的作品文件夹。测量路线对应原始码与参考读数；'
              '模型路线先分组数据，以基线和独立验证集对照；系统路线保留输入、日志与报告。'
              '作品必须带版本和复现步骤，不以术语清单代替交付。', 'IG-008')
    s += [text(270, 226, '测量', 44), text(1170, 226, '模型', 44)]
    # Measurement: a raw-code ruler and a separate reference meter, connected
    # by an annotation rather than an assertion that either is ground truth.
    s += [text(270, 310, '原始码', 40), line(115, 370, 425, 370, 3)]
    for i in range(9):
        x = 115+i*38
        s.append(line(x, 354, x, 386, 3))
    s += [dot(305, 370, 9), _circle(270, 497, 72),
          line(270, 497, 305, 454, 4), dot(270, 497, 6), text(270, 548, 'V', 36),
          text(270, 648, '参考读数', 40), arrow(425, 463, 559, 521, width=4)]
    # Model: preserve group identities before fitting, with a visibly held-out
    # group and an independent baseline trace. No new performance claim.
    s += [text(1170, 310, '数据分组', 40)]
    for group, x in enumerate((1070, 1165, 1260)):
        for dy in (0, 30, 60):
            s.append(dot(x, 352+dy, 7))
        if group == 2:
            s.append(path(f'M{x-28} 331 L{x+28} 331 L{x+28} 435 L{x-28} 435 Z', 3, dash='6 8'))
    s += [line(1030, 555, 1310, 555, 3), line(1030, 555, 1030, 458, 3),
          path('M1034 533 Q1083 530 1117 501 T1195 505 T1303 470', 4),
          line(1034, 529, 1304, 485, 3, dash='7 8'),
          text(1170, 648, '基线·独立验证', 36), arrow(1014, 463, 881, 521, width=4)]
    # The single portfolio folder is the focal point of all three routes.
    s += [_folder(580, 411, 280, 235), text(720, 548, '可审作品', 44),
          text(720, 618, '版本·复现', 36)]
    # System evidence consists of three distinct sheets, then flows upward
    # into the same reviewable work instead of a separate completion badge.
    s += [text(1040, 793, '系统', 44), arrow(720, 758, 720, 670, width=4)]
    for x in (390, 625, 860):
        s += [path(f'M{x} 799 L{x+118} 799 L{x+146} 827 L{x+146} 922 L{x} 922 Z', 4),
              path(f'M{x+118} 799 L{x+118} 827 L{x+146} 827', 3)]
        for dy in (57, 83, 109):
            s.append(line(x+22, 799+dy, x+121, 799+dy, 3))
    s += [text(463, 983, '输入', 40), text(698, 983, '日志', 40), text(933, 983, '报告', 40)]
    return finish(s)


DRAWINGS = {
    '19-control-loop.svg': control_loop,
    '20-fault-origin.svg': fault_origin,
    '21-transfer-delivery.svg': transfer_delivery,
    '22-signal-chain.svg': signal_chain,
    '23-timing-budget.svg': timing_budget,
    '24-engineering-paths.svg': engineering_paths,
}
