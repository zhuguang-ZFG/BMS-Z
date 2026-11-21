"""Guard the editable drawing sources and their actual manuscript placement."""

import json
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "book"))
from generate_reading_sketches import render  # noqa: E402


class ReadingSketchTests(unittest.TestCase):
    def test_all_drawings_are_current_static_and_in_the_manuscript(self):
        entries = json.loads(
            (ROOT / "book/reading-sketches.json").read_text(encoding="utf-8")
        )["entries"]
        self.assertEqual(len({e["asset"] for e in entries}), len(entries))
        self.assertEqual(len({e["chapter"] for e in entries}), len(entries))
        for entry in entries:
            with self.subTest(asset=entry["asset"]):
                source = (ROOT / entry["asset"]).read_text(encoding="utf-8")
                self.assertEqual(source, render(entry))
                svg = ET.fromstring(source)
                self.assertEqual(svg.attrib["viewBox"], "0 0 960 720")
                self.assertFalse(
                    re.search(
                        r"<(?:script|animate|image|foreignObject)\b|\bon\w+=|\bhref=",
                        source,
                    )
                )
                manuscript = (ROOT / entry["chapter"]).read_text(encoding="utf-8")
                matches = re.findall(
                    r'<figure class="reading-sketch">(.*?)</figure>', manuscript, re.S
                )
                self.assertEqual(len(matches), 1)
                self.assertIn(Path(entry["asset"]).name, matches[0])
                self.assertIn(entry["question"], matches[0])
                self.assertIn("原理示意 / 非实拍", matches[0])
                self.assertIn(entry["alt"], matches[0])
                source_ref = re.search(r'src="([^"]+)"', matches[0]).group(1)
                # Volume I resolves assets from analog/, while Volume II uses
                # manuscript-relative paths. This is also the website contract.
                base = (
                    ROOT / "analog"
                    if entry["volume"].startswith("卷 I ·")
                    else (ROOT / entry["chapter"]).parent
                )
                self.assertEqual(
                    (base / source_ref).resolve(), (ROOT / entry["asset"]).resolve()
                )

    def test_body_art_cannot_use_an_old_collection_baseline(self):
        from refresh_collection import validate_changes

        for path in [
            "book/reading-sketches.json",
            "book/generate_reading_sketches.py",
            "bms-book/assets/reading-sketches/heat.svg",
        ]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                validate_changes([path])
