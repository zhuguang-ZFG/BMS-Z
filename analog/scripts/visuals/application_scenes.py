"""Chapter 12 narratives: follow the measured variable and its model boundary."""
import math
from . import application_models as m
from .interface_models import timeline, INK, BLUE, GRAY
from .primitives import text, line, Graphic
from .plotting import polyline, print_header
from .render import Layer

SPECS = {}


def spec(key, title, anchor, boundary, notes, steps, limits, ticks, labels, markers, parameter=None):
    SPECS[key] = dict(title=title, anchor=anchor, boundary=boundary, notes=notes,
                      steps=steps, xlim=limits[0], ylim=limits[1], xticks=ticks[0],
                      yticks=ticks[1], xlabel=labels[0], ylabel=labels[1],
                      markers=markers, parameter=parameter)


spec('loop_error','虚短的精度由环路增益决定','12.1',
     '示意同相增益目标 6；A 为正实数，稳定线性 DC 模型，无失调。',
     ['A=60','A=600','A=6000','A=60000'],
     ['开环增益只有目标增益十倍，闭环仍有明显误差。','开环增益升高，反馈继续缩小两输入压差。','闭环越来越接近六倍，仍不是严格相等。','低频增益很大也不能保证高频虚短或输出摆幅。'],
     ((1,5),(0,40)),([1,2,3,4,5],[0,10,20,30,40]),('log10(A / 倍)','闭环相对误差 / %'),[math.log10(v) for v in [60,600,6000,60000]])
spec('source_loading','增益相同，信号源负担可以不同','12.2',
     '示意理想反相电路：Rf/Rin=10；实线 Rin=10 kΩ，虚线 Rin=100 kΩ。',
     ['源阻 100 Ω','源阻 1 kΩ','源阻 10 kΩ','源阻 100 kΩ'],
     ['两方案的电阻比相同，低源阻下均接近十倍。','源阻增加后，较小输入电阻先产生明显分压。','源阻等于实线的输入电阻，源到输出增益只有五倍。','增大两只电阻能减轻加载，噪声与寄生仍须另算。'],
     ((2,5),(0,11)),([2,3,4,5],[0,5,10]),('log10(Rs / Ω)','源到输出增益幅值'),[2,3,4,5])
spec('resistor_mismatch','电阻绝对容差不等于比值匹配','12.3',
     '示意单位差放，四只独立容差 ±t；取两电阻比相反方向的角点。',
     ['t=0.01%','t=0.1%','t=0.5%','t=1%'],
     ['极小容差仍只能给有限的共模抑制。','容差十倍增大，本角点 CMRR 约降二十分贝。','必须同时算差模增益与共模泄漏。','百分之一独立电阻在本例角点只有约三十四分贝。'],
     ((-2,0),(30,80)),([-2,-1,0],[40,60,80]),('log10(t / %)','CMRR / dB'),[-2,-1,math.log10(.5),0])
spec('leaky_integrator','泄放把无限 DC 增益变成有限平台','12.4',
     '示意 Rin=10 kΩ、Rf=1 MΩ、C=10 nF；理想运放，fp≈15.92 Hz。',
     ['低频平台','泄放拐点','积分频段','仍须检查运放带宽'],
     ['低频输出趋向有限的负一百倍。','泄放极点附近还不是理想积分关系。','高于低极点后，幅频斜率接近每十倍频负二十分贝。','虚线是理想积分幅值，高频真实环路仍有限制。'],
     ((0,4),(-20,70)),([0,1,2,3,4],[-20,0,20,40,60]),('log10(f / Hz)','幅值 / dB'),[0,math.log10(1/(2*math.pi*.01)),2,4])
spec('bandlimited_diff','微分只在限定的频带内成立','12.4',
     '示意 Ci=10 nF、Rin=1 kΩ、Rf=10 kΩ、Cf=1 nF，两极点重合。',
     ['低频近似微分','增益开始弯折','双极点附近','高频增益下降'],
     ['低频随频率上升，输出反映输入变化率。','串联电阻与反馈电容逐渐限制增益。','本例两个时间常数同为十微秒，峰值增益为五倍。','高频不再继续放大，但稳定性还要检查噪声增益。'],
     ((2,6),(-25,20)),([2,3,4,5,6],[-20,0,20]),('log10(f / Hz)','信号增益 / dB'),[2,3,math.log10(1/(2*math.pi*1e-5)),6])
spec('filter_q','同一自然频率，阶跃形状随 Q 变化','12.5',
     '示意标准二阶低通；实线为指定 Q，虚线是终值；时间按 ω0 归一化。',
     ['Q=0.5','Q=1/√3','Q=1/√2','Q=0.864'],
     ['临界阻尼单调到达终值。','二阶 Bessel 的 Q 约为零点五七七。','Butterworth 通带平坦，阶跃仍有约百分之四点三二过冲。','更高 Q 增加振铃；比较响应前须说明频率归一化。'],
     ((0,12),(0,1.2)),([0,6,12],[0,.5,1]),('归一化时间 ω0t','输出 / DC 终值'),[4,4,4.44,3.85],('Q',[.5,1/math.sqrt(3),1/math.sqrt(2),.864],'倍'))
spec('filter_tolerance','电容比改变 Q，同向缩放才保持形状','12.5',
     '示意 R1=R2、K=1，C1=10 nF 固定，C2 扫描；虚线 Q=1/√2。',
     ['C2=4.75 nF','C2=5 nF','C2=5.25 nF','独立容差要扫角点'],
     ['接地电容偏小，电容比增大，Q 上升。','名义电容比为二时，Q 为 Butterworth 值。','接地电容偏大，Q 下降，自然频率也改变。','只有两电容同向等比例缩放，才能单移频率而保留 Q。'],
     ((4.5,5.5),(.65,.76)),([4.5,5,5.5],[.65,.7,.75]),('C2 / nF','品质因数 Q'),[4.75,5,5.25,5.5])
spec('peak_droop','保持电容的电压仍在随时间下降','12.6',
     '示意 C=100 nF、初值 1 V、R=10 MΩ；实线另有 100 nA 外流，虚线无漏流。',
     ['捕获之后','保持 10 ms','保持 50 ms','保持 100 ms'],
     ['二极管截止以后，输出不再自动保持峰值。','电阻与漏流共同取走电容电荷。','跟随器隔离负载，但自身偏置电流也要入账。','加大电容能减缓下垂，也提高捕获所需的充电量。'],
     ((0,100),(.79,1.01)),([0,50,100],[.8,.9,1]),('保持时间 / ms','保持电压 / V'),[0,10,50,100])
spec('phase_cross','相位裕度必须在环路交越处读取','12.7',
     '示意 A=10⁵/(1+jf/10 Hz)，β=0.1；虚线为单位环路增益。',
     ['1 kHz','10 kHz','约 100 kHz 交越','1 MHz 已低于单位'],
     ['开环很大并不能直接给出相位裕度。','继续沿环路幅值曲线寻找零分贝。','本例在约十万赫兹交越，再在此读取相位。','单极点示意的裕度接近九十度，不能替代真实器件模型。'],
     ((3,6),(-25,45)),([3,4,5,6],[-20,0,20,40]),('log10(f / Hz)','|Aβ| / dB'),[3,4,5,6])
spec('riso_step','隔离电阻前后取反馈，阶跃不同','12.9',
     '示意 A0=10⁵、fp=10 Hz、Ro=50 Ω、CL=100 nF，单位化小信号阶跃。',
     ['无隔离电阻','Riso=50 Ω，取 A','同一接法的负载端','Riso=50 Ω，取 B'],
     ['无隔离电阻，输出强烈振铃但最终收敛。','在电阻之前取反馈，运放输出端迅速稳定。','负载端有 RC 延迟，须与运放端一起观察。','移到电阻之后取反馈会失去零点，振铃更大。'],
     ((0,20),(0,1.9)),([0,10,20],[0,1,1.8]),('阶跃后时间 / µs','输出 / 输入阶跃'),[2.8,2,8,4])
spec('tia_noise_gain','结电容抬高噪声增益，不直接给信号带宽','12.10',
     '示意 Rf=1 MΩ、Cin=10 pF、A0=10⁵、fp=100 Hz，Cf=0；虚线为 |A|。',
     ['1 kHz','约 15.9 kHz 拐点','约 399 kHz 交越','高频环路增益不足'],
     ['低频噪声增益接近一。','这个拐点是噪声增益开始上升，不是信号截止。','两条幅值曲线相交，需同时检查相位。','有限开环增益使求和节点不再严格保持零电压。'],
     ((3,7),(0,85)),([3,4,5,6,7],[0,20,40,60,80]),('log10(f / Hz)','幅值 / dB'),[3,math.log10(1/(2*math.pi*1e6*1e-11)),math.log10(m.crossing(lambda f:m.tia_loop(f,0))[0]),7])
spec('tia_compensation','反馈电容改变闭环阻尼与速度','12.10',
     '示意 Rf=1 MΩ、Cin=10 pF、A0=10⁵、fp=100 Hz；电流阶跃归一化。',
     ['Cf=0','Cf≈0.399 pF','Cf=0.6 pF','Cf=1 pF'],
     ['未补偿的二阶模型强烈振铃，不能仅凭它宣布持续振荡。','平方根初估给出一个起点，仍有可见过冲。','增大到零点六皮法，本模型的阻尼进一步增加。','一皮法响应更慢；最终值按噪声、速度与裕度选择。'],
     ((0,10),(0,2)),([0,5,10],[0,1,2]),('电流阶跃后时间 / µs','输出 / 理想终值'),[1.25,1.5,2.5,5],('Cf',[0,math.sqrt(10/(2*math.pi*10)),.6,1],'pF'))
spec('integrator_cycle','恒流改变斜率，初值决定直流中心','12.11',
     '示意 Rin=10 kΩ、C=10 nF，输入 ±1 V、周期 1 ms；初始输出 0 V。',
     ['输入 +1 V','半周期到 −5 V','输入 −1 V','一周期回到 0 V'],
     ['正输入产生负的输出斜率。','五百微秒后下降五伏，这是峰峰值。','输入反号，斜率反向，输出沿直线回升。','初值零给出零到负五伏；零均值时应为正负二点五伏。'],
     ((0,1),(-5.5,1.5)),([0,.5,1],[-5,0]),('时间 / ms','电压 / V'),[.1,.5,.75,1])
spec('sc_charge','平均电流来自每周期搬运的电荷','12.12',
     '示意 C1=1 pF、固定电压差 1 V、fclk=100 kHz；每周期充分建立。',
     ['完成第一周期','完成第二周期','完成第三周期','完成第四周期'],
     ['完成一次两相切换，净搬运一皮库仑。','两周期累计两皮库仑，阶梯不是连续电流。','三个周期的平均搬运率仍为一百纳安。','四周期四皮库仑对应十兆欧平均等效电阻。'],
     ((0,40),(0,4.5)),([0,10,20,30,40],[0,1,2,3,4]),('时间 / µs','累计电荷 / pC'),[10,20,30,40])
spec('sc_settling','半 LSB 要比一 LSB 多一个 ln2','12.12',
     '示意满幅一阶建立、12 bit；实线为残差，虚线为半 LSB。',
     ['4τ','8τ','12 ln2·τ','13 ln2·τ'],
     ['几倍时间常数还不足以满足十二位精度。','接近八倍时间常数，残差仍高于半 LSB。','十二乘 ln2 只达到一 LSB。','半 LSB 要十三乘 ln2，且还没包括其他误差。'],
     ((0,10),(-4.5,.1)),([0,4,8,10],[-4,-3,-2,-1,0]),('建立时间 / τ','log10(残差 / 满幅)'),[4,8,12*math.log(2),13*math.log(2)])
spec('source_noise','源阻改变电压噪声与电流噪声的权重','12.13',
     '示意 300 K；实线 en=5 nV、in=1 pA，虚线 en=20 nV、in=1 fA，均每√Hz。',
     ['Rs=100 Ω','Rs=10 kΩ','Rs=100 kΩ','Rs=1 MΩ'],
     ['低源阻时，较低电压噪声可能占优。','源电阻热噪声与电流噪声已需要共同计入。','源阻继续上升，实线的电流噪声项逐渐主导。','高阻源仍要比较总噪声，不能只看直流偏置误差。'],
     ((2,6),(0,3.2)),([2,3,4,5,6],[0,1,2,3]),('log10(Rs / Ω)','log10(总 ASD / nV/√Hz)'),[2,4,5,6])
spec('bias_offset','偏置误差先按电阻源模型计算','12.13',
     '示意纯电阻电压源；实线 Ib=20 nA，虚线 Ib=1 pA，均为假设值。',
     ['Rs=1 kΩ','Rs=10 kΩ','Rs=100 kΩ','Rs=1 MΩ'],
     ['输入电流流经源阻，产生直流电压误差。','源阻十倍增加，误差也十倍增加。','还要叠加失调、漏电与温度范围内的变化。','一兆欧下分别为二十毫伏与一微伏；不是器件家族保证。'],
     ((3,6),(-3.2,4.5)),([3,4,5,6],[-3,-1,1,3]),('log10(Rs / Ω)','log10(|误差| / µV)'),[3,4,5,6])
spec('midpoint','中点偏置要按阻抗与启动一起算','12.8',
     '示意 12 V、上下各 100 kΩ、Cmid=1 µF；启动理想阶跃，尚未加载。',
     ['启动时刻','一个时间常数','三个时间常数','五个时间常数'],
     ['电容初始未充电，中点并不会立刻到六伏。','等效源阻五十千欧，五十毫秒后到终值约六成。','三个时间常数仍有约百分之五的残差。','启动时间、偏置电流误差与交流噪声要共同预算。'],
     ((0,250),(0,6.5)),([0,50,150,250],[0,3,6]),('上电后时间 / ms','中点电压 / V'),[0,50,150,250])


for _key,_anchor in {
    'bandlimited_diff':'12.4a','filter_q':'12.5a','filter_tolerance':'12.5b',
    'phase_cross':'12.7b','riso_step':'12.9a','tia_compensation':'12.10a',
    'sc_charge':'12.12a','sc_settling':'12.12b','source_noise':'12.13a',
}.items():SPECS[_key]['anchor']=_anchor


def functions(key, stage):
    if key=='loop_error': return [(lambda x:600/(10**x+6),BLUE,'')]
    if key=='source_loading': return [(lambda x:1e5/(1e4+10**x),BLUE,''),(lambda x:1e6/(1e5+10**x),GRAY,'6 4')]
    if key=='resistor_mismatch':
        def cmrr(x):
            t=10**x/100
            ad,ac=m.difference_gains(1-t,1+t,1+t,1-t)
            return 20*math.log10(abs(ad/ac))
        return [(cmrr,BLUE,'')]
    if key=='leaky_integrator': return [(lambda x:20*math.log10(abs(m.leaky(10**x))),BLUE,''),(lambda x:20*math.log10(1/(2*math.pi*10**x*1e-4)),GRAY,'6 4')]
    if key=='bandlimited_diff': return [(lambda x:20*math.log10(abs(m.differentiator(10**x))),BLUE,'')]
    if key=='filter_q':return [(lambda x:m.second_step(x,[.5,1/math.sqrt(3),1/math.sqrt(2),.864][stage]),BLUE,''),(lambda x:1,GRAY,'6 4')]
    if key=='filter_tolerance':return [(lambda x:math.sqrt(10/x)/2,BLUE,''),(lambda x:1/math.sqrt(2),GRAY,'6 4')]
    if key=='peak_droop':return [(lambda x:m.peak_hold(x/1000),BLUE,''),(lambda x:m.peak_hold(x/1000,leakage=0),GRAY,'6 4')]
    if key=='phase_cross':return [(lambda x:20*math.log10(abs(1e4/(1+1j*10**x/10))),BLUE,''),(lambda x:0,GRAY,'6 4')]
    if key=='riso_step':return [(lambda x:m.capacitive_step(x*1e-6,[0,50,50,50][stage],['A','A','A','B'][stage],['load','amp','load','load'][stage]),BLUE,''),(lambda x:1,GRAY,'6 4')]
    if key=='tia_noise_gain':return [(lambda x:20*math.log10(abs(m.tia_ng(10**x,0))),BLUE,''),(lambda x:20*math.log10(abs(1e5/(1+1j*10**x/100))),GRAY,'6 4')]
    if key=='tia_compensation':return [(lambda x:m.tia_step(x*1e-6,[0,math.sqrt(1e-11/(2*math.pi*1e6*1e7)),.6e-12,1e-12][stage]),BLUE,''),(lambda x:1,GRAY,'6 4')]
    if key=='integrator_cycle':return [(lambda x:m.triangle(x/1000),BLUE,''),(lambda x:1 if x<.5 else -1,GRAY,'6 4')]
    if key=='sc_charge':return [(lambda x:math.floor(x/10+1e-12),BLUE,''),(lambda x:x/10,GRAY,'6 4')]
    if key=='sc_settling':return [(lambda x:-x/math.log(10),BLUE,''),(lambda x:math.log10(2**-13),GRAY,'6 4')]
    if key=='source_noise':return [(lambda x:math.log10(m.source_noise(10**x,5e-9,1e-12)*1e9),BLUE,''),(lambda x:math.log10(m.source_noise(10**x,20e-9,1e-15)*1e9),GRAY,'6 4')]
    if key=='bias_offset':return [(lambda x:math.log10(20e-9*10**x*1e6),BLUE,''),(lambda x:math.log10(1e-12*10**x*1e6),GRAY,'6 4')]
    return [(lambda x:6*(1-math.exp(-x/50)),BLUE,''),(lambda x:6,GRAY,'6 4')]


def plot(key,stage,small=False,begin=None):
    s=SPECS[key];xmin,xmax=s['xlim'];ymin,ymax=s['ylim']
    x0,y0,w,h=(55,178,250,94) if small else (90,320,550,155)
    size=18 if small else 20
    px=lambda x:x0+w*(x-xmin)/(xmax-xmin)
    py=lambda y:y0-h*(y-ymin)/(ymax-ymin)
    yield text(8 if small else 35,y0-h-17,s['ylabel'],size)
    for y in s['yticks']:yield line(x0,py(y),x0+w,py(y),GRAY,1,'2 5')+text(x0-7,py(y)+6,f'{y:g}',size,anchor='end')
    for x in s['xticks']:yield text(px(x),y0+26,f'{x:g}',size,anchor='middle')
    yield text(x0+w,y0+51,s['xlabel'],size,anchor='end')
    xs=[xmin+(xmax-xmin)*i/240 for i in range(241)]
    for i,(fn,color,dash) in enumerate(functions(key,stage)):
        points=[(x,fn(x)) for x in xs]
        if key=='integrator_cycle' and i==1:points=[(0,1),(.5,1),(.5,-1),(1,-1)]
        if key=='sc_charge' and i==0:points=[(0,0)]+[(x,y) for n in range(1,5) for x,y in [(n*10,n-1),(n*10,n)]]
        yield polyline([(px(x),py(y)) for x,y in points],color,dash=dash,begin=begin,identity=f'{key}-{stage}-{i}')
    if key in ['integrator_cycle','sc_charge']:
        legend='实线输出；虚线输入' if key=='integrator_cycle' else '实线周期累计；虚线平均'
        yield text(10 if small else 35,267 if small else 385,legend,size)
    fn=functions(key,stage)[0][0];x=s['markers'][stage]
    final=f'<circle cx="{px(x):g}" cy="{py(fn(x)):g}" r="5" fill="{INK}"/>'
    if begin is None:yield final
    else:
        path='M'+' L'.join(f'{px(xmin+(x-xmin)*i/80):g},{py(fn(xmin+(x-xmin)*i/80)):g}' for i in range(81))
        yield Graphic(f'<circle r="5" fill="{INK}" opacity="0"><set attributeName="opacity" to="1" begin="{begin:g}s"/><animateMotion path="{path}" begin="{begin:g}s" dur="2s" fill="freeze"/></circle>',final)


def scene(key):
    s=SPECS[key];tl=timeline(s['title'],s['steps'],s['boundary']);layers=[]
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
    boundary=s['boundary'];split=boundary.find('；')
    if split<0:split=boundary.find('，',30)
    if split<0:split=min(48,len(boundary))
    out += [text(26,880,boundary[:split+1],18),text(26,908,boundary[split+1:],18),'</svg>']
    return '\n'.join(out)


def metadata(key):
    s=SPECS[key];param=s['parameter']
    numbers=[dict(value=str(v),label='示意',reason='教学模型坐标或节拍编号，不是器件保证值；物理条件在正文中列明。') for v in sorted(set([0,1,2,3,4]+s['xticks']+s['yticks']))]
    extras={
        'resistor_mismatch':['0.01','0.5'],
        'tia_noise_gain':['15.9','399'],
        'tia_compensation':['0.6'],
        'bias_offset':['100'],
        'source_noise':['100'],
    }.get(key,[])
    numbers += [dict(value=v,label='示意',reason='正文模型的参数扫描取点，或拐点与交越频率按图示精度舍入；用于曲线比较而非器件保证。') for v in extras]
    return dict(id='ch12-'+key.replace('_','-')+'-v2',chapter=12,source='docs/p2-02-ch12.md',anchor=s['anchor'],type='A3' if param else 'A2',style_id='FA-029',layout_id='IG-015',purpose=s['title'],alt=s['title']+'。'+s['steps'][0]+s['steps'][-1],en_prompt='Four model-derived causal frames, physical axes, moving state marker and explicit boundary. '+key.replace('_',' '),scene=lambda:scene(key),storyboard=lambda:storyboard(key),parameters=[dict(name=param[0],values=param[1],unit=param[2])] if param else [],numbers=numbers)
