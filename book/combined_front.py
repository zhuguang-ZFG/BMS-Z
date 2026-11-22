"""合集共用的卷首文案与矢量封面；PDF 和 EPUB 使用同一版面。"""

from __future__ import annotations

import html
import json
from datetime import datetime, UTC
from pathlib import Path

TITLE = "从模拟电路到 BMS（两卷合集）"
VOL1_TITLE = "卷一　通往模拟电路之路"
VOL2_TITLE = "卷二　BMS 实战：从一颗电芯到一套证据链"
GUIDE = [
    (
        "先猜一次：少掉的 0.40 V 去哪了？",
        "一颗电芯静置时是 3.70 V，带上 20 A 负载后只剩 3.30 V。是电量突然少了，还是读数另有原因？先写下猜测。封面的简化模型给出 U = Uoc − I × R0，取 R0 = 20 mΩ；只计算瞬时欧姆压降，暂不计极化、温度与容量变化。",
    ),
    (
        "选一条线索，带走一个答案",
        "测量：卷一第 9、12、13 章 → 卷二第 5–6 章，画出误差怎样走到读数里。保护：卷一第 16–17 章 → 卷二第 7–9 章，解释异常出现后为什么没有立刻关断。估算：卷二第 10–13 章，分清端电压、开路电压与 SOC。",
    ),
    (
        "每次读完，留下一页实验手记",
        "翻到下一页“三次观察，一张手记”，先做三个纸面问题，再看对照解。写下预测、计算和缺少的证据。零基础先读卷一第 0–8 章，再接卷二第 1–4 章；已有电路基础可从卷二第 1 章进入。",
    ),
    (
        "怎样定位",
        "PDF 总目录列出卷内页码和文件页序，页码标签用 I-、II- 区分两卷。EPUB 总目录与跨卷引用可直接跳转。需要大字号时选 EPUB；想保留整页图文关系时选 PDF。共享术语表在卷二附录区。",
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
                writer.append((x, y), line, font=font, fontsize=size)
                y += size * 1.65
                line = ""
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
    # 两次观察的手记；箭头表示实验先后，不是电气接线。
    for y in range(336, 610, 23):
        page.draw_line((48, y), (547, y), color=(0.86, 0.88, 0.83), width=0.45)
    page.draw_line((72, 325), (72, 610), color=(0.75, 0.57, 0.43), width=0.7)
    text(page, "同一颗电芯，为什么读数变了？", 86, 352, 17)
    for x, label, value in [
        (94, "01  静置时", "3.70 V"),
        (338, "02  带载后", "3.30 V"),
    ]:
        text(page, label, x, 390, 11, teal)
        page.draw_polyline(
            [(x, 409), (x + 166, 407), (x + 168, 489), (x - 1, 491), (x, 409)],
            color=ink,
            width=1.5,
            fill=(0.93, 0.94, 0.88),
        )
        page.draw_rect(
            fitz.Rect(x + 9, 418, x + 157, 467), color=(0.63, 0.69, 0.62), width=0.7
        )
        text(page, value, x + 20, 453, 29, ink)
        page.draw_circle((x + 17, 479), 2.5, color=teal, fill=teal)
        page.draw_line((x + 132, 479), (x + 150, 479), color=ink, width=1)
    page.draw_polyline([(276, 444), (319, 442), (311, 437)], color=orange, width=1.6)
    text(page, "20 A", 277, 425, 10, orange)
    text(page, "接入负载", 274, 470, 9)
    text(page, "少掉的 0.40 V，去哪里了？", 96, 526, 17, orange)
    page.draw_polyline([(97, 533), (250, 535), (379, 532)], color=orange, width=1.2)
    text(page, "U = Uoc − I × R0 = 3.70 − 20 × 0.020 = 3.30 V", 96, 562, 12)
    text(page, "教学假设：R0 = 20 mΩ；只看瞬时欧姆压降。", 96, 588, 9)
    text(page, "翻开导读，先写下你的猜测。", 96, 609, 10, teal)
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
