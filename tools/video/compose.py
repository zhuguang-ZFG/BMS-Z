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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import spec as spec_mod  # noqa: E402

SERIES = "BMS 从入门到精通"


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
        self.f_cap = common.font("text", 46 if v else 34)
        self.f_on = common.font("bold", 58 if v else 46)
        self.f_big = common.font("bold", 190 if v else 230)
        self.f_card = common.font("bold", 86 if v else 96)
        self.f_list = common.font("text", 46 if v else 40)
        self.f_mono = common.font("mono", 40 if v else 34)
        # 字幕不是贴屏幕底边：竖屏下方要给平台文案/进度条留区，横屏也要避开播放器控件。
        self.caption_from_bottom = 290 if v else 88
        self.caption_left = geo.pad
        self.caption_right = 150 if v else geo.pad
        self.caption_width = geo.w - self.caption_left - self.caption_right
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
        cy = geo.h - lay.caption_from_bottom
        size = lay.f_cap
        while size.getlength(caption) > lay.caption_width and size.size > 32:
            size = common.font("text", size.size - 2)
        d.text((lay.caption_cx, cy), caption, font=size, fill=common.TXT, anchor="ma")


def draw_on_screen_box(d, box, lines, lay: Layout):
    x, y, w, h = box
    cy = y + 10
    for line in lines:
        size = lay.f_on
        while common.font("bold", size.size).getlength(line["t"]) > w - 8 and size.size > 24:
            size = common.font("bold", size.size - 2)
        d.text((x + 4, cy), line["t"], font=size, fill=common.TONES[line["tone"]])
        cy += size.size + 14


def card_panel_edges(img, geo) -> tuple[int, int] | None:
    """卡片面板描边的上下两行（整行接近 EDGE 色的行），只在主内容框的列范围内找。

    扫的是渲染结果，不是版面参数：门要能因为"画出来的面板变了"而红，而不是因为
    "算面板的函数自己变了"而红。找不到返回 None——面板没画也是一种失败。

    必须同时限定列范围和行范围：底带分隔线、画面底部那 6 px 色条也是 EDGE 附近的横边，
    不限列会把整幅第一行/最后一行当成面板边（实测那样量出 745 px 的假面板）；
    不限行会让底带分隔线混进首末行（实测把面板量成 603 px）。两处都限定在内容框内。
    """
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
    cy = y + h * 0.42
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


def draw_checklist(d, box, items, ticks: int, lay: Layout, geo, progress: float):
    x, y, w, h = box
    d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=common.INK_PANEL, outline=common.EDGE, width=2)
    row = min(64, (h - 40) // max(len(items), 1))
    cy = y + (h - row * len(items)) / 2 + row / 2
    pop = 1.0 + 0.35 * max(0.0, 1.0 - progress / 0.18)
    for i, item in enumerate(items):
        box_r = row * 0.34
        bx = x + 30
        d.rounded_rectangle([bx - box_r, cy - box_r, bx + box_r, cy + box_r], radius=8,
                            outline=common.TONES["ok"] if i < ticks else common.SMALL, width=3)
        if i < ticks:
            r = box_r * (pop if i == ticks - 1 else 1.0)
            d.line([bx - r * 0.55, cy + r * 0.02, bx - r * 0.1, cy + r * 0.5, bx + r * 0.62, cy - r * 0.5],
                   fill=common.TONES["ok"], width=max(4, int(row * 0.09)), joint="curve")
        size = lay.f_list
        while size.getlength(item) > w - 130 and size.size > 20:
            size = common.font("text", size.size - 2)
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


def draw_quiz(d, box, beat: dict, lay: Layout, geo, progress: float):
    x, y, w, h = box
    d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=common.INK_PANEL, outline=common.EDGE, width=2)
    q = beat.get("question", "")
    size = common.font("bold", 64 if geo.portrait else 68)
    qlines = wrap_to_width(q, size, w - 120)
    while len(qlines) > 3 and size.size > 30:
        size = common.font("bold", size.size - 4)
        qlines = wrap_to_width(q, size, w - 120)
    line_h = size.size * 1.25
    q_top = y + 60
    for i, line in enumerate(qlines):
        d.text((x + w / 2, q_top + i * line_h), line, font=size, fill=common.TXT, anchor="ma")
    opts = beat.get("options", [])
    osz = common.font("text", 52 if geo.portrait else 46)
    oy = q_top + len(qlines) * line_h + osz.size * 0.65
    labels = "ABCD"
    for i, o in enumerate(opts):
        d.ellipse([x + 40, oy - osz.size * 0.62, x + 40 + osz.size * 1.24, oy + osz.size * 0.62],
                  outline=common.TONES["hi"], width=3)
        d.text((x + 40 + osz.size * 0.62, oy), labels[i], font=osz, fill=common.TONES["hi"], anchor="mm")
        d.text((x + 40 + osz.size * 1.7, oy), o, font=osz, fill=common.TXT, anchor="lm")
        oy += osz.size * 1.75
    bar_h = 14
    by = y + h - 54
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
    rects = tl["rects_by_aspect"][aspect]
    for e in tl["beats"]:
        caps = spec_mod.caption_windows(e["vo_dur"], spec_mod.split_captions(e["vo"]))
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
            mp4, meta_p = common.clip_paths(e["svg"], fw, fh, common.FPS)
            if not mp4.exists():
                raise FileNotFoundError(f"clip 还没捕获：{common.rel(mp4)}（先跑 capture.py）")
            meta = common.load_json(meta_p, {}) or {}
            src = ClipSource(mp4, fw, fh, bool(meta.get("repeating", True)))
            sources[e["svg"]] = src
            fb = (x, y)
        last_bytes = None
        last_cap = object()
        for i in range(n):
            t = i / common.FPS
            cap = next((c for a, b, c in caps if a <= t < b), None)
            animatable = e["layout"] in {"checklist", "quiz"}
            if src is None and cap == last_cap and not animatable and last_bytes is not None:
                enc.stdin.write(last_bytes)
                written += 1
                continue
            img = beat_base(geo, lay, tl, e, cap)
            if src is not None:
                assert fb is not None
                fr = src.frame(i)
                if fr is not None:
                    img.paste(fr, (fb[0], fb[1]))
            if animatable:
                d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).Draw(img)
                box = (geo.pad, geo.top + 10, geo.content_w, geo.content_h - 20)
                prog = min(1.0, (t + (e["dur"] - e["vo_dur"])) / max(e["vo_dur"], 0.1))
                if e["layout"] == "checklist":
                    draw_checklist(d, box, tl["checklist"], int(e.get("ticks", 0)), lay, geo,
                                   (t % 1.0) if int(e.get("ticks", 0)) else 1.0)
                else:
                    draw_quiz(d, box, e, lay, geo, prog)
            b = img.tobytes()
            enc.stdin.write(b)
            last_bytes, last_cap = b, cap
            written += 1
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
        if geo.portrait and (lay.caption_from_bottom < 250 or lay.caption_right < 120):
            fails.append(f"{aspect} 字幕没有给平台 UI 留安全区")
        min_cap = 999
        for e in tl["beats"]:
            for _a, _b, text in spec_mod.caption_windows(e["vo_dur"], spec_mod.split_captions(e["vo"])):
                size = lay.f_cap
                while size.getlength(text) > lay.caption_width and size.size > 32:
                    size = common.font("text", size.size - 2)
                min_cap = min(min_cap, size.size)
                if size.getlength(text) > lay.caption_width:
                    fails.append(f"{aspect} {e['id']} 字幕仍越界：{text}")
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
            lines = wrap_to_width(quiz["question"], qfont, geo.content_w - 120)
            if len(lines) > 3:
                fails.append(f"{aspect} quiz 题干超过三行")
        # 卡片面板必须贴着文字块走，而且必须量的**渲染出来的面板**：
        # 早先这道理直读 card_metrics()，可 ratio = 1+2·pad_v/text_h 被构造上界钉在 2.1，
        # 永遠产不出旧实现的 5.60；把 draw_card 的矩形改回满框它也照样绿——门在测自己。
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
