#!/usr/bin/env python3
"""发布包：平台封面 + 四平台文案。

封面复用成片的皮肤三件套（`common.video_bg` 环境光背景 / `compose._paint_panel`
立层面板 / `compose._num_glow` 数字光晕），不引入新视觉语言。一集三张，落在
`media/video/out/publish/`（产物不入库）：

    cover/<slug>-16x9.jpg   1920×1080   B 站、知乎、抖音（横版）
    cover/<slug>-3x4.jpg    1080×1440   小红书
    cover/<slug>-9x16.jpg   1080×1920   抖音（竖版）

加 `--cover-variant q` 另出**问句版**（同名加 `-q`）：大字换成该集开场那道题，
副行写「答案在片尾」。小红书封面 PK 是「主封面 + 最多 3 张备选」的 A/B，备选
可以自己传，所以一张图不够测——问句版就是备选。要换问句在 spec 里加
`cover_question`（默认取第一条带 question 的 beat）。

文案按平台生成标题/正文/话题，正文里的章节时间点取自 `spec.timeline()` 的**实测**
时长，不手抄。落 `<slug>.json`（给脚本用）与 `<slug>.md`（人读，直接复制粘贴）。

平台的字数上限会变，常量在 PLATFORMS 里，以平台当期规则为准；超了截断，并在 JSON
里把 title_trimmed / body_trimmed 标 true——不静默丢字。

用法：
    python3 tools/video/publish.py --episode ep07-engineering-capstone
    python3 tools/video/publish.py --episode ep07-engineering-capstone --selftest
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import compose  # noqa: E402
import spec as spec_mod  # noqa: E402

SERIES = "BMS 从入门到精通"
# 系列（合集）封面用的常量：集数 = 已出的 spec 数 + 阶段 0 那一集（第 1 集）在建
SERIES_COUNT = "7"
SERIES_STAGES = "阶段 0–6"
SERIES_TAGLINE = "七集一条线：从一块电池到毕业项目"
SERIES_CTA = "每集一个能动手勾掉的验收清单"
PUBLISH = common.OUT / "publish"
COVER_DIR = PUBLISH / "cover"

SIZES = {"16x9": (1920, 1080), "3x4": (1080, 1440), "9x16": (1080, 1920), "1x1": (1080, 1080)}
HOOK_SIZE = {"16x9": (112, 92), "3x4": (100, 84), "9x16": (100, 84), "1x1": (96, 80)}  # (一行就放得下, 要折行)
# 1:1 是平台**合集**封面用的（抖音合集要求 ≤5MB、1080×1080 最佳；小红书合集同理）。

# 平台侧：封面用哪张、标题/正文字符预算、话题。预算以平台当期规则为准，会变。
# B 站投稿页另要三个字段：分区（选择器现选，tid 以当期列表为准）、10 个标签、独立的分段章节框。
# 分区只给候选：本轮没能读到投稿页的分区选择器（upos 上传阶段就失败，投稿表单没出现过），
# 所以这两项**未经投稿页核实**，投稿时按当期列表现选。
BILI_AREA = {"candidates": ["科技 · 极客DIY", "知识 · 科学科普"],
             "note": "候选，未经投稿页核实——投稿时按分区选择器当期列表现选"}
BILI_TAGS_MAX = 10
# 小红书发布页 2026-10-18 实测文案：「支持时长 4 小时以内，最大 20GB 的视频文件」。
# 上一轮引用的「15 分钟上限」是 2023 年第三方资料，已过时——以页面当期文案为准。
XHS_LIMIT = {"seconds": 4 * 3600, "bytes": 20 * 1024 ** 3,
             "note": "发布页 2026-10-18 实测：时长 ≤4 小时、文件 ≤20GB"}
PLATFORMS = {
    "bilibili": {"cover": "16x9", "title": 80, "body": 2000,
                 "tags": ["BMS", "锂电池", "电池管理系统", "新能源", "储能",
                          "嵌入式", "电子工程", "硬件设计", "电路设计", "硬核科普"]},
    "xiaohongshu": {"cover": "3x4", "title": 20, "body": 1000,
                    "tags": ["BMS", "锂电池", "新能源", "硬核科普"]},
    "douyin": {"cover": "9x16", "title": 30, "body": 1000,
               "tags": ["BMS", "锂电池", "新能源", "知识分享"]},
    # 知乎发布页实测：标题 50 字（超限时发布按钮保持 disabled、点了也不发）
    "zhihu": {"cover": "16x9", "title": 50, "body": 2000, "tags": []},
}


def hook_of(title: str) -> tuple[str, str]:
    """`阶段 6 · 精通与毕业项目：双通道…毕业` → （阶段标签，钩子短语）。封面大字用钩子。"""
    head, sep, tail = title.partition("：")
    return (head.strip(), tail.strip()) if sep else (title.strip(), "")


def key_big(tl: dict) -> str | None:
    """该集最后一条 number beat 的 `big`——封面上的「本集尺子」。没有就不画。"""
    for b in reversed(tl["beats"]):
        if b.get("big"):
            return str(b["big"])
    return None


def question_of(slug: str) -> str:
    """封面变体用：本集开场那道题（第一条带 question 的 beat）。"""
    for b in spec_mod.timeline(slug)["beats"]:
        if b.get("question"):
            return str(b["question"]).strip()
    return ""


def cover_image(slug: str, key: str, variant: str = ""):
    """画一张封面，返回 (图, 元数据)。元数据给 selftest 用：面板盒与每行文字宽度。

    `variant="q"` 是**问句版**：大字换成开场那道题（封面 A/B 用，小红书封面 PK 可以
    自己上传备选封面）。想换问句在 spec 里加 `cover_question`，别改线上图。
    """
    from PIL import ImageDraw

    spec = spec_mod.load_spec(slug)
    tl = spec_mod.timeline(slug)
    w, h = SIZES[key]
    stage, hook = hook_of(spec["title"])
    if not hook:
        hook = stage
    if variant == "q":
        hook = spec.get("cover_question") or question_of(slug) or hook

    geo = common.Geometry(f"cover-{key}", w, h, top=int(h * 0.13), bottom=0, split_at=0.5)
    img = common.video_bg(geo).copy()
    lay = compose.Layout(geo)
    d = ImageDraw.Draw(img, "RGBA")
    compose.band_top(img, d, geo, lay, spec["no"], stage)

    pw = int(w * 0.86)
    px = (w - pw) // 2
    pad_x, pad_y = int(pw * 0.07), int(h * 0.055)
    inner_w = pw - 2 * pad_x

    single, multi = HOOK_SIZE[key]
    f_hook = common.font("bold", single)
    lines = compose.wrap_punct_first(hook, f_hook, inner_w)
    if len(lines) > 1:
        f_hook = common.font("bold", multi)
        lines = compose.wrap_punct_first(hook, f_hook, inner_w)
    widths = [f_hook.getbbox(ln)[2] for ln in lines]

    big = key_big(tl)
    f_big = common.font("bold", 66 if key == "16x9" else 58)
    f_stage = common.font("text", 46 if key == "16x9" else 42)
    rows: list[tuple[str, str, object, tuple[int, int, int], int]] = []
    for ln in lines:
        rows.append(("hook", ln, f_hook, common.TXT, int(f_hook.size * 1.32)))
    if variant == "q":
        rows.append(("stage", "答案在片尾", f_big, common.TONES["gold"], int(f_big.size * 1.7)))
    elif big:
        rows.append(("big", f"本集尺子　{big}", f_big, common.TONES["hi"], int(f_big.size * 1.6)))
    rows.append(("stage", stage, f_stage, common.TONES["gold"], int(f_stage.size * 1.7)))

    ph = pad_y * 2 + sum(r[4] for r in rows)
    py = int(h * 0.5 - ph / 2) if key == "16x9" else int(h * 0.52 - ph / 2)
    compose._paint_panel(img, (px, py, pw, ph))

    y = py + pad_y
    for kind, text, fnt, fill, rh in rows:
        cy = y + rh / 2
        if kind == "big":
            compose._num_glow(img, w / 2, cy, int(ph * 0.55))
        compose._sh_text(d, (w / 2, cy), text, fnt, fill, anchor="mm")
        y += rh

    f_foot = common.font("text", 38 if key == "16x9" else 34)
    compose._sh_text(d, (w / 2, py + ph + int(h * 0.055)), spec.get("cta", ""),
                     f_foot, common.SMALL, anchor="mm")
    meta = {"size": (w, h), "panel": (px, py, pw, ph), "inner_w": inner_w,
            "lines": lines, "line_widths": widths,
            "hook": hook, "stage": stage, "big": big}
    return img, meta


def render_cover(slug: str, key: str, variant: str = "") -> Path:
    img, _ = cover_image(slug, key, variant)
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    out = COVER_DIR / f"{slug}-{key}{'-' + variant if variant else ''}.jpg"
    img.convert("RGB").save(out, quality=92, optimize=True, progressive=True)
    return out


def series_cover(key: str = "1x1"):
    """系列（合集）封面：标题行写「全 N 集」而不是「第 N 集」，面板里放系列一句话 + 阶段跨度。

    抖音/小红书的**合集**封面要求 1:1（抖音：≤5MB、1080×1080 最佳），所以默认出 1x1；
    `--series-cover` 同时出 16x9，B 站/知乎的合集也能用。
    """
    from PIL import ImageDraw

    w, h = SIZES[key]
    geo = common.Geometry(f"cover-{key}", w, h, top=int(h * 0.13), bottom=0, split_at=0.5)
    img = common.video_bg(geo).copy()
    lay = compose.Layout(geo)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 0, geo.w, geo.top], fill=common.INK)
    img.paste(compose._div_glow(geo), (0, geo.top), compose._div_glow(geo))
    d.line([0, geo.top - 5, geo.w, geo.top - 5], fill=(68, 147, 248), width=5)
    chip = f"{SERIES} · 全 {SERIES_COUNT} 集"
    compose._sh_text(d, (geo.pad, 34 if not geo.portrait else 60), chip, lay.f_chip, common.SMALL, anchor="la")
    tx = geo.w / 2 if geo.portrait else geo.w - geo.pad
    compose._sh_text(d, (tx, 30 if not geo.portrait else 108), SERIES_STAGES, lay.f_seg,
                     common.TXT, anchor="ma" if geo.portrait else "ra")

    pw = int(w * 0.86)
    px = (w - pw) // 2
    pad_x, pad_y = int(pw * 0.07), int(h * 0.055)
    inner_w = pw - 2 * pad_x
    single, multi = HOOK_SIZE[key]
    f_hook = common.font("bold", single)
    lines = compose.wrap_punct_first(SERIES_TAGLINE, f_hook, inner_w)
    if len(lines) > 1:
        f_hook = common.font("bold", multi)
        lines = compose.wrap_punct_first(SERIES_TAGLINE, f_hook, inner_w)
    widths = [f_hook.getbbox(ln)[2] for ln in lines]
    f_stage = common.font("text", 46 if key == "16x9" else 42)
    rows = [("hook", ln, f_hook, common.TXT, int(f_hook.size * 1.32)) for ln in lines]
    rows.append(("stage", SERIES_STAGES, f_stage, common.TONES["gold"], int(f_stage.size * 1.7)))
    ph = pad_y * 2 + sum(r[4] for r in rows)
    py = int(h * 0.5 - ph / 2) if key == "16x9" else int(h * 0.52 - ph / 2)
    compose._paint_panel(img, (px, py, pw, ph))
    y = py + pad_y
    for _kind, text, fnt, fill, rh in rows:
        compose._sh_text(d, (w / 2, y + rh / 2), text, fnt, fill, anchor="mm")
        y += rh
    f_foot = common.font("text", 38 if key == "16x9" else 34)
    compose._sh_text(d, (w / 2, py + ph + int(h * 0.055)), SERIES_CTA, f_foot, common.SMALL, anchor="mm")
    meta = {"size": (w, h), "panel": (px, py, pw, ph), "inner_w": inner_w, "lines": lines, "line_widths": widths}
    return img, meta


def render_series_cover(key: str) -> Path:
    img, _ = series_cover(key)
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    out = COVER_DIR / f"series-{key}.jpg"
    img.convert("RGB").save(out, quality=92, optimize=True, progressive=True)
    return out


def ts(sec: float) -> str:
    s = int(round(sec))
    return f"{s // 60:02d}:{s % 60:02d}"


def chapters(tl: dict) -> list[tuple[float, str]]:
    """每段第一拍的实测起点——B 站/知乎会按 `mm:ss 标题` 生成章节。"""
    out, seen = [], set()
    for b in tl["beats"]:
        if b["seg"] in seen:
            continue
        seen.add(b["seg"])
        out.append((b["start"], b["seg_title"]))
    return out


def clip_text(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    return text[: max(1, limit - 1)].rstrip() + "…", True


def series_meta(spec: dict) -> tuple[str, str, str]:
    """系列三件套：名字 / 集数 / 覆盖范围。

    默认主系列「BMS 从入门到精通」；续集（第 8 集起、阶段 7 起）在 spec 里覆盖
    `series_count` / `series_stages`。续集口径要是整句换（正片与续集各自说清），
    用 `body_series_line`——它整句顶掉「<系列> 第 N 集（全 X 集，覆盖 Y）」，
    因为「全几集」对新旧两种读者是两句话，拼不出来。
    """
    return (spec.get("series") or SERIES,
            str(spec.get("series_count") or SERIES_COUNT),
            spec.get("series_stages") or SERIES_STAGES)


def body_of(spec: dict, tl: dict) -> str:
    ch = "\n".join(f"{ts(t)} {title}" for t, title in chapters(tl))
    ck = "\n".join(f"{i}. {item}" for i, item in enumerate(spec["checklist"], 1))
    dur = tl["duration"]
    series, count, stages = series_meta(spec)
    line = spec.get("body_series_line") or f"{series} 第 {spec['no']} 集（全 {count} 集，覆盖{stages}）。"
    head = (f"《{spec['title']}》\n\n"
            f"{line}"
            f"本集 {int(dur // 60)} 分 {round(dur) % 60:.0f} 秒，{len(spec['segments'])} 段，"
            f"按 chapter 跳：\n\n{ch}\n\n"
            f"本集验收（做完能勾的 {len(spec['checklist'])} 条）：\n{ck}\n\n"
            f"{spec.get('cta', '')}\n")
    return head


def pack(slug: str) -> dict:
    spec = spec_mod.load_spec(slug)
    tl = spec_mod.timeline(slug)
    stage, hook = hook_of(spec["title"])
    series, count, stages = series_meta(spec)
    body = body_of(spec, tl)
    titles = {
        "bilibili": f"{hook}｜{stage}｜{series} 第 {spec['no']} 集",
        # 小红书标题上限 20 字：默认用钩子；钩子不够具象时由 spec 的
        # xiaohongshu_title 给短钩子（改标题要回填到 spec，别只改线上）。
        "xiaohongshu": spec.get("xiaohongshu_title") or (hook or stage),
        # 抖音标题上限 30 字（发布页实测）：默认拼「系列 + 集号 + 钩子」，
        # 钩子太长时由 spec 里的 douyin_title 给短版，别让生成器从中间截断。
        "douyin": spec.get("douyin_title") or f"{series} 第 {spec['no']} 集｜{hook}",
        # 知乎标题上限 50 字（发布页实测）：标题超限时发布按钮变灰，
        # 拼不下时由 spec 里的 zhihu_title 给短版。
        "zhihu": spec.get("zhihu_title") or f"{spec['title']}（{series} 第 {spec['no']} 集）",
    }
    covers = {k: f"media/video/out/publish/cover/{slug}-{k}.jpg" for k in SIZES}
    videos = {}
    for aspect in ("16x9", "9x16"):
        p = common.OUT / f"{slug}-{aspect}.mp4"
        videos[aspect] = {"path": common.rel(p), "mb": round(p.stat().st_size / 1e6, 1) if p.exists() else None}

    platforms = {}
    for name, cfg in PLATFORMS.items():
        title, t_tr = clip_text(titles[name], cfg["title"])
        tags = ("　".join("#" + t for t in cfg["tags"]) if cfg["tags"] else "")
        full = body + (f"\n{tags}\n" if tags else "")
        text, b_tr = clip_text(full, cfg["body"])
        platforms[name] = {"cover": covers[cfg["cover"]], "title": title, "title_trimmed": t_tr,
                           "body": text, "body_trimmed": b_tr, "tags": cfg["tags"],
                           "limits": {"title": cfg["title"], "body": cfg["body"]},
                           "video": videos["9x16" if cfg["cover"] in {"3x4", "9x16"} else "16x9"]}
    return {"slug": slug, "no": spec["no"], "title": spec["title"], "stage": stage, "hook": hook,
            "duration": tl["duration"], "segments": len(spec["segments"]), "beats": len(tl["beats"]),
            "covers": covers, "videos": videos, "chapters": chapters(tl),
            "checklist": spec["checklist"], "platforms": platforms}


def write_md(p: dict) -> Path:
    posix = lambda s: str(s).replace("\\", "/")  # noqa: E731 — 平台文案里的路径统一正斜杠
    lines = [f"# {p['title']}", "",
             f"- slug：`{p['slug']}`　时长 {int(p['duration'] // 60)} 分 {round(p['duration']) % 60:.0f} 秒　"
             f"{p['segments']} 段 / {p['beats']} beat",
             f"- 封面：`{posix(p['covers']['16x9'])}`（16:9）· `{posix(p['covers']['3x4'])}`（3:4）· `{posix(p['covers']['9x16'])}`（9:16）",
             f"- 成片：`{posix(p['videos']['16x9']['path'])}`（{p['videos']['16x9']['mb']} MB）· "
             f"`{posix(p['videos']['9x16']['path'])}`（{p['videos']['9x16']['mb']} MB）", ""]
    for name, plate in p["platforms"].items():
        lines += [f"## {name}", "",
                  f"- 标题（{len(plate['title'])}/{plate['limits']['title']} 字"
                  + ("，已截断" if plate["title_trimmed"] else "") + f"）：{plate['title']}",
                  f"- 封面：`{plate['cover']}`",
                  "", "```text", plate["body"].rstrip(), "```", ""]
    out = PUBLISH / f"{p['slug']}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def write_kit(p: dict) -> list[Path]:
    """一平台一集一份「复制粘贴件」：标题、分区（B 站）、标签/话题、正文、素材路径。

    B 站另出一份分段章节文件——投稿页的「分段章节」是独立输入框，粘在简介里不算。
    """
    kit = PUBLISH / "kit"
    out: list[Path] = []
    for name, plate in p["platforms"].items():
        head = [f"# {p['title']} → {name}（{p['slug']}）", ""]
        head += [f"## 标题（{len(plate['title'])}/{plate['limits']['title']} 字）", plate["title"], ""]
        if name == "bilibili":
            head += [f"## 分区（候选，投稿时现选）\n{' / '.join(BILI_AREA['candidates'])}"
                     f"——{BILI_AREA['note']}", ""]
            head += [f"## 标签（{len(plate['tags'])}/{BILI_TAGS_MAX}）", "，".join(plate["tags"]), ""]
        else:
            head += ["## 话题", ("　".join("#" + t for t in plate["tags"]) or "（该平台不加话题）"), ""]
        head += [f"## 正文（{len(plate['body'])}/{plate['limits']['body']} 字）",
                 "```text", plate["body"].rstrip(), "```", ""]
        if name == "xiaohongshu" and p["duration"] > XHS_LIMIT["seconds"]:
            head += [f"## 时长提醒\n本集 {p['duration']:.0f} s 超过小红书发布页当前写的上限"
                     f"（{XHS_LIMIT['note']}）：需裁短或分段。", ""]
        head += ["## 素材", f"成片：{plate['video']['path']}（{plate['video']['mb']} MB）",
                 f"封面：{plate['cover']}", ""]
        path = kit / name / f"{p['slug']}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(head), encoding="utf-8")
        out.append(path)
    lines = [f"{ts(t)} {title}" for t, title in p["chapters"]]
    chap = kit / "bilibili" / f"{p['slug']}-chapters.txt"
    chap.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out.append(chap)
    return out


def build(slug: str, with_kit: bool = False) -> Path:
    for key in SIZES:
        render_cover(slug, key)
    p = pack(slug)
    common.save_json(PUBLISH / f"{p['slug']}.json", p)
    if with_kit:
        write_kit(p)
    return write_md(p)


def selftest(slug: str) -> int:
    """量渲染出来的封面，不读版面函数：黑帧门、面板描边能扫到、文字不溢出；
    文案侧量预算与章节单调。"""
    import numpy as np

    bad: list[str] = []
    for variant in ("", "q"):
        if variant == "q" and not question_of(slug):
            bad.append("问句版封面没有素材（spec 里没有 question beat）")
        for key, (w, h) in SIZES.items():
            img, meta = cover_image(slug, key, variant)
            if img.size != (w, h):
                bad.append(f"{key}{variant} 尺寸 {img.size} ≠ {(w, h)}")
            a = np.asarray(img.convert("L"), dtype="float32")
            blocks = a[: h // 64 * 64, : w // 64 * 64].reshape(h // 64, 64, w // 64, 64).mean(axis=(1, 3))
            if blocks.min() < 8:
                bad.append(f"{key}{variant} 最暗 64×64 块 {blocks.min():.1f} < 8（黑帧门）")
            if blocks.max() - blocks.min() < 12:
                bad.append(f"{key}{variant} 全图对比只有 {blocks.max() - blocks.min():.1f}，面板没画上？")
            px, py, pw, ph = meta["panel"]
            mid = py + ph // 2
            for x in (px, px + pw - 1):
                r, g, b = img.getpixel((x, mid))[:3]
                if max(abs(r - common.EDGE[0]), abs(g - common.EDGE[1]), abs(b - common.EDGE[2])) > 24:
                    bad.append(f"{key}{variant} 面板描边扫不到：(x={x}, y={mid}) = {(r, g, b)} ≠ EDGE")
            for ln, width in zip(meta["lines"], meta["line_widths"], strict=True):
                if width > meta["inner_w"] + 1:
                    bad.append(f"{key}{variant} 大字溢出面板：{ln!r} {width} > {meta['inner_w']}")
    p = pack(slug)
    sp = spec_mod.load_spec(slug)
    _series, _count, _stages = series_meta(sp)
    want = sp.get("body_series_line") or f"{_series} 第 {sp['no']} 集（全 {_count} 集，覆盖{_stages}）。"
    for name, plate in p["platforms"].items():
        if len(plate["title"]) > plate["limits"]["title"]:
            bad.append(f"{name} 标题 {len(plate['title'])} 超预算 {plate['limits']['title']}")
        if len(plate["body"]) > plate["limits"]["body"]:
            bad.append(f"{name} 正文 {len(plate['body'])} 超预算 {plate['limits']['body']}")
        low = plate["body"].lower()
        if "github" in low or "http" in low:
            bad.append(f"{name} 正文里还有仓库链接（发布文案不写 github/外链）")
        if want not in plate["body"]:
            bad.append(f"{name} 正文的系列口径不是「{want}」")
    if len(p["platforms"]["bilibili"]["tags"]) != BILI_TAGS_MAX:
        bad.append(f"B 站标签 {len(p['platforms']['bilibili']['tags'])} 个 ≠ {BILI_TAGS_MAX} 个")
    for path in write_kit(p):
        if not path.exists() or not path.read_text(encoding="utf-8").strip():
            bad.append(f"kit 文件空或缺失：{path}")
    chap_lines = (PUBLISH / "kit" / "bilibili" / f"{slug}-chapters.txt").read_text(encoding="utf-8").splitlines()
    if len(chap_lines) != p["segments"]:
        bad.append(f"章节文件 {len(chap_lines)} 行 ≠ 段数 {p['segments']}")
    if not chap_lines[:1] or not chap_lines[0].startswith("00:00"):
        bad.append(f"章节文件首行不是 00:00：{chap_lines[:1]}")
    bili = (PUBLISH / "kit" / "bilibili" / f"{slug}.txt").read_text(encoding="utf-8")
    if "未经投稿页核实" not in bili:
        bad.append("B 站 kit 没标明分区是候选（分区列表本轮没在投稿页核实过）")
    xhs = (PUBLISH / "kit" / "xiaohongshu" / f"{slug}.txt").read_text(encoding="utf-8")
    if p["duration"] > XHS_LIMIT["seconds"] and "时长提醒" not in xhs:
        bad.append(f"小红书 kit 缺时长提醒（本集 {p['duration']:.0f} s > {XHS_LIMIT['seconds']} s）")
    if p["duration"] <= XHS_LIMIT["seconds"] and "时长提醒" in xhs:
        bad.append(f"小红书 kit 多写了时长提醒（本集 {p['duration']:.0f} s 在 {XHS_LIMIT['note']} 之内）")
    mb = p["videos"]["9x16"]["mb"] or 0
    if mb * 1e6 > XHS_LIMIT["bytes"]:
        bad.append(f"竖版成片 {mb} MB 超小红书发布页写的 {XHS_LIMIT['bytes'] / 1024 ** 3:.0f} GB")
    simg, smeta = series_cover("1x1")
    if simg.size != (1080, 1080):
        bad.append(f"系列封面尺寸 {simg.size} ≠ (1080, 1080)")
    for ln, width in zip(smeta["lines"], smeta["line_widths"], strict=True):
        if width > smeta["inner_w"] + 1:
            bad.append(f"系列封面大字溢出面板：{ln!r} {width} > {smeta['inner_w']}")
    times = [t for t, _ in p["chapters"]]
    if not times or times[0] != 0.0:
        bad.append(f"章节首条不是 00:00：{times[:1]}")
    if times != sorted(times) or len(set(times)) != len(times):
        bad.append("章节时间没有严格递增")
    if len(p["chapters"]) != p["segments"]:
        bad.append(f"章节 {len(p['chapters'])} 条 ≠ 段数 {p['segments']}")
    for msg in bad:
        print("  ✗", msg)
    print(f"publish selftest {'ok' if not bad else 'FAILED'}：{slug}")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", action="append", required=True)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--kit", action="store_true",
                    help="同时写上传用复制粘贴件 publish/kit/<平台>/<集>.txt（B 站另出分段章节文件）")
    ap.add_argument("--series-cover", action="store_true",
                    help="另出一张系列（合集）封面 series-1x1.jpg + series-16x9.jpg（抖音/小红书合集用 1:1）")
    ap.add_argument("--cover-variant", choices=["q"], default=None,
                    help="另出一套封面变体：q = 问句版（大字换成开场那道题，小红书封面 PK 用）")
    args = ap.parse_args()
    rc = 0
    if args.series_cover:
        for key in ("1x1", "16x9"):
            p = render_series_cover(key)
            print(f"系列封面 → {common.rel(p)}")
    for slug in args.episode:
        if args.selftest:
            rc |= selftest(slug)
        else:
            if args.cover_variant == "q":
                for key in SIZES:
                    print(f"问句版封面 → {common.rel(render_cover(slug, key, 'q'))}")
            md = build(slug, with_kit=args.kit)
            print(f"发布包 → {common.rel(md)}" + (f"（含 kit：{common.rel(PUBLISH / 'kit')}）" if args.kit else ""))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
