#!/usr/bin/env python3
"""概念手绘插图生成器：八张定性示意图，零数字零文字。

视觉语言延续 bms-book 工程手绘口径：暖纸底、深墨轮廓、普鲁士蓝结构线、
青绿/赭黄/砖红少量平涂；人物为极简几何工程师。这些图只表达概念，
不含任何 <text> 元素，量化图仍由 generate_figures.py 从合成模型计算。
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "bms-book" / "assets" / "concepts"
W, H = 960, 560

PAPER = "#fffdf5"
SURFACE = "#f7f2e5"
INK = "#293b3a"
MUTED = "#626d65"
LINE = "#cfc6b2"
BLUE = "#496e96"   # 普鲁士蓝结构线
TEAL = "#176b73"
GREEN = "#377b60"
RED = "#b84745"
GOLD = "#926717"
MINT = "#e4f0df"
ROSE = "#f6e2df"
YELLOW = "#fbefc7"


def wobble_path(points: list[tuple[float, float]], jitter: float = 1.6,
                seed: str = "") -> str:
    """把折线变成轻微手绘抖动的三次贝塞尔路径，确定性（同 seed 同形）。"""
    if len(points) < 2:
        return ""
    out = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
    for index in range(1, len(points)):
        (x0, y0), (x1, y1) = points[index - 1], points[index]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1.0
        # 垂直方向的确定性小抖动
        h1 = int(hashlib.sha256(f"{seed}-{index}-a".encode()).hexdigest()[:6], 16)
        h2 = int(hashlib.sha256(f"{seed}-{index}-b".encode()).hexdigest()[:6], 16)
        off = ((h1 % 100) / 100 - 0.5) * 2 * jitter
        nx, ny = -dy / length, dx / length
        out.append(
            f"Q {mx + nx * off:.1f} {my + ny * off:.1f} {x1:.1f} {y1:.1f}"
        )
        _ = h2  # 保留：便于后续增强双向抖动而不改确定性
    return " ".join(out)


def rough_rect(x: float, y: float, w: float, h: float, seed: str,
               fill: str = "none", stroke: str = INK, sw: float = 3.0) -> str:
    pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    return (
        f'<path d="{wobble_path(pts, 1.8, seed)}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" '
        f'stroke-linejoin="round"/>'
    )


def line(points, seed, stroke=INK, sw=3.0, dash=None):
    dashattr = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<path d="{wobble_path(points, 1.5, seed)}" fill="none" '
            f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round"{dashattr}/>')


def person(x: float, y: float, scale: float = 1.0, pose: str = "stand",
           seed: str = "p") -> str:
    """极简几何小人：圆头 + 梯形身 + 手脚，y 为脚底。"""
    s = scale
    head_r = 9 * s
    parts = [f'<circle cx="{x:.1f}" cy="{y - 46 * s:.1f}" r="{head_r:.1f}" '
             f'fill="{SURFACE}" stroke="{INK}" stroke-width="{2.4 * s}"/>',
             # 眼睛（两点）
             f'<circle cx="{x - 3 * s:.1f}" cy="{y - 47 * s:.1f}" r="{1.2 * s:.1f}" fill="{INK}"/>',
             f'<circle cx="{x + 3 * s:.1f}" cy="{y - 47 * s:.1f}" r="{1.2 * s:.1f}" fill="{INK}"/>']
    body_top = y - 34 * s
    if pose == "point":  # 抬手指向
        parts.append(line([(x, y - 8 * s), (x, body_top)], f"{seed}-b", sw=2.4 * s))
        parts.append(line([(x, body_top + 3 * s), (x + 16 * s, body_top - 12 * s)],
                          f"{seed}-a1", sw=2.2 * s))
        parts.append(line([(x, body_top + 5 * s), (x - 12 * s, body_top - 4 * s)],
                          f"{seed}-a2", sw=2.2 * s))
    elif pose == "hold":  # 双手前捧
        parts.append(line([(x, y - 8 * s), (x, body_top)], f"{seed}-b", sw=2.4 * s))
        parts.append(line([(x, body_top + 3 * s), (x + 10 * s, body_top - 6 * s)],
                          f"{seed}-a1", sw=2.2 * s))
        parts.append(line([(x, body_top + 3 * s), (x - 10 * s, body_top - 6 * s)],
                          f"{seed}-a2", sw=2.2 * s))
    else:  # stand
        parts.append(line([(x, y - 8 * s), (x, body_top)], f"{seed}-b", sw=2.4 * s))
        parts.append(line([(x, body_top + 3 * s), (x + 11 * s, body_top - 8 * s)],
                          f"{seed}-a1", sw=2.2 * s))
        parts.append(line([(x, body_top + 3 * s), (x - 11 * s, body_top - 8 * s)],
                          f"{seed}-a2", sw=2.2 * s))
    # 腿
    parts.append(line([(x, y - 8 * s), (x + 7 * s, y)], f"{seed}-l1", sw=2.4 * s))
    parts.append(line([(x, y - 8 * s), (x - 7 * s, y)], f"{seed}-l2", sw=2.4 * s))
    return "".join(parts)


def hatch(pid: str, color: str = INK, gap: float = 7.0, sw: float = 1.1) -> str:
    return (f'<pattern id="{pid}" width="{gap}" height="{gap}" '
            f'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<line x1="0" y1="0" x2="0" y2="{gap}" stroke="{color}" '
            f'stroke-width="{sw}"/></pattern>')


def svg_doc(title: str, desc: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
  <title id="title">{title}</title>
  <desc id="desc">{desc}</desc>
  <defs>
    {hatch("hatch-ink")}
    {hatch("hatch-blue", BLUE)}
    {hatch("hatch-red", RED, gap=8)}
  </defs>
  <rect x="0" y="0" width="{W}" height="{H}" fill="{PAPER}"/>
  {body}
</svg>
'''


def fig_02_six_jobs() -> str:
    """BMS 六件事：中央电芯 + 六座环岛车站（纯图标，无文字）。"""
    cx, cy = 480, 285
    body = []
    # 环岛路
    body.append(f'<ellipse cx="{cx}" cy="{cy}" rx="300" ry="170" fill="none" '
                f'stroke="{LINE}" stroke-width="10" stroke-linecap="round"/>')
    body.append(f'<ellipse cx="{cx}" cy="{cy}" rx="300" ry="170" fill="none" '
                f'stroke="{BLUE}" stroke-width="2.4" stroke-dasharray="2 14" '
                f'stroke-linecap="round"/>')
    # 中央电芯
    body.append(rough_rect(cx - 52, cy - 86, 104, 172, "02-cell",
                           fill=SURFACE, stroke=INK, sw=3.4))
    body.append(f'<rect x="{cx - 30}" y="{cy - 102}" width="60" height="16" rx="5" '
                f'fill="{SURFACE}" stroke="{INK}" stroke-width="3"/>')
    body.append(f'<circle cx="{cx}" cy="{cy - 30}" r="16" fill="{TEAL}" '
                f'stroke="{INK}" stroke-width="2.6"/>')
    body.append(f'<path d="M {cx} {cy - 14} L {cx} {cy + 52}" stroke="{INK}" '
                f'stroke-width="2.6"/>')
    body.append(f'<path d="M {cx - 22} {cy + 20} L {cx + 22} {cy + 20}" '
                f'stroke="{INK}" stroke-width="2.6"/>')
    stations = [
        ("gauge",  cx,        cy - 188),  # 测量：表
        ("shield", cx + 288,  cy - 66),   # 保护：盾
        ("ledger", cx + 178,  cy + 152),  # 估计：账本
        ("pour",   cx - 178,  cy + 152),  # 均衡：互倒
        ("charge", cx - 288,  cy - 66),   # 充电：注入
        ("waves",  cx,        cy + 205),  # 通信：波纹
    ]
    for kind, sx, sy in stations:
        body.append(f'<circle cx="{sx}" cy="{sy}" r="46" fill="{PAPER}" '
                    f'stroke="{BLUE}" stroke-width="3"/>')
        if kind == "gauge":
            body.append(f'<path d="M {sx - 24} {sy + 14} A 26 26 0 0 1 {sx + 24} {sy + 14}" '
                        f'fill="none" stroke="{INK}" stroke-width="3"/>')
            body.append(line([(sx, sy + 12), (sx + 13, sy - 12)], "02-gn"))
            body.append(f'<circle cx="{sx}" cy="{sy + 12}" r="3.4" fill="{INK}"/>')
        elif kind == "shield":
            body.append(f'<path d="M {sx} {sy - 26} L {sx + 20} {sy - 16} L {sx + 18} {sy + 8} '
                        f'Q {sx} {sy + 26} {sx - 18} {sy + 8} L {sx - 20} {sy - 16} Z" '
                        f'fill="{MINT}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
            body.append(line([(sx - 8, sy - 2), (sx - 2, sy + 6), (sx + 10, sy - 10)],
                             "02-sh", stroke=GREEN, sw=3.4))
        elif kind == "ledger":
            body.append(rough_rect(sx - 20, sy - 24, 40, 48, "02-lg", fill=YELLOW,
                                   stroke=INK, sw=2.8))
            for dy in (-12, 0, 12):
                body.append(line([(sx - 12, sy + dy), (sx + 12, sy + dy)],
                                 f"02-lg{dy}", stroke=MUTED, sw=2))
        elif kind == "pour":
            body.append(rough_rect(sx - 26, sy - 8, 20, 26, "02-p1", fill=MINT,
                                   stroke=INK, sw=2.6))
            body.append(rough_rect(sx + 8, sy - 22, 20, 26, "02-p2", fill=MINT,
                                   stroke=INK, sw=2.6))
            body.append(line([(sx + 12, sy + 8), (sx - 4, sy + 20)], "02-p3",
                             stroke=TEAL, sw=3))
        elif kind == "charge":
            body.append(f'<path d="M {sx} {sy + 22} L {sx} {sy - 6}" stroke="{GREEN}" '
                        f'stroke-width="4" stroke-linecap="round"/>')
            body.append(f'<path d="M {sx} {sy - 18} L {sx - 9} {sy - 2} L {sx} {sy - 2} '
                        f'L {sx - 4} {sy + 10} L {sx + 9} {sy - 6} L {sx} {sy - 6} Z" '
                        f'fill="{GREEN}" stroke="{GREEN}" stroke-width="1.6" '
                        f'stroke-linejoin="round"/>')
        elif kind == "waves":
            for r in (8, 16, 24):
                body.append(f'<path d="M {sx - r} {sy} A {r} {r} 0 0 1 {sx + r} {sy}" '
                            f'fill="none" stroke="{TEAL}" stroke-width="2.8"/>')
    # 小人站在环路边，拿着扳手
    body.append(person(716, 330, 1.05, "stand", "02-w1"))
    body.append(line([(728, 288), (746, 272)], "02-w2", stroke=GOLD, sw=4))
    body.append(f'<circle cx="749" cy="269" r="6" fill="none" stroke="{GOLD}" stroke-width="3.4"/>')
    return svg_doc(
        "BMS 的六件事环岛图",
        "中央是一颗电芯，环岛公路上均匀分布六座车站：测量表、保护盾、估计账本、"
        "均衡互倒、充电注入与通信波纹；一名工程师站在路边拿着扳手。全图无文字无数字。",
        "\n  ".join(body))


def fig_08_second_protection() -> str:
    """硬件失效与二次保护：多米诺被独立栅栏拦住，身后小灯仍亮。"""
    body = []
    body.append(line([(60, 470), (900, 470)], "08-ground", sw=4))
    # 一排多米诺，前四张已倒，三张立着
    xs = [120, 190, 260, 330]
    for index, x in enumerate(xs):
        body.append(f'<rect x="{x}" y="428" width="72" height="18" rx="6" '
                    f'fill="{SURFACE}" stroke="{INK}" stroke-width="2.8" '
                    f'transform="rotate({-78 + index * 4} {x} 446)"/>')
    for x in (400, 470):
        body.append(rough_rect(x, 350, 34, 120, f"08-d{x}", fill=SURFACE,
                               stroke=INK, sw=3))
        body.append(f'<circle cx="{x + 17}" cy="382" r="6" fill="{ROSE}" '
                    f'stroke="{RED}" stroke-width="2"/>')
    # 栅栏（二次保护）
    bx = 560
    body.append(rough_rect(bx, 300, 46, 170, "08-bar", fill=YELLOW, stroke=INK, sw=4))
    for dy in (30, 80, 130):
        body.append(line([(bx + 4, 300 + dy), (bx + 42, 300 + dy)], f"08-b{dy}",
                         stroke=MUTED, sw=2.4))
    body.append(line([(bx - 8, 296), (bx + 54, 296)], "08-cap", stroke=INK, sw=5))
    # 栅栏身后的灯仍亮（提灯：圆顶 + 灯罩内灯泡 + 光晕）
    lx, ly = 730, 380
    body.append(line([(lx, 470), (lx, ly + 74)], "08-pole", sw=4))
    body.append(f'<path d="M {lx - 24} {ly + 24} A 24 24 0 0 1 {lx + 24} {ly + 24} '
                f'L {lx + 18} {ly + 30} L {lx - 18} {ly + 30} Z" fill="{YELLOW}" '
                f'stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
    body.append(rough_rect(lx - 18, ly + 30, 36, 44, "08-lamp", fill=YELLOW,
                           stroke=INK, sw=2.8))
    body.append(f'<circle cx="{lx}" cy="{ly + 52}" r="8" fill="{GOLD}" stroke="{INK}" stroke-width="2.4"/>')
    for ang in (-55, -20, 20, 55):
        rad = math.radians(ang + 90)
        x1, y1 = lx + 14 * math.cos(rad), ly + 52 + 14 * math.sin(rad)
        x2, y2 = lx + 32 * math.cos(rad), ly + 52 + 32 * math.sin(rad)
        body.append(line([(x1, y1), (x2, y2)], f"08-ray{ang}", stroke=GOLD, sw=2.4))
    # 失效传导 vs 独立供电：虚线在两路之间断开
    body.append(line([(120, 330), (400, 330), (470, 330)], "08-chain",
                     stroke=RED, sw=2.6, dash="7 7"))
    body.append(line([(505, 330), (560, 330)], "08-chain2", stroke=RED, sw=2.6, dash="2 10"))
    body.append(line([(640, 330), (730, 330), (730, 350)], "08-good",
                     stroke=GREEN, sw=2.6, dash="7 7"))
    # 独立的第二路供电小方块
    body.append(rough_rect(600, 430, 60, 40, "08-src", fill=MINT, stroke=GREEN, sw=2.8))
    body.append(line([(630, 430), (660, 392), (700, 392)], "08-src2",
                     stroke=GREEN, sw=2.6, dash="5 5"))
    body.append(person(300, 470, 1.0, "point", "08-p"))
    body.append(person(820, 470, 1.0, "hold", "08-p2"))
    return svg_doc(
        "二次保护是独立栅栏",
        "左侧多米诺相继倒下，最右两张被一堵厚实栅栏拦住；栅栏后的小灯仍亮，"
        "绿色虚线表示第二路由独立电源供电，与失效链路之间故意断开。无文字无数字。",
        "\n  ".join(body))


def fig_09_price_tag() -> str:
    """压差价签：同一条放电曲线上两只杯子的高度差挂着价签。"""
    body = []
    # 坐标感：一条 U 形曲线（示意，无刻度轴）
    curve = [(90, 180), (240, 420), (480, 470), (720, 420), (870, 180)]
    body.append(line(curve, "09-curve", stroke=BLUE, sw=4))
    body.append(line([(90, 520), (90, 140)], "09-ax", stroke=MUTED, sw=2.4))
    body.append(line([(90, 520), (900, 520)], "09-ax2", stroke=MUTED, sw=2.4))
    body.append(f'<path d="M 90 140 l -8 16 h 16 Z" fill="{MUTED}"/>')
    body.append(f'<path d="M 900 520 l -16 -8 v 16 Z" fill="{MUTED}"/>')
    # 两只杯子（电芯）在曲线不同高度
    body.append(rough_rect(240, 300, 70, 110, "09-c1", fill=MINT, stroke=INK, sw=3.2))
    body.append(f'<path d="M 244 336 h 62" stroke="{TEAL}" stroke-width="6" '
                f'stroke-linecap="round"/>')
    body.append(rough_rect(660, 240, 70, 110, "09-c2", fill=MINT, stroke=INK, sw=3.2))
    body.append(f'<path d="M 664 300 h 62" stroke="{TEAL}" stroke-width="6" '
                f'stroke-linecap="round"/>')
    # 高度差 + 价签
    body.append(line([(620, 336), (620, 300)], "09-gap", stroke=RED, sw=3.4))
    body.append(line([(600, 336), (640, 336)], "09-gap2", stroke=RED, sw=3.4))
    body.append(line([(600, 300), (640, 300)], "09-gap3", stroke=RED, sw=3.4))
    tx, ty = 620, 210
    body.append(f'<path d="M {tx} {ty} L {tx + 96} {ty + 10} L {tx + 88} {ty + 62} '
                f'L {tx - 8} {ty + 52} Z" fill="{YELLOW}" stroke="{INK}" '
                f'stroke-width="3" stroke-linejoin="round"/>')
    body.append(f'<circle cx="{tx + 10}" cy="{ty + 8}" r="5" fill="{PAPER}" '
                f'stroke="{INK}" stroke-width="2.4"/>')
    body.append(line([(tx + 20, ty + 22), (tx + 74, ty + 27)], "09-tag1",
                     stroke=MUTED, sw=2.4))
    body.append(line([(tx + 18, ty + 38), (tx + 60, ty + 42)], "09-tag2",
                     stroke=MUTED, sw=2.4))
    body.append(line([(tx + 6, ty + 12), (605, 318)], "09-tagline",
                     stroke=INK, sw=2, dash="4 5"))
    # 小人踮脚看价签
    body.append(person(800, 470, 1.0, "point", "09-p"))
    return svg_doc(
        "压差是曲线上的价签",
        "一条定性放电曲线，两只杯子状电芯停在不同高度，液面差用红色括线标出，"
        "并挂上一枚手写价签。坐标轴无刻度，全图无文字无数字。",
        "\n  ".join(body))


def fig_15_soh_two_faces() -> str:
    """SOH 的两张脸：同一颗电芯，左半新鲜右半老化。"""
    body = []
    # 电芯圆角柱
    body.append(f'<rect x="330" y="120" width="300" height="360" rx="26" '
                f'fill="{SURFACE}" stroke="{INK}" stroke-width="4"/>')
    body.append(f'<rect x="420" y="96" width="120" height="26" rx="9" '
                f'fill="{SURFACE}" stroke="{INK}" stroke-width="3.4"/>')
    # 中缝
    body.append(line([(480, 126), (480, 480)], "15-mid", stroke=MUTED, sw=2.6, dash="6 6"))
    # 左半：新鲜（满杯、平滑极板）
    body.append(f'<rect x="344" y="150" width="122" height="300" rx="14" '
                f'fill="{MINT}" stroke="{GREEN}" stroke-width="2.6"/>')
    body.append(f'<path d="M 348 210 h 114" stroke="{TEAL}" stroke-width="7" '
                f'stroke-linecap="round"/>')
    for yy in (270, 330, 390):
        body.append(line([(356, yy), (454, yy)], f"15-l{yy}", stroke=GREEN, sw=2.6))
    # 右半：老化（排线、皱缩极板、沉积点）
    body.append(f'<rect x="494" y="150" width="122" height="300" rx="14" '
                f'fill="url(#hatch-blue)" stroke="{BLUE}" stroke-width="2.6"/>')
    body.append(f'<path d="M 498 250 h 114" stroke="{GOLD}" stroke-width="7" '
                f'stroke-linecap="round"/>')
    for (dx, dy) in [(520, 300), (560, 340), (590, 296), (540, 400),
                     (588, 420), (610, 380)]:
        body.append(f'<circle cx="{dx}" cy="{dy}" r="5" fill="{GOLD}" '
                    f'stroke="{INK}" stroke-width="1.6"/>')
    # 两张脸：左微笑眼 / 右疲惫眼
    body.append(f'<path d="M 380 190 q 10 -10 20 0" fill="none" stroke="{INK}" stroke-width="3"/>')
    body.append(f'<path d="M 430 190 q 10 -10 20 0" fill="none" stroke="{INK}" stroke-width="3"/>')
    body.append(f'<path d="M 528 192 q 10 8 20 0" fill="none" stroke="{INK}" stroke-width="3"/>')
    body.append(f'<path d="M 572 192 q 10 8 20 0" fill="none" stroke="{INK}" stroke-width="3"/>')
    # 头顶两只量杯：一只满一只浅
    body.append(rough_rect(330, 40, 90, 44, "15-t1", fill=MINT, stroke=INK, sw=2.8))
    body.append(f'<path d="M 336 56 h 78" stroke="{TEAL}" stroke-width="8" stroke-linecap="round"/>')
    body.append(rough_rect(540, 40, 90, 44, "15-t2", fill=SURFACE, stroke=INK, sw=2.8))
    body.append(f'<path d="M 546 74 h 78" stroke="{TEAL}" stroke-width="8" stroke-linecap="round"/>')
    body.append(line([(420, 62), (540, 62)], "15-link", stroke=MUTED, sw=2, dash="5 6"))
    body.append(person(720, 500, 1.05, "point", "15-p"))
    body.append(person(250, 500, 1.05, "hold", "15-p2"))
    return svg_doc(
        "SOH 的两张脸",
        "一颗电芯从中缝分成两半：左半新鲜，极板平直、液面高、眼睛弯起；"
        "右半老化，极板区排线皱缩、散落沉积点、眼睛下垂；头顶两只量杯一满一浅。"
        "全图无文字无数字。",
        "\n  ".join(body))


def fig_17_no_truth() -> str:
    """无真值诊断：没有北方的地图，罗盘自由转，提灯照亮几条岔路。"""
    body = []
    # 地图底
    body.append(rough_rect(90, 90, 500, 380, "17-map", fill=SURFACE, stroke=INK, sw=3.4))
    # 等高线（几条无标注曲线）
    for index, off in enumerate((0, 36, 72)):
        pts = [(130, 380 - off), (250, 330 - off), (340, 360 - off),
               (460, 300 - off), (540, 330 - off)]
        body.append(line(pts, f"17-c{index}", stroke=LINE, sw=2.4))
    # 三条岔路（虚线，无终点标记）
    body.append(line([(140, 440), (280, 300), (380, 240), (520, 150)],
                     "17-r1", stroke=BLUE, sw=3, dash="8 7"))
    body.append(line([(140, 440), (300, 380), (420, 300), (540, 260)],
                     "17-r2", stroke=GREEN, sw=3, dash="8 7"))
    body.append(line([(140, 440), (260, 420), (420, 420), (560, 400)],
                     "17-r3", stroke=GOLD, sw=3, dash="8 7"))
    # 罗盘（针乱转）
    gx, gy = 700, 210
    body.append(f'<circle cx="{gx}" cy="{gy}" r="86" fill="{PAPER}" stroke="{INK}" stroke-width="3.6"/>')
    body.append(f'<circle cx="{gx}" cy="{gy}" r="66" fill="none" stroke="{LINE}" stroke-width="2.2"/>')
    body.append(f'<g transform="rotate(38 {gx} {gy})">'
                f'<path d="M {gx} {gy - 58} L {gx + 10} {gy} L {gx} {gy + 10} L {gx - 10} {gy} Z" '
                f'fill="{RED}" stroke="{INK}" stroke-width="2"/>'
                f'<path d="M {gx} {gy + 44} L {gx + 8} {gy} L {gx} {gy - 6} L {gx - 8} {gy} Z" '
                f'fill="{SURFACE}" stroke="{INK}" stroke-width="2"/></g>')
    body.append(f'<circle cx="{gx}" cy="{gy}" r="7" fill="{INK}"/>')
    # 提灯的人：灯光锥照亮三条路的起点
    body.append(person(210, 480, 1.15, "hold", "17-p"))
    lx, ly = 238, 420
    body.append(rough_rect(lx, ly, 34, 42, "17-lamp", fill=YELLOW, stroke=INK, sw=2.8))
    body.append(line([(lx + 17, ly), (lx + 17, ly - 12)], "17-lh", sw=2.6))
    body.append(f'<path d="M {lx + 17} {ly + 42} L 150 460 L 340 452 Z" fill="{YELLOW}" '
                f'opacity="0.35"/>')
    body.append(person(820, 470, 1.0, "stand", "17-p2"))
    return svg_doc(
        "没有真值的诊断现场",
        "一张没有北方标记的地图，三条虚线岔路从同一点散开；旁边罗盘指针自由偏转；"
        "工程师提着灯笼照亮起点，另一名工程师在远处观察。全图无文字无数字。",
        "\n  ".join(body))


def fig_22_open_stack() -> str:
    """开源架构：开放式层架，层与层之间留缝，社区的手递进扳手。"""
    body = []
    # 四块层板，开放留缝
    for index, y in enumerate((140, 250, 360, 470)):
        body.append(rough_rect(150, y, 560, 18, f"22-s{index}", fill=SURFACE,
                               stroke=INK, sw=3.2))
    # 各层方块（模块），层间错缝、可抽取
    blocks = [
        (190, 92, 110, 48, MINT), (330, 92, 90, 48, YELLOW), (450, 92, 130, 48, MINT),
        (220, 202, 90, 48, YELLOW), (350, 202, 140, 48, MINT), (530, 202, 90, 48, YELLOW),
        (180, 312, 140, 48, MINT), (360, 312, 100, 48, YELLOW), (500, 312, 120, 48, MINT),
        (250, 422, 120, 48, YELLOW), (420, 422, 150, 48, MINT),
    ]
    for index, (x, y, w, h, c) in enumerate(blocks):
        body.append(rough_rect(x, y, w, h, f"22-b{index}", fill=c, stroke=INK, sw=2.6))
    # 侧梯
    body.append(line([(750, 130), (750, 500)], "22-l1", sw=3.4))
    body.append(line([(790, 130), (790, 500)], "22-l2", sw=3.4))
    for index, y in enumerate(range(160, 500, 48)):
        body.append(line([(750, y), (790, y)], f"22-r{index}", sw=2.6))
    # 从下方伸上来两只几何手，把扳手递进中间缝
    body.append(f'<path d="M 470 560 Q 480 520 470 496" fill="{SURFACE}" stroke="{INK}" stroke-width="3"/>')
    body.append(f'<path d="M 440 560 Q 448 528 444 508" fill="{SURFACE}" stroke="{INK}" stroke-width="3"/>')
    body.append(line([(458, 500), (510, 452)], "22-w", stroke=GOLD, sw=5))
    body.append(f'<circle cx="514" cy="448" r="8" fill="none" stroke="{GOLD}" stroke-width="4"/>')
    # 接缝虚线：层间是开放的，不是密封盒
    body.append(line([(160, 205), (700, 205)], "22-g1", stroke=BLUE, sw=2, dash="3 9"))
    body.append(line([(160, 315), (700, 315)], "22-g2", stroke=BLUE, sw=2, dash="3 9"))
    body.append(line([(160, 425), (700, 425)], "22-g3", stroke=BLUE, sw=2, dash="3 9"))
    body.append(person(120, 500, 1.0, "point", "22-p"))
    return svg_doc(
        "开源架构是开放式层架",
        "四层开放层板上错落放着可抽取的模块方块，层与层之间留缝并以虚线标出；"
        "一只几何手从下方把扳手递进缝隙，侧面倚着梯子。无文字无数字。",
        "\n  ".join(body))


def fig_24_ai_in_loop() -> str:
    """BMS 与 AI：人手与机械手共握方向盘，下方接电池，旁有安全员。"""
    body = []
    # 方向盘
    cx, cy = 480, 210
    body.append(f'<circle cx="{cx}" cy="{cy}" r="110" fill="none" stroke="{INK}" stroke-width="9"/>')
    body.append(f'<circle cx="{cx}" cy="{cy}" r="24" fill="{SURFACE}" stroke="{INK}" stroke-width="5"/>')
    for ang in (90, 210, 330):
        rad = math.radians(ang)
        body.append(line([(cx + 22 * math.cos(rad), cy + 22 * math.sin(rad)),
                          (cx + 104 * math.cos(rad), cy + 104 * math.sin(rad))],
                         f"24-s{ang}", sw=6))
    # 左手（人手，肤色暖赭几何）
    body.append(f'<path d="M 300 258 Q 340 236 372 240 L 380 262 Q 346 268 312 282 Z" '
                f'fill="{SURFACE}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
    # 右手（机械爪，蓝）
    body.append(f'<path d="M 660 258 Q 620 236 588 240 L 580 262 Q 614 268 648 282 Z" '
                f'fill="{BLUE}" stroke="{INK}" stroke-width="3" stroke-linejoin="round" opacity="0.85"/>')
    # 转向柱 → 电池组
    body.append(line([(480, 334), (480, 396)], "24-col", sw=7))
    for index, x in enumerate((300, 420, 540)):
        body.append(rough_rect(x, 396, 100, 96, f"24-c{index}", fill=MINT,
                               stroke=INK, sw=3))
        body.append(f'<rect x="{x + 14}" y="412" width="72" height="12" rx="4" '
                    f'fill="{TEAL}" opacity="0.7"/>')
    body.append(line([(400, 444), (420, 444)], "24-l1", stroke=INK, sw=3))
    body.append(line([(520, 444), (540, 444)], "24-l2", stroke=INK, sw=3))
    # 护栏弧
    body.append(f'<path d="M 240 470 A 260 200 0 0 1 720 470" fill="none" '
                f'stroke="{GOLD}" stroke-width="6" stroke-linecap="round"/>')
    # 安全员：旁站，抱记事板（无文字）
    body.append(person(800, 500, 1.1, "hold", "24-p"))
    body.append(rough_rect(812, 430, 44, 58, "24-board", fill=YELLOW, stroke=INK, sw=2.6))
    body.append(line([(820, 446), (848, 446)], "24-b1", stroke=MUTED, sw=2))
    body.append(line([(820, 460), (848, 460)], "24-b2", stroke=MUTED, sw=2))
    body.append(line([(820, 474), (838, 474)], "24-b3", stroke=MUTED, sw=2))
    return svg_doc(
        "AI 在环，安全员在位",
        "一只人手和一只蓝色机械手共同握住方向盘，转向柱下接三块电池；"
        "金色护栏弧环绕下方；旁站工程师抱着空白记事板。全图无文字无数字。",
        "\n  ".join(body))


def fig_32_insulation_leak() -> str:
    """高压绝缘检测：电池架在绝缘支架上，一滴漏电流被旁路感应环捉住。"""
    body = []
    # 底盘（地）
    body.append(line([(80, 480), (880, 480)], "32-gnd", sw=4))
    for x in range(100, 880, 60):
        body.append(line([(x, 480), (x - 12, 496)], f"32-g{x}", stroke=MUTED, sw=2))
    # 绝缘支架（两只，画成陶瓷裙边）
    for px in (360, 560):
        body.append(f'<path d="M {px} 480 L {px + 20} 400 L {px + 60} 400 L {px + 80} 480 Z" '
                    f'fill="{SURFACE}" stroke="{INK}" stroke-width="3.2" stroke-linejoin="round"/>')
        body.append(line([(px + 8, 452), (px + 72, 452)], f"32-skirt{px}",
                         stroke=MUTED, sw=2.2))
        body.append(line([(px + 14, 428), (px + 66, 428)], f"32-skirt2{px}",
                         stroke=MUTED, sw=2.2))
    # 电池块（HV 包）
    body.append(rough_rect(300, 300, 240, 100, "32-pack", fill=YELLOW, stroke=INK, sw=3.6))
    body.append(f'<path d="M 540 326 l 26 10 l -26 10 Z" fill="{INK}"/>')
    body.append(line([(330, 340), (500, 340)], "32-hv1", stroke=RED, sw=3))
    body.append(line([(330, 362), (460, 362)], "32-hv2", stroke=RED, sw=3))
    # 外壳裂缝 + 一滴漏电流
    body.append(line([(420, 400), (428, 424), (418, 448), (426, 470)],
                     "32-crack", stroke=INK, sw=2.6))
    body.append(f'<path d="M 436 448 q 10 14 0 26 q -10 -12 0 -26" fill="{TEAL}" '
                f'stroke="{TEAL}" stroke-width="2"/>')
    # 漏电流路径（虚线）到地
    body.append(line([(440, 478), (470, 500), (520, 508)], "32-leak",
                     stroke=TEAL, sw=2.6, dash="5 6"))
    # 感应环（套在路径旁），表头立在独立小杆上，避开绝缘支架
    body.append(f'<circle cx="500" cy="500" r="34" fill="none" stroke="{BLUE}" '
                f'stroke-width="4"/>')
    body.append(line([(534, 494), (700, 470), (700, 420)], "32-sense",
                     stroke=BLUE, sw=3))
    body.append(line([(700, 470), (700, 480)], "32-mpole", sw=3.4))
    body.append(rough_rect(660, 356, 80, 64, "32-meter", fill=PAPER, stroke=BLUE, sw=3))
    body.append(f'<circle cx="700" cy="388" r="20" fill="none" stroke="{BLUE}" stroke-width="2.6"/>')
    body.append(line([(700, 388), (712, 374)], "32-nd", stroke=RED, sw=3))
    # 干燥侧 vs 受潮侧背景暗示
    body.append(f'<path d="M 700 300 q 20 -30 40 0 q -20 30 -40 0" fill="none" '
                f'stroke="{LINE}" stroke-width="2.4"/>')
    body.append(f'<path d="M 760 330 q 14 -22 28 0 q -14 22 -28 0" fill="none" '
                f'stroke="{LINE}" stroke-width="2.4"/>')
    body.append(person(220, 480, 1.05, "point", "32-p"))
    return svg_doc(
        "绝缘检测在等一滴漏电流",
        "高压电池包架在两只陶瓷裙边绝缘支架上，外壳裂缝渗出一滴蓝绿色漏电流，"
        "沿虚线流向底盘；蓝色感应环守在路径旁，引线连到一只无刻度表头。无文字无数字。",
        "\n  ".join(body))


FIGURES = {
    "02-six-jobs-map.svg": fig_02_six_jobs,
    "08-second-protection.svg": fig_08_second_protection,
    "09-differential-price-tag.svg": fig_09_price_tag,
    "15-soh-two-faces.svg": fig_15_soh_two_faces,
    "17-diagnosis-no-truth.svg": fig_17_no_truth,
    "22-open-architecture.svg": fig_22_open_stack,
    "24-ai-in-loop.svg": fig_24_ai_in_loop,
    "32-insulation-leak.svg": fig_32_insulation_leak,
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in FIGURES.items():
        text = fn()
        assert "<text" not in text, f"{name} 含文字元素"
        path = OUT / name
        path.write_text(text, encoding="utf-8")
        print(f"{name}: {len(text.encode('utf-8'))} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
