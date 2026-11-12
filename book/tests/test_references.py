#!/usr/bin/env python3
"""跨卷引用索引与审计的契约测试（不跑成书构建）。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "book"))

from references import ReferenceIndex, site_href  # noqa: E402


class ReferenceIndexTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = ReferenceIndex()

    def test_all_chapters_indexed(self) -> None:
        analog = [c for c in self.index.chapters.values() if c.volume == "I"]
        bms = [c for c in self.index.chapters.values() if c.volume == "II"]
        numbers_i = {c.number for c in analog if c.number.isdigit()}
        numbers_ii = {c.number for c in bms if c.number.isdigit()}
        self.assertEqual(numbers_i, {str(n) for n in range(19)})
        self.assertEqual(numbers_ii, {str(n) for n in range(1, 33)})
        self.assertNotIn(str(ROOT / "bms-book/book/00-前言.md"), self.index.by_source)

    def test_appendix_labels(self) -> None:
        glossary = (ROOT / "bms-book/book/附录C-术语表.md").resolve()
        chapter = self.index.by_source[glossary]
        self.assertEqual(chapter.number, "附录 C")
        self.assertEqual(chapter.label, "卷二·附录 C《术语表》")

    def test_resolves_cross_volume_link(self) -> None:
        source = (ROOT / "analog/docs/p1-10-ch9.md").resolve()
        href = "../../bms-book/book/06-AFE.md"
        resolved = self.index.resolve(source, href)
        self.assertIsNotNone(resolved)
        chapter, anchor = resolved
        self.assertEqual(chapter.volume, "II")
        self.assertEqual(chapter.number, "6")
        self.assertEqual(anchor, "")
        self.assertIsNone(self.index.resolve(source, "p1-01-ch0.md"))

    def test_site_href(self) -> None:
        source = (ROOT / "bms-book/book/05-测量链.md").resolve()
        href = "../../analog/docs/p1-10-ch9.md#ch9"
        self.assertEqual(site_href(self.index, source, href, "/BMS-Z"),
                         "/BMS-Z/volume-1/p1-10-ch9.html#ch9")

    def test_anchor_presence(self) -> None:
        source = (ROOT / "bms-book/book/05-测量链.md").resolve()
        chapter, _ = self.index.resolve(source, "../../analog/docs/p1-10-ch9.md")
        self.assertIn("ch9", self.index.anchors(chapter.source))
        self.assertNotIn("ch99", self.index.anchors(chapter.source))

    def test_repository_audit_is_clean(self) -> None:
        self.assertEqual(self.index.audit(), [])


if __name__ == "__main__":
    unittest.main()
