#!/usr/bin/env python3
"""Generate D02 figures: 2RC equivalent circuit (mechanism) and 1RC vs 2RC
rest-tail residual comparison (data, numbers read from d02_cell_model.py)."""
from __future__ import annotations

from html import escape
from pathlib import Path
import math

import importlib.util
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d02_cell_model", HERE / "d02_cell_model.py")
assert spec is not None and spec.loader is not None
d02 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d02
spec.loader.exec_module(d02)

ROOT = HERE.parents[2]
OUT = ROOT / "bms-book" / "engineering" / "assets" / "d02-model"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .lbl { fill: #4d5d63; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .small { fill: #4d5d63; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .sym { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .wire { stroke: #003153; stroke-width: 2.4; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .cmp { stroke: #8a5019; stroke-width: 2.6; fill: none; stroke-linecap: round; }
  .good { stroke: #176b64; stroke-width: 2.8; fill: none; stroke-linecap: round; }
  .node { fill: #003153; }
  .box { fill: none; stroke: #003153; stroke-width: 2; }
  .axis { stroke: #5c6d73; stroke-width: 1.3; fill: none; }
  .grid { stroke: #d9cfba; stroke-width: 0.9; fill: none; }
  .dev { stroke: #a3322a; stroke-width: 2.2; fill: none; stroke-dasharray: 6 4; }
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


def f1_circuit() -> str:
    w, h = 800, 420
    b = [text(40, 40, "图 D02-F1　二阶 RC 等效电路（极性与 D01 一致）", "title")]
    b.append(text(40, 64, "R0 是瞬时项；两条 R∥C 串联支路分别记 vp1（慢）与 vp2（快）", "sub"))
    # 拓扑：源 -> R0 -> 节点 -> [R1-C1 二端网络] -> [R2-C2 二端网络] -> 正端子 -> 负载 -> 负端子
    y = 210
    b.append(f'<circle class="node" cx="80" cy="{y}" r="5"/>')
    b.append(text(64, y - 14, "＋", "sym", "middle"))
    # R0
    b.append(f'<line class="wire" x1="85" y1="{y}" x2="120" y2="{y}"/>')
    b.append(
        f'<path class="wire" d="M 120 {y} l 8 -12 l 12 24 l 12 -24 l 12 24 l 12 -24 l 12 24 l 8 -12"/>'
    )
    b.append(f'<line class="wire" x1="196" y1="{y}" x2="230" y2="{y}"/>')
    b.append(text(158, y - 34, "R0 20 mΩ（欧姆，µs–ms）", "small", "middle"))
    # 支路 1（慢，τ=45s）
    x1 = 230
    b.append(f'<line class="wire" x1="{x1}" y1="{y}" x2="{x1}" y2="{y - 70}"/>')
    b.append(f'<line class="wire" x1="{x1}" y1="{y - 70}" x2="{x1 + 90}" y2="{y - 70}"/>')
    b.append(
        f'<path class="wire" d="M {x1 + 90} {y - 70} l 0 14 l 60 0 l 0 -14"/>'
    )
    b.append(text(x1 + 120, y - 82, "R1 15 mΩ", "small", "middle"))
    b.append(f'<line class="wire" x1="{x1 + 90}" y1="{y - 56}" x2="{x1 + 90}" y2="{y - 20}"/>')
    b.append(f'<line class="wire" x1="{x1 + 150}" y1="{y - 56}" x2="{x1 + 150}" y2="{y - 20}"/>')
    b.append(f'<line class="wire" x1="{x1 + 84}" y1="{y - 20}" x2="{x1 + 96}" y2="{y - 20}"/>')
    b.append(f'<line class="wire" x1="{x1 + 144}" y1="{y - 20}" x2="{x1 + 156}" y2="{y - 20}"/>')
    b.append(text(x1 + 120, y - 8, "C1 3000 F（τ1 = 45 s，慢）", "small", "middle"))
    b.append(f'<line class="wire" x1="{x1 + 90}" y1="{y - 20}" x2="{x1 + 90}" y2="{y}"/>')
    b.append(f'<line class="wire" x1="{x1 + 150}" y1="{y - 20}" x2="{x1 + 150}" y2="{y}"/>')
    b.append(f'<line class="wire" x1="{x1}" y1="{y}" x2="{x1 + 90}" y2="{y}"/>')
    b.append(f'<line class="wire" x1="{x1 + 150}" y1="{y}" x2="{x1 + 240}" y2="{y}"/>')
    # 支路 2（快，τ=1s）
    x2 = x1 + 240
    b.append(f'<line class="wire" x1="{x2}" y1="{y}" x2="{x2}" y2="{y + 70}"/>')
    b.append(f'<line class="wire" x1="{x2}" y1="{y + 70}" x2="{x2 + 90}" y2="{y + 70}"/>')
    b.append(f'<path class="wire" d="M {x2 + 90} {y + 70} l 0 14 l 60 0 l 0 -14"/>')
    b.append(text(x2 + 120, y + 58, "R2 5 mΩ", "small", "middle"))
    b.append(f'<line class="wire" x1="{x2 + 90}" y1="{y + 84}" x2="{x2 + 90}" y2="{y + 120}"/>')
    b.append(f'<line class="wire" x1="{x2 + 150}" y1="{y + 84}" x2="{x2 + 150}" y2="{y + 120}"/>')
    b.append(f'<line class="wire" x1="{x2 + 84}" y1="{y + 120}" x2="{x2 + 96}" y2="{y + 120}"/>')
    b.append(f'<line class="wire" x1="{x2 + 144}" y1="{y + 120}" x2="{x2 + 156}" y2="{y + 120}"/>')
    b.append(text(x2 + 120, y + 140, "C2 200 F（τ2 = 1 s，快）", "small", "middle"))
    b.append(f'<line class="wire" x1="{x2 + 90}" y1="{y + 120}" x2="{x2 + 90}" y2="{y + 134}"/>')
    b.append(f'<line class="wire" x1="{x2 + 150}" y1="{y + 120}" x2="{x2 + 150}" y2="{y + 134}"/>')
    b.append(f'<line class="wire" x1="{x2}" y1="{y + 134}" x2="{x2 + 90}" y2="{y + 134}"/>')
    b.append(f'<line class="wire" x1="{x2 + 150}" y1="{y + 134}" x2="{x2 + 240}" y2="{y + 134}"/>')
    b.append(f'<line class="wire" x1="{x2 + 240}" y1="{y}" x2="{x2 + 240}" y2="{y + 134}"/>')
    # 端子与负载
    end = x2 + 240
    b.append(f'<line class="wire" x1="{end}" y1="{y}" x2="{end + 60}" y2="{y}"/>')
    b.append(f'<line class="wire" x1="{end}" y1="{y + 134}" x2="{end + 60}" y2="{y + 134}"/>')
    b.append(f'<rect class="box" x="{end + 60}" y="{y - 16}" width="70" height="32"/>')
    b.append(text(end + 95, y + 6, "负载 I", "lbl", "middle"))
    b.append(f'<line class="wire" x1="{end + 130}" y1="{y}" x2="{end + 170}" y2="{y}"/>')
    b.append(f'<line class="wire" x1="{end + 170}" y1="{y}" x2="{end + 170}" y2="{y + 134}"/>')
    b.append(f'<line class="wire" x1="{end + 170}" y1="{y + 134}" x2="{end + 130}" y2="{y + 134}"/>')
    b.append(f'<circle class="node" cx="{end + 175}" cy="{y + 67}" r="5"/>')
    b.append(text(end + 196, y + 62, "vp1 慢支路撤载后 45 s 尺度消退；vp2 快支路 1 s 尺度——S2 看不见它，因为它没有这条支路", "small"))
    return svg(w, h, "二阶 RC 等效电路", "R0 加两条 R-C 极化支路的串联二端网络拓扑，标注各元件教学值与时间常数", "\n".join(b))


def f2_residuals() -> str:
    w, h = 800, 420
    b = [text(40, 40, "图 D02-F2　欠模型的两个指纹：偏 τ 与结构化残差", "title")]
    b.append(text(40, 64, "同一撤流尾段：1RC 把 τ 拉偏到 31.5 s 且残差前大后小；2RC 精确命中 45 s 与 1 s", "sub"))
    rows, tail, fit1, fit2 = d02._fits()
    # 残差曲线（mV, t 0..60s 展示）
    px0, px1, py0, py1 = 80, 740, 90, 330
    t_max = 60.0
    r_max = 3.4

    def sx(t):
        return px0 + t / t_max * (px1 - px0)

    def sy(r):
        return py1 - (r + 0.4) / (r_max + 0.4) * (py1 - py0)

    b.append(f'<line class="axis" x1="{px0}" y1="{py1}" x2="{px1}" y2="{py1}"/>')
    b.append(f'<line class="axis" x1="{px0}" y1="{py0}" x2="{px0}" y2="{py1}"/>')
    for gv in (0.0, 1.0, 2.0, 3.0):
        b.append(f'<line class="grid" x1="{px0}" y1="{sy(gv):.1f}" x2="{px1}" y2="{sy(gv):.1f}"/>')
        b.append(text(px0 - 8, sy(gv) + 4, f"{gv:.0f}", "small", "end"))
    for tv in (0, 15, 30, 45, 60):
        b.append(text(sx(tv), py1 + 22, f"{tv} s", "small", "middle"))

    def resid(t, v, fit):
        taus, coef = fit["taus"], fit["coef"]
        pred = coef[0]
        for c, tau in zip(coef[1:], taus, strict=True):
            pred += c * math.exp(-t / tau)
        return (v - pred) * 1000.0

    pts1 = [(sx(t), sy(resid(t, v, fit1))) for t, v in tail if t <= t_max]
    pts2 = [(sx(t), sy(resid(t, v, fit2))) for t, v in tail if t <= t_max]
    b.append('<polyline class="cmp" points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts1) + '"/>')
    b.append('<polyline class="good" points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts2) + '"/>')
    b.append(text(px1 - 10, sy(2.6), "1RC：前 5 s 3.06 mV，60–180 s 0.13 mV", "lbl", "end"))
    b.append(text(px1 - 10, sy(-0.25), "2RC：残差 0（机器精度）", "lbl", "end"))
    b.append(text(px0 + 8, py0 + 6, "残差 mV（观测 − 拟合）", "small"))
    b.append(text(80, 380, "指纹判定：τ 被拉离真值之间 + 残差前大后小 ⇒ 欠模型；两个指纹都没有 ⇒ 不必升阶", "lbl"))
    return svg(w, h, "1RC 与 2RC 拟合残差对照", "同一撤流尾段上一阶与二阶拟合的残差曲线：欠模型留下前大后小的结构化残差", "\n".join(b))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    figures = {"D02-F1-2rc-circuit.svg": f1_circuit(), "D02-F2-residuals.svg": f2_residuals()}
    for name, payload in figures.items():
        (OUT / name).write_text(payload, encoding="utf-8")
        print(f"wrote {OUT / name}")


if __name__ == "__main__":
    main()
