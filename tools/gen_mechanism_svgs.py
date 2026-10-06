#!/usr/bin/env python3
"""按公式或 code/soc 仿真输出重画机制动画。

运行（仓库根目录）：

    python3 tools/gen_mechanism_svgs.py

会覆盖 docs/circuits/assets/ 里 main() 登记的那些 SVG。
曲线点来自下面的函数，或来自 ``code/soc/compare.py`` 的 ``run()``。
不改 ``code/`` 里的算法。数字是示意或仿真，不是电芯实测。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "circuits" / "assets"
SOC_DIR = ROOT / "code" / "soc"

# 单文件大约 20 KB。超了就少抽样，不要改公式。
MAX_BYTES = 20 * 1024

STYLE = """
    .bg { fill: #ffffff; }
    .panel { fill: #f4f6f8; stroke: #d0d7de; }
    .axis { stroke: #57606a; stroke-width: 1.5; fill: none; }
    .grid { stroke: #d0d7de; stroke-width: 1; fill: none; }
    .txt { fill: #1f2328; font-size: 13px; }
    .small { fill: #57606a; font-size: 12px; }
    .title { fill: #1f2328; font-size: 16px; font-weight: bold; }
    .hi { fill: #0969da; }
    .warn { fill: #cf222e; }
    .ok { fill: #1a7f37; }
    .gold { fill: #9a6700; }
    .lineb { stroke: #0969da; stroke-width: 2.5; fill: none; }
    .liner { stroke: #cf222e; stroke-width: 2.5; fill: none; }
    .lineg { stroke: #1a7f37; stroke-width: 2.2; fill: none; stroke-dasharray: 6 4; }
    .liney { stroke: #bf8700; stroke-width: 2.2; fill: none; }
    .linek { stroke: #57606a; stroke-width: 2.2; fill: none; stroke-dasharray: 7 4; }
    .dotb { fill: #0969da; }
    .dotr { fill: #cf222e; }
    .dotg { fill: #1a7f37; }
    .doty { fill: #bf8700; }
    .boxb { fill: #ddf4ff; stroke: #0969da; }
    .boxy { fill: #fff8c5; stroke: #d4a72c; }
    .boxr { fill: #ffebe9; stroke: #ff8182; }
    @media (prefers-color-scheme: dark) {
      .bg { fill: #0d1117; }
      .panel { fill: #161b22; stroke: #30363d; }
      .axis { stroke: #8b949e; }
      .grid { stroke: #30363d; }
      .txt { fill: #e6edf3; }
      .small { fill: #8b949e; }
      .title { fill: #e6edf3; }
      .hi { fill: #4493f8; }
      .warn { fill: #ff7b72; }
      .ok { fill: #3fb950; }
      .gold { fill: #d29922; }
      .lineb { stroke: #4493f8; }
      .liner { stroke: #ff7b72; }
      .lineg { stroke: #3fb950; }
      .liney { stroke: #d29922; }
      .linek { stroke: #8b949e; }
      .dotb { fill: #4493f8; }
      .dotr { fill: #ff7b72; }
      .dotg { fill: #3fb950; }
      .doty { fill: #d29922; }
      .boxb { fill: #12233a; stroke: #4493f8; }
      .boxy { fill: #3d2e00; stroke: #d29922; }
      .boxr { fill: #3d1418; stroke: #f85149; }
    }
"""

STEP_KT = "0;0.2490;0.2500;0.4990;0.5000;0.7490;0.7500;1"
STEP_OPACITY = (
    "1;1;0.28;0.28;0.28;0.28;0.28;0.28",
    "0.28;0.28;1;1;0.28;0.28;0.28;0.28",
    "0.28;0.28;0.28;0.28;1;1;0.28;0.28",
    "0.28;0.28;0.28;0.28;0.28;0.28;1;1",
)


def wrap(title: str, desc: str, body: str, height: int, formula_note: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 {height}" role="img" '
        f'font-family="ui-monospace, Consolas, monospace">\n'
        f"  <title>{title}</title>\n"
        f"  <desc>{desc}</desc>\n"
        f"  <style>{STYLE}  </style>\n"
        f"  <!-- {formula_note} -->\n"
        f"{body}\n"
        f"</svg>\n"
    )


def steps(lines: list[str], y0: float = 72, dy: float = 26) -> str:
    chunks = []
    for i, line in enumerate(lines):
        y = y0 + i * dy
        chunks.append(
            f'  <text class="txt" x="40" y="{y:.0f}" opacity="0.28">{line}'
            f'<animate attributeName="opacity" values="{STEP_OPACITY[i]}" '
            f'keyTimes="{STEP_KT}" dur="12s" repeatCount="indefinite"/></text>'
        )
    return "\n".join(chunks)


def poly(points: list[tuple[float, float]], cls: str) -> str:
    body = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return (
        f'  <polyline class="{cls}" points="{body}" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
    )


def key_times(n: int) -> str:
    """n 个采样（含首尾）均匀铺满，首项 0、末项 1。"""
    if n < 2:
        raise ValueError("至少两个关键帧")
    parts = ["0"]
    for i in range(1, n - 1):
        parts.append(f"{i / (n - 1):.4f}")
    parts.append("1")
    return ";".join(parts)


def segment_times(n_stations: int) -> str:
    """n 段停留：0, 1/n, …, 1。末段停在最后一站。"""
    parts = ["0"]
    for k in range(1, n_stations):
        parts.append(f"{k / n_stations:.4f}")
    parts.append("1")
    return ";".join(parts)


def dot(
    samples: list[tuple[float, float]],
    cls: str = "doty",
    r: float = 6,
    dur: str = "12s",
    kt: str | None = None,
    begin: str | None = None,
) -> str:
    xs = ";".join(f"{x:.1f}" for x, _ in samples)
    ys = ";".join(f"{y:.1f}" for _, y in samples)
    if kt is None:
        kt = key_times(len(samples))
    x0, y0 = samples[0]
    # 相位差用负的 begin，keyTimes 仍从 0 起。不要去改 keyTimes 的头。
    lag = f' begin="{begin}"' if begin else ""
    return (
        f'  <circle class="{cls}" r="{r}" cx="{x0:.1f}" cy="{y0:.1f}">'
        f'<animate attributeName="cx" values="{xs}" keyTimes="{kt}" dur="{dur}" repeatCount="indefinite"{lag}/>'
        f'<animate attributeName="cy" values="{ys}" keyTimes="{kt}" dur="{dur}" repeatCount="indefinite"{lag}/>'
        f"</circle>"
    )


def fade_labels(
    items: list[str],
    x: float,
    y: float,
    cls: str = "txt",
    anchor: str = "start",
    dur: str = "12s",
    kt: str | None = None,
) -> str:
    """同一位置轮流显示几句读数。离散切换，和游标的关键帧对齐。"""
    n = len(items)
    if kt is None:
        kt = segment_times(n)
    n_keys = len(kt.split(";"))
    chunks = []
    for i, text in enumerate(items):
        vals = ";".join("1" if k == i else "0" for k in range(n_keys))
        opacity = "1" if i == 0 else "0"
        chunks.append(
            f'  <text class="{cls}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" opacity="{opacity}">{text}'
            f'<animate attributeName="opacity" values="{vals}" keyTimes="{kt}" '
            f'calcMode="discrete" dur="{dur}" repeatCount="indefinite"/></text>'
        )
    return "\n".join(chunks)


def axis_box(x0: float, y0: float, x1: float, y1: float) -> str:
    return (
        f'  <line class="axis" x1="{x0:.1f}" y1="{y0:.1f}" x2="{x0:.1f}" y2="{y1:.1f}"/>\n'
        f'  <line class="axis" x1="{x0:.1f}" y1="{y1:.1f}" x2="{x1:.1f}" y2="{y1:.1f}"/>'
    )


def xticks(x_of, y_axis: float, ticks: list[tuple[float, str]]) -> str:
    lines = []
    for value, label in ticks:
        x = x_of(value)
        lines.append(
            f'  <line class="grid" x1="{x:.1f}" y1="{y_axis:.1f}" x2="{x:.1f}" y2="{y_axis + 6:.1f}"/>'
        )
        lines.append(
            f'  <text class="small" x="{x:.1f}" y="{y_axis + 22:.1f}" text-anchor="middle">{label}</text>'
        )
    return "\n".join(lines)


def axis_title_xy(tick_x: float, tick_y: float, tick_label: str) -> tuple[float, float]:
    """轴标题放到最后一个刻度的右侧。

    旧底栏把标题和末刻度写在同一个 (x, y) 上，text-anchor 一个是 end、一个是
    middle，两个字叠在一起。标题从刻度右缘再空一截开始，仍在刻度那一行。
    """
    half = 0.62 * 12 * max(len(tick_label), 1) / 2
    return tick_x + half + 12, tick_y


def yticks(y_of, x_axis: float, ticks: list[tuple[float, str]]) -> str:
    lines = []
    for value, label in ticks:
        y = y_of(value)
        lines.append(
            f'  <line class="grid" x1="{x_axis - 6:.1f}" y1="{y:.1f}" x2="{x_axis:.1f}" y2="{y:.1f}"/>'
        )
        lines.append(
            f'  <text class="small" x="{x_axis - 10:.1f}" y="{y + 4:.1f}" text-anchor="end">{label}</text>'
        )
    return "\n".join(lines)


def _shape(soc: np.ndarray) -> np.ndarray:
    """平台主斜率 0.075 V/单位 SOC，两端用 tanh 抬头。示意，不是电芯表。"""
    s = np.asarray(soc, dtype=float)
    return (
        0.075 * (s - 0.5)
        + 0.09 * np.tanh((s - 0.08) * 24.0)
        + 0.07 * np.tanh((s - 0.93) * 20.0)
    )


def ocv_mean(soc, anchor: float) -> np.ndarray:
    s = np.asarray(soc, dtype=float)
    return anchor + _shape(s) - _shape(np.array(0.5))


def slope_v_per_unit(soc: float, anchor: float) -> float:
    eps = 1e-4
    return float((ocv_mean(soc + eps, anchor) - ocv_mean(soc - eps, anchor)) / (2 * eps))


# 滞回半宽。缝 = 40 mV，和阶段 4 底栏同一组示意数。
HYST_HALF_V = 0.020
HYST_ANCHOR_V = 3.300
PLATEAU_ANCHOR_V = 3.295


def build_hysteresis() -> str:
    soc = np.linspace(0.04, 0.96, 90)
    mean = ocv_mean(soc, HYST_ANCHOR_V)
    chg = mean + HYST_HALF_V
    dis = mean - HYST_HALF_V
    x0, x1, y_top, y_bot = 108.0, 520.0, 228.0, 430.0
    smin, smax = 0.04, 0.96
    vmin, vmax = 3.05, 3.55

    def x_of(s):
        return x0 + (np.asarray(s, dtype=float) - smin) / (smax - smin) * (x1 - x0)

    def y_of(v):
        return y_top + (vmax - np.asarray(v, dtype=float)) / (vmax - vmin) * (y_bot - y_top)

    chg_pts = list(zip(x_of(soc), y_of(chg), strict=True))
    dis_pts = list(zip(x_of(soc), y_of(dis), strict=True))
    stations = [0.08, 0.30, 0.50, 0.70, 0.92]
    dot_pts = [(x_of(s), y_of(float(ocv_mean(s, HYST_ANCHOR_V)))) for s in stations]
    framed = dot_pts + [dot_pts[-1]]
    kt = segment_times(len(stations))
    cursor_x = ";".join(f"{p[0]:.1f}" for p in framed)
    labels = []
    for s in stations:
        v_hi = float(ocv_mean(s, HYST_ANCHOR_V) + HYST_HALF_V)
        v_lo = v_hi - 2 * HYST_HALF_V
        sl_mv = slope_v_per_unit(s, HYST_ANCHOR_V) * 10.0  # mV / 1%
        gap_mv = 2 * HYST_HALF_V * 1000.0
        soc_pp = gap_mv / sl_mv
        labels.append(
            f"s={s:.2f}  充 {v_hi:.3f} V  放 {v_lo:.3f} V  "
            f"{gap_mv:.0f} mV / {sl_mv:.2f} mV每1% → {soc_pp:.1f} 个百分点"
        )
    body = f"""  <rect class="bg" width="800" height="560"/>
  <text class="title" x="24" y="32">同一个荷电，充电电压更高（示意）</text>
  <rect class="panel" x="24" y="48" width="752" height="128" rx="6"/>
{steps([
    "① 先看缝<tspan class=\"small\">　充电支 = 平均支 + 20 mV，放电支 = 平均支 − 20 mV。</tspan>",
    "② 走到 0.50<tspan class=\"small\">　充 3.320 V，放 3.280 V。缝还是 40 mV。</tspan>",
    "③ 平台上<tspan class=\"small\">　斜率大约 0.75 mV/1%。40 mV 能换五十多个百分点。</tspan>",
    "④ 两端变陡<tspan class=\"small\">　同样 40 mV，换到的荷电少很多。口诀：充高放低，静置抹不平。</tspan>",
])}
  <rect class="panel" x="24" y="188" width="752" height="280" rx="6"/>
  <text class="small" x="40" y="210">电压 V（示意）</text>
{axis_box(x0, y_top, x1, y_bot)}
  <text class="small" x="{x1:.1f}" y="468" text-anchor="end">荷电 SOC</text>
{xticks(x_of, y_bot, [(0.2, "0.2"), (0.5, "0.5"), (0.8, "0.8")])}
{yticks(y_of, x0, [(3.20, "3.20"), (3.30, "3.30"), (3.40, "3.40")])}
{poly(chg_pts, "liner")}
{poly(dis_pts, "lineb")}
  <text class="warn" x="400" y="250">充电支</text>
  <text class="hi" x="400" y="400">放电支</text>
  <line class="liney" y1="{y_top:.1f}" y2="{y_bot:.1f}" x1="{framed[0][0]:.1f}" x2="{framed[0][0]:.1f}">
    <animate attributeName="x1" values="{cursor_x}" keyTimes="{kt}" dur="12s" repeatCount="indefinite"/>
    <animate attributeName="x2" values="{cursor_x}" keyTimes="{kt}" dur="12s" repeatCount="indefinite"/>
  </line>
{dot(framed, kt=kt)}
  <rect class="panel" x="24" y="480" width="752" height="64" rx="6"/>
{fade_labels(labels, 40, 518, cls="small", kt=kt)}
"""
    return wrap(
        "OCV 滞回：同一 SOC 充电支高 20 mV、放电支低 20 mV。平台上 40 mV 能换成几十个百分点。数字为示意。",
        "平均支加恒定滞回项。游标走到不同荷电时，读出两支电压、斜率和缝换算的荷电差。示意，不是实测。",
        body,
        560,
        "formula: V=OCV_mean(s)±0.020; OCV_mean anchors 3.300 V at s=0.5; plateau slope 0.075 V per unit SOC",
    )


def build_plateau() -> str:
    soc = np.linspace(0.04, 0.96, 90)
    volt = ocv_mean(soc, PLATEAU_ANCHOR_V)
    x0, x1, y_top, y_bot = 96.0, 430.0, 248.0, 420.0
    smin, smax = 0.04, 0.96
    vmin, vmax = 3.05, 3.55
    ix0, ix1, iy_top, iy_bot = 500.0, 748.0, 276.0, 420.0

    def x_of(s):
        return x0 + (np.asarray(s, dtype=float) - smin) / (smax - smin) * (x1 - x0)

    def y_of(v):
        return y_top + (vmax - np.asarray(v, dtype=float)) / (vmax - vmin) * (y_bot - y_top)

    pts = list(zip(x_of(soc), y_of(volt), strict=True))
    stations = [0.08, 0.30, 0.50, 0.70, 0.92]
    dot_pts = [(x_of(s), y_of(float(ocv_mean(s, PLATEAU_ANCHOR_V)))) for s in stations]
    framed = dot_pts + [dot_pts[-1]]
    kt = segment_times(len(stations))
    labels = []
    noise_mv = 5.0
    for s in stations:
        v = float(ocv_mean(s, PLATEAU_ANCHOR_V))
        sl_mv = slope_v_per_unit(s, PLATEAU_ANCHOR_V) * 10.0
        cover = noise_mv / sl_mv
        labels.append(
            f"s={s:.2f}  V={v:.3f}  斜率 {sl_mv:.2f} mV/1%  5 mV → {cover:.1f} 个百分点"
        )
    # 平台段 0.30–0.70 的电压差，用公式算，不手写。
    v30 = float(ocv_mean(0.30, PLATEAU_ANCHOR_V))
    v70 = float(ocv_mean(0.70, PLATEAU_ANCHOR_V))
    span_mv = (v70 - v30) * 1000.0
    soc_i = np.linspace(0.30, 0.70, 41)
    inset_pts = list(
        zip(
            ix0 + (soc_i - 0.30) / 0.40 * (ix1 - ix0),
            iy_top + (3.33 - ocv_mean(soc_i, PLATEAU_ANCHOR_V)) / 0.06 * (iy_bot - iy_top),
            strict=True,
        )
    )

    def ix_of(s):
        return ix0 + (float(s) - 0.30) / 0.40 * (ix1 - ix0)

    def iy_of(v):
        return iy_top + (3.33 - float(v)) / 0.06 * (iy_bot - iy_top)

    body = f"""  <rect class="bg" width="800" height="560"/>
  <text class="title" x="24" y="32">平台上，几毫伏盖住一大截荷电（示意）</text>
  <rect class="panel" x="24" y="48" width="752" height="128" rx="6"/>
{steps([
    "① 两端还陡<tspan class=\"small\">　斜率大，5 mV 只能换零点几个百分点。</tspan>",
    f"② 进入平台<tspan class=\"small\">　0.30 到 0.70，电压从 {v30:.3f} V 到 {v70:.3f} V，只动 {span_mv:.1f} mV。</tspan>",
    "③ 正中间<tspan class=\"small\">　SOC 0.50 是 3.295 V，斜率 0.75 mV/1%。5 mV 大约盖住 6.7 个百分点。</tspan>",
    "④ 口诀<tspan class=\"small\">　同一小段毫伏，可以是两个很不同的荷电。这段信积分。</tspan>",
])}
  <rect class="panel" x="24" y="188" width="752" height="280" rx="6"/>
  <text class="small" x="40" y="210">电压 V（示意）</text>
{axis_box(x0, y_top, x1, y_bot)}
  <text class="small" x="{x1:.1f}" y="448" text-anchor="end">荷电 SOC</text>
{xticks(x_of, y_bot, [(0.3, "0.30"), (0.5, "0.50"), (0.7, "0.70")])}
{yticks(y_of, x0, [(3.20, "3.20"), (3.30, "3.30"), (3.40, "3.40")])}
  <line class="liner" x1="{x_of(0.30):.1f}" y1="{y_of(v30):.1f}" x2="{x_of(0.70):.1f}" y2="{y_of(v70):.1f}" stroke-width="4"/>
{poly(pts, "lineg")}
{dot(framed, cls="dotr", kt=kt)}
  <text class="small" x="500" y="236">局部放大（示意）</text>
  <text class="small" x="500" y="256">{span_mv:.1f} mV / 40 个百分点</text>
{axis_box(ix0, iy_top, ix1, iy_bot)}
{xticks(ix_of, iy_bot, [(0.30, "0.30"), (0.50, "0.50"), (0.70, "0.70")])}
{yticks(iy_of, ix0, [(3.28, "3.28"), (3.295, "3.295"), (3.31, "3.31")])}
{poly(inset_pts, "lineg")}
  <rect class="panel" x="24" y="480" width="752" height="64" rx="6"/>
{fade_labels(labels, 40, 518, cls="small", kt=kt)}
"""
    return wrap(
        "铁锂平台示意：荷电 0.30 到 0.70 电压只动约 30 mV。游标读出局部 dV/dSOC，以及 5 mV 噪声能盖住多少个百分点。",
        "OCV(SOC) 由平台斜率加两端 tanh 抬头生成。红点沿曲线移动，底栏切换该点的电压、斜率和噪声换算。示意，不是某一颗电芯的规格。",
        body,
        560,
        "formula: OCV anchors 3.295 V at s=0.5; dV/dSOC = 0.075 V per unit on the plateau; ends use tanh",
    )


def k_temp(temp_c: np.ndarray) -> np.ndarray:
    """冷：-20°C 为 0，10°C 为 1。热：45°C 为 1，60°C 为 0。示意。"""
    t = np.asarray(temp_c, dtype=float)
    cold = np.clip((t - (-20.0)) / (10.0 - (-20.0)), 0.0, 1.0)
    hot = np.clip((60.0 - t) / (60.0 - 45.0), 0.0, 1.0)
    return np.minimum(cold, hot)


def k_soc(soc: float) -> float:
    return float(np.clip((soc - 0.05) / (0.20 - 0.05), 0.0, 1.0))


def k_voltage(soc: float, fuse_a: float = 40.0) -> float:
    """电压墙 I=max(0,(OCV-3.00)/0.015)，再除以示意熔断 40 A，封顶 1。"""
    ocv = float(ocv_mean(soc, PLATEAU_ANCHOR_V))
    current = max(0.0, (ocv - 3.00) / 0.015)
    return min(1.0, current / fuse_a)


def k_min_at(temp_c: float, soc: float) -> tuple[float, float, float, float, float]:
    kt = float(k_temp(np.array(temp_c)))
    ks = k_soc(soc)
    kv = k_voltage(soc)
    kf = 1.0
    return kt, ks, kv, kf, min(kt, ks, kv, kf)


def slew_limit(command: np.ndarray, rate: float) -> np.ndarray:
    out = np.empty_like(command)
    prev = float(command[0])
    for i, value in enumerate(command):
        prev = prev + float(np.clip(value - prev, -rate, rate))
        out[i] = prev
    return out


def build_sop() -> str:
    temps = np.linspace(-20.0, 60.0, 81)
    soc_fixed = 0.50
    kt = k_temp(temps)
    kv = k_voltage(soc_fixed)
    kmin = np.minimum(kt, kv)  # 这个荷电上 k_soc=1、熔断=1，最短板就是温度和电压墙
    x0, x1, y_top, y_bot = 72.0, 470.0, 214.0, 360.0

    def x_of(t):
        return x0 + (np.asarray(t, dtype=float) - (-20.0)) / 80.0 * (x1 - x0)

    def y_of(k):
        return y_top + (1.0 - np.asarray(k, dtype=float)) / 1.0 * (y_bot - y_top)

    kt_pts = list(zip(x_of(temps), y_of(kt), strict=True))
    kv_pts = [(x_of(t), y_of(kv)) for t in temps]
    km_pts = list(zip(x_of(temps), y_of(kmin), strict=True))
    mark_t = [-20.0, -10.0, 0.0, 25.0, 50.0, 60.0]
    dot_pts = [(x_of(t), y_of(float(k_temp(np.array(t))))) for t in mark_t]
    labels = []
    for t in mark_t:
        a, b, c, d, m = k_min_at(t, soc_fixed)
        labels.append(
            f"T={t:.0f}°C SOC {soc_fixed:.2f}　温度 {a:.3f}　荷电 {b:.3f}　"
            f"电压墙 {c:.3f}　熔断 {d:.3f}　取最小 {m:.3f}"
        )
    # 柱：T=-10°C 的四条约束，高度来自公式。
    bar_t = -10.0
    parts_k = k_min_at(bar_t, soc_fixed)
    names = ("温度", "荷电", "电压墙", "熔断")
    bar_x0 = 520.0
    bar_w = 48.0
    gap = 16.0
    bars = []
    for i, (name, value) in enumerate(zip(names, parts_k[:4], strict=True)):
        x = bar_x0 + i * (bar_w + gap)
        y = y_of(value)
        h = y_bot - y
        bars.append(
            f'  <rect class="boxb" x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}"/>'
        )
        bars.append(
            f'  <text class="small" x="{x + bar_w / 2:.1f}" y="{y_bot + 16:.1f}" text-anchor="middle">{name}</text>'
        )
        bars.append(
            f'  <text class="small" x="{x + bar_w / 2:.1f}" y="{y - 6:.1f}" text-anchor="middle">{value:.2f}</text>'
        )
    red_y = y_of(parts_k[4])
    # 限斜率：温度从 25°C 一步掉到 -10°C，指令是 min，输出每步最多动 0.012。
    t_cmd = np.array([25.0] * 8 + [-10.0] * 16)
    cmd = np.array([k_min_at(float(t), soc_fixed)[4] for t in t_cmd])
    smooth = slew_limit(cmd, rate=0.012)
    sx0, sx1, sy_top, sy_bot = 72.0, 760.0, 470.0, 560.0

    def sx(i):
        return sx0 + i / (len(cmd) - 1) * (sx1 - sx0)

    def sy(k):
        return sy_top + (0.6 - float(k)) / 0.4 * (sy_bot - sy_top)

    cmd_pts = [(sx(i), sy(v)) for i, v in enumerate(cmd)]
    sm_pts = [(sx(i), sy(v)) for i, v in enumerate(smooth)]
    sm_dot = sm_pts[::3]
    def pulse_scale(seconds: float) -> float:
        return min(2.0, (30.0 / seconds) ** 0.5)

    cold_k = parts_k[4]
    p30 = cold_k * pulse_scale(30.0)
    p10 = cold_k * pulse_scale(10.0)
    p2 = cold_k * pulse_scale(2.0)
    body = f"""  <rect class="bg" width="800" height="640"/>
  <text class="title" x="24" y="32">能出多大力，先把每块板算出来再取最短（示意）</text>
  <rect class="panel" x="24" y="44" width="752" height="128" rx="6"/>
{steps([
    "① 温度系数<tspan class=\"small\">　-20°C 为 0，10°C 到 45°C 为 1，60°C 再回到 0。</tspan>",
    "② 另外三块<tspan class=\"small\">　荷电低于 0.20 才降；电压墙用 (OCV−3.00)/0.015，再除以 40 A。</tspan>",
    "③ 取最小<tspan class=\"small\">　-10°C、SOC 0.50 时，温度那根最矮。红线就卡在那儿。</tspan>",
    "④ 再限斜率<tspan class=\"small\">　指令可以跳，输出每步最多动 0.012。口诀：看最短板，再按秒数降。</tspan>",
], y0=68, dy=24)}
  <rect class="panel" x="24" y="184" width="752" height="230" rx="6"/>
  <text class="small" x="36" y="204">k</text>
  <text class="hi" x="64" y="204">蓝温度</text>
  <text class="ok" x="140" y="204">绿虚线电压墙</text>
  <text class="warn" x="280" y="204">红取最小</text>
{axis_box(x0, y_top, x1, y_bot)}
  <text class="small" x="{x1:.1f}" y="396" text-anchor="end">温度 °C</text>
{xticks(x_of, y_bot, [(-20, "-20"), (-10, "-10"), (10, "10"), (25, "25"), (45, "45"), (60, "60")])}
{yticks(y_of, x0, [(0, "0"), (0.5, "0.5"), (1, "1")])}
{poly(kt_pts, "lineb")}
{poly(kv_pts, "lineg")}
{poly(km_pts, "liner")}
{dot(dot_pts)}
{chr(10).join(bars)}
  <line class="liner" x1="{bar_x0:.1f}" y1="{red_y:.1f}" x2="{bar_x0 + 4 * bar_w + 3 * gap:.1f}" y2="{red_y:.1f}" stroke-width="2.5"/>
  <text class="small" x="24" y="430">柱是 T=-10°C、SOC 0.50 的四块板。脉冲示意 k·min(2, √(30/t))：30 s → {p30:.3f}，10 s → {p10:.3f}，2 s → {p2:.3f}。</text>
  <rect class="panel" x="24" y="444" width="752" height="140" rx="6"/>
  <text class="small" x="36" y="464">下面：25°C 一步掉到 -10°C。红是直接取最小，金线是限斜率之后。</text>
{axis_box(sx0, sy_top, sx1, sy_bot)}
{yticks(sy, sx0, [(0.3, "0.3"), (0.5, "0.5")])}
{poly(cmd_pts, "liner")}
{poly(sm_pts, "liney")}
{dot(sm_dot)}
  <text class="small" x="24" y="624">3.00 V、15 mΩ、40 A 和温度拐点都是教学数。产品阈值以规格书和实测为准。</text>
"""
    return wrap(
        "SOP 降额示意：温度系数、荷电系数和电压墙取最小，再按脉冲时间和斜率限制。柱高和曲线都由公式算出。",
        "k_T 在 -20°C 到 60°C 分段线性。电压墙用平台 OCV。-10°C 时温度是最短板。底栏是限斜率递推，不是手绘贝塞尔。",
        body,
        640,
        "formula: kT piecewise; kSOC clip; kV=min(1,max(0,(OCV-3)/0.015)/40); k=min; slew 0.012/step; pulse min(2,sqrt(30/t))",
    )


def kalman_trace(r_var: float, n_steps: int = 40, p0: float = 0.04, q_var: float = 0.0004):
    """标量随机游走：P←P+Q，K=P/(P+R)，P←(1-K)P。返回每步更新后的 K 和 P。"""
    p = p0
    ks = np.empty(n_steps)
    ps = np.empty(n_steps)
    for i in range(n_steps):
        p = p + q_var
        k = p / (p + r_var)
        p = (1.0 - k) * p
        ks[i] = k
        ps[i] = p
    return ks, ps


def build_kalman() -> str:
    n = 40
    k_quiet, p_quiet = kalman_trace(0.001)
    k_loud, p_loud = kalman_trace(0.02)
    # 同一条 R=0.001，把 Q 乘 4。平台会抬高。这是并进来的 P、Q、R 那张。
    k_bigq, _p_bigq = kalman_trace(0.001, q_var=0.0016)
    x0, x1, y_top, y_bot = 88.0, 520.0, 214.0, 400.0

    def x_of(step):
        return x0 + np.asarray(step, dtype=float) / (n - 1) * (x1 - x0)

    def y_of(k):
        return y_top + (1.0 - np.asarray(k, dtype=float)) / 1.0 * (y_bot - y_top)

    steps_i = np.arange(n)
    quiet_pts = list(zip(x_of(steps_i), y_of(k_quiet), strict=True))
    loud_pts = list(zip(x_of(steps_i), y_of(k_loud), strict=True))
    bigq_pts = list(zip(x_of(steps_i), y_of(k_bigq), strict=True))
    pick = [0, 1, 2, 5, 10, 39]
    dot_pts = [(x_of(i), y_of(k_quiet[i])) for i in pick]
    framed = dot_pts + [dot_pts[-1]]
    kt = segment_times(len(pick))
    labels = []
    for i in pick:
        labels.append(
            f"步 {i + 1}/40 · K(R=0.001) {k_quiet[i]:.4f} · P {p_quiet[i]:.2e}"
            f" · K(R=0.020) {k_loud[i]:.4f}（示意）"
        )
    # 旁边一条平台 OCV，说明平的时候该靠近更小的 K。
    soc = np.linspace(0.2, 0.8, 40)
    volt = ocv_mean(soc, PLATEAU_ANCHOR_V)
    px0, px1, py_top, py_bot = 560.0, 760.0, 250.0, 390.0

    def px(s):
        return px0 + (np.asarray(s, dtype=float) - 0.2) / 0.6 * (px1 - px0)

    def py(v):
        return py_top + (3.34 - np.asarray(v, dtype=float)) / 0.08 * (py_bot - py_top)

    ocv_pts = list(zip(px(soc), py(volt), strict=True))
    sl = slope_v_per_unit(0.5, PLATEAU_ANCHOR_V) * 10.0
    body = f"""  <rect class="bg" width="800" height="560"/>
  <text class="title" x="24" y="32">增益 K = P / (P + R)，吵了自己变小（示意）</text>
  <rect class="panel" x="24" y="44" width="752" height="128" rx="6"/>
{steps([
    f"① 起步<tspan class=\"small\">　P 从 0.04 加 Q=0.0004。R=0.001 时第一步 K={k_quiet[0]:.4f}。</tspan>",
    "② 每一步<tspan class=\"small\">　先 P←P+Q，再 K=P/(P+R)，然后 P←(1−K)P。</tspan>",
    f"③ 测量较静<tspan class=\"small\">　蓝线收到 K={k_quiet[-1]:.4f}，P={p_quiet[-1]:.3e}。还愿意听电压。</tspan>",
    f"④ 测量更吵或平台<tspan class=\"small\">　R=0.020 收到 K={k_loud[-1]:.4f}。口诀：平台上少信电压。</tspan>",
], y0=68, dy=24)}
  <rect class="panel" x="24" y="184" width="752" height="250" rx="6"/>
  <text class="small" x="36" y="204">增益 K</text>
{axis_box(x0, y_top, x1, y_bot)}
  <text class="small" x="{x1:.1f}" y="436" text-anchor="end">更新步</text>
{xticks(x_of, y_bot, [(0, "1"), (9, "10"), (19, "20"), (39, "40")])}
{yticks(y_of, x0, [(0, "0"), (0.5, "0.5"), (1, "1")])}
{poly(quiet_pts, "lineb")}
{poly(loud_pts, "liner")}
{poly(bigq_pts, "lineg")}
{dot(framed, kt=kt)}
{dot(framed, cls="dotr", r=4, kt=kt, begin="-6s")}
  <text class="hi" x="120" y="204">蓝 R=0.001</text>
  <text class="warn" x="250" y="204">红 R=0.020</text>
  <text class="ok" x="390" y="204">绿 Q×4</text>
{axis_box(px0, py_top, px1, py_bot)}
{poly(ocv_pts, "lineg")}
  <text class="small" x="560" y="246">平台 OCV 示意</text>
  <text class="small" x="560" y="414">0.50 处 {sl:.2f} mV/1%</text>
  <rect class="panel" x="24" y="468" width="752" height="72" rx="6"/>
{fade_labels(labels, 40, 498, cls="small", kt=kt)}
  <text class="small" x="40" y="530">Q=0.0004、两档 R 是一维示意。绿线把 Q 提到 0.0016，末步 K={k_bigq[-1]:.3f}。不是 code/soc 里 EKF 的调参。</text>
"""
    return wrap(
        "标量卡尔曼增益：K=P/(P+R)。R 更大，平台更低；Q 更大，平台更高。游标读出 K 和 P。",
        "40 步递推。蓝线 R=0.001、红线 R=0.020，Q 都是 0.0004。绿线把 Q 提到 0.0016。底栏读出这一步的 K 和 P。示意，不是仓库 EKF 参数。",
        body,
        560,
        "formula: P=P+Q; K=P/(P+R); P=(1-K)*P; P0=0.04; Q in {0.0004, 0.0016}; R in {0.001, 0.020}",
    )


def build_ekf() -> str:
    sys.path.insert(0, str(SOC_DIR))
    import compare

    soc_true, soc_est = compare.run(seed=42)
    ekf = soc_est["Thevenin+EKF"]
    coul = soc_est["纯安时积分"]
    n = len(soc_true)
    rmse_ekf = float(np.sqrt(np.mean((ekf - soc_true) ** 2)))
    rmse_coul = float(np.sqrt(np.mean((coul - soc_true) ** 2)))
    hours = (np.arange(n) + 1) * compare.DT_S / 3600.0
    # 折线等距抽样。RMSE 仍用全部步数。
    idx = np.linspace(0, n - 1, 80, dtype=int)
    x0, x1 = 88.0, 760.0
    y_top, y_bot = 206.0, 348.0
    ymin, ymax = 0.20, 1.05

    def x_of(t):
        return x0 + (np.asarray(t, dtype=float) - 0.0) / float(hours[-1]) * (x1 - x0)

    def y_of(s):
        return y_top + (ymax - np.asarray(s, dtype=float)) / (ymax - ymin) * (y_bot - y_top)

    true_pts = list(zip(x_of(hours[idx]), y_of(soc_true[idx]), strict=True))
    ekf_pts = list(zip(x_of(hours[idx]), y_of(ekf[idx]), strict=True))
    coul_pts = list(zip(x_of(hours[idx]), y_of(coul[idx]), strict=True))
    pick = idx[::8]
    dot_pts = [(x_of(hours[i]), y_of(ekf[i])) for i in pick]
    framed = dot_pts + [dot_pts[-1]]
    kt = segment_times(len(pick))
    cursor = ";".join(f"{p[0]:.1f}" for p in framed)
    labels = []
    for i in pick:
        labels.append(
            f"t={hours[i]:.2f} h  真 {soc_true[i] * 100:.1f}%  "
            f"EKF {ekf[i] * 100:.1f}%  差 {(ekf[i] - soc_true[i]) * 100:+.2f} 个百分点"
        )
    ey_top, ey_bot = 455.0, 530.0
    emax = 0.8

    def ey(pp):
        return ey_top + (emax - float(pp)) / (2 * emax) * (ey_bot - ey_top)

    err_pts = [(x_of(hours[i]), ey((ekf[i] - soc_true[i]) * 100.0)) for i in idx]
    zero = [(x0, ey(0.0)), (x1, ey(0.0))]
    body = f"""  <rect class="bg" width="800" height="660"/>
  <text class="title" x="24" y="32">积分会漂，EKF 被电压拉回来</text>
  <text class="small" x="24" y="54">数据：code/soc/compare.py 仿真输出　种子 42　{n} 步 × 1 s　折线等距抽 {len(idx)} 点，RMSE 用全部步</text>
  <rect class="panel" x="24" y="66" width="752" height="100" rx="6"/>
{steps([
    f"① 纯安时<tspan class=\"small\">　整段 RMSE {rmse_coul:.4%}。零漂和容量估错会积着走，没有人拉它。</tspan>",
    f"② EKF<tspan class=\"small\">　整段 RMSE {rmse_ekf:.4%}。预测靠积分，修正靠电压残差。</tspan>",
    "③ 黄点沿蓝线走<tspan class=\"small\">　底栏读这一时刻的真值和误差。下面红线是全程误差。</tspan>",
    "④ 口诀<tspan class=\"small\">　积分往前走，电压负责把它拉回来。这是仿真，不是电芯考试。</tspan>",
], y0=88, dy=22)}
  <rect class="panel" x="24" y="176" width="752" height="240" rx="6"/>
  <text class="small" x="36" y="196">SOC</text>
{axis_box(x0, y_top, x1, y_bot)}
  <text class="small" x="{x1:.1f}" y="386" text-anchor="end">时间 h</text>
{xticks(x_of, y_bot, [(0, "0"), (1, "1"), (2, "2"), (3, "3"), (4, "4")])}
{yticks(y_of, x0, [(0.4, "0.4"), (0.6, "0.6"), (0.8, "0.8"), (1.0, "1.0")])}
{poly(coul_pts, "liney")}
{poly(true_pts, "linek")}
{poly(ekf_pts, "lineb")}
  <line class="liney" y1="{y_top:.1f}" y2="{y_bot:.1f}" x1="{framed[0][0]:.1f}" x2="{framed[0][0]:.1f}">
    <animate attributeName="x1" values="{cursor}" keyTimes="{kt}" dur="12s" repeatCount="indefinite"/>
    <animate attributeName="x2" values="{cursor}" keyTimes="{kt}" dur="12s" repeatCount="indefinite"/>
  </line>
{dot(framed, kt=kt)}
  <text class="gold" x="100" y="408">金：纯安时，充回去仍偏低</text>
  <text class="small" x="360" y="408">灰虚线：真值</text>
  <text class="hi" x="500" y="408">蓝：EKF，贴着真值</text>
  <rect class="panel" x="24" y="428" width="752" height="120" rx="6"/>
  <text class="small" x="110" y="446">EKF 减真值（百分点）　全程 RMSE {rmse_ekf:.4%}</text>
{axis_box(x0, ey_top, x1, ey_bot)}
{yticks(ey, x0, [(-0.8, "-0.8"), (0, "0"), (0.8, "0.8")])}
{poly(zero, "linek")}
{poly(err_pts, "liner")}
  <rect class="panel" x="24" y="558" width="752" height="52" rx="6"/>
{fade_labels(labels, 36, 590, cls="small", kt=kt)}
  <text class="small" x="24" y="640">工况同 compare.py：假定 9.5 Ah（模型 10）、初值 0.7（模型 0.8）、零漂 +2 mA。1 mA×24 h = 24 mAh 是另一笔示意账。</text>
"""
    return wrap(
        "EKF 与纯安时对照。曲线来自 code/soc/compare.py 的仿真输出，不是手绘折线。",
        "真值、Thevenin+EKF 和纯安时积分来自 compare.run(seed=42)。图上标了全程 RMSE，黄点沿 EKF 移动并读出该时刻误差。仿真结果，不是电芯实测。",
        body,
        660,
        "data: code/soc/compare.py run(seed=42); polyline is uniform downsample; RMSE uses every step",
    )


def build_second_order() -> str:
    """真实电芯两路 RC；一阶用合成电阻和更慢的 τ，前段跟不上。"""
    u0, current = 3.700, 20.0
    r0, r1, r2 = 0.002, 0.004, 0.006
    tau1, tau2, tau_1rc = 1.0, 30.0, 12.0
    t = np.linspace(0.0, 10.0, 81)

    def real(tt):
        tt = np.asarray(tt, dtype=float)
        return (
            u0
            - current * r0
            - current * r1 * (1.0 - np.exp(-tt / tau1))
            - current * r2 * (1.0 - np.exp(-tt / tau2))
        )

    def one(tt):
        tt = np.asarray(tt, dtype=float)
        return u0 - current * r0 - current * (r1 + r2) * (1.0 - np.exp(-tt / tau_1rc))

    x0, x1, y_top, y_bot = 88.0, 520.0, 228.0, 400.0
    vmin, vmax = 3.50, 3.72

    def x_of(tt):
        return x0 + np.asarray(tt, dtype=float) / 10.0 * (x1 - x0)

    def y_of(v):
        return y_top + (vmax - np.asarray(v, dtype=float)) / (vmax - vmin) * (y_bot - y_top)

    real_pts = list(zip(x_of(t), y_of(real(t)), strict=True))
    one_pts = list(zip(x_of(t), y_of(one(t)), strict=True))
    one_line = poly(one_pts, "liner").replace(
        "<polyline ",
        '<polyline stroke-dasharray="6 4" ',
        1,
    )
    stations = [0.0, 1.0, 2.0, 4.0, 8.0, 10.0]
    framed = [(float(x_of(s)), float(y_of(real(s)))) for s in stations]
    framed = framed + [framed[-1]]
    kt = segment_times(len(stations))
    labels = []
    for s in stations:
        gap_mv = (float(one(s)) - float(real(s))) * 1000.0
        labels.append(
            f"t={s:.0f} s　真实 {float(real(s)):.3f} V　一阶 {float(one(s)):.3f} V　"
            f"一阶偏高 {gap_mv:.0f} mV"
        )
    body = f"""  <rect class="bg" width="800" height="560"/>
  <text class="title" x="24" y="32">一阶贴不住前段，两路才分得开快慢（示意）</text>
  <rect class="panel" x="24" y="48" width="752" height="128" rx="6"/>
{steps([
    "① 阶跃<tspan class=\"small\">　20 A × 2 mΩ，端电压立刻少 40 mV。两张图这一下是一样的。</tspan>",
    "② 快路<tspan class=\"small\">　4 mΩ、τ=1 s。电荷转移，脉冲开头几秒就坐实。</tspan>",
    "③ 慢路<tspan class=\"small\">　6 mΩ、τ=30 s。浓差还在爬，10 s 里只走完一头。</tspan>",
    "④ 一阶<tspan class=\"small\">　把 10 mΩ 合成一条 τ=12 s。前段偏高，红虚线离开蓝线。</tspan>",
], y0=72, dy=26)}
  <rect class="panel" x="24" y="188" width="752" height="280" rx="6"/>
  <text class="small" x="40" y="210">端电压 V（示意）</text>
{axis_box(x0, y_top, x1, y_bot)}
  <text class="small" x="{x1:.1f}" y="444" text-anchor="end">时间 s</text>
{xticks(x_of, y_bot, [(0, "0"), (2, "2"), (4, "4"), (6, "6"), (8, "8"), (10, "10")])}
{yticks(y_of, x0, [(3.50, "3.50"), (3.60, "3.60"), (3.70, "3.70")])}
{one_line}
{poly(real_pts, "lineb")}
{dot(framed, cls="dotb", kt=kt)}
  <text class="hi" x="540" y="260">蓝 真实（两路）</text>
  <text class="warn" x="540" y="286">红虚线 一阶</text>
  <text class="small" x="540" y="312">前段对不上</text>
  <rect class="panel" x="24" y="480" width="752" height="64" rx="6"/>
{fade_labels(labels, 40, 518, cls="small", kt=kt)}
"""
    return wrap(
        "二阶 RC 与一阶对照。真实曲线是 R0 阶跃加两路指数，一阶用合成电阻和 τ=12 s。",
        "20 A、2 mΩ、快路 4 mΩ/1 s、慢路 6 mΩ/30 s 都是示意。蓝点沿真实曲线走，底栏读出一阶偏高多少毫伏。不是某一颗电芯的 HPPC。",
        body,
        560,
        "formula: U=3.700-20*(0.002+0.004*(1-e^{-t/1})+0.006*(1-e^{-t/30})); 1RC tau=12 s, R=0.010",
    )


def _soh_q(n):
    n = np.asarray(n, dtype=float)
    return 100.0 - 20.0 * (n / 3000.0) ** 1.5


def _soh_r(n):
    n = np.asarray(n, dtype=float)
    return 20.0 + 25.0 * (n / 3000.0) ** 0.45


def build_soh() -> str:
    n = np.linspace(0.0, 3000.0, 81)
    x0, x1, y_top, y_bot = 108.0, 680.0, 236.0, 400.0

    def x_of(cycles):
        return x0 + np.asarray(cycles, dtype=float) / 3000.0 * (x1 - x0)

    def yq(q):
        return y_top + (102.0 - np.asarray(q, dtype=float)) / (102.0 - 74.0) * (y_bot - y_top)

    def yr(r):
        return y_top + (52.0 - np.asarray(r, dtype=float)) / (52.0 - 16.0) * (y_bot - y_top)

    q_pts = list(zip(x_of(n), yq(_soh_q(n)), strict=True))
    r_pts = list(zip(x_of(n), yr(_soh_r(n)), strict=True))
    stations = [0.0, 600.0, 1500.0, 3000.0]
    framed = [(float(x_of(s)), float(yq(_soh_q(s)))) for s in stations]
    framed = framed + [framed[-1]]
    kt = segment_times(len(stations))
    labels = []
    for s in stations:
        labels.append(
            f"{s:.0f} 次　容量 {_soh_q(s):.1f}%　"
            f"{5.0 * _soh_q(s) / 100.0:.2f} Ah　R0 {_soh_r(s):.1f} mΩ"
        )
    body = f"""  <rect class="bg" width="800" height="560"/>
  <text class="title" x="24" y="32">容量还没到线，内阻先把功率收走（示意）</text>
  <rect class="panel" x="24" y="48" width="752" height="128" rx="6"/>
{steps([
    "① 容量<tspan class=\"small\">　Q% = 100 − 20·(n/3000)^1.5。3000 次正好到 80%。</tspan>",
    "② 内阻<tspan class=\"small\">　R0 = 20 + 25·(n/3000)^0.45，单位 mΩ。起步就抬头。</tspan>",
    "③ 大约 600 次<tspan class=\"small\">　容量仍在 98% 附近，R0 已经到 32 mΩ 上下。读数在底栏。</tspan>",
    "④ 口诀<tspan class=\"small\">　先看功率。80% 只是容量那条惯用线，不是功率还在的证明。</tspan>",
], y0=72, dy=26)}
  <rect class="panel" x="24" y="188" width="752" height="280" rx="6"/>
  <text class="hi" x="40" y="212">蓝 容量 %（左）</text>
  <text class="warn" x="220" y="212">红 内阻 mΩ（右）</text>
  <text class="gold" x="460" y="212">金虚线 80%</text>
{axis_box(x0, y_top, x1, y_bot)}
  <text class="small" x="{x1:.1f}" y="444" text-anchor="end">循环数</text>
{xticks(x_of, y_bot, [(0, "0"), (600, "600"), (1500, "1500"), (3000, "3000")])}
{yticks(yq, x0, [(80, "80"), (90, "90"), (100, "100")])}
{yticks(yr, x1 + 56, [(20, "20"), (32, "32"), (45, "45")])}
  <line class="liney" x1="{x0:.1f}" y1="{yq(80):.1f}" x2="{x1:.1f}" y2="{yq(80):.1f}" stroke-dasharray="6 4"/>
{poly(q_pts, "lineb")}
{poly(r_pts, "liner")}
{dot(framed, cls="dotb", kt=kt)}
  <rect class="panel" x="24" y="480" width="752" height="64" rx="6"/>
{fade_labels(labels, 40, 518, cls="small", kt=kt)}
"""
    return wrap(
        "SOH 双指标示意。容量按 (n/3000)^1.5 收到 80%，内阻按 (n/3000)^0.45 从 20 mΩ 收到 45 mΩ。",
        "新电池按 5.0 Ah、20 mΩ 起算。蓝点沿容量走，底栏同时读出这一圈的安时和内阻。不是某一批循环实验。",
        body,
        560,
        "formula: Q%=100-20*(n/3000)^1.5; R_mOhm=20+25*(n/3000)^0.45; Ah=5.0*Q%/100",
    )


def build_waterfall() -> str:
    parts = (
        ("基准温漂", 2.0),
        ("ADC 失调", 1.5),
        ("RC 漏电", 0.8),
        ("电荷注入", 0.3),
        ("布局拾取", 0.9),
    )
    y_top, y_bot = 228.0, 392.0
    vmax = 6.5

    def y_of(mv: float) -> float:
        return y_bot - mv / vmax * (y_bot - y_top)

    bars = []
    running = 0.0
    x = 72.0
    width = 70.0
    gap = 18.0
    for i, (name, delta) in enumerate(parts):
        y = y_of(running + delta)
        h = y_of(running) - y
        appear = (i + 1) / 6
        op = (
            f'<animate attributeName="opacity" values="0;0;1;1" '
            f'keyTimes="0;{appear - 0.04:.2f};{appear:.2f};1" dur="12s" repeatCount="indefinite"/>'
        )
        bars.append(
            f'  <rect class="boxb" x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{h:.1f}">{op}</rect>'
        )
        bars.append(
            f'  <text class="txt" x="{x + width / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" opacity="0">'
            f"+{delta:.1f}{op}</text>"
        )
        bars.append(
            f'  <text class="small" x="{x + width / 2:.1f}" y="412" text-anchor="middle">{name}</text>'
        )
        if i < len(parts) - 1:
            y_join = y_of(running + delta)
            x2 = x + width + gap
            bars.append(
                f'  <line class="axis" x1="{x + width:.1f}" y1="{y_join:.1f}" x2="{x2:.1f}" y2="{y_join:.1f}" opacity="0">{op}</line>'
            )
        running += delta
        x += width + gap
    budget_y = y_of(5.0)
    body = f"""  <rect class="bg" width="800" height="520"/>
  <text class="title" x="24" y="32">误差是一截一截垒上去的（示意）</text>
  <rect class="panel" x="24" y="48" width="752" height="104" rx="6"/>
{steps([
    "① 每一截只记自己的增量<tspan class=\"small\">　柱子从前一截的终点接着画，不从零重来。</tspan>",
    "② 五截加完是 5.5 mV<tspan class=\"small\">　预算线画在 ±5 mV。未标定就探出线外。</tspan>",
    "③ 标定能消掉系统性的那几项<tspan class=\"small\">　剩下大约 1.8 mV，回到线下面。</tspan>",
    "④ 口诀<tspan class=\"small\">　先加总，再看哪一截探出预算。数字是教学累加。</tspan>",
], y0=70, dy=22)}
  <rect class="panel" x="24" y="164" width="500" height="268" rx="6"/>
  <text class="small" x="40" y="186">累计 mV（示意）</text>
  <line class="axis" x1="64" y1="210" x2="64" y2="392"/>
  <line class="axis" x1="64" y1="392" x2="500" y2="392"/>
  <line class="liney" x1="64" y1="{budget_y:.1f}" x2="490" y2="{budget_y:.1f}" stroke-dasharray="6 4"/>
  <text class="gold" x="72" y="{budget_y - 8:.1f}">预算 ±5</text>
{chr(10).join(bars)}
  <rect class="panel" x="536" y="164" width="240" height="268" rx="6"/>
  <text class="txt" x="552" y="196">未标定累加</text>
  <text class="warn" x="552" y="228">{running:.1f} mV</text>
  <text class="small" x="552" y="256">预算线是 ±5 mV</text>
  <text class="small" x="552" y="280">探出 {running - 5:.1f} mV</text>
  <text class="txt" x="552" y="320">标定之后</text>
  <text class="ok" x="552" y="352">约 1.8 mV</text>
  <text class="small" x="552" y="380">系统性的项被系数修掉</text>
  <text class="small" x="24" y="468">2.0、1.5、0.8、0.3、0.9 和标定后的 1.8，都是这张图的示意账，不是某一块采样板的校准记录。</text>
  <text class="small" x="24" y="496">柱内不再放白字。增量写在柱顶，结论写在右边的卡片里。</text>
"""
    return wrap(
        "采样链误差瀑布。每一截从前一截的终点往上垒，五截合计 5.5 mV，探出 ±5 mV 预算。",
        "增量依次是基准温漂 2.0、ADC 1.5、RC 漏电 0.8、电荷注入 0.3、布局拾取 0.9，单位 mV。标定后剩余约 1.8 mV。示意累加，不是实测。",
        body,
        520,
        "formula: cumulative sum of 2.0+1.5+0.8+0.3+0.9 = 5.5 mV; budget line at 5 mV",
    )


def main() -> None:
    import sys

    # --out DIR：写到指定目录，供「生成图对账」门生成到临时目录做逐字节比对，
    # 不碰 assets、也不依赖 git 暂存状态。缺省仍直接覆盖 ASSETS。
    out_dir = ASSETS
    if "--out" in sys.argv:
        out_dir = Path(sys.argv[sys.argv.index("--out") + 1])
        out_dir.mkdir(parents=True, exist_ok=True)

    from batch3_scenes import BUILDERS as batch3

    builders = {
        "ocv-hysteresis.svg": build_hysteresis,
        "ocv-plateau-distrust.svg": build_plateau,
        "sop-derating.svg": build_sop,
        "kalman-gain.svg": build_kalman,
        "ekf-estimation.svg": build_ekf,
        "second-order-rc.svg": build_second_order,
        "soh-aging.svg": build_soh,
        "error-budget-waterfall.svg": build_waterfall,
    }
    builders.update(batch3)
    for name, builder in builders.items():
        text = builder()
        path = out_dir / name
        # 显式 LF：.gitattributes 统一 LF，Windows 上默认文本模式会写成 CRLF，
        # 再生成就会在 diff 里冒出整文件换行差异
        path.write_text(text, encoding="utf-8", newline="\n")
        size = path.stat().st_size
        flag = "OK" if size <= MAX_BYTES else "OVER"
        print(f"{flag} {name} {size} bytes")
        if size > MAX_BYTES:
            raise SystemExit(f"{name} 超过 {MAX_BYTES} 字节")


if __name__ == "__main__":
    main()
