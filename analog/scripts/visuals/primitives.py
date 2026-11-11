"""可复用 SVG 图元和动作；每个动作带确定性静态版本，打印不残留 SMIL。"""
from dataclasses import dataclass
from html import escape
import math

from .tokens import APPROVED, BODY_SIZE, EASE_IN_OUT


@dataclass(frozen=True)
class Graphic:
    animated: str
    final: str


def text(x, y, value, size=BODY_SIZE, colour=APPROVED.ink, anchor='start'):
    return (f'<text x="{x:g}" y="{y:g}" font-size="{size:g}" fill="{colour}" '
            f'text-anchor="{anchor}">{escape(str(value))}</text>')


def line(x1, y1, x2, y2, colour=APPROVED.ink, width=4, dash=''):
    return (f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" '
            f'stroke="{colour}" stroke-width="{width:g}" stroke-dasharray="{dash}"/>')


def directed_arrow(x1, y1, x2, y2, colour=APPROVED.ink, width=2.5):
    """Follow the actual shaft, including left and vertical paths."""
    length=math.hypot(x2-x1,y2-y1)
    if not length:
        raise ValueError('An arrow needs distinct endpoints')
    ux,uy=(x2-x1)/length,(y2-y1)/length
    bx,by=x2-10*ux,y2-10*uy
    return (line(x1,y1,x2,y2,colour,width)+
            f'<polygon points="{x2:g},{y2:g} {bx-5*uy:g},{by+5*ux:g} {bx+5*uy:g},{by-5*ux:g}" fill="{colour}"/>')


def resistor(x, y, width=150, height=54, label='R'):
    return (line(x - 30, y, x, y) + line(x + width, y, x + width + 30, y)
            + f'<rect x="{x:g}" y="{y - height / 2:g}" width="{width:g}" height="{height:g}" '
            f'fill="{APPROVED.paper}" stroke="{APPROVED.ink}" stroke-width="4"/>'
            + text(x + width / 2, y - height / 2 - 18, label, anchor='middle'))


def reveal_path(path, begin, duration, colour=APPROVED.accent, width=7):
    base = f'<path d="{path}" pathLength="1" fill="none" stroke="{colour}" stroke-width="{width:g}"'
    animated = (base + ' stroke-dasharray="1" stroke-dashoffset="1">'
                + f'<animate attributeName="stroke-dashoffset" from="1" to="0" begin="{begin:g}s" '
                f'dur="{duration:g}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="{EASE_IN_OUT}"/></path>')
    return Graphic(animated, base + '/>')


def current_flow(path, begin, duration):
    # 表示约定电流方向的一个标记，单次走完整条路径，不暗示电子漂移速度。
    animated = (f'<circle r="10" fill="{APPROVED.accent}"><animateMotion path="{path}" '
                f'begin="{begin:g}s" dur="{duration:g}s" fill="freeze" calcMode="spline" '
                f'keyPoints="0;1" keyTimes="0;1" keySplines="{EASE_IN_OUT}"/></circle>')
    return Graphic(animated, '')


def focus(x, y, width, height, begin, duration=.5):
    base = (f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" '
            f'rx="8" fill="none" stroke="{APPROVED.accent}" stroke-width="5"')
    return Graphic(base + ' opacity="0">' +
                   f'<animate attributeName="opacity" from="0" to="1" begin="{begin:g}s" dur="{duration:g}s" fill="freeze"/></rect>',
                   base + '/>')


def camera(body, begin, duration, dx=0, dy=0):
    animated = (f'<g>{body}<animateTransform attributeName="transform" type="translate" '
                f'from="0 0" to="{dx:g} {dy:g}" begin="{begin:g}s" dur="{duration:g}s" '
                f'fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="{EASE_IN_OUT}"/></g>')
    return Graphic(animated, f'<g transform="translate({dx:g} {dy:g})">{body}</g>')


def parameter_sweep(y, x_from, x_to, begin, duration, label):
    body = f'<circle cy="{y:g}" cx="{x_from:g}" r="12" fill="{APPROVED.accent}">'
    animated = (body + f'<animate attributeName="cx" from="{x_from:g}" to="{x_to:g}" '
                f'begin="{begin:g}s" dur="{duration:g}s" fill="freeze" calcMode="spline" '
                f'keyTimes="0;1" keySplines="{EASE_IN_OUT}"/></circle>')
    final = f'<circle cy="{y:g}" cx="{x_to:g}" r="12" fill="{APPROVED.accent}"/>'
    return Graphic(animated + text(x_to, y - 25, label, anchor='middle'),
                   final + text(x_to, y - 25, label, anchor='middle'))


def combine(*graphics):
    return Graphic(''.join(g.animated if isinstance(g, Graphic) else g for g in graphics),
                   ''.join(g.final if isinstance(g, Graphic) else g for g in graphics))
