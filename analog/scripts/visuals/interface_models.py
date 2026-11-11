"""Analytical models and presentation helpers for interface teaching scenes."""
import math
from .primitives import text, line
from .plotting import print_header
from .timeline import Timeline, Beat

INK, BLUE, RED, GREEN, GRAY = '#16202b', '#1f5d7a', '#a8321f', '#42654d', '#5b666f'


def charging_accounts(tau_time, capacitance=20e-12, voltage=5):
    """Exact RC step energy: supply, stored, and resistor heat, in joules."""
    fraction = -math.expm1(-max(0, tau_time))
    supply = capacitance * voltage**2 * fraction
    stored = .5 * capacitance * (voltage * fraction)**2
    return supply, stored, supply - stored


def pullup_bounds(capacitance, supply=3.3, low=.4, sink=.003,
                  rise=300e-9, high=2.31, leakage=10e-6):
    return (supply-low)/sink, min(rise/(math.log(7/3)*capacitance),
                                (supply-high)/leakage)


def sink_accounts(sinks, pullups=1, supply=3.3, pullup=1000, on=25):
    """Equal ohmic sinks: bus voltage, total current, each sink current."""
    current = supply / (pullup/pullups + on/sinks)
    return current * on/sinks, current, current/sinks


def unpowered_rail(time_s, pullup=1e4, load=1e4, capacitance=1e-6,
                   supply=3.3, diode=.3):
    final = (supply-diode)*load/(pullup+load)
    tau = capacitance/(1/pullup+1/load)
    return final*(-math.expm1(-max(0, time_s)/tau))


def class_b(peak, rail=12, load=8):
    """Load power and per-device mean dissipation for an ideal class-B pair."""
    output = peak**2/(2*load)
    transistor = rail*peak/(math.pi*load)-peak**2/(4*load)
    return output, transistor


def timeline(title, subtitles, boundary):
    names = ['条件', '变化', '比较', '结论']
    return Timeline(720, 470, 12, tuple(
        Beat(name, i*3, (i+1)*3, caption, INK, hold=i==3)
        for i, (name, caption) in enumerate(zip(names, subtitles))), title, boundary)


def metadata(aid, anchor, kind, title, alt, prompt, scene, storyboard, ticks=()):
    return dict(id=aid, chapter=5, source='docs/p1-06-ch5.md', anchor=anchor,
                type=kind, style_id='FA-029', layout_id='IG-015' if kind=='A2' else 'IG-013',
                purpose=title, alt=alt, en_prompt=prompt, scene=scene, storyboard=storyboard,
                numbers=[dict(value=str(v), label='示意', reason='示意模型坐标刻度或归一化时间；不是器件保证值。') for v in ticks])


def print_scene(title, chart, steps, boundary):
    return '\n'.join(print_header(title, 740, boundary) + [chart] +
                     [text(36, 440+42*i, f'{i+1}. {s}', 20) for i,s in enumerate(steps)] +
                     [text(36, 660, boundary, 18), '</svg>'])


def axes(xmax, ymax, xticks, yticks, xunit, yunit, *, x0=100, y0=350, width=530, height=220):
    out = text(35, y0-height-20, yunit, 18)
    for y in yticks:
        yy = y0-height*y/ymax
        out += line(x0, yy, x0+width, yy, GRAY, 1, '3 5') + text(x0-12, yy+6, f'{y:g}', 18, anchor='end')
    for x in xticks:
        out += text(x0+width*x/xmax, y0+28, f'{x:g}', 18, anchor='middle')
    return out+text(680, y0+28, xunit, 18, anchor='end')
