"""A shared, offline-first worked example for the collection's PDF and EPUB."""

from __future__ import annotations

from decimal import Decimal
from html import escape

from combined_front import text, xhtml

LAB_TITLE = "三次观察，一张手记"
MODEL = "纸面模型：U = Uoc − I × R0，Uoc = 3.70 V，R0 = 20 mΩ。只计算瞬时欧姆压降，忽略极化、温度与容量变化。放电电流取正值。"
OBSERVATIONS = [("01 静置", 0), ("02 接入负载", 20), ("03 撤去负载", 0)]
INTRO = "这是一组教学读数。先看同一颗电芯的三个时刻，最后一次是模型预测。"
PROMPT = "带载时少掉的 0.40 V 去了哪里？撤载后，电芯真的重新充电了吗？"
EXPLANATION = "带载时的欧姆压降为 20 A × 20 mΩ = 0.40 V；撤载后，I × R0 项归零。模型解释了读数为什么回升，但没有描述电芯容量的变化。"
QUESTIONS = [
    ("换一个电流", "其他条件不变，10 A、30 A 时各读到多少伏？先写预测，再代入公式。"),
    ("追问这次回升", "撤去负载后，模型电压回到 3.70 V。这能证明刚才用掉的电量又回来了吗？"),
    ("只剩一个读数", "另一颗电芯也读到 3.30 V，但电流、内阻和开路电压都未知。能直接判断它与图中电芯的 SOC 相同吗？"),
]
ANSWERS = [
    ("1 / 复算", "10 A：3.70 − 10 × 0.020 = 3.50 V；30 A：3.70 − 30 × 0.020 = 3.10 V。\n单位先统一：20 mΩ = 0.020 Ω。"),
    ("2 / 回升的含义", "不能。这次回升来自 I × R0 项归零；本模型没有描述容量变化。它不意味着电芯被充电，也不能给出真实电芯的恢复曲线。"),
    ("3 / 证据还不够", "不能。一个端电压无法分开未知的 Uoc、I 和 R0，更不能单独确定 SOC。继续读卷二第 10 章，区分端电压、开路电压与状态估计。"),
]


def voltage(amps: int) -> str:
    return f"{Decimal('3.70') - Decimal(amps) * Decimal('0.020'):.2f}"


def lab_xhtml() -> bytes:
    observations = "".join(
        f'<li><h3>{escape(label)}</h3><p>I = {amps} A → <strong>{voltage(amps)} V</strong></p></li>'
        for label, amps in OBSERVATIONS
    )
    questions = "".join(
        f'<li><h3>{escape(title)}</h3><p>{escape(body)}</p></li>'
        for title, body in QUESTIONS
    )
    answers = "".join(
        f'<h3>{escape(title)}</h3><p>{escape(body)}</p>' for title, body in ANSWERS
    )
    return xhtml(
        LAB_TITLE,
        f'<h1>{LAB_TITLE}</h1><p>{escape(INTRO)}</p>'
        f'<ol>{observations}</ol>'
        f'<h2>先猜，再看公式</h2><p>{escape(PROMPT)}</p>'
        '<p>我的手记：预测 ______；还缺的读数或条件 ______。</p>'
        f'<h2>用一个简单模型复算</h2><p>{escape(MODEL)}</p>'
        f'<p>{escape(EXPLANATION)}</p>'
        f'<h2>换个条件，自己复算</h2><ol>{questions}</ol>'
        '<p>我的手记：预测 ______；计算 ______；仍缺少的证据 ______。</p>'
        f'<hr/><h2>写完再看：对照解</h2>{answers}',
    )


def lab_page(doc):
    page = doc.new_page(width=595.28, height=841.89)
    teal, ink, rust = (0.09, 0.42, 0.4), (0.12, 0.22, 0.25), (0.72, 0.31, 0.13)
    text(page, "从模拟电路到 BMS / 纸面小实验", 48, 45, 10, teal)
    text(page, LAB_TITLE, 48, 92, 25)
    text(page, INTRO, 48, 120, 10.5, width=495)
    for index, (label, amps) in enumerate(OBSERVATIONS):
        x = 48 + index * 172
        text(page, label, x, 155, 11, teal)
        page.draw_polyline(
            [(x, 171), (x + 146, 169), (x + 148, 235), (x - 1, 237), (x, 171)],
            color=ink, width=1.2, fill=(0.96, 0.97, 0.93),
        )
        text(page, f"{voltage(amps)} V", x + 20, 207, 23)
        text(page, f"I = {amps} A", x + 20, 226, 10)
        if index < 2:
            page.draw_polyline([(x + 154, 198), (x + 166, 198), (x + 162, 194)], color=rust, width=1.2)
    y = text(page, "箭头表示观察先后。先猜，再看公式。", 48, 259, 10) + 3
    y = text(page, PROMPT, 48, y, 11, rust, width=495) + 8
    y = text(page, "我的手记：预测 ______；还缺的读数或条件 ______。", 48, y, 10) + 12
    y = text(page, "用一个简单模型复算", 48, y, 15, teal) + 6
    y = text(page, MODEL, 48, y, 10.5, width=495) + 5
    y = text(page, EXPLANATION, 48, y, 10, width=495) + 12
    y = text(page, "换个条件，自己复算", 48, y, 15, teal) + 6
    for i, (heading, body) in enumerate(QUESTIONS, 1):
        y = text(page, f"{i}. {heading}：{body}", 48, y, 11, width=495) + 7
    y = text(page, "我的手记：预测 __________；计算 __________；缺少的证据 __________。", 48, y + 3, 10) + 18
    page.draw_line((48, y), (547, y), color=teal, width=0.8)
    y = text(page, "写完再看：对照解", 48, y + 24, 14, teal) + 7
    for heading, body in ANSWERS:
        y = text(page, f"{heading}　{body}", 48, y, 10.5, width=495) + 8
    if y > 805:
        raise ValueError(f"纸面实验页溢出: {y}")
    return page
