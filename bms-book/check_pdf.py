#!/usr/bin/env python3
"""Validate the final BMS book PDF readers will download."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any, cast

import fitz

ROOT = Path(__file__).resolve().parent
CHAPTER_RE = re.compile(r"^(第 \d+ 章|附录 [A-E]|前言)")
PAGE_LABEL_RE = re.compile(r"\b\d+\s*/\s*\d+\b")


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


def _outline_sections(document: fitz.Document) -> list[tuple[int, str]]:
    return [
        (page - 1, title.strip())
        for level, title, page in document.get_toc()
        if level == 2 and page >= 1 and CHAPTER_RE.match(title.strip())
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
        section_starts = {start for start, _title in sections}
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
            while next_section < len(sections) and sections[next_section][0] <= index:
                current_title = sections[next_section][1]
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

        anchor_count = sum(_page_text(page).count("SOURCE ANCHORS") for page in document)
        expected_anchors = len(manifest.get("chapter_sources", {}))
        if anchor_count != expected_anchors:
            findings.append(f"PDF 来源锚点卡 {anchor_count} 张，应为 {expected_anchors} 张")
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
