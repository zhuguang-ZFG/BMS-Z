"""下载文件必须和本次合集构建记录一致。"""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import downloads


class CombinedDownloadTests(unittest.TestCase):
    def run_build(self, directory, mismatch=False):
        root = Path(directory)
        source = root / "from-analog-to-bms.epub"
        source.write_bytes(b"fixture epub")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        report = {
            "generated_at": "2026-11-21T00:00:00+00:00",
            "outputs": [
                {
                    "path": "combined/" + source.name,
                    "sha256": "bad" if mismatch else digest,
                }
            ],
        }
        (root / "combined-build-report.json").write_text(
            json.dumps(report), encoding="utf-8"
        )
        release = {
            "title": "合集",
            "subtitle": "阅读",
            "version": "2.0.0",
            "volumes": [],
        }
        files = [
            {
                "volume": "combined",
                "volume_title": "两卷合集",
                "kind": "epub",
                "label": "EPUB",
                "description": "离线阅读",
                "source": source,
                "latest": source.name,
                "versioned": "book-v2.epub",
            }
        ]
        with (
            patch.object(downloads, "load_release", return_value=release),
            patch.object(downloads, "collect_files", return_value=files),
            patch.object(downloads, "COMBINED_DIR", root),
        ):
            return downloads.build_downloads(root / "site")

    def test_download_page_includes_matching_report_and_checksum(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_build(directory)
            target = Path(directory) / "site/downloads"
            self.assertTrue((target / "combined-build-report.json").is_file())
            self.assertIn(
                "combined-build-report.json",
                (target / "index.html").read_text(encoding="utf-8"),
            )
            digest = result["combined_build_report"]["sha256"]
            self.assertIn(
                digest, (target / "SHA256SUMS.txt").read_text(encoding="utf-8")
            )

    def test_stale_report_cannot_replace_existing_downloads(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "site/downloads"
            target.mkdir(parents=True)
            marker = target / "index.html"
            marker.write_text("previous download page", encoding="utf-8")
            with self.assertRaisesRegex(downloads.DownloadError, "不匹配"):
                self.run_build(directory, mismatch=True)
            self.assertEqual(
                marker.read_text(encoding="utf-8"), "previous download page"
            )


if __name__ == "__main__":
    unittest.main()
