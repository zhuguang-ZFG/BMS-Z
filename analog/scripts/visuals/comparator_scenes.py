"""Comparator timing, tolerance, memory and logic with four printable snapshots."""
import math
from . import comparator_models as m
from .interface_models import timeline, INK, BLUE, RED, GRAY, GREEN
from .primitives import text, line, directed_arrow, Graphic
from .plotting import polyline, print_header
from .render import Layer

SPECS={
 'release_timing':dict(title='响应时间的终点，先看手册怎样定义',anchor='7.1',
  boundary='独立 RC 示意：5 V、4.7 kΩ、50 pF，1 µs 时输出管释放。',
  steps=['输出管在示意的 1 µs 释放，随后才按 RC 上升。','越过 1.4 V 约在 1.077 µs；不同于 50% 终点。','50% 约 1.163 µs，70% 约 1.283 µs。','10%→90% 耗 0.516 µs；不能重复加进已测响应。'],
  mini=['输出管释放','输出越过 1.4 V','改看 50% 阈值','再看 70% 阈值'],
  notes=['τ = 0.235 µs','1.4 V：1.077 µs','2.5 V：1.163 µs','3.5 V：1.283 µs'],
  xlim=(0,2),ylim=(0,5),xticks=[0,1,2],yticks=[0,2.5,5],xlabel='时间 / µs',ylabel='输出 / V'),
 'threshold_tolerance':dict(title='电阻比差 2%，分压电压不一定差 2%',anchor='7.2',
  boundary='5 V 精确供电；100 kΩ 等值分压，两电阻反向取容差极限。',
  steps=['两只标称相等的电阻，基准为 2.5 V。','上电阻 −1%、下电阻 +1%：得到 2.525 V。','反向极限给 2.475 V，基准误差为 ±25 mV。','5 mV 失调与 1.225 mV 偏流仅作量级比较，另查保证。'],
  mini=['两电阻均标称','下电阻偏高','下电阻偏低','输入误差各自核算'],
  notes=['初始偏差为零','99 kΩ / 101 kΩ','101 kΩ / 99 kΩ','25 / 5 / 1.225 mV'],
  xlim=(-1,1),ylim=(-30,30),xticks=[-1,0,1],yticks=[-25,0,25],xlabel='下电阻偏差 / %',ylabel='基准误差 / mV'),
 'window_logic':dict(title='窗口内放行，要先接对两路比较极性',anchor='7.2',
  boundary='电池减半分压；理想门限 3.0 / 3.6 V，等于门限时不保证状态。',
  steps=['欠压路：被测电压进正端，1.5 V 基准进负端。','过压路：1.8 V 基准进正端，被测电压进负端。','欠压或过压时，任一路输出管都能拉低公共节点。','只有两路都松手，上拉才能给出窗口内的高电平。'],
  mini=['欠压：电池 2.8 V','窗内：电池 3.2 V','过压：电池 3.8 V','回到窗内 3.2 V'],
  notes=['A 拉低；B 松手','两路松手：高','A 松手；B 拉低','共享上拉；逻辑线与']),
 'feedback_loading':dict(title='开集电极的高电平也会被反馈网络拉低',anchor='7.3',
  boundary='5 V 上拉，2.5 V 理想基准，Rref 10 kΩ、Rf 100 kΩ、VOL 0.2 V。',
  steps=['先把上拉与反馈网络一起列节点电流方程。','Rp=4.7 kΩ 时 VOH≈4.898 V，上阈值约 2.718 V。','Rp=47 kΩ 时 VOH≈4.252 V，上阈值约 2.659 V。','下阈值为 2.291 V；两态分别求解才得到实际窗口。'],
  mini=['高态输出管截止','Rp = 4.7 kΩ','Rp = 47 kΩ','回代两个阈值'],
  notes=['两节点分别列 KCL','VOH = 4.898 V','VOH = 4.252 V','下阈值 2.291 V'],
  xlim=(0,47),ylim=(2.6,2.75),xticks=[0,20,47],yticks=[2.6,2.7,2.75],xlabel='Rp / kΩ',ylabel='上阈值 / V'),
 'oscillator_delay':dict(title='传播等待期间，电容还在继续充放电',anchor='7.3',
  boundary='理想推挽；阈值 1/4、3/4 电源，RC=10 µs，双向延迟 1.3 µs。',
  steps=['无延迟时 T=2RC ln3，约 21.972 µs。','越过门限后再等 1.3 µs，电容继续向电源轨运动。','实际峰谷越过 3/4 与 1/4，下半周期路程也改变。','T=2[d+RC ln(4−exp(−d/RC))]，不能只加 2d。'],
  mini=['无延迟参考','加入翻转等待','峰谷超出阈值','完整周期复核'],
  notes=['虚线：无延迟','实线：有延迟','阈值不等于实际峰谷','定量周期由同一模型算'],
  xlim=(0,50),ylim=(0,1),xticks=[0,25,50],yticks=[0,.25,.75,1],xlabel='时间 / µs',ylabel='电容电压 / 电源'),
 'glitch_memory':dict(title='毛刺会不会触发，要看离当前门限多远',anchor='7.5',
  boundary='反相迟滞理想状态模型；上阈 2.727 V、下阈 2.273 V，初始高。',
  steps=['输入基线 2.4 V；200 mV 毛刺顶到 2.6 V。','300 mV 毛刺到 2.7 V，仍比上阈值低约 27 mV。','400 mV 毛刺到 2.8 V，输出翻低且回到基线仍保持。','输入再跌到下阈以下才翻高；窗口不是任意毛刺保证。'],
  mini=['200 mV 毛刺','300 mV 毛刺','400 mV 毛刺','跌破下门限复位'],
  notes=['离上门限约 127 mV','余量只剩约 27 mV','回到 2.4 V 仍保持低','滞回：有前态记忆'],
  xlim=(0,12),ylim=(2.1,2.9),xticks=[0,6,12],yticks=[2.2,2.5,2.8],xlabel='时间 / ms',ylabel='输入 / V'),
 'hysteresis_timing':dict(title='相对中点的延时，只跨半个对称窗口',anchor='7.5',
  boundary='初态输出高；输入由 2.3 V 以 1 mV/s 上行，忽略传播与 RC 延迟。',
  steps=['无迟滞参考门限 2.5 V，输入在 200 s 到达。','迟滞上阈值 2.727 V，在约 427.3 s 才翻转。','相对 2.5 V 的推迟是 227.3 s，不是 454.5 s。','只有拿下阈值作起点，时间差才对应整个窗口。'],
  mini=['从 2.3 V 上行','越过中点 2.5 V','到达上阈值','量两时刻的距离'],
  notes=['线性慢斜坡','参考时刻 200 s','实际时刻 427.3 s','Δt = ΔV / 输入斜率'],
  xlim=(0,500),ylim=(2.2,2.9),xticks=[0,200,500],yticks=[2.3,2.5,2.727],xlabel='时间 / s',ylabel='输入 / V'),
}


def chart(key,stage,small=False,begin=None):
    if key=='window_logic':
        yield logic(stage,small)
        return
    if key=='feedback_loading' and stage==0:
        yield feedback_circuit(small)
        return
    spec=SPECS[key]
    x0,y0,w,h=(60,175,245,92) if small else (100,320 if key=='glitch_memory' else 348,520,145 if key=='glitch_memory' else 175)
    size=18 if small else 20
    xmin,xmax=spec['xlim'];ymin,ymax=spec['ylim']
    px=lambda x:x0+w*(x-xmin)/(xmax-xmin)
    py=lambda y:y0-h*(y-ymin)/(ymax-ymin)
    out=text(8 if small else 40,y0-h-16,spec['ylabel'],size)
    for y in spec['yticks']:out+=line(x0,py(y),x0+w,py(y),GRAY,1,'2 5')+text(x0-8,py(y)+6,f'{y:g}',size,anchor='end')
    for x in spec['xticks']:out+=text(px(x),y0+25,f'{x:g}',size,anchor='middle')
    out+=text(x0+w,y0+48,spec['xlabel'],size,anchor='end')
    functions=[];markers=[]
    if key=='release_timing':
        functions=[(lambda x:m.release_voltage(x*1e-6),BLUE,'')]
        voltage=[0,1.4,2.5,3.5][stage];xx=m.release_crossing(voltage)*1e6
        markers=[(xx,voltage)]
        out+=line(px(xx),py(0),px(xx),py(voltage),RED,2,'4 4')
    elif key=='threshold_tolerance':
        functions=[(lambda x:m.opposing_error(x/100)*1000,BLUE,'')]
        xx=[0,1,-1,1][stage];markers=[(xx,functions[0][0](xx))]
    elif key=='feedback_loading':
        functions=[(lambda x:m.loaded_thresholds(max(x,.00001)*1000)[1],BLUE,'')]
        xx=[.00001,4.7,47,47][stage];markers=[(xx,functions[0][0](xx))]
    elif key=='oscillator_delay':
        functions=[(lambda x:m.oscillator_voltage(x*1e-6,delay=0),GRAY,'6 4')]
        if stage>=1:functions.insert(0,(lambda x:m.oscillator_voltage(x*1e-6),BLUE,''))
        xx=([m.oscillator_period(delay=0)/2,m.oscillator_period()/2-1.3e-6,m.oscillator_period()/2,m.oscillator_period()][stage])*1e6
        markers=[(xx,functions[0][0](xx))]
    elif key=='glitch_memory':
        functions=[(m.disturbance,BLUE,'')]
        for val,dash in [(30/11,'6 4'),(25/11,'2 4')]:out+=line(px(0),py(val),px(12),py(val),RED,2,dash)
        xx=[2,5,8,11][stage];markers=[(xx,m.disturbance(xx))]
        xs=[i/100 for i in range(1201)];ys=m.hysteresis_trace([m.disturbance(x) for x in xs])
        # One explicit output strip; its y position does not share the voltage axis.
        yy=248 if small else 395
        out+=text(8 if small else 40,yy+5,'OUT',18)
        out+=polyline([(px(x),yy-(16 if high else 0)) for x,high in zip(xs,ys)],INK)
    else:
        functions=[(lambda x:2.3+.001*x,BLUE,'')]
        xx=[0,200,m.ramp_crossing(30/11),m.ramp_crossing(30/11)][stage]
        markers=[(xx,functions[0][0](xx))]
        for val in [2.5,30/11]:out+=line(px(m.ramp_crossing(val)),py(2.3),px(m.ramp_crossing(val)),py(val),GRAY,2,'4 4')
    yield out
    for i,(fn,col,dash) in enumerate(functions):
        xs=[xmin+(xmax-xmin)*i/500 for i in range(501)]
        yield polyline([(px(x),py(fn(x))) for x in xs],col,dash=dash,begin=begin,identity=f'{key}-{stage}-{i}')
    for xx,yy in markers:
        final=f'<circle cx="{px(xx):g}" cy="{py(yy):g}" r="5" fill="{INK}"/>'
        if begin is None:yield final
        else:
            animated=f'<g opacity="0">{final}<animate attributeName="opacity" from="0" to="1" begin="{begin:g}s" dur=".4s" fill="freeze"/></g>'
            yield Graphic(animated,final)


def logic(stage,small=False):
    voltage=[2.8,3.2,3.8,3.2][stage]
    a,b,high=m.window_state(voltage)
    x=145 if small else 310
    ys=[100,188] if small else [175,285]
    out=''
    # The comparator with V+ < V− turns on its output sink.
    for i,(y,sink) in enumerate(zip(ys,[a,b])):
        out+=f'<path d="M{x},{y-28} L{x},{y+28} L{x+45},{y} Z" fill="none" stroke="{INK}" stroke-width="2"/>'
        plus,minus=(f'{voltage/2:g}','1.5') if i==0 else ('1.8',f'{voltage/2:g}')
        out+=text(x-10,y-12,plus+' V',18,anchor='end')+text(x-10,y+22,minus+' V',18,anchor='end')
        out+=text(x+4,y-7,'+',18)+text(x+4,y+22,'−',18)
        out+=line(x+45,y,x+85,y,INK,2)+text(x+100,y+5,'拉低' if sink else '松手',18,RED if sink else GREEN)
    out+=line(x+85,ys[0],x+85,ys[1],INK,2)
    top=ys[0]-40
    out+=line(x+85,ys[0],x+85,top+23,INK,2)
    out+=f'<rect x="{x+79}" y="{top+5}" width="12" height="18" fill="none" stroke="{INK}" stroke-width="2"/>'
    out+=line(x+85,top+5,x+85,top-5,INK,2)
    out+=text(x+103,top+20,'Rp',18)+text(x+85,top-10,'VPU',18,anchor='middle')
    mid=(ys[0]+ys[1])/2
    out+=line(x+85,mid,x+125,mid,INK,2)+text(x+100,mid+25,'H' if high else 'L',22,INK)
    out+=text(14 if small else 70,50 if small else 95,f'电池 {voltage:g} V → 分压 {voltage/2:g} V',18 if small else 22)
    return out


def feedback_circuit(small=False):
    """High-state two-node network: V+ and VOH, with an explicit pull-up."""
    out=text(300,54,'5 V',18,anchor='middle')
    out+=line(300,62,300,75,INK,2)
    out+='<rect x="294" y="75" width="12" height="25" fill="none" stroke="'+INK+'" stroke-width="2"/>'
    out+=text(278,95,'Rp',18,anchor='end')+line(300,100,300,190,INK,2)
    out+=line(150,120,180,120,INK,2)+line(220,120,300,120,INK,2)
    out+='<rect x="180" y="114" width="40" height="12" fill="none" stroke="'+INK+'" stroke-width="2"/>'
    out+=text(200,107,'Rf 100 kΩ',18,anchor='middle')+line(150,120,150,175,INK,2)
    out+=text(12,153,'2.5 V',18)+line(20,175,60,175,INK,2)+line(100,175,220,175,INK,2)
    out+='<rect x="60" y="169" width="40" height="12" fill="none" stroke="'+INK+'" stroke-width="2"/>'
    out+=text(80,202,'10 kΩ',18,anchor='middle')+text(150,164,'V+',18,anchor='middle')
    out+='<path d="M220,155 L220,225 L265,190 Z" fill="none" stroke="'+INK+'" stroke-width="2"/>'
    out+=text(224,181,'+',18)+text(224,216,'−',18)
    out+=line(155,210,220,210,INK,2)+text(153,236,'Vin',18)
    out+=line(265,190,320,190,INK,2)+text(300,217,'VOH',18,anchor='middle')
    for x,y in [(150,175),(300,120)]:out+=f'<circle cx="{x}" cy="{y}" r="3" fill="{INK}"/>'
    return out if small else '<g transform="translate(80 5) scale(1.65)">'+out+'</g>'


def scene(key):
    spec=SPECS[key];tl=timeline(spec['title'],spec['steps'],'示意：'+spec['boundary'])
    layers=[]
    for i,b in enumerate(tl.beats):
        layers.extend(Layer(b.name,g) for g in chart(key,i,begin=b.start+.2 if i<3 else None))
        layers.append(Layer(b.name,text(40,125,spec['notes'][i],20)))
    return tl,layers


def storyboard(key):
    spec=SPECS[key];out=print_header(spec['title'],910,spec['boundary'])
    for i in range(4):
        x,y=18+(i%2)*350,65+(i//2)*300
        out += [f'<g data-storyboard-beat="{i+1}" transform="translate({x} {y})">',
                f'<rect width="334" height="284" rx="8" fill="none" stroke="{GRAY}"/>',text(10,27,f'{i+1}. '+spec['mini'][i],20),
                *chart(key,i,small=True),text(10,274,spec['notes'][i],18),'</g>']
    for i,caption in enumerate(spec['steps']):out.append(text(26,704+32*i,f'{i+1}. '+caption,20))
    out += [text(26,870,'示意：'+spec['boundary'],18),'</svg>']
    return '\n'.join(out)


def metadata(key):
    spec=SPECS[key]
    ticks=set([0,1,2,3,4]+spec.get('xticks',[])+spec.get('yticks',[]))
    if key=='release_timing':ticks.update([.235,3.5])
    return dict(id='ch07-'+key.replace('_','-')+'-v2',chapter=7,source='docs/p1-08-ch7.md',anchor=spec['anchor'],
        type='A1' if key=='window_logic' else 'A2',style_id='FA-029',layout_id='IG-013' if key=='window_logic' else 'IG-015',
        purpose=spec['title'],alt=spec['title']+'。'+' '.join(spec['steps'])+' '+spec['boundary'],
        en_prompt='Four causal snapshots with exact comparator polarity, physical units and explicit model boundary. '+key.replace('_',' '),
        scene=lambda:scene(key),storyboard=lambda:storyboard(key),
        numbers=[dict(value=str(v),label='示意',reason='教学模型坐标刻度和节拍序号，不是器件额定。') for v in sorted(ticks)])
