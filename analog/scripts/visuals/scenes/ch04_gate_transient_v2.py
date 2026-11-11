"""Solve Ctotal*dVg/dt + Vg/R = Cgd*dVd/dt before channel conduction."""
import math
from scripts.visuals.primitives import line,text
from scripts.visuals.plotting import polyline,print_header
from scripts.visuals.render import Layer
from scripts.visuals.timeline import Beat,Timeline
INK,BLUE,RED,GRAY='#16202b','#1f5d7a','#a8321f','#5b666f'
CGD,CGS,SLOPE,RAMP_NS=50e-12,1000e-12,20e9,20


def gate_v(t_ns,resistance):
    tau_ns=resistance*(CGD+CGS)*1e9
    peak=CGD*SLOPE*resistance*(1-math.exp(-RAMP_NS/tau_ns))
    if t_ns<=RAMP_NS:
        return CGD*SLOPE*resistance*(1-math.exp(-max(t_ns,0)/tau_ns))
    return peak*math.exp(-(t_ns-RAMP_NS)/tau_ns)


def axes(baseline=350,scale=20):
    out=text(36,baseline-scale*10-22,'VG / V',18)
    for v in [0,1,10]:
        y=baseline-v*scale
        out+=line(100,y,630,y,GRAY,1,'3 5')+text(86,y+6,str(v),18,anchor='end')
    for t in [0,20,50]:
        out+=text(100+t*10.6,baseline+28,str(t),18,anchor='middle')
    return out+text(680,baseline+28,'ns',18)


def curve(resistance,begin=None,baseline=350,scale=20,identity='gate'):
    return polyline([(100+t*.106,baseline-scale*gate_v(t/100,resistance)) for t in range(0,5001,25)],
                    RED if resistance==10 else BLUE,dash='' if resistance==10 else '7 5',begin=begin,identity=identity)


def scene():
    tl=Timeline(720,470,12,(
        Beat('漏压斜坡',0,3,'400 V / 20 ns；50 pF 注入 1 A 位移电流。',INK),
        Beat('十欧关断',3,6,'10 Ω 与 1050 pF：τ = 10.5 ns，20 ns 约 8.5 V。',RED),
        Beat('一欧关断',6,9,'1 Ω 同条件峰值约 1 V；低阻下拉降低栅压。',BLUE),
        Beat('模型边界',9,12,'跨过实际阈值后沟道参与，须用非线性模型复核。',INK,hold=True),
    ),'栅极被注入电流后，电压随时间积累','固定电容示意模型；未计沟道导通，曲线用于识别误导通风险')
    layers=[Layer(None,axes())]
    for index,beat in enumerate(tl.beats):
        if index==0:
            layers.append(Layer(beat.name,text(120,240,'Cgd dVD/dt = 1 A',28)))
        else:
            for r in ([10] if index==1 else [10,1]):
                layers.append(Layer(beat.name,curve(r,beat.start+.3 if index<3 else None,identity=f'gate-{index}-{r}')))
            layers.append(Layer(beat.name,text(100,92,'实线 10 Ω / 虚线 1 Ω；20 ns 后停止注入',20)))
    return tl,layers


def storyboard():
    out=print_header('栅极误导通：先积电荷，再看峰值',740,'固定电容模型的十欧与一欧关断响应，同一时间与电压刻度。')
    out += [axes(350,20),curve(10),curve(1),text(100,80,'实线 10 Ω / 虚线 1 Ω',20),
            text(36,430,'① 400 V / 20 ns；50 pF × 20 V/ns = 1 A。',20),
            text(36,472,'② Ctotal = 1050 pF，10 Ω：τ = 10.5 ns。',20),
            text(36,514,'③ 改为 1 Ω：τ = 1.05 ns，峰值约 1 V。',20),
            text(36,556,'④ 10 Ω 峰值约 8.5 V；不是瞬间跳到 iR = 10 V。',20),
            text(36,606,'斜坡结束后按相同 τ 放电；浮空分压约 19 V。',20),
            text(36,650,'固定电容、未计沟道导通的示意；跨阈值后另算。',20),
            text(36,694,'减小关断阻抗，仍须查热态阈值、寄生电感与钳位。',18),'</svg>']
    return '\n'.join(out)


META={'id':'ch04-gate-transient-v2','chapter':4,'source':'docs/p1-05-ch4.md','anchor':'4.3',
      'type':'A3','style_id':'FA-029','layout_id':'IG-015','purpose':'区分栅极瞬态响应与电阻、电容分压上界',
      'alt':'400 伏漏压在 20 纳秒上升，50 皮法向总计 1050 皮法的栅节点注入 1 安。10 欧下拉的示意峰值约 8.5 伏，1 欧约 1 伏；随后指数放电。跨过阈值后模型需加入沟道导通。',
      'en_prompt':'Plot two analytically solved gate RC responses on shared axes for the same finite drain-voltage ramp. Preserve the decay after the ramp and distinguish finite-time peaks from asymptotic IR and floating capacitive division.',
      'parameters':[{'name':'Roff','values':[10,1],'unit':'Ω'}],
      'numbers':[{'value':'0','label':'示意','reason':'坐标轴原点。'},{'value':'50','label':'示意','reason':'观察窗口终点，单位 ns。'}],
      'scene':scene,'storyboard':storyboard}
