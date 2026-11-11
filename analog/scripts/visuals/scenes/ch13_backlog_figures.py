"""§13 功率与隔离的静态插图；构图取 `layouts_static`，事实取 13.7/13.8/13.11。"""
from __future__ import annotations

from scripts.visuals.layouts_static import two_col


def h_bridge_states():
    return two_col(
        'H 桥四拍：两个状态位决定电流方向',
        '四只开关组成两个半桥；同臂齐开就是电源直通，换向必须先插死区。',
        {
            'head': '四拍',
            'items': [
                ('正转', ('Q1 + Q4 导通', '电流 +12 V→电机→GND')),
                ('反转', ('Q2 + Q3 导通', '电流整体掉头')),
                ('全关滑行', ('电感电流经体二极管回电源', '动能回收，就是刹车')),
                ('致命错误', ('同臂 Q1 + Q2 齐开', '毫秒级烧管')),
            ],
            'note': '四个开关，只有两个状态位。',
        },
        {
            'head': '死区与驱动',
            'items': [
                ('死区 1~2 µs', ('先关再开', '驱动芯片替你管')),
                ('体二极管', ('死区里电流不肯等', '搭桥先接住')),
                ('高侧自举', ('源极悬在电机电压上', '栅极要举起来才开得动')),
                ('集成驱动', ('DRV8833/L298 打包', '死区/自举/过流保护')),
            ],
            'note': '空挡留给二极管，不留给直通。',
        },
        'H 桥不是四个开关随便开：同臂直通是毫秒级故障，死区是换向的必经空挡。',
    )


def current_sense_sides():
    return two_col(
        '电流检测：低侧还是高侧，先看地',
        '分流电阻把电流变成压降；位置选错，共模与地参考会同时找麻烦。',
        {
            'head': '低侧检测',
            'items': [
                ('电阻在负载与地之间', ('共模≈0 V', '运放随便选')),
                ('破坏地参考', ('负载地被抬高 100 mV', '与其它电路不共地')),
                ('测不到对地短路', ('电流绕过电阻走地', '保护有盲区')),
                ('适用', ('精度优先、单路负载', '负载不接地')),
            ],
            'note': '便宜，但地不再干净。',
        },
        {
            'head': '高侧检测',
            'items': [
                ('电阻在电源与负载之间', ('共模=12/24/48 V', '需高共模器件')),
                ('地完整', ('负载地就是系统地', '通信不抬高')),
                ('能测对地短路', ('短路电流仍经过电阻', '保护无盲区')),
                ('适用', ('保护优先、多路共地', '汽车/工业 12~48 V')),
            ],
            'note': '贵一点，换来完整的地。',
        },
        '只要负载与系统共地，就必须走高侧；低侧的 100 mV 会变成逻辑电平的误差源。',
    )


def opto_ctr():
    return two_col(
        '隔离三条路：信号能过，电流不能过',
        '两个地之间没有欧姆通路，只有光、磁场或电容耦合；选路线先看速度与寿命。',
        {
            'head': '三条路线',
            'items': [
                ('光耦', ('PC817/6N137/TLP521', 'kV 级，kHz~10 MHz')),
                ('数字隔离器', ('ADuM1201/Si8620/ISO7721', '100 Mbps+，不衰减')),
                ('隔离放大器', ('HCPL-7840/AMC1301', '模拟量隔离')),
                ('共同点', ('没有欧姆通路', '共模不再变成环流')),
            ],
            'note': '先问速度，再问寿命。',
        },
        {
            'head': 'CTR 三个坑',
            'items': [
                ('分档散布大', ('PC817 A/B/C/D', '50%~600%，按最小值算')),
                ('温漂与老化', ('100 °C、20 mA 跑 10 年', 'CTR 可能掉一半')),
                ('驱动留余量', ('别贴阈值设计', '至少 2 倍')),
                ('设计式', ('I_C = I_F × CTR', '先算 I_F 够不够')),
            ],
            'note': 'CTR 是下限，不是典型值。',
        },
        '隔离不是“加个光耦”：CTR 会随温度与时间衰减，驱动必须按最差分档留余量。',
    )


FIGURES = {
    'ch13-h-bridge-states': {
        'draw': h_bridge_states, 'title': 'H 桥四拍', 'anchor': '13.7',
        'layout': 'IG-004', 'type': 'V4', 'chapter': 13, 'source': 'docs/p2-03-ch13.md',
        'alt': '左右两栏：左栏四拍是正转 Q1 与 Q4 导通、反转 Q2 与 Q3 导通、全关滑行时电感电流经体二极管回电源、同臂 Q1 与 Q2 齐开会毫秒级烧管；右栏是 1 到 2 微秒死区、体二极管兜底、高侧自举、DRV8833 或 L298 集成驱动。',
    },
    'ch13-current-sense-sides': {
        'draw': current_sense_sides, 'title': '低侧与高侧电流检测', 'anchor': '13.8',
        'layout': 'IG-004', 'type': 'V4', 'chapter': 13, 'source': 'docs/p2-03-ch13.md',
        'alt': '左右两栏：低侧检测共模接近 0 V、会把负载地抬高 100 mV、测不到对地短路，适合精度优先的单路负载；高侧检测共模为 12 或 24 或 48 V、地完整、能测对地短路，适合保护优先的多路共地负载。',
    },
    'ch13-opto-ctr': {
        'draw': opto_ctr, 'title': '隔离三条路线与 CTR', 'anchor': '13.11',
        'layout': 'IG-004', 'type': 'V4', 'chapter': 13, 'source': 'docs/p2-03-ch13.md',
        'alt': '左右两栏：左栏三条隔离路线是光耦、数字隔离器、隔离放大器，共同点是没有欧姆通路；右栏 CTR 三个坑是分档 50% 到 600% 要按最小值、100 摄氏度与 20 毫安下十年可能掉一半、驱动至少留 2 倍余量，设计式为集电极电流等于正向电流乘 CTR。',
    },
}

# Chapter 13 reviewed model overrides.
from scripts.visuals.scenes.ch13_reference_figures import SCENES as _CH13_REVIEWED
for _aid in ['ch13-h-bridge-states', 'ch13-current-sense-sides', 'ch13-opto-ctr']:
    # The legacy builder consumes FIGURES, and these replacements use the
    # 1000×700 paper-and-ink renderer rather than its 1448×1086 papercut canvas.
    FIGURES[_aid] = {**_CH13_REVIEWED[_aid], 'renderer': 'handdrawn'}
