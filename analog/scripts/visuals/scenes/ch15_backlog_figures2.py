"""§15 布线、DFM 与翻车案例的第二批静态插图（事实取 15.3–15.5）。"""
from __future__ import annotations

from scripts.visuals.layouts_static import fanout, steps, two_col
from scripts.visuals.scenes.ch15_reference_figures import SCENES as REFERENCES


def via_parallel():
    # Compatibility entry: the old papercut wave must not revive 0.25 nH.
    from scripts.visuals.scenes.ch15_reference_figures import via_parallel as draw
    return draw()


def crosstalk_3w():
    return two_col(
        '串扰三招：拉开、缩短、包地',
        '平行走线耦合分容性与感性两路；先拉间距，再缩平行长度。',
        {
            'head': '三条对策',
            'items': [
                ('拉开间距', ('通常减小互容与互感', '不承诺固定衰减倍数')),
                ('3W 规则', ('中心距 ≥ 3 倍线宽', '仅作初筛，须看叠层')),
                ('缩短平行', ('垂直交叉比长距离平行干净', '耦合面积最小')),
                ('包地', ('连接连续参考面', '孔距按频率与几何核对')),
            ],
            'note': '先改几何，再谈屏蔽。',
        },
        {
            'head': '包地的边界',
            'items': [
                ('地线要低阻', ('5~10 mm 孔距只是示例', '高频须核整条回流路径')),
                ('线宽与间距', ('两倍线宽只是布局起点', '核对对目标线阻抗的影响')),
                ('防的是电场', ('高 dV/dt 邻居', '容性耦合')),
                ('磁场耦合', ('不能单靠包地保证', '缩环路或拉开距离')),
            ],
            'note': '保护线悬空，会变成注入线。',
        },
        '串扰不是“加一根地线”就完事：地线要低阻、要打过孔，磁场耦合还得缩环路。',
    )


def testpoint_rules():
    return steps(
        '测试点三条规矩：每网有、够大、夹得住',
        '测试点是给未来的自己和产线留的门；夹不进去的测试点等于没有。',
        [
            ('每网至少一个', ('电源轨、复位、时钟、关键模拟节点', '原理图阶段就标 TP')),
            ('直径 ≥1.0 mm', ('能稳定搭探头钩或测试夹', '别拿过孔当测试点')),
            ('放在元件面', ('避开散热器与屏蔽罩阴影', '夹不进等于没有')),
            ('地测试点给足', ('每片区域至少两个', '回流就近走，少测到假噪声')),
        ],
        '测试点不是可有可无的丝印：它是测量链的第一段。',
    )


def panelization():
    return two_col(
        '拼板：V-cut 与邮票孔怎么选',
        'V-cut 便宜但应力大；邮票孔能拼异形，代价是毛刺与板边空间。',
        {
            'head': 'V-cut',
            'items': [
                ('两侧各切 1/3 板厚', ('分板一掰即开', '成本最低')),
                ('槽边 0.5 mm 无铜无件', ('否则分板露铜/崩边', '拼板边必须是直线')),
                ('应力大', ('贴板边 MLCC 可能被掰裂', '裂纹往往出厂测不出')),
                ('适用', ('矩形小板、大批量', '元件退离板边')),
            ],
            'note': '便宜，但别把陶瓷电容放在刀口。',
        },
        {
            'head': '邮票孔',
            'items': [
                ('窄桥打一排小孔', ('可拼异形边', '应力小')),
                ('分板后要打磨', ('板边毛刺', '桥位占空间')),
                ('适用', ('MLCC 贴板边 3 mm 内', '要过跌落/振动')),
                ('分板方向', ('顺 V 槽掰', '逆掰应力打在最外排')),
            ],
            'note': '贵一点，换应力与异形自由。',
        },
        '有贴板边陶瓷电容或振动场合，优先邮票孔；矩形大批量再用 V-cut。',
    )


def dfm_limits():
    return two_col(
        'DFM 四个数：别贴着工艺下限设计',
        '常规双面板工艺能力；具体以板厂工艺卡为准。',
        {
            'head': '几何下限',
            'items': [
                ('最小线宽/间距', ('常规 0.15 mm / 0.15 mm', '低价快板放宽到 0.2 mm')),
                ('最小机械钻孔', ('0.3 mm 起步', '0.2 mm 以下要激光孔')),
                ('丝印', ('字高 ≥1.0 mm', '线宽 ≥0.15 mm')),
                ('铜到板边', ('V-cut ≥0.5 mm', '铣边 ≥1 mm')),
            ],
            'note': '低于下限，良率与报价一起跳。',
        },
        {
            'head': '设计动作',
            'items': [
                ('过孔别贴下限', ('0.3 mm 孔配 0.6 mm 焊盘', '环宽 0.15 mm')),
                ('细间距阻焊桥', ('0.5 mm pitch 集中放', 'Gerber 逐颗查开窗')),
                ('丝印镜像', ('底层必须镜像查看', '正看是反字才对')),
                ('板框与拼板', ('钻孔文件对齐外形层', '核对拼板间距')),
            ],
            'note': '能制造的才是设计。',
        },
        'DFM 不是“画完再查”：线宽、孔径、丝印、板边在布局阶段就定生死。',
    )


def failure_signatures():
    return fanout(
        '翻车案例：症状先分诊，再查根因',
        '表 15-2 的五种死法，倒过来就是画板时的预审清单。',
        {'head': '板子不对', 'lines': ['先看症状', '再定嫌疑区']},
        [
            {'head': 'ADC 读数跳', 'note': '数字回流穿模拟区 / 去耦太远'},
            {'head': '无线距离短', 'note': '天线净空区铺了铜'},
            {'head': '上电就发烫', 'note': '电源/地接反，先限流再上电'},
            {'head': 'EMC 辐射超标', 'note': '地平面开槽 / 晶振贴边 / 电缆'},
        ],
        '症状分诊不是猜根因：每一类都有一条可检查的几何。',
    )


FIGURES = {
    'ch15-via-parallel': {
        'draw': via_parallel, 'title': '过孔并联与电感', 'anchor': '15.3',
        'layout': 'IG-007', 'type': 'V3', 'chapter': 15, 'source': 'docs/p3-02-ch15.md',
        'alt': '纸层量级图：单个 0.3 毫米过孔约 1.3 纳亨，四个并联约 0.25 纳亨，3 安培换层至少 3 只；信号过孔每孔都带寄生，应少打并成对打。',
    },
    'ch15-crosstalk-3w': {
        'draw': crosstalk_3w, 'title': '串扰三招与包地边界', 'anchor': '15.3',
        'layout': 'IG-004', 'type': 'V4', 'chapter': 15, 'source': 'docs/p3-02-ch15.md',
        'alt': '串扰先拉间距、缩短平行段，再评估接地保护线。3W 指中心距三倍线宽，只作初筛，不保证百分之五串扰；5到10mm 地孔间距和两倍线宽也只作布局起点，须核叠层、频率、端接与回流。',
    },
    'ch15-testpoint-rules': {
        'draw': testpoint_rules, 'title': '测试点三条规矩', 'anchor': '15.4',
        'layout': 'IG-001', 'type': 'V5', 'chapter': 15, 'source': 'docs/p3-02-ch15.md',
        'alt': '四步流程：每个网络至少一个测试点，测试点直径至少 1.0 毫米，放在元件面并避开散热器与屏蔽罩阴影，每片区域至少两个地测试点让回流就近走。',
    },
    'ch15-panelization': {
        'draw': panelization, 'title': 'V-cut 与邮票孔', 'anchor': '15.4',
        'layout': 'IG-004', 'type': 'V4', 'chapter': 15, 'source': 'docs/p3-02-ch15.md',
        'alt': '左右两栏：V-cut 两侧各切三分之一板厚、槽边 0.5 毫米无铜无件、分板应力大，适合矩形小板；邮票孔用窄桥小孔拼异形边、应力小但要打磨毛刺，适合贴板边 3 毫米内有陶瓷电容或要过跌落的板。',
    },
    'ch15-dfm-limits': {
        'draw': dfm_limits, 'title': 'DFM 四个数', 'anchor': '15.4',
        'layout': 'IG-004', 'type': 'V4', 'chapter': 15, 'source': 'docs/p3-02-ch15.md',
        'alt': '左右两栏：左栏几何下限是线宽间距常规 0.15 毫米、机械钻孔 0.3 毫米起步、丝印字高至少 1.0 毫米、铜到板边 V-cut 至少 0.5 毫米；右栏设计动作是过孔配 0.6 毫米焊盘、细间距器件集中放并逐颗查阻焊开窗、底层丝印镜像查看、钻孔文件与外形层对齐。',
    },
    'ch15-failure-signatures': {
        'draw': failure_signatures, 'title': '翻车案例分诊', 'anchor': '15.5',
        'layout': 'IG-006', 'type': 'V5', 'chapter': 15, 'source': 'docs/p3-02-ch15.md',
        'alt': '分诊图：板子不对时先看症状，再分四支——ADC 读数跳查数字回流与去耦距离，无线距离短查天线净空区铺铜，上电发烫查电源地接反并先限流，EMC 辐射超标查地平面开槽、晶振贴边与电缆。',
    },
}

# Preserve old wave commands while routing this corrected diagram to its canvas.
FIGURES['ch15-via-parallel'].update(REFERENCES['ch15-via-parallel'])
