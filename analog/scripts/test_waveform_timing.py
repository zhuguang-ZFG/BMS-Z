"""Browser regression for the time-domain teaching diagrams.

Run: python -m unittest discover -s scripts -p test_waveform_timing.py -v
Requires Playwright and installed Google Chrome (channel="chrome").
These tests inspect rendered SMIL positions, not animation markup.
"""
import math
from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright

import handraw

ASSETS = Path(__file__).resolve().parents[1] / "assets" / "svg"
# 波形识别色取自手绘皮肤 token：换调色板时这里自动跟随，
# 但「两条曲线颜色必须不同、各自跟随电流/控制量」的断言一字未改。
SIGNAL = handraw.LIGHT["blue"]
DURATION = 12
CASES = {
    "analog-switch-beats": (20, [8], handraw.LIGHT["purple"]),
    "ldo-transient-beats": (50, [5, 10, 30], handraw.LIGHT["amber"]),
    "555-astable-beats": (1012, [541], handraw.LIGHT["red"]),
}

FOUR_BEATS = {
    "mosfet-four-beats": (10, 90, 760, 4),
    "rectifier-filter-beats": (12, 80, 760, 3),
}
LINEAR_X = {
    "comparator-opamp": 2,
    "wien-bridge": 1,
    "integrator": 2,
    "ldo-feedback": 3,
    "miller-plateau": 3,
    "peak-detector": 1,
    "neg-feedback": 2,
}


def expected_y(name, time):
    if name == "analog-switch-beats":
        return (366 if time < 8 else 386 + (time - 8) / 2,
                430 if time < 8 else 452)
    if name == "ldo-transient-beats":
        if time < 5:
            voltage = 5
        elif time < 10:
            voltage = 4.975 - 0.245 * (time - 5) / 5
        elif time < 30:
            voltage = 4.730 + 0.260 * (time - 10) / 20
        else:
            voltage = 4.990
        return 348 + (5.01 - voltage) / 0.31 * 80, 462 if time < 5 else 436
    voltage = (9 - 6 * math.exp(-time / 780) if time < 541
               else 6 * math.exp(-(time - 541) / 680))
    return 420 - voltage / 9 * 62, 435 if time < 541 else 455


class WaveformTimingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        try:
            cls.browser = cls.playwright.chromium.launch(channel="chrome", headless=True)
        except Exception:
            cls.playwright.stop()
            raise
        cls.addClassCleanup(cls.playwright.stop)
        cls.addClassCleanup(cls.browser.close)
        cls.page = cls.browser.new_page(viewport={"width": 800, "height": 680})

    def snapshot(self, name, times):
        self.page.goto((ASSETS / (name + ".svg")).as_uri())
        self.page.locator("svg").wait_for()
        return self.page.evaluate("""times => {
            const svg = document.documentElement;
            svg.pauseAnimations();
            return times.map(time => {
                svg.setCurrentTime(time);
                const points = Array.from(svg.querySelectorAll('circle[r="4.2"]'), c => {
                    const b = c.getBBox(), m = c.getCTM();
                    return {
                        color: c.getAttribute('fill'),
                        x: m.a * (b.x + b.width / 2) + m.c * (b.y + b.height / 2) + m.e,
                        y: m.b * (b.x + b.width / 2) + m.d * (b.y + b.height / 2) + m.f
                    };
                }).filter(p => p.y >= 335 && p.y <= 478);
                const phases = Array.from(svg.querySelectorAll('.waveform-phase'),
                    e => Number(getComputedStyle(e).opacity));
                return {time, points, phases};
            });
        }""", times)

    def check_positions(self, name, times):
        span, transitions, control_color = CASES[name]
        for frame in self.snapshot(name, times):
            time = (frame["time"] % DURATION) / DURATION * span
            with self.subTest(diagram=name, seconds=frame["time"]):
                self.assertEqual(len(frame["points"]), 2)
                points = {p["color"]: p for p in frame["points"]}
                self.assertEqual(set(points), {SIGNAL, control_color})
                voltage_y, control_y = expected_y(name, time)
                for color, y in [(SIGNAL, voltage_y), (control_color, control_y)]:
                    self.assertAlmostEqual(points[color]["x"], 80 + time / span * 680,
                                           delta=0.6, msg="marker must follow elapsed time")
                    self.assertAlmostEqual(points[color]["y"], y, delta=0.75,
                                           msg="marker must match the electrical state")
                expected_phase = sum(time >= edge for edge in transitions)
                visible_phases = [i for i, opacity in enumerate(frame["phases"])
                                  if opacity > 0.01]
                self.assertEqual(visible_phases, [expected_phase],
                                 "exactly the current phase must be visible")
                self.assertAlmostEqual(frame["phases"][expected_phase], 1, delta=0.01)

    def test_linear_time_axis(self):
        for name in CASES:
            self.check_positions(name, [0, 3, 6, 9, 11.99])

    def test_transition_boundaries(self):
        for name, (span, transitions, _) in CASES.items():
            times = [edge / span * DURATION + offset
                     for edge in transitions for offset in [-0.002, 0.002]]
            self.check_positions(name, times)

    def test_four_beat_markers_follow_time_axis(self):
        for name, (duration, x0, x1, markers) in FOUR_BEATS.items():
            times = [0, duration * 0.17, duration * 0.5,
                     duration * 0.83, duration - 0.01]
            for frame, seconds in zip(self.snapshot(name, times), times):
                expected_x = x0 + seconds / duration * (x1 - x0)
                with self.subTest(diagram=name, seconds=seconds):
                    self.assertEqual(len(frame["points"]), markers)
                    for point in frame["points"]:
                        self.assertAlmostEqual(
                            point["x"], expected_x, delta=0.2,
                            msg=f"marker {point['color']} must follow elapsed time")

    def test_waveform_markers_advance_uniformly(self):
        for name, expected in LINEAR_X.items():
            self.page.goto((ASSETS / (name + ".svg")).as_uri())
            self.page.locator("svg").wait_for()
            markers = self.page.evaluate("""() => {
                const svg = document.documentElement;
                svg.pauseAnimations();
                return Array.from(svg.querySelectorAll('circle')).filter(c => {
                    const am = c.querySelector('animateMotion');
                    const kp = am && am.getAttribute('keyPoints');
                    return kp && kp.split(';').length >= 10;
                }).map(c => {
                    const dur = parseFloat(c.querySelector('animateMotion').getAttribute('dur'));
                    const xs = [];
                    for (let i = 0; i < 60; i++) {
                        svg.setCurrentTime(dur * i / 60);
                        const b = c.getBBox(), m = c.getCTM();
                        const cx = b.x + b.width / 2, cy = b.y + b.height / 2;
                        xs.push(m.a * cx + m.c * cy + m.e);
                    }
                    return xs;
                });
            }""")
            with self.subTest(diagram=name):
                self.assertEqual(len(markers), expected)
                for xs in markers:
                    steps = [b - a for a, b in zip(xs, xs[1:])]
                    median = sorted(steps)[len(steps) // 2]
                    kept = [s for s in steps if abs(s - median) <= abs(median)]
                    self.assertGreaterEqual(len(kept), len(steps) - 1)
                    self.assertGreater(median, 0.5, msg="marker must actually move")
                    for step in kept:
                        self.assertAlmostEqual(
                            step, median, delta=0.6,
                            msg="waveform marker x must advance uniformly")

    def test_cycle_restart_and_seek(self):
        for name in CASES:
            # Jump forwards and backwards; the second cycle must reproduce the first.
            self.check_positions(name, [24.01, 12, 12.01, 23.99, 0, 6])

    def test_cap_bias_sweep_matches_voltage_and_retention(self):
        self.page.goto((ASSETS / 'cap-derating.svg').as_uri())
        times = [0, 12 * 5 / 6.3, 12 * 2.5 / 6.3, 11.99, 12, 12 + 12 * 5 / 6.3]
        positions = self.page.evaluate("""times => {
            const svg = document.documentElement;
            svg.pauseAnimations();
            const dot = document.getElementById('cap-bias-sweep');
            const point = document.getElementById('cap-bias-point');
            return {point: [point.cx.baseVal.value, point.cy.baseVal.value],
                sweep: times.map(t => {
                    svg.setCurrentTime(t);
                    return [dot.cx.animVal.value, dot.cy.animVal.value];
                })};
        }""", times)
        self.assertAlmostEqual(positions['point'][0], 150 + 540 * 5 / 6.3, delta=.01)
        self.assertAlmostEqual(positions['point'][1], 340 - 200 * .26, delta=.01)
        samples = [(0, 1), (1, .93), (2, .80), (3, .62), (4, .43), (5, .26), (6.3, .15)]
        for t, (x, y) in zip(times, positions['sweep']):
            voltage = (t % 12) / 12 * 6.3
            for (a, ra), (b, rb) in zip(samples, samples[1:]):
                if a <= voltage <= b:
                    retention = ra + (rb - ra) * (voltage - a) / (b - a)
                    break
            with self.subTest(time=t):
                self.assertAlmostEqual(x, 150 + 540 * voltage / 6.3, delta=.05)
                self.assertAlmostEqual(y, 340 - 200 * retention, delta=.05)

    def test_cap_bias_captions_never_overlap(self):
        self.page.goto((ASSETS / 'cap-derating.svg').as_uri())
        result = self.page.evaluate("""() => {
            const svg = document.documentElement;
            svg.pauseAnimations();
            const captions = [...svg.querySelectorAll('#cap-bias-captions text')];
            function visible(t) {
                svg.setCurrentTime(t);
                return captions.filter(e => +getComputedStyle(e).opacity > .01).length;
            }
            return {count: captions.length,
                maximum: Math.max(...Array.from({length: 601}, (_, i) => visible(i * .04))),
                midpoints: [1.5, 4.5, 7.5, 10.5, 13.5].map(visible)};
        }""")
        self.assertEqual(4, result['count'])
        self.assertEqual(1, result['maximum'])
        self.assertEqual([1] * 5, result['midpoints'])


if __name__ == "__main__":
    unittest.main()
