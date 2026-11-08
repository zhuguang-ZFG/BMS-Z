#!/usr/bin/env python3
"""Generate D06 figures: return-path comparison (mechanism) and Kelvin/isolation
sketches (mechanism). Numbers come from d06_return_path.py."""
from __future__ import annotations

from html import escape
from pathlib import Path
import importlib.util
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d06_return_path", HERE / "d06_return_path.py")
assert spec is not None and spec.loader is not None
d06 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d06
spec.loader.exec_module(d06)

ROOT = HERE.parents[2]
OUT = ROOT / "bms-book" / "engineering" / "assets" / "d06-pcb"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .lbl { fill: #4d5d63; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .small { fill: #4d5d63; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .sym { fill: #003153; font: 700 19px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .bad { stroke: #a3322a; stroke-width: 2.8; fill: none; stroke-linecap: round; stroke-dasharray: 8 5; }
  .good { stroke: #176b64; stroke-width: 2.8; fill: none; stroke-linecap: round; }
  .wire { stroke: #003153; stroke-width: 2.2; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .box { fill: #fbf8f1; stroke: #003153; stroke-width: 2; rx: 8; }
  .sense { stroke: #8a5019; stroke-width: 2.2; fill: none; stroke-linecap: round; }
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


def f1_return_path() -> str:
    w, h = 800, 420
    b = [text(40, 40, "图 D06-F1　共享回流 vs 改回流路径", "title")]
    b.append(text(40, 64, "100 nH × 20 A / 1 µs = 2000 mV 地弹；动作是改回流，不是加滤波", "sub"))
    # 左：大电流与采样共用回流（错）
    b.append(text(60, 110, "× 共用回流", "sym"))
    b.append('<rect class="box" x="60" y="130" width="120" height="50"/>')
    b.append(text(120, 160, "开关节换 20 A/µs", "small", "middle"))
    b.append('<rect class="box" x="60" y="230" width="120" height="50"/>')
    b.append(text(120, 260, "mV 级采样前端", "small", "middle"))
    b.append('<path class="bad" d="M 180 155 H 260 V 255 H 180"/>')
    b.append(text(270, 200, "公共段 L ≈ 100 nH", "small"))
    b.append(text(270, 220, "地弹 2000 mV 串进采样地", "small"))
    # 右：分离回流 + 小环路（对）
    b.append(text(460, 110, "✓ 改回流路径", "sym"))
    b.append('<rect class="box" x="460" y="130" width="130" height="50"/>')
    b.append(text(525, 160, "开关节换 20 A/µs", "small", "middle"))
    b.append('<rect class="box" x="460" y="230" width="130" height="50"/>')
    b.append(text(525, 260, "mV 级采样前端", "small", "middle"))
    b.append('<path class="good" d="M 590 155 H 640 V 130 H 660 V 155 H 640"/>')
    b.append(text(665, 148, "换流走自己的小环路", "small"))
    b.append('<path class="good" d="M 590 255 H 700"/>')
    b.append(text(665, 244, "采样地独立回参考点", "small"))
    b.append(text(40, 350, "判据：公共段上的 di/dt 噪声与被测信号同量级 → 先改拓扑；加电容只是搬家", "lbl"))
    return svg(w, h, "共享回流与改回流路径对照", "大电流回路与采样前端共用/分离回流的对照示意与地弹账", "\n".join(b))


def f2_kelvin_isolation() -> str:
    w, h = 800, 420
    b = [text(40, 40, "图 D06-F2　Kelvin 四线读法与隔离共模路径", "title")]
    b.append(text(40, 64, "两线读 97.09% 误差；四线把引线排除；隔离给共模电流一条受控返回路", "sub"))
    # 左：Kelvin
    b.append(text(60, 110, "分流器读法", "sym"))
    b.append('<rect x="70" y="150" width="30" height="120" class="wire"/>')
    b.append(text(85, 290, "300 µΩ 分流器", "small", "middle"))
    b.append('<path class="bad" d="M 40 170 H 130 M 40 250 H 130"/>')
    b.append(text(140, 175, "× 两线：引线 10 mΩ 进测量回路 → 97.09%", "small"))
    b.append('<path class="sense" d="M 100 160 H 180 M 100 260 H 180"/>')
    b.append(text(140, 265, "✓ 四线：采样落在焊盘内侧，引线不载流 → ≈0%", "small"))
    # 右：隔离共模
    b.append(text(430, 110, "隔离共模路径", "sym"))
    b.append('<rect class="box" x="430" y="150" width="120" height="70"/>')
    b.append(text(490, 190, "原边 dv/dt 10 kV/µs", "small", "middle"))
    b.append('<rect class="box" x="620" y="150" width="120" height="70"/>')
    b.append(text(680, 190, "副边测量域", "small", "middle"))
    b.append('<path class="bad" d="M 550 165 C 585 150 615 150 620 165"/>')
    b.append(text(585, 140, "寄生 C 10 pF", "small", "middle"))
    b.append('<path class="good" d="M 620 205 C 585 220 570 220 550 205"/>')
    b.append(text(585, 240, "受控返回：屏蔽/Y 电容", "small", "middle"))
    b.append(text(430, 290, "10 pF × 10 kV/µs = 100 mA 级共模电流", "small"))
    b.append(text(40, 350, "读法：隔离不是断开；给共模电流受控的路，比“加强隔离”具体", "lbl"))
    return svg(w, h, "Kelvin 四线读法与隔离共模路径", "分流器两线/四线读法对照与隔离两侧共模电流的受控路径示意", "\n".join(b))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    figures = {"D06-F1-return-path.svg": f1_return_path(), "D06-F2-kelvin-isolation.svg": f2_kelvin_isolation()}
    for name, payload in figures.items():
        (OUT / name).write_text(payload, encoding="utf-8")
        print(f"wrote {OUT / name}")


if __name__ == "__main__":
    main()
