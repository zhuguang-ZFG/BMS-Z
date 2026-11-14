#!/usr/bin/env python3
"""16K PDF：补白、罗马/阿拉伯标签、三级书签、000 回填、页眉页脚。"""
import re
import sys
import tempfile
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book.manifest import BookError  # noqa: E402
from book.pdf import (  # noqa: E402
    _page_starts, _region_links, check_pdf, pad_to_multiple, print_pdf, stamp_pdf)

try:
    import fitz
except ImportError:  # pragma: no cover
    fitz = None

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

MM = 72 / 25.4

MANIFEST = {
    "title": "通往模拟电路之路", "subtitle": "从欧姆定律到芯片内部结构",
    "author": "zhuguang-ZFG 与贡献者", "license": "CC BY-SA 4.0",
    "release": {"edition_status": "draft"},
}

TOC = [
    {"level": 1, "title": "第一篇 测试", "anchor": "part-i", "kind": "part"},
    {"level": 2, "title": "第 0 章 测试章", "anchor": "page-p1-01-ch0",
     "kind": "chapter"},
    {"level": 3, "title": "0.1 测试小节", "anchor": "p1-01-ch0--s1",
     "kind": "section"},
    {"level": 3, "title": "0.2 测试小节二", "anchor": "p1-01-ch0--s2",
     "kind": "section"},
    {"level": 1, "title": "附录 A 测试", "anchor": "appendix-a", "kind": "appendix"},
    {"level": 2, "title": "附录 B 速查", "anchor": "page-p0-08-cheatsheet",
     "kind": "appendix"},
]
LOF = [{"caption": "图 0-1　测试图", "anchor": "p1-01-ch0--fig-1"}]
LOT = [{"caption": "表 0-1　测试表", "anchor": "p1-01-ch0--table-1"}]


def _rows(entries):
    return "".join(
        f'<div class="toc-row"><a href="#{e["anchor"]}">'
        f'{e.get("title") or e["caption"]}<span class="toc-page">000</span></a></div>'
        for e in entries)


TOC_HTML = '<nav><div class="toc-list">' + _rows(TOC) + "</div></nav>"
LOF_HTML = '<nav><div class="toc-list">' + _rows(LOF) + "</div></nav>"
LOT_HTML = '<nav><div class="toc-list">' + _rows(LOT) + "</div></nav>"
PARAGRAPHS = "".join(
    "<p>" + ("测试正文用于把章节撑到多页，验证续页页眉与页脚。" * 3) + "</p>"
    for _ in range(80))
CHAPTER_HTML = (
    '<h1 id="page-p1-01-ch0">第 0 章 测试章</h1>'
    '<h2 id="p1-01-ch0--s1">0.1 测试小节</h2>'
    '<h2 id="p1-01-ch0--s2">0.2 测试小节二</h2>'
    '<figure id="p1-01-ch0--fig-1"><p>图</p><figcaption>图 0-1 测试图</figcaption></figure>'
    '<table id="p1-01-ch0--table-1"><caption>表 0-1 测试表</caption>'
    '<tr><th>列</th></tr><tr><td>值</td></tr></table>' + PARAGRAPHS)


def _page(kind, page_id, title, group, body, **extra):
    page = {"kind": kind, "id": page_id, "title": title, "group": group,
            "html": body}
    page.update(extra)
    return page


FRONT = [
    # 与真实书一致：半书名页与书名页的 h1 都是 manifest 标题，按页序依次匹配。
    _page("half_title", "half-title", "半书名", "front",
          f'<h1 class="book-title">{MANIFEST["title"]}</h1>'),
    _page("title_page", "title-page", "书名页", "front",
          f'<h1 id="title-page">{MANIFEST["title"]}</h1>'),
    _page("copyright", "copyright", "版权页", "front",
          '<h1 id="copyright">版权页</h1>'),
    _page("front", "page-front-a", "前言", "front",
          '<h1 id="page-front-a">前言</h1>'),
    _page("front", "page-front-b", "导读", "front",
          '<h1 id="page-front-b">导读</h1>'),
    _page("front", "page-front-c", "简史", "front",
          '<h1 id="page-front-c">简史</h1>'),
    _page("front", "page-front-d", "约定", "front",
          '<h1 id="page-front-d">约定</h1>'),
    _page("toc", "book-toc", "全书目录", "front",
          '<h1 id="book-toc">全书目录</h1>' + TOC_HTML),
    _page("list_of_figures", "list-of-figures", "插图目录", "front",
          '<h1 id="list-of-figures">插图目录</h1>' + LOF_HTML),
    _page("list_of_tables", "list-of-tables", "表格目录", "front",
          '<h1 id="list-of-tables">表格目录</h1>' + LOT_HTML),
    _page("front", "page-front-e", "符号", "front",
          '<h1 id="page-front-e">符号</h1>'),
]
BODY = [
    _page("part", "part-i", "第一篇 测试", "body",
          '<h1 id="part-i">第一篇 测试</h1>'),
    _page("chapter", "page-p1-01-ch0", "第 0 章 测试章", "body",
          CHAPTER_HTML, header="第一篇 测试"),
    _page("appendix_opener", "appendix-a", "附录 A 测试", "appendix",
          '<h1 id="appendix-a">附录 A 测试</h1>'),
    _page("appendix", "page-p0-08-cheatsheet", "附录 B 速查", "appendix",
          '<h2 id="page-p0-08-cheatsheet">附录 B 速查</h2>',
          source="docs/appendix-b.md"),
]
BACK = [
    _page("bibliography", "bibliography", "参考文献", "back",
          '<h1 id="bibliography">参考文献</h1>'),
    # assemble._model_kind 把索引页映射为 kind="back"（真实模型形状）。
    _page("back", "book-index", "索引", "back",
          '<h1 id="book-index">索引</h1>'
          '<p><a href="#page-p1-01-ch0"><strong>测试术语</strong></a>'
          '<a href="#p1-01-ch0--s1"><span class="index-page">000</span></a></p>'),
    _page("back", "page-p9-12-changelog", "版本记录", "back",
          '<h1 id="page-p9-12-changelog">版本记录</h1>'),
    _page("colophon", "colophon", "版本页", "back",
          '<h1 id="colophon">版本页</h1>'),
]
PAGES = FRONT + BODY + BACK
MODEL = {
    "schema": 1, "manifest_sha256": "0" * 64, "edition_status": "draft",
    "pages": PAGES, "toc": TOC, "lof": LOF, "lot": LOT,
    "figures": 1, "tables": 1, "endnotes": 0,
    "audit": {"errors": [], "warnings": [], "pages": len(PAGES), "bytes": 0},
    "stats": {"logical_pages": len(PAGES), "images": 1, "formulas": 0,
              "chapters": {}},
}


def synthetic_html():
    body = "\n".join(
        f'<section class="book-page">{page["html"]}</section>'
        for page in PAGES)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: 185mm 260mm; margin: 20mm; }}
html, body {{ margin: 0; }}
body {{ font-family: serif; font-size: 10.5pt; line-height: 17.5pt; }}
.book-page {{ break-before: page; }}
.book-page:first-of-type {{ break-before: auto; }}
h1 {{ font-size: 22pt; }}
.toc-list {{ column-count: 2; column-gap: 6mm; }}
.toc-row {{ break-inside: avoid; }}
.toc-row a {{ display: flex; justify-content: space-between; }}
figure, table {{ break-inside: avoid; }}
</style></head><body>
{body}
</body></html>"""


def _link_key(link):
    rect = link["from"]
    target = link.get("to")
    point = None if target is None else (round(target.x, 1), round(target.y, 1))
    return (link.get("kind"), round(rect.x0, 1), round(rect.y0, 1),
            round(rect.x1, 1), round(rect.y1, 1), link.get("page"), point,
            link.get("uri"), link.get("file"), link.get("nameddest"))


def _spans(page, clip=None):
    data = page.get_text("dict", clip=clip)
    return [span for block in data["blocks"] for line in block.get("lines", [])
            for span in line["spans"]]


def _stamp_basefont(page):
    """从 bookstamp 资源解析文本提取所报的 basefont。

    PyMuPDF 1.28 的 Type0 资源 BaseFont 是全名（Noto Sans SC Thin Regular），
    而 span["font"] 用下级 CIDFont 的 BaseFont（NotoSansSC-Thin），故沿
    DescendantFonts 取真正的 basefont。
    """
    entry = next(entry for entry in page.get_fonts()
                 if entry[4] == "bookstamp")
    descendant = page.parent.xref_get_key(entry[0], "DescendantFonts")
    match = re.search(r"(\d+) 0 R", descendant[1])
    if match:
        basefont = page.parent.xref_get_key(int(match.group(1)), "BaseFont")
        if basefont[0] == "name":
            return entry, basefont[1].lstrip("/")
    return entry, entry[3].split("+", 1)[-1]


@unittest.skipIf(fitz is None or sync_playwright is None,
                 "需要 PyMuPDF 与 Playwright")
class PdfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root = Path(cls.tmp.name)
        cls.html = cls.root / "synthetic.html"
        cls.html.write_text(synthetic_html(), encoding="utf-8")
        cls.raw = cls.root / "raw.pdf"
        print_pdf(cls.html, cls.raw)
        raw = fitz.open(cls.raw)
        cls.raw_links = {
            pno: sorted(_link_key(link) for link in raw[pno].get_links())
            for pno in range(raw.page_count)}
        raw.close()
        cls.pdf = cls.root / "stamped.pdf"
        cls.report = stamp_pdf(cls.raw, cls.pdf, MODEL, MANIFEST)
        cls.doc = fitz.open(cls.pdf)

    @classmethod
    def tearDownClass(cls):
        cls.doc.close()

    def test_page_is_16k_and_padded_to_four(self):
        self.assertEqual(0, self.report["pages"] % 4)
        for page in self.doc:
            self.assertAlmostEqual(185, page.rect.width / MM, delta=0.5)
            self.assertAlmostEqual(260, page.rect.height / MM, delta=0.5)
        self.assertTrue(self.report["padded"])

    def test_page_labels_are_roman_then_arabic(self):
        self.assertEqual("i", self.doc[0].get_label())
        self.assertEqual("xi", self.doc[10].get_label())
        self.assertEqual("1", self.doc[self.report["body_start"]].get_label())
        self.assertEqual("2", self.doc[self.report["body_start"] + 1].get_label())

    def test_bookmarks_are_three_levels_from_model(self):
        toc = self.doc.get_toc()
        self.assertEqual([1, 2, 3, 3, 1, 2], [entry[0] for entry in toc])
        self.assertEqual([entry["title"] for entry in MODEL["toc"]],
                         [entry[1] for entry in toc])
        starts = self.report["starts"]
        self.assertEqual(
            [starts[11] + 1, starts[12] + 1, starts[12] + 1,
             starts[12] + 1, starts[13] + 1, starts[14] + 1],
            [entry[2] for entry in toc])

    def test_appendix_h2_participates_in_page_starts(self):
        raw = fitz.open(self.raw)
        try:
            self.assertIn([2, "附录 B 速查", self.report["starts"][14] + 1],
                          raw.get_toc())
        finally:
            raw.close()

    def test_duplicate_front_headings_match_in_order(self):
        raw = fitz.open(self.raw)
        try:
            toc = raw.get_toc()
        finally:
            raw.close()
        self.assertEqual([(1, MANIFEST["title"]), (1, MANIFEST["title"])],
                         [(entry[0], entry[1]) for entry in toc[:2]])
        self.assertEqual([0, 1], self.report["starts"][:2])

    def test_two_column_toc_links_keep_dom_order(self):
        starts = self.report["starts"]
        links = [link for link in self.doc[starts[7]].get_links()
                 if isinstance(link.get("page"), int)]
        columns = {round(link["from"].x0, 1) for link in links}
        self.assertEqual(2, len(columns), "目录必须排成双栏")
        self.assertGreater(max(columns) - min(columns), 100)
        self.assertEqual([starts[11], starts[12], starts[12], starts[12],
                          starts[13], starts[14]],
                         [link["page"] for link in links])

    def test_region_links_keep_annotation_order(self):
        # Chromium 的链接注记顺序即 DOM/阅读顺序；按坐标排序会把右栏行插进左栏行。
        # 小节 2 位于右栏，坐标排序会把它的目标错配到附录 A 页。
        raw = fitz.open(self.raw)
        try:
            links = _region_links(
                raw, self.report["starts"][7], self.report["starts"][8],
                self.report["body_start"])
        finally:
            raw.close()
        starts = self.report["starts"]
        self.assertEqual(
            [starts[11], starts[12], starts[12], starts[12],
             starts[13], starts[14]],
            [link["target"] for link in links])

    def test_links_survive_backfill(self):
        starts = self.report["starts"]
        for pno in (starts[7], starts[8], starts[9], starts[16]):
            after = sorted(_link_key(link) for link in self.doc[pno].get_links())
            self.assertEqual(self.raw_links[pno], after, f"物理页 {pno}")

    def test_000_is_backfilled_and_links_survive(self):
        starts = self.report["starts"]
        regions = [(starts[7], starts[8]), (starts[8], starts[9]),
                   (starts[9], starts[10]), (starts[16], starts[17])]
        for begin, end in regions:
            text = "\n".join(self.doc[p].get_text() for p in range(begin, end))
            self.assertNotIn("000", text)
        # 索引夹具故意把术语与 000 排成无空格的一行（测试术语000）；
        # 红条必须只删三个零，不能连带删掉前面的术语。
        self.assertIn("测试术语", self.doc[starts[16]].get_text())
        self.assertEqual(9, self.report["backfilled"])
        toc_links = [link for link in self.doc[starts[7]].get_links()
                     if isinstance(link.get("page"), int)]
        self.assertEqual(len(TOC), len(toc_links))

    def test_openers_and_front_pages_have_no_folio(self):
        starts = self.report["starts"]
        height = self.doc[0].rect.height
        clip = fitz.Rect(0, height - 18 * MM, self.doc[0].rect.width, height)
        for pno in (0, 1, 2, starts[11], starts[12], starts[13]):
            self.assertEqual("", self.doc[pno].get_text("text", clip=clip).strip())
        continuation = starts[12] + 1
        self.assertTrue(self.doc[continuation].get_text("text", clip=clip).strip())

    def test_running_heads_use_outer_edge_and_chapter_title(self):
        starts = self.report["starts"]
        clip = fitz.Rect(0, 0, self.doc[0].rect.width, 18 * MM)
        chapter_start = starts[12]
        left_page = chapter_start + 1
        right_page = chapter_start + 2
        self.assertEqual(1, left_page % 2, "物理奇数页必须是左页")
        self.assertEqual(0, right_page % 2, "物理偶数页必须是右页")
        left_text = self.doc[left_page].get_text("text", clip=clip)
        right_text = self.doc[right_page].get_text("text", clip=clip)
        self.assertIn("通往模拟电路之路", left_text)
        self.assertIn("第 0 章 测试章", right_text)
        self.assertNotIn("第一篇 测试", right_text)

    def test_running_heads_and_folios_hug_outer_edge(self):
        starts = self.report["starts"]
        width = self.doc[0].rect.width
        height = self.doc[0].rect.height
        chapter_start = starts[12]
        left_page = chapter_start + 1
        right_page = chapter_start + 2
        top = fitz.Rect(0, 0, width, 18 * MM)
        bottom = fitz.Rect(0, height - 18 * MM, width, height)

        left_head = self.doc[left_page].get_text("words", clip=top)
        self.assertTrue(left_head)
        self.assertAlmostEqual(18 * MM, min(w[0] for w in left_head), delta=2)
        right_head = self.doc[right_page].get_text("words", clip=top)
        self.assertTrue(right_head)
        self.assertAlmostEqual(width - 18 * MM, max(w[2] for w in right_head),
                               delta=2)
        left_folio = self.doc[left_page].get_text("words", clip=bottom)
        self.assertTrue(left_folio)
        self.assertAlmostEqual(18 * MM, min(w[0] for w in left_folio), delta=2)
        right_folio = self.doc[right_page].get_text("words", clip=bottom)
        self.assertTrue(right_folio)
        self.assertAlmostEqual(width - 18 * MM, max(w[2] for w in right_folio),
                               delta=2)

    def test_backfill_and_folios_use_embedded_stamp_font(self):
        starts = self.report["starts"]
        width = self.doc[0].rect.width
        height = self.doc[0].rect.height
        top = fitz.Rect(0, 0, width, 18 * MM)
        bottom = fitz.Rect(0, height - 18 * MM, width, height)
        for pno in (starts[7], starts[12] + 1, starts[12] + 2):
            page = self.doc[pno]
            entries = [font for font in page.get_fonts()
                       if font[4] == "bookstamp"]
            self.assertTrue(entries, f"物理页 {pno} 缺少 bookstamp 字体")
            entry, basefont = _stamp_basefont(page)
            self.assertEqual("ttf", entry[1])
            self.assertNotIn("helvetica", basefont.lower())
            for font in page.get_fonts():
                self.assertNotIn("helv", font[4].lower())
                self.assertNotIn("helvetica", font[3].lower())
            if pno == starts[7]:
                digits = [span for span in _spans(page)
                          if re.fullmatch(r"\d+", span["text"])]
                self.assertTrue(digits, f"物理页 {pno} 没有数字回填 span")
                for span in digits:
                    self.assertEqual(basefont, span["font"])
            for clip in (top, bottom):
                spans = _spans(page, clip)
                self.assertTrue(spans)
                for span in spans:
                    self.assertEqual(basefont, span["font"],
                                     (pno, span["text"]))

    def test_check_pdf_reports_draft_length_without_failing(self):
        report = check_pdf(self.pdf, MODEL, MANIFEST)
        self.assertEqual([], report["problems"])
        self.assertTrue(any("450" in warning for warning in report["warnings"]))
        width, height = report["size_mm"]
        self.assertAlmostEqual(185, width, delta=0.5)
        self.assertAlmostEqual(260, height, delta=0.5)

    def test_check_pdf_final_mode_uses_hard_bands(self):
        final_manifest = {**MANIFEST, "release": {"edition_status": "final"}}
        report = check_pdf(self.pdf, MODEL, final_manifest)
        self.assertTrue(any("450" in problem for problem in report["problems"]))
        self.assertTrue(any("535" in warning for warning in report["warnings"]))

    def test_check_pdf_skips_whole_book_bands_for_a_single_volume(self):
        volume_model = {**MODEL, "volume": 1, "volume_label": "上卷"}
        final_manifest = {**MANIFEST, "release": {"edition_status": "final"}}
        for manifest in (MANIFEST, final_manifest):
            report = check_pdf(self.pdf, volume_model, manifest)
            self.assertEqual([], report["problems"])
            for text in ("450", "535", "653"):
                self.assertFalse(
                    any(text in warning for warning in report["warnings"]),
                    (manifest["release"]["edition_status"], text,
                     report["warnings"]))

    def test_check_pdf_still_caps_a_single_volume_at_700_pages(self):
        volume_model = {**MODEL, "volume": 1, "volume_label": "上卷"}
        oversized = Path(self.tmp.name) / "oversized.pdf"
        doc = fitz.open()
        try:
            for _ in range(704):
                doc.new_page(width=185 * MM, height=260 * MM)
            doc.save(oversized)
        finally:
            doc.close()
        report = check_pdf(oversized, volume_model, MANIFEST)
        self.assertTrue(any("700" in problem for problem in report["problems"]),
                        report["problems"])

    def test_pad_to_multiple_is_idempotent(self):
        doc = fitz.open(self.pdf)
        try:
            before = doc.page_count
            padded = pad_to_multiple(doc, 4)
            self.assertEqual([], padded)
            self.assertEqual(before, doc.page_count)
        finally:
            doc.close()


class PageStartsOutlineTests(unittest.TestCase):
    """Chromium 折行会吞掉断点处的空格，大纲比对必须忽略空白差异。"""

    class Doc:
        def __init__(self, toc):
            self._toc = toc

        def get_toc(self):
            return self._toc

    @staticmethod
    def model(title):
        return {"pages": [{
            "id": "page-p1-01-ch0",
            "group": "chapter",
            "source": "p1-01-ch0.md",
            "html": "<h1>%s</h1>" % title,
        }]}

    def test_space_lost_by_line_wrap_still_matches(self):
        outline = self.Doc([(1, "第 0 章 BJT三极管：完整概念体系", 1)])
        starts = _page_starts(outline, self.model("第 0 章 BJT 三极管：完整概念体系"))
        self.assertEqual([0], starts)

    def test_different_title_still_rejected(self):
        outline = self.Doc([(1, "第 0 章 二极管：单向导电", 1)])
        with self.assertRaises(BookError):
            _page_starts(outline, self.model("第 0 章 BJT 三极管：完整概念体系"))


class PageStartsOrderingTests(unittest.TestCase):
    """模型页序在物理页上必须递增；附录题页与内容页同页连排是唯一例外。"""

    class Doc:
        def __init__(self, toc):
            self._toc = toc

        def get_toc(self):
            return self._toc

    @staticmethod
    def chapter(pid, title):
        return {"id": pid, "kind": "chapter", "group": "chapter",
                "source": f"{pid}.md", "html": f"<h1>{title}</h1>"}

    def test_appendix_opener_may_share_page_with_content(self):
        model = {"pages": [
            {"id": "appendix-a", "kind": "appendix_opener",
             "group": "appendix", "html": "<h1>附录 A 卷末资料</h1>"},
            {"id": "appendix-a-table", "kind": "appendix",
             "group": "appendix", "source": "a.md",
             "html": "<h2>附录 A 速查表</h2>"},
        ]}
        outline = self.Doc([(1, "附录 A 卷末资料", 6), (2, "附录 A 速查表", 6)])
        self.assertEqual([5, 5], _page_starts(outline, model))

    def test_same_page_still_rejected_without_opener(self):
        model = {"pages": [
            self.chapter("page-p1-01-ch0", "第 0 章 甲"),
            self.chapter("page-p1-02-ch1", "第 1 章 乙"),
        ]}
        outline = self.Doc([(1, "第 0 章 甲", 6), (1, "第 1 章 乙", 6)])
        with self.assertRaises(BookError):
            _page_starts(outline, model)

    def test_out_of_order_still_rejected(self):
        model = {"pages": [
            self.chapter("page-p1-01-ch0", "第 0 章 甲"),
            self.chapter("page-p1-02-ch1", "第 1 章 乙"),
        ]}
        outline = self.Doc([(1, "第 0 章 甲", 6), (1, "第 1 章 乙", 5)])
        with self.assertRaises(BookError):
            _page_starts(outline, model)


if __name__ == "__main__":
    unittest.main()
