"""V2 语义 token；现役配色与已批准色族分开，风格迁移必须逐图审查。"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    paper: str
    ink: str
    muted: str
    accent: str
    rule: str


CURRENT = Palette('#f6eedb', '#16202b', '#5b666f', '#a4630f', '#c9bb9d')
# 2026-11-05 上游色卡中位像素；来源与哈希见 handraw-style-lock.md。
APPROVED = Palette('#e2d9cf', '#2a2927', '#535453', '#a4441d', '#535453')
INK, MUTED, ACCENT, PAPER, RULE = CURRENT.ink, CURRENT.muted, CURRENT.accent, CURRENT.paper, CURRENT.rule
EASE_IN_OUT = '0.4 0 0.2 1'
MIN_PRINT_PT = 8.5
BODY_SIZE = 32
TITLE_SIZE = 44
