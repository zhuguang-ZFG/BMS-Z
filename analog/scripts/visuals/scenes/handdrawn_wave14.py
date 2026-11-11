"""Wave 14 手绘草图：补最薄的五章（ch12 开关电容与输入级选型、ch11 相位裕度换算、
ch6 741 四级分工、ch1 戴维南两负载实测）。

每张图的数字只取对应 anchor 小节：ch12 取 12.12 的等效电阻算例与 12.13 的源阻判据，
ch11 取 11.5 的 PM/ζ/过冲换算表，ch6 取 6.1 的四级与补偿三笔账，
ch1 取 1.4 的分压算例与两负载实测。
"""
from __future__ import annotations

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK, INK2, PAPER, RED, RULE, arrow, box, header, text,
)


def switched_cap_equivalent():
    parts = [header('开关电容：用时钟和电容"造"一只电阻',
                    '硅片上电阻做不准，就让电容按节拍一包包搬电荷——搬多大看比值，搬多快看晶振。')]
    parts.append(box(50, 130, 430, 240, fill=PAPER, stroke=BLUE))
    parts.append(text(74, 172, '一个时钟周期搬一包电荷', 24, colour=BLUE, weight='700'))
    parts.append(text(74, 216, '每周期搬运 ΔQ = C·ΔV', 22, colour=INK2))
    parts.append(text(74, 252, '平均电流 I = f_clk·C·ΔV', 22, colour=INK2))
    parts.append(f'<line x1="80" y1="280" x2="450" y2="280" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(74, 322, '等效电阻 R = 1 / (f_clk·C)', 24, colour=INK, weight='700'))
    parts.append(text(74, 356, '阻值只由 f_clk 与 C 决定', 22, colour=INK2))

    parts.append(box(520, 130, 430, 240, fill=PAPER, stroke=GREEN))
    parts.append(text(544, 172, '一个算例', 24, colour=GREEN, weight='700'))
    parts.append(text(544, 218, '1 pF 电容', 22, colour=INK2))
    parts.append(text(544, 254, '100 kHz 时钟', 22, colour=INK2))
    parts.append(f'<line x1="550" y1="282" x2="920" y2="282" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(544, 324, '等于', 22, colour=INK2))
    parts.append(text(926, 328, '10 MΩ', 30, colour=GREEN, anchor='end', weight='700'))
    parts.append(text(544, 358, '硅片上几乎不占面积', 22, colour=AMBER, weight='700'))

    parts.append(box(50, 392, 900, 110, fill=PAPER))
    parts.append(text(76, 432, '时间常数里没有"绝对电阻"了，只剩两样最准的东西', 24,
                      colour=INK, weight='700'))
    parts.append(text(76, 470, '电容比值——IC 里匹配到 0.1%；一个晶振——准到 ppm', 22, colour=INK2))

    parts.append(box(50, 516, 900, 110, fill=PAPER, stroke=RED))
    parts.append(text(76, 556, '代价：它从此是个采样系统', 24, colour=RED, weight='700'))
    parts.append(text(76, 594, '有采样就有混叠，前面必须加抗混叠滤波器；时钟常取信号带宽的 50~100 倍',
                      22, colour=INK2))
    return parts


def input_stage_by_source_z():
    parts = [header('输入级选型只有一个判据：源阻抗',
                    '偏置电流在源阻抗上直接变成误差电压，所以同一句"低噪声"，换个源阻结论就翻过来。')]
    parts.append(text(74, 146, '误差电压 V_err = I_b · R_s', 24, colour=INK, weight='700'))

    parts.append(box(50, 170, 430, 230, fill=PAPER, stroke=RED))
    parts.append(text(74, 210, '高源阻：1 MΩ 光电二极管', 24, colour=RED, weight='700'))
    parts.append(text(74, 252, 'BJT 输入，I_b = 20 nA', 22, colour=INK2))
    parts.append(text(456, 254, '20 mV', 26, colour=RED, anchor='end', weight='700'))
    parts.append(text(74, 290, '每升 10 °C 翻倍，40 °C 时', 22, colour=INK2))
    parts.append(text(456, 292, '80 mV', 26, colour=RED, anchor='end', weight='700'))
    parts.append(f'<line x1="80" y1="314" x2="450" y2="314" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(74, 354, 'CMOS 输入，I_b = 1 pA', 22, colour=INK2))
    parts.append(text(456, 356, '1 µV', 26, colour=GREEN, anchor='end', weight='700'))
    parts.append(text(74, 390, '好了四个数量级', 22, colour=GREEN, weight='700'))

    parts.append(box(520, 170, 430, 230, fill=PAPER, stroke=GREEN))
    parts.append(text(544, 210, '低源阻：10 kΩ', 24, colour=GREEN, weight='700'))
    parts.append(text(544, 252, '电阻自身热噪声是地板', 22, colour=INK2))
    parts.append(text(926, 254, '12.9 nV/√Hz', 24, colour=INK, anchor='end', weight='700'))
    parts.append(f'<line x1="550" y1="276" x2="920" y2="276" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(544, 316, 'BJT 总噪声', 22, colour=INK2))
    parts.append(text(926, 318, '13.8', 26, colour=GREEN, anchor='end', weight='700'))
    parts.append(text(544, 354, 'CMOS 总噪声', 22, colour=INK2))
    parts.append(text(926, 356, '23.8', 26, colour=RED, anchor='end', weight='700'))
    parts.append(text(544, 390, 'BJT 赢 1.7 倍', 22, colour=GREEN, weight='700'))

    parts.append(box(50, 418, 900, 96, fill=PAPER, stroke=BLUE))
    parts.append(text(76, 458, '一句话记法', 24, colour=BLUE, weight='700'))
    parts.append(text(280, 458, '低源阻挑 e_n 小的 BJT，高源阻挑 I_b 小的 CMOS / JFET', 22,
                      colour=INK))
    parts.append(text(280, 496, '中间地带比一比 e_n 与 i_n·R_s 谁大', 22, colour=INK2))

    parts.append(box(50, 530, 900, 96, fill=PAPER, stroke=AMBER))
    parts.append(text(76, 570, '买 RRIO 之前要知道的代价', 24, colour=AMBER, weight='700'))
    parts.append(text(76, 608, 'NMOS 对与 PMOS 对交接班处跨导凹陷：失真从 0.001% 抬到 0.01% 量级，'
                      '失调出现台阶', 22, colour=INK2))
    return parts


def phase_margin_conversion():
    parts = [header('相位裕度为什么定在 60°',
                    '它把过冲压到 10% 附近，又不牺牲太多带宽——这张换算表是运放闭环最常用的一张。')]
    rows = [
        ('45°', '0.42', '23%', '过冲偏大', 182, AMBER),
        ('60°', '0.59', '10%', '设计目标', 268, GREEN),
        ('65°', '0.71', '4%', 'Butterworth', 354, BLUE),
    ]
    parts.append(text(80, 164, '相位裕度 PM', 22, colour=INK2))
    parts.append(text(300, 164, '阻尼比 ζ', 22, colour=INK2))
    parts.append(text(470, 164, '闭环过冲', 22, colour=INK2))
    parts.append(text(650, 164, '评价', 22, colour=INK2))
    for pm, zeta, over, note, y, colour in rows:
        parts.append(box(50, y, 900, 72, fill=PAPER, stroke=colour))
        parts.append(text(80, y + 46, pm, 28, colour=colour, weight='700'))
        parts.append(text(300, y + 46, zeta, 26, colour=INK))
        parts.append(text(470, y + 46, over, 26, colour=INK, weight='700'))
        parts.append(text(650, y + 46, note, 22, colour=INK2))

    parts.append(box(50, 444, 430, 182, fill=PAPER, stroke=RED))
    parts.append(text(74, 484, '极点数决定能不能稳', 24, colour=RED, weight='700'))
    parts.append(text(74, 524, '1 个极点：相移 −90°，永不振荡但慢', 22, colour=INK2))
    parts.append(text(74, 560, '2 个极点：次极点越近、相移越多', 22, colour=INK2))
    parts.append(text(74, 596, '3 个极点：可逼近 −180°，振荡', 22, colour=RED, weight='700'))

    parts.append(box(520, 444, 430, 182, fill=PAPER, stroke=BLUE))
    parts.append(text(544, 484, '每个极点收两笔税', 24, colour=BLUE, weight='700'))
    parts.append(text(544, 524, '高频贡献 −20 dB/dec 斜率', 22, colour=INK2))
    parts.append(text(544, 560, '并吃掉 90° 相位', 22, colour=INK2))
    parts.append(text(544, 596, '裕度就是交点处还剩多少相位', 22, colour=AMBER, weight='700'))
    return parts


def opamp_four_blocks():
    from scripts.visuals.scenes.ch06_reference_figures import SCENES as corrected
    return corrected['ch06-741-four-blocks']['draw']()


def thevenin_two_load_test():
    parts = [header('戴维南：把任何线性网络压成两个数',
                    '带不带得动，永远只需比内阻与负载两个数。但等效之前，先确认网络真的线性。')]
    parts.append(box(50, 130, 430, 250, fill=PAPER, stroke=BLUE))
    parts.append(text(74, 170, '算一笔：12 V 经两只 10k 分压', 24, colour=BLUE, weight='700'))
    parts.append(text(74, 214, '开路电压', 22, colour=INK2))
    parts.append(text(456, 216, '6 V', 26, colour=INK, anchor='end', weight='700'))
    parts.append(text(74, 252, '短路电流', 22, colour=INK2))
    parts.append(text(456, 254, '1.2 mA', 26, colour=INK, anchor='end', weight='700'))
    parts.append(f'<line x1="80" y1="276" x2="450" y2="276" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(74, 316, '内阻', 22, colour=INK2))
    parts.append(text(456, 318, '5 kΩ', 30, colour=BLUE, anchor='end', weight='700'))
    parts.append(text(74, 358, '与 R1 并 R2 算得一致', 22, colour=INK2))

    parts.append(box(520, 130, 430, 250, fill=PAPER, stroke=GREEN))
    parts.append(text(544, 170, '带载误差一眼看出', 24, colour=GREEN, weight='700'))
    parts.append(text(544, 214, '负载等于内阻时', 22, colour=INK2))
    parts.append(text(926, 216, '只剩一半 3 V', 24, colour=RED, anchor='end', weight='700'))
    parts.append(text(544, 252, '负载 1 MΩ 时', 22, colour=INK2))
    parts.append(text(926, 254, '5.97 V', 24, colour=GREEN, anchor='end', weight='700'))
    parts.append(text(544, 290, '差', 22, colour=INK2))
    parts.append(text(926, 292, '0.5%', 24, colour=GREEN, anchor='end', weight='700'))
    parts.append(f'<line x1="550" y1="314" x2="920" y2="314" stroke="{RULE}" stroke-width="2"/>')
    parts.append(text(544, 342, '负载等于内阻拿到最大功率，', 22, colour=INK2))
    parts.append(text(544, 368, '但效率只有 50%', 22, colour=AMBER, weight='700'))

    parts.append(box(50, 400, 900, 226, fill=PAPER, stroke=RED))
    parts.append(text(76, 440, '两负载法实测：算不出一致的内阻，就说明它不是纯线性', 24,
                      colour=RED, weight='700'))
    parts.append(text(76, 486, '某传感器开路电压 2.52 V', 22, colour=INK))
    parts.append(text(76, 524, '接 100 kΩ 读 2.40 V', 22, colour=INK2))
    parts.append(text(470, 524, '反推内阻 5 kΩ', 24, colour=INK, weight='700'))
    parts.append(text(76, 562, '接 10 kΩ 读 1.80 V', 22, colour=INK2))
    parts.append(text(470, 562, '反推内阻 4 kΩ', 24, colour=RED, weight='700'))
    parts.append(text(76, 606, '两组不一致 → 端口可能含偏置电流或保护二极管，戴维南的两个数装不下它',
                      22, colour=AMBER, weight='700'))
    return parts


SCENES = {
    'ch12-switched-cap-equivalent': {
        'draw': switched_cap_equivalent, 'title': '开关电容等效电阻的来历与代价',
        'anchor': '12.12', 'chapter': 12, 'source': 'docs/p2-02-ch12.md',
        'alt': '手绘开关电容两栏：左栏写一个时钟周期搬一包电荷，每周期搬运 ΔQ 等于 C 乘 ΔV，'
               '平均电流等于 f_clk 乘 C 乘 ΔV，等效电阻等于 1 除以 f_clk 乘 C，阻值只由 f_clk 与 C 决定；'
               '右栏算例给 1 皮法电容加 100 千赫时钟等于 10 兆欧，硅片上几乎不占面积。'
               '中段写时间常数里没有绝对电阻了，只剩两样最准的东西：电容比值在 IC 里匹配到 0.1%，'
               '一个晶振准到 ppm。底部红框写代价是它从此是个采样系统，有采样就有混叠，'
               '前面必须加抗混叠滤波器，时钟常取信号带宽的 50 到 100 倍。',
    },
    'ch12-input-stage-source-z': {
        'draw': input_stage_by_source_z, 'title': '按源阻抗选运放输入级',
        'anchor': '12.13', 'chapter': 12, 'source': 'docs/p2-02-ch12.md',
        'alt': '手绘输入级选型两栏，顶部写误差电压等于偏置电流乘源阻抗。左侧红框高源阻 1 兆欧光电二极管：'
               'BJT 输入偏置电流 20 纳安得 20 毫伏，偏置电流每升 10 摄氏度约翻一倍、40 摄氏度时 80 毫伏；'
               'CMOS 输入偏置电流 1 皮安得 1 微伏，好了四个数量级。右侧绿框低源阻 10 千欧：'
               '电阻自身热噪声是地板 12.9 纳伏每根号赫兹，BJT 总噪声 13.8、CMOS 总噪声 23.8，BJT 赢 1.7 倍。'
               '下方蓝框一句话记法：低源阻挑电压噪声小的 BJT，高源阻挑偏置电流小的 CMOS 或 JFET，'
               '中间地带比一比电压噪声与电流噪声乘源阻谁大。底部琥珀框写买轨到轨输入输出之前要知道的代价：'
               'NMOS 对与 PMOS 对交接班处跨导凹陷，失真从 0.001% 抬到 0.01% 量级，失调出现台阶。',
    },
    'ch11-phase-margin-table': {
        'draw': phase_margin_conversion, 'title': '相位裕度与阻尼比过冲的换算',
        'anchor': '11.5', 'chapter': 11, 'source': 'docs/p2-01-ch11.md',
        'alt': '手绘三行换算表，列为相位裕度、阻尼比、闭环过冲与评价：相位裕度 45 度对阻尼比 0.42、'
               '过冲 23%，评价过冲偏大；60 度对 0.59、过冲 10%，评价设计目标；'
               '65 度对 0.71、过冲 4%，评价 Butterworth。左下红框写极点数决定能不能稳：'
               '1 个极点相移负 90 度，永不振荡但慢；2 个极点时次极点越近、相移越多；'
               '3 个极点可逼近负 180 度，振荡。右下蓝框写每个极点收两笔税：'
               '高频贡献负 20 分贝每十倍频斜率，并吃掉 90 度相位，裕度就是交点处还剩多少相位。',
    },
    'ch06-741-four-blocks': {
        'draw': opamp_four_blocks, 'title': '741 内部四级的分工与补偿代价',
        'anchor': '6.1', 'chapter': 6, 'source': 'docs/p1-07-ch6.md',
        'alt': '手绘 741 四级框图。左侧四块：差分输入级是长尾对加电流镜负载，'
               '决定失调电压、偏置电流与输入阻抗；中间增益级是共射放大加密勒补偿，开环增益约 200,000 倍；'
               '输出级是互补推挽加 AB 类偏置，决定带载能力与失真指标。'
               '实心箭头自上而下穿过这三级，表示信号通路。'
               '第四块标着偏置网络（不在信号通路），是电流镜阵列，给全芯片供稳定偏流，'
               '它下方不接箭头，以此与前三级区分。'
               '一条红色箭头从中间增益级指向右侧红框，表示补偿电容只属于这一级：'
               '补偿电容 30 皮法，把主极点压到 10 赫兹量级，定增益带宽积，定压摆率，'
               '741 只有 0.5 伏每微秒，这是稳定的代价。'
               '底部写增益按级相乘：输入级几百倍乘中间级几百到上千倍等于 741 的 20 万倍。',
    },
    'ch01-thevenin-two-load': {
        'draw': thevenin_two_load_test, 'title': '戴维南等效与两负载法实测内阻',
        'anchor': '1.4', 'chapter': 1, 'source': 'docs/p1-02-ch1.md',
        'alt': '手绘戴维南三块：左上蓝框算一笔 12 伏经两只 10 千欧分压，开路电压 6 伏、短路电流 1.2 毫安、'
               '内阻 5 千欧，与 R1 并 R2 算得一致；右上绿框带载误差一眼看出，负载等于内阻时只剩一半 3 伏，'
               '负载 1 兆欧时 5.97 伏、差 0.5%，负载等于内阻拿到最大功率但效率只有 50%。'
               '底部红框两负载法实测：某传感器开路电压 2.52 伏，接 100 千欧读 2.40 伏反推内阻 5 千欧，'
               '接 10 千欧读 1.80 伏反推内阻 4 千欧，两组不一致说明端口可能含偏置电流或保护二极管，'
               '戴维南的两个数装不下它。',
    },
}

# Keep historical batch entry points aligned with corrected chapter models.
from scripts.visuals.scenes.ch06_reference_figures import SCENES as _ch06_corrected
SCENES['ch06-741-four-blocks'] = _ch06_corrected['ch06-741-four-blocks']

# Corrected chapter 11 model and visual contract.
from scripts.visuals.scenes.ch11_reference_figures import SCENES as _ch11_corrected
SCENES['ch11-phase-margin-table'] = _ch11_corrected['ch11-phase-margin-table']

# Corrected chapter 12 models and source conditions.
from scripts.visuals.scenes.ch12_reference_figures import SCENES as _ch12_corrected
SCENES['ch12-switched-cap-equivalent'] = _ch12_corrected['ch12-switched-cap-equivalent']
SCENES['ch12-input-stage-source-z'] = _ch12_corrected['ch12-input-stage-source-z']
