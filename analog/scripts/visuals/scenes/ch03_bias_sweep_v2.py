"""Loaded divider calculation and fixed-bias saturation on one current scale."""
from scripts.visuals.primitives import Graphic, line, text
from scripts.visuals.render import Layer
from scripts.visuals.timeline import Beat, Timeline
from scripts.visuals.static_fig import paper_layers

INK, RED, BLUE, GRAY = '#16202b', '#a8321f', '#1f5d7a', '#5b666f'
VCC, VBE, VSAT = 12, .7, .2
RB, RC, R1, R2, RE = 1_130_000, 2_000, 51_000, 9_100, 1_200


def collector_ma(beta, mode):
    if mode == 'fixed':
        return min(beta * (VCC - VBE) / RB, (VCC - VSAT) / RC) * 1000
    if mode == 'divider':
        vth = VCC * R2 / (R1 + R2)
        rth = R1 * R2 / (R1 + R2)
        return beta * (vth - VBE) / (rth + (beta + 1) * RE) * 1000
    raise ValueError(mode)


def coordinates(beta, mode, baseline=350, scale=36):
    return 100 + (beta - 100), baseline - scale * collector_ma(beta, mode)


def axes(baseline=350, scale=36):
    out = [line(100, baseline, 620, baseline, INK, 2), text(645, baseline+30, 'β', 20)]
    for current in [0, 3, 6]:
        y = baseline - scale * current
        out += [line(100, y, 600, y, GRAY, 1, '3 5'), text(88, y+6, str(current), 18, anchor='end')]
    for beta in [100, 300, 600]:
        out += [text(100+beta-100, baseline+28, str(beta), 18, anchor='middle')]
    out += [text(36, baseline-scale*6-16, 'IC / mA', 18)]
    return ''.join(out)


def trace(mode, begin=None, baseline=350, scale=36):
    points = [coordinates(beta, mode, baseline, scale) for beta in range(100, 601, 5)]
    pts = ' '.join(f'{x:g},{y:.4f}' for x, y in points)
    color = RED if mode == 'fixed' else BLUE
    path = f'<polyline data-model="{mode}" points="{pts}" fill="none" stroke="{color}" stroke-width="3"'
    path += (' stroke-dasharray="8 4"' if mode == 'divider' else '') + '/>'
    if begin is None:
        return path
    valsx = ';'.join(f'{x:g}' for x, _ in points)
    valsy = ';'.join(f'{y:.4f}' for _, y in points)
    clip = f'{mode}-{begin:g}'
    moving = (f'<defs><clipPath id="{clip}"><rect x="100" y="70" width="0" height="300">'
              f'<animate attributeName="width" from="0" to="500" begin="{begin:g}s" dur="2s" fill="freeze"/>'
              f'</rect></clipPath></defs><g clip-path="url(#{clip})">{path}</g>'
              f'<circle cx="{points[0][0]:g}" cy="{points[0][1]:.4f}" r="6" fill="{color}">'
              f'<animate attributeName="cx" values="{valsx}" begin="{begin:g}s" dur="2s" fill="freeze" calcMode="linear"/>'
              f'<animate attributeName="cy" values="{valsy}" begin="{begin:g}s" dur="2s" fill="freeze" calcMode="linear"/></circle>')
    return Graphic(moving, path)


def scene():
    tl = Timeline(720, 470, 12, (
        Beat('固定偏置', 0, 3, '固定偏置：β 增加，IC 上升，最终受负载限流。', RED),
        Beat('分压反馈', 3, 6, '分压偏置：基流加载与 RE 反馈一起进入计算。', BLUE),
        Beat('同轴比较', 6, 9, '同一组 β，同一根电流刻度；不能各自放大纵轴。', INK),
        Beat('保留边界', 9, 12, 'β 从 100 到 300：0.866 → 0.908 mA，约增 4.8%。', INK, hold=True),
    ), '偏置漂移：两条曲线共用一把尺', '示意模型：VBE 固定为 0.7 V；固定偏置限流 5.9 mA；温漂另算')
    layers = [Layer(None, axes())]
    for beat, modes in zip(tl.beats, [('fixed',), ('divider',), ('fixed', 'divider'), ('fixed', 'divider')]):
        for mode in modes:
            layers.append(Layer(beat.name, trace(mode, beat.start+.4 if beat is not tl.beats[-1] else None)))
        labels = (text(110, 88, '实线：固定偏置', 20, RED)
                  + text(390, 88, '虚线：分压偏置', 20, BLUE))
        layers.append(Layer(beat.name, labels))
    return tl, layers


def storyboard():
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 780" role="img" aria-labelledby="title desc">',
           '<title id="title">偏置漂移四拍分镜</title>', '<desc id="desc">两条曲线同轴；下方给出三组可复算电流和模型边界。</desc>',
           paper_layers(720, 780), text(36, 36, '① 固定偏置 / ② 分压反馈：同轴比较', 24),
           axes(330, 34), trace('fixed', baseline=330, scale=34), trace('divider', baseline=330, scale=34),
           text(110, 78, '实线：固定偏置', 20, RED), text(390, 78, '虚线：分压偏置', 20, BLUE),
           text(36, 404, '③ 同一组 β，分别代入两种电路', 22),
           text(36, 442, 'β', 20), text(240, 442, '固定偏置 / mA', 20, RED), text(470, 442, '分压偏置 / mA', 20, BLUE)]
    for row, beta in enumerate([100, 300, 600]):
        y = 478 + row*35
        out += [text(36, y, beta, 20), text(240, y, f'{collector_ma(beta, "fixed"):.3f}', 20, RED),
                text(470, y, f'{collector_ma(beta, "divider"):.3f}', 20, BLUE)]
    out += [text(36, 597, '④ 饱和不是 β 放大：固定偏置在 5.9 mA 截止增长。', 20),
            text(36, 635, '12 V；RB 1.13 MΩ，RC 2 kΩ；VBE 0.7 V，VCEsat 0.2 V。', 18),
            text(36, 670, '分压：R1 51 kΩ，R2 9.1 kΩ，RE 1.2 kΩ。', 18),
            text(36, 706, 'IC = β (VTH − VBE) / [RTH + (β + 1) RE]', 20),
            text(36, 746, '示意模型先算 β 漂移，再另算温漂、容差与摆幅。', 20), '</svg>']
    return '\n'.join(out)


META = {
    'id': 'ch03-bias-sweep-v2', 'chapter': 3, 'source': 'docs/p1-04-ch3.md', 'anchor': '3.4',
    'type': 'A2', 'style_id': 'FA-029', 'layout_id': 'IG-015', 'purpose': '同轴比较两种偏置的 β 灵敏度',
    'alt': '贝塔从 100 扫到 600，共用电流刻度：固定偏置从 1 毫安升至 5.9 毫安的饱和限流；分压偏置从 0.866 升至 0.919 毫安。贝塔 300 时分别为 3 与 0.908 毫安。温漂另算。',
    'en_prompt': 'Sweep beta linearly. Plot both calculated collector currents on the same axes. Clip fixed bias at the load limit, preserve divider loading, and label the constant-VBE model. Use dashed and solid lines for grayscale readability.',
    'numbers': [{'value': '0', 'label': '示意', 'reason': '电流坐标轴原点。'}],
    'scene': scene, 'storyboard': storyboard,
}
