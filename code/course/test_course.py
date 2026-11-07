"""Behavior tests for the virtual training project; no hardware safety claim."""
from __future__ import annotations

import binascii
import math
import struct
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

if __name__ == '__main__':
    unittest.main()
