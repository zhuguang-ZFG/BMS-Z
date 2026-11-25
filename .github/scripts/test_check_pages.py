"""Regression tests for static-site path boundaries in check_pages.py."""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_pages  # noqa: E402


class CheckPagesBoundaryTests(unittest.TestCase):
    def test_rejects_encoded_dot_segments_outside_dist(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dist = root / "site"
            dist.mkdir()
            (root / "README.md").write_text("outside the deployed site", encoding="utf-8")
            (dist / "index.html").write_text(
                '<strong data-animation-count="0">0</strong>'
                '<a href="two.html">two</a>'
                '<a href="/BMS-Z/%2e%2e/README.md">outside</a>'
                '<div class="vp-doc">'
                '<img src="/BMS-Z/%2e%2e/README.md" width="1" height="1">'
                '</div>',
                encoding="utf-8",
            )
            (dist / "two.html").write_text('<a href="index.html">home</a>', encoding="utf-8")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch.object(
                sys, "argv", ["check_pages.py", str(dist), "--base", "/BMS-Z/"]
            ), redirect_stdout(stdout), redirect_stderr(stderr):
                result = check_pages.main()

            self.assertEqual(1, result, stdout.getvalue())
            self.assertIn("越界", stderr.getvalue())
            self.assertIn("越界图片", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
