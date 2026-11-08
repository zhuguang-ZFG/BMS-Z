#!/usr/bin/env python3
"""Generate D04 figures: six-term sense-chain (mechanism) and budget comparison
(data, numbers read from d04_error_budget.py)."""

from __future__ import annotations

from html import escape
from pathlib import Path
import importlib.util
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d04_error_budget", HERE / "d04_error_budget.py"
)
assert spec is not None and spec.loader is not None
d04 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d04
spec.loader.exec_module(d04)

ROOT = HERE.parents[2]
OUT = ROOT / "bms-book" / "engineering" / "assets" / "d04-measurement"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .lbl { fill: #4d5d63; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .small { fill: #4d5d63; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .value { fill: #003153; font: 700 18px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .sym { fill: #003153; font: 700 19px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .chain { stroke: #003153; stroke-width: 2.4; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .new { stroke: #a3322a; stroke-width: 2.6; fill: none; stroke-linecap: round; }
  .box { fill: #fbf8f1; stroke: #003153; stroke-width: 2; rx: 8; }
  .box-new { fill: #fbf8f1; stroke: #a3322a; stroke-width: 2.2; rx: 8; }
  .bar-s1 { fill: #003153; opacity: 0.30; }
  .bar-six { fill: #a3322a; opacity: 0.28; }
  .axis { stroke: #5c6d73; stroke-width: 1.3; }
  .halo { paint-order: stroke; stroke: #f6f1e3; stroke-width: 4; stroke-linejoin: round; }
</style>"""


def svg(width: int, height: int, title: str, desc: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{escape(title)}">\n'
        f"<title>{escape(title)}</title>\n<desc>{escape(desc)}</desc>\n{STYLE}\n"
        f'<rect class="bg" x="0" y="0" width="{width}" height="{height}"/>\n{body}\n</svg>\n'
    )


def text(x, y, value, cls="lbl", anchor="start") -> str:
    return (
        f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}">'
        f"{escape(value, quote=False)}</text>"
    )


def f1_chain() -> str:
    w, h = 800, 420
    b = [text(40, 40, "图 D04-F1　六项误差源的信号链", "title")]
    b.append(
        text(
            40,
            64,
            "S1 的四项（黑）+ 本单元新增两项（红）；预算表不许按“看起来小”挑项",
            "sub",
        )
    )
    # 链路：传感 → 增益 → 偏置 → 温漂 → 量化 → 建立 → 读数
    stages = [
        ("电芯电压", "真值 V", False),
        ("增益 g_c", "比例项 2.0 mV", False),
        ("偏置 b_c+b_i", "常值 2.0 mV", False),
        ("温漂 α(T−T0)", "20 °C 考核 3.6 mV", True),
        ("量化 ±LSB/2", "16 bit 0.038 mV", True),
        ("建立 e_dyn", "0.5 mV", False),
        ("读数 y", "六项叠影", False),
    ]
    x = 30
    y = 150
    bw, bh, gap = 96, 64, 14
    for i, (name, note, is_new) in enumerate(stages):
        cls = "box-new" if is_new else "box"
        b.append(
            f'<rect class="{cls}" x="{x}" y="{y}" width="{bw}" height="{bh}" rx="8"/>'
        )
        b.append(text(x + bw / 2, y + 26, name, "sym", "middle"))
        b.append(text(x + bw / 2, y + 48, note, "small", "middle"))
        if i < len(stages) - 1:
            b.append(
                f'<line class="{"new" if is_new or stages[i + 1][2] else "chain"}" '
                f'x1="{x + bw}" y1="{y + bh / 2}" x2="{x + bw + gap}" y2="{y + bh / 2}"/>'
            )
        x += bw + gap
    # 底部三项口径说明
    notes = [
        "比例项：按工作点折算（3.6 V），随电压放大",
        "常值项：mV 级固定账，温度考核点决定温漂一项",
        "合成两个口径：上界 8.138 mV 承诺用；RSS 4.3922 mV 只解释典型波动",
    ]
    for i, note in enumerate(notes):
        b.append(text(40, 280 + i * 30, note, "lbl"))
    return svg(
        w,
        h,
        "六项误差源的信号链",
        "从电芯电压到读数的六站链路与各项教学界，红色为本单元新增两项",
        "\n".join(b),
    )


def f2_budget() -> str:
    w, h = 800, 400
    b = [text(40, 40, "图 D04-F2　四项子集 vs 六项预算", "title")]
    b.append(
        text(40, 64, "加量化与温漂两项后最坏界 4.5 → 8.138 mV；RSS 仍不是绝对界", "sub")
    )
    report = d04.build_report()
    worst6 = report["six_term_worst_mv"]
    rss6 = report["six_term_rss_mv"]
    worst4 = report["s1_subset_worst_mv"]
    rss4 = report["s1_subset_rss_mv"]
    scale = 60.0  # px per mV
    x0 = 200
    rows = [
        ("S1 四项上界", worst4, "bar-s1", f"{worst4} mV"),
        ("六项上界", worst6, "bar-six", f"{worst6} mV"),
        ("S1 四项 RSS", rss4, "bar-s1", f"{rss4} mV（非绝对界）"),
        ("六项 RSS", rss6, "bar-six", f"{rss6} mV（非绝对界）"),
    ]
    y = 110
    for name, val, cls, note in rows:
        b.append(text(x0 - 12, y + 18, name, "lbl", "end"))
        b.append(
            f'<rect class="{cls}" x="{x0}" y="{y}" width="{val * scale:.1f}" height="26" rx="5"/>'
        )
        b.append(text(x0 + val * scale + 10, y + 18, note, "value"))
        y += 56
    b.append(
        text(
            40,
            350,
            "读法：上界用于承诺与门限；RSS 只在互不相关假设下描述典型波动，不能替代上界",
            "lbl",
        )
    )
    return svg(
        w,
        h,
        "四项子集与六项预算对照",
        "S1 四项与本单元六项在最坏上界与 RSS 两个口径下的条形对照",
        "\n".join(b),
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    figures = {"D04-F1-sense-chain.svg": f1_chain(), "D04-F2-budget.svg": f2_budget()}
    for name, payload in figures.items():
        (OUT / name).write_text(payload, encoding="utf-8")
        print(f"wrote {OUT / name}")


if __name__ == "__main__":
    main()
