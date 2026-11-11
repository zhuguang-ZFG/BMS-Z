#!/usr/bin/env python3
"""schema-2 manifest 必须覆盖每一页 docs，并给出 77 个逻辑页。"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from book import config  # noqa: E402
from book.manifest import (BookError, book_pages, direct_files,  # noqa: E402
                           excluded_files, load_manifest, manifest_sha256,
                           validate_manifest)
import book_fixtures  # noqa: E402


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.docs = self.root / "docs"
        self.manifest = book_fixtures.manifest()
        book_fixtures.write_docs(self.docs)

    def problems(self, manifest=None):
        try:
            validate_manifest(self.manifest if manifest is None else manifest,
                              self.docs)
        except BookError as exc:
            return str(exc)
        return ""

    def test_accepts_complete_schema_2_manifest(self):
        validate_manifest(self.manifest, self.docs)
        self.assertEqual(54, len(direct_files(self.manifest)))
        self.assertEqual(10, len(excluded_files(self.manifest)))
        self.assertEqual(64, len(direct_files(self.manifest)) + len(excluded_files(self.manifest)))

    def test_book_pages_are_77_and_ordered(self):
        pages = book_pages(self.manifest)
        self.assertEqual(77, len(pages))
        self.assertEqual(
            ["half-title", "title-page", "copyright", "p0-01-preface",
             "p0-02-how-to-use", "p0-03-timeline", "p0-11-conventions",
             "p0-12-symbols", "toc", "list-of-figures", "list-of-tables"],
            [p["stem"] for p in pages[:11]])
        self.assertEqual("part-I", pages[11]["stem"])
        self.assertEqual(24, sum(1 for p in pages if p["kind"] in {"part", "chapter"}))
        self.assertEqual(36, sum(1 for p in pages if p["kind"].startswith("appendix")))
        self.assertEqual(["bibliography", "index", "p9-12-changelog",
                          "p9-13-thanks", "p9-14-credits", "colophon"],
                         [p["stem"] for p in pages[-6:]])
        self.assertEqual(77, len({p["stem"] for p in pages}))

    def test_book_pages_use_documented_key_order(self):
        keys = ["kind", "stem", "title", "file", "part_id", "part_title",
                "unit_title", "appendix_id", "transform", "generated"]
        pages = book_pages(self.manifest)
        self.assertTrue(pages)
        for page in pages:
            self.assertEqual(keys, list(page))

    def test_rejects_legacy_schema(self):
        self.manifest["schema"] = 1
        self.assertIn("schema", self.problems())

    def test_rejects_missing_chapter(self):
        self.manifest["parts"][0]["units"][0]["chapters"].pop()
        self.assertIn("19", self.problems())

    def test_rejects_duplicate_chapter(self):
        self.manifest["parts"][0]["units"][0]["chapters"].append("p1-01-ch0.md")
        self.assertIn("重复", self.problems())

    def test_rejects_unknown_excluded_page(self):
        self.manifest["excluded_pages"][0]["file"] = "p1-01-ch0.md"
        self.assertIn("排除", self.problems())

    def test_rejects_excluded_without_reason(self):
        self.manifest["excluded_pages"][0]["reason"] = ""
        self.assertIn("reason", self.problems())

    def test_rejects_missing_new_page(self):
        self.manifest["front_matter"] = [
            e for e in self.manifest["front_matter"]
            if e.get("file") != "p0-11-conventions.md"]
        self.assertIn("p0-11", self.problems())

    def test_rejects_duplicate_direct_page(self):
        self.manifest["appendices"][1]["files"].append("p0-01-preface.md")
        self.assertIn("重复", self.problems())

    def test_rejects_manual_spine(self):
        self.manifest["cover"]["spine_mm"] = 20
        self.assertIn("spine_mm", self.problems())

    def test_rejects_negative_bleed(self):
        self.manifest["cover"]["bleed_mm"] = -1
        self.assertIn("cover.bleed_mm 必须为正数", self.problems())

    def test_rejects_boolean_bleed(self):
        self.manifest["cover"]["bleed_mm"] = True
        self.assertIn("cover.bleed_mm 必须为正数", self.problems())

    def test_rejects_non_positive_paper_caliper(self):
        self.manifest["cover"]["paper_caliper_mm"] = 0
        self.assertIn("cover.paper_caliper_mm 必须为正数", self.problems())

    def test_rejects_unknown_appendix_id(self):
        self.manifest["appendices"][-1]["id"] = "Z"
        self.assertIn("附录 ID 必须依次为 ABCDEFGH", self.problems())

    def test_rejects_wrong_appendix_file_count(self):
        self.manifest["appendices"][2]["files"].pop()
        self.assertIn("附录 C 的文件数应为 5，当前为 4", self.problems())

    def test_rejects_appendix_a_without_animation_index_data(self):
        del self.manifest["appendices"][0]["data"]
        self.assertIn("附录 A 必须使用 animation_index 变换并给出 data",
                      self.problems())

    def test_rejects_appendix_f_without_answers_transform(self):
        self.manifest["appendices"][5].pop("transform")
        self.assertIn("附录 F 必须使用 answers 变换", self.problems())

    def test_rejects_missing_back_matter_kind(self):
        self.manifest["back_matter"] = [
            e for e in self.manifest["back_matter"] if e.get("kind") != "index"]
        self.assertIn("index", self.problems())

    def test_rejects_unknown_edition_status(self):
        self.manifest["release"]["edition_status"] = "retired"
        self.assertIn("release.edition_status 必须为 draft 或 final",
                      self.problems())

    def test_rejects_unknown_front_matter_kind(self):
        self.manifest["front_matter"][0]["kind"] = "blank_page"
        self.assertIn("front_matter 含未知生成页：blank_page", self.problems())

    def test_rejects_duplicate_front_matter_kind(self):
        self.manifest["front_matter"].append({"kind": "toc"})
        self.assertIn("front_matter 生成页重复：toc", self.problems())

    def test_rejects_missing_front_matter_kind(self):
        self.manifest["front_matter"] = [
            e for e in self.manifest["front_matter"] if e.get("kind") != "toc"]
        self.assertIn("front_matter 缺少生成页：toc", self.problems())

    def test_rejects_out_of_sequence_chapter_numbers(self):
        self.manifest["parts"][-1]["units"][0]["chapters"][-1] = "p4-03-ch19.md"
        self.assertIn("章节编号必须依次为 0..18", self.problems())

    def test_rejects_null_sections(self):
        expected = {
            "front_matter": "front_matter 缺少生成页",
            "parts": "parts ID 必须依次为",
            "appendices": "附录 ID 必须依次为",
            "back_matter": "back_matter 必须恰好包含",
        }
        for key, message in expected.items():
            manifest = book_fixtures.manifest()
            manifest[key] = None
            with self.subTest(section=key):
                self.assertIn(message, self.problems(manifest))

    def test_rejects_non_list_sections(self):
        for key in ("front_matter", "parts", "appendices", "back_matter"):
            manifest = book_fixtures.manifest()
            manifest[key] = {"bad": True}
            with self.subTest(section=key):
                self.assertIn(f"{key} 必须是列表", self.problems(manifest))

    def test_rejects_non_string_front_matter_kind(self):
        self.manifest["front_matter"][0]["kind"] = None
        self.assertIn("front_matter 的 kind 必须是字符串", self.problems())

    def test_rejects_non_string_back_matter_kind(self):
        self.manifest["back_matter"][0]["kind"] = 5
        self.assertIn("back_matter 的 kind 必须是字符串", self.problems())

    def test_rejects_entries_without_kind_or_file(self):
        for key in ("front_matter", "back_matter"):
            manifest = book_fixtures.manifest()
            manifest[key].append({"title": "无类型页"})
            with self.subTest(section=key):
                self.assertIn(f"{key} 的文件页必须给出 .md 文件",
                              self.problems(manifest))

    def test_rejects_non_object_entries(self):
        for key in ("front_matter", "parts", "appendices", "back_matter"):
            manifest = book_fixtures.manifest()
            manifest[key][0] = "not-an-object"
            with self.subTest(section=key):
                self.assertIn(f"{key} 的条目必须是对象", self.problems(manifest))

    def test_load_manifest_reads_real_file_and_wraps_bad_json(self):
        path = self.root / "manifest.json"
        path.write_text(json.dumps(self.manifest, ensure_ascii=False),
                        encoding="utf-8")
        self.assertEqual(self.manifest, load_manifest(path))
        bad = self.root / "broken.json"
        bad.write_text('{"schema": 2,', encoding="utf-8")
        with self.assertRaises(BookError) as caught:
            load_manifest(bad)
        self.assertIn("JSON", str(caught.exception))

    def test_manifest_sha256_matches_file_bytes(self):
        path = self.root / "manifest.json"
        payload = json.dumps(self.manifest, ensure_ascii=False,
                             indent=2).encode("utf-8")
        path.write_bytes(payload)
        self.assertEqual(hashlib.sha256(payload).hexdigest(),
                         manifest_sha256(path))


class FixturePathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_write_site_uses_argument_as_final_directory(self):
        site = self.root / "site"
        self.assertEqual(site, book_fixtures.write_site(site))
        self.assertTrue((site / "index.html").is_file())
        self.assertTrue((site / "p1-01-ch0.html").is_file())
        self.assertTrue(
            (site / "assets" / "stylesheets" / "main.abc.min.css").is_file())
        self.assertFalse((site / "site").exists())

    def test_write_data_uses_argument_as_final_directory(self):
        data = self.root / "data"
        self.assertEqual(data, book_fixtures.write_data(data))
        self.assertTrue((data / "animations.yml").is_file())
        self.assertTrue((data / "index-terms.yml").is_file())
        self.assertTrue((data / "chapter-signoff.yml").is_file())
        self.assertFalse((data / "data").exists())


class RepositoryManifestTests(unittest.TestCase):
    def test_real_manifest_is_schema_2_and_covers_repository_docs(self):
        manifest = load_manifest()
        validate_manifest(manifest, docs_dir=config.DOCS)
        self.assertEqual(77, len(book_pages(manifest)))
        direct = direct_files(manifest)
        for name in ("p0-11-conventions.md", "p0-12-symbols.md",
                     "p9-15-glossary.md"):
            self.assertIn(name, direct)
        self.assertEqual(10, len(excluded_files(manifest)))
        structure = manifest["cover"]["back_cover"]["structure"]
        self.assertEqual(
            [("第一篇 基础", "电路直觉、无源元件与基本定律"),
             ("第二篇 器件", "二极管、BJT、MOSFET 与运放内部"),
             ("第三篇 拓扑", "放大、比较、电源、定时与信号产生"),
             ("第四篇 设计", "设计方法、参数容差与 PCB 实战"),
             ("第五篇 调试", "排故五步、故障速查与大师心法")],
            [(row["title"], row["scope"]) for row in structure])


if __name__ == "__main__":
    unittest.main()
