"""One-pole normalized thermal response: single pulses and residual heating."""
import math
from scripts.visuals.primitives import line,text
from scripts.visuals.plotting import polyline,print_header
from scripts.visuals.render import Layer
from scripts.visuals.timeline import Beat,Timeline
INK,BLUE,RED,GRAY='#16202b','#1f5d7a','#a8321f','#5b666f'
POWER,RESISTANCE=4.25,60
WIDTH=.5


def step(u):
    return 0 if u<0 else 1-math.exp(-u)


def rise(u,starts):
    return sum(step(u-start)-step(u-start-WIDTH) for start in starts)


def axes(baseline=350,scale=210):
    out=text(36,baseline-scale-28,'ΔT / 255 °C',18)
    for value in [0,.5,1]:
        y=baseline-value*scale
        out+=line(100,y,630,y,GRAY,1,'3 5')+text(87,y+6,str(value),18,anchor='end')
    for t in [0,2,4,6]:
        out+=text(100+t*86,baseline+28,str(t),18,anchor='middle')
    return out+text(670,baseline+28,'t / τ',18,anchor='end')


def curve(kind,begin=None,baseline=350,scale=210,identity='heat'):
    value=(lambda u:step(u)) if kind=='steady' else (lambda u:rise(u,[0] if kind=='single' else [0,2,4]))
    pts=[(100+i*.86,baseline-scale*value(i/100)) for i in range(601)]
    return polyline(pts,GRAY if kind=='steady' else BLUE if kind=='single' else RED,
                    dash='3 5' if kind=='steady' else '10 4' if kind=='single' else '',begin=begin,identity=identity)


def scene():
    tl=Timeline(720,470,12,(
        Beat('稳态上界',0,3,'恒功率持续施加：温升逐渐趋向 P × Rθ。',GRAY),
        Beat('孤立脉冲',3,6,'孤立 0.5τ 脉冲：停止发热后逐渐冷却。',BLUE),
        Beat('重复脉冲',6,9,'每 2τ 重复一次：上次余热仍在，温升会累积。',RED),
        Beat('核对热边界',9,12,'示意单极点；实际用器件曲线及相同冷却边界。',INK,hold=True),
    ),'热量不会在脉冲结束时清零','示意单极点：时间按 τ 归一化；不代表某一器件的实测热响应')
    layers=[Layer(None,axes())]
    for index,beat in enumerate(tl.beats):
        kinds=['steady'] if index==0 else ['steady','single'] if index==1 else ['steady','repeat']
        for kind in kinds:
            layers.append(Layer(beat.name,curve(kind,beat.start+.3 if index<3 else None,identity=f'{kind}-{index}')))
        layers.append(Layer(beat.name,text(100,89,'短虚线持续 / 长虚线孤立 / 实线重复',20)))
    return tl,layers


def storyboard():
    out=print_header('瞬态热阻：短脉冲与余热累积',760,'同一热边界下的持续加热、孤立与重复脉冲。')
    out += [axes(),curve('steady'),curve('single'),curve('repeat'),text(100,80,'短虚线持续 / 长虚线孤立 / 实线重复',20),
            text(36,430,'① 稳态温升：4.25 W × 60 °C/W = 255 °C。',22),
            text(36,474,'② 孤立脉冲宽 0.5τ，冷机起点；结束后指数冷却。',20),
            text(36,518,'③ 每 2τ 重复，后续脉冲叠加余热，不能重置为零。',20),
            text(36,562,'④ 同一边界下 Zθ(t) 趋近 Rθ；不可交换 JC 与 JA。',20),
            text(36,614,'示意：阶跃归一化响应 1 − exp(−t/τ)。',20),
            text(36,658,'真实热网络有多个时间常数，按手册脉冲曲线复核。',20),
            text(36,706,'255 °C 是过热预算示例，不是可持续工作的许可。',18),'</svg>']
    return '\n'.join(out)


META={'id':'ch04-thermal-pulse-v2','chapter':4,'source':'docs/p1-05-ch4.md','anchor':'4.5',
      'type':'A2','style_id':'FA-029','layout_id':'IG-015','purpose':'用响应叠加区分孤立短脉冲和重复脉冲温升',
      'alt':'归一化单极点热模型，持续加热逐渐趋近二百五十五摄氏度温升，孤立半个时间常数脉冲随后冷却，每两个时间常数重复的脉冲叠加余热。实际按器件瞬态热阻和冷却边界校核。',
      'en_prompt':'Compare a sustained thermal step with isolated and repeated rectangular power pulses using the same normalized time and temperature axes. Compute cooling and residual heating by superposition; label the single-pole illustrative boundary.',
      'numbers':[{'value':v,'label':'示意','reason':'归一化时间轴或单极点示意脉宽，不是器件参数。'} for v in ['0','0.5','1','2','4','6']],
      'scene':scene,'storyboard':storyboard}
