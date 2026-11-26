"""Render chapter 28's synthetic interpolation evidence from its numerical report."""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bms-book/code"))
from hppc_grid_evidence import build_report  # noqa: E402

PALETTE = json.loads((ROOT / "tools/visual_palette.json").read_text(encoding="utf-8"))["light"]


def text(x, y, label, size=22, *, color="ink", weight=400, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{PALETTE.get(color, color)}">{escape(label)}</text>')


def line(x1, y1, x2, y2, *, color="line", dash="", width=2):
    return (f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" '
            f'stroke="{PALETTE.get(color, color)}" stroke-width="{width}" stroke-dasharray="{dash}"/>')


def frame(title, desc, height, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}" '
            f'viewBox="0 0 960 {height}" role="img" aria-labelledby="title desc">\n'
            f'<title id="title">{escape(title)}</title>\n<desc id="desc">{escape(desc)}</desc>\n'
            f'<rect width="960" height="{height}" rx="16" fill="{PALETTE["paper"]}"/>\n'
            '<g font-family="Noto Sans CJK SC, Microsoft YaHei, sans-serif">\n'
            + "\n".join(body) + '\n</g>\n</svg>\n')


def hidden_curvature(report):
    data = report["hidden_curvature"]
    x = lambda soc: 100 + (soc-.4)/.2*760  # noqa: E731
    y = lambda volt: 440 - (volt-3.50)/.20*260  # noqa: E731
    ry = lambda mv: 670 - mv/25*120  # noqa: E731
    body = [text(40, 48, "节点都对上了，中间仍差 20 mV", 32, weight=700),
            text(40, 84, "合成反例 · SOC 以 0–1 比例表示 · 曲线全程单调", color="muted"),
            line(100, 124, 145, 124, color="accent", width=4), text(156, 132, "合成真值"),
            line(360, 124, 405, 124, color="ink", dash="10 7", width=3), text(416, 132, "节点间线性插值"),
            text(100, 165, "电压 / V", 20, color="muted")]
    for volt in (3.50, 3.55, 3.60, 3.65, 3.70):
        body += [line(100, y(volt), 860, y(volt)), text(86, y(volt)+7, f"{volt:.2f}", 20, anchor="end")]
    for soc in (.4, .45, .5, .55, .6):
        body += [line(x(soc), 180, x(soc), 440), text(x(soc), 473, f"{soc:.2f}", 20, anchor="middle")]
    body += [text(940, 473, "SOC", 20, anchor="end")]
    for series, values, color, dash in (
        ("true", data["curve_true_v"], PALETTE["accent"], ""),
        ("prediction", data["curve_predicted_v"], PALETTE["ink"], "10 7"),
    ):
        points = " ".join(f"{x(z):.3f},{y(v):.3f}" for z, v in zip(data["curve_soc"], values, strict=True))
        body.append(f'<polyline data-series="{series}" points="{points}" fill="none" '
                    f'stroke="{color}" stroke-width="3" stroke-dasharray="{dash}"/>')
    for soc, volt in zip(data["node_soc"], data["node_values_v"], strict=True):
        body.append(f'<circle cx="{x(soc):.3f}" cy="{y(volt):.3f}" r="7" fill="{PALETTE["ink"]}"/>')
    body += [text(100, 520, "残差 = 合成真值 − 插值 / mV", 22, weight=700)]
    for mv in (0, 10, 20):
        body += [line(100, ry(mv), 860, ry(mv)), text(86, ry(mv)+7, str(mv), 20, anchor="end")]
    residual = [(a-b)*1000 for a, b in zip(data["curve_true_v"], data["curve_predicted_v"], strict=True)]
    points = " ".join(f"{x(z):.3f},{ry(v):.3f}" for z, v in zip(data["curve_soc"], residual, strict=True))
    body.append(f'<polyline data-series="residual" points="{points}" fill="none" '
                f'stroke="{PALETTE["technical"]["red"]}" stroke-width="3"/>')
    for z, mv in zip(data["validation_soc"], data["validation_residual_mv"], strict=True):
        body += [line(x(z), ry(0), x(z), ry(mv), color="ink", dash="4 5"),
                 text(x(z), ry(mv)-15, f"{mv:.0f} mV", 22, weight=700, anchor="middle"),
                 text(x(z), 704, f"验证点 {z:.2f}", 20, anchor="middle")]
    body += [text(40, 756, "三点二阶差分 ≈ 0；独立中点让隐藏的曲率露出来。", 23, weight=700),
             text(40, 791, "节点用于建表，验证点未参与本次建表。此图不代表实测电芯精度。", 21, color="muted")]
    return frame("网格节点正确不保证节点之间准确", "合成单调曲线在 SOC 0.4、0.5、0.6 的节点值共线，"
                 "但在独立验证点 0.45、0.55 处均偏离线性插值 20 mV。实线为真值，虚线为插值，圆点为节点。",
                 825, body)


def error_budget(report):
    rows = report["axis_refinement"]
    bias = report["node_error"]["constant_bias_mv"]
    body = [text(40, 48, "先看哪条轴占了大头，再决定加点", 32, weight=700),
            text(40, 84, "合成二维表 · 全域二阶导数界已知 · 单位：mV", color="muted"),
            '<defs><pattern id="temperature-hatch" width="8" height="8" patternUnits="userSpaceOnUse">'
            f'<rect width="8" height="8" fill="{PALETTE["soft"]}"/>'
            f'<path d="M0 8L8 0" stroke="{PALETTE["muted"]}" stroke-width="1"/></pattern></defs>',
            f'<rect x="40" y="112" width="25" height="20" fill="{PALETTE["accent"]}"/>',
            text(76, 130, "SOC 项（实色）", 21),
            '<rect x="320" y="112" width="25" height="20" fill="url(#temperature-hatch)"/>',
            text(356, 130, "温度项（斜线）", 21),
            text(40, 174, "网格间距：SOC / 温度", 20, color="muted"),
            text(760, 174, "合计", 20, color="muted"), text(894, 174, "节点", 20, anchor="middle", color="muted")]
    labels = ("原网格", "仅 SOC 减半", "仅温度减半", "两轴都减半")
    for i, (label, row) in enumerate(zip(labels, rows, strict=True)):
        yy = 207 + i*88
        sw, tw = row["soc_bound_mv"]*140, row["temperature_bound_mv"]*140
        body += [text(40, yy+9, label, 23, weight=700),
                 text(40, yy+39, f'{row["h_soc"]:g} / {row["h_temp_c"]:g} °C', 20, color="muted"),
                 f'<rect id="budget-{i}-soc" x="300" y="{yy}" width="{sw:g}" height="32" fill="{PALETTE["accent"]}"/>',
                 f'<rect id="budget-{i}-temperature" x="{300+sw:g}" y="{yy}" width="{tw:g}" height="32" fill="url(#temperature-hatch)" stroke="{PALETTE["muted"]}"/>',
                 text(300, yy+59, f'{row["soc_bound_mv"]:g} + {row["temperature_bound_mv"]:g}', 20),
                 text(760, yy+25, f'{row["bound_mv"]:g}', 25, weight=700),
                 text(894, yy+25, str(row["node_count"]), 22, anchor="middle")]
    body += [line(40, 565, 920, 565),
             text(40, 606, f'共同节点偏差 +{bias:g} mV：加密后仍然存在', 27, weight=700),
             text(40, 647, f'原网格：{rows[0]["bound_mv"]:g} + {bias:g} = {report["node_error"]["total_error_mv"]:.0f} mV', 23),
             text(495, 647, f'两轴减半：{rows[-1]["bound_mv"]:g} + {bias:g} = {rows[-1]["bound_mv"]+bias:g} mV', 23),
             text(40, 693, "本算例每格中点达到解析上界；真实参数表需另验曲率与节点误差。", 21, color="muted")]
    return frame("SOC 与温度的插值误差预算", "解析合成表的两轴误差相加。原网格 3 mV，仅 SOC 加密 2.625 mV，"
                 "仅温度加密 1.125 mV，两轴加密 0.75 mV。共同的 2 mV 节点偏差不会因加密消失。", 730, body)


def render_figures(report):
    return {"hppc-grid-hidden-curvature.svg": hidden_curvature(report),
            "hppc-grid-error-budget.svg": error_budget(report)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "bms-book/assets")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, svg in render_figures(build_report()).items():
        (args.out / name).write_text(svg, encoding="utf-8", newline="\n")
        print(name)


if __name__ == "__main__":
    main()
