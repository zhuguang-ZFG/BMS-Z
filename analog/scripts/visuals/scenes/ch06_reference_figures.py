"""Parameter boundaries and quantitative references for chapter 6."""
import math
from scripts.visuals.scenes.handdrawn_wave2 import BLUE, GREEN, INK, INK2, PAPER, RED, RULE, box, header, text
from scripts.visuals.primitives import directed_arrow as arrow
from scripts.visuals import opamp_models as model


def four_blocks():
    out=[header('运放的三个信号级与偏置网络','以双极型两级补偿结构理解分工；现代器件的实现可能不同。')]
    rows=[('差分输入','失调、偏流、输入范围',BLUE),('中间增益与补偿','电压增益、GBW、SR',GREEN),('输出缓冲','带载、摆幅、失真',RED)]
    for i,(title,note,col) in enumerate(rows):
        y=130+i*125
        out += [box(50,y,500,98,fill=PAPER,stroke=col),text(76,y+37,title,25,colour=col,weight='700'),text(76,y+75,note,23)]
        if i<2: out.append(arrow(285,y+100,285,y+122,colour=INK))
    out += [box(610,130,340,348,fill=PAPER),text(635,176,'偏置网络',26,weight='700'),
            text(635,221,'为各级设置工作电流',22),text(635,271,'补偿示意：30 pF',22),text(635,309,'15 µA → 0.5 V/µs',23),
            text(635,358,'A0 = 200000',22),text(635,396,'GBW = 1 MHz',22),text(635,434,'单极点 fp ≈ 5 Hz',22)]
    for y in [178,303,428]: out.append(arrow(605,y,555,y,colour=INK2))
    out += [text(50,552,'CMRR 与 PSRR 受多个内部级影响，不能一项只归一个方框。',24),
            text(50,600,'尾电流不一定等于补偿电容可用电流；限流不等于不限功耗。',23)]
    return out


def stages():
    out=[header('输入允许到哪里，不等于输出能摆到哪里','TI 经典 LM358：5 V 单电源；按正文所引手册条件。')]
    x0,w=300,600
    for v in [0,1,2,3,3.5,4,5]:
        x=x0+w*v/5
        out += [f'<line x1="{x}" y1="145" x2="{x}" y2="335" stroke="{RULE}" stroke-dasharray="3 5"/>',text(x,370,f'{v:g}',22,anchor='middle')]
    out.append(text(905,405,'输入共模 / V',22,anchor='end'))
    for y,limit,label,col in [(190,3.5,'25°C 输入范围',BLUE),(295,3,'0～70°C 输入范围',GREEN)]:
        out += [text(50,y+8,label,24,colour=col),f'<line x1="{x0}" y1="{y}" x2="{x0+w*limit/5}" y2="{y}" stroke="{col}" stroke-width="9"/>',
                f'<circle cx="{x0+w*limit/5}" cy="{y}" r="7" fill="{col}"/>',text(x0+w*limit/5,y-27,f'上限 {limit:g} V',23,colour=col,anchor='end')]
    out += [box(50,440,900,132,fill=PAPER,stroke=RED),text(76,480,'输出摆幅：另按负载电流、温度和输出电压查曲线。',24),
            text(76,522,'不能把输入上限 3.5 V 当作所有负载下的输出保证。',24),
            text(76,556,'典型 GBW 0.7 MHz、SR 0.3 V/µs 也不是保证下限。',22),
            text(50,624,'单电源 ≠ 轨到轨；RRI 是输入、RRO 是输出、RRIO 是两者。',23)]
    return out


def bias_balance():
    out=[header('偏流误差：阻抗和电流方向都要算','下图电流流入输入端为正，输入信号置零。')]
    def wire(x1,y1,x2,y2):return f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{INK}" stroke-width="3"/>'
    out += [f'<path d="M530,210 L530,360 L680,285 Z" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>',
            text(545,258,'−',25),text(545,330,'+',25),wire(680,285,865,285),text(875,292,'OUT',24),
            wire(85,250,160,250),box(160,233,125,34,fill=PAPER),wire(285,250,530,250),text(150,211,'Rin 10 kΩ',24),text(50,290,'Vin=0',23),
            wire(360,250,360,145),wire(360,145,530,145),box(530,128,120,34,fill=PAPER),wire(650,145,810,145),wire(810,145,810,285),text(520,113,'Rf 90 kΩ',24),
            wire(85,325,160,325),box(160,308,125,34,fill=PAPER),wire(285,325,530,325),text(145,384,'Rb 9 kΩ',24),text(50,358,'GND',23),
            arrow(430,234,510,234,colour=RED),text(409,206,'I−',24,colour=RED),arrow(430,341,510,341,colour=BLUE),text(425,379,'I+',24,colour=BLUE)]
    out += [text(50,445,'NG = 10；Verr = Rf I− − NG Rb I+',25),
            text(50,491,'两路 20 nA：+1.8 mV 与 −1.8 mV 相抵。',24),
            text(50,537,'I+ = 22 nA、I− = 20 nA：残余 −0.18 mV。',24),
            text(50,583,'20 nA × 1 kΩ = 20 µV；× 100 kΩ = 2 mV。',23),
            text(50,630,'阻值匹配与温度跟踪影响残余；Rb 自身也贡献热噪声。',23)]
    return out


def slew_vs_gbw():
    out=[header('完整斜坡不能再加完整指数收尾','一阶限速教学模型；1 V 阶跃，fc 1 MHz，SR 0.5 V/µs。')]
    x0,y0,w,h=95,405,460,210
    for y in [0,.5,1]:
        out += [f'<line x1="{x0}" y1="{y0-h*y}" x2="555" y2="{y0-h*y}" stroke="{RULE}" stroke-dasharray="3 5"/>',text(80,y0-h*y+7,str(y),22,anchor='end')]
    for t in [0,1,2,3]:out.append(text(x0+w*t/3,443,str(t),22,anchor='middle'))
    out += [text(70,163,'输出 / V',22),text(555,480,'时间 / µs',22,anchor='end')]
    for fn,col,dash in [(lambda t:model.step_response(t*1e-6),BLUE,''),(lambda t:1-math.exp(-2*math.pi*t),INK2,'7 5')]:
        points=' '.join(f'{x0+w*t/300:.3f},{y0-h*fn(t/100):.3f}' for t in range(301))
        out.append(f'<polyline points="{points}" fill="none" stroke="{col}" stroke-width="3" stroke-dasharray="{dash}"/>')
    out += [text(610,170,'交接条件：e = SRτ',24,colour=BLUE),text(610,220,'τ = 0.159 µs',23),text(610,268,'e = 0.0796 V',23),
            text(610,316,'t = 1.841 µs',23),text(610,376,'到 0.1%：',23),text(610,418,'限速 2.537 µs',25,colour=BLUE),text(610,460,'线性 1.099 µs',23,colour=INK2),
            text(50,533,'实线限速；虚线仅线性。两段在交接处电压与斜率都连续。',24),
            text(50,582,'大信号期间反馈仍连接，不能一概称环路增益归零。',23),text(50,625,'实际建立时间还受过冲、恢复、负载与失调底限影响。',23)]
    return out


def fault_triage():
    out=[header('输入压差是证据，不是故障判决','示意算例另用 ±12 V、轻负载、同相增益 10；不是 5 V 实验。')]
    rows=[('先查条件','测供电、两个输入对地电压、输出及负载。'),
          ('再查反馈','大压差可来自开路、越界、饱和或压摆。'),
          ('修复后验证','Vin 0.8 V，修好 Rf 虚焊后应约 8.0 V。')]
    for i,(title,note) in enumerate(rows):
        y=135+i*133
        out += [box(50,y,900,106,fill=PAPER),text(76,y+38,title,26,colour=BLUE,weight='700'),text(76,y+80,note,24)]
        if i<2:out.append(arrow(500,y+108,500,y+131,colour=INK))
    out += [text(50,590,'正常压差可包含毫伏级失调；相位反转时不能继续假定虚短。',23),
            text(50,635,'共地示波器地夹接公共参考；差分测量用合适的探头或方法。',23)]
    return out


SCENES={}
for aid,fn,anchor,title,alt in [
 ('ch06-741-four-blocks',four_blocks,'6.1','运放信号通路与偏置','三个信号级的箭头依次连接输入、中间和输出。偏置网络从侧面供给电流；补偿单极点教学数值互相一致。'),
 ('ch06-opamp-conditions',stages,'6.2','运放选型的工作条件','五伏供电下，经典 LM358 输入共模范围在二十五摄氏度上限为三点五伏，零到七十摄氏度留到三伏。两条范围条共享电压轴；输出摆幅另查负载与温度条件，不能照搬输入范围。'),
 ('ch06-bias-balance',bias_balance,'6.3','偏流抵消的符号与残余','二十纳安流过一千欧为二十微伏，十万欧为二毫伏。反相输入电阻十千欧、反馈九十千欧，平衡九千欧时匹配偏流抵消；二纳安失配留下零点一八毫伏。'),
 ('ch06-slew-vs-gbw',slew_vs_gbw,'6.7','限速一阶响应的连续交接','限速实线和仅线性虚线共享时间电压轴；一伏阶跃在一点八四一微秒交接，剩余误差零点零七九六伏；千分之一建立时间约二点五三七微秒。'),
 ('ch06-fault-conditions',fault_triage,'6.6','先查边界再诊断反馈','三步流程检查供电共模负载、反馈通路和修复验证。另用正负十二伏供电，同相十倍把零点八伏放大到八伏；大压差不能唯一归因于反馈断路。')]:
    SCENES[aid]=dict(draw=fn,title=title,chapter=6,source='docs/p1-07-ch6.md',anchor=anchor,alt=alt)
