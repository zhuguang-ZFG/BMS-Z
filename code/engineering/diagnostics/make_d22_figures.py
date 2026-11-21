#!/usr/bin/env python3
"""Generate D22 figures: DTC debounce and lifecycle timeline (concept, numbers
read from d22_diagnostics.py default report)."""

from __future__ import annotations

from html import escape
from pathlib import Path
import importlib.util
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d22_diagnostics", HERE / "d22_diagnostics.py"
)
assert spec is not None and spec.loader is not None
d22 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d22
spec.loader.exec_module(d22)

ROOT = HERE.parents[2]
OUT = ROOT / "bms-book" / "engineering" / "assets" / "d22-diagnostics"

STYLE = """<style>
  .bg { fill: #f6f1e3; }
  .title { fill: #003153; font: 700 20px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .sub { fill: #5c6d73; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .lbl { fill: #4d5d63; font: 13px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .small { fill: #4d5d73; font: 12px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .value { fill: #003153; font: 700 18px 'Noto Sans SC','Microsoft YaHei',sans-serif; }
  .sym { fill: #003153; font: 700 17px 'KaiTi','STKaiti','Noto Serif SC',serif; }
  .axis { stroke: #5c6d73; stroke-width: 1.3; }
  .seg { stroke: #003153; stroke-width: 10; stroke-linecap: butt; opacity: 0.85; }
  .seg-fault { stroke: #a3322a; stroke-width: 10; stroke-linecap: butt; }
  .seg-prog { stroke: #7a6a2f; stroke-width: 10; stroke-linecap: butt; }
  .mark { stroke: #a3322a; stroke-width: 2; stroke-dasharray: 5 4; }
  .mark-heal { stroke: #2c6e49; stroke-width: 2; stroke-dasharray: 5 4; }
  .mark-note { stroke: #7a6a2f; stroke-width: 2; stroke-dasharray: 5 4; }
  .gate { fill: #fbf8f1; stroke: #5c6d73; stroke-width: 1.4; rx: 6; }
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


def f1_lifecycle() -> str:
    w, h = 840, 500
    report = d22.build_report(d22.default_events())
    transitions = report["lifecycle"]["transitions"]

    b = [text(40, 40, "图 D22-F1　DTC 去抖与生命周期时间线", "title")]
    b.append(
        text(
            40,
            64,
            "20 条评估驱动：确认 3 票、治愈 5 票；FAULT 锁存只认 service_clear，刷写退出回到进入前状态",
            "sub",
        )
    )

    # 时间轴：0..400 ms → x 60..800
    x0, x1, y_axis = 60, 800, 150
    span = 400.0

    def tx(t: float) -> float:
        return x0 + (t / span) * (x1 - x0)

    b.append(f'<line class="axis" x1="{x0}" y1="{y_axis}" x2="{x1}" y2="{y_axis}"/>')
    for t in range(0, 401, 40):
        b.append(f'<line class="axis" x1="{tx(t):.1f}" y1="{y_axis - 4}" x2="{tx(t):.1f}" y2="{y_axis + 4}"/>')
        b.append(text(tx(t), y_axis + 22, f"{t}", "small", "middle"))

    # 状态带：由迁移构造（0 起始默认 NORMAL 段）
    start_state = transitions[0]["to"] if transitions and transitions[0]["t_ms"] == 0.0 else "NORMAL"
    pts = []
    prev_t = 0.0
    prev_s = start_state
    for t in transitions:
        if t["t_ms"] == 0.0:
            prev_s = t["to"]
            continue
        pts.append((prev_t, t["t_ms"], prev_s))
        prev_t = t["t_ms"]
        prev_s = t["to"]
    pts.append((prev_t, span, prev_s))

    lane_y = y_axis - 26
    for (ta, tb, st) in pts:
        cls = "seg-fault" if st == "FAULT" else ("seg-prog" if st == "PROGRAMMING" else "seg")
        b.append(
            f'<line class="{cls}" x1="{tx(ta):.1f}" y1="{lane_y}" x2="{tx(tb):.1f}" y2="{lane_y}"/>'
        )
        b.append(text((tx(ta) + tx(tb)) / 2, lane_y - 12, st, "small", "middle"))

    # 关键事件标记
    marks = [
        (60.0, "stale_data 确认", "mark"),
        (120.0, "missing_slots 确认", "mark"),
        (220.0, "stale_data 清零", "mark-heal"),
        (240.0, "service_clear", "mark-note"),
        (340.0, "missing_slots 清零", "mark-heal"),
        (370.0, "刷写 gen 42 接受", "mark-note"),
    ]
    y_mark = y_axis + 60
    for t, label, cls in marks:
        b.append(f'<line class="{cls}" x1="{tx(t):.1f}" y1="{y_axis + 6}" x2="{tx(t):.1f}" y2="{y_mark - 8}"/>')
        b.append(text(tx(t), y_mark, label, "small", "middle"))

    # 冻结帧卡片
    freeze = {f["monitor"]: f for f in report["freeze_frames"]}
    card_y = 268
    b.append(f'<rect class="gate" x="60" y="{card_y}" width="350" height="84" rx="6"/>')
    b.append(text(76, card_y + 24, "冻结帧（确认当次，之后不改写）", "value"))
    sd = freeze["stale_data"]
    b.append(text(76, card_y + 46, f"stale_data @t=60：SOC {sd['soc_pp']:.1f} pp · {sd['pack_v_mv']:.0f} mV", "small"))
    ms = freeze["missing_slots"]
    b.append(text(76, card_y + 66, f"missing_slots @t=120：SOC {ms['soc_pp']:.1f} pp · counter {ms['counter']}", "small"))

    b.append(f'<rect class="gate" x="440" y="{card_y}" width="360" height="84" rx="6"/>')
    b.append(text(456, card_y + 24, "刷写三门 + 锁存规则", "value"))
    b.append(text(456, card_y + 46, "拒：非编程会话(session) / gen 越界(range) / 自检降级(self_test)", "small"))
    b.append(text(456, card_y + 66, "FAULT 可进刷写维修，退出仍回 FAULT——不许借刷写绕行", "small"))

    b.append(
        text(
            40,
            420,
            "读法：去抖按评估次数（3/5），不是 D19 的帧；FAULT 的钥匙只有 service_clear；",
            "lbl",
        )
    )
    b.append(
        text(
            40,
            444,
        "治愈清零只清 DTC，不解锁生命周期——两条账分开记。",
            "lbl",
        )
    )
    return svg(
        w,
        h,
        "DTC 去抖与生命周期时间线",
        "默认 20 条评估驱动的生命周期状态带、确认与治愈标记、冻结帧与刷写门",
        "\n".join(b),
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    figures = {"D22-F1-lifecycle-timeline.svg": f1_lifecycle()}
    for name, payload in figures.items():
        (OUT / name).write_text(payload, encoding="utf-8")
        print(f"wrote {OUT / name}")


if __name__ == "__main__":
    main()
