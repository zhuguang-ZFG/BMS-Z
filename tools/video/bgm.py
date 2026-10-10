"""原创背景音乐与音效：全部由 numpy 合成，零版权。

为什么不用现成 BGM 库：B 站/抖音都对音频做指纹比对，一条用了不明来源 loop 的教程可以
被静默限流甚至下架，而这是全七集共用的底噪——一首歌的问题会传染整个系列。自己合成还有
个副作用很好用：拍速、密度、电平全在手里，能给旁白让路（ducking）。

loop 的拍子落在**整数样本网格**上（BEAT_N 取整），不是按 132 BPM 的浮点秒数摆放。代价是
实际拍速差百万分之三（听不出来），换来的是循环点在数学上精确可周期——`--selftest` 里那条
"两个循环逐样本相等"才可能过，浮点网格下它永远差最后一个样本。

用法：
    python3 tools/video/bgm.py --selftest
    python3 tools/video/bgm.py --render
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

BPM = 132.0
BARS = 4
PER_BAR = 4
SR = common.SAMPLE_RATE
BEAT = 60.0 / BPM
BEAT_N = int(round(BEAT * SR))
LOOP_N = BARS * PER_BAR * BEAT_N
LOOP = LOOP_N / SR

# Am – F – C – G，每小节一根；写 MIDI 号而不是频率，核对音名时不用心算
CHORDS = [
    (45, 60, 64, 69),   # A2  Am
    (41, 57, 60, 65),   # F2  F
    (48, 55, 59, 64),   # C3  C
    (43, 50, 54, 59),   # G2  G
]
DENSITY = {
    "tension": {"pad": 0.30, "bass": 0.34, "kick": 0.30, "hat": 0.10, "pluck": 0.00, "pad_cut": 900.0},
    "neutral": {"pad": 0.34, "bass": 0.20, "kick": 0.14, "hat": 0.13, "pluck": 0.22, "pad_cut": 1400.0},
    "outro": {"pad": 0.30, "bass": 0.16, "kick": 0.00, "hat": 0.06, "pluck": 0.30, "pad_cut": 1800.0},
}
FULL_DB = -14.0
DUCKED_DB = -26.0
SEED = 20261010


def midi(n: float) -> float:
    return 440.0 * 2.0 ** ((n - 69) / 12.0)


def _place(out, pos: int, y):
    """把一段声音放进环形缓冲区：pos 可为负或越界，跨循环点的尾巴折到另一端。

    上一版这里写的是 `if pos + len(y) > n: continue`，于是第 4 小节第 4 拍的 pluck 被整段
    丢掉——loop 的最后一拍没有音。改成取模摆放后，两半缓冲区严格相等（selftest 逐样本验），
    接缝不是"接得像"而是不存在。
    """
    import numpy as np

    idx = (np.arange(y.shape[0]) + pos) % out.shape[0]
    np.add.at(out, idx, y)


def _oscs(freqs, seg: int):
    """三个略微失谐的振荡 × 两个谐波叠出 pad 的厚度；失谐取百分比，绝对值随音高缩放。"""
    import numpy as np

    t = np.arange(seg, dtype=np.float64) / SR
    out = np.zeros(seg)
    for f in freqs:
        for det, amp in ((0.0, 0.6), (0.0035, 0.22), (-0.0041, 0.18)):
            w = 2 * np.pi * f * (1 + det)
            out += amp * (np.sin(w * t) + 0.28 * np.sin(2 * w * t))
    return out / max(1.0, len(freqs) * 0.9)


def _lowpass(x, cutoff_hz: float):
    """一阶 RC 低通。不用 scipy（仓库只锁 numpy）；递推跑在 Python 里，每次调用只有一个
    声部的长度，整首 loop 的合成实测不到 1 s，不值得为上托普里茨矩阵优化。"""
    import numpy as np

    a = float(np.exp(-2 * np.pi * cutoff_hz / SR))
    k = 1.0 - a
    y = np.empty(x.shape[0])
    acc = 0.0
    for i in range(x.shape[0]):
        acc = acc * a + x[i] * k
        y[i] = acc
    return y


def _noise(n: int):
    import numpy as np

    # 种子必须钉死：BGM 是可重算产物，随机数不固定的话同一集两次渲染哈希不同，缓存与对账白做
    return np.random.default_rng(SEED).standard_normal(n)


def _bars(reps: int):
    """只走 reps×4 个小节本身，**不多走前一节**：跨界的声音由 `_place` 的取模折回开头，
    那就是"上一循环最后一节"的尾巴。上一版在这里多走 b=-1，结果最后一节被摆两次——
    两半缓冲区差 0.45（正好是一个 pad 的电平），归一化也跟着被那个叠音的假峰值压低。"""
    return range(BARS * reps)


def pad(dens: float, cutoff: float, n: int, reps: int):
    import numpy as np

    out = np.zeros(n)
    bar_n = PER_BAR * BEAT_N
    seg = bar_n
    t = np.arange(seg, dtype=np.float64) / SR
    for b in _bars(reps):
        freqs = [midi(c) / 2 for c in CHORDS[b % BARS][1:]]  # 低八度，给旁白让出中频
        bt = t / (bar_n / SR)
        # 起音 0.18、收尾 0.22（单位：小节），包络完整落在一小节内 → 循环点两侧都是零
        env = np.clip(bt / 0.18, 0, 1) * np.clip((1.0 - bt) / 0.22, 0, 1)
        _place(out, b * bar_n, _lowpass(_oscs(freqs, seg) * env, cutoff) * dens)
    return out


def bass(dens: float, n: int, reps: int):
    import numpy as np

    out = np.zeros(n)
    seg = int(0.9 * BEAT_N)
    t = np.arange(seg, dtype=np.float64) / SR
    for b in _bars(reps):
        f = midi(CHORDS[b % BARS][0])
        x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t)
        env = np.clip(t / 0.012, 0, 1) * np.exp(-t / 0.22)
        for beat in (0, 2.5):
            _place(out, int(round((b * PER_BAR + beat) * BEAT_N)), x * env * dens)
    return out


def kick(dens: float, n: int, reps: int):
    import numpy as np

    if dens == 0:
        return np.zeros(n)
    out = np.zeros(n)
    seg = int(0.16 * SR)
    t = np.arange(seg, dtype=np.float64) / SR
    f = 118.0 * np.exp(-t / 0.045) + 46.0
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.07) * dens
    for b in _bars(reps):
        for beat in (0, 2):
            _place(out, int(round((b * PER_BAR + beat) * BEAT_N)), x)
    return out


def hat(dens: float, n: int, reps: int):
    import numpy as np

    if dens == 0:
        return np.zeros(n)
    out = np.zeros(n)
    seg = int(0.05 * SR)
    x = _noise(seg)
    y = (x - _lowpass(x, 6000.0)) * np.exp(-np.arange(seg) / (0.03 * SR)) * dens
    for b in _bars(reps):
        for beat in (0.5, 1.5, 2.5, 3.5):
            _place(out, int(round((b * PER_BAR + beat) * BEAT_N)), y)
    return out


def pluck(dens: float, n: int, reps: int):
    import numpy as np

    if dens == 0:
        return np.zeros(n)
    out = np.zeros(n)
    seg = int(0.5 * SR)
    t = np.arange(seg, dtype=np.float64) / SR
    hit = np.exp(-t / 0.12) * np.clip(t / 0.004, 0, 1) * dens
    for b in _bars(reps):
        for beat, note in ((1.0, CHORDS[b % BARS][2]), (3.0, CHORDS[b % BARS][3])):
            f = midi(note)
            x = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t) + 0.2 * np.sin(6 * np.pi * f * t)
            _place(out, int(round((b * PER_BAR + beat) * BEAT_N)), x * hit)
    return out


def build(track: str = "neutral", reps: int = 2):
    """合成 reps 个循环首尾相接的环形缓冲（长度 LOOP_N*reps），按峰值归一到 0.9。"""
    import numpy as np

    d = DENSITY[track]
    n = LOOP_N * reps
    x = (pad(d["pad"], d["pad_cut"], n, reps) + bass(d["bass"], n, reps)
         + kick(d["kick"], n, reps) + hat(d["hat"], n, reps) + pluck(d["pluck"], n, reps))
    peak = float(np.max(np.abs(x))) or 1.0
    return x / peak * 0.9


def loop_of(track: str = "neutral"):
    return build(track, 2)[:LOOP_N]


def whoosh(dur: float = 0.55):
    """章节卡过场：噪声按上扫的分频拆开，前段闷后段亮。"""
    import numpy as np

    n = int(dur * SR)
    x = _noise(n)
    sweep = np.linspace(0, 1, n)
    y = _lowpass(x, 800.0) * (1 - sweep) ** 1.5 + (x - _lowpass(x, 2400.0)) * sweep ** 2.0
    t = np.arange(n, dtype=np.float64) / SR
    y = y * np.clip(t / 0.12, 0, 1) * np.exp(-t / (dur * 0.45))
    return y / (float(np.max(np.abs(y))) or 1.0) * 0.5


def tick(dur: float = 0.09):
    """验收清单打勾那一声：1.8 kHz 短促铃。衰减要快，不然七下听着像机枪。"""
    import numpy as np

    n = int(dur * SR)
    t = np.arange(n, dtype=np.float64) / SR
    y = np.sin(2 * np.pi * 1820 * t) * np.exp(-t / 0.022) + 0.4 * np.sin(2 * np.pi * 2730 * t) * np.exp(-t / 0.014)
    return y / float(np.max(np.abs(y))) * 0.42


def blip(dur: float = 0.12, freq: float = 660.0):
    import numpy as np

    n = int(dur * SR)
    t = np.arange(n, dtype=np.float64) / SR
    y = np.sin(2 * np.pi * freq * t) * np.exp(-t / 0.05) * np.clip(t / 0.006, 0, 1)
    return y / float(np.max(np.abs(y))) * 0.5


def tile(loop, seconds: float):
    import numpy as np

    need = int(round(seconds * SR))
    return np.tile(loop, -(-need // loop.shape[0]))[:need]


def duck(bgm, env, full_db: float = FULL_DB, ducked_db: float = DUCKED_DB):
    """旁白在的时候 BGM 让路。env=0（没人说话）拿满电平，env=1（说话中）拿低电平——
    方向写反就变成"念书时音乐变大"，这个错在耳机里一耳朵就能听出来。"""
    import numpy as np

    full = 10.0 ** (full_db / 20.0)
    low = 10.0 ** (ducked_db / 20.0)
    return np.asarray(bgm) * (full + (low - full) * np.clip(env, 0, 1))


def vo_envelope(vo, frame: int = 128, attack: float = 0.03, release: float = 0.30):
    """旁白 → 包络：128 样本（2.7 ms）一帧取 |x| 均值，再按 attack/release 分段递推。

    为什么按帧而不是按样本递推：一整集旁白是两千万样本级，按样本的 Python 循环要跑几十秒；
    按帧把循环压到十万级，而 2.7 ms 的分辨率对 300 ms 的 release 绰绰有余。
    """
    import numpy as np

    x = np.abs(np.asarray(vo, dtype=np.float64).reshape(-1))
    nf = -(-x.shape[0] // frame)
    padded = np.zeros(nf * frame)
    padded[: x.shape[0]] = x
    f = padded.reshape(nf, frame).mean(axis=1)
    aa = float(np.exp(-frame / (attack * SR)))
    ra = float(np.exp(-frame / (release * SR)))
    out = np.empty(nf)
    acc = 0.0
    for i in range(nf):
        a = aa if f[i] <= acc else ra
        acc = acc * a + f[i] * (1.0 - a)
        out[i] = acc
    return np.clip(out / (float(out.max()) or 1.0), 0.0, 1.0)


def envelope_at(env, n: int):
    """帧包络线性拉到 n 个样本。用 repeat 会留下 2.7 ms 的台阶，音量爬坡上一听是 pumping。"""
    import numpy as np

    env = np.asarray(env, dtype=np.float64)
    if env.shape[0] < 2:
        return np.full(n, float(env[0]) if env.shape[0] else 0.0)
    pos = np.linspace(0.0, env.shape[0] - 1, n)
    i0 = np.floor(pos).astype(int)
    frac = pos - i0
    i1 = np.minimum(i0 + 1, env.shape[0] - 1)
    return env[i0] * (1 - frac) + env[i1] * frac


def selftest() -> int:
    import numpy as np

    fails: list[str] = []
    for track in DENSITY:
        buf = build(track, 2)
        a, b = buf[:LOOP_N], buf[LOOP_N:]
        diff = float(np.max(np.abs(a - b)))
        if diff > 1e-9:
            fails.append(f"[{track}] 循环不精确：两个循环的最大差 {diff:.3e}（>1e-9 就是听得到的咔）")
        if buf.shape[0] != 2 * LOOP_N:
            fails.append(f"[{track}] 缓冲长度 {buf.shape[0]} ≠ 2×{LOOP_N}")
        peak = float(np.max(np.abs(a)))
        if abs(peak - 0.9) > 0.02:
            fails.append(f"[{track}] 第一个循环的峰值 {peak:.4f} 不在 0.90±0.02——归一化的参照物不对")
        seam = abs(float(a[0] - a[-1]))
        typical = float(np.median(np.abs(np.diff(a))))
        if seam > 6 * typical + 1e-9:
            fails.append(f"[{track}] 接缝跳变 {seam:.5f} 远大于典型跳变 {typical:.5f}")
        # 四小节都得有音：丢音的 bug 只会让某一节安静一点，逐节 rms 一比就现形
        bars = [float(np.sqrt(np.mean(a[i * PER_BAR * BEAT_N:(i + 1) * PER_BAR * BEAT_N] ** 2)))
                for i in range(BARS)]
        if min(bars) < 0.35 * max(bars):
            fails.append(f"[{track}] 小节能量不均，疑似某拍的音被丢了：{[round(v, 4) for v in bars]}")
        print(f"  {track:8s} loop {LOOP:.4f} s（{LOOP_N} 样本，{BEAT_N}/拍）  peak {peak:.4f}  "
              f"rms {float(np.sqrt(np.mean(a ** 2))):.4f}  两循环差 {diff:.1e}  小节 rms {[round(v, 3) for v in bars]}")

    bgm = loop_of("tension")
    loud = float(np.sqrt(np.mean(bgm ** 2)))
    full = envelope_at(np.ones(8), bgm.shape[0])
    silent = envelope_at(np.zeros(8), bgm.shape[0])
    during = float(np.sqrt(np.mean(duck(bgm, full) ** 2)))
    no_speech = float(np.sqrt(np.mean(duck(bgm, silent) ** 2)))
    if not during < no_speech * 10 ** (-6 / 20.0):
        fails.append(f"ducking 不足：说话时只从 {no_speech:.5f} 降到 {during:.5f}（要求 ≥6 dB）")
    if not abs(no_speech - loud * 10 ** (FULL_DB / 20.0)) < 1e-6:
        fails.append(f"无人说话时不在满电平：{no_speech:.5f} vs {loud * 10 ** (FULL_DB / 20.0):.5f}")
    if during >= loud:
        fails.append("ducking 方向反了：说话时的 BGM 比原始还响")
    speech = vo_envelope(loop_of("neutral") * 0.5)
    if float(speech.max()) < 0.9:
        fails.append(f"vo_envelope 峰值归一化没做到：{float(speech.max()):.3f}")
    print(f"  ducking  满电平 {no_speech:.5f} → 说话中 {during:.5f}（{20 * np.log10(during / no_speech):+.1f} dB）"
          f"  语音包络 {speech.shape[0]} 帧")

    for name, fn in (("whoosh", whoosh), ("tick", tick), ("blip", blip)):
        y = fn()
        p = float(np.max(np.abs(y)))
        if not 0.2 <= p <= 0.55:
            fails.append(f"{name} 峰值不在 0.2–0.55：{p:.3f}")
        print(f"  {name:8s} 长 {len(y) / SR:.3f} s  peak {p:.3f}")

    for p in fails:
        print("  FAIL " + p)
    print("selftest ok" if not fails else f"selftest FAIL：{len(fails)} 条")
    return 0 if not fails else 1


def render() -> int:
    import numpy as np

    for track in DENSITY:
        x = loop_of(track)
        p = common.AUDIO / f"bgm-{track}.wav"
        common.write_wav(p, np.stack([x, x], axis=1))
        print(f"  {common.rel(p)}  {len(x) / SR:.4f} s loop")
    for name, fn in (("whoosh", whoosh), ("tick", tick), ("blip", blip)):
        y = fn()
        p = common.AUDIO / f"sfx-{name}.wav"
        common.write_wav(p, np.stack([y, y], axis=1))
        print(f"  {common.rel(p)}  {len(y) / SR:.3f} s")
    common.save_json(common.AUDIO / "bgm-meta.json", {
        "bpm_nominal": BPM, "bpm_actual": 60.0 * SR / BEAT_N, "beat_samples": BEAT_N,
        "loop_samples": LOOP_N, "loop_seconds": round(LOOP, 6), "bars": BARS,
        "samples_per_bar": PER_BAR * BEAT_N, "sample_rate": SR, "tracks": list(DENSITY),
        "duck_full_db": FULL_DB, "duck_ducked_db": DUCKED_DB, "seed": SEED,
    })
    print(f"  {common.rel(common.AUDIO / 'bgm-meta.json')}")
    return 0


def main() -> int:
    common.ensure_dirs()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.render:
        return render()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
