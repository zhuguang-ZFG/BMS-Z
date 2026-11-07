"""Replay a virtual 4S pack. No hardware connection; all thresholds are teaching values."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import reference
from learn import load_work

SCENARIOS = ('nominal', 'spike', 'undervoltage', 'stale', 'feedback', 'timeout', 'transfer')


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
    controller = Controller(1.6 if scenario == 'transfer' else 2, .05 if scenario == 'transfer' else .1, rules)
    inputs = list(samples(scenario))
    return inputs, [controller.step(row) for row in inputs]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', choices=SCENARIOS, default='nominal')
    parser.add_argument('--out', type=Path, default=Path('.tmp-course-run'))
    parser.add_argument('--work', type=Path, help='run with the learner data/estimation/enable functions')
    args = parser.parse_args()
    rules = load_work(args.work) if args.work else reference
    inputs, rows = replay(args.scenario, rules)
    args.out.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(inputs, ensure_ascii=False, sort_keys=True, allow_nan=False, indent=2)+'\n').encode()
    (args.out / 'input.json').write_bytes(raw)
    with (args.out / 'trace.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    report = {'scenario': args.scenario, 'model': 'virtual-4S-v1',
              'implementation': 'learner' if args.work else 'reference',
              'implementation_sha256': hashlib.sha256((args.work or Path(reference.__file__)).read_bytes()).hexdigest(),
              'controller_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'input_sha256': hashlib.sha256(raw).hexdigest(),
              'first_off_s': next((r['now_s'] for r in rows if not r['command_on']), None),
              'last': rows[-1], 'hardware_verified': False}
    (args.out / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
