#!/usr/bin/env python3
"""Validate docs/circuits/handraw/manifest.json against path-B contract."""
from __future__ import annotations

import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "docs" / "circuits" / "handraw" / "manifest.json"
REQUIRED = {
    "slug", "source_svg", "kp_id", "style", "colors",
    "frames", "export", "caption_ok", "bans_ok", "status",
}
ALLOWED_STYLE = {"FA-002", "FA-029"}
ALLOWED_STATUS = {"prompts_only", "rendered", "exported", "linked", "archived"}

# 帧几何门：只查「有没有画出画布」是抓不到压字/压线的——本批 ocv-rest-timeline 就栽在这里，
# 四条动画的帧在画布内，却把「静置时间 t（min，示意）」压在「I（放电，示意）」上，
# 还有电压标注的左端被 y 轴竖线从末位数字中间穿过去。纯视觉模型靠不住（限流时就用不了），
# 但这类缺陷是纯几何的，能由文本盒算出来，所以放到门里，别再靠人眼守。
CJK_MIN = 0x2E80  # 自此以上的码位按全角计；拉丁与数字按 0.55 全角宽估
SVG_NS = "{http://www.w3.org/2000/svg}"
INHERITED = ("font-size", "text-anchor", "transform")


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def _walk(elem, inherited: dict[str, str]):
    """按继承链遍历：font-size / text-anchor / transform 在 SVG 里是继承属性。

    早先按属性名在 <text> 自己身上找，落在 <g font-size="13"> 里的文本会被当成默认
    字号量宽——宽度系统性偏小，正是要抓的压字反而漏掉。
    """
    current = dict(inherited)
    for key in INHERITED:
        if elem.get(key) is not None:
            current[key] = elem.get(key)
    yield elem, current
    for child in elem:
        yield from _walk(child, current)


def _boxes_from_root(root) -> list[tuple[str, float, float, float, float]]:
    boxes: list[tuple[str, float, float, float, float]] = []
    for elem, inherited in _walk(root, {}):
        if _local(elem.tag) != "text":
            continue
        content = "".join(elem.itertext()).strip()
        if not content or elem.get("x") is None or elem.get("y") is None:
            continue
        try:
            x, y = float(elem.get("x")), float(elem.get("y"))
            size = float(inherited.get("font-size", 16))  # SVG 初始 font-size 是 16
        except ValueError:
            continue
        advance = sum(size if ord(ch) >= CJK_MIN else size * 0.55 for ch in content)
        anchor = inherited.get("text-anchor", "start")
        left = x - advance / 2 if anchor == "middle" else (x - advance if anchor == "end" else x)
        corners = [(left, y - size), (left + advance, y - size),
                   (left + advance, y + size * 0.25), (left, y + size * 0.25)]
        angle = cx = cy = 0.0
        for rot in re.finditer(r"rotate\(\s*(-?[\d.]+)(?:\s+(-?[\d.]+)\s+(-?[\d.]+))?\s*\)",
                               inherited.get("transform", "")):
            angle += float(rot.group(1))
            if rot.group(2):
                cx, cy = float(rot.group(2)), float(rot.group(3))
        if angle:
            rad = math.radians(angle)
            cos, sin = math.cos(rad), math.sin(rad)
            corners = [
                (cx + (px - cx) * cos - (py - cy) * sin, cy + (px - cx) * sin + (py - cy) * cos)
                for px, py in corners
            ]
        xs = [p[0] for p in corners]
        ys = [p[1] for p in corners]
        boxes.append((content, min(xs), max(xs), min(ys), max(ys)))
    return boxes


def _rules_from_root(root) -> list[tuple[float, float, float, float]]:
    """取出用作轴线的直线段，只保留够长的，避免把刻度齿当骨架线。"""
    rules = []
    for elem in root.iter():
        if _local(elem.tag) != "line":
            continue
        try:
            x1, y1, x2, y2 = (float(elem.get(k)) for k in ("x1", "y1", "x2", "y2"))
        except (TypeError, ValueError):
            continue
        if abs(x1 - x2) <= 2 and abs(y1 - y2) >= 60:  # 竖轴
            rules.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
        elif abs(y1 - y2) <= 2 and abs(x1 - x2) >= 60:  # 横轴
            rules.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
    return rules


def _path_segments(d: str) -> list[tuple[float, float, float, float]]:
    """把 path 的 d 拆成线段（M/L 直取，C 采样 8 段，Z 闭合）。

    曲线不查等于放过「标注压在曲线上」这一类——本批 f6 的 `0.05 °C/s` 标注离曲线
    只剩 2.4 px，就是靠肉眼才看见的。不支持的命令整段跳过，不猜。
    """
    toks = re.findall(r"[A-Za-z]|-?\d+(?:\.\d+)?", d)
    segs: list[tuple[float, float, float, float]] = []
    cur = start = None
    cmd = None
    i = 0
    while i < len(toks):
        tok = toks[i]
        if tok.isalpha():
            cmd = tok
            i += 1
            if cmd in "Zz" and cur and start:
                segs.append((cur[0], cur[1], start[0], start[1]))
                cur = start
            continue
        try:
            if cmd in ("M", "L"):
                x, y = float(toks[i]), float(toks[i + 1])
                i += 2
                if cur:
                    segs.append((cur[0], cur[1], x, y))
                else:
                    start = (x, y)
                if cmd == "M":
                    start = (x, y)
                    cmd = "L"
                cur = (x, y)
            elif cmd == "C":
                x1, y1, x2, y2, x, y = (float(v) for v in toks[i:i + 6])
                i += 6
                p0 = cur or (x1, y1)
                prev = p0
                for k in range(1, 9):
                    s = k / 8
                    bx = ((1 - s) ** 3 * p0[0] + 3 * (1 - s) ** 2 * s * x1
                          + 3 * (1 - s) * s * s * x2 + s ** 3 * x)
                    by = ((1 - s) ** 3 * p0[1] + 3 * (1 - s) ** 2 * s * y1
                          + 3 * (1 - s) * s * s * y2 + s ** 3 * y)
                    segs.append((prev[0], prev[1], bx, by))
                    prev = (bx, by)
                cur = (x, y)
            else:
                break
        except (IndexError, ValueError):
            break
    return segs


def _orient(ax, ay, bx, by, cx, cy) -> int:
    v = (by - ay) * (cx - bx) - (bx - ax) * (cy - by)
    return 0 if v == 0 else (1 if v > 0 else -1)


def _segments_cross(ax, ay, bx, by, cx, cy, dx, dy) -> bool:
    return (_orient(ax, ay, bx, by, cx, cy) != _orient(ax, ay, bx, by, dx, dy)
            and _orient(cx, cy, dx, dy, ax, ay) != _orient(cx, cy, dx, dy, bx, by))


def _segment_hits_box(x1, y1, x2, y2, left, right, top, bottom) -> bool:
    if left <= x1 <= right and top <= y1 <= bottom:
        return True
    if left <= x2 <= right and top <= y2 <= bottom:
        return True
    edges = ((left, top, right, top), (right, top, right, bottom),
             (right, bottom, left, bottom), (left, bottom, left, top))
    return any(_segments_cross(x1, y1, x2, y2, *edge) for edge in edges)


def _curves_from_root(root) -> list[tuple[float, float, float, float]]:
    segs: list[tuple[float, float, float, float]] = []
    for elem in root.iter():
        if _local(elem.tag) == "path" and elem.get("d"):
            segs.extend(_path_segments(elem.get("d")))
    return segs


def frame_geometry_problems(svg_path: Path) -> list[str]:
    """单帧的压字 / 压线 / 出界。文本盒按字号估宽（全角=1em、拉丁≈0.55em），宁可报真缺陷。"""
    try:
        root = ET.parse(svg_path).getroot()
    except ET.ParseError as exc:
        return [f"{svg_path.name}: 无法解析 SVG（{exc}）"]
    view = (root.get("viewBox") or "").split()
    try:
        if len(view) == 4:
            width, height = float(view[2]), float(view[3])
        else:
            width, height = float(root.get("width")), float(root.get("height"))
    except (TypeError, ValueError):
        return [f"{svg_path.name}: 读不到画布尺寸"]

    problems = []
    boxes = _boxes_from_root(root)
    for content, left, right, top, bottom in boxes:
        if left < -2 or right > width + 2 or top < -2 or bottom > height - 2:
            problems.append(f"{svg_path.name}: 文本出界「{content[:18]}」")
    for i, (c1, a0, a1, t1, b1) in enumerate(boxes):
        for c2, b0, b2, t2, b2b in boxes[i + 1:]:
            if a0 < b2 and b0 < a1 and t1 < b2b and t2 < b1:
                problems.append(f"{svg_path.name}: 压字「{c1[:14]}」×「{c2[:14]}」")
    rules = _rules_from_root(root)
    for content, left, right, top, bottom in boxes:
        for rx0, ry0, rx1, ry1 in rules:
            if left < rx1 and rx0 < right and top < ry1 and ry0 < bottom:
                problems.append(f"{svg_path.name}: 压线「{content[:18]}」")
    for content, left, right, top, bottom in boxes:
        for sx1, sy1, sx2, sy2 in _curves_from_root(root):
            if _segment_hits_box(sx1, sy1, sx2, sy2, left, right, top, bottom):
                problems.append(f"{svg_path.name}: 压曲线「{content[:18]}」")
                break
    return problems


def validate_manifest(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing manifest: {path}"]
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries")
    if not isinstance(entries, list):
        return ["entries must be a list"]
    if len(entries) != 20:
        errors.append(f"expected 20 entries, got {len(entries)}")
    seen: set[str] = set()
    for i, entry in enumerate(entries):
        prefix = f"entries[{i}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: not an object")
            continue
        missing = REQUIRED - set(entry)
        if missing:
            errors.append(f"{prefix}: missing {sorted(missing)}")
        slug = entry.get("slug")
        if slug in seen:
            errors.append(f"duplicate slug: {slug}")
        seen.add(slug)
        if entry.get("style") not in ALLOWED_STYLE:
            errors.append(f"{slug}: bad style {entry.get('style')}")
        colors = entry.get("colors") or {}
        if colors.get("primary") != "C-03" or colors.get("danger") != "C-15":
            errors.append(f"{slug}: colors must be C-03/C-15")
        if entry.get("status") not in ALLOWED_STATUS:
            errors.append(f"{slug}: bad status {entry.get('status')}")
        src = entry.get("source_svg")
        if src and not (ROOT / src).is_file():
            # 允许 archived 后源文件已搬家：若 status==archived 则检查 archive 旁路
            if entry.get("status") != "archived":
                errors.append(f"{slug}: source_svg missing: {src}")
        if not isinstance(entry.get("frames"), list):
            errors.append(f"{slug}: frames must be list")
        # archived 指「源几何 SVG 已归档」，图本身仍是站点在用的活产物：帧、几何门与
        # 导出存在性都得照查，否则一归档就等于把这张图从门里摘出去。
        if entry.get("status") in {"rendered", "exported", "linked", "archived"}:
            frames = entry.get("frames") or []
            if not (3 <= len(frames) <= 8):
                errors.append(f"{slug}: need 3-8 frames when status>={entry['status']}")
            for rel in frames:
                if not (ROOT / rel).is_file():
                    errors.append(f"{slug}: missing frame {rel}")
            # 有矢量源就查几何：压字/压线/出界不是「画风」问题，是硬缺陷
            for rel in frames:
                svg = (ROOT / rel).with_suffix(".svg")
                if svg.is_file():
                    errors.extend(f"{slug}: {p}" for p in frame_geometry_problems(svg))
        if entry.get("status") in {"exported", "linked", "archived"}:
            export = entry.get("export")
            if not export or not (ROOT / export).is_file():
                errors.append(f"{slug}: missing export {export}")
        if entry.get("status") in {"linked", "archived"}:
            if not entry.get("caption_ok") or not entry.get("bans_ok"):
                errors.append(f"{slug}: caption_ok/bans_ok must be true before link/archive")
    return errors


def main(argv: list[str] | None = None) -> int:
    path = Path(argv[1]) if argv and len(argv) > 1 else DEFAULT
    errors = validate_manifest(path)
    if errors:
        print("HANDRAW MANIFEST FAIL")
        for e in errors:
            print(f" - {e}")
        return 1
    print("HANDRAW MANIFEST OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
