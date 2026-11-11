"""印刷分镜（book.storyboard）的永久回归。

v3.88 之前，印刷版动画只能「保字幕 + 同坐标留末拍」：106 张动画在纸面上
丢掉 293 条接力拍说明，其中 188 条是幸存文本里没有的独有信息（rc-charge
的「第 1 拍……」、error-budget 的「① WC……② RSS……」都在列）。
分镜把这些拍逐字补回印刷版——所以这组测试的硬约束是：**每条接力字幕
必须逐字出现在分镜产物里**，而且帧内不再残留动画节点。
"""
from __future__ import annotations

import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent))

from book.svg_refine import is_legacy_svg, refine_svg
from book.storyboard import bake, build_storyboard, caption_beats

ASSETS = ROOT.parent / "assets" / "svg"
TAG_RE = re.compile(r"<[^>]+>")


def _legacy_files() -> list[pathlib.Path]:
    return sorted(p for p in ASSETS.glob("*.svg")
                  if is_legacy_svg(p.read_text(encoding="utf-8")))


class StoryboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = _legacy_files()
        if not cls.files:
            raise unittest.SkipTest("assets/svg 里没有旧模板动画")

    def test_every_legacy_animation_builds_a_storyboard(self):
        failures = []
        for path in self.files:
            text = path.read_text(encoding="utf-8")
            try:
                build_storyboard(text, refine_svg(text))
            except Exception as exc:  # pragma: no cover - 汇总报错
                failures.append(f"{path.name}: {exc!r}")
        self.assertEqual([], failures)

    def test_every_relay_caption_survives_verbatim(self):
        """被折叠的接力拍，逐拍逐字回到分镜里（换行断行不算丢失）。"""
        missing = []
        for path in self.files:
            text = path.read_text(encoding="utf-8")
            beats = [b["label"] for b in caption_beats(text) if b["label"]]
            if len(beats) < 2:
                continue
            storyboard = build_storyboard(text, refine_svg(text))
            import html as _html
            plain = _html.unescape(TAG_RE.sub("", storyboard))
            for label in beats:
                if label not in plain:
                    missing.append(f"{path.name}: {label[:30]}")
        self.assertEqual([], missing)

    def test_frames_carry_no_animation_residue(self):
        """分镜是静态产物：任何动画节点残留都会在阅读器里乱动。"""
        leftover = []
        for path in self.files:
            text = path.read_text(encoding="utf-8")
            storyboard = build_storyboard(text, refine_svg(text))
            for tag in ("<animate", "<animateTransform", "<animateMotion", "<set "):
                if tag in storyboard:
                    leftover.append(f"{path.name}: {tag}")
        self.assertEqual([], leftover)

    def test_storyboard_is_well_formed_svg_with_paper_background(self):
        import xml.etree.ElementTree as ET
        for path in self.files[:8] + self.files[-4:]:
            text = path.read_text(encoding="utf-8")
            storyboard = build_storyboard(text, refine_svg(text))
            root = ET.fromstring(storyboard)
            self.assertTrue(root.tag.endswith("svg"))
            self.assertIn('fill="#fffdf8"', storyboard)
            self.assertIn("sbTitle", storyboard)
            self.assertIn("sbDesc", storyboard)

    def test_bake_freezes_transform_and_opacity_at_fraction(self):
        """烘焙必须落到指定节拍：单发字幕在该拍可见、后续拍字幕不可见。"""
        sample = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            '<text x="10" y="20">甲'
            '<animate attributeName="opacity" values="0;1;1;0;0" '
            'keyTimes="0;0.1;0.4;0.5;1" dur="5s" repeatCount="indefinite"/>'
            '</text>'
            '<text x="10" y="40">乙'
            '<animate attributeName="opacity" values="0;0;1;1" '
            'keyTimes="0;0.5;0.6;1" dur="5s" repeatCount="indefinite"/>'
            '</text></svg>')
        early = bake(sample, 0.25)
        late = bake(sample, 0.8)
        self.assertIn('opacity="1">甲', early)
        self.assertIn('opacity="1">乙', late)
        self.assertNotIn("<animate", early)

    def test_caption_beats_orders_by_window_start(self):
        text = (ASSETS / "rc-charge.svg").read_text(encoding="utf-8")
        beats = caption_beats(text)
        starts = [b["window"][0] for b in beats]
        self.assertEqual(starts, sorted(starts))
        self.assertTrue(all(0 <= b["fraction"] <= 1 for b in beats))
        self.assertTrue(any("第 1 拍" in b["label"] for b in beats))


if __name__ == "__main__":
    unittest.main()
