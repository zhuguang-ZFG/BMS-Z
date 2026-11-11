#!/usr/bin/env python3
"""77 页装配、模型、目录占位、习题拆分、索引与审计。"""
import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

BOOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOOK))

from book import assemble, intuition  # noqa: E402
from book.manifest import validate_manifest  # noqa: E402
import book_fixtures  # noqa: E402


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.manifest = book_fixtures.manifest()
        book_fixtures.write_docs(root / "docs")
        cls.site = book_fixtures.write_site(root / "site")
        cls.data = book_fixtures.write_data(root / "data")
        cls.out = root / "dist"
        validate_manifest(cls.manifest, docs_dir=root / "docs")
        cls.html_path = assemble.build_html(
            cls.out, cls.site, cls.data, root / "docs", cls.manifest,
            rebuild_site=False, final=False)
        cls.document = cls.html_path.read_text(encoding="utf-8")
        cls.model = json.loads((cls.out / "book-model.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_77_pages_in_fixed_order(self):
        self.assertEqual(77, len(self.model["pages"]))
        kinds = [page["kind"] for page in self.model["pages"]]
        self.assertEqual(11, kinds[:11].count("front") + kinds[:11].count("half_title")
                         + kinds[:11].count("title_page") + kinds[:11].count("copyright")
                         + kinds[:11].count("toc") + kinds[:11].count("list_of_figures")
                         + kinds[:11].count("list_of_tables"))
        self.assertEqual(5, kinds.count("part"))
        self.assertEqual(19, kinds.count("chapter"))
        self.assertEqual(8, kinds.count("appendix_opener"))
        self.assertEqual(6, kinds.count("back"))
        self.assertEqual("half_title", kinds[0])
        self.assertEqual("copyright", kinds[2])
        self.assertEqual("part", kinds[11])
        self.assertEqual("chapter", kinds[12])
        self.assertEqual(5, self.document.count('class="part-intro"'))
        self.assertNotIn('class="part-intro"></p>', self.document)

    def test_titles_are_emoji_free(self):
        self.assertNotIn("📘", self.document)
        self.assertIn('data-title="第 0 章 电路直觉"', self.document)

    def test_toc_lof_lot_and_index_use_000(self):
        for page in self.model["pages"]:
            if page["kind"] in {"toc", "list_of_figures", "list_of_tables", "index"}:
                self.assertIn("000", page["html"])
        self.assertTrue(self.model["toc"])
        self.assertTrue(self.model["lof"])
        self.assertTrue(self.model["lot"])

    def test_chapter_exercises_and_appendix_answers(self):
        self.assertIn("示例问题？", self.document)
        self.assertIn("示例答案。", self.document)
        self.assertNotIn("<details", self.document)
        self.assertEqual(2, self.document.count('class="chapter-exercises"'))
        self.assertIn('href="#p1-01-ch0--q-q-ch0-01"', self.document)

    def test_assets_inline_and_no_remote(self):
        self.assertIn("data:image/svg+xml;base64,", self.document)
        self.assertNotIn('src="assets/', self.document)
        self.assertNotIn('src="http', self.document)
        self.assertNotIn("<iframe", self.document)

    def test_unique_ids_and_reachable_internal_links(self):
        audit = self.model["audit"]
        self.assertEqual([], audit["errors"])
        self.assertEqual(77, audit["pages"])
        self.assertGreater(audit["bytes"], 100_000)

    def test_model_stats(self):
        stats = self.model["stats"]
        self.assertEqual(77, stats["logical_pages"])
        self.assertGreaterEqual(stats["figures"], 1)
        self.assertGreaterEqual(stats["tables"], 1)
        self.assertGreater(stats["images"], 0)

    def test_audit_rejects_external_scripts(self):
        broken = self.document.replace(
            "</body>", '<script src="https://cdn.example/x.js"></script></body>')
        audit = assemble.audit_html(broken, self.model)
        self.assertIn("含外部脚本", audit["errors"])

    def test_audit_ignores_base64_payload_with_placeholder_substring(self):
        payload = "QUJD" + "TBD" + "REVG"
        document = self.document.replace(
            "</body>",
            f'<img alt="" src="data:image/png;base64,{payload}"></body>')
        audit = assemble.audit_html(document, self.model)
        self.assertNotIn(
            "书内仍有占位标记", "\n".join(audit["errors"] + audit["warnings"]))

    def test_audit_flags_visible_placeholder_after_data_token(self):
        document = self.document.replace(
            "</body>", '<p>metadata: TBD</p><img src="x.png"></body>')
        audit = assemble.audit_html(document, self.model)
        self.assertIn("书内仍有占位标记: TBD", audit["errors"])

    def test_appendix_a_table_is_registered_in_lot(self):
        page = next(p for p in self.model["pages"]
                    if p["id"] == "appendix-a-table")
        self.assertEqual(["表 A-1"],
                         [table["number"] for table in page["tables"]])
        entry = next(item for item in self.model["lot"]
                     if item["number"] == "表 A-1")
        self.assertEqual("appendix-a-table-wrap", entry["anchor"])

    def test_animation_table_is_sorted_by_chapter(self):
        rows = [
            {"id": "anim-9", "anchor": "anim-9", "chapter": 10,
             "title": "十", "one_line": "十。"},
            {"id": "anim-1", "anchor": "anim-1", "chapter": 2,
             "title": "二", "one_line": "二。"},
        ]
        table = assemble._animation_table(rows)
        self.assertLess(table.index("第 2 章"), table.index("第 10 章"))

    def test_appendix_source_pages_have_no_h1(self):
        for page in self.model["pages"]:
            if page["kind"] == "appendix" and page["source"]:
                self.assertEqual(
                    0, len(assemble.H1_RE.findall(page["html"])), page["id"])

    def test_appendix_source_page_with_residual_h1_is_flagged(self):
        page = {"id": "page-p6-01-s6-1", "html": "<h1>残留标题</h1>",
                "source": "p6-01-s6-1.md", "group": "appendix"}
        self.assertTrue(assemble._one_h1_problem(page))

    def test_exports_figure_and_table_manifests(self):
        for name in ("figures.yml", "tables.yml"):
            entries = yaml.safe_load(
                (self.out / name).read_text(encoding="utf-8"))
            self.assertTrue(entries, name)
            self.assertEqual(
                {"id", "chapter", "number", "title", "anchor", "source"},
                set(entries[0]), name)

    def test_part_pages_carry_illustrations(self):
        self.assertEqual(5, self.document.count('class="part-art-svg"'))
        parts = [page for page in self.model["pages"]
                 if page["kind"] == "part"]
        self.assertEqual(5, len(parts))
        for page in parts:
            self.assertEqual(1, page["html"].count("<svg"), page["id"])
            self.assertNotIn(
                'class="part-art" aria-hidden="true"></div>', page["html"])

    def test_missing_opener_art_warns_and_keeps_empty_plate(self):
        manifest = copy.deepcopy(book_fixtures.manifest())
        part = next(item for item in manifest["parts"] if item["id"] == "II")
        part.pop("opener_art", None)
        root = Path(self.tmp.name)
        validate_manifest(manifest, docs_dir=root / "docs")
        out = root / "dist-no-art"
        assemble.build_html(
            out, self.site, self.data, root / "docs", manifest,
            rebuild_site=False, final=False)
        model = json.loads(
            (out / "book-model.json").read_text(encoding="utf-8"))
        page = next(page for page in model["pages"]
                    if page["id"] == "part-ii" and page["kind"] == "part")
        self.assertNotIn("<svg", page["html"])
        self.assertIn('<div class="part-art" aria-hidden="true"></div>',
                      page["html"])
        self.assertTrue(
            any("缺少 opener_art" in str(message)
                for message in model["build_warnings"]),
            model["build_warnings"])

    def test_every_chapter_has_one_intuition_lead(self):
        self.assertEqual(19, self.document.count('class="chapter-intuition"'))
        for page in self.model["pages"]:
            if page["kind"] != "chapter":
                self.assertNotIn("chapter-intuition", page["html"], page["id"])
                continue
            self.assertEqual(
                1, page["html"].count('class="chapter-intuition"'), page["id"])
            match = re.search(r"-ch(\d+)$", page["stem"])
            self.assertIsNotNone(match, page["stem"])
            chapter = int(match.group(1))
            self.assertIn(f'class="ci-no" aria-hidden="true">'
                          f'{chapter:02d}<', page["html"])
            self.assertIn(intuition.CHAPTER_LEADS[chapter], page["html"])


if __name__ == "__main__":
    unittest.main()
