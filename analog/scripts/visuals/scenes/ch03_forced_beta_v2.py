"""Base drive is inversely proportional to forced beta at fixed load current."""
from scripts.visuals.primitives import Graphic, line, text
from scripts.visuals.render import Layer
from scripts.visuals.timeline import Beat, Timeline
from scripts.visuals.static_fig import paper_layers

INK, BLUE, RED, GREEN, GRAY = '#16202b', '#1f5d7a', '#a8321f', '#3d6b4a', '#5b666f'
LOAD_MA = 70


def base_ma(forced_beta):
    if forced_beta <= 0:
        raise ValueError('Forced beta must be positive')
    return LOAD_MA / forced_beta


def bar(beta, y, color, begin=None, previous=None):
    width = base_ma(beta) * 12
    end = (f'<rect data-beta="{beta}" x="140" y="{y}" width="{width:g}" height="26" '
           f'fill="{color}" stroke="{INK}"/>')
    if begin is None:
        return end
    start = 0 if previous is None else base_ma(previous) * 12
    anim = (f'<rect x="140" y="{y}" width="{start:g}" height="26" fill="{color}" stroke="{INK}">'
            f'<animate attributeName="width" from="{start:g}" to="{width:g}" begin="{begin:g}s" dur="1.8s" fill="freeze"/>'
            '</rect>')
    return Graphic(anim, end)


def scene():
    tl = Timeline(720, 470, 12, (
        Beat('固定负载', 0, 3, '保持 IC = 70 mA，强制 β 是 IC / IB 的设计比值。', INK),
        Beat('常用起点', 3, 6, '强制 β = 10：需要 7 mA 基流，先查 GPIO 能力。', BLUE),
        Beat('增加过驱动', 6, 9, '改成 2：基流升到 35 mA，过驱动增加。', RED),
        Beat('减少基流', 9, 12, '改成 50：基流降到 1.4 mA，饱和余量减小。', GREEN, hold=True),
    ), '强制 β 越小，基流越大', '示意：负载 70 mA 保持不变；不把设计比值当成器件保证')
    common = (text(36, 104, 'IC = 70 mA', 24) + line(140, 130, 560, 130, INK, 6)
              + text(140, 388, 'IB / mA：各行同一比例', 20))
    for value in [0, 7, 35]:
        x = 140 + value*12
        common += line(x, 166, x, 353, GRAY, 1, '3 5') + text(x, 370, str(value), 18, anchor='middle')
    layers = [Layer(None, common)]
    for index, beat in enumerate(tl.beats):
        if index == 0:
            layers.append(Layer(beat.name, text(140, 236, 'IB = 70 mA / βforced', 28)))
            continue
        for row, (beta, color) in enumerate([(10, BLUE), (2, RED), (50, GREEN)][:index]):
            y = 176 + row*62
            layers += [Layer(beat.name, text(36, y+21, f'β = {beta}', 20, color)
                             + text(640, y+21, f'{base_ma(beta):g} mA', 20, color, anchor='end')),
                       Layer(beat.name, bar(beta, y, color, beat.start+.4 if row==index-1 else None))]
    return tl, layers


def storyboard():
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 690" role="img" aria-labelledby="title desc">',
           '<title id="title">强制贝塔与基流四拍打印分镜</title>',
           '<desc id="desc">固定七十毫安负载，减小强制贝塔增大基流；三条电流条共用比例。</desc>',
           paper_layers(720, 690), text(36, 36, '① 固定负载：IC = 70 mA', 24),
           text(36, 76, '示意：IB = IC / βforced；三条基流条共用刻度', 20)]
    for row, (beta, color, caption) in enumerate([
        (10, BLUE, '② 常用起点：先查手册的饱和测试条件'),
        (2, RED, '③ 基流增加 5 倍：过驱动与存储电荷可能增加'),
        (50, GREEN, '④ 基流减为五分之一：饱和余量减小'),
    ]):
        y = 122 + row*130
        out += [text(36, y, caption, 20, color), text(36, y+52, f'β = {beta}', 20),
                bar(beta, y+30, color), text(650, y+52, f'{base_ma(beta):g} mA', 20, color, anchor='end')]
    out += [line(140, 486, 560, 486, INK, 2)]
    for value in [0, 7, 35]:
        out += [text(140+value*12, 516, str(value), 18, anchor='middle')]
    out += [text(620, 516, 'mA', 18), text(36, 569, '35 mA 可能超过 GPIO 能力；电阻不能凭 β 单独选。', 20),
            text(36, 608, '基流足够仍要实测 VCE(sat)、温升与关断时间。', 20),
            text(36, 649, '不按电流比虚构存储时间，具体值以器件手册和实测为准。', 18), '</svg>']
    return '\n'.join(out)


META = {
    'id': 'ch03-forced-beta-v2', 'chapter': 3, 'source': 'docs/p1-04-ch3.md', 'anchor': '3.5',
    'type': 'A2', 'style_id': 'FA-029', 'layout_id': 'IG-013', 'purpose': '明确强制 β 与基流、过驱动的反向关系',
    'alt': '固定 70 毫安负载，强制贝塔 10、2、50 分别要求 7、35、1.4 毫安基流；三条基流条按同一比例绘制。减小强制贝塔增加过驱动，增大强制贝塔降低饱和余量，仍须验证手册条件与 GPIO 能力。',
    'en_prompt': 'Keep collector load at 70 mA. Animate actual base-current bar lengths for forced beta 10, 2 and 50 on one scale. Explain overdrive direction without inventing storage times; print all stages with explicit numerical labels.',
    'numbers': [{'value': '0', 'label': '示意', 'reason': '基流坐标轴原点。'}],
    'scene': scene, 'storyboard': storyboard,
}
