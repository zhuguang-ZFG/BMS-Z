"""Create and check a learner-owned file. No pip packages required."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import shutil
import traceback

import reference

ROOT = Path(__file__).resolve().parent


def load_work(path):
    spec = importlib.util.spec_from_file_location('bms_course_learner', path.resolve())
    if path.suffix.lower() != '.py' or spec is None or spec.loader is None:
        raise ValueError('作业文件必须以 .py 结尾，请检查是否保存成了 .py.txt')
    module = importlib.util.module_from_spec(spec)
    # Always read saved source: equal-size edits within one timestamp tick can
    # otherwise reuse an older answer from the loader's bytecode cache.
    code = compile(path.read_bytes(), str(path.resolve()), 'exec', dont_inherit=True)
    exec(code, module.__dict__)
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
        return (isinstance(actual, (float, int)) and not isinstance(actual, bool)
                and abs(actual - expected) < 1e-8)
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
    parser = argparse.ArgumentParser(description='创建并检查自己的 BMS 作业，只需 Python 标准库。')
    parser.add_argument('action', choices=['doctor', 'init', 'check'],
                        help='doctor 检查环境；init 创建作业；check 检查实现')
    parser.add_argument('--work', type=Path, help='自己的 .py 作业文件，例如 my_bms.py')
    parser.add_argument('--through', type=int, default=4, choices=range(4, 19),
                        help='检查到哪一课，默认第 4 课；此前各课也会一起检查')
    parser.add_argument('--reference', action='store_true', help='检查配套参考实现，不代表自己的作业通过')
    args = parser.parse_args()
    if args.action == 'doctor':
        import sys
        print(f'Python {sys.version.split()[0]}; standard library only; project={ROOT}')
        print('PASS: struct / binascii / csv / json available; no board or serial port required')
        print('环境可用。第 4 课首次运行 init 创建作业，以后编辑原文件并运行 check。')
        return 0
    if args.action == 'init':
        if args.work is None:
            parser.error('init 需要 --work path.py，指定自己的作业文件')
        if args.work.exists():
            parser.error('work file already exists：作业已存在，直接编辑并运行 check；init 不会覆盖它')
        args.work.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'workbook.py', args.work)
        print(f'created {args.work}; lesson 04 is ready, lessons 05..18 are yours to implement')
        print('已创建作业。接着运行 check --work 后接这个文件名，--through 后接已学课次。')
        return 0
    if args.reference == (args.work is not None):
        parser.error('check 请用 --work path.py 检查自己的作业，或用 --reference 检查参考实现，二选一')
    try:
        module = reference if args.reference else load_work(args.work)
    except SyntaxError as exc:
        parser.exit(1, f'作业语法错误：{exc.filename or args.work}:{exc.lineno}：{exc.msg}\n'
                    '请打开这一行，检查英文冒号、括号和行首缩进，保存后重新运行 check。\n')
    except (OSError, ValueError) as exc:
        parser.exit(1, f'无法载入作业 {args.work}：{type(exc).__name__}: {exc}\n'
                    '请核对 --work 后的路径、文件扩展名和读取权限；尚未创建作业时先运行 init。\n')
    except Exception as exc:
        frames = traceback.extract_tb(exc.__traceback__)
        line = next((frame.lineno for frame in reversed(frames)
                     if Path(frame.filename).resolve() == args.work.resolve()), None)
        location = f'{args.work}:{line}' if line is not None else str(args.work)
        parser.exit(1, f'作业载入失败：{location}：{type(exc).__name__}: {exc}\n'
                    '错误发生在函数检查之前，请先检查文件加载时执行的语句和导入。\n')
    passed, failures = grade(module, args.through)
    print(f'{"REFERENCE" if args.reference else "LEARNER"}: {passed} passed, {len(failures)} failed, through lesson {args.through:02d}')
    print(f'{"参考实现" if args.reference else "学员作业"}：通过 {passed} 项，失败 {len(failures)} 项，检查到第 {args.through:02d} 课。')
    for failure in failures:
        print(f'FAIL {failure}')
    if failures and not args.reference:
        print(f'先回到第 {failures[0][:2]} 课，检查上面列出的函数；修正后用原命令重跑。')
        print('args 是输入，expected 是应得结果，got 是实际结果；出现异常时先按异常消息定位。')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
