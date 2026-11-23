"""Reject invalid per-volume books before replacing the downloadable EPUB."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import epub


class VolumeStandardTests(unittest.TestCase):
    def test_validator_failure_preserves_each_previous_download(self):
        for volume in ("I", "II"):
            with self.subTest(volume=volume), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                out = root / "volume"
                out.mkdir()
                published = out / "book.epub"
                published.write_bytes(b"previous valid EPUB")
                source = (root / "analog/analog-book/dist/analog-circuit-book.epub"
                          if volume == "I" else out / "bms-book.epub")
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_bytes(b"invalid new EPUB")
                with (
                    patch.object(epub, "ROOT", root),
                    patch.object(epub, "VOLUME_DIR", {volume: out}),
                    patch.object(epub, "run"),
                    patch.object(epub, "check_standard", side_effect=ValueError("invalid")) as check,
                ):
                    with self.assertRaisesRegex(ValueError, "invalid"):
                        epub.build_epub(volume, True)
                    check.assert_called_once_with(source)
                self.assertEqual(b"previous valid EPUB", published.read_bytes())


if __name__ == "__main__":
    unittest.main()
