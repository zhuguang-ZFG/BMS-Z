# -*- coding: utf-8 -*-
"""handraw.py —— 手绘纸墨皮肤：108 张 SVG 动画的唯一调色板、纸纹与描边规则。

风格来源（handraw-style 风格库，选型与依据见 analog-book/HANDRAW-STYLE.md）：
  * 画风 FA-029「Geometric Diagrammatic Narrative」——几何精密线条、信息图式留白、
    色彩克制（只取线条/留白/低饱和这三条正向外显特征，不借用任何画面主体）。
  * 主题色 C-30 象牙白（纸）/ C-31 佩恩灰（墨）/ C-29 赭石（标记）。

三个约束决定了这里的写法：
  1. 明暗双模必须共用一套规则——深色不是另画一张图，而是同一组 token 的换色；
  2. 文字对比度 ≥3:1（scripts/test_svg_contrast.py 在 Chromium 里逐字测量）；
  3. generate_svgs.py 仍是唯一生成源，本模块只做「皮肤」，不碰任何图元语义。
"""
from __future__ import annotations

import hashlib
import re

# ---------------------------------------------------------------------------
# 1. token：一处定义，SVG / 站点 / 整书三处引用
# ---------------------------------------------------------------------------
# 纸墨是中性色（明暗对称换算）；六个语义色要拆成三种用法：
#   text   → 深色主题下换亮档（深底上的字）
#   fill   → 深色主题下换深档（浅字/深字的色块都压得住）
#   stroke → 深色主题下换中档（线要看得见）
# 一个语义色只给一个深色值是行不通的：同一支绿既要当深底上的文字，
# 又要当文字下面的色块，两者对亮度的要求正好相反。
NEUTRALS = {
    "paper":   ("#fdf8ea", "#141310"),   # 画布（象牙白 / 焦墨）
    "paper2":  ("#f6eedb", "#1d1a14"),   # 次级纸面（卡片底、面板）
    "edge":    ("#e0d3b8", "#3b3529"),   # 纸边、分隔线
    "rule":    ("#c9bb9d", "#4a4436"),   # 网格、坐标轴发丝线
    "ink":     ("#16202b", "#ece4d3"),   # 正文与主线条
    "ink2":    ("#37424e", "#cfc6b4"),   # 次级文字
    "muted":   ("#5b666f", "#a79e8b"),   # 弱化文字
    "faint":   ("#8b8272", "#857c6c"),   # 装饰性文字/线
}

FAMILIES = {
    #           浅色（= 文字/描边用的深档）  深色文字    深色色块    深色描边
    "blue":   ("#1f5d7a", "#7fb7cf", "#2b4d5f", "#6fa3b9"),
    "sky":    ("#2f7f96", "#8ac9d8", "#2b5660", "#77b2c1"),
    "green":  ("#3d6b4a", "#98c096", "#2f4a33", "#7aa87c"),
    "red":    ("#a8321f", "#e0907a", "#55231b", "#c07a63"),
    "amber":  ("#a4630f", "#dcab63", "#553a17", "#c08a45"),
    "purple": ("#6b3f63", "#c4a2bf", "#452c40", "#a17c9b"),
}

TINTS = {
    "blue_t":   ("#e6eff3", "#17262e"),
    "sky_t":    ("#e4f1f3", "#15262a"),
    "green_t":  ("#e8efe6", "#182418"),
    "red_t":    ("#f6e7e1", "#281a16"),
    "amber_t":  ("#f7eedb", "#292114"),
    "purple_t": ("#efe8ee", "#241c22"),
}

TOKENS = {**{k: v for k, v in NEUTRALS.items()},
          **{k: (v[0], v[1]) for k, v in FAMILIES.items()},
          **TINTS}
LIGHT = {name: pair[0] for name, pair in TOKENS.items()}

# 旧模板的 Tailwind 高饱和色 → 语义族 / 中性 token。
LEGACY = {
    "#ffffff": "paper", "#fff": "paper", "#eef2f8": "paper2",
    "#f8fafc": "paper2", "#f1f5f9": "paper2",
    "#eff6ff": "blue_t", "#dbeafe": "blue_t", "#e0f2fe": "sky_t",
    "#ecfdf5": "green_t", "#d1fae5": "green_t",
    "#fffbeb": "amber_t", "#fff7ed": "amber_t",
    "#fef2f2": "red_t", "#fee2e2": "red_t",
    "#e2e8f0": "edge", "#cbd5e1": "rule",
    "#94a3b8": "faint", "#8497ad": "faint",
    "#64748b": "muted", "#475569": "muted",
    "#334155": "ink2", "#1e293b": "ink", "#0f172a": "ink",
    "#0a1020": "paper", "#141d30": "paper",
    # 蓝族
    "#2563eb": "blue", "#1d4ed8": "blue", "#3b82f6": "blue",
    "#0284c7": "sky", "#0369a1": "sky", "#0ea5e9": "sky",
    "#60a5fa": "sky", "#7dd3fc": "sky", "#38bdf8": "sky",
    "#0891b2": "sky", "#93c5fd": "sky",
    # 绿族
    "#059669": "green", "#10b981": "green", "#34d399": "green", "#065f46": "green",
    # 红族
    "#dc2626": "red", "#b91c1c": "red", "#991b1b": "red",
    "#f87171": "red", "#fca5a5": "red", "#fecaca": "red", "#450a0a": "red",
    # 赭族
    "#f59e0b": "amber", "#b45309": "amber", "#92400e": "amber",
    "#fbbf24": "amber", "#fcd34d": "amber", "#451a03": "amber", "#431407": "amber",
    # 紫族
    "#7c3aed": "purple", "#a78bfa": "purple",
}

# 这些旧色原本是「浅色块」：作形状填充时必须落到水彩淡染（*_t），
# 否则墨色文字会压在深色块上（这正是旧模板用 #065f46 深字配 #34d399 浅底的写法）。
WASH_LEGACY = {
    "#34d399", "#10b981", "#60a5fa", "#7dd3fc", "#38bdf8", "#93c5fd",
    "#f87171", "#fca5a5", "#fecaca", "#fbbf24", "#fcd34d", "#a78bfa",
}

# 手写体只在标题上出现：11~13px 的楷体在屏幕上笔画过细，正文标签一律留在无衬线体。
HAND_FONT = ("'KaiTi','STKaiti','Kaiti SC','LXGW WenKai','Noto Serif CJK SC',"
             "'Source Han Serif SC','Songti SC','SimSun','Noto Serif SC',serif")
# 与 HAND_FONT 同理：楷体/微软雅黑/苹方只在中文桌面系统里有，Linux 与 Android
# 上没有就会掉到通用 sans-serif。SVG 以 <img> 载入时吃不到页面 @font-face，
# 只能靠系统字体名兜底，所以把 Linux 常见的 CJK 无衬线也列进去。
SANS_FONT = ('"Segoe UI","Microsoft YaHei","PingFang SC",'
             '"Hiragino Sans GB","Noto Sans CJK SC","Source Han Sans SC",'
             '"Noto Sans SC",sans-serif')

DARK = {
    name: (pair[1] if name in NEUTRALS else pair[1]) for name, pair in TOKENS.items()
}

HEX_ATTR = re.compile(r'\b(fill|stroke|stop-color|flood-color)="(#[0-9a-fA-F]{3,6})"')
LINE_TAG = re.compile(r'<line\b([^>]*?)/>')
ATTR = re.compile(r'([a-zA-Z-][a-zA-Z0-9-]*)="([^"]*)"')
SHAPES = ("rect", "circle", "path", "line", "polygon", "polyline", "ellipse", "g")
ELEMENT = re.compile(r'<(text|' + "|".join(SHAPES) + r')\b[^>]*>')


# ---------------------------------------------------------------------------
# 2. 色彩：旧色 → token（按元素角色分工）→ 明/暗两套
# ---------------------------------------------------------------------------
def _target(raw: str, element: str, attribute: str) -> tuple[str, str] | None:
    """把一个旧色解析成「token 名, 明色」。角色决定落点，见 FAMILIES 注释。"""
    name = LEGACY.get(raw)
    if name is None:
        return None
    if name in NEUTRALS or name in TINTS:
        return name, LIGHT[name]
    text_role = element == "text"
    if text_role:
        return name, FAMILIES[name][0]
    if attribute == "stroke":
        return name, FAMILIES[name][0]
    if raw in WASH_LEGACY:
        tint = f"{name}_t"
        return tint, LIGHT[tint]
    return name, FAMILIES[name][0]


def retint(text: str) -> str:
    """逐元素换色：文字、色块、描边各走各的落点（只动颜色属性，不动几何）。"""
    def map_tag(match: re.Match) -> str:
        tag = match.group(0)
        element = match.group(1)

        def map_attr(am: re.Match) -> str:
            attribute, raw = am.group(1), am.group(2).lower()
            resolved = _target(raw, element, attribute)
            if resolved is None:
                return am.group(0)
            return f'{attribute}="{resolved[1]}"'
        return HEX_ATTR.sub(map_attr, tag)
    return ELEMENT.sub(map_tag, text)


def _luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    channels = []
    for i in (0, 2, 4):
        c = int(value[i:i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg: str, bg: str) -> float:
    a, b = _luminance(fg), _luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def token_css() -> str:
    """浅/深两套配色与纸纹、描边规则；字符串直接塞进每个 SVG 的 <style>。"""
    rules = []
    for name, pair in NEUTRALS.items():
        light, dark = pair
        rules.append(f'[fill="{light}"]{{fill:{dark}}}\n'
                     f'[stroke="{light}"]{{stroke:{dark}}}')
    # 纸色当文字用时压在深色色块上：深色主题里它必须仍然是浅色。
    rules.append(f'text[fill="{LIGHT["paper"]}"]{{fill:#f9f3e3}}')
    for name, tint in TINTS.items():
        light, dark = tint
        rules.append(f'[fill="{light}"]{{fill:{dark}}}')
    for name, (light, dark_text, dark_fill, dark_stroke) in FAMILIES.items():
        rules.append(f'text[fill="{light}"]{{fill:{dark_text}}}')
        rules.append(f':is({",".join(SHAPES)})[fill="{light}"]{{fill:{dark_fill}}}')
        rules.append(f'[stroke="{light}"]{{stroke:{dark_stroke}}}')
    paint = "\n".join(rules)
    return f'''<style>
text{{font-family:{SANS_FONT};}}
line,path,polyline,polygon{{stroke-linecap:round;stroke-linejoin:round}}
.page-bg{{fill:url(#bgL)}}
.page-grain{{opacity:.5}}
.page-vig{{opacity:1}}
.page-hdr{{fill:url(#hdr)}}
@media (prefers-color-scheme: dark){{
.page-bg{{fill:url(#bgD)}}
.page-grain{{opacity:.34}}
.page-vig{{opacity:.5}}
.page-hdr{{fill:url(#hdrD)}}
{paint}
}}
</style>'''


def svg_defs(width: int, height: int) -> str:
    """纸面：暖象牙底 + 纸纤维颗粒 + 铅笔点阵 + 赭石表头淡染。

    保留 bgL/bgD/hdr/dots 这些 id 与 .page-* 类名——印刷管线
    （analog-book/book/svg_refine.py）靠 `id="bgL"` 判定旧模板并整块剥掉底纹。
    """
    # 浅色底：paper → paper2 的**浅档**。#fdf8ea→#141310 会让每张图的背景从象牙渐变到近黑
    # （page-bg 铺满整幅，底部三分之一彻底变暗），这条曾把 112 张图的下半页压成黑带。
    paper, paper2 = NEUTRALS["paper"][0], NEUTRALS["paper2"][0]
    dark_paper, dark_paper2 = NEUTRALS["paper"][1], NEUTRALS["paper2"][1]
    ink, amber = LIGHT["ink"], LIGHT["amber"]
    dark_amber = FAMILIES["amber"][1]
    return f'''<defs>
<linearGradient id="bgL" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{paper}"/><stop offset="1" stop-color="{paper2}"/>
</linearGradient>
<linearGradient id="bgD" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{dark_paper}"/><stop offset="1" stop-color="{dark_paper2}"/>
</linearGradient>
<radialGradient id="vig" cx="0.5" cy="0.44" r="0.78">
<stop offset="0.55" stop-color="{ink}" stop-opacity="0"/>
<stop offset="1" stop-color="{ink}" stop-opacity="0.055"/>
</radialGradient>
<linearGradient id="hdr" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{amber}" stop-opacity="0.10"/>
<stop offset="0.55" stop-color="{amber}" stop-opacity="0.028"/>
<stop offset="1" stop-color="{amber}" stop-opacity="0"/>
</linearGradient>
<linearGradient id="hdrD" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{dark_amber}" stop-opacity="0.13"/>
<stop offset="0.55" stop-color="{dark_amber}" stop-opacity="0.04"/>
<stop offset="1" stop-color="{dark_amber}" stop-opacity="0"/>
</linearGradient>
<pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse">
<circle cx="2.5" cy="3.5" r="0.9" fill="{LIGHT['rule']}"/>
<circle cx="19" cy="11" r="0.55" fill="{LIGHT['rule']}" opacity="0.7"/>
<circle cx="11.5" cy="22" r="0.6" fill="{LIGHT['rule']}" opacity="0.55"/>
</pattern>
<filter id="soft" x="-40%" y="-40%" width="180%" height="180%">
<feDropShadow dx="0" dy="1.4" stdDeviation="2" flood-color="{ink}" flood-opacity="0.13"/>
</filter>
<filter id="pglow" x="-70%" y="-70%" width="240%" height="240%">
<feGaussianBlur stdDeviation="1.7" result="b"/>
<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
</defs>'''


# ---------------------------------------------------------------------------
# 3. 手绘笔触：直线微弯（不引入 filter——每帧重算的位移滤镜会让 108 张
#    动画在低端机上抖成幻灯片，而几何层面的微弯是零成本、可缓存的）
# ---------------------------------------------------------------------------
def _seed(*numbers: float) -> float:
    raw = ",".join(f"{n:.2f}" for n in numbers).encode()
    digest = hashlib.sha256(raw).hexdigest()
    return (int(digest[:8], 16) / 0xFFFFFFFF) * 2 - 1  # -1 .. 1


def bow_lines(text: str, strength: float = 1.0) -> str:
    """`<line>` → 微微内收的二次贝塞尔；短刻度线保持笔直（手绘也不抖机械刻线）。

    `strength` 只给静态图放大弯度用；动画必须留在 1.0——每帧重算的
    位移滤镜会让 108 张动画在低端机上抖成幻灯片，几何微弯才零成本。
    """
    def repl(match: re.Match) -> str:
        attrs = dict(ATTR.findall(match.group(1)))
        try:
            x1 = float(attrs.pop("x1", "0"))
            y1 = float(attrs.pop("y1", "0"))
            x2 = float(attrs.pop("x2", "0"))
            y2 = float(attrs.pop("y2", "0"))
        except ValueError:
            return match.group(0)
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if length < 14:
            return match.group(0)
        wobble = min(1.5, length * 0.0045) * strength * _seed(x1, y1, x2, y2)
        mx = (x1 + x2) / 2 - (y2 - y1) / length * wobble
        my = (y1 + y2) / 2 + (x2 - x1) / length * wobble
        rest = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        spacer = " " if rest else ""
        d = f"M{x1:g} {y1:g} Q{mx:.2f} {my:.2f} {x2:g} {y2:g}"
        # fill="none" 不能省：<line> 没有填充概念，<path> 的默认填充是黑色。
        # 省掉它，那段微弯就会沿弦闭合成一条 1px 的黑色月牙（印刷管线还会放大它）。
        return f'<path d="{d}" fill="none"{spacer}{rest}/>'
    return LINE_TAG.sub(repl, text)


STROKED_SHAPE = re.compile(
    r'<(path|polygon|polyline|circle|ellipse|rect)\b([^>]*)>')


def stroke_only(text: str) -> str:
    """给「只有描边、没写 fill」的形状补 fill="none"。

    这些元素此前靠 `<line>` 或默认值活着；一旦默认黑填充生效，图上会出现
    看不见来源的黑色细缝，印刷管线把滤镜去掉后尤其明显。
    """
    def repl(match: re.Match) -> str:
        tag, body = match.group(1), match.group(2)
        if 'fill=' in body or 'stroke=' not in body:
            return match.group(0)
        # 放在标签名之后而不是属性末尾：自闭合的 `... />` 后面追加属性会写出
        # `<path ... / fill="none">` 这种非良构 XML（4 张图当场解析失败）。
        return f'<{tag} fill="none"{body}>'
    return STROKED_SHAPE.sub(repl, text)


# ---------------------------------------------------------------------------
# 3b. 静态图专用：卡片重影墨线 + 纸纤维。动画走 apply()，碰不到这两层。
# ---------------------------------------------------------------------------
RECT_TAG = re.compile(r'<rect\b([^>]*?)/>')


def echo_containers(text: str, strength: float = 1.0) -> str:
    """给带描边的卡片补一条错位重影墨线，做出手绘复描的观感。

    只偏移重影，不动原 rect 的坐标与属性：卡片里的文字因此一个像素都不挪。
    小格子（表格、图例）跳过——密排矩形双描边会糊成重影噪声。
    """
    def repl(match: re.Match) -> str:
        attrs = dict(ATTR.findall(match.group(1)))
        if attrs.get("stroke", "none") in ("none", "transparent"):
            return match.group(0)
        if attrs.get("class", "").startswith("page-"):
            return match.group(0)
        if "transform" in attrs:
            # 摆放坐标在 transform 里，照抄 attrs 会把重影放回未旋转原点。
            return match.group(0)
        try:
            x = float(attrs.get("x", "0"))
            y = float(attrs.get("y", "0"))
            w = float(attrs["width"])
            h = float(attrs["height"])
        except (KeyError, ValueError):
            return match.group(0)
        if w < 60 or h < 36:
            return match.group(0)
        sx = _seed(x, y, w, h)
        sy = _seed(y, x, h, w)
        dx = (1.0 + 0.6 * abs(sx)) * strength * (1 if sx >= 0 else -1)
        dy = (0.6 + 0.4 * abs(sy)) * strength * (1 if sy >= 0 else -1)
        rot = 0.12 * _seed(x + w, y + h, w, h) * strength
        clone = " ".join(f'{k}="{v}"' for k, v in attrs.items()
                         if k not in ("fill", "opacity", "class", "transform"))
        return (f'{match.group(0)}\n<rect class="ink-echo" {clone} fill="none" '
                f'opacity="0.32" transform="translate({dx:.2f} {dy:.2f}) '
                f'rotate({rot:.2f} {x + w / 2:.1f} {y + h / 2:.1f})"/>')
    return RECT_TAG.sub(repl, text)


def fiber_defs() -> str:
    """纸纤维：一小组确定性的短笔触，叠在点阵纸纹之上。"""
    rule = LIGHT["rule"]
    return f'''<defs>
<pattern id="fiber" width="96" height="96" patternUnits="userSpaceOnUse" patternTransform="rotate(-6)">
<path d="M8 18 q16 -2.2 36 -0.4" stroke="{rule}" stroke-width="0.55" fill="none" stroke-opacity="0.55"/>
<path d="M54 12 q10 1.4 22 0.2" stroke="{rule}" stroke-width="0.45" fill="none" stroke-opacity="0.4"/>
<path d="M20 52 q14 1.8 30 -0.6" stroke="{rule}" stroke-width="0.5" fill="none" stroke-opacity="0.45"/>
<path d="M62 66 q12 -1.6 24 0.4" stroke="{rule}" stroke-width="0.45" fill="none" stroke-opacity="0.38"/>
<path d="M14 84 q18 1.4 34 -0.2" stroke="{rule}" stroke-width="0.5" fill="none" stroke-opacity="0.42"/>
</pattern>
</defs>'''


def fiber_layer(width: float, height: float) -> str:
    w, h = int(float(width)), int(float(height))
    return (f'\n{fiber_defs()}\n'
            f'<rect class="page-fiber" width="{w}" height="{h}" '
            f'fill="url(#fiber)" opacity="0.55"/>\n')


TEXT_ELEMENT = re.compile(r'(<text\b[^>]*>)(.*?)(</text>)', re.S)


def text_width(plain: str, size: float) -> float:
    """粗略字宽：汉字与全角标点按 1em，拉丁/数字按 0.56em，空格 0.3em。"""
    total = 0.0
    for ch in plain:
        if ch == " ":
            total += 0.30 * size
        elif ord(ch) < 0x2E80:
            total += 0.56 * size
        else:
            total += size
    return total


def header_decor(text: str, canvas_width: int = 1000) -> str:
    """静态场景页眉：左对齐 38px 标题换手写体，背后铺马克笔淡染。

    场景由 `header()` 生成 x=52 / y=58 / 38px 的标题，几何与动画标题
    （y=29 / 19px 居中）不同；`title_decor` 的正则匹配不到它，所以此前
    117 张静态图的标题装饰从未生效。内联 style 才能压过 token_css 里
    `text{font-family:...}` 的全局规则（CSS 规则优先于 presentation 属性）。
    幂等：已带 style 的标题不再加工。
    """
    done = False

    def repl(match: re.Match) -> str:
        nonlocal done
        tag, content, close = match.group(1), match.group(2), match.group(3)
        attrs = dict(ATTR.findall(tag))
        if (done or attrs.get("y") != "58"
                or attrs.get("font-size") != "38" or "style" in attrs):
            return match.group(0)
        done = True
        x = float(attrs.get("x", "52"))
        size = 38.0
        plain = re.sub(r'<[^>]+>', '', content)
        right = min(canvas_width - 14.0,
                    x + text_width(plain, size) + 9)
        wash = marker_wash(x - 8.0, right, 23.5, 64.0,
                           seed=x + len(plain))
        style = f'font-family:{HAND_FONT};font-weight:400'
        return f'{wash}{tag[:-1]} style="{style}">{content}{close}'

    return TEXT_ELEMENT.sub(repl, text)


# ---------------------------------------------------------------------------
# 4. 标题：手写体 + 赭石马克笔下划线
# ---------------------------------------------------------------------------
TITLE_TEXT = re.compile(
    r'(<text\s+x="[\d.]+"\s+y="29"\s+text-anchor="middle"\s+'
    r'font-size="19"\s+font-weight="bold"\s+fill="[^"]*")\s*>')
SWASH = (r'<path d="M{x0:.0f} {y:.0f} c {q1:.0f} 3.4 {q2:.0f} -2.6 {q3:.0f} 0.4" '
         r'fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round" '
         r'opacity="0.5"/>')


def marker_wash(x0: float, x1: float, top: float, bot: float,
                seed: float) -> str:
    """标题背后的赭石马克笔淡染：多边形六点带确定性抖动，像手涂的荧光条。

    填充用 token 浅档，深色主题由 token_css 的 `[fill=...]` 规则自动换档。
    """
    cx = (x0 + x1) / 2
    j = _seed
    pts = [
        (x0 + 2.6 * j(seed, x0, 1), top + 2.0 * j(seed, top, 2)),
        (cx + (cx - x0) * 0.48 * j(seed, cx, 3), top - 1.4 + 1.6 * j(seed, cx, 4)),
        (x1 - 2.2 * j(seed, x1, 5), top + 2.4 * j(seed, x1, 6)),
        (x1 + 1.6 * j(seed, x1, 7), bot - 2.2 * j(seed, x1, 8)),
        (cx + (cx - x0) * 0.36 * j(seed, cx, 9), bot + 1.8 * j(seed, cx, 10)),
        (x0 - 1.3 * j(seed, x0, 11), bot - 2.0 * j(seed, x0, 12)),
    ]
    points = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return (f'<polygon class="marker-wash" points="{points}" '
            f'fill="{LIGHT["amber"]}" opacity="0.13"/>\n')


def title_decor(text: str, width: int, title: str, wash: bool = False) -> str:
    """标题改手写体，并在其下方补一道马克笔划线（长度按标题估算，居中收窄）。

    划线必须画在 `<text>` **之前**：它是同一坐标系的兄弟图元，塞进 `<text>` 里
    不会渲染（`<text>` 只认字符内容与 tspan），而且会被读屏当作标题的一部分。
    `wash` 只给静态图用：先在标题背后铺一条淡染，动画不得出现（apply 不传）。
    """
    # 有副标题的图（标题 y=29、副标题 y≈46）不画划线：那道笔触会横穿副标题。
    head = re.findall(r'<text\b[^>]*>', text)
    crowded = any(
        (m := re.search(r'\by="(\d+)"', tag))
        and 31 <= int(m.group(1)) < 65 and 'text-anchor="middle"' in tag
        for tag in head)
    decor = ""
    if not crowded:
        half = min(width * 0.40, max(60.0, len(title) * 9.6))
        if wash:
            decor += marker_wash(width / 2 - half, width / 2 + half,
                                 10.5, 36.0, seed=width)
        decor += SWASH.format(x0=width / 2 - half, y=38.0, q1=half * 0.5,
                              q2=half * 1.2, q3=half * 2,
                              color=LIGHT["amber"]) + "\n"
    # 楷体没有真正的粗体字重：font-weight:bold 会让 Chrome 合成假粗，笔画被抹平成
    # 黑体观感。这里显式回到 400，手写笔锋才留得住。
    style = f'font-family:{HAND_FONT};font-weight:400'
    return TITLE_TEXT.sub(
        lambda m: f'{decor}{m.group(1)} style="{style}">', text, count=1)


def apply(text: str, width: int = 800, title: str | None = None) -> str:
    """皮肤入口：换色 → 直笔画弯 → 标题装饰。图元几何与文案一律不动。"""
    text = retint(text)
    text = stroke_only(bow_lines(text))
    if title:
        text = title_decor(text, width, title)
    return text
