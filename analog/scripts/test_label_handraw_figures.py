"""Only an exact accessibility-label insertion may carry a prior visual review."""
import hashlib
import unittest

from scripts.label_handraw_figures import label, preserve_review_for_labels


class LabelReviewPreservation(unittest.TestCase):
    def setUp(self):
        self.raw = '<svg viewBox="0 0 100 100"><text x="5" y="20">5 V</text></svg>'
        self.spec = {'title': '电压', 'alt': '示意五伏'}
        self.asset = {'status': 'accepted', 'review_scores': {'事实精度': 5},
                      'review_record': {'asset_sha256': hashlib.sha256(self.raw.encode()).hexdigest()}}

    def test_exact_insertion_keeps_scores_and_records_provenance(self):
        out = label(self.raw, self.spec)
        self.assertTrue(preserve_review_for_labels(self.asset, self.raw, out, self.spec))
        record = self.asset['review_record']
        self.assertEqual(hashlib.sha256(out.encode()).hexdigest(), record['asset_sha256'])
        self.assertEqual(hashlib.sha256(self.raw.encode()).hexdigest(),
                         record['metadata_amendments'][0]['before_sha256'])
        self.assertEqual({'事实精度': 5}, self.asset['review_scores'])
        self.assertEqual(out, label(out, self.spec))

    def test_drawing_change_cannot_inherit_acceptance(self):
        out = label(self.raw, self.spec).replace('5 V', '50 V')
        self.assertFalse(preserve_review_for_labels(self.asset, self.raw, out, self.spec))
        self.assertNotIn('metadata_amendments', self.asset['review_record'])

    def test_stale_hash_cannot_be_repaired_by_labelling(self):
        self.asset['review_record']['asset_sha256'] = 'stale'
        self.assertFalse(preserve_review_for_labels(self.asset, self.raw, label(self.raw, self.spec), self.spec))
        self.assertEqual('stale', self.asset['review_record']['asset_sha256'])

    def test_generated_asset_is_not_promoted(self):
        self.asset['status'] = 'generated'
        self.assertFalse(preserve_review_for_labels(self.asset, self.raw, label(self.raw, self.spec), self.spec))
        self.assertEqual('generated', self.asset['status'])


if __name__ == '__main__':
    unittest.main()
