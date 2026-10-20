"""封面美术：同源但更亮的「海报皮肤」，只给 publish 用。

成片保持深底低饱和的克制；封面在手机列表里只有一百多像素宽，必须第一眼就抓住人，
所以这里用一套更亮的配色：深海军蓝/青绿渐变底、琥珀集号徽章、双色超大标题、暖紫
问句条、三步 chips、右侧电池吉祥物。形状全部平涂 + 描边，不用渐变糊面——缩略图里
只有对比度、一个字、一条线能活下来。

所有半透明装饰都画在 RGBA 层上再 `alpha_composite`：`ImageDraw.Draw(rgb, "RGBA")`
在 RGB 底图上会忽略 alpha（CHANGELOG 记过这个坑），直接画会把「很轻的纹理」变成实心块。

版面按画幅分四套：16x9（横屏平台）、3x4（小红书）、9x16（抖音竖版）、1x1（合集）。
文字块按 zone 宽自动降号；吉祥物/气泡另有碰撞检查，谁压到字谁红。
"""

from __future__ import annotations

import math
from pathlib import Path

if __name__ == "__main__":  # pragma: no cover
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from PIL import Image, ImageDraw

import common

CYAN = common.ACCENTS["cyan"]
AMBER = common.ACCENTS["amber"]
PINK = common.ACCENTS["pink"]
NAVY = (24, 38, 64)
NAVY_DEEP = (15, 25, 44)
BUBBLE_FILL = (24, 32, 54)
Q_FILL = (43, 29, 60)
TXT = common.TXT
SMALL = common.SMALL

MAS = 4                                   # 吉祥物 4× 超采样：圆角与描边缩回才不毛


# ---------------------------------------------------------------- 背景与装饰

_BG_CACHE: dict = {}


def background(w: int, h: int) -> Image.Image:
    """封面底：横向三段深蓝/青绿渐变 + 右侧青光 + 左下暖光 + 斜细线 + 暗角。

    亮度地板守 L≥10：封面 selftest 的最暗 64×64 块门（≥8）与成片的黑帧门同源。
    """
    key = (w, h)
    hit = _BG_CACHE.get(key)
    if hit is not None:
        return hit.copy()
    yy, xx = np.mgrid[0:h, 0:w].astype("float32")
    t = (xx / max(w - 1, 1))[..., None]
    stops = [(0.0, (7, 26, 36)), (0.55, (16, 24, 38)), (1.0, (27, 25, 36))]
    base = np.zeros((h, w, 3), dtype="float32")
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        m = ((t[..., 0] >= p0) & (t[..., 0] <= p1)).astype("float32")
        k = np.clip((t[..., 0] - p0) / (p1 - p0), 0, 1)[..., None]
        seg = np.array(c0, dtype="float32") * (1 - k) + np.array(c1, dtype="float32") * k
        base += seg * m[..., None]
    # 右侧青色光：封面最亮的一块，把吉祥物从底上托起来
    d2 = ((xx - w * 0.80) / (w * 0.46)) ** 2 + ((yy - h * 0.28) / (h * 0.48)) ** 2
    glow = np.exp(-d2)
    base[..., 0] += glow * 6
    base[..., 1] += glow * 30
    base[..., 2] += glow * 40
    # 左下暖光：双色调，避免整张单色
    d2w = ((xx - w * 0.12) / (w * 0.52)) ** 2 + ((yy - h * 0.86) / (h * 0.46)) ** 2
    warm = np.exp(-d2w)
    base[..., 0] += warm * 26
    base[..., 1] += warm * 12
    base[..., 2] += warm * 6
    vd2 = ((xx - w / 2) / (w * 0.75)) ** 2 + ((yy - h / 2) / (h * 0.75)) ** 2
    base *= (1.0 - 0.16 * np.clip(vd2 - 0.32, 0, 1))[..., None]
    img = Image.fromarray(np.clip(base, 10, 255).astype("uint8"), "RGB")

    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    step = max(96, int(min(w, h) * 0.13))
    for off in range(-h, w + h, step):
        d.line([(off, 0), (off + h, h)], fill=(140, 210, 235, 9), width=2)
        d.line([(off + 4, 0), (off + 4 + h, h)], fill=(255, 210, 150, 5), width=1)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def _shadow(d, xy, text, font, fill, anchor="la", off: int = 3, shadow=(4, 7, 12)):
    x, y = xy
    d.text((x, y + off), text, font=font, fill=shadow, anchor=anchor)
    d.text((x, y), text, font=font, fill=fill, anchor=anchor)


def _fit(text: str, kind: str, max_w: float, hi: int, lo: int, step: int = 2):
    size = hi
    while size > lo:
        f = common.font(kind, size)
        if f.getlength(text) <= max_w:
            return f
        size -= step
    return common.font(kind, lo)


def _fit_all(lines: list[str], kind: str, max_w: float, hi: int, lo: int, step: int = 2):
    size = hi
    while size > lo:
        f = common.font(kind, size)
        if all(f.getlength(s) <= max_w for s in lines):
            return f
        size -= step
    return common.font(kind, lo)


def _ruler(d, x0: float, x1: float, y: float, color, step: int = 26, long_every: int = 4):
    """一条像量尺的刻度线：短刻度 + 每四格一根长刻度。问句条下方的“本集尺子”靠它成句。"""
    n = 0
    x = x0
    while x <= x1:
        ln = 9 if n % long_every == 0 else 4
        d.line([(x, y - ln), (x, y)], fill=color, width=2)
        x += step
        n += 1
    d.line([(x0, y), (x1, y)], fill=color, width=1)


def _star(d, cx: float, cy: float, r: float, fill):
    """四角星：外半径 r、内半径 0.26r，是封面里的“亮点”而非主体。"""
    pts = []
    for i in range(8):
        ang = -math.pi / 2 + i * math.pi / 4
        rad = r if i % 2 == 0 else r * 0.26
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=fill)


# ---------------------------------------------------------------- 电池吉祥物

_MASCOT_CACHE: dict = {}


def mascot(w: int, h: int, mood: str) -> Image.Image:
    """拟人电芯：圆角身体 + 琥珀极柱 + 电量条 + 表情。按 (尺寸, 心情) 缓存。"""
    key = (w, h, mood)
    hit = _MASCOT_CACHE.get(key)
    if hit is not None:
        return hit
    W, H = w * MAS, h * MAS
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ink = (10, 17, 28, 255)
    outline = CYAN + (255,)

    # 极柱
    tw0, tw1 = W * 0.40, W * 0.60
    ty0, ty1 = H * 0.075, H * 0.175
    d.rounded_rectangle([tw0, ty0, tw1, ty1], radius=W * 0.035, fill=AMBER + (255,),
                        outline=(120, 80, 10, 255), width=int(W * 0.012))

    # 身体
    bx0, by0, bx1, by1 = W * 0.14, H * 0.155, W * 0.86, H * 0.90
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=W * 0.17, fill=NAVY + (255,),
                        outline=outline, width=int(W * 0.022))
    d.rounded_rectangle([bx0 + W * 0.045, by0 + H * 0.03, bx1 - W * 0.045, by1 - H * 0.03],
                        radius=W * 0.14, outline=(70, 110, 150, 90), width=int(W * 0.008))

    # 电量条：三格，亮两格半
    lx0, lx1 = W * 0.715, W * 0.795
    ly0, ly1 = H * 0.28, H * 0.72
    d.rounded_rectangle([lx0, ly0, lx1, ly1], radius=W * 0.022, fill=(12, 20, 36, 255),
                        outline=(70, 100, 140, 255), width=int(W * 0.008))
    seg_h = (ly1 - ly0 - H * 0.04) / 3
    for i in range(3):
        sy0 = ly1 - H * 0.02 - (i + 1) * seg_h - i * H * 0.006
        sy1 = sy0 + seg_h
        if i < 2 or mood == "guard":
            d.rounded_rectangle([lx0 + W * 0.014, sy0, lx1 - W * 0.014, sy1],
                                radius=W * 0.012, fill=AMBER + (255,))

    # 眼睛
    eye_y = H * 0.40
    er = W * 0.058
    pupil = (8, 14, 24, 255)
    eyes = [(W * 0.375, eye_y), (W * 0.625, eye_y)]
    look = {"happy": (0.0, 0.0), "thinking": (-0.014, -0.020), "guard": (0.0, 0.006)}[mood]
    for ex, ey in eyes:
        d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(255, 255, 255, 255))
        pr = er * 0.46
        px, py = ex + W * look[0], ey + W * look[1]
        d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=pupil)
        d.ellipse([px - pr * 0.34, py - pr * 0.42, px + pr * 0.1, py - pr * 0.02],
                  fill=(255, 255, 255, 235))
        if mood == "guard":
            d.line([(ex - er * 1.05, ey - er * 0.92), (ex + er * 1.05, ey - er * 0.55)],
                   fill=ink, width=int(W * 0.014))

    # 眉毛：happy 平缓，thinking 一高一低，guard 内倾
    bw = int(W * 0.018)
    if mood == "happy":
        for ex, ey in eyes:
            d.line([(ex - er * 0.9, ey - er * 1.65), (ex + er * 0.9, ey - er * 1.65)],
                   fill=ink, width=bw)
    elif mood == "thinking":
        d.line([(eyes[0][0] - er, eye_y - er * 2.0), (eyes[0][0] + er * 0.8, eye_y - er * 2.3)],
               fill=ink, width=bw)
        d.line([(eyes[1][0] - er * 0.8, eye_y - er * 1.45), (eyes[1][0] + er, eye_y - er * 1.45)],
               fill=ink, width=bw)
    else:
        d.line([(eyes[0][0] - er, eye_y - er * 1.55), (eyes[0][0] + er * 0.9, eye_y - er * 2.05)],
               fill=ink, width=bw)
        d.line([(eyes[1][0] - er * 0.9, eye_y - er * 2.05), (eyes[1][0] + er, eye_y - er * 1.55)],
               fill=ink, width=bw)

    # 嘴
    mx, my = W * 0.5, H * 0.585
    if mood == "happy":
        d.arc([mx - W * 0.085, my - H * 0.035, mx + W * 0.085, my + H * 0.045],
              start=20, end=160, fill=ink, width=int(W * 0.016))
        for cx in (W * 0.255, W * 0.745):
            d.ellipse([cx - W * 0.038, my - H * 0.012, cx + W * 0.038, my + H * 0.028],
                      fill=PINK + (110,))
    elif mood == "thinking":
        d.ellipse([mx - W * 0.026, my - H * 0.012, mx + W * 0.026, my + H * 0.028],
                  outline=ink, width=int(W * 0.012))
    else:
        d.line([(mx - W * 0.07, my + H * 0.012), (mx + W * 0.07, my + H * 0.012)],
               fill=ink, width=int(W * 0.018))

    # 心情小符号
    if mood == "thinking":
        f = common.font("bold", max(18, int(W * 0.17)))
        d.text((W * 0.855, H * 0.16), "?", font=f, fill=AMBER + (255,), anchor="mm")
    elif mood == "guard":
        # 胸前小盾：琥珀底 + 深色感叹号
        sx, sy = W * 0.30, H * 0.74
        sr = W * 0.075
        d.polygon([(sx - sr, sy - sr * 0.8), (sx + sr, sy - sr * 0.8), (sx + sr, sy + sr * 0.2),
                   (sx, sy + sr), (sx - sr, sy + sr * 0.2)], fill=AMBER + (255,))
        f = common.font("bold", max(16, int(sr * 1.15)))
        d.text((sx, sy), "!", font=f, fill=NAVY_DEEP + (255,), anchor="mm")

    # 脚
    for fx in (W * 0.32, W * 0.68):
        d.rounded_rectangle([fx - W * 0.075, H * 0.875, fx + W * 0.075, H * 0.945],
                            radius=W * 0.032, fill=NAVY_DEEP + (255,), outline=outline,
                            width=int(W * 0.012))
    spr = layer.resize((w, h), Image.LANCZOS)
    _MASCOT_CACHE[key] = spr
    return spr


def _glow_ellipse(w: int, h: int, color, peak: int = 90) -> Image.Image:
    yy, xx = np.mgrid[0:h, 0:w].astype("float32")
    d2 = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2
    a = (np.exp(-d2 * 2.4) * peak).astype("uint8")
    rgba = np.zeros((h, w, 4), dtype="uint8")
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = color
    rgba[..., 3] = a
    return Image.fromarray(rgba, "RGBA")


def draw_mascot(img: Image.Image, box, mood: str):
    """把吉祥物贴进 box，并在身后垫一圈青光。返回实际占用的矩形（含光晕不外扩）。"""
    x, y, w, h = box
    glow = _glow_ellipse(int(w * 1.7), int(h * 1.5), CYAN, 70)
    img.paste(glow, (int(x + w / 2 - glow.width / 2), int(y + h / 2 - glow.height / 2)), glow)
    spr = mascot(w, h, mood)
    img.paste(spr, (x, y), spr)
    return (x, y, w, h)


def _bubble(img: Image.Image, box, text: str, tail: str = "bl", size: int = 30):
    """对话气泡：navy 底、粉描边、白字；尾巴指向吉祥物。返回实际矩形。"""
    x, y, w, h = (int(v) for v in box)
    layer = Image.new("RGBA", (w + 28, h + 44), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([0, 0, w, h], radius=22, fill=BUBBLE_FILL + (238,),
                        outline=PINK + (230,), width=3)
    tw = 16
    if tail in {"bl", "br"}:
        tx = 34 if tail == "bl" else w - 34
        d.polygon([(tx - tw, h - 2), (tx + tw, h - 2), (tx + (tw // 2 if tail == "br" else -tw // 2), h + 26)],
                  fill=BUBBLE_FILL + (238,))
        d.line([(tx - tw, h), (tx + (tw // 2 if tail == "br" else -tw // 2), h + 26),
                (tx + tw, h)], fill=PINK + (230,), width=3)
    elif tail in {"tl", "tr"}:
        tx = 34 if tail == "tl" else w - 34
        d.polygon([(tx - tw, 2), (tx + tw, 2), (tx + (tw // 2 if tail == "tr" else -tw // 2), -26)],
                  fill=BUBBLE_FILL + (238,))
    f = _fit(text, "bold", w - 36, size, 18)
    d.text((w / 2, h / 2), text, font=f, fill=TXT + (255,), anchor="mm")
    img.paste(layer, (x - 14, y - 14), layer)
    return (x, y, w, h)


# ---------------------------------------------------------------- 版面

LAYOUTS = {
    "16x9": dict(
        pad=112, series_y=54, pill_h=44, badge_y=146, badge_h=64,
        title_y=250, title_w=980, title_hi=150, title_lo=96, title_lead=1.10,
        q_y=690, q_w=980, q_h=100, q_font=42,
        chips_y=852, chip_w=350, chip_h=92, chip_gap=40, chip_layout="row",
        chip_hi=30, chip_lo=24, mascot=(1352, 296, 448, 604),
        bubble=(1188, 158, 396, 116), bubble_size=30, footer_y=1002, footer_size=28,
        big_no=(1640, 610, 470), stage_size=28,
    ),
    "3x4": dict(
        pad=64, series_y=44, pill_h=40, badge_y=116, badge_h=56,
        title_y=206, title_w=760, title_hi=100, title_lo=82, title_lead=1.12,
        q_y=536, q_w=952, q_h=104, q_font=36,
        chips_y=700, chip_w=306, chip_h=112, chip_gap=16, chip_layout="row",
        chip_hi=28, chip_lo=21, mascot=(700, 968, 320, 450),
        bubble=(470, 846, 340, 100), bubble_size=27, footer_y=1356, footer_size=30,
        big_no=(890, 1150, 310), stage_size=26,
    ),
    "9x16": dict(
        pad=72, series_y=76, pill_h=44, badge_y=152, badge_h=60,
        title_y=268, title_w=936, title_hi=104, title_lo=86, title_lead=1.12,
        q_y=576, q_w=936, q_h=116, q_font=38,
        chips_y=752, chip_w=936, chip_h=84, chip_gap=14, chip_layout="col",
        chip_hi=30, chip_lo=23, mascot=(560, 1236, 380, 520),
        bubble=(300, 1090, 400, 112), bubble_size=29, footer_y=1816, footer_size=30,
        big_no=(856, 1470, 390), stage_size=27,
    ),
    "1x1": dict(
        pad=56, series_y=40, pill_h=38, badge_y=94, badge_h=50,
        title_y=168, title_w=700, title_hi=84, title_lo=66, title_lead=1.12,
        q_y=380, q_w=620, q_h=84, q_font=30,
        chips_y=488, chip_w=560, chip_h=64, chip_gap=12, chip_layout="col",
        chip_hi=24, chip_lo=18, mascot=(720, 672, 300, 356),
        bubble=(660, 566, 300, 88), bubble_size=24, footer_y=1006, footer_size=26,
        big_no=(900, 790, 280), stage_size=24,
    ),
}


def _wrap_question(text: str, font, max_w: float) -> list[str]:
    """问句版标题折两行：优先在标点断，其次在宽度中点附近硬断。"""
    text = text.strip()
    if font.getlength(text) <= max_w:
        return [text]
    best = None
    for c in range(2, len(text) - 1):
        head, tail = text[:c].rstrip(), text[c:].lstrip()
        if not head or not tail:
            continue
        w1, w2 = font.getlength(head), font.getlength(tail)
        if w1 > max_w or w2 > max_w:
            continue
        prev = text[c - 1]
        if prev in "，。！？；：、,.!?;: " or prev.isspace():
            pen = 0.0                      # 标点/空格后断：最自然
        elif prev.isascii() and not prev.isalnum():
            pen = max_w * 0.15             # 英文 token 后断（"4.2 V" | "就算…"）
        else:
            pen = max_w * 0.45             # 中文词中间硬断：尽量不选
        cost = abs(w1 - w2) + pen
        if best is None or cost < best[0]:
            best = (cost, c)
    if best:
        return [text[:best[1]].rstrip(), text[best[1]:].lstrip()]
    cut = len(text) // 2
    while cut > 1 and font.getlength(text[:cut]) > max_w:
        cut -= 1
    return [text[:cut], text[cut:]]


def wrap_title(text: str, key: str, title_w: int | None = None) -> list[str]:
    """问句版大标题按目标画幅折两行（渲染时还会再按实际字号缩一次）。"""
    cfg = LAYOUTS[key]
    f = common.font("bold", cfg["title_hi"])
    return _wrap_question(text, f, title_w or cfg["title_w"])[:2]


def render(
    key: str,
    *,
    series_line: str,
    badge: str,
    stage: str,
    title: list[str],
    question: str,
    chips: list[list[str]],
    bubble: str,
    mood: str,
    right_note: str = "",
    footer: str = "",
    big_no: str = "",
    variant: str = "",
    title_w: int | None = None,
) -> tuple[Image.Image, dict]:
    """画一张封面，返回 (图, 元数据)。

    元数据是给 selftest 量渲染结果用的：文字块 zone、吉祥物/气泡矩形、每行实际字号
    与宽度。门读图不读版面公式，改画法能让门红，而不是门自己跟着改。
    """
    cfg = LAYOUTS[key]
    sizes = {"16x9": (1920, 1080), "3x4": (1080, 1440), "9x16": (1080, 1920), "1x1": (1080, 1080)}
    w, h = sizes[key]
    img = background(w, h)
    d = ImageDraw.Draw(img)
    pad = cfg["pad"]
    zones: dict[str, tuple[int, int, int, int]] = {}

    # 背景大集号：纹理，不抢字
    if big_no:
        fac = common.font("bold", cfg["big_no"][2])
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((cfg["big_no"][0], cfg["big_no"][1]), big_no, font=fac,
                                   fill=(120, 190, 245, 20), anchor="mm")
        img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"))

    # 系列胶囊
    f_series = common.font("text", 26 if key != "1x1" else 22)
    sw = f_series.getlength(series_line) + 36
    sx, sy = pad, cfg["series_y"]
    d.rounded_rectangle([sx, sy, sx + sw, sy + cfg["pill_h"]], radius=cfg["pill_h"] // 2,
                        outline=CYAN + (255,), width=2)
    d.text((sx + 18, sy + cfg["pill_h"] / 2), series_line, font=f_series,
           fill=common.TXT, anchor="lm")
    zones["series"] = (sx, sy, int(sw), cfg["pill_h"])

    # 琥珀集号徽章 + 阶段小字
    f_badge = common.font("bold", int(cfg["badge_h"] * 0.52))
    bw = f_badge.getlength(badge) + int(cfg["badge_h"] * 0.74)
    bx, by = pad, cfg["badge_y"]
    d.rounded_rectangle([bx, by, bx + bw, by + cfg["badge_h"]], radius=int(cfg["badge_h"] * 0.22),
                        fill=AMBER + (255,))
    d.text((bx + bw / 2, by + cfg["badge_h"] * 0.52), badge, font=f_badge,
           fill=NAVY_DEEP, anchor="mm")
    zones["badge"] = (bx, by, int(bw), cfg["badge_h"])
    f_stage = common.font("text", cfg["stage_size"])
    stage_x = bx + bw + 22

    # Q 角标：问句版专属。阶段小字放在 Q 之后画一次——两边都画会让两行字叠在一起。
    if variant == "q":
        qz = int(cfg["badge_h"] * 0.58)
        qx = bx + bw + 10
        d.rounded_rectangle([qx, by + (cfg["badge_h"] - qz) / 2, qx + qz, by + (cfg["badge_h"] + qz) / 2],
                            radius=int(qz * 0.26), fill=CYAN + (255,))
        fq = common.font("bold", int(qz * 0.66))
        d.text((qx + qz / 2, by + cfg["badge_h"] / 2), "Q", font=fq, fill=NAVY_DEEP, anchor="mm")
        stage_x = qx + qz + 18
    _shadow(d, (stage_x, by + cfg["badge_h"] * 0.52), stage, f_stage, SMALL, anchor="lm", off=2)

    # 双色超大标题：第一行白、第二行青
    tw_max = title_w or cfg["title_w"]
    f_title = _fit_all(title, "bold", tw_max, cfg["title_hi"], cfg["title_lo"])
    lead = int(f_title.size * cfg["title_lead"])
    ty = cfg["title_y"]
    for i, line in enumerate(title):
        fill = common.TXT if i == 0 else CYAN
        _shadow(d, (pad, ty + i * lead), line, f_title, fill, off=max(3, f_title.size // 28))
    title_w = max(f_title.getlength(s) for s in title)
    zones["title"] = (pad, ty, int(title_w), int(lead * len(title)))
    title_lines = [{"text": s, "width": round(f_title.getlength(s), 1),
                    "max_w": tw_max, "size": f_title.size} for s in title]

    # 暖紫问句条：左青细杠 + 右侧尺子 + 下缘刻度
    qx, qy = pad, cfg["q_y"]
    qw, qh = cfg["q_w"], cfg["q_h"]
    d.rounded_rectangle([qx, qy, qx + qw, qy + qh], radius=14, fill=Q_FILL + (255,),
                        outline=(110, 80, 140, 150), width=2)
    d.rounded_rectangle([qx + 8, qy + 14, qx + 16, qy + qh - 14], radius=4, fill=CYAN + (255,))
    f_note = common.font("bold", 26 if key != "1x1" else 20)
    note_w = f_note.getlength(right_note) if right_note else 0
    f_q = _fit(question, "bold", qw - 60 - note_w, cfg["q_font"], 22)
    _shadow(d, (qx + 34, qy + qh * 0.47), question, f_q, TXT, anchor="lm", off=2)
    if right_note:
        d.text((qx + qw - 22, qy + qh * 0.47), right_note, font=f_note, fill=AMBER, anchor="rm")
    _ruler(d, qx + 34, qx + qw - 24, qy + qh - 9, (120, 210, 225, 90))
    zones["question"] = (qx, qy, qw, qh)

    # 三步 chips：行排或列排；每片左上角有 01/02/03 序号
    f_hi = common.font("bold", cfg["chip_hi"])
    f_lo = common.font("text", cfg["chip_lo"])
    ch_x, ch_y = pad, cfg["chips_y"]
    chip_rects = []
    if cfg["chip_layout"] == "row":
        step_x = cfg["chip_w"] + cfg["chip_gap"]
        for i in range(len(chips)):
            cx = ch_x + i * step_x
            chip_rects.append((cx, ch_y, cfg["chip_w"], cfg["chip_h"]))
            if i:
                ax = cx - cfg["chip_gap"] / 2
                d.text((ax, ch_y + cfg["chip_h"] / 2), "›", font=common.font("bold", 34),
                       fill=AMBER, anchor="mm")
    else:
        for i in range(len(chips)):
            cy = ch_y + i * (cfg["chip_h"] + cfg["chip_gap"])
            chip_rects.append((ch_x, cy, cfg["chip_w"], cfg["chip_h"]))
    for i, ((top, bot), (cx, cy, cw, chh)) in enumerate(zip(chips, chip_rects, strict=True)):
        d.rounded_rectangle([cx, cy, cx + cw, cy + chh], radius=12, fill=(19, 33, 58, 235),
                            outline=CYAN + (150,), width=2)
        num = f"{i + 1:02d}"
        fn = common.font("mono", int(cfg["chip_hi"] * 0.82))
        nw = fn.getlength(num)
        d.text((cx + 12, cy + chh / 2), num, font=fn, fill=AMBER, anchor="lm")
        text_x = cx + 18 + nw
        d.text((text_x, cy + chh * 0.30), top, font=f_hi, fill=TXT, anchor="lm")
        d.text((text_x, cy + chh * 0.72), bot, font=f_lo, fill=AMBER, anchor="lm")
    chips_block = (min(r[0] for r in chip_rects), min(r[1] for r in chip_rects),
                   max(r[0] + r[2] for r in chip_rects) - min(r[0] for r in chip_rects),
                   max(r[1] + r[3] for r in chip_rects) - min(r[1] for r in chip_rects))
    zones["chips"] = tuple(int(v) for v in chips_block)
    chip_lines = [{"text": f"{t} {b}", "width": max(f_hi.getlength(t), f_lo.getlength(b)),
                   "max_w": cfg["chip_w"] - 34 - nw, "size": cfg["chip_hi"]}
                  for t, b in chips]

    # 底部弱化 CTA
    if footer:
        f_foot = common.font("text", cfg["footer_size"])
        d.text((pad, cfg["footer_y"]), "→", font=common.font("bold", cfg["footer_size"]),
               fill=CYAN, anchor="ls")
        d.text((pad + 30, cfg["footer_y"]), footer, font=f_foot, fill=SMALL, anchor="ls")
        zones["footer"] = (pad, cfg["footer_y"] - cfg["footer_size"], int(f_foot.getlength(footer) + 32),
                           cfg["footer_size"] + 6)

    # 吉祥物 + 气泡（气泡先画，尾巴被吉祥物压住一点才像“从它嘴里出来”）
    mb = tuple(int(v) for v in cfg["mascot"])
    if bubble:
        bb = _bubble(img, cfg["bubble"], bubble, tail="br", size=cfg["bubble_size"])
        zones["bubble"] = tuple(int(v) for v in bb)
    d = ImageDraw.Draw(img)
    mascot_rect = draw_mascot(img, mb, mood)

    # 星点：压在吉祥物周围，缩略图里是“亮”
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(layer)
    mx, my, mw, mh = mb
    stars = [
        (mx - mw * 0.10, my + mh * 0.10, mw * 0.045, CYAN + (220,)),
        (mx + mw * 1.02, my + mh * 0.06, mw * 0.060, AMBER + (230,)),
        (mx + mw * 0.94, my + mh * 0.58, mw * 0.034, PINK + (210,)),
        (mx - mw * 0.06, my + mh * 0.52, mw * 0.028, CYAN + (170,)),
    ]
    for sx2, sy2, sr, fill in stars:
        if 0 < sx2 < w and 0 < sy2 < h:
            _star(sd, sx2, sy2, sr, fill)
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"))

    meta = {
        "size": (w, h), "key": key, "zones": zones, "mascot": mascot_rect,
        "title_lines": title_lines, "chip_lines": chip_lines,
        "q_line": {"text": question, "width": round(f_q.getlength(question), 1),
                   "max_w": qw - 60 - note_w, "size": f_q.size},
        "title_size": f_title.size, "q_size": f_q.size,
        "question": question, "right_note": right_note,
        "badge": badge, "stage": stage, "series_line": series_line,
    }
    return img, meta


def selftest_zone_hits(meta: dict, margin: int = 12) -> list[str]:
    """文字与吉祥物/气泡的碰撞：文字 zone 外扩 margin 后不得压到吉祥物或气泡矩形。"""
    hits = []
    m = meta["mascot"]
    obstacles = [m] + ([meta["zones"]["bubble"]] if "bubble" in meta["zones"] else [])
    for name, z in meta["zones"].items():
        if name == "bubble":
            continue
        zx, zy, zw, zh = z
        zx, zy, zw, zh = zx - margin, zy - margin, zw + 2 * margin, zh + 2 * margin
        for o in obstacles:
            ox, oy, ow, oh = o
            if zx < ox + ow and ox < zx + zw and zy < oy + oh and oy < zy + zh:
                hits.append(f"{name} 与 {'吉祥物' if o is m else '气泡'} 相撞")
                break
    return hits
