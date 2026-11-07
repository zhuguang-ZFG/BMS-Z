"""Refine the existing roadmap / HPPC pair; SVG frames remain the editable source.

No new slug, palette, timing, manifest or renderer conventions.
HPPC traces come from bms-book/code/hppc_fit.py, not hand-shaped polylines.
"""
from pathlib import Path
import html
import importlib.util
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/circuits/handraw/storyboard'
INK = '#003153'
PAPER = '#f6f1e3'


def text(x, y, value, size=15, anchor='start', opacity=1, weight='normal', font='Microsoft YaHei'):
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" '
            f'text-anchor="{anchor}" fill="{INK}" opacity="{opacity}" '
            f'font-weight="{weight}">{html.escape(str(value))}</text>\n')


def line(x1, y1, x2, y2, width=1, opacity=1, dash=''):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{INK}" stroke-width="{width}" opacity="{opacity}" '
            f'stroke-dasharray="{dash}" stroke-linecap="round"/>\n')


def rect(x, y, w, h, opacity=0.2, fill='none'):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
            f'fill="{fill}" stroke="{INK}" stroke-width="1" stroke-opacity="{opacity}"/>\n')


def path(points, width=2, opacity=1, dash=''):
    d = 'M' + ' L'.join(f'{x:.2f},{y:.2f}' for x, y in points)
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{width}" '
            f'opacity="{opacity}" stroke-dasharray="{dash}" '
            'stroke-linejoin="round" stroke-linecap="round"/>\n')


def shell(eyebrow, title, subtitle, frame):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="560" viewBox="0 0 960 560">\n'
            '<defs><filter id="grain" x="0" y="0" width="100%" height="100%">'
            '<feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="2" seed="5"/>'
            '<feColorMatrix type="saturate" values="0"/></filter></defs>\n'
            f'<rect width="960" height="560" fill="{PAPER}"/>\n'
            '<rect width="960" height="560" filter="url(#grain)" opacity="0.045"/>\n'
            + text(44, 30, eyebrow, 12, opacity=0.65)
            + text(916, 30, f'{frame:02d} / 06', 12, 'end', opacity=0.65)
            + text(44, 70, title, 27, weight='bold', font='KaiTi')
            + text(44, 98, subtitle, 14, opacity=0.8)
            + line(44, 116, 916, 116, opacity=0.18))


def footer(note, detail):
    return (line(44, 462, 916, 462, opacity=0.18)
            + text(44, 488, note, 16)
            + text(44, 513, detail, 13, opacity=0.75)
            + text(916, 542, '原理示意 / 非实拍', 12, 'end', opacity=0.7)
            + '</svg>\n')


def roadmap(frame):
    labels = ['前置知识', '认识 BMS', '保护板实践', 'AFE + MCU', 'SOC·SOH 算法', '通信与集成', '精通与毕业']
    durations = ['建议 1–2 周', '建议 1 周', '建议 2–4 周', '建议 1–2 月', '建议 1–3 月', '建议 2–4 周', '持续']
    bounds = [66, 158, 250, 356, 510, 684, 790, 900]
    centers = [(a+b)/2 for a,b in zip(bounds, bounds[1:], strict=False)]
    shown = [0, 1, 3, 5, 7, 7][frame-1]
    s = shell('BMS 学习路线', '从一颗电芯，到产品级系统', '七个阶段，同一条路径；长段留给 AFE / MCU 与 SOC / SOH。', frame)
    s += text(44, 144, '建议用时为学习安排，不是按比例绘制的工期。', 12, opacity=0.65)
    s += line(66, 272, 900, 272, 1.5, 0.3)
    if shown:
        s += line(66, 272, bounds[shown], 272, 3.6)
    for i, x in enumerate(centers):
        active = i < shown
        s += line(bounds[i], 263, bounds[i], 281, 1.2, 0.4)
        s += f'<circle cx="{x}" cy="272" r="4" fill="{INK if active else PAPER}" stroke="{INK}" stroke-width="1.4"/>\n'
        if active or frame == 1:
            above = i % 2 == 0
            s += line(x, 229 if above else 287, x, 257 if above else 310, 1, 0.45)
            label_opacity = 1 if active else 0.62
            s += text(x, 179 if above else 334, f'阶段 {i}', 12, 'middle', 0.7)
            s += text(x, 204 if above else 359, labels[i], 17, 'middle', label_opacity, weight='bold', font='KaiTi')
            s += text(x, 226 if above else 382, durations[i], 13, 'middle', label_opacity)
        else:
            s += text(x, 300, str(i), 12, 'middle', 0.5)
    cursor = 54 if not shown else bounds[shown]
    s += f'<circle cx="{cursor}" cy="272" r="7" fill="{INK}"/>\n'
    s += line(900, 263, 900, 281, 1.2, 0.4)
    if frame == 6:
        s += text(480, 415, '业余每天 1–2 小时 · 约 4–8 个月', 17, 'middle')
        for x, label, detail in [(66, '动画与电路图', '随课程索引更新'), (350, '3 个 PC 可跑配套', '把机制变成可复算结果'), (634, '书单 · 术语 · 预算', '需要时回到这三个入口')]:
            s += rect(x, 438, 260, 74, 0.3)
            s += text(x+18, 467, label, 17, weight='bold', font='KaiTi')
            s += text(x+18, 493, detail, 13, opacity=0.75)
        s += text(916, 542, '原理示意 / 非实拍', 12, 'end', opacity=0.7) + '</svg>\n'
    else:
        notes = [
            ('先看全程，再选下一站。', '游标向右推进；节点逐步落位，终点保持开放。'),
            ('先把电压、电流与基本安全说清楚。', '阶段 0：先修知识不是旁支，而是后面每一次判断的底座。'),
            ('从认识保护，到亲手验证保护。', '短站先建立直觉，长站再进入采样、控制与估计。'),
            ('真正需要留时间的是中间两站。', 'AFE / MCU 与 SOC / SOH：既要理解机制，也要能复算、调试和验证。'),
            ('做成系统，不等于学习结束。', '通信与集成之后，毕业项目继续接住前面所有证据。'),
        ]
        s += footer(*notes[frame-1])
    return s


spec = importlib.util.spec_from_file_location('pulse_source', ROOT / 'bms-book/code/hppc_fit.py')
pulse_source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pulse_source)
t, voltage, measured_i, n_pre, n_pulse = pulse_source.simulate_pulse()
on, off = float(t[n_pre]), float(t[n_pre+n_pulse])
a = math.exp(-0.1/35.2)
current = np.zeros_like(t)
current[n_pre:n_pre+n_pulse] = 3.0
urc = np.zeros_like(t)
for k in range(1, len(t)):
    urc[k] = a*urc[k-1] + 0.016*(1-a)*current[k-1]
model_mv = (0.033*current+urc)*1000
measured_mv = (voltage-3.75)*1000
vjump = (voltage[n_pre:n_pre+3].mean()-voltage[n_pre-10:n_pre].mean())*1000
ijump = measured_i[n_pre:n_pre+3].mean()-measured_i[n_pre-10:n_pre].mean()
r0_est = vjump/ijump
fraction = 1-math.exp(-10/35.2)
rest_t = t[n_pre+n_pulse:]-off
rest_v = voltage[n_pre+n_pulse:]
best120 = pulse_source.fit_relaxation(rest_t, rest_v)
best40 = pulse_source.fit_relaxation(rest_t[rest_t <= 40], rest_v[rest_t <= 40])

def fit_error(best):
    _, tau, _, amp = best
    r1 = amp/(1-math.exp(-10/tau))/3
    return abs(r1-0.016)/0.016*100


def pulse(frame):
    s = shell('HPPC 六步解剖', '一次脉冲，三种读数', '先看瞬时跳变，再看极化建立，最后给渐近线足够长的窗口。', frame)
    x0, x1, top, bottom = 94, 644, 172, 316
    def tx(sec):
        return x0+sec/190*(x1-x0)

    def vy(mv):
        return top+mv/160*(bottom-top)
    s += text(94, 143, '电压偏移 / mV（正向朝下）', 13)
    s += line(94, top, 644, top, 0.8, 0.25)
    s += line(94, top, 94, bottom, 1.1, 0.5)
    s += line(94, bottom, 644, bottom, 0.8, 0.25)
    for mv in [0, 100, 160]:
        s += text(81, vy(mv)+4, str(mv), 12, 'end', 0.7)
    s += line(94, 378, 644, 378, 1.0, 0.4)
    s += line(94, 339, 94, 378, 1.0, 0.4)
    s += text(81, 348, '3 A', 12, 'end', 0.7) + text(81, 382, '0', 12, 'end', 0.7)
    for tm in [0, 60, 70, 110, 190]:
        s += line(tx(tm), 382, tx(tm), 387, 1, 0.4)
        # The adjacent injection/removal ticks use staggered labels, not overlapping digits.
        s += text(tx(tm), 404 if tm != 70 else 423, str(tm), 12, 'middle', 0.75)
    s += text(644, 442, '时间 / s', 12, 'end', 0.7)
    s += line(94, 434, 121, 434, 1.5, 0.75) + text(131, 439, '含噪仿真', 12, opacity=0.75)
    s += line(240, 434, 268, 434, 1.8, 1, '5 4') + text(278, 439, '无噪模型', 12, opacity=0.75)
    s += line(678, 136, 678, 442, 1, 0.2)
    # Frame 1 ends strictly before injection. Frame 4 ends before removal.
    stop = [n_pre-1, n_pre+1, n_pre+2, n_pre+n_pulse-1, n_pre+n_pulse+2, len(t)-1][frame-1]
    indices = sorted(set(list(range(0, stop+1, 3)) + [stop] + [i for i in [n_pre-1,n_pre,n_pre+n_pulse-1,n_pre+n_pulse] if i <= stop]))
    s += path([(tx(t[i]), vy(measured_mv[i])) for i in indices], 1.2, 0.65)
    s += path([(tx(t[i]), vy(model_mv[i])) for i in indices], 1.8, 1, '5 4')
    # Exact step corners: never draw an event before it has actually happened.
    steps = [(tx(0), 378)]
    if stop >= n_pre:
        steps += [(tx(on),378),(tx(on),344)]
    if stop >= n_pre+n_pulse:
        steps += [(tx(off),344),(tx(off),378)]
    steps += [(tx(t[stop]), 378-current[stop]/3*34)]
    s += path(steps, 2.0)
    titles = ['预静置','脉冲注入','欧姆跳变','极化建立','撤流回弹','窗口与可信度']
    s += text(706, 160, f'{frame:02d}  {titles[frame-1]}', 20, weight='bold', font='KaiTi')
    if frame == 1:
        s += text(706, 204, '电流为 0 A', 17)
        s += text(706, 249, '0 mV', 28, weight='bold')
        s += text(706, 278, '模型保持静置基线', 14)
        s += text(706, 308, '实线只含 1 mV 电压噪声', 12, opacity=0.75)
    elif frame == 2:
        s += text(706, 204, '+3 A · 10 s', 22, weight='bold')
        s += text(706, 249, '99.0 mV', 28, weight='bold')
        s += text(706, 280, '欧姆项立刻出现', 14)
        s += text(706, 313, '3 A × 33 mΩ', 14, opacity=0.75)
    elif frame == 3:
        s += text(706, 201, f'均值差 {vjump:.1f} mV', 17)
        s += text(706, 248, f'{r0_est:.2f} mΩ', 27, weight='bold')
        s += text(706, 279, 'R0 真值：33.00 mΩ', 14)
        s += text(706, 317, '前 1 s / 后 0.3 s 均值', 12, opacity=0.75)
        s += text(706, 342, '同一份 seed=7 数据复算', 12, opacity=0.75)
    elif frame == 4:
        s += text(706, 202, f'极化建立 {fraction*100:.1f}%', 17)
        s += text(706, 247, f'{urc[n_pre+n_pulse]*1000:.1f} mV', 28, weight='bold')
        s += text(706, 278, '这是 48 mV 极化满幅的一部分', 12)
        s += text(706, 316, '不是总偏移 147 mV 的 24.7%', 12, opacity=0.75)
        s += text(706, 345, 'τ = 35.2 s，脉冲仅 10 s', 12, opacity=0.75)
    elif frame == 5:
        s += text(706, 204, '撤掉的是欧姆项', 17)
        s += text(706, 249, '99.0 mV', 28, weight='bold')
        s += text(706, 280, '极化残余不会同时归零', 14)
        s += text(706, 317, '回弹尾巴才供 RC 拟合使用', 12, opacity=0.75)
    else:
        for yy,label,error in [(184,'40 s 窗',fit_error(best40)),(297,'120 s 窗',fit_error(best120))]:
            s += rect(701,yy,212,96,0.25)
            s += text(716,yy+25,label,15)
            s += text(716,yy+64,f'{error:.2f}%' if error < 1 else f'{error:.1f}%',26,weight='bold')
            s += text(716,yy+84,'R1 估计误差',12,opacity=0.7)
        for y, tm in [(192,110),(216,190)]:
            s += line(tx(off),y,tx(tm),y,1,0.5,'4 4')
            s += line(tx(tm),y-4,tx(tm),y+4,1,0.5)
        s += text(439,204,'40 s',11,'middle',0.8)
        s += text(573,229,'120 s',11,'middle',0.8)
    notes = ['预静置不抢跑：还没有电流台阶，也没有欧姆跳变。',
             '同一时刻看两条轨迹：电流一来，欧姆项立刻出现。',
             'R0 只读跳变附近；静置窗变短，不会替它改变读数。',
             '先分清满幅是谁的：极化支路满幅是 I·R1。',
             '撤流时欧姆项退出，极化残余按时间常数慢慢释放。',
             '同一份数据，只换观察窗：看见曲率，才能约束渐近线。']
    s += footer(notes[frame-1], '合成示例 · R0=33 mΩ / R1=16 mΩ / C1=2200 F · seed=7 · 噪声 1 mV / 5 mA')
    return s


def main():
    for slug, build in [('bms-roadmap', roadmap), ('hppc-pulse', pulse)]:
        for frame in range(1,7):
            p = OUT / slug / f'frame-{frame:02d}.svg'
            p.write_text(build(frame),encoding='utf-8',newline='\n')
            print(p.relative_to(ROOT))


if __name__ == '__main__':
    main()
