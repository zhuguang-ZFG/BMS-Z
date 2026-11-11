"""场景布局只约束内容区域，不把所有动画变成相同模板。"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    width: float
    height: float


def split_columns(width, height, ratio=.5, margin=48, gutter=40):
    if not 0 < ratio < 1 or width <= 2 * margin + gutter or height <= 220:
        raise ValueError('画布或分栏比例不合法')
    usable = width - 2 * margin - gutter
    left = usable * ratio
    return (Box(margin, 100, left, height - 220),
            Box(margin + left + gutter, 100, usable - left, height - 220))


def equation_rows(box, count, spacing=86):
    if count < 1 or spacing * count > box.height:
        raise ValueError('公式行超出内容区')
    return [(box.x + 16, box.y + (index + 1) * spacing) for index in range(count)]
