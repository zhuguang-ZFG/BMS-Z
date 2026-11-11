"""由 Python 绘制的平视纸层：厚度不编码量值，去掉阴影后仍保留完整图意。"""
from __future__ import annotations

from html import escape

PAPER = '#e2d9cf'
INK = '#2a2927'
SHADE = '#535453'
ACCENT = '#a4441d'
FACE = '#f6f2ed'  # C-34 与白纸混合出的亮面，非额外主题色。
EDGE = '#c4b9ab'
W, H = 1448, 1086


def svg(elements):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">' + '\n'.join(elements) + '</svg>\n'


def cut_path(x, y, w, h):
    return (f'M{x + 4},{y + 2} L{x + w * .43},{y} L{x + w - 3},{y + 3} '
            f'L{x + w},{y + h * .57} L{x + w - 3},{y + h - 2} '
            f'L{x + w * .38},{y + h} L{x},{y + h - 4} Z')


def sheet(x, y, w, h, fill=FACE, shadow=True):
    d = cut_path(x, y, w, h)
    parts = []
    if shadow:
        for dx, dy, opacity in [(8, 12, .08), (4, 7, .12), (2, 3, .15)]:
            parts.append(f'<path data-paper-shadow="true" transform="translate({dx} {dy})" d="{d}" fill="{SHADE}" opacity="{opacity}"/>')
    parts.append(f'<path d="{d}" fill="{fill}" stroke="{EDGE}" stroke-width="1.4"/>')
    parts.append(f'<path d="M{x + 6},{y + 4}L{x + w - 7},{y + 5}" fill="none" stroke="#ffffff" stroke-width="2" opacity=".7"/>')
    return ''.join(parts)


def text(x, y, value, size=34, colour=INK, anchor='start', weight='400', background=FACE):
    return (f'<text x="{x}" y="{y}" fill="{colour}" font-size="{size}" font-weight="{weight}" '
            f'font-family="Microsoft YaHei,Noto Sans SC,sans-serif" text-anchor="{anchor}" '
            f'data-background="{background}">{escape(str(value))}</text>')


def line(x1, y1, x2, y2, colour=INK, width=3, dash=''):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour}" '
            f'stroke-width="{width}" stroke-dasharray="{dash}"/>')


def arrow(x1, y1, x2, y2, colour=INK, width=4):
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    ux, uy = math.cos(angle), math.sin(angle)
    points = f'{x2},{y2} {x2 - 13 * ux + 7 * uy},{y2 - 13 * uy - 7 * ux} {x2 - 13 * ux - 7 * uy},{y2 - 13 * uy + 7 * ux}'
    return line(x1, y1, x2, y2, colour, width) + f'<polygon points="{points}" fill="{colour}"/>'


def chip(x, y, size=100):
    parts = [sheet(x, y, size, size, fill=INK)]
    for fraction in (.2, .4, .6, .8):
        offset = size * fraction
        parts.extend([line(x - 12, y + offset, x, y + offset, SHADE, 7),
                      line(x + size, y + offset, x + size + 12, y + offset, SHADE, 7)])
    parts.append(f'<circle cx="{x + 18}" cy="{y + 18}" r="5" fill="{FACE}"/>')
    return ''.join(parts)


def heatsink(x, y, w=160, h=110):
    parts = [sheet(x, y + h - 24, w, 24, fill=EDGE)]
    for i in range(5):
        parts.append(sheet(x + 4 + i * (w - 20) / 4, y, 16, h - 12, fill=FACE))
    return ''.join(parts)


def meter(x, y):
    return (sheet(x, y, 102, 145, fill=EDGE)
            + f'<rect x="{x + 14}" y="{y + 18}" width="74" height="36" rx="3" fill="{FACE}" stroke="{INK}" stroke-width="2"/>'
            + f'<circle cx="{x + 51}" cy="{y + 92}" r="25" fill="{INK}"/>'
            + line(x + 51, y + 92, x + 64, y + 75, FACE, 5)
            + f'<path d="M{x + 24},{y + 144}v26h-25v-15" fill="none" stroke="{INK}" stroke-width="4"/>'
            + f'<path d="M{x + 76},{y + 144}v26h25v-15" fill="none" stroke="{ACCENT}" stroke-width="4"/>')


def probe(x, y):
    return (f'<path d="M{x},{y + 70} Q{x + 20},{y + 100} {x + 55},{y + 72}" stroke="{INK}" stroke-width="5" fill="none"/>'
            + sheet(x + 45, y + 12, 25, 78, fill=EDGE)
            + line(x + 58, y + 12, x + 58, y - 16, INK, 5))


def soldering_iron(x, y):
    return (sheet(x, y, 90, 34, fill=EDGE)
            + line(x + 90, y + 17, x + 126, y + 17, SHADE, 10)
            + f'<polygon points="{x + 126},{y + 12} {x + 150},{y + 22} {x + 126},{y + 22}" fill="{INK}"/>')
