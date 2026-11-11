"""A live pull-up may charge an unpowered rail through an input clamp."""
from scripts.visuals.interface_models import *
from scripts.visuals.primitives import text,line,current_flow
from scripts.visuals.plotting import polyline
from scripts.visuals.render import Layer

TITLE='掉电的电源轨，也可能被信号线充起来'
STEPS=['外部 3.3 V 经 10 kΩ，输入钳位压降取 0.3 V。',
       '掉电轨上并联 1 µF 和 10 kΩ 等效负载。',
       '终值 1.5 V；等效 RC 为 5 ms。',
       '核对 Ioff / 掉电高阻；名称 fail-safe 不能代替它。']
BOUNDARY='固定二极管压降与被动负载示意，不代表任何具体芯片。'


def base():
    out=text(36,100,'3.3 V',18)+line(40,125,620,125,INK,2)
    out+=f'<rect x="150" y="115" width="60" height="20" fill="#f7eed9" stroke="{INK}" stroke-width="2"/>'
    out+=text(180,100,'10 kΩ',18,anchor='middle')
    out+=f'<rect x="285" y="111" width="105" height="28" fill="#f7eed9" stroke="{INK}" stroke-width="2"/>'
    out+=text(338,100,'钳位 0.3 V',18,anchor='middle')+text(338,132,'导通模型',18,anchor='middle')
    out+=text(550,100,'掉电轨',18,anchor='middle')
    out+=line(495,125,495,145,INK,2)+line(480,145,510,145,INK,2)+line(480,153,510,153,INK,2)+line(495,153,495,185,INK,2)
    out+=text(470,174,'1 µF',18,anchor='end')+line(620,125,620,185,INK,2)
    out+=f'<rect x="609" y="142" width="22" height="28" fill="#f7eed9" stroke="{INK}" stroke-width="2"/>'
    out+=text(600,166,'10 kΩ',18,anchor='end')+line(495,185,620,185,INK,2)+text(640,190,'GND',18)
    return out+axes(20,1.5,[0,5,10,20],[0,.75,1.5],'ms','轨压 / V',height=130,y0=365)


def curve(begin=None,identity='rail'):
    return polyline([(100+530*t/20,365-130*unpowered_rail(t/1000)/1.5) for t in [i/10 for i in range(201)]],RED,begin=begin,identity=identity)


def scene():
    tl=timeline(TITLE,STEPS,BOUNDARY)
    layers=[Layer(None,base())]
    for i,b in enumerate(tl.beats):
        if i:
            layers.append(Layer(b.name,curve(b.start+.2 if i==1 else None,f'rail-{i}')))
        if i<2:
            layers.append(Layer(b.name,current_flow('M50,125 L495,125 L495,142',b.start+.2,2)))
    return tl,layers


def storyboard():
    return print_scene(TITLE,base()+curve(),STEPS,BOUNDARY)


META=metadata('ch05-backpower-v2','5.3','A1',TITLE,
    '外部上拉通过输入钳位给掉电轨充电。示意三点三伏经十千欧和零点三伏钳位，轨上并一微法与十千欧，电压以五毫秒时间常数趋向一点五伏。',
    'Show the powered pull-up, clamp and passive unpowered rail load with the analytical rail charging curve. Clearly mark illustrative clamp parameters and power-off isolation requirements.',scene,storyboard,[0,.75,20])
