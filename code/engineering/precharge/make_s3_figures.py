#!/usr/bin/env python3
"""Generate S3 precharge figures from the frozen reference implementation.

F1 (current paths by state) and F4 (measurement validity evidence) are
hand-authored mechanisms. F2 (VC/I/P + energy account), F3 (command/feedback
co-timeline) and F5 (device limits and repeated heating) read their numbers
from ``s3_precharge.py`` at generation time.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

import s3_precharge as s3

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "bms-book" / "engineering" / "assets" / "s3-precharge"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .axis { stroke: #5c6d73; stroke-width: 1.3; fill: none; }
  .grid { stroke: #d9cfba; stroke-width: 0.9; fill: none; }
  .lbl { fill: #4d5a5f; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .small { fill: #4d5a5f; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .value { fill: #003153; font: 700 19px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .sym { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .wire { stroke: #003153; stroke-width: 2.4; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .plate { stroke: #003153; stroke-width: 4; fill: none; stroke-linecap: round; }
  .dash { stroke: #5c6d73; stroke-width: 1.6; fill: none; stroke-dasharray: 7 5; stroke-linecap: round; }
  .good { stroke: #176b64; stroke-width: 3; fill: none; stroke-linecap: round; }
  .warn { stroke: #a3322a; stroke-width: 2.4; fill: none; stroke-linecap: round; }
  .cmp { stroke: #8a5019; stroke-width: 3; fill: none; stroke-linecap: round; }
  .node { fill: #003153; }
  .box { fill: none; stroke: #003153; stroke-width: 2; }
  .win { fill: none; stroke: #a3322a; stroke-width: 1.5; stroke-dasharray: 5 4; }
  .bar-good { fill: #176b64; opacity: 0.22; }
  .bar-warn { fill: #a3322a; opacity: 0.18; }
  .bar-cmp { fill: #8a5019; opacity: 0.18; }
  .halo { paint-order: stroke; stroke: #f6f1e3; stroke-width: 4; stroke-linejoin: round; }
</style>"""


def svg(width: int, height: int, title: str, desc: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{escape(title)}">\n'
        f"<title>{escape(title)}</title>\n<desc>{escape(desc)}</desc>\n{STYLE}\n"
        f'<rect class="bg" x="0" y="0" width="{width}" height="{height}"/>\n{body}\n</svg>\n'
    )


def text(
    x: float, y: float, value: str, cls: str = "lbl", anchor: str = "start", halo: bool = False
) -> str:
    classes = f"halo {cls}" if halo else cls
    return (
        f'<text class="{classes}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}">'
        f'{escape(value, quote=False)}</text>'
    )


def axis(
    x0: float, x1: float, y0: float, y1: float,
    px0: float, px1: float, py0: float, py1: float,
) -> tuple:
    def sx(x: float) -> float:
        return px0 + (x - x0) / (x1 - x0) * (px1 - px0)

    def sy(y: float) -> float:
        return py1 - (y - y0) / (y1 - y0) * (py1 - py0)

    return sx, sy


def polyline(points: list[tuple[float, float]], cls: str) -> str:
    body = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polyline class="{cls}" points="{body}"/>'


def f1_paths() -> str:
    # A narrow, stacked layout keeps 16 px component labels readable at 350 px.
    # Local styles leave F2–F5 and their frozen numerical figures unchanged.
    parts = [
        """<style>
  .f1-title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .f1-heading { fill: #003153; font: 700 18px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .f1-label { fill: #003153; font: 16px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .f1-note { fill: #4d5a5f; font: 14px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .f1-frame { fill: none; stroke: #d9cfba; stroke-width: 1.2; }
  .f1-contact { fill: #f6f1e3; stroke: #003153; stroke-width: 1.8; }
</style>""",
        text(16, 28, "图 S3-F1　三态拓扑", "f1-title"),
        text(16, 54, "绿色标本态通路；不表示恒有电流。", "f1-note"),
        text(16, 76, "实线为导体，开触点用真实断口表示。", "f1-note"),
    ]

    def panel(state, top, heading, main_closed, pre_closed, discharge_closed):
        prefix = f"f1-{state}"
        feeding = main_closed or pre_closed
        parts.extend([
            f'<g id="{prefix}" transform="translate(0,{top})" role="group" aria-label="{escape(heading)}">',
            '<rect class="f1-frame" x="8" y="8" width="384" height="368" rx="8"/>',
            text(16, 32, heading, "f1-heading"),
            text(16, 56, f"Kmain {'合' if main_closed else '开'} · Kpre {'合' if pre_closed else '开'} · Kd {'合' if discharge_closed else '开'}", "f1-note"),
        ])

        def wire(x1, y1, x2, y2, active=False):
            cls = "wire good" if active else "wire"
            parts.append(f'<line class="{cls}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>')

        def switch(name, x, y, closed, vertical=False):
            end_x, end_y = (x, y + 48) if vertical else (x + 48, y)
            blade_x, blade_y = (end_x, end_y) if closed else ((x - 22, y + 38) if vertical else (x + 38, y - 22))
            parts.append(f'<g id="{prefix}-{name}">')
            wire(x, y, blade_x, blade_y, closed)
            for cx, cy in ((x, y), (end_x, end_y)):
                parts.append(f'<circle class="f1-contact" cx="{cx}" cy="{cy}" r="3"/>')
            parts.append('</g>')

        # Distinct source terminals: neither positive feed joins the return.
        wire(42, 116, 42, 226, feeding)
        parts.append('<circle class="box" cx="42" cy="250" r="24"/>')
        parts.extend([
            text(42, 244, "＋", "f1-label", "middle"),
            text(42, 266, "－", "f1-label", "middle"),
            text(76, 260, "VS", "f1-label"),
            text(76, 282, "400 V", "f1-note"),
        ])
        wire(42, 274, 42, 326, feeding)
        wire(42, 116, 98, 116, feeding)

        # Kmain is parallel to the series Rpre + Kpre positive feed.
        wire(98, 116, 154, 116, main_closed)
        switch("Kmain", 154, 116, main_closed)
        wire(202, 116, 256, 116, main_closed)
        parts.append(text(178, 80, "Kmain", "f1-label", "middle"))
        wire(98, 116, 98, 180, pre_closed)
        wire(98, 180, 112, 180, pre_closed)
        resistor_cls = "box good" if pre_closed else "box"
        parts.append(f'<g id="{prefix}-Rpre"><rect class="{resistor_cls}" x="112" y="171" width="42" height="18"/></g>')
        wire(154, 180, 176, 180, pre_closed)
        switch("Kpre", 176, 180, pre_closed)
        wire(224, 180, 256, 180, pre_closed)
        parts.extend([
            text(133, 160, "Rpre", "f1-label", "middle"),
            text(133, 212, "170 Ω", "f1-note", "middle"),
            text(200, 212, "Kpre", "f1-label", "middle"),
        ])

        # Capacitor plates are not a wire: each has its own bus terminal.
        wire(256, 116, 256, 180, main_closed or discharge_closed)
        wire(256, 180, 256, 238, True)
        parts.extend([
            f'<g id="{prefix}-C">',
            '<line class="plate good" x1="235" y1="238" x2="277" y2="238"/>',
            '<line class="plate good" x1="235" y1="254" x2="277" y2="254"/>',
            '</g>',
            text(218, 250, "C", "f1-label", "end"),
            text(218, 274, "1 mF", "f1-note", "end"),
            text(280, 228, "＋", "f1-label"),
            text(280, 282, "－", "f1-label"),
            text(270, 102, "母线＋", "f1-label"),
            text(270, 352, "母线－", "f1-label"),
        ])
        wire(256, 254, 256, 326, True)

        # Rd + Kd spans C, entirely on the bus side of both positive feeds.
        wire(256, 116, 348, 116, discharge_closed)
        wire(348, 116, 348, 164, discharge_closed)
        resistor_cls = "box good" if discharge_closed else "box"
        parts.append(f'<g id="{prefix}-Rd"><rect class="{resistor_cls}" x="338" y="164" width="20" height="40"/></g>')
        wire(348, 204, 348, 240, discharge_closed)
        switch("Kd", 348, 240, discharge_closed, vertical=True)
        wire(348, 288, 348, 326, discharge_closed)
        parts.extend([
            text(318, 190, "Rd", "f1-label", "end"),
            text(318, 264, "Kd", "f1-label", "end"),
        ])
        wire(42, 326, 256, 326, feeding)
        wire(256, 326, 348, 326, discharge_closed)
        for name, x, y in (
            ("source-positive", 42, 116), ("source-negative", 42, 326),
            ("bus-positive", 256, 116), ("bus-negative", 256, 326),
        ):
            parts.append(f'<circle id="{prefix}-{name}" class="node" cx="{x}" cy="{y}" r="3.5"/>')
        parts.extend([
            '<circle class="node" cx="98" cy="116" r="3"/>',
            '<circle class="node" cx="256" cy="180" r="3"/>',
            '</g>',
        ])

    panel("precharge", 92, "① 预充", False, True, False)
    panel("main", 484, "② 主路接通（供电态）", True, False, False)
    panel("discharge", 876, "③ 正端隔离后泄放", False, False, True)
    for index, note in enumerate((
        "模型未画负接触器，负端始终共线。",
        "③只隔离正端馈电，不代表安全隔离或无电。",
        "未画负载与回灌；②无负载稳态电流为零。",
        "图示理想状态，不规定换接时序与完整许可。",
        "状态、测量、反馈、升压窗口须分别成立；",
        "95% 仅为示例电压条件，不能单独放行。",
        "仅供仿真与设计审查，不是高压搭建指导。",
    )):
        parts.append(text(16, 1280 + index * 22, note, "f1-note"))
    return svg(
        400, 1432,
        "S3 预充、主路接通与正端隔离后泄放的三态拓扑",
        "三个面板共用同一理想拓扑：电源正端经 Kmain 或串联的 Rpre 与 Kpre 接母线正端，母线电容 C 负端与电源负端共线，Rd 与 Kd 串联跨接 C。预充态仅 Kpre 闭合；主路态仅 Kmain 闭合；正端隔离后仅 Kd 闭合以泄放电容。开触点有真实断口。模型未画负接触器、负载与回灌，不表示安全隔离或无电；不规定换接时序。主闸完整许可仍需状态、测量有效性、反馈和升压窗口证据，95% 只是示例电压条件。仅供仿真与设计审查，不是高压搭建指导。",
        "\n".join(parts),
    )


def f2_energy_curves() -> str:
    cfg = s3.PrechargeConfig()
    parts = [
        text(24, 32, "S3-F2　VC / I / P 与三者能量账", "title"),
        text(24, 58, "左图为 400 V、1 mF、170 Ω 的理想 RC 过程；右图为源供、电阻耗、电容储三者的能量账。", "sub"),
    ]
    # Left: curves to 0.6 s.
    sx, sy = axis(0, 0.6, 0, 400, 92, 392, 96, 330)
    for t in (0, 0.2, 0.4, 0.6):
        parts.append(f'<line class="grid" x1="{sx(t):.1f}" y1="96" x2="{sx(t):.1f}" y2="330"/>')
        parts.append(text(sx(t), 348, f"{t:g}", "small", "middle"))
    for v in (0, 100, 200, 300, 400):
        parts.append(f'<line class="grid" x1="92" y1="{sy(v):.1f}" x2="392" y2="{sy(v):.1f}"/>')
        parts.append(text(84, sy(v) + 4, str(v), "small", "end"))
    v_points = []
    i_points = []
    for step in range(0, 61):
        t = step * 0.01
        v_points.append((sx(t), sy(s3.bus_voltage(cfg, t))))
        i_points.append((sx(t), sy(s3.loop_current(cfg, t) * 100)))  # current scaled x100 to share axis (unit: 0.01 A / tick)
    parts.append(polyline(v_points, "good"))
    parts.append(polyline(i_points, "warn"))
    t95 = s3.time_to_fraction(cfg, 0.95)
    parts.append(f'<line class="warn" x1="{sx(t95):.1f}" y1="96" x2="{sx(t95):.1f}" y2="330"/>')
    parts.append(f'<circle class="node" cx="{sx(t95):.1f}" cy="{sy(380):.1f}" r="4"/>')
    parts.append(text(sx(t95) + 8, 250, f"{t95:.5g} s", "small", halo=True))
    parts.append(text(92, 84, "VC / V（绿）；I×100 / V（红，0.01 A/格）", "lbl"))
    parts.append(text(242, 372, "时间 / s", "lbl", "middle"))

    # Right: energy bars at 95% and at steady state.
    e95 = s3.energy_account(cfg, 0.95)
    einf = s3.energy_account(cfg, 1.0)
    parts.append(text(470, 84, "能量 / J", "lbl"))
    categories = [("95% 时源供", e95["supplied_j"], "bar-good"), ("95% 时电阻耗", e95["spent_j"], "bar-warn"),
                  ("95% 时电容储", e95["stored_j"], "bar-cmp"), ("稳态源供", einf["supplied_j"], "bar-good"),
                  ("稳态电阻耗", einf["spent_j"], "bar-warn"), ("稳态电容储", einf["stored_j"], "bar-cmp")]
    for index, (label, value, cls) in enumerate(categories):
        y = 104 + index * 38
        width = value / 170 * 280
        parts.append(f'<rect class="{cls}" x="470" y="{y}" width="{width:.1f}" height="24"/>')
        parts.append(text(478, y + 17, label, "small"))
        parts.append(text(478 + width + 8, y + 17, f"{value:.4g} J", "value"))
    parts.append(text(24, 404, "在理想无负载环路中 ES = ER + ΔEC；本场景三者分别为 152 = 79.8 + 72.2 J（95%）与 160 = 80 + 80 J（稳态）。", "small"))
    return svg(
        800, 420,
        "S3 预充电压电流曲线与三者能量账",
        "左图VC从零升到400伏在0.50927秒达95%，电流从2.35294安衰减；右图95%时源供152焦耳等于电阻耗79.8加电容储72.2，稳态160等于80加80。",
        "\n".join(parts),
    )


def f3_timeline() -> str:
    parts = [
        text(24, 32, "S3-F3　命令、辅助触点、母线、电流与故障共时轴", "title"),
        text(24, 58, "四个信号共用同一时间轴（示意标签，不按比例）；反馈超时或升压异常时状态机停在预充，不合主闸。", "sub"),
    ]
    rows = [
        ("命令", 120, "cmd", [("0", "断开"), ("开", "预充"), ("许可", "主闸"), ("锁存", "切断")]),
        ("辅助触点", 210, "aux", [("0", "断开"), ("开", "闭合"), ("许可", "闭合"), ("锁存", "断开")]),
        ("母线 VC", 300, "vc", [("0", "0 V"), ("升", "→ 380 V"), ("许可", "合格"), ("锁存", "跌落")]),
        ("环路电流", 390, "i", [("0", "2.35 A"), ("衰", "→ 0.12 A"), ("许可", "稳态"), ("锁存", "尖峰")]),
        ("故障/复位", 480, "flt", [("0", "无"), ("—", "监控"), ("许可", "有效"), ("锁存", "停机")]),
    ]
    for name, y, _cls, ticks in rows:
        parts.append(f'<line class="axis" x1="92" y1="{y}" x2="716" y2="{y}"/>')
        parts.append(text(24, y + 4, name, "small"))
        # four phase ticks (label text carries the phase; position is by index)
        for index, (_label, value) in enumerate(ticks):
            x = 120 + index * 190
            parts.append(f'<circle class="node" cx="{x}" cy="{y}" r="4"/>')
            parts.append(text(x + 8, y - 8, value, "small", halo=True))
    parts.append(text(24, 540, "读法：先有命令，才有辅助触点；母线与电流是被测对象，不是许可本身。锁存阶段的跌落或尖峰必须能在同一轴上对齐。", "small"))
    parts.append(text(24, 564, "时间标签为示意；真实截止时间以对应注入、观测点和器件资料为准，不按本图比例抄数。", "small"))
    return svg(
        800, 580,
        "S3 预充命令与反馈的共时轴",
        "命令、辅助触点、母线电压、环路电流和故障复位在同一时间轴上依次出现；反馈超时或升压异常时停在预充不合主闸。",
        "\n".join(parts),
    )


def f4_validity_evidence() -> str:
    parts = [
        text(24, 32, "S3-F4　母线有电≠可合闸：单读数不能定因", "title"),
        text(24, 58, "380 V 可对应多种原因，也可能同时存在；须用独立观测缩小范围，不能由一个读数确定根因。", "sub"),
    ]
    cards = [
        ("残压", "电容仍有储能", "泄放路径与衰减曲线", "good"),
        ("外部回灌", "外部负载/电源反送", "外部能源与电流方向", "warn"),
        ("触点粘连", "主触点可能未断开", "辅助触点与路径电流", "warn"),
        ("测量卡值", "读数保持在 380 V", "独立测点或诊断激励", "warn"),
    ]
    for index, (title, body, evidence, cls) in enumerate(cards):
        x = 24 + index * 196
        parts.append(f'<rect class="bar-{cls}" x="{x}" y="96" width="180" height="150"/>')
        parts.append(f'<line class="{cls}" x1="{x}" y1="96" x2="{x}" y2="246"/>')
        parts.append(text(x + 12, 124, title, "value"))
        parts.append(text(x + 12, 152, body, "small"))
        parts.append(text(x + 12, 178, "所需观测：", "small"))
        parts.append(text(x + 12, 202, evidence, "small"))
        parts.append(text(x + 12, 230, "不能从读数反推根因", "small"))
    parts.append(text(24, 290, "可能原因可组合；下列证据须注明观测点、有效性与时间：", "lbl"))
    steps = [
        "1. 辅助触点、路径电流与命令是否相符（辅助触点不能单独证明主触点）",
        "2. 独立电压测点与诊断激励的响应是否一致（排查卡值或测量失效）",
        "3. 已确认的能源路径及电流方向能否解释母线维持（排查回灌或馈电未断）",
        "4. 已知泄放路径下是否符合预期衰减（排查残压，允许多原因组合）",
    ]
    y = 316
    for step in steps:
        parts.append(text(24, y, step, "small"))
        y += 30
    parts.append(text(24, 452, "四项过程证据：预充状态完成、测量有效、反馈一致、升压在窗口内；95% 只是示例电压条件。", "small"))
    parts.append(text(24, 476, "仍须核接通电流与器件证据；仅供设计审查，非高压步骤；泄放不等于紧急分断。", "small"))
    return svg(
        800, 492,
        "S3 母线高电压的可能原因、组合与所需证据",
        "残压、外部回灌、触点粘连和测量卡值是可能原因，可以组合出现；须结合辅助触点与路径电流、独立测点、能源路径和泄放衰减核查。四项过程证据与示例电压条件不能替代接通电流及器件限值证据。仅供仿真与设计审查，不是高压操作步骤。", 
        "\n".join(parts),
    )


def f5_device_limits() -> str:
    cfg = s3.PrechargeConfig()
    rush = s3.initial_inrush(cfg)
    e95 = s3.energy_account(cfg, 0.95)
    parts = [
        text(24, 32, "S3-F5　器件限制与重复热的工作点", "title"),
        text(24, 58, "左图把峰值电流、单次能量、脉冲功率与重复间隔放在同一张限值表上；右图说明重复预充的热量从哪来。", "sub"),
    ]
    # Left: limit table in millimetres (bar of current).
    parts.append(text(24, 84, "峰值电流（教学限值 3.0 A）", "lbl"))
    width = rush["current_a"] / cfg.devices_precharge_peak_a * 320
    parts.append(f'<rect class="bar-good" x="24" y="100" width="{width:.1f}" height="36"/>')
    parts.append(f'<line class="warn" x1="{24 + 320:.1f}" y1="92" x2="{24 + 320:.1f}" y2="148"/>')
    parts.append(text(30, 124, f"{rush['current_a']:.5g} A", "value"))
    parts.append(text(24 + 320 - 4, 92, "限值", "small", "end"))
    parts.append(text(24, 168, f"初始功率 {rush['power_w']:.5g} W；95% 时功率 {e95['bus_v'] * 0.05 * cfg.source_v / cfg.precharge_r_ohm:.5g}·…", "small"))
    parts.append(text(24, 196, "单次能量 80 J；重复间隔、热降额、脉冲功率曲线必须查具体料号后才可当验收阈值。", "small"))

    # Right: repeated heating points.
    parts.append(text(420, 84, "重复预充的热量账", "lbl"))
    repeats = [1, 2, 5, 10]
    for index, n in enumerate(repeats):
        x = 420 + index * 92
        height = min(n * 18, 120)
        parts.append(f'<rect class="bar-cmp" x="{x}" y="{240 - height}" width="64" height="{height}"/>')
        parts.append(text(x + 32, 258, f"n={n}", "small", "middle"))
        parts.append(text(x + 32, 240 - height - 8, f"{n * 80} J", "small", "middle", halo=True))
    parts.append(text(24, 292, "每次预充把约 80 J 送进回路（稳态上限）；重复脉冲的热量用重复间隔与热降额判断，不是按单次合格推断。", "small"))

    parts.append(text(24, 330, "20 V 残余压差的接通电流：预充 170 Ω 下 0.118 A，但 20 mΩ 主闸回路则为 1000 A（见 s3 代码注释）。", "small"))
    parts.append(text(24, 354, "不能只按 95% 比例签字：剩余压差乘以主闸回路电阻才是接通电流，未知的回路电阻就是未知风险。", "small"))
    return svg(
        800, 372,
        "S3 器件限制、重复预充热量与残余压差工作点",
        "左图峰值电流2.35294安、单次能量80焦耳有教学限值；右图重复预充热量按80焦耳倍增；20伏残余压差在预充电阻下0.118安、在20毫欧主闸回路下1000安。",
        "\n".join(parts),
    )


def build_targets() -> dict[str, str]:
    return {
        "S3-F1-current-paths.svg": f1_paths(),
        "S3-F2-energy-account.svg": f2_energy_curves(),
        "S3-F3-state-timeline.svg": f3_timeline(),
        "S3-F4-validity-evidence.svg": f4_validity_evidence(),
        "S3-F5-device-limits.svg": f5_device_limits(),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, content in build_targets().items():
        path = OUT / name
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
