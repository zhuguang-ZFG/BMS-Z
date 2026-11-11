"""A local tangent cannot be extrapolated back to the threshold of a parabola."""
from scripts.visuals.primitives import line,text
from scripts.visuals.plotting import polyline,print_header
from scripts.visuals.render import Layer
from scripts.visuals.timeline import Beat,Timeline
INK,BLUE,RED,GREEN,GRAY='#16202b','#1f5d7a','#a8321f','#3d6b4a','#5b666f'
THRESHOLD,K=2,5


def current(vgs):
    return K*max(0,vgs-THRESHOLD)**2


def tangent(vgs):
    return 5+10*(vgs-3)


def xy(vgs,current_a):
    return 110+(vgs-2)*420,350-current_a*29


def axes():
    out=line(110,350,640,350,INK,2)+line(110,350,110,100,INK,2)
    for v in [2,2.5,3]:
        x,_=xy(v,0);out+=text(x,380,str(v),18,anchor='middle')
    for a in [0,5]:
        _,y=xy(2,a);out+=line(110,y,630,y,GRAY,1,'3 5')+text(90,y+6,str(a),18,anchor='end')
    return out+text(36,100,'ID / A',18)+text(670,380,'VGS / V',18,anchor='end')


def parabola(begin=None,identity='parabola'):
    return polyline([xy(2+i*.006,current(2+i*.006)) for i in range(201)],BLUE,begin=begin,identity=identity)


def slope_lines(include_secant=True):
    secant=line(*xy(2,0),*xy(3,5),GREEN,2,'7 5') if include_secant else ''
    tan=line(*xy(2.5,0),*xy(3.2,7),RED,2)
    return secant+tan+text(136,106,'割线 5 A/V；切线 gm = 10 S' if include_secant else '局部切线：gm = 10 S',20)


def scene():
    tl=Timeline(720,470,12,(
        Beat('转移曲线',0,3,'示意平方律：ID = 5 (VGS − 2)²，电流单位 A。',BLUE),
        Beat('局部切线',3,6,'Q 点为 3 V / 5 A；局部导数 gm = 10 S。',RED),
        Beat('阈值割线',6,9,'切线延长交在 2.5 V，不是阈值 2 V。',GREEN),
        Beat('回代平方律',9,12,'VGS = VTH + 2ID/gm = 3 V；真实器件查曲线。',INK,hold=True),
    ),'跨导是切线斜率，不是从阈值起算的割线','示意长沟道模型；实线切线、虚线割线；数值各自按坐标绘制')
    layers=[Layer(None,axes())]
    for index,beat in enumerate(tl.beats):
        layers.append(Layer(beat.name,parabola(beat.start+.3 if index==0 else None)))
        if index:
            layers.append(Layer(beat.name,slope_lines(index>=2)+f'<circle cx="530" cy="205" r="6" fill="{INK}"/>'))
    return tl,layers


def storyboard():
    out=print_header('跨导：四步区分切线与割线',720,'转移曲线、局部斜率、阈值割线与平方律回代。')
    out += [axes(),parabola(),slope_lines(),text(36,430,'① 平方律示意：ID = 5 (VGS − 2)²，单位 A。',20),
            text(36,476,'② Q 点 3 V / 5 A，导数 gm = 10 S。',20),
            text(36,522,'③ 切线外推的 2.5 V 截距，不是阈值 2 V。',20),
            text(36,568,'④ 过驱动 = 2ID/gm = 1 V，故 VGS = 3 V。',20),
            text(36,620,'平台高度应对应实际负载下的转移或栅电荷曲线。',20),
            text(36,670,'长沟道公式不能替代真实功率 MOSFET 的数据。',20),'</svg>']
    return '\n'.join(out)


META={'id':'ch04-transconductance-v2','chapter':4,'source':'docs/p1-05-ch4.md','anchor':'4.2',
      'type':'A2','style_id':'FA-029','layout_id':'IG-015','purpose':'纠正平台估算中把局部跨导当成割线的错误',
      'alt':'平方律转移曲线上的 3 伏、5 安工作点，局部切线跨导为 10 西门子，外推截距为 2.5 伏；实际阈值是 2 伏。过驱动为两倍漏电流除以跨导，即 1 伏。',
      'en_prompt':'Draw the transfer parabola, local tangent and threshold secant to scale. Compare their intercepts and derive overdrive as twice the operating current divided by transconductance. State the long-channel model boundary.',
      'numbers':[{'value':'0','label':'示意','reason':'坐标轴原点。'}],'scene':scene,'storyboard':storyboard}
