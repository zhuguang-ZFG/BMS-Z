"""跨卷离线阅读与 PDF 重排的回归，不依赖大型 dist 产物。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from combined_epub import (
    IDENTIFIER,
    N,
    X,
    make_nav,
    make_ncx,
    nav_list,
    rewrite_links,
    link_print_references,
    xml,
    normalize_content,
    content_properties,
    validate_chapter_references,
)
from combined_front import text, xhtml
from combined_pdf import build, validate, page_label_rules


class EpubReadingTests(unittest.TestCase):
    def test_legacy_markup_migration_preserves_prose_and_author_css(self):
        files = {
            "v1/nav.xhtml": xhtml(
                "目录",
                '<nav xmlns:epub="http://www.idpf.org/2007/epub" epub:type="toc"><p align="center" style="color:red">居中批注</p><img align="right" src="a.png" alt="图"/></nav>',
            )
        }
        before = "".join(xml(files["v1/nav.xhtml"]).itertext())
        changes = normalize_content(files)
        root = xml(files["v1/nav.xhtml"])
        self.assertEqual(changes, {"namespaces": 1, "align_attributes": 2})
        self.assertEqual("".join(root.itertext()), before)
        self.assertEqual(
            next(root.iter(X + "nav")).get("{http://www.idpf.org/2007/ops}type"), "toc"
        )
        self.assertEqual(
            next(root.iter(X + "p")).get("style"), "text-align:center;color:red"
        )
        self.assertEqual(next(root.iter(X + "img")).get("style"), "float:right;")
        self.assertFalse(root.xpath("//*[@align]"))

    def test_embedded_vocabularies_declared_but_linked_svg_is_not_inline(self):
        self.assertEqual(
            content_properties(xhtml("正文", '<img src="a.svg" alt="图"/>')), set()
        )
        self.assertEqual(
            content_properties(
                xhtml(
                    "正文",
                    '<svg xmlns="http://www.w3.org/2000/svg"/><math xmlns="http://www.w3.org/1998/Math/MathML"/>',
                )
            ),
            {"svg", "mathml"},
        )

    def test_cross_volume_link_targets_real_heading(self):
        files = {
            "v1/text/chapter.xhtml": xhtml(
                "卷一",
                '<p><a href="https://example.test/../../bms-book/book/06-AFE.md">AFE</a></p>',
            ),
            "v2/book.xhtml": xhtml(
                "卷二", '<h2 id="actual-afe-heading">第 6 章 AFE</h2>'
            ),
        }
        log = rewrite_links(
            files, {}, {"06-AFE.md": "v2/book.xhtml#actual-afe-heading"}
        )
        a = next(xml(files["v1/text/chapter.xhtml"]).iter(X + "a"))
        self.assertEqual(a.get("href"), "../../v2/book.xhtml#actual-afe-heading")
        self.assertEqual(len(log), 1)

    def test_unresolved_cross_volume_target_fails(self):
        files = {
            "v1/a.xhtml": xhtml(
                "卷一",
                '<a href="https://example.test/bms-book/book/missing.md">目标</a>',
            )
        }
        with self.assertRaisesRegex(ValueError, "无合集目标"):
            rewrite_links(files, {}, {})

    def test_reverse_link_preserves_namespaced_fragment(self):
        files = {
            "v2/book.xhtml": xhtml(
                "卷二",
                '<a href="https://example.test/analog/docs/ch6.md#gain">增益</a>',
            ),
            "v1/ch6.xhtml": xhtml("卷一", '<h2 id="ch6--gain">增益</h2>'),
        }
        rewrite_links(files, {}, {"ch6.md": "v1/ch6.xhtml"})
        self.assertEqual(
            next(xml(files["v2/book.xhtml"]).iter(X + "a")).get("href"),
            "../v1/ch6.xhtml#ch6--gain",
        )

    def test_removed_shared_section_references_redirect(self):
        files = {
            "v2/book.xhtml": xhtml(
                "卷二", '<a href="#shared-01-reading-guide">导读</a>'
            )
        }
        rewrite_links(
            files, {"v2/book.xhtml#shared-01-reading-guide": "guide.xhtml"}, {}
        )
        self.assertEqual(
            next(xml(files["v2/book.xhtml"]).iter(X + "a")).get("href"),
            "../guide.xhtml",
        )

    def test_plain_references_link_both_text_and_tail_without_changing_prose(self):
        files = {
            "v1/text/ch6.xhtml": xhtml("卷一", '<h1 id="ch6">第 6 章 运放</h1>'),
            "v2/book.xhtml": xhtml(
                "卷二",
                "<p>先读卷一·第 6 章《运放》；<em>再查</em>卷一·第 6 章《运放》。</p>",
            ),
        }
        before = "".join(xml(files["v2/book.xhtml"]).itertext())
        self.assertEqual(link_print_references(files), 2)
        after = xml(files["v2/book.xhtml"])
        self.assertEqual("".join(after.itertext()), before)
        self.assertEqual(
            [a.get("href") for a in after.iter(X + "a")],
            ["../v1/text/ch6.xhtml#ch6"] * 2,
        )

    def test_nav_removes_shared_group_without_losing_chapters(self):
        data = xhtml(
            "目录",
            '<nav><ol><li><span>共享卷首</span><ol><li><a href="shared.xhtml">扉页</a></li></ol></li>'
            '<li><a href="chapter.xhtml">正文</a></li></ol></nav>',
        )
        ol = nav_list(data, "v1/", {"v1/shared.xhtml"})
        self.assertEqual(len(ol), 1)
        self.assertEqual(next(ol.iter(X + "a")).get("href"), "v1/chapter.xhtml")

    def test_numbered_quiz_headings_cannot_hijack_chapter_references(self):
        files = {
            "v1/text/ch9.xhtml": xhtml(
                "正文", '<h1 id="chapter9">第 9 章 电压基准</h1>'
            ),
            "v1/text/quiz.xhtml": xhtml(
                "自测",
                '<h1>第九篇：自测与练习</h1><h2 id="quiz9">第 9 章 电压基准</h2>',
            ),
            "v2/book.xhtml": xhtml(
                "卷二", "<h2>第 5 章 测量</h2><p>先读卷一·第 9 章《电压基准》。</p>"
            ),
        }
        self.assertEqual(link_print_references(files), 1)
        link = next(xml(files["v2/book.xhtml"]).iter(X + "a"))
        self.assertEqual(link.get("href"), "../v1/text/ch9.xhtml#chapter9")
        documents = {path: xml(data) for path, data in files.items()}
        self.assertEqual(validate_chapter_references(documents), 1)
        next(documents["v2/book.xhtml"].iter(X + "a")).set(
            "href", "../v1/text/quiz.xhtml#quiz9"
        )
        with self.assertRaisesRegex(ValueError, "non-chapter"):
            validate_chapter_references(documents)

    def test_ncx_has_same_book_id_and_no_conflicting_orders(self):
        ol1 = xml(f'<ol xmlns="{X[1:-1]}"><li><a href="v1/a.xhtml">甲</a></li></ol>')
        ol2 = xml(f'<ol xmlns="{X[1:-1]}"><li><a href="v2/b.xhtml#b">乙</a></li></ol>')
        ncx = xml(make_ncx(make_nav(ol1, ol2)))
        self.assertEqual(
            ncx.find(N + "head").find(N + "meta").get("content"), IDENTIFIER
        )
        orders = {}
        for point in ncx.iter(N + "navPoint"):
            target = point.find(N + "content").get("src")
            order = point.get("playOrder")
            self.assertEqual(orders.setdefault(order, target), target)


class PdfReadingTests(unittest.TestCase):
    def test_page_labels_follow_printed_number_gaps(self):
        with fitz.open() as doc:
            labels = [
                "Front-1",
                "I-cover",
                "I-front-2",
                "I-1",
                "I-2",
                "II-cover",
                "II-6",
                "II-7",
            ]
            for _ in labels:
                doc.new_page()
            doc.set_page_labels(page_label_rules(labels))
            self.assertEqual([p.get_label() for p in doc], labels)

    def make_source(self, path):
        with fitz.open() as doc:
            headings = [
                "分卷封面",
                "从模拟电路到 BMS",
                "两卷怎么读",
                "两卷总目录",
                "版本、许可与勘误",
                "第 1 章 正文测试",
                "附录 A 资料",
            ]
            for i, title in enumerate(headings):
                page = doc.new_page(width=595.28, height=841.89)
                text(page, title, 48, 90, 18)
                if i >= 5:
                    text(page, f"{i} / 6", 280, 815, 10)
            for target, y in [(6, 130), (2, 170)]:
                doc[5].insert_link(
                    {
                        "kind": fitz.LINK_GOTO,
                        "from": fitz.Rect(50, y, 150, y + 20),
                        "page": target,
                        "to": fitz.Point(30, 90),
                    }
                )
            doc[6].insert_link(
                {
                    "kind": fitz.LINK_URI,
                    "from": fitz.Rect(50, 130, 150, 150),
                    "uri": "https://example.test/reference",
                }
            )
            # Chromium 导出的命名目标在 PyMuPDF 中是 kind=4，也必须保留。
            doc.xref_set_key(
                doc.pdf_catalog(),
                "Names",
                f"<< /Dests << /Names [(chapter) [{doc[6].xref} 0 R /XYZ 30 751.89 0]] >> >>",
            )
            page = doc.reload_page(doc[5])
            link = page.get_links()[0]
            doc.xref_set_key(link["xref"], "A", "<< /S /GoTo /D (chapter) >>")
            doc.set_toc(
                [
                    [1, "从模拟电路到 BMS", 2],
                    [1, "两卷怎么读", 3],
                    [1, "正文", 6],
                    [2, "第 1 章 正文测试", 6],
                    [1, "附录 A 资料", 7],
                ]
            )
            doc.save(path)

    def test_rearranging_front_preserves_body_and_links(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b, out = [
                Path(directory) / name for name in ("a.pdf", "b.pdf", "combined.pdf")
            ]
            self.make_source(a)
            self.make_source(b)
            with fitz.open(a) as source:
                self.assertEqual(source[5].get_links()[0]["kind"], fitz.LINK_NAMED)
            built = build(a, b, out)
            checked = validate(out, a, b)
            self.assertEqual(built["removed_shared_pages"], [4, 4])
            self.assertEqual(checked["preserved_links_checked"], 6)
            self.assertEqual(checked["retained_text_pages_checked"], 4)
            self.assertEqual(checked["toc_links_checked"], 6)


if __name__ == "__main__":
    unittest.main()
