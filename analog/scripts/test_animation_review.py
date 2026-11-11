"""Review pages must not hide stale or missing acceptance evidence."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import build_animation_review as review


class ReviewStatus(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patch = patch.object(review, 'ROOT', self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        (self.root / 'asset.svg').write_bytes(b'<svg/>\r\n')
        (self.root / 'review.md').write_text('Review evidence', encoding='utf-8')
        self.asset = {
            'status': 'accepted', 'output': 'asset.svg',
            'review_record': {
                'asset_sha256': hashlib.sha256(b'<svg/>\n').hexdigest(),
                'record': 'review.md',
            },
        }

    def test_current_evidence_accepts_normalized_newlines(self):
        self.assertEqual('已验收', review.review_status(self.asset))

    def test_changed_bytes_require_review(self):
        (self.root / 'asset.svg').write_bytes(b'<svg><text>changed</text></svg>')
        self.assertIn('须复审', review.review_status(self.asset))

    def test_missing_record_is_visible_even_when_hash_matches(self):
        (self.root / 'review.md').unlink()
        self.assertIn('缺审阅记录', review.review_status(self.asset))

    def test_generated_output_is_not_presented_as_accepted(self):
        self.asset['status'] = 'generated'
        self.assertEqual('已生成，待审阅', review.review_status(self.asset))


if __name__ == '__main__':
    unittest.main()
