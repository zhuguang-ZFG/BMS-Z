"""Track supply energy, capacitor storage, and dissipated heat separately."""
import math
from scripts.visuals.interface_models import *
from scripts.visuals.primitives import text
from scripts.visuals.plotting import polyline
from scripts.visuals.render import Layer

TITLE='一次充放电，能量去了哪里'
STEPS=['20 pF、5 V：完整充电从电源取 0.5 nJ。',
       '电容储能 0.25 nJ，充电路径已耗 0.25 nJ。',
       '放电再耗 0.25 nJ；一周期共耗 0.5 nJ。',
       '10 MHz 完整周期为 5 mW；3.3 V 为 2.178 mW。']
BOUNDARY='理想 RC 示意；完整充放电，未含直通、漏电与直流负载。'


def chart(stage, begin=None):
    out=axes(6,.5,[0,2,4,6],[0,.25,.5],'t/RC','能量 / nJ')
    colors=[INK,BLUE,RED]
    dashes=['','7 5','2 5']
    for index in range(1 if stage==0 else 3):
        pts=[]
        for t in [i/40 for i in range(241)]:
            if stage>=2:
                # New local time origin at discharge; source has already supplied 0.5 nJ.
                stored=.25*math.exp(-2*t)
                value=[.5,stored,.5-stored][index]
            else:
                value=charging_accounts(t)[index]*1e9
            pts.append((100+530*t/6,350-440*value))
        curve=polyline(pts,colors[index],dash=dashes[index],begin=begin,identity=f'energy-{stage}-{index}')
        if begin is not None:
            # Keep animation and print forms as separate layers.
            yield curve
        else:
            out+=curve
    out+=text(100,90,'实线：已供能；长虚线：储能；点线：累计热',18)
    yield out


def scene():
    tl=timeline(TITLE,STEPS,BOUNDARY)
    layers=[]
    for i,b in enumerate(tl.beats):
        layers.extend(Layer(b.name,g) for g in chart(i,b.start+.2 if i<3 else None))
        if i>=2:
            layers.append(Layer(b.name,text(100,405,'放电从新 t=0 起算；0.25 nJ 储能变成热',18,RED)))
    return tl,layers


def storyboard():
    return print_scene(TITLE,''.join(chart(3))+text(100,402,'本图：充满后开始放电，时间重新从零计。',18),STEPS,BOUNDARY)


META=metadata('ch05-capacitive-energy-v2','5.1','A1',TITLE,
    'RC 充电中的电源能量、储能与热量共用能量轴；二十皮法、五伏一完整充放电周期耗零点五纳焦，十兆赫为五毫瓦。放电只消耗此前存下的能量。',
    'Plot analytically conserved source energy, capacitor energy and charging heat. Separate subsequent discharge heat and define frequency as complete cycles.',scene,storyboard,[0,2,4,6,.25])
