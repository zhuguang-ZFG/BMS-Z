"""视频系列的公共件：路径、ffmpeg 入口、字体、画幅几何、缓存键。

不画界面、不做决策——只把「这台机器上到底有什么」钉成一份，其余模块都从这里取，
免得 capture / compose / assemble 三家各自拼一遍路径然后拼出三个不同的缓存目录。
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
import shutil
import subprocess
import wave
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "circuits" / "assets"

# 产物全在 media/ 下（.gitignore 已排除）。MP4 与帧是可重算的派生物，入库会把仓库压垮。
MEDIA = ROOT / "media" / "video"
WORK = MEDIA / "work"
CLIPS = WORK / "clips"
TTS = WORK / "tts"
AUDIO = WORK / "audio"
EPISODES = WORK / "episodes"
OUT = MEDIA / "out"

FPS = 30
SAMPLE_RATE = 48000

VOICE_NAMES = {
    "teacher": "zh-CN-XiaoxiaoNeural",
    "guest": "zh-CN-YunxiNeural",
    "announcer": "zh-CN-XiaoyiNeural",
}
# 断网兜底：本机装了的离线语音。音质降级，但系列不能因为一个在线服务就断更。
SAPI_NAMES = {
    "teacher": "Microsoft Huihui Desktop - 中文(中国)",
    "guest": "Microsoft Huihui Desktop - 中文(中国)",
    "announcer": "Microsoft Huihui Desktop - 中文(中国)",
}

# 视频统一走站点动画的深色套色：白色动画与近黑卡片交替会整屏闪烁。
# 主题进入 clip 缓存键；改主题后绝不能静默复用上一套帧。
VIDEO_THEME = "dark"
VIDEO_BG = "#0d1117"
INK = (13, 17, 23)          # .bg 深色 #0d1117
INK_PANEL = (22, 27, 34)    # .panel 深色
TXT = (230, 237, 243)       # .txt 深色
SMALL = (139, 148, 158)     # .small 深色
EDGE = (48, 54, 61)         # .panel 边
TONES = {
    "": TXT,
    "hi": (68, 147, 248),   # .hi
    "warn": (255, 123, 114),  # .warn
    "ok": (63, 185, 80),    # .ok
    "gold": (210, 153, 34),  # .gold（只给字，不给线）
    "small": SMALL,         # .small：次要行，比如"平均 1.96"这种要被比下去的数
}



class Geometry:
    """一个画幅的全部版面尺寸。带子高度是量出来的，不是凑的：竖屏底部要躲开抖音的
    点赞/评论图标与文案折叠区，横屏底部要装得下两行 40 px 字幕。"""

    def __init__(self, key: str, w: int, h: int, top: int, bottom: int, split_at: float):
        self.key = key
        self.w = w
        self.h = h
        self.top = top
        self.bottom = bottom
        self.pad = 40 if w < h else 56
        self.split_at = split_at

    @property
    def content_y(self) -> int:
        return self.top

    @property
    def content_h(self) -> int:
        return self.h - self.top - self.bottom

    @property
    def content_w(self) -> int:
        return self.w - 2 * self.pad

    def figure_box(self, layout: str) -> tuple[int, int, int, int]:
        """图区外框 (x, y, w, h)，w/h 已取偶（yuv420p 要求偶数尺寸）。"""
        cw, ch = self.content_w, self.content_h
        if layout == "split":
            if self.portrait:
                fw, fh = _even(cw), _even(int(ch * 0.62))
                return self.pad, self.content_y, fw, fh
            fw = _even(int(cw * 0.5))
            return self.pad, self.content_y, fw, _even(ch)
        return self.pad, self.content_y, _even(cw), _even(ch)

    def figure_rect(self, layout: str, ratio: float | None) -> tuple[int, int, int, int]:
        """按 viewBox 比例缩放进图区并居中——capture 就按这个尺寸截，compose 直接贴。"""
        x, y, bw, bh = self.figure_box(layout)
        if ratio:
            fw, fh = bw, _even(int(bw / ratio))
            if fh > bh:
                fh = bh
                fw = _even(int(bh * ratio))
            x += (bw - fw) // 2
            y += (bh - fh) // 2
            return x, y, _even(fw), fh
        return x, y, bw, bh

    def text_box(self, layout: str) -> tuple[int, int, int, int]:
        cw, ch = self.content_w, self.content_h
        if layout == "split":
            if self.portrait:
                return self.pad, self.content_y + _even(int(ch * 0.62)), cw, _even(int(ch * 0.38))
            fx, fy, fw, fh = self.figure_box("split")
            return fx + fw + 56, fy, _even(int(cw * 0.44)), fh
        return self.pad, self.h - self.bottom + 24, cw, self.bottom - 48

    @property
    def portrait(self) -> bool:
        return self.h > self.w

    def __repr__(self) -> str:
        return f"Geometry({self.key} {self.w}x{self.h})"


def _even(v: int) -> int:
    return int(v) // 2 * 2


ASPECTS = {
    "16x9": Geometry("16x9", 1920, 1080, top=118, bottom=208, split_at=0.5),
    "9x16": Geometry("9x16", 1080, 1920, top=250, bottom=590, split_at=0.62),
}


def ensure_dirs() -> None:
    for d in (MEDIA, WORK, CLIPS, TTS, AUDIO, EPISODES, OUT, ROOT / ".local"):
        d.mkdir(parents=True, exist_ok=True)


def svg_ratio(svg_path: Path) -> float | None:
    """根 viewBox 的宽高比。画幅按它把图缩放进图区：不缩的话一张 800×500 的图塞进
    1000×1080 的竖屏图区，浏览器自己 meet 一下就在上下各留 200 多 px 白，看着像漏了一块。"""
    import xml.etree.ElementTree as ET

    vb = (ET.fromstring(svg_path.read_text(encoding="utf-8")).get("viewBox") or "").split()
    if len(vb) != 4:
        return None
    w, h = float(vb[2]), float(vb[3])
    return w / h if h else None


def clip_paths(svg: str, w: int, h: int, fps: int = FPS, theme: str = VIDEO_THEME) -> tuple[Path, Path]:
    """clip 与元数据。缓存键含尺寸、帧率和主题；少一维就会复用错误的帧。"""
    mp4 = CLIPS / f"{svg.removesuffix('.svg')}@{w}x{h}_{fps}fps-{theme}.mp4"
    return mp4, mp4.with_suffix(".json")


@functools.lru_cache(maxsize=1)
def ffmpeg_exe() -> str:
    """系统没有 ffmpeg，用 imageio-ffmpeg 自带的那一个（V1）。"""
    import imageio_ffmpeg

    exe = imageio_ffmpeg.get_ffmpeg_exe()
    if not os.path.exists(exe):
        raise FileNotFoundError(f"imageio-ffmpeg 指向的 ffmpeg 不存在：{exe}")
    return exe


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"命令失败（退出码 {r.returncode}）：{' '.join(str(c) for c in cmd[:6])} …\n{r.stderr[-2000:]}")
    return r.stdout + r.stderr


def ff(*args: str, check: bool = True) -> str:
    return run([ffmpeg_exe(), "-hide_banner", "-y", *args], check=check)


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def read_wav(path: Path) -> tuple[NDArray[np.float32], int]:
    """stdlib wave → float32 numpy (n, ch)。不引 soundfile/librosa，仓库的依赖面要保持小。"""
    import numpy as np

    with wave.open(str(path), "rb") as w:
        n, ch, sr, width = w.getnframes(), w.getnchannels(), w.getframerate(), w.getsampwidth()
        raw = w.readframes(n)
    if width != 2:
        raise ValueError(f"只支持 16 bit PCM，{path} 是 {width * 8} bit")
    a = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    return a.reshape(-1, ch) if ch > 1 else a.reshape(-1, 1), sr


def write_wav(path: Path, samples, sr: int = SAMPLE_RATE) -> None:
    import numpy as np

    a = np.asarray(samples, dtype=np.float32)
    if a.ndim == 1:
        a = a.reshape(-1, 1)
    clipped = np.clip(a, -1.0, 1.0)
    data = (clipped * 32767.0).astype("<i2").tobytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(a.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data)


def trim_silence(path: Path, thr_rel: float = 0.02, lead: float = 0.010,
                 tail: float = 0.030) -> float:
    """就地削掉语音容器自带的首尾静音，返回削掉的秒数；削干净了返回 0，所以可以反复跑。

    edge-tts 给的是 mp3，解成 PCM 后头尾各带一段填充：ep02 的 74 条实测**首 170–200 ms、
    尾 520–845 ms**，合计 54.8 s。不削有两笔账对不上——画面在 beat 的 start 那一帧就切，
    话却晚 0.18 s 出口；分镜写 gap=0.30 s，听感却是 1.03 s 的空白。时长表必须由削完的
    语音来量，否则整条流水线跟着一起长。
    阈值按峰值的相对值取（不是绝对 0.01）：轻读的短句绝对幅度小，绝对阈值会把首字削掉。
    """
    import numpy as np

    a, sr = read_wav(path)
    x = np.asarray(a, dtype=np.float32)
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if peak <= 0.0:
        return 0.0
    active = np.nonzero(np.max(np.abs(x), axis=1) > thr_rel * peak)[0]
    if active.size == 0:
        return 0.0
    i0 = max(0, int(active[0]) - int(lead * sr))
    i1 = min(x.shape[0], int(active[-1]) + int(tail * sr) + 1)
    if i0 == 0 and i1 == x.shape[0]:
        return 0.0
    tmp = path.with_name(path.stem + ".trim.wav")
    write_wav(tmp, x[i0:i1], sr)
    tmp.replace(path)
    return (x.shape[0] - (i1 - i0)) / sr


def sha(*parts: object) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:20]


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")


@functools.lru_cache(maxsize=64)
def font(kind: str, size: int):
    from PIL import ImageFont

    table = {
        "title": ("msyhbd.ttc", 0),      # 微软雅黑 Bold
        "bold": ("msyhbd.ttc", 0),
        "text": ("msyh.ttc", 0),         # 微软雅黑 Regular
        "mono": ("consola.ttf", 0),      # 数字打点用等宽，读秒/读数不跳
        "hei": ("simhei.ttf", 0),
    }
    name, index = table[kind]
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size, index=index)


def have_tmp_disk(path: Path, need_mb: int) -> None:
    free = shutil.disk_usage(str(path.parent if path.parent.exists() else path)).free / 1e6
    if free < need_mb:
        raise RuntimeError(f"{path} 所在盘只剩 {free:.0f} MB，至少需要 {need_mb} MB")


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)
