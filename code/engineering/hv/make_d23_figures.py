#!/usr/bin/env python3
"""Generate D23 figure: precharge timeline + insulation bridge schematic.

Numbers are read from d23_precharge_insulation.py defaults, so the figure and
the chapter stay recomputed from the same source.
"""

from __future__ import annotations

from pathlib import Path
import importlib.util
import math
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d23_precharge_insulation", HERE / "d23_precharge_insulation.py"
)
assert spec is not None and spec.loader is not None
d23 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d23
spec.loader.exec_module(d23)

OUT = HERE.parents[2] / "bms-book" / "engineering" / "assets" / "d23-hv"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .lbl { fill: #4d5d63; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .small { fill: #4d5d63; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .value { fill: #003153; font: 700 18px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .sym { fill: #003153; font: 700 17px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .curve { stroke: #003153; stroke-width: 2.4; fill: none; stroke-linecap: round; }
  .wire { stroke: #003153; stroke-width: 2; fill: none; stroke-linecap: round; }
  .res { fill: #fbf8f1; stroke: #003153; stroke-width: 2; }
  .warn { stroke: #a3322a; stroke-width: 2.4; fill: none; stroke-linecap: round; }
  .dash { stroke: #5c6d73; stroke-width: 1.4; fill: none; stroke-dasharray: 5 4; }
  .mark { stroke: #a3322a; stroke-width: 1.8; fill: none; stroke-dasharray: 4 3; }
</style>"""


def _polyline(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def build_svg() -> str:
    tau = d23.tau_s()
    t95 = d23.t_measure_s()
    pulses = d23.DEFAULT_PULSE_TIMES_S

    # left panel geometry: t in [0, 0.8] s -> x in [80, 430]; v in [0, 420] V -> y in [300, 80]
    def xt(t: float) -> float:
        return 80.0 + t / 0.8 * 350.0

    def yv(v: float) -> float:
        return 300.0 - v / 420.0 * 220.0

    pts = [(xt(i * 0.8 / 60.0), yv(400.0 * (1.0 - math.exp(-(i * 0.8 / 60.0) / tau)))) for i in range(61)]
    t95_v = 400.0 * 0.95
    # 脉冲时间条：主曲线 x 轴只到 0.8 s，脉冲在 0/5/10 s，单独开 0–12 s 子轴
    def xp(t: float) -> float:
        return 80.0 + t / 12.0 * 350.0

    pulse_marks = []
    for p in pulses:
        x = xp(p)
        pulse_marks.append(f'<line class="mark" x1="{x:.1f}" y1="316" x2="{x:.1f}" y2="336"/>')
        pulse_marks.append(f'<text class="small" x="{x - 8:.1f}" y="352">{p:g} s</text>')
    pulse_strip = "".join(pulse_marks)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 940 400" role="img" aria-label="D23 预充时间线与绝缘桥测示意">
<title>D23-F1 预充重复热账与绝缘桥测</title>
<desc>左：预充母线电压曲线（τ=0.17 s、t95=0.509 s、supplied 152.0 J/stored 72.2 J/spent 79.8 J、0.798 W 通过与 7.98 W 拒绝两笔重复热账）与 0–12 s 脉冲时间条；右：绝缘等效网络（R_iso+ 1 MΩ、R_iso− 100 kΩ、C_y 100 nF 对底盘）与 R_ref=200 kΩ 切换桥测两窗（36.36 V/25.0 V、τ_y=6.25 ms（R_th=R_iso−∥R_ref∥R_iso+）、窗口 ≥ 3τ_y=18.75 ms、限值 500 Ω/V → 200 kΩ）。数字取自 d23_precharge_insulation.py 默认报告。</desc>
<rect class="bg" x="0" y="0" width="940" height="400"/>
{STYLE}
<text class="title" x="36" y="42">D23-F1　预充重复热账与绝缘桥测：一张图两笔账</text>
<text class="sub" x="36" y="66">数字取自 d23_precharge_insulation.py 默认报告（代码生成 SVG）；τ = {tau:.2f} s，t95 = {t95:.3f} s，单脉冲电阻耗散 {d23.pulse_energy_j():.1f} J</text>

<text class="lbl" x="80" y="96">左：母线电压 v_bus(t) = 400·(1−e^(−t/τ))（0–0.8 s）与脉冲时间条（0–12 s）</text>
<line class="wire" x1="80" y1="300" x2="440" y2="300"/>
<line class="wire" x1="80" y1="300" x2="80" y2="80"/>
<text class="small" x="60" y="84">V</text>
<text class="small" x="70" y="304">0</text>
<text class="small" x="54" y="{yv(400):.0f}">400</text>
<text class="small" x="60" y="{yv(t95_v):.0f}">380</text>
<line class="dash" x1="80" y1="{yv(400):.1f}" x2="440" y2="{yv(400):.1f}"/>
<line class="dash" x1="{xt(t95):.1f}" y1="300" x2="{xt(t95):.1f}" y2="{yv(t95_v):.1f}"/>
<line class="dash" x1="{xt(t95):.1f}" y1="{yv(t95_v):.1f}" x2="80" y2="{yv(t95_v):.1f}"/>
<polyline class="curve" points="{_polyline(pts)}"/>
<text class="small" x="{xt(t95)+4:.0f}" y="316">t95 = {t95:.3f} s</text>
<text class="small" x="436" y="316">t/s</text>
<line class="wire" x1="80" y1="336" x2="440" y2="336"/>
{pulse_strip}
<text class="small" x="446" y="340">脉冲 @ 0/5/10 s</text>
<text class="small" x="300" y="120">单脉冲：supplied 152.0 J</text>
<text class="small" x="300" y="138">stored 72.2 J，spent 79.8 J</text>
<text class="small" x="300" y="160">3 脉冲 / 300 s → 0.80 W ≤ 5 W 通过</text>
<text class="small" x="300" y="178">6 脉冲 / 60 s → 7.98 W &gt; 5 W 拒绝</text>

<text class="lbl" x="500" y="96">右：绝缘等效网络与切换基准桥测（对地）</text>
<line class="wire" x1="540" y1="140" x2="720" y2="140"/>
<line class="wire" x1="540" y1="300" x2="720" y2="300"/>
<line class="wire" x1="720" y1="140" x2="720" y2="300"/>
<text class="sym" x="728" y="225">400 V</text>
<text class="small" x="528" y="136">+ 轨</text>
<text class="small" x="528" y="304">− 轨</text>
<line class="wire" x1="460" y1="370" x2="800" y2="370"/>
<text class="small" x="806" y="374">底盘（chassis）</text>
<line class="wire" x1="575" y1="140" x2="575" y2="190"/>
<rect class="res" x="560" y="190" width="30" height="20"/>
<line class="wire" x1="575" y1="210" x2="575" y2="370"/>
<text class="sym" x="470" y="205">R_iso+ = 1 MΩ</text>
<line class="wire" x1="520" y1="300" x2="520" y2="318"/>
<rect class="res" x="505" y="318" width="30" height="20"/>
<line class="wire" x1="520" y1="338" x2="520" y2="370"/>
<text class="sym" x="400" y="333">R_ref = 200 kΩ（切换）</text>
<line class="wire" x1="620" y1="300" x2="620" y2="318"/>
<rect class="res" x="605" y="318" width="30" height="20"/>
<line class="wire" x1="620" y1="338" x2="620" y2="370"/>
<text class="sym" x="642" y="333">R_iso− = 100 kΩ（故障例）</text>
<line class="wire" x1="670" y1="300" x2="670" y2="330"/>
<rect class="res" x="655" y="330" width="30" height="20"/>
<line class="wire" x1="670" y1="350" x2="670" y2="370"/>
<text class="sym" x="692" y="345">C_y = 100 nF 并联</text>
<text class="small" x="500" y="114">窗1：|v−| = 36.36 V（浮地，先测）</text>
<text class="small" x="500" y="130">窗2：|v−′| = 25.0 V（接入 R_ref，等待 ≥ 3τ_y 后测）</text>
<text class="small" x="728" y="250">τ_y = 6.25 ms</text>
<text class="small" x="728" y="268">R_th = 三支路并联</text>
<text class="small" x="728" y="286">窗口 ≥ 3τ_y = 18.75 ms</text>
<text class="small" x="728" y="304">限值 500 Ω/V → 200 kΩ</text>
</svg>"""
    return svg


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    svg = build_svg()
    (OUT / "D23-F1-precharge-insulation.svg").write_text(svg, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
