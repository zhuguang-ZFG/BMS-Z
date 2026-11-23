"""Broken navigation, formula resources and reading order must block an EPUB."""
import tempfile
import unittest
import zipfile
from pathlib import Path

from epub_validation import EpubError, validate_epub


class BookLinksTests(unittest.TestCase):
    def test_book_anchors_become_cross_file_links(self):
        from build_epub import rewrite_book_links
        files = {'p3-01-ch14': '027-p3-01-ch14.xhtml'}
        text = ('<a href="#p3-01-ch14--ch14">章</a>'
                '<a href="#page-p3-01-ch14">页</a>'
                '<a href="#book-toc">目录</a>'
                '<a href="#local">本节</a>')
        self.assertEqual(
            '<a href="027-p3-01-ch14.xhtml#p3-01-ch14--ch14">章</a>'
            '<a href="027-p3-01-ch14.xhtml">页</a>'
            '<a href="../nav.xhtml#toc">目录</a>'
            '<a href="#local">本节</a>', rewrite_book_links(text, files))


class SharedPagesTests(unittest.TestCase):
    def test_shared_front_is_split_into_four_titled_pages(self):
        from build_epub import shared_front_pages
        pages = shared_front_pages()
        self.assertEqual(
            ["系列扉页", "两卷怎么读", "两卷总目录", "版本、许可与勘误"],
            [page["title"] for page in pages])
        self.assertTrue(all(page["html"].strip() for page in pages))

    def test_shared_glossary_page_carries_header_and_first_term(self):
        from build_epub import shared_glossary_page
        html = shared_glossary_page()["html"]
        self.assertIn("<th>术语</th>", html)
        self.assertIn("<td>虚短/虚断</td>", html)


class FigureContentTests(unittest.TestCase):
    def test_legacy_alignment_preserves_layout_with_css(self):
        from lxml import etree
        from build_epub import xhtml
        doc = etree.fromstring(xhtml("alignment", '<p align="center" style="color:red">文字</p>'
                                    '<img align="center" src="figure.svg"/>'
                                    '<table align="right"><tr><td>表</td></tr></table>').encode())
        self.assertFalse(doc.xpath('//*[@align]'))
        namespace = {"h": "http://www.w3.org/1999/xhtml"}
        self.assertEqual('text-align:center;color:red', doc.find('.//h:p', namespace).get('style'))
        self.assertIn('margin-left:auto', doc.find('.//h:img', namespace).get('style'))
        self.assertIn('float:right', doc.find('.//h:table', namespace).get('style'))

    def test_navigation_and_manifest_describe_epub_content(self):
        from lxml import etree
        from build_epub import nav_doc, opf
        nav = etree.fromstring(nav_doc([]).encode())
        self.assertEqual(1, len(nav.xpath('//*[@epub:type="toc"]',
                                         namespaces={'epub': 'http://www.idpf.org/2007/ops'})))
        meta = dict(title='Book', subtitle='Sub', language='zh-CN', author='Author',
                    date='2026-11-23', license='CC BY', site_url='https://example.org/')
        pages = [dict(file='inline.xhtml', title='Inline', html='<svg xmlns="http://www.w3.org/2000/svg"/>'),
                 dict(file='image.xhtml', title='Image', html='<img src="figure.svg"/>')]
        package = etree.fromstring(opf(meta, pages, {}).encode())
        ns = {'o': 'http://www.idpf.org/2007/opf', 'dc': 'http://purl.org/dc/elements/1.1/'}
        self.assertEqual('svg', package.find('.//o:item[@id="page-0"]', ns).get('properties'))
        self.assertIsNone(package.find('.//o:item[@id="page-1"]', ns).get('properties'))
        self.assertEqual(meta['site_url'], package.find('.//dc:source', ns).text)

    def test_actual_reading_sketches_retain_caption_and_question(self):
        import json
        import re
        from lxml import etree
        from build_epub import xhtml

        root = Path(__file__).resolve().parents[2]
        entries = json.loads((root / "book/reading-sketches.json").read_text(encoding="utf-8"))["entries"]
        namespace = {"h": "http://www.w3.org/1999/xhtml"}
        for entry in entries[:4]:
            with self.subTest(drawing=entry["drawing"]):
                source = (root / entry["chapter"]).read_text(encoding="utf-8")
                body = re.search(r'<figure class="reading-sketch">.*?</figure>', source, re.S)[0]
                doc = etree.fromstring(xhtml(entry["title"], body).encode())
                figure = doc.find(".//h:figure", namespace)
                self.assertEqual("figcaption", etree.QName(figure[-1]).localname)
                self.assertIn(entry["caption"], "".join(figure.itertext()))
                self.assertIn(entry["question"], "".join(figure.itertext()))
                self.assertEqual(entry["alt"], figure.find("h:img", namespace).get("alt"))

    def test_caption_already_first_keeps_its_position(self):
        from build_epub import xhtml
        result = xhtml("caption", "<figure><figcaption>标题</figcaption><p>图</p></figure>")
        self.assertIn("<figure><figcaption>标题</figcaption><p>图</p></figure>", result)


class EpubTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'book.epub'
        self.entries = {
            'META-INF/container.xml': '''<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
              <rootfiles><rootfile full-path="OEBPS/content.opf"/></rootfiles></container>''',
            'OEBPS/content.opf': '''<package xmlns="http://www.idpf.org/2007/opf">
              <manifest>
                <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
                <item id="chapter" href="text/ch.xhtml" media-type="application/xhtml+xml"/>
                <item id="css" href="css/book.css" media-type="text/css"/>
                <item id="formula" href="math/f.svg" media-type="image/svg+xml"/>
              </manifest><spine><itemref idref="nav"/><itemref idref="chapter"/></spine></package>''',
            'OEBPS/nav.xhtml': '''<html xmlns="http://www.w3.org/1999/xhtml"><body>
              <a href="text/ch.xhtml#%E7%94%B5%E8%B7%AF">电路</a></body></html>''',
            'OEBPS/text/ch.xhtml': '''<html xmlns="http://www.w3.org/1999/xhtml"><body>
              <h1 id="电路">电路</h1><a href="#电路">返回</a>
              <img src="../math/f.svg" alt="I=V/R"/></body></html>''',
            'OEBPS/math/f.svg': '''<svg xmlns="http://www.w3.org/2000/svg">
              <defs><path id="glyph" d="M0 0L1 1"/></defs><use href="#glyph"/></svg>''',
            'OEBPS/css/book.css': 'body{color:black}',
        }

    def write(self):
        with zipfile.ZipFile(self.path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            for name, text in self.entries.items():
                archive.writestr(name, text)
        return self.path

    def test_valid_book_with_encoded_fragment_and_svg_use(self):
        report = validate_epub(self.write())
        self.assertEqual(1, report['chapters'])
        self.assertEqual(4, report['local_references'])

    def test_missing_anchor_is_not_hidden_by_existing_chapter_file(self):
        self.entries['OEBPS/nav.xhtml'] = self.entries['OEBPS/nav.xhtml'].replace(
            '#%E7%94%B5%E8%B7%AF', '#missing')
        with self.assertRaisesRegex(EpubError, '锚点缺失'):
            validate_epub(self.write())

    def test_missing_formula_glyph_is_detected(self):
        self.entries['OEBPS/math/f.svg'] = self.entries['OEBPS/math/f.svg'].replace(
            'href="#glyph"', 'href="#missing"')
        with self.assertRaisesRegex(EpubError, '锚点缺失'):
            validate_epub(self.write())

    def test_duplicate_ids_are_rejected(self):
        self.entries['OEBPS/text/ch.xhtml'] = self.entries['OEBPS/text/ch.xhtml'].replace(
            '</body>', '<p id="电路">重复</p></body>')
        with self.assertRaisesRegex(EpubError, '重复 id'):
            validate_epub(self.write())

    def test_broken_spine_is_rejected(self):
        self.entries['OEBPS/content.opf'] = self.entries['OEBPS/content.opf'].replace(
            'idref="chapter"', 'idref="unknown"')
        with self.assertRaisesRegex(EpubError, 'spine 引用无效'):
            validate_epub(self.write())

    def test_chapter_missing_from_toc_is_rejected(self):
        self.entries['OEBPS/nav.xhtml'] = '<html xmlns="http://www.w3.org/1999/xhtml"/>'
        with self.assertRaisesRegex(EpubError, '目录缺少章节'):
            validate_epub(self.write())

    def test_font_url_must_exist(self):
        self.entries['OEBPS/css/book.css'] = '@font-face{src:url("../fonts/missing.woff2")}'
        with self.assertRaisesRegex(EpubError, '内部引用缺失'):
            validate_epub(self.write())

    def test_external_image_is_not_offline(self):
        self.entries['OEBPS/text/ch.xhtml'] = self.entries['OEBPS/text/ch.xhtml'].replace(
            '../math/f.svg', 'https://example.com/f.svg')
        with self.assertRaisesRegex(EpubError, '离线可用'):
            validate_epub(self.write())

    def test_paths_cannot_escape_archive(self):
        self.entries['OEBPS/text/ch.xhtml'] = self.entries['OEBPS/text/ch.xhtml'].replace(
            '../math/f.svg', '../../../outside.svg')
        with self.assertRaisesRegex(EpubError, '越出 EPUB'):
            validate_epub(self.write())

    def test_manifest_mime_matches_resource(self):
        self.entries['OEBPS/content.opf'] = self.entries['OEBPS/content.opf'].replace(
            'image/svg+xml', 'image/webp')
        with self.assertRaisesRegex(EpubError, 'media-type'):
            validate_epub(self.write())


if __name__ == '__main__':
    unittest.main()
