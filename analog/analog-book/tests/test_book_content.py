#!/usr/bin/env python3
"""站点 HTML -> 书内片段：标题、锚点、链接、图片、表格与 Mermaid。"""
import re
import sys
import tempfile
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import content  # noqa: E402
from book.manifest import BookError  # noqa: E402

ARTICLE = '<html><body><article class="md-content__inner md-typeset">{}</article></body></html>'
MANIFEST = {"site_url": "https://example.test/book/"}


def write_site(root, name, body):
    path = root / name.replace(".md", ".html")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ARTICLE.format(body), encoding="utf-8")
    return path


class ExtractTests(unittest.TestCase):
    def test_extracts_title_and_namespaced_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            write_site(site, "p1-01-ch0.md",
                       '<h1>第 0 章 电路直觉</h1><h2 id="why">0.1 为什么</h2>'
                       '<p name="why">正文。</p>')
            page = content.extract_article(site, "p1-01-ch0.md")
            self.assertEqual(page.title, "第 0 章 电路直觉")
            self.assertIn('id="p1-01-ch0--why"', page.html)
            self.assertNotIn('name="why"', page.html)
            self.assertEqual(page.stem, "p1-01-ch0")

    def test_missing_article_and_missing_h1_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            (site / "p1-01-ch0.html").write_text("<html></html>", encoding="utf-8")
            with self.assertRaisesRegex(BookError, "article"):
                content.extract_article(site, "p1-01-ch0.md")
            write_site(site, "p1-02-ch1.md", "<p>没有标题</p>")
            with self.assertRaisesRegex(BookError, "h1"):
                content.extract_article(site, "p1-02-ch1.md")


class HeadingTests(unittest.TestCase):
    def test_assigns_deterministic_ids_only_when_missing(self):
        fragment = ('<h1 id="p--title">章</h1><h2 id="p--a">0.1 A</h2>'
                    '<h2>0.2 B</h2><h3>0.2.1 C</h3>')
        result = content.assign_heading_ids(fragment, "p")
        self.assertIn('id="p--a"', result)
        self.assertIn('id="p--h2-1"', result)
        self.assertIn('id="p--h3-1"', result)
        self.assertEqual(result, content.assign_heading_ids(fragment, "p"))

    def test_generated_heading_ids_skip_existing_ids(self):
        fragment = ('<h1 id="p--title">章</h1>'
                    '<h2 id="p--h2-1">0.1 已有锚点</h2><h2>0.2 新节</h2>')
        result = content.assign_heading_ids(fragment, "p")
        self.assertIn('<h2 id="p--h2-1">0.1 已有锚点</h2>', result)
        self.assertIn('<h2 id="p--h2-2">0.2 新节</h2>', result)
        ids = re.findall(r'(?<![\w-])id="([^"]+)"', result)
        self.assertEqual(len(ids), len(set(ids)))

    def test_collects_numbered_headings(self):
        fragment = ('<h1 id="p--title">第 0 章</h1>'
                    '<h2 id="p--s1">0.1 电压</h2>'
                    '<h2 id="p--s2">本章练习</h2>'
                    '<h3 id="p--s3">0.1.1 电位</h3>')
        headings = content.collect_headings(fragment)
        self.assertEqual([h.level for h in headings], [1, 2, 2, 3])
        self.assertEqual([h.numbered for h in headings], [False, True, False, True])
        self.assertEqual(headings[1].text, "0.1 电压")


class NamespaceTests(unittest.TestCase):
    def test_leaves_escaped_id_text_byte_identical(self):
        fragment = ('<p>写作 <code>&lt;a id="pick-*"&gt;</code> 与 '
                    '<code>&lt;p name="why"&gt;</code>。</p>'
                    '<p id="pick-a" name="pick-a">真实标签</p>')
        result = content.namespace_ids(fragment, "p9-12-changelog")
        self.assertIn('<code>&lt;a id="pick-*"&gt;</code>', result)
        self.assertIn('<code>&lt;p name="why"&gt;</code>', result)
        self.assertIn('id="p9-12-changelog--pick-a"', result)
        self.assertNotIn('name="pick-a"', result)


class LinkTests(unittest.TestCase):
    def setUp(self):
        self.manifest = MANIFEST
        self.stems = {"p1-01-ch0", "p1-02-ch1"}

    def rewrite(self, href, current="p1-01-ch0"):
        return content.rewrite_links(
            f'<a href="{href}">x</a>', current, self.stems, self.manifest)

    def test_same_page_anchor(self):
        self.assertIn('href="#p1-01-ch0--sec"', self.rewrite("#sec"))

    def test_cross_page_anchor_and_page(self):
        self.assertIn('href="#p1-02-ch1--sec"',
                      self.rewrite("p1-02-ch1.html#sec"))
        self.assertIn('href="#page-p1-02-ch1"', self.rewrite("p1-02-ch1.html"))

    def test_index_and_excluded_pages_use_book_targets(self):
        self.assertIn('href="#book-toc"', self.rewrite("index.html"))
        self.assertIn('href="#book-toc"', self.rewrite("p0-07-toc.html"))
        self.assertIn('href="#part-i"', self.rewrite("p1-00-part1.html"))
        self.assertIn('href="#anim-87"',
                      self.rewrite("p5-00-part5.html#demo87"))
        self.assertIn('href="#appendix-c"', self.rewrite("p6-00-part6.html"))

    def test_quiz_links_target_exercises_and_answers(self):
        self.assertIn('href="#chapter-2--exercises"',
                      self.rewrite("p9-00-quiz.html#quiz-ch2"))
        self.assertIn('href="#appendix-f-answers"',
                      self.rewrite("p9-00-quiz.html#part9"))
        self.assertIn('href="#appendix-f-answers"',
                      self.rewrite("p9-00-quiz.html"))

    def test_external_and_assets_are_not_namespaced(self):
        self.assertIn('href="https://example.test/x"', self.rewrite("https://example.test/x"))
        self.assertIn('href="https://example.test/book/assets/a.svg"',
                      self.rewrite("assets/a.svg"))


class ResourceTests(unittest.TestCase):
    def test_inline_images_and_remote_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "assets").mkdir()
            (root / "assets" / "a.svg").write_text("<svg/>", encoding="utf-8")
            result, count = content.inline_images(
                '<p><img src="assets/a.svg" alt="a"></p>', root)
            self.assertEqual(1, count)
            self.assertIn('src="data:image/svg+xml;base64,', result)
            with self.assertRaisesRegex(BookError, "远程图片"):
                content.inline_images('<img src="https://x.test/a.png">', root)

    def test_rejects_image_outside_repo_and_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "outside.svg"
            outside.write_text("<svg/>", encoding="utf-8")
            with self.assertRaisesRegex(BookError, "不在仓库或站点目录内"):
                content._data_uri(outside, root / "site")

    def test_wrap_tables(self):
        fragment = '<table><tr><td>1</td></tr></table>'
        self.assertEqual(
            '<div class="table-wrap"><table><tr><td>1</td></tr></table></div>',
            content.wrap_tables(fragment))

    def test_wrap_tables_is_idempotent(self):
        fragment = '<p>说明</p><table><tr><td>1</td></tr></table>'
        once = content.wrap_tables(fragment)
        self.assertEqual(once, content.wrap_tables(once))

    def test_wrap_tables_keeps_one_wrapper_for_captioned_table(self):
        fragment = ('<p><strong>表 1-1 参数</strong></p>'
                    '<table><tr><td>1</td></tr></table>')
        wrapped = content.wrap_tables(content.wrap_tables(fragment))
        self.assertEqual(1, wrapped.count('class="table-wrap"'))
        self.assertIn('<p><strong>表 1-1 参数</strong></p>'
                      '<div class="table-wrap"><table>', wrapped)

    def test_mermaid_snapshot_mismatch_raises(self):
        fragment = '<pre class="mermaid">x</pre>'
        roadmap = content.replace_mermaid(fragment)
        self.assertIn('<figure class="book-roadmap">', roadmap)
        snapshot_file = (BOOK / "static" / "roadmap.svg").read_text(encoding="utf-8")
        self.assertIn(snapshot_file.strip(), roadmap)

        snapshot = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 10">'
                    '<path d="M0 0L20 10"/></svg>')
        source = "flowchart LR\n  A-->B\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            static = root / "static"
            docs.mkdir()
            static.mkdir()
            (docs / "p0-06-roadmap.md").write_text(
                "```mermaid\n" + source + "```\n", encoding="utf-8")
            (static / "roadmap.source.txt").write_text(source, encoding="utf-8")
            (static / "roadmap.svg").write_text(snapshot, encoding="utf-8")
            self.assertEqual(
                '<figure class="book-roadmap">' + snapshot
                + '<figcaption>六阶段学习路线与方向深化</figcaption></figure>',
                content.replace_mermaid(
                    fragment, docs_dir=docs, static_dir=static))

            (docs / "p0-06-roadmap.md").write_text(
                "```mermaid\nflowchart LR\n  A-->C\n```\n", encoding="utf-8")
            with self.assertRaisesRegex(BookError, "不一致"):
                content.replace_mermaid(
                    fragment, docs_dir=docs, static_dir=static)

            (static / "roadmap.svg").unlink()
            with self.assertRaisesRegex(BookError, "缺少"):
                content.replace_mermaid(
                    fragment, docs_dir=docs, static_dir=static)

    def test_mermaid_page_without_fence_raises_book_error(self):
        fragment = '<pre class="mermaid">x</pre>'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            static = root / "static"
            docs.mkdir()
            static.mkdir()
            (docs / "p0-06-roadmap.md").write_text("没有图表。\n", encoding="utf-8")
            (static / "roadmap.source.txt").write_text(
                "flowchart LR\n  A-->B\n", encoding="utf-8")
            (static / "roadmap.svg").write_text("<svg/>", encoding="utf-8")
            with self.assertRaisesRegex(BookError, "mermaid"):
                content.replace_mermaid(
                    fragment, docs_dir=docs, static_dir=static)


class LoadPageTests(unittest.TestCase):
    def test_load_page_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            (site / "assets" / "svg").mkdir(parents=True)
            (site / "assets" / "svg" / "a.svg").write_text("<svg/>", encoding="utf-8")
            write_site(site, "p1-01-ch0.md",
                       '<h1>第 0 章</h1><h2 id="s">0.1 节</h2>'
                       '<p><img src="assets/svg/a.svg"></p><table><tr><td>1</td></tr></table>')
            page = content.load_page(
                site, "p1-01-ch0.md", {"p1-01-ch0"}, MANIFEST)
            self.assertIn("data:image/svg+xml;base64,", page.html)
            self.assertIn('<div class="table-wrap">', page.html)
            self.assertEqual(1, page.images)


if __name__ == "__main__":
    unittest.main()
