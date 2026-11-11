"""Count both dead intervals once, with units retained through the energy ledger."""
from scripts.visuals.primitives import Graphic,line,text
from scripts.visuals.plotting import print_header
from scripts.visuals.render import Layer
from scripts.visuals.timeline import Beat,Timeline
INK,BLUE,RED,GREEN,GRAY='#16202b','#1f5d7a','#a8321f','#3d6b4a','#5b666f'
VF,CURRENT,DEAD_NS,FREQUENCY=.8,5,100,100_000


def energy_j():
    return VF*CURRENT*DEAD_NS*1e-9


def timing(y=145):
    # Two 50 ns windows on a physical 10 us period, then a labelled magnification below.
    out=text(36,y-28,'① 完整周期 10 µs；两次死区各 50 ns（示意）',20)
    out+=line(100,y,620,y,INK,3)
    for t in [.0,5.0]:
        out+=f'<rect x="{100+52*t:g}" y="{y-13}" width="2.6" height="26" fill="{RED}"/>'
    out+=text(100,y+35,'0',18)+text(620,y+35,'10 µs',18,anchor='end')
    return out


def closeup(begin=None,y=255):
    out=text(36,y-25,'② 单次换流放大：上管关 → 死区 → 下管开',20)
    states=[(100,80,BLUE,'上管'),(180,260,RED,'体二极管'),(440,180,GREEN,'下管')]
    for x,w,c,label in states:
        out+=f'<rect x="{x}" y="{y}" width="{w}" height="40" fill="none" stroke="{c}" stroke-width="2"/>'
        out+=text(x+w/2,y+27,label,20,c,anchor='middle')
    out+=text(310,y+69,'此处 50 ns；另一沿另有 50 ns',18,anchor='middle')
    if begin is None: return out
    cursor=(f'<line x1="100" x2="100" y1="{y-6}" y2="{y+46}" stroke="{INK}" stroke-width="3">'
            f'<animate attributeName="x1" from="100" to="620" begin="{begin:g}s" dur="2s" fill="freeze"/>'
            f'<animate attributeName="x2" from="100" to="620" begin="{begin:g}s" dur="2s" fill="freeze"/></line>')
    return Graphic(out+cursor,out)


def scene():
    tl=Timeline(720,470,12,(
        Beat('完整周期',0,3,'一个 10 µs 周期，两段死区合计 100 ns。',INK),
        Beat('换流路径',3,6,'死区由体二极管续流；开通后沟道接管。',RED),
        Beat('每次能量',6,9,'0.8 V × 5 A × 100 ns = 0.4 µJ / 周期。',BLUE),
        Beat('平均损耗',9,12,'0.4 µJ × 100 kHz = 0.04 W，即 40 mW。',INK,hold=True),
    ),'死区损耗：时间单位不能漏掉一位','示意两次各 50 ns；分清单次换流与整个开关周期')
    layers=[Layer(None,timing())]
    for index,beat in enumerate(tl.beats):
        if index==1: layers.append(Layer(beat.name,closeup(3.3)))
        elif index>=2:
            layers.append(Layer(beat.name,text(100,253,'P瞬时 = 0.8 V × 5 A = 4 W',24,RED)
                                +text(100,302,'E周期 = 4 W × 100 ns = 0.4 µJ',24,BLUE)
                                +(text(100,351,'P平均 = 0.04 W = 40 mW',26) if index==3 else '')))
    return tl,layers


def storyboard():
    out=print_header('死区损耗：先计完整周期，再乘频率',750,'两段死区合计一百纳秒，平均损耗四十毫瓦。')
    out += [timing(),closeup(),text(36,405,'③ 每周期：0.8 V × 5 A × 100 ns = 0.4 µJ。',22),
            text(36,458,'④ 每秒：0.4 µJ × 100 kHz = 0.04 W = 40 mW。',22),
            text(36,520,'沟道导通时：5 A × 30 mΩ = 0.15 V。',20),
            text(36,565,'体二极管在死区承受 0.8 V；该损耗须单独核算。',20),
            text(36,620,'两段合计 100 ns，不能再重复乘两次。',20),
            text(36,675,'死区仍须覆盖关断延迟与传播差，不能按零设置。',20),'</svg>']
    return '\n'.join(out)


META={'id':'ch04-deadtime-energy-v2','chapter':4,'source':'docs/p1-05-ch4.md','anchor':'4.4',
      'type':'A1','style_id':'FA-029','layout_id':'IG-013','purpose':'按完整周期核算死区能量与平均损耗',
      'alt':'十微秒周期内两段死区各五十纳秒，体二极管承受零点八伏、五安；每周期零点四微焦，乘一百千赫为零点零四瓦，即四十毫瓦。放大的单次换流图标明独立尺度。',
      'en_prompt':'Show the complete switching-period timing strip and a separately labelled commutation close-up. Count both dead intervals once, then convert voltage-current-time energy to average power with explicit units.',
      'numbers':[{'value':'0','label':'示意','reason':'时间轴原点。'}],'scene':scene,'storyboard':storyboard}
