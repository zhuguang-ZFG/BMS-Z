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
    from check_pdf import _index_findings, _notdef_findings
    from index_terms import contains_term, index_label, index_term_rect
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


def test_notdef_gate_accepts_pdf_with_cjk_coverage(tmp_path):
    """有中文字体覆盖（china-s/Heiti）的页面不许报豆腐块。"""
    path = tmp_path / "healthy.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 100), "安时积分与功能安全", fontname="china-s", fontsize=12)
    document.save(path)
    document.close()
    document = fitz.open(path)
    try:
        assert _notdef_findings(document) == []
    finally:
        document.close()


def test_notdef_gate_flags_missing_cjk_coverage(tmp_path):
    """真实的 Linux CI 病灶复现：拉丁字形集印汉字落到 gid 0，必须是红灯。

    `fitz.Font("helv")` 的 NimbusSans 只带拉丁字形，插入汉字时 PyMuPDF 落
    .notdef——这正是 ubuntu-24.04 runner 缺 fonts-noto-cjk 时 Chrome 的行为。
    """
    font_path = tmp_path / "nimbus.ttf"
    font_path.write_bytes(fitz.Font("helv").buffer)
    path = tmp_path / "tofu.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 100), "安时积分", fontname="latin-only", fontfile=str(font_path), fontsize=12)
    document.save(path)
    document.close()
    document = fitz.open(path)
    try:
        findings = _notdef_findings(document)
        assert len(findings) == 1, findings
        assert "第 1 页" in findings[0], findings
        assert "fonts-noto-cjk" in findings[0], findings
    finally:
        document.close()


def test_index_label_appends_ellipsis_only_beyond_six():
    """省略号是「还有」的信号：恰好六页不加，第七页才加。"""
    assert index_label([1, 2]) == "1, 2"
    assert index_label([1, 2, 3, 4, 5, 6]) == "1, 2, 3, 4, 5, 6"
    assert index_label([1, 2, 3, 4, 5, 6, 7]) == "1, 2, 3, 4, 5, 6, ..."


def test_index_findings_rejects_false_ellipsis(tmp_path):
    """≤6 个命中却盖了「...」必须报红——虚报的省略号会让读者以为漏了页。"""
    path = tmp_path / "index.pdf"
    document = _index_fixture(path)
    try:
        index_page = document[4]
        # 基线 104：盖戳词中心 ≈102，词条行中心 ≈98，落在 gate 的 ±7pt 窗口内
        index_page.insert_text(
            (index_page.rect.width - 120, 104), "1, 2, ...", fontname="helv", fontsize=8
        )
        findings = _index_findings(document, ["SOC"])
        assert any("省略号" in finding for finding in findings), findings
    finally:
        document.close()


def test_safety_chain_table_rows_match_its_declared_step_count():
    """第 25 章 §25.1 的安全链：正文说几步，表里就得有几行。

    初稿在这里失配过：正文写「链条同样七步」，但示例只列了四步（危害分析／
    ASIL／安全目标／技术安全需求），剩下三步（场景分析、功能安全要求、验证）
    只出现在另一段 300 字的破折号长句里。读者按「七步」去数，数不出来。
    现在两个危害并排走同一张七行骨架，这条测试把「声明的步数 == 表格行数」钉住。
    """
    chapter = (ROOT / "book" / "25-功能安全与量产.md").read_text(encoding="utf-8")
    section = chapter[chapter.index("## 25.1"):chapter.index("## 25.2")]

    rows = [line for line in section.splitlines()
            if line.startswith("| ") and not line.startswith("|---")
            and not line.startswith("| 步 ")]
    assert len(rows) == 7, f"表 25-1 应有七行步骤，实际 {len(rows)}"

    # 每一步都要带序号，且 1..7 连续不跳号。
    numbers = [int(row.split()[1]) for row in rows]
    assert numbers == list(range(1, 8)), f"步骤编号应为 1..7，实际 {numbers}"

    # 两个危害各占一列，七行都不能留空。
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert len(cells) == 3, f"每行应为「步 + 两个危害」三格：{row[:40]}"
        assert all(cells), f"七行里不许有空格子：{row[:40]}"

    # 正文若再写「共 N 步」这类基数声明，N 必须等于表格行数。
    # 「第 N 步」是序数（指第几步），不是步数声明，要排除——否则「第 3 步的三问」
    # 会被误读成「声明只有 3 步」。
    import re
    digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    # 「第 N 步」里 第 与数字之间可能有空格，所以连空白一起排除。
    # 「后面四步」这类说的是表格的一个子区间，不是总步数，单独列白。
    subrange_ok = {"后面四步"}
    for match in re.finditer(r"(第\s*)?([一二三四五六七八九十]|\d+)\s*步", section):
        if match.group(1):            # 序数：第 N 步
            continue
        phrase = section[max(0, match.start() - 2):match.end()]
        if any(ok in phrase for ok in subrange_ok):
            continue
        claim = match.group(2)
        value = int(claim) if claim.isdigit() else digits[claim]
        assert value == 7, f"正文声明「{claim}步」与表格七行不一致（上下文：{phrase}）"


def test_chapter_25_section_cross_references_resolve():
    """表 25-1 引用了 §32.3、§32.5、§8.3——必须真的存在。"""
    book = ROOT / "book"
    targets = {
        "32.3": "32-高压安全与绝缘检测.md",
        "32.5": "32-高压安全与绝缘检测.md",
        "8.3": "08-硬件失效与二次保护.md",
    }
    for ref, filename in targets.items():
        text = (book / filename).read_text(encoding="utf-8")
        assert f"## {ref} " in text, f"§{ref} 在 {filename} 里不存在"
