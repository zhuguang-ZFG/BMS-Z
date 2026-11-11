"""Ground bounce is L di/dt, not a fixed offset proportional to current."""
from scripts.visuals.interface_models import *
from scripts.visuals.primitives import text
from scripts.visuals.plotting import polyline
from scripts.visuals.render import Layer

TITLE='电流升得越快，共用地线弹得越高'
STEPS=['每路 20 mA；八路共同回流为 160 mA。',
       '从零上升用 2 ns，共用电感取 5 nH。',
       '八路同翻为 0.4 V；单路同速度为 0.05 V。',
       '电流恒定后电感压降为零，真实回路还会振铃。']
BOUNDARY='分段线性电流与集中电感示意；未包含电阻、寄生电容。'


def current(t,n):
    return .02*n*max(0,min(t/2,1))


def bounce(t,n):
    return 5e-9*(.02*n/2e-9) if 0<t<2 else 0


def chart(n, voltage=False, begin=None, ident='bounce'):
    xmax=6
    y0=215 if not voltage else 350
    scale=468.75 if not voltage else 187.5
    ys=[current(t,n) if not voltage else bounce(t,n) for t in [0,.001,1.999,2,6]]
    pts=[(100+530*t/xmax,y0-scale*y) for t,y in zip([0,.001,1.999,2,6],ys)]
    return polyline(pts,RED if n==8 else BLUE,dash='' if n==8 else '7 5',begin=begin,identity=ident)


def base():
    return (text(200,90,'实线八路 / 虚线单路；时间轴相同',18)+
            axes(6,.16,[],[0,.16],'','总电流 / A',y0=215,height=75)+
            axes(6,.4,[0,2,6],[0,.4],'ns','地电压 / V',y0=350,height=75))


def scene():
    tl=timeline(TITLE,STEPS,BOUNDARY)
    layers=[Layer(None,base())]
    for i,b in enumerate(tl.beats):
        for n in ([8] if i<2 else [8,1]):
            for voltage in ([False] if i==0 else [False,True]):
                layers.append(Layer(b.name,chart(n,voltage,b.start+.3 if i<3 else None,f'bounce-{i}-{n}-{voltage}')))
    return tl,layers


def storyboard():
    chart_svg=base()+''.join(chart(n,v) for n in [8,1] for v in [False,True])
    return print_scene(TITLE,chart_svg,STEPS,BOUNDARY)


META=metadata('ch05-ground-bounce-v2','5.1','A2',TITLE,
    '同一时间轴的总回流和地电压。五纳亨共用电感上，八路共一百六十毫安在两纳秒内上升产生零点四伏，单路零点零五伏；恒流段理想电感压降为零。',
    'Use aligned current and voltage plots for one versus eight outputs. Show voltage only during the current ramp according to L di/dt.',scene,storyboard,[0,6,.16])
