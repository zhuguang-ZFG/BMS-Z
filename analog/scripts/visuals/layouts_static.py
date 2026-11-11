"""静态纸层插图的构图库：只画无文字纸层，技术文字由 overlay 单独排。

六种布局对应六类教学职责，避免同一章连续三图同构：
- `steps`   V5 流程：编号步骤纵向推进；
- `two_col` V4 对比：两栏同构，左右各一组因果；
- `ledger`  V3 定量：行标签 + 条带 + 读数；
- `ladder`  V3 层级：自下而上叠加的预算、量级或推导；
- `matrix`  V4 边界：两轴四象限；
- `fanout`  V5 分诊：单入口扇出到互斥分支。

所有几何固定为 1448×1086（4:3）；文字最小 32px，对应 138mm 版心
约 8.7pt。数值只许来自 `source_facts` 小节，本模块不做换算。
"""
from __future__ import annotations

from .papercut import (
    PAPER, INK, SHADE, ACCENT, FACE, EDGE, W, H,
    sheet, text, line, arrow, chip, meter, probe, heatsink,
)

MUTED = SHADE
RULE = EDGE
PANEL = FACE
TINT = '#efe7dc'          # C-34 纸白与 C-35 石板灰之间的浅洗，不是新增主题色。


# ---------------------------------------------------------------- 公共件
def header(title: str, subtitle: str, size: int = 50) -> list[str]:
    return [
        text(72, 92, title, size, weight='700', background=PAPER),
        text(74, 146, subtitle, 32, colour=SHADE, background=PAPER),
    ]


def footer(value: str, y: int = 986) -> list[str]:
    return [
        sheet(64, y, 1320, 78, fill=PANEL),
        text(92, y + 50, value, 33, weight='700', background=PANEL),
    ]


def _panel(x, y, w, h, stroke=RULE, fill=PANEL):
    return sheet(x, y, w, h, fill=fill) + (
        f'<path d="{_inner(x, y, w, h)}" fill="none" stroke="{stroke}" stroke-width="2" opacity=".55"/>')


def _inner(x, y, w, h):
    return (f'M{x + 18},{y + 14} L{x + w - 16},{y + 16} '
            f'L{x + w - 14},{y + h - 16} L{x + 20},{y + h - 14} Z')


def _number(cx, cy, colour=ACCENT):
    return f'<circle cx="{cx}" cy="{cy}" r="31" fill="{PAPER}" stroke="{colour}" stroke-width="3"/>'


def _tag(x, y, label, colour=ACCENT):
    return (f'<rect x="{x}" y="{y}" width="6" height="34" fill="{colour}"/>'
            + text(x + 16, y + 27, label, 32, colour=colour, weight='700'))


# ---------------------------------------------------------------- 流程
def steps(title, subtitle, items, takeaway, start_y=206, gap=148, card_h=122):
    """items: [(head, detail), ...]；4–5 步。"""
    base = [_panel(190, start_y - 12, 1186, gap * (len(items) - 1) + card_h + 24)]
    labels = header(title, subtitle)
    for i, (head, detail) in enumerate(items):
        y = start_y + i * gap
        base.append(_number(136, y + card_h // 2))
        labels.append(text(136, y + card_h // 2 + 12, '一二三四五六七八'[i], 34,
                           colour=ACCENT, anchor='middle', weight='700', background=PAPER))
        if i:
            base.append(arrow(136, y - 26, 136, y - 4, RULE, 3))
        labels.append(text(226, y + 46, head, 36, weight='700', background=PANEL))
        detail_lines = detail if isinstance(detail, (tuple, list)) else (detail,)
        for j, line_text in enumerate(detail_lines):
            labels.append(text(226, y + 88 + j * 36, line_text, 32, colour=SHADE, background=PANEL))
    labels += footer(takeaway)
    return base, labels


# ---------------------------------------------------------------- 对比
def two_col(title, subtitle, left, right, takeaway, tint_left=TINT, tint_right=PANEL):
    """left/right: {'head': str, 'items': [(head, note), ...], 'note': str}"""
    base = [
        _panel(64, 204, 620, 704, fill=tint_left),
        _panel(764, 204, 620, 704, fill=tint_right),
        f'<path d="M714,536 L754,536" stroke="{ACCENT}" stroke-width="3" stroke-dasharray="8,6"/>',
    ]
    labels = header(title, subtitle)
    for side, (panel_x, data) in enumerate(((64, left), (764, right))):
        labels.append(text(panel_x + 34, 268, data['head'], 42, weight='700',
                           colour=ACCENT if side == 0 else INK, background=data.get('bg', tint_left if side == 0 else tint_right)))
        labels.append(line(panel_x + 34, 292, panel_x + 586, 292, RULE, 2))
        for i, (head, note) in enumerate(data['items']):
            y = 344 + i * 128
            bg = data.get('bg', tint_left if side == 0 else tint_right)
            base.append(f'<rect x="{panel_x + 34}" y="{y - 24}" width="8" height="42" fill="{ACCENT if side == 0 else SHADE}"/>')
            labels.append(text(panel_x + 58, y + 6, head, 34, weight='700', background=bg))
            note_lines = note if isinstance(note, (tuple, list)) else (note,)
            for j, line_text in enumerate(note_lines):
                labels.append(text(panel_x + 58, y + 46 + j * 36, line_text, 32, colour=SHADE, background=bg))
        if data.get('note'):
            labels.append(text(panel_x + 34, 856, data['note'], 32, weight='700',
                               colour=SHADE, background=data.get('bg', tint_left if side == 0 else tint_right)))
    labels += footer(takeaway)
    return base, labels


# ---------------------------------------------------------------- 紧凑层级
def compact_ladder(title, subtitle, rows, takeaway):
    """rows 自下而上：[(label, value, note), ...]；最多 7 层，层高不编码数值。"""
    base = [_panel(64, 204, 1320, 704)]
    labels = header(title, subtitle)
    count = len(rows)
    for i, (label, value, note) in enumerate(rows):
        w = 1120 - (count - 1 - i) * 12
        x = 168 + (count - 1 - i) * 6
        y = 792 - i * 96
        base.append(sheet(x, y, w, 92, fill=PANEL if i % 2 == 0 else TINT))
        if i == count - 1:
            base.append(f'<path d="M{x + 20},{y + 10} L{x + w - 20},{y + 10}" stroke="{ACCENT}" stroke-width="4"/>')
        labels.append(text(x + 28, y + 40, label, 34, weight='700',
                           background=PANEL if i % 2 == 0 else TINT))
        labels.append(text(x + w - 26, y + 40, value, 34, weight='700',
                           colour=ACCENT if i == count - 1 else INK, anchor='end',
                           background=PANEL if i % 2 == 0 else TINT))
        labels.append(text(x + 28, y + 76, note, 32, colour=SHADE,
                           background=PANEL if i % 2 == 0 else TINT))
    base.append(arrow(110, 872, 110, 388, RULE, 3))
    labels += footer(takeaway)
    return base, labels


# ---------------------------------------------------------------- 定量账
def ledger(title, subtitle, rows, takeaway, value_head='读数'):
    """rows: [(label, note, ratio 0..1, value), ...]；条带长度只编码 ratio。"""
    base = [_panel(64, 204, 1320, 704)]
    labels = header(title, subtitle)
    labels.append(text(620, 268, '相对量级（定性条带）', 32, colour=SHADE, background=PANEL))
    labels.append(text(1200, 268, value_head, 32, colour=SHADE, background=PANEL))
    for i, (label, note, ratio, value) in enumerate(rows):
        y = 322 + i * 124
        labels.append(text(92, y + 38, label, 34, weight='700', background=PANEL))
        labels.append(text(92, y + 78, note, 32, colour=SHADE, background=PANEL))
        base.append(f'<rect x="620" y="{y + 18}" width="560" height="34" rx="8" fill="{PAPER}" stroke="{RULE}" stroke-width="1.4"/>')
        base.append(f'<rect x="620" y="{y + 18}" width="{max(10, min(1, ratio)) * 560:.1f}" height="34" rx="8" fill="{ACCENT}" opacity=".78"/>')
        labels.append(text(1200, y + 44, value, 34, weight='700', background=PANEL))
    labels += footer(takeaway)
    return base, labels


# ---------------------------------------------------------------- 层级
def ladder(title, subtitle, rows, takeaway):
    """rows 自下而上：[(label, value, note), ...]；层高相等，不编码数值。"""
    base = [_panel(64, 204, 1320, 704)]
    labels = header(title, subtitle)
    count = len(rows)
    for i, (label, value, note) in enumerate(rows):
        w = 1120 - (count - 1 - i) * 34
        x = 168 + (count - 1 - i) * 17
        y = 790 - i * 128
        base.append(sheet(x, y, w, 108, fill=PANEL if i % 2 == 0 else TINT))
        if i == count - 1:
            base.append(f'<path d="M{x + 20},{y + 12} L{x + w - 20},{y + 12}" stroke="{ACCENT}" stroke-width="4"/>')
        labels.append(text(x + 30, y + 48, label, 36, weight='700', background=PANEL if i % 2 == 0 else TINT))
        labels.append(text(x + w - 28, y + 48, value, 36, weight='700', colour=ACCENT if i == count - 1 else INK,
                           anchor='end', background=PANEL if i % 2 == 0 else TINT))
        labels.append(text(x + 30, y + 88, note, 32, colour=SHADE, background=PANEL if i % 2 == 0 else TINT))
    base.append(arrow(110, 872, 110, 388, RULE, 3))
    labels += footer(takeaway)
    return base, labels


# ---------------------------------------------------------------- 象限
def matrix(title, subtitle, x_label, y_label, quads, takeaway):
    """quads: 4 dicts {head, lines:[...]}，顺序 左下/右下/左上/右上。"""
    base = [
        _panel(286, 226, 1094, 652),
        arrow(300, 878, 1380, 878, RULE, 3),
        arrow(300, 878, 300, 226, RULE, 3),
    ]
    labels = header(title, subtitle)
    labels.append(text(842, 926, x_label, 33, colour=SHADE, anchor='middle', background=PAPER))
    labels.append(text(246, 552, y_label, 33, colour=SHADE, anchor='middle', background=PAPER))
    positions = [(300, 552), (842, 552), (300, 226), (842, 226)]
    for (x, y), q in zip(positions, quads):
        base.append(f'<rect x="{x + 12}" y="{y + 12}" width="512" height="296" fill="none" stroke="{RULE}" stroke-width="1.4" stroke-dasharray="6,6"/>')
        labels.append(text(x + 34, y + 56, q['head'], 36, weight='700', colour=ACCENT if q.get('hot') else INK, background=PAPER))
        for i, value in enumerate(q['lines']):
            labels.append(text(x + 34, y + 106 + i * 48, value, 32, colour=SHADE, background=PAPER))
    labels += footer(takeaway)
    return base, labels


# ---------------------------------------------------------------- 分诊
def fanout(title, subtitle, center, branches, takeaway):
    """center: {'head','lines'}；branches: [{'head','note'}...]，2–4 支。"""
    base = [_panel(64, 392, 434, 286, fill=TINT)]
    labels = header(title, subtitle)
    labels.append(text(92, 456, center['head'], 40, weight='700', colour=ACCENT, background=TINT))
    for i, value in enumerate(center['lines']):
        labels.append(text(92, 506 + i * 44, value, 32, colour=SHADE, background=TINT))
    count = len(branches)
    top = 232
    step = 176
    for i, branch in enumerate(branches):
        y = top + i * step
        base.append(_panel(756, y, 628, 146))
        base.append(arrow(508, 536, 742, y + 73, RULE, 2.6))
        labels.append(text(786, y + 54, branch['head'], 35, weight='700', background=PANEL))
        labels.append(text(786, y + 96, branch['note'], 32, colour=SHADE, background=PANEL))
    labels += footer(takeaway)
    return base, labels


# ---------------------------------------------------------------- 波形
def waveform(title, subtitle, series, x_label, y_label, callouts, takeaway):
    """series: [(points, colour, dash, label)]；points 为画布坐标。"""
    base = [_panel(64, 204, 1320, 704), arrow(190, 830, 1340, 830, RULE, 3), arrow(190, 830, 190, 238, RULE, 3)]
    labels = header(title, subtitle)
    labels.append(text(760, 884, x_label, 32, colour=SHADE, anchor='middle', background=PANEL))
    labels.append(text(132, 520, y_label, 32, colour=SHADE, anchor='middle', background=PANEL))
    drawn = 0
    for points, colour, dash, label in series:
        base.append(f'<polyline points="{points}" fill="none" stroke="{colour}" stroke-width="5" stroke-dasharray="{dash}"/>')
        if label:
            labels.append(text(1020, 250 + drawn * 44, label, 32, colour=colour, background=PANEL))
            drawn += 1
    for x, y, value in callouts:
        labels.append(text(x, y, value, 32, weight='700', colour=ACCENT, background=PANEL))
    labels += footer(takeaway)
    return base, labels
