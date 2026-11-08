"""Source-bound, zero-number conceptual illustrations for the BMS book.

The 36 archived Chinese prompts remain the content source; the S2 illustration
adds one new concept. All quantitative values stay in code-generated SVGs.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "bms-book" / "ILLUSTRATION-PROMPTS.md"
REFERENCE = Path(os.environ.get(
    "BMS_HANDDRAW_REFERENCE",
    str(ROOT / "bms-book/illustrations/handdraw/style-reference.png"),
))

STYLE_ZH = (
    "原创工程教科书手绘，暖象牙纸、深墨轮廓、普鲁士蓝结构线，少量青绿与赭黄平涂。"
    "细钢笔线条带自然起落，稀疏排线表现厚度，清晰轮廓与大片留白。"
    "出现人物时使用原创成年工程师的极简几何形象，表情克制；不模仿任何具体作者。"
)
ISOLATION_ZH = (
    "所附图片仅用于参考画风。只提取参考图的风格特征，例如线条、笔触、媒介、材质、"
    "色彩倾向和整体视觉语言；不要使用、复制或延续参考图中的任何主体、人物、动物、"
    "服装、道具、动作、姿态、场景、背景、构图、布局、文字或故事。"
    "最终画面内容完全以用户提供的主题为准。"
)
ZERO_DIGITS_ZH = "画面中不出现任何文字、数字、刻度值或字母，只有图形。"


@dataclass(frozen=True)
class Asset:
    key: str
    prompt: str
    target: str
    canvas: tuple[int, int] = (1536, 896)
    size: str = "1536x1024"


def _chinese_prompt(section: str) -> str:
    match = re.search(r"\*\*中文\*\*\s*```\s*\n(.*?)```", section, re.DOTALL)
    if match is None:
        raise ValueError("archived illustration has no Chinese prompt")
    return match.group(1).strip()


def _original_style_prompt(section: str) -> str:
    archived = _chinese_prompt(section)
    _, separator, scene = archived.partition("画面要求：")
    if not separator:
        raise ValueError("archived illustration has no scene contract")
    return STYLE_ZH + "画面要求：" + scene + ZERO_DIGITS_ZH + ISOLATION_ZH


def archived_assets() -> dict[str, Asset]:
    source = ARCHIVE.read_text(encoding="utf-8")
    assets = {}
    headers = (
        ("1. 封面", "cover", "docs/public/illustrations/book-cover.webp", (1536, 1152)),
        ("2. 第 1 章章首", "01-cell-workshop", "bms-book/assets/concepts/01-cell-workshop.webp", (1536, 896)),
        ("3. 第 7 章章首", "07-tick-guard", "bms-book/assets/concepts/07-tick-guard.webp", (1536, 896)),
    )
    for heading, key, target, canvas in headers:
        section = source.split("## " + heading, 1)[1].split("\n## ", 1)[0]
        prompt = _original_style_prompt(section)
        assets[key] = Asset(key, prompt, target, canvas)
    stages = re.split(r"^#### (s[0-7]-[a-z0-9-]+)[^\n]*\n", source, flags=re.MULTILINE)
    for index in range(1, len(stages), 2):
        key, section = stages[index:index + 2]
        if key in assets:
            raise ValueError(f"duplicate archived illustration: {key}")
        prompt = _original_style_prompt(section)
        assets[key] = Asset(key, prompt, f"docs/stages/assets/{key}.webp")
    if len(assets) != 36:
        raise ValueError(f"expected the 36 archived illustrations, found {len(assets)}")
    return assets


S2_HERO = Asset(
    key="s2-hero",
    target="bms-book/engineering/assets/s2-model/S2-handdrawn-intro.webp",
    prompt=(
        STYLE_ZH
        + "画面要求：暖象牙纸底。一条很长的纸带从画面左侧悬垂到右侧，纸带上用一根粗线"
        "画出一条先陡降、再缓缓回升的曲线；纸带中段被一只小小的手捏住，手指正好压在"
        "拐点上。纸带下方并排放着两只外形完全相同的不透明圆柱电芯。每只电芯旁各立一张"
        "库存状态卡，卡上只画长短不同的色条，作为不可见内部状态的隐喻；电芯内部不画液位。"
        "一只原创成年工程师的极简几何人物蹲在纸带右端，举着一枚放大镜对准末端几乎平直的一段；"
        "另一只小人站在两只电芯之间，双手各指向一只，表情冷面。"
        + ZERO_DIGITS_ZH
        + ISOLATION_ZH
    ),
)
ASSETS = archived_assets()
ASSETS[S2_HERO.key] = S2_HERO
