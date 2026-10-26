#!/usr/bin/env python3
"""Validate the final BMS book PDF readers will download."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any, cast

import fitz

from index_terms import ELLIPSIS, body_text, contains_term, first_body_page, index_term_rect, term_pages, term_pattern

ROOT = Path(__file__).resolve().parent
CHAPTER_RE = re.compile(r"^(第 \d+ 章|附录 [A-E]|前言)")
HEADER_SECTION_RE = re.compile(r"^(第 \d+ 章|附录 [A-E]|前言|索引)")
INDEX_NUMBER_RE = re.compile(r"\d+")
PAGE_LABEL_RE = re.compile(r"\b\d+\s*/\s*\d+\b")
# Chrome 生成 PDF 大纲时会在标题里插入零宽字符（CI 的 Linux 侧实测：中文标题尾随 U+200B）。
# 这类字符不进文字层，页眉画出来后提取不到——期望值必须先剥掉，两边才比的是同一个字符串。
INVISIBLE_RE = re.compile(r"[\u00ad\u200b-\u200f\u2028\u2029\u202a-\u202e\ufeff]")


class PdfContractError(RuntimeError):
    """The generated PDF does not meet the publication contract."""


type PdfWord = tuple[float, float, float, float, str, int, int, int]
type PdfLink = dict[str, Any]


def _words(page: fitz.Page) -> list[PdfWord]:
    value = page.get_text("words")
    if not isinstance(value, list):
        raise PdfContractError("PyMuPDF did not return a word list")
    return cast(list[PdfWord], value)


def _page_text(page: fitz.Page) -> str:
    value = page.get_text("text")
    if not isinstance(value, str):
        raise PdfContractError("PyMuPDF did not return page text")
    return value


def _links(page: fitz.Page) -> list[PdfLink]:
    return cast(list[PdfLink], page.get_links())


def _clean_title(title: str) -> str:
    return INVISIBLE_RE.sub("", title).strip()


def _outline_sections(
    document: fitz.Document, pattern: re.Pattern[str] = CHAPTER_RE
) -> list[tuple[int, str]]:
    return [
        (page - 1, _clean_title(title))
        for level, title, page in document.get_toc()
        if level == 2 and page >= 1 and pattern.match(_clean_title(title))
    ]


def _outline_range(document: fitz.Document, title_prefix: str) -> tuple[int, int] | None:
    sections = [
        (page - 1, _clean_title(title))
        for level, title, page in document.get_toc()
        if level == 2 and page >= 1
    ]
    for pos, (start, title) in enumerate(sections):
        if title.startswith(title_prefix):
            end = sections[pos + 1][0] if pos + 1 < len(sections) else document.page_count
            return start, end
    return None


def _expected_index_refs(document: fitz.Document, terms: list[str]) -> dict[str, list[int]]:
    index_range = _outline_range(document, "索引")
    if index_range is None:
        return {}
    index_start, _index_end = index_range
    glossary = _outline_range(document, "附录 C")
    return term_pages(
        document, terms, index_start, glossary or (index_start, index_start),
        floor=first_body_page(document),
    )


def _index_findings(document: fitz.Document, terms: list[str]) -> list[str]:
    """验证卷末索引存在、每个页码右对齐盖章且真的含有该术语。"""
    findings: list[str] = []
    index_range = _outline_range(document, "索引")
    if index_range is None:
        return ["PDF 缺卷末索引书签"]
    index_start, _index_end = index_range
    expected = _expected_index_refs(document, terms)
    for term in terms:
        target = index_term_rect(document, index_start, term)
        if target is None:
            findings.append(f"PDF 索引缺术语 {term!r}")
            continue
        page_index, rect = target
        page = document[page_index]
        center = (rect.y0 + rect.y1) / 2
        right_text = " ".join(
            word[4]
            for word in _words(page)
            if word[0] > rect.x1 and abs((word[1] + word[3]) / 2 - center) <= 7
        )
        actual = [int(number) for number in INDEX_NUMBER_RE.findall(right_text)]
        has_more = ELLIPSIS in right_text
        wanted = expected.get(term, [])
        if not wanted:
            findings.append(f"PDF 索引术语 {term!r} 在正文无命中")
            continue
        if actual != wanted[:6]:
            findings.append(f"PDF 索引术语 {term!r} 页码 {actual}，应为 {wanted[:6]}")
            continue
        if has_more != (len(wanted) > 6):
            findings.append(
                f"PDF 索引术语 {term!r} 省略号与命中数不符（正文实际命中 {len(wanted)} 页）"
            )
            continue
        for target_page in actual:
            page_text = body_text(document[target_page])
            joined = page_text
            # 行级匹配与盖章端一致：同块续行相接也算（见 index_terms.term_line_hits）
            for block in document[target_page].get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                joined += "\n" + "".join(
                    span["text"]
                    for line in block.get("lines", [])
                    for span in line.get("spans", [])
                )
            if not contains_term(term, page_text) and not term_pattern(term).search(
                "".join(part for part in joined.split("\n") if part)
            ):
                findings.append(f"PDF 索引术语 {term!r} 指向第 {target_page} 页但该页无此词")
    return findings


def _notdef_findings(document: fitz.Document) -> list[str]:
    """整书不许出现 .notdef 字形（glyph id 0）：它意味着字体覆盖不到该字符。

    CI 的 ubuntu-24.04 runner 默认不带中文字体，Chrome 便把每个汉字画成豆腐块：
    整书 117120 个字形的 gid 落到 0，文字层里对应字符退化成 NUL，索引门才报
    「缺术语」。构建端装字体是治本，这道门是防复发——只要还有一处缺字体，
    第一页页码就够定位了。
    """
    total = 0
    pages: list[int] = []
    for index in range(document.page_count):
        page_total = 0
        for item in document[index].get_texttrace():
            page_total += sum(1 for char in item["chars"] if char[1] == 0)
        if page_total:
            pages.append(index + 1)
            total += page_total
    if not total:
        return []
    shown = ", ".join(str(page) for page in pages[:5])
    suffix = "…" if len(pages) > 5 else ""
    return [
        f"PDF 有 {total} 个 .notdef 字形（第 {shown}{suffix} 页）："
        "构建端缺该字符所需字体（中文要 fonts-noto-cjk）"
    ]


def _top_text(page: fitz.Page) -> str:
    return " ".join(word[4] for word in _words(page) if word[1] < 30)


def _bottom_text(page: fitz.Page) -> str:
    return " ".join(word[4] for word in _words(page) if word[1] > page.rect.height - 40)

def _section_links(page: fitz.Page, targets: set[int]) -> list[PdfLink]:
    return [
        link
        for link in _links(page)
        if isinstance(link.get("page"), int) and link["page"] in targets
    ]


def _find_toc_pages(document: fitz.Document, targets: set[int], first_divider: int) -> list[int]:
    candidates = list(range(1, max(1, first_divider)))
    best: list[int] | None = None
    for start_pos, start in enumerate(candidates):
        covered: set[int] = set()
        for end in candidates[start_pos:]:
            covered.update(int(link["page"]) for link in _section_links(document[end], targets))
            if covered >= targets:
                found = list(range(start, end + 1))
                if best is None or len(found) < len(best):
                    best = found
                break
    return best or []


def _has_toc_label(page: fitz.Page, link: PdfLink, label: str) -> bool:
    rect = fitz.Rect(link["from"])
    link_center = (rect.y0 + rect.y1) / 2
    for word in _words(page):
        if word[4] != label or word[0] <= rect.x1:
            continue
        word_center = (word[1] + word[3]) / 2
        if abs(word_center - link_center) <= 10:
            return True
    return False


def validate_pdf(pdf_path: Path, manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_files = [name for part in manifest["parts"] for name in part["files"]]
    expected_metadata = {
        "title": manifest["title"],
        "author": manifest["author"],
        "subject": manifest["subtitle"],
        "keywords": manifest["keywords"],
    }
    findings: list[str] = []

    document = fitz.open(pdf_path)
    try:
        metadata = document.metadata or {}
        for key, expected in expected_metadata.items():
            actual = metadata.get(key, "")
            if actual != expected:
                findings.append(f"PDF 元数据 {key} 不一致：{actual!r} != {expected!r}")

        sections = _outline_sections(document)
        if len(sections) != len(expected_files):
            findings.append(f"PDF 书签章节数 {len(sections)}，应为 {len(expected_files)}")
        section_starts = {start for start, _title in _outline_sections(document, HEADER_SECTION_RE)}
        header_sections = _outline_sections(document, HEADER_SECTION_RE)
        dividers = {
            page - 1
            for level, _title, page in document.get_toc()
            if level == 1 and page > 1
        }
        total = document.page_count - 1
        if PAGE_LABEL_RE.search(_bottom_text(document[0])):
            findings.append("PDF 封面不应有页脚页码")
        for index in range(1, document.page_count):
            expected = f"{index} / {total}"
            if expected not in _bottom_text(document[index]):
                findings.append(f"PDF 第 {index + 1} 物理页缺页脚 {expected}")

        current_title: str | None = None
        next_section = 0
        short_title = manifest["title"].split("：", 1)[0]
        for index in range(1, document.page_count):
            while next_section < len(header_sections) and header_sections[next_section][0] <= index:
                current_title = header_sections[next_section][1]
                next_section += 1
            top = _top_text(document[index])
            if index in section_starts or index in dividers:
                if top:
                    findings.append(f"PDF 第 {index + 1} 物理页为章首/分部页，却出现页眉 {top!r}")
                continue
            if current_title is None:
                continue
            expected_header = short_title if index % 2 == 0 else current_title
            if expected_header not in top:
                findings.append(f"PDF 第 {index + 1} 物理页缺页眉 {expected_header!r}")

        if sections:
            targets = {start for start, _title in sections}
            first_divider = min(dividers) if dividers else min(targets)
            toc_pages = _find_toc_pages(document, targets, first_divider)
            if not toc_pages:
                findings.append("PDF 未找到覆盖全部章节的目录页")
            else:
                covered: set[int] = set()
                for index in toc_pages:
                    page = document[index]
                    for link in _section_links(page, targets):
                        target = int(link["page"])
                        covered.add(target)
                        if not _has_toc_label(page, link, str(target)):
                            findings.append(
                                f"PDF 目录页 {index + 1} 的目标页 {target} 缺右对齐目录页码"
                            )
                if covered != targets:
                    findings.append(
                        f"PDF 目录只覆盖 {len(covered)}/{len(targets)} 个章节目标"
                    )

        anchor_count = sum(_page_text(page).count("本章证据来源") for page in document)
        expected_anchors = len(manifest.get("chapter_sources", {}))
        if anchor_count != expected_anchors:
            findings.append(f"PDF 来源锚点卡 {anchor_count} 张，应为 {expected_anchors} 张")

        index_terms = manifest.get("index_terms")
        if index_terms:
            terms = json.loads((manifest_path.parent / index_terms).read_text(encoding="utf-8"))
            findings.extend(_index_findings(document, terms))

        findings.extend(_notdef_findings(document))
    finally:
        document.close()

    if findings:
        raise PdfContractError("PDF 出版契约失败：\n- " + "\n- ".join(findings))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", nargs="?", type=Path, default=ROOT / "dist" / "bms-book.pdf")
    parser.add_argument("--manifest", type=Path, default=ROOT / "manifest.json")
    args = parser.parse_args()
    try:
        validate_pdf(args.pdf, args.manifest)
    except (OSError, json.JSONDecodeError, PdfContractError) as exc:
        parser.error(str(exc))
    print(f"PASS: PDF publication contract ({args.pdf})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
