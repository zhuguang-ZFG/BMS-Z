"""A configured standard validator must fail closed, including warnings."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from epub_standard import check


class StandardTests(unittest.TestCase):
    def run_check(self, warnings=0, returncode=0):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            jar = root / "validator.jar"
            jar.touch()

            def run(command, **kwargs):
                Path(command[-1]).write_text(
                    json.dumps(
                        {
                            "checker": {
                                "checkerVersion": "5.4.0",
                                "nFatal": 0,
                                "nError": 0,
                                "nWarning": warnings,
                                "nUsage": 0,
                            }
                        }
                    ),
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=returncode, stdout="", stderr="")

            with (
                patch.dict("os.environ", {"EPUBCHECK_JAR": str(jar)}),
                patch("epub_standard.subprocess.run", side_effect=run),
            ):
                return check(root / "book.epub")

    def test_success_reports_actual_validator_version(self):
        self.assertEqual(self.run_check()["version"], "5.4.0")

    def test_warnings_block_publication_even_with_zero_exit(self):
        with self.assertRaisesRegex(ValueError, "EPUBCheck failed"):
            self.run_check(warnings=1)

    def test_nonzero_exit_blocks_publication_even_with_empty_report(self):
        with self.assertRaisesRegex(ValueError, "EPUBCheck failed"):
            self.run_check(returncode=1)

    def test_bad_configuration_cannot_silently_skip_check(self):
        with patch.dict("os.environ", {"EPUBCHECK_JAR": "missing-validator.jar"}):
            with self.assertRaisesRegex(ValueError, "does not exist"):
                check(Path("book.epub"))


if __name__ == "__main__":
    unittest.main()
