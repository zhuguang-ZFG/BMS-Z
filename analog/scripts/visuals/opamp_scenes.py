"""Four causal snapshots per op-amp model, drawn at final print text size."""
import math
from . import opamp_models as m
from .interface_models import timeline, INK, BLUE, RED, GREEN, GRAY
from .primitives import text, line, Graphic
from .plotting import polyline, print_header
from .render import Layer


SPECS={
 'compensation': dict(title='补偿电容同时约束带宽与斜率',anchor='6.1',
  boundary='固定跨导与可用充电电流；简化两级模型，不代表任意运放。',
  steps=['30 pF：GBW 1 MHz，SR 0.5 V/µs。','保持 gm 与 15 µA 电流，逐渐加大电容。','60 pF：带宽与斜率都降为原来一半。','稳定性还要查其余极点与负载，不能只看 Cc。'],
  mini=['初态：30 pF','扰动：增大 Cc','结果：60 pF','两项性能一起降低'],
  note=['1 MHz；0.5 V/µs','gm 与电流固定','0.5 MHz；0.25 V/µs','同轴为各自相对值'],
  xlabel='Cc / pF',ylabel='GBW、SR / 初值',xlim=(30,60),ylim=(0,1),xticks=[30,45,60],yticks=[0,.5,1],
  legend='两曲线重合：GBW/1 MHz = SR/(0.5 V/µs)'),
 'dc_error': dict(title='跟随器误差先定符号再相加',anchor='6.2',
  boundary='示意 Vos 为正、偏流流入正端；典型幅值不是误差保证。',
  steps=['设 Vos = +3 mV，偏流 20 nA 流入正端。','1 kΩ 源阻引起 −20 µV；100 kΩ 为 −2 mV。','有限开环增益 100000，1 V 信号约损失 10 µV。','本例误差会抵消；最坏预算另加各项绝对值。'],
  mini=['初态：低源阻','扰动：增加源阻','加入有限增益误差','有符号合成'],
  note=['偏流项为负','100 kΩ：−2 mV','1 V / 100000 = 10 µV','实线合成；虚线偏流'],
  xlabel='Rs / kΩ',ylabel='误差 / mV',xlim=(0,100),ylim=(-2.5,3.5),xticks=[0,50,100],yticks=[-2,0,3],
  legend='实线：合成误差；虚线：偏流项；点线：+3 mV'),
 'bias_balance': dict(title='平衡电阻抵消的是相关偏流',anchor='6.3',
  boundary='电流流入输入端为正；Rin 10 kΩ、Rf 90 kΩ、噪声增益 10。',
  steps=['反相放大器输入置零，先把正端直接接地。','负端偏流 20 nA 经 90 kΩ 产生 +1.8 mV。','正端串 9 kΩ 且两偏流相等：两项相抵。','正端 22 nA、负端 20 nA，残余为 −0.18 mV。'],
  mini=['初态：Rb = 0','误差：+1.8 mV','匹配：Rb = 9 kΩ','失配：22 / 20 nA'],
  note=['Vin=0，正端接地','Rf × I−','NG × Rb × I+ 抵消','虚线失配：−0.18 mV'],
  xlabel='Rb / kΩ',ylabel='输出误差 / mV',xlim=(0,9),ylim=(-.3,2),xticks=[0,4.5,9],yticks=[0,1,2],
  legend='实线：两端 20 nA；虚线：正端改为 22 nA'),
 'speed_envelope': dict(title='小信号幅频与大信号斜率分别核算',anchor='6.3',
  boundary='独立教学参数 GBW 0.7 MHz、NG 100、SR 0.5 V/µs、Vp 5 V。',
  steps=['小信号闭环极点 7 kHz，直流增益 100。','10 kHz 增益约 57.35，已经明显衰减。','若要求输出仍达 5 V 峰值，另算正弦最大斜率。','15.9 kHz 时所需斜率达到 SR；供电摆幅也须满足。'],
  mini=['初态：小信号模型','带宽先限制幅度','另设输出峰值 5 V','斜率比跨过 1'],
  note=['闭环极点 7 kHz','10 kHz：57.35 倍','虚线：所需斜率 / SR','15.9 kHz 达到上限'],
  xlabel='f / kHz',ylabel='增益/100；斜率/SR',xlim=(0,25),ylim=(0,1.6),xticks=[0,10,25],yticks=[0,1,1.5],
  legend='实线：幅频归一化；虚线：5 V 正弦所需斜率/SR'),
 'rejection': dict(title='抑制比先折算输入误差，再乘噪声增益',anchor='6.3',
  boundary='扰动频率处 CMRR、PSRR 均示意为 40 dB；先核对手册定义。',
  steps=['1 V 共模扰动除以 100，输入折算为 10 mV。','50 mV 电源纹波除以 100，输入折算为 0.5 mV。','两路误差各自经过该频率处的噪声增益。','NG 从 1 到 10：输出共模误差从 10 到 100 mV。'],
  mini=['共模：1 V → 10 mV','电源：50 → 0.5 mV','噪声增益继续放大','NG = 10 的结果'],
  note=['CMRR = 40 dB','PSRR = 40 dB','输入折算不等于输出','共模 100；电源 5 mV'],
  xlabel='噪声增益',ylabel='输出误差 / mV',xlim=(1,10),ylim=(0,100),xticks=[1,5,10],yticks=[0,50,100],
  legend='实线：共模扰动所致；虚线：电源纹波所致'),
 'noise_bandwidth': dict(title='噪声积分不能把截止频率当砖墙',anchor='6.3',
  boundary='仅算 40 nV/√Hz 白电压噪声；另计 1/f、电流噪声与电阻。',
  steps=['矩形带宽 20 kHz：白噪声为 5.66 µV RMS。','一阶低通在 fc 外还有噪声能量通过。','积分 |H|²：ENBW = πfc/2，约 31.42 kHz。','同为 fc 20 kHz，一阶结果 7.09 µV RMS。'],
  mini=['理想矩形带宽','改用一阶低通','累积噪声功率','积分上限趋于无穷'],
  note=['虚线：矩形 |H|²','实线：一阶 |H|²','实线 atan(f/fc)','6fc 外仍有噪声尾部'],
  xlabel='f / fc',ylabel='累计积分 / fc',xlim=(0,6),ylim=(0,1.7),xticks=[0,1,6],yticks=[0,1,1.57],
  legend='实线：一阶 atan(f/fc)；虚线：矩形 min(f/fc,1)'),
 'settling': dict(title='压摆斜坡与指数尾部必须连续交接',anchor='6.7',
  boundary='1 V 阶跃；一阶闭环极点 1 MHz、SR 0.5 V/µs，不含过冲。',
  steps=['只受线性带宽限制：0.1% 建立约 1.099 µs。','大阶跃先以 0.5 V/µs 斜率上升。','剩余误差达到 SRτ = 0.0796 V，约 1.841 µs 交接。','从交接点指数收尾，0.1% 建立约 2.537 µs。'],
  mini=['线性参考','压摆斜坡','斜率连续交接','进入 0.1% 误差带'],
  note=['虚线：仅线性模型','实线：限速模型','不是完整 2 µs 斜坡','总时长约 2.537 µs'],
  xlabel='时间 / µs',ylabel='输出 / V',xlim=(0,3),ylim=(0,1.1),xticks=[0,1,3],yticks=[0,.5,1],
  legend='实线：限速一阶；虚线：仅线性；圆点：当前读数'),
}


def curves(key,stage):
    if key=='compensation':
        return [(lambda x: m.compensation(x*1e-12)[0]/1e6, BLUE, '')]
    if key=='dc_error':
        return [(lambda x: m.follower_error(x*1000)*1000,BLUE,''),
                (lambda x:-.02*x,RED,'6 4'),(lambda x:3,GRAY,'2 4')]
    if key=='bias_balance':
        result=[(lambda x:m.balanced_error(x*1000)*1000,BLUE,'')]
        if stage==3: result.append((lambda x:m.balanced_error(x*1000,plus=22e-9)*1000,RED,'6 4'))
        return result
    if key=='speed_envelope':
        result=[(lambda x:m.closed_gain(x*1000)/100,BLUE,'')]
        if stage>=2: result.append((lambda x:m.sine_slope(x*1000)/.5e6,RED,'6 4'))
        return result
    if key=='rejection':
        result=[(lambda x:m.rejection_error(1,noise_gain=x)*1000,BLUE,'')]
        if stage>=1: result.append((lambda x:m.rejection_error(.05,noise_gain=x)*1000,RED,'6 4'))
        return result
    if key=='noise_bandwidth':
        if stage<2:
            result=[(lambda x:1 if x<=1 else 0,GRAY,'6 4')]
            if stage==1: result.insert(0,(lambda x:1/(1+x*x),BLUE,''))
            return result
        result=[(lambda x:min(x,1),GRAY,'6 4')]
        result.insert(0,(math.atan,BLUE,''))
        return result
    result=[(lambda x:1-math.exp(-2*math.pi*x),GRAY,'6 4')]
    if stage>=1: result.insert(0,(lambda x:m.step_response(x*1e-6),BLUE,''))
    return result


def plot(key,stage,*,small=False,begin=None):
    spec=SPECS[key]
    x0,y0,w,h=(56,180,250,102) if small else (100,347,520,175)
    size=18 if small else 20
    xmin,xmax=spec['xlim']; ymin,ymax=spec['ylim']
    px=lambda x:x0+w*(x-xmin)/(xmax-xmin)
    py=lambda y:y0-h*(y-ymin)/(ymax-ymin)
    ylabel='功率传递 |H|²' if key=='noise_bandwidth' and stage<2 else spec['ylabel']
    body=text(10 if small else 45,y0-h-17,ylabel,size)
    for y in spec['yticks']:
        body+=line(x0,py(y),x0+w,py(y),GRAY,1,'2 5')+text(x0-8,py(y)+6,f'{y:g}',size,anchor='end')
    for x in spec['xticks']:
        body+=text(px(x),y0+25,f'{x:g}',size,anchor='middle')
    body+=text(x0+w,y0+50,spec['xlabel'],size,anchor='end')
    xs=[xmin+(xmax-xmin)*i/100 for i in range(101)]
    yield body
    for index,(fn,col,dash) in enumerate(curves(key,stage)):
        points=[(px(x),py(fn(x))) for x in xs]
        if key=='noise_bandwidth' and stage<2 and dash:
            points=[(px(x),py(y)) for x,y in [(0,1),(1,1),(1,0),(6,0)]]
        yield polyline(points,col,dash=dash,begin=begin,identity=f'{key}-{stage}-{index}')
    # A physical-coordinate marker moves with the sweep, independent of the curve reveal.
    markers={ 'compensation':[30,45,60,60], 'dc_error':[1,100,100,100],
              'bias_balance':[0,0,9,9], 'speed_envelope':[7,10,15.9,15.9],
              'rejection':[1,1,5,10], 'noise_bandwidth':[1,1,3,6],
              'settling':[1.099,1,1.841,2.537] }
    xx=markers[key][stage]
    highlight=-1 if (key=='bias_balance' and stage==3) or (key=='speed_envelope' and stage>=2) else 0
    fn=curves(key,stage)[highlight][0]
    final=f'<circle cx="{px(xx):g}" cy="{py(fn(xx)):g}" r="5" fill="{INK}"/>'
    if begin is None:
        yield final
    else:
        pts=[(px(xmin+(xx-xmin)*i/50),py(fn(xmin+(xx-xmin)*i/50))) for i in range(51)]
        path='M'+' L'.join(f'{x:g},{y:g}' for x,y in pts)
        yield Graphic(f'<circle r="5" fill="{INK}" opacity="0"><set attributeName="opacity" to="1" begin="{begin:g}s"/><animateMotion path="{path}" begin="{begin:g}s" dur="2s" fill="freeze"/></circle>',final)


def scene(key):
    spec=SPECS[key]; tl=timeline(spec['title'],spec['steps'],'示意：'+spec['boundary'])
    layers=[]
    for i,b in enumerate(tl.beats):
        legend='实线：一阶功率传递；虚线：矩形功率传递' if key=='noise_bandwidth' and i<2 else spec['legend']
        layers.append(Layer(b.name,text(45,87,legend,18)))
        layers.extend(Layer(b.name,g) for g in plot(key,i,begin=b.start+.2 if i<3 else None))
        layers.append(Layer(b.name,text(45,117,spec['note'][i],20,INK)))
    return tl,layers


def storyboard(key):
    spec=SPECS[key]
    out=print_header(spec['title'],900,'示意：'+spec['boundary'])
    for i in range(4):
        x,y=18+(i%2)*350,65+(i//2)*300
        out += [f'<g data-storyboard-beat="{i+1}" transform="translate({x} {y})">',
                f'<rect width="334" height="284" rx="8" fill="none" stroke="{GRAY}"/>',
                text(10,27,f'{i+1}. '+spec['mini'][i],20),*plot(key,i,small=True),
                text(10,265,spec['note'][i],18),'</g>']
    for i,caption in enumerate(spec['steps']):
        out.append(text(26,704+32*i,f'{i+1}. '+caption,20))
    out += [text(26,865,'示意：'+spec['boundary'],18),'</svg>']
    return '\n'.join(out)


def metadata(key):
    s=SPECS[key]
    return dict(id='ch06-'+key.replace('_','-')+'-v2',chapter=6,source='docs/p1-07-ch6.md',
        anchor=s['anchor'],type='A2',style_id='FA-029',layout_id='IG-015',purpose=s['title'],
        alt=s['title']+'。'+' '.join(s['steps'])+' '+s['boundary'],
        en_prompt='Four causal snapshots with physical axes and analytical curves. '+key.replace('_',' ')+'. Print uses four redrawn panels at readable type size.',
        scene=lambda:scene(key),storyboard=lambda:storyboard(key),
        numbers=[dict(value=str(v),label='示意',reason='教学模型坐标刻度或序号，不是器件保证。') for v in sorted(set([1,2,3,4]+s['xticks']+s['yticks']))])
