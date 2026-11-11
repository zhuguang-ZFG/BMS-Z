#!/usr/bin/env python3
"""整书构建单元测试：manifest、清洗、ID 命名空间、链接、资源与结构审计。"""
import hashlib
import re
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
ROOT = BOOK.parent
sys.path.insert(0, str(BOOK))

import build_book  # noqa: E402


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = build_book.load_manifest()

    def test_covers_every_content_page_exactly_once(self):
        stems = build_book.validate_manifest(self.manifest)
        docs = ({p.stem for p in (ROOT / "docs").glob("*.md")}
                - {"index"} - build_book.PRINT_ONLY_STEMS)
        self.assertEqual(60, len(stems))
        self.assertEqual(docs, set(stems))
        self.assertEqual(60, len(set(stems)))
        self.assertEqual(3, len(self.manifest["appendix"]["files"]))

    def test_print_only_stems_are_exactly_the_three_16k_pages(self):
        self.assertEqual(
            {"p0-11-conventions", "p0-12-symbols", "p9-15-glossary"},
            build_book.PRINT_ONLY_STEMS)

    def test_metadata_is_complete(self):
        for key in ("title", "subtitle", "version", "source_version", "date",
                    "language", "author", "site_url", "repository", "license"):
            self.assertTrue(self.manifest[key], key)


class ExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = build_book.load_manifest()
        build_book.validate_manifest(cls.manifest)
        cls.parts = build_book.manuscript(cls.manifest)
        cls.pages = [p for part in cls.parts for p in part["pages"]]

    def test_sixty_pages_in_eleven_parts(self):
        self.assertEqual(11, len(self.parts))
        self.assertEqual(60, len(self.pages))

    def test_site_only_dom_is_gone(self):
        for page in self.pages:
            for needle in ("legacy-anchor", "md-content__button", "headerlink",
                           "✍️ <strong>参与共建"):
                self.assertNotIn(needle, page["html"], f'{page["stem"]}: {needle}')
            self.assertNotRegex(page["html"], r'<img[^>]+loading="lazy"',
                                page["stem"])

    def test_reading_checkpoint_survives(self):
        self.assertTrue(any("reading-checkpoint" in p["html"] for p in self.pages))

    def test_ids_are_namespaced_and_unique_across_book(self):
        seen = {}
        for page in self.pages:
            prefix = page["stem"] + "--"
            ids = re.findall(r'(?<![\w-])(?:id|name)="([^"]+)"', page["html"])
            self.assertTrue(ids, page["stem"])
            for value in ids:
                self.assertTrue(value.startswith(prefix), f'{page["stem"]}: {value}')
                self.assertNotIn(value, seen, f'重复 ID {value}')
                seen[value] = page["stem"]

    def test_every_page_keeps_an_h1_title(self):
        for page in self.pages:
            self.assertTrue(page["title"])
            self.assertRegex(page["html"], r"<h1[^>]*>")


class LinkAndAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = build_book.load_manifest()
        build_book.validate_manifest(cls.manifest)
        cls.parts = build_book.manuscript(cls.manifest)
        cls.stems = {p["stem"] for part in cls.parts for p in part["pages"]}

    def prepared_pages(self):
        pages = []
        for part in self.parts:
            for page in part["pages"]:
                item = dict(page)
                item["html"] = build_book.replace_mermaid(item["html"])
                item["html"] = build_book.rewrite_links(
                    item["html"], item["stem"], self.stems, self.manifest)
                item["html"], _count = build_book.inline_images(item["html"])
                pages.append(item)
        return pages

    def test_links_are_rewritten(self):
        pages = self.prepared_pages()
        ids = {i for p in pages
               for i in re.findall(r'(?<![\w-])(?:id|name)="([^"]+)"', p["html"])}
        # 装配阶段才会写入的跳转锚点。
        ids |= {f"page-{stem}" for stem in self.stems} | {"book-toc"}
        broken = []
        for page in pages:
            for target in re.findall(r'href="#([^"]+)"', page["html"]):
                if target not in ids:
                    broken.append(f'{page["stem"]}: #{target}')
        self.assertEqual([], broken[:20])

    def test_no_internal_site_links_remain(self):
        for page in self.prepared_pages():
            self.assertNotRegex(page["html"], r'href="[\w\-]+\.html')
            self.assertNotRegex(page["html"], r'href="assets/')

    def test_images_become_data_uris(self):
        for page in self.prepared_pages():
            body = page["html"]
            self.assertNotRegex(body, r'src="assets/')
            self.assertNotRegex(body, r'srcset="assets/')
            self.assertNotRegex(body, r'src="https?://')
            self.assertNotRegex(body, r'srcset="https?://')
            self.assertNotRegex(body, r"<iframe|<video")
            self.assertEqual(0, body.count("<script src="))

    def test_mermaid_is_replaced_by_static_svg(self):
        pages = self.prepared_pages()
        roadmap = next(p for p in pages if p["stem"] == "p0-06-roadmap")
        self.assertNotIn('<pre class="mermaid">', roadmap["html"])
        self.assertIn('<figure class="book-roadmap">', roadmap["html"])
        self.assertGreater(roadmap["html"].count("<svg"), 0)

    def test_youtube_links_are_plain_text_entries(self):
        pages = self.prepared_pages()
        for page in pages:
            self.assertNotIn("data-study-video", page["html"])
            self.assertNotRegex(page["html"], r"<a[^>]+youtube\.com[^>]*>\s*<img")


class AssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = build_book.load_manifest()
        build_book.validate_manifest(cls.manifest)
        cls.parts = build_book.manuscript(cls.manifest)
        stems = {p["stem"] for part in cls.parts for p in part["pages"]}
        for part in cls.parts:
            for page in part["pages"]:
                page["html"] = build_book.replace_mermaid(page["html"])
                page["html"] = build_book.rewrite_links(
                    page["html"], page["stem"], stems, cls.manifest)
                page["html"], _count = build_book.inline_images(page["html"])
                page["html"] = build_book.wrap_tables(page["html"])
        cls.document = build_book.assemble_book(cls.manifest, cls.parts)

    def test_front_matter_and_structure(self):
        self.assertIn('class="book-cover"', self.document)
        self.assertIn('class="book-copyright"', self.document)
        self.assertIn('id="book-toc"', self.document)
        self.assertEqual(60, self.document.count('class="book-page"'))
        self.assertEqual(11, self.document.count('class="book-part"'))
        for stem in ("p0-01-preface", "p1-01-ch0", "p6-01-s6-1",
                     "p9-12-changelog", "p9-14-credits"):
            self.assertIn(f'data-page="{stem}"', self.document)
        self.assertIn('name="book-manifest-sha256"', self.document)
        self.assertIn(build_book.manifest_sha256(), self.document)

    def test_toc_has_every_page(self):
        toc = re.search(r'<section class="book-toc".*?</section>', self.document, re.S).group(0)
        self.assertEqual(60, toc.count('<a href="#page-'))
        self.assertEqual(11, toc.count("<h2"))
        self.assertEqual(10, toc.count(">本篇导读</a>"),
                         "各篇首页标题与篇名重复，目录里应改为导读")

    def test_offline_search_is_wired(self):
        self.assertEqual(60, self.document.count('data-part-title="'))
        self.assertIn('id="book-search-input"', self.document)
        self.assertIn('id="book-search-panel"', self.document)
        self.assertIn('id="book-search-results"', self.document)
        self.assertIn('id="book-search-status"', self.document)
        self.assertIn("buildIndex", self.document)
        self.assertIn("appendHighlighted", self.document)
        self.assertIn("Ctrl+K", self.document)
        self.assertNotRegex(self.document, r'<script[^>]+src=')

    def test_cover_art_and_back_to_top_are_wired(self):
        self.assertIn('class="book-cover-art"', self.document)
        self.assertIn('class="book-cover-rule"', self.document)
        self.assertNotIn("cover-art.svg", self.document, "封面插图必须内联")
        self.assertIn('id="book-top"', self.document)
        self.assertIn('aria-label="回到顶部"', self.document)
        self.assertIn('getElementById("book-top")', self.document)

    def test_reading_progress_skip_link_and_author(self):
        author = self.manifest["author"]
        self.assertIn(f'<meta name="book-author" content="{author}">', self.document)
        self.assertIn(f'class="book-cover-author">{author}</p>', self.document)
        self.assertIn('class="book-skip" href="#book-toc">跳到目录</a>',
                      self.document)
        self.assertIn('class="book-progress" id="book-progress" aria-hidden="true"',
                      self.document)
        self.assertIn('getElementById("book-progress")', self.document)
        self.assertIn("scaleX(", self.document)
        css = (build_book.BOOK_DIR / "styles" / "book.css").read_text(encoding="utf-8")
        print_block = css.split("@media print", 1)[1]
        self.assertIn(".book-progress, .book-skip { display: none !important; }",
                      print_block)

    def test_page_footer_navigation_follows_the_reading_sequence(self):
        self.assertEqual(60, self.document.count('class="book-page-nav"'))
        self.assertEqual(59, self.document.count('rel="prev"'))
        self.assertEqual(59, self.document.count('rel="next"'))
        self.assertIn('href="#page-p1-00-part1" rel="prev"', self.document,
                      "跨篇翻页应接上前一篇的最后一页")
        self.assertIn('href="#page-p0-02-how-to-use" rel="next"', self.document)
        first = self.document.split('id="page-p0-01-preface"', 1)[1].split("</section>", 1)[0]
        self.assertNotIn('rel="prev"', first)
        last = self.document.split('id="page-p9-14-credits"', 1)[1].split("</section>", 1)[0]
        self.assertNotIn('rel="next"', last)
        css = (build_book.BOOK_DIR / "styles" / "book.css").read_text(encoding="utf-8")
        print_block = css.split("@media print", 1)[1]
        self.assertIn(".book-page-nav", print_block)
        self.assertNotIn(".book-page-back", css)
        self.assertIn(".book .md-typeset a {", css)
        self.assertIn("text-decoration-color: rgba(180, 83, 9, .32)", css)
        self.assertIn(".book .md-typeset .reading-nav a { text-decoration: none; }", css)

    def test_print_layout_avoids_page_shrink(self):
        css = (build_book.BOOK_DIR / "styles" / "book.css").read_text(encoding="utf-8")
        self.assertNotIn("@media (max-width: 720px)", css,
                         "移动端样式不能泄漏到 A4 打印")
        self.assertIn("@media screen and (max-width: 720px)", css)
        print_block = css.split("@media print", 1)[1]
        self.assertIn("table-layout: fixed", print_block)
        self.assertIn("word-break: break-word", print_block)
        self.assertIn(".book-copyright { font-size: 10.5pt;", print_block)
        self.assertIn("break-before: auto; break-after: auto;", print_block)

    def test_no_remote_or_site_only_assets(self):
        self.assertNotRegex(self.document, r'<script[^>]+src=')
        self.assertNotRegex(self.document, r'<link[^>]+rel="stylesheet"')
        self.assertNotIn("<iframe", self.document)
        self.assertNotIn("<video", self.document)
        self.assertNotRegex(self.document, r'(?:src|srcset)="(?!#)(?:assets/|https?://)')
        self.assertIn("MathJax", self.document)

    def test_ids_are_globally_unique(self):
        markup = build_book.EMBEDDED_BLOCK_RE.sub("", self.document)
        ids = re.findall(r'(?<![\w-])(?:id|name)="([^"]+)"', markup)
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        self.assertEqual([], duplicates[:10])

    def test_audit_counts(self):
        report = build_book.audit_html(self.document, self.manifest, self.parts)
        self.assertEqual(60, report["pages"])
        self.assertGreater(report["images"], 90)
        self.assertGreater(report["formulas"], 1000)
        self.assertLess(report["bytes"], build_book.MAX_HTML_BYTES)

    def test_collapsible_answers_are_open_and_tables_are_wrapped(self):
        self.assertNotRegex(self.document, r"<details(?! open)")
        self.assertNotIn("<table", self.document.replace('<div class="table-wrap"><table', ""))

    def test_deterministic(self):
        again = build_book.assemble_book(self.manifest, self.parts)
        self.assertEqual(hashlib.sha256(self.document.encode()).hexdigest(),
                         hashlib.sha256(again.encode()).hexdigest())


if __name__ == "__main__":
    unittest.main()
