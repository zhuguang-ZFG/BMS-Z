#!/usr/bin/env python3
"""发布包：平台封面 + 四平台文案。

封面复用成片的皮肤三件套（`common.video_bg` 环境光背景 / `compose._paint_panel`
立层面板 / `compose._num_glow` 数字光晕），不引入新视觉语言。一集三张，落在
`media/video/out/publish/`（产物不入库）：

    cover/<slug>-16x9.jpg   1920×1080   B 站、知乎、抖音（横版）
    cover/<slug>-3x4.jpg    1080×1440   小红书
    cover/<slug>-9x16.jpg   1080×1920   抖音（竖版）

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
REPO = "https://github.com/zhuguang-ZFG/BMS-Z"
PUBLISH = common.OUT / "publish"
COVER_DIR = PUBLISH / "cover"

SIZES = {"16x9": (1920, 1080), "3x4": (1080, 1440), "9x16": (1080, 1920)}
HOOK_SIZE = {"16x9": (112, 92), "3x4": (100, 84), "9x16": (100, 84)}  # (一行就放得下, 要折行)

# 平台侧：封面用哪张、标题/正文字符预算、话题。预算以平台当期规则为准，会变。
PLATFORMS = {
    "bilibili": {"cover": "16x9", "title": 80, "body": 2000,
                 "tags": ["BMS", "锂电池", "电池管理系统", "硬核科普"]},
    "xiaohongshu": {"cover": "3x4", "title": 20, "body": 1000,
                    "tags": ["BMS", "锂电池", "新能源", "硬核科普"]},
    "douyin": {"cover": "9x16", "title": 55, "body": 1000,
               "tags": ["BMS", "锂电池", "新能源", "知识分享"]},
    "zhihu": {"cover": "16x9", "title": 100, "body": 2000, "tags": []},
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


def cover_image(slug: str, key: str):
    """画一张封面，返回 (图, 元数据)。元数据给 selftest 用：面板盒与每行文字宽度。"""
    from PIL import ImageDraw

    spec = spec_mod.load_spec(slug)
    tl = spec_mod.timeline(slug)
    w, h = SIZES[key]
    stage, hook = hook_of(spec["title"])
    if not hook:
        hook = stage

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
    if big:
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


def render_cover(slug: str, key: str) -> Path:
    img, _ = cover_image(slug, key)
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    out = COVER_DIR / f"{slug}-{key}.jpg"
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


def body_of(spec: dict, tl: dict) -> str:
    ch = "\n".join(f"{ts(t)} {title}" for t, title in chapters(tl))
    ck = "\n".join(f"{i}. {item}" for i, item in enumerate(spec["checklist"], 1))
    dur = tl["duration"]
    head = (f"《{spec['title']}》\n\n"
            f"{SERIES} 第 {spec['no']} 集（全 6 集，覆盖阶段 1–6）。"
            f"本集 {int(dur // 60)} 分 {round(dur) % 60:.0f} 秒，{len(spec['segments'])} 段，"
            f"按 chapter 跳：\n\n{ch}\n\n"
            f"本集验收（做完能勾的 {len(spec['checklist'])} 条）：\n{ck}\n\n"
            f"{spec.get('cta', '')}\n讲义与可勾选清单：{REPO}\n")
    return head


def pack(slug: str) -> dict:
    spec = spec_mod.load_spec(slug)
    tl = spec_mod.timeline(slug)
    stage, hook = hook_of(spec["title"])
    body = body_of(spec, tl)
    titles = {
        "bilibili": f"{hook}｜{stage}｜{SERIES} 第 {spec['no']} 集",
        "xiaohongshu": hook or stage,
        "douyin": f"{SERIES} 第 {spec['no']} 集｜{hook}",
        "zhihu": f"{spec['title']}（{SERIES} 第 {spec['no']} 集）",
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


def build(slug: str) -> Path:
    for key in SIZES:
        render_cover(slug, key)
    p = pack(slug)
    common.save_json(PUBLISH / f"{p['slug']}.json", p)
    return write_md(p)


def selftest(slug: str) -> int:
    """量渲染出来的封面，不读版面函数：黑帧门、面板描边能扫到、文字不溢出；
    文案侧量预算与章节单调。"""
    import numpy as np

    bad: list[str] = []
    for key, (w, h) in SIZES.items():
        img, meta = cover_image(slug, key)
        if img.size != (w, h):
            bad.append(f"{key} 尺寸 {img.size} ≠ {(w, h)}")
        a = np.asarray(img.convert("L"), dtype="float32")
        blocks = a[: h // 64 * 64, : w // 64 * 64].reshape(h // 64, 64, w // 64, 64).mean(axis=(1, 3))
        if blocks.min() < 8:
            bad.append(f"{key} 最暗 64×64 块 {blocks.min():.1f} < 8（黑帧门）")
        if blocks.max() - blocks.min() < 12:
            bad.append(f"{key} 全图对比只有 {blocks.max() - blocks.min():.1f}，面板没画上？")
        px, py, pw, ph = meta["panel"]
        mid = py + ph // 2
        for x in (px, px + pw - 1):
            r, g, b = img.getpixel((x, mid))[:3]
            if max(abs(r - common.EDGE[0]), abs(g - common.EDGE[1]), abs(b - common.EDGE[2])) > 24:
                bad.append(f"{key} 面板描边扫不到：(x={x}, y={mid}) = {(r, g, b)} ≠ EDGE")
        for ln, width in zip(meta["lines"], meta["line_widths"], strict=True):
            if width > meta["inner_w"] + 1:
                bad.append(f"{key} 大字溢出面板：{ln!r} {width} > {meta['inner_w']}")
    p = pack(slug)
    for name, plate in p["platforms"].items():
        if len(plate["title"]) > plate["limits"]["title"]:
            bad.append(f"{name} 标题 {len(plate['title'])} 超预算 {plate['limits']['title']}")
        if len(plate["body"]) > plate["limits"]["body"]:
            bad.append(f"{name} 正文 {len(plate['body'])} 超预算 {plate['limits']['body']}")
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
    args = ap.parse_args()
    rc = 0
    for slug in args.episode:
        if args.selftest:
            rc |= selftest(slug)
        else:
            md = build(slug)
            print(f"发布包 → {common.rel(md)}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
