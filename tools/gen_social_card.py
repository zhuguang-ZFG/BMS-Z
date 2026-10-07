#!/usr/bin/env python3
"""重画 GitHub 社交卡 docs/circuits/assets/bms-roadmap-social.png。

运行（仓库根目录）：

    python3 tools/gen_social_card.py            # 覆盖入库的社交卡
    python3 tools/gen_social_card.py --out DIR  # 只写到 DIR，供本地「生成图对账」

为什么要生成器：这张图原先是手工做的位图，仓库里没有源。动画从 147 涨到 148 时，
README、门户 HTML、路线图 SVG 都跟着改了，只有它还在写 147——而它是分享出去最先被
看到的一张。现在图上的三个数（教程篇数、动画张数、配套包数）都从仓库现算，
和 check_docs.py 数的是同一批文件，没有手抄的空间。

版式（配色、字号、坐标）是照着上一版量出来的，不是新设计。中文字体走系统里的
Noto Sans SC，只在本地跑——CI 没有这块字体，也不跑这道门（理由同生成图对账）。
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "circuits" / "assets"
OUT = ASSETS / "bms-roadmap-social.png"

W, H = 1280, 640

BG_TOP = (0x0B, 0x4F, 0x6B)
BG_BOTTOM = (0x0E, 0x5D, 0x5C)
ACCENT = "#ccfbf1"
WHITE = "#ffffff"
CARD = "#f8f8f9"
TEAL = "#0f766e"
INK = "#0f172a"
MUTED = "#334155"

FONT_DIRS = (Path("C:/Windows/Fonts"), Path("/usr/share/fonts"), Path("/Library/Fonts"))
FONTS = {
    "regular": ("Noto Sans SC (TrueType).otf", "NotoSansSC-Regular.otf"),
    "bold": ("Noto Sans SC Bold (TrueType).otf", "NotoSansSC-Bold.otf"),
}


def load_font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    for name in FONTS[weight]:
        for d in FONT_DIRS:
            p = d / name
            if p.exists():
                return ImageFont.truetype(str(p), size)
    raise SystemExit(
        f"FAIL: 找不到中文字体 {FONTS[weight]}。这张图只在本地生成，"
        "需要系统装有 Noto Sans SC。"
    )


def counts() -> tuple[int, int, int]:
    """图上三个数字的唯一来源：教程篇数、动画张数、配套包数。"""
    stages = len(list((ROOT / "docs" / "stages").glob("stage-*.md")))
    svgs = len(list(ASSETS.glob("*.svg")))
    code = len(
        [
            p
            for p in (ROOT / "code").iterdir()
            if p.is_dir() and not p.name.startswith((".", "_"))
        ]
    )
    return stages, svgs, code


STAGES = [
    ("0", "前置知识", "懂了电池，保护规则你能自己推出来。"),
    ("1", "认识 BMS", "一节变成一串：木桶、五大功能、五大保护。"),
    ("2", "保护板", "保护板怎么接。短路不要用真电池。"),
    ("3", "AFE + MCU", "AFE 巡逻采样，MCU 状态机守住保护。"),
    ("4", "SOC / SOH", "「还剩百分之几」来自积分、开路电压和卡尔曼。"),
    ("5", "通信", "开口说话：UART、Modbus、CAN、BLE。"),
    ("6", "毕业", "做成产品：高压、安全、可生产、可维护。"),
]


def gradient() -> Image.Image:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        draw.line(
            (0, y, W, y),
            fill=tuple(
                round(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM, strict=True)
            ),
        )
    return img


def draw_text(draw, xy, text, font, fill):
    """把 (x, y) 当视觉顶边用：em 框在字形上方有一段空白，不减掉会整体下坠。"""
    x, y = xy
    draw.text((x, y - font.getbbox(text)[1]), text, font=font, fill=fill)


def fit_font(draw, text, weight, size, limit):
    """胶囊宽度是量出来的死数，标签长一个字就得缩一号，不然会溢出到背景上。"""
    while size > 12:
        font = load_font(weight, size)
        if draw.textlength(text, font=font) <= limit:
            return font
        size -= 2
    return font


def main() -> int:
    out_dir = None
    if "--out" in sys.argv:
        out_dir = Path(sys.argv[sys.argv.index("--out") + 1])
        out_dir.mkdir(parents=True, exist_ok=True)

    n_stages, n_svgs, n_code = counts()
    img = gradient()
    draw = ImageDraw.Draw(img)

    f_top = load_font("regular", 28)
    f_title = load_font("bold", 76)
    f_sub = load_font("regular", 36)
    f_num = load_font("bold", 56)
    f_line = load_font("regular", 28)
    f_head = load_font("bold", 30)
    f_stage = load_font("bold", 26)
    f_desc = load_font("regular", 20)
    f_badge = load_font("bold", 22)

    draw_text(draw, (58, 58), "中文免费 · 从入门到产品级", f_top, ACCENT)
    draw_text(draw, (58, 118), "BMS 学习路线", f_title, WHITE)
    draw_text(draw, (58, 200), f"{n_stages} 教程 × {n_svgs} 动画", f_sub, ACCENT)

    for i, (num, label) in enumerate(
        [(str(n_stages), "阶段教程"), (str(n_svgs), "动画电路图"), (str(n_code), "PC 可跑配套")]
    ):
        x = 58 + i * 184
        draw.rounded_rectangle((x, 292, x + 164, 404), radius=16, fill=WHITE)
        w = draw.textlength(num, font=f_num)
        draw_text(draw, (x + (164 - w) / 2, 300), num, f_num, TEAL)
        f_pill_label = fit_font(draw, label, "regular", 20, 140)
        w = draw.textlength(label, font=f_pill_label)
        draw_text(draw, (x + (164 - w) / 2, 366), label, f_pill_label, MUTED)

    draw_text(draw, (58, 450), "离子走里面，电子走外面。", f_line, WHITE)
    draw_text(draw, (58, 490), "先做第 0 天，再顺着七个阶段往下走。", f_line, WHITE)

    draw.rounded_rectangle((620, 28, 1240, 612), radius=24, fill=CARD)
    draw_text(draw, (660, 56), "七个阶段", f_head, INK)
    for i, (badge, title, desc) in enumerate(STAGES):
        top = 108 + i * 70
        draw.ellipse((652, top, 692, top + 40), fill=TEAL)
        w = draw.textlength(badge, font=f_badge)
        draw_text(draw, (672 - w / 2, top + 5), badge, f_badge, WHITE)
        draw_text(draw, (710, top + 2), title, f_stage, INK)
        draw_text(draw, (710, top + 36), desc, f_desc, MUTED)

    target = out_dir / OUT.name if out_dir else OUT
    img.save(target)
    print(f"ok: {target} （{n_stages} 教程 / {n_svgs} 动画 / {n_code} 配套）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
