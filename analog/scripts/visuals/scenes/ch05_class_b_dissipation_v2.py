"""A class-B transistor dissipates most at intermediate output amplitude."""
from scripts.visuals.interface_models import *
from scripts.visuals.primitives import text,line,parameter_sweep
from scripts.visuals.plotting import polyline
from scripts.visuals.render import Layer

TITLE='B 类管耗最大，发生在满幅之前'
STEPS=['±12 V、8 Ω；满幅 12 V 的负载功率为 9 W。',
       '每管 PT = VCC·Vp/(πRL) − Vp²/(4RL)。',
       'Vp = 2VCC/π = 7.64 V 时，每管约 1.824 W。',
       '65 °C/W、25 °C 环境：最大结温约 143.6 °C。']
BOUNDARY='理想 B 类与纯电阻示意；AB 偏置、驱动压降和电抗另计。'


def base():
    return axes(12,9,[0,4,8,12],[0,3,6,9],'','功率 / W')+text(680,398,'Vp / V',18,anchor='end')+text(100,92,'实线：负载；虚线：每只晶体管',18)


def curve(index,begin=None,identity='power'):
    return polyline([(100+530*v/12,350-220*class_b(v)[index]/9) for v in [i/20 for i in range(241)]],BLUE if index==0 else RED,dash='' if index==0 else '7 5',begin=begin,identity=identity)


def peak_label():
    vp=24/math.pi
    y=350-220*class_b(vp)[1]/9
    return line(100+530*vp/12,175,100+530*vp/12,y,RED,2,'3 5')+text(420,160,'7.64 V / 1.824 W',20,RED,anchor='middle')


def scene():
    tl=timeline(TITLE,STEPS,BOUNDARY)
    layers=[Layer(None,base())]
    for i,b in enumerate(tl.beats):
        for index in ([0] if i==0 else [0,1]):
            layers.append(Layer(b.name,curve(index,b.start+.2 if i<2 else None,f'power-{i}-{index}')))
        if i>=2:layers.append(Layer(b.name,peak_label()))
    return tl,layers


def storyboard():
    return print_scene(TITLE,base()+curve(0)+curve(1)+peak_label(),STEPS,BOUNDARY)


META=metadata('ch05-class-b-dissipation-v2','5.6','A2',TITLE,
    '同一输出幅度轴上比较负载功率和每管平均耗散。正负十二伏、八欧的理想 B 类，在输出峰值七点六四伏时每管最热约一点八二四瓦，满幅时反而约一点二三瓦。',
    'Plot load power and per-transistor average dissipation from the ideal class-B half-cycle integral. Mark the intermediate-amplitude thermal maximum and separate ideal-model limits.',scene,storyboard,[0,3,4,6])
