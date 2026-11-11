#!/usr/bin/env python3
"""19 章「先看一个场景」：位置、长度、独特性与两端接线。"""
import re
import sys
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
ROOT = BOOK.parent
sys.path.insert(0, str(BOOK))
sys.path.insert(0, str(ROOT / "scripts"))

from book import intuition, transforms  # noqa: E402

CHAPTER_FILES = (
    "p1-01-ch0.md", "p1-02-ch1.md", "p1-03-ch2.md", "p1-04-ch3.md",
    "p1-05-ch4.md", "p1-06-ch5.md", "p1-07-ch6.md", "p1-08-ch7.md",
    "p1-09-ch8.md", "p1-10-ch9.md", "p1-11-ch10.md", "p2-01-ch11.md",
    "p2-02-ch12.md", "p2-03-ch13.md", "p3-01-ch14.md", "p3-02-ch15.md",
    "p4-01-ch16.md", "p4-02-ch17.md", "p4-03-ch18.md",
)
SCENE_RE = re.compile(r"^> \*\*场景\*\*：(.+)$", re.M)
FORBIDDEN = ("$", "\\", "**", "`", "TODO", "TBD", "待补", "占位", "http")


class SceneContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = {name: (ROOT / "docs" / name).read_text(encoding="utf-8")
                     for name in CHAPTER_FILES}

    def scenes(self):
        for name, text in self.texts.items():
            found = SCENE_RE.findall(text)
            with self.subTest(chapter=name):
                self.assertEqual(1, len(found),
                                 f"{name} 应有且只有一个场景开场")
            yield name, found[0]

    def test_scene_is_plain_short_and_complete(self):
        for name, scene in self.scenes():
            with self.subTest(chapter=name):
                self.assertGreaterEqual(len(scene), 50, scene)
                self.assertLessEqual(len(scene), 160, scene)
                self.assertTrue(scene.endswith("。"), scene)
                for token in FORBIDDEN:
                    self.assertNotIn(token, scene, (name, token))

    def test_scene_sits_after_title_and_before_first_section(self):
        for name, text in self.texts.items():
            with self.subTest(chapter=name):
                title = text.find("\n## ")
                scene = text.find("> **场景**：")
                section = text.find("\n### ")
                self.assertGreaterEqual(title, 0, name)
                self.assertGreater(scene, title, name)
                self.assertGreater(section, scene, name)

    def test_scenes_are_unique(self):
        scenes = [scene for _name, scene in self.scenes()]
        self.assertEqual(19, len(scenes))
        self.assertEqual(19, len(set(scenes)))

    def test_every_chapter_file_is_covered(self):
        self.assertEqual(19, len(CHAPTER_FILES))
        for name in CHAPTER_FILES:
            self.assertTrue((ROOT / "docs" / name).is_file(), name)


class SceneWiringTests(unittest.TestCase):
    def test_scene_kind_is_wired_into_site_and_book(self):
        from build_site import CALLOUT_KINDS
        self.assertEqual("scene", CALLOUT_KINDS["场景"])
        self.assertEqual("场景", transforms.CALLOUT_LABELS["scene"])

    def test_scene_has_styles_for_site_a4_and_print(self):
        site = (ROOT / "scripts" / "site_media" / "typography.css").read_text(
            encoding="utf-8")
        self.assertIn(".callout-scene", site)
        self.assertIn('[data-md-color-scheme="slate"] .md-typeset .callout-scene',
                      site)
        a4 = (BOOK / "styles" / "book.css").read_text(encoding="utf-8")
        self.assertIn(".book-callout-scene", a4)
        print_css = (BOOK / "styles" / "print.css").read_text(encoding="utf-8")
        self.assertIn(".book .book-callout-scene", print_css)

    def test_lead_follows_the_scene_in_print(self):
        lead = intuition.chapter_lead(3)
        fragment = (
            '<h1>第 3 章</h1>\n'
            '<aside class="book-callout book-callout-scene" data-label="场景">'
            "故事</aside>"
            '<aside class="book-callout book-callout-goal">目标</aside>')
        result = intuition.insert_lead(fragment, lead)
        self.assertLess(result.index("book-callout-scene"),
                        result.index("chapter-intuition"))
        self.assertLess(result.index("chapter-intuition"),
                        result.index("book-callout-goal"))

    def test_lead_falls_back_to_just_after_the_title(self):
        lead = intuition.chapter_lead(0)
        fragment = "<h1>第 0 章</h1>\n<p>正文</p>"
        result = intuition.insert_lead(fragment, lead)
        self.assertLess(result.index("</h1>"), result.index("chapter-intuition"))
        self.assertLess(result.index("chapter-intuition"), result.index("<p>正文</p>"))

    def test_lead_requires_a_title(self):
        with self.assertRaisesRegex(Exception, "缺少章标题"):
            intuition.insert_lead("<p>没有标题</p>", intuition.chapter_lead(0))


if __name__ == "__main__":
    unittest.main()
