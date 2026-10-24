import json
from pathlib import Path
import sys

import fitz
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
try:
    from check_pdf import PdfContractError, validate_pdf
finally:
    sys.path.pop(0)


def _manifest(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "title": "BMS 实战：从一颗电芯到一套证据链",
                "author": "BMS-Z 开源社区",
                "subtitle": "出版级 PDF 合同测试",
                "keywords": "BMS, battery",
                "parts": [
                    {"id": "p1", "title": "第一部分", "description": "示例", "files": ["01-示例.md"]},
                    {"id": "p8", "title": "附录", "description": "工具箱", "files": ["附录A-示例.md"]},
                ],
                "chapter_sources": {"01-示例.md": ["source-1"], "附录A-示例.md": ["source-2"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _insert_cn(page: fitz.Page, x: float, y: float, text: str, size: float = 10) -> None:
    page.insert_text((x, y), text, fontname="china-s", fontsize=size)


def _book_pdf(path: Path, *, missing_footer: int | None = None, toc_numbers: bool = True) -> Path:
    doc = fitz.open()
    for _ in range(8):
        doc.new_page(width=595, height=842)
    title = "BMS 实战：从一颗电芯到一套证据链"
    doc.set_metadata(
        {
            "title": title,
            "author": "BMS-Z 开源社区",
            "subject": "出版级 PDF 合同测试",
            "keywords": "BMS, battery",
        }
    )
    doc.set_toc(
        [
            [1, title, 1],
            [1, "第一部分", 4],
            [2, "第 1 章 示例", 5],
            [2, "附录 A 示例", 7],
        ]
    )

    _insert_cn(doc[0], 72, 100, title, 18)
    _insert_cn(doc[1], 72, 72, "阅读路线")
    doc[1].insert_link({"kind": fitz.LINK_GOTO, "from": fitz.Rect(70, 58, 180, 76), "page": 4})

    toc = doc[2]
    _insert_cn(toc, 72, 72, "目录", 16)
    entries = [("第 1 章 示例", 4, 110), ("附录 A 示例", 6, 140)]
    for label, target, y in entries:
        _insert_cn(toc, 72, y, label)
        rect = fitz.Rect(70, y - 13, 260, y + 4)
        toc.insert_link({"kind": fitz.LINK_GOTO, "from": rect, "page": target})
        if toc_numbers:
            toc.insert_text((520, y), str(target), fontname="helv", fontsize=8)

    _insert_cn(doc[3], 72, 100, "第一部分")
    _insert_cn(doc[4], 72, 100, "第 1 章 示例")
    doc[4].insert_text((72, 150), "SOURCE ANCHORS", fontname="helv", fontsize=9)
    _insert_cn(doc[5], 72, 100, "正文")
    _insert_cn(doc[5], 595 - 42 - 80, 20, "第 1 章 示例", 7.5)
    _insert_cn(doc[6], 72, 100, "附录 A 示例")
    doc[6].insert_text((72, 150), "SOURCE ANCHORS", fontname="helv", fontsize=9)
    _insert_cn(doc[7], 72, 100, "附录正文")
    _insert_cn(doc[7], 595 - 42 - 80, 20, "附录 A 示例", 7.5)

    total = doc.page_count - 1
    for index in range(1, doc.page_count):
        if index == missing_footer:
            continue
        label = f"{index} / {total}"
        width = fitz.get_text_length(label, fontname="helv", fontsize=8)
        doc[index].insert_text(((595 - width) / 2, 832), label, fontname="helv", fontsize=8)

    doc.save(path)
    doc.close()
    return path


def test_validate_pdf_accepts_complete_publication_contract(tmp_path):
    validate_pdf(_book_pdf(tmp_path / "book.pdf"), _manifest(tmp_path / "manifest.json"))


def test_validate_pdf_rejects_missing_footer(tmp_path):
    with pytest.raises(PdfContractError, match="页脚"):
        validate_pdf(
            _book_pdf(tmp_path / "book.pdf", missing_footer=5),
            _manifest(tmp_path / "manifest.json"),
        )


def test_validate_pdf_rejects_missing_toc_page_numbers(tmp_path):
    with pytest.raises(PdfContractError, match="目录页码"):
        validate_pdf(
            _book_pdf(tmp_path / "book.pdf", toc_numbers=False),
            _manifest(tmp_path / "manifest.json"),
        )
