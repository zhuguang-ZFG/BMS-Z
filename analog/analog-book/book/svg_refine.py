"""印刷用 SVG 净化：去掉模板背景、深色模式、动效与高饱和配色。

处理 118 张动画模板图（同时带 ``bgL`` 渐变与深色模式）：
装饰性动画整块移除；含文字的字幕组按坐标分组只留末拍，
opacity 落峰值可见态，印刷不再丢字幕（v3.86 修复 112/118 丢字）。
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
REMOVE_TAGS = {
    "linearGradient", "radialGradient", "pattern", "filter",
    "animate", "animateMotion", "animateTransform", "set",
    "style", "script", "foreignObject",
}
ANIMATION_TAGS = {"animate", "animateMotion", "animateTransform", "set"}
# waveform-phase 曾在此列——那是离散换场的节拍字幕（calcMode="discrete"），
# 整类删除等于再丢一次字幕（555-astable/analog-switch/ldo-transient 共 8 条）。
# 它们走 step 1 的 (x,y) 分组留末拍规则，不再按类连坐。
PAGE_CLASSES = {"page-bg", "page-vig", "page-hdr"}
HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}")
URL_RE = re.compile(r"url\(#[^)]+\)")
EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF\uFE0F\u200D]+")

# 旧模板的 Tailwind 高饱和色 -> 书籍印刷色。蓝/青绿分开保留，
# 让同一张图里的多条曲线仍然可区分。
COLOR_MAP = {
    "#ffffff": "#fffdf8", "#fff": "#fffdf8",
    "#f8fafc": "#fbf7ef", "#f1f5f9": "#f4eee2",
    "#eff6ff": "#e6f1ef", "#ecfdf5": "#eef0e2",
    "#fffbeb": "#faf0dd", "#fff7ed": "#faf0dd",
    "#fef2f2": "#f7e8e5", "#fee2e2": "#f7e8e5",
    "#dbeafe": "#d5e5e2", "#e0f2fe": "#e0efec",
    "#d1fae5": "#eef0e2", "#e2e8f0": "#ded5c4",
    "#cbd5e1": "#d8cfbf",
    "#94a3b8": "#52606d", "#8497ad": "#52606d",
    "#64748b": "#52606d", "#475569": "#52606d",
    "#334155": "#14213d", "#1e293b": "#14213d",
    "#0f172a": "#14213d", "#0a1020": "#14213d",
    "#141d30": "#14213d",
    "#2563eb": "#0f766e", "#1d4ed8": "#0f766e",
    "#3b82f6": "#0f766e", "#0284c7": "#0f766e",
    "#0369a1": "#0f766e", "#0ea5e9": "#0f766e",
    "#60a5fa": "#0f766e", "#7dd3fc": "#0f766e",
    "#38bdf8": "#0f766e", "#0891b2": "#0f766e",
    "#93c5fd": "#0f766e", "#082f49": "#0b5e57",
    "#172554": "#0b5e57", "#1e3a8a": "#0b5e57",
    "#059669": "#3f6f4f", "#10b981": "#3f6f4f",
    "#34d399": "#3f6f4f", "#065f46": "#3f6f4f",
    "#022c22": "#3f6f4f", "#6ee7b7": "#3f6f4f",
    "#7c3aed": "#7b4b6e", "#a78bfa": "#7b4b6e",
    "#dc2626": "#b42318", "#b91c1c": "#b42318",
    "#991b1b": "#b42318", "#f87171": "#b42318",
    "#fca5a5": "#b42318", "#fecaca": "#b42318",
    "#450a0a": "#b42318",
    "#f59e0b": "#b45309", "#b45309": "#b45309",
    "#92400e": "#b45309", "#fbbf24": "#b45309",
    "#fcd34d": "#b45309", "#451a03": "#b45309",
    "#431407": "#b45309",
    "#eef2f8": "#fbf7ef",
}
FONT_STACK = ('"Microsoft YaHei","Noto Sans SC","PingFang SC",'
              '"Hiragino Sans GB",sans-serif')
PRINT_STYLE = (
    f"text{{font-family:{FONT_STACK}}}"
    "line,path,polyline,polygon{stroke-linecap:round;"
    "stroke-linejoin:round}"
)


def is_legacy_svg(text: str) -> bool:
    """旧模板同时带 bgL 渐变和 prefers-color-scheme。

    handraw 纸墨皮肤的静态手绘图（`class="page-grain"` 颗粒层、无 SMIL）
    不算旧模板：印刷保留纸面渐变、颗粒与楷体手写体，剥掉它们等于把
    手绘图重画成机械矢量图。旧动画虽然也带皮肤，但含 `<animate`，
    仍走净化与分镜管线。
    """
    if 'id="bgL"' not in text or "prefers-color-scheme" not in text:
        return False
    if 'class="page-grain"' in text and "<animate" not in text.lower():
        return False
    return True


def is_animated_svg(text: str) -> bool:
    """真动画：带 SMIL `<animate*>`。

    153 张旧动画全部含 SMIL，而静态插图（含 handraw 皮肤注入纸面层后的新图）
    一张都没有——分镜只对真动画有意义，静态图进 build_storyboard 会把
    整幅图按节拍裁成一帧，正文图注与尺寸信息丢失。
    """
    return "<animate" in text.lower()


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _map_colors(value: str) -> str:
    return HEX_RE.sub(
        lambda match: COLOR_MAP.get(match.group(0).lower(), match.group(0)),
        value)


def refine_svg(text: str) -> str:
    if not is_legacy_svg(text):
        return text
    if "<!DOCTYPE" in text or "<!ENTITY" in text:
        raise ValueError("SVG 含 DTD 或实体声明，拒绝解析")
    root = ET.fromstring(text)
    namespace = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""
    parent = {child: node for node in root.iter() for child in node}

    def drop(element) -> None:
        holder = parent.get(element)
        if holder is not None:
            holder.remove(element)
            parent.pop(element, None)

    # 1) 动画元素分流（v3.86 前是整块连坐删除，112/118 张图印刷丢字幕）：
    #    · 纯装饰（粒子、高亮、走位）——整块删除，行为不变；
    #    · 子树含 <text> 的——进入字幕候选：只摘动画子节点，把 opacity
    #      落到 values 的峰值（节拍字幕的可见态），元素本身保留；
    #    · caption() 的同坐标接力字幕（beat_captions：零重叠时隙共用同一
    #      (x,y)）——按坐标分组，只留文档序最后一拍，其余连同药丸底衬整条删，
    #      否则全部落可见会在纸上叠成一坨墨。
    protected = set()

    def _ancestors(el):
        node = parent.get(el)
        while node is not None:
            yield node
            node = parent.get(node)

    def _opacity_peak(child) -> float | None:
        raw = child.get("values", "")
        nums = []
        for piece in raw.split(";"):
            try:
                nums.append(float(piece.strip()))
            except ValueError:
                continue
        if nums:
            return max(nums)
        try:
            return float(child.get("to", "").strip())
        except ValueError:
            return None

    def _settle(el) -> None:
        """摘掉动画子节点；若曾以动画驱动 opacity，落到峰值可见态。"""
        peak = None
        for child in [c for c in el if _local(c.tag) in ANIMATION_TAGS]:
            if child.get("attributeName") == "opacity":
                candidate = _opacity_peak(child)
                if candidate is not None:
                    peak = candidate if peak is None else max(peak, candidate)
            drop(child)
        if peak is not None:
            el.set("opacity", f"{peak:g}")

    captions = []  # (element, (x, y)) 文档序
    for element in list(root.iter()):
        if element is root:
            continue
        if not any(_local(child.tag) in ANIMATION_TAGS for child in element):
            continue
        if any(ancestor in protected for ancestor in _ancestors(element)):
            # 已保留字幕组内部（药丸底衬、文字本体）：同样摘动画落可见。
            _settle(element)
            continue
        if any(_local(d.tag) == "text" for d in element.iter()):
            _settle(element)
            text_el = next(d for d in element.iter() if _local(d.tag) == "text")
            key = (text_el.get("x", ""), text_el.get("y", ""))
            if key == ("", ""):
                key = ("__no_coord__", id(element))
            captions.append((element, key))
            protected.add(element)
        else:
            drop(element)

    by_coord = {}
    for element, key in captions:
        by_coord.setdefault(key, []).append(element)
    for group in by_coord.values():
        for stale in group[:-1]:
            protected.discard(stale)
            drop(stale)

    # 2) 模板 defs 里的渐变/图案/滤镜与主题样式整体移除。
    for element in list(root.iter()):
        if element is root:
            continue
        if _local(element.tag) in REMOVE_TAGS:
            drop(element)

    # 3) 页面底纹、全屏渐变、深色叠层、零透明度元素。
    for element in list(root.iter()):
        if element is root:
            continue
        classes = set(element.get("class", "").split())
        fill = element.get("fill", "")
        stroke = element.get("stroke", "")
        if classes & PAGE_CLASSES:
            drop(element)
        elif URL_RE.search(fill) or URL_RE.search(stroke):
            drop(element)
        elif element.get("opacity", "").strip().lower() in {"0", "0.0", "0.00"}:
            drop(element)
        else:
            element.attrib.pop("filter", None)
            style = element.get("style")
            if style and ("filter:" in style or "animation" in style):
                element.attrib.pop("style", None)
            if "font-family" in element.attrib:
                element.set("font-family",
                            "Microsoft YaHei, Noto Sans SC, sans-serif")

    # 4) 清掉动画移除后留下的空组与空 defs。
    changed = True
    while changed:
        changed = False
        for element in list(root.iter()):
            if element is root:
                continue
            if _local(element.tag) in {"g", "defs"} and len(element) == 0 \
                    and not (element.text or "").strip():
                drop(element)
                changed = True

    # 5) 统一的印刷字体与线帽；SVG data URI 无法使用父页面的字体。
    style = ET.Element(namespace + "style")
    style.text = PRINT_STYLE
    root.insert(0, style)

    # 6) 文字与属性里的旧配色、emoji 一并清理。
    for element in root.iter():
        for key, value in list(element.attrib.items()):
            element.set(key, _map_colors(EMOJI_RE.sub("", value)))
        if element.text:
            element.text = EMOJI_RE.sub("", element.text)
        if element.tail:
            element.tail = EMOJI_RE.sub("", element.tail)

    if namespace:
        ET.register_namespace("", SVG_NS)
    return ET.tostring(root, encoding="unicode")
