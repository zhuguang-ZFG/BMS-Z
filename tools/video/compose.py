"""版面合成：时间轴 + clip 帧 → 一集的无声视频（+ 与烧字同源的一份 .srt）。

两种画幅是两套版面，不是裁切。竖屏尤其不能"把横屏中间那块抠出来"——这些电路图的
viewBox 是 800×500 到 800×826 不等，中心裁切会把左右两端的标注切掉，读者看到的是一半
的图。所以竖屏走三段式：顶部集数与段名、中部图按宽缩放、底部大字与字幕（字幕要大到
手机静音刷也能读）。

帧不落地：合成好的 RGB 直接管到 ffmpeg 的 rawvideo 输入，省掉一集两万张 PNG 的读写。
静帧（卡片、数字、清单）按"字幕条"缓存同一份字节，重复写出去，所以真正做画的帧数远小于
总帧数。

用法：
    python3 tools/video/compose.py --episode ep02-recognize-bms --aspect 16x9
    python3 tools/video/compose.py --episode ep02-recognize-bms --both
    python3 tools/video/compose.py --episode ep02-recognize-bms --preview 3 --aspect 9x16
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import spec as spec_mod  # noqa: E402

SERIES = "BMS 从入门到精通"

XFADE_FRAMES = 8                     # beat 边界交叉淡化的帧数（8 帧 = 0.267 s @30fps）
XFADE_OUT_FRAMES = 40                # 片尾淡出的帧数（40 帧 = 1.333 s，对齐音频 FADE_OUT=1.40 s）
XFADE_IN_FRAMES = 18                 # 片头淡入的帧数（18 帧 = 0.6 s，对齐 assemble 的 FADE_IN=0.60 s）
SEG_DIP_FRAMES = 6                   # 段切换两侧各淡几帧（合计 12 帧 = 0.4 s 的“过场”）


class ClipSource:
    """把一个 clip 的 mp4 解成帧，循环或定格。

    不一次性读进内存：一个 12 s 的 664×668 clip 是 480 MB 的 RGB。解到末尾就重启解码器，
    重启那 30 ms 摊在 12 s 的循环上看不见。
    """

    def __init__(self, mp4: Path, w: int, h: int, repeating: bool):
        self.mp4, self.w, self.h, self.repeating = mp4, w, h, repeating
        self.frame_bytes = w * h * 3
        self.proc: subprocess.Popen[bytes] | None = None
        self.last = None
        self.pos = 0
        self.open()

    def open(self):
        self.proc = subprocess.Popen(
            [common.ffmpeg_exe(), "-loglevel", "error", "-i", str(self.mp4),
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.pos = 0

    def close(self):
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
        self.proc = None

    def frame(self, index: int):
        from PIL import Image

        want = index
        if not self.repeating and self.last is not None and self.pos >= self.count:
            return self.last
        while self.pos <= want % max(self.count, 1) if self.repeating else self.pos <= want:
            if not self.proc or not self.proc.stdout:
                raise RuntimeError(f"clip 解码管道已关闭：{common.rel(self.mp4)}")
            raw = self.proc.stdout.read(self.frame_bytes)
            if len(raw) < self.frame_bytes:
                self.close()
                if not self.repeating:
                    return self.last
                self.open()
                continue
            self.last = Image.frombytes("RGB", (self.w, self.h), raw)
            self.pos += 1
            if self.pos > want % self.count if self.repeating else self.pos > want:
                break
        return self.last

    @property
    def count(self) -> int:
        meta = common.load_json(self.mp4.with_suffix(".json"), {}) or {}
        return int(meta.get("frames", 1)) or 1


class Layout:
    """一个画幅的字号与颜色。字号是量出来的：竖屏字幕 44 px 在 6 寸手机里约等于 12 pt。"""

    def __init__(self, geo):
        self.g = geo
        v = geo.portrait
        self.f_chip = common.font("text", 30 if v else 26)
        self.f_seg = common.font("bold", 40 if v else 32)
        # 字幕字号按“全部字幕都放得下”的上限取，不是拍一个偏小的数。横屏旧值 34 px 只占
        # 屏高 3.1%，而最宽字幕在 34 px 时仅用掉可用宽的 42%、放到 50 px 也才 61%——
        # 手机上是把字看小的根因。现取 44 px（屏高 4.1%），最宽字幕占 54%，仍留一半余量；
        # 配合 selftest 的“实际用号不得低于 40 px”，改了文案也不会悄悄缩回小字。
        self.f_cap = common.font("text", 46 if v else 44)
        self.f_on = common.font("bold", 58 if v else 46)
        self.f_big = common.font("bold", 190 if v else 230)
        self.f_card = common.font("bold", 86 if v else 96)
        self.f_list = common.font("text", 46 if v else 40)
        self.f_mono = common.font("mono", 40 if v else 34)
        # 字幕不是贴屏幕底边：竖屏下方要给平台文案/进度条留区，横屏也要避开播放器控件。
        self.caption_from_bottom = 290 if v else 88
        # 字幕带以**画面**为心。竖屏另要左右各守 10% 的侧边危险带——右侧是点赞/评论/分享
        # 动作栏，左下是评论区输入框（竖屏安全区：字幕带 75%–88% 高、10%–90% 宽）。
        # 旧写法 caption_right=150 把整条带子推向左：心落在 x=485 而画幅心是 540，
        # 偏心 55 px（5.1% 宽）——字幕看着就没居中，而 40px 下最宽字幕 886px 又顶满了
        # 890px 老带子，左右两边各差一点都放不下。现在左右同宽，心就是画幅心。
        self.caption_left = max(geo.pad, int(geo.w * 0.10)) if v else geo.pad
        self.caption_right = self.caption_left
        self.caption_width = geo.w - self.caption_left - self.caption_right
        # 由边距导出而非直接写画幅心：这样 selftest 的"带心在画幅心"量的才是真实几何，
        # 谁再把左右边距改得不相等，门立刻红。
        self.caption_cx = self.caption_left + self.caption_width / 2


def band_top(d, geo: common.Geometry, lay: Layout, no: int, seg_title: str):
    d.rectangle([0, 0, geo.w, geo.top], fill=common.INK)
    d.line([0, geo.top - 5, geo.w, geo.top - 5], fill=(68, 147, 248), width=5)
    chip = f"{SERIES} · 第 {no} 集"
    d.text((geo.pad, 34 if not geo.portrait else 60), chip, font=lay.f_chip, fill=common.SMALL)
    title = seg_title if spec_mod.text_width(seg_title) * _pt(lay) < geo.w - 2 * geo.pad else seg_title[:18] + "…"
    tx = geo.w / 2 if geo.portrait else geo.w - geo.pad
    d.text((tx, 30 if not geo.portrait else 108), title, font=lay.f_seg,
           fill=common.TXT, anchor="ma" if geo.portrait else "ra")


def _pt(lay: Layout) -> float:
    return 40.0 if lay.g.portrait else 32.0


CAPTION_MIN = 40  # 与实际用号门同一根线：缩号到此为止，再放不下就折行。
# 折行只能断在标点上——一句话中间硬断，读者要倒回去重读。
CAPTION_BREAK = "，。！？；：、,.!?;:"


def _caption_two_lines(text: str, size, width: float) -> list[str]:
    """一条字幕恰好折两行：优先在标点断，同时不许两行失衡。

    两条都不可少，各有实测事故：
    · 只贪心填满带宽（旧的 `wrap_to_width(text, size, width)`）——第一行吃到 840/864 px，
      剩下一枚"，"自成一行，比值 0.05；
    · 只贪心填半宽（`wrap_to_width(text, size, width/2)`）——880 px 的句子出**三**行，
      横竖放不下字幕安全带。
    所以在这里显式枚举断点：代价 = 两行宽度差 +（不在标点则加 0.30×带宽的罚分），
    并硬性排除——只剩标点的行、被拆开的一对"——"、任一行超带宽。
    """
    penalty = 0.30 * width
    best: tuple[float, int] | None = None
    for c in range(2, len(text) - 1):
        if text[c - 1:c + 1] == "——":
            continue                      # 破折号成对，别拆
        head, tail = text[:c].rstrip(), text[c:].lstrip()
        if len(head) < 2 or len(tail) < 2:
            continue
        if not any(ch not in CAPTION_BREAK for ch in head):
            continue
        if not any(ch not in CAPTION_BREAK for ch in tail):
            continue                      # 剩下半句只有标点 = 孤字行
        w1, w2 = size.getlength(head), size.getlength(tail)
        if w1 > width or w2 > width:
            continue
        cost = abs(w1 - w2) + (0.0 if text[c - 1] in CAPTION_BREAK else penalty)
        if best is None or cost < best[0]:
            best = (cost, c)
    if best is None:
        return [text]
    c = best[1]
    return [text[:c].rstrip(), text[c:].lstrip()]


def caption_block(text: str, lay: Layout) -> tuple:
    """一条字幕 → (字号, [行])。缩号只缩到 CAPTION_MIN，仍放不下就折行。

    为什么折行而不是继续缩：竖屏守左右 10% 侧边危险带后只剩 864 px，而 209 条字幕在
    40 px 下最宽 886 px——继续缩会把那一成字幕压到 38 px，字幕在手机上重新变小（这正是
    上一轮把 34 px 提到 44 px 要治的病）。折行保字号；两行也仍收在 75%–88% 高的字幕
    安全带里，且折行只往上长、不往下探。
    """
    size = lay.f_cap
    while size.size > CAPTION_MIN and size.getlength(text) > lay.caption_width:
        size = common.font("text", size.size - 2)
    if size.getlength(text) <= lay.caption_width:
        return size, [text]
    return size, _caption_two_lines(text, size, lay.caption_width)


def band_bottom(d, geo: common.Geometry, lay: Layout, on_screen: list[dict], caption: str,
                show_on_screen: bool):
    y0 = geo.h - geo.bottom
    d.rectangle([0, y0, geo.w, geo.h], fill=common.INK)
    d.line([0, y0, geo.w, y0], fill=common.EDGE, width=2)
    pad = geo.pad
    cx = geo.w // 2
    cursor = y0 + 22
    if show_on_screen:
        for line in on_screen:
            size = lay.f_on
            text = line["t"]
            while spec_mod.text_width(text) * (size.size / 46.0 if not geo.portrait else size.size / 58.0) > (geo.w - 2 * pad):
                size = common.font("bold", size.size - 4)
            d.text((cx, cursor), text, font=size, fill=common.TONES[line["tone"]], anchor="ma")
            cursor += size.size + 12
    if caption:
        size, lines = caption_block(caption, lay)
        step = int(round(size.size * 1.28))
        # 整块底边固定：单行与折行的收口都在同一位置，折行只往上长——下方留给平台文案/进度条。
        top = geo.h - lay.caption_from_bottom - step * (len(lines) - 1)
        for k, ln in enumerate(lines):
            d.text((lay.caption_cx, top + k * step), ln, font=size, fill=common.TXT, anchor="ma")


def draw_on_screen_box(d, box, lines, lay: Layout):
    x, y, w, h = box
    # 整块在文字区里居中，而且居中是**墨迹**不是 ascender 盒。旧写法从 y+10 起顶部对齐：
    # 横屏三行只占文字框 22%、下部空 76%，竖屏占 49%、空 46%（beat_base 实测），
    # 大块文字贴在区域顶上、下面一片黑。改成居中了还会差一截：58 px 的中文粗体墨迹顶在
    # ascender 下 13 px、墨迹心比 ascender 盒心低 2.5 px，按 ascender 盒居中"看起来仍偏低"
    # ——门量的是墨迹，所以这里按 getbbox 的墨迹范围算。
    fonts, sizes = [], []
    for line in lines:
        size = lay.f_on
        while common.font("bold", size.size).getlength(line["t"]) > w - 8 and size.size > 24:
            size = common.font("bold", size.size - 2)
        fonts.append(common.font("bold", size.size))
        sizes.append(size)
    tops = [f.getbbox(line["t"])[1] for f, line in zip(fonts, lines, strict=True)]
    bots = [f.getbbox(line["t"])[3] for f, line in zip(fonts, lines, strict=True)]
    last = sum(s.size + 14 for s in sizes[:-1]) if len(sizes) > 1 else 0
    cy = y + h / 2 - (tops[0] + last + bots[-1]) / 2
    for line, size in zip(lines, sizes, strict=True):
        d.text((x + 4, cy), line["t"], font=size, fill=common.TONES[line["tone"]])
        cy += size.size + 14


def card_panel_edges(img, geo) -> tuple[int, int] | None:
    """卡片面板描边的上下两行（整行接近 EDGE 色的行），只在主内容框的列范围内找。

    扫的是渲染结果，不是版面参数：门要能因为"画出来的面板变了"而红，而不是因为
    "算面板的函数自己变了"而红。找不到返回 None——面板没画也是一种失败。

    必须同时限定列范围和行范围：底带分隔线、画面底部那 6 px 色条也是 EDGE 附近的横边，
    不限列会把整幅第一行/最后一行当成面板边（实测那样量出 745 px 的假面板）；
    不限行会让底带分隔线混进首末行（实测把面板量成 603 px）。两处都限定在内容框内。

    只对**不贴 clip 的版面**用（card / checklist / quiz）。figure / split 的 beat_base
    不贴 clip，所以门看到的画面里没有图；但这几个函数都别拿去量贴了 clip 的交付帧：
    实测 `thermal-runaway.svg` 的图区跨度随动画相位从 618 漂到 996（5 个相位、极差 378 px，
    那支 clip 的帧间像素差 0–13.5，确认真的在动），亮度法如此，EDGE 扫法同期量出
    618/235/235/235/无、同样不稳——不是换扫法能救的，是那支 SVG 的边界本来就在动。
    另三支同样在动的 clip（帧间差 0–4.1：2.28 / 4.12 / 2.16）读数却稳（868 / 868 / 970，
    极差 0），所以漂移是 clip 属性而非测量毛病。要给图区设门得先有相位无关的量，例如按
    clip 的 viewBox 比例算几何，而不是扫描像素。"""
    import numpy as np

    a = np.asarray(img.convert("RGB")).astype(int)
    if a.ndim != 3:
        return None
    edge = np.array(common.EDGE)
    near = np.abs(a - edge).sum(axis=2) < 24
    x0, x1 = geo.pad + 8, geo.w - geo.pad - 8          # 面板描边在 pad 内，避开圆角
    lo, hi = geo.top + 10, geo.h - geo.bottom - 10     # 内容框的上下沿
    strip = near[lo:hi + 1, x0:x1]
    rows = np.flatnonzero(strip.sum(axis=1) > (x1 - x0) * 0.9) + lo
    if rows.size < 2:
        return None
    # 面板描边是两条各 2 px 的线段，不是长连续段——按跨高取最大段会在两条一样高时
    # 取到上边，量出 1 px 的面板（实测踩过）。取内容框内命中阈值的首末两行才对：
    # 上面那条是面板上边，下面那条是下边。
    return int(rows[0]), int(rows[-1])


def _panel_void(img, geo) -> int | None:
    """面板内最长的一段连续空白行（像素）。

    和 panel_content_span 一样扫渲染结果。只看内容总跨度会漏掉“断层”：进度条这类
    锚在面板底的元素会把跨度撑满，而中段其实空着一大片。
    """
    import numpy as np

    edges = card_panel_edges(img, geo)
    if edges is None:
        return None
    top, bot = edges
    a = np.asarray(img.convert("RGB")).astype(int)
    panel = np.array(common.INK_PANEL)
    band = a[top + 6:bot - 5]
    bright = (np.abs(band - panel).sum(axis=2) > 60).sum(axis=1)
    rows = bright > geo.w * 0.02
    if not rows.any():
        return None
    idx = np.flatnonzero(rows)
    # 相邻两行内容之间的最大行距；两端留白不算断层
    gaps = np.diff(idx)
    return int(gaps.max()) if gaps.size else 0


def content_rows(img, geo, lo: int | None = None, hi: int | None = None,
                 col_lo: int | None = None, col_hi: int | None = None) -> tuple[int, int] | None:
    """指定行/列范围内**亮于 INK 背景**的内容行上下沿，给没有面板的版面用。

    行范围可传：number 量整个内容框，split 只量它那块文字区（clip 占另外一畦，
    不限范围就会把图里的内容一起量进去）。列范围同样可传：横屏 split 的图在左半幅，
    不限列会把图的上下沿当成文字块。色板里所有内容色都远离 INK（见 panel_content_span），
    不存在"暗色看不见"的问题——用 ticks=0 的全未勾选清单实测过，与 ticks=5 跨度一致。

    别拿去量**贴了 clip 的画面**：亮度计数会把动画里运动元素的像素算进来，实测
    `thermal-runaway.svg` 的图区跨度在 5 个相位上从 618 漂到 996（详见 card_panel_edges
    的备注，含"改 EDGE 扫法同样不稳"的判决）。
    """
    import numpy as np

    a = np.asarray(img.convert("RGB")).astype(int)
    lo = geo.top + 10 if lo is None else lo
    hi = geo.h - geo.bottom - 10 if hi is None else hi
    x0 = 0 if col_lo is None else col_lo
    x1 = a.shape[1] if col_hi is None else col_hi
    band = a[lo:hi + 1, x0:x1]
    ink = np.array(common.INK)
    bright = (np.abs(band - ink).sum(axis=2) > 60).sum(axis=1)
    rows = np.flatnonzero(bright > (x1 - x0) * 0.02)
    if rows.size == 0:
        return None
    return int(rows[0]) + lo, int(rows[-1]) + lo


def panel_content_span(img, geo) -> tuple[int, int, int, int] | None:
    """面板的上下沿与**面板内**内容行的上下沿：(panel_top, panel_bot, content_top, content_bot)。

    和 card_panel_edges 一样扫渲染结果。内容行用"显著亮于面板底色的像素数"判，
    阈值随面板宽度归一：1080 画幅一行字占的行均值与 1920 画幅不同，固定阈值会漏。
    找不到返回 None——没面板或没内容都算失败。
    """
    import numpy as np

    edges = card_panel_edges(img, geo)
    if edges is None:
        return None
    top, bot = edges
    a = np.asarray(img.convert("RGB")).astype(int)
    panel = np.array(common.INK_PANEL)
    band = a[top + 6:bot - 5]
    # 每行亮于面板底色的像素数：文字、勾选框、进度条都算内容
    bright = (np.abs(band - panel).sum(axis=2) > 60).sum(axis=1)
    rows = np.flatnonzero(bright > geo.w * 0.02)
    if rows.size == 0:
        return None
    return top, bot, int(rows[0]) + top + 6, int(rows[-1]) + top + 6


def card_metrics(box, lines, lay: Layout) -> tuple[float, float, float]:
    """卡片的版面三件套：面板高、文字块高、上下留白。

    旧代码用基准字号 `sum(f_card.size + 22)` 估高度，于是面板恒等于整个内容框。
    还原旧实现后由 `card_panel_edges()` 实测：竖屏面板 1060 px（行 260–1320）对文字 194 px，
    比值 5.46；横屏 734 px（内容框全高）对 214 px，比值 3.43。一只 5 倍以上大于内容的
    盒子，读起来是空的。现在先按每行**实际会用到的字号**量文字块，面板再贴上去，
    留白与文字块成比例。顺带修掉一处 6 px 的居中漂移：旧代码把缩小后的行高加回未缩小的
    基准总和里。
    """
    sizes = []
    for line in lines:
        size = lay.f_card
        while size.getlength(line["t"]) > box[2] - 60 and size.size > 30:
            size = common.font("bold", size.size - 4)
        sizes.append(size)
    gap = 22
    text_h = sum(s.size for s in sizes) + gap * max(len(sizes) - 1, 0)
    pad_v = max(56, text_h * 0.55)
    return text_h + 2 * pad_v, text_h, pad_v


def draw_card(d, box, lines, lay: Layout, geo):
    x, y, w, h = box
    ph, text_h, pad_v = card_metrics(box, lines, lay)
    ph = min(ph, h)
    py = y + (h - ph) / 2
    d.rounded_rectangle([x, py, x + w, py + ph], radius=18, fill=common.INK_PANEL,
                        outline=common.EDGE, width=2)
    cy = py + pad_v + (ph - 2 * pad_v - text_h) / 2
    for line in lines:
        size = lay.f_card
        while size.getlength(line["t"]) > w - 60 and size.size > 30:
            size = common.font("bold", size.size - 4)
        d.text((x + w / 2, cy + size.size / 2), line["t"], font=size,
               fill=common.TONES[line["tone"]], anchor="mm")
        cy += size.size + 22


def draw_number(d, box, big: str, lines, lay: Layout, geo):
    import re

    x, y, w, h = box
    m = re.match(r"^(-?[\d.,%]+\s*[A-Za-zμ%Ω/·²]*|[\d.,%]+)(.*)$", big.strip())
    num, unit = (m.group(1), m.group(2)) if m else (big, "")
    size = lay.f_big
    while common.font("bold", size.size).getlength(num) > w - 40 and size.size > 60:
        size = common.font("bold", size.size - 8)
    # 数字块（大字 + 单位 + 说明行）整体在内容框里居中。旧写法把大字中心钉在
    # y + h*0.42，说明行又挂在下面，于是整块偏上：竖屏实测内容 628–877、块中心比框中心
    # 高 37 px（上空 35% vs 下空 42%），横屏同样偏 4 px。先量块高再定起点。
    sizes = []
    for line in lines:
        s = lay.f_on
        while s.getlength(line["t"]) > w - 40 and s.size > 24:
            s = common.font("bold", s.size - 4)
        sizes.append(s)
    # 居中的是**整块墨迹**，不是 em 盒。anchor="mm" 把锚点放在 em 盒中心，而中文粗体的
    # 墨迹心比 em 心低一截（58 px 低 2.5 px、190 px 低 9 px），说明行也是同一个 anchor，
    # 所以要把大字与每一行说明的墨迹范围都折进去解锚点：只校正大字的那个版本实测
    # 竖屏仍偏 11 px、动也不动。做法是把首行墨迹顶与末行墨迹底都写成 cy 的式子，
    # 令二者中点等于内容框中心。
    num_f = common.font("bold", size.size)
    nb = num_f.getbbox(num)
    n_em = sum(num_f.getmetrics()) / 2
    lab_f = [common.font("bold", s.size) for s in sizes]
    lb = [f.getbbox(line["t"]) for f, line in zip(lab_f, lines, strict=True)]
    l_em = [sum(f.getmetrics()) / 2 for f in lab_f]
    ly0 = size.size * 0.75                                   # 首行说明相对 cy 的偏移
    ly_last = ly0 + sum(s.size + 12 for s in sizes[:-1]) if sizes else 0.0
    top_off = -(n_em - nb[1])                                # 墨迹顶 − cy
    bot_off = ly_last + (lb[-1][3] - l_em[-1]) if lb else (n_em - nb[3])
    cy = y + h / 2 - (top_off + bot_off) / 2
    d.text((x + w / 2, cy), num, font=size, fill=common.TONES["hi"], anchor="mm")
    if unit.strip():
        us = common.font("bold", max(40, size.size // 3))
        d.text((x + w / 2 + size.getlength(num) / 2 + 14, cy + size.size // 3), unit.strip(),
               font=us, fill=common.TONES["gold"], anchor="la")
    ly = cy + size.size * 0.75
    for line in lines:
        s = lay.f_on
        while s.getlength(line["t"]) > w - 40 and s.size > 24:
            s = common.font("bold", s.size - 4)
        d.text((x + w / 2, ly), line["t"], font=s, fill=common.TONES[line["tone"]], anchor="mm")
        ly += s.size + 12


CHECKLIST_ROW_MAX = 150               # 行高上限：再大 checkbox 就成主视觉了
CHECKLIST_PANEL_PAD = 36              # 行区与面板边的距离


def _checklist_box_text_ratio(img, geo) -> float | None:
    """清单里“打勾那行的勾选框高度 ÷ 同行文字高度”。

    量渲染结果，不读版面公式——读公式就是门在测自己。勾选框（含勾）是绿色的
    （TONES['ok'] = (63,185,80)），同行文字是 TXT 或 SMALL，颜色分得开：先定勾选框的
    纵向跨度，再取同一行带里文字的纵向跨度。
    """
    import numpy as np

    a = np.asarray(img.convert("RGB")).astype(int)
    green = (np.abs(a - np.array(common.TONES["ok"])).sum(axis=2) < 60)
    if not green.any():
        return None
    rows = np.flatnonzero(green.any(axis=1))
    box_top, box_bot = int(rows[0]), int(rows[-1])
    # 文字：同一行带内、勾选框右侧的亮色像素
    band = a[box_top:box_bot + 1]
    txt = (np.abs(band - np.array(common.TXT)).sum(axis=2) < 60)
    trows = np.flatnonzero(txt.any(axis=1))
    if trows.size == 0:
        return None
    return (box_bot - box_top + 1) / (int(trows[-1]) - int(trows[0]) + 1)


def draw_checklist(d, box, items, ticks: int, lay: Layout, geo, progress: float):
    x, y, w, h = box
    d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=common.INK_PANEL,
                        outline=common.EDGE, width=2)
    # 行高按"填满面板且四边留白不低于 CHECKLIST_PANEL_PAD"取。旧写法 min(64, …) 把行高
    # 死顶在 64：竖屏 5 项时内容只有 320 px，挤在 1060 px 面板里上下各空 370+（实测上空
    # 385 / 下空 449，内容仅占 21%），读起来是只空盒子——和卡片修掉的是同一个病。
    row = min(CHECKLIST_ROW_MAX, (h - 2 * CHECKLIST_PANEL_PAD) // max(len(items), 1))
    cy = y + (h - row * len(items)) / 2 + row / 2
    pop = 1.0 + 0.35 * max(0.0, 1.0 - progress / 0.18)
    for i, item in enumerate(items):
        size = lay.f_list
        while size.getlength(item) > w - 130 and size.size > 20:
            size = common.font("text", size.size - 2)
        # 勾选框跟着**字号**走，不跟行高。旧写法 box_r = row*0.34：行高改成“填满面板”后
        # （曾因此把内容占比从 21% 提到 66%）框被拉到直径 92 px，而文字只有 40 px——框是字的
        # 2.3 倍，五行读起来像五个大空框，框压倒字。取字号的 1.3 倍（框直径/字高），
        # 比 glyph 略大又不抢戏；行高只管行的疏密，不再决定框的大小。
        box_r = size.size * 0.65
        bx = x + 30
        d.rounded_rectangle([bx - box_r, cy - box_r, bx + box_r, cy + box_r], radius=8,
                            outline=common.TONES["ok"] if i < ticks else common.SMALL, width=3)
        if i < ticks:
            r = box_r * (pop if i == ticks - 1 else 1.0)
            d.line([bx - r * 0.55, cy + r * 0.02, bx - r * 0.1, cy + r * 0.5, bx + r * 0.62, cy - r * 0.5],
                   fill=common.TONES["ok"], width=max(4, int(box_r * 0.18)), joint="curve")
        d.text((bx + box_r + 22, cy), item, font=size,
               fill=common.TXT if i < ticks else common.SMALL, anchor="lm")
        cy += row


def wrap_to_width(text: str, font, max_width: float) -> list[str]:
    """按实际字体像素宽度断行；中英文数字混排时字符数不是宽度。"""
    lines: list[str] = []
    rest = text.strip()
    while rest:
        if font.getlength(rest) <= max_width:
            lines.append(rest)
            break
        cut = 1
        for i in range(2, len(rest) + 1):
            if font.getlength(rest[:i]) > max_width:
                cut = i - 1
                break
        while 1 < cut < len(rest) and spec_mod.is_token_char(rest[cut - 1]) and spec_mod.is_token_char(rest[cut]):
            cut -= 1
        lines.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
    return lines


def wrap_punct_first(text: str, font, max_width: float, width_floor: float = 0.62) -> list[str]:
    """quiz 题干折行：贪心定界后优先退回标点。wrap_to_width 只保 ASCII token，
    中文逐字硬断，实测把「…总压 14.2 V。这个包健康吗？」折成「…这个包 / 健康吗？」。
    字幕折行的 _caption_two_lines 是恰好两行版；题干最多三行，这里是 N 行版：
    贪心断点（含 token 保护）先定，再在 [floor×cut, cut] 窗口内从右往左找行尾
    标点，命中且尾行不只剩标点就退到它，否则维持硬断。width_floor 卡住退行幅度——
    退太多行宽失衡比硬断更难看（字幕两行失衡门同款代价思路）。"""
    lines: list[str] = []
    rest = text.strip()
    while rest:
        if font.getlength(rest) <= max_width:
            lines.append(rest)
            break
        cut = 1
        for i in range(2, len(rest) + 1):
            if font.getlength(rest[:i]) > max_width:
                cut = i - 1
                break
        else:
            cut = len(rest)
        while 1 < cut < len(rest) and spec_mod.is_token_char(rest[cut - 1]) and spec_mod.is_token_char(rest[cut]):
            cut -= 1
        lo = max(2, int(cut * width_floor))
        for c in range(cut, lo - 1, -1):
            if rest[c - 1] in CAPTION_BREAK:
                head, tail = rest[:c].rstrip(), rest[c:].lstrip()
                if len(head) >= 2 and len(tail) >= 2 and any(ch not in CAPTION_BREAK for ch in tail):
                    cut = c
                break
        lines.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
    return lines


def quiz_metrics(beat: dict, geo, box) -> tuple[float, float]:
    """quiz 版面两件套：面板高、内容高。

    旧实现把进度条钉在面板底（`by = y + h - 54`），而题干+选项只占上部约 300 px——
    横屏中间空 387 px（占面板 53%）、竖屏空 750 px（占 71%），读起来是只空盒子，
    和卡片修掉的是同一个病。面板填充门没抓到它，因为进度条把内容跨度锚到了底部。
    现在面板贴着内容走：内容高 = 题干块 + 间距 + 选项块 + 间距 + 进度条。
    """
    w = box[2]
    qsize = common.font("bold", 64 if geo.portrait else 68)
    qlines = wrap_punct_first(beat.get("question", ""), qsize, w - 120)
    while len(qlines) > 3 and qsize.size > 30:
        qsize = common.font("bold", qsize.size - 4)
        qlines = wrap_punct_first(beat.get("question", ""), qsize, w - 120)
    osz = common.font("text", 58 if geo.portrait else 52)
    nopts = len(beat.get("options", []))
    content = (len(qlines) * qsize.size * 1.25        # 题干块
               + osz.size * 0.65                       # 题干→选项
               + nopts * osz.size * 1.75               # 选项块（末项含一个行距作缓冲）
               + osz.size * 0.6                        # 选项→进度条
               + 14)                                   # 进度条
    pad_v = max(56, content * 0.18)
    return content + 2 * pad_v, content


def draw_quiz(d, box, beat: dict, lay: Layout, geo, progress: float):
    x, y, w, h = box
    ph, _content = quiz_metrics(beat, geo, box)
    ph = min(ph, h)
    py = y + (h - ph) / 2
    d.rounded_rectangle([x, py, x + w, py + ph], radius=18, fill=common.INK_PANEL,
                        outline=common.EDGE, width=2)
    q = beat.get("question", "")
    size = common.font("bold", 64 if geo.portrait else 68)
    qlines = wrap_punct_first(q, size, w - 120)
    while len(qlines) > 3 and size.size > 30:
        size = common.font("bold", size.size - 4)
        qlines = wrap_punct_first(q, size, w - 120)
    line_h = size.size * 1.25
    pad_v = max(56, _content * 0.18)
    q_top = py + pad_v
    for i, line in enumerate(qlines):
        d.text((x + w / 2, q_top + i * line_h), line, font=size, fill=common.TXT, anchor="ma")
    opts = beat.get("options", [])
    osz = common.font("text", 58 if geo.portrait else 52)
    oy = q_top + len(qlines) * line_h + osz.size * 0.65
    labels = "ABCD"
    for i, o in enumerate(opts):
        d.ellipse([x + 40, oy - osz.size * 0.62, x + 40 + osz.size * 1.24, oy + osz.size * 0.62],
                  outline=common.TONES["hi"], width=3)
        d.text((x + 40 + osz.size * 0.62, oy), labels[i], font=osz, fill=common.TONES["hi"], anchor="mm")
        d.text((x + 40 + osz.size * 1.7, oy), o, font=osz, fill=common.TXT, anchor="lm")
        oy += osz.size * 1.75
    bar_h = 14
    # 进度条紧贴选项块下方，不再钉在面板底：钉底会把中段拉出一大片空白（见 quiz_metrics）
    by = oy - osz.size * 1.75 + osz.size * 0.6
    d.rectangle([x + 40, by, x + w - 40, by + bar_h], fill=common.EDGE)
    d.rectangle([x + 40, by, x + 40 + (w - 80) * min(progress, 1.0), by + bar_h], fill=common.TONES["gold"])


def beat_base(geo, lay, tl, e, caption: str | None):
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (geo.w, geo.h), common.INK)
    d = ImageDraw.Draw(img)
    layout = e["layout"]
    # 主内容框统一传 (x, y, width, height)。旧代码误把 right/bottom 当 width/height，
    # 横屏右边缘因此顶到 1920、底边多伸 118 px；卡片与数字中心也随之右偏。
    content = (geo.pad, geo.top + 10, geo.content_w, geo.content_h - 20)
    if layout in {"figure", "split"} and e["svg"]:
        pass  # clip 自带深色画布，按 figure_rect 原位贴入
    if layout == "card":
        draw_card(d, content, e["on_screen"], lay, geo)
    elif layout == "number":
        draw_number(d, content, e.get("big", ""), e["on_screen"], lay, geo)
    elif layout == "checklist":
        draw_checklist(d, content, tl["checklist"], int(e.get("ticks", 0)), lay, geo, 1.0)
    elif layout == "quiz":
        draw_quiz(d, content, e, lay, geo, 1.0)
    if layout == "split":
        draw_on_screen_box(d, geo.text_box("split"), e["on_screen"], lay)
    band_top(d, geo, lay, tl["no"], e["seg_title"])
    # figure 的结论只在底带出现；split 已在白色说明区展示，card/number/checklist/quiz
    # 已在主画面展示。后四类再抄到底带会让同一句出现两遍，横屏三行还会撞上字幕。
    band_bottom(d, geo, lay, e["on_screen"], caption or "", layout == "figure")
    d.rectangle([0, geo.h - 6, geo.w, geo.h], fill=common.INK)
    return img


def _fade_to_ink(frame: np.ndarray, geo, a: float) -> np.ndarray:
    """把整帧按 alpha 朝 INK 背景溶解。a=1 原样，a=0 纯背景。

    淡到 INK 而不是黑：背景本来就是 INK，溶解进背景读作淡入/淡出，且中间帧亮度停在
    17 以上，audit 的黑帧门（L<8）不会误触。片头片尾都用它，方向由调用方给的 alpha 定。
    """
    ink = np.array(common.INK, dtype="float32")
    return (frame * a + ink * (1.0 - a)).round().astype("uint8")


def _fade_out(frame: np.ndarray, geo, idx: int, total: int) -> np.ndarray:
    """片尾淡出：最后 XFADE_OUT_FRAMES 帧的 alpha 从 1 降到 0，末帧正好是纯背景。"""
    a = (total - 1 - idx) / XFADE_OUT_FRAMES
    return _fade_to_ink(frame, geo, a)


def _segment_dip(tl) -> dict[int, float]:
    """段（seg_title 变化）边界两侧各 SEG_DIP_FRAMES 帧的朝背景 alpha 表。

    段切换是章节过场，值得比普通 beat 边界更明确的处理。但**不能**用交叉淡化：实测
    交叉淡化会把出场与入场的文字叠在一起互相糊（quiz 选项压着 card 标题），而段边界
    恰好八成是 card 出场（10 个段边界里 9 个）。所以走“过场”——出场那几帧淡向背景、
    入场那几帧从背景浮起，任何时刻都只有一套文字在屏幕上，不存在两层相叠。

    alpha 不到 0：边界那一帧留 1/SEG_DIP_FRAMES 的内容，不出现纯背景帧（纯背景帧在
    深色片里读作闪一下）。首段（帧 0）没有前段，跳过。
    """
    dips: dict[int, float] = {}
    for i in range(1, len(tl["beats"])):
        if tl["beats"][i]["seg_title"] == tl["beats"][i - 1]["seg_title"]:
            continue
        n = int(round(tl["beats"][i]["start"] * common.FPS))
        for j in range(1, SEG_DIP_FRAMES + 1):
            if n - j >= 0:
                dips[n - j] = j / SEG_DIP_FRAMES          # 出场侧：越靠边界越淡
            dips[n + j - 1] = j / SEG_DIP_FRAMES          # 入场侧：越靠边界越淡
    return dips


def render(slug: str, aspect: str, preview: int | None = None) -> Path:
    geo = common.ASPECTS[aspect]
    lay = Layout(geo)
    tl = spec_mod.timeline(slug)
    ep_dir = common.EPISODES / tl["slug"]
    out = ep_dir / f"{tl['slug']}-{aspect}-video.mp4"
    if preview is not None:
        e = tl["beats"][preview]
        img = beat_base(geo, lay, tl, e, e["vo"][:18])
        p = common.ROOT / ".local" / f"preview-{tl['slug']}-{aspect}-{preview}.png"
        img.save(p)
        print(f"  预览 {common.rel(p)}（beat {e['id']} / {e['layout']}）")
        return p

    total_frames = int(round(tl["duration"] * common.FPS))
    common.have_tmp_disk(out, 200)
    enc = subprocess.Popen(
        [common.ffmpeg_exe(), "-hide_banner", "-y", "-loglevel", "error",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{geo.w}x{geo.h}", "-r", str(common.FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-an", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert enc.stdin and enc.stderr
    t0 = time.time()
    sources: dict[str, ClipSource] = {}
    written = 0
    prev_arr = None                              # 上一 beat 的末帧，供本 beat 开头几帧淡化
    prev_layout = None                           # 上一 beat 的 layout：只有纯图形出场才淡化
    b = b""                                      # 末帧字节；n=0 的 beat 不写帧，先绑个空值
    dips = _segment_dip(tl)                      # 段切换过场的 alpha 表（帧号 → alpha）
    seg_starts = {int(round(tl["beats"][i]["start"] * common.FPS))
                  for i in range(1, len(tl["beats"]))
                  if tl["beats"][i]["seg_title"] != tl["beats"][i - 1]["seg_title"]}
    rects = tl["rects_by_aspect"][aspect]
    for e in tl["beats"]:
        caps = spec_mod.caption_windows(e["vo_dur"], spec_mod.split_captions(e["vo"]))
        # 本 beat 是不是一段的开头：是则走过场，不再做内容区交叉淡化（一次边界一种处理）
        seg_start = int(round(e["start"] * common.FPS)) in seg_starts
        # 帧数按全局时间边界取，不按本 beat 时长各自 round：74 个 beat 各自 round 再求和
        # 与 round(总时长×FPS) 能差出几帧（实测 ep02 差 4 帧），assemble 的帧数门会整条拦下。
        # 边界摊过去每 beat 的 [start, end) 首尾相接，总数恒等于总帧数。
        n = int(round(e["end"] * common.FPS)) - int(round(e["start"] * common.FPS))
        src = None
        fb = None
        if e["svg"]:
            # 尺寸与落点都取 timeline 里那份 rect（capture 就是按它截的）：自己再算一遍
            # figure_box 会去找一个从来没被捕获过的文件名，还会把图贴在图区左上角而不是居中位
            x, y, fw, fh = rects[e["svg"]][e["layout"]]
            # capture 按 CLIP_SS 倍超采样捕获，这里按实际 clip 尺寸解码，paste 时缩回
            cw, ch = fw * common.CLIP_SS, fh * common.CLIP_SS
            mp4, meta_p = common.clip_paths(e["svg"], cw, ch, common.FPS)
            if not mp4.exists():
                raise FileNotFoundError(f"clip 还没捕获：{common.rel(mp4)}（先跑 capture.py）")
            meta = common.load_json(meta_p, {}) or {}
            src = ClipSource(mp4, cw, ch, bool(meta.get("repeating", True)))
            sources[e["svg"]] = src
            fb = (x, y, fw, fh)
        last_bytes = None
        last_cap = object()
        for i in range(n):
            t = i / common.FPS
            cap = next((c for a, b, c in caps if a <= t < b), None)
            animatable = e["layout"] in {"checklist", "quiz"}
            # 交叉淡化只在这几个条件同时成立时做：
            #  ① 出场的那个 beat 内容区是**纯图形**（figure：clip 占满内容区，PIL 不画字）；
            #  ② 只混内容区，上下两条带子（集数/段名/大字结论/字幕）保持硬切；
            #  ③ 本 beat 起点不是段边界——段边界走过场（见 _segment_dip），一次边界只用
            #     一种处理。两者叠加会把跳变顶到 2.4–3.0，超过转场平滑门为淡化标定的 2.0。
            # 全帧无差别淡化实测会把出场与入场的文字叠在一起：quiz 的选项和 card 的金色标题
            # 在溶解中段各半透明互相糊（实测帧 330），读起来是"糊/廉价"，而清晰度正是前面
            # 几轮校正字块换来的。文字密集的 layout（card/quiz/checklist/number）出场时直接
            # 硬切——硬切至少干净。
            fading = (i < XFADE_FRAMES and prev_arr is not None
                      and prev_layout == "figure" and not seg_start)
            # 片尾淡出：整条片子最后 XFADE_OUT_FRAMES 帧朝 INK 背景溶解。音频侧 assemble 的
            # FADE_OUT=1.40 s 早就在淡 BGM（实测末 1.3 s 从 -17 dB 降到 -47 dB），而视频一路
            # 全亮到最后一帧——声画在这件事上不同步。淡到 INK 而不是纯黑：背景本来就是 INK，
            # 溶解进背景读作"淡出"，且亮度停在 17 附近，黑帧门（L<8）不会误触。
            # 当前帧的全局序号。注意就是 `written` 本身：它在每个迭代末尾加 1，
            # 所以迭代 i 开始时已经等于"本 beat 已写帧数 + 之前所有 beat 的帧数"。
            # 曾经写成 written+i，那会把本 beat 内的进度数第二遍，末 beat 直接冲出
            # 总帧数（实测 idx 到 20769 > 20557），alpha 变负、淡出从头到尾都是坏的。
            idx = written
            ending = idx >= total_frames - XFADE_OUT_FRAMES
            # 片头淡入：前 XFADE_IN_FRAMES 帧从 INK 背景浮现。音频侧 assemble 的
            # FADE_IN=0.60 s 早就在淡 BGM（实测前 0.6 s 从 -26 dB 升到 -18 dB），而视频
            # 第一帧就全亮——和片尾是同一个声画不同步，只是方向相反。
            opening = idx < XFADE_IN_FRAMES
            dipping = idx in dips
            if not fading and not ending and not opening and not dipping and src is None and cap == last_cap and not animatable and last_bytes is not None:
                enc.stdin.write(last_bytes)
                written += 1
                continue
            img = beat_base(geo, lay, tl, e, cap)
            if src is not None:
                assert fb is not None
                fr = src.frame(i)
                if fr is not None:
                    img.paste(fr.resize((fb[2], fb[3]), Image.LANCZOS), (fb[0], fb[1]))
            if animatable:
                d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).Draw(img)
                box = (geo.pad, geo.top + 10, geo.content_w, geo.content_h - 20)
                prog = min(1.0, (t + (e["dur"] - e["vo_dur"])) / max(e["vo_dur"], 0.1))
                if e["layout"] == "checklist":
                    draw_checklist(d, box, tl["checklist"], int(e.get("ticks", 0)), lay, geo,
                                   (t % 1.0) if int(e.get("ticks", 0)) else 1.0)
                else:
                    draw_quiz(d, box, e, lay, geo, prog)
            if fading:
                assert prev_arr is not None
                a = (i + 1) / XFADE_FRAMES
                cur = np.frombuffer(img.tobytes(), dtype="uint8")
                cur = cur.reshape(geo.h, geo.w, 3).astype("float32")
                prev = prev_arr.reshape(geo.h, geo.w, 3)
                # 只混内容区的行：上下两条带子原样取新帧，字幕与段名因此是硬切，
                # 不会和出场帧的同类文字互相糊。带子里的文字密度远高于内容区，
                # 字幕每 2–3 s 还换一次，硬切反而更干净。
                y0, y1 = geo.top, geo.h - geo.bottom
                cur[y0:y1] = prev[y0:y1] * (1.0 - a) + cur[y0:y1] * a
                cur = cur.round().astype("uint8")
                if ending:
                    cur = _fade_out(cur, geo, idx, total_frames)
                elif opening:
                    cur = _fade_to_ink(cur, geo, (idx + 1) / XFADE_IN_FRAMES)
                b = cur.tobytes()
            elif ending or opening or dipping:
                cur = np.frombuffer(img.tobytes(), dtype="uint8")
                cur = cur.reshape(geo.h, geo.w, 3).astype("float32")
                if ending:
                    cur = _fade_out(cur, geo, idx, total_frames)
                elif opening:
                    cur = _fade_to_ink(cur, geo, (idx + 1) / XFADE_IN_FRAMES)
                else:
                    cur = _fade_to_ink(cur, geo, dips[idx])
                b = cur.tobytes()
            else:
                b = img.tobytes()
            enc.stdin.write(b)
            last_bytes, last_cap = b, cap
            written += 1
        # 记下本 beat 的 layout 与末帧，供下一个 beat 判断能否淡化、以及混哪些行。
        # n 为 0 的 beat（理论上是 0 时长，实际不会出现）不会写任何帧，b 未绑定；
        # 此时保留上一个 beat 的状态，不去碰 prev_arr。
        if n:
            prev_layout = e["layout"]
            prev_arr = np.frombuffer(b, dtype="uint8").astype("float32")
    for s in sources.values():
        s.close()
    enc.stdin.close()
    err = enc.stderr.read().decode("utf-8", "replace")
    rc = enc.wait()
    if rc != 0:
        raise RuntimeError(f"编码失败（{rc}）：{err[-1500:]}")
    secs = time.time() - t0
    print(f"  {aspect}: {written}/{total_frames} 帧 / {tl['duration']:.1f} s 内容，"
          f"墙钟 {secs:.0f} s（{written / max(secs, 0.1):.0f} 帧/秒）→ {common.rel(out)}")
    if abs(written - total_frames) > 2:
        print(f"  ⚠ 帧数与时间轴差 {written - total_frames} 帧，音画对齐会漂")
    sp = ep_dir / f"{tl['slug']}-{aspect}.srt"
    sp.write_text(spec_mod.srt(tl), encoding="utf-8")
    common.save_json(ep_dir / f"{tl['slug']}-{aspect}-render.json",
                     {"slug": tl["slug"], "aspect": aspect, "frames": written,
                      "expected": total_frames, "seconds": tl["duration"],
                      "wall_seconds": round(secs, 1), "out": common.rel(out), "srt": common.rel(sp)})
    return out


def selftest(slug: str) -> int:
    """不编码视频，守住下集换文案最容易回归的构图契约。"""
    fails: list[str] = []
    tl = spec_mod.timeline(slug)
    for aspect, geo in common.ASPECTS.items():
        lay = Layout(geo)
        box = (geo.pad, geo.top + 10, geo.content_w, geo.content_h - 20)
        x, y, w, h = box
        if (x + w, y + h) != (geo.w - geo.pad, geo.h - geo.bottom - 10):
            fails.append(f"{aspect} 主内容框越界：{box}")
        # 字幕安全区，量的是 Layout 里的几何而非绘制函数的内部状态：
        # ① 带子以画幅为心；② 竖屏左右各守 10% 侧边危险带（右为动作栏、左下为评论框）；
        # ③ 整块收在 75%–88% 高的字幕安全带内；④ 实际用号不得低于 CAPTION_MIN。
        # 竖屏旧值 caption_right=150 令带子左偏 55 px（5.1% 宽）——字幕看着就没居中。
        if lay.caption_cx != geo.w / 2:
            fails.append(f"{aspect} 字幕带心 {lay.caption_cx} 不在画幅心 {geo.w / 2}")
        # 侧边危险带（右为动作栏、左下为评论框）与 250 px 下部空间都是**竖屏**平台 UI 的
        # 产物；横屏播放器没有这两样，只守"带子居中"这一条。
        if geo.portrait:
            if lay.caption_left < geo.w * 0.10 - 1 or geo.w - lay.caption_right < geo.w * 0.10 - 1:
                fails.append(f"{aspect} 字幕左右缘侵入侧边危险带：{lay.caption_left}/{lay.caption_right}")
            if lay.caption_from_bottom < 250:
                fails.append(f"{aspect} 字幕没有给平台 UI 留够下部空间：{lay.caption_from_bottom}")
        min_cap = 999
        for e in tl["beats"]:
            for _a, _b, text in spec_mod.caption_windows(e["vo_dur"], spec_mod.split_captions(e["vo"])):
                size, lines = caption_block(text, lay)
                min_cap = min(min_cap, size.size)
                for ln in lines:
                    if size.getlength(ln) > lay.caption_width:
                        fails.append(f"{aspect} {e['id']} 字幕折行后仍越界：{ln}")
                if len(lines) > 2:
                    fails.append(f"{aspect} {e['id']} 字幕折成 {len(lines)} 行，超过两行")
                if len(lines) == 2:
                    # 两行的窄/宽不得低于 40%。实测过两种反面：贪心填满带宽时剩下一枚"，"
                    # 自成一行（比值 0.05）；贪心填半宽时 880 px 的句子出到三行。故定这道门。
                    w1 = size.getlength(lines[0])
                    w2 = size.getlength(lines[1])
                    if min(w1, w2) < max(w1, w2) * 0.40:
                        fails.append(f"{aspect} {e['id']} 字幕两行失衡 {w1:.0f}/{w2:.0f} px：{text}")
                # 竖屏字幕安全区 75%–88% 高；横屏无底部动作栏，只守下部播放器控件。
                if geo.portrait:
                    step = int(round(size.size * 1.28))
                    blk_top = geo.h - lay.caption_from_bottom - step * (len(lines) - 1)
                    blk_bot = geo.h - lay.caption_from_bottom + step
                    if blk_top < geo.h * 0.75 - 1 or blk_bot > geo.h * 0.88 + 1:
                        fails.append(f"{aspect} {e['id']} 字幕块出安全带 "
                                     f"{blk_top / geo.h * 100:.0f}%-{blk_bot / geo.h * 100:.0f}%")
        # 纯中文长句不能被当成一个不可切断的 token。字幕折行自己枚举断点、不走 token 保护，
        # 所以这条 bug 在字幕上看不出来；它咬的是 quiz 题干与 on_screen 文字——全库只有 1 条
        # 题干，折 3 行仍在"不超过三行"门内，故另立这道门直接探 wrap_to_width 本身。
        probe = "主动均衡是拿电感电容把能量从高个子搬给矮个子，为什么整包电量还是对不齐"
        wl = wrap_to_width(probe, common.font("text", 40), lay.caption_width)
        if not wl or common.font("text", 40).getlength(wl[0]) < 600:
            fails.append(f"{aspect} wrap_to_width 把纯中文当整词：{[x[:8] for x in wl]}")
        sample_by_layout: dict[str, dict] = {}
        for e in tl["beats"]:
            sample_by_layout.setdefault(e["layout"], e)
        for layout, e in sample_by_layout.items():
            img = beat_base(geo, lay, tl, e, e["vo"][:18])
            if img.size != (geo.w, geo.h):
                fails.append(f"{aspect} {layout} 预览尺寸 {img.size} 错")
        quiz = sample_by_layout.get("quiz")
        if quiz:
            qfont = common.font("bold", 64 if geo.portrait else 68)
            lines = wrap_punct_first(quiz["question"], qfont, geo.content_w - 120)
            if len(lines) > 3:
                fails.append(f"{aspect} quiz 题干超过三行")
        # 面板不能被内容空着——card / checklist / quiz 三类都画面板，量的都是渲染结果。
        # 竖屏 checklist 实测过上空 385 / 下空 449、内容只占面板 21%（行高被 min(64, …)
        # 死顶在 64），读起来是只空盒子。判据取渲染出来的内容跨度与留白，不读版面函数：
        # 读函数就是门在测自己，改了画法它也不知道。
        # 卡片修好后内容占 48%、留白各 26%，quiz 占 89%，都给阈值留了余量。
        for layout, e in sample_by_layout.items():
            if layout not in {"card", "checklist", "quiz"}:
                continue
            img = beat_base(geo, lay, tl, e, e["vo"][:18])
            span = panel_content_span(img, geo)
            if span is None:
                fails.append(f"{aspect} {layout} 渲染结果里量不到面板或面板内没有内容")
                continue
            ptop, pbot, ctop, cbot = span
            ph, ch = pbot - ptop, cbot - ctop
            pad_top, pad_bot = ctop - ptop, pbot - cbot
            if ch / max(ph, 1) < 0.45:
                fails.append(f"{aspect} {layout} 面板内内容只占 {ch / ph * 100:.0f}%"
                             f"（{ch} px / {ph} px）——面板被空着")
            if pad_top > ph * 0.30:
                fails.append(f"{aspect} {layout} 面板上空白 {pad_top} px（面板 {ph} px 的 "
                             f"{pad_top / ph * 100:.0f}%）——内容没填满面板")
            if pad_bot > ph * 0.30:
                fails.append(f"{aspect} {layout} 面板下空白 {pad_bot} px（面板 {ph} px 的 "
                             f"{pad_bot / ph * 100:.0f}%）——内容没填满面板")
            # 面板**内部**也不能有断层。上面几条只看内容总跨度，而进度条这类“锚底元素”
            # 会把跨度撑满：quiz 旧实现把进度条钉在面板底，内容跨度 89% 全绿，可中段
            # 实际空着 387 px（横屏 53%）/ 750 px（竖屏 71%）——读起来是只上下有字、
            # 中间一大片空的盒子。量渲染结果里最长的连续空白行段。
            void = _panel_void(img, geo)
            if void is not None and void > ph * 0.30:
                fails.append(f"{aspect} {layout} 面板中段有 {void} px 连续空白"
                             f"（面板 {ph} px 的 {void / ph * 100:.0f}%）——内容断层")
        # 没有面板的版面（number / split）也有一份"整块必须居中"的契约，参照区不同：
        # number 比内容框，split 比它那块文字区。旧实现两个都把块体钉在区域顶部——
        # number 实测偏 37–54 px 且方向随文案行数而变；split 横屏三行只占文字框 22%、
        # 下部空 76%，竖屏占 49%、空 46%。量渲染出来的内容行，块心偏离区心超过 3% 就红。
        for layout in ("number", "split"):
            for e in tl["beats"]:
                if e["layout"] != layout:
                    continue
                img = beat_base(geo, lay, tl, e, e["vo"][:18])
                # split 只量它那块文字区的**列**：横屏左半幅是图，不限列就会把图里的内容
                # 一起量进来（实测那样量出 134–856 的"文字块"，其实是图的上下沿）。
                if layout == "split":
                    bx, by, bw, bh = geo.text_box("split")
                    span = content_rows(img, geo, by + 4, by + bh - 4, bx + 8, bx + bw - 8)
                else:
                    by, bh = geo.top + 10, geo.content_h - 20
                    span = content_rows(img, geo, by + 4, by + bh - 4)
                if span is None:
                    fails.append(f"{aspect} {e['id']} 渲染结果里量不到{layout}版面的内容")
                    continue
                ctr = (span[0] + span[1]) / 2
                off = ctr - (by + bh / 2)
                if abs(off) > bh * 0.03:
                    fails.append(f"{aspect} {e['id']} {layout} 块体比所在区"
                                 f"{'高' if off < 0 else '低'} {abs(off):.0f} px"
                                 f"（区心 {by + bh / 2:.0f}，块心 {ctr:.0f}，区高 {bh}）"
                                 "——整块没居中")
        # 卡片面板必须贴着文字块走，而且必须量的**渲染出来的面板**：
        # 早先这道理直读 card_metrics()，可 ratio = 1+2·pad_v/text_h 被构造上界钉在 2.1，
        # 永遠产不出旧实现的 5.46；把 draw_card 的矩形改回满框它也照样绿——门在测自己。
        # 现在扫 beat_base 渲染结果的 EDGE 横边：面板真是画出来的那一圈，draw_card 不照
        # card_metrics 画、不画面板、或不再居中，这三条各自都能让它红。
        for e in tl["beats"]:
            if e["layout"] != "card" or not e["on_screen"]:
                continue
            ph_raw, text_h, _pad = card_metrics(box, e["on_screen"], lay)
            # 与 draw_card 一样先钳到内容框高度：不钳的话，将来一行很高的卡片
            # （文字块加 proportional padding 超过内容框）会画出被钳短的面板，而这里拿未钳的
            # 值去比，红得毫无道理。当前所有卡片都远低于内容框，钳不钳都一样。
            ph_want = min(ph_raw, h)
            img = beat_base(geo, lay, tl, e, e["vo"][:18])
            edges = card_panel_edges(img, geo)
            if edges is None:
                fails.append(f"{aspect} {e['id']} 渲染结果里找不到卡片面板的描边——面板没画")
                continue
            top, bot = edges
            ph = bot - top
            if abs(ph - ph_want) > 4:
                fails.append(f"{aspect} {e['id']} 面板高 {ph} px，card_metrics 算的是 "
                             f"{ph_want:.0f} px——draw_card 没照它画（改回满框会在这里红）")
            if ph / max(text_h, 1) > 2.6:
                fails.append(f"{aspect} {e['id']} 面板是文字块的 {ph / max(text_h, 1):.2f} 倍"
                             f"（{ph} px 面板 / {text_h:.0f} px 文字）——面板没贴着内容走")
            if abs((top - y) - ((y + h) - bot)) > 2:
                fails.append(f"{aspect} {e['id']} 面板在内容框里不居中：上空 {top - y} px / "
                             f"下空 {(y + h) - bot} px")
        # 字幕可读性地：实际用号不得低于 40 px。旧横屏基准 34 px（占屏高 3.1%）时
        # 209 条字幕无一条需要缩小——最宽字幕只用掉可用宽 42%，放到 50 px 也才 61%，
        # 纯粹是基数拍小了，手机上看字小是必然。基准调到 44 px 后这道门守着别再缩回去。
        if min_cap < 40:
            fails.append(f"{aspect} 字幕最小 {min_cap}px < 40px——手机上看字太小"
                         f"（基准 {lay.f_cap.size}px，要么基数偏小要么文案超宽被压）")
        # 清单的勾选框不能大过文字：行高改成"填满面板"后框被拉到字号的 2.3 倍，五行读起来
        # 像五个大空框。现在框取字号的 1.3 倍，这里守住上限，别再被行高带跑。
        # 量的是渲染结果里**绿色像素**（打勾那行的框+勾）与同行文字的纵向跨度，不读算框的
        # 公式——读公式就是门在测自己，改画法它也不会红。
        for e in tl["beats"]:
            if e["layout"] != "checklist":
                continue
            img = beat_base(geo, lay, tl, dict(e, ticks=1), e["vo"][:18])
            m = _checklist_box_text_ratio(img, geo)
            if m is None:
                fails.append(f"{aspect} {e['id']} 渲染结果里量不到打勾的勾选框")
            elif m > 1.5:
                fails.append(f"{aspect} {e['id']} 勾选框是文字的 {m:.2f} 倍——框压倒字")
        print(f"  {aspect}: 内容框 {w}×{h} / 字幕最小 {min_cap}px / {len(sample_by_layout)} 种布局")
    if not common.clip_paths("x.svg", 2, 2)[0].stem.endswith(f"-{common.VIDEO_THEME}"):
        fails.append("clip 缓存键没有主题")
    for p in fails:
        print("  FAIL " + p)
    print("selftest ok" if not fails else f"selftest FAIL：{len(fails)} 条")
    return 0 if not fails else 1


def main() -> int:
    common.ensure_dirs()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--episode", required=True)
    ap.add_argument("--aspect", choices=list(common.ASPECTS))
    ap.add_argument("--both", action="store_true")
    ap.add_argument("--preview", type=int, help="只渲染第 N 个 beat 成 PNG，用来看版面")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.preview is not None:
        render(a.episode, a.aspect or "16x9", a.preview)
        return 0
    if a.selftest:
        return selftest(a.episode)
    for aspect in (list(common.ASPECTS) if a.both else [a.aspect or "16x9"]):
        render(a.episode, aspect)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
