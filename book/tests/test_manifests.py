#!/usr/bin/env python3
"""总 manifest 与 BMS 卷转换器的契约测试（不跑成书构建）。"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "book"))

from manifests.convert_bms import ManifestError, convert  # noqa: E402


def make_source(tmp: Path, *, guides=None, sources=None, chapter_sources=None,
                book_sources=None, terms=None, parts=None) -> Path:
    manifest = {
        "title": "合成卷",
        "subtitle": "测试",
        "author": "test",
        "license": {"docs": "CC BY-SA 4.0"},
        "language": "zh-CN",
        "parts": parts or [
            {"id": "p0", "title": "导读", "files": ["00-前言.md"]},
            {"id": "p1", "title": "第一部分", "files": ["01-甲.md"]},
        ],
        "part_goals": {"p1": "把事说清楚"},
        "chapter_guides": guides if guides is not None else {
            "01-甲.md": {"question": "问", "deliverable": "交", "boundary": "不证"}},
        "sources": sources if sources is not None else {"s1": {"title": "来源"}},
        "book_sources": book_sources if book_sources is not None else [],
        "chapter_sources": chapter_sources if chapter_sources is not None else {
            "01-甲.md": ["s1"]},
        "index_terms": "terms.json",
    }
    (tmp / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False),
                                       encoding="utf-8")
    (tmp / "terms.json").write_text(json.dumps(terms or ["AFE"], ensure_ascii=False),
                                    encoding="utf-8")
    return tmp / "manifest.json"


class RootManifestTests(unittest.TestCase):
    def test_schema3_and_volumes(self):
        root = json.loads((ROOT / "book/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(3, root["schema"])
        self.assertEqual(["I", "II"], [v["id"] for v in root["volumes"]])
        for volume in root["volumes"]:
            self.assertTrue((ROOT / volume["manifest"]).is_file(), volume["manifest"])
            self.assertEqual(700, volume["print"]["max_pages_per_volume"])


class ConvertBmsTests(unittest.TestCase):
    def test_real_manifest_counts(self):
        volume = convert()
        self.assertEqual(3, volume["schema"])
        self.assertEqual("II", volume["id"])
        chapters = sum(len(part["files"]) for part in volume["parts"])
        self.assertEqual(32, chapters)
        self.assertEqual(1, len(volume["front_matter"]))
        self.assertEqual(5, len(volume["appendix"]["files"]))
        self.assertEqual(99, len(volume["index_terms"]))
        self.assertEqual(700, volume["print"]["max_pages_per_volume"])

    def test_missing_chapter_guide_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = make_source(Path(tmp), guides={})
            with self.assertRaisesRegex(ManifestError, "章节罗盘缺章"):
                convert(source)

    def test_orphan_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = make_source(Path(tmp), sources={"s1": {}, "s2": {}})
            with self.assertRaisesRegex(ManifestError, "孤儿"):
                convert(source)

    def test_undefined_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = make_source(Path(tmp), chapter_sources={"01-甲.md": ["s9"]})
            with self.assertRaisesRegex(ManifestError, "未登记来源"):
                convert(source)

    def test_empty_term_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = make_source(Path(tmp), terms=["AFE", " "])
            with self.assertRaisesRegex(ManifestError, "空项"):
                convert(source)

    def test_duplicate_term_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = make_source(Path(tmp), terms=["AFE", "AFE"])
            with self.assertRaisesRegex(ManifestError, "重复"):
                convert(source)

    def test_unclassified_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = make_source(Path(tmp), parts=[
                {"id": "p1", "title": "第一部分", "files": ["01-甲.md", "散页.md"]}])
            with self.assertRaisesRegex(ManifestError, "无法归类"):
                convert(source)


if __name__ == "__main__":
    unittest.main()
