from scripts.visuals.scenes.handdrawn_wave2 import BLUE,GREEN,INK,INK2,PAPER,RED,RULE,AMBER,box,header,text
from scripts.visuals.primitives import directed_arrow as arrow
from scripts.visuals import comparator_models as model


def window_logic():
    out=[header('窗口监控的两路极性','两路均为开集电极；电池减半分压，基准独立稳定。')]
    for y,name,plus,minus in [(230,'欠压 A','被测 / 2','1.5 V'),(400,'过压 B','1.8 V','被测 / 2')]:
        out += [text(375,y-53,name,25,colour=BLUE),
                f'<path d="M370,{y-40} L370,{y+40} L440,{y} Z" fill="none" stroke="{INK}" stroke-width="3"/>',
                text(377,y-10,'+',24),text(377,y+30,'−',24),text(245,y-12,plus,24,anchor='end'),text(245,y+32,minus,24,anchor='end'),
                f'<path d="M255,{y-20} H370 M255,{y+20} H370 M440,{y} H700" fill="none" stroke="{INK}" stroke-width="3"/>']
    out += [f'<path d="M700,145 V160 M700,195 V400 M700,315 H880" fill="none" stroke="{INK}" stroke-width="3"/>',
            f'<rect x="690" y="160" width="20" height="35" fill="none" stroke="{INK}" stroke-width="3"/>',
            f'<circle cx="700" cy="315" r="5" fill="{INK}"/>',text(700,135,'VPU',24,anchor='middle'),text(735,187,'Rp',24),text(805,300,'OUT',25),
            text(50,495,'电池 2.8 V：分压 1.4 V，A 拉低 → OUT 低',25),
            text(50,540,'电池 3.2 V：分压 1.6 V，两路松手 → OUT 高',25,colour=GREEN),
            text(50,585,'电池 3.8 V：分压 1.9 V，B 拉低 → OUT 低',25),
            text(50,636,'等于 3.0 / 3.6 V 门限时不保证状态，须留误差与迟滞余量。',23)]
    return out


def delay_endpoints():
    out=[header('输出跨哪个门限，决定响应时间量到哪里','示意 RC 输出：5 V、4.7 kΩ、50 pF；输出管在 1 µs 释放。')]
    x0,y0,w,h=100,435,530,260
    px=lambda t:x0+w*(t-.9)/.7
    py=lambda v:y0-h*v/5
    for v in [0,1.4,2.5,3.5,5]:
        out += [f'<line x1="{x0}" y1="{py(v)}" x2="630" y2="{py(v)}" stroke="{RULE}" stroke-dasharray="3 5"/>',text(85,py(v)+7,f'{v:g}',22,anchor='end')]
    out += [text(50,150,'输出 / V',22),text(630,505,'时间 / µs',22,anchor='end')]
    for t in [1,1.3,1.6]:out.append(text(px(t),475,f'{t:g}',22,anchor='middle'))
    pts=' '.join(f'{px(.9+i*.001):.3f},{py(model.release_voltage((.9+i*.001)*1e-6)):.3f}' for i in range(701))
    out.append(f'<polyline points="{pts}" fill="none" stroke="{BLUE}" stroke-width="3"/>')
    for i,v in enumerate([1.4,2.5,3.5]):
        t=model.release_crossing(v)*1e6
        out += [f'<circle cx="{px(t)}" cy="{py(v)}" r="6" fill="{INK}"/>',text(690,205+i*75,f'{v:g} V：{t:.3f} µs',23)]
    out += [text(50,555,'经典 LM393 手册的 1.3 µs 典型响应量到输出跨 1.4 V。',24),text(50,599,'不能再加整个 RC 上升区间；本图不反推其内部延迟。',23),text(50,641,'10%→90% 为区间长度，本例 0.516 µs。',23)]
    return out


def threshold_budget():
    out=[header('半压分压的 1% 容差，是 ±25 mV','5 V 精确供电；两只 100 kΩ、1% 电阻反向取极限。')]
    for i,(name,value,col) in enumerate([('分压极限',25,BLUE),('25°C 失调上限',5,RED),('典型偏流示意',1.225,INK2)]):
        y=170+i*115
        out += [text(50,y+30,name,24),f'<rect x="310" y="{y}" width="{value*18}" height="40" fill="none" stroke="{col}" stroke-width="3"/>',text(325+value*18,y+30,f'{value:g} mV',24,colour=col)]
    out += [text(50,528,'5 × 101 / (99 + 101) = 2.525 V；反向为 2.475 V。',24),text(50,573,'25 nA × (50 kΩ − 1 kΩ) = 1.225 mV，只作量级比较。',23),text(50,618,'全温失调最大 9 mV；偏流最坏预算另用适用保证值。',23)]
    return out


def pullup_accounts():
    out=[header('上拉电阻先求可行区间','示意 5 V、50 pF、10%→90% 小于 1 µs，限流目标 2 mA。')]
    out += [text(50,170,'由电流定下限',26,colour=RED),text(50,211,'保守用 VOL=0：R ≥ 2.5 kΩ',24),text(520,170,'由上升时间定上限',26,colour=BLUE),text(520,211,'ln9 · RC ≤ 1 µs：R ≤ 9.10 kΩ',24)]
    px=lambda r:90+75*r
    out += [f'<rect x="{px(2.5)}" y="300" width="{px(9.1)-px(2.5)}" height="90" fill="{PAPER}" stroke="{GREEN}" stroke-width="3"/>',text(600,352,'可行区间',27,colour=GREEN,anchor='middle'),f'<line x1="90" y1="410" x2="900" y2="410" stroke="{INK}"/>']
    for r in [0,2.5,4.7,9.1]:out.append(text(px(r),449,'9.10' if r==9.1 else f'{r:g}',24,anchor='middle'))
    out += [text(910,485,'kΩ',23,anchor='end'),f'<circle cx="{px(4.7)}" cy="350" r="9" fill="{INK}"/>',text(50,540,'4.7 kΩ：约 0.516 µs、最大约 1.064 mA。',24),text(50,583,'再按后级 VIL 查 VOL；6 mA 条目是在 VOL=1.5 V 测的。',23),text(50,626,'330 Ω 上拉到 12 V 的 36.4 mA 估值已超出绝对最大。',23)]
    return out


def hysteresis_window():
    out=[header('迟滞回环，先写输出极性与参考条件','同相示意：独立 6 V 基准，VOH=12 V、VOL=0.1 V，R1/R2=10/390。')]
    px=lambda v:100+650*(v-5.7)/.6
    py=lambda v:435-240*v/12
    lo=model.noninverting_threshold(12,reference=6,rin=10000,rfeedback=390000)
    hi=model.noninverting_threshold(.1,reference=6,rin=10000,rfeedback=390000)
    for v in [0,6,12]:out+=[text(82,py(v)+7,str(v),23,anchor='end'),f'<line x1="100" y1="{py(v)}" x2="750" y2="{py(v)}" stroke="{RULE}" stroke-dasharray="3 5"/>']
    out.append(f'<path d="M{px(5.7)},{py(.1)} H{px(hi)} V{py(12)} H{px(6.3)} M{px(6.3)},{py(12)} H{px(lo)} V{py(.1)} H{px(5.7)}" fill="none" stroke="{BLUE}" stroke-width="3"/>')
    out += [arrow(px(5.85),py(.1),px(6),py(.1),colour=BLUE),arrow(px(6.15),py(12),px(6),py(12),colour=RED),text(px(lo),480,f'{lo:.3f}',24,anchor='middle'),text(px(hi),480,f'{hi:.3f}',24,anchor='middle'),text(50,162,'输出 / V',23),text(750,518,'输入 / V',23,anchor='end'),
            text(50,566,'窗口约 305 mV；120 mVpp 噪声仍需结合门限距离验证。',24),text(50,609,'实际开集电极输出须重算加载，电池绝对电压要用独立参考。',23)]
    return out


def glitch_margin():
    out=[header('200 mV 毛刺是否免疫，先问基线在哪里','理想反相迟滞，初态高；上阈值 2.727 V，下阈值 2.273 V。')]
    x0,y0,w,h=130,420,650,230
    py=lambda v:y0-h*(v-2.3)/.6
    out += [text(55,153,'输入 / V',23)]
    for v in [2.4,2.6,30/11,2.8]:
        out += [text(108,py(v)+7,f'{v:.3f}' if v==30/11 else f'{v:g}',22,anchor='end'),f'<line x1="130" y1="{py(v)}" x2="800" y2="{py(v)}" stroke="{RULE}" stroke-dasharray="4 5"/>']
    for x,base in [(250,2.4),(620,2.6)]:
        out += [f'<path d="M{x-80},{py(base)} H{x-30} L{x},{py(base+.2)} L{x+30},{py(base)} H{x+80}" fill="none" stroke="{BLUE}" stroke-width="4"/>',text(x,470,'保持高' if base==2.4 else '越上阈，翻低',24,anchor='middle')]
    out += [text(50,539,'同为 +200 mV：2.4→2.6 V 不越阈；2.6→2.8 V 会越阈。',24),text(50,585,'毛刺幅度比窗口小，不等于不会触发。',24,colour=RED),text(50,630,'实际还受过驱动、传播延迟和最小脉宽限制。',23)]
    return out


SCENES={}
for aid,fn,anchor,title,alt in [
 ('ch07-window-logic',window_logic,'7.2','窗口比较器极性与线与','欠压路被测进正端，过压路基准进正端；任一路越界都能拉低公共输出，窗口内两路松手。'),
 ('ch07-delay-endpoints',delay_endpoints,'7.1','响应时间的测量终点','示意 RC 充电曲线上，输出越过一点四伏、二点五伏和三点五伏的时刻不同；手册指定的响应终点不能再加完整上升区间。'),
 ('ch07-threshold-budget',threshold_budget,'7.2','分压容差与偏流误差','五伏等值分压，两只百分之一电阻反向极限产生正负二十五毫伏；与五毫伏室温失调上限和一点二二五毫伏典型偏流示意分别比较。'),
 ('ch07-pullup-three-accounts',pullup_accounts,'7.2','上拉电阻的可行区间','五伏、五十皮法、上升小于一微秒且电流不超过二毫安，上拉取值区间约二点五到九点一千欧；四点七千欧回代合格还须核对低电平保证。'),
 ('ch07-hysteresis-window',hysteresis_window,'7.3','同相迟滞回环的独立参考','独立六伏基准、理想输出十二伏与零点一伏，同相输入上行六点一五一伏翻高，下行五点八四六伏翻低；窗口约三百零五毫伏，非电池自身比例参考。'),
 ('ch07-glitch-margin',glitch_margin,'7.5','相同毛刺不同门限距离','同样二百毫伏毛刺，基线二点四伏时不超过二点七二七伏门限，基线二点六伏时越阈翻转；是否触发取决于当前状态和门限距离。')]:
    SCENES[aid]=dict(draw=fn,title=title,chapter=7,source='docs/p1-08-ch7.md',anchor=anchor,alt=alt)

SCENES['ch07-delay-endpoints']['numbers']=[
    dict(value='0',label='示意',reason='独立 RC 模型假定输出释放前为零伏。'),
    dict(value='2.5',label='示意',reason='五伏模型的 50% 输出测量门限。'),
    dict(value='3.5',label='示意',reason='五伏模型的 70% 输出测量门限。'),
]
