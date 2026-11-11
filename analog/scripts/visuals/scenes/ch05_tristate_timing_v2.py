"""Output-drive timing uses disable maximum and enable minimum, plus skew."""
from scripts.visuals.interface_models import *
from scripts.visuals.primitives import text,line,reveal_path
from scripts.visuals.render import Layer

TITLE='三态交接，比较真正开始与停止驱动的时刻'
STEPS=['A 在零时刻收到禁用，最晚 30 ns 才高阻。',
       'B 的使能延迟最小 10 ns，不是命令到即驱动。',
       '命令只晚 5 ns → B 在 15 ns 驱动，重叠 15 ns。',
       '命令晚 30 ns → B 最早 40 ns 驱动，空档 10 ns。']
BOUNDARY='示意不含控制器偏差；实际须加时序裕量，空档不采样数据。'


def interval(delay,disable_max=30,enable_min=10):
    return delay+enable_min-disable_max


def x(t): return 170+t*8


def drawing(safe, show_b=True):
    start=40 if safe else 15
    out=text(40,95,'粗线为实际驱动；指令与输出之间有延迟',18)
    out+=text(40,170,'A 驱动',20)+line(x(0),165,x(30),165,BLUE,10)
    out+=text(40,245,'B 驱动',20)
    if show_b: out+=line(x(start),240,x(60),240,RED,10)
    out+=line(x(30),125,x(30),285,BLUE,2,'7 5')
    out+=line(x(start),200,x(start),285,RED,2,'7 5')
    for t in [0,15,30,40,60]:out+=text(x(t),310,str(t),18,anchor='middle')
    out+=text(690,310,'ns',18)
    out+=text(360,370,'空档 10 ns：允许，禁止采样' if safe else '重叠 15 ns：两路可能冲突',22,GREEN if safe else RED,anchor='middle')
    return out


def scene():
    tl=timeline(TITLE,STEPS,BOUNDARY)
    layers=[Layer(b.name,drawing(i==3,False)) for i,b in enumerate(tl.beats)]
    for i,b in enumerate(tl.beats):
        start=40 if i==3 else 15
        layers.append(Layer(b.name,reveal_path(f'M{x(start)},240 L{x(60)},240',b.start+.2,2,RED,10)))
    return tl,layers


def storyboard():
    return print_scene(TITLE,drawing(True),STEPS,BOUNDARY)


META=metadata('ch05-tristate-timing-v2','5.4','A2',TITLE,
    '三态驱动条共用纳秒轴。旧器件最晚三十纳秒释放，新器件使能最小十纳秒；指令间隔五纳秒可重叠十五纳秒，间隔三十纳秒则留十纳秒空档。',
    'Compare actual drive intervals using worst-case disable maximum and enable minimum. Distinguish command separation, drive overlap and legal undriven time.',scene,storyboard,[0,60])
