"""Validate download contents and actual ngspice voltages against reference points."""
import bisect
import csv
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import build_lab_packages
from build_lab_packages import IDS, LABS, build_packages


class LabPackageTests(unittest.TestCase):
    def test_archives_are_identical_with_windows_line_endings(self):
        expected = dict(build_packages())
        with tempfile.TemporaryDirectory(prefix='analog-lab-crlf-') as folder:
            work = Path(folder)
            sources = [build_lab_packages.ROOT / 'LICENSE', build_lab_packages.ROOT / 'docs/p8-03-s8-3.md']
            sources += [path for lab in IDS for path in (LABS / lab).iterdir()]
            for source in sources:
                target = work / source.relative_to(build_lab_packages.ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_text(encoding='utf-8').replace('\n', '\r\n').encode('utf-8'))
            with patch.multiple(build_lab_packages, ROOT=work, LABS=work / 'assets/labs'):
                self.assertEqual(expected, dict(build_packages()))

    def test_downloads_are_reproducible_and_include_instructions_and_blank_measurements(self):
        for lab, expected in build_packages():
            with self.subTest(lab=lab):
                self.assertEqual(expected, (LABS / f'{lab}-lab.zip').read_bytes())
                with zipfile.ZipFile(io.BytesIO(expected)) as archive:
                    self.assertEqual({'README.md', 'LICENSE', 'circuit.cir', 'bom.csv', 'reference.csv', 'measurements.csv'}, set(archive.namelist()))
                    instructions = archive.read('README.md').decode('utf-8')
                    self.assertIn('模型边界', instructions)
                    self.assertIn('验收', instructions)
                    self.assertIn('实测', instructions)
                    rows = list(csv.reader(io.StringIO(archive.read('measurements.csv').decode('utf-8'))))
                    self.assertTrue(rows[0])
                    self.assertTrue(all(not value for row in rows[1:] for value in row))

    def test_spice_output_matches_reference_voltages(self):
        executable = os.environ.get('NGSPICE') or shutil.which('ngspice') or shutil.which('ngspice_con')
        self.assertTrue(executable, 'Install ngspice or set NGSPICE to its executable; simulations must actually run.')
        for lab in IDS:
            with self.subTest(lab=lab), tempfile.TemporaryDirectory(prefix='analog-spice-') as folder:
                work = Path(folder)
                shutil.copyfile(LABS / lab / 'circuit.cir', work / 'circuit.cir')
                result = subprocess.run([executable, '-b', 'circuit.cir'], cwd=work, capture_output=True,
                                        text=True, encoding='utf-8', errors='replace', timeout=60)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                output = work / 'waveform.csv'
                self.assertTrue(output.is_file(), result.stdout + result.stderr)
                rows = [[float(value) for value in line.split()] for line in output.read_text().splitlines()[1:] if line.strip()]
                self.assertGreater(len(rows), 100)
                self.assertTrue(all(len(row) == 3 for row in rows))
                times = [row[0] for row in rows]
                with (LABS / lab / 'reference.csv').open(encoding='utf-8', newline='') as reference:
                    for sample in csv.DictReader(reference):
                        time = float(sample['time_s'])
                        position = bisect.bisect_left(times, time)
                        self.assertGreater(position, 0)
                        self.assertLess(position, len(rows))
                        before, after = rows[position - 1], rows[position]
                        fraction = (time - before[0]) / (after[0] - before[0])
                        for column, name in ((1, 'input_V'), (2, 'output_V')):
                            value = before[column] + fraction * (after[column] - before[column])
                            self.assertAlmostEqual(float(sample[name]), value, delta=float(sample['tolerance_V']),
                                                   msg=f'{lab} at {time}s: {name}')


if __name__ == '__main__':
    unittest.main()
