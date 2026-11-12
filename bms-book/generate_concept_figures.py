#!/usr/bin/env python3
"""概念手绘插图生成器：十二张定性示意图，零数字零文字。

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


def fig_10_model_stunt() -> str:
    """等效模型：真身电芯在试镜镜框外，镜内站着四位约定规矩的替身。"""
    body = []
    # 真身电芯（卷绕圆柱）
    bx, by, bw, bh = 130, 170, 130, 290
    body.append(f'<path d="M {bx} {by + 26} L {bx} {by + bh} '
                f'A 65 26 0 0 0 {bx + bw} {by + bh} L {bx + bw} {by + 26} Z" '
                f'fill="{SURFACE}" stroke="{INK}" stroke-width="3.4"/>')
    body.append(f'<ellipse cx="{bx + bw / 2}" cy="{by + 26}" rx="65" ry="26" '
                f'fill="{MINT}" stroke="{INK}" stroke-width="3.4"/>')
    for off in (70, 130, 190):
        body.append(f'<path d="M {bx + 14} {by + 26 + off} q 50 22 102 0" '
                    f'fill="none" stroke="{LINE}" stroke-width="2.4"/>')
    # 试镜镜框（立式大镜）
    mx, my, mw, mh = 400, 100, 210, 390
    body.append(rough_rect(mx, my, mw, mh, "10-mirror", fill=MINT, stroke=INK, sw=4))
    body.append(line([(mx + 12, my + 12), (mx + mw - 30, my + mh - 24)],
                     "10-glass1", stroke="#ffffff", sw=3))
    body.append(line([(mx + 40, my + 10), (mx + mw - 8, my + mh - 52)],
                     "10-glass2", stroke="#ffffff", sw=2.2))
    # 镜内四位替身（自上而下：恒压块、短棒、弹簧对、储能罐）
    ix = mx + mw / 2
    body.append(rough_rect(ix - 34, my + 34, 68, 52, "10-ocv", fill=TEAL,
                           stroke=INK, sw=2.8))
    body.append(line([(ix - 40, my + 60), (ix - 34, my + 60)], "10-ocv-t1", sw=3))
    body.append(line([(ix + 34, my + 60), (ix + 40, my + 60)], "10-ocv-t2", sw=3))
    body.append(line([(ix - 42, my + 122), (ix + 42, my + 122)], "10-r0", sw=9))
    pts = [(ix - 42, my + 168)]
    for k in range(1, 8):
        pts.append((ix - 42 + k * 12, my + 168 + (14 if k % 2 else -14)))
    pts.append((ix + 42, my + 168))
    body.append(line(pts, "10-rc", stroke=GREEN, sw=3.2))
    body.append(rough_rect(ix - 30, my + 226, 60, 74, "10-cap", fill=YELLOW,
                           stroke=INK, sw=2.8))
    body.append(f'<ellipse cx="{ix}" cy="{my + 226}" rx="30" ry="10" '
                f'fill="{PAPER}" stroke="{INK}" stroke-width="2.4"/>')
    body.append(f'<ellipse cx="{ix}" cy="{my + 300}" rx="30" ry="10" '
                f'fill="{YELLOW}" stroke="{INK}" stroke-width="2.4"/>')
    # 镜脚与地面虚线：替身按约定替真身出场
    body.append(line([(mx + 20, my + mh), (mx + 6, my + mh + 34)], "10-leg1", sw=3.4))
    body.append(line([(mx + mw - 20, my + mh), (mx + mw - 6, my + mh + 34)],
                     "10-leg2", sw=3.4))
    body.append(line([(bx + bw, 460), (mx - 4, 470)], "10-agree", stroke=BLUE,
                     sw=2.4, dash="6 8"))
    # 右侧工程师：拿图纸卷对表
    body.append(person(740, 470, 1.15, "hold", "10-p"))
    body.append(f'<g transform="rotate(-18 780 420)">'
                f'{rough_rect(772, 396, 66, 46, "10-doc", fill=PAPER, stroke=INK, sw=2.6)}'
                f'</g>')
    body.append(line([(772, 408), (830, 408)], "10-doc-l1", stroke=BLUE, sw=1.8))
    body.append(line([(774, 420), (828, 420)], "10-doc-l2", stroke=BLUE, sw=1.8))
    body.append(line([(776, 432), (824, 432)], "10-doc-l3", stroke=BLUE, sw=1.8))
    body.append(line([(mx + mw, 300), (700, 400)], "10-agree2", stroke=BLUE,
                     sw=2.4, dash="6 8"))
    return svg_doc(
        "模型是与真身对过表的替身",
        "一颗卷绕电芯立在试镜大镜旁，镜内自上而下站着四位替身：带极耳的恒压块、"
        "一根短棒、一对之字弹簧、一只储能罐；蓝色虚线把真身、镜面与工程师手里的"
        "图纸卷连成一份约定。无文字无数字。",
        "\n  ".join(body))


def fig_16_two_clocks() -> str:
    """老化物理：日历座钟自己翻页，循环摆锤反复折弯同一片金属。"""
    body = []
    # 左：日历座钟（无指针无刻度的空白圆面，顶部吐纸口）
    cx1, cy1 = 240, 250
    body.append(rough_rect(cx1 - 62, cy1 + 90, 124, 130, "16-base1", fill=SURFACE,
                           stroke=INK, sw=3.2))
    body.append(f'<circle cx="{cx1}" cy="{cy1}" r="86" fill="{PAPER}" '
                f'stroke="{INK}" stroke-width="3.6"/>')
    body.append(f'<circle cx="{cx1}" cy="{cy1}" r="62" fill="none" stroke="{LINE}" '
                f'stroke-width="2.2"/>')
    body.append(rough_rect(cx1 - 46, cy1 - 128, 92, 34, "16-slot", fill=SURFACE,
                           stroke=INK, sw=2.8))
    # 飘落的空白页与撕下的页堆
    body.append(f'<g transform="rotate(14 {cx1 + 96} {cy1 - 90})">'
                f'{rough_rect(cx1 + 70, cy1 - 112, 52, 40, "16-leaf1", fill=PAPER, stroke=INK, sw=2.2)}'
                f'</g>')
    body.append(f'<g transform="rotate(-9 {cx1 + 150} {cy1 - 10})">'
                f'{rough_rect(cx1 + 124, cy1 - 32, 52, 40, "16-leaf2", fill=PAPER, stroke=INK, sw=2.2)}'
                f'</g>')
    for index in range(3):
        body.append(rough_rect(cx1 - 58 + index * 8, cy1 + 196 - index * 12,
                               116, 12, f"16-stack{index}", fill=PAPER,
                               stroke=INK, sw=2))
    # 右：循环钟 + 摆锤反复折弯金属片
    cx2, cy2 = 680, 250
    body.append(rough_rect(cx2 - 62, cy2 + 90, 124, 96, "16-base2", fill=SURFACE,
                           stroke=INK, sw=3.2))
    body.append(f'<circle cx="{cx2}" cy="{cy2}" r="86" fill="{PAPER}" '
                f'stroke="{INK}" stroke-width="3.6"/>')
    body.append(line([(cx2 - 40, cy2 - 20), (cx2, cy2 + 4), (cx2 + 40, cy2 - 20)],
                     "16-crack", stroke=RED, sw=2.2))
    body.append(f'<path d="M {cx2} {cy2 + 86} L {cx2 + 26} {cy2 + 150} '
                f'L {cx2 - 2} {cy2 + 208} L {cx2 + 22} {cy2 + 262}" fill="none" '
                f'stroke="{GOLD}" stroke-width="5" stroke-linecap="round"/>')
    body.append(f'<circle cx="{cx2 + 12}" cy="{cy2 + 232}" r="20" fill="{SURFACE}" '
                f'stroke="{INK}" stroke-width="3"/>')
    # 被折的金属片（折痕累积，裂缝发红）
    sx, sy = 726, 452
    body.append(f'<path d="M {sx} {sy} l 34 -26 l -6 34 l 34 -26 l -6 34 l 34 -26 '
                f'l -6 34" fill="none" stroke="{BLUE}" stroke-width="6" '
                f'stroke-linecap="round" stroke-linejoin="round"/>')
    body.append(rough_rect(sx - 12, sy + 12, 128, 16, "16-anvil", fill=SURFACE,
                           stroke=INK, sw=2.6))
    body.append(line([(sx + 30, sy - 16), (sx + 40, sy - 2)], "16-c1", stroke=RED, sw=1.8))
    body.append(line([(sx + 62, sy - 18), (sx + 70, sy - 4)], "16-c2", stroke=RED, sw=1.8))
    # 中间小苗：从两片叶到一片叶到落黄
    for index, (px, leaves, col) in enumerate(((430, 2, GREEN), (500, 1, GOLD),
                                               (560, 0, RED))):
        body.append(line([(px, 470), (px, 430)], f"16-stem{index}", stroke=GREEN, sw=3))
        if leaves >= 1:
            body.append(f'<path d="M {px} 448 q 22 -14 34 -4 q -20 12 -34 4" fill="{col}"/>')
        if leaves >= 2:
            body.append(f'<path d="M {px} 440 q -22 -14 -34 -4 q 20 12 34 4" fill="{col}"/>')
        if leaves == 0:
            body.append(f'<g transform="rotate(30 {px + 22} 462)">'
                        f'{rough_rect(px + 12, 456, 26, 12, f"16-fall{index}", fill=GOLD, stroke=INK, sw=1.8)}'
                        f'</g>')
    return svg_doc(
        "老化有两只钟",
        "左边日历座钟的空白圆面旁，纸页不断从顶部吐出、飘落，脚下撕下的页越堆越厚；"
        "右边循环钟的摆锤反复折弯砧上同一片金属，折痕处裂纹发红；中间一株小苗"
        "从两片绿叶退到一片黄叶再到一片落叶。无文字无数字。",
        "\n  ".join(body))


def fig_19_tower_routes() -> str:
    """总线全景：一座塔台指挥三条航线，粗线、细线与虚线各有规矩。"""
    body = []
    # 塔台（梯形塔身 + 指挥室）
    body.append(f'<path d="M 170 480 L 206 300 L 304 300 L 340 480 Z" '
                f'fill="{SURFACE}" stroke="{INK}" stroke-width="3.4"/>')
    body.append(f'<path d="M 196 300 L 210 236 L 300 236 L 314 300 Z" '
                f'fill="{MINT}" stroke="{INK}" stroke-width="3.4"/>')
    for y in (316, 356, 396):
        body.append(line([(178 + (y - 316) // 3, y), (332 - (y - 316) // 3, y)],
                         f"19-win{y}", stroke=BLUE, sw=3))
    body.append(line([(255, 236), (255, 176)], "19-mast", sw=3.4))
    body.append(f'<path d="M 255 178 L 300 190 L 255 204 Z" fill="{RED}" '
                f'stroke="{INK}" stroke-width="2"/>')
    # 三条航线（粗实线、细实线、虚线）
    body.append(line([(296, 246), (520, 170), (760, 130), (900, 116)],
                     "19-bus1", stroke=BLUE, sw=6))
    body.append(line([(300, 258), (540, 260), (770, 240), (902, 224)],
                     "19-bus2", stroke=GREEN, sw=3))
    body.append(line([(304, 270), (530, 350), (760, 392), (900, 404)],
                     "19-bus3", stroke=GOLD, sw=3, dash="10 8"))
    # 三架小飞机（机型不同）
    def plane(x, y, s, col):
        return (f'<g transform="translate({x} {y}) scale({s})">'
                f'<path d="M 0 0 L 34 -6 L 40 0 L 34 6 Z" fill="{col}" '
                f'stroke="{INK}" stroke-width="2.4"/>'
                f'<path d="M 12 -2 L -8 -18 L -2 -18 L 16 -2 Z" fill="{col}" '
                f'stroke="{INK}" stroke-width="2"/>'
                f'<path d="M 12 2 L -8 18 L -2 18 L 16 2 Z" fill="{col}" '
                f'stroke="{INK}" stroke-width="2"/></g>')
    body.append(plane(858, 108, 1.25, BLUE))
    body.append(plane(862, 232, 0.95, GREEN))
    body.append(plane(860, 414, 0.8, GOLD))
    # 地面停机位带（右侧一条地面线，三个停机位并排）
    body.append(line([(560, 500), (920, 500)], "19-ground", stroke=INK, sw=3))
    for index, x in enumerate((590, 700, 810)):
        body.append(rough_rect(x, 456, 90, 44, f"19-bay{index}",
                               fill="none", stroke=LINE, sw=2.4))
    body.append(line([(340, 470), (470, 492), (635, 478)], "19-g1",
                     stroke=LINE, sw=1.8, dash="4 8"))
    body.append(line([(345, 480), (520, 504), (745, 492)], "19-g2",
                     stroke=LINE, sw=1.8, dash="4 8"))
    body.append(line([(350, 490), (560, 518), (855, 494)], "19-g3",
                     stroke=LINE, sw=1.8, dash="4 8"))
    # 指挥员
    body.append(person(120, 480, 1.15, "point", "19-p"))
    return svg_doc(
        "总线是一座塔台指挥的航线网",
        "梯形塔台升起天线与红旗，三条航线从指挥室出发：粗实线、细实线与虚线，"
        "末端各有一架不同机型的小飞机；地面三个停机位以虚线引导入位，"
        "一名指挥员在塔台前抬手指引。无文字无数字。",
        "\n  ".join(body))


def fig_26_threshold_gate() -> str:
    """从原型到产品：工作台上的飞线原型跨过门槛，传送带那头是盖章成品。"""
    body = []
    # 左：工作台（面包板 + 飞线 + 示波器）
    body.append(rough_rect(80, 330, 260, 18, "26-top", fill=SURFACE, stroke=INK, sw=3.2))
    body.append(rough_rect(96, 348, 16, 130, "26-leg1", fill=SURFACE, stroke=INK, sw=3))
    body.append(rough_rect(308, 348, 16, 130, "26-leg2", fill=SURFACE, stroke=INK, sw=3))
    body.append(rough_rect(110, 288, 120, 40, "26-board", fill=PAPER,
                           stroke=INK, sw=2.6))
    for hx, hy in ((126, 302), (150, 302), (174, 302), (198, 302),
                   (138, 314), (162, 314), (186, 314), (210, 314)):
        body.append(f'<circle cx="{hx}" cy="{hy}" r="2.6" fill="{INK}"/>')
    body.append(f'<path d="M 210 296 C 250 240, 300 262, 284 330" fill="none" '
                f'stroke="{RED}" stroke-width="2.6"/>')
    body.append(f'<path d="M 132 290 C 120 240, 200 232, 232 288" fill="none" '
                f'stroke="{BLUE}" stroke-width="2.6"/>')
    body.append(f'<path d="M 176 288 C 190 236, 260 244, 252 330" fill="none" '
                f'stroke="{GREEN}" stroke-width="2.6"/>')
    body.append(rough_rect(244, 288, 84, 42, "26-scope", fill=SURFACE, stroke=INK, sw=2.6))
    body.append(line([(252, 316), (266, 304), (278, 320), (292, 300), (306, 312),
                      (320, 304)], "26-wave", stroke=TEAL, sw=2.2))
    # 中：门槛 + 门柱 + 图纸卷
    body.append(rough_rect(430, 210, 26, 270, "26-post1", fill=SURFACE, stroke=INK, sw=3.4))
    body.append(rough_rect(606, 210, 26, 270, "26-post2", fill=SURFACE, stroke=INK, sw=3.4))
    body.append(rough_rect(420, 186, 222, 30, "26-lintel", fill=SURFACE, stroke=INK, sw=3.4))
    body.append(rough_rect(416, 470, 234, 22, "26-sill", fill=SURFACE, stroke=INK, sw=3.4))
    body.append(f'<g transform="rotate(-14 560 430)">'
                f'{rough_rect(516, 414, 92, 30, "26-roll", fill=PAPER, stroke=INK, sw=2.6)}'
                f'</g>')
    body.append(line([(524, 428), (600, 428)], "26-roll-l1", stroke=BLUE, sw=1.8))
    body.append(line([(528, 438), (596, 438)], "26-roll-l2", stroke=BLUE, sw=1.8))
    body.append(line([(608, 428), (628, 428)], "26-roll-t", sw=2.4))
    # 右：传送带 + 成品盒 + 质检章（吊杆 visibly 悬挂）
    body.append(line([(700, 420), (916, 420)], "26-belt1", sw=4))
    body.append(line([(700, 452), (916, 452)], "26-belt2", sw=4))
    for x in range(712, 916, 34):
        body.append(f'<circle cx="{x}" cy="436" r="8" fill="{SURFACE}" '
                    f'stroke="{INK}" stroke-width="2.4"/>')
    body.append(rough_rect(770, 366, 84, 54, "26-box", fill=MINT, stroke=INK, sw=2.8))
    body.append(line([(770, 384), (854, 384)], "26-box-t1", stroke=INK, sw=2))
    body.append(line([(812, 366), (812, 420)], "26-box-t2", stroke=INK, sw=2))
    body.append(line([(866, 304), (866, 250), (900, 250)], "26-mount", sw=3))
    body.append(f'<circle cx="866" cy="330" r="26" fill="{YELLOW}" stroke="{INK}" '
                f'stroke-width="3"/>')
    body.append(f'<circle cx="866" cy="330" r="15" fill="none" stroke="{RED}" '
                f'stroke-width="2.4"/>')
    # 跨门槛的工程师
    body.append(person(500, 468, 1.2, "stand", "26-p"))
    return svg_doc(
        "原型跨过一道上锁的门槛才成为产品",
        "左侧工作台上面包板插着孔阵，红蓝绿三根飞线垂到桌沿，示波器亮着波形；"
        "中间高门槛的门柱间横着门楣，门槛上斜放一卷图纸；一名工程师正抬腿跨过，"
        "右侧传送带托着成品盒，上方悬挂一枚质检圆章。无文字无数字。",
        "\n  ".join(body))


FIGURES = {
    "02-six-jobs-map.svg": fig_02_six_jobs,
    "08-second-protection.svg": fig_08_second_protection,
    "09-differential-price-tag.svg": fig_09_price_tag,
    "10-model-stunt-double.svg": fig_10_model_stunt,
    "15-soh-two-faces.svg": fig_15_soh_two_faces,
    "16-two-clocks.svg": fig_16_two_clocks,
    "17-diagnosis-no-truth.svg": fig_17_no_truth,
    "19-tower-routes.svg": fig_19_tower_routes,
    "22-open-architecture.svg": fig_22_open_stack,
    "24-ai-in-loop.svg": fig_24_ai_in_loop,
    "26-threshold-gate.svg": fig_26_threshold_gate,
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
