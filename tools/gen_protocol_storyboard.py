"""Render six hand-drawn protocol panels using the actual teaching parser trace.

SVG source only; use the existing storyboard WebP export pipeline for publication.
"""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'code/protocol'))
from frames import Frame, FrameParser  # noqa: E402

INK = '#003153'


def text(x, y, value, size=22, anchor='start'):
    return (f'<text x="{x:g}" y="{y:g}" font-size="{size}" '
            f'text-anchor="{anchor}">{escape(value)}</text>')


def trace(stream):
    parser = FrameParser()
    points = []
    for b in stream:
        parser.feed(b)
        points.append((parser.frames_ok, parser.frames_bad_crc))
    return points


def panel(number):
    good = bytes.fromhex('00 11 22') + Frame(1, 3, bytes.fromhex('0e74')).to_bytes()
    bad = bytearray(good)
    bad[-1] ^= 1
    good_counts, bad_counts = trace(good), trace(bad)
    progress = [2, 4, 9, 10, 10, 10][number-1]
    shown = bad if number == 5 else good
    captions = [
        '① 00 11 22 是垃圾前缀；逐字节跳过，两个计数仍为 0。',
        '② 找到 AA 55：接着等元信息，不能把每次 read 当成帧界。',
        '③ 地址 01、命令 03、长度 02、载荷 0E 74；还差 CRC。',
        '④ 末字节 13 到达：CRC-8/SMBUS 通过，好流完成 1 帧。',
        '⑤ 独立回放：仅把 CRC 的 13 翻为 12，坏 CRC 计数变为 1。',
        '⑥ 两次回放各自计数：好流收回 1 帧，翻位流拒绝 1 帧。',
    ]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="560" viewBox="0 0 960 560" role="img" aria-labelledby="title desc">',
             f'<title id="title">教学帧重同步，第{number}步</title>',
             '<desc id="desc">三个垃圾字节后是完整八字节教学帧AA550103020E7413。'
             'CRC覆盖0103020E74。下方为好流与仅翻转CRC末位的坏流两次独立回放；最后输入索引为10。</desc>',
             '<defs><filter id="w" x="-5%" y="-10%" width="110%" height="120%"><feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="2" seed="11" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="1.6" xChannelSelector="R" yChannelSelector="G"/></filter></defs>',
             '<rect width="960" height="560" fill="#f6f1e3"/>',
             f'<g fill="{INK}" font-family="KaiTi, Microsoft YaHei, sans-serif">',
             text(40, 49, '从垃圾字节，到一条完整好帧', 31),
             text(40, 87, '本书教学协议 · 下方两条计数线来自两次独立回放', 21)]
    labels = ['噪声','噪声','噪声','帧头','帧头','地址','命令','长度','数据','数据','CRC']
    for i, (byte, label) in enumerate(zip(shown, labels, strict=True)):
        left, center = 62+i*78, 93+i*78
        opacity = 1 if i <= progress else .35
        parts += [f'<g opacity="{opacity}">',
                  f'<rect x="{left}" y="145" width="62" height="58" fill="none" stroke="{INK}" stroke-width="1.8" filter="url(#w)"/>',
                  text(center,132,label,19,'middle'), text(center,182,f'{byte:02X}',26,'middle'),
                  text(center,233,str(i),17,'middle'), '</g>']
    parts += [text(40,271,'字节索引 0…10；CRC 输入：01 03 02 0E 74 → 13',22),
              text(40,311,'好流：完成帧数',21), text(40,385,'翻位流：坏 CRC 数',21)]
    for counts, which, base, dashed in [(good_counts,0,350,False),(bad_counts,1,424,True)]:
        points = [(93,base)]
        for i in range(progress+1):
            value = counts[i][which]
            x = 93+i*78
            points += [(x,points[-1][1]),(x,base-26*value)]
        points.append((912,points[-1][1]))
        d = 'M'+' L'.join(f'{x},{y}' for x,y in points)
        dash = ' stroke-dasharray="7 6"' if dashed else ''
        parts += [f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="2.2"{dash} filter="url(#w)"/>',
                  text(917,points[-1][1]+7,str(int((base-points[-1][1])/26)),20)]
    if number == 5:
        parts.append('<circle cx="873" cy="173" r="28" fill="none" stroke="#d43527" stroke-width="2.2"/>')
    parts += [text(40,489,captions[number-1],22),
              text(40,528,'原理示意 / 非实拍；0x0E74 按大端毫伏约定为 3700 mV。',21),
              '</g></svg>']
    return '\n'.join(parts)+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'docs/circuits/handraw/storyboard/protocol-resync')
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    for number in range(1,7):
        (args.out/f'frame-{number:02d}.svg').write_text(panel(number),encoding='utf-8',newline='\n')
    print('Generated six panels from the parser: 11 input bytes, completion at index 10.')


if __name__=='__main__':
    main()
