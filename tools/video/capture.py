"""把 SMIL 动画逐帧截成短片：Chromium 是唯一能忠实渲染这批图的东西。

为什么不用 rsvg/cairosvg：仓库里 150 张图全靠 SMIL（`<animate>` / `repeatCount`），
静态渲染器只会给出第 0 帧；Chromium 的 `svg.setCurrentTime(t)` 能把时间轴钉在任意时刻，
于是"这一帧对应第几秒"是可控的、可复现的，而不是等浏览器自己走完再祈祷。

产物是 clips/<svg>@<w>x<h>_<fps>.mp4 + 同名 json（周期、是否循环、帧数）。缓存键带上
尺寸与帧率：同一张图在横屏和竖屏里占的像素不一样，不能共用一份帧。

用法：
    python3 tools/video/capture.py --episode ep02-recognize-bms
    python3 tools/video/capture.py --list ep02-recognize-bms --aspect 9x16
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import spec as spec_mod  # noqa: E402

CHROMIUM = Path(r"C:\Users\zhugu\AppData\Local\ms-playwright")
DUR_RE = re.compile(r"^(\d+(?:\.\d+)?)(ms|s)$")
MAX_PERIOD = 12.0
MIN_PERIOD = 2.0


def chromium_exe() -> Path:
    hits = sorted(CHROMIUM.glob("chromium-*/chrome-win64/chrome.exe"))
    for h in reversed(hits):
        if h.exists():
            return h
    raise FileNotFoundError(f"找不到 Playwright 的 Chromium（{CHROMIUM} 下没有 chromium-*/chrome-win64/chrome.exe）")


def parse_dur(v: str | None) -> float:
    if not v or v in {"indefinite", "media", "compound"}:
        return 0.0
    m = DUR_RE.match(v.strip())
    if not m:
        return 0.0
    n, unit = float(m.group(1)), m.group(2)
    return n / 1000.0 if unit == "ms" else n


def svg_timing(svg_path: Path) -> dict:
    """周期 = 所有 animate* 里最长的 dur；repeatCount=indefinite 决定 beat 超时长时是循环还是定格。"""
    root = ET.fromstring(svg_path.read_text(encoding="utf-8"))
    period = 0.0
    repeating = False
    count = 0
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag.startswith("animate") or tag in {"set", "discard"}:
            count += 1
            period = max(period, parse_dur(el.get("dur")) + parse_dur(el.get("max")))
            if el.get("repeatCount") == "indefinite":
                repeating = True
    return {
        "ratio": common.svg_ratio(svg_path),
        "period": min(max(period, MIN_PERIOD), MAX_PERIOD) if count else 0.0,
        "repeating": repeating,
        "anim_nodes": count,
    }


def ensure_clip(svg: str, w: int, h: int, fps: int, page) -> dict:
    mp4, meta_p = common.clip_paths(svg, w, h, fps)
    if mp4.exists() and meta_p.exists() and mp4.stat().st_size > 2048:
        m = common.load_json(meta_p)
        if isinstance(m, dict):
            m["cached"] = True
            return m
    src = common.ASSETS / svg
    timing = svg_timing(src)
    frames = max(1, int(round(timing["period"] * fps)))
    tmp = common.WORK / "tmp" / common.sha(svg, w, h, fps, common.VIDEO_THEME)
    for stale in (mp4, meta_p):
        stale.unlink(missing_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)

    body = (f"<body style='margin:0;background:{common.VIDEO_BG}'>" + src.read_text(encoding="utf-8") + "</body>")
    page.set_content(body)
    page.wait_for_timeout(60)
    got = page.evaluate(
        """([w,h]) => {const s=document.querySelector('svg');
            if (!s) return null;
            s.setAttribute('width', w); s.setAttribute('height', h);
            s.style.width = w+'px'; s.style.height = h+'px'; s.style.display='block';
            const b=s.getAttribute('preserveAspectRatio');
            if (!b) s.setAttribute('preserveAspectRatio','xMidYMid meet');
            return {vb: s.viewBox.baseVal, canSet: typeof s.setCurrentTime === 'function'};}""",
        [w, h])
    if not got or not got["canSet"]:
        raise RuntimeError(f"{svg} 里没找到可控制时间的 <svg> 根元素")

    t0 = time.time()
    shot = str(tmp / "f%06d.png")
    try:
        for i in range(frames):
            page.evaluate("(t)=>document.querySelector('svg').setCurrentTime(t)", i / fps)
            page.screenshot(path=shot % (i + 1), clip={"x": 0, "y": 0, "width": w, "height": h})
        secs = time.time() - t0

        common.ff("-loglevel", "error", "-framerate", str(fps), "-start_number", "1",
                  "-i", str(tmp / "f%06d.png"), "-frames:v", str(frames),
                  "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p",
                  "-an", "-movflags", "+faststart", str(mp4))
    finally:
        for f in tmp.glob("*.png"):
            f.unlink()
        try:
            tmp.rmdir()
        except OSError:
            pass

    meta = {"svg": svg, "w": w, "h": h, "fps": fps, "theme": common.VIDEO_THEME,
            "frames": frames, "period": timing["period"], "repeating": timing["repeating"],
            "ratio": timing["ratio"], "anim_nodes": timing["anim_nodes"],
            "seconds": round(frames / fps, 4),
            "capture_seconds": round(secs, 2), "bytes": mp4.stat().st_size, "cached": False}
    common.save_json(meta_p, meta)
    print(f"  {svg:38s} {w}x{h} {frames:4d} 帧 / {timing['period']:.1f} s "
          f"循环={'是' if timing['repeating'] else '否'}  耗时 {secs:.1f} s  → {mp4.stat().st_size / 1e6:.2f} MB")
    return meta


def needed(slug: str, aspect: str | None) -> dict[tuple[str, str, str], tuple[int, int]]:
    """这集要哪些 clip、各多大，键是 `(画幅, 布局, 图名)`。同一张图在两个画幅里、或在
    `figure` 与 `split` 两种布局下占的像素不一样，键少一维就会有一轮悄悄复用别人的帧——
    要么 compose 到那一轮炸「clip 还没捕获」，要么半张图被拉横。
    走 clip_plan 而不是 timeline：捕获不该等配音时长。"""
    plan = spec_mod.clip_plan(spec_mod.load_spec(slug))
    out: dict[tuple[str, str, str], tuple[int, int]] = {}
    for a, by_svg in plan.items():
        if aspect and a != aspect:
            continue
        for svg, by_layout in by_svg.items():
            for layout, rect in by_layout.items():
                out[(a, layout, svg)] = (rect[2] * common.CLIP_SS, rect[3] * common.CLIP_SS)
    return out


def main() -> int:
    common.ensure_dirs()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--episode", required=True)
    ap.add_argument("--aspect", choices=list(common.ASPECTS))
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        for (asp, layout, svg), (w, h) in needed(a.episode, a.aspect).items():
            mp4, _ = common.clip_paths(svg, w, h, common.FPS)
            m = common.load_json(mp4.with_suffix(".json")) or {}
            print(f"  {asp} {layout:7s} {svg:34s} {w}x{h}  周期 {m.get('period', '?')} s  "
                  f"{m.get('frames', '-')} 帧  {'已缓存' if mp4.exists() else '待捕获'}")
        return 0

    need = needed(a.episode, a.aspect)
    if not need:
        print("这一集没有需要捕获的动画")
        return 0
    exe = chromium_exe()
    from playwright.sync_api import sync_playwright

    t0 = time.time()
    hits = 0
    sizes = {sz for sz in need.values()}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(exe), args=["--force-color-profile=srgb"])
        w, h = max(need.values(), key=lambda v: v[0] * v[1])
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1,
                                color_scheme=common.VIDEO_THEME)
        # 按尺寸从大到小排：同一尺寸的几个布局连着做完，视口只改一次
        for (_asp, _layout, svg), (cw, ch) in sorted(need.items(), key=lambda kv: -kv[1][0] * kv[1][1]):
            mp4, meta_p = common.clip_paths(svg, cw, ch, common.FPS)
            if mp4.exists() and meta_p.exists():
                hits += 1
                continue
            page.set_viewport_size({"width": cw, "height": ch})
            ensure_clip(svg, cw, ch, common.FPS, page)
        browser.close()
    print(f"捕获完成：{len(need)} 个 clip 位（{len(sizes)} 种尺寸），命中缓存 {hits} 个，"
          f"墙钟 {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
