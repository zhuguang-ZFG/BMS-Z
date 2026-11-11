"""Shared-axis RC curves with explicit 30–70 percent measurement endpoints."""
import math
from scripts.visuals.scenes.handdrawn_wave2 import BLUE, GREEN, INK, PAPER, RED, RULE, box, header, text


def charge(t_ns,resistance):
    return 3.3*(-math.expm1(-max(t_ns,0)*1e-9/(resistance*100e-12)))


def crossing(fraction,resistance):
    return -resistance*100e-12*math.log(1-fraction)*1e9


def open_drain_rise():
    parts=[header('上升时间量两个阈值之间',
                  '3.3 V、100 pF、从零充电的示意曲线；同一时间与电压刻度。')]
    for fraction in [0,.3,.7,1]:
        y=440-270*fraction
        parts += [f'<line x1="100" y1="{y}" x2="630" y2="{y}" stroke="{RULE}" stroke-dasharray="4 5"/>',
                  text(85,y+7,f'{fraction*100:g}%',22,anchor='end')]
    for t in [0,300,600]:
        parts.append(text(100+530*t/600,478,str(t),22,anchor='middle'))
    parts.append(text(650,512,'ns',22))
    for r,col,dash in [(1000,BLUE,''),(2200,GREEN,'9 5'),(4700,RED,'2 5')]:
        points=' '.join(f'{100+530*t/600:.3f},{440-270*charge(t,r)/3.3:.3f}' for t in range(601))
        parts.append(f'<polyline data-ohm="{r}" points="{points}" fill="none" stroke="{col}" stroke-width="3" stroke-dasharray="{dash}"/>')
    # Highlight both endpoints on only one curve; a rise-time interval is not an absolute deadline.
    for f in [.3,.7]:
        xx=100+530*crossing(f,2200)/600
        yy=440-270*f
        parts += [f'<circle cx="{xx}" cy="{yy}" r="6" fill="{GREEN}"/>',
                  f'<line x1="{xx}" y1="{yy}" x2="{xx}" y2="490" stroke="{GREEN}" stroke-dasharray="3 5"/>']
    x1,x2=[100+530*crossing(f,2200)/600 for f in [.3,.7]]
    parts += [f'<line x1="{x1}" y1="492" x2="{x2}" y2="492" stroke="{GREEN}" stroke-width="3"/>',
              text((x1+x2)/2,522,'2.2 kΩ：Δt = 186 ns',22,colour=GREEN,anchor='middle'),
              box(710,140,240,310,fill=PAPER),text(735,180,'30% → 70%',24,weight='700')]
    for i,(r,ns,col,dash) in enumerate([('1 kΩ',85,BLUE,''),('2.2 kΩ',186,GREEN,'9 5'),('4.7 kΩ',398,RED,'2 5')]):
        y=235+i*66
        parts += [text(735,y,r,22,colour=col),text(735,y+30,f'{ns} ns',24,colour=col,weight='700'),
                  f'<line x1="850" y1="{y-8}" x2="925" y2="{y-8}" stroke="{col}" stroke-width="3" stroke-dasharray="{dash}"/>']
    parts += [text(50,570,'零到 70% 为 1.204 RC；30%→70% 才是 0.8473 RC。',24),
              text(50,612,'300 ns 是两交点的时间差上限，不是横轴上的绝对时刻。',22),
              text(50,654,'低电平也须通过 VOL / IOL 保证；速度合格并不表示电流合格。',22)]
    return parts


SCENES={'ch05-open-drain-rise':dict(draw=open_drain_rise,title='开漏上升时间的测量端点',chapter=5,
    source='docs/p1-06-ch5.md',anchor='5.2',
    alt='三点三伏、一百皮法的 RC 充电曲线，分别使用一千欧、二点二千欧和四点七千欧。上升时间从百分之三十到百分之七十测量，约八十五、一百八十六和三百九十八纳秒；二点二千欧曲线标出两个交点。')}
