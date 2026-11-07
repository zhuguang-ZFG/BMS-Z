"""Behavior tests for the virtual training project; no hardware safety claim."""
from __future__ import annotations

import binascii
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import types
import unittest

import learn
import project
import reference


def row(now, *, sampled=None, cells=None, closed=True, current=1.0):
    return {'now_s': now, 'sampled_s': now if sampled is None else sampled,
            'cells_v': [3.7] * 4 if cells is None else cells,
            'current_a': current, 'temp_c': 25.0,
            'feedback_closed': closed, 'remote_requested': True, 'remote_received_s': now}


def first(rows, predicate):
    return next((item['now_s'] for item in rows if predicate(item)), None)


class ArithmeticTests(unittest.TestCase):
    def test_delay_uses_elapsed_time_and_resets_after_a_good_observation(self):
        self.assertAlmostEqual(reference.trip_at([0, .05, .2], [True] * 3, .2), .2)
        self.assertIsNone(reference.trip_at([0, .1, .3, .4], [True, False, True, True], .2))
        self.assertAlmostEqual(reference.trip_at([0, .1, .2, .3], [False, True, True, True], .2), .3)

    def test_charge_sign_capacity_and_seconds_are_independent(self):
        self.assertAlmostEqual(reference.soc_step(.6, .8, 900, 2), .5)
        self.assertAlmostEqual(reference.soc_step(.5, -.5, 720, 2), .55)
        self.assertAlmostEqual(reference.soc_step(1, 1, 576, 1.6), .9)
        for args in [(1, 1, 1, 0), (1, 1, -1, 2), (1, math.nan, 1, 2)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                reference.soc_step(*args)

    def test_quality_rejects_bad_values_and_boundary_ages(self):
        self.assertTrue(reference.sample_ok([3.7] * 4, 1, 1.5, .5))
        self.assertTrue(reference.sample_ok([3.7] * 4, .6, 1.1, .5))
        for values, sampled, now in [([3.7] * 4, 1, 1.50001),
                                     ([3.7] * 3, 1, 1),
                                     ([3.7, math.nan, 3.7, 3.7], 1, 1),
                                     ([3.7] * 4, 2, 1),
                                     ([3.7] * 4, 1, math.inf)]:
            with self.subTest(values=values, sampled=sampled, now=now):
                self.assertFalse(reference.sample_ok(values, sampled, now, .5))

    def test_balance_time_rejects_nonfinite_values_and_nonphysical_signs(self):
        for args in [(-.1, .05), (.1, 0), (.1, -.05), (math.nan, .05),
                     (.1, math.inf), (math.inf, .05), (.1, math.nan)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                reference.balance_hours(*args)


class WireTests(unittest.TestCase):
    def test_signed_milliamps_little_endian_and_full_frame_round_trip(self):
        frame = reference.encode(14.81, -1.25, 255)
        self.assertEqual(frame[:6], bytes.fromhex('da391efbff01'))
        self.assertEqual(reference.decode(frame), (14.81, -1.25, 255))

    def test_any_single_bit_error_in_the_eight_byte_fixture_is_rejected(self):
        good = reference.encode(14.81, -1.25, 255)
        for position in range(len(good)):
            for bit in range(8):
                damaged = bytearray(good)
                damaged[position] ^= 1 << bit
                with self.subTest(position=position, bit=bit), self.assertRaises(ValueError):
                    reference.decode(bytes(damaged))

    def test_valid_crc_cannot_make_bad_quality_range_or_length_valid(self):
        good = reference.encode(14.81, 1, 1)
        for frame in [good[:-1], good + b'\0', reference.encode(14.81, 1, 1, 0),
                      reference.encode(20.001, 1, 1)]:
            with self.subTest(frame=frame), self.assertRaises(ValueError):
                reference.decode(frame)

    def test_sequence_wrap_is_accepted_but_replay_and_missing_frames_are_not(self):
        self.assertTrue(reference.sequence_ok(255, 0))
        self.assertTrue(reference.sequence_ok(None, 73))
        self.assertFalse(reference.sequence_ok(73, 73))
        self.assertFalse(reference.sequence_ok(73, 75))


class ControllerTests(unittest.TestCase):
    def test_controller_rejects_invalid_capacity_or_period_before_starting(self):
        for invalid in [0, -1, math.nan, math.inf]:
            with self.subTest(capacity=invalid), self.assertRaises(ValueError):
                project.Controller(capacity_ah=invalid)
            with self.subTest(period=invalid), self.assertRaises(ValueError):
                project.Controller(period_s=invalid)

    def test_invalid_local_clock_cannot_contaminate_state_or_feedback_timer(self):
        control = project.Controller()
        control.step(row(0))
        off = row(.1)
        off['remote_requested'] = False
        control.step(off)
        before = {key: value.copy() if isinstance(value, set) else value
                  for key, value in control.__dict__.items()}
        for now in [math.nan, math.inf, .1, .05]:
            with self.subTest(now=now), self.assertRaises(ValueError):
                control.step(row(now))
            self.assertEqual(control.__dict__, before)
        for now in [.2, .3]:
            off = row(now)
            off['remote_requested'] = False
            result = control.step(off)
            self.assertEqual('ACTUATOR_STUCK' in result['faults'], now == .3)

    def test_nominal_replay_keeps_output_enabled_with_valid_soc(self):
        _, rows = project.replay('nominal')
        self.assertTrue(all(item['command_on'] and item['soc_valid'] for item in rows))
        self.assertAlmostEqual(rows[-1]['soc'], 1 - 2 / (3600 * 2))

    def test_one_tick_spike_cannot_accumulate_into_undervoltage(self):
        _, rows = project.replay('spike')
        self.assertIsNone(first(rows, lambda item: not item['command_on']))
        self.assertTrue(all('UV' not in item['faults'] for item in rows))

    def test_undervoltage_action_and_feedback_have_separate_times(self):
        _, rows = project.replay('undervoltage')
        self.assertEqual(first(rows, lambda item: not item['command_on']), .5)
        self.assertEqual(first(rows, lambda item: not item['feedback_closed']), .6)
        self.assertIsNone(first(rows, lambda item: 'ACTUATOR_STUCK' in item['faults']))

    def test_pretrip_recovery_clears_continuous_time_even_inside_reset_hysteresis(self):
        control = project.Controller()
        control.step(row(0, cells=[2.95, 3.7, 3.7, 3.7]))
        control.step(row(.1, cells=[3.10, 3.7, 3.7, 3.7]))
        result = control.step(row(.2, cells=[2.95, 3.7, 3.7, 3.7]))
        self.assertTrue(result['command_on'])
        self.assertNotIn('UV', result['faults'])

    def test_fault_latch_survives_voltage_recovery_and_remote_enable(self):
        control = project.Controller()
        for now in [0, .1, .2]:
            control.step(row(now, cells=[2.95, 3.7, 3.7, 3.7]))
        recovered = control.step(row(.3, closed=False, current=0))
        self.assertFalse(recovered['command_on'])
        self.assertIn('UV', recovered['faults'])

    def test_repeated_timestamp_is_rejected_before_age_limit(self):
        control = project.Controller()
        control.step(row(0))
        result = control.step(row(.1, sampled=0))
        self.assertFalse(result['sample_valid'])
        self.assertFalse(result['command_on'])
        self.assertFalse(result['soc_valid'])
        self.assertIn('SAMPLE_INVALID', result['faults'])

    def test_missing_interval_does_not_get_integrated_as_known_current(self):
        control = project.Controller()
        control.step(row(0))
        result = control.step(row(.3))
        self.assertFalse(result['soc_valid'])
        self.assertFalse(result['command_on'])
        self.assertIn('SAMPLE_GAP', result['faults'])
        self.assertEqual(result['soc'], 1)

    def test_invalid_cell_sets_produce_a_safe_log_instead_of_crashing(self):
        for cells in [[], [3.7] * 3, [3.7, math.nan, 3.7, 3.7]]:
            with self.subTest(cells=cells):
                control = project.Controller()
                result = control.step(row(0, cells=cells))
                self.assertFalse(result['sample_valid'])
                self.assertFalse(result['command_on'])
                self.assertFalse(result['soc_valid'])
                self.assertIn('SAMPLE_INVALID', result['faults'])
                self.assertIsNone(result['min_v'])
                self.assertIsNone(result['pack_v'])

    def test_feedback_timeout_is_latched_at_elapsed_boundary(self):
        _, rows = project.replay('feedback')
        self.assertEqual(first(rows, lambda item: not item['command_on']), .5)
        self.assertEqual(first(rows, lambda item: 'ACTUATOR_STUCK' in item['faults']), .7)
        self.assertIn('ACTUATOR_STUCK', rows[-1]['faults'])

    def test_remote_timeout_is_separate_from_measurement_quality_and_stays_latched(self):
        control = project.Controller()
        for now in [0, .1, .2, .3]:
            sample = row(now)
            sample['remote_received_s'] = 0
            result = control.step(sample)
            self.assertTrue(result['command_on'])
            self.assertTrue(result['remote_fresh'])
        sample = row(.4)
        sample['remote_received_s'] = 0
        result = control.step(sample)
        self.assertTrue(result['sample_valid'])
        self.assertFalse(result['remote_fresh'])
        self.assertFalse(result['command_on'])
        self.assertIn('COMM_TIMEOUT', result['faults'])
        recovered = control.step(row(.5, closed=False, current=0))
        self.assertTrue(recovered['remote_fresh'])
        self.assertFalse(recovered['command_on'])
        self.assertIn('COMM_TIMEOUT', recovered['faults'])

    def test_timeout_fixture_stops_remote_updates_without_stopping_measurements(self):
        inputs, rows = project.replay('timeout')
        self.assertEqual(inputs[7]['remote_received_s'], .4)
        self.assertEqual(inputs[8]['sampled_s'], .8)
        self.assertTrue(rows[7]['command_on'])
        self.assertEqual(first(rows, lambda item: not item['command_on']), .8)
        self.assertTrue(rows[8]['sample_valid'])
        self.assertFalse(rows[8]['remote_fresh'])
        self.assertIn('COMM_TIMEOUT', rows[8]['faults'])

    def test_soc_stops_spending_charge_only_when_feedback_and_fixture_current_open(self):
        inputs, rows = project.replay('undervoltage')
        self.assertEqual(inputs[6]['current_a'], 0)
        self.assertAlmostEqual(rows[-1]['soc'], 1 - .6 / (3600 * 2))

    def test_transfer_changes_period_capacity_and_bad_cell_without_changing_delay(self):
        inputs, rows = project.replay('transfer')
        self.assertEqual(inputs[1]['now_s'] - inputs[0]['now_s'], .05)
        self.assertEqual(inputs[6]['cells_v'][0], 2.98)
        self.assertEqual(first(rows, lambda item: not item['command_on']), .5)
        self.assertEqual(first(rows, lambda item: not item['feedback_closed']), .55)
        # Check the interval before the switch opens; its current is still exactly 1 A.
        self.assertAlmostEqual(rows[10]['soc'], 1 - .5 / (3600 * 1.6))

    def test_integration_uses_the_supplied_learner_rules(self):
        rules = types.SimpleNamespace(**{name: getattr(reference, name)
                                        for name in ('pack_voltage', 'sample_ok', 'soc_step', 'remote_enable')})
        rules.pack_voltage = lambda cells: 123.0
        result = project.Controller(rules=rules).step(row(0))
        self.assertEqual(result['pack_v'], 123.0)


class GraderTests(unittest.TestCase):
    def learner_copy(self):
        return types.SimpleNamespace(**{name: getattr(reference, name) for _, name, _, _ in learn.checks()})

    def test_reference_passes_but_a_constant_answer_fails_the_changed_input(self):
        passed, failures = learn.grade(reference, 18)
        self.assertGreater(passed, 0)
        self.assertEqual(failures, [])
        learner = self.learner_copy()
        learner.pack_voltage = lambda cells: 14.81
        passed, failures = learn.grade(learner, 4)
        self.assertEqual(passed, 1)
        self.assertEqual(len(failures), 1)
        self.assertIn('13.0', failures[0])

    def test_wrong_current_sign_and_always_enabled_remote_are_rejected(self):
        learner = self.learner_copy()
        learner.soc_step = lambda soc, current_a, dt_s, capacity_ah: min(
            1, max(0, soc + current_a * dt_s / (3600 * capacity_ah)))
        learner.remote_enable = lambda local_safe, fresh, requested: True
        _, failures = learn.grade(learner, 18)
        self.assertTrue(any('soc_step' in failure for failure in failures))
        self.assertTrue(any('remote_enable' in failure for failure in failures))

    def test_grader_rejects_missing_charge_request_and_temperature_upper_bound(self):
        mutants = [lambda temp, valid, requested: bool(valid and 0 <= temp <= 45),
                   lambda temp, valid, requested: bool(valid and requested and temp >= 0),
                   lambda temp, valid, requested: bool(valid and requested and 0 <= temp < 45)]
        for mutant in mutants:
            with self.subTest(mutant=mutant):
                learner = self.learner_copy()
                learner.charge_allowed = mutant
                _, failures = learn.grade(learner, 13)
                self.assertTrue(any('charge_allowed' in failure for failure in failures))

    def test_grader_rejects_missing_inclusive_overvoltage_boundary(self):
        learner = self.learner_copy()
        learner.violations = lambda cells, low, high: min(cells) <= low or max(cells) > high
        _, failures = learn.grade(learner, 7)
        self.assertTrue(any('violations' in failure for failure in failures))

    def test_grader_rejects_soc_that_silently_clamps_invalid_time_or_capacity(self):
        learner = self.learner_copy()
        learner.soc_step = lambda soc, current, dt, capacity: max(
            0.0, min(1.0, soc - current * dt / (3600 * capacity)))
        _, failures = learn.grade(learner, 10)
        self.assertTrue(any('soc_step' in failure and 'expected=' in failure for failure in failures))

    def test_grader_rejects_good_crc_but_unchecked_voltage_range(self):
        def decode_without_voltage_range(frame):
            if len(frame) != 8:
                raise ValueError('length')
            payload = frame[:6]
            if binascii.crc_hqx(payload, 0xFFFF) != struct.unpack('<H', frame[6:])[0]:
                raise ValueError('crc')
            mv, ma, sequence, quality = struct.unpack('<HhBB', payload)
            if quality != 1:
                raise ValueError('quality')
            return mv / 1000, ma / 1000, sequence

        learner = self.learner_copy()
        learner.decode = decode_without_voltage_range
        _, failures = learn.grade(learner, 17)
        self.assertTrue(any('decode' in failure for failure in failures))

    def test_grader_rejects_balance_time_that_lets_nonfinite_values_through(self):
        def balance_without_finite_check(delta, current):
            if delta < 0 or current <= 0:
                raise ValueError('sign')
            return delta / current

        learner = self.learner_copy()
        learner.balance_hours = balance_without_finite_check
        _, failures = learn.grade(learner, 14)
        self.assertTrue(any('balance_hours' in failure for failure in failures))

class ReplayFileTests(unittest.TestCase):
    """Exercise the learner's real CLI and the evidence it leaves on disk."""

    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(
            prefix='.tmp-course-replay-', dir=Path(__file__).resolve().parents[2])
        self.addCleanup(self.workspace.cleanup)
        self.directory = Path(self.workspace.name)
        self.counter = 0

    def document(self):
        return {'schema': 'bms-course-input-v1',
                'config': {'capacity_ah': 2.0, 'period_s': .1},
                'samples': list(project.samples('nominal'))[:3]}

    def cli(self, *arguments):
        return subprocess.run(
            [sys.executable, '-B', str(Path(project.__file__).resolve()), *map(str, arguments)],
            cwd=self.directory,
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUTF8': '1'},
            capture_output=True, encoding='utf-8', timeout=30,
        )

    def replay_file(self, document=None, *, raw=None, work=None, succeeds=True):
        self.counter += 1
        source = self.directory / f'input-{self.counter}.json'
        output = self.directory / f'run-{self.counter}'
        source.write_bytes(raw if raw is not None else json.dumps(document).encode('utf-8'))
        arguments = ['--input', source, '--out', output]
        if work is not None:
            arguments += ['--work', work]
        result = self.cli(*arguments)
        if succeeds:
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((output / 'report.json').read_bytes())
            return output, report
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse(output.exists(), f'failed replay left an output directory: {result.stderr}')
        return result

    def test_default_cli_exports_complete_configuration_and_source_metadata(self):
        output = self.directory / 'default-run'
        result = self.cli('--out', output)
        self.assertEqual(result.returncode, 0, result.stderr)
        document = json.loads((output / 'input.json').read_bytes())
        report = json.loads((output / 'report.json').read_bytes())
        self.assertEqual(set(document), {'schema', 'config', 'samples'})
        self.assertEqual(document['schema'], 'bms-course-input-v1')
        self.assertEqual(document['config'], {'capacity_ah': 2.0, 'period_s': .1})
        self.assertEqual(len(document['samples']), 21)
        self.assertEqual(report['scenario'], 'nominal')
        self.assertEqual(report['input_source'], {'kind': 'builtin', 'scenario': 'nominal'})
        self.assertEqual(report['config'], document['config'])
        self.assertFalse(report['hardware_verified'])
        self.assertEqual(report['python_version'], sys.version.split()[0])
        self.assertEqual(report['argv'][-2:], ['--out', str(output)])
        self.assertEqual(report['input_sha256'], hashlib.sha256((output / 'input.json').read_bytes()).hexdigest())
        self.assertAlmostEqual(report['last']['soc'], 1 - 2 / (3600 * 2))

    def test_transfer_file_replay_preserves_configuration_trace_and_original_bytes(self):
        exported = self.directory / 'exported'
        result = self.cli('--scenario', 'transfer', '--out', exported)
        self.assertEqual(result.returncode, 0, result.stderr)
        document = json.loads((exported / 'input.json').read_bytes())
        self.assertEqual(document['config'], {'capacity_ah': 1.6, 'period_s': .05})
        # Whitespace deliberately differs from the built-in exporter. Preserve
        # the actual input bytes, not a normalized JSON approximation of them.
        raw = b' \n' + json.dumps(document, separators=(',', ':')).encode('utf-8') + b'\n\t'
        replayed, report = self.replay_file(raw=raw)
        original = json.loads((exported / 'report.json').read_bytes())
        self.assertEqual((replayed / 'input.json').read_bytes(), raw)
        self.assertEqual((replayed / 'trace.csv').read_bytes(), (exported / 'trace.csv').read_bytes())
        self.assertEqual(report['last'], original['last'])
        self.assertEqual(report['first_off_s'], original['first_off_s'])
        self.assertEqual(report['scenario'], 'custom')
        self.assertEqual(report['input_source']['kind'], 'file')
        self.assertEqual(report['config'], document['config'])
        self.assertEqual(report['input_sha256'], hashlib.sha256(raw).hexdigest())

    def test_changed_current_and_remote_request_change_actual_trace_and_summary(self):
        baseline, before = self.replay_file(self.document())
        current = self.document()
        for sample in current['samples']:
            sample['current_a'] = 2.0
        changed, after = self.replay_file(current)
        self.assertNotEqual((changed / 'trace.csv').read_bytes(), (baseline / 'trace.csv').read_bytes())
        self.assertLess(after['last']['soc'], before['last']['soc'])
        request = self.document()
        request['samples'][1]['remote_requested'] = False
        changed, after = self.replay_file(request)
        self.assertNotEqual((changed / 'trace.csv').read_bytes(), (baseline / 'trace.csv').read_bytes())
        self.assertEqual(after['first_off_s'], .1)
        self.assertIsNone(before['first_off_s'])

    def test_file_capacity_changes_soc_and_period_changes_missing_interval_diagnosis(self):
        _, baseline = self.replay_file(self.document())
        document = self.document()
        document['config']['capacity_ah'] = 1.0
        _, report = self.replay_file(document)
        self.assertAlmostEqual(report['last']['soc'], 1 - .2 / 3600)
        self.assertLess(report['last']['soc'], baseline['last']['soc'])
        document = self.document()
        document['config']['period_s'] = .05
        _, report = self.replay_file(document)
        self.assertIn('SAMPLE_GAP', report['last']['faults'])
        self.assertFalse(report['last']['soc_valid'])
        self.assertNotIn('SAMPLE_GAP', baseline['last']['faults'])

    def test_cell_count_and_range_faults_reach_the_quality_layer(self):
        for cells in ([], [3.7] * 3, [3.7] * 5, [-.1, 3.7, 3.7, 3.7], [3.7, 5.01, 3.7, 3.7]):
            with self.subTest(cells=cells):
                document = self.document()
                document['samples'] = document['samples'][:1]
                document['samples'][0]['cells_v'] = cells
                _, report = self.replay_file(document)
                self.assertIn('SAMPLE_INVALID', report['last']['faults'])
                self.assertFalse(report['last']['command_on'])
                self.assertFalse(report['last']['sample_valid'])
                self.assertIsNone(report['last']['pack_v'])

    def test_existing_output_paths_are_refused_without_changing_evidence(self):
        output, _ = self.replay_file(self.document())
        before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in output.iterdir()}
        result = self.cli('--scenario', 'transfer', '--out', output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('run-02', result.stderr)
        self.assertEqual(before, {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in output.iterdir()})
        empty = self.directory / 'empty-directory'
        empty.mkdir()
        file = self.directory / 'ordinary-file'
        file.write_text('keep this evidence', encoding='utf-8')
        for existing in (empty, file):
            with self.subTest(existing=existing):
                result = self.cli('--out', existing)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('output path already exists', result.stderr)
        self.assertEqual(list(empty.iterdir()), [])
        self.assertEqual(file.read_text(encoding='utf-8'), 'keep this evidence')

    def test_input_and_scenario_are_mutually_exclusive(self):
        output = self.directory / 'invalid-choice'
        result = self.cli('--input', 'not-read.json', '--scenario', 'nominal', '--out', output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('not allowed with argument', result.stderr)
        self.assertFalse(output.exists())

    def test_legacy_lists_bad_json_and_duplicate_keys_never_create_output(self):
        legacy = self.replay_file(raw=b'[]', succeeds=False)
        self.assertIn('export the scenario again', legacy.stderr)
        valid = json.dumps(self.document())
        duplicates = [
            valid.replace('"schema":', '"schema": "bms-course-input-v1", "schema":', 1),
            valid.replace('"period_s":', '"period_s": 0.1, "period_s":', 1),
            valid.replace('"now_s":', '"now_s": 0, "now_s":', 1),
        ]
        for raw in ('{', '', *duplicates):
            with self.subTest(raw=raw[:80]):
                result = self.replay_file(raw=raw.encode(), succeeds=False)
                if raw in duplicates:
                    self.assertIn('duplicate JSON key', result.stderr)

    def test_nonfinite_json_constants_and_numeric_overflow_are_rejected(self):
        valid = json.dumps(self.document())
        for token in ('NaN', 'Infinity', '-Infinity', '1e999', '9' * 400):
            with self.subTest(token=token[:20]):
                raw = valid.replace('"current_a": 1.0', f'"current_a": {token}', 1).encode()
                self.replay_file(raw=raw, succeeds=False)

    def test_invalid_config_schema_and_sample_structure_never_create_output(self):
        cases = []
        for field in ('capacity_ah', 'period_s'):
            for value in (0, -1, True, '0.1', None):
                document = self.document()
                document['config'][field] = value
                cases.append(document)
            document = self.document()
            del document['config'][field]
            cases.append(document)
        for config in ([], None, {'capacity_ah': 2, 'period_s': .1, 'initial_soc': .5}):
            document = self.document()
            document['config'] = config
            cases.append(document)
        for key in ('schema', 'config', 'samples'):
            document = self.document()
            del document[key]
            cases.append(document)
        document = self.document()
        document['unexpected'] = 1
        cases.append(document)
        for value in ('unknown-version', 1, None):
            document = self.document()
            document['schema'] = value
            cases.append(document)
        for value in ([], {}, None, [None], [[]]):
            document = self.document()
            document['samples'] = value
            cases.append(document)
        for index, document in enumerate(cases):
            with self.subTest(case=index):
                self.replay_file(document, succeeds=False)

    def test_row_fields_types_and_local_clock_are_validated_before_output(self):
        invalid_rows = []
        for key in project.SAMPLE_FIELDS:
            sample = copy.deepcopy(self.document()['samples'][0])
            del sample[key]
            invalid_rows.append(sample)
        sample = copy.deepcopy(self.document()['samples'][0])
        sample['unrecognized'] = 1
        invalid_rows.append(sample)
        for key in ('now_s', 'sampled_s', 'current_a', 'temp_c', 'remote_received_s'):
            for value in (True, '0.0', None):
                sample = copy.deepcopy(self.document()['samples'][0])
                sample[key] = value
                invalid_rows.append(sample)
        for key in ('feedback_closed', 'remote_requested'):
            for value in (0, 1, 'false', None):
                sample = copy.deepcopy(self.document()['samples'][0])
                sample[key] = value
                invalid_rows.append(sample)
        for cells in (None, {}, '3.7', [True], ['3.7'], [None]):
            sample = copy.deepcopy(self.document()['samples'][0])
            sample['cells_v'] = cells
            invalid_rows.append(sample)
        for index, sample in enumerate(invalid_rows):
            with self.subTest(row=index):
                document = self.document()
                document['samples'] = [sample]
                self.replay_file(document, succeeds=False)
        for now in (0, -.1):
            document = self.document()
            document['samples'][1]['now_s'] = now
            result = self.replay_file(document, succeeds=False)
            self.assertIn('strictly increasing', result.stderr)

    def test_supplied_learner_file_is_executed_and_identified(self):
        work = self.directory / 'my_bms.py'
        work.write_text('''def pack_voltage(cells):
    return 123.0
def sample_ok(cells, sampled_s, now_s, max_age_s):
    return True
def soc_step(soc, current_a, dt_s, capacity_ah):
    return 0.42
def remote_enable(local_safe, fresh, requested):
    return False
''', encoding='utf-8')
        _, report = self.replay_file(self.document(), work=work)
        self.assertEqual(report['implementation'], 'learner')
        self.assertEqual(report['implementation_sha256'], hashlib.sha256(work.read_bytes()).hexdigest())
        self.assertEqual(report['last']['pack_v'], 123.0)
        self.assertEqual(report['last']['soc'], .42)
        self.assertFalse(report['last']['command_on'])

    def test_learner_load_execution_and_serialization_failures_leave_no_output(self):
        for content in ('def broken(:\n', 'raise RuntimeError("load failed")\n',
                        'def sample_ok(*args):\n    raise RuntimeError("learner failed")\n',
                        'def sample_ok(*args):\n    return True\n'
                        'def pack_voltage(*args):\n    return float("nan")\n'
                        'def remote_enable(*args):\n    return True\n'):
            with self.subTest(content=content[:70]):
                work = self.directory / f'bad-learner-{self.counter}.py'
                work.write_text(content, encoding='utf-8')
                # One sample reaches the serialization failure without needing
                # an SOC function; this also checks full preflight ordering.
                document = self.document()
                document['samples'] = document['samples'][:1]
                self.replay_file(document, work=work, succeeds=False)


if __name__ == '__main__':
    unittest.main()
