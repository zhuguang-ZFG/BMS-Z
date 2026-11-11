"""纸层插图的数学语义、重建一致性与打印完整性。"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.visuals.scenes.ch17_papercut_figures import FIGURES, i2c
from scripts.visuals.papercut import svg
from compose_technical_overlay import compose
import build_papercut_pilot as builder


class PapercutFigureTests(unittest.TestCase):
    def test_i2c_curve_uses_capacitance_and_resistance_scales(self):
        _, labels = i2c()
        tree = ET.fromstring(svg(labels))
        curve = next(e for e in tree if e.tag.endswith('polyline'))
        points = [tuple(map(float, p.split(','))) for p in curve.get('points').split()]
        for x, y in points:
            capacitance_pf = (x - 200) / 690 * 400
            resistance_kohm = (770 - y) / 350 * 12
            expected = 1e6 / (.8473 * capacitance_pf) / 1000
            self.assertAlmostEqual(expected, resistance_kohm, delta=.001)
        self.assertGreater(points[-1][0], points[0][0])
        self.assertGreater(points[-1][1], points[0][1])

    def test_three_figures_rebuild_exactly_and_keep_print_shapes(self):
        for asset_id in FIGURES:
            with self.subTest(asset=asset_id), tempfile.TemporaryDirectory() as tmp:
                spec_path = ROOT / builder.REVIEW / f'{asset_id}.json'
                spec = json.loads(spec_path.read_text(encoding='utf-8'))
                scratch = Path(tmp)
                for key in ('base_svg', 'overlay'):
                    target = scratch / Path(spec[key]).name
                    target.write_bytes((ROOT / spec[key]).read_bytes())
                    spec[key] = target.name
                spec['output'] = f'{asset_id}.svg'
                outputs = compose(spec, scratch)
                for path in outputs.values():
                    expected = ROOT / 'assets/figures-v2' / path.name
                    self.assertEqual(expected.read_text(encoding='utf-8'), path.read_text(encoding='utf-8'))
                printed = outputs['print'].read_text(encoding='utf-8')
                self.assertIn('id="paper-illustration"', printed)
                self.assertNotIn('data-paper-shadow', printed)
                self.assertNotIn('<image', printed)

    def test_changed_image_cannot_keep_old_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'docs/superpowers/visual/prompts').mkdir(parents=True)
            (root / 'assets/figures-v2').mkdir(parents=True)
            output = 'assets/figures-v2/demo.svg'
            (root / output).write_text('<svg/>', encoding='utf-8')
            spec = {'id': 'demo', 'title': '示例', 'alt': '说明', 'output': output}
            old = {'id': 'demo', 'status': 'accepted', 'review_scores': {'教学必要性': 5},
                   'status_history': ['planned', 'generated', 'reviewed', 'accepted'],
                   'review_record': {'asset_sha256': 'stale'}}
            data = {'assets': [old]}
            with patch.object(builder, 'ROOT', root):
                builder.register(spec, '17.0', 'IG-014', 'V4', data)
            self.assertEqual('generated', data['assets'][0]['status'])
            self.assertEqual({}, data['assets'][0]['review_scores'])

    def test_accepted_artifacts_match_the_reviewed_hash(self):
        from check_visual_manifest import load
        for asset in load()['assets']:
            if asset.get('generator') != 'python-svg-papercut-v1' or asset.get('status') not in ('accepted', 'published'):
                continue
            raw = (ROOT / asset['output']).read_bytes().replace(b"\r\n", b"\n")
            digest = hashlib.sha256(raw).hexdigest()
            self.assertEqual(digest, asset['review_record']['asset_sha256'], asset['id'])


if __name__ == '__main__':
    unittest.main()
