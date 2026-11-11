"""Chapter 9: source-bound reference, thermal, dropout and charge-account scenes."""
import math
from . import regulator_models as m
from .interface_models import timeline, INK, BLUE, RED, GRAY
from .primitives import text, line, Graphic
from .plotting import polyline, print_header
from .render import Layer

SPECS={
 'bandgap_balance':dict(title='带隙的一阶补偿，要把电流密度比算进去',anchor='9.1',
  boundary='线性示意：25°C 的 VBE 为 0.65 V，斜率 −2 mV/°C，N=8。',
  steps=['先看 VBE：温度上升时，示意电压线性下降。','ΔVBE=(kT/q)ln8，乘合适比例后斜率相反。','令两条斜率相消，本例总电压为 1.2463 V。','一阶平直不等于实际零漂；曲率、修调和应力另计。'],
  mini=['CTAT 项','加权 PTAT 项','两项相加','模型与保证分开'],
  notes=['VBE 斜率 −2 mV/°C','加权斜率 +2 mV/°C','总值 1.2463 V','虚线和实线区分两项'],
  xlim=(-40,85),ylim=(0,1.4),xticks=[-40,25,85],yticks=[0,.7,1.4],xlabel='温度 / °C',ylabel='电压 / V',markers=[25,25,85,85]),
 'shunt_corners':dict(title='分流稳压，最小电流和最大功耗不在同一角',anchor='9.1',
  boundary='示意恒定 5.1 V 分流器，R=360 Ω，输入 10.8–13.2 V，负载 0–10 mA。',
  steps=['输入最低、负载最重：留给分流器约 5.83 mA。','输入升到 12 V，电阻电流分给负载和分流器。','输入最高、负载为零：分流电流约 22.5 mA。','此角分流器约 115 mW，电阻约 182 mW；分别查降额。'],
  mini=['最低输入满载','标称输入满载','最高输入空载','复核发热'],
  notes=['最小分流 5.83 mA','实线：负载 10 mA','虚线：负载为零','两条曲线相差 10 mA'],
  xlim=(10.8,13.2),ylim=(0,25),xticks=[10.8,12,13.2],yticks=[0,10,25],xlabel='输入 / V',ylabel='分流电流 / mA',markers=[10.8,12,13.2,13.2]),
 'tl431_bias':dict(title='TL431 偏流流入 REF，输出误差是加号',anchor='9.2',
  boundary='示意 Vref=2.5 V、Iref=2 µA，两电阻相等；忽略其余误差。',
  steps=['REF 节点：上电阻电流等于下电阻电流加偏流。','Vout=Vref(1+R1/R2)+Iref·R1，符号为正。','各 10 kΩ 时输出为 5.020 V，不是 4.980 V。','各 100 kΩ 时输出为 5.200 V；阻值上限由预算反推。'],
  mini=['节点电流方向','各取 1 kΩ','各取 10 kΩ','各取 100 kΩ'],
  notes=['Iref 流入 REF','误差 +2 mV','误差 +20 mV','误差 +200 mV'],
  xlim=(0,100),ylim=(0,210),xticks=[0,10,100],yticks=[0,100,200],xlabel='每只电阻 / kΩ',ylabel='输出误差 / mV',markers=[0,1,10,100]),
 'dropout_ripple':dict(title='稳压余量看输入谷值，不只看平均值',anchor='9.3',
  boundary='准静态示意：目标 3.3 V，负载 0.5 A，Ron=0.3 Ω，输入正弦 1 kHz。',
  steps=['输入为 3.5 V 加 0.2 V 正弦，平均值看似足够。','最高点 3.7 V，目标输出仍为 3.3 V。','输入谷值 3.3 V，扣去 0.15 V 压差只能输出 3.15 V。','谷值须覆盖输出加压差；实际还查动态 PSRR 与温度。'],
  mini=['初始输入 3.5 V','波峰有余量','波谷进入掉压','完整周期比较'],
  notes=['虚线输入；实线输出','输出受参考调节','输出谷值 3.15 V','不把本模型当 PSRR 曲线'],
  xlim=(0,2),ylim=(3.1,3.8),xticks=[0,1,2],yticks=[3.15,3.3,3.7],xlabel='时间 / ms',ylabel='电压 / V',markers=[0,.25,.75,1.75]),
 'thermal_budget':dict(title='热预算把地脚电流和环境温度一起算',anchor='9.3',
  boundary='示意 12→5 V、IQ=5 mA、环境 45°C；热阻 50 或 21°C/W。',
  steps=['输入功率减负载功率：P=(12−5)I+12·IQ。','300 mA 时耗散 2.16 W；50°C/W 给结温 153°C。','热阻降到 21°C/W，同样条件约为 90.4°C。','以 125°C 为设计上限，两路径限流约 220 / 536 mA。'],
  mini=['先把总功耗列齐','原路径 50°C/W','改善至 21°C/W','回算电流上限'],
  notes=['实线 50；虚线 21°C/W','300 mA：153°C','300 mA：90.4°C','上限是设计约束'],
  xlim=(0,.6),ylim=(40,270),xticks=[0,.3,.6],yticks=[45,125,225],xlabel='负载 / A',ylabel='结温 / °C',markers=[0,.3,.3,m.thermal_current(21)]),
 'light_load_efficiency':dict(title='轻载效率，要用完整输入功率作分母',anchor='9.3',
  boundary='示意 5→3.3 V；恒定 IQ 分别为 5 mA 和 50 µA，不对应特定型号。',
  steps=['忽略 IQ 的理想上限为 3.3/5，即 66%。','10 mA 负载、5 mA IQ：效率只有 44%。','同一负载改为 50 µA IQ，效率约 65.67%。','到 300 mA 负载，两者都接近上限；仍需核对热预算。'],
  mini=['低负载放大静态损耗','10 mA，IQ=5 mA','10 mA，IQ=50 µA','300 mA 对照'],
  notes=['虚线：较低静态电流','44%','65.67%','高负载接近 66%'],
  xlim=(.1,300),ylim=(0,70),xticks=[.1,10,300],yticks=[0,44,66],xlabel='负载 / mA（对数）',ylabel='效率 / %',markers=[.1,10,10,300]),
 'load_transient':dict(title='控制开始恢复时，电容仍可能继续放电',anchor='9.5',
  boundary='示意 ΔI=0.49 A、C=10 µF、ESR=50 mΩ；延迟 5 µs，恢复 τ=5 µs。',
  steps=['负载加阶跃时，电容电流先给出 −24.5 mV ESR 台阶。','5 µs 时电容电压降 245 mV，总偏差 −269.5 mV。','恢复开始后电流缺口仍在，最深跌落还在后面。','本例临界阻尼回稳；反向阶跃镜像过冲，须分别验上下限。'],
  mini=['负载刚增加','延迟段终点','恢复中的最低点','两个方向均检查'],
  notes=['忽略 ESL 与有限负载沿','总跌落尚未到最大','由电容电流积分求电压','虚线：反向阶跃'],
  xlim=(-2,40),ylim=(-.35,.35),xticks=[0,20,40],yticks=[-.3,0,.3],xlabel='时间 / µs',ylabel='输出偏差 / V',markers=[0,5,m.transient_minimum_time()*1e6,35]),
 'reference_pulses':dict(title='基准电容反复取走电荷，补电不完会累积偏差',anchor='9.1',
  boundary='示意每 10 µs 抽取 1 nC；缓冲等效 R=10 Ω、C=1 µF。',
  steps=['一次抽走 1 nC，1 µF 电容立刻下降 1 mV。','10 µs 后只恢复一部分，下一次又下降 1 mV。','经过多次采样，形成重复的补电与放电周期。','稳态最大偏差约 1.582 mV；平均补电电流为 100 µA。'],
  mini=['第一脉冲','第二脉冲','第四脉冲','稳定重复周期'],
  notes=['ΔV = Q / C','τ = RC = 10 µs','前一拍未完全恢复','最大偏差约 1.582 mV'],
  xlim=(0,60),ylim=(0,1.8),xticks=[0,30,60],yticks=[0,1,1.582],xlabel='时间 / µs',ylabel='基准下降量 / mV',markers=[0,10,30,60]),
}


def bias_circuit(small=False):
    out=text(105,65,'Vout',18,anchor='middle')+line(105,75,105,95,INK,2)
    out+='<path d="M95,95 H115 V130 H95 Z M95,190 H115 V225 H95 Z" fill="none" stroke="'+INK+'" stroke-width="2"/>'
    out+=line(105,130,105,190,INK,2)+line(105,225,105,245,INK,2)+line(90,245,120,245,INK,2)
    out+=line(105,160,270,160,INK,2)+text(135,118,'R1',18)+text(135,215,'R2',18)
    out+=text(262,145,'REF',18,anchor='end')+text(235,188,'2.5 V',18,anchor='middle')
    out+='<path d="M180,160 L170,155 M180,160 L170,165" fill="none" stroke="'+RED+'" stroke-width="2"/>'
    out+=text(203,220,'Iref →',18,RED)+f'<circle cx="105" cy="160" r="3" fill="{INK}"/>'
    return out if small else '<g transform="translate(70 0) scale(1.55)">'+out+'</g>'


def curves(key,stage):
    if key=='bandgap_balance':
        all_curves=[(lambda x:m.bandgap(x)[0],BLUE,''),(lambda x:m.bandgap(x)[1],GRAY,'6 4'),(lambda x:m.bandgap(x)[2],RED,'')]
        return all_curves[:stage+1] if stage<2 else all_curves
    if key=='shunt_corners':return [(lambda x:m.shunt(x,.01)[0]*1000,BLUE,''),(lambda x:m.shunt(x,0)[0]*1000,GRAY,'6 4')]
    if key=='tl431_bias':return [(lambda x:2*x,BLUE,'')]
    if key=='dropout_ripple':return [(lambda x:m.dropout(x*1e-3)[1],BLUE,''),(lambda x:m.dropout(x*1e-3)[0],GRAY,'6 4')]
    if key=='thermal_budget':return [(lambda x:m.junction(x,50),BLUE,''),(lambda x:m.junction(x,21),GRAY,'6 4')]
    if key=='light_load_efficiency':return [(lambda x:m.efficiency(x*1e-3)*100,BLUE,''),(lambda x:m.efficiency(x*1e-3,iq=50e-6)*100,GRAY,'6 4')]
    if key=='load_transient':
        result=[(lambda x:m.transient(x*1e-6)[2],BLUE,'')]
        if stage==3:result.append((lambda x:m.transient(x*1e-6,delta=-.49)[2],GRAY,'6 4'))
        return result
    return [(lambda x:m.pulse_deficit(x*1e-6)*1000,BLUE,'')]


def plot(key,stage,small=False,begin=None):
    if key=='tl431_bias' and stage==0:
        yield bias_circuit(small);return
    s=SPECS[key]
    x0,y0,w,h=(65,180,240,95) if small else (100,345,520,175)
    xmin,xmax=s['xlim'];ymin,ymax=s['ylim'];size=18 if small else 20
    logx=key=='light_load_efficiency'
    px=lambda x:x0+w*(math.log(x/xmin)/math.log(xmax/xmin) if logx else (x-xmin)/(xmax-xmin))
    py=lambda y:y0-h*(y-ymin)/(ymax-ymin)
    yield text(8 if small else 40,y0-h-16,s['ylabel'],size)
    for y in s['yticks']:yield line(x0,py(y),x0+w,py(y),GRAY,1,'2 5')+text(x0-8,py(y)+6,f'{y:g}',size,anchor='end')
    for x in s['xticks']:yield text(px(x),y0+26,f'{x:g}',size,anchor='middle')
    yield text(x0+w,y0+49,s['xlabel'],size,anchor='end')
    functions=curves(key,stage)
    for index,(fn,col,dash) in enumerate(functions):
        xs=[xmin*(xmax/xmin)**(i/600) if logx else xmin+(xmax-xmin)*i/600 for i in range(601)]
        if key=='reference_pulses':
            xs=sorted(set(xs+[i*10-1e-7 for i in range(1,7)]))
        if key=='load_transient':xs=sorted(set(xs+[-1e-7,0,5,m.transient_minimum_time()*1e6]))
        yield polyline([(px(x),py(fn(x))) for x in xs],col,dash=dash,begin=begin,identity=f'{key}-{stage}-{index}')
    xx=s['markers'][stage]
    chosen=2 if key=='bandgap_balance' and stage>=2 else 1 if (key=='bandgap_balance' and stage==1) or (key=='shunt_corners' and stage>=2) or (key=='thermal_budget' and stage>=2) or (key=='light_load_efficiency' and stage==2) else 0
    fn=functions[chosen][0]
    final=f'<circle cx="{px(xx):g}" cy="{py(fn(xx)):g}" r="5" fill="{INK}"/>'
    if begin is None:yield final
    else:
        # Move the pointer along the model, rather than only fading a whole chart.
        pts=[(px(xmin+(xx-xmin)*i/80),py(fn(xmin+(xx-xmin)*i/80))) for i in range(81)]
        path='M'+' L'.join(f'{x:g},{y:g}' for x,y in pts)
        yield Graphic(f'<circle r="5" fill="{INK}" opacity="0"><set attributeName="opacity" to="1" begin="{begin:g}s"/><animateMotion path="{path}" begin="{begin:g}s" dur="2s" fill="freeze"/></circle>',final)


def scene(key):
    s=SPECS[key];tl=timeline(s['title'],s['steps'],'示意：'+s['boundary']);layers=[]
    for i,b in enumerate(tl.beats):
        layers.append(Layer(b.name,text(40,117,s['notes'][i],20)))
        layers.extend(Layer(b.name,g) for g in plot(key,i,begin=b.start+.2 if i<3 else None))
    return tl,layers


def storyboard(key):
    s=SPECS[key];out=print_header(s['title'],910,s['boundary'])
    for i in range(4):
        x,y=18+(i%2)*350,65+(i//2)*300
        out += [f'<g data-storyboard-beat="{i+1}" transform="translate({x} {y})">',
                f'<rect width="334" height="284" rx="8" fill="none" stroke="{GRAY}"/>',text(10,27,f'{i+1}. '+s['mini'][i],20),
                *plot(key,i,small=True),text(10,271,s['notes'][i],18),'</g>']
    for i,caption in enumerate(s['steps']):out.append(text(26,704+32*i,f'{i+1}. '+caption,20))
    out += [text(26,870,'示意：'+s['boundary'],18),'</svg>']
    return '\n'.join(out)


def metadata(key):
    s=SPECS[key]
    return dict(id='ch09-'+key.replace('_','-')+'-v2',chapter=9,source='docs/p1-10-ch9.md',anchor=s['anchor'],
        type='A2',style_id='FA-029',layout_id='IG-015',purpose=s['title'],
        alt=s['title']+'。'+' '.join(s['steps'])+' '+s['boundary'],
        en_prompt='Four causal snapshots, physical axes, model equations and explicit device boundaries. '+key.replace('_',' '),
        scene=lambda:scene(key),storyboard=lambda:storyboard(key),
        numbers=[dict(value=str(v),label='示意',reason='模型坐标刻度与节拍序号，不是器件规格。') for v in sorted(set([0,1,2,3,4]+s['xticks']+s['yticks']))])
