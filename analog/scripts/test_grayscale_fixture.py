# -*- coding: utf-8 -*-
"""16K 灰度对照夹具的闸值测试。

锁住 2026-11-05 拍板的色族角色：石板灰只能做阴影，不得做纸底。
上游 handraw-style 未安装时跳过（色值必须从上游色卡解析，测试不内置 hex）。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import make_grayscale_fixture as g  # noqa: E402

try:
    ROOT = g.upstream_root()
    UNAVAILABLE = None
except SystemExit as exc:  # 上游未安装
    ROOT, UNAVAILABLE = None, str(exc)


@unittest.skipIf(UNAVAILABLE, f"handraw-style 安装根不可用：{UNAVAILABLE}")
class GrayscaleFixtureTest(unittest.TestCase):
    def test_approved_palette_passes_print_thresholds(self):
        res = g.build(self.out)
        data = res["approved"]
        self.assertGreaterEqual(data["paper_vs_ink"], g.MIN_PAPER_INK_RATIO)
        self.assertGreaterEqual(data["paper_vs_accent"], g.MIN_PAPER_ACCENT_RATIO)

    def test_slate_as_paper_is_rejected_by_the_same_gate(self):
        data = g.build(self.out)["rejected_slate_as_paper"]
        self.assertLess(data["paper_vs_ink"], g.MIN_PAPER_INK_RATIO)
        self.assertLess(data["paper_vs_accent"], g.MIN_PAPER_ACCENT_RATIO)

    def test_accent_must_not_sit_on_slate_shade(self):
        data = g.build(self.out)["approved"]
        self.assertLess(data["shade_vs_accent"], 1.5,
                        "石板灰与柿子橙在灰度下几乎同明度，重点色压在阴影层上等于隐形")

    def test_fixture_files_written(self):
        g.build(self.out)
        for name in ("fixture-approved-color.png", "fixture-approved-print16k.png",
                     "grayscale-fixture-sheet.png"):
            self.assertTrue(os.path.exists(os.path.join(self.out, name)), name)

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.out = self._tmp.name
        self.addCleanup(self._tmp.cleanup)


if __name__ == "__main__":
    unittest.main()
