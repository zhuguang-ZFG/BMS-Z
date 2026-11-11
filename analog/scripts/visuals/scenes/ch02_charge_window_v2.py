"""Equal charge does not imply equal peak current: integrate drawn pulse shapes."""
from __future__ import annotations

from html import escape
from scripts.visuals.primitives import Graphic, line, text
from scripts.visuals.render import Layer
from scripts.visuals.timeline import Beat, Timeline
from scripts.visuals.static_fig import paper_layers

INK, BLUE, RED, GREEN, GRAY = '#16202b', '#1f5d7a', '#a8321f', '#3d6b4a', '#5b666f'
PERIOD_MS, WINDOW_MS, LOAD_A = 10.0, 3.0, 1.0


def pulse(kind: str) -> list[tuple[float, float]]:
    """Physical coordinates in milliseconds and amperes, with exact area 10 mC."""
    average = LOAD_A * PERIOD_MS / WINDOW_MS
    if kind == 'load':
        return [(0, LOAD_A), (PERIOD_MS, LOAD_A)]
    if kind == 'rectangle':
        return [(0, 0), (3.5, 0), (3.5, average), (6.5, average), (6.5, 0), (10, 0)]
    if kind == 'triangle':
        return [(0, 0), (3.5, 0), (5, 2 * average), (6.5, 0), (10, 0)]
    raise ValueError(kind)


def graph(kind, baseline=360, scale=30, color=BLUE, begin=None, identity='pulse'):
    points = pulse(kind)
    path = 'M' + ' L'.join(f'{82 + t * 55:g},{baseline - a * scale:g}' for t, a in points)
    area = path + f' L632,{baseline} L82,{baseline} Z'
    geometry = (f'<path data-pulse="{kind}" d="{area}" fill="{color}" fill-opacity=".13"/>'
                f'<path d="{path}" fill="none" stroke="{color}" stroke-width="3"'
                + (' stroke-dasharray="7 4"' if kind == 'triangle' else '') + '/>')
    if begin is None:
        return geometry
    animated = (f'<defs><clipPath id="{identity}"><rect x="82" y="{baseline-220}" width="0" height="225">'
                f'<animate attributeName="width" from="0" to="550" begin="{begin:g}s" dur="2s" fill="freeze"/>'
                '</rect></clipPath></defs>'
                f'<g clip-path="url(#{identity})">{geometry}</g>'
                f'<line x1="82" x2="82" y1="{baseline-210}" y2="{baseline}" stroke="{GRAY}" stroke-width="1.5">'
                f'<animate attributeName="x1" from="82" to="632" begin="{begin:g}s" dur="2s" fill="freeze"/>'
                f'<animate attributeName="x2" from="82" to="632" begin="{begin:g}s" dur="2s" fill="freeze"/>'
                '</line>')
    return Graphic(animated, geometry)


def scene():
    tl = Timeline(720, 470, 12, (
        Beat('负载耗电', 0, 3, '1 A × 10 ms：负载每周期取走 10 mC。', BLUE),
        Beat('矩形补电', 3, 6, '矩形示意：3 ms × 3.3 A，补回同一份电荷。', GREEN),
        Beat('三角补电', 6, 9, '三角示意：面积相同，峰值约 6.7 A。', RED),
        Beat('同面积不同峰值', 9, 12, '3.3 A 是导通窗口平均值；实际峰值另查脉形。', INK, hold=True),
    ), '电流脉冲：面积相同，峰值可以不同', '示意脉形；时间轴相同，电流轴相同，阴影面积代表电荷')
    axes = (line(82, 360, 650, 360, INK, 2) + line(82, 360, 82, 115, INK, 2)
            + text(30, 120, 'A', 18) + text(82, 387, '0', 18)
            + text(632, 387, '10 ms', 18, anchor='end'))
    layers = [Layer(None, axes)]
    for beat, kind, color, label in zip(tl.beats[:3], ['load', 'rectangle', 'triangle'],
                                       [BLUE, GREEN, RED], ['1 A', '3.3 A', '6.7 A']):
        layers += [Layer(beat.name, graph(kind, color=color, begin=beat.start + .4, identity=kind)),
                   Layer(beat.name, text(110, 110, label + '；面积 10 mC', 22, color))]
    layers += [Layer(tl.beats[-1].name, graph('rectangle', color=GREEN) + graph('triangle', color=RED)
                     + text(110, 110, '实线矩形 / 虚线三角：都补回 10 mC', 22, INK))]
    return tl, layers


def storyboard():
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 720" role="img" aria-labelledby="title desc">',
             '<title id="title">充电窗口与峰值：四拍打印分镜</title>',
             '<desc id="desc">三个波形同时间轴、同电流比例；矩形与三角面积相同，三角峰值为两倍。</desc>',
             paper_layers(720, 720), text(36, 34, '充电窗口：同电荷，不同峰值', 24),
             text(36, 64, '示意脉形；所有行共用电流比例和 10 ms 周期', 18)]
    for index, (kind, color, caption) in enumerate([
        ('load', BLUE, '① 负载：1 A × 10 ms = 10 mC'),
        ('rectangle', GREEN, '② 矩形：导通 3 ms，平均约 3.3 A'),
        ('triangle', RED, '③ 三角：同样 3 ms，峰值约 6.7 A'),
    ]):
        y = 100 + index * 175
        parts += [text(36, y, caption, 20, color), graph(kind, baseline=y+100, scale=12, color=color),
                  line(82, y+100, 632, y+100, INK, 1.5), text(82, y+127, '0', 18),
                  text(632, y+127, '10 ms', 18, anchor='end')]
    parts += [text(36, 653, '④ 先守电荷，再验峰值：不能用平均值替代额定峰值。', 20),
              text(36, 686, '实际波形由源阻、管子、电容与 ESR 联合决定。', 18), '</svg>']
    return '\n'.join(parts)


META = {
    'id': 'ch02-charge-window-v2', 'chapter': 2, 'anchor': '2.10.5', 'type': 'A2',
    'source': 'docs/p1-03-ch2.md', 'style_id': 'FA-029', 'layout_id': 'IG-015',
    'purpose': '电荷面积相同不代表电流峰值相同',
    'alt': '相同坐标轴上的三种电流：1 安负载持续 10 毫秒耗电 10 毫库；3 毫秒矩形脉冲平均 3.3 安，三角脉冲峰值 6.7 安，两者补回同一份电荷。示意脉形，不能替代实际整流仿真。',
    'en_prompt': 'Compare charge as the area under load, rectangular and triangular current traces. Keep the same time and current scales. Sweep a cursor at constant physical time. Distinguish the conduction-window mean from the peak; label the pulses as illustrative shapes.',
    'numbers': [{'value': '0', 'label': '示意', 'reason': '时间轴原点；不是额外的器件参数。'}],
    'scene': scene, 'storyboard': storyboard,
}
