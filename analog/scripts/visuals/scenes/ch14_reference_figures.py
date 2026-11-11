"""Design-method diagrams: explicit reference levels, units and statistical assumptions."""
from __future__ import annotations

import math

from scripts.visuals.scenes.handdrawn_wave2 import (
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

BUDGET = (.03, .04, .05, .005, .01, .04)


def rss(values):
    return math.sqrt(sum(value**2 for value in values))


def uniform_three_pdf(x):
    """Density of the sum of three independent U[-1, 1] variables."""
    return sum((-1)**k * math.comb(3, k) * max(x+3-2*k, 0)**2
               for k in range(4)) / 16 if -3 <= x <= 3 else 0


def pt100_zero():
    p = [header('先扣零点，再讨论 40 倍增益',
                '线性示意 PT100：100–138.5 Ω、1 mA；原始电压 100–138.5 mV。')]
    for y, label, start, end, colour in (
        (250, '直接 ×40', 4, 5.54, RED),
        (420, '减 100 mV 后 ×40', 0, 1.54, BLUE),
    ):
        p.append(text(60, y-50, label, 26, colour=colour, weight='700'))
        for v in (0, 2, 4, 6):
            x = 140 + v*120
            p += [f'<line x1="{x}" y1="{y-15}" x2="{x}" y2="{y+20}" stroke="{RULE}"/>',
                  text(x, y+52, str(v), 22, anchor='middle')]
        p += [f'<line x1="140" y1="{y}" x2="860" y2="{y}" stroke="{INK2}"/>',
              f'<rect x="{140+start*120}" y="{y-12}" width="{(end-start)*120}" height="24" fill="{colour}"/>',
              text(140+(start+end)/2*120, y-26, f'{start:g}–{end:g} V', 24, anchor='middle', colour=colour)]
    p += [text(60, 540, 'ADC 满量程 2.048 V；下行是扣零点后的理想增量范围。', 23),
          text(60, 588, '实际加基线偏置并留输出摆幅、输入共模和端点余量。', 23),
          text(60, 636, '1 LSB = 500 µV，折合 0.03247 °C；不等于系统准确度。', 22, colour=INK2)]
    return p


def meas_window():
    p = [header('测量窗口要跟着被测事件走',
                '时域阶跃示意，无数值时间轴；先定阶跃时刻，再定峰值与建立判据。')]
    p.append(f'<path d="M100 170 V460 H900" fill="none" stroke="{INK2}" stroke-width="2"/>')
    p.append(f'<rect x="320" y="190" width="530" height="260" fill="{PAPER}" stroke="{BLUE}" stroke-dasharray="6 6"/>')
    p.append(f'<path d="M100 430 H320 C340 430 340 190 390 190 S460 360 510 300 S600 290 680 300 H880" fill="none" stroke="{BLUE}" stroke-width="3"/>')
    p.append(f'<line x1="100" y1="300" x2="900" y2="300" stroke="{GREEN}" stroke-dasharray="5 5"/>')
    p += [text(320, 498, '阶跃 t₀', 23, anchor='middle'), text(850, 498, '窗口末端', 23, anchor='middle'),
          text(420, 162, '峰值', 24, colour=BLUE), text(740, 278, '最终稳态', 22, colour=GREEN),
          text(60, 550, '.meas 的 MAX/MIN 要限定事件之后；稳态值另取稳定区间。', 22),
          text(60, 598, '建立时间：进入并持续留在指定误差带内，不只看首次穿越。', 22),
          text(60, 646, '.ac 是工作点附近线性化；不能替代饱和、限流或启动的 .tran。', 22, colour=INK2)]
    return p


def buck_budget():
    components = (math.sqrt(2)/6, 1/3, .2/3, .5/3)
    p = [header('反馈分压：先算灵敏度，再写分布假设',
                'R1 = R2；一阶相对误差 δV ≈ δVref + (δR1−δR2)/2。')]
    labels = ('两只电阻合成', '基准初始', '基准温漂', '负载调整率')
    for i, (label, value) in enumerate(zip(labels, components, strict=True)):
        y=210+i*78
        p += [text(60, y+8, label, 24),
              f'<rect x="310" y="{y-12}" width="{value/.4*470}" height="24" fill="{BLUE}"/>',
              text(330+value/.4*470,y+8,f'{value:.4f}%',23,colour=BLUE)]
    p += [text(60, 560, f'独立、零均值、限值按 3σ 的演示假设：合成 σ ≈ {rss(components):.4f}%。',22),
          text(60, 608, '一阶 WC = 2.7%；真实电阻比的非线性极限须另算。',23),
          text(60, 654, '器件限值不能自动除以 3；分布和相关性必须有实测或规格依据。',22,colour=INK2)]
    return p


def ratio_cancel():
    p = [header('比率测量抵消共同项，不是消灭所有误差',
                '理想示意：同一 Vref 激励传感器并作为 ADC 参考，先忽略放大器。')]
    p += [box(350,145,300,76),text(500,195,'共同 Vref',28,anchor='middle',colour=BLUE),
          varrow(400,230,250,310,BLUE,3),varrow(600,230,750,310,BLUE,3),
          box(60,325,400,115),box(540,325,400,115),
          text(260,370,'I = Vref / Rset',26,anchor='middle'),
          text(260,412,'VPT = I × RPT',24,anchor='middle'),
          text(740,370,'归一化 ADC 码',26,anchor='middle'),
          text(740,412,'VPT / Vref',24,anchor='middle'),
          text(500,512,'VPT / Vref = RPT / Rset',30,anchor='middle',colour=GREEN,weight='700'),
          text(60,580,'共同 Vref 因子约掉；Rset、引线、自热、失调与噪声仍在。',22),
          text(60,628,'参考缓冲和不同温度路径的残差另建模；不要重复计同一共同项。',22,colour=INK2)]
    return p


def error_budget():
    p = [header('先统一统计口径，再比较预算贡献',
                '六项演示数值：若作为独立 1σ，RSS 是标准差；若作为界限，另算 WC。')]
    labels=('传感','激励残差','放大','滤波','ADC','参考链残差')
    for i,(label,value) in enumerate(zip(labels,BUDGET, strict=True)):
        y=172+i*58
        p += [text(60,y+8,label,23),
              f'<rect x="300" y="{y-10}" width="{value/.05*430}" height="20" fill="{BLUE}"/>',
              text(320+value/.05*430,y+8,f'{value:g} °C',22)]
    p += [text(60,552,f'作为 1σ：RSS = {rss(BUDGET):.6f} °C；3σ = {3*rss(BUDGET):.6f} °C。',22),
          text(60,600,'作为误差界限的另一组假设：WC = 0.175 °C；不能混作同一口径。',22),
          text(60,648,'0.1 °C 若是绝对误差要求，不能因 1σ < 0.1 就宣布通过。',22,colour=RED)]
    return p


def uniform_sum():
    p = [header('三个均匀误差之和，仍然不是正态分布',
                '每项独立 U[−1%, +1%]，合成 σ = 1%；支撑范围是 −3% 至 +3%。')]
    p.append(f'<path d="M110 180 V470 H900" fill="none" stroke="{INK2}" stroke-width="2"/>')
    points=[]
    for i in range(121):
        value=-3+i*.05
        points.append(f'{505+value*120:.1f},{470-uniform_three_pdf(value)*650:.1f}')
    p.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{BLUE}" stroke-width="3"/>')
    for value in range(-3,4):
        x=505+value*120
        p += [text(x,510,f'{value}%',22,anchor='middle')]
        if abs(value)==2:
            p.append(f'<line x1="{x}" y1="210" x2="{x}" y2="470" stroke="{RED}" stroke-dasharray="5 5"/>')
    p += [text(60,560,'落在 ±2% 内的精确概率 = 23/24 ≈ 95.83%；不是 99.7%。',22),
          text(60,608,'目标放宽至 ±4%：WC 与 3σ 尺度均小于目标，都通过。',22),
          text(60,656,'只把一项从 ±1% 降至 ±0.5%，WC 仍为 ±2.5%，不满足 ±2%。',22,colour=INK2)]
    return p


def bom_trace():
    p = [header('BOM 的每项要求，要接到一个验证动作',
                '示意连线表示追溯关系，不表示完整电路；候选器件仍需选具体型号。')]
    rows=(('0.1% 增益电阻','40 倍增益及温漂','零点/满量程校准'),
          ('10 ppm/°C 参考链','共同项与独立残差分开','温箱中固定输入'),
          ('接口保护器件','钳位、寄生与回流','按适用等级做 ESD'))
    for y, row in zip((200,345,490),rows, strict=True):
        for x,label in zip((55,370,685),row, strict=True):
            p += [box(x,y,260,84),text(x+130,y+50,label,22,anchor='middle')]
        p += [varrow(320,y+42,360,y+42,BLUE,2),varrow(635,y+42,675,y+42,BLUE,2)]
    p += [text(60,150,'器件要求',24),text(380,150,'对应预算',24),text(700,150,'测试证据',24),
          text(60,636,'封装、容差与替代料条件一起冻结；无法对应预算的参数要追问来源。',22)]
    return p


def design_evidence():
    p = [header('设计说明交付的是可复核证据',
                '五项互相对应；至少覆盖 3 个 corner，失败后有下一步测量。')]
    rows=(('指标','量程、带宽、精度、功耗与环境'),
          ('选型','器件窗口、封装、备选与否决理由'),
          ('极限工况','供电、温度、负载与容差的组合'),
          ('测试','仪器、接法、步骤、数字判据'),
          ('失败预案','先测哪一节点，用结果区分假设'))
    for i,(label,desc) in enumerate(rows):
        y=150+i*91
        p += [box(60,y,190,65),text(155,y+42,label,25,anchor='middle',colour=BLUE),
              varrow(265,y+32,335,y+32,BLUE,2),text(355,y+42,desc,23)]
    p.append(text(60,662,'PT100 练习：0–100 °C、0.1 °C 分辨力、3.3 V；不要把分辨力写成准确度。',22,colour=INK2))
    return p


SCENES={
    'ch14-pt100-zero-v2': {'draw':pt100_zero,'title':'PT100 零点与增量','anchor':'14.4','alt':'1mA 激励下 100至138.5mV 直接乘40得4至5.54V，超出2.048V量程；先扣100mV再放大得0至1.54V理想增量，实际须加基线偏置并核共模与输出余量。'},
    'ch14-meas-window-v2': {'draw':meas_window,'title':'仿真测量的时间窗口','anchor':'14.6','alt':'阶跃时刻后的窗口包含峰值和稳定区域；峰值与稳态测量区间分开，建立时间要求进入并留在容差带，AC线性化不能验证大信号饱和。'},
    'ch14-buck-budget-v2': {'draw':buck_budget,'title':'反馈分压误差的统计假设','anchor':'14.8','alt':'电阻比为一时两只电阻相对灵敏度分别正负二分之一；限值按3sigma且独立的演示模型，电阻、参考初始、温漂、负载贡献为0.2357、0.3333、0.0667、0.1667%，总sigma约0.4460%，一阶WC为2.7%。'},
    'ch14-ratio-cancel-v2': {'draw':ratio_cancel,'title':'比率测量抵消共同因子','anchor':'14.9','alt':'共同参考电压用于激励和ADC参考，理想归一化码等于RPT除以Rset；共同电压因子约掉，设定电阻、引线、自热、失调及独立噪声仍须预算。'},
    'ch14-error-budget-v2': {'draw':error_budget,'title':'PT100 预算统计口径','anchor':'14.9','alt':'六项0.03、0.04、0.05、0.005、0.01、0.04摄氏度按独立1sigma解释时RSS为0.082006，3sigma为0.246018；若改作误差上限则WC为0.175，不能混用。'},
    'ch14-uniform-sum-v2': {'draw':uniform_sum,'title':'三个均匀误差的覆盖率','anchor':'14.10','alt':'三个独立正负1%均匀误差之和的概率密度，范围正负3%，sigma为1%；正负2%内概率23/24约95.83%，正负4%目标下WC和3sigma都通过。'},
    'ch14-bom-trace-v2': {'draw':bom_trace,'title':'BOM 预算与测试追溯','anchor':'14.12','alt':'三行对应：0.1%增益电阻到40倍增益及校准，10ppm每摄氏度参考链到残差预算及温箱测试，保护器件到钳位回流及板级ESD测试；封装和替代料一起核对。'},
    'ch14-design-evidence-v2': {'draw':design_evidence,'title':'设计说明的五项证据','anchor':'设计说明作业（精通出口）','alt':'指标、选型、极限工况、测试、失败预案五项逐行对应验证材料；至少三个corner；PT100练习0到100摄氏度、0.1摄氏度分辨力和3.3伏供电，不把分辨力当准确度。'},
}
for meta in SCENES.values():
    meta.update(chapter=14,source='docs/p3-01-ch14.md',renderer='handdrawn')
