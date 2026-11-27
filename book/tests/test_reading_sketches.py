"""Guard the editable drawing sources and their actual manuscript placement."""

import base64
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "book"))
sys.path.insert(0, str(ROOT / "bms-book/code"))
from generate_reading_sketches import FONT_PATH, render  # noqa: E402


class ReadingSketchTests(unittest.TestCase):
    def test_cccv_sketch_replays_both_normalized_ledgers(self):
        from cccv_charge import simulate_cccv

        entries = json.loads((ROOT / 'book/reading-sketches.json').read_text(
            encoding='utf-8'))['entries']
        entry = next((e for e in entries if e['drawing'] == 'cccv'), None)
        self.assertIsNotNone(entry, 'the CC-CV reading sketch is missing')
        result = simulate_cccv()
        total_time = result['t_cut_s']
        cv_time = result['t_cut_s'] - result['t_sw_s']
        total_charge = result['ah_cc'] + result['ah_cv']
        labels = [
            ''.join(node.itertext())
            for node in ET.fromstring(render(entry)).iter('{http://www.w3.org/2000/svg}text')
        ]

        self.assertEqual(labels.count(entry['title']), 1)
        self.assertIn(f"CC {result['t_sw_s'] / 60:.0f} min", labels)
        self.assertIn(f"CV {cv_time / 60:.0f} min", labels)
        self.assertIn(f"占总时间 {100 * cv_time / total_time:.0f}%", labels)
        self.assertIn(f"CC {result['ah_cc']:.2f} Ah", labels)
        self.assertIn(f"CV {result['ah_cv']:.2f} Ah", labels)
        self.assertIn(f"占总充入 {100 * result['ah_cv'] / total_charge:.0f}%", labels)

    def test_embedded_font_covers_every_label_and_keeps_its_license(self):
        from fontTools.ttLib import TTFont

        raw = FONT_PATH.read_bytes()
        metadata = json.loads(FONT_PATH.with_suffix('.json').read_text(encoding='utf-8'))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), metadata['sha256'])
        for license_key in ['license', 'symbol_donor_license']:
            self.assertIn('SIL OPEN FONT LICENSE',
                          (FONT_PATH.parent / metadata[license_key]).read_text(encoding='utf-8'))
        entries = json.loads((ROOT / 'book/reading-sketches.json').read_text(encoding='utf-8'))['entries']
        for entry in entries:
            with self.subTest(drawing=entry['drawing']):
                svg = ET.fromstring(render(entry))
                style = svg.find('{http://www.w3.org/2000/svg}style').text
                encoded = re.search(r'base64,([A-Za-z0-9+/=]+)', style).group(1)
                font = TTFont(io.BytesIO(base64.b64decode(encoded)))
                codepoints = set(font.getBestCmap())
                for label in svg.iter('{http://www.w3.org/2000/svg}text'):
                    self.assertFalse(set(map(ord, ''.join(label.itertext()))) - codepoints)

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
