"""Topology narratives: conserved current, charge, damping and loaded budgets."""
import math
from . import topology_models as m
from .interface_models import timeline, INK, BLUE, RED, GRAY
from .primitives import text, line, Graphic
from .plotting import polyline, print_header
from .render import Layer

SPECS = {}


def spec(key, title, anchor, boundary, steps, notes, xlim, ylim, ticks, labels, markers):
    SPECS[key] = dict(title=title, anchor=anchor, boundary=boundary, steps=steps,
                     notes=notes, xlim=xlim, ylim=ylim, xticks=ticks[0], yticks=ticks[1],
                     xlabel=labels[0], ylabel=labels[1], markers=markers)


spec('diff_steer','差分电压重新分配同一份尾电流','11.2',
     '示意匹配 BJT，集电流和 1 mA，VT=26 mV；忽略基流与 Early 效应。',
     ['负差模把电流分给右管，总量仍是 1 mA。','零差模时两管各得 0.5 mA。','各输入 ±10 mV 对应差模 20 mV，已偏离直线近似。','大差模让一边接近独占，不能无限线性放大。'],
     ['实线 I1；虚线 I2','两路之和恒定','tanh 曲线决定分配','还须留集电极电压余量'],
     (-60,60),(0,1),([-60,0,60],[0,.5,1]),('差模 vd / mV','集电流 / mA'),[-40,0,20,40])
spec('mirror_beta','参考电流还要供给两只管子的基流','11.3',
     '示意匹配 β、同 VBE；实线忽略 Early，虚线 VA=100 V、输出 5 V。',
     ['β=20 时，参考支路的基流占比不可忽略。','β=50 时，忽略 Early 的复制比约 96.15%。','β=100 时，复制比为 100/102。','β 增大只缩小基流误差；VCE 差仍会改变复制比。'],
     ['IREF=IC1+IB1+IB2','实线 β/(β+2)','不是只减去一份基流','虚线包含 VCE 不一致'],
     (20,300),(90,105),([20,100,300],[90,95,100,105]),('共同 β / 倍','Iout / Iref / %'),[20,50,100,300])
spec('crossover','预偏置逐渐缩小理想推挽死区','11.4',
     '示意固定 VBE=0.65 V、输入峰值 1 V；恒压降模型不计算静态电流。',
     ['无预偏置，过零附近两支路都不导通。','基极间加 0.6 V，剩余死区缩小。','偏置增至 1 V，过零缺口进一步缩小。','1.3 V 在此模型中恰好消除死区；实物须测静态电流与温漂。'],
     ['虚线输入；实线输出','死区由两侧共同分担','不能只看峰值增益','不是安全偏置的通用值'],
     (0,1),(-1.1,1.1),([0,.5,1],[-1,0,1]),('时间 / 周期','电压 / V'),[.1,.2,.3,.4])
spec('miller_charge','电荷随两端压差变化，电容本身没变','11.5',
     '示意 Cbc=10 pF；输入 ±1 mV，输出增益为 −A；低频电压增益近似。',
     ['A=0，电容输出端固定，电荷只随输入变化。','A=10，输出反相，电容两端摆幅增加。','A=50，同一输入需搬运更多电荷。','A=100，等效输入电容为 1.01 nF。'],
     ['电荷 q=Cbc(vi−vo)','电荷斜率就是等效电容','输出仍须在线性区','高频时应改用完整网络'],
     (-1,1),(-1.1,1.1),([-1,0,1],[-1,0,1]),('输入变化 / mV','电荷变化 / pC'),[-.8,-.3,.3,.8])
spec('pm_step','相位裕度与过冲的换算依赖环路模型','11.5',
     '示意单位反馈 L(s)=ωn²/[s(s+2ζωn)]；时间按 ωn 归一化。',
     ['PM=30°，标准二阶闭环有较强振铃。','PM=45°，ζ≈0.420，过冲约 23.32%。','PM=60°，ζ≈0.612，过冲约 8.77%。','PM=65°，ζ≈0.697，过冲约 4.72%；并非通用换算。'],
     ['实线阶跃；虚线终值','多极点系统需另算','零点与延迟会改变结果','Butterworth 对应约 65.53°'],
     (0,12),(0,1.5),([0,6,12],[0,1,1.5]),('归一化时间 ωnt','闭环输出 / 终值'),[3,3.5,4,5])
spec('pole_split','补偿电容改变两个极点的位置','11.5',
     '示意 R1=R2=100 kΩ、C1=10 pF、C2=100 pF、gm2=1 mS。',
     ['Cc=0 时，两个节点各有自己的 RC 极点。','跨接 2 pF 后，慢极点下降、快极点上移。','Cc=10 pF 时，极点约 1.411 kHz 与 855.0 kHz。','继续加 Cc，不能只看极点；还须计入右半平面零点。'],
     ['实线慢极点；虚线快极点','纵轴每格代表十倍频率','由二次分母精确求根','ω 单位 rad/s，f 单位 Hz'],
     (0,30),(2,7),([0,10,30],[2,3,4,5,6,7]),('补偿 Cc / pF','log10(f / Hz)'),[0,2,10,30])
spec('noise_spectrum','1/f 的斜率要分清功率谱与幅度谱','11.6',
     '示意共同白噪声地板；实线 fc=100 Hz、虚线 fc=1 kHz，不代表器件排名。',
     ['低频闪烁项占优，相对 ASD 的斜率趋近 −10 dB/dec。','到实线的 100 Hz 拐角，两项功率相等。','虚线到 1 kHz 才到同样的拐角。','高频逐渐靠近共同地板，不是突然变平。'],
     ['横轴按十倍频率递增','总 ASD 比地板高 3.01 dB','PSD 的平方根才是 ASD','实际选型还要看输入电流噪声'],
     (0,5),(0,32),([0,2,3,5],[0,10,20,30]),('log10(f / Hz)','ASD / 地板 / dB'),[0,2,3,5])
spec('noise_bandwidth','截止频率之外的噪声仍在积分','11.10',
     '示意白噪声经过一阶低通，fH 为 −3 dB 点；按均方值累计。',
     ['积分到 fH，只收齐全部白噪声均方值的一半。','到 2fH，累计约 70.48%。','到 5fH，仍未收齐高频尾部。','积分到无穷才得到等效噪声带宽 πfH/2。'],
     ['实线：累计均方值比例','不能把截止频率直接当 ENBW','不是先积分幅度再开方','其他滤波器按各自响应积分'],
     (0,10),(0,100),([0,1,5,10],[0,50,100]),('积分上限 / fH','累计均方值 / %'),[1,2,5,10])
spec('diff_cm','同一输出口径内比较差模与共模','11.7',
     '示意尾电流 1 mA、Rc=10 kΩ；虚线仅含 Rc 两侧 ±1% 失配。',
     ['尾阻 10 kΩ，单端共模泄漏明显。','尾阻增至 100 kΩ，单端 CMRR 约 65.69 dB。','到 1 MΩ，单端 CMRR 约 85.68 dB。','差分输出会抵消对称泄漏；不能混用两个输出口径。'],
     ['实线单端；虚线差分','本图只改变尾阻','其他失配与频率效应未计','负载失配的结论需要条件'],
     (4,7),(40,150),([4,5,6,7],[40,80,120]),('log10(Rtail / Ω)','CMRR / dB'),[4,5,6,7])
spec('active_load','有源负载的高增益仍会被后级分流','11.8',
     '示意 gm=40 mS、两管 ro 各 50 kΩ；电阻方案 Rc=2.2 kΩ。',
     ['1 kΩ 外负载同时限制两种方案的增益。','10 kΩ 负载下，有源负载增益只有约 286。','外负载变大，有源负载方案才接近空载增益。','空载极限为 1000，但实线电阻方案仅约 84.3。'],
     ['实线电阻负载；虚线有源负载','空载增益不能带旧负载照抄','取三条并联支路','还要检查噪声与电压余量'],
     (3,6),(0,1050),([3,4,5,6],[0,500,1000]),('log10(RL / Ω)','电压增益幅值 / 倍'),[3,4,5,6])
spec('cascode_resistance','BJT 的有限 β 会限制叠管增阻','11.8',
     '示意两管 ro=100 kΩ、上管 gm=40 mS；基极理想交流接地。',
     ['β=50 时，上管 rπ 分流内部节点。','β=100 时，输出电阻提高但远低于无限 β 模型。','β=200 时，算得约 19.15 MΩ。','增加 β 继续改善；高输出电阻也可能降低输出极点。'],
     ['rπ 与下管 ro 并联','不是一律 gm·ro²','MOS 对应模型没有这条基流通路','输出负载、电容仍要单独核算'],
     (50,300),(0,30),([50,100,200,300],[0,10,20,30]),('上管 β / 倍','输出电阻 / MΩ'),[50,100,200,300])
spec('psrr_ripple','同样的纹波，抑制比随频率变化','11.9',
     '示意电源纹波 100 mVrms；PSRR 在 1 kHz 前 80 dB，随后每十倍频降 20 dB。',
     ['100 Hz 的 80 dB 抑制把纹波折为 10 µVrms。','1 kHz 仍在本例的低频平台。','100 kHz 已降到 40 dB，输入等效纹波为 1 mVrms。','1 MHz 时为 20 dB；不能拿 DC 数字外推。'],
     ['曲线只表示一个教学假设','正负电源分别看手册曲线','输出还须乘相应噪声增益','同一 RMS 口径比较'],
     (2,6),(0,4.2),([2,3,5,6],[0,1,2,3,4]),('log10(f / Hz)','log10(输入误差 / µV)'),[2,3,5,6])
spec('cascade_loading','输出负载会逐级传回增益预算','11.11',
     '原候选：β=200、IC1=0.4 mA、IC2=IC3=1 mA，RE3=1 kΩ。',
     ['100 Ω 与射随器的 1 kΩ 电阻并联，增益约 807。','负载变为 300 Ω，输出电压跟随能力改善。','1 kΩ 仍不是空载，输入阻抗与增益都受影响。','接近空载才回到原来的约千倍；还未检查大信号驱动。'],
     ['各级按受载输入阻抗连算','后级不只是电压增益接近一','虚线为 1000 倍要求','1 mA 静态电流带不了 ±10 mA'],
     (2,5),(700,1100),([2,3,4,5],[800,1000,1100]),('log10(RL / Ω)','总电压增益 / 倍'),[2,math.log10(300),3,5])
spec('beta_budget','标称通过后，还要重算 β 与偏置','11.11',
     '修订候选按正文完整偏置模型，扫共同 β；温度与器件电容未扫描。',
     ['β=100，输入电阻约 8.76 kΩ，低于目标。','β=150 时输入电阻恢复，但还需看其他指标。','β=200 标称输入电阻约 13.13 kΩ。','β=300 输入电阻更高，带宽却下降；不能只挑一个指标。'],
     ['实线模型；虚线 10 kΩ 要求','每次重新求 DC 工作点','不能固定 IC 后只改 rπ','这不是器件保证角点'],
     (100,300),(5,20),([100,200,300],[5,10,15,20]),('共同 β / 倍','输入电阻 / kΩ'),[100,150,200,300])
spec('source_loading','端口增益与源到负载增益是两笔账','11.11',
     '修订候选 β=200，完整 hybrid-π；实线 Rs=10 kΩ，虚线 Rs=0.1 Ω。',
     ['低频时 10 kΩ 源阻已经造成输入分压。','到 100 kHz，寄生电容开始进一步影响信号。','本例源到负载 −3 dB 高频截止约 138.3 kHz。','源阻改变时，输入分压与频率响应都要重新求。'],
     ['各曲线按自身低频值归一','实际低频增益另列正文','Cπ=25 pF、Cµ=5 pF 为示意','旁路与耦合的低频端另验'],
     (3,6),(-30,2),([3,4,5,6],[-30,-20,-10,0]),('log10(f / Hz)','相对低频增益 / dB'),[3,5,math.log10(m.design_bandwidth()),6])


def functions(key, stage):
    if key=='diff_steer': return [(lambda x:m.differential(x/1000)[0]*1000,BLUE,''),(lambda x:m.differential(x/1000)[1]*1000,GRAY,'6 4')]
    if key=='mirror_beta': return [(lambda x:m.mirror(x)*100,BLUE,''),(lambda x:m.mirror(x,5,100)*100,GRAY,'6 4')]
    if key=='crossover': return [(lambda x:m.crossover(math.sin(2*math.pi*x),[0,.6,1,1.3][stage]),BLUE,''),(lambda x:math.sin(2*math.pi*x),GRAY,'6 4')]
    if key=='miller_charge': return [(lambda x:.01*(1+[0,10,50,100][stage])*x,BLUE,'')]
    if key=='pm_step': return [(lambda x:m.step(x,m.damping([30,45,60,65][stage])),BLUE,''),(lambda x:1,GRAY,'6 4')]
    if key=='pole_split': return [(lambda x:math.log10(m.compensated(x*1e-12)[0]),BLUE,''),(lambda x:math.log10(m.compensated(x*1e-12)[1]),GRAY,'6 4')]
    if key=='noise_spectrum': return [(lambda x:20*math.log10(m.noise_density(10**x)/1e-8),BLUE,''),(lambda x:20*math.log10(m.noise_density(10**x,1000)/1e-8),GRAY,'6 4')]
    if key=='noise_bandwidth': return [(lambda x:200/math.pi*math.atan(x),BLUE,'')]
    if key=='diff_cm': return [(lambda x:20*math.log10(abs(m.cmrr(10**x)[0]/m.cmrr(10**x)[1])),BLUE,''),(lambda x:20*math.log10(abs(m.cmrr(10**x)[2]/m.cmrr(10**x)[3])),GRAY,'6 4')]
    if key=='active_load': return [(lambda x:.04*m.parallel(2200,50000,10**x),BLUE,''),(lambda x:.04*m.parallel(50000,50000,10**x),GRAY,'6 4')]
    if key=='cascode_resistance': return [(lambda x:m.cascode_r(beta=x)/1e6,BLUE,'')]
    if key=='psrr_ripple': return [(lambda x:1+max(0,x-3),BLUE,'')]
    if key=='cascade_loading': return [(lambda x:m.old_cascade(load=10**x)[3],BLUE,''),(lambda x:1000,GRAY,'6 4')]
    if key=='beta_budget': return [(lambda x:10*m.design_ac(0,x)[0].real/(1-m.design_ac(0,x)[0].real),BLUE,''),(lambda x:10,GRAY,'6 4')]
    return [(lambda x:20*math.log10(abs(m.design_ac(10**x,source=10000)[4]/m.design_ac(0,source=10000)[4])),BLUE,''),(lambda x:20*math.log10(abs(m.design_ac(10**x,source=.1)[4]/m.design_ac(0,source=.1)[4])),GRAY,'6 4')]


def plot(key,stage,small=False,begin=None):
    s=SPECS[key];xmin,xmax=s['xlim'];ymin,ymax=s['ylim']
    x0,y0,w,h=(55,178,250,94) if small else (90,320,550,155)
    if key=='diff_steer' and not small:y0,h=290,125
    size=18 if small else 20
    px=lambda x:x0+w*(x-xmin)/(xmax-xmin)
    py=lambda y:y0-h*(y-ymin)/(ymax-ymin)
    yield text(8 if small else 35,y0-h-17,s['ylabel'],size)
    for y in s['yticks']:yield line(x0,py(y),x0+w,py(y),GRAY,1,'2 5')+text(x0-7,py(y)+6,f'{y:g}',size,anchor='end')
    for x in s['xticks']:yield text(px(x),y0+26,f'{x:g}',size,anchor='middle')
    yield text(x0+w,y0+51,s['xlabel'],size,anchor='end')
    xs=[xmin+(xmax-xmin)*i/240 for i in range(241)]
    for i,(fn,color,dash) in enumerate(functions(key,stage)):
        yield polyline([(px(x),py(fn(x))) for x in xs],color,dash=dash,begin=begin,identity=f'{key}-{stage}-{i}')
    selected=int((key=='noise_spectrum' and stage==2) or (key=='active_load' and stage in [1,2]) or (key=='mirror_beta' and stage==3))
    fn=functions(key,stage)[selected][0];x=s['markers'][stage]
    final=f'<circle cx="{px(x):g}" cy="{py(fn(x)):g}" r="5" fill="{INK}"/>'
    if begin is None:yield final
    else:
        path='M'+' L'.join(f'{px(xmin+(x-xmin)*i/80):g},{py(fn(xmin+(x-xmin)*i/80)):g}' for i in range(81))
        yield Graphic(f'<circle r="5" fill="{INK}" opacity="0"><set attributeName="opacity" to="1" begin="{begin:g}s"/><animateMotion path="{path}" begin="{begin:g}s" dur="2s" fill="freeze"/></circle>',final)
    if key=='diff_steer':
        a,b=m.differential(x/1000);by=257 if small else 375;bw=250 if small else 550
        yield f'<rect x="{x0}" y="{by-13}" width="{bw*a/.001:g}" height="12" fill="{BLUE}"/><rect x="{x0+bw*a/.001:g}" y="{by-13}" width="{bw*b/.001:g}" height="12" fill="{GRAY}" stroke="{INK}"/>'
        yield text(x0,by+23,f'I1={a*1000:.3f}，I2={b*1000:.3f} mA',size)


def scene(key):
    s=SPECS[key];boundary=s['boundary'] if s['boundary'].startswith('示意') else '示意：'+s['boundary']
    tl=timeline(s['title'],s['steps'],boundary);layers=[]
    for i,beat in enumerate(tl.beats):
        layers.append(Layer(beat.name,text(35,116,s['notes'][i],20)))
        layers.extend(Layer(beat.name,g) for g in plot(key,i,begin=beat.start+.2 if i<3 else None))
    return tl,layers


def storyboard(key):
    s=SPECS[key];out=print_header(s['title'],940,s['boundary'])
    for i in range(4):
        x,y=18+(i%2)*350,65+(i//2)*310
        out += [f'<g data-storyboard-beat="{i+1}" transform="translate({x} {y})">',f'<rect width="334" height="298" rx="8" fill="none" stroke="{GRAY}"/>',text(10,27,f'{i+1}. '+s['notes'][i],18),*plot(key,i,small=True),'</g>']
    for i,caption in enumerate(s['steps']):out.append(text(26,724+32*i,f'{i+1}. '+caption,18))
    # Two explicit lines keep the physical conditions readable at print width.
    boundary=s['boundary'] if s['boundary'].startswith('示意') else '示意：'+s['boundary']
    split=boundary.find('；')
    if split<0:split=boundary.find('，',35)
    if split<0:split=min(52,len(boundary))
    out += [text(26,880,boundary[:split+1],18),text(26,908,boundary[split+1:],18),'</svg>']
    return '\n'.join(out)


def metadata(key):
    s=SPECS[key]
    param={
        'mirror_beta':('β',[20,50,100,300],'倍'),
        'pm_step':('PM',[30,45,60,65],'°'),
        'pole_split':('Cc',[0,2,10,30],'pF'),
        'noise_spectrum':('f',[1,100,1000,100000],'Hz'),
        'noise_bandwidth':('F/fH',[1,2,5,10],'倍'),
        'diff_cm':('Rtail',[1e4,1e5,1e6,1e7],'Ω'),
        'active_load':('RL',[1e3,1e4,1e5,1e6],'Ω'),
        'cascode_resistance':('β',[50,100,200,300],'倍'),
        'psrr_ripple':('f',[100,1000,100000,1000000],'Hz'),
        'cascade_loading':('RL',[100,300,1000,100000],'Ω'),
        'beta_budget':('β',[100,150,200,300],'倍'),
        'source_loading':('f',[1000,100000,m.design_bandwidth(),1000000],'Hz'),
    }.get(key)
    numbers=[dict(value=str(v),label='示意',reason='教学模型的坐标或节拍编号，按正文假设计算，不作为器件保证。') for v in sorted(set([0,1,2,3,4]+s['xticks']+s['yticks']))]
    if key=='diff_steer':numbers += [dict(value=f'{v*1000:.3f}',label='示意',reason='匹配 BJT 的 tanh 电流分配模型，在该节拍指定差模电压处求值，单位 mA，显示三位小数。') for x in s['markers'] for v in m.differential(x/1000)]
    return dict(id='ch11-'+key.replace('_','-')+'-v2',chapter=11,source='docs/p2-01-ch11.md',anchor=s['anchor'],type='A3' if param else 'A1',style_id='FA-029',layout_id='IG-015',purpose=s['title'],alt=s['title']+'。'+' '.join(s['steps'])+' '+s['boundary'],en_prompt='Four causal model frames with physical axes, explicit conditions, readable print and dashed reference curves. '+key.replace('_',' '),scene=lambda:scene(key),storyboard=lambda:storyboard(key),parameters=[dict(name=param[0],values=param[1],unit=param[2])] if param else [],numbers=numbers)
