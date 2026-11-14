"""章徽/篇题手绘化一遍：把几何完美的线描转成带钢笔起落的线描。

章徽（ch*.svg，64×64、currentColor 单色）：
- 描边 <circle>（r≥3.5）→ 随机起笔角的 12 折线微抖圆，闭合后多走 ~25° 压笔回锋；
- 描边 <rect> → 周长路径，长边中点垂直微抖，rx 圆角保留为二次曲线，起笔角轻过冲；
- <path> 直线段（长度≥6）中点垂直微抖，≥18 两次细分；曲线控制点微抖，
  端点不动（保拓扑与接头）；fill="currentColor" 的实心点不动；
- 主轮廓（面积/复杂度最大的描边形状）追加一笔速写复笔：同一结构参数重新抖动
  重画（起笔角/过冲一致、噪声各异），透明度 .3、笔宽 1.4，是钢笔复勾的痕迹。

篇题（part-*.svg，720×240 图版）：美术方向「纸是印的、墨是画的」——
- <g> 组属性向子元素继承后判定：#94a3b8 灰蓝描边（网格/外框/坐标轴/刻度）与
  印刷感低透明纹理不动，<text> 不动，实心标记点不动；
- 三色墨线（#14213d/#176b73/#f2b84b）按章徽同法手绘化，振幅按画布放大；
- 中小图形（圆 6≤r<12、矩形 400≤面积<2000）只错位重摆以省字节；
- 主轮廓复笔紧跟原元素之后插入（保持叠印次序）；
- 字节分档降级：全配 → 撤复笔 → 加大 min_seg，直到 ≤6000 字节。

契约不变式（book_art.validate_svg）：单根 <svg>+viewBox、章徽只用 currentColor、
无 <text>（章徽）/id=/href=/url(、≤6000 字节。脚本末尾逐枚自检。
确定性：种子 = 文件名干，同一输入重跑结果一致。
注意：一次性变换——不要对已手绘化的文件再跑（抖动会叠加）；
排线（稀疏短笔触）在变换后由人工逐版补画，不在本脚本职责内。

用法：python sketch_pass.py            # 原地手绘化 assets/emblems/ch*.svg
      python sketch_pass.py --parts    # 原地手绘化 assets/emblems/part-*.svg
      加 --dry-run                     # 只打印每枚前后字节数，不写文件
"""

from __future__ import annotations

import hashlib
import math
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EMBLEM_DIR = ROOT / "assets" / "emblems"

JITTER_LINE = 1.0  # 直线中点垂直抖动（64 viewBox 单位）
JITTER_CTRL = 0.8  # 曲线控制点抖动
CIRCLE_WOB = 0.05  # 圆半径调制幅度

ECHO_OPACITY = 0.3
MIN_SEG = 6.0  # 短于此的段不抖（箭头、刻度保持利落）
MAX_BYTES = 6000

TOKEN_RE = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?")


def fmt(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in {"-0", ""} else s


class Seg:
    def __init__(self, cmd: str, pts: list[float], end: tuple[float, float]):
        self.cmd = cmd  # 规范化后的绝对命令：M L C Q A Z
        self.pts = pts  # 绝对坐标参数
        self.end = end


def parse_path(d: str) -> list[Seg]:
    tokens = TOKEN_RE.findall(d)
    segs: list[Seg] = []
    i = 0
    cmd = ""
    x = y = 0.0  # 当前点
    sx = sy = 0.0  # 子路径起点
    px = py = 0.0  # 上一控制点（S/T 反射用）
    prev = ""

    def num() -> float:
        nonlocal i
        v = float(tokens[i])
        i += 1
        return v

    n_params = {
        "M": 2,
        "L": 2,
        "H": 1,
        "V": 1,
        "C": 6,
        "S": 4,
        "Q": 4,
        "T": 2,
        "A": 7,
        "Z": 0,
    }
    while i < len(tokens):
        t = tokens[i]
        if re.fullmatch(r"[A-Za-z]", t):
            cmd = t
            i += 1
            if cmd in "Zz":
                segs.append(Seg("Z", [], (sx, sy)))
                x, y = sx, sy
                prev = "Z"
                continue
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M" and segs and prev == "M":
            c, cmd = "L", "l" if rel else "L"  # 隐式 lineto
        n = n_params[c]
        vals = [num() for _ in range(n)]
        if c == "M" or c == "L":
            nx, ny = vals
            if rel:
                nx, ny = x + nx, y + ny
            segs.append(Seg(c, [nx, ny], (nx, ny)))
            x, y = nx, ny
            if c == "M":
                sx, sy = x, y
            px, py = x, y
        elif c == "H":
            nx = vals[0] + x if rel else vals[0]
            segs.append(Seg("L", [nx, y], (nx, y)))
            x = nx
            px, py = x, y
        elif c == "V":
            ny = vals[0] + y if rel else vals[0]
            segs.append(Seg("L", [x, ny], (x, ny)))
            y = ny
            px, py = x, y
        elif c == "C":
            x1, y1, x2, y2, nx, ny = vals
            if rel:
                x1, y1, x2, y2, nx, ny = x + x1, y + y1, x + x2, y + y2, x + nx, y + ny
            segs.append(Seg("C", [x1, y1, x2, y2, nx, ny], (nx, ny)))
            px, py = x2, y2
            x, y = nx, ny
        elif c == "S":
            x2, y2, nx, ny = vals
            if rel:
                x2, y2, nx, ny = x + x2, y + y2, x + nx, y + ny
            x1, y1 = (2 * x - px, 2 * y - py) if prev in {"C", "S"} else (x, y)
            segs.append(Seg("C", [x1, y1, x2, y2, nx, ny], (nx, ny)))
            px, py = x2, y2
            x, y = nx, ny
        elif c == "Q":
            x1, y1, nx, ny = vals
            if rel:
                x1, y1, nx, ny = x + x1, y + y1, x + nx, y + ny
            segs.append(Seg("Q", [x1, y1, nx, ny], (nx, ny)))
            px, py = x1, y1
            x, y = nx, ny
        elif c == "T":
            nx, ny = vals
            if rel:
                nx, ny = x + nx, y + ny
            x1, y1 = (2 * x - px, 2 * y - py) if prev in {"Q", "T"} else (x, y)
            segs.append(Seg("Q", [x1, y1, nx, ny], (nx, ny)))
            px, py = x1, y1
            x, y = nx, ny
        elif c == "A":
            rx, ry, rot, laf, sf, nx, ny = vals
            if rel:
                nx, ny = x + nx, y + ny
            segs.append(Seg("A", [rx, ry, rot, laf, sf, nx, ny], (nx, ny)))
            x, y = nx, ny
            px, py = x, y
        prev = c if c != "M" else "M"
    return segs


def sketch_segs(
    segs: list[Seg],
    rng: random.Random,
    jline: float = JITTER_LINE,
    jctrl: float = JITTER_CTRL,
    min_seg: float = MIN_SEG,
) -> list[str]:
    """抖动后的绝对命令 d 片段列表。"""
    out: list[str] = []
    cur = (0.0, 0.0)
    for s in segs:
        if s.cmd == "Z":
            out.append("Z")
            continue
        if s.cmd == "M":
            out.append(f"M{fmt(s.pts[0])} {fmt(s.pts[1])}")
            cur = s.end
            continue
        if s.cmd == "L":
            x0, y0 = cur
            x1, y1 = s.end
            length = math.hypot(x1 - x0, y1 - y0)
            if length >= min_seg:
                # 垂直方向微抖；≥3×min_seg 细分两次
                nx, ny = (-(y1 - y0) / length, (x1 - x0) / length)
                cuts = [0.5] if length < 3 * min_seg else [1 / 3, 2 / 3]
                pts = []
                for t in cuts:
                    off = rng.uniform(-jline, jline)
                    pts.append(
                        (x0 + (x1 - x0) * t + nx * off, y0 + (y1 - y0) * t + ny * off)
                    )
                for px_, py_ in pts:
                    out.append(f"L{fmt(px_)} {fmt(py_)}")
            out.append(f"L{fmt(x1)} {fmt(y1)}")
            cur = s.end
        elif s.cmd == "C":
            x1, y1, x2, y2, x3, y3 = s.pts
            if math.hypot(x3 - cur[0], y3 - cur[1]) >= min_seg:
                x1 += rng.uniform(-jctrl, jctrl)
                y1 += rng.uniform(-jctrl, jctrl)
                x2 += rng.uniform(-jctrl, jctrl)
                y2 += rng.uniform(-jctrl, jctrl)
            out.append(f"C{fmt(x1)} {fmt(y1)} {fmt(x2)} {fmt(y2)} {fmt(x3)} {fmt(y3)}")
            cur = s.end
        elif s.cmd == "Q":
            x1, y1, x2, y2 = s.pts
            if math.hypot(x2 - cur[0], y2 - cur[1]) >= min_seg:
                x1 += rng.uniform(-jctrl, jctrl)
                y1 += rng.uniform(-jctrl, jctrl)
            out.append(f"Q{fmt(x1)} {fmt(y1)} {fmt(x2)} {fmt(y2)}")
            cur = s.end
        elif s.cmd == "A":
            rx, ry, rot, laf, sf, x1, y1 = s.pts
            rx *= 1 + rng.uniform(-0.02, 0.02)
            ry *= 1 + rng.uniform(-0.02, 0.02)
            out.append(
                f"A{fmt(rx)} {fmt(ry)} {fmt(rot)} {int(laf)} {int(sf)} {fmt(x1)} {fmt(y1)}"
            )
            cur = s.end
    return out


def wobbly_circle(
    cx: float,
    cy: float,
    r: float,
    rng: random.Random,
    base: float | None = None,
    phase: float | None = None,
    wob: float = CIRCLE_WOB,
) -> tuple[str, float, float]:
    """手绘圆：随机起笔角，12 折线微抖，整圈闭合后再多走 ~25° 压笔回锋。

    返回 (d, base, phase)：复笔用同一 base/phase 重画，两条线起落一致、抖动各异。
    """
    if base is None:
        base = rng.uniform(0, math.pi * 2)
    if phase is None:
        phase = rng.uniform(0, math.pi * 2)
    pts = []
    steps = 12
    for k in range(steps + 2):
        if k <= steps:
            theta = base + 2 * math.pi * k / steps
        else:
            theta = base + 2 * math.pi + math.radians(25)
        wob_r = (
            1
            + wob
            * (
                0.6 * math.sin(2 * theta + phase)
                + 0.4 * math.sin(5 * theta + 2 * phase)
            )
            + rng.uniform(-0.01, 0.01)
        )
        pts.append((cx + r * wob_r * math.cos(theta), cy + r * wob_r * math.sin(theta)))
    d = [f"M{fmt(pts[0][0])} {fmt(pts[0][1])}"]
    d += [f"L{fmt(px)} {fmt(py)}" for px, py in pts[1:]]
    return "".join(d), base, phase


def wobbly_rect(
    x: float,
    y: float,
    w: float,
    h: float,
    rx: float,
    rng: random.Random,
    ov: float | None = None,
    jline: float = JITTER_LINE,
    min_seg: float = MIN_SEG,
) -> tuple[str, float]:
    """手绘圆角矩形：四边中点微抖，圆角用二次曲线，起点角轻微过冲。

    返回 (d, ov)：复笔沿用同一过冲量，两笔在同一个角起收。
    """
    rx = min(rx, w / 2, h / 2)
    if ov is None:
        ov = rng.uniform(0.4, 0.9)

    def edge(x0, y0, x1, y1):
        length = math.hypot(x1 - x0, y1 - y0)
        if length < min_seg:
            return f"L{fmt(x1)} {fmt(y1)}"
        nx, ny = (-(y1 - y0) / length, (x1 - x0) / length)
        off = rng.uniform(-jline, jline)
        mx, my = (x0 + x1) / 2 + nx * off, (y0 + y1) / 2 + ny * off
        return f"L{fmt(mx)} {fmt(my)}L{fmt(x1)} {fmt(y1)}"

    d = [f"M{fmt(x - ov)} {fmt(y + rx)}"]
    d.append(f"Q{fmt(x)} {fmt(y)} {fmt(x + rx)} {fmt(y)}")
    d.append(edge(x + rx, y, x + w - rx, y))
    d.append(f"Q{fmt(x + w)} {fmt(y)} {fmt(x + w)} {fmt(y + rx)}")
    d.append(edge(x + w, y + rx, x + w, y + h - rx))
    d.append(f"Q{fmt(x + w)} {fmt(y + h)} {fmt(x + w - rx)} {fmt(y + h)}")
    d.append(edge(x + w - rx, y + h, x + rx, y + h))
    d.append(f"Q{fmt(x)} {fmt(y + h)} {fmt(x)} {fmt(y + h - rx)}")
    d.append(f"L{fmt(x)} {fmt(y + rx - ov * 0.6)}")
    return "".join(d), ov


TAG_RE = re.compile(r"<(rect|circle|path)\b[^>]*>", re.I)
ATTR_RE = re.compile(r'([\w-]+)\s*=\s*"([^"]*)"')


def attrs_of(tag: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in ATTR_RE.finditer(tag)}


def sketch_file(svg: str, stem: str) -> str:
    rng = random.Random(hashlib.sha1(stem.encode()).hexdigest())
    pieces: list[str] = []
    last = 0
    hero_area = 0.0
    hero_redraw = None  # 主轮廓复笔：同一结构参数、新鲜抖动的重画闭包
    for m in TAG_RE.finditer(svg):
        pieces.append(svg[last : m.start()])
        tag = m.group(0)
        kind = m.group(1).lower()
        at = attrs_of(tag)
        filled = at.get("fill", "").strip() == "currentColor"
        new_tag = tag
        if kind == "circle" and not filled:
            cx, cy, r = float(at["cx"]), float(at["cy"]), float(at["r"])
            if r >= 3.5:
                d, base, phase = wobbly_circle(cx, cy, r, rng)
                keep = {k: v for k, v in at.items() if k not in {"cx", "cy", "r"}}
                attr_s = "".join(f' {k}="{v}"' for k, v in keep.items())
                new_tag = f'<path d="{d}"{attr_s}/>'
                if r >= 9 and r * r > hero_area:
                    hero_area = r * r

                    def hero_redraw(cx=cx, cy=cy, r=r, base=base, phase=phase):
                        return wobbly_circle(cx, cy, r, rng, base, phase)[0]
        elif kind == "rect" and not filled:
            x, y = float(at.get("x", 0)), float(at.get("y", 0))
            w, h = float(at["width"]), float(at["height"])
            rxv = float(at.get("rx", 0) or 0)
            d, ov = wobbly_rect(x, y, w, h, rxv, rng)
            keep = {
                k: v
                for k, v in at.items()
                if k not in {"x", "y", "width", "height", "rx"}
            }
            attr_s = "".join(f' {k}="{v}"' for k, v in keep.items())
            new_tag = f'<path d="{d}"{attr_s}/>'
            if min(w, h) >= 18 and w * h > hero_area:
                hero_area = w * h

                def hero_redraw(x=x, y=y, w=w, h=h, rxv=rxv, ov=ov):
                    return wobbly_rect(x, y, w, h, rxv, rng, ov)[0]
        elif kind == "path" and not filled:
            d = at.get("d", "")
            if d:
                segs = parse_path(d)
                d2 = "".join(sketch_segs(segs, rng))
                keep = {k: v for k, v in at.items() if k != "d"}
                attr_s = "".join(f' {k}="{v}"' for k, v in keep.items())
                new_tag = f'<path d="{d2}"{attr_s}/>'
                # 主轮廓路径：足够长、无 opacity（一级描边），以 d 长度作复杂度代理
                if "opacity" not in at and len(d2) > hero_area and len(d2) > 60:
                    hero_area = float(len(d2))

                    def hero_redraw(segs=segs):
                        return "".join(sketch_segs(segs, rng))

        pieces.append(new_tag)
        last = m.end()
    pieces.append(svg[last:])
    out = "".join(pieces)
    if hero_redraw:
        echo_d = hero_redraw()
        echo = f'<path d="{echo_d}" opacity="{ECHO_OPACITY}" stroke-width="1.4"/>'
        out = out.replace("</svg>", echo + "</svg>")
    return out


# ---- 篇题（720×240 图版）模式 ----
# 美术方向：纸是印的（#94a3b8 灰蓝网格/边框/刻度不动），墨是画的（三色墨线手绘化）。
PART_JLINE = 1.1
PART_JCTRL = 0.9
PART_WOB = 0.04
PART_MIN_SEG = 10.0
PART_ECHO_OPACITY = 0.25
PAPER_STROKE = "#94a3b8"


G_RE = re.compile(r"<g\b[^>]*>|</g\s*>", re.I)


def _walk_shapes(svg: str):
    """按文档序产出 (match, 合并后属性)：跟踪 <g> 栈，组属性向子元素继承。"""
    events = []
    for m in TAG_RE.finditer(svg):
        events.append((m.start(), "shape", m))
    for m in G_RE.finditer(svg):
        events.append((m.start(), "g", m))
    events.sort(key=lambda e: e[0])
    stack: list[dict[str, str]] = []
    for _, kind, m in events:
        if kind == "g":
            if m.group(0).startswith("</"):
                if stack:
                    stack.pop()
            else:
                stack.append(attrs_of(m.group(0)))
            continue
        merged: dict[str, str] = {}
        for g_attrs in stack:
            merged.update(g_attrs)
        merged.update(attrs_of(m.group(0)))
        yield m, merged


def _is_paper(at: dict[str, str]) -> bool:
    """灰蓝描边（含 <g> 继承）视为印刷纸纹：网格、外框、角刻度、坐标轴。"""
    stroke = at.get("stroke", "").lower()
    if stroke == PAPER_STROKE:
        return True
    opacity = at.get("stroke-opacity", at.get("opacity", "1"))
    try:
        return stroke == "" and float(opacity) <= 0.2
    except ValueError:
        return False


def _filled_shape(at: dict[str, str]) -> bool:
    fill = at.get("fill", "").strip().lower()
    stroke = at.get("stroke", "").strip().lower()
    return fill not in {"", "none"} and stroke in {"", "none"}


def sketch_part(
    svg: str,
    stem: str,
    allow_echo: bool = True,
    min_seg: float = PART_MIN_SEG,
    jline: float = PART_JLINE,
) -> str:
    """篇题图版手绘化：只动三色墨线，纸纹与文字保持印刷感。"""
    rng = random.Random(hashlib.sha1(("part:" + stem).encode()).hexdigest())
    pieces: list[str] = []
    last = 0
    hero_score = 0.0
    hero_redraw = None
    hero_attrs = ""
    echo_at = -1  # 复笔插入点（紧跟主轮廓之后，保持叠印次序）
    for m, merged in _walk_shapes(svg):
        pieces.append(svg[last : m.start()])
        tag = m.group(0)
        kind = m.group(1).lower()
        at = attrs_of(tag)  # 元素自身属性：重建标签时只带这些（继承靠留在原组内）
        new_tag = tag
        skip = _is_paper(merged) or _filled_shape(merged)
        if not skip and kind == "circle":
            cx, cy, r = float(at["cx"]), float(at["cy"]), float(at["r"])
            if r >= 12:
                d, base, phase = wobbly_circle(cx, cy, r, rng, wob=PART_WOB)
                keep = {k: v for k, v in at.items() if k not in {"cx", "cy", "r"}}
                attr_s = "".join(f' {k}="{v}"' for k, v in keep.items())
                new_tag = f'<path d="{d}"{attr_s}/>'
                if r * r > hero_score:
                    hero_score = r * r
                    hero_attrs = attr_s

                    def hero_redraw(cx=cx, cy=cy, r=r, base=base, phase=phase):
                        return wobbly_circle(cx, cy, r, rng, base, phase, wob=PART_WOB)[
                            0
                        ]

                    echo_at = len(pieces)  # 本元素之后
            elif r >= 6:
                # 小圆：只挪圆心、微调半径——手摆感，字节近零成本
                cx2 = cx + rng.uniform(-0.6, 0.6)
                cy2 = cy + rng.uniform(-0.6, 0.6)
                r2 = r * (1 + rng.uniform(-0.03, 0.03))
                keep = {k: v for k, v in at.items() if k not in {"cx", "cy", "r"}}
                attr_s = "".join(f' {k}="{v}"' for k, v in keep.items())
                new_tag = (
                    f'<circle cx="{fmt(cx2)}" cy="{fmt(cy2)}" r="{fmt(r2)}"{attr_s}/>'
                )

        elif not skip and kind == "rect":
            x, y = float(at.get("x", 0)), float(at.get("y", 0))
            w, h = float(at["width"]), float(at["height"])
            rxv = float(at.get("rx", 0) or 0)
            if w * h >= 2000:  # 中大矩形整周手绘化
                d, ov = wobbly_rect(x, y, w, h, rxv, rng, jline=jline, min_seg=min_seg)
                keep = {
                    k: v
                    for k, v in at.items()
                    if k not in {"x", "y", "width", "height", "rx"}
                }
                attr_s = "".join(f' {k}="{v}"' for k, v in keep.items())
                new_tag = f'<path d="{d}"{attr_s}/>'
                if w * h > hero_score:
                    hero_score = w * h
                    hero_attrs = attr_s

                    def hero_redraw(x=x, y=y, w=w, h=h, rxv=rxv, ov=ov):
                        return wobbly_rect(
                            x, y, w, h, rxv, rng, ov, jline=jline, min_seg=min_seg
                        )[0]

                    echo_at = len(pieces)
            elif w * h >= 400:
                # 小矩形：错位重摆，保持 <rect> 元素以省字节
                x2 = x + rng.uniform(-0.6, 0.6)
                y2 = y + rng.uniform(-0.6, 0.6)
                keep = {k: v for k, v in at.items() if k not in {"x", "y"}}
                attr_s = "".join(f' {k}="{v}"' for k, v in keep.items())
                new_tag = f'<rect x="{fmt(x2)}" y="{fmt(y2)}"{attr_s}/>'
        elif not skip and kind == "path":
            d = at.get("d", "")
            if d and d.count("M") <= 6:  # 多段纹理（网格等）不动
                segs = parse_path(d)
                d2 = "".join(
                    sketch_segs(
                        segs, rng, jline=jline, jctrl=PART_JCTRL, min_seg=min_seg
                    )
                )
                keep = {k: v for k, v in at.items() if k != "d"}
                attr_s = "".join(f' {k}="{v}"' for k, v in keep.items())
                new_tag = f'<path d="{d2}"{attr_s}/>'
                if (
                    "opacity" not in at
                    and "stroke-dasharray" not in at
                    and len(d2) > hero_score
                    and len(d2) > 80
                ):
                    hero_score = float(len(d2))
                    hero_attrs = attr_s

                    def hero_redraw(segs=segs):
                        return "".join(
                            sketch_segs(
                                segs,
                                rng,
                                jline=jline,
                                jctrl=PART_JCTRL,
                                min_seg=min_seg,
                            )
                        )

                    echo_at = len(pieces)
        pieces.append(new_tag)
        last = m.end()
    pieces.append(svg[last:])
    if hero_redraw and echo_at >= 0 and allow_echo:
        echo_d = hero_redraw()
        # 复笔沿用主轮廓配色，只降不透明度、收细笔宽
        attrs = re.sub(r'stroke-width="[^"]*"', "", hero_attrs)
        echo = (
            f'<path d="{echo_d}"{attrs} opacity="{PART_ECHO_OPACITY}"'
            f' stroke-width="1.2"/>'
        )
        pieces.insert(echo_at + 1, echo)
    return "".join(pieces)


def main() -> int:
    dry = "--dry-run" in sys.argv
    parts_mode = "--parts" in sys.argv
    sys.path.insert(0, str(ROOT))
    from book_art import validate_svg  # noqa: E402

    glob_pat = "part-*.svg" if parts_mode else "ch*.svg"
    kind = "part" if parts_mode else "chapter"
    for path in sorted(EMBLEM_DIR.glob(glob_pat)):
        src = path.read_text(encoding="utf-8").strip()
        if parts_mode:
            # 字节分档：全配（复笔+细抖）→ 撤复笔 → 加大 min_seg 少细分
            out = None
            tiers = (
                dict(),
                dict(allow_echo=False),
                dict(allow_echo=False, min_seg=18.0),
                dict(allow_echo=False, min_seg=26.0, jline=0.9),
            )
            for tier, kw in enumerate(tiers):
                cand = sketch_part(src, path.stem, **kw)
                if len(cand.encode("utf-8")) <= MAX_BYTES:
                    out = cand
                    if tier:
                        print(f"  {path.name}: 降到第 {tier + 1} 档")
                    break
            if out is None:
                raise SystemExit(f"{path.name}: 四档后仍超 {MAX_BYTES}B 上限")
        else:
            out = sketch_file(src, path.stem)
        validate_svg(out, path.name, kind)
        size = len(out.encode("utf-8"))
        if size > MAX_BYTES:
            raise SystemExit(f"{path.name}: 变换后 {size}B 超上限")
        print(f"{path.name}: {len(src.encode())}B -> {size}B")
        if not dry:
            path.write_text(out, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
