"""Invalid book sources must fail before expensive rendering begins."""
import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build


class PreflightTests(unittest.TestCase):
    def test_invalid_terminology_stops_before_site_and_media_builds(self):
        failures = [{"name": "术语 lint", "status": "fail", "detail": "禁用变体新增"}]
        error = io.StringIO()
        with (
            patch.object(build, "check_manifest", return_value=failures),
            patch.object(build, "build_site") as site,
            patch.object(build, "build_html") as html,
            contextlib.redirect_stderr(error),
        ):
            self.assertEqual(1, build.main(["all"]))
        site.assert_not_called()
        html.assert_not_called()
        self.assertIn("术语 lint", error.getvalue())


if __name__ == "__main__":
    unittest.main()
