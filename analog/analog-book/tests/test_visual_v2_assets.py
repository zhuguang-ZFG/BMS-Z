"""V2 书内来源跟随 manifest；网页底图不能误充矢量印刷图。"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from book import config
from book.content import _asset_path, clean_fragment
from book.manifest import BookError
import build_book


class VisualV2BookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        folder = self.root / "assets/figures-v2"
        folder.mkdir(parents=True)
        (folder / "chart.svg").write_text("<svg/>", encoding="utf-8")
        (folder / "chart-print.svg").write_text("<svg/>", encoding="utf-8")
        self.manifest = self.root / "docs/superpowers/visual/visual-manifest.yml"
        self.manifest.parent.mkdir(parents=True)
        self.asset = {"kind": "figure", "status": "accepted", "output": "assets/figures-v2/chart.svg",
                      "print_fallback": "assets/figures-v2/chart-print.svg"}
        patcher = patch.object(config, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def save(self):
        self.manifest.write_text(yaml.safe_dump({"assets": [self.asset]}), encoding="utf-8")

    def test_accepted_figure_uses_vector_print_fallback(self):
        self.save()
        self.assertEqual(self.root / self.asset["print_fallback"],
                         _asset_path(self.asset["output"], self.root))

    def test_unreviewed_figure_cannot_enter_book(self):
        self.asset["status"] = "generated"
        self.save()
        with self.assertRaises(BookError):
            _asset_path(self.asset["output"], self.root)

    def test_missing_fallback_does_not_silently_use_base(self):
        self.save()
        (self.root / self.asset["print_fallback"]).unlink()
        with self.assertRaises(BookError):
            _asset_path(self.asset["output"], self.root)

    def test_animation_uses_storyboard_instead_of_conclusion(self):
        self.asset.update(kind="animation", output="assets/svg-v2/flow.svg",
                          storyboard="assets/figures-v2/chart-print.svg")
        self.save()
        self.assertEqual(self.root / self.asset["storyboard"],
                         _asset_path(self.asset["output"], self.root))

    def test_unregistered_v2_file_cannot_enter_book(self):
        self.save()
        orphan = self.root / "assets/figures-v2/orphan.svg"
        orphan.write_text("<svg/>", encoding="utf-8")
        with self.assertRaises(BookError):
            _asset_path("assets/figures-v2/orphan.svg", self.root)

    def test_web_player_becomes_storyboard_reference_without_controls(self):
        markup = ('<figure><div class="visual-player" data-visual-player="flow" '
                  'data-animation-src="assets/svg-v2/flow.svg" data-timeline="{}">'
                  '<div class="visual-player-viewport"><img src="assets/svg-v2/flow-static.svg" alt="说明"></div>'
                  '<div class="visual-player-controls"></div><p class="visual-player-status">结论静帧</p>'
                  '<p class="visual-player-links"><a href="gallery.html">动画中心</a></p></div>'
                  '<figcaption>原图注</figcaption></figure>')
        output = clean_fragment(markup)
        self.assertIn('src="assets/svg-v2/flow.svg"', output)
        self.assertNotIn('visual-player', output)
        self.assertIn('<figcaption>原图注</figcaption>', output)
        self.assertEqual(output, build_book._clean_fragment(markup))


if __name__ == "__main__":
    unittest.main()
