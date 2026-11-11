"""A resistor is usable only when all guaranteed bounds overlap."""
from scripts.visuals.interface_models import *
from scripts.visuals.primitives import text,line,parameter_sweep
from scripts.visuals.render import Layer

TITLE='上拉电阻：先找到不为空的区间'
STEPS=['3.3 V、0.4 V、3 mA：下限约 967 Ω。',
       '100 pF、300 ns：上限约 3541 Ω。',
       '400 pF 的上限约 885 Ω，已小于下限。',
       '改电容、模式或驱动能力；不是硬塞一只 820 Ω。']
BOUNDARY='示意电阻上拉模型；99 kΩ 漏电上限在此例不构成最紧约束。'


def x(r): return 100+530*r/4000


def drawing(stage):
    lo,hi=pullup_bounds(100e-12 if stage<2 else 400e-12)
    out=text(100,100,'同一阻值轴；绿段为可行交集',20)
    out+=line(100,270,630,270,GRAY,2)
    for r in [0,1000,2000,3000,4000]:out+=text(x(r),310,f'{r//1000:g}',18,anchor='middle')
    out+=text(676,310,'kΩ',18,anchor='end')
    out+=line(x(lo),170,x(lo),280,RED,3)+text(x(lo)-10,156,'967 Ω',20,RED,anchor='end')
    if stage:
        out+=line(x(hi),190,x(hi),280,BLUE,3,'7 5')
        out+=text(x(hi)+10,180,f'{hi:.0f} Ω',20,BLUE)
        if hi>=lo:
            out+=line(x(lo),250,x(hi),250,GREEN,12)
            out+=text(400,365,'100 pF：967–3541 Ω',22,GREEN,anchor='middle')
        else:
            out+=text(370,365,'400 pF：无解，885 < 967',22,RED,anchor='middle')
    return out


def scene():
    tl=timeline(TITLE,STEPS,BOUNDARY)
    layers=[Layer(b.name,drawing(i)) for i,b in enumerate(tl.beats)]
    layers.append(Layer(tl.beats[2].name,parameter_sweep(225,x(pullup_bounds(100e-12)[1]),x(pullup_bounds(400e-12)[1]),6.2,2,'')))
    layers.append(Layer(tl.beats[2].name,text(320,125,'电容增大，上限左移',18)))
    return tl,layers


def storyboard():
    return print_scene(TITLE,drawing(1)+text(100,400,'增到 400 pF → 上限 885 Ω → 无交集',20,RED),STEPS,BOUNDARY)


META=metadata('ch05-pullup-window-v2','5.2','A2',TITLE,
    '同一电阻坐标轴上求灌电流下限和上升时间上限的交集。三点三伏、一百皮法可取九百六十七至三千五百四十一欧；四百皮法时上限八百八十五欧，区间为空。',
    'Intersect low-level and rise-time resistor bounds on a shared physical resistance axis. Sweep capacitance to demonstrate an empty interval instead of picking a too-small resistor.',scene,storyboard,[0,1,2,3,4])
