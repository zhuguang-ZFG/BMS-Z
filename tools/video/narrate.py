"""旁白：分镜里每条 vo → 语音文件 + **实测时长**。

时间轴由这里量出来的秒数驱动，不是由"这段大概 8 秒"的估计驱动。估的话要么画面先完
而人在说话，要么人说完画面还僵着，两种都很廉价；实测回灌之后 beat 长度 = 语音时长 +
gap，接缝是掐着算出来的。

量的之前先削静音：edge-tts 解出来的 PCM 头尾各带一段容器填充（ep02 实测头 0.17–0.20 s、
尾 0.52–0.85 s，74 条共 54.8 s）。不削的话量到的是容器长度不是说话长度，画面在 beat 起点
就切、话晚 0.18 s 出口，分镜里 0.30 s 的 gap 听感变成 1.03 s 的空白。削完再测，
`trim_silence` 幂等，重跑只测不重复削。

缓存键 = sha(vo, voice, rate)：改一个字就重合成，没改的重跑直接命中，于是"网络服务
挂了"和"我在改稿"两件事互不干扰。在线语音（edge-tts）是网络服务，所以留了 SAPI 离线
兜底——音质降级，但系列不能因为一个在线服务断更。

用法：
    python3 tools/video/narrate.py --episode ep02-recognize-bms
    python3 tools/video/narrate.py --episode ep02-recognize-bms --engine sapi
    python3 tools/video/narrate.py --episode ep02-recognize-bms --report
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import spec as spec_mod  # noqa: E402

TARGET_SR = common.SAMPLE_RATE


def beat_wav(key: str) -> Path:
    return common.TTS / f"{key}.wav"


def to_wav(src: Path, dst: Path) -> None:
    """统一成 48 kHz 单声道 PCM——混音只认这一种，避免 mp3 的编码器延迟把时间轴顶偏。"""
    common.ff("-loglevel", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", str(TARGET_SR),
              "-c:a", "pcm_s16le", str(dst))


def synth_edge(text: str, voice: str, rate: str, dst: Path) -> None:
    """edge-tts 只会给 mp3，落地的却是 `dst` 这个名字。直接把 mp3 的字节写成 `.wav`，
    下一步 `wave.open` 会当成非法头——所以先写成明明白白的 .mp3，再由 ffmpeg 转成 PCM。"""
    import edge_tts

    mp3 = dst.with_name(dst.stem + ".edge.mp3")

    async def go():
        await edge_tts.Communicate(text, voice=voice, rate=rate).save(str(mp3))

    try:
        asyncio.run(go())
        if mp3.stat().st_size < 512:
            raise RuntimeError(f"edge-tts 返回的音频过小（{mp3.stat().st_size} B），判为失败")
        to_wav(mp3, dst)
    finally:
        mp3.unlink(missing_ok=True)


def synth_sapi(text: str, dst: Path) -> None:
    """离线兜底：Windows System.Speech。音色与语速都不如神经语音，只是保证断网也能出片。

    文本走 UTF-8 文件而不是 stdin：PowerShell 的 stdin 按控制台代码页解码，中文在这台
    机器上会变成乱码，念出来的是一堆问号。
    """
    txt = dst.with_suffix(".in.txt")
    script = dst.with_suffix(".sapi.ps1")
    raw = dst.with_suffix(".raw.wav")
    txt.write_text(text, encoding="utf-8")
    code = """
param([string]$InputPath, [string]$OutputPath)
Add-Type -AssemblyName System.Speech
$in = [IO.File]::ReadAllText($InputPath, [Text.Encoding]::UTF8)
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.Rate = 1
$s.SetOutputToWaveFile($OutputPath)
$s.Speak($in)
$s.Dispose()
"""
    script.write_text(code, encoding="utf-8-sig")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                            "-File", str(script), str(txt), str(raw)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            raise RuntimeError(f"SAPI 合成失败：{r.stderr[-400:]}")
        if not raw.exists() or raw.stat().st_size < 512:
            raise RuntimeError(
                f"SAPI 返回成功但没有生成有效 WAV：{raw}；stdout={r.stdout[-200:]!r}，"
                f"stderr={r.stderr[-200:]!r}"
            )
        to_wav(raw, dst)
    finally:
        txt.unlink(missing_ok=True)
        script.unlink(missing_ok=True)
        raw.unlink(missing_ok=True)


def synth_one(text: str, voice_key: str, rate: str, dst: Path, engine: str, tries: int = 3) -> None:
    name = common.VOICE_NAMES[voice_key]
    last: Exception | None = None
    for attempt in range(1, tries + 1):
        try:
            if engine == "edge":
                synth_edge(text, name, rate, dst)
            else:
                synth_sapi(text, dst)
            return
        except Exception as e:  # noqa: BLE001 - 网络服务的失败形态太多，逐条列不出来
            last = e
            if attempt < tries:
                time.sleep(1.5 * attempt)
    raise RuntimeError(f"语音合成失败（{engine}，{voice_key}，试了 {tries} 次）：{type(last).__name__}: {last}")


def run(slug: str, engine: str) -> dict:
    spec = spec_mod.load_spec(slug)
    tl_dir = common.EPISODES / spec["slug"]
    tl_dir.mkdir(parents=True, exist_ok=True)
    durations: dict[str, float] = {}
    rows = []
    todo = []
    trimmed = 0.0
    for seg, beat, idx in spec_mod.beats(spec):
        bid = spec_mod.beat_id(seg, beat, idx)
        v = beat.get("voice", "teacher")
        r = beat.get("rate", spec.get("rate", "+6%"))
        key = common.sha(beat["vo"], v, r, engine)
        dst = beat_wav(key)
        if dst.exists() and dst.stat().st_size > 1024:
            trimmed += common.trim_silence(dst)
            durations[bid] = common.wav_duration(dst)
            rows.append((bid, v, len(beat["vo"]), round(durations[bid], 2), "cache"))
        else:
            todo.append((bid, beat["vo"], v, r, key, dst))

    dur_p = tl_dir / "durations.json"

    def save_durations() -> None:
        # 先写 .part 再 replace：逐条落盘是给断网续跑用的，但写到一半被杀不能留下一份截断的 JSON
        t = dur_p.with_name(dur_p.stem + ".part")
        t.write_text(json.dumps(durations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        t.replace(dur_p)

    if todo:
        print(f"需要合成 {len(todo)} 条（命中缓存 {len(durations)} 条），引擎 {engine}")
    done = 0
    for bid, vo, v, r, _key, dst in todo:
        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_name(dst.stem + ".part.wav")
        synth_one(vo, v, r, tmp, engine)
        tmp.replace(dst)
        trimmed += common.trim_silence(dst)
        durations[bid] = common.wav_duration(dst)
        rows.append((bid, v, len(vo), round(durations[bid], 2), "new"))
        done += 1
        cps = len(vo) / max(durations[bid], 0.001)
        print(f"  [{done}/{len(todo)}] {bid} {v:9s} {len(vo):3d} 字 / {durations[bid]:5.2f} s = {cps:4.1f} 字/秒")
        save_durations()

    # 全命中那一轮也得写：削静音改的就是时长，只测不写的话 durations.json 停在旧值、
    # narrate.json 已是新值，两份账对不上，下游按哪份算都错
    save_durations()

    total = sum(durations.values())
    meta = {"slug": spec["slug"], "engine": engine, "beats": len(rows),
            "vo_seconds": round(total, 2), "cache_hits": sum(1 for r in rows if r[4] == "cache"),
            "trimmed_seconds": round(trimmed, 2),
            "rows": [{"id": r[0], "voice": r[1], "chars": r[2], "seconds": r[3], "src": r[4]} for r in rows]}
    common.save_json(tl_dir / "narrate.json", meta)
    print(f"合计 {len(rows)} 条 / 纯语音 {total:.1f} s（{total / 60:.1f} min），"
          f"削掉容器静音 {trimmed:.1f} s，表写入 {common.rel(tl_dir / 'durations.json')}")
    return meta


def report(slug: str) -> int:
    spec = spec_mod.load_spec(slug)
    p = common.EPISODES / spec["slug"] / "narrate.json"
    if not p.exists():
        print("还没有 narrate.json，先跑 --episode")
        return 1
    m = json.loads(p.read_text(encoding="utf-8"))
    print(f"{m['slug']}：{m['beats']} 条 / 引擎 {m['engine']} / 命中缓存 {m['cache_hits']} / 纯语音 {m['vo_seconds']} s")
    slow = [r for r in m["rows"] if r["seconds"] > 0 and r["chars"] / r["seconds"] < 3.4]
    long = [r for r in m["rows"] if r["seconds"] > 16]
    for r in m["rows"]:
        flag = "  ⚠" if r in slow or r in long else ""
        print(f"  {r['id']:12s} {r['voice']:9s} {r['chars']:3d} 字 {r['seconds']:6.2f} s "
              f"{r['chars'] / max(r['seconds'], 0.001):4.1f} 字/秒 {r['src']}{flag}")
    if slow:
        print(f"  提示：{len(slow)} 条慢于 3.4 字/秒——旁白听起来会拖")
    if long:
        print(f"  提示：{len(long)} 条超过 16 s——一条字幕放不下，拆 beat")
    return 0


def main() -> int:
    common.ensure_dirs()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--episode")
    ap.add_argument("--engine", choices=["edge", "sapi"], default="edge")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.report and a.episode:
        return report(a.episode)
    if a.episode:
        run(a.episode, a.engine)
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
