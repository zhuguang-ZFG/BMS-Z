"""Chapter 9 print diagrams derived from explicit reference/regulator models."""
import math
from scripts.visuals.scenes.handdrawn_wave2 import BLUE,GREEN,INK,INK2,PAPER,RED,RULE,box,header,text
from scripts.visuals.primitives import directed_arrow as arrow
from scripts.visuals import regulator_models as m
from scripts.visuals.regulator_scenes import bias_circuit


def wire(x1,y1,x2,y2,dash=''):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{INK}" stroke-width="3" stroke-dasharray="{dash}"/>'


def reference_budget():
    out=[header('基准选型先分误差，不能只按 ADC 位数排档','示意：3.3 V、12 位；基准误差分配 0.2 mV，系统其余项另计。')]
    for y,value,label in [(170,3.3/4096*1000,'1 LSB'),(265,.2,'基准分配')]:
        out += [text(45,y+34,label,26),box(205,y,value*800,52,fill=PAPER,stroke=BLUE),text(220+value*800,y+36,('0.2' if value==.2 else f'{value:.3f}')+' mV',24)]
    out += [text(50,385,'0.2 mV / 3.3 V ≈ 60.6 ppm，不能在多项里重复花。',25)]
    for i,label in enumerate(['初始误差','温区漂移','带内噪声','长期漂移']):
        x=50+i*235
        out += [box(x,435,210,90,fill=PAPER),text(x+105,488,label,25,anchor='middle')]
    out += [text(50,580,'能否校准、是否比例式测量，都会改变各项分配。',25),text(50,630,'串联 / 分流是结构分类；带隙 / 齐纳是参考机制。',24)]
    return out


def shunt_corners():
    out=[header('分流电流怎么分，先画两条支路','示意恒压 5.1 V、R=360 Ω；输入 10.8–13.2 V，负载 0–10 mA。')]
    out += [text(300,160,'VIN',25,anchor='middle'),wire(300,170,300,195),box(286,195,28,60,fill=PAPER),text(345,234,'360 Ω',24),wire(300,255,300,390),wire(300,300,590,300),text(605,308,'5.1 V',25),wire(590,300,590,390),box(576,390,28,65,fill=PAPER),text(635,430,'负载',25),wire(590,455,590,490),wire(300,440,300,490),wire(270,490,620,490)]
    out += [f'<path d="M280,420 L300,390 L320,420 Z M278,382 V390 H322 V398" fill="none" stroke="{INK}" stroke-width="3"/>',wire(300,420,300,440),text(180,423,'分流器',24,anchor='middle'),arrow(370,330,370,390,colour=BLUE),text(400,370,'IZ',25),arrow(660,330,660,390,colour=RED)]
    out += [text(50,555,'最低输入 + 满载：IZ ≈ 5.83 mA。',25),text(50,600,'最高输入 + 空载：IZ = 22.5 mA，分流约 115 mW。',25),text(50,645,'电阻约 182 mW；实物须重算电压曲线、容差与降额。',24)]
    return out


def tl431_bias():
    out=[header('TL431 的参考偏流，要加在输出电压上','示意 Vref=2.5 V、Iref=2 µA；R1=R2，其他误差另计。')]
    out += ['<g transform="translate(10 130) scale(1.5)">'+bias_circuit(True)+'</g>',text(495,225,'上支路 = 下支路 + Iref',26,colour=BLUE),text(495,290,'10 kΩ：250 + 2 = 252 µA',24),text(495,345,'Vout = 5.020 V',28,colour=GREEN),text(495,415,'100 kΩ：Vout = 5.200 V',25,colour=RED),text(50,585,'Vout = Vref(1 + R1/R2) + Iref·R1',27),text(50,635,'实际典型 Vref 为 2.495 V；保证预算另查型号、温度与最大值。',23)]
    return out


def esr_window():
    out=[header('ESR 窗口必须写出器件和电容条件','TI LM1117，SNOS412Q §9.2.2.1.3；不是所有 1117 的共同保证。')]
    px=lambda r:80+840*(math.log10(r)+3)/5
    out += [text(50,170,'最低 10 µF 钽电容；可调版加 CADJ 时改用 22 µF。',25),box(px(.3),260,px(22)-px(.3),95,fill=PAPER,stroke=GREEN),text((px(.3)+px(22))/2,318,'该手册的 ESR 区间',26,anchor='middle'),wire(80,400,920,400)]
    for r,label in [(.005,'5 mΩ'),(.3,'0.3 Ω'),(22,'22 Ω')]:
        out += [wire(px(r),390,px(r),412),text(px(r),451,label,25,anchor='middle')]
    out += [text(920,493,'ESR（对数轴）',24,anchor='end'),text(50,548,'5 mΩ 不满足本表条件；不能继续引用这份稳定保证。',25),text(50,595,'fz = 1/(2π·ESR·C)：10 µF、0.3 Ω 时约 53.1 kHz。',24),text(50,640,'换型号、容量、偏压、温度或并联组合后，重新核对环路。',24)]
    return out


def thermal_path():
    out=[header('结温由功耗与实际散热路径共同决定','示意 12→5 V、300 mA、IQ=5 mA；环境 45°C。')]
    out += [text(50,165,'2.10 W 调整损耗 + 0.06 W 地脚损耗 = 2.16 W',27,colour=BLUE)]
    for i,(name,val) in enumerate([('结到壳','5°C/W'),('界面','1°C/W'),('散热片到环境','15°C/W')]):
        x=50+i*315
        out += [box(x,245,265,150,fill=PAPER),text(x+132,292,name,24,anchor='middle'),text(x+132,350,val,29,anchor='middle')]
        if i<2:out.append(arrow(x+268,320,x+310,320,colour=INK))
    out += [text(50,465,'总热阻约 21°C/W → 温升 45.36°C → 结温 90.36°C',26),text(50,525,'若路径为 50°C/W，同一工况结温约 153°C。',26,colour=RED),text(50,587,'125°C 是本例设计上限，不是统一的热关断温度。',24),text(50,635,'手册 θJA 依测试板与环境；安装接触和实际回流热路径要落实。',23)]
    return out


def four_accounts():
    out=[header('同样输出异常，先区分是哪条约束被破坏','按测量推进：谷值 → 温度 → 稳定性 → 启动，修后覆盖完整工况。')]
    rows=[('输入谷值','VIN,min 是否覆盖 VOUT + dropout？','测源阻、整流谷值与负载压降'),('结温','环境温度 + 功耗 × 热阻是否越限？','量温并核环境、铜面积与散热界面'),('稳定性','电容有效值、ESR 与布线是否符合手册？','排除探头拾取，再扫负载与温区'),('启动 / 掉电','输出是否越过后级电压与时序条件？','抓 EN、输入、输出及反向电流')]
    for i,(name,question,action) in enumerate(rows):
        y=125+i*132
        out += [box(40,y,190,100,fill=PAPER),text(135,y+60,name,25,anchor='middle'),arrow(235,y+50,285,y+50,colour=BLUE),text(305,y+36,question,24),text(305,y+78,action,23,colour=INK2)]
    return out


def load_transient():
    out=[header('5 µs 的跌落还不是最大跌落','示意 ΔI=0.49 A、10 µF、50 mΩ；延迟 5 µs，临界恢复 τ=5 µs。')]
    px=lambda t:120+780*(t+2)/42
    py=lambda v:430-250*(v+.35)/.35
    for v in [-.3,-.2,-.1,0]:out += [f'<line x1="120" y1="{py(v)}" x2="900" y2="{py(v)}" stroke="{RULE}" stroke-width="1.2" stroke-dasharray="3 5"/>',text(105,py(v)+7,f'{v:g}',23,anchor='end')]
    for t in [0,5,20,40]:out.append(text(px(t),470,str(t),23,anchor='middle'))
    for col,dash,idx in [(BLUE,'',2),(INK2,'6 5',0)]:
        times=sorted(set([i/20 for i in range(-40,801)]+[-1e-7,0,m.transient_minimum_time()*1e6]))
        pts=' '.join(f'{px(t):g},{py(m.transient(t*1e-6)[idx]):g}' for t in times)
        out.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="3" stroke-dasharray="{dash}"/>')
    out += [text(45,150,'偏差 / V',23),text(900,510,'时间 / µs',23,anchor='end'),text(50,552,'实线：电容电压 + ESR 电压；虚线：仅电容电压。',24),text(50,594,'5 µs 时为 −269.5 mV；后续电流缺口仍会继续放电。',24),text(50,636,'恢复过程按电流积分求解，不由振铃次数推断固定相位裕度。',23)]
    return out


def reference_charge():
    out=[header('参考端抽电荷，缓冲器在两次采样间补回','示意每 10 µs 抽走 1 nC；R=10 Ω、C=1 µF，忽略其他寄生。')]
    out += [text(70,200,'理想基准',25),wire(80,235,265,235),box(265,222,75,26,fill=PAPER),text(300,198,'10 Ω',25,anchor='middle'),wire(340,235,800,235),wire(500,235,500,330),wire(465,330,535,330),wire(465,345,535,345),wire(500,345,500,410),wire(480,410,520,410),text(565,348,'1 µF',25),text(770,202,'ADC 参考端',25,anchor='middle'),arrow(800,260,800,365,colour=RED),text(800,410,'每拍取 1 nC',25,anchor='middle')]
    out += [arrow(365,285,450,285,colour=BLUE),text(300,330,'补电',25),text(50,490,'一次下降 Q/C = 1 mV；RC = 10 µs，下一拍前没补完。',25),text(50,545,'重复后最大下降约 1.582 mV，最小约 0.582 mV。',25),text(50,600,'平均补电电流 Q/T = 100 µA；瞬时电流由电容和驱动共同承担。',23),text(50,645,'实际网络必须按 ADC 推荐、缓冲稳定性和建立时间核对。',24)]
    return out


def transient_budget():
    out=[header('上下电压窗口，各自从标称值计预算','示意 3.3 V、±5%：下限 3.135 V，上限 3.465 V；不能把两边合花。')]
    px=lambda v:90+820*(v-3.1)/.4
    out += [box(px(3.135),190,px(3.465)-px(3.135),80,fill=PAPER,stroke=GREEN),wire(90,305,910,305)]
    for v in [3.135,3.3,3.465]:out += [wire(px(v),180,px(v),315),text(px(v),355,f'{v:g} V',25,anchor='middle')]
    out += [text(500,240,'允许电压窗口',26,anchor='middle'),text(50,420,'若下降目标为 99 mV，可分配为：',26)]
    x=60
    for width,label in [(20,'ESR 20 mV'),(60,'缺口电荷 60 mV'),(19,'余项 19 mV')]:
        out += [box(x,460,width*8,70,fill=PAPER),text(x+width*4,570,label,23,anchor='middle')]
        x+=width*8
    out += [text(50,635,'控制接管后仍可能放电；恢复段缺口也必须纳入 99 mV 总预算。',24)]
    return out


SCENES={}
for aid,fn,anchor,title,alt in [
 ('ch09-reference-ladder',reference_budget,'9.1','基准误差预算','三点三伏十二位的一个 LSB 为零点八零六毫伏，基准分配零点二毫伏；初始误差、温漂、噪声与长期漂移分别列项。'),
 ('ch09-shunt-corners',shunt_corners,'9.1','分流器两个最坏角','限流电阻后电流分给负载与分流器；最低输入满载看最小分流电流，最高输入空载看器件与电阻功耗。'),
 ('ch09-reference-charge',reference_charge,'9.1','参考脉冲电荷与补电','参考缓冲串联十欧姆给一微法补电，ADC 每十微秒取一纳库仑；单次一毫伏的下降会因未完全恢复而累积。'),
 ('ch09-tl431-divider-floor',tl431_bias,'9.2','TL431 参考偏流符号','参考端偏流流入芯片，上电阻电流为下电阻电流加偏流；示意两只十千欧给五点零二伏，百千欧给五点二伏。'),
 ('ch09-esr-window',esr_window,'9.3','特定 LM1117 的电容条件','零点三至二十二欧姆 ESR 区间明确绑定 TI LM1117 与钽电容条件，不能泛化为所有稳压器。'),
 ('ch09-thermal-path',thermal_path,'9.3','实际热路径','结到壳、界面和散热片三个热阻串联为二十一度每瓦，完整功耗二点一六瓦，在四十五度环境得到约九十点三六度结温。'),
 ('ch09-ldo-four-accounts',four_accounts,'9.4','稳压器排故测量入口','依次检查输入谷值、结温、稳定性和启动掉电，各项都写出可验证条件和测量对象。'),
 ('ch09-load-transient',load_transient,'9.5','负载瞬态的电流积分','总输出偏差与电容电压分开画，五微秒控制接管时尚未达到最大跌落，后续恢复从同一电容电流继续积分。')]:
    SCENES[aid]=dict(draw=fn,title=title,chapter=9,source='docs/p1-10-ch9.md',anchor=anchor,alt=alt)

SCENES['ch09-transient-budget']=dict(draw=transient_budget,title='双向瞬态预算',chapter=9,source='docs/p1-10-ch9.md',anchor='9.5',alt='三点三伏的上下各百分之五窗口分别核对；下降九十九毫伏预算分为 ESR 二十、缺口电荷六十、余项十九毫伏，后续恢复仍要计入。')
for aid,values,reason in [
 ('ch09-thermal-path',['0.06','2.10','45.36','90.36'],'由示意完整功耗 2.16 W 与 21°C/W 相乘得到温升 45.36°C，再加环境 45°C；2.10/0.06 W 分别为调整与地脚损耗。'),
 ('ch09-load-transient',['0.1','0.2','0.3','40'],'独立瞬态模型的坐标刻度，单位由图中电压和时间轴给出。'),
]:
    SCENES[aid]['numbers']=[dict(value=v,label='示意',reason=reason) for v in values]
