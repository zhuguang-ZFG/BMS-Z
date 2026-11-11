"""Numerically verify the chapter 12 examples with actual ngspice."""
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CircuitExamplesTests(unittest.TestCase):
    def simulate(self, circuit, outputs):
        executable = os.environ.get('NGSPICE') or shutil.which('ngspice')
        self.assertTrue(executable, 'Install ngspice or set NGSPICE to its console executable')
        with tempfile.TemporaryDirectory(prefix='analog-examples-') as temp:
            work = Path(temp)
            shutil.copyfile(ROOT / 'assets/examples' / circuit, work / circuit)
            result = subprocess.run([executable, '-b', circuit], cwd=work, capture_output=True,
                                    text=True, errors='replace', timeout=60)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            data = {}
            for name in outputs:
                self.assertTrue((work / name).is_file(), result.stdout + result.stderr)
                data[name] = [[float(v) for v in line.split()] for line in
                              (work / name).read_text().splitlines()[1:] if line.strip()]
            return data

    def test_capacitive_load_feedback_location_changes_the_actual_return_ratio(self):
        data = self.simulate('opamp-stability.cir', ('loop.csv', 'step.csv'))
        margins = []
        for column in (1, 3, 5):
            curve = [(row[0], complex(row[column], row[column + 1])) for row in data['loop.csv']]
            crossing = next(i for i in range(1, len(curve))
                            if abs(curve[i - 1][1]) >= 1 > abs(curve[i][1]))
            # Dense log sweep; the interpolation error is well below 0.2deg.
            before, after = curve[crossing - 1][1], curve[crossing][1]
            fraction = math.log(abs(before)) / math.log(abs(before) / abs(after))
            def angle(z):
                return math.degrees(math.atan2(z.imag, z.real))
            margins.append(180 + angle(before) + fraction * (angle(after) - angle(before)))
        for actual, expected in zip(margins, (10.2, 88.2, 7.2)):
            self.assertAlmostEqual(expected, actual, delta=0.25)
        # Probe the amplifier itself as well as the filtered load node.
        peaks = [max(row[column] for row in data['step.csv']) / 0.01 - 1 for column in (1, 2, 3, 4)]
        self.assertGreater(peaks[0], 0.70)
        self.assertLess(peaks[1], 0.05)
        self.assertLess(peaks[2], 0.05)
        self.assertGreater(peaks[3], peaks[0])

    def test_integrator_half_cycle_change_is_peak_to_peak_not_peak_amplitude(self):
        data = self.simulate('integrator-amplitude.cir', ('integrator.csv',))['integrator.csv']
        period = [row for row in data if 0.001 <= row[0] <= 0.002]
        self.assertGreater(len(period), 1000)
        for column, expected in ((1, 5), (2, 2), (3, 4)):
            swing = max(row[column] for row in period) - min(row[column] for row in period)
            self.assertAlmostEqual(expected, swing, delta=0.015)


if __name__ == '__main__':
    unittest.main()
