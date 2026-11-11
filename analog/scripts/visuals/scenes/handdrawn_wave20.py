"""Wave 20 手绘草图：四个无手绘图的长节。

ch16 §16.9 一页纸排故记录表、ch11 §11.6 噪声现场辨认、
ch4 §4.1 沟道形成、ch3 §3.2 三区判读。
图中数字只取对应小节原文；印刷下限 21.8px，正文一律 ≥22。
"""
from __future__ import annotations

from scripts.visuals.scenes.handdrawn_wave2 import (
    AMBER, BLUE, GREEN, INK, INK2, PAPER, RED, RULE, arrow, box, header, text,
)


def _bar(x, y, w, h, colour):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" '
            f'fill="{colour}" stroke="{INK}" stroke-width="1.4"/>')


def _larrow(x1, y1, x2, y2, colour=INK2, width=2.5):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour}" '
            f'stroke-width="{width}" stroke-linecap="round"/>'
            f'<polygon points="{x2},{y2} {x2 + 10},{y2 - 5} {x2 + 10},{y2 + 5}" fill="{colour}"/>')


def _rows(x, y0, gap, lines, size=22, colour=INK):
    return [text(x, y0 + i * gap, line, size, colour=colour) for i, line in enumerate(lines)]


def record_card():
    parts = [header('一页纸排故记录表：一张能接上的索引',
                    '记录不是给领导看的，是给三个月后的自己；超过一页，通常说明问题还没想清楚。')]
    cards = [
        (56, '现场：钉住事实', GREEN, [
            '编号·日期·板号', '现象：只写客观', '复现率与条件',
            '环境与版本', '电源与静态测量', '动态测量＋附件号']),
        (366, '推演：逐条判决', AMBER, [
            '假设链逐条判决', '已证实 / 已证伪', '证伪的也要留',
            '单变量实验', '每次只改一项', '改别的单独记']),
        (676, '收口：关单四问', BLUE, [
            '根因：物理机制', '修复：动作批次', '回归：条件判据',
            '防呆：负责人日期', '根因回归不能空', '“已修好”不算回归']),
    ]
    for x, title, colour, lines in cards:
        parts.append(box(x, 126, 268, 336, fill=PAPER))
        parts.append(text(x + 134, 160, title, 25, colour=colour, anchor='middle', weight='700'))
        parts.append(f'<line x1="{x + 22}" y1="180" x2="{x + 246}" y2="180" stroke="{RULE}" stroke-width="1.5"/>')
        for i, line in enumerate(lines):
            parts.append(text(x + 134, 214 + i * 40, line, 22, anchor='middle',
                              colour=INK2 if i == len(lines) - 1 else INK))
    parts.append(box(56, 478, 888, 192, fill=PAPER, stroke=INK2))
    parts.append(text(500, 512, '一页纸的边界与去处', 26, anchor='middle', weight='700'))
    parts.append(f'<line x1="90" y1="532" x2="910" y2="532" stroke="{RULE}" stroke-width="1.5"/>')
    parts.extend(_rows(90, 566, 40, [
        '波形附件编号能后补，但要在动态测量里写“稍后补＋日期”',
        '防呆能后补，但必须落到具体动作和负责人，否则永远不会发生',
        '它也是交接文档：接手者三分钟读完假设链，从已证实处接着走',
    ]))
    return parts


def noise_identify():
    parts = [header('噪声现场辨认：先对症状，再核频谱与工况',
                    '先把信号和噪声放在同一测量条件下，再决定动哪只旋钮。')]
    parts.append(box(56, 126, 888, 356, fill=PAPER))
    heads = [(90, '听 / 看'), (350, '先怀疑'), (640, '下一步')]
    for x, label in heads:
        parts.append(text(x, 162, label, 24, colour=INK2, weight='700'))
    parts.append(f'<line x1="90" y1="180" x2="910" y2="180" stroke="{RULE}" stroke-width="1.5"/>')
    rows = [
        ('宽带「嘶——」', '白噪声/热噪声', '看带宽与预算大头'),
        ('低频起伏慢漂', '1/f＋温漂＋干扰', '比 e_n(f) 与 i_n(f)'),
        ('50 Hz 及谐波', '地环/纹波/耦合', '先查屏蔽与接地'),
        ('随偏置电流变', '散粒噪声一项', '重算增益与失真'),
        ('随源阻变', '热噪声√R 或 i_n·Z_s', '并电阻会加载信号源'),
    ]
    for i, (sym, suspect, action) in enumerate(rows):
        y = 218 + i * 50
        parts.append(text(90, y, sym, 24, weight='700'))
        parts.append(text(350, y, suspect, 22))
        parts.append(text(640, y, action, 22, colour=INK2))
        if i < len(rows) - 1:
            parts.append(f'<line x1="90" y1="{y + 16}" x2="910" y2="{y + 16}" stroke="{RULE}" stroke-width="1"/>')
    parts.append(box(56, 500, 888, 170, fill=PAPER, stroke=INK2))
    parts.append(text(500, 534, '一句话地图', 26, anchor='middle', weight='700'))
    parts.append(f'<line x1="90" y1="554" x2="910" y2="554" stroke="{RULE}" stroke-width="1.5"/>')
    parts.extend(_rows(90, 588, 40, [
        '白噪看带宽与各项来源；1/f 看实际频谱与工况；工频看接地与电源',
        '不能凭听感给 1/f 定案：先对症状，再用频谱与工况核账',
    ]))
    return parts


def channel_formation():
    parts = [header('沟道形成三步：电场把 P 型表面改成 N 型',
                    '栅极隔着氧化层不碰沟道：它靠电场把电子拉到表面，铺出一条 N 型走廊。')]
    panels = [
        (56, 'VGS = 0', 'VGS = 0', 0),
        (366, 'VGS > VTH', 'VGS > VTH', 1),
        (676, 'VGS 更大', 'VGS 更大', 2),
    ]
    for x, title, gtext, stage in panels:
        parts.append(box(x, 126, 268, 300, fill=PAPER))
        parts.append(text(x + 134, 160, title, 24, anchor='middle', weight='700'))
        parts.append(text(x + 134, 198, 'G', 22, anchor='middle', weight='700'))
        parts.append(_bar(x + 96, 206, 76, 12, INK))
        parts.append(f'<line x1="{x + 96}" y1="230" x2="{x + 172}" y2="230" stroke="{AMBER}" stroke-width="6"/>')
        parts.append(f'<rect x="{x + 22}" y="250" width="224" height="66" fill="#efe6d4" stroke="{INK}" stroke-width="1.5"/>')
        parts.append(f'<rect x="{x + 40}" y="250" width="54" height="34" fill="#dce4e8" stroke="{INK}" stroke-width="1.4"/>')
        parts.append(f'<rect x="{x + 174}" y="250" width="54" height="34" fill="#dce4e8" stroke="{INK}" stroke-width="1.4"/>')
        parts.append(text(x + 67, 274, 'N+', 22, anchor='middle', weight='700'))
        parts.append(text(x + 201, 274, 'N+', 22, anchor='middle', weight='700'))
        parts.append(text(x + 67, 240, 'S', 22, anchor='middle', colour=INK2))
        parts.append(text(x + 201, 240, 'D', 22, anchor='middle', colour=INK2))
        parts.append(text(x + 134, 304, 'P 型衬底', 22, anchor='middle', colour=INK2))
        if stage >= 1:
            h = 10 if stage == 1 else 18
            parts.append(f'<rect x="{x + 94}" y="250" width="80" height="{h}" rx="2" '
                         f'fill="{BLUE}" stroke="{INK}" stroke-width="1.2"/>')
        parts.append(text(x + 134, 354, gtext, 22, anchor='middle', colour=BLUE, weight='700'))
        note = '两个背靠背 PN 结' if stage == 0 else ('反型层连起源漏' if stage == 1 else '沟道更厚')
        note2 = '体二极管另看' if stage == 0 else ('沟道导通' if stage == 1 else 'RDS(on) 更低')
        parts.append(text(x + 134, 384, note, 22, anchor='middle'))
        parts.append(text(x + 134, 412, note2, 22, anchor='middle', colour=INK2))
    parts.append(box(56, 440, 888, 230, fill=PAPER, stroke=INK2))
    parts.append(text(500, 474, '栅极这只电容：开关瞬间的账', 26, anchor='middle', weight='700'))
    parts.append(f'<line x1="90" y1="494" x2="910" y2="494" stroke="{RULE}" stroke-width="1.5"/>')
    parts.extend(_rows(90, 528, 40, [
        '栅氧厚度与工艺有关；栅源额定常见 ±20 V，必须查具体型号',
        'VTH 随温度下降 −2~−5 mV/°C：热管更容易被 dv/dt 误导通',
        '3.3 V 驱动应查对应栅压的 RDS(on) 保证，不只看 VTH',
    ]))
    return parts


def region_check():
    parts = [header('三区判读：不拆焊，先量两个电压',
                    '判区看两个 PN 结的偏置：量出 VBE 与 VCE，工作区自己会报名字。')]
    parts.append(box(56, 150, 230, 200, fill=PAPER))
    parts.append(text(171, 186, '先量', 25, anchor='middle', weight='700'))
    parts.append(text(171, 232, 'VBE', 34, anchor='middle', colour=BLUE, weight='700'))
    parts.append(text(171, 272, '与 VCE', 24, anchor='middle', weight='700'))
    parts.append(text(171, 318, '基极有电压？', 22, anchor='middle', colour=INK2))
    parts.append(f'<line x1="306" y1="200" x2="306" y2="450" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(f'<line x1="630" y1="200" x2="630" y2="450" stroke="{INK2}" stroke-width="2.5"/>')
    parts.append(_larrow(286, 250, 306, 250))
    cards = [
        (340, 136, '放大区', GREEN, ['VBE ≈ 0.7 V', 'VCE > 1 V', '信号全程留这里']),
        (650, 136, '饱和区', AMBER, ['VBE ≈ 0.8 V', 'VCE ≈ 0.1~0.3 V', '开关才故意进来']),
        (340, 326, '截止区', BLUE, ['VBE < 0.5 V', 'VCE ≈ VCC', '漏流随温度翻倍']),
        (650, 326, '尚未正偏', RED, ['VBE = 0 V', '查驱动 / B-E 短路', '不能直接判开路']),
    ]
    for x, y, title, colour, lines in cards:
        parts.append(box(x, y, 290, 170, fill=PAPER))
        parts.append(text(x + 145, y + 34, title, 25, colour=colour, anchor='middle', weight='700'))
        parts.append(f'<line x1="{x + 22}" y1="{y + 54}" x2="{x + 268}" y2="{y + 54}" stroke="{RULE}" stroke-width="1.5"/>')
        for i, line in enumerate(lines):
            parts.append(text(x + 145, y + 90 + i * 34, line, 22, anchor='middle',
                              colour=INK2 if i == 2 else INK))
        parts.append(_larrow(306 if x < 600 else 630, y + 85, x - 4, y + 85))
    parts.append(box(56, 520, 888, 150, fill=PAPER, stroke=INK2))
    parts.append(text(500, 552, '两条边界不能忘', 26, anchor='middle', weight='700'))
    parts.append(f'<line x1="90" y1="570" x2="910" y2="570" stroke="{RULE}" stroke-width="1.5"/>')
    parts.extend(_rows(90, 602, 38, [
        '击穿不是第四区：BVCEO 40 V（2N2222A）是失效边界，不是设计空间',
        '截止漏流每升 8~10 °C 翻倍：85 °C 高阻负载要按微安级重算',
    ]))
    return parts


SCENES = {
    'ch16-record-card': {
        'draw': record_card,
        'title': '一页纸排故记录表',
        'anchor': '16.9 一页纸排故记录表', 'chapter': 16,
        'source': 'docs/p4-01-ch16.md',
        'alt': '三栏记录卡：现场栏列编号日期板号、客观现象、复现率与条件、环境与版本、'
               '电源与静态测量、动态测量与波形附件编号；推演栏列假设链逐条判决（已证实/已证伪）、'
               '证伪的也要留、单变量实验每次只改一项；收口栏列根因、修复、回归、防呆，'
               '并强调根因回归不能空。底部三条边界：附件与防呆可后补、一页纸也是交接文档。'},
    'ch11-noise-identify': {
        'draw': noise_identify,
        'title': '噪声现场辨认表',
        'anchor': '11.6 噪声：放大器躲不掉的"本底"', 'chapter': 11,
        'source': 'docs/p2-01-ch11.md',
        'alt': '五症状对照表：宽带嘶声先怀疑白噪与热噪，看带宽与预算大头；低频起伏慢漂查 1/f、'
               '温漂与干扰，比较 e_n(f) 与 i_n(f)；50 Hz 及谐波查地环、纹波与耦合，先查屏蔽与接地；'
               '随偏置电流变查散粒噪声，连带重算增益与失真；随源阻变区分热噪声与输入电流噪声，'
               '注意并电阻会加载信号源。底部一条地图：白噪看带宽、1/f 看频谱与工况、工频看地。'},
    'ch04-channel-formation': {
        'draw': channel_formation,
        'title': '沟道形成三步',
        'anchor': '4.1 沟道形成原理（N 沟道增强型）', 'chapter': 4,
        'source': 'docs/p1-05-ch4.md',
        'alt': '三幅 N 沟道增强型 MOSFET 剖面：VGS=0 时两个 N+ 区被 P 型衬底隔开、增强沟道关闭，体二极管另看极性；'
               'VGS>VTH 时氧化层下形成蓝色反型层，把源漏连起来；VGS 更大时沟道更厚、RDS(on) 更低。'
               '底部三条电容账：栅氧厚度取决于工艺，栅源额定常见 ±20 V、须查型号；VTH 随温度下降 −2~−5 mV/°C；'
               '3.3 V 驱动要查对应栅压的 RDS(on) 保证，不能只看 VTH(max)。'},
    'ch03-region-check': {
        'draw': region_check,
        'title': '三区判读流程',
        'anchor': '3.2 三个工作区（判断方法是看两个 PN 结的偏置）', 'chapter': 3,
        'source': 'docs/p1-04-ch3.md',
        'alt': '判读流程：先量 VBE 与 VCE，再分四路——VBE 约 0.7 V、VCE 大于 1 V 是放大区；'
               'VBE 约 0.8 V、VCE 约 0.1~0.3 V 是饱和区；VBE 小于 0.5 V、VCE 接近 VCC 是截止区；'
               'VBE 为 0 V 说明尚未正偏，应查驱动或 B-E 短路，不能直接判开路。底部两条边界：'
               'BVCEO 40 V 是失效边界不是第四区；截止漏流每升 8~10 °C 翻倍，85 °C 高阻负载要重算。'},
}

# Corrected chapter 11 model and visual contract.
from scripts.visuals.scenes.ch11_reference_figures import SCENES as _ch11_corrected
SCENES['ch11-noise-identify'] = _ch11_corrected['ch11-noise-identify']
