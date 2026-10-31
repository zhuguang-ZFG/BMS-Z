"""手帐式动效注记层：给电路动画加可读的批注装饰，不碰技术几何与既有 SMIL。

只做插入：标题荧光笔、手绘下划线、表头小星、提示框贴纸、确认勾的爆花，
以及移动光点的柔和光晕。所有装饰元素用 ``bms-`` 类名标记、``aria-hidden``，
并共用一块 ``id="bms-motion"`` 样式；``decorate()`` 幂等，可反复运行。
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PALETTE = json.loads((ROOT / "tools/visual_palette.json").read_text(encoding="utf-8"))
LIGHT, DARK = PALETTE["light"], PALETTE["dark"]
NS = "{http://www.w3.org/2000/svg}"


def _rgb(color: str) -> str:
    color = color.lstrip("#")
    return ",".join(str(int(color[i:i + 2], 16)) for i in (0, 2, 4))


GOLD_L = LIGHT["technical"]["gold"]
GOLD_D = DARK["technical"]["gold"]
GREEN_L = LIGHT["technical"]["green"]
GREEN_D = DARK["technical"]["green"]
SOFT_L = LIGHT["technical"]["blue"]
SOFT_D = DARK["technical"]["blue"]

STYLE = f"""
    /* bms-motion: 手帐式动效注记（纯装饰，不改技术几何与既有 SMIL 时序） */
    .bms-marker {{ fill: {LIGHT['notes']['yellow']}; opacity: .78; }}
    .bms-under {{ fill: none; stroke: {GOLD_L}; stroke-width: 2.4; stroke-linecap: round; opacity: .9; }}
    .bms-spark-line {{ fill: none; stroke: {GOLD_L}; stroke-width: 1.9; stroke-linecap: round; }}
    .bms-spark-fill {{ fill: {GOLD_L}; }}
    .bms-spark-soft {{ fill: {SOFT_L}; opacity: .8; }}
    .bms-sticker {{ fill: none; stroke: {GOLD_L}; stroke-width: 2; stroke-dasharray: 7 5; stroke-linecap: round; opacity: .85; }}
    .bms-halo {{ fill: none; stroke: {GOLD_L}; stroke-width: 2; }}
    .bms-marker, .bms-under, .bms-sticker, .bms-halo,
    .bms-spark, .bms-success, .bms-doodle {{ pointer-events: none; }}
    circle:has(> animateMotion) {{ filter: drop-shadow(0 0 2px rgba({_rgb(GOLD_L)},.5)) drop-shadow(0 0 5px rgba(196,145,52,.45)); }}
    rect:has(> animateMotion) {{ filter: drop-shadow(0 0 3px rgba(196,145,52,.75)); }}
    g:has(> circle):has(> path.stroke-check) {{ filter: drop-shadow(0 0 5px rgba({_rgb(GREEN_L)},.5)); }}
    @media (prefers-color-scheme: dark) {{
      .bms-marker {{ fill: {DARK['notes']['yellow']}; opacity: .85; }}
      .bms-under {{ stroke: {GOLD_D}; }}
      .bms-spark-line {{ stroke: {GOLD_D}; }}
      .bms-spark-fill {{ fill: {GOLD_D}; }}
      .bms-spark-soft {{ fill: {SOFT_D}; }}
      .bms-sticker {{ stroke: {GOLD_D}; }}
      .bms-halo {{ stroke: {GOLD_D}; }}
      circle:has(> animateMotion) {{ filter: drop-shadow(0 0 2px rgba({_rgb(GOLD_D)},.8)) drop-shadow(0 0 7px rgba({_rgb(GOLD_D)},.9)); }}
      rect:has(> animateMotion) {{ filter: drop-shadow(0 0 6px rgba({_rgb(GOLD_D)},.8)); }}
      g:has(> circle):has(> path.stroke-check) {{ filter: drop-shadow(0 0 6px rgba({_rgb(GREEN_D)},.7)); }}
    }}
    @media (prefers-reduced-motion: reduce) {{ .bms-spark, .bms-success, .bms-doodle {{ display: none; }} }}
"""


def mask_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", lambda m: " " * len(m.group(0)), text, flags=re.S)


def group_spans(text: str) -> list[tuple[int, int, int]]:
    """返回每个 <g> 的 (开始, 结束标签起点, 结束标签终点)，按文档顺序。"""
    masked = mask_comments(text)
    tokens = [(m.start(), "open") for m in re.finditer(r"<g\b", masked)]
    tokens += [(m.start(), "close") for m in re.finditer(r"</g\s*>", masked)]
    tokens.sort()
    stack: list[int] = []
    spans: list[tuple[int, int, int]] = []
    for pos, kind in tokens:
        if kind == "open":
            if masked[masked.index(">", pos) - 1] == "/":
                continue
            stack.append(pos)
        elif stack:
            start = stack.pop()
            close_end = masked.index(">", pos) + 1
            spans.append((start, pos, close_end))
    spans.sort()
    return spans


def insert_many(text: str, items: list[tuple[int, str]]) -> str:
    for pos, html in sorted(items, key=lambda item: -item[0]):
        text = text[:pos] + html + text[pos:]
    return text


def _css_title_size(root: ET.Element) -> float | None:
    """取样式表里 .title 的最后一个 font-size（内联属性优先级更低）。"""
    size = None
    for style in root.iter(f"{NS}style"):
        if style.get("id") == "bms-motion":
            continue
        for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", style.text or ""):
            if not re.search(r"(?:^|,)\s*\.title\s*(?:,|$)", selector.strip()):
                continue
            found = re.search(r"font-size\s*:\s*([\d.]+)px", body)
            if found:
                size = float(found.group(1))
    return size


def title_meta(root: ET.Element):
    titles = root.findall(f'.//{NS}text[@class="title"]')
    if not titles:
        return None
    title = titles[0]
    label = "".join(title.itertext()).strip()
    try:
        x, y = float(title.get("x")), float(title.get("y"))
    except (TypeError, ValueError):
        return None
    size = _css_title_size(root)
    if size is None:
        size = 16.0
        if title.get("font-size"):
            try:
                size = float(title.get("font-size"))
            except ValueError:
                pass
    width = 0.0
    for char in label:
        width += size * (1.0 if ord(char) > 0x2E80 else (0.32 if char == " " else 0.6))
    return x, y, size, min(width, 700)


def title_deco(root: ET.Element) -> str:
    meta = title_meta(root)
    if meta is None:
        return ""
    x, y, size, width = meta
    baseline = 9 if y < 0 else 8
    marker_w = min(max(width + 14, 90), 650)
    marker_y = y - size * 0.93
    segment = 48
    count = max(2, int(min(width, 560) // segment))
    underline = f"M{x:.1f} {y + baseline:.1f} q {segment / 2:.1f} -2.4 {segment:.1f} 0"
    underline += f" t {segment} 0" * (count - 1)
    return (
        f'<rect class="bms-marker" aria-hidden="true" x="{x - 6:.1f}" y="{marker_y:.1f}" '
        f'width="{marker_w:.1f}" height="{size * 1.08:.1f}" rx="{size * 0.24:.1f}" '
        f'transform="rotate(-.5 {x - 6:.1f} {marker_y + size * 0.54:.1f})"/>'
        f'<path class="bms-under" aria-hidden="true" d="{underline}"/>'
    )


def header_deco(root: ET.Element) -> str:
    panels = [r for r in root.iter(f"{NS}rect") if r.get("class") == "panel"]
    if not panels:
        return ""
    panel = panels[0]
    try:
        px, py, pw = (float(panel.get(key)) for key in ("x", "y", "width"))
    except (TypeError, ValueError):
        return ""
    if pw < 600:
        return ""
    for text in root.iter(f"{NS}text"):
        try:
            tx, ty = float(text.get("x")), float(text.get("y"))
        except (TypeError, ValueError):
            continue
        if px + pw - 200 <= tx <= px + pw and py <= ty <= py + 36:
            return ""
    x = px + pw
    return (
        f'<g class="bms-doodle" aria-hidden="true" transform="translate({x - 30:.1f} {py + 24:.1f})">'
        '<animateTransform attributeName="transform" type="rotate" values="-6;7;-6" '
        'keyTimes="0;0.5;1" dur="5.4s" repeatCount="indefinite" additive="sum"/>'
        '<animate attributeName="opacity" values="0.62;1;0.62" keyTimes="0;0.5;1" '
        'dur="3.6s" repeatCount="indefinite"/>'
        '<path class="bms-spark-fill" d="M0 -9 L2.3 -2.3 L9 0 L2.3 2.3 L0 9 L-2.3 2.3 L-9 0 L-2.3 -2.3 Z"/>'
        "</g>"
        f'<g class="bms-doodle" aria-hidden="true" transform="translate({x - 66:.1f} {py + 14:.1f})">'
        '<animateTransform attributeName="transform" type="rotate" values="5;-4;5" '
        'keyTimes="0;0.5;1" dur="6.2s" repeatCount="indefinite" additive="sum"/>'
        '<animate attributeName="opacity" values="0.5;0.9;0.5" keyTimes="0;0.5;1" '
        'dur="4.4s" repeatCount="indefinite"/>'
        '<path class="bms-spark-soft" d="M0 -5.5 L1.4 -1.4 L5.5 0 L1.4 1.4 L0 5.5 L-1.4 1.4 L-5.5 0 L-1.4 -1.4 Z"/>'
        "</g>"
        '<g class="bms-doodle" aria-hidden="true">'
        f'<circle class="bms-spark-fill" cx="{x - 48:.1f}" cy="{py + 33:.1f}" r="1.3"/>'
        f'<circle class="bms-spark-soft" cx="{x - 80:.1f}" cy="{py + 30:.1f}" r="1.1"/>'
        "</g>"
    )


def as_callout(group: ET.Element):
    children = list(group)
    rects = [c for c in children if c.tag == f"{NS}rect"]
    texts = [c for c in children if c.tag == f"{NS}text"]
    activations = [
        c for c in children
        if c.tag == f"{NS}animate" and c.get("attributeName") == "opacity"
    ]
    if len(rects) != 1 or not texts or not activations:
        return None
    rect = rects[0]
    try:
        width = float(rect.get("width"))
        height = float(rect.get("height"))
    except (TypeError, ValueError):
        return None
    classes = rect.get("class") or ""
    if not ("box" in classes or "panel" in classes):
        return None
    if width < 140 or not (30 <= height <= 100):
        return None
    return rect


def as_check(group: ET.Element):
    children = list(group)
    circles = [c for c in children if c.tag == f"{NS}circle"]
    checks = [
        c for c in children
        if c.tag == f"{NS}path" and "stroke-check" in (c.get("class") or "")
    ]
    activations = [
        c for c in children
        if c.tag == f"{NS}animate" and c.get("attributeName") == "opacity"
    ]
    if len(circles) != 1 or not checks or not activations:
        return None
    return circles[0]


def activation_keytime(group: ET.Element):
    for child in group:
        if (
            child.tag == f"{NS}animate"
            and child.get("attributeName") == "opacity"
            and child.get("keyTimes")
            and child.get("values")
        ):
            try:
                times = [float(v) for v in child.get("keyTimes").split(";")]
                values = [float(v) for v in child.get("values").split(";")]
            except ValueError:
                return None
            if len(times) != len(values):
                return None
            previous = 0.0
            for time, value in zip(times, values, strict=True):
                if value >= 0.8 and previous < 0.5:
                    return time
                previous = value
            return None
    return None


def group_duration(group: ET.Element) -> str:
    for child in group:
        if (
            child.tag == f"{NS}animate"
            and child.get("attributeName") == "opacity"
            and child.get("dur")
        ):
            return child.get("dur")
    return "8s"


def success_burst(group: ET.Element, circle: ET.Element) -> str:
    activation = activation_keytime(group)
    if activation is None or activation > 0.9:
        return ""
    try:
        cx, cy, radius = (float(circle.get(k)) for k in ("cx", "cy", "r"))
    except (TypeError, ValueError):
        return ""
    settle = min(activation + 0.04, 0.995)
    rest = min(activation + 0.12, 0.998)
    key = f"0;{activation:.4f};{settle:.4f};{rest:.4f};1"
    ring = radius + 4
    rays = (
        f"M{ring:.1f} 0 h 8 "
        f"M{ring * 0.72:.1f} -{ring * 0.72:.1f} l 6 -6 "
        f"M-{ring * 0.72:.1f} -{ring * 0.72:.1f} l -6 -6 "
        f"M-{ring:.1f} 0 h -8 "
        f"M-{ring * 0.72:.1f} {ring * 0.72:.1f} l -6 6 "
        f"M{ring * 0.72:.1f} {ring * 0.72:.1f} l 6 6"
    )
    return (
        f'<g class="bms-success" aria-hidden="true" transform="translate({cx:.1f} {cy:.1f})">'
        '<animateTransform attributeName="transform" type="scale" values="0.55;0.55;1.28;1;1" '
        f'keyTimes="{key}" dur="{group_duration(group)}" repeatCount="indefinite" additive="sum"/>'
        f'<circle class="bms-halo" r="{ring - 1.5:.1f}"/>'
        f'<path class="bms-spark-line" d="{rays}"/></g>'
    )


SPARK = (
    '<g class="bms-spark" aria-hidden="true" transform="translate({x:.1f} {y:.1f})">'
    '<animateTransform attributeName="transform" type="rotate" values="-8;9;-8" '
    'keyTimes="0;0.5;1" dur="4.8s" repeatCount="indefinite" additive="sum"/>'
    '<animate attributeName="opacity" values="0.55;1;0.55" keyTimes="0;0.5;1" '
    'dur="3.2s" repeatCount="indefinite"/>'
    '<path class="bms-spark-fill" d="M0 -9 L2.3 -2.3 L9 0 L2.3 2.3 L0 9 L-2.3 2.3 L-9 0 L-2.3 -2.3 Z"/>'
    "</g>"
)


def strip_decorations(text: str) -> str:
    """移除 bms 装饰元素与样式块，其余字节原样保留，供刷新装饰层使用。"""
    masked = mask_comments(text)
    spans: list[tuple[int, int]] = []
    for match in re.finditer(
        r'<style\b[^>]*\bid="bms-motion"[^>]*>.*?</style\s*>', masked, re.S
    ):
        spans.append((match.start(), match.end()))
    for match in re.finditer(
        r'<[A-Za-z][\w:.-]*\b[^>]*\bclass="[^"]*\bbms-[^"]*"[^>]*/>', masked
    ):
        spans.append((match.start(), match.end()))
    for start, _close_start, close_end in group_spans(text):
        open_end = masked.index(">", start) + 1
        if re.search(r'\bclass="[^"]*\bbms-[^"]*"', masked[start:open_end]):
            spans.append((start, close_end))
    spans.sort()
    kept: list[tuple[int, int]] = []
    for start, end in spans:
        if kept and end <= kept[-1][1]:
            continue
        kept.append((start, end))
    for start, end in reversed(kept):
        text = text[:start] + text[end:]
    return text


def decorate(text: str, *, refresh: bool = False) -> str:
    """插入装饰层；已有装饰时默认原样返回，``refresh=True`` 则先剥离再重插。"""
    if 'id="bms-motion"' in text:
        if not refresh:
            return text
        text = strip_decorations(text)
        if re.search(r'class="[^"]*\bbms-', text) or 'id="bms-motion"' in text:
            raise ValueError("装饰层未能完整剥离")
    root = ET.fromstring(text)
    spans = group_spans(text)
    groups = list(root.iter(f"{NS}g"))
    if len(groups) != len(spans):
        raise ValueError(f"<g> 结构与源文本不一致：{len(groups)} vs {len(spans)}")
    items: list[tuple[int, str]] = []
    for group, (_start, close_start, _close_end) in zip(groups, spans, strict=True):
        rect = as_callout(group)
        if rect is not None:
            x, y, w, h = (float(rect.get(k)) for k in ("x", "y", "width", "height"))
            cx, cy = x + w / 2, y + h / 2
            items.append((
                close_start,
                f'<rect class="bms-sticker" aria-hidden="true" x="{x}" y="{y}" width="{w}" height="{h}" '
                f'rx="{rect.get("rx") or 8}" transform="rotate(-.45 {cx:.1f} {cy:.1f})"/>'
                + SPARK.format(x=x + w - 16, y=y + 16),
            ))
            continue
        circle = as_check(group)
        if circle is not None:
            try:
                cx, cy, radius = (float(circle.get(k)) for k in ("cx", "cy", "r"))
            except (TypeError, ValueError):
                continue
            items.append((
                close_start,
                SPARK.format(x=cx + radius + 9, y=cy - radius - 2) + success_burst(group, circle),
            ))

    title_tag = re.search(r'<text\b[^>]*class="title"[^>]*>', text)
    if title_tag:
        items.append((title_tag.start(), title_deco(root)))

    doodles = header_deco(root)
    if doodles:
        panel_tag = re.search(r'<rect\b[^>]*class="panel"[^>]*/>', text)
        if panel_tag:
            items.append((panel_tag.end(), doodles))

    decorated = insert_many(text, items)
    style = f'<style id="bms-motion">{STYLE}</style>'
    last_style = decorated.rfind("</style>")
    if last_style < 0:
        root_tag = re.search(r"<svg\b[^>]*>", decorated)
        if root_tag is None:
            raise ValueError("找不到 <svg> 根元素")
        cut = root_tag.end()
    else:
        cut = last_style + len("</style>")
    decorated = decorated[:cut] + style + decorated[cut:]
    ET.fromstring(decorated)
    return decorated


def _is_decoration(el: ET.Element) -> bool:
    if el.tag == f"{NS}style" and el.get("id") == "bms-motion":
        return True
    return any(name.startswith("bms-") for name in (el.get("class") or "").split())


def technical_canonical(text: str) -> str:
    """非装饰内容的稳定文本指纹：标签、排序属性、自带文本与可见尾随文字。"""
    root = ET.fromstring(text)
    lines: list[str] = []

    def walk(el: ET.Element, depth: int) -> None:
        if _is_decoration(el):
            return
        attrs = " ".join(
            f"{key}={json.dumps(value, ensure_ascii=False)}"
            for key, value in sorted(el.attrib.items())
        )
        own = " ".join((el.text or "").split())
        tail = " ".join((el.tail or "").split())
        line = f'{"  " * depth}{el.tag.replace(NS, "")} {attrs} :: {own}'
        if tail:
            line += f" ~ {tail}"
        lines.append(line)
        for child in el:
            walk(child, depth + 1)

    walk(root, 0)
    return "\n".join(lines) + "\n"
