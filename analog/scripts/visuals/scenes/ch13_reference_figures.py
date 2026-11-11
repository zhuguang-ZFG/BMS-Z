"""Wiring, polarity and bounded budgets for chapter 13."""
from scripts.visuals.scenes.handdrawn_wave2 import BLUE, INK, INK2, PAPER, RED, box, header, text
from scripts.visuals.primitives import directed_arrow as arrow


def wire(x,y,u,v):return f'<path d="M{x} {y} L{u} {v}" fill="none" stroke="{INK}" stroke-width="3"/>'
def node(x,y):return f'<circle cx="{x}" cy="{y}" r="5" fill="{INK}"/>'
def part(x,y,w,label):return box(x,y,w,50)+text(x+w/2,y+33,label,23,anchor='middle')


def buck():
    out=[header('Buck：电流连续，斜率由两种电压决定','示意理想 CCM：12→5 V、22 µH、150 kHz、100 µF、负载 1 A。')]
    out += [text(35,180,'12 V',24),wire(100,172,150,172),part(150,147,140,'开关'),wire(290,172,380,172),node(380,172),text(380,135,'SW',24,anchor='middle'),wire(380,172,450,172),part(450,147,140,'电感'),wire(590,172,760,172),node(760,172),text(835,180,'5 V',24)]
    out += [wire(380,172,380,240),part(300,240,160,'二极管 K↑A↓'),wire(380,290,380,340),wire(760,172,760,240),part(680,240,160,'C 与负载并联'),wire(760,290,760,340),wire(380,340,760,340),text(580,375,'GND',24,anchor='middle')]
    out += [arrow(150,210,290,210,colour=BLUE),arrow(610,210,730,210,colour=BLUE),arrow(270,320,270,210,colour=RED)]
    rows=[('导通 2.778 µs','vL=+7 V','电流上升'),('关断 3.889 µs','vL=−5 V','二极管接管'),('ΔIL≈0.88384 A','谷值 0.5581 A','峰值 1.4419 A')]
    for i,row in enumerate(rows):
        for x,value in zip([45,370,680],row):out.append(text(x,440+65*i,value,25))
    out += [text(45,660,'箭头为常规电流方向；开关尖峰、寄生、器件额定与温升另算。',23)]
    return out


def compliance():
    out=[header('恒流预算：供电先扣采样与调整管压差','示意 1 mA、Rs=100 Ω、调整管预留 0.7 V；图宽不编码电压大小。')]
    for i,(vs,rl) in enumerate([('2.8 V','2.0 kΩ'),('5 V','4.2 kΩ'),('12 V','11.2 kΩ')]):
        y=155+i*130
        out += [part(45,y,150,vs),arrow(205,y+25,255,y+25,colour=BLUE),part(265,y,270,'减去 0.1 V 与 0.7 V'),arrow(545,y+25,595,y+25,colour=BLUE),part(605,y,335,'负载上限 '+rl)]
    out += [text(45,590,'还要检查输入共模、输出驱动、调整管安全工作区及散热。',25),text(45,650,'0.7 V 是这笔预算指定的余量，不是所有调整管的最小压差。',23)]
    return out


def sampling():
    out=[header('采样与量化：两道不同的限制','示意 12 bit、3.3 V 满量程：台阶 q≈0.8057 mV；DC 可以稳定输出单一码。')]
    out += [part(45,155,235,'带限模拟输入'),arrow(290,180,340,180,colour=BLUE),part(350,155,235,'采样与保持'),arrow(595,180,645,180,colour=BLUE),part(655,155,285,'量化与输出码')]
    for x,title,lines in [(55,'时间轴',['fs 需要高于带限最高频率的两倍','实际滤波器必须留过渡带','带外折叠后不能靠数字滤波找回']), (535,'幅度轴',['q=满量程 / 2^N','阈值、噪声和输入共同决定抖码','分辨率不等于 ENOB 或直流准确度'])]:
        out += [box(x,275,410,290),text(x+205,320,title,28,anchor='middle')]
        for j,value in enumerate(lines):out.append(text(x+20,385+j*65,value,22))
    out += [text(45,635,'SAR、Σ-Δ、Flash 的速率与位数有重叠，最终比较具体器件的误差与时序。',23)]
    return out


def bridge():
    out=[header('H 桥：先定义开关，再分开滑行与制动','Q1 左上、Q2 左下、Q3 右上、Q4 右下；电机电流不能瞬间反向。')]
    out += [wire(180,150,790,150),text(480,135,'母线正端',24,anchor='middle'),wire(180,150,180,190),part(130,190,100,'Q1'),wire(180,240,180,310),node(180,310),wire(790,150,790,190),part(740,190,100,'Q3'),wire(790,240,790,310),node(790,310),wire(180,310,410,310),part(410,285,150,'电机'),wire(560,310,790,310),wire(180,310,180,380),part(130,380,100,'Q2'),wire(790,310,790,380),part(740,380,100,'Q4'),wire(180,430,180,470),wire(790,430,790,470),wire(180,470,790,470),text(480,505,'母线负端',24,anchor='middle')]
    out += [arrow(290,265,650,265,colour=BLUE),text(470,240,'Q1+Q4：左端电压较高',23,anchor='middle'),arrow(650,355,290,355,colour=RED),text(470,400,'Q2+Q3：右端电压较高',23,anchor='middle')]
    out += [text(45,555,'同臂同开：直通。全关：先续流，可能回灌，再随电流与反电势变化。',23),text(45,605,'两低侧导通：短路制动。受控回灌：再生，先确认母线能吸收能量。',23),text(45,655,'死区按实际延迟、关断与米勒条件设计；图省略续流器件，不能用于直接接线。',23)]
    return out


def sides():
    out=[header('分流位置：沿真实电流路径判断能否测到','高侧与低侧都只看流经自身分流的电流；不能按“对地短路”四字一概判断。')]
    for x,high in [(60,False),(550,True)]:
        out += [text(x+190,160,'高侧分流' if high else '低侧分流',28,anchor='middle'),text(x+190,205,'电源',24,anchor='middle')]
        for j,label in enumerate(['分流 Rs','负载'] if high else ['负载','分流 Rs']):
            y=240+j*145
            out += [wire(x+190,y-25,x+190,y),part(x+80,y,220,label),wire(x+190,y+50,x+190,y+120)]
        out += [text(x+190,555,'系统地',24,anchor='middle')]
        if high:out += [text(x,610,'保留负载地，放大器需承受高共模。',23)]
        else:out += [text(x,610,'负载地抬高 IRs，检查接口地预算。',23)]
    out.append(text(45,665,'低侧还须查近地输入范围与负瞬态；高侧还须查共模边沿与恢复时间。',23))
    return out


def sense():
    out=[header('同一分流，额定与堵转的热耗差十六倍','示意 10 mΩ，额定 5 A、堵转 20 A；时间、PCB 散热与降额决定可承受程度。')]
    for x,title,current,voltage,power in [(45,'额定','5 A','50 mV','0.25 W'),(535,'堵转','20 A','200 mV','4 W')]:
        out += [box(x,160,420,330),text(x+210,210,title,30,anchor='middle'),text(x+210,280,current,34,anchor='middle'),arrow(x+210,300,x+210,350,colour=BLUE),text(x+210,400,voltage+' / '+power,30,anchor='middle')]
    out += [text(45,550,'V=IR，P=I²R；不能只凭 1 W 或 2512 封装判定能承受堵转。',25),text(45,605,'Kelvin 示例：多取进 50 µΩ / 10 mΩ = 0.5% 误差。',25),text(45,660,'双输入各 100 Ω，跨输入 100 nF：差模极点约 7.96 kHz。',24)]
    return out


def audio():
    out=[header('功放热账：先从负载功率反推摆幅','示意 8 Ω、10 W 正弦；效率假设必须标明，不能直接由类别保证。')]
    out += [part(45,155,235,'Vrms=8.944 V'),arrow(290,180,340,180,colour=BLUE),part(350,155,235,'Vpk=12.649 V'),arrow(595,180,645,180,colour=BLUE),part(655,155,285,'检查电源与输出压差')]
    for x,eta,pin,heat in [(45,'假定效率 60%','输入 16.667 W','热耗 6.667 W'),(535,'假定效率 90%','输入 11.111 W','热耗 1.111 W')]:
        out += [box(x,280,420,250),text(x+210,330,eta,28,anchor='middle'),text(x+210,410,pin,28,anchor='middle'),text(x+210,480,heat,28,anchor='middle')]
    out += [text(45,590,'Irms=1.118 A；热阻、静态损耗、削顶和 EMI 仍需按具体器件验证。',24),text(45,650,'±15 V 仅为电源示例；理想 B 类的摆幅相关效率另由下一图计算。',23)]
    return out


def crystal():
    out=[header('晶体外部负载电容与动态电容分开命名','外部 Ca、Cb；晶体动态支路 Rm、Lm、Cm，静态电容 C0。')]
    out += [wire(160,200,390,200),part(390,175,200,'反相放大器'),wire(590,200,830,200),wire(160,200,160,300),wire(830,200,830,300),wire(160,300,390,300),part(390,275,200,'晶体'),wire(590,300,830,300),wire(160,200,160,130),wire(160,130,390,130),part(390,105,200,'反馈电阻 Rf'),wire(590,130,830,130),wire(830,130,830,200)]
    for x,label in [(160,'Ca'),(830,'Cb')]:
        out += [wire(x,300,x,365),wire(x-30,365,x+30,365),wire(x-30,380,x+30,380),wire(x,380,x,420),text(x+42,385,label,24),text(x,455,'地',24,anchor='middle')]
    out += [text(45,515,'CL=Ca·Cb/(Ca+Cb)+Cstray',30),text(45,570,'两只 22 pF，加等效寄生 4 pF → CL=15 pF。',27),text(45,625,'这是指定负载，不能自动匹配所有 12–18 pF 规格。',24),text(45,670,'反馈与可选限流电阻按芯片推荐；量引脚时把探头加载算进去。',23)]
    return out


def negative_resistance():
    out=[header('起振与驱动：两道不同的验收门槛','示意简化 Pierce 模型；跨导按指定参数计算，不拿 MCU 典型值保证裕量。')]
    out += [text(45,155,'gm,crit=4·ESR·(2πf0)²·(C0+CL)²',30)]
    for i,(f,r,c,g) in enumerate([('32.768 kHz','50 kΩ','1.5 / 12.5 pF','1.662 µS'),('4 MHz','200 Ω','3 / 15 pF','0.164 mS'),('8 MHz','80 Ω','3 / 15 pF','0.262 mS'),('16 MHz','50 Ω','3 / 15 pF','0.655 mS'),('25 MHz','40 Ω','3 / 15 pF','1.279 mS')]):
        for x,v in zip([45,285,485,775],[f,r,c,g]):out.append(text(x,260+i*60,v,24))
    for x,v in zip([45,285,485,775],['频率','ESR','C0 / CL','临界跨导']):out.append(text(x,210,v,23))
    out += [text(45,590,'负阻用 |Rneg| 比损耗；五倍裕量是部分厂商建议，按实际说明验收。',23),text(45,645,'驱动功率 DL=ESR·Im,rms²；用动态支路电流，串阻会同时影响起振。',23)]
    return out


def opto():
    out=[header('隔离屏障：电流传输比与绝缘指标各算各的','示意光晶体管；输入侧地与输出侧地独立，光箭头不表示导电连接。')]
    out += [part(50,170,230,'输入电阻与 LED'),arrow(290,195,420,195,colour=BLUE),wire(480,130,480,440),text(480,480,'隔离屏障',25,anchor='middle'),arrow(540,195,670,195,colour=BLUE),part(680,170,260,'光晶体管与上拉')]
    out += [text(160,295,'输入电流 IF',25,anchor='middle'),text(810,295,'输出电流 IC',25,anchor='middle'),text(160,360,'原边地',25,anchor='middle'),text(810,360,'隔离侧地',25,anchor='middle')]
    out += [text(45,540,'CTR=(IC/IF)×100%；计算电流时用比例 κ，50% 对应 0.5。',25),text(45,595,'有源区 CTR 不直接保证低 VOL；还须核饱和、温度、驱动与寿命。',24),text(45,650,'耐压、工作电压、CMTI、爬电、间隙及绝缘寿命分别检查。',24)]
    return out


SCENES={}
for aid,fn,anchor,title,alt in [
    ('ch13-buck-ripple',buck,'13.2c','Buck 的连接与电流预算','导通与续流共享电感，列出同一算例的峰谷电流，说明理想模型之外还须核寄生与热耗。'),
    ('ch13-compliance-ceiling',compliance,'13.5','恒流源的电压余量','三种供电扣除采样和指定调整管余量后得到不同的最大负载，不把余量当器件通用压差。'),
    ('ch13-sampling-quantization',sampling,'13.6','采样与量化分别预算','流程把时间采样和幅度量化分开，指出恒定输入可以输出固定码，位数不保证直流或动态精度。'),
    ('ch13-h-bridge-states',bridge,'13.7','H 桥的电压极性与制动状态','明确四开关的位置，对角决定电压极性，同臂禁止直通，并区分全关、短接和受控回灌。'),
    ('ch13-current-sense-sides',sides,'13.8','沿分流路径判断故障可见性','低侧和高侧各画电源、分流与负载，说明地抬升与共模范围，故障是否可见取决于流经路径。'),
    ('ch13-current-sense-budget',sense,'13.8a','分流功耗与 Kelvin 误差','额定与堵转电流四倍、热耗十六倍，封装额定不能替代瞬态热预算，并核差分滤波的两只串阻。'),
    ('ch13-audio-class-heat',audio,'13.9','功放摆幅与效率假设','先算负载电压电流，再在两种明确假定效率下比较热耗，不保证同音质或封装大小。'),
    ('ch13-crystal-load-cap',crystal,'13.10','Pierce 连接与负载电容','外部 Ca、Cb 与动态 Cm 分开命名，两只二十二皮法及四皮法寄生合成十五皮法，须匹配指定晶体。'),
    ('ch13-crystal-neg-resistance',negative_resistance,'13.10c','起振跨导与驱动功率','五组指定模型参数分别算跨导，负阻取绝对值，驱动功率使用动态支路电流。'),
    ('ch13-opto-ctr',opto,'13.11','光耦电流与隔离屏障','光箭头跨屏障而地不连通；CTR 百分数与计算比例分开，并区分饱和保证和绝缘指标。'),
]:SCENES[aid]=dict(draw=fn,title=title,chapter=13,source='docs/p2-03-ch13.md',anchor=anchor,alt=alt)

SCENES['ch13-compliance-ceiling']['anchor']='13.5.1'
SCENES['ch13-compliance-ceiling']['numbers']=[dict(value='0.1',label='示意',reason='1 mA 乘 100 Ω 的采样压降；该节指定预算的算术结果。')]
SCENES['ch13-opto-ctr']['anchor']='13.11a'
SCENES['ch13-buck-ripple']['numbers']=[dict(value=v,label='示意',reason='沿用正文 13.2 同一理想 CCM 算例：由 12→5 V、22 µH、150 kHz 与 1 A 计算，13.2c 指定继续使用该组条件。') for v in ['0.5581','0.88384','2.778','3.889','7']]
