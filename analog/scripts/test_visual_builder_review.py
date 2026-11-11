#!/usr/bin/env python3
"""登记器重跑时的审图数据保全：底图字节未变才允许带过人工评分。

背景：`build_handdrawn_wave2.py` / `build_backlog_wave3.py` 的 `register()` 会整条
替换 manifest 条目。曾因无条件替换，任何人重跑一次 builder 就把已签核的
`status`/`review_scores`/`review_record` 清回 `generated`——图没变，评分却没了。
这里锁住两条相反的边：字节一致必须保图保分，字节变了必须降级重审。
"""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_backlog_wave3 as backlog_builder  # noqa: E402
import build_handdrawn_wave2 as handdrawn_builder  # noqa: E402

from scripts.visuals import font_gate as gate  # noqa: E402

SVG = '<svg xmlns="http://www.w3.org/2000/svg"><text>示意</text></svg>\n'
META = {
    'draw': lambda: ['<text>示意</text>'],
    'title': '示例图', 'anchor': '18.3', 'chapter': 18,
    'layout': 'IG-013', 'type': 'V4',
    'source': 'docs/p4-03-ch18.md', 'alt': '示例替代文本',
}


def reviewed_entry(asset_id: str, digest: str) -> dict:
    return {
        'id': asset_id, 'chapter': 18, 'kind': 'figure', 'type': 'V4',
        'anchor': '18.3', 'purpose': '示例图', 'style_id': 'FA-029',
        'layout_id': 'IG-013', 'color_ids': ['C-30'],
        'source_facts': ['docs/p4-03-ch18.md#18.3'],
        'prompt_file': f'docs/superpowers/visual/prompts/{asset_id}.md',
        'output': f'assets/figures-v2/{asset_id}.svg',
        'print_fallback': f'assets/figures-v2/{asset_id}-print.svg',
        'alt': '旧替代文本', 'status': 'accepted',
        'status_history': ['planned', 'generated', 'reviewed', 'accepted'],
        'review_scores': {'教学必要性': 5, '事实精度': 5,
                          '构图层级': 5, '风格一致性': 5, '印刷可读性': 5},
        'review_record': {'asset_sha256': digest, 'reviewer': 'zhuguang-ZFG'},
    }


class BuilderReviewCarryOver(unittest.TestCase):
    def sandbox(self, asset_id: str, on_disk: str):
        tmp = Path(tempfile.mkdtemp())
        assets = tmp / 'assets' / 'figures-v2'
        prompts = tmp / 'prompts'
        assets.mkdir(parents=True)
        prompts.mkdir(parents=True)
        (assets / f'{asset_id}.svg').write_bytes(on_disk.encode('utf-8'))
        return assets, prompts

    def register(self, builder, asset_id: str, on_disk: str, digest: str) -> dict:
        assets, prompts = self.sandbox(asset_id, on_disk)
        old_assets, old_prompts = builder.ASSETS, builder.PROMPTS
        builder.ASSETS, builder.PROMPTS = assets, prompts
        try:
            data = {'assets': [reviewed_entry(asset_id, digest)]}
            builder.register(asset_id, META, data)
        finally:
            builder.ASSETS, builder.PROMPTS = old_assets, old_prompts
        return data['assets'][0]

    def digest(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8').replace(b'\r\n', b'\n')).hexdigest()

    def test_unchanged_bytes_keep_the_review(self):
        for builder in (handdrawn_builder, backlog_builder):
            with self.subTest(builder=builder.__name__):
                asset = self.register(builder, 'ch18-demo', SVG, self.digest(SVG))
                self.assertEqual('accepted', asset['status'])
                self.assertEqual(5, asset['review_scores']['事实精度'])
                self.assertEqual('zhuguang-ZFG', asset['review_record']['reviewer'])
                self.assertEqual('示例替代文本', asset['alt'])

    def test_changed_bytes_drop_the_review(self):
        for builder in (handdrawn_builder, backlog_builder):
            with self.subTest(builder=builder.__name__):
                changed = SVG.replace('示意', '改图')
                asset = self.register(builder, 'ch18-demo', changed, self.digest(SVG))
                self.assertEqual('generated', asset['status'])
                self.assertEqual({}, asset['review_scores'])
                self.assertNotIn('review_record', asset)


class Chapter13BuilderRouting(unittest.TestCase):
    def test_legacy_entry_points_use_current_renderer_and_metadata(self):
        """Old wave commands must not revive the incorrect papercut diagrams."""
        from scripts.visuals.scenes.ch13_reference_figures import SCENES
        for asset_id in ('ch13-h-bridge-states', 'ch13-current-sense-sides',
                         'ch13-opto-ctr'):
            with self.subTest(asset=asset_id):
                meta = backlog_builder.CH13[asset_id]
                self.assertIs(meta['draw'], SCENES[asset_id]['draw'])
                self.assertEqual(meta['anchor'], SCENES[asset_id]['anchor'])
                data = {'assets': []}
                with patch.object(handdrawn_builder, 'build_one') as build, \
                     patch.object(handdrawn_builder, 'register') as register:
                    backlog_builder.build_one(asset_id, meta)
                    backlog_builder.register(asset_id, meta, data)
                    build.assert_called_once_with(asset_id, meta)
                    register.assert_called_once_with(asset_id, meta, data)


class FontCoverageGate(unittest.TestCase):
    """`绽` 的教训：图内用字必须在书籍字体子集里，否则 print16k 才红。"""

    def test_missing_glyph_is_reported_with_font_name(self):
        report = gate.missing_in_assets('<svg><text>破绽</text></svg>')
        self.assertTrue(report)
        self.assertIn('绽', ''.join(report.values()))
        self.assertTrue(all(name.endswith('.woff2') for name in report))

    def test_covered_text_passes(self):
        self.assertEqual({}, gate.missing_in_assets('<svg><text>探头补偿</text></svg>'))

    def test_title_and_desc_are_checked_too(self):
        self.assertIn('绽', ''.join(gate.missing_in_assets(
            '<svg><title>破绽</title><desc>说明</desc></svg>').values()))

    def test_gate_fails_the_build_script(self):
        with self.assertRaises(SystemExit) as caught:
            gate.assert_covered('<svg><text>破绽</text></svg>', 'ch18-demo')
        self.assertIn('绽', str(caught.exception))

    def test_every_committed_figure_stays_covered(self):
        """已有 45+ 张新图的现存文字也一并锁住，防止回归。"""
        checked = 0
        for path in sorted((ROOT / 'assets' / 'figures-v2').glob('*.svg')):
            report = gate.missing_in_assets(path.read_text(encoding='utf-8'))
            self.assertEqual({}, report, f'{path.name}: {report}')
            checked += 1
        self.assertGreater(checked, 40)


if __name__ == '__main__':
    unittest.main()
