"""Timer figures: connected circuit paths, model plots and source-bound budgets."""
import math
from scripts.visuals.scenes.handdrawn_wave2 import BLUE,GREEN,INK,INK2,PAPER,RED,RULE,box,header,text
from scripts.visuals.primitives import directed_arrow as arrow
from scripts.visuals import timer_models as m


def wire(x1,y1,x2,y2,dash=''):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{INK}" stroke-width="3" stroke-dasharray="{dash}"/>'


def grid(x1,y,x2):
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{RULE}" stroke-width="1.2" stroke-dasharray="3 5"/>'


def curve(points,color=BLUE,dash=''):
    return '<polyline points="'+' '.join(f'{x:g},{y:g}' for x,y in points)+f'" fill="none" stroke="{color}" stroke-width="3" stroke-dasharray="{dash}"/>'


def thresholds():
    out=[header('两只比较器决定动作，锁存器保留中间状态','8 脚供电、1 脚接地；RESET 优先于 TRIG，TRIG 优先于 THRES。')]
    out += [text(110,150,'VCC',24,anchor='middle'),wire(110,160,110,180)]
    for y in [180,300,420]:out += [box(98,y,24,55,fill=PAPER),wire(110,y+55,110,y+120)]
    out += [wire(80,540,140,540),text(45,645,'三只等值电阻',24)]
    for y,label,polarity,other in [(260,'2/3 VCC','−','+ THRES ⑥'),(380,'1/3 VCC','+','− TRIG ②')]:
        out += [wire(110,y,350,y),text(160,y-18,label,23),box(350,y-35,210,90,fill=PAPER),text(370,y+6,polarity,27),wire(300,y+30,350,y+30),text(370,y+35,other,23),arrow(565,y+5,650,y+5,colour=INK)]
    out += [box(650,200,125,265,fill=PAPER),text(712,310,'锁存',27,anchor='middle'),text(665,270,'R',24),text(665,390,'S',24),arrow(775,270,910,270,colour=BLUE),text(840,235,'OUT ③',24),arrow(775,400,910,400,colour=RED),text(840,445,'DISCH ⑦',24),text(650,155,'RESET ④',24),arrow(712,165,712,195,colour=INK),text(200,495,'CONT ⑤ 接上抽头，可改变门限；不等于引脚被钳位。',23),text(200,545,'OUT 低 → 放电开关导通；OUT 高 → 放电开关截止。',23),text(200,595,'各输入仍须满足手册电压范围，不能越过 VCC 使用。',23)]
    return out


def modes():
    out=[header('先看谁发起事件，再看 2、6、7 脚怎么接','所有模式都要处理 RESET、CONT、供电去耦和输入电压范围。')]
    rows=[('无稳态','②⑥ → 定时 C；⑦ → RA/RB 中点','周期由充放两段相加',[(0,1),(.3,1),(.3,0),(.5,0),(.5,1),(.8,1),(.8,0),(1,0)]),('单稳态','② → 触发；⑥⑦ → 定时 C','RC 定时；不自动从最新触发重计',[(0,0),(.15,0),(.15,1),(.75,1),(.75,0),(1,0)]),('双稳态','② → 置位；⑥ → 复位；⑦ 可闲置','无定时 C，状态由输入命令保持',[(0,0),(.25,0),(.25,1),(.85,1),(.85,0),(1,0)])]
    for i,(name,pins,note,pts) in enumerate(rows):
        y=145+i*170
        out += [text(50,y+30,name,28),text(220,y+25,pins,24),text(220,y+70,note,23),curve([(700+x*240,y+105-v*50) for x,v in pts]),text(705,y+140,'OUT：时间 →',22)]
    return out


def fault_tree():
    out=[header('同一输出症状，要用输入与定时节点排除原因','先确认供电与 RESET，再同步抓 TRIG、THRES、DISCH、OUT。')]
    rows=[('OUT 常高','TRIG 是否持续低？','释放触发后再查 THRES 与 ⑦'),('OUT 常低','RESET 是否有效？','再查触发幅度、宽度和接线'),('周期漂移','C 实值、漏电、CONT 是否变化？','逐项改变温度或负载，保留记录'),('启动异常','电源与 RESET 的先后关系？','测快慢上电、掉电和残留电荷')]
    for i,(symptom,question,next_step) in enumerate(rows):
        y=135+i*128
        out += [box(40,y,185,94,fill=PAPER),text(132,y+56,symptom,25,anchor='middle'),arrow(230,y+46,280,y+46,colour=BLUE),text(300,y+34,question,24),text(300,y+76,next_step,23,colour=INK2)]
    out.append(text(50,665,'CONT 的 2/3 VCC 是标称值；偏离不直接证明芯片或外部电路损坏。',23))
    return out


def reverse_design():
    out=[header('38 kHz 先反算，再按实际元件回算','示意标称门限、零放电压降；C=1 nF，RA=1 kΩ。')]
    out += [text(50,165,'RA + 2RB = 1 / (ln2 × 38 kHz × 1 nF) ≈ 37.966 kΩ',25),text(50,222,'因此 RB ≈ 18.483 kΩ。下图画实际 RB 对频率的影响。',25)]
    px=lambda r:120+(r-17)*700/3;py=lambda f:470-(f-32)*200/10
    for f in [34,38,42]:out += [grid(120,py(f),820),text(105,py(f)+8,str(f),23,anchor='end')]
    out.append(curve([(px(r),py(1/(math.log(2)*(1000+2*r*1000)*1e-9)/1000)) for r in [17+i/100 for i in range(301)]]))
    for r in [17,18.4,20]:out.append(text(px(r),510,f'{r:g}',23,anchor='middle'))
    out += [text(50,249,'频率 / kHz',23),text(870,550,'RB / kΩ',23,anchor='end'),text(50,600,'18 kΩ → 38.992 kHz；18.4 kΩ → 38.167 kHz。',25),text(50,646,'接收器的允许频偏、突发长度和占空比，按具体协议与手册验收。',23)]
    return out


def duty_paths():
    out=[header('接近 50% 的三条路，都有各自前提','示意门限为 VCC/3 与 2VCC/3；占空比指输出高电平比例。')]
    rows=[('二极管绕过 RB','VF=0 且 RA=RB → 50%','5 V、VF=0.6 V、等阻值 → 57.58%'),('输出单电阻反馈','VOH=VCC、VOL=0 → 对称','受载电平偏离电源后，分别算两段'),('稳定时钟二分频','D 接反相 Q，每个有效沿翻转','连续等周期输入给近 50%；仍计抖动与延迟')]
    for i,(name,ideal,real) in enumerate(rows):
        y=150+i*155
        out += [box(45,y,260,115,fill=PAPER),text(175,y+62,name,25,anchor='middle'),arrow(310,y+57,360,y+57,colour=INK),text(380,y+35,ideal,25),text(380,y+85,real,23,colour=INK2)]
    out += [text(50,655,'单端 0–VCC 方波即使 50%，平均电压也不为零，不能直接当 LCD 交流驱动。',22)]
    return out


def mono_budget():
    lo,hi=m.tolerance_corners()
    out=[header('把 R、C 与门限分别取极限，再相乘','示意 R±1%、C±5%、上阈比例 α=0.65–0.68；不是 NE555 保证窗口。')]
    out += [text(50,165,'t = −RC ln(1−α)，标称 α=2/3 时 t = RC ln3。',27)]
    for i,(label,value) in enumerate([('最短',lo),('标称',1),('最长',hi)]):
        y=220+i*105
        out += [text(50,y+34,label,26),box(180,y,value*600,55,fill=PAPER),text(200+value*600,y+37,f'{value*100:.2f}%',26)]
    out += [text(50,580,'本例相对窗口约 −10.13% / +9.99%，不是只把百分点机械相加。',24),text(50,630,'两段延时都 ±8%，相加后的总延时仍为 ±8%；绝对误差先相加。',24)]
    return out


def recovery_gap():
    out=[header('恢复残压必须带进下一次充电的初值','示意 5 V、100 kΩ、10 µF，放电等效 100 Ω；供电电阻一直存在。')]
    px=lambda t:120+t/6*760;py=lambda v:425-v/3.5*240
    for v in [0,1,2,3]:out += [grid(120,py(v),880),text(105,py(v)+7,str(v),23,anchor='end')]
    out.append(curve([(px(t),py(m.recovery(t/1000)[0])) for t in [i/100 for i in range(601)]]))
    for t in [0,1,5,6]:out.append(text(px(t),470,str(t),23,anchor='middle'))
    out += [text(50,145,'残压 / V',23),text(885,510,'恢复间隔 / ms',23,anchor='end'),text(50,555,'1 ms：残压 1.228 V → 下一拍约 0.817 s。',25),text(50,600,'5 ms：残压 27.3 mV → 下一拍约 1.093 s。',25),text(50,645,'零初值理想脉宽 1.099 s；实物由放电曲线与容差决定所需间隔。',23)]
    return out


def discharge_current():
    out=[header('7 脚导通时，同时接收电源与电容的电流','示意 9 V、RA=1 kΩ、RB=6.8 kΩ、VC=6 V、VD=0.15 V。')]
    out += [text(150,170,'VCC = 9 V',25),wire(180,190,180,245),box(167,245,26,70,fill=PAPER),text(220,290,'RA',25),wire(180,315,180,420),wire(180,360,410,360),box(410,347,95,26,fill=PAPER),wire(505,360,760,360),text(445,325,'RB',25),wire(760,360,760,430),wire(725,430,795,430),wire(725,445,795,445),wire(760,445,760,500),text(800,445,'C',25),text(710,310,'VC = 6 V',24),box(140,420,80,65,fill=PAPER),text(180,460,'⑦',27,anchor='middle'),wire(180,485,180,500),wire(150,500,790,500)]
    out += [arrow(100,250,100,350,colour=BLUE),text(50,225,'8.85 mA',23),arrow(650,400,530,400,colour=RED),text(540,440,'0.860 mA',23),text(50,575,'总放电管电流约 9.710 mA；不能只算电容支路。',26),text(50,630,'减小 RA 会增加导通期间的电源直通电流，先查压降与功耗。',24)]
    return out


def logic_margin():
    out=[header('输出能带电流，不等于逻辑高电平有保证','TI NE555 SLFS022K §5.5：5 V、25°C、源出 100 mA 时。')]
    out += [text(50,160,'手册 VOH 最低 2.75 V、典型 3.3 V；不固定等于 VCC−1.4 V。',24)]
    for y,v,label in [(230,2.75,'最低 VOH'),(335,3.3,'典型 VOH'),(440,3.5,'示意后级 VIH')]:
        out += [text(45,y+36,label,25),box(240,y,v*170,58,fill=PAPER),text(260+v*170,y+39,f'{v:g} V',26)]
    out += [text(50,580,'相对 3.5 V 门限，保证裕量为 −0.75 V，不能通过此工作点。',25),text(50,635,'轻载、温区、缓冲方案需重新核对；不由典型值外推全部电流。',24)]
    return out


def leakage():
    out=[header('越接近上门限，可用充电电流越小','示意 9 V、R=560 kΩ；上阈 6 V。漏电会占用这条电流预算。')]
    px=lambda v:120+v/6*760;py=lambda i:440-i/18*250
    for i in [0,5,10,15]:out += [grid(120,py(i),880),text(105,py(i)+7,str(i),23,anchor='end')]
    out.append(curve([(px(v),py((9-v)/560000*1e6)) for v in [i/10 for i in range(61)]]))
    out.append(curve([(px(0),py(1)),(px(6),py(1))],INK2,'6 5'))
    for v in [0,3,6]:out.append(text(px(v),485,str(v),23,anchor='middle'))
    out += [text(45,150,'电流 / µA',23),text(885,530,'电容电压 / V',23,anchor='end'),text(50,575,'到 6 V 时只剩 5.357 µA；图中虚线为 1 µA 恒流漏电。',25),text(50,630,'到达门限要求充电仍为正；计时精度通常先于无法触发而超限。',24)]
    return out


def clock_gating():
    out=[header('异步 RESET 可以截短正在输出的高脉冲','示意关闭命令落在高态中间；边沿计数系统仍需无毛刺门控。')]
    px=lambda t:200+t*700
    tracks=[(210,'自由 OUT',[(0,1),(.3,1),(.3,0),(.5,0),(.5,1),(.8,1),(.8,0),(1,0)]),(350,'RESET',[(0,1),(.15,1),(.15,0),(1,0)]),(490,'实际 OUT',[(0,1),(.15,1),(.15,0),(1,0)])]
    for y,label,pts in tracks:
        out += [text(45,y-20,label,25),curve([(px(t),y-v*65) for t,v in pts]),text(930,y,'0',22),text(930,y-60,'1',22)]
    out += [wire(px(.15),130,px(.15),520,'5 5'),text(50,575,'关闭时刻 → 高脉冲被截断；用 RESET 并不自动获得完整时钟。',24),text(50,630,'二分频只在连续有效时钟沿下成立；暂停、重启和输入抖动另验。',24)]
    return out


SCENES={}
for aid,fn,anchor,title,alt in [
 ('ch10-555-threshold-clamp',thresholds,'10.1','555 内部状态路径','三只等值电阻形成两门限，阈值比较器和触发比较器进入锁存器，RESET 具有最高优先级，OUT 与放电开关状态对应。'),
 ('ch10-555-modes',modes,'10.2','三种模式的连接与输出','无稳态将触发与阈值并到定时电容，单稳态另接触发，双稳态分别接受置位复位；各自连接和输出波形并列。'),
 ('ch10-555-fault-tree',fault_tree,'10.3','555 的测量排故入口','输出常高先查触发，常低先查复位；漂移测实际电容漏电与控制节点，启动测供电和复位时序。'),
 ('ch10-astable-reverse-design',reverse_design,'10.4','载波频率反算与回算','三十八千赫和一纳法反求电阻和约三十七点九六六千欧，再用实际阻值重新核算频率与协议窗口。'),
 ('ch10-duty-fifty-paths',duty_paths,'10.4','对称占空比的条件','二极管路径计入压降，输出反馈计入受载电平，数字分频计入连续有效时钟；单端方波平均电压不为零。'),
 ('ch10-monostable-budget',mono_budget,'10.5','单稳态精度的角点预算','示意电阻电容和门限范围取角点相乘，最短约标称八十九点八七百分比，最长约一百零九点九九百分比。'),
 ('ch10-recovery-gap',recovery_gap,'10.5','恢复残压与第二拍','放电等效电阻模型中保留电源馈入，一毫秒后残压一点二二八伏，五毫秒后二十七点三毫伏，下一拍各自重新计算。'),
 ('ch10-discharge-current',discharge_current,'10.1','放电脚两条电流支路','电源经 RA 与电容经 RB 的电流一起进入七脚，示意八点八五与零点八六毫安相加，不能漏算电源电流。'),
 ('ch10-logic-margin',logic_margin,'10.3','受载输出与逻辑门限','特定五伏和一百毫安条件下，NE555 最低高电平二点七五伏，对示意三点五伏输入门限没有保证裕量。'),
 ('ch10-timer-leakage',leakage,'10.5','定时末段的充电电流预算','电容电压越高，电阻充电电流越小；到上门限只剩五点三五七微安，漏电预算必须在此端点检查。'),
 ('ch10-clock-gating',clock_gating,'10.4','异步门控的短脉冲','关闭命令在高脉冲中段到达时，RESET 会把输出提前截断；关闭和重启都须按时钟接收器要求验收。')]:
    SCENES[aid]=dict(draw=fn,title=title,chapter=10,source='docs/p1-11-ch10.md',anchor=anchor,alt=alt)

for aid,values,reason in [
 ('ch10-monostable-budget',['89.87','100.00','109.99'],'明确示意 R/C/门限角点计算的百分比，按图内标称归一化并取两位小数。'),
 ('ch10-astable-reverse-design',['17','34','42'],'反算电阻曲线的坐标刻度，单位分别为千欧与千赫，不是接收器规格。'),
]:
    SCENES[aid]['numbers']=[dict(value=v,label='示意',reason=reason) for v in values]
