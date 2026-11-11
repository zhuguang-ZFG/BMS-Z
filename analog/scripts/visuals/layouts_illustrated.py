"""带场景的纸雕版式：上半幅画现场，下半幅放紧凑的技术判据。

场景层只画无文字图形；电压、频率、判据和结论仍由技术层排字。
"""
from __future__ import annotations

from .papercut import (
    PAPER, INK, SHADE, ACCENT, FACE, EDGE,
    sheet, text, line, chip,
)
from .layouts_static import header, footer, _panel, TINT, PANEL, RULE


# ---------------------------------------------------------------- 场景零件
def board(x, y, w, h):
    parts = [sheet(x, y, w, h, fill=EDGE)]
    parts.append(f'<path d="M{x + 12},{y + 10} L{x + w - 14},{y + 12} '
                 f'L{x + w - 12},{y + h - 12} L{x + 14},{y + h - 10} Z" '
                 f'fill="none" stroke="{INK}" stroke-width="2" opacity=".28"/>')
    for cx, cy in ((x + 18, y + 18), (x + w - 18, y + 18),
                   (x + 18, y + h - 18), (x + w - 18, y + h - 18)):
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="{PAPER}" '
                     f'stroke="{INK}" stroke-width="1.6"/>')
    for offset in (44, 78, 112):
        parts.append(line(x + 30, y + h - offset, x + w - 40, y + h - offset,
                          SHADE, 1.4, '10,8'))
    return ''.join(parts)


def resistor(x, y, w=96, height=18):
    step = w / 8
    points = [(x, y)]
    for i in range(8):
        points.append((x + step * (i + .5), y - height if i % 2 == 0 else y + height))
    points.append((x + w, y))
    path = 'M' + ' L'.join(f'{px:.1f},{py:.1f}' for px, py in points)
    return f'<path d="{path}" fill="none" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'


def capacitor(x, y, scale=1.0):
    gap = 12 * scale
    width = 54 * scale
    return (
        line(x + width / 2, y - 34 * scale, x + width / 2, y - gap, INK, 4)
        + line(x, y - gap, x + width, y - gap, INK, 6)
        + line(x, y + gap, x + width, y + gap, INK, 6)
        + line(x + width / 2, y + gap, x + width / 2, y + 34 * scale, INK, 4)
    )


def probe(x, y, angle=0, length=86):
    """原点在探针尖，针体向上延伸；angle 为顺时针旋转角。"""
    return (
        f'<g transform="translate({x} {y}) rotate({angle})">'
        f'<polygon points="-3,0 3,0 0,-22" fill="{INK}"/>'
        f'<rect x="-9" y="{-length}" width="18" height="{length - 18}" rx="7" '
        f'fill="{EDGE}" stroke="{INK}" stroke-width="2"/>'
        f'<path d="M0,{-length} C-34,{-length - 18} -52,{-length + 26} -76,{-length + 16}" '
        f'fill="none" stroke="{SHADE}" stroke-width="3" stroke-linecap="round"/>'
        f'</g>'
    )


def scope(x, y, w=340, h=230, wave='sine'):
    parts = [
        sheet(x, y, w, h, fill=FACE),
        f'<rect x="{x + 22}" y="{y + 22}" width="{w - 100}" height="{h - 78}" rx="6" '
        f'fill="{PAPER}" stroke="{INK}" stroke-width="2.4"/>',
    ]
    left, right = x + 34, x + w - 92
    mid = y + 22 + (h - 78) / 2
    if wave == 'sine':
        amp = (h - 102) / 2
        path = (f'M{left},{mid} C{left + 24},{mid - amp} {left + 48},{mid - amp} {left + 72},{mid} '
                f'C{left + 96},{mid + amp} {left + 120},{mid + amp} {left + 144},{mid} '
                f'C{left + 168},{mid - amp} {left + 192},{mid - amp} {left + 216},{mid} '
                f'C{left + 240},{mid + amp} {left + 264},{mid + amp} {right},{mid}')
        parts.append(f'<path d="{path}" fill="none" stroke="{ACCENT}" stroke-width="4"/>')
    else:
        parts.append(line(left, mid, right, mid, ACCENT, 4))
    for i in range(3):
        cy = y + 44 + i * 46
        parts.append(f'<circle cx="{x + w - 48}" cy="{cy}" r="13" fill="{EDGE}" '
                     f'stroke="{INK}" stroke-width="2"/>')
    return ''.join(parts)


def dmm(x, y, scale=1.0, wave='flat'):
    parts = [
        f'<g transform="translate({x} {y}) scale({scale})">',
        sheet(0, 0, 112, 158, fill=EDGE),
        f'<rect x="14" y="18" width="84" height="44" rx="4" fill="{FACE}" '
        f'stroke="{INK}" stroke-width="2"/>',
    ]
    if wave == 'flat':
        parts.append(line(24, 40, 88, 40, ACCENT, 4))
    else:
        parts.append(f'<path d="M24,44 C34,26 44,26 54,44 C64,62 74,62 84,44" '
                     f'fill="none" stroke="{ACCENT}" stroke-width="3"/>')
    parts += [
        f'<circle cx="56" cy="101" r="27" fill="{INK}"/>',
        line(56, 101, 70, 82, FACE, 5),
        f'<path d="M26,158v24H4v-16" fill="none" stroke="{INK}" stroke-width="4"/>',
        f'<path d="M86,158v24h22v-16" fill="none" stroke="{ACCENT}" stroke-width="4"/>',
        '</g>',
    ]
    return ''.join(parts)


def notebook(x, y, w=250, h=150):
    parts = [sheet(x, y, w, h, fill=PANEL)]
    for i in range(4):
        yy = y + 38 + i * 24
        parts.append(line(x + 22, yy, x + w - 24, yy - 2, SHADE, 1.6))
    parts.append(f'<path d="M{x + 22},{y + h - 26} L{x + 90},{y + h - 70} '
                 f'L{x + 150},{y + h - 22}" fill="none" stroke="{ACCENT}" stroke-width="3"/>')
    parts.append(line(x + 176, y + 26, x + 214, y + h - 22, INK, 5))
    parts.append(f'<polygon points="{x + 214},{y + h - 22} {x + 222},{y + h - 8} '
                 f'{x + 206},{y + h - 12}" fill="{INK}"/>')
    return ''.join(parts)


def preamp(x, y, w=150, h=112):
    parts = [sheet(x, y, w, h, fill=FACE)]
    parts.append(f'<rect x="{x + 18}" y="{y + 20}" width="{w - 36}" height="{h - 42}" '
                 f'fill="{PAPER}" stroke="{INK}" stroke-width="2"/>')
    parts.append(f'<circle cx="{x + 34}" cy="{y + h - 22}" r="8" fill="{ACCENT}"/>')
    parts.append(f'<circle cx="{x + 62}" cy="{y + h - 22}" r="8" fill="{EDGE}" '
                 f'stroke="{INK}" stroke-width="1.4"/>')
    return ''.join(parts)


def mug(x, y):
    return (
        sheet(x, y, 66, 82, fill=FACE)
        + f'<path d="M{x + 66},{y + 18} C{x + 100},{y + 18} {x + 100},{y + 64} {x + 66},{y + 64}" '
          f'fill="none" stroke="{INK}" stroke-width="5"/>'
        + f'<path d="M{x + 10},{y + 12} C{x + 18},{y - 2} {x + 28},{y + 6} {x + 34},{y - 2}" '
          f'fill="none" stroke="{SHADE}" stroke-width="2.4"/>'
    )


def spring_ground(x, y, length=54):
    points = []
    for i in range(7):
        points.append(f'{x + (8 if i % 2 == 0 else -8)},{y - i * length / 6:.1f}')
    return (f'<path d="M{x},{y} L' + ' L'.join(points) + '" fill="none" '
            f'stroke="{ACCENT}" stroke-width="3" stroke-linecap="round"/>')


# ---------------------------------------------------------------- 版式
def illustrated_two_col(title, subtitle, scene_base, scene_labels,
                        left, right, takeaway):
    """上半幅场景带，下半幅两栏技术判据；场景只承载关系，文字仍是判据。"""
    base = [sheet(64, 180, 1320, 260, fill=PANEL)]
    base += scene_base
    base += [_panel(64, 460, 620, 480, fill=TINT),
             _panel(764, 460, 620, 480, fill=PANEL)]
    labels = header(title, subtitle)
    labels += scene_labels
    for side, (panel_x, data, fill) in enumerate(((64, left, TINT), (764, right, PANEL))):
        labels.append(text(panel_x + 34, 516, data['head'], 40, weight='700',
                           colour=ACCENT if side == 0 else INK, background=fill))
        labels.append(line(panel_x + 34, 542, panel_x + 586, 542, RULE, 2))
        for i, (head, note) in enumerate(data['items']):
            y = 590 + i * 112
            base.append(f'<rect x="{panel_x + 34}" y="{y - 26}" width="8" height="42" '
                        f'fill="{ACCENT if side == 0 else SHADE}"/>')
            labels.append(text(panel_x + 58, y, head, 34, weight='700', background=fill))
            note_lines = note if isinstance(note, (tuple, list)) else (note,)
            for j, line_text in enumerate(note_lines):
                labels.append(text(panel_x + 58, y + 36 + j * 32, line_text, 32,
                                   colour=SHADE, background=fill))
        if data.get('note'):
            labels.append(text(panel_x + 34, 924, data['note'], 32, weight='700',
                               colour=SHADE, background=fill))
    labels += footer(takeaway, y=986)
    return base, labels


def hero_scene(title, subtitle, scene_base, scene_labels, takeaway):
    """整幅场景插图：现场占主体，标注只做短句索引。"""
    base = [sheet(64, 180, 1320, 720, fill=PANEL)]
    base += scene_base
    labels = header(title, subtitle)
    labels += scene_labels
    labels += footer(takeaway, y=986)
    return base, labels
