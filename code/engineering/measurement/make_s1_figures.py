#!/usr/bin/env python3
"""Generate S1 measurement figures from the frozen reference implementation.

F1 is a hand-authored mechanism path (sensor -> calibration -> sampling ->
protection feedback). F2-F4 are data/timing plots whose numbers are read from
``s1_measurement.py`` at generation time, so figures cannot drift from the report.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

import s1_measurement as s1

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "bms-book" / "engineering" / "assets" / "s1-measurement"

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


def f1_path() -> str:
    parts = [
        text(24, 32, "S1-F1　一个读数要过的四站，以及它怎样变成动作", "title"),
        text(24, 58, "蓝线是电信号与连接；虚线是数字数据或反馈。校准只修正固定偏差，滤波与确认负责噪声与误动作。", "sub"),
    ]
    # Sensor front end: divider + RC + mux.
    parts += [
        '<circle class="wire" cx="70" cy="250" r="26"/>',
        text(70, 246, "+", "sym", "middle"),
        text(70, 268, "−", "sym", "middle"),
        '<line class="wire" x1="70" y1="224" x2="70" y2="180"/>',
        '<line class="wire" x1="70" y1="276" x2="70" y2="360"/>',
        '<line class="wire" x1="70" y1="180" x2="150" y2="180"/>',
        '<rect class="box" x="150" y="162" width="52" height="36"/>',
        text(176, 148, "分压", "small", "middle"),
        '<line class="wire" x1="202" y1="180" x2="260" y2="180"/>',
        '<rect class="box" x="260" y="162" width="52" height="36"/>',
        text(286, 148, "RC", "small", "middle"),
        '<line class="wire" x1="312" y1="180" x2="368" y2="180"/>',
        '<rect class="box" x="368" y="158" width="92" height="44"/>',
        text(414, 176, "多路开关", "small", "middle"),
        text(414, 194, "16 串", "small", "middle"),
        '<line class="wire" x1="460" y1="180" x2="516" y2="180"/>',
        '<rect class="box" x="516" y="158" width="88" height="44"/>',
        text(560, 176, "ADC / AFE", "small", "middle"),
        text(560, 194, "基准 + 标定", "small", "middle"),
        # Digital chain.
        '<line class="dash" x1="604" y1="180" x2="660" y2="180"/>',
        '<polygon class="node" points="660,180 650,174 650,186"/>',
        '<rect class="box" x="660" y="150" width="112" height="60"/>',
        text(716, 172, "滤波 + 确认", "small", "middle"),
        text(716, 196, "N 拍", "small", "middle"),
        '<line class="dash" x1="716" y1="210" x2="716" y2="270"/>',
        '<polygon class="node" points="716,270 710,260 722,260"/>',
        '<rect class="box" x="640" y="270" width="152" height="60"/>',
        text(716, 292, "判决与执行", "small", "middle"),
        text(716, 316, "接触器 / MOS", "small", "middle"),
        '<line class="dash" x1="640" y1="300" x2="560" y2="300"/>',
        '<polygon class="node" points="560,300 570,294 570,306"/>',
        text(500, 326, "独立反馈回到证据链", "small", "middle"),
        # Calibration annotation.
        '<line class="dash" x1="560" y1="132" x2="560" y2="158"/>',
        text(560, 120, "单点校准：只修一个已知点的固定偏差", "small", "middle"),
        # Return path.
        '<line class="wire" x1="716" y1="330" x2="716" y2="360"/>',
        '<line class="wire" x1="716" y1="360" x2="70" y2="360"/>',
        '<polygon class="node" points="200,360 210,354 210,366"/>',
        text(200, 386, "回流与参考点必须明确", "small", "middle"),
        text(24, 430, "四站：被测对象 → 传感与调理 → 转换与标定 → 数据质量与时刻；任何一站缺证据，后面的数字都不合格。", "small"),
        text(24, 454, "图为机制示意，参数取 S1-sense-chain；不是实物接线图，也不是高压搭建指导。", "small"),
    ]
    return svg(
        800, 476,
        "S1 测量链的四站与反馈路径",
        "电芯正负端经分压与RC进入多路开关和AFE，数字量经滤波与连续确认后判决执行，独立反馈回到证据链；回流与参考点单独标出。",
        "\n".join(parts),
    )


def f2_error_budget() -> str:
    cfg = s1.ChainConfig()
    worst = s1.worst_case_mv(cfg.rss_limit_mv)
    rss = s1.rss_mv(cfg.rss_limit_mv)
    parts = [
        text(24, 32, "S1-F2　四条误差上限、两种合成方式与相关系数", "title"),
        text(24, 58, "四个误差源取幅值上限；同向叠加是绝对界，平方和开根只是特定假设下的典型值。", "sub"),
    ]
    # Left: individual bars + totals.
    sx, sy = axis(0, 5, 0, 5, 92, 372, 96, 330)
    for mv in range(0, 6):
        parts.append(f'<line class="grid" x1="92" y1="{sy(mv):.1f}" x2="372" y2="{sy(mv):.1f}"/>')
        parts.append(text(84, sy(mv) + 4, str(mv), "small", "end"))
    labels = ["源 1", "源 2", "源 3", "源 4"]
    for index, (label, value) in enumerate(zip(labels, cfg.rss_limit_mv, strict=True)):
        y = 116 + index * 40
        parts.append(f'<rect class="bar-cmp" x="92" y="{y}" width="{value / 5 * 280:.1f}" height="18"/>')
        parts.append(text(100, y + 14, label, "small"))
        parts.append(text(92 + value / 5 * 280 + 8, y + 14, f"{value:g} mV", "small"))
    parts.append(f'<line class="warn" x1="{sx(worst):.1f}" y1="96" x2="{sx(worst):.1f}" y2="330"/>')
    parts.append(text(sx(worst) - 4, 92, f"最坏 {worst:g} mV", "small", "end"))
    parts.append(f'<line class="good" x1="{sx(rss):.1f}" y1="96" x2="{sx(rss):.1f}" y2="330"/>')
    parts.append(text(sx(rss) + 4, 92, f"RSS {rss:.5g} mV", "small"))
    parts.append(text(232, 356, "误差源上限 / mV", "lbl", "middle"))
    parts.append('<line class="axis" x1="92" y1="330" x2="372" y2="330"/>')

    # Right: sigma of a sum vs correlation.
    sx, sy = axis(0, 1, 0.9, 1.5, 470, 760, 96, 330)
    for rho in (0, 0.25, 0.5, 0.75, 1.0):
        parts.append(f'<line class="grid" x1="{sx(rho):.1f}" y1="96" x2="{sx(rho):.1f}" y2="330"/>')
        parts.append(text(sx(rho), 348, f"{rho:g}", "small", "middle"))
    for sigma in (1.0, 1.1, 1.2, 1.3, 1.4):
        parts.append(f'<line class="grid" x1="470" y1="{sy(sigma):.1f}" x2="760" y2="{sy(sigma):.1f}"/>')
        parts.append(text(462, sy(sigma) + 4, f"{sigma:.1f}", "small", "end"))
    points = []
    for step in range(0, 101):
        rho = step / 100
        points.append((sx(rho), sy(s1.correlated_sigma_mv(*cfg.sigma_mv, rho))))
    parts.append(polyline(points, "cmp"))
    for rho in (0.0, 0.75, 1.0):
        sigma = s1.correlated_sigma_mv(*cfg.sigma_mv, rho)
        parts.append(f'<circle class="node" cx="{sx(rho):.1f}" cy="{sy(sigma):.1f}" r="4"/>')
        parts.append(text(sx(rho) + 8, sy(sigma) - 6, f"{sigma:.4g}", "small", halo=True))
    parts.append(text(615, 372, "相关系数 ρ", "lbl", "middle"))
    parts.append(text(470, 84, "合成标准差 / mV", "lbl"))
    parts.append(text(24, 402, "ρ=1 时两项完全同向，标准差是 1.4 mV；ρ=0.75 时 1.3115 mV。把最坏界当标准差，或反过来，都会误导预算。", "small"))
    return svg(
        800, 420,
        "S1 误差上限、合成方式与相关系数",
        "左图四个误差源上限为2、1.2、0.8、0.5毫伏，同向最坏4.5毫伏，平方和开根2.51595毫伏；右图两个0.6与0.8毫伏噪声随相关系数0到1合成1.0到1.4毫伏。",
        "\n".join(parts),
    )


def f3_settling_scan() -> str:
    cfg = s1.ChainConfig()
    settle = s1.settling_time_s(cfg.tau_s, cfg.settle_ratio)
    scan = s1.sequential_scan_s(cfg)
    parts = [
        text(24, 32, "S1-F3　建立到 1 mV 要多久，16 串还装得下 10 ms 吗", "title"),
        text(24, 58, "左图为一阶建立残差；右图为同一建立时间乘以 16 串，另加每串 20 µs 转换开销。", "sub"),
    ]
    # Left: residual vs time (ms), log-ish visual via linear 0..10 mV.
    sx, sy = axis(0, 1.2, 0, 10, 92, 392, 96, 330)
    for ms in (0, 0.3, 0.6, 0.9, 1.2):
        parts.append(f'<line class="grid" x1="{sx(ms):.1f}" y1="96" x2="{sx(ms):.1f}" y2="330"/>')
        parts.append(text(sx(ms), 348, f"{ms:g}", "small", "middle"))
    for mv in (0, 2, 4, 6, 8, 10):
        parts.append(f'<line class="grid" x1="92" y1="{sy(mv):.1f}" x2="392" y2="{sy(mv):.1f}"/>')
        parts.append(text(84, sy(mv) + 4, str(mv), "small", "end"))
    points = []
    for step in range(0, 61):
        t_ms = step / 50.0
        residual_mv = s1.settling_residual_v(cfg.settle_step_v, cfg.tau_s, t_ms / 1000.0) * 1000
        points.append((sx(t_ms), sy(min(residual_mv, 10.0))))
    parts.append(polyline(points, "good"))
    parts.append(f'<line class="warn" x1="{sx(settle * 1000):.1f}" y1="96" x2="{sx(settle * 1000):.1f}" y2="330"/>')
    parts.append(f'<circle class="node" cx="{sx(settle * 1000):.1f}" cy="{sy(1.0):.1f}" r="4"/>')
    parts.append(text(sx(settle * 1000) + 8, 250, f"{settle * 1e6:.2f} µs", "small", halo=True))
    parts.append(text(242, 372, "时间 / ms", "lbl", "middle"))
    parts.append(text(92, 84, "残差 / mV", "lbl"))
    # Right: scan budget bar.
    parts.append(text(452, 84, "16 串顺序扫描", "lbl"))
    parts.append('<rect class="bar-warn" x="452" y="110" width="300" height="34"/>')
    width = min(scan["total_s"] / 0.012 * 300, 300)
    parts.append(f'<rect class="bar-good" x="452" y="110" width="{width:.1f}" height="34"/>')
    parts.append(f'<line class="warn" x1="{452 + 10e-3 / 0.012 * 300:.1f}" y1="98" x2="{452 + 10e-3 / 0.012 * 300:.1f}" y2="156"/>')
    parts.append(text(452 + 10e-3 / 0.012 * 300 - 4, 94, "10 ms 任务", "small", "end"))
    parts.append(text(458, 132, f"{scan['total_s'] * 1000:.4g} ms", "value"))
    parts.append(text(452, 190, f"每串：建立 {settle * 1e6:.2f} µs + 开销 20 µs", "small"))
    parts.append(text(452, 214, f"总余量 {scan['total_margin_s'] * 1000:+.4g} ms（相对 10 ms）", "small"))
    parts.append(text(452, 238, f"相对 20 ms 周期仍余 {scan['sample_period_margin_s'] * 1000:.4g} ms", "small"))
    parts.append(text(452, 286, "结论只覆盖理想顺序扫描；AFE 内部并行、过采样与其他任务未计入。", "small"))
    parts.append(text(24, 404, "5τ = 500 µs 时残差仍有 3.369 mV，不满足 1 mV；621.46 µs 才是本模型下的下限。", "small"))
    return svg(
        800, 420,
        "S1 建立时间与 16 串扫描时序",
        "左图一阶建立残差在621.46微秒降到1毫伏，5τ仍剩3.369毫伏；右图16串共10.26337毫秒，超过10毫秒任务但小于20毫秒周期。",
        "\n".join(parts),
    )


def f4_filter_budget() -> str:
    cfg = s1.ChainConfig()
    budget = s1.feedback_budget_s(cfg)
    parts = [
        text(24, 32, "S1-F4　N=1/5/9 的因果窗与完整反馈时间", "title"),
        text(24, 58, "左图为 4.1→4.3 V 阶跃经因果滑动平均后的首达阈值；右图为物理故障到安全反馈的最坏预算。", "sub"),
    ]
    sx, sy = axis(0, 30, 4.08, 4.32, 92, 420, 96, 320)
    for tick in (0, 5, 10, 15, 20, 25, 30):
        parts.append(f'<line class="grid" x1="{sx(tick):.1f}" y1="96" x2="{sx(tick):.1f}" y2="320"/>')
        parts.append(text(sx(tick), 338, str(tick), "small", "middle"))
    for volt in (4.1, 4.2, 4.3):
        parts.append(f'<line class="grid" x1="92" y1="{sy(volt):.1f}" x2="420" y2="{sy(volt):.1f}"/>')
        parts.append(text(84, sy(volt) + 4, f"{volt:.1f}", "small", "end"))
    parts.append(f'<line class="warn" x1="92" y1="{sy(cfg.threshold_v):.1f}" x2="420" y2="{sy(cfg.threshold_v):.1f}"/>')
    parts.append(text(420, sy(cfg.threshold_v) - 5, "阈值 4.2 V", "small", "end"))
    samples = [4.1] * 12 + [4.3] * 30
    for window, cls in ((1, "good"), (5, "cmp"), (9, "warn")):
        filtered = s1.moving_average(samples, window)
        points = []
        for index, value in enumerate(filtered):
            if value is None:
                continue
            points.append((sx(index), sy(value)))
        parts.append(polyline(points, cls))
    parts.append(text(92, 84, "滤波输出 / V", "lbl"))
    parts.append(text(256, 362, "采样序号（Ts = 20 ms）", "lbl", "middle"))
    parts.append(text(100, 286, "N=1", "small", halo=True))
    parts.append(text(100, 270, "N=5", "small", halo=True))
    parts.append(text(100, 254, "N=9", "small", halo=True))
    # Right: budget bars.
    parts.append(text(470, 84, "物理故障 → 安全反馈 / ms", "lbl"))
    base = 470
    for index, (window, row) in enumerate(budget["windows"].items()):
        y = 108 + index * 66
        width = row["total_s"] * 1000 / 180 * 280
        cls = "bar-good" if row["within_fti"] else "bar-warn"
        parts.append(f'<rect class="{cls}" x="{base}" y="{y}" width="{width:.1f}" height="30"/>')
        parts.append(text(base + 6, y + 21, f"N={window}", "lbl"))
        parts.append(text(base + width + 8, y + 21, f"{row['total_s'] * 1000:g} ms", "value"))
    parts.append(f'<line class="warn" x1="{base + 100 / 180 * 280:.1f}" y1="96" x2="{base + 100 / 180 * 280:.1f}" y2="306"/>')
    parts.append(text(base + 100 / 180 * 280 - 4, 92, "100 ms", "small", "end"))
    parts.append(text(470, 336, "20 + 滤波 + 40（确认）+ 2 + 15 ms", "small"))
    parts.append(text(24, 396, "群延迟是因果窗的一半左右，不是整窗长度；确认另加 (N−1)·Ts，不能混成一个数。", "small"))
    return svg(
        800, 412,
        "S1 滤波窗与完整反馈预算",
        "左图N=1、5、9的因果滑动平均首达4.2伏分别为第12、14、16个样本；右图含首拍20毫秒、确认40毫秒、判决2毫秒、反馈15毫秒的总时为77、117、157毫秒。",
        "\n".join(parts),
    )


def build_targets() -> dict[str, str]:
    return {
        "S1-F1-sense-chain.svg": f1_path(),
        "S1-F2-error-budget.svg": f2_error_budget(),
        "S1-F3-settling-scan.svg": f3_settling_scan(),
        "S1-F4-filter-budget.svg": f4_filter_budget(),
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
