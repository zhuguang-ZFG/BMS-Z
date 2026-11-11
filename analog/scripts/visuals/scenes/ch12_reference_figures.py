"""Connection diagrams and constrained budgets for chapter 12 applications."""
from scripts.visuals.scenes.handdrawn_wave2 import BLUE, GREEN, INK, INK2, PAPER, RED, RULE, box, header, text
from scripts.visuals.primitives import directed_arrow as arrow
from scripts.visuals import application_models as m


def wire(x1,y1,x2,y2):
    return f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="{INK}" stroke-width="3"/>'


def resistor(x,y,label):
    return wire(x,y,x+15,y)+box(x+15,y-12,65,24,fill=PAPER)+wire(x+80,y,x+95,y)+text(x+47,y-28,label,23,anchor='middle')


def cap(x,y,label,vertical=False):
    if vertical:
        return wire(x,y,x,y+25)+wire(x-20,y+25,x+20,y+25)+wire(x-20,y+37,x+20,y+37)+wire(x,y+37,x,y+65)+text(x+28,y+38,label,23)
    return wire(x,y,x+25,y)+wire(x+25,y-20,x+25,y+20)+wire(x+37,y-20,x+37,y+20)+wire(x+37,y,x+65,y)+text(x+30,y-30,label,23,anchor='middle')


def node(x,y):return f'<circle cx="{x}" cy="{y}" r="5" fill="{INK}"/>'


def riso():
    out=[header('隔离负载前，先标清反馈从哪一端取','示意 A0=10⁵、fp=10 Hz、Ro=50 Ω、CL=100 nF；小信号模型。')]
    out += [text(45,190,'运放内部',25),wire(180,180,230,180),resistor(230,180,'Ro'),wire(325,180,420,180),node(420,180),text(420,145,'A',27,anchor='middle'),wire(420,180,500,180),resistor(500,180,'Riso'),wire(595,180,750,180),node(750,180),text(750,145,'B',27,anchor='middle'),cap(750,180,'CL',True),wire(750,245,750,275),text(750,310,'GND',23,anchor='middle')]
    out += [arrow(420,190,420,270,colour=BLUE),text(235,310,'A 回送：有补偿零点',24),arrow(800,190,900,270,colour=RED),text(670,355,'B 回送：没有该零点',24)]
    for i,(label,value,note) in enumerate([('无 Riso','PM≈10.2°','振铃，仍收敛'),('50 Ω，取 A','PM≈88.2°','运放端与负载端过冲均 <5%'),('50 Ω，取 B','PM≈7.2°','比无 Riso 更欠阻尼')]):
        y=415+i*78
        out += [text(45,y,label,26),text(350,y,value,26),text(620,y,note,24)]
    out.append(text(45,670,'只适用于该线性模型；真实电路还要验证额外极点、压摆率与负载范围。',23))
    return out


def sk():
    out=[header('Sallen-Key 的电容位置决定 Q 公式','串联 R1、R2：输入 → 中间节点 X → 运放正输入 Y；下图 K=1。')]
    out += [text(30,275,'Vin',25),wire(80,270,120,270),resistor(120,270,'R1'),wire(215,270,300,270),node(300,270),text(300,310,'X',25,anchor='middle'),wire(300,270,360,270),resistor(360,270,'R2'),wire(455,270,540,270),node(540,270),text(540,235,'Y',25,anchor='middle')]
    out += [wire(540,270,630,270),f'<path d="M630 220 L630 390 L775 305 Z" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>',text(645,280,'+',25),text(645,355,'−',25),wire(775,305,900,305),text(900,280,'Vout',25,anchor='middle'),node(840,305),wire(840,305,840,425),wire(840,425,590,425),wire(590,425,590,350),wire(590,350,630,350)]
    out += [wire(300,270,300,155),wire(300,155,500,155),cap(500,155,'C1'),wire(565,155,840,155),wire(840,155,840,305),cap(540,270,'C2',True),wire(540,335,540,380),text(535,412,'GND',23,anchor='end')]
    out += [text(45,510,'C1 从 X 接输出；C2 从 Y 接地。两只电容不可对调后仍照抄公式。',24),text(45,565,'R1=R2，C1=2C2 → Q=1/√2；等值电容只给 Q=0.5。',25),text(45,620,'10 kHz、C1=10 nF、C2=5 nF → R≈2250.79 Ω。',25),text(45,670,'改用 2.2 kΩ 时 f0≈10.23 kHz；真实运放带宽与容差须另验。',23)]
    return out


def tia():
    out=[header('TIA 三笔账：跨阻、噪声增益与闭环响应','示意 Rf=1 MΩ、Cin=10 pF、A0=10⁵、fp=100 Hz；ft≈10 MHz。')]
    rows=[('DC 跨阻','Vout≈−Iph·Rf','1 nA → −1 mV；10 MΩ 时 → −10 mV'),('噪声增益','NG=(1+sRf(Cin+Cf))/(1+sRfCf)','Cf=0：15.9 kHz 是 NG 拐点，交越约 399 kHz'),('补偿起点','Cf≈√(Cin/(2πRf·ft))≈0.399 pF','这是初估；按完整环路、寄生、过冲和噪声修订')]
    for i,(label,equation,remark) in enumerate(rows):
        y=150+i*165
        out += [box(40,y,185,115,fill=PAPER),text(132,y+64,label,26,anchor='middle'),arrow(232,y+57,280,y+57,colour=BLUE),text(300,y+40,equation,24),text(300,y+95,remark,22)]
    out.append(text(45,670,'Cin 含结电容、输入电容和布局寄生；它不是“光电二极管的等效 1 MΩ”。',23))
    return out


def sc():
    out=[header('开关电容的平均电阻仍依赖绝对电容','两相不重叠、每相充分建立；C1 反复在 V1 与 V2 之间转接。')]
    for i,(phase,source) in enumerate([('φ1：接 V1','V1'),('φ2：接 V2','V2')]):
        x=70+500*i
        out += [box(x,160,390,280,fill=PAPER),text(x+195,205,phase,28,anchor='middle'),text(x+45,290,source,25),wire(x+95,280,x+155,280),node(x+155,280),wire(x+155,280,x+245,280),cap(x+245,280,'C1',True),text(x+245,390,'参考地',23,anchor='middle')]
    out += [arrow(470,300,550,300,colour=BLUE),text(45,510,'每周期 ΔQ=C1(V1−V2)，Iavg=fclk·ΔQ，Req=1/(fclk·C1)。',26),text(45,565,'C1=1 pF、fclk=100 kHz → Req=10 MΩ；1 V 差产生 100 nA。',25),text(45,620,'与 C2 组成时间常数：τ=C2/(fclk·C1)，此时才出现电容比。',25),text(45,670,'绝对 Req 看绝对 C1；滤波时间常数看比值，两者的精度来源应分开。',23)]
    return out


def sc_errors():
    out=[header('一个采样周期要同时满足时间与误差预算','示意 12 bit 满幅一阶建立；不把特定器件时钟比写成通用规则。')]
    widths=[120,330,120,330];x=40
    for label,w in zip(['非重叠','φ1 建立','非重叠','φ2 建立'],widths):
        out += [box(x,165,w,90,fill=PAPER),text(x+w/2,218,label,23,anchor='middle')];x+=w
    rows=[('建立','1 LSB：12 ln2·τ≈8.318τ','半 LSB：13 ln2·τ≈9.011τ'),('采样','噪声均方值示意为 kT/C','输入带外谱按混叠预算滤除'),('开关','电荷注入 ΔV≈ΔQ/C','全差分与 dummy 可减误差，不能保证归零'),('两种校零','Chopper 调制与解调','Auto-zero 采样后相减，须检查噪声折叠')]
    for i,(name,left,right) in enumerate(rows):
        y=330+i*92
        out += [text(45,y,name,25),text(235,y,left,24),text(235,y+37,right,23,colour=INK2)]
    return out


def source_budget():
    out=[header('源阻只是起点，直流与噪声分别算','示意电阻型电压源 Rs=1 MΩ；参数是假设，不是 BJT/CMOS/JFET 排名。')]
    for i,(label,current,error) in enumerate([('候选 A','Ib=20 nA','|Ib·Rs|=20 mV'),('候选 B','Ib=1 pA','|Ib·Rs|=1 µV')]):
        x=45+i*480
        out += [box(x,150,430,240,fill=PAPER),text(x+215,190,label,28,anchor='middle'),text(x+215,228,current,25,anchor='middle'),arrow(x+80,246,x+350,246,colour=BLUE),text(x+42,300,'Vs',23),wire(x+75,292,x+170,292),resistor(x+170,292,''),text(x+217,329,'Rs',23,anchor='middle'),wire(x+265,292,x+350,292),node(x+350,292),text(x+365,301,'输入',22),text(x+215,366,error,27,anchor='middle')]
    out += [text(50,435,'单边白噪声：en,total²=4kTRs + en² + (in·Rs)²。',27),text(50,490,'300 K、1 MΩ 的电阻热噪声约 128.7 nV/√Hz，但不能忽略 in·Rs。',24),text(50,545,'温度变化查器件曲线，不给整个输入器件家族强加“每 10°C 翻倍”。',24),text(50,600,'光电二极管按电流源、结电容、并联电阻与暗电流模型分析。',24),text(50,655,'偏置、失调、频谱、输入范围、输出驱动与建立时间共同决定选型。',23)]
    return out


def input_types():
    out=[header('读输入级结构，最后仍要回到器件保证条件','左侧为结构示意，不按电压比例；RRIO 的输入与输出条件分别核对。')]
    rows=[('互补输入对','共模变化时两组输入对交接','交接点、gm、失调与失真由具体实现决定'),('内部电荷泵','扩展内部输入级供电范围','同时检查开关纹波、带宽和电流噪声'),('非轨到轨输入','在允许共模范围内使用','并不自动具有最好的线性或最低噪声')]
    for i,(label,mechanism,tradeoff) in enumerate(rows):
        y=155+i*160
        out += [text(170,y+20,label,25,anchor='middle'),text(350,y+35,mechanism,25),text(350,y+88,tradeoff,23)]
        if i==0:
            out += [wire(50,y+65,290,y+65),wire(50,y+99,290,y+99),box(50,y+50,150,27,fill=PAPER),box(145,y+84,145,27,fill=PAPER),text(125,y+72,'输入对一',22,anchor='middle'),text(217,y+106,'输入对二',22,anchor='middle')]
        elif i==1:
            out += [box(50,y+48,90,55,fill=PAPER),text(95,y+84,'时钟',22,anchor='middle'),arrow(150,y+75,205,y+75,colour=INK),box(215,y+48,90,55,fill=PAPER),text(260,y+84,'抬压',22,anchor='middle')]
        else:
            out += [wire(50,y+80,305,y+80),wire(50,y+69,50,y+91),wire(305,y+69,305,y+91),box(100,y+65,155,29,fill=PAPER),text(177,y+87,'允许共模',22,anchor='middle')]
    out += [text(45,660,'检查 Vos 对 Vcm、温度与频率的曲线，再用实际信号摆幅测 THD 和建立。',23)]
    return out


def feedback():
    out=[header('先定义端口与量纲，再套反馈阻抗规律','简化单环路的信号流示意：T=Aβ 无量纲；A、β 自身可能带单位。')]
    rows=[('电压串联','Av','Zin ×(1+T)','Zout ÷(1+T)'),('电压并联','跨阻 V/I','Zin ÷(1+T)','Zout ÷(1+T)'),('电流串联','跨导 I/V','Zin ×(1+T)','Zout ×(1+T)'),('电流并联','Ai','Zin ÷(1+T)','Zout ×(1+T)')]
    for i,(name,target,zin,zout) in enumerate(rows):
        y=155+i*110
        inputs=['Vin','Iin','Vin','Iin'];outputs=['Vout','Vout','Iout','Iout']
        out += [text(40,y+22,name,25),text(40,y+64,target,22),text(215,y+20,inputs[i],22),arrow(265,y+12,300,y+12,colour=INK),box(310,y-8,80,40,fill=PAPER),text(350,y+20,'A',25,anchor='middle'),arrow(400,y+12,470,y+12,colour=INK),text(480,y+20,outputs[i],22),wire(450,y+12,450,y+65),wire(450,y+65,350,y+65),arrow(350,y+65,280,y+65,colour=BLUE),wire(280,y+65,280,y+12),text(365,y+91,'反馈 β',22,anchor='middle'),text(610,y+23,zin,24),text(610,y+67,zout,24)]
        out += [f'<circle cx="280" cy="{y+12}" r="10" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>',text(254,y+48,'−',22)]
    out += [text(45,610,'示意 DC：A=1000、β=0.1 → 1+T=101；不直接预测高频稳定性。',24),text(45,660,'发射极 RE 采样的是 IE；只有 β 足够大时才近似看成 IC。',24)]
    return out


def phase():
    out=[header('先找 |Aβ|=1，再量与 −180° 的距离','单个频点的相位不是相位裕度；多交越、开环不稳定系统另做完整分析。')]
    for i,(title,mag,phase_text,result) in enumerate([('原错误检查点','A=1000，β=0.1','相位 −120°','|Aβ|=100：不是交越'),('有效交越示例','A=10，β=0.1','相位 −120°','|Aβ|=1：PM=60°'),('低裕度交越示例','A=10，β=0.1','相位 −170°','|Aβ|=1：PM=10°')]):
        y=155+i*155
        out += [box(45,y,250,115,fill=PAPER),text(170,y+60,title,24,anchor='middle'),text(325,y+30,mag,25),text(325,y+78,phase_text,25),text(625,y+78,result,25)]
    out.append(text(45,670,'60°、45° 是常见设计目标；过冲与裕度的关系取决于零极点和延迟。',23))
    return out


SCENES={}
for aid,fn,anchor,title,alt in [
    ('ch12-riso-feedback-point',riso,'12.9','隔离电阻的两个反馈位置','输出阻抗后标记 A，隔离电阻后标记 B，电容从 B 接地；三种连接分别给出相位裕度，并提醒低裕度模型仍收敛。'),
    ('ch12-sallen-key-network',sk,'12.5','Sallen-Key 的电容连接','R1、R2 串联，C1 由两电阻中点连接输出，C2 从运放正输入接地；跟随反馈接负端，列出 Butterworth 电容比。'),
    ('ch12-tia-three-way',tia,'12.10','TIA 三笔预算','分开直流跨阻、噪声增益拐点与补偿初估，不再把十五点九千赫兹当信号截止或振荡频率。'),
    ('ch12-switched-cap-equivalent',sc,'12.12','电荷搬运与平均电阻','两相把同一只电容轮流连接 V1 和 V2，每周期净搬运量由电压差决定，绝对电阻与电容比时间常数分别列式。'),
    ('ch12-switch-cap',sc_errors,'12.12','开关电容的误差与建立','完整周期分成两次建立与非重叠段，半 LSB 比一 LSB 多一个 ln2 时间常数，同时计噪声、注入与混叠。'),
    ('ch12-input-stage-source-z',source_budget,'12.13','电阻源的偏置与噪声','两候选只代表给定参数，偏置电流乘源阻后分别为二十毫伏与一微伏；噪声包含电压、电流与热噪声。'),
    ('ch12-input-types',input_types,'12.13','输入结构的条件与代价','互补输入、电荷泵与非轨到轨输入按具体器件曲线评估，避免把固定失真或温漂数字归给整个家族。'),
    ('ch12-feedback-ports',feedback,'12.7','反馈的端口与阻抗','四行比较受控量、输入混合、输出采样带来的阻抗方向，强调环路增益无量纲与模型适用条件。'),
    ('ch12-phase-crossing',phase,'12.7','相位裕度的正确检查点','原 A 一千乘零点一不是单位交越，改用 A 十倍乘零点一，再分别读取负一百二十与负一百七十度。'),
]:
    SCENES[aid]=dict(draw=fn,title=title,chapter=12,source='docs/p2-02-ch12.md',anchor=anchor,alt=alt)

for _aid,_anchor in {
    'ch12-riso-feedback-point':'12.9a','ch12-tia-three-way':'12.10a',
    'ch12-switch-cap':'12.12c','ch12-input-stage-source-z':'12.13a',
    'ch12-input-types':'12.13c','ch12-phase-crossing':'12.7a',
}.items():SCENES[_aid]['anchor']=_anchor
for _aid,_values,_reason in [
    ('ch12-tia-three-way',['15.9','399','10'],'噪声增益拐点与交越频率在同一正文模型中按三位有效数字显示；10 MΩ 仅用于 DC 跨阻比较。'),
    ('ch12-switch-cap',['12','13','8.318','9.011'],'12 bit 满幅一阶建立到一 LSB 与半 LSB 的时间常数倍数；正文 12.12b 给出推导，图以三位小数显示。'),
    ('ch12-input-stage-source-z',['20','1'],'正文 12.13 的两个输入偏置假设，图同时列示误差与 12.13a 的噪声方程，不作为家族规格。'),
]:SCENES[_aid]['numbers']=[dict(value=v,label='示意',reason=_reason) for v in _values]
