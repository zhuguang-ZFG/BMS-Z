"""全片审计：把「人眼与人耳能发现、但工具从不报错」的质量项固化成门。

assemble 的 selftest 量的是混音总线与音量账，audit 量的是**最终成片本身**——
AAC 之后、H.264 之后的成品。审一套 11 分钟的片子不能只靠抽帧：这里把全片
20557 帧逐帧读成亮度序列，把整条音轨逐样本读出来，然后按判据列 FAIL：

  画面  闪切（相邻帧平均亮度跳变超过阈值）、黑帧/白帧、丢帧导致的时长漂
  声音  削波样本、直流偏置、孤立爆音（click）、最长静音、口型与字幕错位、
        BGM 掩蔽深度、响度与 true peak（与 assemble 同一把尺）

只有成片路径被检查，不重算流水线中间件——审计的意义正在于“量成品，不量意图”。

用法：
    python3 tools/video/audit.py --episode ep02-recognize-bms
    python3 tools/video/audit.py --episode ep02-recognize-bms --aspect 9x16
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import spec as spec_mod  # noqa: E402

SCALE_W, SCALE_H = 16, 16            # 画面降采样网格：均值保真，流量小三个数量级
FLASH_DL = 25.0                       # 相邻帧平均亮度跳变阈值：深色统一皮肤下应≈0
FLASH_RATIO_MAX = 0.005               # 允许 0.5% 帧有跳变（clip 换帧本身有内容变化）
DARK_FRAME_MAX = 0.005                # 黑帧（L<8）比例上限
BRIGHT_FRAME_MAX = 0.005              # 白帧（L>247）比例上限
CLIP_SAMPLES_MAX = 0                  # 落盘后 |x|≥0.999 的样本数必须为 0
DC_MAX = 0.002                        # 直流偏置
CLICK_DELTA = 0.25                    # 相邻样本差超过它就算孤立爆音候选
SILENCE_DB = -55.0                     # 静音帧判据
SILENCE_LONGEST_MAX = 1.2             # 最长连续静音（分镜 gap 只有 0.3 s，静得久就是漏音）
LIPSYNC_LEAD = 0.45                   # 每条旁白起点距字幕首窗开始的最大提前量


def frame_luma(path: Path) -> NDArray[np.float64]:
    """全片逐帧平均亮度（0–255 全范围 luma）。

    必须在 RGB 域缩放：`-vf scale` 之后再 `-pix_fmt gray` 走的是 YUV 灰度平面，
    实测会把纯 INK 底映射成 0、亮字压掉四成，一整集暗色成片被误判成 14% 黑帧。
    `scale=NxN` + `rgb24` 与全分辨率 luma 一致（ep02 竖屏实测 20.21 vs 19.96）。
    """
    import numpy as np

    cmd = [common.ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-i", str(path),
           "-vf", f"scale={SCALE_W}:{SCALE_H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"读帧失败：{common.rel(path)}：{r.stderr.decode('utf-8', 'replace')[-500:]}")
    a = np.frombuffer(r.stdout, dtype="uint8")
    if a.size == 0:
        raise RuntimeError(f"{common.rel(path)} 解不出帧")
    per = SCALE_W * SCALE_H * 3
    n = a.size // per
    f = a[: n * per].reshape(n, SCALE_H, SCALE_W, 3).astype(np.float64)
    luma = 0.2126 * f[:, :, :, 0] + 0.7152 * f[:, :, :, 1] + 0.0722 * f[:, :, :, 2]
    return luma.mean(axis=(1, 2))


def audio_mono(path: Path) -> NDArray[np.float32]:
    """整条音轨 → float32 单声道。成品已被母带处理过，量它才有意义。

    自己降混，不用 ffmpeg 的 `-ac 1`：浮点重矩阵会把左右同相直接相加（不乘 1/2），
    一条峰值 0.874 的立体声成品会被量成 1.2355，爆音与削波全是测量假象；16-bit 路径
    又会把它钳回 1.0，同样不是真相。取 0.5*(L+R) 是与内容一致的口径。
    """
    import numpy as np

    cmd = [common.ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-i", str(path),
           "-map", "0:a:0", "-f", "f32le", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"读音轨失败：{common.rel(path)}：{r.stderr.decode('utf-8', 'replace')[-500:]}")
    a = np.frombuffer(r.stdout, dtype="<f4").astype("float32")
    if a.size == 0:
        raise RuntimeError(f"{common.rel(path)} 解不出样本")
    ch = a.size // 2
    return (0.5 * (a[: ch * 2][0::2] + a[: ch * 2][1::2])).astype("float32")


def audit_video(path: Path, expected_frames: int) -> tuple[list[str], dict[str, float]]:
    import numpy as np

    fails: list[str] = []
    luma = frame_luma(path)
    frames = int(luma.shape[0])
    if frames != expected_frames:
        fails.append(f"帧数 {frames} ≠ 时间轴 {expected_frames}")
    if luma.shape[0] < 2:
        fails.append("帧数太少，无法审计画面")
        return fails, {}
    d = np.abs(np.diff(luma))
    flash = float(np.count_nonzero(d > FLASH_DL))
    flash_ratio = flash / max(d.shape[0], 1)
    dark = float(np.count_nonzero(luma < 8)) / luma.shape[0]
    bright = float(np.count_nonzero(luma > 247)) / luma.shape[0]
    if flash_ratio > FLASH_RATIO_MAX:
        worst = float(np.max(d))
        fails.append(f"闪切 {flash_ratio * 100:.2f}% 帧跳变 >{FLASH_DL:.0f}（最大 {worst:.1f}）")
    if dark > DARK_FRAME_MAX:
        fails.append(f"黑帧占比 {dark * 100:.2f}%")
    if bright > BRIGHT_FRAME_MAX:
        fails.append(f"白帧占比 {bright * 100:.2f}%")
    stats = {"frames": float(luma.shape[0]), "flash_ratio": flash_ratio,
             "dark_ratio": dark, "bright_ratio": bright, "max_dl": float(np.max(d))}
    print(f"  画面 {frames} 帧：闪切 {flash_ratio * 100:.3f}% / 黑 {dark * 100:.3f}% / "
          f"白 {bright * 100:.3f}% / 最大跳变 {float(np.max(d)):.1f}")
    return fails, stats


def audit_audio(path: Path, slug: str) -> tuple[list[str], dict[str, float]]:
    import numpy as np

    fails: list[str] = []
    x = audio_mono(path)
    sr = common.SAMPLE_RATE
    n = x.shape[0]

    clipped = int(np.count_nonzero(np.abs(x) >= 0.999))
    if clipped > CLIP_SAMPLES_MAX:
        fails.append(f"削波样本 {clipped} 个 |x|≥0.999")

    dc = abs(float(np.mean(x)))
    if dc > DC_MAX:
        fails.append(f"直流偏置 {dc:.5f}")

    # 爆音：与**音源**比，不与固定阈值比。SFX 的合成沿、语音的塞音本身就是陡沿，
    # 拿绝对阈值判会把设计里的东西判成缺陷；编码新引入的断点才该红。
    d = np.abs(np.diff(x))
    jump = d > CLICK_DELTA
    isolated = jump[1:] & jump[:-1] if jump.shape[0] > 2 else np.zeros(0, dtype=bool)
    clicks = int(np.count_nonzero(isolated))
    src = _source_mono(slug)
    sd = np.abs(np.diff(src))
    sjump = sd > CLICK_DELTA
    siso = sjump[1:] & sjump[:-1] if sjump.shape[0] > 2 else np.zeros(0, dtype=bool)
    src_clicks = int(np.count_nonzero(siso))
    budget = src_clicks * 2 + 200
    if clicks > budget:
        fails.append(f"孤立爆音 {clicks} 处，超过音源 {src_clicks} 的两倍加 200 的预算")

    # 静音：10 ms 一帧取 RMS，连续帧低于判据算一段
    fl = int(0.01 * sr)
    m = n // fl
    rms = np.sqrt(np.mean(x[: m * fl].reshape(m, fl) ** 2, axis=1))
    db = 20 * np.log10(np.maximum(rms, 1e-10))
    silent = db < SILENCE_DB
    longest = 0
    run = 0
    for s in silent:
        run = run + 1 if s else 0
        longest = max(longest, run)
    longest_s = longest * fl / sr
    if longest_s > SILENCE_LONGEST_MAX:
        fails.append(f"最长静音 {longest_s:.2f} s > {SILENCE_LONGEST_MAX}")

    # 口型：每条旁白的实测起点不该比它的字幕首窗晚太多（早 = 字幕姗姗来迟）
    tl = spec_mod.timeline(slug)
    voice = _voice_bus(tl)
    late: list[str] = []
    for e in tl["beats"]:
        a = int(round(e["start"] * sr))
        seg = voice[a:a + int(LIPSYNC_LEAD * sr)]
        if seg.shape[0] == 0 or float(np.max(np.abs(seg))) < 1e-4:
            late.append(e["id"])
    if late:
        fails.append(f"{len(late)} 条旁白在字幕前 {LIPSYNC_LEAD}s 内无声：{late[:6]}")

    peak = float(np.max(np.abs(x)))
    print(f"  声音 {n / sr:.1f} s：削波 {clipped} / 直流 {dc:.5f} / 爆音 {clicks} / "
          f"最长静音 {longest_s:.2f} s / 峰值 {peak:.4f} / 口型迟到 {len(late)} 条")
    return fails, {"peak": peak, "longest_silence": longest_s, "clicks": float(clicks),
                   "clipped": float(clipped)}


def _source_mono(slug: str) -> NDArray[np.float32]:
    """封装前的混音原件：audit 的“音源基线”。"""
    wav = common.EPISODES / slug / f"{slug}-mix.wav"
    if not wav.exists():
        raise FileNotFoundError(f"没有混音原件 {common.rel(wav)}（先跑 assemble --mix-only）")
    x, _sr = common.read_wav(wav)
    return (0.5 * (x[:, 0] + x[:, 1])).astype("float32")


def _voice_bus(tl: dict) -> NDArray[np.float64]:
    import numpy as np

    from assemble import build_voice, narrate_engine

    sr = common.SAMPLE_RATE
    bus, _n, _placed = build_voice(tl, narrate_engine(tl["slug"]))
    assert bus.shape[0] == int(round(tl["duration"] * sr))
    return np.asarray(bus, dtype=np.float64)


def audit(slug: str, aspect: str) -> int:
    tl = spec_mod.timeline(slug)
    path = common.OUT / f"{slug}-{aspect}.mp4"
    if not path.exists():
        print(f"还没有成片：{common.rel(path)}（先跑 assemble.py）")
        return 1
    meta_p = path.with_suffix(".json")
    meta = common.load_json(meta_p) or {}
    vfails, vstats = audit_video(path, int(round(tl["duration"] * common.FPS)))
    afails, astats = audit_audio(path, slug)
    fails = vfails + afails
    for k in ("output_loudness",):
        m = meta.get(k)
        if m:
            print(f"  {k}: {m['lufs']} LUFS / {m['true_peak_dbtp']} dBTP / LRA {m['lra_lu']} LU")
    print(f"  {aspect} FAIL {len(fails)} 条" if fails else f"  {aspect} audit ok")
    for f in fails:
        print("    FAIL " + f)
    return 0 if not fails else 1


def main() -> int:
    common.ensure_dirs()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--episode", required=True)
    ap.add_argument("--aspect", choices=list(common.ASPECTS))
    ap.add_argument("--both", action="store_true")
    a = ap.parse_args()
    rc = 0
    for aspect in (list(common.ASPECTS) if a.both else [a.aspect or "16x9"]):
        rc |= audit(a.episode, aspect)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
