"""书籍化前后置页与索引的出版契约。

这些测试是新增功能的 RED/GREEN 证据：扉页/版权页/本书约定要真实进入 HTML，
索引页码必须指向实际含有该术语的正文页，并排除术语表自身。
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
try:
    import build_html
    from check_pdf import _index_findings
    from index_terms import contains_term, index_term_rect
finally:
    sys.path.pop(0)


def test_front_matter_contains_book_identity_and_reader_contract():
    text = build_html._front_matter_html()

    assert 'id="title-page"' in text
    assert 'id="colophon"' in text
    assert 'id="conventions"' in text
    assert build_html.MANIFEST["title"] in text
    assert f'v{build_html.MANIFEST["version"]}' in text
    assert build_html.MANIFEST["author"] in text
    assert build_html.MANIFEST["license"] in text
    assert "CITATION.cff" in text
    assert "勘误" in text
    assert "实测 / 合成 / 参考 / 独立真值" in text


def test_index_html_lists_terms_once_and_reserves_number_column():
    text = build_html._index_html(["SOC", "NIS"])

    assert 'id="book-index"' in text
    assert text.count('data-index-term="SOC"') == 1
    assert text.count('data-index-term="NIS"') == 1
    assert text.count('class="book-index__refs"') == 2


def _index_fixture(path: Path) -> fitz.Document:
    document = fitz.open()
    document.new_page().insert_text((72, 80), "COVER", fontsize=12)
    document.new_page().insert_text((72, 80), "SOC NIS", fontsize=12)
    document.new_page().insert_text((72, 80), "SOC", fontsize=12)
    glossary = document.new_page()
    glossary.insert_text((72, 80), "APPENDIX C", fontsize=12)
    glossary.insert_text((72, 100), "SOC NIS", fontsize=12)
    index = document.new_page()
    index.insert_text((72, 60), "INDEX", fontsize=16)
    index.insert_text((72, 100), "SOC", fontsize=12)
    index.insert_text((72, 120), "NIS", fontsize=12)
    document.set_toc([
        [1, "BACK MATTER", 4],
        [2, "附录 C 术语表", 4],
        [2, "索引", 5],
    ])
    document.save(path)
    document.close()
    return fitz.open(path)


def test_stamp_index_refs_points_to_body_and_excludes_glossary(tmp_path):
    path = tmp_path / "index.pdf"
    document = _index_fixture(path)
    try:
        refs = build_html._stamp_index_refs(document, fitz, ["SOC", "NIS"])
        assert refs == {"SOC": [1, 2], "NIS": [1]}
        assert _index_findings(document, ["SOC", "NIS"]) == []
    finally:
        document.close()


def test_index_contract_rejects_missing_term_entry(tmp_path):
    path = tmp_path / "index.pdf"
    document = _index_fixture(path)
    try:
        findings = _index_findings(document, ["SOC", "NIS", "R0"])
        assert any("R0" in finding for finding in findings)
    finally:
        document.close()


def test_term_matcher_requires_word_boundaries_for_ascii_terms():
    """ASCII 缩写不许命中别人的词干：EMS≠Systems、SPM≠SPMe、OTA≠total、CAN≠scan。"""
    assert not contains_term("EMS", "Battery Management Systems")
    assert not contains_term("SPM", "SPMe 增加电解液动力学")
    assert not contains_term("OTA", "total 充电电量")
    assert not contains_term("CAN", "scan 一遍寄存器")
    assert contains_term("EMS", "EMS 调度上层功率")
    assert contains_term("SPM", "SPM 单粒子模型")
    assert contains_term("CAN", "CAN 总线仲裁")
    assert contains_term("CAN", "CAN bus 上的仲裁")
    assert not contains_term("CAN", "can bus 上的仲裁")
    assert not contains_term("CAN", "https://example.com/can/bus")
    # 换行是硬边界：跨行拼出来的词不算命中
    assert not contains_term("回放", "返回\n放电")
    assert not contains_term("木桶效应", "木桶效\n应")
    # 中文术语按字面匹配，子串命中是期望行为（均衡 ⊂ 被动均衡）
    assert contains_term("均衡", "被动均衡只能微调")


def test_index_term_rect_accepts_right_column_of_two_column_row(tmp_path):
    """双栏索引把左右两条词条排进同一物理行：右栏词条靠「前一词条的页码串」定位。"""
    import fitz

    document = fitz.open()
    document.new_page().insert_text((72, 80), "COVER", fontsize=12)
    document.new_page().insert_text((72, 80), "SOC 出现在正文", fontsize=12)
    index = document.new_page()
    index.insert_text((72, 100), "均衡 5, 23 安时积分 34", fontsize=12)
    document.set_toc([[1, "卷末", 3], [2, "索引", 3]])
    path = tmp_path / "twocol.pdf"
    document.save(path)
    document.close()
    document = fitz.open(path)
    try:
        left = index_term_rect(document, 2, "均衡")
        right = index_term_rect(document, 2, "安时积分")
        assert left is not None and right is not None
        assert left[0] == right[0] == 2
        assert right[1].x0 > left[1].x0, "右栏词条应在左栏词条之后"
    finally:
        document.close()


def _header_fixture(path: Path) -> fitz.Document:
    """词条页上方带书名页眉：页眉里也含 `BMS`，取词条行时不许取到它。"""
    document = fitz.open()
    document.new_page().insert_text((72, 80), "COVER", fontsize=12)
    document.new_page().insert_text((72, 80), "BMS 出现在正文", fontsize=12)
    index = document.new_page()
    index.insert_text((42, 20), "BMS 实战", fontsize=7.5)
    index.insert_text((72, 100), "BMS", fontsize=12)
    document.set_toc([[1, "卷末", 3], [2, "索引", 3]])
    document.save(path)
    document.close()
    return fitz.open(path)


def test_index_term_rect_ignores_running_header(tmp_path):
    document = _header_fixture(tmp_path / "header.pdf")
    try:
        target = index_term_rect(document, 2, "BMS")
        assert target is not None
        page_index, rect = target
        assert page_index == 2
        assert rect.y0 > 30, "页眉里的 BMS 不能被当成词条行"
    finally:
        document.close()


def test_index_findings_rejects_wrong_stamped_page_number(tmp_path):
    path = tmp_path / "index.pdf"
    document = _index_fixture(path)
    try:
        index_page = document[4]
        index_page.insert_text(
            (index_page.rect.width - 60, 108), "99", fontname="helv", fontsize=8
        )
        findings = _index_findings(document, ["SOC"])
        assert any("页码" in finding for finding in findings), findings
    finally:
        document.close()
