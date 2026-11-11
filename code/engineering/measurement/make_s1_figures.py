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
        text(20, 34, "S1-F1　从读数到动作", "f1-title"),
        text(20, 66, "功能路径，不是板级接线图", "f1-note"),
        text(24, 108, "① 模拟采样：对象与参考", "f1-label"),
        '<rect class="box" x="24" y="136" width="352" height="52"/>',
        text(200, 168, "电芯：正 / 负测量端与参考", "f1-label", "middle"),
        '<line class="wire" x1="200" y1="188" x2="200" y2="220"/>',
        '<polygon class="node" points="200,220 194,210 206,210"/>',
        '<rect class="box" x="24" y="220" width="352" height="64"/>',
        text(200, 247, "分压 / RC / 多路开关", "f1-label", "middle"),
        text(200, 272, "16 串通道，逐通道建立", "f1-note", "middle"),
        '<line class="wire" x1="200" y1="284" x2="200" y2="316"/>',
        '<polygon class="node" points="200,316 194,306 206,306"/>',
        '<rect class="box" x="24" y="316" width="352" height="64"/>',
        text(200, 343, "AFE（模拟前端）/ ADC", "f1-label", "middle"),
        text(200, 368, "基准、转换与原始输出", "f1-note", "middle"),
        text(24, 416, "实线：模拟信号方向（含参考）", "f1-note"),
        text(24, 448, "原始数字输出进入下一段 ↓", "f1-note"),
        text(24, 496, "② 数字保护：先校准，再判决", "f1-label"),
        '<rect class="box" x="24" y="520" width="352" height="64"/>',
        text(200, 547, "单点标定：修已知点的偏移", "f1-label", "middle"),
        text(200, 572, "不消除增益、温漂和动态项", "f1-note", "middle"),
        '<line class="dash" x1="200" y1="584" x2="200" y2="620"/>',
        '<polygon class="node" points="200,620 194,610 206,610"/>',
        '<rect class="box" x="24" y="620" width="352" height="64"/>',
        text(200, 647, "因果滤波 → 连续确认", "f1-label", "middle"),
        text(200, 672, "保留样本时刻与有效性", "f1-note", "middle"),
        '<line class="dash" x1="200" y1="684" x2="200" y2="724"/>',
        '<polygon class="node" points="200,724 194,714 206,714"/>',
        '<rect class="box" x="24" y="724" width="352" height="52"/>',
        text(200, 756, "判决：发出保护命令", "f1-label", "middle"),
        text(24, 812, "保护命令进入下一段 ↓", "f1-note"),
        text(24, 860, "③ 执行与反馈：命令不等于动作", "f1-label"),
        '<rect class="box" x="24" y="884" width="352" height="56"/>',
        text(200, 918, "驱动 → MOS / 接触器", "f1-label", "middle"),
        '<line class="dash" x1="200" y1="940" x2="200" y2="976"/>',
        '<polygon class="node" points="200,976 194,966 206,966"/>',
        '<rect class="box" x="24" y="976" width="352" height="64"/>',
        text(200, 1003, "独立观测：触点 / 实际电流", "f1-label", "middle"),
        text(200, 1028, "与命令对照，记录超时或不一致", "f1-note", "middle"),
        '<path class="dash" d="M376 1008 H388 V750 H376"/>',
        '<polygon class="node" points="376,750 386,744 386,756"/>',
        text(24, 1080, "虚线：数据、命令或反馈，不是导线", "f1-note"),
        text(24, 1112, "每段分别记录误差、时刻与失败证据", "f1-note"),
        text(24, 1144, "教学功能示意；不是高压搭建指导", "f1-note"),
    ]
    f1_style = STYLE.replace("</style>", """
  .f1-title { fill: #003153; font: 700 22px 'Microsoft YaHei',sans-serif; }
  .f1-label { fill: #003153; font: 700 18px 'Microsoft YaHei',sans-serif; }
  .f1-note { fill: #4d5a5f; font: 16px 'Microsoft YaHei',sans-serif; }
</style>""")
    return svg(
        400, 1172,
        "S1 模拟采样、数字保护与独立反馈的功能路径",
        "竖排三段区分模拟信号、数字处理和执行反馈；模拟端必须有参考，"
        "反馈与命令独立记录。箭头表示功能信号方向，不表示实际导线或电流回路。",
        "\n".join(parts),
    ).replace(STYLE, f1_style, 1)

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
        text(24, 32, "S1-F4　N=1/5/9 的因果窗与条件反馈预算", "title"),
        text(24, 58, "左：因果平均首达阈值；右：给定首个高输出等待≤20 ms后的教学预算，不是实测整链上界。", "sub"),
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
    parts.append(text(470, 84, "条件反馈预算 / ms", "lbl"))
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
    parts.append(text(24, 396, "群延迟不是通用检出延迟；本例连续3拍另加2个Ts，首个高输出等待另列。", "small"))
    return svg(
        800, 412,
        "S1 滤波窗与条件反馈预算",
        "左图N=1、5、9的因果滑动平均首达4.2伏分别为第12、14、16个样本；右图在首个高输出等待不超过20毫秒的假设下，含确认40毫秒、判决2毫秒、执行反馈15毫秒，总时为77、117、157毫秒，不证明实际AFE整链上界。",
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
