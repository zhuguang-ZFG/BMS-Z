#!/usr/bin/env python3
"""Generate D05 figures: MUX input-stage settling (mechanism+data) and open-wire
detector comparison (data, numbers from d05_mux_settling.py)."""

from __future__ import annotations

from html import escape
from pathlib import Path
import importlib.util
import math
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d05_mux_settling", HERE / "d05_mux_settling.py"
)
assert spec is not None and spec.loader is not None
d05 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d05
spec.loader.exec_module(d05)

ROOT = HERE.parents[2]
OUT = ROOT / "bms-book" / "engineering" / "assets" / "d05-afe"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .lbl { fill: #4d5d63; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .small { fill: #4d5d63; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .sym { fill: #003153; font: 700 19px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .wire { stroke: #003153; stroke-width: 2.2; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .curve { stroke: #176b64; stroke-width: 2.8; fill: none; stroke-linecap: round; }
  .thr { stroke: #a3322a; stroke-width: 1.8; fill: none; stroke-dasharray: 6 4; }
  .box { fill: #fbf8f1; stroke: #003153; stroke-width: 2; rx: 8; }
  .axis { stroke: #5c6d73; stroke-width: 1.3; }
  .grid { stroke: #d9cfba; stroke-width: 0.9; }
  .stuck { stroke: #a3322a; stroke-width: 2.6; fill: none; stroke-linecap: round; }
  .cell { stroke: #176b64; stroke-width: 2.2; fill: none; stroke-linecap: round; }
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


def f1_settling() -> str:
    w, h = 800, 430
    b = [text(40, 40, "图 D05-F1　MUX 切换后的 RC 建立", "title")]
    b.append(
        text(
            40,
            64,
            "源阻抗 10 kΩ × 采样电容 10 nF → τ = 100 µs；12 bit 建立要 901.09 µs",
            "sub",
        )
    )
    # 左：等效电路
    b.append('<rect class="box" x="40" y="100" width="220" height="90"/>')
    b.append(text(150, 126, "MUX 等效", "sym", "middle"))
    b.append(text(150, 150, "Rs 10 kΩ 串 Cs 10 nF", "small", "middle"))
    b.append(text(150, 172, "τ = Rs·Cs = 100 µs", "small", "middle"))
    # 右：建立曲线
    px0, px1, py0, py1 = 320, 740, 110, 330
    t_us = 1200.0
    v_step = 5.0

    def sx(t):
        return px0 + t / t_us * (px1 - px0)

    def sy(v):
        return py1 - v / v_step * (py1 - py0)

    b.append(f'<line class="axis" x1="{px0}" y1="{py1}" x2="{px1}" y2="{py1}"/>')
    b.append(f'<line class="axis" x1="{px0}" y1="{py0}" x2="{px0}" y2="{py1}"/>')
    lsb_half = v_step / 4096 / 2
    pts = []
    for i in range(0, 241):
        t = t_us * i / 240
        v = v_step * (1 - math.exp(-t / 100.0))
        pts.append((sx(t), sy(v)))
    b.append(
        '<polyline class="curve" points="'
        + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        + '"/>'
    )
    b.append(
        f'<line class="thr" x1="{px0}" y1="{sy(lsb_half)}" x2="{px1}" y2="{sy(lsb_half)}"/>'
    )
    b.append(
        f'<line class="thr" x1="{sx(901.09)}" y1="{py0}" x2="{sx(901.09)}" y2="{py1}"/>'
    )
    b.append(text(px0 + 6, sy(lsb_half) - 8, "LSB/2 = 0.610 mV（建立判据）", "small"))
    b.append(text(sx(901.09) + 6, py0 + 16, "t = 901.09 µs", "small"))
    for tv, lab in (
        (0, "0"),
        (300, "300 µs"),
        (600, "600 µs"),
        (900, "900 µs"),
        (1200, "1.2 ms"),
    ):
        b.append(text(sx(tv), py1 + 20, lab, "small", "middle"))
    b.append(text(40, 300, "扫描预算 = 每串（建立 901.09 µs + 转换 20 µs）", "lbl"))
    b.append(
        text(
            40,
            326,
            "16 串 = 14.73746 ms > 10 ms 任务：装不下的账必须改前端/指标/架构",
            "lbl",
        )
    )
    return svg(
        w,
        h,
        "MUX 切换后的 RC 建立",
        "源阻抗与采样电容决定的一阶建立曲线与 12 bit 建立时刻",
        "\n".join(b),
    )


def f2_open_wire() -> str:
    w, h = 800, 430
    b = [text(40, 40, "图 D05-F2　量程内开线与三种检测手段", "title")]
    b.append(
        text(
            40,
            64,
            "开线保持 3.280 V：卡值窗只在漂移时碰巧触发，主动稽核与静置与否无关",
            "sub",
        )
    )
    ow = d05.open_wire_trace()
    px0, py0 = 70, 110
    # 两条时间线：A 静置 / B 漂移
    for row, (label, trace, color_cls) in enumerate(
        (
            ("A 静置：卡值窗漏报", ow["rest"]["cell_trace_v"], "cell"),
            ("B 漂移：卡值窗碰巧触发", ow["drift"]["cell_trace_v"], "cell"),
        )
    ):
        y = py0 + row * 90
        b.append(text(px0, y - 10, label, "lbl"))
        for i, v in enumerate(trace):
            x = px0 + i * 46
            top = y + 60 - (v - 3.26) * 4000
            b.append(
                f'<line class="{color_cls}" x1="{x}" y1="{y + 60}" x2="{x}" y2="{top:.1f}"/>'
            )
        held = ow["stuck_v"]
        held_y = y + 60 - (held - 3.26) * 4000
        b.append(
            f'<line class="stuck" x1="{px0 - 8}" y1="{held_y:.1f}" x2="{px0 + 6 * 46 + 16}" y2="{held_y:.1f}"/>'
        )
        b.append(text(px0 + 6 * 46 + 24, held_y + 4, "开线保持 3.280 V", "small"))
    # 稽核示意
    y = py0 + 2 * 90 + 10
    b.append(text(px0, y - 10, "C 主动稽核：注入 +5.0 mV 偏置", "lbl"))
    b.append(f'<rect class="box" x="{px0}" y="{y}" width="150" height="44"/>')
    b.append(text(px0 + 75, y + 27, "注入 +5.0 mV", "small", "middle"))
    b.append(
        f'<line class="wire" x1="{px0 + 150}" y1="{y + 22}" x2="{px0 + 220}" y2="{y + 22}"/>'
    )
    b.append(f'<rect class="box" x="{px0 + 220}" y="{y}" width="170" height="44"/>')
    b.append(text(px0 + 305, y + 27, "响应 0.0 mV → 开线", "small", "middle"))
    b.append(
        text(
            70,
            400,
            "结论：能写进需求的只有主动稽核；卡值窗的漂移成功是碰巧不是设计",
            "lbl",
        )
    )
    return svg(
        w,
        h,
        "量程内开线与三种检测手段",
        "静置与漂移两种真实轨迹下开线保持值与卡值窗/主动稽核的对照",
        "\n".join(b),
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    figures = {
        "D05-F1-mux-settling.svg": f1_settling(),
        "D05-F2-open-wire.svg": f2_open_wire(),
    }
    for name, payload in figures.items():
        (OUT / name).write_text(payload, encoding="utf-8")
        print(f"wrote {OUT / name}")


if __name__ == "__main__":
    main()
