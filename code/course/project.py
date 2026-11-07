"""Replay a virtual 4S pack. No hardware connection; all thresholds are teaching values."""
from __future__ import annotations

import argparse
import csv
import hashlib
from io import StringIO
import json
import math
from pathlib import Path
import sys

import reference
from learn import load_work

SCENARIOS = ('nominal', 'spike', 'undervoltage', 'stale', 'feedback', 'timeout', 'transfer')
INPUT_SCHEMA = 'bms-course-input-v1'
SAMPLE_FIELDS = {'now_s', 'sampled_s', 'cells_v', 'current_a', 'temp_c',
                 'feedback_closed', 'remote_requested', 'remote_received_s'}


def scenario_config(scenario):
    return {'capacity_ah': 1.6 if scenario == 'transfer' else 2.0,
            'period_s': .05 if scenario == 'transfer' else .1}


def exact_fields(value, fields, location):
    if not isinstance(value, dict):
        raise ValueError(f'{location} must be a JSON object')
    missing, extra = fields - value.keys(), value.keys() - fields
    if missing or extra:
        raise ValueError(f'{location} fields differ: missing={sorted(missing)}, extra={sorted(extra)}')


def finite_number(value, location):
    # bool is an int subclass in Python, but it is not a measurement in JSON.
    if type(value) not in (int, float):
        raise ValueError(f'{location} must be a finite number, not a boolean or string')
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(f'{location} must be a finite number')


def validate_input(document):
    """Validate file structure while leaving cell-quality faults injectable."""
    if isinstance(document, list):
        raise ValueError('legacy list input is unsupported; export the scenario again to get '
                         'schema/config/samples with its capacity and sampling period')
    exact_fields(document, {'schema', 'config', 'samples'}, 'input')
    if document['schema'] != INPUT_SCHEMA:
        raise ValueError(f'input.schema must be {INPUT_SCHEMA!r}')
    config = document['config']
    exact_fields(config, {'capacity_ah', 'period_s'}, 'config')
    for key, value in config.items():
        finite_number(value, f'config.{key}')
        if value <= 0:
            raise ValueError(f'config.{key} must be positive')
    inputs = document['samples']
    if not isinstance(inputs, list) or not inputs:
        raise ValueError('samples must be a nonempty JSON array')
    last_now = None
    for index, sample in enumerate(inputs):
        location = f'samples[{index}]'
        exact_fields(sample, SAMPLE_FIELDS, location)
        for key in ('now_s', 'sampled_s', 'current_a', 'temp_c', 'remote_received_s'):
            finite_number(sample[key], f'{location}.{key}')
        for key in ('feedback_closed', 'remote_requested'):
            if type(sample[key]) is not bool:
                raise ValueError(f'{location}.{key} must be a JSON boolean (true or false)')
        cells = sample['cells_v']
        if not isinstance(cells, list):
            raise ValueError(f'{location}.cells_v must be a JSON array')
        for cell_index, value in enumerate(cells):
            finite_number(value, f'{location}.cells_v[{cell_index}]')
        if last_now is not None and sample['now_s'] <= last_now:
            raise ValueError(f'{location}.now_s must be strictly increasing')
        last_now = sample['now_s']
    return config, inputs


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key!r}')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f'non-finite JSON constant {value!r} is not allowed')


def load_input(path):
    raw = path.read_bytes()
    document = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
    config, inputs = validate_input(document)
    return raw, config, inputs


def samples(scenario):
    """Deterministic fixtures; sampled_s and now_s are different clocks of one timeline."""
    period = .05 if scenario == 'transfer' else .1
    for n in range(21):
        now = round(n * period, 6)
        cells = [3.70, 3.72, 3.68, 3.71]
        if scenario in ('undervoltage', 'feedback') and n >= 3:
            cells[2] = 2.95
        if scenario == 'spike' and n == 3:
            cells[2] = 2.95
        if scenario == 'transfer' and n >= 6:
            cells[0] = 2.98
        sampled = 0 if scenario == 'stale' and n >= 6 else now
        # In this fixture healthy switches open one sample after the UV command.
        opens_at = .55 if scenario == 'transfer' else .6
        closed = scenario == 'feedback' or now < opens_at or scenario in ('nominal', 'spike')
        if scenario == 'stale':
            closed = now < .7
        if scenario == 'timeout':
            closed = now < .9
        received = .4 if scenario == 'timeout' and n >= 5 else now
        yield {'now_s': now, 'sampled_s': sampled, 'cells_v': cells,
               'current_a': 1.0 if closed else 0.0, 'temp_c': 25.0,
               'feedback_closed': closed, 'remote_requested': True, 'remote_received_s': received}


class Controller:
    def __init__(self, capacity_ah=2.0, period_s=.1, rules=reference):
        if not all(math.isfinite(x) and x > 0 for x in (capacity_ah, period_s)):
            raise ValueError('capacity and sampling period must be finite and positive')
        self.rules = rules
        self.capacity_ah, self.period_s = capacity_ah, period_s
        self.soc, self.last_sample, self.last_now = 1.0, None, None
        self.uv_since, self.off_since = None, None
        self.faults = set()
        self.soc_valid = True

    def step(self, row):
        r = self.rules
        now, sampled = row['now_s'], row['sampled_s']
        # now is the controller's local monotonic clock, not a sensor timestamp.
        # A broken replay clock is an input contract error; do not poison state.
        if not math.isfinite(now) or (self.last_now is not None and now <= self.last_now):
            raise ValueError('controller clock must be finite and strictly increasing')
        cells, current, temp = row['cells_v'], row['current_a'], row['temp_c']
        fresh = (r.sample_ok(cells, sampled, now, .5)
                 and all(math.isfinite(x) for x in (current, temp))
                 and (self.last_sample is None or sampled > self.last_sample))
        # A repeated timestamp is not a new observation even while still younger than max_age.
        if not fresh:
            self.faults.add('SAMPLE_INVALID')
            self.soc_valid = False
        else:
            if self.last_sample is not None:
                dt = sampled - self.last_sample
                if dt <= self.period_s * 1.5:
                    # Left endpoint current held during each fixture interval.
                    self.soc = r.soc_step(self.soc, self.last_current, dt, self.capacity_ah)
                else:
                    self.soc_valid = False
                    self.faults.add('SAMPLE_GAP')
            self.last_sample, self.last_current = sampled, current
            if max(cells) >= 4.2:
                self.faults.add('OV')
            if not 0 <= temp <= 45:
                self.faults.add('TEMP')
            if min(cells) <= 3.0:
                if self.uv_since is None:
                    self.uv_since = now
                if now - self.uv_since >= .2 - 1e-9:
                    self.faults.add('UV')
            else:
                self.uv_since = None
        received = row['remote_received_s']
        remote_fresh = math.isfinite(received) and 0 <= now - received <= .3 + 1e-9
        if not remote_fresh:
            self.faults.add('COMM_TIMEOUT')
        command_on = r.remote_enable(not self.faults, fresh and remote_fresh, row['remote_requested'])
        if not command_on:
            if self.off_since is None:
                self.off_since = now
            if row['feedback_closed'] and now - self.off_since >= .2 - 1e-9:
                self.faults.add('ACTUATOR_STUCK')
        else:
            self.off_since = None
        self.last_now = now
        display_valid = len(cells) == 4 and all(math.isfinite(v) and 0 <= v <= 5 for v in cells)
        return {'now_s': now, 'sampled_s': sampled, 'min_v': min(cells) if display_valid else None,
                'pack_v': r.pack_voltage(cells) if display_valid else None, 'sample_valid': fresh,
                'soc': self.soc, 'soc_valid': self.soc_valid, 'command_on': command_on,
                'remote_fresh': remote_fresh, 'feedback_closed': row['feedback_closed'],
                'faults': '|'.join(sorted(self.faults))}


def replay(scenario, rules=reference):
    inputs = list(samples(scenario))
    return inputs, replay_samples(scenario_config(scenario), inputs, rules)


def replay_samples(config, inputs, rules=reference):
    controller = Controller(config['capacity_ah'], config['period_s'], rules)
    return [controller.step(row) for row in inputs]


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, indent=2)+'\n').encode('utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--scenario', choices=SCENARIOS, help='built-in fixture; defaults to nominal')
    source.add_argument('--input', type=Path, help='replay a bms-course-input-v1 JSON file, including its config')
    parser.add_argument('--out', type=Path, default=Path('.tmp-course-run'))
    parser.add_argument('--work', type=Path, help='run with the learner data/estimation/enable functions')
    args = parser.parse_args(argv)
    if args.out.exists() or args.out.is_symlink():
        parser.error(f'output path already exists: {args.out}; choose a new directory, '
                     'for example my-run/run-02, to preserve previous evidence')
    try:
        if args.input is not None:
            raw, config, inputs = load_input(args.input)
            scenario = 'custom'
            input_source = {'kind': 'file', 'path': str(args.input)}
        else:
            scenario = args.scenario or 'nominal'
            config = scenario_config(scenario)
            inputs = list(samples(scenario))
            document = {'schema': INPUT_SCHEMA, 'config': config, 'samples': inputs}
            validate_input(document)
            raw = json_bytes(document)
            input_source = {'kind': 'builtin', 'scenario': scenario}
        rules = load_work(args.work) if args.work else reference
        rows = replay_samples(config, inputs, rules)
        stream = StringIO(newline='')
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        trace_raw = stream.getvalue().encode('utf-8')
        report = {'scenario': scenario, 'model': 'virtual-4S-v1',
                  'input_source': input_source, 'config': config,
                  'python_version': sys.version.split()[0],
                  'argv': [sys.executable, *sys.argv] if argv is None else [sys.executable, __file__, *argv],
                  'implementation': 'learner' if args.work else 'reference',
                  'implementation_sha256': hashlib.sha256((args.work or Path(reference.__file__)).read_bytes()).hexdigest(),
                  'controller_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'input_sha256': hashlib.sha256(raw).hexdigest(),
                  'first_off_s': next((r['now_s'] for r in rows if not r['command_on']), None),
                  'last': rows[-1], 'hardware_verified': False}
        report_raw = json_bytes(report)
    except Exception as exc:
        # Parsing, learner execution and serialization finish before any output
        # directory is created. A failed exercise cannot leave a success report.
        parser.error(f'replay failed: {type(exc).__name__}: {exc}')
    try:
        args.out.mkdir(parents=True)
    except FileExistsError:
        parser.error(f'output path already exists: {args.out}; choose a new directory, '
                     'for example my-run/run-02, to preserve previous evidence')
    (args.out / 'input.json').write_bytes(raw)
    (args.out / 'trace.csv').write_bytes(trace_raw)
    (args.out / 'report.json').write_bytes(report_raw)
    print(report_raw.decode('utf-8'), end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
