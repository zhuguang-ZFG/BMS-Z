"""印刷分镜：把一张 SMIL 动画按节拍烘成「多格帧 + 原字号字幕」的静态图。

印刷版没有时间轴，``svg_refine`` 过去只能「保字幕 + 同坐标留末拍」，于是
106 张动画在纸面上丢掉了 293 条接力拍说明（其中 188 条是幸存文本里没有的
独有信息，例如 rc-charge 的「第 1 拍……第 2 拍……」）。本模块补上规格
（SPEC-V4 §2.1 S2）要求的「静态多格分镜」：

* 顶部保留整张图的全尺寸画布——图内标签仍然可读；
* 中间是 N 格按节拍烘焙的缩略帧——看得到状态怎么走（帧内字幕剥掉，避免
  小字重影）；
* 底部是**原字号**的编号字幕——文字不缩，纸面读者读得全。

缩略帧里的字当然小，所以字幕必须另排一遍：帧负责「变」，字负责「说什么」。
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from .svg_refine import refine_svg

SVG_NS = "http://www.w3.org/2000/svg"
ANIMATION_TAGS = {"animate", "animateMotion", "animateTransform", "set"}
TEXT_ATTRS = ("opacity", "height", "y", "r", "cy", "cx", "x", "x1", "x2",
              "width", "stroke-dashoffset")
MARKS = "①②③④⑤⑥⑦⑧⑨"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _numbers(raw: str) -> list[float]:
    out = []
    for piece in raw.split(";"):
        try:
            out.append(float(piece.strip()))
        except ValueError:
            return []
    return out


def _label(element) -> str:
    return ("".join(element.itertext())).strip()


def _parent_map(root):
    return {child: node for node in root.iter() for child in node}


def _anim_children(element, holder):
    """动画可能挂在元素自身，也可能挂在包住它的组上——两处都收。"""
    kids = [c for c in element if _local(c.tag) in ANIMATION_TAGS]
    if holder is not None:
        kids += [c for c in holder if _local(c.tag) in ANIMATION_TAGS]
    return kids


def _opacity_window(element, holder) -> tuple[float, float] | None:
    for child in _anim_children(element, holder):
        if _local(child.tag) != "animate":
            continue
        if child.get("attributeName") != "opacity":
            continue
        values = _numbers(child.get("values", ""))
        key_times = _numbers(child.get("keyTimes", ""))
        if not values or len(values) != len(key_times):
            continue
        visible = [index for index, value in enumerate(values) if value >= 0.5]
        if not visible:
            return None
        return key_times[visible[0]], key_times[visible[-1]]
    return None


def caption_beats(text: str) -> list[dict]:
    """同坐标接力字幕 → 节拍列表（文档序），每拍带可见窗口与整组文案。

    分组口径与 ``svg_refine`` 一致：同一个 (x, y) 上先后出现的多条字幕
    是同一处的接力拍，印刷版会把它们折叠成末拍——分镜要把每一拍补回来。
    """
    root = ET.fromstring(text)
    parents = _parent_map(root)
    groups: dict[tuple[str, str], list[dict]] = {}
    for element in root.iter():
        if _local(element.tag) != "text":
            continue
        holder = parents.get(element)
        if holder is None:
            continue
        window = _opacity_window(element, holder)
        if window is None:
            continue
        label = _label(element)
        if not label:
            continue
        key = (element.get("x", ""), element.get("y", ""))
        groups.setdefault(key, []).append(
            {"label": label, "window": window, "holder": holder, "key": key})

    beats: list[dict] = []
    for key, members in groups.items():
        if len(members) < 2:
            continue
        for member in members:
            beats.append(member)
    beats.sort(key=lambda item: item["window"][0])

    for index, beat in enumerate(beats):
        start, end = beat["window"]
        if end <= start:
            end = min(start + 0.04, 1.0)
        beat["fraction"] = round(min((start + end) / 2, 0.98), 3)
        beat["index"] = index
    return beats


def _value_at(anim, fraction: float) -> str | None:
    raw = anim.get("values", "")
    values = [piece.strip() for piece in raw.split(";")] if raw else []
    if not values:
        return None
    key_times = _numbers(anim.get("keyTimes", ""))
    if len(key_times) != len(values):
        key_times = [i / (len(values) - 1) for i in range(len(values))]
    discrete = anim.get("calcMode", "linear") == "discrete"
    if fraction <= key_times[0]:
        return values[0]
    if fraction >= key_times[-1]:
        return values[-1]
    for index in range(1, len(key_times)):
        if fraction <= key_times[index]:
            if discrete:
                return values[index - 1]
            span = key_times[index] - key_times[index - 1]
            ratio = 0.0 if span <= 0 else (fraction - key_times[index - 1]) / span
            return _interpolate(values[index - 1], values[index], ratio)
    return values[-1]


def _interpolate(left: str, right: str, ratio: float) -> str:
    a, b = _numbers(left), _numbers(right)
    if not a or len(a) != len(b):
        return left if ratio < 0.5 else right
    return " ".join(f"{x + (y - x) * ratio:.3f}".rstrip("0").rstrip(".")
                    for x, y in zip(a, b))


def bake(text: str, fraction: float, drop_coords: set | None = None) -> str:
    """把动画烘到 ``fraction`` 这一时刻；``drop`` 里的元素整块摘掉。"""
    root = ET.fromstring(text)
    parents = _parent_map(root)
    for element in list(root.iter()):
        animations = [c for c in element if _local(c.tag) in ANIMATION_TAGS]
        if not animations:
            continue
        for animation in animations:
            tag = _local(animation.tag)
            if tag == "animate":
                name = animation.get("attributeName", "")
                value = _value_at(animation, fraction)
                if value is not None and (name in TEXT_ATTRS or name == "transform"):
                    element.set(name, value)
            elif tag == "animateTransform":
                value = _value_at(animation, fraction)
                if value is not None:
                    kind = animation.get("type", "translate")
                    element.set("transform", f"{kind}({value})")
            element.remove(animation)
    if drop_coords:
        for element in list(root.iter()):
            if _local(element.tag) != "text":
                continue
            if (element.get("x", ""), element.get("y", "")) not in drop_coords:
                continue
            holder = parents.get(element)
            if holder is None:
                continue
            if holder is root:
                # 字幕没有包裹组（直接挂在 <svg> 上）：只删文字本身。
                holder.remove(element)
            else:
                grand = parents.get(holder)
                if grand is not None and holder in list(grand):
                    grand.remove(holder)
    return ET.tostring(root, encoding="unicode")


def _wrap(text: str, limit: int) -> list[str]:
    lines, current = [], ""
    for char in text:
        current += char
        if len(current) >= limit:
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines or [text]


def _mark(index: int) -> str:
    return MARKS[index] if index < len(MARKS) else f"({index + 1})"


def build_storyboard(text: str, refined: str, panel_width: int = 290) -> str:
    """整张图 + 节拍缩略帧 + 原字号编号字幕，合成一张印刷用静态 SVG。

    ``text`` 是原始动画 SVG，``refined`` 是 ``refine_svg`` 之后的全尺寸画布
    （图内标签可读）。
    """
    source = ET.fromstring(text)
    view_box = source.get("viewBox", "0 0 800 600").split()
    canvas_w = float(view_box[2]) if len(view_box) > 2 else 800.0
    canvas_h = float(view_box[3]) if len(view_box) > 3 else 600.0

    beats = caption_beats(text)
    if len(beats) < 2:
        beats = [{"label": "", "fraction": fraction, "holder": None,
                  "index": index}
                 for index, fraction in enumerate((0.15, 0.5, 0.85))]
    beats = beats[:5]
    count = len(beats)

    scale = panel_width / canvas_w
    panel_h = canvas_h * scale
    columns = count if count <= 3 else 2
    rows = (count + columns - 1) // columns
    gap, margin, line_h = 18.0, 24.0, 26.0
    width = 960.0

    grid_w = columns * panel_width + (columns - 1) * gap
    grid_x = (width - grid_w) / 2
    canvas_scale = width / canvas_w
    canvas_h_scaled = canvas_h * canvas_scale
    grid_y = margin + canvas_h_scaled + 34

    caption_lines: list[str] = []
    for index, beat in enumerate(beats):
        if not beat["label"]:
            continue
        wrapped = _wrap(beat["label"], 44)
        if wrapped[0][:1] not in MARKS:
            wrapped[0] = f"{_mark(index)} {wrapped[0]}"
        caption_lines.extend(wrapped)
    caption_y = grid_y + rows * panel_h + (rows - 1) * gap + 36
    height = caption_y + max(len(caption_lines), 1) * line_h + 16

    title = ""
    for element in source.iter():
        if _local(element.tag) == "title":
            title = _label(element)
            break

    parts = [
        f'<svg xmlns="{SVG_NS}" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'role="img" aria-labelledby="sbTitle sbDesc">',
        f'<title id="sbTitle">{_escape(title)}（印刷分镜）</title>',
        f'<desc id="sbDesc">{_escape(_describe(title, beats, count))}</desc>',
        f'<rect width="{width:.0f}" height="{height:.0f}" fill="#fffdf8"/>',
    ]

    inner = _strip_shell(refined)
    parts.append(f'<g transform="translate(0,{margin}) '
                 f'scale({canvas_scale:.4f})">{inner}</g>')

    caption_coords = {(b["key"]) for b in beats if b.get("key")}
    for index, beat in enumerate(beats):
        frame = refine_svg(bake(text, beat["fraction"],
                                drop_coords=caption_coords))
        frame_inner = _strip_shell(frame)
        frame_inner = re.sub(r"<(title|desc)[^>]*>.*?</\\1>", "", frame_inner,
                             flags=re.S)
        column, row = index % columns, index // columns
        x = grid_x + column * (panel_width + gap)
        y = grid_y + row * (panel_h + gap)
        parts.append(f'<g transform="translate({x:.1f},{y:.1f})">')
        parts.append(f'<rect x="0" y="0" width="{panel_width}" '
                     f'height="{panel_h:.1f}" fill="#ffffff" stroke="#d0d5dd" '
                     f'stroke-width="1.2"/>')
        parts.append(f'<g transform="scale({scale:.4f})">{frame_inner}</g>')
        parts.append(f'<text x="7" y="18" font-family="\'Book Sans\','
                     f'\'Noto Sans SC\',sans-serif" font-size="14" '
                     f'font-weight="700" fill="#14213d">'
                     f'{_mark(index)}</text>')
        parts.append("</g>")

    parts.append(f'<text x="{margin}" y="{grid_y - 14:.0f}" '
                 f'font-family="\'Book Sans\',\'Noto Sans SC\',sans-serif" '
                 f'font-size="15" font-weight="700" fill="#14213d">'
                 f'节拍分镜：这一张图怎么走</text>')
    for index, line in enumerate(caption_lines):
        parts.append(f'<text x="{margin}" y="{caption_y + index * line_h:.0f}" '
                     f'font-family="\'Book Sans\',\'Noto Sans SC\',sans-serif" '
                     f'font-size="15" fill="#14213d">{_escape(line)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def _strip_shell(document: str) -> str:
    body = re.sub(r"^.*?<svg[^>]*>", "", document, count=1, flags=re.S)
    return re.sub(r"</svg>\s*$", "", body)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _describe(title: str, beats: list[dict], count: int) -> str:
    head = f"{title}的印刷分镜：{count} 格缩略帧按节拍从左到右排列，"
    labels = [beat["label"] for beat in beats if beat["label"]]
    if not labels:
        return head + "底部按原字号列出说明。"
    return head + "底部按顺序列出每一拍的说明：" + "；".join(labels) + "。"
