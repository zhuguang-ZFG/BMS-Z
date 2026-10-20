#!/usr/bin/env python3
"""发布包：平台封面 + 四平台文案。

封面走一套**更亮的同源皮肤**（`cover_art`）：深海军蓝/青绿渐变底、琥珀集号徽章、
双色超大标题、暖紫问句条、三步 chips、右侧电池吉祥物。成片本身仍用深底低饱和的
克制皮肤——两者同源（同一套字体、同一组强调色），但封面要在手机列表里第一眼抓人。
一集三张，落在 `media/video/out/publish/`（产物不入库）：

    cover/<slug>-16x9.jpg   1920×1080   B 站、知乎、抖音（横版）
    cover/<slug>-3x4.jpg    1080×1440   小红书
    cover/<slug>-9x16.jpg   1080×1920   抖音（竖版）

加 `--cover-variant q` 另出**问句版**（同名加 `-q`）：大字换成该集开场那道题，
问句条写「答案在片尾」。小红书封面 PK 是「主封面 + 最多 3 张备选」的 A/B，备选
可以自己传，所以一张图不够测——问句版就是备选。要换问句在 spec 里加
`cover_question`（默认取第一条带 question 的 beat）。封面文案字段：
`cover_title`（两行大字）、`cover_question`、`cover_chips`（三片，每片两行）、
`cover_bubble`（吉祥物气泡）、`cover_mood`（happy/thinking/guard）。

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
import cover_art  # noqa: E402
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
    # tags_in_body：标签是否写进正文。B 站/知乎走独立标签栏，正文里写 `#标签`
    # 只是噪声（还占正文预算）；小红书把 `#话题` 当正文一部分（且需在编辑器里
    # 从联想项选中才算话题）；抖音正文里的 `#话题` 会原生变成话题。
    "bilibili": {"cover": "16x9", "title": 80, "body": 2000, "tags_in_body": False,
                 "tags": ["BMS", "锂电池", "电池管理系统", "新能源", "储能",
                          "嵌入式", "电子工程", "硬件设计", "电路设计", "硬核科普"]},
    "xiaohongshu": {"cover": "3x4", "title": 20, "body": 1000, "tags_in_body": True,
                    "tags": ["BMS", "锂电池", "新能源", "硬核科普"]},
    "douyin": {"cover": "9x16", "title": 30, "body": 1000, "tags_in_body": True,
               "tags": ["BMS", "锂电池", "新能源", "知识分享"]},
    # 知乎发布页实测：标题 50 字（超限时发布按钮保持 disabled、点了也不发）
    "zhihu": {"cover": "16x9", "title": 50, "body": 2000, "tags": [], "tags_in_body": False},
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


def _fallback_chips(spec: dict) -> list[list[str]]:
    """没写 cover_chips 时的兜底：取前三个非开场/非口诀的段名，上行为主、下行留空。"""
    names = [s["title"] for s in spec["segments"]
             if "开场" not in s["title"] and "口诀" not in s["title"]]
    out = [[n[:8], ""] for n in names[:3]]
    return out + [["", ""]] * (3 - len(out))


def cover_image(slug: str, key: str, variant: str = ""):
    """画一张封面，返回 (图, 元数据)。元数据给 selftest 用：文字 zone、吉祥物矩形、
    每行实际字号与宽度。

    `variant="q"` 是**问句版**：大字换成开场那道题（封面 A/B 用，小红书封面 PK 可以
    自己上传备选封面）。想换问句在 spec 里加 `cover_question`，别改线上图。
    """
    spec = spec_mod.load_spec(slug)
    tl = spec_mod.timeline(slug)
    stage, hook = hook_of(spec["title"])
    question = (spec.get("cover_question") or question_of(slug) or "").strip()
    if variant == "q":
        title = cover_art.wrap_title(question or hook, key)
        strip_text = "答案在片尾"
    else:
        title = [str(t).strip() for t in (spec.get("cover_title") or [])]
        title = [t for t in title if t][:2] or [hook or stage]
        strip_text = question or (str((spec.get("cover_chips") or [[""]])[0][0]))
    chips = spec.get("cover_chips") or _fallback_chips(spec)
    big = key_big(tl)
    right_note = f"本集尺子 {big}" if big else ""
    img, meta = cover_art.render(
        key,
        series_line=spec.get("series") or SERIES,
        badge=f"第 {spec['no']:02d} 集",
        stage=stage,
        title=title,
        question=strip_text,
        chips=chips,
        bubble=str(spec.get("cover_bubble") or ""),
        mood=str(spec.get("cover_mood") or "happy"),
        right_note=right_note,
        footer=str(spec.get("cta") or ""),
        big_no=(f"{spec['no']:02d}" if variant != "q" else "?"),
        variant=variant,
    )
    return img, meta


def render_cover(slug: str, key: str, variant: str = "") -> Path:
    img, _ = cover_image(slug, key, variant)
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    out = COVER_DIR / f"{slug}-{key}{'-' + variant if variant else ''}.jpg"
    img.convert("RGB").save(out, quality=92, optimize=True, progressive=True)
    return out


def series_cover(key: str = "1x1"):
    """系列（合集）封面：标题写系列一句话，徽章写「全 N 集」，chips 是三个能力段。

    抖音/小红书的**合集**封面要求 1:1（抖音：≤5MB、1080×1080 最佳），所以默认出 1x1；
    `--series-cover` 同时出 16x9，B 站/知乎的合集也能用。系列口径（7 集 / 阶段 0–6）
    仍由 SERIES_COUNT / SERIES_STAGES / SERIES_TAGLINE 三个常量给，不从这里另造一套。
    """
    title = SERIES_TAGLINE.replace("：", "||").split("||")
    title_w = 968 if key == "1x1" else (1060 if key == "16x9" else None)
    # 16:9 的标题与右侧气泡同高，宽度要收到气泡左缘之外（1188−12），否则
    # 第二行会压到气泡上；1:1 的吉祥物在右下，标题可以占满整幅。
    img, meta = cover_art.render(
        key,
        series_line=f"{SERIES} · 合集",
        badge=f"全 {SERIES_COUNT} 集",
        stage=SERIES_STAGES,
        title=title,
        question=SERIES_CTA,
        chips=[["阶段 0–2", "打地基"], ["阶段 3–5", "核心能力"], ["阶段 6", "毕业项目"]],
        bubble="一条线走完",
        mood="happy",
        right_note="",
        footer="",
        big_no=f"{int(SERIES_COUNT):02d}",
        title_w=title_w,
    )
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


def depth_block(spec: dict) -> str:
    """可选的内容加深块：一句话结论 / 关键数字 / 常见误区。

    只写视频里真实出现过的数字与结论（旁白里推过的），不另造数据。
    """
    d = spec.get("depth") or {}
    if not d:
        return ""
    parts = []
    if d.get("one_liner"):
        parts.append(f"本集一句话\n{d['one_liner']}\n")
    nums = d.get("numbers") or []
    if nums:
        parts.append("关键数字与结论（视频里逐个推过）\n" + "\n".join(f"- {n}" for n in nums) + "\n")
    myths = d.get("myths") or []
    if myths:
        parts.append("先别踩的坑\n" + "\n".join(f"- {m}" for m in myths) + "\n")
    if not parts:
        return ""
    return "\n".join(parts).rstrip("\n") + "\n\n"


def body_of(spec: dict, tl: dict) -> str:
    ch = "\n".join(f"{ts(t)} {title}" for t, title in chapters(tl))
    ck = "\n".join(f"{i}. {item}" for i, item in enumerate(spec["checklist"], 1))
    dur = tl["duration"]
    series, count, stages = series_meta(spec)
    line = spec.get("body_series_line") or f"{series} 第 {spec['no']} 集（全 {count} 集，覆盖{stages}）。"
    depth = depth_block(spec)
    head = (f"《{spec['title']}》\n\n"
            f"{line}"
            f"本集 {int(dur // 60)} 分 {round(dur) % 60:.0f} 秒，{len(spec['segments'])} 段，"
            f"按 chapter 跳：\n\n{ch}\n\n"
            f"{depth}"
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
        tags = (" ".join("#" + t for t in cfg["tags"])
                if cfg["tags"] and cfg.get("tags_in_body", True) else "")
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
            head += ["## 话题", (" ".join("#" + t for t in plate["tags"]) or "（该平台不加话题）"), ""]
            if name == "xiaohongshu":
                head += ["## 话题挂载（重要）",
                         "粘贴的 `#` 只是普通文字，不算话题，推荐会少一路入口。",
                         "发布时在正文末尾打 `#` + 名字，从联想里选中真话题（四个："
                         + " / ".join(plate["tags"]) + "），让它变成话题块再发布。", ""]
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


def _accent_share(img) -> float:
    """青色 + 琥珀色像素占比。封面要“第一眼抓人”，但不能靠大面积亮色糊成广告——
    1.5%–20% 是给缩略图留的可读区间：低于下限说明强调色没画上/被盖住，高于上限
    说明亮色已经成了底色，白字反而难读。"""
    import numpy as np

    a = np.asarray(img.convert("RGB")).astype(int)
    cy = np.abs(a - np.array(cover_art.CYAN)).sum(axis=2) < 90
    am = np.abs(a - np.array(cover_art.AMBER)).sum(axis=2) < 90
    return float((cy | am).mean())


def _amber_fill(img, rect) -> float:
    """矩形内接近琥珀色的像素占比：集号徽章必须是实心琥珀，不能只是一圈描边。"""
    import numpy as np

    x, y, w, h = rect
    a = np.asarray(img.convert("RGB")).astype(int)[y:y + h, x:x + w]
    return float((np.abs(a - np.array(cover_art.AMBER)).sum(axis=2) < 90).mean())


def _field_limits(sp: dict) -> list[str]:
    """封面文案的格数上限：大字每行 12、问句 24、chip 每行 10、气泡 10。
    只校验 spec 里真写了的字段；缺字段走回退，不在这里另立文案。"""
    import spec as sm

    bad = []
    for i, line in enumerate(sp.get("cover_title") or []):
        if sm.text_width(line) > 12:
            bad.append(f"cover_title 第 {i + 1} 行 {sm.text_width(line):.1f} 格 > 12：{line!r}")
    q = sp.get("cover_question")
    if q and sm.text_width(q) > 24:
        bad.append(f"cover_question {sm.text_width(q):.1f} 格 > 24：{q!r}")
    for ci, chip in enumerate(sp.get("cover_chips") or []):
        for line in chip:
            if sm.text_width(line) > 10:
                bad.append(f"cover_chips[{ci}] {sm.text_width(line):.1f} 格 > 10：{line!r}")
    if len(sp.get("cover_chips") or []) != 3:
        bad.append(f"cover_chips 有 {len(sp.get('cover_chips') or [])} 片，要 3 片")
    bubble = sp.get("cover_bubble")
    if bubble and sm.text_width(bubble) > 10:
        bad.append(f"cover_bubble {sm.text_width(bubble):.1f} 格 > 10：{bubble!r}")
    if sp.get("cover_mood") and sp["cover_mood"] not in {"happy", "thinking", "guard"}:
        bad.append(f"cover_mood 不认识：{sp['cover_mood']!r}")
    return bad


def selftest(slug: str) -> int:
    """量渲染出来的封面，不读版面函数：黑帧门、强调色占比、徽章实心、文字放得下、
    文字 zone 不压吉祥物；文案侧量预算与章节单调。"""
    import numpy as np

    bad: list[str] = []
    sp = spec_mod.load_spec(slug)
    if not (sp.get("cover_question") or question_of(slug)):
        bad.append("问句版封面没有素材（spec 里没有 cover_question 或 question beat）")
    bad += _field_limits(sp)
    size_floor = {"16x9": 108, "3x4": 82, "9x16": 86, "1x1": 66}
    for variant in ("", "q"):
        for key, (w, h) in SIZES.items():
            img, meta = cover_image(slug, key, variant)
            if img.size != (w, h):
                bad.append(f"{key}{variant} 尺寸 {img.size} ≠ {(w, h)}")
            a = np.asarray(img.convert("L"), dtype="float32")
            blocks = a[: h // 64 * 64, : w // 64 * 64].reshape(h // 64, 64, w // 64, 64).mean(axis=(1, 3))
            if blocks.min() < 8:
                bad.append(f"{key}{variant} 最暗 64×64 块 {blocks.min():.1f} < 8（黑帧门）")
            if blocks.max() - blocks.min() < 12:
                bad.append(f"{key}{variant} 全图对比只有 {blocks.max() - blocks.min():.1f}，图形没画上？")
            share = _accent_share(img)
            if not 0.015 <= share <= 0.20:
                bad.append(f"{key}{variant} 青+琥珀像素占比 {share * 100:.1f}% 不在 1.5%–20%")
            if _amber_fill(img, meta["zones"]["badge"]) < 0.40:
                bad.append(f"{key}{variant} 集号徽章不是实心琥珀（填充 "
                           f"{_amber_fill(img, meta['zones']['badge']) * 100:.0f}%）")
            for line in meta["title_lines"]:
                if line["width"] > line["max_w"] + 1:
                    bad.append(f"{key}{variant} 标题溢出：{line['text']!r} "
                               f"{line['width']} > {line['max_w']}")
                if line["size"] < size_floor[key]:
                    bad.append(f"{key}{variant} 标题缩到 {line['size']}px < 下限 {size_floor[key]}px")
            ql = meta["q_line"]
            if ql["width"] > ql["max_w"] + 1:
                bad.append(f"{key}{variant} 问句条溢出：{ql['text']!r} {ql['width']} > {ql['max_w']}")
            for line in meta["chip_lines"]:
                if line["width"] > line["max_w"] + 1:
                    bad.append(f"{key}{variant} chip 溢出：{line['text']!r} "
                               f"{line['width']} > {line['max_w']}")
            for hit in cover_art.selftest_zone_hits(meta):
                bad.append(f"{key}{variant} {hit}")
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
    for skey, (sw, sh) in (("1x1", (1080, 1080)), ("16x9", (1920, 1080))):
        simg, smeta = series_cover(skey)
        if simg.size != (sw, sh):
            bad.append(f"系列封面 {skey} 尺寸 {simg.size} ≠ {(sw, sh)}")
        for line in smeta["title_lines"]:
            if line["width"] > line["max_w"] + 1:
                bad.append(f"系列封面 {skey} 标题溢出：{line['text']!r} "
                           f"{line['width']} > {line['max_w']}")
        for hit in cover_art.selftest_zone_hits(smeta):
            bad.append(f"系列封面 {skey} {hit}")
        if not 0.015 <= _accent_share(simg) <= 0.20:
            bad.append(f"系列封面 {skey} 青+琥珀占比 {_accent_share(simg) * 100:.1f}% 越界")
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
