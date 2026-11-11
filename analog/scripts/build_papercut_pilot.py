"""按用户授权，用 Python 矢量绘制纸层插图；底图与中文技术层分开落盘。

`ch17_papercut_figures.FIGURES` 保留最初三张试片；`BACKLOG` 汇总 Task 8
各章的 backlog 插图。两批共用同一 compose 与 manifest 登记路径，区别只在
审图目录与来源脚本。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import check_visual_manifest as manifest
from compose_technical_overlay import compose, preview
from scripts.visuals.papercut import PAPER, svg
from scripts.visuals.scenes.ch17_papercut_figures import FIGURES
from scripts.visuals.scenes import (
    ch00_backlog_figures, ch08_backlog_figures, ch14_backlog_figures,
    ch17_backlog_figures, ch18_backlog_figures,
)

REVIEW = 'docs/superpowers/visual/reviews/python-papercut-2026-11-05'
TASK8_REVIEW = 'docs/superpowers/visual/reviews/task8-2026-11-05'

ORIGINAL_ALT = {
    'ch17-i2c-rise-time-budget': '左图按 Rp,max=tr/(0.8473×Cb) 绘制电阻上限；400pF 时约为 2.9kΩ，10kΩ 工作点在上限之外；右图标出开漏总线的上拉电阻与电容。',
    'ch17-thermal-chain-audit': '纸层芯片、外壳和散热器依次连接为热阻链；同样 3.5W 损耗与 25°C 环境，正文两种热阻示例给出 235°C 与约 57°C 的结温估算。',
    'ch17-prior-cost-matrix': '等面积四象限定性比较故障概率和验证成本；高概率且易验证的电源连接优先测量，拆焊与低概率项后置；图形和文字共同区分顺序。',
}


def backlog():
    out = {}
    out.update(ch17_backlog_figures.FIGURES)
    out.update(ch00_backlog_figures.FIGURES)
    out.update(ch08_backlog_figures.FIGURES)
    out.update(ch14_backlog_figures.FIGURES)
    out.update(ch18_backlog_figures.FIGURES)
    return out


def registry():
    """统一成 {id: meta}；原始三张保留旧审图目录，新图进 Task 8 目录。"""
    out = {}
    for asset_id, (draw, title, anchor, layout, kind) in FIGURES.items():
        out[asset_id] = {
            'draw': draw, 'title': title, 'anchor': anchor, 'layout': layout,
            'type': kind, 'chapter': 17, 'source': 'docs/p4-02-ch17.md',
            'alt': ORIGINAL_ALT[asset_id], 'review': REVIEW,
            'source_script': 'scripts/visuals/scenes/ch17_papercut_figures.py',
        }
    for asset_id, meta in backlog().items():
        scripts = {
            0: 'scripts/visuals/scenes/ch00_backlog_figures.py',
            8: 'scripts/visuals/scenes/ch08_backlog_figures.py',
            14: 'scripts/visuals/scenes/ch14_backlog_figures.py',
            17: 'scripts/visuals/scenes/ch17_backlog_figures.py',
            18: 'scripts/visuals/scenes/ch18_backlog_figures.py',
        }
        script = scripts[meta['chapter']]
        out[asset_id] = {**meta, 'review': TASK8_REVIEW, 'source_script': script}
    return out


def build(asset_id: str, render=False, meta=None):
    meta = meta or registry()[asset_id]
    base, technical = meta['draw']()
    review = meta.get('review', REVIEW)
    folder = ROOT / review
    folder.mkdir(parents=True, exist_ok=True)
    base_path = f'{review}/{asset_id}-base.svg'
    overlay_path = f'{review}/{asset_id}-overlay.svg'
    (ROOT / base_path).write_text(svg(base), encoding='utf-8')
    (ROOT / overlay_path).write_text(svg(technical), encoding='utf-8')
    spec = {'id': asset_id, 'title': meta['title'], 'alt': meta['alt'],
            'canvas': [1448, 1086], 'print_width_mm': 138, 'paper': PAPER,
            'base_svg': base_path, 'overlay': overlay_path,
            'output': f'assets/figures-v2/{asset_id}.svg',
            'chapter': meta.get('chapter', 17), 'source': meta.get('source', 'docs/p4-02-ch17.md'),
            'source_script': meta.get('source_script', 'scripts/visuals/scenes/ch17_papercut_figures.py'),
            'review': review, 'anchor': meta['anchor']}
    (folder / f'{asset_id}.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    outputs = compose(spec)
    if render:
        # 预览输出留在审图目录，正式目录只保留登记的 SVG 与 WebP。
        for name, output in outputs.items():
            copied = folder / output.name
            copied.write_bytes(output.read_bytes())
            print(asset_id, name, preview(copied, spec))
        preview_path = Path(spec['output']).with_suffix('.webp')
        (ROOT / preview_path).write_bytes((folder / f'{asset_id}.webp').read_bytes())
        spec['preview_ready'] = True
    return spec, meta['anchor'], meta['layout'], meta['type']


def register(spec, anchor, layout, kind, data):
    asset_id = spec['id']
    prompt_path = f'docs/superpowers/visual/prompts/{asset_id}.md'
    source = spec.get('source', 'docs/p4-02-ch17.md')
    review = spec.get('review', REVIEW)
    record = {'id': asset_id, 'generator': 'python-svg-papercut-v1',
              'reference_policy': 'name+style+traits', 'style_id': 'FF-015', 'layout_id': layout,
              'color_ids': ['C-34', 'C-32', 'C-35', 'C-26'], 'numbers': [],
              'source_facts': [f'{source}#{anchor}'],
              'authorization': '2026-11-05 用户允许 Python 绘制插图',
              'source_script': spec.get('source_script', 'scripts/visuals/scenes/ch17_papercut_figures.py'),
              'composition': f'{review}/{asset_id}.json',
              'zh_prompt': f'风格名称：纸雕插画。主题：{spec["title"]}。采用平视等厚纸层、奶油白纸、炭黑墨、石板灰阴影、柿子橙重点。由 Python 绘制完整矢量插图，厚度不编码量值；公式、电路和中文由独立 SVG 技术层绘制。',
              'en_prompt': f'Style name: Paper Sculpture Illustration. Subject: {spec["title"]}. A deterministic Python SVG with equally thick paper layers, cream paper, charcoal ink, slate shadows and persimmon accents. Layer depth never encodes values. Equations, circuits and labels occupy a separate technical SVG layer.'}
    (ROOT / prompt_path).write_text('---\n' + yaml.safe_dump(record, allow_unicode=True, sort_keys=False, width=100) + '---\n', encoding='utf-8')
    asset = {'id': asset_id, 'chapter': spec.get('chapter', 17), 'kind': 'figure', 'type': kind,
             'anchor': anchor, 'purpose': spec['title'], 'style_id': 'FF-015', 'layout_id': layout,
             'color_ids': record['color_ids'], 'source_facts': record['source_facts'],
             'prompt_file': prompt_path, 'output': spec['output'],
             'print_fallback': spec['output'].replace('.svg', '-print.svg'),
             'alt': spec['alt'],
             'status': 'generated', 'status_history': ['planned', 'generated'], 'review_scores': {},
             'generator': record['generator'], 'composition': record['composition'],
             'quant_rules': {'layer_encodes_value': False, 'value_channel': 'overlay-axis',
                             'leader_route': 'margin', 'accent_on': 'paper',
                             'series_distinguisher': ['marker', 'label', 'dash']}}
    if spec.get('preview_ready'):
        asset['preview'] = spec['output'].replace('.svg', '.webp')
    existing = next((a for a in data['assets'] if a['id'] == asset_id), None)
    if existing is not None:
        # 仅逐字节相同的产物能沿用评分；改图后必须重新审查。
        digest = hashlib.sha256((ROOT / spec['output']).read_bytes()).hexdigest()
        if existing.get('review_record', {}).get('asset_sha256') == digest:
            for key in ('status', 'status_history', 'review_scores', 'review_record', 'preview'):
                if key in existing:
                    asset[key] = existing[key]
        data['assets'][data['assets'].index(existing)] = asset
    else:
        data['assets'].append(asset)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--render', action='store_true', help='浏览器渲染并检查彩色、灰度和字号')
    ap.add_argument('--only', action='append', default=[], help='只重建指定 id')
    args = ap.parse_args(argv)
    data = manifest.load()
    items = registry()
    chosen = args.only or list(items)
    for asset_id in chosen:
        register(*build(asset_id, args.render, items[asset_id]), data)
    manifest.dump(data)
    manifest.dump(manifest.animation_index(data), manifest.MANIFEST.with_name('animation-v2-manifest.yml'))
    print(f'{len(chosen)} 张 Python 纸层插图已绘制；审查状态从未审图开始，需检查实际产物。')


if __name__ == '__main__':
    main()
