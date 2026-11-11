#!/usr/bin/env python3
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_ship_residual as residual  # noqa: E402


class ShipResidualTests(unittest.TestCase):
    def test_full_scan_passes_on_current_tree(self):
        issues = []
        issues += residual.check_contract()
        issues += residual.check_slop()
        issues += residual.check_references()
        issues += residual.check_svg_floor()
        issues += residual.check_no_parallel_tree()
        issues += residual.check_five_line_sample()
        self.assertEqual([], issues, issues)

    def test_parallel_tree_detector_fires(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "book-manuscript").mkdir()
            issues = residual.check_no_parallel_tree(root=root)
            self.assertEqual(["发现疑似平行书稿目录：book-manuscript/（spec §3 废止）"], issues)

    def test_motto_registry_regex_extracts_rows(self):
        import re
        row = "| [第 16 章](p4-01-ch16.md#ch16) | 一次只改一个变量 | 排故像做实验 |"
        m = re.search(r"\|\s*\[第 16 章\]\(p[\d-]+-ch16\.md#ch16\)\s*\|([^|]+)\|", row)
        self.assertIsNotNone(m)
        self.assertIn("一次只改一个变量", m.group(1))

    def test_ep_needles_catch_drift(self):
        # 抽检对数值漂移敏感：缺正典数值的分镜探针应报不一致
        with tempfile.TemporaryDirectory() as d:
            shots = Path(d)
            names = ["ep04-divider.json", "ep05-probe.json", "ep02-virtual-short.json",
                     "ep07-pullup.json", "ep09-electrolytic.json", "ep13-buck.json"]
            for name in names:
                (shots / name).write_text("{}", encoding="utf-8")
            issues = residual.check_five_line_sample(ep_dir=shots)
            drift = [i for i in issues if i.startswith("ep04-divider.json")]
            self.assertTrue(drift, issues)


if __name__ == "__main__":
    unittest.main()
