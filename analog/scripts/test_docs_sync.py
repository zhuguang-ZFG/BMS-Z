#!/usr/bin/env python3
"""docs/ 是唯一数据源：README.md 与 BOOK.md 必须能由 docs/ 重建。

README 是短入口，BOOK 是全量单文件；防止出现「改了入口忘了改 docs」
或反之——三者漂移即红灯。
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_readme  # noqa: E402


class DocsReadmeSync(unittest.TestCase):
    def test_readme_and_book_are_generated_from_docs(self):
        readme = ROOT / "README.md"
        book = ROOT / "BOOK.md"
        self.assertTrue(readme.exists(), "README.md 缺失")
        self.assertTrue(book.exists(), "BOOK.md 缺失")
        expected_readme = build_readme.build_readme().replace("\r\n", "\n")
        actual_readme = readme.read_text(encoding="utf-8").replace("\r\n", "\n")
        self.assertEqual(expected_readme, actual_readme,
                         "README.md 与 docs/ 不同步：请运行 python scripts/build_readme.py")
        expected_book = build_readme.build_book().replace("\r\n", "\n")
        actual_book = book.read_text(encoding="utf-8").replace("\r\n", "\n")
        self.assertEqual(expected_book, actual_book,
                         "BOOK.md 与 docs/ 不同步：请运行 python scripts/build_readme.py")

    def test_readme_is_a_short_portal(self):
        """README 首页必须保持短入口；完整内容移到 BOOK.md。"""
        readme = ROOT / "README.md"
        self.assertLess(readme.stat().st_size, 1_000_000,
                        "README.md 超过 GitHub 在线渲染阈值，完整内容应留在 BOOK.md")
        text = readme.read_text(encoding="utf-8")
        self.assertIn("[完整单文件版 BOOK.md](BOOK.md)", text)
        self.assertIn('<a id="readme-portal"></a>', text)

    def test_docs_pages_are_non_empty(self):
        pages = build_readme.collect_pages()
        self.assertGreater(len(pages), 30, "docs/ 页面数量异常")
        for p in pages:
            self.assertTrue(p.read_text(encoding="utf-8").strip(), "%s 是空页面" % p.name)

    def test_readme_has_no_cross_page_link_leak(self):
        """拼合后的 README 里不应残留 docs 的跨页链接形式。"""
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        leaked = [m for m in build_readme.MD_LINK.findall(text)]
        self.assertEqual([], leaked, "README 中残留跨页链接：%s" % leaked[:5])

    def test_readme_page_links_point_into_docs(self):
        """无锚点的整页链接必须带 docs/ 前缀，否则单文件版会指向不存在的文件。"""
        import re
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        pages = {p.name for p in build_readme.collect_pages()}
        bare = [m for m in re.findall(r"\]\(([\w\-]+\.md)\)", text) if m in pages]
        self.assertEqual([], bare, "README 中残留裸页面链接：%s" % bare[:5])
        bare_html = [m for m in re.findall(r'href="([\w\-]+\.md)"', text) if m in pages]
        self.assertEqual([], bare_html, "README 中残留裸页面 href：%s" % bare_html[:5])
        for rel in re.findall(r"\]\(docs/([\w\-]+\.md)\)", text):
            self.assertTrue((ROOT / "docs" / rel).exists(), "缺少目标页 docs/%s" % rel)
        for rel in re.findall(r'href="docs/([\w\-]+\.md)"', text):
            self.assertTrue((ROOT / "docs" / rel).exists(), "缺少目标页 docs/%s" % rel)


if __name__ == "__main__":
    unittest.main()
