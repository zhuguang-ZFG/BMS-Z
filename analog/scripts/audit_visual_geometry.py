#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""视觉几何审计：文字出画布 / 文字互压 / 文字越界面框 / 文字压曲线。

解析用 ElementTree。`transform` 按 translate/rotate/scale/matrix 合成仿射矩阵，
字框四角变换后取轴对齐外包框，所以竖排（`rotate(-90 ...)`）的轴标签也量得准。
`font-size` 与 `text-anchor` 沿祖先 `<g>` 继承——手绘图大量把字号写在外层组上，
按元素自身属性取默认值会把字号估大近一倍，凭空报出一片「出画布」。
文字宽度按 CJK 1.0 em、其余 0.55 em 粗估，所以报告是「提示」不是结论：
真压字一定会被这里点到，但点到不一定是真压字，最终以人眼与审图为准。

面板口径：宽 ≥40、高 ≥44 的 `<rect>` 才算面板（更扁的是进度条与分隔带，
标签本来就在条外）。完整落在某个框内的文字属于那个框，不再对它报越界。

三个资产目录各有一套检查口径（`DIRS`）：
  assets/figures-v2  静态合成图，四项全查；
  assets/figures     静态手绘图，四项全查；
  assets/svg         SMIL 动画图，**只查出画布**——分节拍出现的文字在时间轴上
                     并不共存，互压与越界面板会整片误报。

用法：
  python scripts/audit_visual_geometry.py                # 审计三个目录全部资产
  python scripts/audit_visual_geometry.py id1 id2 ...    # 只审计指定图（裸 id 按
                                                         # figures-v2→figures→svg 找）
  python scripts/audit_visual_geometry.py --dir svg      # 只审计某个目录
退出码：0 报告模式；`--gate` 时有缺陷返回 1。
"""
from __future__ import annotations

import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# name -> (目录, 是否 SMIL 动画图)。动画图只查出画布，见模块文档。
DIRS = {
    'figures-v2': (ROOT / 'assets' / 'figures-v2', False),
    'figures': (ROOT / 'assets' / 'figures', False),
    'svg': (ROOT / 'assets' / 'svg', True),
}
FULLWIDTH = '，。、；：（）「」“”？！℃'
# 楷体把这些符号按近似全角出：按 0.55 em 算会低估右边界，实测会漏掉真溢出。
WIDE_SYM = 'Ωµ°±×÷≈≤≥→←↑↓−–—…∥τβθπΔ①②③④⑤'



def width_cjk(value: str, size: float) -> float:
    """粗估文字宽度：CJK/全角 1.0 em，楷体宽符号 0.9 em，其余 0.55 em。"""
    total = 0.0
    for ch in value:
        if '\u4e00' <= ch <= '\u9fff' or ch in FULLWIDTH:
            total += 1.0
        elif ch in WIDE_SYM:
            total += 0.9
        else:
            total += 0.55
    return total * size


def span(x: float, y: float, value: str, size: float, anchor: str) -> tuple:
    w = width_cjk(value, size)
    if anchor == 'middle':
        x0 = x - w / 2
    elif anchor == 'end':
        x0 = x - w
    else:
        x0 = x
    return (x0, y - size * 0.76, x0 + w, y + size * 0.20)


def parse_transform(value: str):
    """把一串 transform 合成仿射矩阵 (a, b, c, d, e, f)，按 SVG 从左到右相乘。

    只处理本仓用到的 translate/rotate/scale/matrix；其余（skew 等）忽略。
    """
    mat = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

    def mul(m, n):
        a1, b1, c1, d1, e1, f1 = m
        a2, b2, c2, d2, e2, f2 = n
        return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
                a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
                a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)

    for name, body in re.findall(r'(translate|rotate|scale|matrix)\s*\(([^)]*)\)', value or ''):
        nums = [float(n) for n in re.findall(r'-?[\d.]+(?:e-?\d+)?', body)]
        if name == 'translate' and nums:
            mat = mul(mat, (1.0, 0.0, 0.0, 1.0, nums[0], nums[1] if len(nums) > 1 else 0.0))
        elif name == 'rotate' and nums:
            ang = math.radians(nums[0])
            cos, sin = math.cos(ang), math.sin(ang)
            rot = (cos, sin, -sin, cos, 0.0, 0.0)
            if len(nums) >= 3:                       # rotate(a cx cy) = T(c)·R·T(−c)
                cx, cy = nums[1], nums[2]
                rot = mul(mul((1.0, 0.0, 0.0, 1.0, cx, cy), rot),
                          (1.0, 0.0, 0.0, 1.0, -cx, -cy))
            mat = mul(mat, rot)
        elif name == 'scale' and nums:
            sx = nums[0]
            sy = nums[1] if len(nums) > 1 else sx
            mat = mul(mat, (sx, 0.0, 0.0, sy, 0.0, 0.0))
        elif name == 'matrix' and len(nums) >= 6:
            mat = mul(mat, tuple(nums[:6]))
    return mat


def apply_mat(mat, x: float, y: float):
    a, b, c, d, e, f = mat
    return (a * x + c * y + e, b * x + d * y + f)


def aabb(mat, box: tuple) -> tuple:
    """把字框四角按矩阵变换后取轴对齐外包框：旋转文字也能量准。"""
    x0, y0, x1, y1 = box
    pts = [apply_mat(mat, px, py)
           for px, py in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def collect(path: Path):
    """返回 (canvas, texts, panels, polys)，坐标已按祖先 transform 链变换。

    `font-size`/`text-anchor` 会沿祖先继承——图里大量文字把字号写在外层 `<g>` 上，
    按元素自身属性取默认值会把字号估大一倍，凭空报出一片「出画布」。
    """
    tree = ET.parse(path)
    root = tree.getroot()
    vb = root.get('viewBox', '0 0 1000 700').split()
    canvas = (float(vb[2]), float(vb[3]))
    parent = {c: p for p in root.iter() for c in p}
    texts, panels, polys = [], [], []

    def chain(el):
        """从根到 el 的祖先链（含自身）。"""
        out, node = [], el
        while True:
            out.append(node)
            if node not in parent:
                break
            node = parent[node]
        return list(reversed(out))

    def matrix_of(el):
        mat = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        a1, b1, c1, d1, e1, f1 = mat
        for node in chain(el):
            t = node.get('transform')
            if not t:
                continue
            n = parse_transform(t)
            a2, b2, c2, d2, e2, f2 = n
            mat = (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
                   a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
                   a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)
            a1, b1, c1, d1, e1, f1 = mat
        return mat

    def inherited(el, attr, default):
        for node in reversed(chain(el)):
            got = node.get(attr)
            if got:
                return got
        return default

    for el in root.iter():
        tag = el.tag.split('}')[-1]
        mat = matrix_of(el)
        if tag == 'text':
            try:
                size = float(str(inherited(el, 'font-size', '22')).replace('px', ''))
            except ValueError:
                size = 22.0
            x, y = float(el.get('x', 0)), float(el.get('y', 0))
            value = ''.join(el.itertext()).strip()
            if not value:
                continue
            anchor = inherited(el, 'text-anchor', 'start')
            local = span(x, y, value, size, anchor)
            texts.append({'value': value, 'box': aabb(mat, local),
                          'local': local, 'mat': mat})
        elif tag == 'rect':
            w, h = float(el.get('width', 0)), float(el.get('height', 0))
            if w >= 40 and h >= 44:          # 细条是进度条/分隔带，不是面板
                x, y = float(el.get('x', 0)), float(el.get('y', 0))
                bx0, by0, bx1, by1 = aabb(mat, (x, y, x + w, y + h))
                panels.append((bx0, by0, bx1 - bx0, by1 - by0))
        elif tag == 'polyline':
            pts = []
            for pair in (el.get('points') or '').split():
                if ',' in pair:
                    a, b = pair.split(',')[:2]
                    pts.append(apply_mat(mat, float(a), float(b)))
            if len(pts) >= 2:
                polys.append(pts)
    return canvas, texts, panels, polys


def audit(path: Path, animated: bool = False) -> list:
    """审计一张图。`animated=True` 只查出画布：分节拍的文字在时间轴上不共存。"""
    canvas, texts, panels, polys = collect(path)
    defects = []

    def contained(t, p):
        px, py, pw, ph = p
        x0, y0, x1, y1 = t['box']
        return px <= x0 and x1 <= px + pw and py <= y0 and y1 <= py + ph

    for t in texts:
        x0, y0, x1, y1 = t['box']
        if x0 < -1 or y0 < -1 or x1 > canvas[0] + 1 or y1 > canvas[1] + 1:
            defects.append(f'出画布 {t["value"][:22]!r} 右缘={x1:.0f} 画布={canvas[0]:.0f}')

    if animated:
        return defects

    def same_mat(m, n) -> bool:
        return all(abs(p - q) < 1e-9 for p, q in zip(m, n))

    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            # 同一变换下的两段文字按局部坐标比。仿射变换可逆，局部不压则变换后也不压；
            # 而旋转后的轴对齐外包框只是真字框的超集：164px 宽的斜排文字被量高
            # 164·sin5° ≈ 14px，足以把 24px 的正常行距报成「互压 7px」。
            if same_mat(texts[i]['mat'], texts[j]['mat']):
                a, b = texts[i]['local'], texts[j]['local']
            else:
                a, b = texts[i]['box'], texts[j]['box']
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > 2 and oy > 2:
                defects.append(f'文字互压 {texts[i]["value"][:16]!r} × {texts[j]["value"][:16]!r} '
                               f'交叠 {ox:.0f}×{oy:.0f}')

    for t in texts:
        # 完整落在某个框内的文字属于那个框（子框骑跨父面板是刻意构图）。
        if any(contained(t, p) for p in panels):
            continue
        x0, y0, x1, y1 = t['box']
        for px, py, pw, ph in panels:
            ox = min(x1, px + pw) - max(x0, px)
            oy = min(y1, py + ph) - max(y0, py)
            if ox > 2 and oy > 2:
                defects.append(
                    f'越界面板 {t["value"][:18]!r} 面板=({px:.0f},{py:.0f},{pw:.0f},{ph:.0f})'
                    f' 文字右缘={x1:.0f} 面板右缘={px + pw:.0f}')
    # 文字压曲线：字框内缩 4px 后仍被折线穿过，才算真压（贴边不算）。
    for t in texts:
        x0, y0, x1, y1 = t['box']
        ix0, iy0, ix1, iy1 = x0 + 4, y0 + 4, x1 - 4, y1 - 4
        if ix1 <= ix0 or iy1 <= iy0:
            continue
        for pts in polys:
            hit = False
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                steps = max(2, int(max(abs(bx - ax), abs(by - ay)) / 4))
                for s in range(steps + 1):
                    px = ax + (bx - ax) * s / steps
                    py = ay + (by - ay) * s / steps
                    if ix0 <= px <= ix1 and iy0 <= py <= iy1:
                        hit = True
                        break
                if hit:
                    break
            if hit:
                defects.append(f'文字压曲线 {t["value"][:20]!r} 字框=({x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f})')
                break

    return defects


def resolve(name: str):
    """裸 id 按 figures-v2 → figures → svg 顺序找；返回 (标签, 路径, 是否动画)。"""
    for key, (folder, animated) in DIRS.items():
        candidate = folder / f'{name}.svg'
        if candidate.exists():
            return f'{key}/{name}', candidate, animated
    raise SystemExit(f'找不到资产：{name}（已查 {"、".join(DIRS)}）')


def main() -> int:
    args = sys.argv[1:]
    names = [a for a in args if not a.startswith('--')]
    gate = '--gate' in args
    only = None
    for a in args:
        if a.startswith('--dir='):
            only = a.split('=', 1)[1]
        elif a == '--dir':
            only = args[args.index(a) + 1] if args.index(a) + 1 < len(args) else None
    if only:
        names = [n for n in names if n != only]
        if only not in DIRS:
            raise SystemExit(f'--dir 取值须是 {"、".join(DIRS)} 之一，收到 {only!r}')

    if names:
        targets = [resolve(n) for n in names]
    else:
        targets = []
        for key, (folder, animated) in DIRS.items():
            if only and key != only:
                continue
            for p in sorted(folder.glob('*.svg')):
                if p.stem.endswith('-print'):
                    continue          # 印刷副本与屏幕版同源，审一次即可
                targets.append((f'{key}/{p.stem}', p, animated))

    bad = 0
    for label, path, animated in targets:
        d = audit(path, animated)
        if d:
            bad += 1
            print(f'FAIL {label}')
            for line in d:
                print('   ', line)
        else:
            print(f'ok   {label}')
    print(f'\n审计 {len(targets)} 张，有缺陷 {bad} 张')
    return 1 if (bad and gate) else 0


if __name__ == '__main__':
    raise SystemExit(main())
