"""全片审计：把「人眼与人耳能发现、但工具从不报错」的质量项固化成门。

assemble 的 selftest 量的是混音总线与音量账，audit 量的是**最终成片本身**——
AAC 之后、H.264 之后的成品。审一套 11 分钟的片子不能只靠抽帧：这里把全片
20557 帧逐帧读成亮度网格，把整条音轨逐样本读出来，然后按判据列 FAIL：

  画面  闪切（相邻帧平均亮度跳变超过阈值）、黑帧/白帧、丢帧导致的时长漂、
        该淡化的边界上是否真的淡了（文字密集的出场刻意硬切，不在此列）、
        以及「这张图到底是不是 compose 刚跑出来的那版底板」
  声音  削波样本、直流偏置、最长静音、口型与字幕错位
        孤立爆音只作诊断量打印（SFX 的合成陡沿本身就是陡沿，且 AAC 让它变少而非变多）
  来源  成片到底是不是本流水线刚造出来的那版底板、那条混音：
        画面逐像素对 compose 的无声底板、音轨对齐 `-mix.wav` 比残差
        ——这两条是 `-c:v copy` 与音频直送 AAC 给的构造恒等式
  交付  响度与 true peak（与 assemble 同一把尺），与 assemble 记在同名 JSON 里；
        音轨残差另按**同位置 10 ms 局部电平**归一再量一次，抓单样本级损坏

只有成片路径被检查，不重算流水线中间件——审计的意义正在于“量成品，不量意图”。
后半句还有更狠的一半：`-c:v copy` 让成片画面逐像素等于底板、音轨逐样本等于混音，
这两件事是构造上的恒等式。拿它们当门，mux 换错底板、拿错音轨就必然现形，
而那几样错了，帧数、响度、闪切门全是绿的。

不是所有判据都能靠恒等式：残差信噪比与残差比的下限只能取“实测值与故障值之间的
中点”，理由写在常量旁。爆音那条连中点都取不了——它按定义分不出编码陡沿余振与
真断点，所以降级成诊断数字。

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

# 成片必须就是流水线造出来的东西：mux 换错底板、拿错音轨、母带增益失准，这三样错了
# 帧数、响度、闪切、爆音门全是绿的——只有把成品和原件逐流比一遍才看得见。
LUMA_TOL = 0.5                        # 逐像素亮度差；`-c:v copy` 实测恒为 0，容差只留给浮点噪声
AAC_TAIL_MAX_S = 0.1                  # AAC 帧尾垫的样本上限（ep02 实测 704 个样本 = 14.7 ms）
GAIN_TOL_DB = 0.5                     # 成片实测增益与母带意图 MASTER_GAIN_DB 的最大偏差
ENCODE_SNR_MIN_DB = 24.0              # 成片对原件的残差信噪比下限（192 kbps AAC 实测 27.9）
# 单样本级损坏：一个 0.5 的毛刺落在安静段，峰值不动、整段信噪比不动（实测 27.89 → 27.89）、
# 直流偏置不动，于是每一道门都是绿的。拿残差和**同位置**的局部电平比才看得见。
# 阈值不贴着实测上限放（那等于按一次观测拟合），放两端分离的中点：
#   正常 AAC 陡沿余振  4.77 倍局部电平（ep02 两画幅同值 @462.5 s）
#   0.5 毛刺           250–514 倍（依注入处安静程度）
# 4.77 与 514 的几何中点是 49.5，取 50。安静段里因此能判到 0.1（−20 dBFS）以上的毛刺，
# 而那正是听得见的量级。floor 的作用与之独立：最静的 10 ms 窗 RMS 只有 9.7e-4，
# 不设下限会把比值放大到 250 倍以上，那是把正常内容判成缺陷。
RESIDUAL_LOCAL_RMS_MAX = 50.0
RESIDUAL_RMS_FLOOR = 2e-3             # 局部 RMS 下限：静段除零，且"静段里的毛刺"仍可判
LOCAL_WINDOW_S = 0.01                 # 局部电平窗（10 ms）


def frame_luma_grid(path: Path) -> NDArray[np.float64]:
    """全片逐帧 16×16 luma 网格。

    必须在 RGB 域缩放：`-vf scale` 之后再 `-pix_fmt gray` 走的是 YUV 灰度平面，
    实测会把纯 INK 底映射成 0、亮字压掉四成，一整集暗色成片被误判成 14% 黑帧。
    `scale=NxN` + `rgb24` 与全分辨率 luma 一致（ep02 竖屏实测 20.21 vs 19.96）。
    返回整张网格而不是只返回均值：均值门看一维序列就够，要判“成片画面是不是底板
    画面”却得逐像素比——一版旧主题底板和一版新底板的平均亮度可能相同，像素分布不同。
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
    return 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]


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


def audit_video(path: Path, expected_frames: int, base: Path,
                fade_edges: set[int] | None = None,
                content_rows: tuple[int, int] | None = None,
                text_edges: dict[int, int] | None = None) -> tuple[list[str], dict[str, float]]:
    """审一条成片。`fade_edges` 是"该做交叉淡化"的边界帧号集合（出场 beat 为 figure 的那些）。
    `content_rows` 是内容区在 16×16 亮度网格里的行区间 [r0, r1)：淡化只混这个区间（上下两条
    带子按设计硬切），所以转场平滑门也只量这个区间——带上字幕/结论带的硬切全帧均值能到 2.2
    （ep03 9x16 帧 5431，出场 figure 结论带三行亮字），越的是门不是淡化。
    `text_edges` 是入场为 PIL 文字版式的过场边界 → 过场末帧号；过场结束后文字不得倒退。"""
    import numpy as np

    fails: list[str] = []
    fade_edges = fade_edges or set()
    text_edges = text_edges or {}
    grid = frame_luma_grid(path)
    luma = grid.mean(axis=(1, 2))
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
    # 转场平滑门**只管该淡化的那批边界**。全片 73 个边界里只有 16 个的出场 beat 是 figure
    # （内容区纯图形、没有 PIL 文字）——文字密集的 layout（card/quiz/checklist/number）
    # 出场时刻意硬切：全帧无差别淡化会把出场与入场的文字叠在一起互相糊（实测 quiz 的选项
    # 与 card 的金色标题在溶解中段各半透明，读起来"糊/廉价"），硬切至少干净。
    # 所以这里只查那批边界，且只量内容区行（`content_rows`）：带子是同一批边界上**刻意**的硬切，
    # 全帧均值会把字幕/结论带的换字算进跳变（ep03 9x16 实测 2.2，出现在淡化完全正常的一帧）。
    # 判定不看固定阈值，看**步长是否摊在 8 帧淡化窗里**：入场文字越亮、与出场图的
    # 对比度越大，单步就越大——满屏大字的 card 淡入，「正常一步」也会到 2–3；真退化
    # 成硬切时全部对比度砸在 1 帧（同一边界会是 ~25）。所以取该边界 8 帧窗内的总
    # 对比度 total：单步 ≤ max(2.0, total/5) 才算摊开了（total/5 < 8×total/8，余量 1.6 倍）；
    # 低对比边界（figure→figure）total≈0，退化为原 2.0 绝对门。
    # 入场文字若在淡化期间还在逐行显形，单步会混入揭示动画——那是 compose 的缺陷
    # （ep04 帧 17014/7851 实测 1.26/1.02 倍），不是门太严：compose 现在把揭示压满
    # REVEAL 窗，淡化期间入场版式是静止的。
    if fade_edges:
        worst_msg, worst_ratio = "", 0.0
        tgrid = grid[:, content_rows[0]:content_rows[1], :] if content_rows else grid
        tluma = tgrid.mean(axis=(1, 2))
        td = np.abs(np.diff(tluma))
        for n in sorted(fade_edges):
            if n < 1 or n + 7 >= td.shape[0]:
                continue
            total = abs(float(tluma[n + 7] - tluma[n - 1]))
            step = float(np.max(td[n - 1: n + 7]))
            ratio = step / max(total / 5, 2.0)
            if ratio > worst_ratio:
                worst_ratio = ratio
                worst_msg = (f"第 {n} 帧（该淡化的边界）单帧跳变 {step:.1f}，8 帧窗总对比 "
                             f"{total:.1f}——跳变没摊开到 8 帧，交叉淡化没生效，退化成硬切")
        if worst_ratio > 1.0:
            fails.append(worst_msg)
    # 过场（段过场 6 帧 / 内容交叉淡化 8 帧）结束后，入场文字不得倒退。compose 曾把
    # 揭示压到 1.0 只压过场那几帧，过场一结束 p 跌回 i/REVEAL，已显形的行退回半透明
    # 再重放一遍（实测 ep01 帧 4669 内容区亮度 32.0→27.8，每个段边界都有一下）。
    # 只查入场为 card/number 的边界：figure 是录像，本身亮度就会呼吸，掉几个点不算倒退。
    if text_edges:
        tgrid = grid[:, content_rows[0]:content_rows[1], :] if content_rows else grid
        tluma = tgrid.mean(axis=(1, 2))
        for n, end in sorted(text_edges.items()):
            if end + 7 >= tluma.shape[0]:
                continue
            ref = float(tluma[end])
            low = float(np.min(tluma[end + 1:end + 8]))
            if ref - low > 1.5:
                fails.append(f"第 {n} 帧过场后入场文字倒退：过场末帧内容区亮度 {ref:.1f}，"
                             f"随后 7 帧最低 {low:.1f}——文字从全显退回半透明再重放")
    if dark > DARK_FRAME_MAX:
        fails.append(f"黑帧占比 {dark * 100:.2f}%")
    if bright > BRIGHT_FRAME_MAX:
        fails.append(f"白帧占比 {bright * 100:.2f}%")

    # 画面是不是 compose 那版底板：帧数、闪切、黑白帧都只看自己，mux 换错底板照样全绿。
    bgrid = frame_luma_grid(base)
    diff = 0.0
    if bgrid.shape[0] != grid.shape[0]:
        fails.append(f"成片 {grid.shape[0]} 帧 ≠ 底板 {bgrid.shape[0]} 帧——mux 的不是 compose 那版底板")
    else:
        dd = np.abs(grid - bgrid)
        diff = float(np.max(dd))
        bad = int(np.count_nonzero(dd.max(axis=(1, 2)) > LUMA_TOL))
        if bad:
            first = int(np.argmax(dd.max(axis=(1, 2)) > LUMA_TOL))
            fails.append(f"{bad} 帧画面与底板不符（最大差 {diff:.1f}，首见第 {first} 帧）"
                         "——mux 进去的可能不是 compose 刚跑出来的那版底板")
    stats = {"frames": float(luma.shape[0]), "flash_ratio": flash_ratio,
             "dark_ratio": dark, "bright_ratio": bright, "max_dl": float(np.max(d)),
             "grid_diff": diff}
    print(f"  画面 {frames} 帧：闪切 {flash_ratio * 100:.3f}% / 黑 {dark * 100:.3f}% / "
          f"白 {bright * 100:.3f}% / 最大跳变 {float(np.max(d)):.1f} / 逐帧贴合底板差 {diff:.2f}")
    return fails, stats


def _click_positions(a: NDArray[np.float32]) -> NDArray:
    """孤立爆音的样本下标：左右两侧相邻样本差都超过 CLICK_DELTA 的点。

    单侧大跳变不算——语音起句、SFX 起振本来就沿一侧冲上去；咔哒声的指纹是
    "上得去也下得来"，即同一小段内两次反向跳变。
    """
    import numpy as np

    d = np.abs(np.diff(a))
    jump = d > CLICK_DELTA
    if jump.shape[0] < 2:
        return np.zeros(0, dtype=int)
    return (np.flatnonzero(jump[1:] & jump[:-1]) + 1).astype(int)


def audit_provenance(path: Path, slug: str) -> tuple[list[str], dict[str, float]]:
    """成片音轨对得上混音原件吗？

    前面的判据（削波、直流、静音、响度）都只看成品自己。mux 拿错音轨、母带增益失准、
    AAC 把内容打坏，帧数门和响度门依然是绿的——只有把成品和原件对齐了比残差才看得见。
    增益不写死而是实测最佳拟合：意图变了门自动跟；偏差超过容差才算故障。
    """
    import numpy as np
    from assemble import master_gain_db

    intended_gain_db = master_gain_db(slug)

    fails: list[str] = []
    x = audio_mono(path)
    src = _source_mono(slug)
    sr = common.SAMPLE_RATE
    tail = (x.shape[0] - src.shape[0]) / sr
    if tail < -1.0 / sr:
        fails.append(f"音轨比混音原件短 {-tail:.3f} s——封装时音频被截，尾部会没声")
    elif tail > AAC_TAIL_MAX_S:
        fails.append(f"音轨比混音原件长 {tail:.3f} s > {AAC_TAIL_MAX_S} s，音画长度对不上")

    n = min(x.shape[0], src.shape[0])
    a = x[:n].astype("float64")
    b = src[:n].astype("float64")
    denom = float(np.sum(b * b))
    gain = float(np.sum(a * b) / denom) if denom > 0 else 0.0
    gain_db = 20.0 * float(np.log10(gain)) if gain > 0 else -99.0
    res = a - gain * b
    e_a = float(np.sum(a * a))
    e_r = float(np.sum(res * res))
    snr = 10.0 * float(np.log10(e_a / e_r)) if e_r > 0 else 99.0
    worst_at = int(np.argmax(np.abs(res))) / sr

    # 单样本级损坏：毛刺不推高峰值、几乎不动整段信噪比（实测 0.5 的毛刺让 SNR 停在 27.89），
    # 于是上面几道门全盲。判据换成"残差 ÷ 同位置局部电平"——AAC 陡沿余振实测最大 4.77，
    # 毛刺在安静段是 250–514，阈值取两端的几何中点 50。
    fl = int(LOCAL_WINDOW_S * sr)
    m = min(a.shape[0], b.shape[0]) // fl
    loc = np.repeat(np.sqrt(np.mean(b[: m * fl].reshape(m, fl) ** 2, axis=1)), fl)
    ratio = np.abs(res[: m * fl]) / np.maximum(loc, RESIDUAL_RMS_FLOOR)
    peak_ratio = float(np.max(ratio))
    ratio_at = int(np.argmax(ratio)) / sr
    # 帧尾垫的那 704 个样本没有原件可比，长度已有门；内容只作诊断（实测恒为数字静音，
    # 峰值 0.000000），混音末段本身只有 0.005 峰值，设内容阈值只能拍。已验证这个数字
    # 会动：同相灌 0.4 进去，尾段峰值 0.423614（AAC 过冲）。
    #
    # 注意它是单声道口径，`audio_mono` 做 0.5*(L+R)，所以**反相**内容会被降混抵消从而
    # 看不见——这是量测口径的固有边界，不是这个诊断量的缺陷。整条单声道反相也不会让 mono
    # 归零（反相件实测 mono 峰值 0.4050：AAC 之后 L≠R，抵消不干净），而是让 mono 与混音原件
    # 去相关，于是增益拟合 −99 dB、残差信噪比 0.0 dB，静音门同时报 5.43 s > 1.2 s。
    # 漏得出去的只有"部分反相"，而本流水线没有任何一步能产生它
    # （mix 写的是 `np.stack([mixy, mixy], 1)`，双单声道；成品里实测 L−R 中位 0、
    # 99 分位 0.0046，最大 0.343，那是 AAC 去相关）。
    tail_peak = float(np.max(np.abs(x[n:]))) if x.shape[0] > n else 0.0

    if abs(gain_db - intended_gain_db) > GAIN_TOL_DB:
        fails.append(f"成片增益 {gain_db:.2f} dB，母带意图 {intended_gain_db} dB，"
                     f"偏差 {abs(gain_db - intended_gain_db):.2f} dB > {GAIN_TOL_DB} dB")
    if snr < ENCODE_SNR_MIN_DB:
        fails.append(f"成片对原件的残差信噪比 {snr:.1f} dB < {ENCODE_SNR_MIN_DB} dB——编码把内容打坏了")
    if peak_ratio > RESIDUAL_LOCAL_RMS_MAX:
        fails.append(f"单点残差达局部电平的 {peak_ratio:.1f} 倍（{ratio_at:.1f} s 处，"
                     f"上限 {RESIDUAL_LOCAL_RMS_MAX}）——峰值与整段信噪比都照旧绿，只有这一道看得见")
    print(f"  贴合原件：最佳增益 {gain_db:.3f} dB（意图 {intended_gain_db}）/ 残差信噪比 {snr:.1f} dB / "
          f"单点残差最大 {peak_ratio:.2f} 倍局部电平（{ratio_at:.1f} s）/ 音轨尾差 {tail * 1000:+.0f} ms"
          f"（尾段峰值 {tail_peak:.6f}）/ 最大残差在 {worst_at:.1f} s")
    return fails, {"gain_db": gain_db, "encode_snr": snr, "tail_s": tail,
                   "peak_residual_ratio": peak_ratio, "tail_peak": tail_peak}


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

    # 爆音计数只作诊断，不作门。两道门都试过，都立不住：
    #  · 原判据是「超过音源两倍加 200」——AAC 把陡沿抹平，成品爆音只会比原件少
    #    （ep02：原件 4790 → 成品 215），预算 9780 基本不可能触及，等于没有门。
    #  · 改成「只数音源里没有的新增爆音」（实测 49 处）有了判据价值，但上限只能拍
    #    （49 的四倍），而且它抓的东西——编码在陡沿上的余振——已被残差比门按幅度
    #    量过一遍：那 49 处的残差只有局部电平的百分之几，是设计内的编码行为。
    # 残差比门才是真正的守卫，这里留下数字给维护者看趋势。
    src = _source_mono(slug)
    ci = _click_positions(x)
    si = _click_positions(src)
    clicks = int(ci.shape[0])
    src_clicks = int(si.shape[0])
    shifted = np.concatenate([si + k for k in range(-2, 3)]) if si.shape[0] else si
    new_clicks = int(np.count_nonzero(~np.isin(ci, shifted)))

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
    print(f"  声音 {n / sr:.1f} s：削波 {clipped} / 直流 {dc:.5f} / 孤立爆音 {clicks}"
          f"（音源 {src_clicks}，其中音源里没有的新增 {new_clicks}，均只作诊断）"
          f"/ 最长静音 {longest_s:.2f} s / 峰值 {peak:.4f} / 口型迟到 {len(late)} 条")
    return fails, {"peak": peak, "longest_silence": longest_s, "clicks": float(clicks),
                   "clipped": float(clipped), "new_clicks": float(new_clicks)}


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


# 与 README 出片人检的排布约定一致：横屏 4×5、竖屏 5×5。
CONTACT_COLS = {"16x9": 4, "9x16": 5}
CONTACT_CELL = {"16x9": (460, 259), "9x16": (200, 356)}
CONTACT_CAPTION_H = 46          # 两行：id/layout/时间 + 段名（竖屏 200 px 宽塞不下单行全标注）
CONTACT_CAP_FONT = 15


def _clip_label(s: str, font, width: float) -> str:
    """标注超格宽就逐字截到加得下省略号为止。"""
    if font.getlength(s) <= width:
        return s
    while s and font.getlength(s + "…") > width:
        s = s[:-1]
    return s + "…" if s else ""


def contact_sheet(slug: str, aspect: str) -> list[Path]:
    """每个 beat 中点抽一帧拼审片格，一图集覆盖全片，供出片后人工过目。

    工具门量出来的都是统计量：断行断在词中间、chroma bleed 色带这类"只有人眼
    看得见"的缺陷，全片 audit 绿也会漏（ep02 两例都是这么发现的）。README 因此
    要求出片后给每个 beat 抽中点拼格——靠人记换一集就漏，做成一条命令才落得了地。
    画面取无声底板：`-c:v copy` 下它与成片逐像素相同（audit 的构造恒等式），
    又少一条音频流，解码快得多。
    """
    from PIL import Image, ImageDraw

    tl = spec_mod.timeline(slug)
    base = common.EPISODES / slug / f"{slug}-{aspect}-video.mp4"
    if not base.exists():
        raise FileNotFoundError(f"没有无声底板 {common.rel(base)}（先跑 compose.py）")
    total = int(round(tl["duration"] * common.FPS))
    marks = []
    for e in tl["beats"]:
        n = min(max(int(round((e["start"] + e["dur"] / 2) * common.FPS)), 0), total - 1)
        marks.append((n, e))
    sel = "+".join(f"eq(n\\,{n})" for n, _e in marks)
    tmp = common.WORK / "tmp" / f"contact-{slug}-{aspect}"
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        common.ff("-loglevel", "error", "-i", str(base),
                  "-vf", f"select={sel}", "-vsync", "0",
                  "-f", "image2", str(tmp / "c%04d.png"))
        frames = sorted(tmp.glob("c*.png"))
        if len(frames) != len(marks):
            raise RuntimeError(f"审片格抽帧数 {len(frames)} ≠ beat 数 {len(marks)}")
        cols = CONTACT_COLS[aspect]
        cw, ch = CONTACT_CELL[aspect]
        cap_h = CONTACT_CAPTION_H
        cell_w, cell_h = cw, ch + cap_h
        pad = 20
        rows = 5
        per = cols * rows
        f_cap = common.font("text", CONTACT_CAP_FONT)
        pages: list[Path] = []
        pairs = list(zip(frames, (e for _n, e in marks), strict=True))
        for p0 in range(0, len(pairs), per):
            chunk = pairs[p0:p0 + per]
            rows_n = (len(chunk) + cols - 1) // cols
            W = cols * cell_w + (cols + 1) * pad
            H = rows_n * cell_h + (rows_n + 1) * pad
            sheet = Image.new("RGB", (W, H), (10, 12, 16))
            d = ImageDraw.Draw(sheet)
            for k, (fp, e) in enumerate(chunk):
                r, c = divmod(k, cols)
                x = pad + c * (cell_w + pad)
                y = pad + r * (cell_h + pad)
                im = Image.open(fp).resize((cw, ch), Image.LANCZOS)
                sheet.paste(im, (x, y))
                mm, ss = int(e["start"] // 60), int(e["start"] % 60)
                d.text((x + 2, y + ch + 3),
                       f"{e['id']}  {e['layout']}  {mm:02d}:{ss:02d}",
                       font=f_cap, fill=(200, 208, 216))
                d.text((x + 2, y + ch + 24), _clip_label(e["seg_title"], f_cap, cell_w - 8),
                       font=f_cap, fill=(150, 158, 166))
                d.rectangle([x, y, x + cell_w - 1, y + cell_h - 1], outline=(48, 54, 61))
            out = common.ROOT / ".local" / f"contact-{slug}-{aspect}-p{p0 // per + 1}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            sheet.save(out)
            pages.append(out)
        return pages
    finally:
        for f in tmp.glob("*.png"):
            f.unlink()
        try:
            tmp.rmdir()
        except OSError:
            pass


def audit(slug: str, aspect: str) -> int:
    tl = spec_mod.timeline(slug)
    path = common.OUT / f"{slug}-{aspect}.mp4"
    if not path.exists():
        print(f"还没有成片：{common.rel(path)}（先跑 assemble.py）")
        return 1
    base = common.EPISODES / tl["slug"] / f"{tl['slug']}-{aspect}-video.mp4"
    if not base.exists():
        print(f"没有无声底板 {common.rel(base)}：先跑 compose.py --episode {slug}")
        return 1
    meta_p = path.with_suffix(".json")
    meta = common.load_json(meta_p) or {}
    # 该做交叉淡化的边界 = 出场 beat 为 figure 的那些，且**不是段边界**（段边界走过场，
    # 不用内容淡化——一次边界一种处理；两者叠加实测把跳变顶到 2.4–3.0）。
    # 与 compose.render 的判据同一套：那边只在这些边界淡内容，这边只在这些边界查。
    seg_starts = {int(round(tl["beats"][j]["start"] * common.FPS))
                  for j in range(1, len(tl["beats"]))
                  if tl["beats"][j]["seg_title"] != tl["beats"][j - 1]["seg_title"]}
    fade_edges = {int(round(tl["beats"][i]["end"] * common.FPS))
                  for i in range(len(tl["beats"]) - 1)
                  if tl["beats"][i]["layout"] == "figure"
                  and int(round(tl["beats"][i + 1]["start"] * common.FPS)) not in seg_starts}
    # 入场为 card/number 的过场边界 → 过场末帧（段过场入场侧 6 帧 = compose.SEG_DIP_FRAMES，
    # 内容交叉淡化 8 帧 = compose.XFADE_FRAMES）。这些边界结束后文字必须保持全显。
    text_edges: dict[int, int] = {}
    for i in range(len(tl["beats"]) - 1):
        nxt = tl["beats"][i + 1]
        n = int(round(nxt["start"] * common.FPS))
        if nxt["layout"] not in {"card", "number"}:
            continue
        if n in seg_starts:
            text_edges[n] = n + 5
        elif tl["beats"][i]["layout"] == "figure":
            text_edges[n] = n + 7
    geo = common.ASPECTS[aspect]
    r0 = int(round(geo.top / geo.h * 16))
    r1 = int(round((geo.h - geo.bottom) / geo.h * 16))
    vfails, vstats = audit_video(path, int(round(tl["duration"] * common.FPS)), base, fade_edges,
                                 (r0, r1), text_edges)
    afails, astats = audit_audio(path, slug)
    pfails, pstats = audit_provenance(path, slug)
    fails = vfails + afails + pfails
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
    ap.add_argument("--contact-sheet", action="store_true",
                    help="每个 beat 中点抽帧拼审片格（出片后人工过目用），不跑审计")
    a = ap.parse_args()
    if a.contact_sheet:
        for aspect in (list(common.ASPECTS) if a.both else [a.aspect or "16x9"]):
            pages = contact_sheet(a.episode, aspect)
            for p in pages:
                print(f"  {aspect} 审片格（{len(pages)} 页之 {p.stem.rsplit('-p', 1)[-1]}）→ {common.rel(p)}")
        return 0
    rc = 0
    for aspect in (list(common.ASPECTS) if a.both else [a.aspect or "16x9"]):
        rc |= audit(a.episode, aspect)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
