#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新图字体覆盖闸：SVG 里的每个字都必须在书籍字体子集里。

`analog-book/book/fonts.py:required_text()` 会把 `assets/figures-v2/**/*.svg` 的可见
文字并进全书字符集，因此新图只要写进一个子集没有的汉字（如「绽」），print16k 的
`test_book_fonts` 就会红——而 CI 不能重建子集（`fonts/sources.json` 钉死哈希，源字体
在 gitignore 的 build/fonts-src，需联网下载）。教训来自 ch16-probe-compensation：
一个副标题的用字让整条 CI 跑完 20 分钟才发现。

所以画完就查：本模块在落盘前调用，缺字直接抛错并给出字与字体名。
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOK = ROOT / 'analog-book'
if str(BOOK) not in sys.path:
    sys.path.insert(0, str(BOOK))

from book import config as book_config            # noqa: E402
from book.fonts import FONT_FACES, missing_glyphs  # noqa: E402

_WHITESPACE = "\r\n\t"


def svg_text(svg: str) -> str:
    """取 SVG 的全部文本（含 title/desc）；解析失败时退回去标签的纯文本。

    必须覆盖 title/desc：`book/fonts.py:required_text()` 是把整份 SVG 的标签
    剥掉后并入字符集的，只查 <text> 会漏掉写在 <title> 里的字。
    """
    try:
        tree = ET.fromstring(svg)
    except ET.ParseError:
        return re.sub(r'<[^>]+>', ' ', svg)
    return ' '.join(tree.itertext())


def missing_in_assets(svg: str, fonts_dir: Path | None = None) -> dict[str, str]:
    """返回 {字体名: 缺字串}；空字典表示覆盖完整。"""
    text = ''.join(ch for ch in svg_text(svg) if ch not in _WHITESPACE)
    fonts_dir = fonts_dir or book_config.FONTS_DIR
    report = {}
    for family, _weight, name in FONT_FACES:
        # 与 test_book_fonts 同范围：只查正文的衬线/黑体四款。JetBrains Mono
        # 是代码字体，本来就不含汉字，把它算进来只会制造假告警。
        if family == 'Book Mono':
            continue
        path = Path(fonts_dir) / name
        if not path.is_file():
            continue
        missing = ''.join(sorted(missing_glyphs(path, text)))
        if missing:
            report[name] = missing
    return report


def assert_covered(svg: str, label: str, fonts_dir: Path | None = None) -> None:
    report = missing_in_assets(svg, fonts_dir)
    if report:
        detail = '；'.join(f'{name} 缺 {chars}' for name, chars in sorted(report.items()))
        raise SystemExit(f'{label}: 图内文字缺字形，print16k 会红——{detail}。'
                         '换用已有字形的说法，或先跑 python scripts/subset_fonts.py --download 重建子集。')
