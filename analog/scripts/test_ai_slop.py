#!/usr/bin/env python3
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_ai_slop  # noqa: E402


class AiSlopTests(unittest.TestCase):
    def test_flags_fake_contrast(self):
        hits = check_ai_slop.scan_text("这不是电阻，而是电感。", whitelist=[])
        self.assertTrue(hits)

    def test_allows_whitelisted_engineering_contrast(self):
        wl = ["开环 ≠ 闭环"]
        hits = check_ai_slop.scan_text("记住：开环 ≠ 闭环。", whitelist=wl)
        self.assertEqual(hits, [])

    def test_flags_empty_outro(self):
        hits = check_ai_slop.scan_text("总而言之，值得注意的是我们在本章中我们将继续前进。", whitelist=[])
        self.assertTrue(hits)


if __name__ == "__main__":
    unittest.main()
