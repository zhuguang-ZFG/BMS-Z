"""Refine the existing signal-budget / protection-debounce six-frame sequences.

Reuses the established precision pass typography and margins. All timings and
voltages below are teaching examples, not firmware settings or measured limits.
"""
from dataclasses import dataclass
from pathlib import Path

from gen_handraw_refined_pair import INK, footer, line, path, rect, shell, text

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/circuits/handraw/storyboard'
RED = '#E34234'

BUDGET = (('采样', 8.0), ('估算', 3.0), ('判决', 1.0), ('执行', 0.2))
WINDOW = 20.0
THRESHOLD = 4.25
RELEASE = 4.15
# Explicit steps avoid suggesting a different threshold-crossing time through
# interpolation. The short excursion ends before frame 2 is observed.
EVENTS = ((0.0, 4.12), (11.0, 4.27), (16.0, 4.12), (20.0, 4.27),
          (42.0, 4.20), (48.0, 4.12))
REVEAL = (10.0, 16.5, 34.0, 40.0, 46.0, 50.0)


@dataclass(frozen=True)
class ProtectionState:
    voltage: float
    elapsed: float
    closed: bool
    tripped_at: float | None


def protection_state(now: float) -> ProtectionState:
    """Continuous-time teaching delay with a hysteretic, non-latching release.

    This is only the drawing's state sequence, not a substitute for product
    protection firmware. The same event stream supplies waveform and timer.
    """
    voltage = EVENTS[0][1]
    above_since = None
    closed = True
    tripped_at = None
    for event_time, next_voltage in EVENTS[1:]:
        if event_time > now:
            break
        if above_since is not None and closed and event_time - above_since >= WINDOW:
            closed = False
            tripped_at = above_since + WINDOW
        voltage = next_voltage
        if voltage > THRESHOLD:
            if above_since is None:
                above_since = event_time
        else:
            above_since = None
        if voltage < RELEASE:
            closed = True
    if above_since is not None and closed and now - above_since >= WINDOW:
        closed = False
        tripped_at = above_since + WINDOW
    elapsed = 0.0 if above_since is None else min(now - above_since, WINDOW)
    return ProtectionState(voltage, elapsed, closed, tripped_at)


def budget(frame: int) -> str:
    completed = (0, 1, 2, 3, 4, 4)[frame - 1]
    cumulative = sum(duration for _, duration in BUDGET[:completed])
    total = sum(duration for _, duration in BUDGET)
    s = shell('一拍软件信号链 · 教学预算', '12.2 ms，时间花在哪一站？',
              '同一条累加尺看占比，右侧账栏看数值；硬件快速路径单独核验。', frame)
    s += text(70, 153, '软件串行路径', 16, weight='bold', font='KaiTi')
    s += text(641, 153, '长度按时间比例绘制', 12, 'end', 0.7)
    x0, width = 70, 570
    cumulative_before = 0.0
    for i, (_, duration) in enumerate(BUDGET):
        x = x0 + cumulative_before / total * width
        w = duration / total * width
        active = i < completed
        s += (f'<rect x="{x:.2f}" y="210" width="{w:.2f}" height="46" '
              f'fill="{INK}" fill-opacity="{0.14 if active else 0.025}" '
              f'stroke="{INK}" stroke-opacity="{0.85 if active else 0.25}" stroke-width="1.2"/>\n')
        cumulative_before += duration
    for value in (0.0, 8.0, 11.0, 12.2):
        x = x0 + value / total * width
        s += line(x, 264, x, 271, 1, 0.5)
        s += text(x, 292, f'{value:g}', 13, 'middle', 0.8)
    s += text(641, 320, '累计时间 / ms', 12, 'end', 0.7)
    cursor = x0 + cumulative / total * width
    s += f'<circle cx="{cursor:.2f}" cy="195" r="5" fill="{INK}"/>\n'
    s += text(70, 190, '采样段最长', 14, opacity=0.75)
    s += line(680, 136, 680, 444, 1, 0.2)
    s += text(704, 153, '本段 / 累计', 15, weight='bold', font='KaiTi')
    acc = 0.0
    for i, (name, duration) in enumerate(BUDGET):
        acc += duration
        y = 174 + i*54
        s += rect(700, y, 212, 47, 0.5 if i == completed - 1 else 0.16)
        s += text(713, y+20, f'{name}  +{duration:g} ms', 14,
                  opacity=1 if i < completed or frame == 1 else 0.6)
        s += text(899, y+39, f'累计 {acc:g} ms', 12, 'end', 0.75)
    s += text(704, 414, '当前落账', 12, opacity=0.65)
    s += text(910, 442, f'{cumulative:g} ms', 27, 'end', weight='bold')
    # Detached diagram: no arrow from the software decision box to this lane.
    s += rect(70, 346, 570, 94, 0.3)
    s += text(87, 369, '软件链之外：硬件快速路径', 15, weight='bold', font='KaiTi')
    s += text(87, 402, '比较器', 16)
    s += path([(173,397),(224,397),(217,393),(224,397),(217,401)], 1.3)
    s += text(240, 402, '驱动 / 切断', 16)
    s += text(87, 425, '不计入 12.2 ms；反应时间必须另测、另列预算。', 12, opacity=0.8)
    notes = ['先认四站，再看哪一笔时间最重。',
             '先把采样时间记进账，后面的处理才有输入。',
             '估算再加 3 ms，累计到 11 ms。',
             '软件判决加 1 ms，不等于硬件比较器等了 1 ms。',
             '执行只加 0.2 ms；图上很窄，账栏里不能漏。',
             '8 + 3 + 1 + 0.2 = 12.2 ms：顺序与占比一起读。']
    return s + footer(notes[frame - 1], '示意预算，不是某颗 MCU 实测；软件链与硬件快速路径不能混成一本账。')


def waveform_points(now: float):
    points = [EVENTS[0]]
    previous = EVENTS[0][1]
    for tm, value in EVENTS[1:]:
        if tm > now:
            break
        points.extend(((tm, previous), (tm, value)))
        previous = value
    points.append((now, previous))
    return points


def debounce(frame: int) -> str:
    now = REVEAL[frame - 1]
    state = protection_state(now)
    s = shell('保护去抖与回差 · 教学示意', '超限，为什么没有立刻断？',
              '同一条波形驱动计时与开关；先躲过毛刺，再判断是否达到动作条件。', frame)
    x0, x1, top, bottom = 136, 638, 166, 391

    def tx(tm):
        return x0 + tm/50*(x1-x0)

    def vy(v):
        return bottom-(v-4.10)/0.20*(bottom-top)

    s += text(136, 144, '单体电压 / V', 13)
    s += line(x0, top, x0, bottom, 1.2, 0.45)
    s += line(x0, bottom, x1, bottom, 1.2, 0.45)
    for value, label in [(THRESHOLD, '阈值 4.25'), (RELEASE, '恢复 4.15')]:
        s += line(x0, vy(value), x1, vy(value), 1.1, 0.65, '6 5')
        s += text(121, vy(value)+4, label, 12, 'end', 0.85)
    for tm in (0, 10, 20, 40, 50):
        s += line(tx(tm), bottom+4, tx(tm), bottom+10, 1, 0.4)
        s += text(tx(tm), 420, str(tm), 12, 'middle', 0.75)
    s += text(638, 442, '时间 / ms', 12, 'end', 0.7)
    s += path([(tx(tm),vy(v)) for tm,v in waveform_points(now)], 2.1)
    s += line(tx(now),top,tx(now),bottom,0.9,0.23,'3 5')
    s += f'<circle cx="{tx(now):.2f}" cy="{vy(state.voltage):.2f}" r="4" fill="{INK}"/>\n'
    # Full trace appears only in the final frame; the first frame cannot imply a
    # future event has already happened.
    s += line(680,136,680,442,1,0.2)
    titles = ['正常：未计时', '毛刺回落：已清零', '持续超限：未计满',
              '确认满窗：切断', '回差区：仍断开', '低于恢复线：导通']
    s += text(704,160,titles[frame-1],18,weight='bold',font='KaiTi')
    s += text(704,194,'去抖计时 / 20 ms',13,opacity=0.75)
    s += rect(704,212,198,24,0.5)
    if state.elapsed:
        s += (f'<rect x="707" y="215" width="{192*state.elapsed/WINDOW:.2f}" '
              f'height="18" fill="{INK}" opacity="0.8"/>\n')
    s += text(704,273,f'{state.elapsed:g} / 20 ms',25,weight='bold')
    if frame == 4:
        s += f'<line x1="910" y1="211" x2="910" y2="237" stroke="{RED}" stroke-width="2.6" stroke-linecap="round"/>\n'
    # The blade joins both terminal dots when closed; no disconnected rails.
    s += line(704,332,742,332,1.7)
    s += line(840,332,900,332,1.7)
    if state.closed:
        s += line(742,332,840,332,2)
    else:
        s += line(742,332,813,302,2)
    for x in (742,840):
        s += f'<circle cx="{x}" cy="332" r="3.5" fill="{INK}"/>\n'
    s += text(704,368,'MOS：'+('导通' if state.closed else '断开'),17,weight='bold',font='KaiTi')
    context = [('未越限，不积累计时。','开关保持导通。'),
               ('短于窗口，回落即清零。','画面是清零后的状态。'),
               ('14 ms 还没到 20 ms。','超限仍在，开关尚未断。'),
               ('持续超限达到 20 ms。','此帧红色只标动作时刻。'),
               ('低于阈值，但未过恢复线。','计时为零，开关仍断开。'),
               ('这里只示意可恢复型。','锁存型还须另验清除条件。')]
    s += text(704,403,context[frame-1][0],12,opacity=0.8)
    s += text(704,428,context[frame-1][1],12,opacity=0.8)
    notes = ['去抖不是把所有故障都拖慢；这里只画一个可恢复型示例。',
             '毛刺结束时，电压回落、计时清零、开关不动作。',
             '越线多久，与此刻电压多高，是两件事。',
             '计满才切断：时间条件与开关动作必须对在同一帧。',
             '计时清零不等于允许恢复；回差条件还没有满足。',
             '去抖躲毛刺，回差防颤振；锁存需另外定义清除条件。']
    return s + footer(notes[frame-1], '阈值 4.25 V / 恢复 4.15 V / 去抖 20 ms 均为示意，不是产品设定值。')


def main():
    for slug, build in [('bms-signal-budget', budget), ('protection-debounce', debounce)]:
        for frame in range(1,7):
            target = OUT/slug/f'frame-{frame:02d}.svg'
            target.write_text(build(frame),encoding='utf-8',newline='\n')
            print(target.relative_to(ROOT))


if __name__ == '__main__':
    main()
