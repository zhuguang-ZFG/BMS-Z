"""§18 大师排故智慧的静态插图；构图取 `layouts_static`，事实取正文。

每张图的数字只来自对应 anchor 的小节；经验值在图中标“经验”或“≈”。
"""
from __future__ import annotations

from scripts.visuals.papercut import (
    PAPER, INK, SHADE, ACCENT, FACE, EDGE, sheet, text, line, chip,
)
from scripts.visuals.layouts_static import steps, PANEL, TINT, RULE
from scripts.visuals.layouts_illustrated import (
    illustrated_two_col, hero_scene, board, resistor, capacitor, probe,
    scope, dmm, notebook, preamp, mug, spring_ground,
)


def _power_scene():
    base = [
        board(110, 205, 800, 205),
        chip(150, 260, 90),
        chip(760, 250, 100),
        line(240, 310, 420, 310, ACCENT, 10),
        resistor(420, 310, 96),
        line(516, 310, 760, 310, ACCENT, 10),
        line(240, 370, 760, 370, SHADE, 3, '10,8'),
        capacitor(650, 370, .9),
        probe(300, 310, -18),
        probe(700, 310, 18),
        probe(676, 370, 38),
    ]
    labels = [
        text(250, 238, '①', 38, colour=ACCENT, weight='700', background=PANEL),
        text(732, 238, '②', 38, colour=ACCENT, weight='700', background=PANEL),
        text(720, 430, '③', 38, colour=ACCENT, weight='700', background=PANEL),
        text(452, 386, 'R', 32, colour=INK, weight='700', background=PANEL),
    ]
    return base, labels


def power_three_points():
    base, labels = _power_scene()
    return illustrated_two_col(
        '三处电压，160 mV 的落差',
        'LDO 输出 5.02 V、运放 VCC 4.86 V；负载 120 mA，路径约 1.3 Ω。',
        base, labels,
        {
            'head': '依次量三点',
            'items': [
                ('① 稳压器输出脚', ('5.02 V', '电源的源头')),
                ('② 芯片电源引脚', ('4.86 V', '负载真正拿到')),
                ('③ 去耦电容两端', ('应与②毫伏级一致', '差几十 mV 是走线')),
            ],
            'note': '→ 三点只差毫伏级；否则病灶在路径。',
        },
        {
            'head': '160 mV 去哪了',
            'items': [
                ('ΔV = 5.02 − 4.86', ('= 160 mV', '不是芯片吃掉的')),
                ('R = ΔV / 120 mA', ('≈ 1.3 Ω', '路径电阻的账')),
                ('1 oz 铜 ≈ 0.5 mΩ/方', ('0.2 mm × 200 mm', '≈ 1000 方，约 0.5 Ω',
                                         '加过孔与接插件，1 Ω 出头')),
            ],
        },
        '三点对账：源头、引脚、电容；差几十毫伏，先查走线而不是换芯片。',
    )


def _dmm_scene():
    base = [
        dmm(140, 235, .95, 'flat'),
        board(350, 270, 170, 100),
        f'<path d="M243,408 C290,410 320,350 350,340" fill="none" '
        f'stroke="{SHADE}" stroke-width="3"/>',
        f'<path d="M360,300 C380,280 400,280 420,300 C440,320 460,320 480,300" '
        f'fill="none" stroke="{ACCENT}" stroke-width="4"/>',
        scope(700, 200, 440, 225, 'sine'),
        f'<path d="M720,395 C660,380 620,360 520,350" fill="none" '
        f'stroke="{SHADE}" stroke-width="3"/>',
    ]
    labels = [
        text(150, 222, 'DC 档', 32, colour=INK, weight='700', background=PANEL),
        text(730, 190, 'AC 耦合', 32, colour=ACCENT, weight='700', background=PANEL),
    ]
    return base, labels


def dmm_average():
    base, labels = _dmm_scene()
    return illustrated_two_col(
        '万用表把振荡平均成 2.5 V',
        'DC 档积分窗口百毫秒，AC 档带宽几十到几百 Hz；1 MHz 振荡两档都看不见。',
        base, labels,
        {
            'head': '表上读到的',
            'items': [
                ('DC 档', ('2.5 V，纹丝不动', '正负摆动互相抵消')),
                ('AC 档', ('≈ 零', '1 MHz 远超带宽')),
                ('平均滤镜', ('摆得越对称越安静', '稳定得可疑')),
            ],
            'note': '→ 两个档位都在撒谎，不是电路稳定。',
        },
        {
            'head': '示波器摊开时间',
            'items': [
                ('AC 耦合 + 毫伏档', ('先看有没有振荡', '再谈直流精度')),
                ('1 MHz、±2 V', ('峰峰值 4 V', '在平均窗口外')),
                ('模拟节点', ('一律示波器复核', '尤其电源与基准')),
            ],
            'note': '→ 表静得可疑就上探头，不要先信读数。',
        },
        '稳定得可疑的模拟节点，先用示波器 AC 耦合扫一遍；表读数是平均值，不是真相。',
    )


def _workbench_scene():
    base = [
        sheet(430, 720, 950, 56, fill=EDGE),
        line(442, 726, 1368, 726, FACE, 3),
        scope(450, 470, 280, 230, 'sine'),
        dmm(740, 560, 1.0, 'flat'),
        board(860, 575, 290, 135),
        chip(960, 610, 60),
        resistor(900, 650, 70),
        capacitor(1060, 650, .7),
        line(1020, 640, 1060, 640, ACCENT, 7),
        line(1114, 640, 1130, 640, ACCENT, 7),
        line(1130, 640, 1130, 600, ACCENT, 7),
        probe(950, 600, -48),
        f'<path d="M874,530 C820,548 770,540 730,560" fill="none" '
        f'stroke="{SHADE}" stroke-width="3"/>',
        spring_ground(928, 620, 44),
        notebook(1160, 575, 180, 135),
        preamp(1110, 420, 150, 100),
        line(1110, 520, 1260, 520, RULE, 2),
        mug(1290, 635),
    ]
    labels = [
        text(1120, 552, '①', 34, colour=ACCENT, weight='700', background=PANEL),
        text(895, 548, '②', 34, colour=ACCENT, weight='700', background=PANEL),
        text(1015, 555, '③', 34, colour=ACCENT, weight='700', background=PANEL),
        text(1082, 404, '④', 34, colour=ACCENT, weight='700', background=PANEL),
    ]
    return base, labels


def williams_workbench():
    base, labels = _workbench_scene()
    labels += [
        text(96, 238, '① 先预测', 40, colour=ACCENT, weight='700', background=PANEL),
        text(96, 284, '下探头前写下直流、交流、', 32, colour=SHADE, background=PANEL),
        text(96, 318, '时间尺度；对不上就改模型。', 32, colour=SHADE, background=PANEL),
        text(96, 384, '② 短地线', 40, colour=ACCENT, weight='700', background=PANEL),
        text(96, 430, '15 cm 地夹的振铃，可能是', 32, colour=SHADE, background=PANEL),
        text(96, 464, '探头自己造的；换 1 cm 地针。', 32, colour=SHADE, background=PANEL),
        text(96, 530, '③ 最小电路', 40, colour=ACCENT, weight='700', background=PANEL),
        text(96, 576, '剥到仍能复现的裸骨架，', 32, colour=SHADE, background=PANEL),
        text(96, 610, '再动烙铁。', 32, colour=SHADE, background=PANEL),
        text(96, 676, '④ 源头放大', 40, colour=ACCENT, weight='700', background=PANEL),
        text(96, 722, '信号在污染前养大，', 32, colour=SHADE, background=PANEL),
        text(96, 756, '信噪比才锁得住。', 32, colour=SHADE, background=PANEL),
        text(96, 836, '读大师，抄的是顺序，', 32, colour=INK, background=PANEL),
        text(96, 870, '不是装备清单。', 32, colour=INK, background=PANEL),
    ]
    return hero_scene(
        'Williams 的工作台：先想透，再动手',
        '预测、短地线、最小电路、源头放大——四件动作都在探头落下之前。',
        base, labels,
        '大师的工作台不是摆拍：每件工具都在替一个假设服务。',
    )


def probe_loading():
    return two_col(
        '探头一挂，拐点从 16 kHz 掉到 160 kHz',
        '100 kΩ 节点：×1 档约 100 pF，×10 档约 10–15 pF。',
        {
            'head': '×1 档：100 pF',
            'items': [
                ('f = 1/(2πRC)', ('≈ 16 kHz', '100 kΩ × 100 pF')),
                ('20 kHz 信号', ('幅度掉近四成', '相位落后约五十度')),
                ('屏幕上看到的', ('像电路的滚降', '其实是探头的')),
                ('风险', ('把探头当电路', '越测越糊涂')),
            ],
            'note': '载入电容改变了被测节点。',
        },
        {
            'head': '×10 档：10–15 pF',
            'items': [
                ('同一节点', ('拐点 ≈ 160 kHz', '载入电容降一个量级')),
                ('20 kHz', ('幅度与相位接近真实', '真相浮出来')),
                ('档位纪律', ('先报档位再报数值', '×1/×10 差十倍')),
                ('高阻节点', ('优先 ×10', '或差分/有源探头')),
            ],
            'note': '先问探头并了多少电容。',
        },
        '高阻节点先算探头电容：×1 的 100 pF 会把 16 kHz 的拐点栽给电路，换 ×10 再看。',
    )


def reset_clock_enable():
    return steps(
        '芯片不工作：复位、时钟、使能',
        '三脚各量一次，比读十页数据手册快；顺序不能乱。',
        [
            ('① 复位释放了吗', ('复位脚仍被拉低，时钟与使能都无意义', '先看电平与释放时刻')),
            ('② 时钟起振了吗', ('×10 探头先看；×1 的 100 pF 可能压停晶振', '不起振就查负载电容与驱动')),
            ('③ 使能脚对吗', ('悬空、极性反、上拉缺失都会让芯片沉默', '对照 datasheet 的电平定义')),
            ('④ 三脚都过再读手册', ('电源已过关的前提下，这三脚覆盖多数不启动', '顺序：复位→时钟→使能')),
        ],
        '复位没释放，时钟再好也白搭；时钟没起振，使能再对也无济于事。',
    )


def measurement_snr():
    return two_col(
        '先放大，再上路：信噪比 0.1 → 10',
        '20 µV 信号、200 µV 环境拾取；在源头放大 100 倍，污染前锁住信噪比。',
        {
            'head': '直接进示波器',
            'items': [
                ('信号 20 µV', ('噪声 200 µV', '信噪比 0.1')),
                ('信号被淹没', ('灵敏度拧到底也没用', '噪声已掺进第一段线')),
                ('污染不可逆', ('后级滤波救不了', '先脏后滤是空话')),
                ('结果', ('只看得到噪声', '测量链先输一截')),
            ],
            'note': '在污染发生前把信号养大。',
        },
        {
            'head': '源头先放大 ×100',
            'items': [
                ('信号变成 2 mV', ('同样 200 µV 拾取', '信噪比 10')),
                ('抗扰提高百倍', ('代价只是一个低噪声前级', '前级噪声 < 2 µV')),
                ('前级噪声预算', ('至少比信号小一个量级', '否则放大器成噪声源')),
                ('顺序', ('先放大再上路', '不是到示波器端再拧灵敏度')),
            ],
            'note': '放大发生在污染之前。',
        },
        '源头放大 100 倍，信噪比从 0.1 到 10；前级噪声要小一个量级。',
    )


def ground_lead():
    return two_col(
        '15 cm 地夹，3.8 V 假振铃',
        '地线约 1 nH/mm；50 mA 在 2 ns 内摆完，V = L·di/dt。',
        {
            'head': '15 cm 长地夹',
            'items': [
                ('L ≈ 150 nH', ('15 cm × 1 nH/mm', '经验值')),
                ('di/dt = 50 mA / 2 ns', ('快沿', '电流在 2 ns 内摆完')),
                ('V = L·di/dt', ('≈ 3.8 V', '屏幕上的假尖峰')),
                ('误判', ('以为电路在振铃', '其实是探头地线')),
            ],
            'note': '地线环路也是天线。',
        },
        {
            'head': '1 cm 弹簧地针',
            'items': [
                ('L ≈ 10 nH', ('缩短 15 倍', '环路面积同步缩小')),
                ('同一边沿', ('假尖峰 ≈ 0.25 V', '量级降下来')),
                ('判据', ('先问地线多长', '再问电路多糟')),
                ('高速测量', ('弹簧地针/最短地', '别用长鳄鱼夹')),
            ],
            'note': '先把测量装置自己的投影去掉。',
        },
        '看到振铃先量地线：15 cm 地夹能造出 3.8 V；换 1 cm 地针再看电路。',
    )


FIGURES = {
    'ch18-power-three-touchpoints': {
        'draw': power_three_points, 'title': '先量电源的三处触点', 'anchor': '18.1',
        'layout': 'IG-004', 'type': 'V4', 'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '上半幅画一块供电板：LDO、细长走线、负载芯片与去耦电容，三支探针依次点在①输出脚、②芯片电源脚、③电容两端；下半幅左栏列 5.02 V、4.86 V 与毫伏级判据，右栏算 160 mV 除以 120 mA 约 1.3 Ω 的路径账。',
    },
    'ch18-dmm-averaging': {
        'draw': dmm_average, 'title': '万用表的平均滤镜', 'anchor': '18.1',
        'layout': 'IG-004', 'type': 'V4', 'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '上半幅左边是万用表，显示一条不动的 2.5 V 直线；右边是示波器，把同一节点摊成 ±2 V 的正弦波。下半幅左栏解释 DC 与 AC 档为何都看不见 1 MHz 振荡，右栏给出示波器 AC 耦合与毫伏档的复核判据。',
    },
    'ch18-probe-loading': {
        'draw': probe_loading, 'title': '探头电容把拐点拉低', 'anchor': '18.1',
        'layout': 'IG-004', 'type': 'V4', 'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '左右两栏对比 100 kΩ 节点的探头负载：×1 档约 100 pF，拐点约 16 kHz，20 kHz 幅度掉近四成、相位落后约 50 度；×10 档约 10 到 15 pF，拐点约 160 kHz，20 kHz 接近真实。',
    },
    'ch18-reset-clock-enable': {
        'draw': reset_clock_enable, 'title': '不启动的三板斧', 'anchor': '18.1',
        'layout': 'IG-008', 'type': 'V5', 'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '四步顺序卡：先查复位脚是否释放，再查时钟是否起振（×10 探头避免 100 pF 压停晶振），再查使能脚电平与上拉，最后才读数据手册；顺序为复位、时钟、使能。',
    },
    'ch18-measurement-snr': {
        'draw': measurement_snr, 'title': '源头放大锁住信噪比', 'anchor': '18.2',
        'layout': 'IG-004', 'type': 'V4', 'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '左右两栏对比：20 µV 信号直接进示波器，被 200 µV 环境拾取淹没，信噪比 0.1；在源头先放大 100 倍变成 2 mV，同样拾取下信噪比 10，前级自身噪声需小于 2 µV。',
    },
    'ch18-ground-lead-inductance': {
        'draw': ground_lead, 'title': '探头地线的假振铃', 'anchor': '18.2',
        'layout': 'IG-004', 'type': 'V4', 'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '左右两栏对比探头地线：15 cm 地夹约 150 nH，50 mA 在 2 ns 内变化给出约 3.8 V 假尖峰；1 cm 弹簧地针约 10 nH，同一边沿的假尖峰降到约 0.25 V。',
    },
    'ch18-williams-workbench': {
        'draw': williams_workbench, 'title': 'Williams 的工作台', 'anchor': '18.2',
        'layout': 'IG-013', 'type': 'V1', 'chapter': 18, 'source': 'docs/p4-03-ch18.md',
        'alt': '纸雕工作台场景：左侧四段标注①先预测、②短地线、③最小电路、④源头放大；右侧桌上摆示波器、万用表、最小电路板、预测笔记和前级放大器，探针从示波器接到板上，地用短弹簧针。',
    },
}
