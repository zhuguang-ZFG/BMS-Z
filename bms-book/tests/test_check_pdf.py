import importlib.util
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
    doc[4].insert_text((72, 150), "本章证据来源", fontname="china-s", fontsize=9)
    _insert_cn(doc[5], 72, 100, "正文")
    _insert_cn(doc[5], 595 - 42 - 80, 20, "第 1 章 示例", 7.5)
    _insert_cn(doc[6], 72, 100, "附录 A 示例")
    doc[6].insert_text((72, 150), "本章证据来源", fontname="china-s", fontsize=9)
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


def _rewrite_outline(path: Path, target: Path, *, suffix: str) -> Path:
    document = fitz.open(path)
    document.set_toc(
        [[level, f"{title}{suffix}" if level == 2 else title, page]
         for level, title, page in document.get_toc()]
    )
    document.save(target)
    document.close()
    return target


def test_validate_pdf_accepts_headers_when_outline_titles_carry_zero_width_space(tmp_path):
    """Chrome 在 Linux 上会把零宽字符塞进大纲标题；页眉文字层里没有这些字符。"""
    dirty = _rewrite_outline(
        _book_pdf(tmp_path / "clean.pdf"), tmp_path / "book.pdf", suffix="\u200b"
    )
    validate_pdf(dirty, _manifest(tmp_path / "manifest.json"))


def test_pdf_sections_strip_zero_width_space_from_outline():
    module = _load_build_html()
    document = fitz.open()
    document.new_page()
    document.new_page()
    document.set_toc([[1, "第一部分", 1], [2, "第 1 章 示例\u200b", 2]])
    assert module._pdf_sections(document) == [(1, "第 1 章 示例")]
    document.close()


def _load_build_html():
    sys.path.insert(0, str(ROOT))
    try:
        spec = importlib.util.spec_from_file_location("build_html_units", ROOT / "build_html.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


def _raw_book_pdf(path: Path, *, suffix: str = "") -> Path:
    """一份还没盖章的书稿 PDF：目录跨两页，第二页只剩最后一条条目。

    layout：0 封面 / 1 阅读路线 / 2-3 目录 / 4 分部页 / 5-7 第 1 章 / 8-9 附录 A。
    """
    document = fitz.open()
    for _ in range(10):
        document.new_page(width=595, height=842)
    title = "BMS 实战：从一颗电芯到一套证据链"
    document.set_toc(
        [
            [1, title, 1],
            [1, "第一部分", 5],
            [2, f"第 1 章 示例{suffix}", 6],
            [2, f"附录 A 示例{suffix}", 9],
        ]
    )
    _insert_cn(document[0], 72, 100, title, 18)
    _insert_cn(document[1], 72, 72, "阅读路线")
    document[1].insert_link({"kind": fitz.LINK_GOTO, "from": fitz.Rect(70, 58, 180, 76), "page": 5})

    first = document[2]
    _insert_cn(first, 72, 72, "目录", 16)
    for row in range(10):
        y = 110 + row * 19
        _insert_cn(first, 72, y, f"第 1 章 示例（{row}）")
        first.insert_link({"kind": fitz.LINK_GOTO, "from": fitz.Rect(70, y - 13, 260, y + 4), "page": 5})
    second = document[3]
    _insert_cn(second, 72, 72, "附录 A 示例")
    second.insert_link({"kind": fitz.LINK_GOTO, "from": fitz.Rect(70, 58, 260, 76), "page": 8})

    _insert_cn(document[4], 72, 100, "第一部分")
    _insert_cn(document[5], 72, 100, "第 1 章 示例")
    document[5].insert_text((72, 150), "本章证据来源", fontname="china-s", fontsize=9)
    _insert_cn(document[6], 72, 100, "正文一")
    _insert_cn(document[7], 72, 100, "正文二")
    _insert_cn(document[8], 72, 100, "附录 A 示例")
    document[8].insert_text((72, 150), "本章证据来源", fontname="china-s", fontsize=9)
    _insert_cn(document[9], 72, 100, "附录正文")

    document.save(path)
    document.close()
    return path


def _stamp_and_validate(path: Path, monkeypatch, tmp_path: Path) -> None:
    module = _load_build_html()
    monkeypatch.setattr(module, "MANIFEST", {"title": "BMS 实战：从一颗电芯到一套证据链"})
    module._stamp_pdf(
        path,
        {
            "title": "BMS 实战：从一颗电芯到一套证据链",
            "author": "BMS-Z 开源社区",
            "subject": "出版级 PDF 合同测试",
            "keywords": "BMS, battery",
        },
    )
    validate_pdf(path, _manifest(tmp_path / "manifest.json"))


def test_stamp_pdf_numbers_entries_on_a_single_entry_toc_page(tmp_path, monkeypatch):
    """目录续页只剩一条条目时也要盖章：旧判据（≥2 条前向内链）在这里断链。"""
    _stamp_and_validate(
        _raw_book_pdf(tmp_path / "book.pdf"), monkeypatch, tmp_path
    )


def test_stamp_pdf_strips_zero_width_space_from_outline_headers(tmp_path, monkeypatch):
    """大纲标题带零宽字符时，页眉仍要能被契约门在文字层里找到。"""
    _stamp_and_validate(
        _raw_book_pdf(tmp_path / "book.pdf", suffix="\u200b"), monkeypatch, tmp_path
    )
