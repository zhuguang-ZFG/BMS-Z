"""抖音切片：从 9x16 成片里按 beat 边界取 60–90 秒，接 4 秒片尾卡。

取段规则（不在命令行里手填秒数）：跳过开场题，再跳过“答案片尾给”的铺垫
beat，从第一个有内容的 beat 起算；终点优先取 90 秒内最靠后的**段边界**，
没有段边界就取最靠后的 beat 边界。切片只在 beat 边界切——旁白一句一句走，
切在句子中间会听出半句。

帧号是硬账：起帧 ceil(start×30)（帧含 beat 起点才算），止帧 round(end×30)
（排除边界帧，避免把下一段的淡入首帧带进来）。止帧−起帧才是成片帧数，
音频按这个帧数截，片尾卡固定 4 秒 120 帧，混音不用 -shortest。

片尾卡的水印必须走 RGBA 层合成：RGB 图上 ImageDraw 会忽略 alpha，
半透明大字会画成纯白实心并压住 CTA（publish.py 的封面也踩过同一个坑）。
"""
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import common
import spec as spec_mod

FPS = common.FPS
CARD_SECONDS = 4
CARD_FRAMES = int(CARD_SECONDS * FPS)
CLIP_MIN = 60.0
CLIP_MAX = 90.0
W, H = common.ASPECTS["9x16"].w, common.ASPECTS["9x16"].h
CYAN = common.ACCENTS["cyan"]
AMBER = common.ACCENTS["amber"]
HASHTAGS = "#BMS #锂电池 #新能源 #知识分享"

# 片尾卡版式（竖屏 1080×1920）：文字块全在上半区，水印只占下半区留白。
CARD_MARGIN = 40
CAPSULE_Y = 306
HEAD_Y = 742
RULE_Y = 854
SUB_Y = 972
CTA_Y = 1100
META_Y = 1192
WM_Y = 1585
WM_SIZE = 640
WM_ALPHA = 22


def _fmt(sec: float) -> str:
    m, s = divmod(max(0.0, sec), 60)
    return f"{int(m):02d}:{s:05.2f}"


def series_total() -> int:
    # 切片指向完整合集（正片 + 续集）；publish.SERIES_COUNT 是正片口径，留给旧发布包。
    return len(list(spec_mod.SPEC_DIR.glob("*.json")))


def _fit_font(text: str, kind: str, hi: int, lo: int, max_w: float):
    size = hi
    while size > lo:
        f = common.font(kind, size)
        if f.getlength(text) <= max_w:
            return f
        size -= 2
    return common.font(kind, lo)


def _text_box(draw, text: str, font, cx: float, cy: float):
    x0, y0, x1, y1 = font.getbbox(text, anchor="mm")
    return (cx + x0, cy + y0, cx + x1, cy + y1)


def card_texts(tl: dict, sp: dict) -> dict:
    no = int(tl["no"])
    series = str(sp.get("series_count") or series_total())
    minutes = max(1, int(round(tl["duration"] / 60)))
    stage = tl["title"].split("：")[0].strip()
    cover = [s for s in (sp.get("cover_title") or []) if s]
    subtitle = "，".join(cover) if len(cover) >= 2 else (cover[0] if cover else stage)
    return {
        "capsule": f"BMS 从入门到精通 · 第 {no} 集",
        "headline": f"完整版 {minutes} 分钟",
        "subtitle": subtitle,
        "cta": f"主页合集 · 全 {series} 集",
        "meta": stage,
        "watermark": f"{no:02d}",
        "minutes": minutes,
        "series": series,
        "no": no,
    }


def build_card(tl: dict, sp: dict) -> tuple[Image.Image, dict]:
    t = card_texts(tl, sp)
    img = common.video_bg(common.ASPECTS["9x16"]).copy()

    wm_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dw = ImageDraw.Draw(wm_layer)
    f_wm = common.font("bold", WM_SIZE)
    dw.text((W // 2, WM_Y), t["watermark"], font=f_wm,
            fill=(210, 225, 240, WM_ALPHA), anchor="mm")
    img = Image.alpha_composite(img.convert("RGBA"), wm_layer).convert("RGB")

    d = ImageDraw.Draw(img)
    f_cap = common.font("text", 46)
    f_head = _fit_font(t["headline"], "bold", 112, 72, 960)
    f_sub = _fit_font(t["subtitle"], "bold", 80, 52, 940)
    f_cta = _fit_font(t["cta"], "bold", 58, 44, 900)
    f_meta = _fit_font(t["meta"], "text", 40, 32, 900)

    def sh(xy, text, font, fill, off=3):
        x, y = xy
        d.text((x, y + off), text, font=font, fill=(4, 7, 12), anchor="mm")
        d.text((x, y), text, font=font, fill=fill, anchor="mm")

    cap_w = d.textlength(t["capsule"], font=f_cap)
    x0 = (W - cap_w) / 2 - 40
    x1 = (W + cap_w) / 2 + 40
    y0, y1 = CAPSULE_Y, CAPSULE_Y + 46 + 44
    d.rounded_rectangle([x0, y0, x1, y1], radius=32, outline=CYAN, width=2)
    sh((W // 2, (y0 + y1) / 2 - 2), t["capsule"], f_cap, CYAN)

    sh((W // 2, HEAD_Y), t["headline"], f_head, AMBER, off=4)
    d.rectangle([W / 2 - 140, RULE_Y, W / 2 + 140, RULE_Y + 4], fill=CYAN)
    sh((W // 2, SUB_Y), t["subtitle"], f_sub, common.TXT, off=4)
    sh((W // 2, CTA_Y), t["cta"], f_cta, CYAN)
    sh((W // 2, META_Y), t["meta"], f_meta, common.SMALL)

    geo = {
        "capsule": (f_cap, _text_box(d, t["capsule"], f_cap, W // 2, (y0 + y1) / 2 - 2)),
        "capsule_rect": (x0, y0, x1, y1),
        "headline": (f_head, _text_box(d, t["headline"], f_head, W // 2, HEAD_Y)),
        "subtitle": (f_sub, _text_box(d, t["subtitle"], f_sub, W // 2, SUB_Y)),
        "cta": (f_cta, _text_box(d, t["cta"], f_cta, W // 2, CTA_Y)),
        "meta": (f_meta, _text_box(d, t["meta"], f_meta, W // 2, META_Y)),
        "watermark": (f_wm, _text_box(d, t["watermark"], f_wm, W // 2, WM_Y)),
    }
    return img, geo


def pick_beats(tl: dict) -> tuple[int, int]:
    """返回 [i0, i1) beat 下标。i0 跳过开场题与“答案片尾给”的铺垫。"""
    beats = tl["beats"]
    i0 = 1
    if i0 < len(beats) and str(beats[i0].get("vo") or "").startswith("答案"):
        i0 += 1
    while i0 < len(beats) and beats[i0]["layout"] == "quiz":
        i0 += 1
    if i0 >= len(beats):
        raise RuntimeError("没有可切的 beat")
    start = beats[i0]["start"]

    best_seg = None
    best_beat = None
    for j in range(i0, len(beats)):
        dur = beats[j]["end"] - start
        if dur > CLIP_MAX:
            break
        if dur < CLIP_MIN:
            continue
        seg_edge = j + 1 >= len(beats) or beats[j + 1]["seg_title"] != beats[j]["seg_title"]
        if seg_edge:
            best_seg = j
        best_beat = j
    end = best_seg if best_seg is not None else best_beat
    if end is None:
        raise RuntimeError("60–90 秒内找不到 beat 边界")
    return i0, end + 1


def frame_span(start: float, end: float) -> tuple[int, int, int]:
    first = int(math.ceil(start * FPS - 1e-9))
    last = int(round(end * FPS))
    if last <= first:
        raise RuntimeError(f"取段太短：{_fmt(start)}–{_fmt(end)}")
    return first, last, last - first


def hook_line(tl: dict, i0: int, sp: dict) -> str:
    for b in tl["beats"][i0:i0 + 4]:
        for item in b.get("on_screen") or []:
            s = str(item.get("t") or "").strip()
            if not s or s == "BMS 从入门到精通" or s.startswith("答案"):
                continue
            if re.match(r"^(续集)?第\s*\d+\s*集", s):
                continue
            return s
    cover = sp.get("cover_title") or []
    return cover[0] if cover else tl["title"]


def caption_texts(tl: dict, sp: dict, i0: int, i1: int, first: int, last: int) -> dict:
    no = int(tl["no"])
    series = str(sp.get("series_count") or series_total())
    minutes = max(1, int(round(tl["duration"] / 60)))
    hook = hook_line(tl, i0, sp)
    suffix = f"｜BMS 第 {no} 集"
    title = f"{hook}{suffix}"
    if len(title) > 30:
        title = hook[:30] if len(hook) >= 24 else f"{hook[:30 - len(suffix)]}…{suffix}"
        if len(title) > 30:
            title = title[:30]
    segs: list[str] = []
    for b in tl["beats"][i0:i1]:
        s = b["seg_title"]
        if s == "开场那道题":
            continue
        s = s.removeprefix("开场：")
        if s not in segs:
            segs.append(s)
    covered = " → ".join(segs) if segs else tl["beats"][i0]["seg_title"]
    body = (f"{hook}\n\n这一段讲：{covered}\n\n"
            f"完整版 {minutes} 分钟，主页合集《BMS 从入门到精通》全 {series} 集。\n\n{HASHTAGS}")
    return {
        "title": title, "body": body, "hook": hook, "minutes": minutes,
        "series": series, "no": no, "covered": covered,
        "frames": last - first, "clip_seconds": (last - first) / FPS,
    }


def write_caption(path: Path, tl: dict, i0: int, i1: int, c: dict, total_sec: float) -> None:
    slug = tl["slug"]
    cover = common.OUT / "publish" / "cover" / f"{slug}-9x16.jpg"
    text = f"""# {slug} 抖音切片（{c['clip_seconds']:.1f} s 正片 + {CARD_SECONDS} s 片尾卡）

## 标题（{len(c['title'])}/30 字）
{c['title']}

## 话题
{HASHTAGS}

## 正文（{len(c['body'])}/1000 字）
```text
{c['body']}
```

## 素材
切片：media/video/out/publish/douyin/{slug}-clip-01.mp4（1080x1920，{total_sec:.1f} s）
封面：{common.rel(cover).replace(chr(92), "/")}
源片：media/video/out/{slug}-9x16.mp4，取 {_fmt(tl['beats'][i0]['start'])}–{_fmt(tl['beats'][i1 - 1]['end'])}（{tl['beats'][i0]['id']} 起，{tl['beats'][i1 - 1]['id']} 止）
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def count_frames(path: Path) -> int:
    out = common.run([common.ffmpeg_exe(), "-hide_banner", "-i", str(path),
                      "-map", "0:v:0", "-f", "null", "-"])
    found = re.findall(r"frame=\s*(\d+)", out)
    if not found:
        raise RuntimeError(f"数不出帧：{common.rel(path)}")
    return int(found[-1])


def probe_duration(path: Path) -> float:
    # 只喂输入不给输出，ffmpeg 必以 1 退出——这里要的是它打在 stderr 的 Duration 行。
    out = common.run([common.ffmpeg_exe(), "-hide_banner", "-i", str(path)], check=False)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out)
    if not m:
        raise RuntimeError(f"读不出时长：{common.rel(path)}")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def loudness(path: Path, seconds: float | None = None) -> tuple[float, float]:
    cmd = [common.ffmpeg_exe(), "-hide_banner"]
    if seconds is not None:
        cmd += ["-t", f"{seconds:.3f}"]
    cmd += ["-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"]
    out = common.run(cmd)
    m_i = re.findall(r"I:\s*(-?\d+(?:\.\d+)?) LUFS", out)
    m_p = re.findall(r"Peak:\s*(-?\d+(?:\.\d+)?) dBFS", out)
    if not m_i or not m_p:
        raise RuntimeError(f"量不出响度：{common.rel(path)}")
    return float(m_i[-1]), float(m_p[-1])


def encode(tl: dict, i0: int, i1: int, card: Path, out: Path) -> dict:
    b0, b1 = tl["beats"][i0], tl["beats"][i1 - 1]
    start, end = b0["start"], b1["end"]
    first, last, frames = frame_span(start, end)
    src_first = int(math.floor(start * FPS + 1e-6))
    drop = first - src_first
    clip_dur = frames / FPS
    master = common.OUT / f"{tl['slug']}-9x16.mp4"
    if not master.exists():
        raise FileNotFoundError(f"缺成片：{common.rel(master)}")
    common.have_tmp_disk(out, 200)

    cmd = [
        common.ffmpeg_exe(), "-hide_banner", "-y", "-loglevel", "error",
        "-ss", f"{start:.6f}", "-t", f"{clip_dur + 0.2:.6f}", "-i", str(master),
        "-loop", "1", "-framerate", str(FPS), "-t", str(CARD_SECONDS + 1), "-i", str(card),
        "-filter_complex",
        f"[0:v]select='between(n,{drop},{drop + frames - 1})',setpts=N/{FPS}/TB,setsar=1[v0];"
        f"[1:v]scale={W}:{H}:flags=lanczos,setsar=1,trim=end_frame={CARD_FRAMES},setpts=PTS-STARTPTS[v1];"
        f"[v0][v1]concat=n=2:v=1:a=0[v];"
        f"[0:a]atrim=0:{clip_dur:.6f},asetpts=PTS-STARTPTS,"
        f"afade=t=out:st={max(0.0, clip_dur - 0.3):.3f}:d=0.3,apad=pad_dur={CARD_SECONDS}[a]",
        "-map", "[v]", "-map", "[a]", "-r", str(FPS),
        "-c:v", "libx264", "-preset", "slow", "-crf", "20",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-video_track_timescale", "15360",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
        str(out),
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    common.run(cmd)

    expect = frames + CARD_FRAMES
    got = count_frames(out)
    dur = probe_duration(out)
    if got != expect:
        raise RuntimeError(f"{common.rel(out)} 帧数 {got} ≠ 预期 {expect}")
    if abs(dur - expect / FPS) > 0.06:
        raise RuntimeError(f"{common.rel(out)} 时长 {dur:.3f}s ≠ {expect / FPS:.3f}s")
    lufs, peak = loudness(out)
    if not (-19.0 <= lufs <= -15.0):
        raise RuntimeError(f"{common.rel(out)} 响度 {lufs} LUFS 越界（−19…−15）")
    if peak > -1.0:
        raise RuntimeError(f"{common.rel(out)} 真峰值 {peak} dBTP > −1")
    return {"first": first, "last": last, "frames": frames, "card": CARD_FRAMES,
            "out_frames": got, "duration": dur, "lufs": lufs, "peak": peak,
            "start": start, "end": end, "clip_dur": clip_dur}


def run_episode(slug: str, from_beat: str | None, to_beat: str | None, list_only: bool) -> int:
    tl = spec_mod.timeline(slug)
    sp = spec_mod.load_spec(slug)
    beats = tl["beats"]
    if from_beat or to_beat:
        ids = [b["id"] for b in beats]
        if from_beat not in ids or to_beat not in ids:
            raise SystemExit(f"--from/--to 必须是 beat id：{ids[0]} … {ids[-1]}")
        i0, i1 = ids.index(from_beat), ids.index(to_beat) + 1
        if i1 <= i0:
            raise SystemExit("--to 必须在 --from 之后")
    else:
        i0, i1 = pick_beats(tl)
    first, last, frames = frame_span(beats[i0]["start"], beats[i1 - 1]["end"])
    clip_sec = frames / FPS
    print(f"  {slug}: beat {beats[i0]['id']} … {beats[i1 - 1]['id']}  "
          f"{_fmt(beats[i0]['start'])}–{_fmt(beats[i1 - 1]['end'])}  "
          f"{frames} 帧 / {clip_sec:.2f} s")
    if list_only:
        return 0

    img, _ = build_card(tl, sp)
    card = common.WORK / "clips" / f"endcard-{slug}-9x16.png"
    card.parent.mkdir(parents=True, exist_ok=True)
    img.save(card)
    out = common.OUT / "publish" / "douyin" / f"{slug}-clip-01.mp4"
    r = encode(tl, i0, i1, card, out)
    c = caption_texts(tl, sp, i0, i1, first, last)
    write_caption(out.with_suffix(".txt"), tl, i0, i1, c,
                  (r["frames"] + CARD_FRAMES) / FPS)
    print(f"  成片 {common.rel(out)}  {r['out_frames']} 帧 / {r['duration']:.2f} s  "
          f"{r['lufs']} LUFS / {r['peak']} dBTP")
    print(f"  文案 {common.rel(out.with_suffix('.txt'))}  标题「{c['title']}」")
    return 0


def selftest() -> int:
    fails: list[str] = []
    eps = sorted(p.name for p in common.EPISODES.iterdir() if p.is_dir())
    for slug in eps:
        tl = spec_mod.timeline(slug)
        sp = spec_mod.load_spec(slug)
        i0, i1 = pick_beats(tl)
        first, last, frames = frame_span(tl["beats"][i0]["start"], tl["beats"][i1 - 1]["end"])
        clip_sec = frames / FPS
        if not (CLIP_MIN <= clip_sec <= CLIP_MAX):
            fails.append(f"{slug}: 切片 {clip_sec:.2f}s 不在 60–90s")
        if tl["beats"][i0]["layout"] == "quiz":
            fails.append(f"{slug}: 切片从 quiz beat 开始")
        img, geo = build_card(tl, sp)
        wm_top = geo["watermark"][1][1]
        for key in ("headline", "subtitle", "cta", "meta"):
            box = geo[key][1]
            if box[0] < CARD_MARGIN or box[2] > W - CARD_MARGIN:
                fails.append(f"{slug}: 片尾卡 {key} 出横向安全区 {box}")
            if box[3] > wm_top - 4:
                fails.append(f"{slug}: 片尾卡 {key} 压到水印（底 {box[3]:.0f} vs 水印顶 {wm_top:.0f}）")
        if geo["capsule_rect"][0] < CARD_MARGIN or geo["capsule_rect"][2] > W - CARD_MARGIN:
            fails.append(f"{slug}: 系列胶囊出横向安全区")
        # 逐像素最暗会被文字投影压到 4（投影 (4,7,12)），黑帧门量的是整帧亮度；
        # 这里同样只看均值，别把一片正常深底误判成黑帧。
        luma_mean = float(np.asarray(img).mean())
        if luma_mean < 10:
            fails.append(f"{slug}: 片尾卡均值亮度 {luma_mean:.1f} < 10")
        c = caption_texts(tl, sp, i0, i1, first, last)
        if len(c["title"]) > 30:
            fails.append(f"{slug}: 标题 {len(c['title'])} 字 > 30")
        if len(c["body"]) > 1000:
            fails.append(f"{slug}: 正文 {len(c['body'])} 字 > 1000")
        if "http" in c["body"].lower() or "github" in c["body"].lower():
            fails.append(f"{slug}: 正文含外链")
        if c["body"].count("#") != 4:
            fails.append(f"{slug}: 话题不是 4 个")
        print(f"  {slug}: {clip_sec:.1f}s  title={len(c['title'])}「{c['title']}」  "
              f"body={len(c['body'])}  card_luma={luma_mean:.1f}  "
              f"{'OK' if not any(slug in f for f in fails) else 'FAIL'}")
    if fails:
        print("\n".join(f"  FAIL: {f}" for f in fails))
        return 1
    print(f"PASS  {len(eps)} 集切片：取段、帧账、片尾卡与文案都在预算内")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="抖音 9x16 切片（60–90 秒 + 4 秒片尾卡）")
    ap.add_argument("--episode", help="集数 slug，如 ep02-recognize-bms")
    ap.add_argument("--all", action="store_true", help="处理全部集数")
    ap.add_argument("--list", action="store_true", help="只打印取段，不渲染")
    ap.add_argument("--from", dest="from_beat", help="起始 beat id（含）")
    ap.add_argument("--to", dest="to_beat", help="结束 beat id（含）")
    ap.add_argument("--selftest", action="store_true", help="校验取段、片尾卡与文案")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if args.all:
        eps = sorted(p.name for p in common.EPISODES.iterdir() if p.is_dir())
    elif args.episode:
        eps = [args.episode]
    else:
        ap.error("需要 --episode 或 --all（或 --selftest）")
    rc = 0
    for slug in eps:
        try:
            rc |= run_episode(slug, args.from_beat, args.to_beat, args.list)
        except Exception as e:  # 一集失败不吞后续集，但退出码必须非零
            print(f"  FAIL {slug}: {e}")
            rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
