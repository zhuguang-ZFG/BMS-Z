"""A2 分压推导代表场景；公式由代码绘制，来源 ch0 §0.3。"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.visuals.timeline import Beat, Timeline
from scripts.visuals.render import Layer, write
from scripts.visuals.primitives import text, line, resistor, focus, camera, combine
from scripts.visuals.layouts import split_columns, equation_rows


def scene():
    beats = (
        Beat('空载条件', 0, 2, '输出不抽取电流，串联两电阻中的电流相同。'),
        Beat('先求电流', 2, 4, '把两只串联电阻相加，先求 I。'),
        Beat('下臂压降', 4, 6, 'Vout 是 R2 上的压降，用欧姆定律。'),
        Beat('代入消元', 6, 8, '把 I 代入后，Vout = V × R2 / (R1 + R2)。', hold=True),
    )
    tl = Timeline(1200, 900, 8, beats, '分压公式：从同一股电流开始', '适用条件：空载；接负载后须重新计算下臂等效电阻')
    left, right = split_columns(1200, 900, ratio=.36)
    rows = equation_rows(right, 4, spacing=110)
    formulas = ['I = V / (R1 + R2)', 'Vout = I × R2', 'Vout = V × R2 / (R1 + R2)', '空载成立；带载重新列式']
    circuit = (line(130, 270, 180, 270) + resistor(210, 270, label='R1')
               + line(390, 270, 420, 270) + line(420, 270, 420, 440)
               + line(420, 440, 390, 440) + resistor(210, 440, label='R2')
               + line(180, 440, 130, 440) + text(80, 220, 'V')
               + text(420, 220, 'Vout', anchor='middle')
               + line(420, 270, 460, 270) + line(130, 440, 130, 490)
               + line(100, 490, 160, 490) + line(110, 505, 150, 505)
               + line(120, 520, 140, 520) + text(90, 600, '输出开路，无支流', size=28))
    layers = [Layer(None, circuit), Layer('空载条件', focus(70, 175, 410, 470, .2))]
    for i, beat in enumerate(beats[1:]):
        visible = ''.join(text(x, y, formulas[j], size=30) for j, (x, y) in enumerate(rows[:i + 1]))
        x, y = rows[i]
        if i == 2:
            visible += text(rows[3][0], rows[3][1], formulas[3], size=30)
        layers.append(Layer(beat.name, combine(camera(visible, beat.start + .2, .5, dy=-5),
                                             focus(x - 10, y - 42, right.width - 20, 62, beat.start + .2))))
    return tl, layers


if __name__ == '__main__':
    write(*scene(), ROOT / 'assets/svg-v2', 'ch00-divider-derivation-v2')
