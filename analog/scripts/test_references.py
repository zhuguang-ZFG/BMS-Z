#!/usr/bin/env python3
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_references  # noqa: E402

REF = ROOT / "analog-book/data/references.yml"
SRC = ROOT / "analog-book/data/sources.yml"


class ReferencesTests(unittest.TestCase):
    def test_schema_and_unique_ids(self):
        errors = check_references.validate(REF, SRC)
        schema_errors = [e for e in errors if ("缺字段" in e or "id 重复" in e
                                               or "顶层" in e or "chapters" in e)]
        self.assertEqual([], schema_errors, schema_errors)

    def test_expansion_floor_and_required_entries(self):
        errors = check_references.validate(REF, SRC)
        self.assertEqual([], errors, errors)

    def test_all_chapters_have_citations_slot(self):
        import re
        files = sorted(p for p in (ROOT / "docs").glob("p*-ch*.md")
                       if re.fullmatch(r"p\d+-\d+-ch\d+\.md", p.name))
        errors = check_references.scan_chapters(files)
        self.assertEqual([], errors, errors)


if __name__ == "__main__":
    unittest.main()
