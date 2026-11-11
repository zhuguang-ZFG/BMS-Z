"""Timer narratives with state changes, continuous models and redrawn print frames."""
import math
from . import timer_models as m
from .interface_models import timeline, INK, BLUE, RED, GRAY
from .primitives import text, line, Graphic
from .plotting import polyline, print_header
from .render import Layer

SPECS={
 'threshold_memory':dict(title='RESET、TRIG、THRES 按优先级改变状态',anchor='10.1',type='A1',
  boundary='示意 9 V、标称 3/6 V 门限；不在相等边界判定保证状态。',
  steps=['RESET 有效时，即使 TRIG 低，输出也保持低。','释放 RESET；TRIG 低于 3 V，优先置位输出。','TRIG 与 THRES 都在非动作区，锁存器保留高态。','TRIG 已释放，THRES 超过 6 V，输出复位并放电。'],
  mini=['复位优先','触发置位','中间区记忆','阈值复位'],notes=['OUT 低，DISCH 导通','TRIG 优先于 THRES','保持，不是重新计算','OUT 低，DISCH 导通']),
 'astable_cycle':dict(title='电容连续变化，输出在门限处切换',anchor='10.4',type='A1',
  boundary='示意 9 V、RA=1 kΩ、RB=6.8 kΩ、C=100 nF，理想开关。',
  steps=['稳态从 3 V 起，RA 与 RB 一起给电容充电。','约 540.65 µs 到 6 V，输出转低、放电管导通。','经 RB 放电约 471.34 µs 后回到 3 V。','周期约 1.012 ms；输出高占 53.42%，并非对称。'],
  mini=['充电路径','达到上阈','达到下阈','连续周期'],notes=['OUT 高时放电管截止','电容电压连续','放电只经 RB','下轨单独表示 OUT'],
  xlim=(0,2.1),ylim=(2.8,6.2),xticks=[0,1,2],yticks=[3,6],xlabel='时间 / ms',ylabel='电容 / V',markers=[.25,.5406548,1.0119949,2.02]),
 'first_pulse':dict(title='首次从零起充，比稳态高脉冲更长',anchor='10.2',type='A2',
  boundary='示意 9 V、RA+RB=7.8 kΩ、C=100 nF；电源已经稳定。',
  steps=['首次从 0 V 起充，目标电压仍是 9 V。','稳态从 3 V 起充，到 6 V 约 540.65 µs。','首次到 6 V 则需约 856.92 µs。','比值 ln3/ln2≈1.585；残留电荷和慢上电会改变首拍。'],
  mini=['两种起点','稳态到顶','首次到顶','比较时间'],notes=['实线首拍；虚线稳态','曲线在门限处结束','不是固定多加一段延迟','不把零初值当通用保证'],
  xlim=(0,1),ylim=(0,6.5),xticks=[0,.5,1],yticks=[0,3,6],xlabel='时间 / ms',ylabel='电容 / V',markers=[0,.5406548,.8569176,.8569176]),
 'discharge_floor':dict(title='放电低点抬高，放到下门限反而更慢',anchor='10.3',type='A3',
  boundary='示意 9 V、RB=6.8 kΩ、C=100 nF；固定放电压降 VD。',
  steps=['VD=0 时，从 6 V 放到 3 V 需 471.34 µs。','VD=0.15 V 时，放电目标抬高，电流减小。','VD 继续增大，达到相同 3 V 门限需要更久。','VD 接近下阈时无法正常复位；不是压降越大频率越高。'],
  mini=['理想地电位','增加放电压降','相同门限更慢','回到可达条件'],notes=['上、下阈值不变','电流取 (VC−VD)/RB','实线：低电平持续时间','必须有 VD < 下门限'],
  xlim=(0,2),ylim=(400,1000),xticks=[0,1,2],yticks=[500,750,1000],xlabel='放电低点 VD / V',ylabel='低电平 / µs',markers=[0,.15,1,2]),
 'diode_duty':dict(title='二极管有压降，等电阻也不等于 50%',anchor='10.4',type='A3',
  boundary='示意 5 V、RA=RB=10 kΩ、C=100 nF；VD=0、恒定 VF。',
  steps=['理想二极管绕过 RB，等电阻给出对称充放时间。','VF=0.3 V 时，充电目标降到 4.7 V，高段变长。','VF=0.6 V 时，门限仍不变，充电目标只有 4.4 V。','这段扫描中二极管一直导通；压降更大需分段求解。'],
  mini=['零压降极限','0.3 V 压降','0.6 V 压降','核对导通条件'],notes=['输出高占空比 50%','不改变上下阈值','高占空比约 57.58%','扫至 0.8 V 仍满足条件'],
  xlim=(0,.8),ylim=(48,64),xticks=[0,.4,.8],yticks=[50,55,60],xlabel='二极管 VF / V',ylabel='高占空比 / %',markers=[0,.3,.6,.8]),
 'output_feedback':dict(title='从输出脚充电，负载会改变计时时间',anchor='10.4',type='A3',
  boundary='示意 5 V、R=72 kΩ、C=10 nF、VOL=0.1 V；VOH 单独扫描。',
  steps=['VOH=5 V 时，高段约 499 µs；低段由 VOL 决定。','VOH 降到 4 V，充电电流减小，高段变长。','VOH 接近 3.333 V 上阈，高段迅速增长。','VOH 不高于上阈便无法起振，等时间常数不保证对称。'],
  mini=['高电平贴近电源','负载拉低 VOH','接近上阈','确认可达性'],notes=['实线高段；虚线低段','VOL 不随本次扫描变化','不是脉宽变短','VOH > 3.333 V 才可达'],
  xlim=(3.4,5),ylim=(0,2.5),xticks=[3.4,4,5],yticks=[0,1,2],xlabel='输出 VOH / V',ylabel='持续时间 / ms',markers=[5,4,3.4,3.4]),
 'control_sweep':dict(title='CTRL 改变门限，频率响应不是直线',anchor='10.4',type='A3',
  boundary='示意 9 V、RA=1 kΩ、RB=6.8 kΩ、C=100 nF，理想放电。',
  steps=['CTRL=3 V 时，下阈为 1.5 V，充电行程较短。','升到 4.5 V，充电时间增长，频率下降。','CTRL=6 V 时，频率约 988.1 Hz。','趋近电源时充电更慢；理想低段仍为 ln2·RB·C。'],
  mini=['较低门限','增加控制电压','标称工作点','接近电源'],notes=['下阈 = CTRL/2','频率非线性下降','实线为本例计算值','实物再查控制范围与驱动'],
  xlim=(3,8),ylim=(400,1700),xticks=[3,6,8],yticks=[500,1000,1500],xlabel='CTRL / V',ylabel='频率 / Hz',markers=[3,4.5,6,8]),
 'monostable_leakage':dict(title='漏电先拉长脉宽，过大时永远达不到上阈',anchor='10.5',type='A3',
  boundary='示意 9 V、R=560 kΩ、C=47 µF；恒流漏电流出电容节点。',
  steps=['无漏电，从零充到 6 V 的脉宽约 28.92 s。','漏电 1 µA，目标变为 8.44 V，脉宽约 32.66 s。','漏电继续增大，末段充电电流越来越小。','达到约 5.357 µA 时，目标不高于上阈，不再结束。'],
  mini=['零漏电参考','1 µA 漏电','接近电流预算','检查终点可达'],notes=['终点为 2/3 VCC','一微安也不能忽略','长定时不是无限加大 R','极限 I = (VCC−VH)/R'],
  xlim=(0,5.2),ylim=(0,110),xticks=[0,1,5],yticks=[0,30,90],xlabel='漏电 / µA',ylabel='脉宽 / s',markers=[0,1,4,5.2]),
 'recovery_gap':dict(title='下一次触发，要继承电容尚未放完的电压',anchor='10.5',type='A2',
  boundary='示意 5 V、R=100 kΩ、C=10 µF；放电等效 100 Ω，保留电源馈入。',
  steps=['输出回低后电容经放电路径衰减，不能瞬间清零。','恢复仅 1 ms 后仍有约 1.228 V，下一拍被缩短。','等 5 ms 后残压约 27.3 mV，下一拍约 1.093 s。','图的后两拍切换为下一拍脉宽；用允许误差反推最小间隔。'],
  mini=['先看恢复残压','短间隔重触发','再看下一拍时间','按误差留恢复'],notes=['放电期间 R 仍接电源','残压由完整分流网络决定','虚线为从零计时 1.099 s','不以固定百微秒作保证'],
  xlim=(0,6),ylim=(0,3.5),xticks=[0,1,5],yticks=[0,1.5,3],xlabel='恢复间隔 / ms',ylabel='残压 / V',markers=[0,1,5,6]),
 'reset_ramp':dict(title='RESET 门限低，RC 常数不是复位保持时间',anchor='10.5',type='A2',
  boundary='示意理想高阻 RESET：12 V、100 kΩ、4.7 µF；真实脚电流另计。',
  steps=['RC=0.47 s，但复位门限并不是 63.2% 的电源。','越过 0.3 V 只需约 11.9 ms。','越过 0.7 V 约 28.3 ms，越过 1 V 约 40.9 ms。','双极 RESET 不是理想高阻；精确延时还须考虑脚电流与慢沿。'],
  mini=['建立理想充电模型','低端门限','典型门限','高端门限与实物'],notes=['只画前 50 ms','不是 0.47 s 延时','阈值区间影响释放时刻','需要保证时用监控器'],
  xlim=(0,50),ylim=(0,1.3),xticks=[0,25,50],yticks=[0,.7,1],xlabel='时间 / ms',ylabel='RESET / V',markers=[0,m.crossing(0,12,.3,.47)*1000,m.crossing(0,12,.7,.47)*1000,m.crossing(0,12,1,.47)*1000]),
}


def functions(key,stage):
    if key=='astable_cycle':return [(lambda x:m.cycle(x/1000)[0],BLUE,'')]
    if key=='first_pulse':return [(lambda x:min(6,m.first_charge(x/1000)),BLUE,''),(lambda x:min(6,m.first_charge(x/1000,3)),GRAY,'6 4')]
    if key=='discharge_floor':return [(lambda x:m.astable(floor=x)[1]*1e6,BLUE,'')]
    if key=='diode_duty':return [(lambda x:100*m.diode_times(x)[0]/sum(m.diode_times(x)),BLUE,'')]
    if key=='output_feedback':return [(lambda x:m.output_feedback(x)[0]*1000,BLUE,''),(lambda x:m.output_feedback(x)[1]*1000,GRAY,'6 4')]
    if key=='control_sweep':return [(lambda x:1/sum(m.astable(control=x)),BLUE,'')]
    if key=='monostable_leakage':return [(lambda x:m.monostable(x*1e-6),BLUE,'')]
    if key=='recovery_gap':
        curves=[(lambda x:m.recovery(x/1000)[int(stage>=2)],BLUE,'')]
        if stage>=2:curves.append((lambda x:math.log(3),GRAY,'6 4'))
        return curves
    return [(lambda x:m.reset_ramp(x/1000),BLUE,'')]


def state_plot(stage,small=False,begin=None):
    scale=1 if small else 1.6
    rows=[('有效',1,8,0),('释放',1,8,1),('释放',4,4,1),('释放',4,7,0)]
    reset,trigger,threshold,out=rows[stage]
    body=[text(12,65,'RESET：'+reset,18),text(12,101,f'TRIG：{trigger} V',18),text(12,137,f'THRES：{threshold} V',18),line(160,55,160,143,GRAY,2),text(176,100,'锁存',20),line(220,100,265,100,INK,2),text(270,106,str(out),24),text(12,190,'DISCH：'+('截止' if out else '导通'),20)]
    if small:body.append(text(12,230,'输出与放电开关同步改变',18))
    prefix='<g transform="translate('+('0 0' if small else '100 70')+f') scale({scale})">'+''.join(body)
    final=prefix+'</g>'
    if begin is None:return final
    active_y=[65,101,101,137][stage]
    motion=(f'<circle r="4" fill="{RED}" opacity="0"><set attributeName="opacity" to="1" begin="{begin:g}s"/>'
            f'<animateMotion path="M145,{active_y} L160,{active_y} L200,100 L260,100" begin="{begin:g}s" dur="2s" fill="freeze"/></circle>')
    return Graphic(prefix+motion+'</g>',final)


def plot(key,stage,small=False,begin=None):
    if key=='threshold_memory':
        yield state_plot(stage,small,begin);return
    spec=SPECS[key];xmin,xmax=spec['xlim'];ymin,ymax=spec['ylim'];ticks=spec['yticks'];ylabel=spec['ylabel']
    if key=='recovery_gap' and stage>=2:ymin,ymax=0,1.2;ticks=[0,.5,1];ylabel='下一拍 / s'
    x0,y0,w,h=(65,170,240,85) if small else (100,310,520,145)
    size=18 if small else 20
    px=lambda x:x0+w*(x-xmin)/(xmax-xmin)
    py=lambda y:y0-h*(y-ymin)/(ymax-ymin)
    yield text(8 if small else 40,y0-h-16,ylabel,size)
    for y in ticks:yield line(x0,py(y),x0+w,py(y),GRAY,1,'2 5')+text(x0-8,py(y)+6,f'{y:g}',size,anchor='end')
    for x in spec['xticks']:yield text(px(x),y0+26,f'{x:g}',size,anchor='middle')
    yield text(x0+w,y0+49,spec['xlabel'],size,anchor='end')
    fs=functions(key,stage)
    xs=[xmin+(xmax-xmin)*i/600 for i in range(601)]
    if key=='astable_cycle':
        th,tl=m.astable()
        xs=sorted(set(xs+[(n*(th+tl)+offset)*1000 for n in [0,1] for offset in [th,th+tl] if (n*(th+tl)+offset)*1000<xmax]))
    for index,(fn,color,dash) in enumerate(fs):
        curve_xs=xs
        if key=='first_pulse':
            endpoint=.78*math.log(3 if index==0 else 2)
            curve_xs=[x for x in xs if x<endpoint]+[endpoint]
        yield polyline([(px(x),py(fn(x))) for x in curve_xs],color,dash=dash,begin=begin,identity=f'{key}-{stage}-{index}')
    marker=spec['markers'][stage];chosen=1 if key=='first_pulse' and stage==1 else 0;fn=fs[chosen][0]
    final=f'<circle cx="{px(marker):g}" cy="{py(fn(marker)):g}" r="5" fill="{INK}"/>'
    if begin is None:yield final
    else:
        path='M'+' L'.join(f'{px(xmin+(marker-xmin)*i/80):g},{py(fn(xmin+(marker-xmin)*i/80)):g}' for i in range(81))
        yield Graphic(f'<circle r="5" fill="{INK}" opacity="0"><set attributeName="opacity" to="1" begin="{begin:g}s"/><animateMotion path="{path}" begin="{begin:g}s" dur="2s" fill="freeze"/></circle>',final)
    if key=='astable_cycle':
        baseline=249 if small else 390;amp=13 if small else 20
        yield text(8 if small else 40,baseline,'OUT',size)
        points=[]
        for x in xs:
            points += [(px(x),baseline-amp*m.cycle(max(0,x/1000-1e-12))[1]),(px(x),baseline-amp*m.cycle(x/1000+1e-12)[1])]
        yield polyline(points,GRAY,begin=begin,identity=f'out-{stage}')


def scene(key):
    spec=SPECS[key];tl=timeline(spec['title'],spec['steps'],'示意：'+spec['boundary']);layers=[]
    for i,beat in enumerate(tl.beats):
        layers.append(Layer(beat.name,text(40,117,spec['notes'][i],20)))
        layers.extend(Layer(beat.name,g) for g in plot(key,i,begin=beat.start+.2 if i<3 else None))
    return tl,layers


def storyboard(key):
    spec=SPECS[key];out=print_header(spec['title'],910,spec['boundary'])
    for i in range(4):
        x,y=18+(i%2)*350,65+(i//2)*300
        out += [f'<g data-storyboard-beat="{i+1}" transform="translate({x} {y})">',f'<rect width="334" height="284" rx="8" fill="none" stroke="{GRAY}"/>',text(10,27,f'{i+1}. '+spec['mini'][i],20),*plot(key,i,small=True),text(10,273,spec['notes'][i],18),'</g>']
    for i,caption in enumerate(spec['steps']):out.append(text(26,704+32*i,f'{i+1}. '+caption,19))
    out += [text(26,870,'示意：'+spec['boundary'],18),'</svg>']
    return '\n'.join(out)


def metadata(key):
    s=SPECS[key]
    parameter={'discharge_floor':('VD','V'),'diode_duty':('VF','V'),'output_feedback':('VOH','V'),'control_sweep':('CONT','V'),'monostable_leakage':('Ileak','µA')}.get(key)
    return dict(id='ch10-'+key.replace('_','-')+'-v2',chapter=10,source='docs/p1-11-ch10.md',anchor=s['anchor'],type=s['type'],style_id='FA-029',layout_id='IG-015',purpose=s['title'],alt=s['title']+'。'+' '.join(s['steps'])+' '+s['boundary'],en_prompt='Four causal snapshots, explicit circuit conditions, physical axes and separate state lanes. '+key.replace('_',' '),scene=lambda:scene(key),storyboard=lambda:storyboard(key),parameters=[dict(name=parameter[0],values=s['markers'],unit=parameter[1])] if parameter else [],numbers=[dict(value=str(v),label='示意',reason='物理模型的坐标刻度或节拍编号，不作为器件保证。') for v in sorted(set([0,1,2,3,4]+s.get('xticks',[])+s.get('yticks',[])))])
