#!/usr/bin/env python3
"""视频层不变量：清单、章节入口、索引表三处必须互相印证。

视频是书里唯一会自己失效的外部资源。这份测试离线跑（不联网），守四件事：
1. `docs/` 里的每个视频链接都在 `analog-book/data/videos.yml` 里，且带平台核对
   过的标题/频道/时长/日期——清单由 `scripts/video_catalog.py --refresh` 生成；
2. 19 章每章至少有一个中文（B 站）和一个英文（YouTube）入口，杜绝"这章没得看"；
3. 清单里的 `chapters` 与 docs 实际出现位置一致，防止新增/搬家后记录过期；
4. `7.2 按章清单` 里的每一行：时长与平台核对值一致、链接在清单里、章号对得上。
   表里写错的时长是最容易被读者当场发现的那种错。
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import video_catalog as catalog  # noqa: E402

DOCS = ROOT / "docs"
DURATION_RE = re.compile(r"^\d+:\d{2}(?::\d{2})?$")
TABLE_ROW_RE = re.compile(
    r"^\| \[(\d+)\]\(p[\w-]+\.md#ch\d+\) \| \[(.+?)\]\((https://[^)]+)\) \| "
    r"(\d+:\d{2}(?::\d{2})?)\s*\|", re.M)


class CatalogShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = catalog.scan_docs()
        cls.known = catalog.load_catalog()

    def test_catalog_covers_every_doc_link(self):
        self.assertEqual(set(), set(self.docs) - set(self.known))

    def test_catalog_has_no_orphans(self):
        self.assertEqual(set(), set(self.known) - set(self.docs))

    def test_entries_are_platform_verified(self):
        for vid, item in self.known.items():
            with self.subTest(video=vid):
                self.assertIn(item["platform"], ("bilibili", "youtube"))
                self.assertTrue(item["title"], vid)
                self.assertTrue(item["author"], vid)
                self.assertRegex(item["duration"], DURATION_RE)
                self.assertRegex(item["checked"], r"^\d{4}-\d{2}-\d{2}$")

    def test_chapter_records_match_docs(self):
        for vid, info in self.docs.items():
            item = self.known[vid]
            with self.subTest(video=vid):
                self.assertEqual(sorted(info["chapters"]), item["chapters"])


class ChapterEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = {}
        for path in DOCS.glob("p*-ch*.md"):
            match = re.search(r"ch(\d+)\.md$", path.name)
            if match:
                cls.files[int(match.group(1))] = path

    def test_nineteen_chapters(self):
        self.assertEqual(list(range(19)), sorted(self.files))

    def test_every_chapter_has_chinese_and_english_entry(self):
        for chapter, path in self.files.items():
            text = path.read_text(encoding="utf-8")
            with self.subTest(chapter=chapter):
                self.assertTrue(catalog.BV_RE.search(text), "缺 B 站入口")
                self.assertTrue(catalog.YT_RE.search(text), "缺 YouTube 入口")
                self.assertTrue(
                    any(line.startswith("> **配套视频**")
                        for line in text.splitlines()), "缺「配套视频」卡片")

    def test_chapter_links_avoid_obvious_duplicates(self):
        for chapter, path in self.files.items():
            text = path.read_text(encoding="utf-8")
            for line in text.splitlines():
                if not line.startswith("> **配套视频**"):
                    continue
                ids = catalog.BV_RE.findall(line) + catalog.YT_RE.findall(line)
                with self.subTest(chapter=chapter):
                    self.assertEqual(len(ids), len(set(ids)), line[:80])


class IndexTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (DOCS / "p7-02-s7-2.md").read_text(encoding="utf-8")
        cls.rows = TABLE_ROW_RE.findall(cls.text)
        cls.known = {item["id"]: item for item in catalog.load_catalog().values()}

    def test_table_covers_all_chapters(self):
        chapters = {int(row[0]) for row in self.rows}
        self.assertEqual(set(range(19)), chapters)

    def test_rows_match_verified_metadata(self):
        for chapter, title, url, duration in self.rows:
            with self.subTest(url=url):
                self.assertIn("youtube.com/watch?v=", url)
                vid = url.rsplit("=", 1)[1]
                item = self.known.get(vid)
                self.assertIsNotNone(item, f"{vid} 未进清单")
                self.assertEqual(item["duration"], duration)
                self.assertIn(int(chapter), item["chapters"])

    def test_titles_are_not_placeholders(self):
        for _chapter, title, _url, _duration in self.rows:
            with self.subTest(title=title):
                self.assertGreaterEqual(len(title), 8)
                for token in ("TODO", "TBD", "占位", "待补"):
                    self.assertNotIn(token, title)


if __name__ == "__main__":
    unittest.main(verbosity=2)
