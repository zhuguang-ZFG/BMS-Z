#!/usr/bin/env python3
"""教材化不变量：19 章章首的「场景 / 难度 / 白话」三件套与全站难度地图。

守的是三件容易悄悄坏掉的事：
1. 章首块的**位置**——它必须夹在场景之后、先修/目标之前，否则读者先看到
   一串元信息却不知道这一章要解决什么麻烦；
2. 章首块的**内容**——节数、白话文案与印刷版导读是同一份，不能各写各的；
3. 三处**接线**（站点提示块、印刷卡片、两套 CSS）——漏一处就会退化成
   一根普通引用条，肉眼很难发现，只有在成品里才看得出来。
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "analog-book"))

import curriculum  # noqa: E402
from book import intuition, transforms  # noqa: E402

DOCS = ROOT / "docs"
SCENE_RE = re.compile(r"^> \*\*场景\*\*：", re.M)
LEVEL_RE = re.compile(
    r"^> \*\*难度\*\*：(L[0-3]) (零基础|入门|进阶|深入)，(\d+) 节，"
    r"精读约 (\d+) 分钟$", re.M)
LEAD_RE = re.compile(r"^> \*\*白话\*\*：(.+)$", re.M)
PREREQ_RE = re.compile(r"^> \*\*先修\*\*：", re.M)
GOAL_RE = re.compile(r"^> \*\*学完你应能\*\*：", re.M)


def chapter_texts() -> dict[int, str]:
    return {chapter: (DOCS / name).read_text(encoding="utf-8")
            for chapter, (name, _level, _minutes) in curriculum.CHAPTER_META.items()}


class ChapterCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = chapter_texts()

    def test_every_chapter_has_exactly_one_card(self):
        for chapter, text in self.texts.items():
            with self.subTest(chapter=chapter):
                self.assertEqual(1, len(LEVEL_RE.findall(text)))
                self.assertEqual(1, len(LEAD_RE.findall(text)))

    def test_card_sits_between_scene_and_sections(self):
        for chapter, text in self.texts.items():
            with self.subTest(chapter=chapter):
                scene = SCENE_RE.search(text)
                level = LEVEL_RE.search(text)
                lead = LEAD_RE.search(text)
                section = re.search(r"^### ", text, re.M)
                self.assertIsNotNone(scene, chapter)
                self.assertLess(scene.start(), level.start())
                self.assertLess(level.start(), lead.start())
                self.assertLess(lead.end(), section.start())

    def test_section_count_matches_the_document(self):
        for chapter, text in self.texts.items():
            with self.subTest(chapter=chapter):
                (_code, _label, sections, _minutes) = LEVEL_RE.search(text).groups()
                self.assertEqual(len(re.findall(r"^### ", text, re.M)), int(sections))

    def test_level_and_minutes_match_the_table(self):
        for chapter, text in self.texts.items():
            _code, _label, _sections, minutes = LEVEL_RE.search(text).groups()
            _file, level, planned = curriculum.CHAPTER_META[chapter]
            with self.subTest(chapter=chapter):
                self.assertEqual(level, _code)
                self.assertEqual(planned, int(minutes))
                self.assertEqual(0, int(minutes) % 5)
                self.assertGreaterEqual(int(minutes), 5)
                self.assertLessEqual(int(minutes), 60)

    def test_plain_language_lead_is_plain(self):
        for chapter, text in self.texts.items():
            lead = LEAD_RE.search(text).group(1)
            with self.subTest(chapter=chapter):
                self.assertTrue(lead.endswith("。"), lead)
                self.assertLessEqual(len(lead), 80, lead)
                for marker in ("$", "\\", "**", "`", "TODO"):
                    self.assertNotIn(marker, lead)

    def test_lead_text_is_the_same_as_the_printed_book(self):
        for chapter, text in self.texts.items():
            with self.subTest(chapter=chapter):
                self.assertEqual(intuition.CHAPTER_LEADS[chapter],
                                 LEAD_RE.search(text).group(1))

    def test_prereq_and_goal_cards_survive(self):
        for chapter, text in self.texts.items():
            with self.subTest(chapter=chapter):
                self.assertEqual(1, len(GOAL_RE.findall(text)))
                if chapter == 0:
                    self.assertEqual([], PREREQ_RE.findall(text))
                else:
                    self.assertEqual(1, len(PREREQ_RE.findall(text)))


class DriftTests(unittest.TestCase):
    def test_docs_match_the_metadata_table(self):
        self.assertEqual([], curriculum.drift())

    def test_insert_is_idempotent(self):
        for chapter in curriculum.CHAPTER_META:
            text = chapter_texts()[chapter]
            with self.subTest(chapter=chapter):
                self.assertEqual(text, curriculum.insert_block(text, chapter))
                once = curriculum.insert_block(text, chapter)
                self.assertEqual(once, curriculum.insert_block(once, chapter))

    def test_missing_scene_is_an_error(self):
        with self.assertRaises(ValueError):
            curriculum.insert_block("## 第 0 章\n\n没有场景。\n", 0)


class WiringTests(unittest.TestCase):
    def test_callout_kinds_are_registered(self):
        from build_site import CALLOUT_KINDS
        self.assertEqual("level", CALLOUT_KINDS["难度"])
        self.assertEqual("lead", CALLOUT_KINDS["白话"])
        self.assertEqual("难度", transforms.CALLOUT_LABELS["level"])
        self.assertEqual("白话导读", transforms.CALLOUT_LABELS["lead"])

    def test_styles_exist_for_site_book_and_print(self):
        site = (ROOT / "scripts" / "site_media" / "typography.css").read_text(
            encoding="utf-8")
        skin = (ROOT / "scripts" / "site_media" / "handraw.css").read_text(
            encoding="utf-8")
        a4 = (ROOT / "analog-book" / "styles" / "book.css").read_text(
            encoding="utf-8")
        print_css = (ROOT / "analog-book" / "styles" / "print.css").read_text(
            encoding="utf-8")
        for slug in ("level", "lead"):
            with self.subTest(kind=slug):
                self.assertIn(f".callout-{slug}", site)
                self.assertIn(
                    f'[data-md-color-scheme="slate"] .md-typeset .callout-{slug}',
                    site)
                self.assertIn(f".callout-{slug}", skin)
                self.assertIn(f".book-callout-{slug}", a4)
                self.assertIn(f".book .book-callout-{slug}", print_css)

    def test_printed_book_does_not_double_the_lead(self):
        """docs 已带白话卡时，印刷管线不再插第二条导读。"""
        fragment = (
            '<h1>第 3 章</h1>\n'
            '<aside class="book-callout book-callout-scene" data-label="场景">'
            "故事</aside>\n"
            '<aside class="book-callout book-callout-lead" data-label="白话导读">'
            "<p>大白话。</p></aside>")
        result = intuition.insert_lead(fragment, intuition.chapter_lead(3))
        self.assertEqual(fragment, result)
        self.assertNotIn("chapter-intuition", result)


class ShortestPathTests(unittest.TestCase):
    def test_how_to_use_maps_every_chapter_to_its_level(self):
        text = (DOCS / "p0-02-how-to-use.md").read_text(encoding="utf-8")
        rows = re.findall(
            r"^\| \*\*(L[0-3]) [^|]*\|[^|]*\| (.+) \|$", text, re.M)
        self.assertEqual(4, len(rows), rows)
        seen: dict[str, list[int]] = {}
        for level, cells in rows:
            numbers = [int(n) for n in re.findall(r"\[(\d+)\]", cells)]
            self.assertTrue(numbers, level)
            seen[level] = numbers
        planned: dict[str, list[int]] = {}
        for chapter, (_file, level, _minutes) in curriculum.CHAPTER_META.items():
            planned.setdefault(level, []).append(chapter)
        self.assertEqual({k: sorted(v) for k, v in planned.items()},
                         {k: sorted(v) for k, v in seen.items()})

    def test_shortest_path_minutes_add_up(self):
        """表里的用时 = 各章开头的精读分钟之和；别再写“约 1 小时”糊过去。"""
        text = (DOCS / "p0-02-how-to-use.md").read_text(encoding="utf-8")
        rows = re.findall(
            r"^\| \*\*([①②③]) [^|]*\|[^|]*\| (.*?) \| 约 (\d+) 分钟 \|$",
            text, re.M)
        self.assertEqual(3, len(rows), rows)
        for mark, cells, minutes in rows:
            chapters = [int(n) for n in re.findall(r"\[第 (\d+) 章\]", cells)]
            self.assertTrue(chapters, mark)
            total = sum(curriculum.CHAPTER_META[c][2] for c in chapters)
            with self.subTest(path=mark, chapters=chapters):
                self.assertEqual(total, int(minutes))

    def test_shortest_path_links_resolve(self):
        text = (DOCS / "p0-02-how-to-use.md").read_text(encoding="utf-8")
        for name, anchor in re.findall(r"\((p\d+-\d+-ch\d+\.md)#([^)]+)\)", text):
            with self.subTest(page=name):
                self.assertTrue((DOCS / name).is_file(), name)
                self.assertIn(f'<a id="{anchor}"></a>',
                              (DOCS / name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
