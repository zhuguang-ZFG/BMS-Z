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
    parts = [
        text(24, 32, "S3-F1　预充 / 主回路 / 泄放：三个状态，三条路", "title"),
        text(24, 58, "实线为导电路径，虚线为控制信号。主闸断开时，只有预充支路导电；泄放支路平时必须断开。", "sub"),
    ]
    # Source on the left, bus capacitor on the right.
    parts += [
        '<rect class="box" x="56" y="150" width="120" height="120"/>',
        text(116, 176, "电源", "lbl", "middle"),
        text(116, 200, "400 V", "small", "middle"),
        text(116, 224, "直流母线", "small", "middle"),
        '<line class="wire" x1="176" y1="180" x2="240" y2="180"/>',
        # Main contactor (normally open in precharge state).
        '<rect class="box" x="240" y="158" width="96" height="44"/>',
        text(288, 176, "主触点", "small", "middle"),
        text(288, 194, "断开", "small", "middle"),
        '<line class="wire" x1="336" y1="180" x2="420" y2="180"/>',
        # Bus capacitor.
        '<rect class="box" x="420" y="150" width="140" height="120"/>',
        text(490, 176, "母线电容", "lbl", "middle"),
        text(490, 200, "1 mF", "small", "middle"),
        text(490, 224, "电压 VC", "small", "middle"),
        # Precharge branch (resistor + contactor) below.
        '<line class="wire" x1="116" y1="270" x2="116" y2="340"/>',
        '<rect class="box" x="56" y="340" width="120" height="44"/>',
        text(116, 358, "预充 R + 触点", "small", "middle"),
        text(116, 376, "导通", "small", "middle"),
        '<line class="wire" x1="176" y1="362" x2="336" y2="362"/>',
        '<line class="wire" x1="336" y1="362" x2="336" y2="270"/>',
        '<line class="wire" x1="336" y1="270" x2="420" y2="270"/>',
        # Discharge branch (dashed: normally off).
        '<line class="dash" x1="490" y1="270" x2="490" y2="412"/>',
        '<rect class="box" x="430" y="412" width="120" height="44"/>',
        text(490, 430, "泄放 R + 触点", "small", "middle"),
        text(490, 448, "断开", "small", "middle"),
        # Return path.
        '<line class="wire" x1="490" y1="456" x2="490" y2="500"/>',
        '<line class="wire" x1="490" y1="500" x2="116" y2="500"/>',
        '<line class="wire" x1="116" y1="500" x2="116" y2="270"/>',
        '<polygon class="node" points="300,500 310,494 310,506"/>',
        text(300, 528, "负回线（只有一条）", "small", "middle"),
        # Control signals.
        '<line class="dash" x1="288" y1="100" x2="288" y2="158"/>',
        text(288, 88, "控制", "small", "middle"),
        '<line class="dash" x1="116" y1="150" x2="116" y2="100"/>',
        text(470, 88, "主闸许可还要看反馈与有效性", "small", "middle"),
        text(24, 558, "预充态：预充支路是唯一导电路径；主闸与泄放支路都断开。合主闸的许可另看 S3-F3/F4，不能只看 95%。", "small"),
        text(24, 582, "图为分状态电流路径的机制图，不是高压搭建指导。高电压与绝缘在正文只作仿真与设计审查对象。", "small"),
    ]
    return svg(
        800, 600,
        "S3 预充、主回路与泄放三状态的电流路径",
        "电源经主触点或预充电阻触点到母线电容，泄放支路平时断开；预充状态只有预充支路导电，主闸与泄放均断开。",
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
        text(24, 32, "S3-F4　母线有电≠可以合闸：四种证据无法区分", "title"),
        text(24, 58, "同一句“母线 380 V”对应四种互斥根因，必须用独立证据区分；只读一个电压值是根因诊断错误。", "sub"),
    ]
    cards = [
        ("残压", "泄放后电容仍留电", "查泄放状态与放电时间", "good"),
        ("外部回灌", "外部负载/电源反送", "查电源侧与回路方向", "warn"),
        ("触点粘连", "主触点已直接导通", "看辅助触点与实际电流", "warn"),
        ("测量卡值", "传感器卡在 380 V", "冗余通道或独立激励", "warn"),
    ]
    for index, (title, body, evidence, cls) in enumerate(cards):
        x = 24 + index * 196
        parts.append(f'<rect class="bar-{cls}" x="{x}" y="96" width="180" height="150"/>')
        parts.append(f'<line class="{cls}" x1="{x}" y1="96" x2="{x}" y2="246"/>')
        parts.append(text(x + 12, 124, title, "value"))
        parts.append(text(x + 12, 152, body, "small"))
        parts.append(text(x + 12, 178, "独立证据：", "small"))
        parts.append(text(x + 12, 202, evidence, "small"))
        parts.append(text(x + 12, 230, "不能从读数反推根因", "small"))
    parts.append(text(24, 290, "可区分的证据链（每一项都要有观测点）：", "lbl"))
    steps = [
        "1. 辅助触点状态与实际环路电流是否一致（粘连 vs 正常）",
        "2. 冗余电压通道或开线激励是否仍然给出 380 V（卡值 vs 真值）",
        "3. 电源侧断开与负载侧断开后，母线是否仍维持（回灌 vs 残压）",
        "4. 泄放支路动作后电压是否按 RC 衰减（残压与测量链是否正常）",
    ]
    y = 316
    for step in steps:
        parts.append(text(24, y, step, "small"))
        y += 30
    parts.append(text(24, 452, "主闸许可必须同时满足：状态为 PRECHARGE_DONE、测量有效、反馈正常、升压在窗口内（F3），缺一即拒绝。", "small"))
    parts.append(text(24, 476, "图为机制与证据清单，不是高压操作步骤。残压泄放策略与紧急分断策略不能混同。", "small"))
    return svg(
        800, 492,
        "S3 母线电压读数的四种根因与可区分证据",
        "残压、外部回灌、触点粘连和测量卡值都会读出高电压；必须用辅助触点电流、冗余通道、电源隔离与泄放衰减等独立证据区分。",
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
