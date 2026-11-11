"""Check physical geometry, not copied captions, for ch2 charge and bridge scenes."""
from pathlib import Path
import sys
import unittest
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.visuals.scenes import ch02_charge_window_v2 as charge
from scripts.visuals.scenes import ch02_bridge_power_v2 as bridge
from scripts.visuals.render import write


class Ch02AnimationTests(unittest.TestCase):
    def test_integrated_load_and_both_charge_pulses_balance(self):
        areas = {}
        for kind in ['load', 'rectangle', 'triangle']:
            points = charge.pulse(kind)
            areas[kind] = sum((b[0] - a[0]) * (a[1] + b[1]) / 2 for a, b in zip(points, points[1:]))
        self.assertAlmostEqual(10, areas['load'])  # A·ms = mC
        self.assertAlmostEqual(areas['load'], areas['rectangle'])
        self.assertAlmostEqual(areas['load'], areas['triangle'])
        self.assertAlmostEqual(2 * max(a for _, a in charge.pulse('rectangle')),
                               max(a for _, a in charge.pulse('triangle')))

    def test_both_bridge_paths_traverse_load_in_same_direction(self):
        for points in bridge.PATHS.values():
            segments = list(zip(points, points[1:]))
            self.assertIn(((580, 115), (580, 375)), segments)
        self.assertEqual(bridge.PATHS['positive'][0], bridge.PATHS['negative'][-1])
        self.assertEqual(bridge.PATHS['positive'][-1], bridge.PATHS['negative'][0])

    def test_each_path_crosses_two_correct_diodes_forward(self):
        expected = {'positive': {'D1', 'D4'}, 'negative': {'D2', 'D3'}}
        for polarity, points in bridge.PATHS.items():
            visited = set()
            for start, end in zip(points, points[1:]):
                if start[0] != end[0] or start[0] == 580:
                    continue
                for name, (x, y) in bridge.POSITIONS.items():
                    if x == start[0] and min(start[1], end[1]) < y < max(start[1], end[1]):
                        self.assertLess(end[1], start[1], 'All bridge diodes point upward')
                        visited.add(name)
            self.assertEqual(expected[polarity], visited)

    def test_total_bridge_loss_equals_two_forward_drops_times_load(self):
        self.assertAlmostEqual(2 * bridge.DIODE_VF * bridge.LOAD_A, sum(bridge.losses().values()))

    def test_print_diagrams_have_readable_labels_without_smaller_nested_transforms(self):
        for module in [charge, bridge]:
            tree = ET.fromstring(module.storyboard())
            for node in tree.iter():
                self.assertNotIn('scale(', node.get('transform', ''))
                self.assertFalse(node.tag.rsplit('}', 1)[-1].startswith('animate'))
                if node.tag.endswith('}text'):
                    # 138 mm usable width at 720 SVG units.
                    self.assertGreaterEqual(float(node.get('font-size')) * (138 / 25.4 * 72) / 720, 8.5)

    def test_builder_writes_the_explicit_print_layout_and_validates_xml(self):
        with tempfile.TemporaryDirectory() as directory:
            tl, layers = bridge.scene()
            write(tl, layers, directory, 'bridge', print_storyboard=bridge.storyboard())
            path = Path(directory) / 'bridge-storyboard.svg'
            self.assertEqual(bridge.storyboard(), path.read_text(encoding='utf-8'))
            with self.assertRaises(ET.ParseError):
                write(tl, layers, directory, 'broken', print_storyboard='<svg>')
            self.assertFalse((Path(directory) / 'broken.svg').exists())


if __name__ == '__main__':
    unittest.main()
