"""A1 电流流动代表场景；源于 ch0 §0.2，未通过全章风格复评前不回填正文。"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.visuals.timeline import Beat, Timeline
from scripts.visuals.render import Layer, write
from scripts.visuals.primitives import text, line, resistor, reveal_path, current_flow, focus, combine


def scene():
    beats = (
        Beat('闭合回路', 0, 2, '先找闭合路径：电源、两只电阻、回到电源。'),
        Beat('同一股电流', 2, 4, 'I = 5V / (1kΩ + 4kΩ) = 1mA。'),
        Beat('分配电压', 4, 6, '同一股 1mA 电流：1kΩ 留下 1V，4kΩ 留下 4V。'),
        Beat('回路守恒', 6, 8, '回路闭合，电流相同；两段压降相加等于 5V。', hold=True),
    )
    tl = Timeline(1200, 900, 8, beats, '同一股电流，分配两份电压',
                  '约定电流方向示意；运动速度为教学慢放，不表示电子漂移速度')
    path = 'M180 600 L180 280 L1020 280 L1020 600 L180 600'
    circuit = (line(180, 280, 300, 280) + resistor(330, 280, label='1kΩ')
               + line(510, 280, 690, 280) + resistor(720, 280, label='4kΩ')
               + line(900, 280, 1020, 280) + line(1020, 280, 1020, 600)
               + line(1020, 600, 180, 600) + line(180, 600, 180, 460)
               + line(180, 280, 180, 360) + line(145, 360, 215, 360)
               + line(160, 390, 200, 390) + line(180, 390, 180, 460)
               + text(90, 425, '5V') + text(220, 380, '+'))
    summary = text(310, 720, '1V + 4V = 5V', size=44) + text(310, 785, '每一处电流都是 1mA', size=36)
    layers = [Layer(None, circuit),
              Layer('闭合回路', reveal_path(path, 0, 1.6)),
              Layer('同一股电流', combine(current_flow(path, 2.4, 1.2), text(380, 470, 'I = 1mA', size=46)), (0, -4)),
              Layer('分配电压', combine(text(350, 370, '1V'), text(750, 370, '4V'), focus(300, 200, 600, 190, 4.3)), (0, -4)),
              Layer('回路守恒', summary, (0, -4))]
    return tl, layers


if __name__ == '__main__':
    write(*scene(), ROOT / 'assets/svg-v2', 'ch00-current-loop-v2')
