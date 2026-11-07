"""Generate three vector scientific figures from the course's teaching equations.

python tools/generate_course_figures.py
python tools/generate_course_figures.py --check

Generation needs the existing matplotlib dependency and a Chinese sans-serif
font. --check uses only the standard library: numerical/label/palette semantics
and an SVG body digest make it portable across font and matplotlib versions.
These figures are calculated illustrations, not experimental measurements.
"""
from __future__ import annotations

import argparse
import hashlib
from io import StringIO
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/course/assets'
PALETTE = ROOT / 'tools/visual_palette.json'
SCHEMA = 'bms-course-scientific-figure-v1'
SVG = '{http://www.w3.org/2000/svg}'


def samples(start, stop, count):
    return [round(start + (stop - start) * n / (count - 1), 8) for n in range(count)]


def specifications():
    palette = json.loads(PALETTE.read_text(encoding='utf-8'))['light']
    colors = {key: palette[key] for key in ('paper', 'ink', 'muted', 'line', 'accent')}
    colors.update({key: palette['technical'][key] for key in ('red', 'gold')})
    current = samples(0, 4, 81)
    hours = samples(0, 8, 81)
    bleed_ma = samples(20, 100, 81)
    common = {'schema': SCHEMA, 'colors': colors, 'text_as_paths': True,
              'font_size_pt': 17, 'source': '按课程给定条件计算，非实测数据'}
    return [
        {**common, 'name': 'load-current-effects', 'lesson': '03-load.md',
         'title': '同一电阻下，电流翻倍会发生什么',
         'description': '总电阻0.12欧姆，电流0至4安培。上图压降随电流线性增加，下图发热功率按电流平方增加。2安培时压降0.24伏、发热0.48瓦；4安培时为0.48伏和1.92瓦。',
         'parameters': {'resistance_ohm': .12},
         'x': current, 'drop_v': [round(i * .12, 8) for i in current],
         'heat_w': [round(i * i * .12, 8) for i in current],
         'styles': ['solid-circle', 'dashed-square'],
         'labels': ['放电电流 I / A', '压降 ΔV / V', '发热功率 P / W',
                    'A · 压降与电流成正比', 'B · 发热与电流平方成正比']},
        {**common, 'name': 'soc-offset-drift', 'lesson': '11-drift.md',
         'title': '小小的电流偏移，会随时间累积',
         'description': '真实电流为零、容量为2安时。正0.02安培偏移让SOC低估，负0.02安培偏移让SOC高估。5小时后误差分别为负5和正5个百分点。误差定义为估计值减真实值。',
         'parameters': {'capacity_ah': 2, 'offsets_a': [.02, -.02]},
         'x': hours, 'positive_offset_error_pp': [-round(h, 8) for h in hours],
         'negative_offset_error_pp': hours,
         'styles': ['solid-triangle-down', 'dashed-circle'],
         'labels': ['持续时间 / h', 'SOC误差 / 个百分点',
                    '+0.02 A 偏移：SOC低估', '−0.02 A 偏移：SOC高估']},
        {**common, 'name': 'balance-current-budget', 'lesson': '14-balancing.md',
         'title': '均衡更快，也会增加瞬时发热',
         'description': '泄放电量0.10安时、单节电压固定4伏，连续导通。20、50、100毫安时所需时间分别为5、2、1小时，发热功率分别为0.08、0.20、0.40瓦。总泄放能量均约0.40瓦时。',
         'parameters': {'charge_ah': .1, 'cell_voltage_v': 4, 'duty': 1},
         'x': bleed_ma, 'duration_h': [round(.1 / (i / 1000), 8) for i in bleed_ma],
         'heat_w': [round(4 * i / 1000, 8) for i in bleed_ma],
         'styles': ['solid-circle', 'dashed-square'],
         'labels': ['泄放电流 / mA', '导通时间 / h', '发热功率 / W',
                    'A · 电流越大，所需时间越短', 'B · 电流越大，导通功率越高']},
    ]


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def font_name():
    from matplotlib import font_manager
    available = {font.name for font in font_manager.fontManager.ttflist}
    for candidate in ('Microsoft YaHei', 'Noto Sans CJK SC', 'Source Han Sans SC', 'SimHei'):
        if candidate in available:
            return candidate
    raise RuntimeError('需要中文无衬线字体：Microsoft YaHei / Noto Sans CJK SC / Source Han Sans SC / SimHei')


def figure_body(spec):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    c = spec['colors']
    plt.rcParams.update({
        'font.family': font_name(), 'font.size': spec['font_size_pt'],
        'axes.titlesize': 18, 'axes.labelsize': 17, 'xtick.labelsize': 16,
        'ytick.labelsize': 16, 'axes.unicode_minus': False, 'svg.fonttype': 'path',
        'svg.hashsalt': SCHEMA, 'figure.facecolor': c['paper'],
        'axes.facecolor': c['paper'], 'text.color': c['ink'],
        'axes.labelcolor': c['ink'], 'axes.edgecolor': c['muted'],
        'xtick.color': c['ink'], 'ytick.color': c['ink'],
        'savefig.facecolor': c['paper'],
    })
    stacked = spec['name'] != 'soc-offset-drift'
    fig, axes = plt.subplots(2 if stacked else 1, 1,
                             figsize=(7.5, 8.5 if stacked else 6.8))
    axes = list(axes) if stacked else [axes]
    fig.subplots_adjust(left=.18, right=.95, top=.86, bottom=.26 if stacked else .31,
                        hspace=.76 if stacked else .2)
    fig.suptitle(spec['title'], x=.5, y=.965, fontsize=20, weight='bold')

    def setup(ax, xlabel, ylabel, title=None):
        ax.set_xlabel(xlabel, labelpad=8)
        ax.set_ylabel(ylabel, labelpad=12)
        if title:
            ax.set_title(title, loc='left', pad=12)
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='y', color=c['line'], linewidth=.7, alpha=.75)
        ax.set_axisbelow(True)
        ax.yaxis.set_major_locator(MaxNLocator(5))

    def point(ax, x, y, label, color, marker, offset, align='left'):
        ax.plot([x], [y], marker=marker, markersize=8, markerfacecolor=c['paper'],
                markeredgecolor=color, markeredgewidth=2, linestyle='none', zorder=4)
        ax.annotate(label, xy=(x, y), xytext=offset, textcoords='offset points',
                    color=c['ink'], fontsize=15, ha=align, va='center',
                    bbox={'boxstyle': 'round,pad=.2', 'facecolor': c['paper'],
                          'edgecolor': 'none', 'alpha': .95})

    x = spec['x']
    labels = spec['labels']
    if spec['name'] == 'load-current-effects':
        for ax, y, ylabel, title, color, style, marker in (
            (axes[0], spec['drop_v'], labels[1], labels[3], c['accent'], '-', 'o'),
            (axes[1], spec['heat_w'], labels[2], labels[4], c['red'], '--', 's'),
        ):
            ax.plot(x, y, color=color, linestyle=style, linewidth=2.5)
            setup(ax, labels[0], ylabel, title)
            ax.set_xlim(0, 4.25)
            ax.set_xticks(range(5))
            ax.set_ylim(0, .58 if ax is axes[0] else 2.25)
            point(ax, 2, .24 if ax is axes[0] else .48,
                  '2 A → 0.24 V' if ax is axes[0] else '2 A → 0.48 W',
                  color, marker, (-10, 22), 'right')
            point(ax, 4, .48 if ax is axes[0] else 1.92,
                  '4 A → 0.48 V' if ax is axes[0] else '4 A → 1.92 W',
                  color, marker, (-9, -25), 'right')
        note = 'R = 0.12 Ω；ΔV = I × R；P = I² × R\n来源：第 3 课给定条件，公式计算（非实测）\n发热功率不是温升；散热与局部热点未在此建模。'
    elif spec['name'] == 'soc-offset-drift':
        ax = axes[0]
        ax.plot(x, spec['positive_offset_error_pp'], color=c['red'], linewidth=2.5,
                linestyle='-', marker='v', markevery=10, markersize=6, label=labels[2])
        ax.plot(x, spec['negative_offset_error_pp'], color=c['accent'], linewidth=2.5,
                linestyle='--', marker='o', markevery=10, markersize=6, label=labels[3])
        ax.axhline(0, color=c['gold'], linewidth=1.2, linestyle=':')
        setup(ax, labels[0], labels[1])
        ax.set_xlim(0, 8.2)
        ax.set_xticks(range(0, 9, 2))
        ax.set_ylim(-9, 9)
        ax.set_yticks([-8, -4, 0, 4, 8])
        ax.legend(loc='upper left', fontsize=14, frameon=True,
                  facecolor=c['paper'], edgecolor=c['line'])
        point(ax, 5, -5, '5 h → −5 个百分点', c['red'], 'v', (-6, -25), 'right')
        point(ax, 5, 5, '5 h → +5 个百分点', c['accent'], 'o', (10, 0), 'left')
        note = '误差 = 估计SOC − 真实SOC；Q = 2 Ah，真实电流 = 0 A\n来源：第 11 课给定条件，误差 = −偏移 × 时间 / Q × 100\n计算示意，未包含温度、容量变化或 SOC 边界截断。'
    else:
        for ax, y, ylabel, title, color, style, marker in (
            (axes[0], spec['duration_h'], labels[1], labels[3], c['accent'], '-', 'o'),
            (axes[1], spec['heat_w'], labels[2], labels[4], c['red'], '--', 's'),
        ):
            ax.plot(x, y, color=color, linestyle=style, linewidth=2.5)
            setup(ax, labels[0], ylabel, title)
            ax.set_xlim(15, 105)
            ax.set_xticks([20, 50, 100])
            ax.set_ylim(0, 5.8 if ax is axes[0] else .48)
            for current, offset in ((20, (8, 22)), (50, (7, 16)), (100, (-8, 18))):
                if current == 20 and ax is axes[0]:
                    offset = (8, -22)
                value = .1 / (current / 1000) if ax is axes[0] else 4 * current / 1000
                label = f'{value:g} h' if ax is axes[0] else f'{value:.2f} W'
                point(ax, current, value, label, color, marker, offset,
                      'right' if current == 100 else 'left')
        note = 'ΔQ = 0.10 Ah；V = 4.0 V；连续导通（100%）\n来源：第 14 课公式，t = ΔQ / I；P = V × I（非实测）\n总泄放能量均约 0.40 Wh；此图不计算温升。'
    fig.text(.06, .035, note, ha='left', va='bottom', fontsize=12.5,
             linespacing=1.6, color=c['muted'])
    buffer = StringIO()
    fig.savefig(buffer, format='svg', metadata={'Date': None, 'Creator': 'BMS-Z course scientific figures'})
    plt.close(fig)
    return buffer.getvalue()


def decorate(body, spec):
    # Matplotlib emits spaces at path-data line ends; normalize before hashing
    # and writing so regeneration remains stable and git whitespace checks pass.
    body = '\n'.join(line.rstrip() for line in body.splitlines()) + '\n'
    digest = hashlib.sha256(body.encode()).hexdigest()
    addition = (f'<metadata id="course-figure-data">{escape(canonical(spec))}</metadata>\n'
                f'<metadata id="course-figure-body-sha256">{digest}</metadata>\n'
                f'<title id="course-title">{escape(spec["title"])}</title>\n'
                f'<desc id="course-desc">{escape(spec["description"])}</desc>\n')
    body = body.replace('<svg ', '<svg role="img" aria-labelledby="course-title course-desc" ', 1)
    return re.sub(r'(<svg\b[^>]*>\n)', lambda m: m[1] + addition, body, count=1)


def check(path, expected):
    if not path.exists():
        return ['missing figure; run generator']
    text = path.read_text(encoding='utf-8')
    root = ET.fromstring(text)
    data = root.find(f'{SVG}metadata[@id="course-figure-data"]')
    digest = root.find(f'{SVG}metadata[@id="course-figure-body-sha256"]')
    problems = []
    if data is None or json.loads(data.text) != expected:
        problems.append('numeric/label/palette semantic drift; regenerate')
    body = re.sub(r'<(?:metadata|title|desc) id="course-[^"]+">[\s\S]*?</(?:metadata|title|desc)>\n', '', text)
    body = body.replace(' role="img" aria-labelledby="course-title course-desc"', '', 1)
    if digest is None or hashlib.sha256(body.encode()).hexdigest() != digest.text:
        problems.append('SVG body digest mismatch; regenerate')
    if root.get('role') != 'img' or root.find(f'{SVG}title') is None or root.find(f'{SVG}desc') is None:
        problems.append('missing accessible title/description')
    if any(True for _ in root.iter(f'{SVG}image')) or not any(True for _ in root.iter(f'{SVG}path')):
        problems.append('figure must contain vector paths without raster image payloads')
    source = (ROOT / 'docs/course' / expected['lesson']).read_text(encoding='utf-8')
    if f'assets/{expected["name"]}.svg' not in source:
        problems.append('figure is not referenced by its lesson')
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='verify embedded semantics and SVG integrity without matplotlib/font requirements')
    args = parser.parse_args()
    failed = False
    for spec in specifications():
        target = OUTPUT / f'{spec["name"]}.svg'
        if not args.check:
            OUTPUT.mkdir(parents=True, exist_ok=True)
            target.write_text(decorate(figure_body(spec), spec), encoding='utf-8', newline='\n')
        problems = check(target, spec)
        print(f'{"FAIL" if problems else "PASS"} {target.relative_to(ROOT)}' +
              (': ' + '; '.join(problems) if problems else ' — numeric semantics, vector paths and digest'))
        failed |= bool(problems)
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
