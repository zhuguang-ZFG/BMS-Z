"""Numerical regression for the real noise-budget SVG generator.

Run: python -B scripts/test_noise_budget.py -v
Only this figure is generated, into a temporary directory; no assets are changed.
Expectations come from independent one-sided PSD arithmetic, not generator helpers.
"""
import math
from pathlib import Path
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET

import generate_svgs as generator


ROOT = Path(__file__).resolve().parents[1]
NS = {"s": "http://www.w3.org/2000/svg"}
# 曲线识别色取自手绘皮肤 token：换调色板时测试自动跟随，
# 但「两条曲线颜色必须不同、各带一个拐点标记」的断言强度不变。
CURVES = {generator.handraw.LIGHT["green"]: 100.0,
          generator.handraw.LIGHT["red"]: 1000.0}


class NoiseBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix="analog-noise-budget-")
        cls.addClassCleanup(temporary.cleanup)
        cls.output = Path(temporary.name)
        previous_out = generator.OUT
        try:
            generator.OUT = str(cls.output)
            generator.make_noise_budget()
        finally:
            generator.OUT = previous_out
        cls.generated = cls.output / "noise-budget.svg"
        cls.svg = ET.parse(cls.generated).getroot()
        cls.paths = {
            color: cls.svg.find(f'.//s:path[@stroke="{color}"][@stroke-width="2.4"]', NS)
            for color in CURVES
        }
        # Calibrate using the displayed ticks. This deliberately supports the old
        # negative dB axis too, so a failure diagnoses the spectrum, not a redesign.
        texts = cls.svg.findall(".//s:text", NS)
        frequency_ticks = {
            (t.text or "").strip(): float(t.get("x")) for t in texts
            if (t.text or "").strip() in ("100Hz", "1MHz")
        }
        cls.x100 = frequency_ticks["100Hz"]
        cls.pixels_per_decade = (frequency_ticks["1MHz"] - cls.x100) / 4
        db_ticks = {}
        for text in texts:
            value = (text.text or "").strip().replace("−", "-")
            if (text.get("text-anchor") == "end"
                    and float(text.get("x", "0")) < cls.x100
                    and re.fullmatch(r"[+-]?\d+(?:dB)?", value)):
                db_ticks[float(value.removesuffix("dB"))] = float(text.get("y")) - 4
        cls.y_zero = db_ticks[0.0]
        other_db = next(db for db in db_ticks if db != 0)
        cls.pixels_per_db = (db_ticks[other_db] - cls.y_zero) / other_db

    def points(self, color):
        path = self.paths[color]
        self.assertIsNotNone(path, "The generated spectrum must be a visible path")
        numbers = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", path.get("d"))]
        self.assertEqual(len(numbers) % 2, 0)
        points = list(zip(numbers[::2], numbers[1::2]))
        self.assertGreater(len(points), 100, "A label or straight guide is not a spectrum")
        return points

    def db_at(self, color, frequency):
        x = self.x100 + math.log10(frequency / 100) * self.pixels_per_decade
        points = self.points(color)
        self.assertGreaterEqual(x, points[0][0] - 0.01)
        self.assertLessEqual(x, points[-1][0] + 0.01)
        for (xa, ya), (xb, yb) in zip(points, points[1:]):
            if xa - 0.01 <= x <= xb + 0.01:
                y = ya + (yb - ya) * (x - xa) / (xb - xa)
                return (y - self.y_zero) / self.pixels_per_db
        self.fail(f"No path segment at {frequency} Hz")

    def flicker_psd(self, color, frequency):
        # Undo total ASD dB, then subtract the common unit white PSD floor.
        return 10 ** (self.db_at(color, frequency) / 10) - 1

    def test_flicker_psd_drops_tenfold_per_decade(self):
        # Catches the original accidental (fc/f)^2 power spectrum.
        for color in CURVES:
            with self.subTest(color=color):
                ratio = self.flicker_psd(color, 100) / self.flicker_psd(color, 10)
                self.assertAlmostEqual(ratio, 0.1, delta=0.003)

    def test_flicker_asd_drops_by_sqrt_ten_per_decade(self):
        for color in CURVES:
            with self.subTest(color=color):
                ratio = math.sqrt(self.flicker_psd(color, 100) / self.flicker_psd(color, 10))
                self.assertAlmostEqual(ratio, 0.31622776601683794, delta=0.006)

    def test_flicker_asd_slope_is_minus_ten_db_per_decade(self):
        for color in CURVES:
            with self.subTest(color=color):
                asd_ratio = math.sqrt(self.flicker_psd(color, 100) / self.flicker_psd(color, 10))
                self.assertAlmostEqual(20 * math.log10(asd_ratio), -10.0, delta=0.12)

    def test_every_spectrum_vertex_matches_sum_of_white_and_flicker_power(self):
        for color, corner in CURVES.items():
            points = self.points(color)
            self.assertTrue(all(b[0] > a[0] for a, b in zip(points, points[1:])))
            for x, y in points:
                with self.subTest(color=color, x=x):
                    frequency = 100 * 10 ** ((x - self.x100) / self.pixels_per_decade)
                    actual_db = (y - self.y_zero) / self.pixels_per_db
                    # Separate components: white PSD=1; flicker PSD=fc/f.
                    expected_asd = math.sqrt(1 + corner / frequency)
                    self.assertAlmostEqual(actual_db, 20 * math.log10(expected_asd), delta=0.015)

    def test_corner_and_white_floor_have_physical_levels(self):
        # At fc two equal powers sum to 2, not two equal amplitudes to 2.
        for color, corner in CURVES.items():
            with self.subTest(color=color):
                self.assertAlmostEqual(self.db_at(color, corner), 3.01029995664, delta=0.015)
                self.assertAlmostEqual(self.db_at(color, 1e6), 0.0, delta=0.01)
                markers = self.svg.findall(f'.//s:circle[@stroke="{color}"][@cx]', NS)
                self.assertEqual(len(markers), 1)
                marker_db = (float(markers[0].get("cy")) - self.y_zero) / self.pixels_per_db
                self.assertAlmostEqual(marker_db, 3.01029995664, delta=0.015)

    def test_each_animated_marker_uses_its_visible_spectrum_path(self):
        # Catches the old red marker travelling on an unrelated straight line.
        for color in CURVES:
            with self.subTest(color=color):
                motions = self.svg.findall(f'.//s:circle[@fill="{color}"]/s:animateMotion', NS)
                self.assertEqual(len(motions), 1)
                self.assertEqual(motions[0].get("path"), self.paths[color].get("d"))

    def test_only_requested_asset_is_generated_and_published(self):
        self.assertEqual([p.name for p in self.output.iterdir()], ["noise-budget.svg"])
        published = ROOT / "assets" / "svg" / "noise-budget.svg"
        self.assertEqual(self.generated.read_text(encoding="utf-8"),
                         published.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
