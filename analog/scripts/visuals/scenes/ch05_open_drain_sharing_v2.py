"""One pull-up supplies one total current, shared among active sinks."""
from scripts.visuals.interface_models import *
from scripts.visuals.primitives import text,line,current_flow
from scripts.visuals.render import Layer

TITLE='两个开漏拉低，共用同一份上拉电流'
STEPS=['3.3 V、1 kΩ、下拉 25 Ω：一管约 3.22 mA。',
       '第二只下拉导通：总电流约 3.26 mA。',
       '相等支路各约 1.63 mA；实际不保证均分。',
       '另并上拉才增供流：两只 1 kΩ 时约 6.44 mA。']
BOUNDARY='下拉按相等电阻示意；每个真实器件仍须独自满足整条总线。'


def drawing(stage):
    n=1 if stage==0 else 2
    p=2 if stage==3 else 1
    voltage,total,each=sink_accounts(n,p)
    out=text(360,98,'3.3 V',20,anchor='middle')
    if p==1:
        out+=line(360,110,360,210)
        out+=f'<rect x="346" y="130" width="28" height="45" fill="#f7eed9" stroke="{INK}" stroke-width="3"/>'
        out+=text(390,156,'1 kΩ',20)
    else:
        out+=line(330,110,390,110)+line(330,190,390,190)+line(360,190,360,210)
        for xx in [330,390]:
            out+=line(xx,110,xx,190)
            out+=f'<rect x="{xx-14}" y="130" width="28" height="45" fill="#f7eed9" stroke="{INK}" stroke-width="3"/>'
        out+=text(425,156,'各 1 kΩ',20)
    out+=line(200,210,520,210)+text(100,202,f'总线 {voltage:.4f} V',18)
    for i,xx in enumerate([230,490]):
        on=i<n
        out+=line(xx,210,xx,320,BLUE if on else GRAY,4,'' if on else '7 5')
        out+=f'<rect x="{xx-14}" y="255" width="28" height="40" fill="#f7eed9" stroke="{BLUE if on else GRAY}" stroke-width="3"/>'
        out+=text(xx,350,'25 Ω 导通' if on else '高阻',20,anchor='middle')
        out+=text(xx,382,f'{each*1e3:.2f} mA' if on else '无灌电流',20,anchor='middle')
    out+=line(200,320,520,320)+text(360,345,'GND',18,anchor='middle')
    out+=text(100,130,f'总计 {total*1e3:.2f} mA',22,RED)
    return out


def scene():
    tl=timeline(TITLE,STEPS,BOUNDARY)
    layers=[]
    for i,b in enumerate(tl.beats):
        layers.append(Layer(b.name,drawing(i)))
        for xx in ([230] if i==0 else [230,490]):
            layers.append(Layer(b.name,current_flow(f'M360,112 L360,210 L{xx},210 L{xx},320',b.start+.2,2)))
    return tl,layers


def storyboard():
    return print_scene(TITLE,drawing(2),STEPS,BOUNDARY)


META=metadata('ch05-open-drain-sharing-v2','5.2','A1',TITLE,
    '一只上拉给两个开漏输出供电。第二个下拉导通后总电流约三点二六毫安，由两条相等支路分担；另并一只上拉时总电流才升至约六点四四毫安。',
    'Draw the common pull-up and two explicit current branches. Animate current continuity; distinguish an extra sink from an extra parallel pull-up.',scene,storyboard,[.0805,.0407,.0815])
