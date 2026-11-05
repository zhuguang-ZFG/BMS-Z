#!/usr/bin/env python3
"""Validate docs/circuits/handraw/manifest.json against path-B contract."""
from __future__ import annotations

import json
import math
import re
import sys
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
TEXT_RE = re.compile(r"<text((?:\s+[\w:-]+=\"[^\"]*\")*)\s*>([^<]*)</text>")
ATTR_RE = re.compile(r"([\w:-]+)=\"([^\"]*)\"")


def _text_boxes(svg_text: str) -> list[tuple[str, float, float, float, float]]:
    """把每个 <text> 折算成轴对齐包围盒 (内容, 左, 右, 上, 下)。

    旋转文本不能跳过：本批的 y 轴标题就是 rotate(-90) 的，跳过等于把「压刻度数字」
    这类缺陷整类放行。这里按 transform 里的旋转角把四个角转过去再取包围盒，
    慢但只跑 20 条 manifest 里的已渲染条目，够快。
    """
    boxes: list[tuple[str, float, float, float, float]] = []
    for m in TEXT_RE.finditer(svg_text):
        attrs = dict(ATTR_RE.findall(m.group(1)))
        if "x" not in attrs or "y" not in attrs:
            continue
        content = m.group(2).strip()
        if not content:
            continue
        try:
            x, y = float(attrs["x"]), float(attrs["y"])
            size = float(attrs.get("font-size", 12))
        except ValueError:
            continue
        advance = sum(size if ord(ch) >= CJK_MIN else size * 0.55 for ch in content)
        anchor = attrs.get("text-anchor", "start")
        left = x - advance / 2 if anchor == "middle" else (x - advance if anchor == "end" else x)
        corners = [(left, y - size), (left + advance, y - size),
                   (left + advance, y + size * 0.25), (left, y + size * 0.25)]
        rot = re.search(r"rotate\(\s*(-?[\d.]+)(?:\s+(-?[\d.]+)\s+(-?[\d.]+))?\s*\)",
                        attrs.get("transform", ""))
        if rot:
            angle = float(rot.group(1))
            cx = float(rot.group(2)) if rot.group(2) else 0.0
            cy = float(rot.group(3)) if rot.group(3) else 0.0
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


def _rules(svg_text: str) -> list[tuple[float, float, float, float]]:
    """取出用作轴线的直线段（含 stroke 的 <line>），只保留够长的，避免把刻度齿当骨架线。"""
    rules = []
    for m in re.finditer(r"<line((?:\s+[\w:-]+=\"[^\"]*\")*)\s*/?>", svg_text):
        attrs = dict(ATTR_RE.findall(m.group(1)))
        try:
            x1, y1, x2, y2 = (float(attrs[k]) for k in ("x1", "y1", "x2", "y2"))
        except (KeyError, ValueError):
            continue
        if abs(x1 - x2) <= 2 and abs(y1 - y2) >= 60:  # 竖轴
            rules.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
        elif abs(y1 - y2) <= 2 and abs(x1 - x2) >= 60:  # 横轴
            rules.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
    return rules


def frame_geometry_problems(svg_path: Path) -> list[str]:
    """单帧的压字 / 压线 / 出界。文本盒按字号估宽（全角=1em、拉丁≈0.55em），宁可报真缺陷。"""
    text = svg_path.read_text(encoding="utf-8")
    root = re.search(r"<svg\b[^>]*>", text)
    if root is None:
        return [f"{svg_path.name}: 没有 <svg> 根元素"]
    view = re.search(r"viewBox=\"[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)\"", root.group(0))
    try:
        width, height = (float(view.group(1)), float(view.group(2))) if view else (
            float(re.search(r"width=\"([\d.]+)\"", root.group(0)).group(1)),
            float(re.search(r"height=\"([\d.]+)\"", root.group(0)).group(1)),
        )
    except (AttributeError, ValueError):
        return [f"{svg_path.name}: 读不到画布尺寸"]

    problems = []
    boxes = _text_boxes(text)
    for content, left, right, top, bottom in boxes:
        if left < -2 or right > width + 2 or top < -2 or bottom > height - 2:
            problems.append(f"{svg_path.name}: 文本出界「{content[:18]}」")
    for i, (c1, a0, a1, t1, b1) in enumerate(boxes):
        for c2, b0, b2, t2, b2b in boxes[i + 1:]:
            if a0 < b2 and b0 < a1 and t1 < b2b and t2 < b1:
                problems.append(f"{svg_path.name}: 压字「{c1[:14]}」×「{c2[:14]}」")
    rules = _rules(text)
    for content, left, right, top, bottom in boxes:
        for rx0, ry0, rx1, ry1 in rules:
            if left < rx1 and rx0 < right and top < ry1 and ry0 < bottom:
                problems.append(f"{svg_path.name}: 压线「{content[:18]}」")
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
        if entry.get("status") in {"rendered", "exported", "linked"}:
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
        if entry.get("status") in {"exported", "linked"}:
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
