"""The same bias point has different linearized and exponential large-signal traces."""
import math
from scripts.visuals.primitives import Graphic, line, text
from scripts.visuals.render import Layer
from scripts.visuals.timeline import Beat, Timeline
from scripts.visuals.static_fig import paper_layers

INK, BLUE, RED, GRAY = '#16202b', '#1f5d7a', '#a8321f', '#5b666f'
VCC, ICQ, RC, VE, VT, VSAT = 12, .003, 2000, 1.8, .026, .2


def output_v(phase, input_pp_mv, model):
    vin = input_pp_mv / 2000 * math.sin(phase)
    if model == 'linear':
        return VCC - RC * ICQ * (1 + vin / VT)
    if model == 'exponential':
        return max(VE + VSAT, min(VCC, VCC - RC * ICQ * math.exp(vin / VT)))
    raise ValueError(model)


def axes(baseline=350, scale=20):
    out = []
    for voltage in [2, 6, 12]:
        y = baseline - voltage*scale
        out += [line(100, y, 630, y, GRAY, 1, '3 5'), text(88, y+6, f'{voltage} V', 18, anchor='end')]
    out += [text(100, baseline+27, '0', 18), text(630, baseline+27, '一周期', 18, anchor='end')]
    return ''.join(out)


def trace(amplitude, model, baseline=350, scale=20, begin=None):
    points = [(100 + 530*i/160, baseline-scale*output_v(2*math.pi*i/160, amplitude, model)) for i in range(161)]
    pts = ' '.join(f'{x:.4f},{y:.4f}' for x, y in points)
    color = BLUE if model == 'linear' else RED
    curve = f'<polyline data-model="{model}" data-input-pp-mv="{amplitude}" points="{pts}" fill="none" stroke="{color}" stroke-width="3"'
    curve += (' stroke-dasharray="8 5"' if model == 'linear' else '') + '/>'
    if begin is None:
        return curve
    identity = f'{model}-{amplitude}-{begin:g}'
    moving = (f'<defs><clipPath id="{identity}"><rect x="100" y="70" width="0" height="300">'
              f'<animate attributeName="width" from="0" to="530" begin="{begin:g}s" dur="2s" fill="freeze"/>'
              f'</rect></clipPath></defs><g clip-path="url(#{identity})">{curve}</g>')
    return Graphic(moving, curve)


def scene():
    tl = Timeline(720, 470, 12, (
        Beat('小信号', 0, 3, '输入 10 mVpp：线性化与指数模型已经略有差别。', BLUE),
        Beat('增大输入', 3, 6, '输入 35 mVpp：指数模型下沿先碰到 2 V。', RED),
        Beat('比较模型', 6, 9, '线性外推的 8 Vpp 余量，不是失真指标的保证。', INK),
        Beat('验收失真', 9, 12, '按失真要求减小输入或增加负反馈，再实测。', INK, hold=True),
    ), '共射级：没削波，也可能已有失真', '示意模型：VE 固定、忽略厄利效应；虚线线性化，实线指数律')
    layers = [Layer(None, axes())]
    for index, beat in enumerate(tl.beats):
        amplitude = 10 if index == 0 else 35
        layers.append(Layer(beat.name, text(100, 88, f'输入 {amplitude} mVpp；输出共用电压轴', 20)))
        for model in ['linear', 'exponential']:
            layers.append(Layer(beat.name, trace(amplitude, model, begin=beat.start+.4 if index<2 else None)))
    return tl, layers


def storyboard():
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 800" role="img" aria-labelledby="title desc">',
           '<title id="title">共射线性与削波四拍打印分镜</title>',
           '<desc id="desc">两幅同尺度波形比较十与三十五毫伏峰峰输入；虚线线性化，实线指数模型。</desc>',
           paper_layers(720, 800), text(36, 36, '虚线：小信号线性化 / 实线：指数模型', 22)]
    for index, amplitude in enumerate([10, 35]):
        baseline = 270 + index*270
        out += [text(36, baseline-195, f'{index+1}  输入 {amplitude} mVpp', 22), axes(baseline, 13)]
        for model in ['linear', 'exponential']:
            out.append(trace(amplitude, model, baseline, 13))
    out += [text(36, 610, '③ 8 Vpp 来自轨道余量；不能据此保证低失真。', 22),
            text(36, 650, '④ 减小输入或增加负反馈，并按失真要求验收。', 22),
            text(36, 694, '示意：VC = 12 − 6 exp(vBE / 26 mV)，下限 2 V。', 18),
            text(36, 730, 'Q 点：3 mA、RC 2 kΩ、VC 6 V、VE 1.8 V。', 18),
            text(36, 768, '固定发射极电位、忽略厄利效应；不替代器件仿真。', 18), '</svg>']
    return '\n'.join(out)


META = {
    'id': 'ch03-ce-linearity-v2', 'chapter': 3, 'source': 'docs/p1-04-ch3.md', 'anchor': '3.9',
    'type': 'A3', 'style_id': 'FA-029', 'layout_id': 'IG-015', 'purpose': '区分削波余量与低失真输入范围',
    'alt': '相同电压轴比较 10 与 35 毫伏峰峰输入；虚线为小信号线性化，实线为指数模型。指数模型输出不对称，35 毫伏时下沿已碰到 2 伏。8 伏峰峰轨道余量不能保证低失真。',
    'en_prompt': 'Plot linearized and exponential collector-voltage traces on identical axes at two input amplitudes. Reveal constant-time traces. Mark the lower voltage rail and distinguish clipping headroom from distortion. State the fixed-emitter teaching-model limits.',
    'numbers': [{'value': '0', 'label': '示意', 'reason': '时间轴原点。'}],
    'parameters': [{'name': 'input_pp_mv', 'label': '输入峰峰值', 'unit': 'mVpp', 'min': 10, 'max': 35, 'values': [10, 35]}],
    'scene': scene, 'storyboard': storyboard,
}
