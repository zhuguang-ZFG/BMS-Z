"""Four-frame energy and signal narratives backed by explicit chapter 13 models."""
import math
from . import power_signal_models as m
from .interface_models import timeline, INK, BLUE, GRAY
from .primitives import text, line, Graphic
from .plotting import polyline, print_header
from .render import Layer

SPECS={}


def spec(key,title,anchor,boundary,notes,steps,limits,ticks,labels,markers,parameter=None):
    SPECS[key]=dict(title=title,anchor=anchor,boundary=boundary,notes=notes,steps=steps,
                    xlim=limits[0],ylim=limits[1],xticks=ticks[0],yticks=ticks[1],
                    xlabel=labels[0],ylabel=labels[1],markers=markers,parameter=parameter)


spec('zener_budget','先扣基流，再看齐纳管还能否稳压','13.1',
     '示意 Vin=9 V、R=330 Ω、Vz=5.6 V、β=50；负值表示稳压假设失效。',
     ['空载','负载 100 mA','负载 300 mA','负载 500 mA'],
     ['串联电阻电流全部流入齐纳管。','负载增加，基流从同一支路分走电流。','还要与齐纳规定的最小工作电流比较。','接近零并不表示稳压仍好；须重算非理想工作点。'],
     ((0,500),(0,11)),([0,250,500],[0,5,10]),('负载 IE / mA','可用 IZ / mA'),[0,100,300,500])
spec('buck_cycle','同一电感电流，开关与二极管轮流接管','13.2',
     '示意理想 CCM：12→5 V、22 µH、150 kHz、负载 1 A；D=5/12。',
     ['导通初段','导通结束','关断续流','周期回到谷值'],
     ['电感两端七伏，电流以正斜率上升。','峰值到达后关开关，电流保持连续。','二极管接管，负五伏使电流逐渐下降。','回到同一电流才满足稳态伏秒平衡。'],
     ((0,1),(0,1.6)),([0,.5,1],[0,1,1.5]),('时间 / 开关周期','电感电流 / A'),[.15,5/12,.7,1])
spec('buck_charge','纹波看电荷的峰谷差，整周期净电荷为零','13.2a',
     '示意同一 Buck：C=100 µF；实线 ΔQ，从周期起点积分，虚线为零。',
     ['先给负载放电','电荷到谷值','电荷到峰值','净电荷回到零'],
     ['电感电流低于负载时，电容提供差额。','电容电流第一次过零，电压到谷值。','正电流面积给出峰谷间的充电量。','全周期正负面积相消，不是每周期净收到电荷。'],
     ((0,1),(-.4,.5)),([0,.5,1],[-.4,0,.4]),('时间 / 开关周期','相对电荷 / µC'),[.1,5/24,17/24,1])
spec('buck_dcm','固定占空比进入 DCM 后，输出随负载变化','13.2b',
     '示意二极管 Buck：12 V、22 µH、150 kHz、D=5/12；忽略纹波影响。',
     ['RL=5 Ω','临界约 11.3 Ω','RL=30 Ω','RL=100 Ω'],
     ['较重负载保持 CCM，电压为五伏。','电流谷值触零，来到两种模式的边界。','轻载出现零电流区间，固定 D 输出升高。','闭环会调占空比；同步强制 CCM 则可能允许负电流。'],
     ((5,100),(4,11)),([5,50,100],[5,8,11]),('负载 RL / Ω','输出电压 / V'),[5,5/m.buck_ripple()*2,30,100])
spec('boost_cycle','升压的关断阶段才把电感电流送往输出','13.3',
     '示意理想 CCM：5→12 V、47 µH、100 kHz、输出 0.2 A；D=7/12。',
     ['导通储能','即将关断','输入与电感共同供能','回到周期起点'],
     ['开关导通，输出电容单独向负载供电。','电感电流升至峰值，但输出二极管仍截止。','开关断开后，输入与电感经二极管向输出供电。','输入平均电流大于输出，理想输入输出功率相等。'],
     ((0,1),(0,.9)),([0,.5,1],[0,.5,.9]),('时间 / 开关周期','电感电流 / A'),[.15,7/12,.8,1])
spec('boost_stress','占空比越接近一，升压电流代价越大','13.3a',
     '示意理想 CCM、固定输出 0.2 A；实线 ILavg/Iout，未计损耗与限流。',
     ['D=0.2','D=0.5','D=0.7','D=0.8'],
     ['平均输入电流已高于输出电流。','二倍升压对应二倍输入电流。','更短的供能窗口要求更大的电感电流。','五倍只是理想变换比，不能保证真实电压或效率。'],
     ((.1,.8),(1,5.5)),([.2,.5,.8],[1,3,5]),('占空比 D','ILavg / Iout'),[.2,.5,.7,.8])
spec('pump_load','飞跨电容的搬运速率限制带载电压','13.3b',
     '示意反相泵幅值模型：Vin=5 V、Cfly=1 µF、f=10 kHz，Req=100 Ω。',
     ['空载','负载 5 mA','负载 10 mA','负载 20 mA'],
     ['理想空载幅值接近输入电压。','每秒搬运电荷有限，带载开始压降。','本慢开关等效模型下降一伏。','开关电阻、频率区间和输出电容纹波仍须另计。'],
     ((0,20),(2.5,5.5)),([0,10,20],[3,4,5]),('输出电流 / mA','负压输出幅值 / V'),[0,5,10,20])
spec('inverting_ratio','反相 Buck-Boost 的极性来自放电连接','13.3c',
     '示意理想 CCM、Vin=5 V；有符号输出为 −D·Vin/(1−D)。',
     ['D=0.2','D=0.4','D=0.5','D=0.7'],
     ['小占空比产生幅值较小的负电压。','提高占空比，负压幅值继续增大。','一半占空比时理想输出为负五伏。','高占空比增大电流与耐压应力，不能据此保证带载能力。'],
     ((.1,.75),(-16,0)),([.1,.5,.75],[-15,-10,-5,0]),('占空比 D','输出电压 / V'),[.2,.4,.5,.7])
spec('wien_select','文氏桥只在一个频率兼有零相位与三分之一增益','13.4',
     '示意等 R、等 C，β=sRC/[(sRC)²+3sRC+1]；横轴相对 f0。',
     ['f=0.1f0','f=0.5f0','f=f0','f=10f0'],
     ['低频反馈较弱，且带有相位超前。','靠近选频点，反馈幅值增加。','在自然频率处相位为零，幅值为三分之一。','高频再次衰减且相位滞后，仍需考虑放大器自身响应。'],
     ((-1,1),(0,.36)),([-1,0,1],[0,.167,.333]),('log10(f / f0)','反馈幅值 |β|'),[-1,math.log10(.5),0,1])
spec('wien_amplitude','起振增长与稳幅是两件事','13.4a',
     '示意慢包络：dA/dt=0.8A(1−A²)，A(0)=0.02；不作为灯泡模型。',
     ['小噪声种子','小信号增长','非线性减小增长率','趋向稳态幅度'],
     ['零初值在理想方程里不会自行起振。','小幅度增长来自足够的环路余量。','幅度增加后，需要限制机制降低有效增益。','只有大于一的增益条件不足以保证所需的稳定正弦。'],
     ((0,10),(0,1.1)),([0,5,10],[0,.5,1]),('模型时间 / s','包络 / 目标幅度'),[0,3,5,10])
spec('lc_energy','电场能与磁场能交替，理想总能量不变','13.4b',
     '示意无损 LC 自由振荡；实线电容能 cos²，虚线电感能 sin²。',
     ['电容全储能','能量等分','电感全储能','能量返回电容'],
     ['初始电压最大，电感电流为零。','电容放电，磁场能随电流增长。','四分之一周期后电压为零，电流最大。','实际损耗使自由振荡衰减，有源维持须补足能量。'],
     ((0,1),(0,1.1)),([0,.5,1],[0,.5,1]),('时间 / 振荡周期','能量 / 总能量'),[0,.125,.25,.5])
spec('current_compliance','负载电压用尽余量后，电流再也保持不了','13.5.1',
     '示意目标 1 mA、Rs=100 Ω、调整管预留 0.7 V；硬限幅模型。',
     ['供电 2.8 V','供电 5 V','供电 12 V','回查输出级边界'],
     ['两千欧负载已经用尽本例电压预算。','提高供电到五伏，最大负载变为四点二千欧。','十二伏下，预算允许十一点二千欧。','还要检查运放共模、驱动与管子耗散，曲线不是器件保证。'],
     ((0,15),(0,1.1)),([0,5,10,15],[0,.5,1]),('负载电阻 / kΩ','输出电流 / mA'),[2,4.2,11.2,15],('Vs',[2.8,5,12,12],'V'))
spec('sar_trials','逐位试探时保持输入不变','13.6a',
     '示意四位 SAR，满量程归一化，输入 0.63；实线试探 DAC，虚线输入。',
     ['试 0.5：保留','试 0.75：撤回','试 0.625：保留','试 0.6875：撤回'],
     ['先决定最高位，比较器只给一次大小判断。','试探超过输入，清掉第二位。','第三位试探仍不超过输入，保留。','最终码十，对应零点六二五；静态输入并不必然抖码。'],
     ((1,4),(.4,.85)),([1,2,3,4],[.5,.63,.75]),('试探次序','DAC / 满量程'),[1,2,3,4])
spec('alias_samples','相干采样把一千赫兹折成相位相关直流','13.6b',
     '示意 fs=1 kHz、初相 π/6；实线由样本插值辅助看形状，不是原模拟波。',
     ['输入 50 Hz','输入 950 Hz','输入 1000 Hz','输入 1001 Hz'],
     ['五十赫兹在本例中可还原，但须先限制带外输入。','九百五十赫兹折回五十赫兹，样本无法分辨来源。','恰好同频采样，每次都是同一相位，得到固定半幅值。','仅偏离一赫兹便出现慢拍；不能把精确同频也称作慢漂。'],
     ((0,20),(-1.1,1.1)),([0,10,20],[-1,0,1]),('采样时间 / ms','样本 / 正弦峰值'),[5,10,15,20],('fin',[50,950,1000,1001],'Hz'))
spec('quantization','量化是固定台阶，不会凭空产生随机抖动','13.6c',
     '示意舍入量化 q=1/8，避开满量程过载；实线量化值、虚线输入。',
     ['输入 0.1','输入 0.3','输入 0.5','输入 0.8'],
     ['输入落在同一量化区间时输出固定。','跨过阈值才跳到下一个台阶。','均匀误差模型需要输入或噪声满足相应统计条件。','q 除以根号十二是该模型的 RMS，不是所有直流读数的随机性。'],
     ((0,.9),(0,1)),([0,.5,.9],[0,.5,1]),('输入 / 满量程','量化输出 / 满量程'),[.1,.3,.5,.8])
spec('jitter','同样的时间抖动，高频信号付出更多噪声','13.6d',
     '示意正弦输入、独立小孔径抖动 σt=10 ps RMS；只计算抖动这一项。',
     ['输入 100 kHz','输入 1 MHz','输入 5 MHz','输入 10 MHz'],
     ['低频正弦斜率较小，时间误差造成的电压误差小。','一兆赫兹时，抖动上限约八十四分贝。','输入频率提高，噪声上限持续下降。','十兆赫兹只剩约六十四分贝；总 SINAD 还含其他误差。'],
     ((5,7),(60,110)),([5,6,7],[60,80,100]),('log10(fin / Hz)','抖动 SNR / dB'),[5,6,math.log10(5e6),7])
spec('acquisition','采集时间固定时，源阻会留下指数残差','13.6e',
     '示意满幅阶跃、Cin=20 pF、采集 500 ns、12 bit；虚线半 LSB。',
     ['Rtotal=2 kΩ','Rtotal≈2.774 kΩ','Rtotal=4 kΩ','Rtotal=5 kΩ'],
     ['两千欧时，本一阶模型低于半 LSB。','约二点七七四千欧用尽建立误差预算。','超过后只是残差变大，不能泛称必定丢码。','增采集时间、降源阻或改善驱动均可；还须扣开关电阻。'],
     ((2,5),(-6,.1)),([2,3,4,5],[-6,-4,-2,0]),('总串联电阻 / kΩ','log10(残差 / 满幅)'),[2,500e-9/(20e-12*13*math.log(2))/1000,4,5])
spec('hbridge_reverse','电压可以换向，电感电流必须连续','13.7a',
     '示意零反电势 RL：R=2 Ω、L=10 mH，初始 +2 A，桥输出改为 −12 V。',
     ['刚换向','电流仍为正','电流过零','负电流逐步建立'],
     ['电流不能随电压跳变，初始仍为正两安。','电压为负而电流为正，桥侧短时接收能量。','约一点四四毫秒后才穿越零点。','真实电机还有反电势与机械惯性，转速不会按此曲线瞬间翻转。'],
     ((0,10),(-6,2.5)),([0,5,10],[-6,-3,0,2]),('施加反压后 / ms','电流，左到右为正 / A'),[0,1,5*math.log(4/3),10])
spec('sense_cmr','共模误差预算随抑制比分贝换算','13.8b',
     '示意共模变化 12 V；输入等效误差=12/10^(CMRR/20)，虚线 0.2 mV。',
     ['CMRR=70 dB','CMRR=80 dB','CMRR≈95.56 dB','CMRR=110 dB'],
     ['七十分贝只是假设，在本例产生约三点八毫伏。','八十分贝仍超过分配给共模的误差。','达到约九十五点五六分贝，才压到零点二毫伏。','更高抑制不替代允许共模范围，也不保证 PWM 边沿恢复。'],
     ((70,110),(0,4)),([70,90,110],[0,2,4]),('CMRR / dB','输入等效误差 / mV'),[70,80,20*math.log10(60000),110])
spec('audio_heat','效率与发热必须对应同一输出摆幅','13.9a',
     '示意理想 B 类 ±15 V、8 Ω；实线热耗，虚线假定效率 90% 的 D 类。',
     ['输出 1 W','输出 5 W','输出 10 W','接近最大摆幅'],
     ['小输出下，B 类效率低于其理论最大值。','热耗随输出改变，不是额定功率乘固定比例。','十瓦时理想 B 类热耗约五点一瓦，D 类假设约一点一一瓦。','B 类最高效率只在最大不削顶正弦附近达到。'],
     ((0,14),(0,6)),([0,5,10,14],[0,3,6]),('正弦输出功率 / W','功率器件热耗 / W'),[1,5,10,14])
spec('crystal_pull','大步长负载偏移要直接算两个谐振频率','13.10a',
     '示意无损晶体：Cm=10 fF、C0=1.5 pF，以 CL=12 pF 频率作基准。',
     ['CL=12 pF','CL=13 pF','CL=14 pF','CL=15 pF'],
     ['参考负载处相对频偏为零。','增加负载电容使并联谐振频率降低。','牵引斜率随负载变化，不能用终点斜率乘整个步长。','十五皮法约慢六十七点三 ppm，即每天约慢五点八一秒。'],
     ((12,15),(-75,5)),([12,13,14,15],[-75,-50,-25,0]),('负载 CL / pF','相对 12 pF 频偏 / ppm'),[12,13,14,15])
spec('crystal_start','决定增长速度的是净负阻余量','13.10b',
     '示意串联动态支路 Lm=2400 H、Rm=50 kΩ，初幅 1 µA；线性起振阶段。',
     ['|Rneg|=25 kΩ','|Rneg|=50 kΩ','|Rneg|=100 kΩ','|Rneg|=150 kΩ'],
     ['负阻小于损耗，初始扰动衰减。','负阻刚好抵消损耗，线性模型没有增长。','净负阻为五万欧，包络指数增长。','更大余量增长更快，但稳态驱动与限幅必须另验。'],
     ((0,.2),(-.5,2)),([0,.1,.2],[-.5,0,1,2]),('起振时间 / s','log10(包络 / µA)'),[.2,.2,.2,.2],('|Rneg|',[25,50,100,150],'kΩ'))
spec('opto_ctr','降额后的 CTR 还要能拉动输出负载','13.11a',
     '示意输入 3.3 V、VF=1.2 V；实线 Rin=1 kΩ，虚线 470 Ω；有源区估算。',
     ['CTR=100%','CTR=50%','CTR=25%','核对饱和条件'],
     ['先按规定工作点计算可用集电极电流。','百分之五十下，一千欧方案估算有余量。','降至百分之二十五时，一千欧方案低于所需零点六三八毫安。','较小电阻增加驱动，但还须验证低输出电压时的饱和曲线。'],
     ((20,100),(0,4.8)),([25,50,100],[0,2,4]),('CTR / %','有源区可用 IC / mA'),[100,50,25,25])
spec('iso_displacement','无直流通路仍会有跨屏障位移电流','13.11b',
     '示意隔离寄生电容 1 pF；恒定边沿斜率期间 i=Ciso·dv/dt。',
     ['1 kV/µs','10 kV/µs','50 kV/µs','100 kV/µs'],
     ['寄生电容让快速电压变化产生短暂电流。','斜率十倍增加，位移电流也十倍增加。','回流路径与接口承受能力会影响误触发。','耐压、工作电压与 CMTI 是不同指标，必须分别核对。'],
     ((0,100),(0,110)),([0,50,100],[0,50,100]),('屏障 dv/dt / kV/µs','位移电流 / mA'),[1,10,50,100])


def curves(key,stage):
    blue=lambda fn:(fn,BLUE,'')
    gray=lambda fn:(fn,GRAY,'6 4')
    if key=='zener_budget':return [blue(lambda x:m.zener_current(9,x/1000)*1000)]
    if key=='buck_cycle':return [blue(m.buck_current),gray(lambda x:1)]
    if key=='buck_charge':return [blue(lambda x:m.buck_charge(x)*1e6),gray(lambda x:0)]
    if key=='buck_dcm':return [blue(lambda x:12*m.buck_dcm_ratio(x)),gray(lambda x:5)]
    if key=='boost_cycle':return [blue(m.boost_current),gray(lambda x:.2)]
    if key=='boost_stress':return [blue(lambda x:1/(1-x))]
    if key=='pump_load':return [blue(lambda x:5-.1*x)]
    if key=='inverting_ratio':return [blue(lambda x:-5*x/(1-x))]
    if key=='wien_select':return [blue(lambda x:abs(m.wien(10**x)))]
    if key=='wien_amplitude':return [blue(m.amplitude),gray(lambda x:1)]
    if key=='lc_energy':return [blue(lambda x:math.cos(2*math.pi*x)**2),gray(lambda x:math.sin(2*math.pi*x)**2)]
    if key=='current_compliance':return [blue(lambda x:1000*m.compliance_current(x*1000,[2.8,5,12,12][stage]))]
    if key=='sar_trials':return [blue(lambda x:m.sar_trials()[min(3,int(x)-1)][0]),gray(lambda x:.63)]
    if key=='alias_samples':
        f=[50,950,1000,1001][stage]
        return [blue(lambda x:math.sin(2*math.pi*f*x/1000+math.pi/6))]
    if key=='quantization':return [blue(m.quantize_nearest),gray(lambda x:x)]
    if key=='jitter':return [blue(lambda x:m.jitter_snr(10**x))]
    if key=='acquisition':return [blue(lambda x:math.log10(m.acquisition_error(x*1000))),gray(lambda x:math.log10(1/8192))]
    if key=='hbridge_reverse':return [blue(lambda x:m.bridge_current(x/1000)),gray(lambda x:0)]
    if key=='sense_cmr':return [blue(lambda x:12000/10**(x/20)),gray(lambda x:.2)]
    if key=='audio_heat':return [blue(lambda x:m.class_b_power(x)[1]),gray(lambda x:x*(1/.9-1))]
    if key=='crystal_pull':return [blue(m.crystal_pull_ppm)]
    if key=='crystal_start':return [blue(lambda x:math.log10(m.crystal_envelope(x,[25e3,50e3,100e3,150e3][stage])*1e6))]
    if key=='opto_ctr':return [blue(lambda x:m.opto_available(1000,x/100)*1000),gray(lambda x:m.opto_available(470,x/100)*1000)]
    if key=='iso_displacement':return [blue(lambda x:x)]
    raise KeyError(key)


def points(key,stage,index,fn):
    xmin,xmax=SPECS[key]['xlim']
    if key=='alias_samples':return [(x,fn(x)) for x in range(21)]
    if key=='sar_trials' and index==0:
        values=[row[0] for row in m.sar_trials()]
        return [(1,values[0])]+[(x,y) for n in range(1,4) for x,y in [(n+1,values[n-1]),(n+1,values[n])]]
    if key=='quantization' and index==0:
        result=[(0,0)]
        for n in range(7):
            x=(n+.5)/8
            result.extend([(x,n/8),(x,(n+1)/8)])
        return result+[(xmax,fn(xmax))]
    extra={'buck_cycle':[5/12],'buck_charge':[5/24,17/24],'boost_cycle':[7/12]}.get(key,[])
    return [(x,fn(x)) for x in sorted(set([xmin+(xmax-xmin)*i/240 for i in range(241)]+extra))]


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
    for i,(fn,color,dash) in enumerate(curves(key,stage)):
        pts=points(key,stage,i,fn)
        yield polyline([(px(x),py(y)) for x,y in pts],color,dash=dash,begin=begin,identity=f'{key}-{stage}-{i}')
        if key=='alias_samples':
            for x,y in pts:yield f'<circle cx="{px(x):g}" cy="{py(y):g}" r="3" fill="{INK}"/>'
    fn=curves(key,stage)[0][0];x=s['markers'][stage]
    final=f'<circle cx="{px(x):g}" cy="{py(fn(x)):g}" r="5" fill="{INK}"/>'
    if begin is None:yield final
    else:
        path='M'+' L'.join(f'{px(xx):g},{py(yy):g}' for xx,yy in points(key,stage,0,fn) if xx<=x)
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
    numbers=[dict(value=str(v),label='示意',reason='模型坐标、采样序号或展示取点；物理参数与适用条件见正文。') for v in sorted(set([0,1,2,3,4]+s['xticks']+s['yticks']))]
    extras={'buck_dcm':['11.3','30'],'boost_stress':['0.7'],'quantization':['0.1','0.3','0.8'],'acquisition':['10','2.774'],'crystal_start':['10']}.get(key,[])
    numbers += [dict(value=v,label='示意',reason='对应正文模型的扫描取点、对数底数或按图示精度舍入的临界值，不作器件保证。') for v in extras]
    return dict(id='ch13-'+key.replace('_','-')+'-v2',chapter=13,source='docs/p2-03-ch13.md',anchor=s['anchor'],type='A3' if param else 'A2',style_id='FA-029',layout_id='IG-015',purpose=s['title'],alt=s['title']+'；'+s['notes'][0]+'至'+s['notes'][-1]+'。',en_prompt='Four causal frames from an explicit physical model, axes, moving marker and bounded conclusions. '+key.replace('_',' '),scene=lambda:scene(key),storyboard=lambda:storyboard(key),parameters=[dict(name=param[0],values=param[1],unit=param[2])] if param else [],numbers=numbers)
