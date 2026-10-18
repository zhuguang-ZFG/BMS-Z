"""分镜（spec）的读、校验、派生。

一集一份 `specs/epNN-*.json`，它是这条流水线唯一的"编剧"文件：画面上出现哪张动画、
旁白念什么、大字写什么，全在这里。时间轴不由人估秒数——`--timeline` 拿旁白的**实测**
时长回灌，compose 与 assemble 只认这份时间轴，不各数一遍。

用法：
    python3 tools/video/spec.py --check ep02-recognize-bms
    python3 tools/video/spec.py --draft docs/stages/stage-1-认识BMS.md --no 2
    python3 tools/video/spec.py --timeline ep02-recognize-bms
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

SPEC_DIR = Path(__file__).resolve().parent / "specs"
SVG_RE = re.compile(r"\((?:\.\./)?circuits/assets/([^)#\s]+\.svg)")
HEAD_RE = re.compile(r"^(#{2,3})\s+(.*?)\s*$", re.M)
KOUJUE_RE = re.compile(r"^> \*\*口诀\*\*\s+(.+?)\s*$", re.M)
CHECK_RE = re.compile(r"^- \[ \]\s+(.+?)\s*$", re.M)

LAYOUTS = {"figure", "split", "card", "number", "checklist", "quiz"}
# 与 bgm.py 的 DENSITY / SFX 同名同套：分镜里写错一个名字，混音时才发现就没法看了
BGM_TRACKS = {"tension", "neutral", "outro"}
SFX_NAMES = {"whoosh", "tick", "blip"}
MAX_ON_SCREEN = 4
MAX_LINES_PER_FIELD = 6
CAPTION_CHARS = 22


def char_width(ch: str) -> float:
    """中日韩字算 1 格，ASCII 与标点算半格——按字符数断行会把 "123.8 s" 切成两半。"""
    return 1.0 if ord(ch) > 0x2E80 else 0.55


def is_token_char(ch: str) -> bool:
    """不可切的一个 token 成员：**ASCII** 字母数字，加上把它们粘起来的符号。只判 isalnum 的话
    `123.8 s` 会在小数点后切开，屏幕上出现「…但 123.」和「8 s 这个数…」两条字幕。
    但必须再加 isascii()：Python 的 str.isalnum() 对汉字也返回 True，整段中文会被当成一个
    不可切断的 token，token 保护循环把断点一路左移到第 1 个字符——实测
    `wrap_to_width("主动均衡是拿电感电容…", …, 864)` 折出「主」+「动均衡是…」这种行。
    selftest 的"纯中文长句首行不得短于 600 px"就是守这一条。"""
    return (ch.isascii() and ch.isalnum()) or ch in ".,%+-/"


def text_width(s: str) -> float:
    return sum(char_width(c) for c in s)


def split_captions(text: str, max_chars: float = CAPTION_CHARS) -> list[str]:
    """旁白 → 一条一条的字幕。整段 vo 直接烧在屏幕上是读不完的（一句 60 字很常见），
    所以按标点断、再按宽度合并，每条约 22 格——手机上一眼看完的长度。"""
    parts = re.split(r"(?<=[，。！？；：、,.!?;:])", text.strip())
    chunks: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        while text_width(p) > max_chars:
            cut = len(p)
            for i in range(1, len(p) + 1):
                if text_width(p[:i]) > max_chars:
                    cut = i - 1
                    break
            cut = max(cut, 1)
            # 数字串与英文单词不拦腰切。只判 isalnum 的话 `123.8 s` 会切成「123.」+「8 s」，
            # 所以小数点、百分号这类把它们粘起来的符号也算 token
            while 1 < cut < len(p) and is_token_char(p[cut - 1]) and is_token_char(p[cut]):
                cut -= 1
            chunks.append(p[:cut])
            p = p[cut:].lstrip()
        if chunks and text_width(chunks[-1]) + text_width(p) <= max_chars:
            chunks[-1] += p
        else:
            chunks.append(p)
    return chunks


def caption_windows(vo_dur: float, chunks: list[str]) -> list[tuple[float, float, str]]:
    """一条字幕占多长，按它的字数在整句里分摊——念得长的句子在屏上留得久。"""
    if not chunks:
        return []
    weights = [max(text_width(c), 1.0) for c in chunks]
    total = sum(weights)
    out, t = [], 0.0
    for c, wgt in zip(chunks, weights, strict=True):
        span = vo_dur * wgt / total
        out.append((t, t + span, c))
        t += span
    return out


def iter_stage_svgs(stage_doc: Path) -> list[str]:
    """该阶段正文引用的动画，按出现顺序去重——系列结构靠它，不手抄图名。"""
    seen: list[str] = []
    for name in SVG_RE.findall(stage_doc.read_text(encoding="utf-8")):
        if name not in seen:
            seen.append(name)
    return seen


def find_spec(slug: str) -> Path:
    exact = SPEC_DIR / f"{slug}.json"
    if exact.exists():
        return exact
    hits = sorted(p for p in SPEC_DIR.glob("*.json") if p.stem.startswith(slug) or slug in p.stem)
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise FileNotFoundError(f"找不到分镜：{slug}（{common.rel(SPEC_DIR)} 里有的：{[p.stem for p in sorted(SPEC_DIR.glob('*.json'))]}）")
    raise ValueError(f"--episode {slug} 命中多个分镜，请写全：{[p.stem for p in hits]}")


def load_spec(slug: str) -> dict:
    return json.loads(find_spec(slug).read_text(encoding="utf-8"))


def beats(spec: dict):
    """(segment, beat, 全局序号) 的平铺迭代——所有下游模块都按这个顺序数格子。"""
    i = 0
    for seg in spec["segments"]:
        for beat in seg["beats"]:
            yield seg, beat, i
            i += 1


def beat_id(seg: dict, beat: dict, idx: int) -> str:
    return f"{seg['id']}-{idx:03d}"


def beat_layout(beat: dict, seg: dict) -> str:
    return beat.get("layout", seg.get("layout", "figure"))


def on_screen_lines(beat: dict, seg: dict) -> list[dict]:
    raw = beat.get("on_screen", seg.get("on_screen", []))
    out = []
    for item in raw:
        if isinstance(item, str):
            out.append({"t": item, "tone": ""})
        else:
            out.append({"t": item.get("t", ""), "tone": item.get("tone", "")})
    return out


ANIM_RE = re.compile(r"<(animate|animateMotion|animateTransform)\b[^>]*?/?>")


def anim_problems(svg_text: str, name: str) -> tuple[list[str], str]:
    """动效契约：运动/淡入淡出必须交代时间曲线。

    仓库的图全走 SMIL，Chromium 逐帧钉时间轴（`setCurrentTime`）渲染，所以「动画糙不糙」
    只取决于图里写没写缓动：2026-10-18 全库体检时 1600 个 animate 里 **keySplines = 0**，
    1433 个 linear、167 个 discrete——元素在「跳变」而不是「运动」，这就是观感粗糙的根。
    规则：非 discrete 的 animate 要么带 keySplines，要么显式 `data-ease="linear"`
    （时间轴上的匀速是**语义正确**的，例如点沿时间轴扫掠；这种要作者自己声明，不能靠默认）。
    另外给一句提示（不算错）：整张图 ≥6 个 animate 却一个位移/变换都没有＝纯透明度动效。
    """
    bad: list[str] = []
    n_anim = n_ease = n_motion = 0
    for m in ANIM_RE.finditer(svg_text):
        tag = m.group(0)
        n_anim += 1
        attr_name = re.search(r'attributeName="([\w-]+)"', tag)
        is_motion = (tag.startswith("<animateMotion") or tag.startswith("<animateTransform")
                     or (attr_name and attr_name.group(1) in {
                         "transform", "cx", "cy", "x", "y", "x1", "y1", "x2", "y2", "d", "points",
                         "r", "width", "height", "stroke-width", "stroke-dashoffset", "stroke-dasharray"}))
        if is_motion:
            n_motion += 1
        if 'calcMode="discrete"' in tag:
            continue
        if "keySplines=" in tag or 'data-ease="linear"' in tag:
            n_ease += 1
        else:
            who = attr_name.group(1) if attr_name else tag.split()[0].lstrip("<")
            bad.append(f"{name}：<animate {who}> 没交代时间曲线（补 keySplines，或显式 data-ease=\"linear\"）")
    note = ""
    if n_anim >= 6 and n_motion == 0:
        note = f"{name}：{n_anim} 个 animate 全是透明度（没有一个位移/变换）——动效只剩闪进闪出，考虑加运动"
    return bad, note


def check(slug: str) -> list[str]:
    problems: list[str] = []
    path = find_spec(slug)
    spec = json.loads(path.read_text(encoding="utf-8"))
    for key in ("slug", "no", "series", "title", "stage_doc", "segments"):
        if key not in spec:
            problems.append(f"{common.rel(path)} 缺字段 {key}")
    doc = common.ROOT / spec.get("stage_doc", "")
    if not spec.get("stage_doc") or not doc.exists():
        problems.append(f"stage_doc 指向的文件不存在：{spec.get('stage_doc')}")
    if spec.get("slug") != path.stem:
        problems.append(f"slug 与文件名不一致：{spec.get('slug')} vs {path.stem}")

    used: list[str] = []
    for seg in spec.get("segments", []):
        if not seg.get("id") or not seg.get("title"):
            problems.append(f"段缺 id/title：{seg.get('id') or seg}")
        if not seg.get("beats"):
            problems.append(f"段 {seg.get('id')} 没有 beat")
        for i, beat in enumerate(seg.get("beats", [])):
            bid = f"{seg.get('id')}#{i}"
            vo = beat.get("vo", "")
            if not vo.strip():
                problems.append(f"{bid} 的 vo 为空——全系列旁白驱动，静默 beat 要显式写 silence")
            if len(vo) > 260:
                problems.append(f"{bid} 的 vo 有 {len(vo)} 字，超过一条字幕上限，拆 beat")
            if beat.get("voice", "teacher") not in common.VOICE_NAMES:
                problems.append(f"{bid} 的 voice 不认识：{beat.get('voice')}")
            layout = beat_layout(beat, seg)
            if layout not in LAYOUTS:
                problems.append(f"{bid} 的 layout 不认识：{layout}（可选 {sorted(LAYOUTS)}）")
            svg = beat.get("svg", seg.get("svg"))
            if layout in {"figure", "split"}:
                if not svg:
                    problems.append(f"{bid} 用 {layout} 布局但没给 svg")
                else:
                    used.append(svg)
                    if not (common.ASSETS / svg).exists():
                        problems.append(f"{bid} 的动画文件不存在：docs/circuits/assets/{svg}")
            lines = on_screen_lines(beat, seg)
            if len(lines) > MAX_ON_SCREEN:
                problems.append(f"{bid} 的 on_screen 有 {len(lines)} 条，最多 {MAX_ON_SCREEN}")
            for ln in lines:
                if ln["tone"] not in common.TONES:
                    problems.append(f"{bid} 的 tone 不认识：{ln['tone']}")
                if len(ln["t"]) > 46:
                    problems.append(f"{bid} 的大字过长（{len(ln['t'])} 字）：{ln['t'][:24]}…")
            if layout == "number" and not beat.get("big"):
                problems.append(f"{bid} 是 number 布局但没给 big")
            if layout == "quiz":
                if not beat.get("question"):
                    problems.append(f"{bid} 是 quiz 布局但没给 question")
                opts = beat.get("options", [])
                if not 2 <= len(opts) <= 4:
                    problems.append(f"{bid} 的 options 有 {len(opts)} 个，选择题要 2–4 个")
            if layout == "checklist":
                n = int(beat.get("ticks", 0))
                if not 0 <= n <= len(spec.get("checklist", [])):
                    problems.append(f"{bid} 的 ticks={n}，超出验收清单的 {len(spec.get('checklist', []))} 条")
            if beat.get("sfx") and beat["sfx"] not in SFX_NAMES:
                problems.append(f"{bid} 的 sfx 不认识：{beat['sfx']}（可选 {sorted(SFX_NAMES)}）")
            for name in (beat.get("bgm"), seg.get("bgm")):
                if name and name not in BGM_TRACKS:
                    problems.append(f"{bid} 的 bgm 不认识：{name}（可选 {sorted(BGM_TRACKS)}）")
    unknown = [u for u in used if u not in iter_stage_svgs(doc)] if doc.exists() else []
    for u in set(unknown):
        problems.append(f"动画 {u} 不在 {doc.name} 的引用清单里（别从别的阶段串图）")
    for svg in sorted(set(used)):
        p = common.ASSETS / svg
        if not p.exists():
            continue
        bad_anim, note = anim_problems(p.read_text(encoding="utf-8"), svg)
        problems += bad_anim
        if note:
            print("  … ", note)
    if doc.exists():
        refs = iter_stage_svgs(doc)
        missing = [r for r in refs if r not in used]
        if missing:
            problems.append(f"该阶段引用的动画有 {len(missing)} 张没进分镜：{missing}")
    if not spec.get("checklist"):
        problems.append("缺 checklist：集尾的真·验收没有内容可打勾")
    return problems


def draft(stage_doc: Path, no: int) -> dict:
    """从阶段文档抽出骨架：图按正文出现顺序排，段标题取 ## / ###，口诀与验收照搬。
    生成的 vo 是占位，必须逐条重写——念文档原句会像念 PPT。"""
    text = stage_doc.read_text(encoding="utf-8")
    heads = [h[1].strip() for h in HEAD_RE.findall(text) if h[1].strip() != "本页目录"]
    svgs = iter_stage_svgs(stage_doc)
    koujue = KOUJUE_RE.findall(text)
    checklist = [c.strip() for c in CHECK_RE.findall(text)]
    segments = []
    for i, svg in enumerate(svgs):
        title = heads[i] if i < len(heads) else f"第 {i + 1} 段"
        segments.append({
            "id": f"s{i + 1:02d}",
            "title": title,
            "svg": svg,
            "layout": "figure",
            "beats": [{
                "vo": f"（占位，待写）讲 {svg.removesuffix('.svg')}：{title}",
                "on_screen": [{"t": title, "tone": "hi"}],
            }],
        })
    if koujue:
        segments.append({
            "id": "sk",
            "title": "本集口诀",
            "layout": "card",
            "beats": [{"vo": f"（占位，待写）念口诀：{k}", "svg": None, "layout": "card",
                       "on_screen": [{"t": k, "tone": "gold"}]} for k in koujue[:4]],
        })
    return {
        "slug": f"ep{no:02d}-draft",
        "no": no,
        "series": "BMS 从入门到精通",
        "title": stage_doc.stem.split("-", 2)[-1],
        "stage_doc": common.rel(stage_doc),
        "bgm": "neutral",
        "segments": segments,
        "checklist": checklist[:5],
        "cta": "文档站里每篇都有可勾选的过关标准",
        "_note": "骨架由 spec.py --draft 生成；vo 与 on_screen 必须人工重写后才可出片",
    }


def clip_plan(spec: dict) -> dict[str, dict[str, dict[str, list[int]]]]:
    """这一集需要哪些 clip：`画幅 → 图名 → 布局 → [x, y, w, h]`，也就是按 viewBox 缩进图区后
    居中放置的实际像素位置。位置在这里算一次，是为了 capture 与 compose 不会各自算出两个不同的
    居中坐标——差 2 px 就是图歪。

    键里有布局：同一张图在这一集里既可能铺满（figure）也可能只占半栏（split），两种布局的图区
    不一样大。只按图名收的话，第二个布局会静悄悄复用第一个的帧，竖屏里半张图被拉横。
    只看图、布局与画幅，不碰时长——捕获不必等配音，这两件事各跑各的。"""
    rects: dict[str, dict[str, dict[str, list[int]]]] = {}
    for aspect, g in common.ASPECTS.items():
        by_svg: dict[str, dict[str, list[int]]] = {}
        for seg, beat, _ in beats(spec):
            layout = beat_layout(beat, seg)
            svg = beat.get("svg", seg.get("svg")) if layout in {"figure", "split"} else None
            if svg:
                by_svg.setdefault(svg, {})[layout] = [
                    int(v) for v in g.figure_rect(layout, common.svg_ratio(common.ASSETS / svg))]
        rects[aspect] = by_svg
    return rects


def timeline(slug: str, durations: dict[str, float] | None = None) -> dict:
    """旁白实测时长 → 最终时间轴。缺时长就直接报错，不用估计数把后面全蒙一遍。"""
    spec = load_spec(slug)
    if durations is None:
        p = common.EPISODES / spec["slug"] / "durations.json"
        durations = common.load_json(p)
        if durations is None:
            raise FileNotFoundError(f"还没有旁白时长表：先跑 narrate.py --episode {slug}")
    entries = []
    t = 0.0
    for seg, beat, idx in beats(spec):
        bid = beat_id(seg, beat, idx)
        vo_dur = durations.get(bid)
        if vo_dur is None:
            raise KeyError(f"时间轴缺少 {bid} 的实测时长（narrate 是否漏了这一段？）")
        gap = float(beat.get("gap", 0.30))
        hold = float(beat.get("hold", 0.0))
        dur = round(vo_dur + gap + hold, 4)
        layout = beat_layout(beat, seg)
        svg = beat.get("svg", seg.get("svg")) if layout in {"figure", "split"} else None
        entries.append({
            "id": bid,
            "seg": seg["id"],
            "seg_title": seg["title"],
            "title": beat.get("title", seg["title"]),
            "vo": beat["vo"],
            "voice": beat.get("voice", "teacher"),
            "rate": beat.get("rate", spec.get("rate", "+6%")),
            "bgm": beat.get("bgm", seg.get("bgm", spec.get("bgm", "neutral"))),
            "svg": svg,
            "layout": layout,
            "big": beat.get("big"),
            "ticks": int(beat.get("ticks", 0)),
            "question": beat.get("question", ""),
            "options": list(beat.get("options", [])),
            "sfx": beat.get("sfx"),
            "on_screen": on_screen_lines(beat, seg),
            "vo_dur": round(vo_dur, 4),
            "gap": gap,
            "start": round(t, 4),
            "end": round(t + dur, 4),
            "dur": dur,
        })
        t += dur
    out = {
        "slug": spec["slug"],
        "no": spec["no"],
        "title": spec["title"],
        "fps": common.FPS,
        "duration": round(t, 4),
        "beats": entries,
        "checklist": spec.get("checklist", []),
        "cta": spec.get("cta", ""),
    }
    plan = clip_plan(spec)
    out["rects_by_aspect"] = plan
    # 每个画幅实际要落几个 clip 文件：同一张图的两个布局可能缩成同一个尺寸，那种共用一份帧
    out["clip_files"] = {
        a: sorted({(svg, r[2], r[3]) for by_layout in rects.values() for r in by_layout.values()})
        for a, rects in plan.items()}
    return out


def srt(tl: dict) -> str:
    def stamp(sec: float) -> str:
        ms = int(round(sec * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    blocks, n = [], 0
    for e in tl["beats"]:
        for a, b, text in caption_windows(e["vo_dur"], split_captions(e["vo"])):
            n += 1
            blocks.append(f"{n}\n{stamp(e['start'] + a)} --> {stamp(e['start'] + b)}\n{text}\n")
    return "\n".join(blocks)


def main() -> int:
    common.ensure_dirs()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", metavar="EPISODE")
    ap.add_argument("--timeline", metavar="EPISODE")
    ap.add_argument("--draft", type=Path)
    ap.add_argument("--no", type=int, default=1)
    ap.add_argument("--write", action="store_true", help="时间轴写入分镜目录旁边（默认只打摘要）")
    a = ap.parse_args()

    if a.draft:
        print(json.dumps(draft(a.draft, a.no), ensure_ascii=False, indent=2))
        return 0
    if a.check:
        problems = check(a.check)
        spec = load_spec(a.check)
        nb = sum(len(s["beats"]) for s in spec["segments"])
        print(f"分镜 {common.rel(find_spec(a.check))}：{len(spec['segments'])} 段 / {nb} 个 beat / "
              f"{len(spec.get('checklist', []))} 条验收")
        for p in problems:
            print(f"  PROBLEM {p}")
        print("ok" if not problems else f"FAIL：{len(problems)} 条")
        return 0 if not problems else 1
    if a.timeline:
        spec = load_spec(a.timeline)
        tl = timeline(a.timeline)
        svgs = len(tl["rects_by_aspect"]["16x9"])
        print(f"时间轴 {spec['slug']}：{len(tl['beats'])} beat / 总长 {tl['duration']:.1f} s "
              f"（{tl['duration'] / 60:.1f} min）/ 用到 {svgs} 张动画")
        frames = sum(int(round(e["dur"] * common.FPS)) for e in tl["beats"] if e["svg"])
        for aspect, files in tl["clip_files"].items():
            print(f"  {aspect}: {len(files)} 个 clip，图帧共约 {frames} 帧要合成")
        if a.write:
            p = common.EPISODES / spec["slug"] / "timeline.json"
            common.save_json(p, tl)
            sp = common.EPISODES / spec["slug"] / "episode.srt"
            sp.write_text(srt(tl), encoding="utf-8")
            print(f"  写入 {common.rel(p)} 与 {common.rel(sp)}")
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
