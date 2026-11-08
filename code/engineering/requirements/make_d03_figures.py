#!/usr/bin/env python3
"""Generate D03 requirements figures (mechanism diagrams, hand-authored).

F1: system boundary and the flow of quantities (task -> quantified needs ->
measurement/estimation/protection owners).
F2: constraint map: the five requirement windows drawn as overlapping ranges
with the weakest-cell counterexample marked.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "bms-book" / "engineering" / "assets" / "d03-requirements"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .lbl { fill: #4d5a5f; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .small { fill: #4d5a5f; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .sym { fill: #003153; font: 700 19px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .wire { stroke: #003153; stroke-width: 2.2; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .flow { stroke: #176b64; stroke-width: 2.6; fill: none; stroke-linecap: round; marker-end: url(#arrow); }
  .box { fill: #fbf8f1; stroke: #003153; stroke-width: 2; rx: 8; }
  .owner { fill: #fbf8f1; stroke: #8a5019; stroke-width: 2; rx: 8; }
  .range { height: 26; rx: 6; opacity: 0.28; }
  .mark { stroke: #a3322a; stroke-width: 2.4; stroke-dasharray: 6 4; }
  .axis { stroke: #5c6d73; stroke-width: 1.3; }
</style>"""


def svg(width: int, height: int, title: str, desc: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{escape(title)}">\n'
        f"<title>{escape(title)}</title>\n<desc>{escape(desc)}</desc>\n"
        f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#176b64"/></marker></defs>\n'
        f"{STYLE}\n"
        f'<rect class="bg" x="0" y="0" width="{width}" height="{height}"/>\n{body}\n</svg>\n'
    )


def text(x, y, value, cls="lbl", anchor="start") -> str:
    return (
        f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}">'
        f"{escape(value, quote=False)}</text>"
    )


def f1_boundary() -> str:
    w, h = 800, 420
    b = [text(40, 40, "图 D03-F1　系统边界与量的流向", "title")]
    b.append(
        text(
            40,
            64,
            "任务进来，量化需求落地；测量/估计/保护各归一个所有者，跨界走显式接口",
            "sub",
        )
    )
    # 左：负载任务
    b.append('<rect class="box" x="40" y="110" width="170" height="90"/>')
    b.append(text(125, 140, "负载任务", "sym", "middle"))
    b.append(text(125, 164, "电流/功率谱", "small", "middle"))
    b.append(text(125, 184, "温度·SOC·寿命", "small", "middle"))
    # 中：量化需求（12 字段）
    b.append('<rect class="box" x="300" y="100" width="200" height="110"/>')
    b.append(text(400, 130, "量化需求（12 字段）", "sym", "middle"))
    b.append(text(400, 154, "化学体系·串并·窗口", "small", "middle"))
    b.append(text(400, 174, "一致性·职责归属", "small", "middle"))
    b.append(text(400, 194, "缺一格即规格缺项", "small", "middle"))
    # 右：三个所有者
    owners = [
        ("测量", "值·时刻·有效位", 80),
        ("估计", "状态·不确定度", 200),
        ("保护", "动作·时限·锁存", 320),
    ]
    for name, desc, y in owners:
        b.append(f'<rect class="owner" x="580" y="{y}" width="180" height="80"/>')
        b.append(text(670, y + 30, name, "sym", "middle"))
        b.append(text(670, y + 54, desc, "small", "middle"))
    # 流向箭头
    b.append('<path class="flow" d="M 210 155 H 292"/>')
    b.append('<path class="flow" d="M 500 130 C 540 130 540 120 572 120"/>')
    b.append('<path class="flow" d="M 500 155 H 572"/>')
    b.append('<path class="flow" d="M 500 180 C 540 180 540 360 572 360"/>')
    b.append(text(246, 140, "变成可核对的数", "small", "middle"))
    b.append(text(536, 240, "跨界走显式接口与证据", "small", "middle"))
    # 底部注
    b.append(
        text(40, 300, "示例：持续 40 A × 单节 8 mΩ → 12.8 W/串（热账喂 D16）", "lbl")
    )
    b.append(
        text(
            40,
            326,
            "示例：过压 100 ms 动作 → 测量链误差与延迟预算有上界（喂 D04/D08，C1 初稿）",
            "lbl",
        )
    )
    return svg(
        w,
        h,
        "系统边界与量的流向",
        "任务到量化需求再到测量/估计/保护三职责的分工与接口流向",
        "\n".join(b),
    )


def f2_constraint_map() -> str:
    w, h = 800, 440
    b = [text(40, 40, "图 D03-F2　约束地图与最弱单节", "title")]
    b.append(
        text(
            40,
            64,
            "五扇窗口各管一件事；均值达标、最弱单节越限的反例标在电压窗上",
            "sub",
        )
    )
    # 约束行
    rows = [
        ("电压窗（单节）", "3.30 V", "3.65 V", 3.30, 3.65, "#003153"),
        ("SOC 窗（可用）", "10 %", "90 %", 0.10, 0.90, "#176b64"),
        ("温度窗（充电）", "0 °C", "45 °C", 0.0, 45.0, "#8a5019"),
        ("持续电流", "−30 A", "40 A", -30.0, 40.0, "#5c6d73"),
        ("寿命目标", "2000 循环", "容量 ≥80 %", 0.0, 2000.0, "#a3322a"),
    ]
    y = 110
    for name, lo, hi, _lo_val, _hi_val, color in rows:
        b.append(text(40, y + 18, name, "lbl"))
        width = 300 if name == "电压窗（单节）" else 240
        x0 = 240
        b.append(
            f'<rect class="range" x="{x0}" y="{y}" width="{width}" height="26" rx="6" fill="{color}"/>'
        )
        b.append(text(x0 - 8, y + 18, lo, "small", "end"))
        b.append(text(x0 + width + 8, y + 18, hi, "small", "start"))
        y += 52

    # 最弱单节标记画在电压窗行
    # 3.30→3.65 映射到 240..540
    def vx(v: float) -> float:
        return 240 + (v - 3.30) / (3.65 - 3.30) * 300

    b.append(
        f'<line class="mark" x1="{vx(3.28):.1f}" y1="100" x2="{vx(3.28):.1f}" y2="146"/>'
    )
    b.append(
        f'<line class="mark" x1="{vx(3.3687):.1f}" y1="100" x2="{vx(3.3687):.1f}" y2="146"/>'
    )
    b.append(text(vx(3.28), 164, "最弱 3.28 V（越限）", "small", "middle"))
    b.append(text(vx(3.3687), 92, "均值 3.3687 V", "small", "middle"))
    b.append(
        text(
            40,
            400,
            "判据结构：均值管能量账，单节最小/最大管安全门——两层各自独立越限、独立动作",
            "lbl",
        )
    )
    return svg(
        w,
        h,
        "约束地图与最弱单节",
        "五扇需求窗口与最弱单节反例在电压窗上的标记",
        "\n".join(b),
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    figures = {
        "D03-F1-boundary-flow.svg": f1_boundary(),
        "D03-F2-constraint-map.svg": f2_constraint_map(),
    }
    for name, payload in figures.items():
        (OUT / name).write_text(payload, encoding="utf-8")
        print(f"wrote {OUT / name}")


if __name__ == "__main__":
    main()
