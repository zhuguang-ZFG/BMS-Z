"""混音与封装：无声底板 + 实测旁白 + 原创 BGM/SFX → 成片 MP4。

流水线到这里才有"声音"。前三家各管一摊：spec 定时间轴，narrate 量出每句的秒数，
compose 按同一份 timeline 数帧。混音不另起一套秒数——所有摆位都从 timeline(slug) 的
start/end 取，这样画面上大字出现的那一帧和 blip 响的那一样本必然同刻；估一次秒数就漂
一次，漂到集尾就是口型对不上字幕。

三件事的形状：
  旁白 —— 每条 beat 的语音放在它的 start（上一句的 gap 已经算在时间轴里），句内不压
    缩不 limiting，只按整集的**活动段 RMS** 定一个总增益。edge-tts 每条的响度本来就
    一致，逐句归一反而会把"这句话说得轻"这个信息抹掉。
  BGM —— 走全局拍网格：循环点钉在 t=0，换曲处取的是同一网格上不同的样本区间。三条曲子
    同 132 BPM、同 Am–F–C–G 走向，只有密度不同，所以换曲落在任意时刻鼓点都不会错位，
    再叠一段等功率交叉淡化就听不出接缝。代价是别去猜"换曲在小节线上"——分镜的换曲点是
    beat 边界，不是小节边界，网格对齐才是唯一保证。
  ducking —— 用 bgm.vo_envelope(整集旁白) 驱动 bgm.duck，env=1（说话中）拿 -26 dB、
    env=0 拿 -14 dB。方向写反就是念书时音乐变大。

用法：
    python3 tools/video/assemble.py --episode ep02-recognize-bms --both
    python3 tools/video/assemble.py --episode ep02-recognize-bms --aspect 16x9
    python3 tools/video/assemble.py --episode ep02-recognize-bms --mix-only
    python3 tools/video/assemble.py --episode ep02-recognize-bms --selftest
    python3 tools/video/assemble.py --episode ep02-recognize-bms --report
"""


from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bgm  # noqa: E402
import common  # noqa: E402
import spec as spec_mod  # noqa: E402

SR = common.SAMPLE_RATE
XFADE = 0.35       # 换曲交叉淡化
FADE_IN = 0.60     # 开场 BGM 进
FADE_OUT = 1.40    # 片尾 BGM 出
VOICE_RMS_DB = -19.0   # 活动语音的目标电平；BGM 满电平 -14 / 说话中 -26 是相对它定的
CEILING = 0.98
MASTER_GAIN_DB = -0.8       # AAC 编码后实测约 -17.3 LUFS / -1.16 dBTP；不改 voice/BGM/SFX 比例
OUTPUT_LUFS_RANGE = (-18.0, -16.0)
OUTPUT_TRUE_PEAK_MAX_DBTP = -1.0

_TRACK_CACHE: dict[str, NDArray[np.float64]] = {}


def master_gain_db(slug: str) -> float:
    """默认守系列母带；个别片若 AAC 真峰值贴线，可在分镜显式再衰减一点。

    只允许 0 到 -6 dB：它是最终文件的窄幅安全修正，不是拿来掩盖混音失控的旋钮。
    """
    value = float(spec_mod.load_spec(slug).get("master_gain_db", MASTER_GAIN_DB))
    if not -6.0 <= value <= 0.0:
        raise ValueError(f"{slug} 的 master_gain_db={value} 不在 -6…0 dB")
    return value


def track_loop(name: str) -> NDArray[np.float64]:
    import numpy as np

    if name not in _TRACK_CACHE:
        _TRACK_CACHE[name] = np.asarray(bgm.loop_of(name), dtype=np.float64)
    return _TRACK_CACHE[name]


def narrate_engine(slug: str) -> str:
    meta = common.load_json(common.EPISODES / slug / "narrate.json")
    if not meta:
        raise FileNotFoundError(f"还没有 narrate.json：先跑 narrate.py --episode {slug}")
    return meta["engine"]


def voice_path(beat: dict, engine: str) -> Path:
    """和 narrate 同一个缓存键：sha(vo, voice, rate, engine)。改一个字 → 键变了 → 这里报缺文件，
    而不是悄悄用上一次的旧配音，这是音画漂移里最难查的一种。"""
    key = common.sha(beat["vo"], beat["voice"], beat["rate"], engine)
    p = common.TTS / f"{key}.wav"
    if not p.exists():
        raise FileNotFoundError(f"缺旁白音频 {common.rel(p)}（beat {beat['id']}）：先跑 narrate.py")
    return p


def build_voice(tl: dict, engine: str):
    import numpy as np

    n = int(round(tl["duration"] * SR))
    bus = np.zeros(n)
    placed = 0
    for e in tl["beats"]:
        x, _ = common.read_wav(voice_path(e, engine))
        x = x[:, 0]
        a = int(round(e["start"] * SR))
        b = min(a + x.shape[0], n)
        if b > a:
            bus[a:b] += x[: b - a]
            placed += 1
    return bus, n, placed


def rms_target_gain(voice):
    """按活动段的 RMS 定增益，别按峰值：峰值由单个齿音决定，按它归一会让整集听起来又小又闷。
    活动段 = 包络 ≥0.25 的那些帧，包络来自 bgm.vo_envelope（它自己按整集最大值归一）。"""
    import numpy as np

    env = bgm.vo_envelope(voice)
    nf = env.shape[0]
    frame = -(-voice.shape[0] // nf)
    f = np.array([float(np.sqrt(np.mean(voice[i * frame:(i + 1) * frame] ** 2))) for i in range(nf)])
    act = env >= 0.25
    if not act.any():
        raise RuntimeError("整集旁白包络都低于 0.25——配音是空的？")
    active_rms = float(f[act].mean())
    peak = float(np.max(np.abs(voice))) or 1e-9
    gain = min(10.0 ** (VOICE_RMS_DB / 20.0) / max(active_rms, 1e-9), CEILING / peak)
    return gain, active_rms, peak


def spans_of(tl: dict) -> list[tuple[float, float, str]]:
    """逐 beat 的 bgm 压成极大连续同曲段。只在换曲处断开，同曲连播不制造接缝。"""
    out: list[list] = []
    for e in tl["beats"]:
        if out and out[-1][2] == e["bgm"] and abs(out[-1][1] - e["start"]) < 1e-9:
            out[-1][1] = e["end"]
        else:
            out.append([e["start"], e["end"], e["bgm"]])
    return [(float(a), float(b), c) for a, b, c in out]


def grid_slice(name: str, pos: int, length: int):
    """全局拍网格上 [pos, pos+length) 这段 BGM。循环点钉在 t=0，所以任意两段的鼓点相位差
    就是它们的样本距离对 LOOP_N 取模——换曲不歪拍。"""
    import numpy as np

    loop = track_loop(name)
    L = loop.shape[0]
    out = np.empty(length)
    i = 0
    while i < length:
        k = (pos + i) % L
        take = min(length - i, L - k)
        out[i:i + take] = loop[k:k + take]
        i += take
    return out


def build_bgm(tl: dict, n: int):
    import numpy as np

    bus = np.zeros(n)
    sp = spans_of(tl)
    xf = int(round(XFADE * SR))
    for j, (t0, t1, track) in enumerate(sp):
        a = max(0, int(round(t0 * SR)))
        b = min(int(round(t1 * SR)), n)
        if j + 1 < len(sp):
            b = min(b + xf, n)          # 多走一段，和下一段重叠出一个淡化窗
        if b <= a:
            continue
        y = grid_slice(track, a, b - a)
        g = np.ones(y.shape[0])
        if j == 0:
            k = min(int(round(FADE_IN * SR)), g.shape[0])
            g[:k] *= np.linspace(0.0, 1.0, k) ** 0.5
        else:
            k = min(xf, g.shape[0])
            g[:k] *= np.sin(np.pi / 2 * np.linspace(0.0, 1.0, k))   # 等功率：与上一段的 cos 配平
        if j + 1 < len(sp):
            k = min(xf, g.shape[0])
            g[-k:] *= np.cos(np.pi / 2 * np.linspace(0.0, 1.0, k))
        bus[a:b] += y * g
    k = min(int(round(FADE_OUT * SR)), n)
    if k > 0:
        bus[n - k:] *= np.linspace(1.0, 0.0, k) ** 0.5
    return bus, len(sp)


def build_sfx(tl: dict, n: int):
    import numpy as np

    bus = np.zeros(n)
    hits = 0
    for e in tl["beats"]:
        name = e.get("sfx")
        if not name:
            continue
        y = np.asarray(getattr(bgm, name)(), dtype=np.float64)
        if y.ndim > 1:
            y = y[:, 0]
        a = int(round(e["start"] * SR))
        if name == "whoosh":
            # 过场风声甩在切卡**之前**：card 出现的那一帧是重音落点，风尾压着切点收尾才像
            # "被这一下带进去"，从切点开始响就变成画面已经走了声音还在追
            a -= y.shape[0]
        a = max(0, a)
        b = min(a + y.shape[0], n)
        if b > a:
            bus[a:b] += y[: b - a]
            hits += 1
    return bus, hits


def _rms_db(x) -> float | None:
    import numpy as np

    if x.size == 0:
        return None
    return round(20.0 * float(np.log10(max(float(np.sqrt(np.mean(np.asarray(x) ** 2))), 1e-9))), 2)


def mix(slug: str, write_mix: bool = True):
    import numpy as np

    tl = spec_mod.timeline(slug)
    engine = narrate_engine(tl["slug"])
    voice, n, placed = build_voice(tl, engine)
    gain, active_rms, vpeak = rms_target_gain(voice)
    voice *= gain
    bgm_bus, nspans = build_bgm(tl, n)
    env = bgm.vo_envelope(voice)
    env_s = bgm.envelope_at(env, n)      # 帧包络拉到样本级：拿它当掩码数 BGM 电平才对得上样本
    bgm_ducked = bgm.duck(bgm_bus, env_s)
    sfx_bus, hits = build_sfx(tl, n)
    mixy = voice + bgm_ducked + sfx_bus
    peak = float(np.max(np.abs(mixy)))
    headroom = 1.0
    if peak > CEILING:
        headroom = CEILING / peak
        mixy *= headroom
    stereo = np.stack([mixy, mixy], axis=1)
    # 音画按同一把尺收尾：compose 的帧数恒等于 round(总时长 × 30)，音频样本数却是
    # round(总时长 × 48000)。两者构造上就差零点几帧（ep02 差 342 个样本 = 7.1 ms），
    # 而 mux 用 `-shortest` 会按短的那条流截——截掉的是视频，成片比时间轴少 3 帧，
    # 结尾整张 CTA 卡没了，元数据门却全是绿的。补齐到整帧边界，两边长度按构造相等。
    video_frames = int(round(tl["duration"] * common.FPS))
    want = int(round(video_frames / common.FPS * SR))
    if want < stereo.shape[0]:
        # 反向越界（ep03：+373 样本 ≈ 0.23 帧）：逐 beat 取整的帧数可以和总时长差零点几帧，
        # 与 pad 方向同一处理——对齐到整帧边界，截掉的是结尾 CTA 卡的静音尾。
        print(f"  trim 混音尾部 {stereo.shape[0] - want} 样本对齐整帧边界")
        stereo = stereo[:want]
    if want > stereo.shape[0]:
        stereo = np.concatenate([stereo, np.zeros((want - stereo.shape[0], 2), dtype=stereo.dtype)])
    meta = {
        "slug": tl["slug"], "engine": engine, "beats": len(tl["beats"]), "vo_placed": placed,
        "seconds": round(tl["duration"], 4), "samples": want, "sample_rate": SR,
        "video_frames": video_frames,
        "voice_gain": round(float(gain), 5),
        "voice_active_rms_db": _rms_db(np.array([active_rms * gain])),
        "voice_peak_pre": round(vpeak, 5),
        "bgm_spans": nspans, "bgm_rms_before_duck": round(float(np.sqrt(np.mean(bgm_bus ** 2))), 5),
        "bgm_rms_ducked": round(float(np.sqrt(np.mean(bgm_ducked ** 2))), 5),
        "sfx_hits": hits, "mix_peak": round(peak, 5), "headroom": round(headroom, 5),
        "mix_rms": round(float(np.sqrt(np.mean(mixy ** 2))), 5),
        "duck_during_speech_db": _rms_db(bgm_ducked[env_s > 0.6]),
        "duck_in_gaps_db": _rms_db(bgm_ducked[env_s < 0.05]),
    }
    wav = common.EPISODES / tl["slug"] / f"{tl['slug']}-mix.wav"
    if write_mix:
        common.write_wav(wav, stereo)
        meta["mix_wav"] = common.rel(wav)
        common.save_json(wav.with_suffix(".json"), meta)
    return wav, meta


def video_for(slug: str, aspect: str) -> Path:
    tl = spec_mod.load_spec(slug)
    v = common.EPISODES / tl["slug"] / f"{tl['slug']}-{aspect}-video.mp4"
    if not v.exists():
        raise FileNotFoundError(f"还没有无声底板：{common.rel(v)}（先跑 compose.py --episode {slug}）")
    return v


def count_video_frames(path: Path) -> int:
    """数成片里真实有多少帧。元数据说的帧数不算数——mux 那一刻才知道少了没有。"""
    out = common.run([
        common.ffmpeg_exe(), "-hide_banner", "-nostats", "-i", str(path),
        "-map", "0:v:0", "-f", "null", "-"], check=True)
    m = re.findall(r"frame=\s*(\d+)", out)
    if not m:
        raise RuntimeError(f"数不出帧数：{common.rel(path)}")
    return int(m[-1])


def measure_output_loudness(path: Path) -> dict[str, float]:
    """对最终编码文件量 EBU R128 响度与 true peak；mix.wav 的样本峰值不能替代 AAC 成品。"""
    out = common.run([
        common.ffmpeg_exe(), "-hide_banner", "-nostats", "-i", str(path),
        "-af", "loudnorm=I=-16:LRA=7:TP=-1.5:print_format=json", "-f", "null", "-"], check=True)
    m = re.search(r"\{\s*\"input_i\".*?\}", out, re.S)
    if not m:
        raise RuntimeError(f"ffmpeg 没有返回 loudnorm 量测：{common.rel(path)}")
    raw = json.loads(m.group(0))
    return {"lufs": float(raw["input_i"]), "true_peak_dbtp": float(raw["input_tp"]),
            "lra_lu": float(raw["input_lra"]), "threshold_lufs": float(raw["input_thresh"])}


def assemble(slug: str, aspect: str) -> Path:
    v = video_for(slug, aspect)
    # compose 把帧数记在 `-render.json` 里（视频文件是 `-video.mp4`），拿 mp4 的同名 .json 去找永远找不到
    render_p = v.with_name(v.stem.replace("-video", "") + "-render.json")
    render = common.load_json(render_p)
    if not render:
        raise FileNotFoundError(f"缺渲染记账 {common.rel(render_p)}：compose 那一轮没落盘")
    _, m = mix(slug)
    wav = Path(common.EPISODES / m["slug"] / f"{m['slug']}-mix.wav")
    out = common.OUT / f"{m['slug']}-{aspect}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    if render["frames"] != render["expected"]:
        raise RuntimeError(f"compose 自己就报了帧数不齐：{render['frames']}/{render['expected']}，音画必然漂")
    vsec = render["frames"] / common.FPS
    asec = m["samples"] / SR
    if abs(vsec - asec) > 1.0 / common.FPS + 1e-6:
        raise RuntimeError(f"音画时长差 {asec - vsec:+.3f} s，超过一帧——对齐会漂，先查 compose/narrate")
    if abs(asec - render["seconds"]) > 1.0 / common.FPS + 1e-6:
        raise RuntimeError(f"混音 {asec:.3f} s 与时间轴 {render['seconds']:.3f} s 不是同一条——narrate 改过时长而 compose 没重跑")
    t0 = time.time()
    master_db = master_gain_db(slug)
    # 不用 `-shortest`：它按短流截，截掉的是视频，元数据门却全绿。长度已在 mix 里对齐。
    common.ff("-loglevel", "error", "-i", str(v), "-i", str(wav),
              "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
              "-af", f"volume={master_db}dB",
              "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-ac", "2",
              "-movflags", "+faststart", str(out))
    secs = time.time() - t0
    delivered = count_video_frames(out)
    if delivered != render["frames"]:
        raise RuntimeError(
            f"成片只有 {delivered} 帧，时间轴 {render['frames']}——mux 吃了 "
            f"{render['frames'] - delivered} 帧（约 {(render['frames'] - delivered) / common.FPS:.2f} s）")
    measured = measure_output_loudness(out)
    if not OUTPUT_LUFS_RANGE[0] <= measured["lufs"] <= OUTPUT_LUFS_RANGE[1]:
        raise RuntimeError(f"成片响度 {measured['lufs']:.2f} LUFS 不在 {OUTPUT_LUFS_RANGE}")
    if measured["true_peak_dbtp"] > OUTPUT_TRUE_PEAK_MAX_DBTP:
        raise RuntimeError(f"成片 true peak {measured['true_peak_dbtp']:.2f} dBTP > {OUTPUT_TRUE_PEAK_MAX_DBTP}")
    res = {"slug": m["slug"], "aspect": aspect, "video": common.rel(v), "audio": common.rel(wav),
           "out": common.rel(out), "bytes": out.stat().st_size,
           "video_seconds": round(vsec, 4), "audio_seconds": round(asec, 4),
           "mux_seconds": round(secs, 2), "master_gain_db": master_db,
           "output_loudness": measured,
           "mix": {k: m[k] for k in ("voice_active_rms_db", "bgm_rms_ducked",
                                      "duck_during_speech_db", "duck_in_gaps_db", "mix_peak")}}
    common.save_json(out.with_suffix(".json"), res)
    print(f"  {aspect}: {vsec:.1f} s 音画 / {measured['lufs']:.2f} LUFS / "
          f"{measured['true_peak_dbtp']:.2f} dBTP / BGM 说话中 {m['duck_during_speech_db']} dB、"
          f"留白 {m['duck_in_gaps_db']} dB → {common.rel(out)}（{out.stat().st_size / 1e6:.1f} MB，封装 {secs:.0f} s）")
    return out


def selftest(slug: str) -> int:
    """不检查"代码跑通了"，检查那些错了不会报错、只会不好听的东西：摆位漂、ducking 方向反、
    换曲不在网格上、削顶、响度不达标。这几条错了视频照样出得来，观众却一眼（一耳）就能看出是机器活。"""
    import numpy as np

    fails: list[str] = []
    tl = spec_mod.timeline(slug)
    wav, m = mix(slug)
    x, sr = common.read_wav(wav)
    if sr != SR:
        fails.append(f"混音采样率 {sr} ≠ {SR}")
    if x.shape[0] != m["samples"]:
        fails.append(f"混音 {x.shape[0]} 样本 ≠ 时间轴 {m['samples']} 样本")
    if m["vo_placed"] != len(tl["beats"]):
        fails.append(f"旁白只摆了 {m['vo_placed']}/{len(tl['beats'])} 条")
    # 混音必须落在整帧边界：否则 mux 会按短流截视频，成片无声少几帧
    want_samples = int(round(int(round(tl["duration"] * common.FPS)) / common.FPS * SR))
    if x.shape[0] != want_samples:
        fails.append(f"混音 {x.shape[0]} 样本 ≠ 整帧边界 {want_samples}（差 {x.shape[0] - want_samples}）")
    if float(np.max(np.abs(x))) > CEILING + 1e-6:
        fails.append(f"混音削顶：落盘峰值 {float(np.max(np.abs(x))):.4f} > {CEILING}")
    if not -22.0 <= m["voice_active_rms_db"] <= -16.0:
        fails.append(f"语音活动 RMS {m['voice_active_rms_db']} dBFS 不在 -22…-16，平台响度验收过不了")
    ds, dg = m["duck_during_speech_db"], m["duck_in_gaps_db"]
    if ds is None or dg is None or ds > dg - 3.0:
        fails.append(f"ducking 不够或方向反了：说话中 {ds} dB vs 留白 {dg} dB（要求说话中至少低 3 dB）")
    want_sfx = sum(1 for e in tl["beats"] if e.get("sfx"))
    if m["sfx_hits"] != want_sfx:
        fails.append(f"SFX 摆了 {m['sfx_hits']}/{want_sfx} 下")
    final = common.OUT / f"{tl['slug']}-16x9.mp4"
    if final.exists():
        lm = measure_output_loudness(final)
        if not OUTPUT_LUFS_RANGE[0] <= lm["lufs"] <= OUTPUT_LUFS_RANGE[1]:
            fails.append(f"成片响度 {lm['lufs']:.2f} LUFS 不在 {OUTPUT_LUFS_RANGE}")
        if lm["true_peak_dbtp"] > OUTPUT_TRUE_PEAK_MAX_DBTP:
            fails.append(f"成片 true peak {lm['true_peak_dbtp']:.2f} dBTP > {OUTPUT_TRUE_PEAK_MAX_DBTP}")
        delivered = count_video_frames(final)
        if delivered != int(round(tl["duration"] * common.FPS)):
            fails.append(f"成片 {delivered} 帧 ≠ 时间轴 {int(round(tl['duration'] * common.FPS))} 帧")
    else:
        lm = None

    voice, n, _ = build_voice(tl, m["engine"])
    for e in tl["beats"]:
        a = int(round(e["start"] * SR))
        if float(np.max(np.abs(voice[a:a + int(0.06 * SR)]))) < 1e-4:
            fails.append(f"{e['id']} 的 start 处 60 ms 内没有语音——摆位漂了")
            break
    gain, _, _ = rms_target_gain(voice)
    if abs(gain - m["voice_gain"]) > 1e-4:
        fails.append(f"增益不可复现：两次算出 {gain:.6f} 与 {m['voice_gain']:.6f}")

    # 换曲段必须落在同一全局拍网格上：拿单段重建和整集总线逐样本比（所有淡化窗除外）
    bus, nspans = build_bgm(tl, n)
    xf = int(round(XFADE * SR))
    fi, fo = int(FADE_IN * SR), int(FADE_OUT * SR)
    checked = 0
    for j, (t0_, t1_, tr) in enumerate(spans_of(tl)):
        a = max(0, int(round(t0_ * SR)))
        b = min(int(round(t1_ * SR)), n)
        lo, hi = a + (fi if j == 0 else xf), b - (fo if j + 1 == nspans else 0)
        if hi - lo < 2000:
            continue
        checked += 1
        if float(np.max(np.abs(bus[lo:hi] - grid_slice(tr, a, hi - a)[lo - a:]))) > 1e-12:
            fails.append(f"段 {j}（{t0_:.1f}–{t1_:.1f} s / {tr}）不在全局拍网格上")
            break
    print(f"  混音 {n / SR:.1f} s / 语音增益 {m['voice_gain']} / BGM {nspans} 段（网格核对 {checked} 段）"
          f"/ SFX {m['sfx_hits']} 下")
    print(f"  语音活动 RMS {m['voice_active_rms_db']} dBFS  混音峰值 {m['mix_peak']}  "
          f"duck 说话中 {ds} / 留白 {dg} dB（差 {round(dg - ds, 2) if ds is not None and dg is not None else '?'} dB）")
    for p in fails:
        print("  FAIL " + p)
    print("selftest ok" if not fails else f"selftest FAIL：{len(fails)} 条")
    return 0 if not fails else 1


def report(slug: str) -> int:
    resolved = spec_mod.load_spec(slug)["slug"]
    m = common.load_json(common.EPISODES / resolved / f"{resolved}-mix.json")
    if not m:
        print("还没有 -mix.json，先跑 --episode")
        return 1
    for k, v in m.items():
        print(f"  {k:24s} {v}")
    return 0


def main() -> int:
    common.ensure_dirs()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--episode", required=True)
    ap.add_argument("--aspect", choices=list(common.ASPECTS))
    ap.add_argument("--both", action="store_true")
    ap.add_argument("--mix-only", action="store_true", help="只出 -mix.wav，不封装")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.report:
        return report(a.episode)
    if a.selftest:
        return selftest(a.episode)
    if a.mix_only:
        wav, m = mix(a.episode)
        print(f"  {common.rel(wav)}  {m['samples'] / SR:.1f} s  峰值 {m['mix_peak']}  "
              f"语音 {m['voice_active_rms_db']} dBFS  BGM 说话中 {m['duck_during_speech_db']} dB")
        return 0
    for aspect in (list(common.ASPECTS) if a.both else [a.aspect or "16x9"]):
        assemble(a.episode, aspect)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
