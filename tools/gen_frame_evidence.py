"""Generate the chapter 18/29 static evidence diagrams from explicit teaching data.

Run from any directory: python tools/gen_frame_evidence.py [--out DIR].
No external renderer, fonts, or network are required to write the editable SVGs.
"""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INK = "#293B3A"
TEAL = "#176B73"
GOLD = "#926717"
RED = "#A53C38"


def text(x, y, label, size=23, color=INK, anchor="start", weight=400):
    return (f'<text x="{x:g}" y="{y:g}" font-size="{size}" fill="{color}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{escape(label)}</text>')


def rect(x, y, w, h, fill="#FFFFFF", stroke="#CED8CF", radius=12):
    return (f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
            f'rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')


def line(x1, y1, x2, y2, color=INK, dash="", width=2):
    dashed = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" '
            f'stroke="{color}" stroke-width="{width}"{dashed}/>')


def svg(title, description, height, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 {height}" '
            f'width="960" height="{height}" role="img" aria-labelledby="title desc" '
            'font-family="Noto Sans CJK SC, Microsoft YaHei, sans-serif">\n'
            f'<title id="title">{escape(title)}</title>\n'
            f'<desc id="desc">{escape(description)}</desc>\n'
            f'<rect width="960" height="{height}" fill="#FFFDF5"/>\n'
            + "\n".join(body) + "\n</svg>\n")


def freshness():
    timeout = 200
    times = (0, 100, 200)
    start_x, end_x = 210, 850
    def x(t):
        return start_x + (end_x - start_x) * t / timeout

    body = [text(40, 50, "报文在来，截止时间没有后移", 32, weight=700),
            text(40, 87, "本地单调时钟 · 同一会话 · 合成教学记录", 21),
            text(40, 160, "报文", 23, weight=700),
            text(40, 304, "接纳起点", 23, weight=700),
            text(40, 415, "本地年龄", 23, weight=700)]
    for t in times:
        body += [line(x(t), 198, x(t), 444, "#BBC8BF", "4 6"),
                 rect(x(t)-84, 115, 168, 79, "#E6F0EF" if t == 0 else "#FFFFFF"),
                 text(x(t), 145, "counter = 7", 23, TEAL, "middle", 700),
                 text(x(t), 177, "接纳新样本" if t == 0 else "重复 / 不续命", 20, INK, "middle"),
                 text(x(t), 242, f"{t} ms", 23, INK, "middle")]
    body += [line(x(0), 211, x(timeout), 211, TEAL, width=3),
             line(x(0), 300, x(timeout), 300, TEAL, width=3),
             f'<circle cx="{x(0):g}" cy="300" r="7" fill="{TEAL}"/>',
             text(530, 335, "last_accepted_new 始终为 0 ms", 22, TEAL, "middle"),
             line(x(0), 400, x(timeout), 400, GOLD, width=3)]
    for t in times:
        body += [f'<circle cx="{x(t):g}" cy="400" r="6" fill="{GOLD}"/>',
                 text(x(t), 439, f"{t} ms", 26, GOLD, "middle", 700)]
    body += [line(x(timeout), 250, x(timeout), 454, RED, "7 5", 3),
             text(850, 482, "截止 200 ms", 24, RED, "middle", 700),
             rect(40, 513, 880, 105, "#F6F0E1"),
             text(60, 547, "边界核对（不按比例）", 21, GOLD, weight=700),
             text(60, 587, "199 ms：未过期", 24),
             text(405, 587, "200 ms：age ≥ 200，过期", 24, RED),
             text(40, 659, "200 ms 没有任何报文也一样：定时检查不能依赖收包回调。", 22)]
    return svg("重复帧不能给旧数据续命",
               "零毫秒接纳counter七；一百和两百毫秒重复到达，不更新接纳起点。"
               "本地年龄依次为零、一百、两百毫秒。小框单独核对199毫秒未过期、200毫秒达到截止；"
               "199毫秒是检查点而不是新报文。没有报文时也须定时检查。", 690, body)


def frame_layout():
    fields = [("帧头", "AA 55", 2), ("addr", "01", 1), ("cmd", "03", 1),
              ("len", "02", 1), ("data", "0E A0", 2), ("crc8", "31", 1)]
    body = [text(40, 50, "这 8 个字节，谁在 CRC 的括号里？", 32, weight=700),
            text(40, 88, "教学帧 / 非厂商协议　　总长 6 + len = 8 B；len 只数载荷", 22)]
    left, unit = 40, 110
    coverage_start = left + fields[0][2] * unit
    coverage_end = left + sum(f[2] for f in fields[:-1]) * unit
    for name, value, nbytes in fields:
        width = unit * nbytes
        protected = name not in ("帧头", "crc8")
        body += [rect(left, 128, width-4, 127, "#E6F0EF" if protected else "#FFFFFF", radius=8),
                 text(left+(width-4)/2, 159, name, 23, INK, "middle", 700),
                 text(left+(width-4)/2, 205, value, 30, TEAL, "middle", 700),
                 text(left+(width-4)/2, 239, f"{nbytes} B", 20, INK, "middle")]
        left += width
    body += [line(coverage_start, 270, coverage_start, 289, TEAL, width=3),
             line(coverage_start, 289, coverage_end-4, 289, TEAL, width=3),
             line(coverage_end-4, 270, coverage_end-4, 289, TEAL, width=3),
             text((coverage_start+coverage_end-4)/2, 326, "CRC 输入：01 03 02 0E A0（5 B）", 23, TEAL, "middle", 700),
             rect(40, 357, 880, 152, "#F6F0E1"),
             text(62, 391, "CRC-8/SMBUS", 27, GOLD, weight=700),
             text(62, 430, "width=8     poly=0x07     init=0x00", 23),
             text(62, 469, "refin=false     refout=false     xorout=0x00", 23),
             text(40, 550, "校验向量：ASCII 123456789 → F4；本帧输入 → 31", 24, weight=700),
             text(40, 591, "改了 len，也改了 CRC 输入；帧头和 crc8 字节都不在括号内。", 22)]
    return svg("教学帧的CRC覆盖范围与六参数",
               "AA55、地址01、命令03、长度02、载荷0EA0、CRC31，共八字节。"
               "CRC覆盖地址到载荷五字节，包括长度，不含帧头和CRC字节。"
               "CRC-8/SMBUS参数为8、07、00、不反射、不反射、00；ASCII标准向量结果F4。", 625, body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "bms-book/assets")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for filename, builder in (("freshness-deadline.svg", freshness), ("frame-layout.svg", frame_layout)):
        (args.out / filename).write_text(builder(), encoding="utf-8", newline="\n")
        print(args.out / filename)


if __name__ == "__main__":
    main()
