"""Body changes must never slip into a publication built from old editions."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from refresh_collection import validate_changes


class RefreshTests(unittest.TestCase):
    def test_collection_edit_is_reusable(self):
        validate_changes(["book/reading_lab.py", "book/tests/test_combined_reading.py"])

    def test_body_site_and_manifest_edits_require_full_build(self):
        for path in ["bms-book/book/05-测量链.md", "analog/analog-book/build_book.py",
                     "docs/reading.md", "book/manifest.json", "package-lock.json"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                validate_changes(["book/reading_lab.py", path])
