#!/usr/bin/env python3
"""Generate D07 and D08 figures (mechanism + data, numbers from the demo modules)."""
from __future__ import annotations

from html import escape
from pathlib import Path
import importlib.util
import sys

HERE = Path(__file__).resolve().parent


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, HERE / path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


d07 = load("d07_mos_path", "d07_mos_path.py")
d08 = load("d08_protection_timing", "d08_protection_timing.py")

ROOT = HERE.parents[2]
OUT7 = ROOT / "bms-book" / "engineering" / "assets" / "d07-power"
OUT8 = ROOT / "bms-book" / "engineering" / "assets" / "d08-protection"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .lbl { fill: #4d5d63; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .small { fill: #4d5d63; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .value { fill: #003153; font: 700 18px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .sym { fill: #003153; font: 700 19px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .wire { stroke: #003153; stroke-width: 2.2; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .body { stroke: #a3322a; stroke-width: 2.6; fill: none; stroke-linecap: round; stroke-dasharray: 7 5; }
  .channel { stroke: #176b64; stroke-width: 2.6; fill: none; stroke-linecap: round; }
  .box { fill: #fbf8f1; stroke: #003153; stroke-width: 2; rx: 8; }
  .soa-line { stroke: #003153; stroke-width: 2.4; fill: none; }
  .soa-pt { fill: #176b64; }
  .soa-bad { fill: #a3322a; }
  .axis { stroke: #5c6d73; stroke-width: 1.3; }
  .lane { stroke: #d9cfba; stroke-width: 0.9; }
  .bar { stroke: #003153; stroke-width: 2; }
  .hyst { stroke: #8a5019; stroke-width: 2.4; fill: none; }
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


def f7_1_paths() -> str:
    w, h = 800, 430
    b = [text(40, 40, "图 D07-F1　单颗 vs 背靠背：电流从哪条路走", "title")]
    b.append(text(40, 64, "单颗 NMOS 只挡一个方向；背靠背让体二极管互相顶住", "sub"))
    # 左：单颗
    b.append(text(60, 110, "× 单颗高边 NMOS（禁充）", "sym"))
    b.append('<rect class="box" x="120" y="130" width="70" height="46"/>')
    b.append(text(155, 158, "Q1", "sym", "middle"))
    b.append('<path class="body" d="M 40 190 H 340 M 40 200 H 340"/>')
    b.append(text(60, 184, "放电电流 → 体二极管照常导通", "small"))
    # 右：背靠背
    b.append(text(440, 110, "✓ 背靠背（源对源）", "sym"))
    b.append('<rect class="box" x="470" y="130" width="70" height="46"/>')
    b.append(text(505, 158, "Q1", "sym", "middle"))
    b.append('<rect class="box" x="590" y="130" width="70" height="46"/>')
    b.append(text(625, 158, "Q2", "sym", "middle"))
    b.append('<path class="channel" d="M 430 190 H 560 M 430 200 H 560"/>')
    b.append(text(440, 184, "任一方向都被一颗的沟道控制", "small"))
    # 底部热账
    b.append(text(40, 280, "热账：10 A 体二极管 7 W vs 沟道 0.2 W（35 倍）；40 A 热态 Rds_on 4.8 W", "lbl"))
    b.append(text(40, 308, "读法：每个“关断”命令都要问电流此刻从哪条路走", "lbl"))
    return svg(w, h, "单颗与背靠背电流路径对照", "单颗 NMOS 的体二极管漏电流路径与背靠背双向切断的对照", "\n".join(b))


def f7_2_soa() -> str:
    w, h = 800, 430
    b = [text(40, 40, "图 D07-F2　SOA 按脉冲宽度分层读", "title")]
    b.append(text(40, 64, "同一 Vds 下允许电流随脉宽分层：10 ms 行 30 A，100 ms 行 15 A（教学替身表）", "sub"))
    px0, px1, py0, py1 = 90, 740, 100, 340
    b.append(f'<line class="axis" x1="{px0}" y1="{py1}" x2="{px1}" y2="{py1}"/>')
    b.append(f'<line class="axis" x1="{px0}" y1="{py0}" x2="{px0}" y2="{py1}"/>')

    def sx(i_a):
        return px0 + i_a / 35.0 * (px1 - px0)

    def sy(pulse_s):
        import math
        lo, hi = -4.0, 1.5
        e = math.log10(pulse_s)
        return py1 - (e - lo) / (hi - lo) * (py1 - py0)

    rows = [(8.0, "DC"), (10.0, "1 s"), (15.0, "100 ms"), (30.0, "10 ms")]
    pts = " ".join(f"{sx(i):.1f},{sy(p):.1f}" for i, p in ((8.0, 30.0), (10.0, 1.0), (15.0, 0.1), (30.0, 0.01)))
    b.append(f'<polyline class="soa-line" points="{pts}"/>')
    for i_a, label in rows:
        y = sy({"DC": 30.0, "1 s": 1.0, "100 ms": 0.1, "10 ms": 0.01}[label])
        b.append(f'<circle class="soa-pt" cx="{sx(i_a):.1f}" cy="{y:.1f}" r="5"/>')
        b.append(text(sx(i_a) + 10, y + 4, f"{label}：{i_a:.0f} A", "small"))
    b.append(text(sx(20), sy(0.01) - 14, "● 20 A / 10 ms ✓", "small"))
    b.append(f'<circle class="soa-pt" cx="{sx(20):.1f}" cy="{sy(0.01):.1f}" r="6"/>')
    b.append(f'<circle class="soa-bad" cx="{sx(20):.1f}" cy="{sy(0.1):.1f}" r="6"/>')
    b.append(text(sx(20) + 10, sy(0.1) + 16, "● 20 A / 100 ms ✗（超 15 A）", "small"))
    b.append(text(90, 380, "纪律：先定脉宽，再对电流；把 10 ms 的许可当 100 ms 用是头号误用", "lbl"))
    return svg(w, h, "SOA 分层读图", "60 V 处按脉冲宽度分层的允许电流与两个读表练习点", "\n".join(b))


def f8_1_lanes() -> str:
    w, h = 800, 430
    b = [text(40, 40, "图 D08-F1　反应窗口全泳道（最坏档 72.263 ms）", "title")]
    b.append(text(40, 64, "相位 10.26337 + 确认 40 + 判决 2 + 执行反馈 15 + 调度 5 ms", "sub"))
    lanes = [
        ("故障→首样本", 0, 10.263, "#a3322a"),
        ("确认 3 拍", 10.263, 40.0, "#8a5019"),
        ("判决", 50.263, 2.0, "#003153"),
        ("执行→反馈", 52.263, 15.0, "#176b64"),
        ("调度抖动", 67.263, 5.0, "#5c6d73"),
    ]
    px0, scale = 60, 9.0
    y = 110
    total = 72.263
    for name, start, dur, color in lanes:
        b.append(text(px0 - 8, y + 16, name, "lbl", "end"))
        b.append(f'<rect x="{px0 + start * scale:.1f}" y="{y}" width="{dur * scale:.1f}" height="26" rx="5" fill="{color}" opacity="0.30"/>')
        b.append(text(px0 + (start + dur) * scale + 8, y + 17, f"{dur:.3g} ms", "small"))
        y += 48
    b.append(f'<line class="bar" x1="{px0 + total * scale:.1f}" y1="100" x2="{px0 + total * scale:.1f}" y2="{y - 10}"/>')
    b.append(text(px0 + total * scale + 6, y - 16, f"最坏 {total} ms（唯一可承诺档）", "value"))
    b.append(text(60, 380, "承诺只写最坏档；典型档等于把相位风险转嫁给现场", "lbl"))
    return svg(w, h, "反应窗口全泳道时序", "最坏相位下从故障到有效反馈的各段泳道与总窗口", "\n".join(b))


def f8_2_blind_hyst() -> str:
    w, h = 800, 430
    b = [text(40, 40, "图 D08-F2　确认窗的双面性与迟滞回环", "title")]
    b.append(text(40, 64, "40 ms 确认窗：8 ms 毛刺被抑制，25 ms 真实故障漏检（盲区 ~60 ms）；迟滞 50/45 A 把 12 次抖动折成 1 次", "sub"))
    # 左：毛刺 vs 故障
    px0, py0 = 70, 130
    for label, dur, color, verdict in (
        ("8 ms 毛刺", 8.0, "#176b64", "抑制 ✓"),
        ("25 ms 真实故障", 25.0, "#a3322a", "漏检 ✗"),
    ):
        width = dur * 6
        b.append(text(px0, py0 - 8, label, "lbl"))
        b.append(f'<rect x="{px0}" y="{py0}" width="{width:.1f}" height="22" rx="4" fill="{color}" opacity="0.5"/>')
        b.append(text(px0 + width + 8, py0 + 16, verdict, "small"))
        py0 += 52
    b.append(f'<line class="lane" x1="{px0}" y1="{py0 + 6}" x2="{px0 + 60 * 6}" y2="{py0 + 6}"/>')
    b.append(text(px0, py0 + 28, "确认窗 40 ms（+一拍采样 = 盲区 ~60 ms）", "small"))
    # 右：迟滞回环
    hx0, hy0, hw, hh = 470, 140, 260, 160
    b.append(f'<path class="hyst" d="M {hx0} {hy0 + hh} H {hx0 + hw * 0.55} V {hy0} H {hx0 + hw}"/>')
    b.append(f'<path class="hyst" d="M {hx0 + hw} {hy0} V {hy0 + hh * 0.28} H {hx0 + hw * 0.35} V {hy0 + hh} H {hx0}"/>')
    b.append(text(hx0 + hw * 0.55, hy0 - 12, "触发 50 A", "small", "middle"))
    b.append(text(hx0 + hw * 0.35, hy0 + hh + 24, "释放 45 A", "small", "middle"))
    b.append(text(hx0 - 8, hy0 + 6, "动作", "small", "end"))
    b.append(text(hx0 - 8, hy0 + hh, "释放", "small", "end"))
    b.append(text(hx0 + hw + 14, hy0 + hh / 2, "12 次 → 1 次", "value"))
    b.append(text(60, 400, "读法：确认窗与迟滞都是双刃剑——把收益写进文档时，把代价写同一行", "lbl"))
    return svg(w, h, "确认窗双面性与迟滞回环", "确认窗抑制毛刺同时造成盲区的对照与 50/45 A 迟滞回环示意", "\n".join(b))


def main() -> None:
    OUT7.mkdir(parents=True, exist_ok=True)
    OUT8.mkdir(parents=True, exist_ok=True)
    figures7 = {"D07-F1-current-paths.svg": f7_1_paths(), "D07-F2-soa-reading.svg": f7_2_soa()}
    figures8 = {"D08-F1-reaction-lanes.svg": f8_1_lanes(), "D08-F2-blind-hysteresis.svg": f8_2_blind_hyst()}
    for name, payload in figures7.items():
        (OUT7 / name).write_text(payload, encoding="utf-8")
        print(f"wrote {OUT7 / name}")
    for name, payload in figures8.items():
        (OUT8 / name).write_text(payload, encoding="utf-8")
        print(f"wrote {OUT8 / name}")


if __name__ == "__main__":
    main()
