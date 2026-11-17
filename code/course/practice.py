"""Small paired experiments: predict first, ask for hints, then reveal the result."""
from __future__ import annotations

import argparse
import random

import project
import reference

CASES = ('load', 'pulse', 'capacity', 'stale')


def make_exercise(name, seed):
    rng = random.Random(seed)
    if name == 'load':
        current, resistance = rng.choice((1, 2, 3)), rng.choice((.08, .12, .16))
        return {
            'title': '电流翻倍，掉压和发热也都翻倍吗？',
            'lesson': '03',
            'inputs': {'current_a': current, 'resistance_ohm': resistance},
            'conditions': [
                f'4S 教学包：OCV=14.80 V，总电阻 R={resistance:.2f} Ω，假定保持不变。',
                f'A：放电电流 {current} A；B：只把电流改为 {2 * current} A。'],
            'question': '分别算端电压和电阻上的发热功率，再比较两者变化的倍数。',
            'hints': ('先算 I×R 的压降，再从 OCV 中扣除。',
                      '发热功率是 I²×R。电流在这个式子里出现了两次。'),
            'answer': {'voltage_a': 14.8 - current * resistance,
                       'voltage_b': 14.8 - 2 * current * resistance,
                       'power_a': current ** 2 * resistance,
                       'power_b': (2 * current) ** 2 * resistance},
        }
    if name == 'pulse':
        period = rng.choice((.05, .1))
        times = [round(n * period, 6) for n in range(14)]
        unsafe_a = [n in (2, 3) for n in range(14)]
        unsafe_b = [n >= 2 for n in range(14)]
        return {
            'title': '连续两个低样本，够不够触发保护？',
            'lesson': '08',
            'inputs': {'period_s': period},
            'conditions': [
                f'等间隔采样周期 {period:.2f} s，欠压连续确认时间 0.20 s。',
                '编号从 0 开始：A 只有第 2、3 号点欠压，第 4 号起恢复；B 从第 2 号起持续欠压。',
                '样本均有效，只比较首次欠压确认，不包含执行器等待。',
                '采样时间(s)：' + ', '.join(f'{time:.2f}' for time in times)],
            'question': 'A、B 各在何时首次确认欠压？没有触发就写“未触发”。',
            'hints': ('给第一个欠压点记下时间，先数相邻点之间有几个时间间隔。',
                      '用当前时间减去连续欠压的起点；中途恢复会清掉尚未触发的计时。'),
            'answer': {'trip_a': reference.trip_at(times, unsafe_a, .2),
                       'trip_b': reference.trip_at(times, unsafe_b, .2)},
        }
    if name == 'capacity':
        current, duration = rng.choice((.5, 1, 2)), rng.choice((180, 360, 720))
        return {
            'title': '同样放出一笔电量，SOC 为什么降得不同？',
            'lesson': '10',
            'inputs': {'current_a': current, 'duration_s': duration},
            'conditions': [
                f'两组初始 SOC 都为 0.80，均以 {current} A 放电 {duration} s，忽略损耗和参数变化。',
                'A：容量 2.0 Ah；B：只把容量改为 1.6 Ah。'],
            'question': '各放出多少 Ah？各剩多少 SOC？先判断哪个比例降得更多。',
            'hints': ('电流乘时间得到 Ah 前，先把秒换成小时。',
                      '扣掉的 SOC 比例 = 放出 Ah / 各自容量；两组的分母不同。'),
            'answer': {'charge_ah': current * duration / 3600,
                       'soc_a': reference.soc_step(.8, current, duration, 2),
                       'soc_b': reference.soc_step(.8, current, duration, 1.6)},
        }
    if name == 'stale':
        now = rng.choice((.05, .1, .2))
        baseline = next(project.samples('nominal'))
        a = dict(baseline, now_s=now, sampled_s=now, remote_received_s=now)
        b = dict(a, sampled_s=0)
        rows = []
        for sample in (a, b):
            controller = project.Controller(period_s=now)
            controller.step(baseline)
            rows.append(controller.step(sample))
        return {
            'title': '数值正常、年龄没过期，为什么仍然禁止输出？',
            'lesson': '20',
            'inputs': {'now_s': now},
            'conditions': [
                '两组各自从同一控制器初态开始，0 s 时都已接受一行采样时间为 0 s 的正常记录。',
                f'采样周期 {now:.2f} s，下一拍本地时间 {now:.2f} s，四节电压仍为 3.70、3.72、3.68、3.71 V。',
                f'A：采样时间为 {now:.2f} s；B：只把采样时间改为 0 s。',
                '电流和温度正常，远程请求刚更新，开关反馈闭合；样本最大年龄为 0.50 s。'],
            'question': '年龄检查与完整控制循环会得到相同判断吗？写出两组的采样、SOC 质量和输出许可。',
            'hints': ('检查样本年龄之后，还要把本拍采样时间与上一拍对照。',
                      'sample_ok 只检查单行范围与年龄；Controller 另外要求时间递增，并保留 SOC 质量故障。'),
            'answer': {'age_only_ok': reference.sample_ok(b['cells_v'], 0, now, .5),
                       'a': rows[0], 'b': rows[1]},
        }
    raise ValueError(f'unknown exercise: {name}')


def show_answer(name, exercise):
    answer = exercise['answer']
    print('\n参考推演（教学配置，不是学员作业评分）')
    if name == 'load':
        for label in ('a', 'b'):
            print(f'{label.upper()}：端电压 {answer[f"voltage_{label}"]:.3f} V；'
                  f'发热功率 {answer[f"power_{label}"]:.3f} W')
        print('电阻不变时，电流翻倍使压降翻倍、发热功率变为四倍；真实温升还取决于散热等条件。')
    elif name == 'pulse':
        for label in ('a', 'b'):
            time = answer[f'trip_{label}']
            print(f'{label.upper()}：' + ('未触发' if time is None else f'{time:.2f} s 首次确认欠压'))
        print('两个欠压点只隔了一个采样周期。比较连续经过的秒数，不能拿低样本个数代替时长。')
    elif name == 'capacity':
        print(f'两组均放出 {answer["charge_ah"]:.6f} Ah。')
        print(f'A：SOC {answer["soc_a"]:.4%}；B：SOC {answer["soc_b"]:.4%}。')
        print('同样的 Ah 除以更小的容量，得到更大的 SOC 降幅；这不表示放出的电量变多了。')
    else:
        print(f'只检查单行范围与年龄：两组都是 {answer["age_only_ok"]}。')
        for label in ('a', 'b'):
            row = answer[label]
            print(f'{label.upper()}：sample_valid={row["sample_valid"]}，soc_valid={row["soc_valid"]}，'
                  f'command_on={row["command_on"]}，remote_fresh={row["remote_fresh"]}，'
                  f'faults={row["faults"] or "无"}')
        print('B 重复用了已经接收过的采样时间。远程消息仍新鲜，故障来自测量链。')


def main(argv=None):
    parser = argparse.ArgumentParser(description='四组对照练习：先预测，再看提示，最后核对。只需 Python 标准库。')
    parser.add_argument('--case', choices=CASES, default='load', help='选一组练习，默认 load')
    parser.add_argument('--seed', type=int, default=7, help='固定题目条件；复现时使用相同种子和代码版本')
    reveal = parser.add_mutually_exclusive_group()
    reveal.add_argument('--hint', type=int, choices=(1, 2), help='显示第 1 级或累计两级提示')
    reveal.add_argument('--solve', action='store_true', help='写完预测后再显示参考推演')
    args = parser.parse_args(argv)
    exercise = make_exercise(args.case, args.seed)
    print(f'{exercise["title"]}\n题目：{args.case}；种子：{args.seed}；回看第 {exercise["lesson"]} 课。')
    for condition in exercise['conditions']:
        print(condition)
    print(f'先写预测：{exercise["question"]}')
    if args.hint:
        for number, hint in enumerate(exercise['hints'][:args.hint], 1):
            print(f'提示 {number}：{hint}')
    if args.solve:
        show_answer(args.case, exercise)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
