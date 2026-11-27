"""合集共用的卷首文案与矢量封面；PDF 和 EPUB 使用同一版面。"""

from __future__ import annotations

import html
import json
from datetime import datetime, UTC
from pathlib import Path

TITLE = "从模拟电路到 BMS（两卷合集）"
VOL1_TITLE = "卷一　通往模拟电路之路"
VOL2_TITLE = "卷二　BMS 实战：从一颗电芯到一套证据链"
NO_LINE_START = "，。；：？！、）》】」』”’"
GUIDE = [
    (
        "读下一页前，先记下猜测",
        "把你对撤载读数的解释记在纸上。下一页会从三次观察开始复算，再给出推理过程和模型边界。",
    ),
    (
        "按问题选读",
        "想查测量误差怎样进入读数，可读卷一第 9、12、13 章，再接卷二第 5–6 章。想弄清保护动作的时序，读卷一第 16–17 章和卷二第 7–9 章。估算 SOC 可从卷二第 10–13 章开始，留意端电压与开路电压的区别。",
    ),
    (
        "从哪一章开始",
        "先翻到下一页“三次观察，一张手记”，记下你对三个读数的判断。零基础先读卷一第 0–10 章，再接卷二第 1–9 章；卷二第 10–24 章讲模型、状态估算和系统协作，最后读卷一第 15–18 章与卷二第 25–32 章，进入 PCB、排故、安全和产品验证。已有电路基础，可从卷二第 1 章开始。",
    ),
    (
        "页码与跳转",
        "PDF 总目录并列列出卷内页与文件页，书签和页码标签用 I-、II- 区分两卷。EPUB 总目录及跨卷引用可以直接跳转。需要放大字号时选 EPUB；想保留整页图文关系时选 PDF。共享术语表在卷二附录区。",
    ),
]
COLOPHON = [
    (
        "版本与编排",
        "两卷正文保留原有章节与页序，合集重新编排封面、共享卷首和总目录。各卷署名、来源说明及参考资料保留。",
    ),
    (
        "许可与署名",
        "正文采用 CC BY-SA 4.0，代码采用 MIT。卷一转入的第三方图片、字体与工具仍按原许可署名；详见卷一版权说明、来源与许可，以及仓库 LICENSE。作者：zhuguang-ZFG 与贡献者；卷二由 BMS-Z 开源社区共同编写。",
    ),
    (
        "引用",
        "引用本书请注明《从模拟电路到 BMS》、卷次、章节和版本。两卷可以分别引用。跨卷引用沿用“卷一／卷二 · 第 N 章”的格式；PDF 页码请同时注明卷次。",
    ),
    (
        "勘误与复算",
        "请在项目仓库 Issues 中附上卷次、章节、版本与复算过程。教学示例保留原书的假设和适用边界；实测、合成、参考值与独立真值应分清。",
    ),
    (
        "版本核对",
        "下载页提供合集构建记录与 SHA-256 校验值，可用于核对版本、修订日期和文件完整性。",
    ),
]


def colophon_sections():
    version = json.loads(
        (Path(__file__).resolve().parent / "manifest.json").read_text(encoding="utf-8")
    )["version"]
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    return [
        (COLOPHON[0][0], f"合集版本 {version} · 修订日期 {date}。" + COLOPHON[0][1]),
        *COLOPHON[1:],
    ]


def xhtml(title: str, body: str) -> bytes:
    return (
        f'<?xml version="1.0" encoding="utf-8"?>\n'
        f'<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN">'
        f"<head><title>{html.escape(title)}</title>"
        "<style>body{max-width:42em;margin:2em auto;padding:0 1em;line-height:1.8;"
        "font-family:serif}h1{line-height:1.35}h2{font-size:1.2em;"
        "margin-top:1.6em}a{color:inherit;text-decoration:underline}li{margin:.4em 0}"
        "img{max-width:100%;height:auto}p{orphans:2;widows:2}</style>"
        f"</head><body>{body}</body></html>"
    ).encode()


def prose_xhtml(title: str, sections: list[tuple[str, str]]) -> bytes:
    return xhtml(
        title,
        f"<h1>{html.escape(title)}</h1>"
        + "".join(
            f"<h2>{html.escape(h)}</h2><p>{html.escape(p)}</p>" for h, p in sections
        ),
    )


def text(
    page,
    value: str,
    x: float,
    y: float,
    size: float = 11,
    color=(0.12, 0.22, 0.25),
    width: float = 490,
) -> float:
    """按真实字宽换行，返回下一行基线；不裁剪中文。"""
    import fitz

    font = fitz.Font("cjk")
    writer = fitz.TextWriter(page.rect)
    for paragraph in value.split("\n"):
        line = ""
        for char in paragraph:
            if line and font.text_length(line + char, fontsize=size) > width:
                carry = ""
                if char in NO_LINE_START:
                    carry = line[-1]
                    line = line[:-1]
                writer.append((x, y), line, font=font, fontsize=size)
                y += size * 1.65
                line = carry
            line += char
        if line:
            writer.append((x, y), line, font=font, fontsize=size)
        y += size * 1.65
    writer.write_text(page, color=color)
    return y


def cover(doc, volume: int = 0):
    import fitz

    page = doc.new_page(width=595.28, height=841.89)
    cream, ink, teal, orange = (
        (0.98, 0.97, 0.93),
        (0.12, 0.22, 0.25),
        (0.09, 0.42, 0.4),
        (0.72, 0.31, 0.13),
    )
    page.draw_rect(page.rect, fill=cream, color=cream)
    page.draw_line((48, 60), (548, 60), color=ink, width=1.3)
    text(page, "BMS-Z  /  硬件自学与工程实践", 48, 48, 10)
    text(
        page,
        "两卷合集" if not volume else f"卷 {'I' if volume == 1 else 'II'}",
        48,
        108,
        13,
        teal,
    )
    if not volume:
        text(page, "从模拟电路", 45, 181, 46)
        text(page, "到 BMS", 45, 243, 46)
        subtitle = "一条从器件原理走到电池管理系统的硬件自学路线"
    elif volume == 1:
        text(page, "通往模拟", 45, 181, 46)
        text(page, "电路之路", 45, 243, 46)
        subtitle = "从欧姆定律到芯片内部结构"
    else:
        text(page, "BMS 实战", 45, 181, 46)
        text(page, "从一颗电芯到一套证据链", 48, 239, 22)
        subtitle = "把原理、测量与验证放进同一套系统"
    text(page, subtitle, 48, 284, 12, width=500)
    # 三个教学读数；箭头表示先后，不是电气接线。
    for y in range(336, 610, 23):
        page.draw_line((48, y), (547, y), color=(0.86, 0.88, 0.83), width=0.45)
    if volume == 0:
        # 三个教学读数；箭头表示先后，不是电气接线。
        page.draw_line((72, 325), (72, 610), color=(0.75, 0.57, 0.43), width=0.7)
        text(page, "同一颗电芯，为什么读数变了？", 86, 352, 17)
        text(page, "教学示意 · 三个时刻", 86, 374, 9, teal)
        for x, label, value in [
            (60, "01  静置", "3.70 V"),
            (228, "02  带载", "3.30 V"),
            (396, "03  撤载", "3.70 V"),
        ]:
            text(page, label, x + 7, 390, 9, teal, width=126)
            page.draw_polyline(
                [(x, 409), (x + 138, 407), (x + 140, 489), (x - 1, 491), (x, 409)],
                color=ink,
                width=1.5,
                fill=(0.93, 0.94, 0.88),
            )
            page.draw_rect(
                fitz.Rect(x + 8, 418, x + 132, 467), color=(0.63, 0.69, 0.62), width=0.7
            )
            text(page, value, x + 10, 453, 22, ink, width=118)
            page.draw_circle((x + 17, 479), 2.5, color=teal, fill=teal)
            page.draw_line((x + 110, 479), (x + 128, 479), color=ink, width=1)
        page.draw_polyline([(205, 444), (222, 442), (217, 438)], color=orange, width=1.6)
        page.draw_polyline([(373, 444), (390, 442), (385, 438)], color=orange, width=1.6)
        text(page, "20 A", 202, 425, 8, orange, width=25)
        text(page, "少掉的 0.40 V，去哪里了？", 96, 526, 17, orange)
        page.draw_polyline([(97, 533), (250, 535), (379, 532)], color=orange, width=1.2)
        text(page, "撤去负载，电压回来了。电量也回来了吗？", 96, 562, 11)
        text(page, "翻开导读，先写下你的猜测。", 96, 588, 10, teal)
    elif volume == 1:
        text(page, "从元件到可测输出", 86, 352, 17)
        text(page, "卷一主题示意 · 电阻分压", 86, 374, 9, teal)
        text(page, "理想空载时，Uout = Uin × R2 / (R1 + R2)", 86, 413, 10, teal)
        page.draw_circle((120, 476), 22, color=ink, fill=(0.93, 0.94, 0.88), width=1.5)
        text(page, "+", 114, 471, 11, teal, width=14)
        text(page, "−", 114, 486, 11, teal, width=14)
        text(page, "Uin", 99, 518, 9, teal, width=40)
        page.draw_line((120, 498), (120, 588), color=ink, width=1.3)
        page.draw_line((120, 588), (326, 588), color=ink, width=1.3)
        page.draw_line((142, 476), (183, 476), color=ink, width=1.3)
        page.draw_rect(fitz.Rect(183, 455, 258, 497), color=ink,
                       fill=(0.93, 0.94, 0.88), width=1.3)
        text(page, "R1", 207, 481, 11, width=30)
        page.draw_line((258, 476), (326, 476), color=ink, width=1.3)
        page.draw_circle((326, 476), 3, color=teal, fill=teal)
        page.draw_line((326, 476), (492, 476), color=ink, width=1.3)
        text(page, "Uout", 450, 457, 9, teal, width=45)
        page.draw_line((326, 476), (326, 518), color=ink, width=1.3)
        page.draw_rect(fitz.Rect(306, 518, 346, 576), color=ink,
                       fill=(0.93, 0.94, 0.88), width=1.3)
        text(page, "R2", 354, 552, 11, width=30)
        page.draw_line((326, 576), (326, 588), color=ink, width=1.3)
        page.draw_line((105, 588), (135, 588), color=ink, width=1.2)
        page.draw_line((110, 594), (130, 594), color=ink, width=1.2)
        page.draw_line((115, 600), (125, 600), color=ink, width=1.2)
        text(page, "GND", 98, 617, 8, teal, width=40)
    else:
        text(page, "把读数变成可核对的判断", 86, 352, 17)
        text(page, "卷二主题示意 · 从采样到验证", 86, 374, 9, teal)
        stages = [
            (58, "采样", "电压与电流"),
            (183, "估算", "SOC 与容量"),
            (308, "保护", "告警与断流"),
            (433, "验证", "结果可复算"),
        ]
        for index, (x, heading, detail) in enumerate(stages):
            page.draw_rect(fitz.Rect(x, 421, x + 104, 503), color=(0.63, 0.69, 0.62),
                           fill=(0.93, 0.94, 0.88), width=1.1)
            text(page, f"0{index + 1}", x + 9, 441, 8, orange, width=20)
            text(page, heading, x + 9, 464, 13, ink, width=86)
            text(page, detail, x + 9, 486, 8.5, teal, width=88)
            if index < len(stages) - 1:
                page.draw_polyline([(x + 108, 462), (x + 120, 460),
                                    (x + 116, 456)], color=orange, width=1.4)
        text(page, "卷二把测量值、模型判断与验证记录连在一起。", 96, 562, 11)
    text(page, "I  通往模拟电路之路", 48, 651, 15)
    text(page, "II  BMS 实战：从一颗电芯到一套证据链", 48, 685, 15)
    page.draw_line((48, 737), (548, 737), color=ink, width=1)
    text(page, "zhuguang-ZFG 与贡献者", 48, 771, 11)
    text(page, "中文 · 开源教学用书", 48, 796, 10, color=teal)
    return page


def prose_page(doc, title: str, sections: list[tuple[str, str]]):
    page = doc.new_page(width=595.28, height=841.89)
    text(page, "从模拟电路到 BMS", 48, 45, 10, color=(0.09, 0.42, 0.4))
    text(page, title, 48, 100, 25)
    y = 151
    for heading, paragraph in sections:
        y = text(page, heading, 48, y, 14, color=(0.09, 0.42, 0.4)) + 6
        y = text(page, paragraph, 48, y, 11, width=495) + 24
    if y > 805:
        raise ValueError(f"卷首文字溢出: {title} ({y})")
    return page


def cover_png() -> bytes:
    import fitz

    with fitz.open() as doc:
        page = cover(doc)
        return page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).tobytes("png")
