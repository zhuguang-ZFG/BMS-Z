"""Create and check a learner-owned file. No pip packages required."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import shutil

import reference

ROOT = Path(__file__).resolve().parent


def load_work(path):
    spec = importlib.util.spec_from_file_location('bms_course_learner', path.resolve())
    if spec is None or spec.loader is None:
        raise ValueError('work file must be a Python file')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checks():
    good = reference.encode(14.81, -1.25, 255)
    corrupt = good[:2] + bytes([good[2] ^ 1]) + good[3:]
    return [
        (4, 'pack_voltage', ([3.7, 3.72, 3.68, 3.71],), 14.81),
        (4, 'pack_voltage', ([3.1, 3.2, 3.3, 3.4],), 13.0),
        (5, 'calibrate', (3.712, .012), 3.7),
        (5, 'calibrate', (3.68, -.02), 3.7),
        (6, 'sample_ok', ([3.7]*4, 1, 1.5, .5), True),
        (6, 'sample_ok', ([3.7]*4, .6, 1.1, .5), True),
        (6, 'sample_ok', ([3.7]*4, 1, 1.501, .5), False),
        (6, 'sample_ok', ([3.7, float('nan'), 3.7, 3.7], 1, 1, .5), False),
        (6, 'sample_ok', ([3.7]*3, 1, 1, .5), False),
        (6, 'sample_ok', ([3.7]*4, 2, 1, .5), False),
        (6, 'sample_ok', ([3.7, 5.01, 3.7, 3.7], 1, 1, .5), False),
        (6, 'sample_ok', ([3.7]*4, 1, float('inf'), .5), False),
        (7, 'violations', ([4.25, 3.52, 3.52, 3.52], 3, 4.2), True),
        (7, 'violations', ([3.7]*4, 3, 4.2), False),
        (7, 'violations', ([3]*4, 3, 4.2), True),
        (7, 'violations', ([3.7, 4.2, 3.7, 3.7], 3, 4.2), True),
        (8, 'trip_at', ([0, .1, .2, .3], [False, True, True, True], .2), .3),
        (8, 'trip_at', ([0, .1, .3, .4], [True, False, True, True], .2), None),
        (8, 'trip_at', ([0, .05, .2], [True]*3, .2), .2),
        (9, 'can_reset', (True, True, True), True),
        (9, 'can_reset', (False, True, True), False),
        (9, 'can_reset', (True, False, True), False),
        (9, 'can_reset', (True, True, False), False),
        (10, 'soc_step', (1, 1, 1800, 2), .75),
        (10, 'soc_step', (.5, -1, 360, 2), .55),
        (10, 'soc_step', (.01, 2, 3600, 2), 0),
        (10, 'soc_step', (.99, -2, 3600, 2), 1),
        (10, 'soc_step', (.5, 1, 1, 0), ValueError),
        (10, 'soc_step', (.5, 1, 1, -2), ValueError),
        (10, 'soc_step', (.5, 1, -1, 2), ValueError),
        (10, 'soc_step', (.5, float('nan'), 1, 2), ValueError),
        (11, 'drift', (.02, 5, 2), .05),
        (11, 'drift', (-.01, 2, 1), -.02),
        (12, 'ocv_soc', (3.7, 3.3, 4.1), .5),
        (12, 'ocv_soc', (4.2, 3.3, 4.1), 1),
        (13, 'charge_allowed', (-1, True, True), False),
        (13, 'charge_allowed', (25, False, True), False),
        (13, 'charge_allowed', (0, True, True), True),
        (13, 'charge_allowed', (45, True, True), True),
        (13, 'charge_allowed', (45.001, True, True), False),
        (13, 'charge_allowed', (25, True, False), False),
        (14, 'balance_hours', (.1, .05), 2),
        (14, 'balance_hours', (.06, .02), 3),
        (14, 'balance_hours', (-.1, .05), ValueError),
        (14, 'balance_hours', (.1, 0), ValueError),
        (14, 'balance_hours', (float('nan'), .05), ValueError),
        (14, 'balance_hours', (.1, float('inf')), ValueError),
        (15, 'remaining_ah', ([2, 2, 1.8, 2], [.5]*4), .9),
        (15, 'remaining_ah', ([2]*4, [.5, .4, .3, .6]), .6),
        (16, 'decode', (good,), (14.81, -1.25, 255)),
        (17, 'decode', (corrupt,), ValueError),
        (17, 'decode', (good[:-1],), ValueError),
        (17, 'decode', (reference.encode(14.8, 1, 1, 0),), ValueError),
        (17, 'decode', (reference.encode(20.001, 1, 1),), ValueError),
        (17, 'sequence_ok', (255, 0), True),
        (17, 'sequence_ok', (4, 4), False),
        (17, 'sequence_ok', (4, 6), False),
        (17, 'sequence_ok', (None, 19), True),
        (18, 'remote_enable', (False, True, True), False),
        (18, 'remote_enable', (True, False, True), False),
        (18, 'remote_enable', (True, True, False), False),
        (18, 'remote_enable', (True, True, True), True),
    ]


def equal(actual, expected):
    if isinstance(expected, bool):
        return actual is expected
    if isinstance(expected, (float, int)):
        return isinstance(actual, (float, int)) and abs(actual - expected) < 1e-8
    if isinstance(expected, tuple):
        return isinstance(actual, tuple) and len(actual) == len(expected) and all(equal(a, b) for a, b in zip(actual, expected, strict=True))
    return actual == expected


def grade(module, through):
    failures, passed = [], 0
    for lesson, name, args, expected in checks():
        if lesson > through:
            continue
        try:
            actual = getattr(module, name)(*args)
            if expected is ValueError or not equal(actual, expected):
                failures.append(f'{lesson:02d} {name}: args={args!r}; expected={expected!r}; got={actual!r}')
                continue
        except ValueError:
            if expected is not ValueError:
                failures.append(f'{lesson:02d} {name}: unexpected ValueError')
                continue
        except Exception as exc:
            failures.append(f'{lesson:02d} {name}: {type(exc).__name__}: {exc}')
            continue
        passed += 1
    return passed, failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['doctor', 'init', 'check'])
    parser.add_argument('--work', type=Path)
    parser.add_argument('--through', type=int, default=4, choices=range(4, 19))
    parser.add_argument('--reference', action='store_true', help='explicitly check the supplied solution')
    args = parser.parse_args()
    if args.action == 'doctor':
        import sys
        print(f'Python {sys.version.split()[0]}; standard library only; project={ROOT}')
        print('PASS: struct / binascii / csv / json available; no board or serial port required')
        return 0
    if args.action == 'init':
        if args.work is None:
            parser.error('init requires --work path.py')
        if args.work.exists():
            parser.error('work file already exists; choose another path to preserve your answers')
        args.work.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'workbook.py', args.work)
        print(f'created {args.work}; lesson 04 is ready, lessons 05..18 are yours to implement')
        return 0
    if args.reference == (args.work is not None):
        parser.error('check requires exactly one of --work path.py or --reference')
    module = reference if args.reference else load_work(args.work)
    passed, failures = grade(module, args.through)
    print(f'{"REFERENCE" if args.reference else "LEARNER"}: {passed} passed, {len(failures)} failed, through lesson {args.through:02d}')
    for failure in failures:
        print(f'FAIL {failure}')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
