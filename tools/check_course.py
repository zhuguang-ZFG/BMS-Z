#!/usr/bin/env python3
"""Validate the ordered course contract without conflating it with reader acceptance."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
COURSE = ROOT / 'docs/course'


def validate(data, directory=COURSE):
    problems, seen, files, counts = [], set(), set(), {}
    modules = {m['id'] for m in data['modules']}
    lessons = data['lessons']
    if len(lessons) != 24 or len(modules) != 8:
        problems.append('expected 24 sequential lessons and 8 distinct modules')
    for number, lesson in enumerate(lessons, 1):
        key = lesson['id']
        if key != f'{number:02d}' or key in seen:
            problems.append(f'{key}: duplicate or out-of-order lesson ID')
        if any(dep not in seen for dep in lesson['requires']):
            problems.append(f'{key}: prerequisite not taught earlier')
        if number > 1 and f'{number - 1:02d}' not in lesson['requires']:
            problems.append(f'{key}: missing transition from previous lesson')
        seen.add(key)
        module = lesson['module']
        if module not in modules:
            problems.append(f'{key}: unknown module {module}')
        counts[module] = counts.get(module, 0) + 1
        filename = lesson['file']
        if filename in files or Path(filename).name != filename:
            problems.append(f'{key}: duplicate file or path outside course')
        files.add(filename)
        path = directory / filename
        if not path.is_file():
            problems.append(f'{key}: missing manuscript {filename}')
            continue
        text = path.read_text(encoding='utf-8')
        if not text.startswith(f'# {key} · '):
            problems.append(f'{key}: heading ID differs from manifest')
        if '先修：' not in text:
            problems.append(f'{key}: missing prerequisite explanation')
        checks = re.findall(r'<details class="course-check">([\s\S]*?)</details>', text)
        if len(checks) != 1 or not re.search(r'<summary>[^<]+</summary>\s*\S', checks[0]):
            problems.append(f'{key}: independent answer section missing or empty')
        if re.search(r'<details\b[^>]*\bopen', text):
            problems.append(f'{key}: website reveals answer before attempt')
        if number < len(lessons) and f']({lessons[number]["file"]})' not in text:
            problems.append(f'{key}: no link to next lesson')
        if lesson['exercise'] not in {'units','pack','load','pack_voltage','calibrate','sample_ok',
                'violations','trip_at','can_reset','soc_step','drift','ocv_soc','charge_allowed',
                'balance_hours','remaining_ah','decode','sequence_ok','remote_enable','integration',
                'faults','capstone','trace','matrix','portfolio'}:
            problems.append(f'{key}: unregistered exercise')
    if any(counts.get(module) != 3 for module in modules):
        problems.append('each module must have three connected lessons')
    return problems


def main():
    data = json.loads((COURSE / 'manifest.json').read_text(encoding='utf-8'))
    problems = validate(data)
    if problems:
        print('\n'.join(f'FAIL {message}' for message in problems))
        return 1
    print('PASS: 24 ordered lessons, 8 modules, earlier prerequisites, exercises and hidden website rubrics')
    print('W5 real reader acceptance and hardware evidence remain separate.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
