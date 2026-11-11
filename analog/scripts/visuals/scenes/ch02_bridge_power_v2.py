"""Trace both bridge paths, then sum four whole-cycle diode losses."""
from __future__ import annotations

from scripts.visuals.primitives import Graphic, line, text
from scripts.visuals.render import Layer
from scripts.visuals.timeline import Beat, Timeline
from scripts.visuals.static_fig import paper_layers

INK, BLUE, RED, GREEN, GRAY = '#16202b', '#1f5d7a', '#a8321f', '#3d6b4a', '#5b666f'
DIODE_VF, LOAD_A = .9, 1.0
POSITIONS = {'D1': (190, 178), 'D2': (400, 178), 'D3': (190, 310), 'D4': (400, 310)}
PATHS = {'positive': [(190, 245), (190, 115), (580, 115), (580, 375), (400, 375), (400, 245)],
         'negative': [(400, 245), (400, 115), (580, 115), (580, 375), (190, 375), (190, 245)]}


def diode(name, x, y):
    return (line(x, y-36, x, y+36, INK, 2)
            + f'<polygon points="{x-14},{y+15} {x+14},{y+15} {x},{y-13}" fill="#fdf8ea" stroke="{INK}" stroke-width="2"/>'
            + line(x-16, y-16, x+16, y-16, INK, 2.5) + text(x-44, y+5, name, 18))


def circuit():
    return (line(190, 115, 580, 115, INK, 2) + line(190, 375, 580, 375, INK, 2)
            + line(190, 115, 190, 375, INK, 2) + line(400, 115, 400, 375, INK, 2)
            + line(190, 245, 265, 245, INK, 2) + line(325, 245, 400, 245, INK, 2)
            + '<circle cx="295" cy="245" r="30" fill="#fdf8ea" stroke="#16202b" stroke-width="2"/>'
            + text(295, 253, 'AC', 18, anchor='middle')
            + line(580, 115, 580, 213, INK, 2) + line(580, 277, 580, 375, INK, 2)
            + '<rect x="566" y="213" width="28" height="64" fill="#fdf8ea" stroke="#16202b" stroke-width="2"/>'
            + text(608, 249, '负载', 18) + text(603, 143, '+', 20) + text(603, 364, '−', 20)
            + ''.join(diode(name, *pos) for name, pos in POSITIONS.items()))


def flow(polarity, begin):
    points = PATHS[polarity]
    path = 'M' + ' L'.join(f'{x},{y}' for x, y in points)
    color = BLUE if polarity == 'positive' else RED
    # Offset by 9 px from circuit wires: arrows remain visible without hiding diode symbols.
    trace = (f'<path data-current-path="{polarity}" d="{path}" transform="translate(9 0)" '
             f'fill="none" stroke="{color}" stroke-width="3" stroke-dasharray="7 4"/>'
             f'<polygon points="594,295 604,295 599,307" fill="{color}"/>')
    animated = trace + (f'<circle r="6" fill="{color}" transform="translate(9 0)">'
                         f'<animateMotion path="{path}" begin="{begin:g}s" dur="2s" fill="freeze"/></circle>')
    return Graphic(animated, trace)


def losses():
    per_diode = DIODE_VF * LOAD_A / 2
    return {name: per_diode for name in POSITIONS}


def ledger(y=150):
    parts = [text(50, y-28, '每管全周期平均：0.5 A × 0.9 V', 22)]
    for i, (name, watts) in enumerate(losses().items()):
        x = 65 + i * 165
        parts += [f'<rect data-diode="{name}" x="{x}" y="{y}" width="110" height="110" fill="{BLUE}" fill-opacity=".15" stroke="{BLUE}"/>',
                  text(x+55, y+42, name, 22, anchor='middle'), text(x+55, y+80, f'{watts:g} W', 22, anchor='middle')]
    parts += [text(360, y+168, '四管相加 = 1.8 W', 28, RED, anchor='middle'),
              text(360, y+208, '两只同时导通的系数，已包含半周轮换。', 20, anchor='middle')]
    return ''.join(parts)


def average_current():
    parts = [text(50, 112, '对称换向：每只轮到半周', 24)]
    for index, name in enumerate(POSITIONS):
        y = 150 + index * 50
        x = 200 if name in {'D1', 'D4'} else 375
        parts += [text(95, y+23, name, 20),
                  f'<rect x="200" y="{y}" width="350" height="30" fill="none" stroke="{GRAY}"/>',
                  f'<rect x="{x}" y="{y}" width="175" height="30" fill="{BLUE}" fill-opacity=".3"/>',
                  text(570, y+23, '0.5 A', 20)]
    parts += [text(200, 390, '正半周', 18), text(375, 390, '负半周', 18)]
    return ''.join(parts)


def scene():
    tl = Timeline(720, 470, 12, (
        Beat('正半周', 0, 3, 'D1、D4 导通；负载电流从上到下。', BLUE),
        Beat('负半周', 3, 6, 'D2、D3 接班；负载电流仍从上到下。', RED),
        Beat('单管平均', 6, 9, '对称换向：每管全周期平均 0.5 A。', GREEN),
        Beat('四管相加', 9, 12, '每管 0.45 W，四管合计 1.8 W。', INK, hold=True),
    ), '桥堆功耗：半周轮换，四管相加', '对称连续电流示意；负载 1 A，恒定管压降 0.9 V')
    layers = []
    for beat, polarity in zip(tl.beats[:2], ['positive', 'negative']):
        layers += [Layer(beat.name, circuit()), Layer(beat.name, flow(polarity, beat.start + .4))]
    layers += [Layer('单管平均', average_current()), Layer('四管相加', ledger())]
    return tl, layers


def storyboard():
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 800" role="img" aria-labelledby="title desc">',
             '<title id="title">桥堆功耗四拍分镜</title>',
             '<desc id="desc">正半周 D1 D4、负半周 D2 D3；每管平均 0.5 安，各 0.45 瓦，总计 1.8 瓦。</desc>',
             paper_layers(720, 800), text(36, 36, '桥堆：轮换导通，分开算平均再求和', 24),
             text(36, 70, '对称连续电流示意；1 A 负载，管压降 0.9 V', 18),
             circuit(), flow('positive', 0).final,
             flow('negative', 0).final.replace('translate(9 0)', 'translate(-9 0)').replace('7 4', '2 5'),
             text(36, 415, '① 长虚线：正半周 D1 → 负载 → D4', 20, BLUE),
             text(36, 451, '② 点线：负半周 D2 → 负载 → D3', 20, RED),
             text(36, 496, '③ 每管：平均 0.5 A × 0.9 V = 0.45 W', 22),
             text(36, 537, '④ 四管相加；不能再乘一次半周系数', 22)]
    for i, name in enumerate(POSITIONS):
        x = 42 + i * 168
        parts += [f'<rect x="{x}" y="565" width="135" height="85" fill="{BLUE}" fill-opacity=".12" stroke="{BLUE}"/>',
                  text(x+67, 596, name, 20, anchor='middle'), text(x+67, 631, '0.45 W', 22, anchor='middle')]
    parts += [text(360, 696, '总计 1.8 W = 2 × 0.9 V × 1 A', 24, RED, anchor='middle'),
              text(36, 739, '窄脉冲整流须积分 vF(t)i(t)，再查封装降额。', 18),
              text(36, 775, '每管平均电流成立的前提是对称换向。', 18), '</svg>']
    return '\n'.join(parts)


META = {
    'id': 'ch02-bridge-power-v2', 'chapter': 2, 'anchor': '2.12.1', 'type': 'A1',
    'source': 'docs/p1-03-ch2.md', 'style_id': 'FA-029', 'layout_id': 'IG-013',
    'purpose': '桥堆导通路径与四管平均功耗',
    'alt': '桥式整流两条电流路径：正半周 D1 与 D4、负半周 D2 与 D3，负载方向相同。对称 1 安负载、恒定 0.9 伏管压降，每管平均 0.5 安，各损耗 0.45 瓦，四管共 1.8 瓦。连续电流仅用于示意，实际窄脉冲要积分。',
    'en_prompt': 'Trace both real conduction paths of a full bridge with directed current markers. The load direction stays unchanged. Then add the four whole-cycle diode losses without double-counting the half-cycle duty factor. Label the continuous current and fixed forward drop assumptions.',
    'scene': scene, 'storyboard': storyboard,
}
