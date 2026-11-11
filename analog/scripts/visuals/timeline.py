#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V2 动画最薄时间轴层：命名节拍与透明度窗口。

spec §7.5 禁令下不扩 generate_svgs.py；本层只描述「什么时候出现、
什么时候退场」，几何与文案全部在 scenes/chXX_*.py 里。

节拍规则（spec §7.3）：开场 1 秒内入题；每拍唯一主角；结论拍停留
（hold=True 且排在最后）；动画默认播放一次不循环（所有 SMIL fill=freeze）。
"""
from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Beat:
    name: str          # 短节拍名（storyboard 格标题 + desc 记录）
    start: float       # 秒
    end: float         # 秒
    caption: str       # 底部字幕条文本（该拍讲一句话）
    color: str = "#1f5d7a"
    hold: bool = False  # 结论拍：不退场，且 final 帧保留


@dataclass(frozen=True)
class Timeline:
    width: int
    height: int
    duration: float
    beats: tuple[Beat, ...]
    title: str
    subtitle: str = ""

    def __post_init__(self):
        if self.width <= 0 or self.height <= 0 or not math.isfinite(self.duration) or self.duration <= 0:
            raise ValueError("画布尺寸与时长必须为正数")
        if not 4 <= len(self.beats) <= 7:
            raise ValueError("每个动画须有 4–7 个命名节拍")
        names = set()
        end = 0.0
        for beat in self.beats:
            if not beat.name or beat.name in names:
                raise ValueError("节拍名称不能为空或重复")
            if not math.isclose(beat.start, end) or not beat.start < beat.end <= self.duration:
                raise ValueError("节拍必须连续覆盖时间轴")
            names.add(beat.name)
            end = beat.end
        if not math.isclose(end, self.duration) or not self.beats[-1].hold:
            raise ValueError("末拍须停留并覆盖完整时长")

    def beat(self, name: str) -> Beat:
        for b in self.beats:
            if b.name == name:
                return b
        raise KeyError(name)

    def in_window(self, name: str, t: float) -> bool:
        b = self.beat(name)
        return b.start <= t < b.end or (b is self.beats[-1] and t == self.duration)


def opacity_window(timeline: Timeline, beat: Beat) -> tuple[float, float | None]:
    """(入场秒, 退场秒|None)。hold 拍与最后一个拍不退场。"""
    is_last = beat is timeline.beats[-1]
    if beat.hold or is_last:
        return beat.start, None
    return beat.start, beat.end


def fade_in(begin: float, dur: float = 0.45) -> str:
    """入场 animate：opacity 0→1，spline 非线性缓动，单次播放。"""
    return (f'<animate attributeName="opacity" values="0;1" keyTimes="0;1" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1" '
            f'begin="{begin:g}s" dur="{dur:g}s" fill="freeze"/>')


def fade_out(begin: float, dur: float = 0.4) -> str:
    """退场 animate：后触发者覆盖先前的 freeze 值。"""
    return (f'<animate attributeName="opacity" values="1;0" keyTimes="0;1" '
            f'calcMode="spline" keySplines="0.4 0 0.6 1" '
            f'begin="{begin:g}s" dur="{dur:g}s" fill="freeze"/>')


def drift(begin: float, dx: float, dy: float, dur: float = 0.6) -> str:
    """主角第二层运动：轻位移。scene 把它贴进拍组内。"""
    return (f'<animateTransform attributeName="transform" type="translate" '
            f'from="0 0" to="{dx:g} {dy:g}" begin="{begin:g}s" '
            f'dur="{dur:g}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1" keyTimes="0;1"/>')
