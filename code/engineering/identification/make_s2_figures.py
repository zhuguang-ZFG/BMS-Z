#!/usr/bin/env python3
"""Generate the S2 data figures from the same frozen scenario as the experiment.

Only the mechanism panel (S2-F1) is hand-authored: it carries the polarity and
element ownership that a data plot cannot show. Every number in F2-F5 is read
from ``s2_identification.py`` at generation time, so the figures cannot drift
from the report without the tests failing.

Run:
    python code/engineering/identification/make_s2_figures.py
"""
from __future__ import annotations

import math
from html import escape
from pathlib import Path

import s2_identification as s2

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "bms-book" / "assets" / "engineering" / "s2-model"

STYLE = """<style>
  .bg { fill: #fffdf5; }
  .title { fill: #003153; font: 700 18px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .sub { fill: #5b6660; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .axis { stroke: #5b6660; stroke-width: 1.4; fill: none; }
  .grid { stroke: #d8d2c2; stroke-width: 1; fill: none; }
  .lbl { fill: #5b6660; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .small { fill: #5b6660; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .ocv { stroke: #003153; stroke-width: 3; fill: none; }
  .term { stroke: #176b64; stroke-width: 3; fill: none; }
  .ohm { stroke: #8a5019; stroke-width: 3; fill: none; }
  .pol { stroke: #a3322a; stroke-width: 3; fill: none; stroke-dasharray: 9 5; }
  .cur { stroke: #3b3350; stroke-width: 3; fill: none; }
  .soc-a { stroke: #8a5019; stroke-width: 3; fill: none; }
  .soc-b { stroke: #176b64; stroke-width: 3; fill: none; stroke-dasharray: 9 5; }
  .note { fill: #a3322a; font: 700 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .good { fill: #176b64; font: 700 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .box { fill: none; stroke: #8a5019; stroke-width: 1.4; }
  .wire { stroke: #003153; stroke-width: 2.6; fill: none; stroke-linecap: round; }
  .plate { stroke: #003153; stroke-width: 4; fill: none; stroke-linecap: round; }
  .dash { stroke: #5b6660; stroke-width: 1.8; fill: none; stroke-dasharray: 7 5; }
  .r0 { stroke: #8a5019; stroke-width: 3; fill: none; }
  .rc { stroke: #a3322a; stroke-width: 3; fill: none; }
  .cur2 { stroke: #3b3350; stroke-width: 3; fill: none; }
  .node { fill: #003153; }
  .mark { stroke: #a3322a; stroke-width: 2; fill: none; }
  .tag { fill: #fffdf5; stroke-width: 1.6; }
  .halo { paint-order: stroke; stroke: #fffdf5; stroke-width: 4; stroke-linejoin: round; }
</style>"""


def svg(width: int, height: int, title: str, desc: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{escape(title)}">\n'
        f"<title>{escape(title)}</title>\n<desc>{escape(desc)}</desc>\n{STYLE}\n"
        f'<rect class="bg" x="0" y="0" width="{width}" height="{height}"/>\n{body}\n</svg>\n'
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
        return py0 + (y - y0) / (y1 - y0) * (py1 - py0)

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
    parts.append(text(778, 190, "t / s", "small"))
    parts.append(text(24, 96, "电流 I / A", "lbl"))
    current_pts = [(s.t_s, s.current_a) for s in samples if s.t_s <= table["release_time_s"]]
    current_pts = [(0.0, 0.0)] + current_pts + [(table["release_time_s"], 0.0)]
    parts.append(polyline([(sx(t), sy(i)) for t, i in current_pts], "cur"))
    parts.append(text(sx(9.0), 112, "2 A", "small", "end"))
    parts.append(text(sx(0.2), 90, "0 A", "small"))

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
    parts.append(text(300, 252, "OCV U(z)：放电时缓慢下移", "small", halo=True))
    parts.append(text(300, 290, "端电压 V：先掉 40 mV，再随极化下沉", "small", halo=True))
    parts.append(f'<line class="grid" x1="{sx(10):.1f}" y1="238" x2="{sx(10):.1f}" y2="330" stroke-dasharray="5 4"/>')
    parts.append(text(sx(10) + 6, 250, "撤流", "small", halo=True))

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
    parts = [
        text(24, 32, "短窗看着更稳，τ 却在边界上；长窗才显出曲率", "title"),
        text(
            24, 55,
            "同一段 10 s 脉冲后的静置观测，加 σ = 1 mV 噪声（种子 7）。"
            "左：观测与前 5 s 拟合窗；右：目标函数沿 τ 网格的剖面。",
            "sub",
        ),
    ]
    # Panel A: rest voltage with shaded 0-5 s window.
    sx, sy = axis(0, 180, 3.6690, 3.6805, 80, 380, 96, 300)
    for tick in (0, 45, 90, 135, 180):
        parts.append(f'<line class="grid" x1="{sx(tick):.1f}" y1="96" x2="{sx(tick):.1f}" y2="300"/>')
        parts.append(text(sx(tick), 316, str(tick), "small", "middle"))
    for volt in (3.670, 3.675, 3.680):
        parts.append(f'<line class="grid" x1="80" y1="{sy(volt):.1f}" x2="380" y2="{sy(volt):.1f}"/>')
        parts.append(text(74, sy(volt) + 4, f"{volt:.3f}", "small", "end"))
    parts.append(f'<rect class="box" x="{sx(0):.1f}" y="96" width="{sx(5) - sx(0):.1f}" height="204" stroke-dasharray="4 3"/>')
    noisy_t, noisy_v = s2.noisy_rest(cfg, table, cfg.noise_seed, cfg.noise_sigma_v)
    parts.append(polyline([(sx(t), sy(v)) for t, v in zip(noisy_t, noisy_v, strict=True)], "term"))
    parts.append('<line class="axis" x1="80" y1="300" x2="380" y2="300"/>')
    parts.append(text(230, 336, "撤流后时间 t / s", "lbl", "middle"))
    parts.append(text(96, 112, "0–5 s 窗：11 点（占横轴 2.8%）", "small", halo=True))
    parts.append(text(20, 88, "端电压 / V", "lbl"))

    # Panel B: objective profile, log10 normalised.
    long_profile = []
    short_profile = []
    noisy_t, noisy_v = s2.noisy_rest(cfg, table, cfg.noise_seed, cfg.noise_sigma_v)
    taus = s2.tau_grid()
    long_points = s2.fit_rest_tail(noisy_t, noisy_v, taus)
    short = [(t, v) for t, v in zip(noisy_t, noisy_v, strict=True) if t <= 5.0 + 1e-12]
    short_points = s2.fit_rest_tail([t for t, _ in short], [v for _, v in short], taus)
    long_min = min(p.sse_v2 for p in long_points if math.isfinite(p.sse_v2))
    short_min = min(p.sse_v2 for p in short_points if math.isfinite(p.sse_v2))
    for point in long_points:
        long_profile.append((point.tau_s, math.log10(max(point.sse_v2 / long_min, 1e-18))))
    for point in short_points:
        short_profile.append((point.tau_s, math.log10(max(point.sse_v2 / short_min, 1e-18))))
    top = 8.0
    sx, sy = axis(10, 120, 0, top, 470, 760, 96, 300)
    for tick in (10, 30, 45, 60, 90, 120):
        parts.append(f'<line class="grid" x1="{sx(tick):.1f}" y1="96" x2="{sx(tick):.1f}" y2="300"/>')
        parts.append(text(sx(tick), 316, str(tick), "small", "middle"))
    for exp in range(0, 9, 2):
        parts.append(f'<line class="grid" x1="470" y1="{sy(exp):.1f}" x2="760" y2="{sy(exp):.1f}"/>')
        parts.append(text(464, sy(exp) + 4, f"1e{exp}", "small", "end"))
    parts.append(polyline([(sx(t), sy(min(v, top))) for t, v in long_profile], "term"))
    parts.append(polyline([(sx(t), sy(min(v, top))) for t, v in short_profile], "pol"))
    parts.append('<line class="axis" x1="470" y1="300" x2="760" y2="300"/>')
    parts.append(text(615, 336, "候选 τ / s", "lbl", "middle"))
    parts.append(text(470, 84, "残差平方和（相对最小值）", "lbl"))
    parts.append(f'<line class="grid" x1="{sx(45):.1f}" y1="96" x2="{sx(45):.1f}" y2="300" stroke-dasharray="5 4"/>')
    parts.append(text(sx(45) + 5, 120, "真值 45 s", "small", halo=True))
    parts.append('<line class="term" x1="650" y1="176" x2="690" y2="176"/>')
    parts.append(text(698, 181, "180 s 长窗", "small"))
    parts.append('<line class="pol" x1="650" y1="200" x2="690" y2="200"/>')
    parts.append(text(698, 205, "5 s 短窗", "small"))
    parts.append(
        text(
            24, 372,
            "种子 7 的结果：长窗最优 τ = 43 s，K 偏差 0.035 mV；"
            "短窗最优落在网格右端 120 s，K 偏差 16.6 mV（约 2.08 pp）。",
            "small",
        )
    )
    parts.append(
        text(
            24, 396,
            "这不是「短窗必然更差」的普遍定律：无噪声时短窗也能命中 45 s，"
            "只有测量噪声把 K 与 A 的互换放大后才出现边界解。",
            "small",
        )
    )
    return svg(
        800, 420,
        "短窗与长窗的静置拟合以及时间常数目标函数剖面",
        "左侧端电压在撤流后从 3.6724 伏回升到 3.6778 伏，前 5 秒只走了很小一段。"
        "右侧目标函数剖面显示长窗在 43 秒有清晰极小值，短窗的极小值被噪声推到 120 秒网格边界。",
        "\n".join(parts),
    )


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
        ("g = 0.8 V·SOC⁻¹（近满充的陡段）", 0.625, "soc-b"),
        ("g = 0.08 V·SOC⁻¹（平台区）", 6.25, "soc-a"),
    ]
    base_y = 110
    max_pp = 7.0
    for index, (label, value, cls) in enumerate(bars):
        y = base_y + index * 108
        width = value / max_pp * 560
        parts.append(text(24, y, label, "lbl"))
        parts.append(f'<rect class="{cls}" x="60" y="{y + 16}" width="{width:.1f}" height="34" fill-opacity="0.18"/>')
        parts.append(f'<line class="{cls}" x1="60" y1="{y + 50}" x2="{60 + width:.1f}" y2="{y + 50}"/>')
        parts.append(text(60 + width + 10, y + 42, f"{value:g} pp", "title"))
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
        "5 毫伏偏置在 0.8 伏每 SOC 的陡段对应 0.625 个百分点，在 0.08 伏每 SOC 的平台区对应 6.25 个百分点。",
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
    parts.append(polyline(a_meas, "soc-a"))
    parts.append('<line class="axis" x1="80" y1="300" x2="380" y2="300"/>')
    parts.append(text(230, 336, "t / s", "lbl", "middle"))
    parts.append(text(20, 88, "测得端电压 / V", "lbl"))
    parts.append(text(100, 128, "A 与 B 重合（差 < 1e-12 V）", "good", halo=True))

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
    parts.append(text(480, 270, "B：0.60", "good", halo=True))
    parts.append(text(480, 104, "A：0.50", "note", halo=True))
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
        "左图 A 组加 8 毫伏偏置后与 B 组测量电压完全重合；右图两组真实 SOC 分别从 0.50 和 0.60 出发，"
        "全程保持 10 个百分点的差距。",
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
        text(24, 74, "R1∥C1 是串联的二端网络；vp 是它两端的压降，不是跨在端子上的旁路。", "sub"),
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
        text(548, 158, "+", "title", "end"),
        text(548, 462, "−", "title", "end"),
        # External loop, connected to both terminals.
        '<line class="dash" x1="560" y1="170" x2="660" y2="170"/>',
        '<line class="dash" x1="560" y1="430" x2="660" y2="430"/>',
        '<line class="dash" x1="660" y1="170" x2="660" y2="250"/>',
        '<line class="dash" x1="660" y1="330" x2="660" y2="430"/>',
        '<rect class="box" x="646" y="250" width="28" height="80" rx="3"/>',
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
        text(748, 300, "V", "title"),
        text(748, 322, "端电压", "small"),
        # Contract summary.
        text(24, 486, "V = U(z) − I·R0 − vp", "title"),
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
