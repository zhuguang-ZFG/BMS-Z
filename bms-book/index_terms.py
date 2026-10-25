"""索引术语的加载、匹配与正文取词——盖章端与契约门共用同一份实现。

两处必须共用：如果盖章用一套匹配、契约门用另一套，门就可能「祝福」自己的错。
ASCII 缩写要按词边界匹配，否则 `EMS` 会命中 `Systems`、`SPM` 会命中 `SPMe`、
`OTA` 会命中 `total`；中文术语按字面匹配（中文没有词边界，靠完整子串）。
"""
from __future__ import annotations

import json
from pathlib import Path
import re

# 纯 ASCII 术语（可含空格、连字符、点、斜杠）：需要词边界
_ASCII_TERM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.\-+/()]*$")
# Chrome 会在大纲标题里插零宽字符（CI 的 Linux 侧实测），解析正文起点前先剥掉
_INVISIBLE = re.compile(r"[\u00ad\u200b-\u200f\u2028\u2029\u202a-\u202e\ufeff]")
# 页眉/页脚带：取正文文字时要排除，否则书名里的 `BMS` 会让每页都算命中
BODY_TOP = 30.0
BODY_BOTTOM_MARGIN = 40.0


def load_terms(path: Path) -> list[str]:
    """读取去重后的术语清单；空项或重复项直接挡在构建前。"""
    terms = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(terms, list) or not all(isinstance(term, str) for term in terms):
        raise RuntimeError(f"索引术语必须是字符串数组：{path}")
    cleaned = [term.strip() for term in terms]
    if any(not term for term in cleaned):
        raise RuntimeError(f"索引术语不能有空项：{path}")
    if len(cleaned) != len(set(cleaned)):
        raise RuntimeError(f"索引术语不能重复：{path}")
    return cleaned


def term_pattern(term: str) -> re.Pattern[str]:
    """术语匹配器：ASCII 走词边界，含中文的走字面。

    - 只允许**横向**空白差异（同一行内 PDF 会把中英混排或分栏插空格），
      绝不跨行：`回放` 不该命中「返回\\n放电」，`CAN` 必须命中「CAN bus」
      （把空白整体删掉会把 `CANbus` 变成命中、把跨行拼接变成命中）。
    - 多词术语（`Joseph form`）内部允许空格写法差异。
    """
    tokens = [re.escape(token) for token in term.split()]
    body = r"[ \t\u00a0]*".join(tokens)
    if _ASCII_TERM.match(term):
        # 大小写敏感：`CAN` 不该命中英文小词 `can` 或 URL 里的 `can`，
        # `SOC` 不该命中路径里的 `soc`——索引要的是这个词本身。
        return re.compile(rf"(?<![A-Za-z0-9_]){body}(?![A-Za-z0-9_])")
    return re.compile(body)


def contains_term(term: str, text: str) -> bool:
    return term_pattern(term).search(text) is not None


def body_text(page, top: float = BODY_TOP, bottom_margin: float = BODY_BOTTOM_MARGIN) -> str:
    """页面正文文字（排除页眉与页脚带），**按行**拼接。

    行内把 span 直接相接（PDF 会在中英混排处插空格），行之间保留 `\\n`——
    跨行命中会伪造页码，所以换行必须是硬边界。
    """
    limit = page.rect.height - bottom_margin
    lines: list[str] = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans or spans[0]["bbox"][1] < top or spans[0]["bbox"][3] > limit:
                continue
            lines.append("".join(span["text"] for span in spans))
    return "\n".join(lines)


# 词条行右侧只允许出现页码与分隔符；省略号用 ASCII 三点，中文字体不保证 U+2026
_REF_TAIL_RE = re.compile(r"^[\s\d,\.·…]*$")
ELLIPSIS = "..."


def _line_text(page, y0: float, y1: float) -> str:
    rect = (0, max(0.0, y0 - 1), page.rect.width, y1 + 1)
    return page.get_textbox(rect).strip()


def index_term_rect(document, start: int, term: str):
    """索引区内该术语的词条行位置，返回 (页号, Rect) 或 None。

    三道过滤缺一不可：只扫索引区（含续页）、排除页眉/页脚带（书名页眉里也含
    `BMS` 这类词）、词条行只能是「术语 + 页码」。以前只比字符串前缀，页眉
    `BMS 实战` 会被当成词条行，取到的「右侧文字」是 `实战`。
    """
    for page_index in range(start, document.page_count):
        page = document[page_index]
        limit = page.rect.height - BODY_BOTTOM_MARGIN
        for rect in page.search_for(term):
            if rect.y0 < BODY_TOP or rect.y1 > limit:
                continue
            line = _line_text(page, rect.y0, rect.y1)
            if not line.startswith(term):
                continue
            if _REF_TAIL_RE.match(line[len(term):]):
                return page_index, rect
    return None


def first_body_page(document) -> int:
    """正文起点（0 基）：大纲里第一个「第 N 章」二级书签所在页。

    索引只统计正文：扉页、版权页与目录页也会出现 `BMS`、`SOC` 这类词，把它们
    算进去会占满六页上限、把真正的正文页挤掉。
    """
    for level, title, page in document.get_toc():
        if level == 2 and page >= 1 and re.match(r"^第 \d+ 章", _INVISIBLE.sub("", title)):
            return page - 1
    return 1


def term_pages(
    document, terms: list[str], start: int, skipped: tuple[int, int], floor: int = 1
) -> dict[str, list[int]]:
    """每个术语命中的正文页（0 基，等于页脚标签）；`skipped` 区段与 `floor` 之前不计入。"""
    skip_start, skip_end = skipped
    texts = [body_text(document[index]) for index in range(start)]
    return {
        term: [
            index
            for index in range(max(floor, 1), start)
            if not skip_start <= index < skip_end and contains_term(term, texts[index])
        ][:6]
        for term in terms
    }