#!/usr/bin/env python3
"""Wave 3 纸层插图：ch13/ch15/ch16 共 8 张，落盘、预览并登记 manifest。"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import check_visual_manifest as manifest
from compose_technical_overlay import preview
from label_handraw_figures import label  # noqa: E402
from scripts.visuals import static_fig
from scripts.visuals.font_gate import assert_covered
from scripts.visuals.scenes.ch13_backlog_figures import FIGURES as CH13
from scripts.visuals.scenes.ch15_backlog_figures import FIGURES as CH15
from scripts.visuals.scenes.ch15_backlog_figures2 import FIGURES as CH15B
from scripts.visuals.scenes.ch16_backlog_figures import FIGURES as CH16

REVIEW = ROOT / 'docs/superpowers/visual/reviews/task8-2026-11-05'
PROMPTS = ROOT / 'docs/superpowers/visual/prompts'
ASSETS = ROOT / 'assets/figures-v2'
CANVAS = (1448, 1086)
PRINT_MM = 138
STYLE = 'FF-015'
COLORS = ['C-34', 'C-32', 'C-35', 'C-26']
GENERATOR = 'python-svg-papercut-v1'


def render(meta: dict) -> str:
    parts = meta['draw']()
    if parts and isinstance(parts[0], (list, tuple)):
        parts = [item for group in parts for item in group]
    inner = '\n'.join(parts)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS[0]} {CANVAS[1]}">'
           f'\n{inner}\n</svg>\n')
    return label(static_fig.finalize(svg, meta['title']), meta)


def build_one(asset_id: str, meta: dict) -> None:
    if meta.get('renderer') == 'handdrawn':
        import build_handdrawn_wave2
        build_handdrawn_wave2.build_one(asset_id, meta)
        return
    svg = render(meta)
    assert_covered(svg, asset_id)
    REVIEW.mkdir(parents=True, exist_ok=True)
    review_svg = REVIEW / f'{asset_id}.svg'
    review_svg.write_text(svg, encoding='utf-8')
    for suffix in ('.svg', '-print.svg'):
        (ASSETS / f'{asset_id}{suffix}').write_text(svg, encoding='utf-8')
    report = preview(review_svg, {'canvas': list(CANVAS), 'print_width_mm': PRINT_MM})
    (ASSETS / f'{asset_id}.webp').write_bytes(review_svg.with_suffix('.webp').read_bytes())
    spec = {
        'id': asset_id, 'title': meta['title'], 'alt': meta['alt'],
        'anchor': meta['anchor'], 'source': meta['source'],
        'canvas': list(CANVAS), 'print_width_mm': PRINT_MM,
        'generator': GENERATOR,
        'output': f'assets/figures-v2/{asset_id}.svg',
        'print_fallback': f'assets/figures-v2/{asset_id}-print.svg',
    }
    (REVIEW / f'{asset_id}.json').write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(asset_id, report)


def register(asset_id: str, meta: dict, data: dict) -> None:
    if meta.get('renderer') == 'handdrawn':
        import build_handdrawn_wave2
        build_handdrawn_wave2.register(asset_id, meta, data)
        return
    prompt = PROMPTS / f'{asset_id}.md'
    record = {
        'id': asset_id, 'generator': GENERATOR,
        'reference_policy': 'name+style+traits', 'style_id': STYLE,
        'layout_id': meta['layout'], 'color_ids': COLORS, 'numbers': [],
        'source_facts': [f'{meta["source"]}#{meta["anchor"]}'],
        'authorization': '2026-11-05 用户要求增加插图与手绘',
        'composition': f'docs/superpowers/visual/reviews/task8-2026-11-05/{asset_id}.json',
        'zh_prompt': (f'风格名称：纸雕三层。主题：{meta["title"]}。'
                      '米白纸底、石板灰与炭黑纸层、少量赭石标记；'
                      '中文标签保持印刷可读，几何不编码虚假量值。'),
        'en_prompt': (f'Style name: three-layer papercut. Subject: {meta["title"]}. '
                      'Ivory paper ground, slate and charcoal paper layers, restrained ochre accents; '
                      'print-readable Chinese labels; geometry never encodes invented values.'),
    }
    prompt.write_text('---\n' + yaml.safe_dump(
        record, allow_unicode=True, sort_keys=False, width=100) + '---\n',
        encoding='utf-8')
    asset = {
        'id': asset_id, 'chapter': meta['chapter'], 'kind': 'figure', 'type': meta['type'],
        'anchor': meta['anchor'], 'purpose': meta['title'], 'style_id': STYLE,
        'layout_id': meta['layout'], 'color_ids': COLORS,
        'source_facts': record['source_facts'],
        'prompt_file': f'docs/superpowers/visual/prompts/{asset_id}.md',
        'output': f'assets/figures-v2/{asset_id}.svg',
        'print_fallback': f'assets/figures-v2/{asset_id}-print.svg',
        'preview': f'assets/figures-v2/{asset_id}.webp',
        'alt': meta['alt'], 'status': 'generated',
        'status_history': ['planned', 'generated'], 'review_scores': {},
        'generator': GENERATOR, 'composition': record['composition'],
        'quant_rules': {
            'layer_encodes_value': False,
            'value_channel': 'overlay-axis',
            'leader_route': 'margin',
            'accent_on': 'paper',
            'series_distinguisher': ['marker', 'label', 'dash'],
        },
    }
    old = next((a for a in data['assets'] if a['id'] == asset_id), None)
    if old is None:
        data['assets'].append(asset)
        return
    # 与手绘 builder 同规矩：底图字节未变才带过人工审图结果。
    raw = (ASSETS / f'{asset_id}.svg').read_bytes().replace(b'\r\n', b'\n')
    reviewed = (old.get('review_record') or {}).get('asset_sha256')
    if reviewed and reviewed == hashlib.sha256(raw).hexdigest():
        for field in ('status', 'status_history', 'review_scores', 'review_record'):
            if old.get(field):
                asset[field] = old[field]
    data['assets'][data['assets'].index(old)] = asset


def main() -> int:
    data = manifest.load()
    figures = {**CH13, **CH15, **CH15B, **CH16}
    for asset_id, meta in figures.items():
        build_one(asset_id, meta)
        register(asset_id, meta, data)
    manifest.dump(data)
    print(f'{len(figures)} 张纸层插图已绘制；待人工审图。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
