"""Recalculate published examples independently of their drawing labels."""
import math
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.visuals.scenes.handdrawn_wave10 import esd_chain
from scripts.visuals.scenes.handdrawn_wave16 import bridge_junction_ledger, q_selectivity_map


def labels(parts):
    return ' '.join(re.sub('<[^>]+>', '', part) for part in parts)


class VisualCalculationsTests(unittest.TestCase):
    def test_q_is_carrier_frequency_over_half_power_bandwidth(self):
        text = labels(q_selectivity_map())
        results = [float(n) for n in re.findall(r'→ Q [=≈] (\d+)', text)]
        self.assertEqual(2, len(results))
        for actual, carrier, bandwidth in zip(results, [1e6, 100e6], [5e3, 150e3]):
            self.assertAlmostEqual(carrier / bandwidth, actual, delta=0.5)

    def test_bridge_total_counts_all_four_diodes(self):
        text = labels(bridge_junction_ledger())
        current = float(re.search(r'每只平均 ([\d.]+) A', text)[1])
        each = float(re.search(r'四只各 ([\d.]+) W', text)[1])
        total = float(re.search(r'总损耗为 ([\d.]+) W', text)[1])
        self.assertAlmostEqual(0.9 * current, each)
        self.assertAlmostEqual(4 * each, total)
        self.assertAlmostEqual(2 * 0.9 * 1.0, total)

    def test_esd_selected_resistor_meets_injection_limit(self):
        text = labels(esd_chain())
        chosen = float(re.search(r'取 (\d+)Ω', text)[1])
        self.assertLessEqual((9.2 - 5.7) / chosen, 0.01)
        self.assertGreater((9.2 - 5.7) / 330, 0.01)

    def test_moving_series_resistor_changes_source_current(self):
        text = labels(esd_chain())
        current, power = map(float, re.search(r'约 ([\d.]+)A、([\d.]+)kW', text).groups())
        actual = (8000 - 9.2) / (330 + 100)
        self.assertAlmostEqual(actual, current, delta=0.05)
        self.assertAlmostEqual(actual ** 2 * 100 / 1000, power, delta=0.1)


if __name__ == '__main__':
    unittest.main()
