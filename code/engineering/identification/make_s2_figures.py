#!/usr/bin/env python3
"""Generate the S2 data figures from the same frozen scenario as the experiment.

Only the mechanism panel (S2-F1) is hand-authored: it carries the polarity and
element ownership that a data plot cannot show. Every number in F2-F5 is read
from ``s2_identification.py`` at generation time, so the figures cannot drift
from the report without the tests failing.

Visual language (original BMS handdraw, no external style ID): warm paper,
Prussian-blue structure, teal for the normal branch, ochre for comparison,
vermilion for the fault/counterexample branch, and KaiTi headings. Data
polylines, quantitative axes and text are never jittered or filtered; only the
mechanism bodies (resistors, load, fitting window) carry restrained crosshatch.

Run:
    python code/engineering/identification/make_s2_figures.py
"""
from __future__ import annotations

import math
from html import escape
from pathlib import Path

import s2_identification as s2

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "bms-book" / "engineering" / "assets" / "s2-model"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .paper-grain { fill: url(#paper-grain); }
  .grain-dot { fill: #b6a988; opacity: 0.55; }
  .rule { stroke: #b9ab8d; stroke-width: 1.1; fill: none; stroke-linecap: round; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; letter-spacing: 0.2px; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .stamp { fill: #8a8271; font: 12px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .axis { stroke: #5c6d73; stroke-width: 1.35; fill: none; stroke-linecap: round; }
  .grid { stroke: #d9cfba; stroke-width: 0.9; fill: none; }
  .lbl { fill: #4d5a5f; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .small { fill: #4d5a5f; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .value { fill: #003153; font: 700 20px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .eq { fill: #003153; font: 700 19px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sym { fill: #003153; font: 700 22px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .ocv { stroke: #003153; stroke-width: 3.2; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .term { stroke: #1d6a62; stroke-width: 3.2; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .ohm { stroke: #9a5b22; stroke-width: 3.2; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .pol { stroke: #b23a2e; stroke-width: 3.2; fill: none; stroke-dasharray: 10 5; stroke-linecap: round; }
  .cur { stroke: #34495c; stroke-width: 3.2; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .soc-a { stroke: #9a5b22; stroke-width: 3.2; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .soc-b { stroke: #003153; stroke-width: 3.2; fill: none; stroke-dasharray: 10 5; stroke-linecap: round; }
  .overlap { stroke: #9a5b22; stroke-width: 2.1; fill: none; stroke-dasharray: 3 3; stroke-linecap: round; }
  .note { fill: #b23a2e; font: 700 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .good { fill: #1d6a62; font: 700 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .window { fill: url(#hatch-window); stroke: #b23a2e; stroke-width: 1.6; stroke-dasharray: 4 3; }
  .bar-a { fill: #9a5b22; opacity: 0.16; }
  .bar-b { fill: #1d6a62; opacity: 0.14; }
  .wire { stroke: #003153; stroke-width: 2.4; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .plate { stroke: #003153; stroke-width: 4.2; fill: none; stroke-linecap: round; }
  .dash { stroke: #5c6d73; stroke-width: 1.6; fill: none; stroke-dasharray: 7 5; stroke-linecap: round; }
  .r0 { stroke: #9a5b22; stroke-width: 2.6; fill: url(#hatch-umber); }
  .rc { stroke: #b23a2e; stroke-width: 2.6; fill: url(#hatch-red); }
  .load { stroke: #003153; stroke-width: 2.2; fill: url(#hatch-ink); }
  .cur2 { stroke: #34495c; stroke-width: 2.8; fill: none; stroke-linecap: round; }
  .node { fill: #003153; }
  .mark { stroke: #b23a2e; stroke-width: 2; fill: none; }
  .boundary-dot { fill: none; stroke: #b23a2e; stroke-width: 2; }
  .halo { paint-order: stroke; stroke: #f6f1e3; stroke-width: 4; stroke-linejoin: round; }
  .hatch-umber-line { stroke: #9a5b22; stroke-width: 1.1; opacity: 0.42; fill: none; }
  .hatch-red-line { stroke: #b23a2e; stroke-width: 1.0; opacity: 0.38; fill: none; }
  .hatch-ink-line { stroke: #003153; stroke-width: 1.0; opacity: 0.30; fill: none; }
  .hatch-window-line { stroke: #b23a2e; stroke-width: 0.9; opacity: 0.30; fill: none; }
</style>"""


def defs() -> str:
    """Paper grain and restrained crosshatch fills, all authored geometry."""
    dots = []
    for index in range(26):
        x = (index * 47 + 11) % 120
        y = (index * 71 + 29) % 120
        radius = 0.55 + (index % 4) * 0.22
        dots.append(f'<circle class="grain-dot" cx="{x}" cy="{y}" r="{radius:.2f}"/>')
    hatch = {
        "hatch-umber": ('hatch-umber-line', 7),
        "hatch-red": ('hatch-red-line', 8),
        "hatch-ink": ('hatch-ink-line', 9),
        "hatch-window": ('hatch-window-line', 8),
    }
    patterns = []
    for name, (cls, pitch) in hatch.items():
        patterns.append(
            f'<pattern id="{name}" width="{pitch}" height="{pitch}" '
            f'patternUnits="userSpaceOnUse" patternTransform="rotate(35)">'
            f'<path class="{cls}" d="M0.6 0 V{pitch} M0 0.6 H{pitch}"/></pattern>'
        )
    return (
        "<defs>\n"
        '<pattern id="paper-grain" width="120" height="120" patternUnits="userSpaceOnUse">\n'
        + "".join(dots)
        + "\n</pattern>\n"
        + "\n".join(patterns)
        + "\n</defs>"
    )


def rule(width: int) -> str:
    return f'<path class="rule" d="M24 39 Q{width / 2:g} 37.4 {width - 24} 39"/>'


def stamp(width: int) -> str:
    return text(width - 24, 32, "自绘示意 · 教学合成值", "stamp", "end")


def svg(width: int, height: int, title: str, desc: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{escape(title)}">\n'
        f"<title>{escape(title)}</title>\n<desc>{escape(desc)}</desc>\n{STYLE}\n{defs()}\n"
        f'<rect class="bg" x="0" y="0" width="{width}" height="{height}"/>\n'
        f'<rect class="paper-grain" x="0" y="0" width="{width}" height="{height}"/>\n'
        f"{rule(width)}\n{stamp(width)}\n{body}\n</svg>\n"
    )


def fmt(value: float) -> str:
    return f"{value:.6g}"


def axis(
    x0: float, x1: float, y0: float, y1: float,
    px0: float, px1: float, py0: float, py1: float,
) -> tuple:
    def sx(x: float) -> float:
        return px0 + (x - x0) / (x1 - x0) * (px1 - px0)

    def sy(y: float) -> float:
        # y0 sits at the bottom (py1) and y1 at the top (py0): larger values go up.
        return py1 - (y - y0) / (y1 - y0) * (py1 - py0)

    return sx, sy


def polyline(points: list[tuple[float, float]], cls: str) -> str:
    body = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polyline class="{cls}" points="{body}"/>'


def text(
    x: float, y: float, value: str, cls: str = "lbl", anchor: str = "start", halo: bool = False
) -> str:
    classes = f"halo {cls}" if halo else cls
    return (
        f'<text class="{classes}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}">'
        f'{escape(value, quote=False)}</text>'
    )


def f2_components() -> str:
    cfg = s2.CellConfig()
    table = s2.simulate_pulse(cfg)
    samples = table["samples"]
    t_max = samples[-1].t_s
    parts = [
        text(24, 32, "同一根时间轴上，四个电压项各自何时变化", "title"),
        text(
            24, 55,
            "教学场景 S2-pulse-identification：2 A 放电 10 s，撤流后静置 180 s；"
            "欧姆项随电流跳变，极化项有记忆。",
            "sub",
        ),
    ]

    # Lane 1: current.
    sx, sy = axis(0, t_max, 0, 2.4, 80, 760, 92, 168)
    parts.append('<line class="axis" x1="80" y1="168" x2="760" y2="168"/>')
    parts.append('<line class="axis" x1="80" y1="92" x2="80" y2="168"/>')
    for tick in range(0, 191, 20):
        parts.append(f'<line class="grid" x1="{sx(tick):.1f}" y1="92" x2="{sx(tick):.1f}" y2="168"/>')
        parts.append(text(sx(tick), 186, str(tick), "small", "middle"))
    parts.append(text(776, 84, "t / s", "small", "end"))
    parts.append(text(24, 96, "I / A", "lbl"))
    current_pts = [(s.t_s, s.current_a) for s in samples if s.t_s <= table["release_time_s"]]
    current_pts = [(0.0, 0.0)] + current_pts + [(table["release_time_s"], 0.0)]
    parts.append(polyline([(sx(t), sy(i)) for t, i in current_pts], "cur"))
    parts.append(text(sx(5.0), 100, "2 A", "small", "middle"))
    parts.append(text(sx(120), 161, "0 A", "small", "middle"))

    # Lane 2: OCV and terminal voltage.
    sx, sy = axis(0, t_max, 3.630, 3.690, 80, 760, 238, 330)
    for tick in range(0, 191, 20):
        parts.append(f'<line class="grid" x1="{sx(tick):.1f}" y1="238" x2="{sx(tick):.1f}" y2="330"/>')
    for volt in (3.64, 3.66, 3.68):
        parts.append(f'<line class="grid" x1="80" y1="{sy(volt):.1f}" x2="760" y2="{sy(volt):.1f}"/>')
        parts.append(text(72, sy(volt) + 4, f"{volt:.2f}", "small", "end"))
    parts.append(text(24, 232, "电压 / V", "lbl"))
    ocv_pts, term_pts = [], []
    for s in samples:
        ocv = cfg.ocv(s.z)
        ocv_pts.append((sx(s.t_s), sy(ocv)))
        if s.t_s == 0.0 and s.current_a == 0.0:
            continue
        term_pts.append((sx(s.t_s), sy(s.voltage_v)))
    parts.append('<line class="axis" x1="80" y1="330" x2="760" y2="330"/>')
    parts.append(polyline(ocv_pts, "ocv"))
    parts.append(polyline(term_pts, "term"))
    parts.append(text(300, 248, "OCV U(z)：放电时缓慢下移", "small", halo=True))
    parts.append(text(300, 292, "端电压 V：先掉 40 mV，再随极化下沉", "small", halo=True))
    parts.append(f'<line class="grid" x1="{sx(10):.1f}" y1="238" x2="{sx(10):.1f}" y2="330" stroke-dasharray="5 4"/>')
    parts.append(text(sx(10) + 6, 246, "撤流", "small", halo=True))

    # Lane 3: ohmic and polarization terms in mV.
    sx, sy = axis(0, t_max, 0, 46, 80, 760, 396, 494)
    for tick in range(0, 191, 20):
        parts.append(f'<line class="grid" x1="{sx(tick):.1f}" y1="396" x2="{sx(tick):.1f}" y2="494"/>')
    for mv in (0, 10, 20, 30, 40):
        parts.append(f'<line class="grid" x1="80" y1="{sy(mv):.1f}" x2="760" y2="{sy(mv):.1f}"/>')
        parts.append(text(72, sy(mv) + 4, str(mv), "small", "end"))
    parts.append(text(24, 380, "分量 / mV", "lbl"))
    parts.append('<line class="axis" x1="80" y1="494" x2="760" y2="494"/>')
    parts.append(text(sx(t_max / 2), 514, "t / s", "small", "middle"))
    ohm_pts = []
    pol_pts = []
    for s in samples:
        if s.t_s == 0.0:
            continue
        ohm_pts.append((sx(s.t_s), sy(cfg.r0_ohm * s.current_a * 1000)))
        pol_pts.append((sx(s.t_s), sy(s.vp_v * 1000)))
    parts.append(polyline(ohm_pts, "ohm"))
    parts.append(polyline(pol_pts, "pol"))
    parts.append(text(sx(30), sy(40) - 6, "欧姆项 I·R0：撤流即归零", "small", halo=True))
    parts.append(text(sx(48), sy(12), "极化 vp：撤流瞬间 5.98 mV，按 exp(−t/45 s) 回落", "small", halo=True))
    parts.append(f'<line class="grid" x1="{sx(10):.1f}" y1="396" x2="{sx(10):.1f}" y2="494" stroke-dasharray="5 4"/>')

    parts.append(
        text(
            24, 548,
            "读图：欧姆项是输入的即时函数，极化项是状态；把两者都塞进一个 R0 会让短脉冲参数互相顶替。",
            "small",
        )
    )
    return svg(
        800, 566,
        "同一时间轴上的电流、OCV、欧姆压降、极化压降与端电压",
        "2 安放电 10 秒后撤流静置 180 秒。电流在 10 秒处回零，欧姆压降同时消失，"
        "极化压降从 5.98 毫伏按 45 秒时间常数衰减，端电压因此先跳起再缓慢逼近 OCV。",
        "\n".join(parts),
    )


def f3_windows() -> str:
    cfg = s2.CellConfig()
    table = s2.simulate_pulse(cfg)
    noisy_t, noisy_v = s2.noisy_rest(cfg, table, cfg.noise_seed, cfg.noise_sigma_v)
    taus = s2.tau_grid()
    long_points = s2.fit_rest_tail(noisy_t, noisy_v, taus)
    short = [(t, v) for t, v in zip(noisy_t, noisy_v, strict=True) if t <= 5.0 + 1e-12]
    short_points = s2.fit_rest_tail([t for t, _ in short], [v for _, v in short], taus)
    # RMS preserves the SSE argmin within each fixed window, not an accuracy ranking
    # between windows. Keep the frozen samples and every finite grid candidate.
    long_rms = [
        (p.tau_s, math.sqrt(p.sse_v2 / len(noisy_t)))
        for p in long_points
        if math.isfinite(p.sse_v2)
    ]
    short_rms = [
        (p.tau_s, math.sqrt(p.sse_v2 / len(short)))
        for p in short_points
        if math.isfinite(p.sse_v2)
    ]
    long_min_pt = min(long_rms, key=lambda item: item[1])
    short_min_pt = min(short_rms, key=lambda item: item[1])

    parts = [
        text(24, 70, "短窗与长窗：看见了什么", "f3-title"),
        text(24, 98, "同一脉冲 · σ = 1 mV · 种子 7", "f3-small"),
        text(24, 136, "A　窗口覆盖", "f3-label"),
        text(24, 164, "端电压 / V", "f3-label"),
        text(376, 164, f"{cfg.rest_s:g} s 长窗 · {len(noisy_t)} 点", "f3-small", "end"),
    ]
    # Panel A: the 5/180 window keeps its true width on the full rest-time axis.
    sx, sy = axis(0, 180, 3.6690, 3.6805, 84, 376, 216, 396)
    for tick in (0, 45, 90, 135, 180):
        parts.append(f'<line class="grid" x1="{sx(tick):.1f}" y1="216" x2="{sx(tick):.1f}" y2="396"/>')
        parts.append(text(sx(tick), 420, str(tick), "f3-small", "middle"))
    for volt in (3.670, 3.675, 3.680):
        parts.append(f'<line class="grid" x1="84" y1="{sy(volt):.1f}" x2="376" y2="{sy(volt):.1f}"/>')
        parts.append(text(76, sy(volt) + 5, f"{volt:.3f}", "f3-small", "end"))
    parts.append(f'<rect class="window" x="{sx(0):.2f}" y="216" width="{sx(5) - sx(0):.2f}" height="180"/>')
    parts.append(polyline([(sx(t), sy(v)) for t, v in zip(noisy_t, noisy_v, strict=True)], "term"))
    parts.append('<line class="axis" x1="84" y1="396" x2="376" y2="396"/>')
    parts.append(text(230, 446, "撤流后时间 t / s", "f3-label", "middle"))
    parts.append(text(128, 190, f"5 s 短窗 · {len(short)} 点", "f3-small"))
    parts.append(f'<path class="mark" d="M128 196 H108 L{sx(2.5):.2f} 212"/>')

    # Panel B: unchanged per-sample RMS values on a shared mV scale.
    parts.append(text(24, 492, "B　本窗目标函数", "f3-label"))
    parts.append(text(24, 524, "每样本 RMS 残差 / mV", "f3-label"))
    parts.append('<line class="term" x1="84" y1="548" x2="114" y2="548"/>')
    parts.append(text(122, 554, "180 s 长窗", "f3-small"))
    parts.append('<line class="pol" x1="242" y1="548" x2="272" y2="548"/>')
    parts.append(text(280, 554, "5 s 短窗", "f3-small"))
    sx, sy = axis(10, 120, 1.00, 1.45, 84, 376, 592, 772)
    for tick in (10, 30, 45, 60, 90, 120):
        parts.append(f'<line class="grid" x1="{sx(tick):.1f}" y1="592" x2="{sx(tick):.1f}" y2="772"/>')
        parts.append(text(sx(tick), 796, str(tick), "f3-small", "middle"))
    for mv in (1.00, 1.10, 1.20, 1.30, 1.40):
        parts.append(f'<line class="grid" x1="84" y1="{sy(mv):.1f}" x2="376" y2="{sy(mv):.1f}"/>')
        parts.append(text(76, sy(mv) + 5, f"{mv:.2f}", "f3-small", "end"))
    parts.append(polyline([(sx(t), sy(v * 1000.0)) for t, v in long_rms], "term"))
    parts.append(polyline([(sx(t), sy(v * 1000.0)) for t, v in short_rms], "pol"))
    parts.append('<line class="axis" x1="84" y1="772" x2="376" y2="772"/>')
    parts.append(text(230, 824, "候选 τ / s", "f3-label", "middle"))
    parts.append(f'<line class="grid" x1="{sx(45):.1f}" y1="592" x2="{sx(45):.1f}" y2="772" stroke-dasharray="5 4"/>')
    parts.append(text(sx(45) + 8, 618, "真值 45 s", "f3-small", halo=True))
    parts.append(
        f'<circle class="node" cx="{sx(long_min_pt[0]):.1f}" '
        f'cy="{sy(long_min_pt[1] * 1000.0):.1f}" r="3.5"/>'
    )
    parts.append(
        f'<circle class="boundary-dot" cx="{sx(short_min_pt[0]):.1f}" '
        f'cy="{sy(short_min_pt[1] * 1000.0):.1f}" r="4.2"/>'
    )
    parts.append(
        text(sx(long_min_pt[0]) + 12, sy(long_min_pt[1] * 1000.0) - 12,
             f"{long_min_pt[0]:g} s", "f3-small", halo=True)
    )
    parts.append(
        text(368, sy(short_min_pt[1] * 1000.0) - 18,
             f"{short_min_pt[0]:g} s 边界", "f3-small", "end", halo=True)
    )
    parts.append(text(24, 864, "RMS 只比较本窗内的 τ 候选。", "f3-small"))
    parts.append(text(24, 892, "两窗不能按残差大小排名精度。", "f3-small"))

    # F3 alone uses mobile-sized text, including the stamp emitted by svg().
    # Leave the shared style and the other four figures byte-for-byte unchanged.
    f3_style = """
  .f3-title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .f3-label { fill: #4d5a5f; font: 700 18px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .f3-small { fill: #4d5a5f; font: 16px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .f3-stamp { fill: #8a8271; font: 16px 'KaiTi','STKaiti','Noto Serif SC',serif; }
"""
    return svg(
        400, 920,
        "短窗与长窗的静置拟合以及时间常数的 RMS 残差剖面",
        "上面板为种子 7 的带噪端电压，保留 361 个观测点；"
        "前 5 秒窗含 11 点，按 5/180 的真实比例绘制。"
        "下面板保留长短窗在全部 τ 候选上的每样本 RMS 残差；"
        "长窗本窗最小值在 43 秒，短窗几乎水平（变化不到 0.4%），"
        "本窗最小值在 120 秒网格边界，但合成真值 45 秒在网格内。"
        "RMS 不能跨窗排名精度，边界最优也不证明真值在网格外或算法无解。",
        "\n".join(parts),
    ).replace("</style>", f"{f3_style}</style>", 1).replace('class="stamp"', 'class="f3-stamp"', 1)


def f4_slope() -> str:
    parts = [
        text(24, 32, "同一个 5 mV 偏置，斜率决定它换算成多少 SOC", "title"),
        text(
            24, 55,
            "局部反演 Δz = b / g。g 是 OCV 斜率，V·SOC⁻¹；斜率越平，同样的电压误差越致命。",
            "sub",
        ),
    ]
    bars = [
        ("g = 0.8 V·SOC⁻¹（近满充的陡段）", 0.625, "soc-b", "bar-b"),
        ("g = 0.08 V·SOC⁻¹（平台区）", 6.25, "soc-a", "bar-a"),
    ]
    base_y = 110
    max_pp = 7.0
    for index, (label, value, cls, fill_cls) in enumerate(bars):
        y = base_y + index * 108
        width = value / max_pp * 560
        parts.append(text(24, y, label, "lbl"))
        parts.append(f'<rect class="{fill_cls}" x="60" y="{y + 16}" width="{width:.1f}" height="34"/>')
        parts.append(f'<line class="{cls}" x1="60" y1="{y + 50}" x2="{60 + width:.1f}" y2="{y + 50}"/>')
        parts.append(text(60 + width + 10, y + 42, f"{value:g} pp", "value"))
    axis_y = 300
    parts.append(f'<line class="axis" x1="60" y1="{axis_y}" x2="620" y2="{axis_y}"/>')
    for pp in (0, 2, 4, 6, 7):
        x = 60 + pp / max_pp * 560
        parts.append(f'<line class="axis" x1="{x:.1f}" y1="{axis_y}" x2="{x:.1f}" y2="{axis_y + 5}"/>')
        parts.append(text(x, axis_y + 20, f"{pp:g}", "small", "middle"))
    parts.append(text(630, axis_y + 4, "SOC 偏差 / pp", "lbl"))
    parts.append(text(24, 350, "5 mV 偏置在陡段只值 0.625 pp，在平台区值 6.25 pp——差 10 倍。", "note"))
    parts.append(
        text(
            24, 376,
            "所以「电压误差 5 mV」不能单独作为 SOC 精度指标；必须连同当时的 OCV 斜率、温度、滞回方向一起报告。",
            "small",
        )
    )
    parts.append(text(24, 400, "条形长度按 pp 线性缩放；这不是实测分布，是同一偏置在两段斜率上的解析换算。", "small"))
    return svg(
        800, 420,
        "同一电压偏置在不同 OCV 斜率上换算出的 SOC 误差",
        "5 毫伏偏置在 0.8 伏每 SOC 的陡段对应 0.625 个百分点，在 0.08 伏每 SOC 的平台区对应 6.25 个百分点；"
        "条形长度按百分点线性缩放，是解析换算，不是实测分布。",
        "\n".join(parts),
    )


def f5_counterexample() -> str:
    cfg = s2.CellConfig(scenario_id=s2.FLAT_SCENARIO_ID, ocv_slope_v_per_soc=0.08, noise_sigma_v=0.0)
    a_cfg = s2.replace(cfg, z0=0.50)
    b_cfg = s2.replace(cfg, z0=0.60)
    a = s2.simulate_pulse(a_cfg)["samples"]
    b = s2.simulate_pulse(b_cfg)["samples"]
    bias_v = 0.008
    t_max = a[-1].t_s
    parts = [
        text(24, 32, "两条完全重合的测量电压，背后可以是相差 10 pp 的 SOC", "title"),
        text(
            24, 55,
            "平台区 g = 0.08 V·SOC⁻¹：A 组 z0 = 0.50 且偏置 +8 mV；B 组 z0 = 0.60、无偏置。"
            "输入、R0/R1/C1 与初始极化相同。",
            "sub",
        ),
    ]
    # Left: measured voltage (identical).
    sx, sy = axis(0, t_max, 3.550, 3.615, 80, 380, 96, 300)
    for tick in (0, 60, 120, 180):
        parts.append(f'<line class="grid" x1="{sx(tick):.1f}" y1="96" x2="{sx(tick):.1f}" y2="300"/>')
        parts.append(text(sx(tick), 316, str(tick), "small", "middle"))
    for volt in (3.56, 3.58, 3.60):
        parts.append(f'<line class="grid" x1="80" y1="{sy(volt):.1f}" x2="380" y2="{sy(volt):.1f}"/>')
        parts.append(text(74, sy(volt) + 4, f"{volt:.2f}", "small", "end"))
    a_meas = [(sx(s.t_s), sy(s.voltage_v + bias_v)) for s in a if s.t_s > 0]
    b_meas = [(sx(s.t_s), sy(s.voltage_v)) for s in b if s.t_s > 0]
    parts.append(polyline(b_meas, "term"))
    parts.append(polyline(a_meas, "overlap"))
    parts.append('<line class="axis" x1="80" y1="300" x2="380" y2="300"/>')
    parts.append(text(230, 336, "t / s", "lbl", "middle"))
    parts.append(text(20, 88, "测得端电压 / V", "lbl"))
    parts.append(text(150, 272, "A 与 B 重合（差 < 1e-12 V）", "good", halo=True))

    # Right: SOC, separated by 10 pp.
    sx, sy = axis(0, t_max, 0.49, 0.61, 470, 760, 96, 300)
    for tick in (0, 60, 120, 180):
        parts.append(f'<line class="grid" x1="{sx(tick):.1f}" y1="96" x2="{sx(tick):.1f}" y2="300"/>')
        parts.append(text(sx(tick), 316, str(tick), "small", "middle"))
    for soc in (0.50, 0.55, 0.60):
        parts.append(f'<line class="grid" x1="470" y1="{sy(soc):.1f}" x2="760" y2="{sy(soc):.1f}"/>')
        parts.append(text(464, sy(soc) + 4, f"{soc:.2f}", "small", "end"))
    parts.append(polyline([(sx(s.t_s), sy(s.z)) for s in a if s.t_s > 0], "soc-a"))
    parts.append(polyline([(sx(s.t_s), sy(s.z)) for s in b if s.t_s > 0], "soc-b"))
    parts.append('<line class="axis" x1="470" y1="300" x2="760" y2="300"/>')
    parts.append(text(615, 336, "t / s", "lbl", "middle"))
    parts.append(text(396, 100, "真实 SOC", "lbl"))
    parts.append(text(480, 104, "B：0.60", "good", halo=True))
    parts.append(text(480, 270, "A：0.50", "note", halo=True))
    parts.append(f'<line class="mark" x1="740" y1="{sy(0.60):.1f}" x2="740" y2="{sy(0.50):.1f}"/>')
    parts.append(text(732, sy(0.55) + 4, "10 pp", "note", "end", halo=True))
    parts.append(
        text(
            24, 372,
            "解除混淆需要新信息：独立校准的电压通道、一次已知静置的 OCV 锚点、",
            "small",
        )
    )
    parts.append(
        text(
            24, 392,
            "改变 SOC 的充放电账本，或一条能压过偏置量级的激励。仅凭这组电压，A 与 B 不可区分。",
            "small",
        )
    )
    parts.append(text(24, 412, "本图用平直线性 OCV 做严格反例；它不证明所有真实工况永远不可辨识。", "small"))
    return svg(
        800, 420,
        "平台区偏置反例：电压重合而 SOC 相差十个百分点",
        "严格反例（线性 OCV）：左图 A 组 z0=0.50 加 8 毫伏偏置后与 B 组 z0=0.60 的测量电压逐点重合；"
        "右图两组真实 SOC 分别从 0.50 和 0.60 出发，全程保持 10 个百分点的差距。",
        "\n".join(parts),
    )


def f1_circuit() -> str:
    """Series Thevenin loop: source -> R0 -> (R1 || C1) -> terminals -> load.

    The parallel cell is drawn as a two-terminal ladder inside the series path.
    Its bottom rung is NOT tied to the negative rail; otherwise the cell would be
    a shunt across the terminals and vp would no longer be the series drop.
    """
    parts = [
        text(24, 32, "谁拥有哪一段电压：R0 是即时项，vp 是带记忆的状态", "title"),
        text(24, 55, "回路顺序：U(z) → R0 → R1∥C1 → 正端子；放电为正，电流从 + 端子经负载回到 − 端子。", "sub"),
        text(24, 74, "矩形内的剖面线只表示器件体；R1∥C1 是串联的二端网络，vp 不是跨在端子上的旁路。", "sub"),
        # Left leg: ideal OCV source, + plate on top.
        '<circle class="wire" cx="120" cy="300" r="34"/>',
        '<line class="plate" x1="98" y1="286" x2="142" y2="286"/>',
        '<line class="plate" x1="108" y1="304" x2="132" y2="304"/>',
        text(78, 272, "+", "lbl", "end"),
        text(78, 340, "−", "lbl", "end"),
        text(162, 296, "U(z)", "lbl"),
        text(162, 316, "OCV，随 SOC 变化", "small"),
        '<line class="wire" x1="120" y1="170" x2="120" y2="266"/>',
        '<line class="wire" x1="120" y1="334" x2="120" y2="430"/>',
        # Top rail: source -> R0 -> left bridge of the parallel cell.
        '<line class="wire" x1="120" y1="170" x2="190" y2="170"/>',
        '<rect class="r0" x="190" y="156" width="64" height="28" rx="3"/>',
        text(222, 146, "R0 = 20 mΩ", "lbl", "middle"),
        text(222, 206, "电流一变，压降立刻变", "small", "middle"),
        '<line class="wire" x1="254" y1="170" x2="300" y2="170"/>',
        # Parallel cell: two rungs joined by two end bridges, in series on the top path.
        '<line class="wire" x1="300" y1="170" x2="300" y2="300"/>',
        '<line class="wire" x1="430" y1="170" x2="430" y2="300"/>',
        '<line class="wire" x1="300" y1="170" x2="330" y2="170"/>',
        '<rect class="rc" x="330" y="156" width="70" height="28" rx="3"/>',
        '<line class="wire" x1="400" y1="170" x2="430" y2="170"/>',
        text(365, 146, "R1 = 15 mΩ", "lbl", "middle"),
        '<line class="wire" x1="300" y1="300" x2="348" y2="300"/>',
        '<line class="plate" x1="352" y1="286" x2="352" y2="314"/>',
        '<line class="plate" x1="368" y1="286" x2="368" y2="314"/>',
        '<line class="wire" x1="372" y1="300" x2="430" y2="300"/>',
        text(365, 340, "C1 = 3000 F", "lbl", "middle"),
        # vp is the drop across the cell, measured along the series path.
        '<line class="dash" x1="306" y1="236" x2="372" y2="236"/>',
        '<polygon points="380,236 366,230 366,242" class="node"/>',
        text(365, 226, "vp", "note", "middle"),
        # Series path continues to the + terminal.
        '<line class="wire" x1="430" y1="170" x2="560" y2="170"/>',
        '<line class="wire" x1="120" y1="430" x2="560" y2="430"/>',
        '<circle class="node" cx="300" cy="170" r="4"/>',
        '<circle class="node" cx="430" cy="170" r="4"/>',
        '<circle class="node" cx="300" cy="300" r="4"/>',
        '<circle class="node" cx="430" cy="300" r="4"/>',
        '<circle class="node" cx="560" cy="170" r="5"/>',
        '<circle class="node" cx="560" cy="430" r="5"/>',
        text(548, 158, "+", "sym", "end"),
        text(548, 462, "−", "sym", "end"),
        # External loop, connected to both terminals.
        '<line class="dash" x1="560" y1="170" x2="660" y2="170"/>',
        '<line class="dash" x1="560" y1="430" x2="660" y2="430"/>',
        '<line class="dash" x1="660" y1="170" x2="660" y2="250"/>',
        '<line class="dash" x1="660" y1="330" x2="660" y2="430"/>',
        '<rect class="load" x="646" y="250" width="28" height="80" rx="3"/>',
        '<line class="cur2" x1="660" y1="184" x2="660" y2="228"/>',
        '<polygon points="660,236 654,222 666,222" class="node"/>',
        text(672, 198, "I > 0 放电", "small"),
        text(638, 264, "外部回路", "small", "end"),
        text(638, 284, "负载 / 充电机", "small", "end"),
        # Terminal voltage across the load, extensions from the branch corners.
        '<line class="dash" x1="660" y1="170" x2="740" y2="170"/>',
        '<line class="dash" x1="660" y1="430" x2="740" y2="430"/>',
        '<line class="cur2" x1="740" y1="186" x2="740" y2="414"/>',
        '<polygon points="740,170 734,184 746,184" class="node"/>',
        '<polygon points="740,430 734,416 746,416" class="node"/>',
        text(748, 300, "V", "sym"),
        text(748, 322, "端电压", "small"),
        # Contract summary.
        text(24, 486, "V = U(z) − I·R0 − vp", "eq"),
        text(24, 512, "状态 z、vp 在区间内连续更新；欧姆项只由当前电流决定。同一状态的两侧极限：", "small"),
        text(24, 534, "V(t−) = U(z) − I·R0 − vp，V(t+) = U(z) − I′·R0 − vp。电流在区间端点改变时，V 跳过 R0·ΔI。", "small"),
        text(24, 556, "因此「采样点在跳变前还是跳变后」必须写进场景合同；把返回值当区间起点会错开一拍。", "small"),
    ]
    return svg(
        800, 566,
        "一阶 RC 等效电路：OCV、欧姆项、极化项与端电压的归属和极性",
        "理想 OCV 源串联 R0，再串联 R1 与 C1 的并联二端网络，最后接到正端子；"
        "外部回路由两端子引出，经负载回到负端子。放电电流从正端子流出，"
        "端电压等于 OCV 减去欧姆压降 I 乘 R0，再减去串联网络上的极化压降 vp。",
        "\n".join(parts),
    )


def build_targets() -> dict[str, str]:
    """Return every figure as a string, keyed by file name. Pure: no disk writes."""
    return {
        "S2-F1-rc-polarity.svg": f1_circuit(),
        "S2-F2-common-time-axis.svg": f2_components(),
        "S2-F3-window-and-tau-profile.svg": f3_windows(),
        "S2-F4-slope-sensitivity.svg": f4_slope(),
        "S2-F5-bias-counterexample.svg": f5_counterexample(),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, content in build_targets().items():
        path = OUT / name
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(ROOT)} ({len(content)} chars, {fmt(len(content) / 1024)} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
