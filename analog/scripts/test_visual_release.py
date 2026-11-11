"""Regression coverage for release counts that could otherwise report false green."""
import json
from pathlib import Path
import tempfile
import unittest

import audit_visual_density as density
import check_visual_manifest as manifest
import check_visual_release as release
from review_visuals_agent import score_total


class VisualReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'review.md').write_text('Reviewed all frames and calculations.', encoding='utf-8')
        (self.root / 'motion.svg').write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"><circle cx="0">'
            '<animate attributeName="cx" from="0" to="100" dur="2s"/>'
            '</circle></svg>', encoding='utf-8')
        self.asset = {'id': 'motion', 'kind': 'animation', 'output': 'motion.svg',
                      'status': 'accepted',
                      'review_scores': dict.fromkeys(manifest.SCORE_DIMS + manifest.ANIM_DIMS, 5),
                      'review_record': {'record': 'review.md',
                                        'asset_sha256': release.digest(self.root / 'motion.svg')}}

    def run_inventory(self, *assets):
        return release.inventory({'assets': list(assets)}, self.root)

    def test_bundle_and_duplicate_registration_do_not_multiply_count(self):
        self.asset.update(reduced_motion='static.svg', storyboard='storyboard.svg')
        duplicate = {**self.asset, 'id': 'duplicate'}
        accepted, errors = self.run_inventory(self.asset, duplicate)
        self.assertEqual({'motion.svg'}, accepted['animation'])
        self.assertTrue(any('duplicate main output' in e for e in errors))

    def test_copying_animation_under_another_filename_is_not_independent(self):
        (self.root / 'copy.svg').write_bytes((self.root / 'motion.svg').read_bytes())
        accepted, errors = self.run_inventory(self.asset, {**self.asset, 'id': 'copy', 'output': 'copy.svg'})
        self.assertEqual(1, len(accepted['animation']))
        self.assertTrue(any('duplicate animation bytes' in e for e in errors))

    def test_static_svg_cannot_masquerade_as_animation(self):
        (self.root / 'motion.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding='utf-8')
        self.asset['review_record']['asset_sha256'] = release.digest(self.root / 'motion.svg')
        accepted, errors = self.run_inventory(self.asset)
        self.assertFalse(accepted['animation'])
        self.assertTrue(any('static output' in e for e in errors))

    def test_changing_accepted_bytes_requires_new_review(self):
        path = self.root / 'motion.svg'
        path.write_text(path.read_text().replace('100', '200'))
        accepted, errors = self.run_inventory(self.asset)
        self.assertFalse(accepted['animation'])
        self.assertTrue(any('reviewed bytes differ' in e for e in errors))

    def test_review_total_uses_all_seven_dimensions(self):
        scores = self.asset['review_scores']
        scores[manifest.ANIM_DIMS[-1]] = 4
        self.assertEqual(34, score_total('animation', scores))
        self.assertEqual(25, score_total('figure', scores))
        accepted, errors = self.run_inventory(self.asset)
        self.assertEqual({'motion.svg'}, accepted['animation'])
        self.assertEqual([], errors)

    def test_all_fours_fail_animation_total_even_when_each_dimension_passes(self):
        self.asset['review_scores'] = dict.fromkeys(self.asset['review_scores'], 4)
        accepted, errors = self.run_inventory(self.asset)
        self.assertFalse(accepted['animation'])
        self.assertTrue(any('below 30/35' in e for e in errors))

    def test_review_report_and_pending_status_are_not_optional(self):
        pending = {**self.asset, 'status': 'generated'}
        accepted, _ = self.run_inventory(pending)
        self.assertFalse(accepted['animation'])
        (self.root / 'review.md').unlink()
        accepted, errors = self.run_inventory(self.asset)
        self.assertFalse(accepted['animation'])
        self.assertTrue(any('missing review evidence' in e for e in errors))

    def test_legacy_inventory_uses_frozen_list_and_checks_replacement_acceptance(self):
        baseline = {'inventory': {'svg_animations': {'sha256': {'old.svg': 'original'}}}}
        old = {'id': 'old', 'output': 'assets/svg/old.svg',
               'legacy_disposition': {'action': 'rebuild', 'reason': 'Incorrect circuit',
                                      'record': 'review.md', 'replacement': 'motion.svg'}}
        data = {'assets': [old, self.asset]}
        self.assertEqual([], release.legacy_errors(data, baseline, self.root))
        data['assets'][1]['status'] = 'generated'
        self.assertTrue(any('replacement lacks acceptance' in e
                            for e in release.legacy_errors(data, baseline, self.root)))
        data['assets'] = [self.asset]
        self.assertTrue(any('missing individual' in e
                            for e in release.legacy_errors(data, baseline, self.root)))


class ProseReductionTests(unittest.TestCase):
    """规格要的是「正文字符下降 10%–20%」，不是把图注与 alt 一起算进去的原文总量。"""

    PROSE = '先画回路，再列节点。增益、摆幅、带宽与稳定性分别验。'
    CHROME = ('<figure>\n<img src="assets/figures/x.svg" width="720" '
              'alt="手绘对照图：两条曲线、谷底位置与频段分工带">\n'
              '<figcaption>同一张对数坐标上的两条真实曲线：谷底约 1Ω @ 356kHz。</figcaption>\n'
              '</figure>\n')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_figure_chrome_is_not_prose(self):
        with_chrome = self.PROSE + '\n' + self.CHROME + self.PROSE
        self.assertEqual(density.nonws(self.PROSE) * 2, density.prose_chars(with_chrome))
        self.assertGreater(density.nonws(with_chrome), density.prose_chars(with_chrome))

    def test_standalone_image_tag_is_not_prose(self):
        text = self.PROSE + '\n<img src="assets/svg/y.svg" alt="示意图">\n' + self.PROSE
        self.assertEqual(density.nonws(self.PROSE) * 2, density.prose_chars(text))

    def test_audit_reports_both_conventions(self):
        path = self.root / 'p1-02-ch1.md'
        path.write_text(self.PROSE + '\n' + self.CHROME, encoding='utf-8')
        row = density.audit(path)
        self.assertEqual(density.nonws(self.PROSE), row['prose_chars'])
        self.assertEqual(density.nonws(self.PROSE + '\n' + self.CHROME), row['chars'])

    def test_frozen_baseline_carries_prose_for_every_chapter(self):
        baseline = json.loads(release.BASELINE.read_text(encoding='utf-8'))
        self.assertEqual(19, len(baseline['chapters']))
        for row in baseline['chapters']:
            self.assertIn('prose_chars', row, f"ch{row['chapter']} 缺冻结正文口径")
            self.assertLess(row['prose_chars'], row['chars'])
        self.assertIn('prose_convention', baseline['meta'])

    def reduction(self, base_prose, base_raw, now_prose, now_raw):
        baseline = {'chapters': [{'chapter': 0, 'chars': base_raw, 'prose_chars': base_prose}]}
        rows = [{'chapter': 0, 'chars': now_raw, 'prose_chars': now_prose}]
        return release.reduction_errors(baseline, rows)

    def test_raw_growth_from_new_figures_does_not_fail_the_floor(self):
        errors, measured = self.reduction(1000, 1000, 850, 2000)
        self.assertEqual([], errors)
        self.assertAlmostEqual(.15, measured['prose'])
        self.assertAlmostEqual(-1.0, measured['raw'])

    def test_prose_growth_fails_even_when_raw_shrinks(self):
        errors, measured = self.reduction(1000, 2000, 1100, 900)
        self.assertTrue(any('prose' in e for e in errors), errors)
        self.assertAlmostEqual(-.10, measured['prose'])

    def test_exact_floor_passes(self):
        errors, measured = self.reduction(1000, 1000, 900, 900)
        self.assertEqual([], errors)
        self.assertAlmostEqual(.10, measured['prose'])

    def test_small_prose_cut_fails(self):
        errors, _ = self.reduction(1000, 1000, 950, 950)
        self.assertEqual(1, len(errors))
        self.assertIn('5.0%', errors[0])

    def check_reduction(self, now_prose, now_raw):
        baseline = {'chapters': [{'chapter': 0, 'chars': 1000, 'prose_chars': 1000}],
                    'inventory': {'svg_animations': {'sha256': {}}}}
        rows = [{'chapter': 0, 'visuals': 0, 'budget': 0, 'longest_gap': 0, 'clusters': 0,
                 'h2_no_visual': [], 'assets': [], 'chars': now_raw, 'prose_chars': now_prose}]
        return release.check({'assets': []}, baseline, rows, self.root)

    def test_check_wires_prose_and_still_reports_raw(self):
        result = self.check_reduction(800, 2000)
        self.assertFalse(any('reduction' in e for e in result['errors']), result['errors'])
        self.assertAlmostEqual(.20, result['source_character_reduction'])
        self.assertAlmostEqual(-1.0, result['raw_character_reduction'])
        grown = self.check_reduction(1200, 500)
        self.assertTrue(any('reduction' in e for e in grown['errors']), grown['errors'])


if __name__ == '__main__':
    unittest.main()
