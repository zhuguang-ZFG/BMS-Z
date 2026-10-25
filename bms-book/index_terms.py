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


ELLIPSIS = "..."


def _line_spans(page):
    """逐行产出 (bbox, 行文字)；行内 span 直接相接（PDF 会在中英之间插空格）。"""
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            yield line["bbox"], "".join(span["text"] for span in spans)


def index_term_rect(document, start: int, term: str):
    """索引区内该术语的词条行位置，返回 (页号, Rect) 或 None。

    按**行**扫描而不是按 `search_for` 精确命中：不同平台的字体度量会让同一行的
    垂直范围略有差别，用搜索矩形的上下各扩 1pt 去取文字就可能连带取到相邻行，
    把词条行判成「不是术语 + 页码」。行首必须是该术语（去空白、大小写不敏感）；
    行尾允许页码/分隔符或继续排着别的词条——多栏排版会把两条词条放进同一行，
    但被匹配到的词条总是行首那一个。
    """
    needle = re.sub(r"\s+", "", term).casefold()
    for page_index in range(start, document.page_count):
        page = document[page_index]
        limit = page.rect.height - BODY_BOTTOM_MARGIN
        for bbox, text in _line_spans(page):
            if bbox[1] < BODY_TOP or bbox[3] > limit:
                continue
            stripped = re.sub(r"\s+", "", text).casefold()
            if not stripped.startswith(needle):
                continue
            return page_index, page.rect.__class__(bbox)
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


def term_line_hits(document, start: int, end: int, term: str):
    """正文区里该术语出现的页（0 基，生成器），行内相邻、同块续行相接都算。

    换行是唯一硬边界：`get_text("dict")` 有时会把同一物理行拆成两个 line
    （中文长句、标点换行），所以同一 block 里相邻两个 line 首尾相接的文本
    也参与匹配；跨 block 仍不算——那是真正的另起一段。
    """
    pattern = term_pattern(term)
    for page_index in range(max(start, 1), end):
        page = document[page_index]
        limit = page.rect.height - BODY_BOTTOM_MARGIN
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            chunks: list[str] = []
            y_top = None
            y_bottom = None
            prev_x1 = None
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                if y_top is None:
                    y_top = spans[0]["bbox"][1]
                y_bottom = spans[-1]["bbox"][3]
                text = "".join(span["text"] for span in spans)
                # 表格单元格里相邻两格会被合成一个 block：词尾与下一格词首
                # 直接连写（`EMS` + `CAN/...`）会让词边界失配。列边界（前一
                # 行右缘与后一行左缘之间有明显间隙）还原成空格，维持词边界。
                x0 = spans[0]["bbox"][0]
                if prev_x1 is not None and x0 - prev_x1 > 4.0:
                    text = " " + text
                prev_x1 = spans[-1]["bbox"][2]
                chunks.append(text)
            if y_top is None or y_top < BODY_TOP or y_bottom > limit:
                continue
            text = "".join(chunks)
            if pattern.search(text):
                yield page_index
                break


def term_pages(
    document, terms: list[str], start: int, skipped: tuple[int, int], floor: int = 1
) -> dict[str, list[int]]:
    """每个术语命中的正文页（0 基，等于页脚标签）；`skipped` 区段与 `floor` 之前不计入。"""
    skip_start, skip_end = skipped
    pages: dict[str, list[int]] = {}
    for term in terms:
        hits = [index for index in term_line_hits(document, floor, start, term)
                if not skip_start <= index < skip_end]
        pages[term] = hits[:6]
    return pages