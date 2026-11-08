#!/usr/bin/env python3
"""Generate D01 cell-evidence figures (mechanism diagrams, hand-authored).

F1: cell cross-section showing electron path (external circuit) vs ion path
(electrolyte), with the four terminal-voltage contributions labelled.
F2: logarithmic time-scale map of the four polarization terms.

Both are mechanism sketches; numbers appear only where D01 freezes them.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "bms-book" / "engineering" / "assets" / "d01-cell"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .lbl { fill: #4d5a5f; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .small { fill: #4d5a5f; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .sym { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .wire { stroke: #003153; stroke-width: 2.4; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .electron { stroke: #a3322a; stroke-width: 2.6; fill: none; stroke-linecap: round; stroke-dasharray: 2 6; }
  .ion { stroke: #176b64; stroke-width: 2.6; fill: none; stroke-linecap: round; }
  .electrode-p { fill: #003153; opacity: 0.16; stroke: #003153; stroke-width: 1.6; }
  .electrode-n { fill: #8a5019; opacity: 0.16; stroke: #8a5019; stroke-width: 1.6; }
  .separator { fill: #f6f1e3; stroke: #5c6d73; stroke-width: 1.6; stroke-dasharray: 4 4; }
  .collector { stroke: #003153; stroke-width: 3; fill: none; }
  .axis { stroke: #5c6d73; stroke-width: 1.3; fill: none; }
  .band { opacity: 0.20; }
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


def f1_cross_section() -> str:
    w, h = 800, 476
    b = [text(40, 40, "图 D01-F1　电芯剖面与两条载流路径", "title")]
    b.append(text(40, 64, "机制示意：电子走外电路，锂离子穿隔膜；端电压是四项之和", "sub"))
    # 电芯体（层叠示意，非任何料号结构）
    cell_x, cell_y, cell_w, cell_h = 120, 100, 300, 300
    b.append(
        f'<rect x="{cell_x}" y="{cell_y}" width="{cell_w}" height="{cell_h}" '
        'class="box" rx="10"/>'
    )
    # 正极集流体 + 正极涂层 + 隔膜 + 负极涂层 + 负极集流体（从左到右层叠）
    layers = [
        ("正极集流体", 18, "collector"),
        ("正极涂层", 76, "electrode-p"),
        ("隔膜（锂离子通过）", 24, "separator"),
        ("负极涂层", 76, "electrode-n"),
        ("负极集流体", 18, "collector"),
    ]
    x = cell_x + 16
    cx_mid = float(cell_x + cell_w / 2)  # 兜底：隔膜层必然会把下面的值覆盖掉
    for name, lw, cls in layers:
        if cls == "collector":
            b.append(
                f'<rect x="{x}" y="{cell_y + 14}" width="{lw}" height="{cell_h - 28}" class="collector"/>'
            )
        else:
            b.append(
                f'<rect x="{x}" y="{cell_y + 14}" width="{lw}" height="{cell_h - 28}" class="{cls}" rx="4"/>'
            )
        b.append(text(x + lw / 2, cell_y + cell_h + 26, name, "small", "middle"))
        if name.startswith("隔膜"):
            cx_mid = float(x + lw / 2)
        x += lw + 22
    assert cx_mid is not None
    # 电子路径：外电路（顶部导线 + 负载），红虚线
    b.append(
        f'<path class="electron" d="M {cell_x + 6} {cell_y - 22} H {cell_x + cell_w - 6}"/>'
    )
    b.append(
        f'<path class="electron" d="M {cell_x + 6} {cell_y} V {cell_y - 22} M {cell_x + cell_w - 6} {cell_y} V {cell_y - 22}"/>'
    )
    b.append(text(cell_x + cell_w / 2, cell_y - 32, "e⁻ 外电路（负载，放电为正）", "small", "middle"))
    # 锂离子路径：穿过隔膜，绿色
    b.append(
        f'<path class="ion" d="M {cx_mid - 120} 250 Q {cx_mid - 40} 210 {cx_mid} 250 '
        f'Q {cx_mid + 40} 290 {cx_mid + 120} 250"/>'
    )
    b.append(text(cx_mid, 226, "Li⁺", "sym", "middle"))
    b.append(text(cx_mid, 292, "锂离子经电解质/隔膜", "small", "middle"))
    # 端子
    b.append(text(cell_x - 14, cell_y + cell_h / 2, "＋", "sym", "end"))
    b.append(text(cell_x + cell_w + 14, cell_y + cell_h / 2, "－", "sym", "start"))
    # 右侧：端电压四项
    items = [
        ("U_ocv(z, T)", "化学势差（平衡电势），由 SOC 与温度定"),
        ("I·R_Ω", "欧姆极化 µs–ms，随电流瞬时消失"),
        ("η_ct", "电荷转移极化 ms–s，撤载后指数衰减"),
        ("η_conc", "浓差极化 十秒–分钟，最慢的尾巴"),
    ]
    ix, iy = 470, 120
    b.append(text(ix, iy - 20, "端电压 = 四项之和", "sym"))
    for i, (sym, desc) in enumerate(items):
        y = iy + i * 62
        b.append(f'<rect x="{ix}" y="{y}" width="300" height="48" class="box" rx="6"/>')
        b.append(text(ix + 14, y + 22, sym, "sym"))
        b.append(text(ix + 14, y + 40, desc, "small"))
    b.append(
        text(470, 420, "读数 = 叠影，不是状态本身；拆不开就说不清", "lbl")
    )
    return svg(w, h, "电芯剖面与两条载流路径", "电子经外电路、锂离子经隔膜的机制示意，右侧列端电压四项构成", "\n".join(b))


def f2_time_scales() -> str:
    w, h = 800, 372
    b = [text(40, 40, "图 D01-F2　极化项的时间尺度", "title")]
    b.append(text(40, 64, "同一读数里叠着快慢不同的项；用哪个读数就要等掉或建模比它慢的项", "sub"))
    # 对数时间轴 1e-6 s .. 1e4 s

    t0, t1 = -6.0, 4.0
    px0, px1 = 90, 740
    y_axis = 300

    def sx(exp: float) -> float:
        return px0 + (exp - t0) / (t1 - t0) * (px1 - px0)

    b.append(f'<line class="axis" x1="{px0}" y1="{y_axis}" x2="{px1}" y2="{y_axis}"/>')
    for e in range(-6, 5):
        x = sx(e)
        label = f"10^{e} s" if e not in (0,) else "1 s"
        b.append(f'<line class="axis" x1="{x:.1f}" y1="{y_axis}" x2="{x:.1f}" y2="{y_axis + 6}" stroke-width="1"/>')
        b.append(text(x, y_axis + 24, label, "small", "middle"))
    bands = [
        ("欧姆极化 I·R_Ω", -6, -3, "#a3322a", "一阶跃就消失"),
        ("电荷转移 η_ct", -3, 0.7, "#8a5019", "ms–s 指数衰减"),
        ("浓差极化 η_conc", 0.7, 4, "#176b64", "十秒–分钟弛豫"),
    ]
    for name, e0, e1, color, note in bands:
        x0, x1 = sx(e0), sx(e1)
        y = 120 + bands.index((name, e0, e1, color, note)) * 54
        b.append(
            f'<rect class="band" x="{x0:.1f}" y="{y}" width="{x1 - x0:.1f}" height="34" rx="6" fill="{color}"/>'
        )
        b.append(text(x0 + 8, y + 23, name, "lbl"))
        b.append(text(x1 - 8, y + 23, note, "small", "end"))
    b.append(text(px0, 108, "撤载后行为：", "sym"))
    b.append(text(90, 344, "读数时刻必须声明：刚撤载（三项都在）、静置后（只剩 OCV 与温度项）、带载（四项全在）", "small"))
    return svg(w, h, "极化项的时间尺度", "欧姆、电荷转移、浓差三项极化在对数时间轴上的分布与撤载后行为", "\n".join(b))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    figures = {
        "D01-F1-cross-section.svg": f1_cross_section(),
        "D01-F2-time-scales.svg": f2_time_scales(),
    }
    for name, payload in figures.items():
        (OUT / name).write_text(payload, encoding="utf-8")
        print(f"wrote {OUT / name}")


if __name__ == "__main__":
    main()
