"""Separate the gate-charge, driver-current and energy ledgers without mixing units."""
from scripts.visuals.primitives import Graphic,line,text
from scripts.visuals.plotting import print_header
from scripts.visuals.render import Layer
from scripts.visuals.timeline import Beat,Timeline
INK,BLUE,RED,GREEN='#16202b','#1f5d7a','#a8321f','#3d6b4a'
QG,VDRIVE,FREQUENCY,RESISTANCE=7e-9,10,100_000,10


def accounts():
    return {'average_a':QG*FREQUENCY,'power_w':QG*VDRIVE*FREQUENCY,'initial_a':VDRIVE/RESISTANCE}


def path(begin=None):
    body=(text(100,127,'本地去耦',22,BLUE)+text(470,127,'栅极电荷',22,GREEN)
          +line(150,150,150,190,INK,2)+line(110,190,190,190,INK,3)+line(110,203,190,203,INK,3)
          +line(150,203,150,240,INK,2)+line(150,150,280,150,INK,2)+line(410,150,530,150,INK,2)
          +f'<rect x="280" y="132" width="130" height="36" fill="none" stroke="{INK}" stroke-width="2"/>'
          +text(345,158,'驱动器',22,anchor='middle')
          +line(530,150,530,190,INK,2)+line(490,190,570,190,INK,3)+line(490,203,570,203,INK,3)
          +line(530,203,530,240,INK,2)+line(150,240,530,240,INK,2)
          +text(340,215,'示意电荷转移路径',18,anchor='middle'))
    if begin is None:return body
    moving=(f'<circle r="7" fill="{RED}"><animateMotion path="M150,150 L530,150" begin="{begin:g}s" dur="2s" fill="freeze"/></circle>')
    return Graphic(body+moving,body)


def scene():
    tl=Timeline(720,470,12,(
        Beat('搬运电荷',0,3,'每周期搬运 Qg = 7 nC；由近旁去耦提供瞬态电荷。',BLUE),
        Beat('平均供电',3,6,'7 nC × 100 kHz = 0.7 mA，属于平均供电账。',GREEN),
        Beat('峰值驱动',6,9,'10 V / 10 Ω = 1 A，只是初始峰值估计。',RED),
        Beat('功率归属',9,12,'Qg × Vdrv × f = 7 mW，分散耗在驱动回路。',INK,hold=True),
    ),'栅极驱动：平均电流小，瞬态电流大','7 nC、10 V、100 kHz 为同组示意条件；实际 Qg 要对齐测试条件')
    layers=[]
    for index,beat in enumerate(tl.beats):
        layers.append(Layer(beat.name,path(.3 if index==0 else None)))
        labels=[('Q = 7 nC / 周期',BLUE),('I平均 = 0.7 mA',GREEN),('I初始 ≈ 1 A',RED),('P驱动 = 7 mW',INK)]
        for row in range(index+1):
            label,color=labels[row]
            x=36 if row%2==0 else 375;y=304+(row//2)*58
            layers.append(Layer(beat.name,text(x,y,label,24,color)))
    return tl,layers


def storyboard():
    out=print_header('栅极驱动的四本账',740,'电荷、平均供电、初始峰值和驱动功率分别计算。')
    out += [path(),text(36,310,'① 电荷：Qg = 7 nC / 周期。',22,BLUE),
            text(36,362,'② 平均供电：Qg × 100 kHz = 0.7 mA。',22,GREEN),
            text(36,414,'③ 初始峰值：10 V / 10 Ω ≈ 1 A。',22,RED),
            text(36,466,'④ 驱动功率：7 nC × 10 V × 100 kHz = 7 mW。',22),
            text(36,530,'示意条件固定；实际电流随栅压与驱动器阻抗变化。',20),
            text(36,577,'平均电流用于供电预算，峰值用于驱动和去耦路径。',20),
            text(36,624,'驱动损耗分布在驱动器、外串电阻与内部栅阻。',20),
            text(36,677,'不能把全部 7 mW 都加进 MOSFET 的结温预算。',20),'</svg>']
    return '\n'.join(out)


META={'id':'ch04-gate-power-v2','chapter':4,'source':'docs/p1-05-ch4.md','anchor':'4.6',
      'type':'A1','style_id':'FA-029','layout_id':'IG-013','purpose':'分清峰值驱动能力、平均供电与驱动功率的归属',
      'alt':'每周期七纳库栅电荷，一百千赫时平均供电零点七毫安；十伏、十欧回路初始峰值约一安；平均驱动功率七毫瓦，分布在驱动器及栅极回路中，不全在 MOSFET 内。',
      'en_prompt':'Show charge transfer from local decoupling to the gate, then keep four ledgers with distinct units: charge, average current, initial current and average power. Do not draw unlike units on one magnitude scale or allocate all driver loss to the MOSFET.',
      'numbers':[],'scene':scene,'storyboard':storyboard}
