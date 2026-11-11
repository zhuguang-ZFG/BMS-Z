"""Replace legacy diagrams with physical coordinates and readable labels."""
from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER,BLUE,GREEN,INK,INK2,PAPER,RED,RULE,box,header,text,
)


def drain_current(vds,overdrive):
    # mu*Cox*W/L = 200 uA/V² * 10^4 = 2 A/V².
    return 2*(overdrive*vds-vds*vds/2) if vds<overdrive else overdrive**2


def output_regions():
    parts=[header('同一组模型，画出欧姆段与饱和段','示意长沟道；每条曲线固定过驱动电压；截止是另一组栅压条件。')]
    parts += [text(50,148,'ID / A',22),text(620,518,'VDS / V',22,anchor='end')]
    for v in [0,1,2,3,4,5]:
        x=100+v*100
        parts += [f'<line x1="{x}" y1="166" x2="{x}" y2="460" stroke="{RULE}" stroke-dasharray="4 6"/>',text(x,490,str(v),22,anchor='middle')]
    for a in [0,3,6,9]:
        y=460-a*30
        parts += [f'<line x1="100" y1="{y}" x2="600" y2="{y}" stroke="{RULE}" stroke-dasharray="4 6"/>',text(83,y+6,str(a),22,anchor='end')]
    for od,col,dash in [(1,BLUE,'4 5'),(2,GREEN,'10 5'),(3,RED,'')]:
        points=' '.join(f'{100+i*2.5:g},{460-30*drain_current(i*.025,od):.4f}' for i in range(201))
        parts += [f'<polyline data-overdrive="{od}" points="{points}" stroke="{col}" stroke-width="3" stroke-dasharray="{dash}" fill="none"/>',
                  text(610,466-30*od**2,f'{od} V',22,colour=col),
                  f'<circle cx="{100+100*od}" cy="{460-30*od**2}" r="6" fill="{col}"/>']
    parts += [box(690,130,260,355,fill=PAPER),text(714,169,'每个圆点：',24,weight='700'),
              text(714,207,'VDS = VGS − VTH',22),text(714,248,'圆点左侧：欧姆段',22),
              text(714,286,'圆点右侧：饱和段',22),text(714,335,'过驱动 3 V 时',22),
              text(714,373,'原点斜率 6 A/V',22),text(714,411,'RDS ≈ 0.17 Ω',22,colour=RED),
              text(714,456,'不含沟道长度调制',22),
              text(50,542,'μnCox = 200 µA/V²，W/L = 10⁴；三条曲线使用同一组参数。',24),
              text(50,590,'近原点才有 RDS ≈ 1 / [2 × (VGS − VTH)]，不能把整个欧姆段当直线。',22),
              text(50,635,'低于阈值时仍有亚阈值电流；60–100 mV / 十倍电流，不是频率单位。',22),
              text(50,677,'换到真实器件：核对栅压、结温、SOA 与保证的 RDS(on)。',22)]
    return parts


def switching_values(t):
    if t<=150: vg,vd,ic=2*t/150,20,0
    elif t<=400: vg,vd,ic=2+.9*(t-150)/250,20,5*(t-150)/250
    elif t<=560: vg,vd,ic=2.9,20-19.85*(t-400)/160,5
    else: vg,vd,ic=2.9+7.1*(t-560)/140,.15,5
    return vg,vd,ic,vd*ic


def switching_energy():
    parts=[header('同轴看四条波形，能量按转换分别记账','独立教学波形：20 V、5 A；平台 2.9 V，不能当成某型号的保证数据。')]
    for row,(label,maximum,col) in enumerate([('VGS',10,BLUE),('VDS',20,RED),('ID',5,INK),('P',100,AMBER)]):
        y=188+row*78
        parts += [text(50,y-28,label,24,colour=col,weight='700'),
                  f'<line x1="150" y1="{y}" x2="710" y2="{y}" stroke="{RULE}"/>']
        points=' '.join(f'{150+t*.8:g},{y-switching_values(t)[row]/maximum*54:.4f}' for t in range(701))
        parts += [f'<polyline data-quantity="{label}" points="{points}" fill="none" stroke="{col}" stroke-width="3"/>',
                  text(747,y-24,['0→10 V','20→0.15 V','0→5 A','峰值 100 W'][row],22,colour=col),
                  text(747,y+3,['平台 2.9 V','400–560 ns','150–400 ns','末态 0.75 W'][row],22)]
    for t in [0,150,400,560,700]:
        x=150+t*.8
        parts += [f'<line x1="{x:g}" y1="125" x2="{x:g}" y2="428" stroke="{RULE}" stroke-dasharray="4 6"/>',text(x,464,str(t),22,anchor='middle')]
    parts += [text(740,464,'ns',22),text(50,515,'开通重叠 410 ns：Eon ≈ ½ × 20 V × 5 A × 410 ns = 20.5 µJ。',22),
              text(50,557,'100 kHz 下开通部分约 2.05 W；总开关损耗还须加 Eoff × f。',24),
              text(50,603,'本图 0.15 V 残压积分约 20.56 µJ；0.75 W 导通功率不为零。',22),
              text(50,646,'Qg / Idrv = 700 ns 是总充电时间，不能直接替代 410 ns 重叠窗口。',22),
              text(50,685,'实际波形含非线性电容、反向恢复与寄生，最终按 v(t)i(t) 积分。',22)]
    return parts


SCENES={
    'ch04-output-regions':{'draw':output_regions,'title':'输出特性与原点导通电阻','chapter':4,'source':'docs/p1-05-ch4.md','anchor':'4.2',
                         'alt':'同一长沟道模型的三条输出曲线，过驱动一、二、三伏，夹断点分别在漏压一、二、三伏。过驱动三伏时原点斜率六安每伏，对应约零点一七欧；欧姆段并非全程直线，饱和电流分别为一、四、九安。'},
    'ch04-switching-energy-ledger':{'draw':switching_energy,'title':'开通能量与总开关损耗的区别','chapter':4,'source':'docs/p1-05-ch4.md','anchor':'4.6',
                                    'alt':'四条波形共用纳秒时间轴。电流在一百五十至四百纳秒上升，漏压在四百至五百六十纳秒下降；开通重叠四百一十纳秒，三角近似二十点五微焦，一百千赫下约二点零五瓦，仅是开通部分。导通末态仍有零点七五瓦。'},
}
