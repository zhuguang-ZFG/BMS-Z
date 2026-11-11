#!/usr/bin/env python3
"""扩量下限闸：assets/svg 数量不得低于 150（Task 11b 出口闸）。"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SvgCountFloor(unittest.TestCase):
    def test_at_least_150_svgs(self):
        n = len(list((ROOT / "assets" / "svg").glob("*.svg")))
        # 扩量完成后 ≥150；迁移中期可临时 118，但本任务结束必须过线
        self.assertGreaterEqual(n, 150, f"only {n} svgs; expansion gate is >=150")


if __name__ == "__main__":
    unittest.main()
