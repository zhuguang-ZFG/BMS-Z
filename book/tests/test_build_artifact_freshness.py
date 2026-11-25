"""Build artifact audits must include non-Markdown source inputs."""

import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

BOOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BOOK))
SPEC = importlib.util.spec_from_file_location("collection_build_freshness", BOOK / "build.py")
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class ArtifactFreshnessTests(unittest.TestCase):
    def test_newer_non_markdown_source_marks_volume_artifact_stale(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            chapter = root / "bms-book" / "book" / "01-chapter.md"
            asset = root / "bms-book" / "assets" / "diagram.svg"
            output_dir = root / "book" / "dist" / "volume-2"
            artifact = output_dir / "book.html"
            for path, content in (
                (chapter, "chapter source"),
                (asset, "changed SVG source"),
                (artifact, "old built HTML"),
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            now = time.time()
            for path, offset in ((chapter, 100), (artifact, 150), (asset, 200)):
                os.utime(path, (now + offset, now + offset))

            with (
                patch.object(build, "ROOT", root),
                patch.object(build, "EXPECTED", {"II": ["book.html"]}),
                patch.object(build, "VOLUME_DIR", {"II": output_dir}),
                patch.object(build, "HTML_LIMITS_BYTES", {"II": 1024}),
            ):
                checks, artifacts = build.check_artifacts()

            self.assertEqual(1, len(artifacts))
            self.assertEqual("fail", checks[0]["status"])

    def test_newer_volume_i_inputs_mark_artifact_stale(self):
        inputs = (
            "analog/analog-book/data/animations.yml",
            "analog/analog-book/build_book.py",
            "analog/analog-book/build_print_book.py",
            "analog/scripts/build_site.py",
            "analog/scripts/visual_player.py",
            "analog/scripts/site_media/reading.css",
            "book/manifest.json",
            "book/shared/00-title.md",
            "book/shared_front.py",
            "book/glossary.md",
            "book/shared_glossary.py",
            "book/references.py",
            "bms-book/manifest.json",
            "bms-book/book/01-chapter.md",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            chapter = root / "analog/docs/chapter.md"
            output_dir = root / "book/dist/volume-1"
            artifact = output_dir / "book.html"
            test_script = root / "analog/scripts/test_site_build.py"
            paths = (chapter, artifact, test_script, *(root / item for item in inputs))
            for path in paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(path.name, encoding="utf-8")

            now = time.time()
            for path in paths:
                os.utime(path, (now + 100, now + 100))
            os.utime(artifact, (now + 150, now + 150))
            os.utime(test_script, (now + 200, now + 200))

            with (
                patch.object(build, "ROOT", root),
                patch.object(build, "EXPECTED", {"I": ["book.html"]}),
                patch.object(build, "VOLUME_DIR", {"I": output_dir}),
                patch.object(build, "HTML_LIMITS_BYTES", {"I": 1024}),
            ):
                checks, _ = build.check_artifacts()
                self.assertEqual("ok", checks[0]["status"], "test scripts are not inputs")
                for item in inputs:
                    source = root / item
                    with self.subTest(source=item):
                        os.utime(source, (now + 200, now + 200))
                        checks, _ = build.check_artifacts()
                        self.assertEqual("fail", checks[0]["status"])
                        os.utime(source, (now + 100, now + 100))

    def test_newer_shared_content_marks_volume_ii_artifact_stale(self):
        inputs = (
            "bms-book/ocv-lab.css",
            "book/manifest.json",
            "book/shared/00-title.md",
            "book/shared_front.py",
            "book/glossary.md",
            "book/shared_glossary.py",
            "docs/public/illustrations/bms-scrapbook.svg",
            "docs/.vitepress/book-sources.mjs",
            "docs/.vitepress/book-reading-split.mjs",
            "docs/.vitepress/cross-volume.mjs",
            "docs/.vitepress/base.ts",
            "analog/analog-book/manifest.json",
            "analog/docs/p1-10-ch9.md",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            chapter = root / "bms-book/book/01-chapter.md"
            output_dir = root / "book/dist/volume-2"
            artifact = output_dir / "book.html"
            unrelated = root / "docs/.vitepress/book-sources.test.mjs"
            paths = (chapter, artifact, unrelated, *(root / item for item in inputs))
            for path in paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(path.name, encoding="utf-8")

            now = time.time()
            for path in paths:
                os.utime(path, (now + 100, now + 100))
            os.utime(artifact, (now + 150, now + 150))
            os.utime(unrelated, (now + 200, now + 200))

            with (
                patch.object(build, "ROOT", root),
                patch.object(build, "EXPECTED", {"II": ["book.html"]}),
                patch.object(build, "VOLUME_DIR", {"II": output_dir}),
                patch.object(build, "HTML_LIMITS_BYTES", {"II": 1024}),
            ):
                checks, _ = build.check_artifacts()
                self.assertEqual("ok", checks[0]["status"], "test modules are not inputs")
                for item in inputs:
                    source = root / item
                    with self.subTest(source=item):
                        os.utime(source, (now + 200, now + 200))
                        checks, _ = build.check_artifacts()
                        self.assertEqual("fail", checks[0]["status"])
                        os.utime(source, (now + 100, now + 100))

    def test_planning_notes_do_not_mark_artifacts_stale(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            chapter = root / "bms-book/book/01-chapter.md"
            note = root / "analog/docs/superpowers/visual/backlog.yml"
            output_dir = root / "book/dist/volume-2"
            artifact = output_dir / "book.html"
            for path in (chapter, note, artifact):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(path.name, encoding="utf-8")

            now = time.time()
            os.utime(chapter, (now + 100, now + 100))
            os.utime(artifact, (now + 150, now + 150))
            os.utime(note, (now + 200, now + 200))

            with (
                patch.object(build, "ROOT", root),
                patch.object(build, "EXPECTED", {"II": ["book.html"]}),
                patch.object(build, "VOLUME_DIR", {"II": output_dir}),
                patch.object(build, "HTML_LIMITS_BYTES", {"II": 1024}),
            ):
                checks, _ = build.check_artifacts()
            self.assertEqual("ok", checks[0]["status"])


if __name__ == "__main__":
    unittest.main()
